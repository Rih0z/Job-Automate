#!/usr/bin/env python3
"""make_square_cards.py — SNS 投稿用の正方形カード 4 枚を、設定 JSON から検査し、1080x1080 の JPEG にする。

使い方（リポジトリのルートから）:
  python3 .claude/skills/sns-square-slides/scripts/make_square_cards.py --config <cards.json> --check
  python3 .claude/skills/sns-square-slides/scripts/make_square_cards.py --preflight [--config <cards.json>]
  python3 .claude/skills/sns-square-slides/scripts/make_square_cards.py --config <cards.json> --out-dir <出力先> [--name cards]
出力: <出力先>/<name>-1.jpg 〜 -4.jpg（1080x1080）と <name>.pptx。失敗した時は出力先に何も足さず、何も消さない（この実行で作った出力先は、空のまま失敗したら消す）。
  例外は最後の 5 つの移動（os.replace）の途中の OS のエラーだけで、移し終えたファイルの名前を出して exit 4 にする。

数値と点検表の正本は ../criteria/card-rules.json（--rules で差し替えられる）。
終了コード: 0 合格 / 1 検査の違反 / 2 入力の誤り / 3 道具が無い / 4 描画の失敗 / 5 内部の誤り（想定外の例外）。
道具: python-pptx、LibreOffice（soffice）、poppler（pdftoppm）。soffice と pdftoppm の探し方は
  ../../slide-clarity-review/scripts/render_deck.py の find_soffice / find_pdftoppm を使う（環境変数 SOFFICE / PDFTOPPM → PATH → 持ち運び版 → Windows の既定の場所）。
環境変数: SOFFICE・PDFTOPPM・FC_LIST（道具の場所）、SNS_CARDS_PROFILE（LibreOffice の利用者プロファイル。既定は
  $XDG_CACHE_HOME か ~/.cache の下の sns-square-cards/lo_profile）、SNS_CARDS_SOFFICE_TIMEOUT（既定 600 秒）・SNS_CARDS_PDFTOPPM_TIMEOUT（既定 60 秒）、
  SNS_CARDS_RENDER_DECK（試験用の継ぎ目。通常は設定しない）。
"""
import argparse
import glob
import importlib.util
import json
import math
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import traceback
import unicodedata

for _s in (sys.stdout, sys.stderr):  # Windows の既定の文字コードで日本語の出力が落ちないようにする
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_RULES = os.path.join(HERE, "..", "criteria", "card-rules.json")
DEFAULT_RENDER_DECK = os.path.join(HERE, "..", "..", "slide-clarity-review", "scripts", "render_deck.py")
RULES_SCHEMA = "sns-square-cards-rules/v3"
LIMIT_KEYS = ("title_max", "title_recommended", "title_max_lines", "body_max", "body_recommended", "body_max_lines",
              "note_max", "label_max")
FONT_PT_KEYS = ("label", "title", "title_small", "body", "body_small", "note", "page_number")
LAYOUT_KEYS = ("label", "title", "body", "note", "page_number")
POST_MODES = ("x", "chars")
ROLE_SLOTS = ("dark_bg", "light_bg", "text_on_dark", "text_on_light", "label_on_dark", "label_on_light",
              "note_on_light", "note_on_dark")
IMAGE_PX = 1080
SLIDE_INCH = 10
TOP_KEYS = {"_note", "label", "font", "palette_ref", "palette", "page_numbers", "cards", "post"}
CARD_KEYS = {"role", "title", "body", "note"}
POST_KEYS = {"text", "supplement_source", "count"}
HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")
URL_TRAILING = ".,;:!?'\")]"
URL_RE = re.compile(r"https?://[!-~]+")  # ASCII の印字可能な文字だけ。日本語で URL は終わる（X も同じ）
BARE_DOMAIN_RE = re.compile(r"(?<![A-Za-z0-9/.@-])[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.(?:com|net|org|jp|io|co|dev|app|info|me)(?![A-Za-z0-9-])")


class InputError(Exception):
    """引数・設定・palette_ref・criteria の誤り（exit 2）。"""


class DependencyError(Exception):
    """道具が無い（exit 3）。"""


class RenderError(Exception):
    """描画の失敗・時間切れ・JPEG の枚数か大きさの違い（exit 4）。"""


