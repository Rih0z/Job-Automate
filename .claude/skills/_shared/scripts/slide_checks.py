"""slide_checks.py — スライド系 skill の共有ロジック（標準ライブラリのみ）。

- evaluate_check(practice, value): auto practice 1 件を値に当てて、違反本文 or None を返す
- normalize_text(raw): 取得本文の正規化（fetch-log の照合用）
- contrast_ratio(hex_a, hex_b): WCAG の相対輝度式によるコントラスト比
check_deck.py（pptx 側）と validate_slide_data.py deck-spec（構成仕様側）の両方が同じ判定を使う。
"""
import html
import json
import re

SCOPES = ("deck", "deck-spec")
DECK_METRICS = ("body_chars", "bullet_count", "min_font_pt", "title")
SPEC_METRICS = ("points_count", "action_title_chars", "closing_present", "content_source_present",
                "focal_element_present", "raw_color_absent")
OPS = ("max", "min", "required")

HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def fmt(value):
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def evaluate_check(practice, value):
    """違反なら `<id> violated (...)` を返し、適合・判定不能なら None を返す。

    max/min: 値が None（継承フォント等で判定不能）なら違反にしない。
    required: None・空文字（strip 後）・False は違反。数値の 0 は存在するとみなす。
    """
    check = practice["check"]
    op = check["op"]
    pid = practice["id"]
    if op == "required":
        missing = value is None or value is False or (isinstance(value, str) and not value.strip())
        return "%s violated (%s required)" % (pid, check["metric"]) if missing else None
    if value is None:
        return None
    thr = check["threshold"]
    if op == "max" and value > thr:
        return "%s violated (%s > %s)" % (pid, fmt(value), fmt(thr))
    if op == "min" and value < thr:
        return "%s violated (%s < %s)" % (pid, fmt(value), fmt(thr))
    return None


def normalize_text(raw):
    """script/style 除去 → タグ除去 → 実体参照の展開 → 空白（全角含む）を 1 つの半角空白に畳む。"""
    raw = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    return re.sub(r"[\s　]+", " ", raw).strip()


def _luminance(hex_color):
    channels = []
    for i in (1, 3, 5):
        c = int(hex_color[i:i + 2], 16) / 255.0
        channels.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast_ratio(hex_a, hex_b):
    la, lb = _luminance(hex_a), _luminance(hex_b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)
