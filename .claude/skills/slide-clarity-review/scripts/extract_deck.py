#!/usr/bin/env python3
"""extract_deck.py — .pptx から事実情報（deck-facts.json）を抽出する。

使い方: python extract_deck.py <deck.pptx> -o <deck-facts.json>
依存: 標準ライブラリのみ（zipfile + xml.etree）。python-pptx は使わない。

注意: python-pptx を使っていた旧版を、依存を減らすため標準ライブラリで書き直した版（2026-11）。
旧版と同じ出力 JSON になることは、_shared/scripts/test_slide_skills.py の試験（python-pptx で作った
fixture を読む）で確かめる。旧版から text_blocks を足した。

抽出の定義（スライド毎）:
  title        タイトルプレースホルダの文字列（strip 後。無い／空なら null）
  body_chars   タイトル以外の全テキスト（表のセル・グループ内を再帰的に含む。ノート・改行は数えない）
  bullet_count タイトル以外のテキストフレームで strip 後に非空の段落数（グループ内は再帰。表のセルは数えない）
  min_font_pt  明示指定された run のフォントサイズ(pt)の最小値。明示指定が無ければ null（継承値は取れない）
  image_count  画像（picture）シェイプ数（グループ内を再帰。プレースホルダ内の画像は数えない）
  has_notes    ノートに非空テキストがあるか
  paragraphs   タイトル以外の非空段落のテキスト（表のセルは含まない。reviewer が内容を判定するための事実情報）
  text_blocks  タイトル以外の文面を、画面の位置順（上から下、左から右）に並べたもの。図形ごとの段落と、表のセル（行ごと）を含む。日本語点検が読む
  shapes       タイトル以外のトップレベル図形の kind / left / top / width / height（インチ, 小数 2 桁）と fill（明示された塗り色）。
               プレースホルダで位置の指定が無いものは、レイアウト→マスターの順に継承した値
  left_edge_count  トップレベルの text / picture / table 図形の左端の種類数（0.05 インチ刻み。図形が 2 つ未満なら null）
  distinct_colors  明示された RGB の色（文字色・図形の塗り・背景）の種類数。明示が無ければ 0
  min_contrast 文字色と背景色（図形の塗り、無ければ明示されたスライド背景）が両方 RGB で明示された組の最小コントラスト比。
               背景が明示されない／文字色が継承の run は判定できないので数えない。1 つも無ければ null
limitations には font と color の検査できた範囲（inherited / checked / theme-based）を必ず出す。
テーマ色（scheme color）は解決しない。解決しないことを `color theme-based: N slides` として記録する。
グループ内の図形は座標系が異なるため、shapes と left_edge_count には含めない。
"""
import argparse
import json
import os
import posixpath
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "_shared", "scripts"))
import slide_checks as sc  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8")

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}
A = "{%s}" % NS["a"]
P = "{%s}" % NS["p"]
R = "{%s}" % NS["r"]
REL_BASE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
EMU_PER_INCH = 914400
EDGE_STEP = 0.05
LEAF_TAGS = (P + "sp", P + "pic", P + "graphicFrame", P + "cxnSp")
TOP_TAGS = LEAF_TAGS + (P + "grpSp",)
# レイアウトのプレースホルダの、マスター側の対応種別（python-pptx と同じ表）
MASTER_TYPE = {"title": "title", "ctrTitle": "title", "dt": "dt", "ftr": "ftr", "sldNum": "sldNum"}


def plain(text):
    return re.sub(r"[\r\n\v\x0b]", "", text)


def number(v):
    return int(v) if float(v).is_integer() else v


def para_text(p):
    """段落のテキスト。a:r / a:fld は本文、a:br は垂直タブ（python-pptx と同じ）。"""
    out = []
    for el in p:
        if el.tag in (A + "r", A + "fld"):
            t = el.find(A + "t")
            out.append(t.text if t is not None and t.text else "")
        elif el.tag == A + "br":
            out.append("\v")
    return "".join(out)


def frame_text(txbody):
    return "\n".join(para_text(p) for p in txbody.findall(A + "p")) if txbody is not None else ""