# ---------------------------------------------------------------- 読込
def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        raise InputError("%s を読めない: %s" % (path, e))


def _is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def _is_num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def rules_problems(rules):
    """criteria の形と型の誤りを返す（空なら妥当）。生成や検査の途中で KeyError や TypeError にしないため。"""
    p = []
    if not isinstance(rules, dict):
        return ["最上位が object ではない"]

    def need(cond, msg):
        if not cond:
            p.append(msg)

    need(rules.get("schema") == RULES_SCHEMA, "schema が %s ではない" % RULES_SCHEMA)
    need(_is_int(rules.get("card_count")) and rules.get("card_count", 0) > 0, "card_count は正の整数")
    layout = rules.get("cards_layout")
    need(isinstance(layout, list) and _is_int(rules.get("card_count")) and len(layout) == rules["card_count"]
         and all(isinstance(c, dict) and isinstance(c.get("role"), str) and c.get("bg") in ("dark", "light") for c in layout),
         "cards_layout は card_count 個の {role: 文字列, bg: dark か light}")
    lim = rules.get("limits")
    need(isinstance(lim, dict) and all(_is_int(lim.get(k)) for k in LIMIT_KEYS), "limits に整数の %s" % ", ".join(LIMIT_KEYS))
    pc = rules.get("post_count")
    ok_pc = isinstance(pc, dict) and isinstance(pc.get("default"), str) and pc.get("default") in pc
    x = pc.get("x") if isinstance(pc, dict) else None
    ok_pc = ok_pc and isinstance(x, dict) and all(_is_int(x.get(k)) for k in ("max", "scale", "default_weight", "url_length")) \
        and x.get("scale", 0) > 0 and isinstance(x.get("ranges"), list) \
        and all(isinstance(r, list) and len(r) == 3 and all(_is_int(v) for v in r) for r in x["ranges"])
    ch = pc.get("chars") if isinstance(pc, dict) else None
    ok_pc = ok_pc and isinstance(ch, dict) and _is_int(ch.get("max"))
    need(ok_pc, "post_count は default と x（max・scale・default_weight・url_length・ranges）と chars（max）")
    need(_is_int(rules.get("copy_min_chars")), "copy_min_chars は整数")
    need(_is_num(rules.get("min_contrast")), "min_contrast は数")
    fp = rules.get("font_pt")
    need(isinstance(fp, dict) and all(_is_num(fp.get(k)) for k in FONT_PT_KEYS), "font_pt に数の %s" % ", ".join(FONT_PT_KEYS))
    lay = rules.get("layout_in")
    need(isinstance(lay, dict) and all(isinstance(lay.get(k), list) and len(lay[k]) == 4 and all(_is_num(v) for v in lay[k])
                                       for k in LAYOUT_KEYS), "layout_in に 4 つの数の %s" % ", ".join(LAYOUT_KEYS))
    need(_is_num(rules.get("line_spacing")), "line_spacing は数")
    pnf = rules.get("page_number_format")
    try:
        pnf_ok = isinstance(pnf, str) and "{n}" in pnf and bool(pnf.format(n=1, total=1))
    except (KeyError, ValueError, IndexError):
        pnf_ok = False
    need(pnf_ok, "page_number_format は {n}（と任意の {total}）だけを置換欄に持つ文字列")
    df = rules.get("default_font")
    need(isinstance(df, dict) and isinstance(df.get("darwin"), str) and isinstance(df.get("other"), str),
         "default_font に文字列の darwin と other")
    pru = rules.get("palette_roles_used")
    need(isinstance(pru, dict) and all(isinstance(pru.get(k), str) for k in ROLE_SLOTS),
         "palette_roles_used に %s" % ", ".join(ROLE_SLOTS))
    dp = rules.get("default_palette")
    need(isinstance(dp, dict) and isinstance(dp.get("roles"), dict), "default_palette.roles は object")
    return p


def load_rules(path):
    rules = load_json(path)
    problems = rules_problems(rules)
    if problems:
        raise InputError("%s の形が違う: %s" % (path, " / ".join(problems)))
    return rules


