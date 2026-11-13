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
  notes_text   ノートの本文（段落を改行で結合。無ければ ""）。点検員が「画面に無くノートにだけある前提」を判定する材料（2026-11）
  notes_chars  notes_text の空白を除いた文字数
  screen_chars 見出しと text_blocks 全体（表のセルを含む）の空白を除いた文字数
  layout_name  スライドレイアウトの名前（無ければ ""）
  paragraphs   タイトル以外の非空段落のテキスト（表のセルは含まない。reviewer が内容を判定するための事実情報）
  text_blocks  タイトル以外の文面を、画面の位置順（上から下、左から右）に並べたもの。図形ごとの段落と、表のセル（行ごと）を含む。日本語点検が読む
  shapes       タイトル以外のトップレベル図形の kind / left / top / width / height（インチ, 小数 2 桁）と fill（明示された塗り色）。
               プレースホルダで位置の指定が無いものは、レイアウト→マスターの順に継承した値
  left_edge_count  トップレベルの text / picture / table 図形の左端の種類数（0.05 インチ刻み。図形が 2 つ未満なら null）
  distinct_colors  明示された RGB の色（文字色・図形の塗り・背景）の種類数。明示が無ければ 0
  min_contrast 文字色と背景色（図形の塗り、無ければ明示されたスライド背景）が両方 RGB で明示された組の最小コントラスト比。
               背景が明示されない／文字色が継承の run は判定できないので数えない。1 つも無ければ null
2026-11 追加（トップ）:
  slide_width / slide_height  スライドの大きさ（インチ。presentation.xml の sldSz）
  sections     章の一覧 [{name, slides: [番号]}]（presentation.xml の拡張にある章。無ければ空）