def shape_id(el):
    for path in ("p:nvSpPr/p:cNvPr", "p:nvPicPr/p:cNvPr", "p:nvGrpSpPr/p:cNvPr",
                 "p:nvGraphicFramePr/p:cNvPr", "p:nvCxnSpPr/p:cNvPr"):
        c = el.find(path, NS)
        if c is not None:
            return c.get("id")
    return None


def ph_of(el):
    for path in ("p:nvSpPr/p:nvPr/p:ph", "p:nvPicPr/p:nvPr/p:ph", "p:nvGraphicFramePr/p:nvPr/p:ph"):
        ph = el.find(path, NS)
        if ph is not None:
            return ph
    return None


def walk(parent):
    """グループを再帰して、葉のシェイプ要素を順に返す。"""
    for el in parent:
        if el.tag == P + "grpSp":
            yield from walk(el)
        elif el.tag in LEAF_TAGS:
            yield el


def find_title(sptree):
    """python-pptx の shapes.title と同じ: 最上位の、idx が 0（省略時 0）のプレースホルダ。"""
    for el in sptree:
        if el.tag in TOP_TAGS:
            ph = ph_of(el)
            if ph is not None and int(ph.get("idx", "0")) == 0:
                return el
    return None


# ---- 色 ----------------------------------------------------------------
def color_of(parent):
    """solidFill を持つ要素 → ('rgb', '#RRGGBB') / ('theme', None) / None。"""
    fill = parent.find(A + "solidFill") if parent is not None else None
    if fill is None:
        return None
    srgb = fill.find(A + "srgbClr")
    if srgb is not None and srgb.get("val"):
        return ("rgb", "#" + srgb.get("val").upper())
    if fill.find(A + "schemeClr") is not None:
        return ("theme", None)
    return None


def sppr_fill(el):
    """図形（sp）の塗りが solid なら color_of の結果。pic / graphicFrame / cxnSp は塗りを持たない扱い（None）。"""
    if el.tag != P + "sp":
        return None
    return color_of(el.find(P + "spPr"))


def run_info(txbody):
    """段落ごとの run から (サイズ pt, 文字色) の列を返す。"""
    out = []
    if txbody is None:
        return out
    for p in txbody.findall(A + "p"):
        for r in p.findall(A + "r"):
            rpr = r.find(A + "rPr")
            size = int(rpr.get("sz")) / 100.0 if rpr is not None and rpr.get("sz") else None
            out.append((size, color_of(rpr)))
    return out


# ---- 位置（プレースホルダは layout → master を継承） -----------------------
def own_geometry(el):
    """要素自身が持つ (left, top, width, height) の EMU。無い項目は None。"""
    if el.tag == P + "graphicFrame":
        xfrm = el.find("p:xfrm", NS)
    else:
        xfrm = el.find("p:spPr/a:xfrm", NS)
    if xfrm is None:
        return [None] * 4
    off, ext = xfrm.find(A + "off"), xfrm.find(A + "ext")
    vals = [off.get("x") if off is not None else None, off.get("y") if off is not None else None,
            ext.get("cx") if ext is not None else None, ext.get("cy") if ext is not None else None]
    return [int(v) if v is not None else None for v in vals]


class Package:
    def __init__(self, z):
        self.z = z
        self._trees, self._rels = {}, {}

    def tree(self, path):
        if path not in self._trees:
            self._trees[path] = ET.fromstring(self.z.read(path))
        return self._trees[path]

    def rels(self, part):
        if part not in self._rels:
            rp = posixpath.join(posixpath.dirname(part), "_rels", posixpath.basename(part) + ".rels")
            self._rels[part] = (ET.fromstring(self.z.read(rp)).findall("rel:Relationship", NS)
                                if rp in self.z.namelist() else [])
        return self._rels[part]

    def related(self, part, kind):
        for rel in self.rels(part):
            if rel.get("Type") == REL_BASE + kind:
                return posixpath.normpath(posixpath.join(posixpath.dirname(part), rel.get("Target")))
        return None