def load_palette_ref(config, config_dir):
    """palette_ref の roles を読む。palette_ref が無い（文字列でない時も）なら None。"""
    ref = config.get("palette_ref") if isinstance(config, dict) else None
    if not isinstance(ref, str):
        return None
    path = ref if os.path.isabs(ref) else os.path.join(config_dir, ref)
    data = load_json(path)
    if not isinstance(data, dict) or not isinstance(data.get("roles"), dict):
        raise InputError("%s に roles（object）が無い" % path)
    return data["roles"]


# ---------------------------------------------------------------- 数え方と明暗差
def _lf(s):
    return s.replace("\r\n", "\n").replace("\r", "\n")


def text_length(s):
    """改行を除き、NFC に正規化した code point の数。"""
    return len(_lf(unicodedata.normalize("NFC", s)).replace("\n", ""))


def line_count(s):
    """行数 = 改行の数 + 1（CRLF は 1 つ。末尾の改行も数える）。"""
    return _lf(s).count("\n") + 1


def post_length(text, mode, rules):
    text = unicodedata.normalize("NFC", text)
    spec = rules["post_count"][mode]
    if mode == "chars":
        return len(text)
    scale = spec["scale"]
    weight = 0
    rest = []
    pos = 0
    for m in URL_RE.finditer(text):
        url = m.group(0)
        stripped = url.rstrip(URL_TRAILING)  # 末尾の句読点は URL に含めず文字として数える（X と同じ）
        rest.append(text[pos:m.start()])
        rest.append(url[len(stripped):])
        weight += spec["url_length"] * scale
        pos = m.end()
    rest.append(text[pos:])
    for ch in "".join(rest):
        cp = ord(ch)
        w = spec["default_weight"]
        for start, end, rw in spec["ranges"]:
            if start <= cp <= end:
                w = rw
                break
        weight += w
    return math.ceil(weight / scale)


def _luminance(hex_color):
    channels = []
    for i in (1, 3, 5):
        c = int(hex_color[i:i + 2], 16) / 255.0
        channels.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast_ratio(a, b):
    la, lb = _luminance(a), _luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _norm_for_copy(s):
    return re.sub(r"\s", "", unicodedata.normalize("NFC", s))


# ---------------------------------------------------------------- 検査
def used_roles(rules):
    return sorted(set(rules["palette_roles_used"].values()))


def resolve_palette(config, ref_roles, rules):
    """palette_ref（読込済み）か既定を土台にし、設定の palette を重ねる。使う役割の欠け・形の誤りは C5。"""
    base = dict(ref_roles) if ref_roles is not None else dict(rules["default_palette"]["roles"])
    over = config.get("palette") if isinstance(config, dict) else None
    if isinstance(over, dict):
        for k, val in over.items():
            if isinstance(val, str):
                base[k] = val
    violations = []
    for role in used_roles(rules):
        if role not in base:
            violations.append("C5 palette: 役割 %s が無い" % role)
        elif not isinstance(base[role], str) or not HEX_COLOR.match(base[role]):
            violations.append("C5 palette: 役割 %s の値 %r が #RRGGBB ではない" % (role, base[role]))
    return base, violations


def _contrast_pairs(rules):
    u = rules["palette_roles_used"]
    pairs = []
    for bg, names in (("dark_bg", ("text_on_dark", "label_on_dark", "note_on_dark")),
                      ("light_bg", ("text_on_light", "label_on_light", "note_on_light"))):
        for n in names:
            pairs.append((bg, u[bg], n, u[n]))
    return pairs