2026-11 追加（スライド毎）:
  empty_placeholder_count  文字も画像も無いプレースホルダーの数（日付・フッター・ページ番号・ヘッダーとタイトルは数えない）
  partial_overlap_count / overlap_pairs  部分的に重なる図形の対の数と一覧。対象は文字を持つ図形（非空の段落がある p:sp）・表・画像と、
               本文の図形に対するタイトル。重なりが小さい方の面積の 5% 超 95% 未満、かつ 0.05 平方インチ超の対だけ数える
               （95% 以上の包含は意図的な重ねとして除く）。線・コネクタ・文字の無い図形・グループ内は数えない
  hyperlinks   外部リンクの行き先（スライドの rels）
  citation_markers  {markers: 出典番号らしい表記（[1]〜[99]・[^1]・※1・注1）, url_text_count, source_label_count, has_locator}。
               コードらしい段落（= { ; を含む）の番号は数えない。has_locator は URL の文字列・リンク・「出典」「参考」「Source」で始まる行のどれかがあるか
  table_estimates  表ごとの {top, left, width, frame_height, estimated_height, font_assumed}。推定の高さは、行ごとに
               セルの段落の文字幅（全角 1.0・半角 0.55 字幅 × 文字サイズ）を列幅（左右の余白を除く）で割った行数 × 1.2 行送り
               ＋上下の余白、と枠の行の高さの大きい方の合計。文字サイズが取れない段落は 18pt と仮定し font_assumed を true にする
limitations には font と color の検査できた範囲（inherited / checked / theme-based）を必ず出す。
テーマ色（scheme color）は解決しない。解決しないことを `color theme-based: N slides` として記録する。
グループ内の図形は座標系が異なるため、shapes と left_edge_count には含めない。
"""
import argparse
import json
import math
import os
import posixpath
import re
import sys
import unicodedata
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
    "p14": "http://schemas.microsoft.com/office/powerpoint/2010/main",
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
# 空の枠として数えないプレースホルダーの種類（日付・フッター・ページ番号・ヘッダー・タイトル）
NOT_COUNTED_PH = ("dt", "ftr", "sldNum", "hdr", "title", "ctrTitle")
OVERLAP_MIN_RATIO, OVERLAP_MAX_RATIO, OVERLAP_MIN_AREA = 0.05, 0.95, 0.05  # 運用上の値（threshold_origin: adaptation）
CITATION = re.compile(r"\[\^?([1-9]\d?)\]|※\s?([1-9]\d?)|注\s?([1-9]\d?)")
CODE_LIKE = re.compile(r"[={;]")
URL_TEXT = re.compile(r"https?://\S+|www\.\S+", re.I)
SOURCE_LABEL = re.compile(r"^\s*(出典|参考|source)", re.I)
DEFAULT_TABLE_PT = 18
CELL_MAR_LR, CELL_MAR_TB = 91440, 45720  # 表のセルの既定の余白（EMU）


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


def notes_text_of(pkg, slide_path):
    """ノートの本文（本文プレースホルダーの段落を改行で結合し、前後の空白を除く）。無ければ ""。"""
    notes = pkg.related(slide_path, "notesSlide")
    if notes is None:
        return ""
    for sp in pkg.tree(notes).iter(P + "sp"):
        ph = ph_of(sp)
        if ph is not None and ph.get("type") == "body":
            return frame_text(sp.find(P + "txBody")).replace("\v", "\n").strip()
    return ""


def layout_name_of(pkg, slide_path):
    layout = pkg.related(slide_path, "slideLayout")
    if layout is None:
        return ""
    csld = pkg.tree(layout).find("p:cSld", NS)
    return (csld.get("name") or "") if csld is not None else ""


def visible_chars(text):
    return len(re.sub(r"\s", "", text or ""))


def has_text_sp(el):
    tb = el.find(P + "txBody")
    return tb is not None and any(plain(para_text(p)).strip() for p in tb.findall(A + "p"))


def empty_placeholders(sptree, title_id):
    n = 0
    for el in walk(sptree):
        if el.tag != P + "sp":
            continue
        ph = ph_of(el)
        if ph is None or ph.get("type") in NOT_COUNTED_PH or (title_id is not None and shape_id(el) == title_id):
            continue
        if has_text_sp(el) or el.find("p:spPr/a:blipFill", NS) is not None:
            continue
        n += 1
    return n


def overlap_items(pkg, slide_path, sptree, title_el):
    """重なりの判定の対象（トップレベルの、文字を持つ図形・表・画像）。タイトルは別に返す。"""
    items, title = [], None
    for el in sptree:
        if el.tag not in LEAF_TAGS or el.tag == P + "cxnSp":
            continue
        if el.tag == P + "sp":
            if not has_text_sp(el):
                continue
            kind = "text"
            label = plain(frame_text(el.find(P + "txBody"))).strip()[:20]
        elif el.tag == P + "pic":
            kind, label = "picture", "picture"
        elif el.find("a:graphic/a:graphicData/a:tbl", NS) is not None:
            kind, label = "table", "table"
        else:
            continue
        geo = effective_geometry(pkg, slide_path, el)
        if None in geo or geo[2] <= 0 or geo[3] <= 0:
            continue
        item = {"kind": kind, "label": label, "geo": [g / EMU_PER_INCH for g in geo]}
        if title_el is not None and el is title_el:
            title = dict(item, kind="title")
        else:
            items.append(item)
    return items, title


def overlap_of(a, b):
    ax, ay, aw, ah = a["geo"]
    bx, by, bw, bh = b["geo"]
    w = min(ax + aw, bx + bw) - max(ax, bx)
    h = min(ay + ah, by + bh) - max(ay, by)
    if w <= 0 or h <= 0:
        return 0.0, 0.0
    area = w * h
    return area, area / min(aw * ah, bw * bh)


def partial_overlaps(items, title):
    pairs = []
    cands = [(a, b) for i, a in enumerate(items) for b in items[i + 1:]]
    if title is not None:
        cands += [(title, b) for b in items]
    for a, b in cands:
        area, ratio = overlap_of(a, b)
        if area > OVERLAP_MIN_AREA and OVERLAP_MIN_RATIO < ratio < OVERLAP_MAX_RATIO:
            pairs.append({"a": "%s: %s" % (a["kind"], a["label"]), "b": "%s: %s" % (b["kind"], b["label"]),
                          "overlap_in2": round(area, 2), "ratio": round(ratio, 2)})
    return pairs


def hyperlinks_of(pkg, slide_path):
    out = []
    for rel in pkg.rels(slide_path):
        if rel.get("Type") == REL_BASE + "hyperlink" and rel.get("TargetMode") == "External":
            out.append(rel.get("Target"))
    return out


def citation_facts(lines, hyperlinks):
    markers, urls, labels = [], 0, 0
    for line in lines:
        urls += len(URL_TEXT.findall(line))
        if SOURCE_LABEL.match(line):
            labels += 1
        if CODE_LIKE.search(line):
            continue
        for m in CITATION.finditer(line):
            if m.group(0) not in markers:
                markers.append(m.group(0))
    return {"markers": markers, "url_text_count": urls, "source_label_count": labels,
            "has_locator": bool(urls or labels or hyperlinks)}


def char_em(ch):
    return 1.0 if unicodedata.east_asian_width(ch) in ("W", "F") else 0.55


def table_estimate(tbl, geo):
    cols = [int(c.get("w", "0")) for c in tbl.findall("a:tblGrid/a:gridCol", NS)]
    assumed = False
    total = 0
    for tr in tbl.findall(A + "tr"):
        row_h = int(tr.get("h", "0"))
        ci = 0
        for tc in tr.findall(A + "tc"):
            span = int(tc.get("gridSpan", "1"))
            if tc.get("hMerge") or tc.get("vMerge"):
                ci += span
                continue
            width = sum(cols[ci:ci + span]) if cols else geo[2]
            ci += span
            pr = tc.find(A + "tcPr")
            mar_l = int(pr.get("marL", CELL_MAR_LR)) if pr is not None else CELL_MAR_LR
            mar_r = int(pr.get("marR", CELL_MAR_LR)) if pr is not None else CELL_MAR_LR
            mar_t = int(pr.get("marT", CELL_MAR_TB)) if pr is not None else CELL_MAR_TB
            mar_b = int(pr.get("marB", CELL_MAR_TB)) if pr is not None else CELL_MAR_TB
            avail_pt = max(1.0, (width - mar_l - mar_r) / EMU_PER_INCH * 72)
            height_pt = 0.0
            tb = tc.find(A + "txBody")
            for p in (tb.findall(A + "p") if tb is not None else []):
                sizes = [int(r.find(A + "rPr").get("sz")) / 100.0 for r in p.findall(A + "r")
                         if r.find(A + "rPr") is not None and r.find(A + "rPr").get("sz")]
                end = p.find(A + "endParaRPr")
                if not sizes and end is not None and end.get("sz"):
                    sizes = [int(end.get("sz")) / 100.0]
                if not sizes:
                    assumed = True
                size = max(sizes) if sizes else DEFAULT_TABLE_PT
                text = plain(para_text(p))
                lines = max(1, math.ceil(sum(char_em(c) for c in text) * size / avail_pt))
                height_pt += lines * size * 1.2
            cell_h = height_pt / 72 * EMU_PER_INCH + mar_t + mar_b
            row_h = max(row_h, cell_h)
        total += row_h
    return {"top": inches(geo[1]), "left": inches(geo[0]), "width": inches(geo[2]), "frame_height": inches(geo[3]),
            "estimated_height": inches(int(total)), "font_assumed": assumed}


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
    notes = notes_text_of(pkg, slide_path)
    text_blocks.sort(key=lambda b: (round((b["top"] or 0) / 0.3), b["left"] or 0))
    items, title_item = overlap_items(pkg, slide_path, sptree, title_el)
    pairs = partial_overlaps(items, title_item)
    links = hyperlinks_of(pkg, slide_path)
    lines = ([title] if title else []) + [x for b in text_blocks for x in
                                          (b.get("paragraphs") or [c for row in b.get("rows", []) for c in row])]
    tables = []
    for el in sptree:
        if el.tag == P + "graphicFrame":
            tbl = el.find("a:graphic/a:graphicData/a:tbl", NS)
            geo = effective_geometry(pkg, slide_path, el)
            if tbl is not None and None not in geo:
                tables.append(table_estimate(tbl, geo))
    return {"no": no, "title": title or None, "body_chars": body_chars, "bullet_count": bullets,
            "min_font_pt": number(min(sizes)) if sizes else None, "image_count": images,
            "has_notes": bool(notes), "notes_text": notes, "notes_chars": visible_chars(notes),
            "screen_chars": sum(visible_chars(x) for x in lines), "layout_name": layout_name_of(pkg, slide_path),
            "paragraphs": paragraphs, "text_blocks": text_blocks, "shapes": shapes,
            "left_edge_count": len(edges) if sum(1 for s in shapes if s["kind"] in ("text", "picture", "table")) >= 2 else None,
            "distinct_colors": len(colors),
            "min_contrast": round(min(contrasts), 2) if contrasts else None,
            "empty_placeholder_count": empty_placeholders(sptree, title_id),
            "partial_overlap_count": len(pairs), "overlap_pairs": pairs,
            "hyperlinks": links, "citation_markers": citation_facts(lines, links),
            "table_estimates": tables,
            "has_group": any(el.tag == P + "grpSp" for el in sptree)}, has_text, theme_used


def slide_paths(z):
    pres = ET.fromstring(z.read("ppt/presentation.xml"))
    rels = ET.fromstring(z.read("ppt/_rels/presentation.xml.rels"))
    target = {r.get("Id"): r.get("Target") for r in rels.findall("rel:Relationship", NS)}
    paths = []
    for sld in pres.findall("p:sldIdLst/p:sldId", NS):
        t = target[sld.get(R + "id")]
        paths.append(t.lstrip("/") if t.startswith("/") else posixpath.normpath(posixpath.join("ppt", t)))
    return paths


def deck_layout(z):
    """スライドの大きさ（インチ）と章の一覧。"""
    pres = ET.fromstring(z.read("ppt/presentation.xml"))
    size = pres.find("p:sldSz", NS)
    width = inches(int(size.get("cx"))) if size is not None else None
    height = inches(int(size.get("cy"))) if size is not None else None
    order = {sld.get("id"): i for i, sld in enumerate(pres.findall("p:sldIdLst/p:sldId", NS), 1)}
    sections = []
    for sec in pres.iter("{%s}section" % NS["p14"]):
        nos = [order[x.get("id")] for x in sec.iter("{%s}sldId" % NS["p14"]) if x.get("id") in order]
        sections.append({"name": sec.get("name"), "slides": nos})
    return width, height, sections


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
        width, height, sections = deck_layout(z)
    total = len(slides)
    font_checked = sum(1 for s in slides if s["min_font_pt"] is not None)
    color_checked = sum(1 for s in slides if s["min_contrast"] is not None)
    out = {"file": os.path.basename(args.pptx), "slide_count": total, "slide_width": width, "slide_height": height,
           "sections": sections, "slides": slides,
           "limitations": ["font inherited: %d slides" % inherited,
                           "font checked: %d/%d slides" % (font_checked, total),
                           "color checked: %d/%d slides" % (color_checked, total),
                           "color theme-based: %d slides" % theme_slides,
                           "group shapes not checked for overlap: %d slides" % sum(1 for s in slides if s.pop("has_group"))]}
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