def layout_geometry(pkg, slide_path, ph):
    """スライドのプレースホルダの継承値: layout（idx 一致）→ master（種別一致）の順。"""
    result = [None] * 4
    layout = pkg.related(slide_path, "slideLayout")
    if layout is None:
        return result
    idx = int(ph.get("idx", "0"))
    layout_root = pkg.tree(layout)
    layout_ph = None
    for el in layout_root.find("p:cSld/p:spTree", NS):
        lph = ph_of(el) if el.tag in TOP_TAGS else None
        if lph is not None and int(lph.get("idx", "0")) == idx:
            layout_ph = el
            break
    if layout_ph is None:
        return result
    result = own_geometry(layout_ph)
    if None in result:
        master = pkg.related(layout, "slideMaster")
        ltype = ph_of(layout_ph).get("type", "obj")
        want = MASTER_TYPE.get(ltype, "body")
        if master is not None:
            for el in pkg.tree(master).find("p:cSld/p:spTree", NS):
                mph = ph_of(el) if el.tag in TOP_TAGS else None
                if mph is not None and MASTER_TYPE.get(mph.get("type", "obj"), "body") == want:
                    base = own_geometry(el)
                    result = [r if r is not None else b for r, b in zip(result, base)]
                    break
    return result


def effective_geometry(pkg, slide_path, el):
    geo = own_geometry(el)
    ph = ph_of(el)
    if ph is not None and None in geo:
        inh = layout_geometry(pkg, slide_path, ph)
        geo = [g if g is not None else i for g, i in zip(geo, inh)]
    return geo


def inches(emu):
    return None if emu is None else round(emu / EMU_PER_INCH, 2)


def kind_of(el):
    if el.tag == P + "pic" and ph_of(el) is None:
        return "picture"
    if el.tag == P + "graphicFrame" and el.find("a:graphic/a:graphicData/a:tbl", NS) is not None:
        return "table"
    if el.tag == P + "sp":
        return "text"
    return "other"


def slide_background(root):
    bg = root.find("p:cSld/p:bg", NS)
    if bg is None:
        return None
    return color_of(bg.find("p:bgPr", NS))


def notes_nonempty(pkg, slide_path):
    notes = pkg.related(slide_path, "notesSlide")
    if notes is None:
        return False
    for sp in pkg.tree(notes).iter(P + "sp"):
        ph = ph_of(sp)
        if ph is not None and ph.get("type") == "body":
            return bool(frame_text(sp.find(P + "txBody")).strip())
    return False