def check_config(config, rules, ref_roles):
    """C1〜C7 の違反と警告を返す（I/O なし）。"""
    v, w = [], []
    if not isinstance(config, dict):
        return ["C7 設定の最上位が object ではない"], w
    lim = rules["limits"]

    for k in sorted(set(config) - TOP_KEYS):
        v.append("C7 設定: 許されないキー %r" % k)
    for k in ("label", "font", "palette_ref"):
        if k in config and not isinstance(config[k], str):
            v.append("C7 設定: %s は文字列にする" % k)
    if "page_numbers" in config and not isinstance(config["page_numbers"], bool):
        v.append("C7 設定: page_numbers は真偽値にする")
    palette_ok = True
    if "palette" in config:
        pal = config["palette"]
        if not isinstance(pal, dict):
            v.append("C7 設定: palette は object にする")
            palette_ok = False
        else:
            for k in sorted(pal):
                if k not in used_roles(rules):
                    v.append("C7 palette: 使わない役割 %r（使うのは %s）" % (k, ", ".join(used_roles(rules))))
                elif not isinstance(pal[k], str):
                    v.append("C7 palette: %s の値は文字列にする" % k)
    if isinstance(config.get("label"), str) and text_length(config["label"]) > lim["label_max"]:
        v.append("C3 label: 上限 %d 字を超える (%d 字)" % (lim["label_max"], text_length(config["label"])))

    # カード
    cards = config.get("cards")
    layout = rules["cards_layout"]
    if not isinstance(cards, list):
        v.append("C1 cards: 配列ではない")
        cards = []
    elif len(cards) != rules["card_count"]:
        v.append("C1 cards: %d 枚ではない (%d 枚)" % (rules["card_count"], len(cards)))
    count_ok = isinstance(config.get("cards"), list) and len(cards) == rules["card_count"]
    for i, card in enumerate(cards, 1):
        where = "card %d" % i
        if not isinstance(card, dict):
            v.append("C7 %s: object ではない" % where)
            continue
        for k in sorted(set(card) - CARD_KEYS):
            v.append("C7 %s: 許されないキー %r" % (where, k))
        if count_ok:
            want = layout[i - 1]["role"]
            if card.get("role") != want:
                v.append("C2 %s: role が %s ではない (%r)" % (where, want, card.get("role")))
        for field in ("title", "body", "note"):
            if field in card and not isinstance(card[field], str):
                v.append("C7 %s: %s は文字列にする" % (where, field))
        title = card.get("title", "")
        if isinstance(title, str):
            n = text_length(title)
            if n == 0:
                v.append("C3 %s: title が空" % where)
            elif n > lim["title_max"]:
                v.append("C3 %s: title が上限 %d 字を超える (%d 字)" % (where, lim["title_max"], n))
            elif n > lim["title_recommended"]:
                w.append("%s: title が目安 %d 字を超える (%d 字)" % (where, lim["title_recommended"], n))
            if n and line_count(title) > lim["title_max_lines"]:
                v.append("C3 %s: title の行数が上限 %d を超える (%d 行)" % (where, lim["title_max_lines"], line_count(title)))
        body = card.get("body", "")
        if isinstance(body, str):
            n = text_length(body)
            if n > lim["body_max"]:
                v.append("C3 %s: body が上限 %d 字を超える (%d 字)" % (where, lim["body_max"], n))
            elif n > lim["body_recommended"]:
                w.append("%s: body が目安 %d 字を超える (%d 字)" % (where, lim["body_recommended"], n))
            if n and line_count(body) > lim["body_max_lines"]:
                v.append("C3 %s: body の行数が上限 %d を超える (%d 行)" % (where, lim["body_max_lines"], line_count(body)))
        note = card.get("note", "")
        if isinstance(note, str) and text_length(note) > lim["note_max"]:
            v.append("C3 %s: note が上限 %d 字を超える (%d 字)" % (where, lim["note_max"], text_length(note)))

    # 配色と明暗差
    if palette_ok:
        roles, pv = resolve_palette(config, ref_roles, rules)
        v.extend(pv)
        if not pv:
            for bg_slot, bg_role, fg_slot, fg_role in _contrast_pairs(rules):
                r = contrast_ratio(roles[bg_role], roles[fg_role])
                if r < rules["min_contrast"]:
                    v.append("C4 palette: %s（%s %s）と %s（%s %s）の明暗差 %.2f < %s" % (
                        bg_slot, bg_role, roles[bg_role], fg_slot, fg_role, roles[fg_role], r, rules["min_contrast"]))

    # 投稿文
    if "post" in config:
        post = config["post"]
        if not isinstance(post, dict):
            v.append("C7 post: object にする")
        else:
            v.extend(_check_post(post, cards, rules, w))
    return v, w


