#!/usr/bin/env python3
"""extract_deck.py — .pptx から事実情報（deck-facts.json）を抽出する。

使い方: python extract_deck.py <deck.pptx> -o <deck-facts.json>
依存: python-pptx。

抽出の定義（スライド毎）:
  title        タイトルプレースホルダの文字列（strip 後。無い／空なら null）
  body_chars   タイトル以外の全テキスト（表のセル・グループ内を再帰的に含む。ノート・改行は数えない）
  bullet_count タイトル以外のテキストフレームで strip 後に非空の段落数（グループ内は再帰。表のセルは数えない）
  min_font_pt  明示指定された run のフォントサイズ(pt)の最小値。明示指定が無ければ null（継承値は取れない）
  image_count  画像（picture）シェイプ数（グループ内を再帰）
  has_notes    ノートに非空テキストがあるか
  paragraphs   タイトル以外の非空段落のテキスト（表のセルは含まない。reviewer が内容を判定するための事実情報）
  shapes       タイトル以外のトップレベル図形の kind / left / top / width / height（インチ, 小数 2 桁）と fill（明示された塗り色）
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
import re
import sys

from pptx import Presentation
from pptx.enum.dml import MSO_COLOR_TYPE, MSO_FILL
from pptx.enum.shapes import MSO_SHAPE_TYPE

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "_shared", "scripts"))
import slide_checks as sc  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8")

EMU_PER_INCH = 914400
EDGE_STEP = 0.05


def walk(shapes):
    for sh in shapes:
        if sh.shape_type == MSO_SHAPE_TYPE.GROUP:
            yield from walk(sh.shapes)
        else:
            yield sh


def plain(text):
    return re.sub(r"[\r\n\v\x0b]", "", text)


def number(v):
    return int(v) if float(v).is_integer() else v


def color_of(color_format):
    """ColorFormat → ('rgb', '#RRGGBB') / ('theme', None) / None。"""
    try:
        kind = color_format.type
        if kind == MSO_COLOR_TYPE.RGB:
            return ("rgb", "#" + str(color_format.rgb).upper())
        if kind == MSO_COLOR_TYPE.SCHEME:
            return ("theme", None)
    except (AttributeError, KeyError, TypeError):
        pass
    return None


def fill_of(obj):
    """図形・セル・背景の塗りが solid なら color_of の結果、そうでなければ None。"""
    try:
        fill = obj.fill
        if fill.type == MSO_FILL.SOLID:
            return color_of(fill.fore_color)
    except (AttributeError, KeyError, TypeError, NotImplementedError):
        pass
    return None


def inches(emu):
    return None if emu is None else round(emu / EMU_PER_INCH, 2)


def kind_of(sh):
    if sh.shape_type == MSO_SHAPE_TYPE.PICTURE:
        return "picture"
    if getattr(sh, "has_table", False) and sh.has_table:
        return "table"
    if getattr(sh, "has_text_frame", False) and sh.has_text_frame:
        return "text"
    return "other"


def slide_background(slide):
    if slide.follow_master_background:
        return None
    return fill_of(slide.background)


def slide_facts(no, slide):
    title_shape = slide.shapes.title
    title = title_shape.text_frame.text.strip() if title_shape is not None else ""
    body_chars = bullets = images = 0
    sizes, paragraphs = [], []
    colors, contrasts = set(), []
    theme_used = False
    has_text = False
    bg = slide_background(slide)
    if bg and bg[0] == "rgb":
        colors.add(bg[1])
    theme_used = theme_used or bool(bg and bg[0] == "theme")

    def take_runs(paragraph_list, background):
        nonlocal theme_used
        for p in paragraph_list:
            for r in p.runs:
                if r.font.size is not None:
                    sizes.append(r.font.size.pt)
                fg = color_of(r.font.color)
                if fg is None:
                    continue
                if fg[0] == "theme":
                    theme_used = True
                    continue
                colors.add(fg[1])
                if background and background[0] == "rgb":
                    contrasts.append(sc.contrast_ratio(fg[1], background[1]))

    for sh in walk(slide.shapes):
        if title_shape is not None and sh.shape_id == title_shape.shape_id:
            continue
        shape_fill = fill_of(sh)
        if shape_fill and shape_fill[0] == "rgb":
            colors.add(shape_fill[1])
        theme_used = theme_used or bool(shape_fill and shape_fill[0] == "theme")
        background = shape_fill or bg
        if sh.shape_type == MSO_SHAPE_TYPE.PICTURE:
            images += 1
        if getattr(sh, "has_table", False) and sh.has_table:
            for row in sh.table.rows:
                for cell in row.cells:
                    text = plain(cell.text_frame.text)
                    body_chars += len(text)
                    has_text = has_text or bool(text.strip())
                    cell_fill = fill_of(cell)
                    if cell_fill and cell_fill[0] == "rgb":
                        colors.add(cell_fill[1])
                    take_runs(cell.text_frame.paragraphs, cell_fill or bg)
        elif getattr(sh, "has_text_frame", False) and sh.has_text_frame:
            for p in sh.text_frame.paragraphs:
                text = plain(p.text)
                body_chars += len(text)
                if text.strip():
                    bullets += 1
                    has_text = True
                    paragraphs.append(text.strip())
            take_runs(sh.text_frame.paragraphs, background)

    shapes, edges = [], set()
    for sh in slide.shapes:
        if title_shape is not None and sh.shape_id == title_shape.shape_id:
            continue
        if sh.shape_type == MSO_SHAPE_TYPE.GROUP:
            continue
        kind = kind_of(sh)
        left = inches(sh.left)
        f = fill_of(sh)
        shapes.append({"kind": kind, "left": left, "top": inches(sh.top), "width": inches(sh.width),
                       "height": inches(sh.height), "fill": f[1] if f and f[0] == "rgb" else None})
        if kind in ("text", "picture", "table") and left is not None:
            edges.add(round(round(left / EDGE_STEP) * EDGE_STEP, 2))
    notes = slide.has_notes_slide and bool(slide.notes_slide.notes_text_frame.text.strip())
    return {"no": no, "title": title or None, "body_chars": body_chars, "bullet_count": bullets,
            "min_font_pt": number(min(sizes)) if sizes else None, "image_count": images,
            "has_notes": bool(notes), "paragraphs": paragraphs, "shapes": shapes,
            "left_edge_count": len(edges) if sum(1 for s in shapes if s["kind"] in ("text", "picture", "table")) >= 2 else None,
            "distinct_colors": len(colors),
            "min_contrast": round(min(contrasts), 2) if contrasts else None}, has_text, theme_used


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pptx")
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args(argv)
    try:
        prs = Presentation(args.pptx)
    except Exception as e:  # python-pptx は形式不正で多様な例外を出す
        print("ERROR: cannot open %s: %s" % (args.pptx, e), file=sys.stderr)
        return 2
    slides, inherited, theme_slides = [], 0, 0
    for i, slide in enumerate(prs.slides, 1):
        facts, has_text, theme_used = slide_facts(i, slide)
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