def slide_facts(no, pkg, slide_path):
    root = pkg.tree(slide_path)
    sptree = root.find("p:cSld/p:spTree", NS)
    title_el = find_title(sptree)
    title = ""
    if title_el is not None and title_el.tag == P + "sp":
        title = frame_text(title_el.find(P + "txBody")).strip()
    title_id = shape_id(title_el) if title_el is not None else None
    body_chars = bullets = images = 0
    sizes, paragraphs = [], []
    text_blocks = []  # 画面の位置順に並べた文面（表のセルを含む）。日本語点検などが読む
    colors, contrasts = set(), []
    theme_used = False
    has_text = False
    bg = slide_background(root)
    if bg and bg[0] == "rgb":
        colors.add(bg[1])
    theme_used = theme_used or bool(bg and bg[0] == "theme")

    def take_runs(txbody, background):
        nonlocal theme_used
        for size, fg in run_info(txbody):
            if size is not None:
                sizes.append(size)
            if fg is None:
                continue
            if fg[0] == "theme":
                theme_used = True
                continue
            colors.add(fg[1])
            if background and background[0] == "rgb":
                contrasts.append(sc.contrast_ratio(fg[1], background[1]))

    for el in walk(sptree):
        if title_id is not None and shape_id(el) == title_id:
            continue
        shape_fill = sppr_fill(el)
        if shape_fill and shape_fill[0] == "rgb":
            colors.add(shape_fill[1])
        theme_used = theme_used or bool(shape_fill and shape_fill[0] == "theme")
        background = shape_fill or bg
        if el.tag == P + "pic" and ph_of(el) is None:
            images += 1
        tbl = el.find("a:graphic/a:graphicData/a:tbl", NS) if el.tag == P + "graphicFrame" else None
        _g = effective_geometry(pkg, slide_path, el)
        blk_top = inches(_g[1]) if _g and _g[1] is not None else 0
        blk_left = inches(_g[0]) if _g and _g[0] is not None else 0
        if tbl is not None:
            rows = []
            for tr in tbl.findall(A + "tr"):
                rows.append([plain(frame_text(tc.find(A + "txBody"))).strip() for tc in tr.findall(A + "tc")])
            text_blocks.append({"kind": "table", "top": blk_top, "left": blk_left, "rows": rows})
            for tc in tbl.iter(A + "tc"):
                tb = tc.find(A + "txBody")
                text = plain(frame_text(tb))
                body_chars += len(text)
                has_text = has_text or bool(text.strip())
                cell_fill = color_of(tc.find(A + "tcPr"))
                if cell_fill and cell_fill[0] == "rgb":
                    colors.add(cell_fill[1])
                take_runs(tb, cell_fill or bg)
        elif el.tag == P + "sp":
            tb = el.find(P + "txBody")
            shape_paras = []
            for p in (tb.findall(A + "p") if tb is not None else []):
                text = plain(para_text(p))
                body_chars += len(text)
                if text.strip():
                    bullets += 1
                    has_text = True
                    paragraphs.append(text.strip())
                    shape_paras.append(text.strip())
            if shape_paras:
                text_blocks.append({"kind": "text", "top": blk_top, "left": blk_left, "paragraphs": shape_paras})
            take_runs(tb, background)

    shapes, edges = [], set()
    for el in sptree:
        if el.tag not in LEAF_TAGS:
            continue
        if title_id is not None and shape_id(el) == title_id:
            continue
        kind = kind_of(el)
        left, top, width, height = (inches(v) for v in effective_geometry(pkg, slide_path, el))
        f = sppr_fill(el)
        shapes.append({"kind": kind, "left": left, "top": top, "width": width, "height": height,
                       "fill": f[1] if f and f[0] == "rgb" else None})
        if kind in ("text", "picture", "table") and left is not None:
            edges.add(round(round(left / EDGE_STEP) * EDGE_STEP, 2))
    notes = notes_nonempty(pkg, slide_path)
    text_blocks.sort(key=lambda b: (round((b["top"] or 0) / 0.3), b["left"] or 0))
    return {"no": no, "title": title or None, "body_chars": body_chars, "bullet_count": bullets,
            "min_font_pt": number(min(sizes)) if sizes else None, "image_count": images,
            "has_notes": bool(notes), "paragraphs": paragraphs, "text_blocks": text_blocks, "shapes": shapes,
            "left_edge_count": len(edges) if sum(1 for s in shapes if s["kind"] in ("text", "picture", "table")) >= 2 else None,
            "distinct_colors": len(colors),
            "min_contrast": round(min(contrasts), 2) if contrasts else None}, has_text, theme_used


def slide_paths(z):
    pres = ET.fromstring(z.read("ppt/presentation.xml"))
    rels = ET.fromstring(z.read("ppt/_rels/presentation.xml.rels"))
    target = {r.get("Id"): r.get("Target") for r in rels.findall("rel:Relationship", NS)}
    paths = []
    for sld in pres.findall("p:sldIdLst/p:sldId", NS):
        t = target[sld.get(R + "id")]
        paths.append(t.lstrip("/") if t.startswith("/") else posixpath.normpath(posixpath.join("ppt", t)))
    return paths


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pptx")
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args(argv)
    try:
        z = zipfile.ZipFile(args.pptx)
        paths = slide_paths(z)
    except Exception as e:  # 存在しない・壊れた zip・pptx ではない、などをまとめて扱う
        print("ERROR: cannot open %s: %s" % (args.pptx, e), file=sys.stderr)
        return 2
    slides, inherited, theme_slides = [], 0, 0
    with z:
        pkg = Package(z)
        for i, sp in enumerate(paths, 1):
            facts, has_text, theme_used = slide_facts(i, pkg, sp)
            if has_text and facts["min_font_pt"] is None:
                inherited += 1
            theme_slides += 1 if theme_used else 0
            slides.append(facts)
    total = len(slides)
    font_checked = sum(1 for s in slides if s["min_font_pt"] is not None)
    color_checked = sum(1 for s in slides if s["min_contrast"] is not None)
    out = {"file": os.path.basename(args.pptx), "slide_count": total, "slides": slides,
           "limitations": ["font inherited: %d slides" % inherited,
                           "font checked: %d/%d slides" % (font_checked, total),
                           "color checked: %d/%d slides" % (color_checked, total),
                           "color theme-based: %d slides" % theme_slides]}
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