def _check_post(post, cards, rules, warnings):
    v = []
    for k in sorted(set(post) - POST_KEYS):
        v.append("C7 post: 許されないキー %r" % k)
    for k in POST_KEYS:
        if k in post and not isinstance(post[k], str):
            v.append("C7 post: %s は文字列にする" % k)
    src = post.get("supplement_source")
    if src is None or (isinstance(src, str) and not src.strip()):
        v.append("C6 post: supplement_source（投稿文に足した一次の補足の所在）が無い")
    text = post.get("text", "")
    if not isinstance(text, str):
        return v
    if not text.strip():
        v.append("C6 post: text が空")
        return v
    mode = post.get("count", rules["post_count"]["default"])
    modes = list(POST_MODES)  # 形を確かめた方式だけ（rules_problems）
    if isinstance(mode, str):
        if mode not in modes:
            v.append("C6 post: count %r は使えない（%s のどちらか）" % (mode, " / ".join(modes)))
        else:
            n, mx = post_length(text, mode, rules), rules["post_count"][mode]["max"]
            if n > mx:
                v.append("C6 post: 長さ %d が上限 %d を超える（数え方 %s）" % (n, mx, mode))
    normalized = _norm_for_copy(text)
    for i, card in enumerate(cards, 1):
        if not isinstance(card, dict):
            continue
        seen = set()
        candidates = []
        for field in ("title", "note", "body"):
            val = card.get(field)
            if isinstance(val, str):
                candidates.append((field, val))
                if field == "body":
                    candidates.extend(("body の行", line) for line in val.splitlines())
        for field, val in candidates:
            s = _norm_for_copy(val)
            if len(s) >= rules["copy_min_chars"] and s not in seen and s in normalized:
                seen.add(s)
                v.append("C6 post: card %d の %s を丸ごと写している（%s）" % (i, field, val.replace("\n", " / ")))
    if BARE_DOMAIN_RE.search(URL_RE.sub("", text)):
        warnings.append("post: https:// の無いドメイン名がある（X は URL として 23 と数えるが、この検査は文字として数える。URL は https:// から書く）")
    return v


# ---------------------------------------------------------------- 生成
def default_font(rules):
    return rules["default_font"]["darwin" if sys.platform == "darwin" else "other"]


def build_pptx(config, roles, rules, path):
    try:
        from pptx import Presentation
        from pptx.dml.color import RGBColor
        from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
        from pptx.oxml.ns import qn
        from pptx.util import Inches, Pt
    except ImportError:
        raise DependencyError("python-pptx が無い（pip install python-pptx）")
    lim, pt, used, box = rules["limits"], rules["font_pt"], rules["palette_roles_used"], rules["layout_in"]
    font = config.get("font") or default_font(rules)
    label = config.get("label")
    show_pages = config.get("page_numbers", True)
    cards = config["cards"]

    prs = Presentation()
    prs.slide_width = Inches(SLIDE_INCH)
    prs.slide_height = Inches(SLIDE_INCH)
    blank = prs.slide_layouts[6]

    def add_text(slide, text, box, size, color, align, bold=False, anchor=MSO_ANCHOR.TOP):
        shape = slide.shapes.add_textbox(Inches(box[0]), Inches(box[1]), Inches(box[2]), Inches(box[3]))
        tf = shape.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = anchor
        for n, line in enumerate(_lf(text).split("\n")):
            para = tf.paragraphs[0] if n == 0 else tf.add_paragraph()
            para.alignment = align
            para.line_spacing = rules["line_spacing"]
            run = para.add_run()
            run.text = line
            run.font.size = Pt(size)
            run.font.bold = bold
            run.font.color.rgb = RGBColor.from_string(color[1:])
            run.font.name = font
            rpr = run._r.get_or_add_rPr()
            prev = rpr.find(qn("a:latin"))
            for tag in ("a:ea", "a:cs"):  # 日本語の文字にも同じフォントを使わせる（順序は latin → ea → cs）
                el = rpr.find(qn(tag))
                if el is None:
                    el = rpr.makeelement(qn(tag), {})
                    prev.addnext(el)
                el.set("typeface", font)
                prev = el
        return shape

    for i, card in enumerate(cards, 1):
        dark = rules["cards_layout"][i - 1]["bg"] == "dark"
        side = "dark" if dark else "light"
        slide = prs.slides.add_slide(blank)
        fill = slide.background.fill
        fill.solid()
        fill.fore_color.rgb = RGBColor.from_string(roles[used["%s_bg" % side]][1:])
        text_c = roles[used["text_on_%s" % side]]
        label_c = roles[used["label_on_%s" % side]]
        note_c = roles[used["note_on_%s" % side]]
        if label:
            add_text(slide, label, box["label"], pt["label"], label_c, PP_ALIGN.LEFT, bold=True)
        title = card["title"]
        tsize = pt["title_small"] if text_length(title) > lim["title_recommended"] else pt["title"]
        add_text(slide, title, box["title"], tsize, text_c, PP_ALIGN.CENTER, bold=True, anchor=MSO_ANCHOR.MIDDLE)
        body = card.get("body", "")
        if body:
            bsize = pt["body_small"] if text_length(body) > lim["body_recommended"] else pt["body"]
            add_text(slide, body, box["body"], bsize, text_c, PP_ALIGN.CENTER)
        if card.get("note"):
            add_text(slide, card["note"], box["note"], pt["note"], note_c, PP_ALIGN.CENTER)
        if show_pages:
            add_text(slide, rules["page_number_format"].format(n=i, total=len(cards)), box["page_number"],
                     pt["page_number"], note_c, PP_ALIGN.RIGHT)
    prs.save(path)


# ---------------------------------------------------------------- 画像化
def jpeg_size(data):
    """JPEG のバイト列から (幅, 高さ) を読む。SOF0〜SOF15（C4・C8・CC を除く）が無い・JPEG でない時は None。"""
    if len(data) < 4 or data[0:2] != b"\xff\xd8":
        return None
    i = 2
    while i + 4 <= len(data):
        if data[i] != 0xFF:
            return None
        marker = data[i + 1]
        if marker == 0xFF:  # 詰め物
            i += 1
            continue
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        if marker == 0xD9:
            return None
        seg_len = int.from_bytes(data[i + 2:i + 4], "big")
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            if i + 9 > len(data):
                return None
            height = int.from_bytes(data[i + 5:i + 7], "big")
            width = int.from_bytes(data[i + 7:i + 9], "big")
            return width, height
        i += 2 + seg_len
    return None


def _timeout(env_name, default):
    raw = os.environ.get(env_name)
    if raw is None:
        return default
    try:
        val = float(raw)
    except ValueError:
        raise InputError("%s が数でない: %r" % (env_name, raw))
    if val <= 0:
        raise InputError("%s は正の数にする: %r" % (env_name, raw))
    return val


def profile_dir():
    """LibreOffice の利用者プロファイル。共有の一時フォルダの決まった名前は他の利用者に先に作られうるので、利用者のキャッシュに置く。"""
    if os.environ.get("SNS_CARDS_PROFILE"):
        return os.environ["SNS_CARDS_PROFILE"]
    cache = os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache")
    return os.path.join(cache, "sns-square-cards", "lo_profile")


def render_jpegs(pptx_path, out_dir, name, soffice, pdftoppm, timeouts, rules):
    """pptx（描画用の ASCII 名のフォルダにある）を JPEG にし、出力先へ <name>-N.jpg と <name>.pptx を置く。"""
    work = os.path.dirname(pptx_path)
    base = os.path.splitext(os.path.basename(pptx_path))[0]
    cmd = [soffice, "-env:UserInstallation=" + pathlib.Path(profile_dir()).resolve().as_uri(), "--headless",
           "--convert-to", "pdf", "--outdir", work, pptx_path]
    try:
        subprocess.run(cmd, check=True, timeout=timeouts["soffice"], capture_output=True)
    except subprocess.TimeoutExpired:
        raise RenderError("soffice が %s 秒で終わらない（初回はプロファイルの作成に数分かかる。同時に 2 つ動かしていないかも確かめる）" % timeouts["soffice"])
    except (subprocess.CalledProcessError, OSError) as e:
        raise RenderError("soffice で PDF にできない: %s" % e)
    pdf = os.path.join(work, base + ".pdf")
    if not os.path.isfile(pdf):
        raise RenderError("soffice が PDF を作らなかった（同じプロファイルを使う soffice が他で動いていないか確かめる）")
    prefix = os.path.join(work, "page")
    try:
        subprocess.run([pdftoppm, "-jpeg", "-jpegopt", "quality=92", "-scale-to", str(IMAGE_PX), pdf, prefix],
                       check=True, timeout=timeouts["pdftoppm"], capture_output=True)
    except subprocess.TimeoutExpired:
        raise RenderError("pdftoppm が %s 秒で終わらない" % timeouts["pdftoppm"])
    except (subprocess.CalledProcessError, OSError) as e:
        raise RenderError("pdftoppm で JPEG にできない: %s" % e)

    def page_no(p):
        m = re.search(r"-(\d+)\.jpg$", p)
        return int(m.group(1)) if m else -1
    pages = sorted(glob.glob(prefix + "-*.jpg"), key=page_no)
    if len(pages) != rules["card_count"]:
        raise RenderError("JPEG が %d 枚ではない (%d 枚)" % (rules["card_count"], len(pages)))
    for p in pages:
        with open(p, "rb") as f:
            size = jpeg_size(f.read())
        if size != (IMAGE_PX, IMAGE_PX):
            raise RenderError("%s の大きさが %dx%d ではない (%s)" % (os.path.basename(p), IMAGE_PX, IMAGE_PX, size))

    stage = tempfile.mkdtemp(prefix=".sns-cards-stage-", dir=out_dir)
    try:
        staged = []
        for n, p in enumerate(pages, 1):
            dst = os.path.join(stage, "%s-%d.jpg" % (name, n))
            shutil.copyfile(p, dst)
            staged.append(dst)
        dst = os.path.join(stage, name + ".pptx")
        shutil.copyfile(pptx_path, dst)
        staged.append(dst)
        moved = []
        for src in staged:
            target = os.path.join(out_dir, os.path.basename(src))
            try:
                os.replace(src, target)
            except OSError as e:
                raise RenderError("出力先への移動の途中で失敗した（移し終えたもの: %s）: %s" % (", ".join(moved) or "なし", e))
            moved.append(target)
        return moved
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def find_tools():
    path = os.environ.get("SNS_CARDS_RENDER_DECK") or DEFAULT_RENDER_DECK
    if not os.path.isfile(path):
        raise DependencyError("render_deck.py を import できない（%s が無い。slide-clarity-review を同じ相対パスに置く）" % path)
    spec = importlib.util.spec_from_file_location("render_deck_for_sns_cards", path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        return mod.find_soffice(), mod.find_pdftoppm()
    except Exception as e:  # import した先の誤りは道具の不在として扱う
        raise DependencyError("render_deck.py を import できない: %s" % e)


# ---------------------------------------------------------------- CLI
def _has_pptx():
    try:
        import pptx  # noqa: F401
        return True
    except ImportError:
        return False


def _font_check(font):
    fc = os.environ.get("FC_LIST")
    if not fc or not os.path.isfile(fc):  # SOFFICE と同じく、環境変数が無効なら PATH を探す
        fc = shutil.which("fc-list")
    if not fc:
        return None, "未確認 font %s: fc-list が無い（macOS は標準で持たない。既定の Hiragino Sans は macOS に標準で入っている）" % font
    try:
        out = subprocess.run([fc, ":", "family"], capture_output=True, text=True, timeout=30).stdout
    except (subprocess.SubprocessError, OSError) as e:
        return None, "未確認 font %s: fc-list を実行できない (%s)" % (font, e)
    names = {n.strip() for line in out.splitlines() for n in line.split(",") if n.strip()}
    if font in names:
        return True, "OK font %s" % font
    return False, "NG font %s: fc-list に無い（LibreOffice が別のフォントに置き換え、折り返しが変わる）" % font


def preflight(config_font, rules):
    ok = True
    lines = []
    if _has_pptx():
        lines.append("OK python-pptx")
    else:
        ok = False
        lines.append("NG python-pptx: 無い（pip install python-pptx）")
    try:
        soffice, pdftoppm = find_tools()
        lines.append("OK render_deck.py（道具の探し方）")
        for label, p in (("soffice", soffice), ("pdftoppm", pdftoppm)):
            if p:
                lines.append("OK %s: %s" % (label, p))
            else:
                ok = False
                lines.append("NG %s: 見つからない（環境変数 %s か PATH）" % (label, label.upper()))
    except DependencyError as e:
        ok = False
        lines.append("NG render_deck: %s" % e)
    font_ok, msg = _font_check(config_font or default_font(rules))
    lines.append(msg)
    if font_ok is False:
        ok = False
    print("\n".join(lines))
    return 0 if ok else 3


def run(argv):
    ap = argparse.ArgumentParser(description="SNS 投稿用の正方形カード 4 枚を検査し、1080x1080 の JPEG にする")
    ap.add_argument("--config", help="cards.json のパス")
    ap.add_argument("--check", action="store_true", help="検査だけ（標準ライブラリだけで動く）")
    ap.add_argument("--preflight", action="store_true", help="道具とフォントの有無を確かめる")
    ap.add_argument("--out-dir", help="出力先（既定のモードで必須）")
    ap.add_argument("--name", default="cards", help="出力の名前（英数字・_・- のみ。既定 cards）")
    ap.add_argument("--rules", default=DEFAULT_RULES, help="criteria の場所（既定は skill の criteria/card-rules.json）")
    a = ap.parse_args(argv)  # 引数の誤りは argparse が exit 2 にする

    if not NAME_RE.match(a.name):
        raise InputError("--name は英数字・_・- だけにする: %r" % a.name)
    if not a.preflight and not a.config:
        raise InputError("--config が要る")
    if not a.preflight and not a.check and not a.out_dir:
        raise InputError("--out-dir が要る（検査だけなら --check）")
    rules = load_rules(a.rules)
    config = None
    if a.config:
        config = load_json(a.config)
        if not isinstance(config, dict):
            raise InputError("%s の最上位が object ではない" % a.config)

    if a.preflight:
        font = config.get("font") if config and isinstance(config.get("font"), str) else None
        return preflight(font, rules)

    config_dir = os.path.dirname(os.path.abspath(a.config))
    ref_roles = load_palette_ref(config, config_dir)
    violations, warnings = check_config(config, rules, ref_roles)
    for x in warnings:
        print("WARN " + x, file=sys.stderr)
    if violations:
        for x in violations:
            print(x)
        return 1
    if a.check:
        print("PASS: 違反なし（警告 %d 件）" % len(warnings))
        return 0

    timeouts = {"soffice": _timeout("SNS_CARDS_SOFFICE_TIMEOUT", 600),
                "pdftoppm": _timeout("SNS_CARDS_PDFTOPPM_TIMEOUT", 60)}
    if not _has_pptx():
        raise DependencyError("python-pptx が無い（pip install python-pptx）")
    soffice, pdftoppm = find_tools()
    if not soffice:
        raise DependencyError("soffice が見つからない（環境変数 SOFFICE か PATH）")
    if not pdftoppm:
        raise DependencyError("pdftoppm が見つからない（環境変数 PDFTOPPM か PATH）")
    roles, _ = resolve_palette(config, ref_roles, rules)
    out_dir = os.path.abspath(a.out_dir)
    created = not os.path.isdir(out_dir)
    try:
        os.makedirs(out_dir, exist_ok=True)
    except OSError as e:
        raise InputError("出力先 %s を作れない: %s" % (out_dir, e))
    work = tempfile.mkdtemp(prefix="sns_cards_render_")
    try:
        pptx_path = os.path.join(work, "deck.pptx")
        build_pptx(config, roles, rules, pptx_path)
        outputs = render_jpegs(pptx_path, out_dir, a.name, soffice, pdftoppm, timeouts, rules)
    except BaseException:
        if created and os.path.isdir(out_dir) and not os.listdir(out_dir):
            os.rmdir(out_dir)  # この実行で作り、空のまま失敗した出力先は残さない
        raise
    finally:
        shutil.rmtree(work, ignore_errors=True)
    for p in outputs:
        print(p)
    return 0


def main(argv=None):
    try:
        return run(sys.argv[1:] if argv is None else argv)
    except InputError as e:
        print("入力の誤り: %s" % e, file=sys.stderr); return 2
    except DependencyError as e:
        print("道具が無い: %s" % e, file=sys.stderr); return 3
    except RenderError as e:
        print("描画の失敗: %s" % e, file=sys.stderr); return 4
    except SystemExit:
        raise
    except Exception:  # 想定外の例外は exit 1（違反）と区別する
        traceback.print_exc()
        return 5


if __name__ == "__main__":
    sys.exit(main())
