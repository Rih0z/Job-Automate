"""slide_checks.py — スライド系 skill の共有ロジック（標準ライブラリのみ）。

- evaluate_check(practice, value): auto practice 1 件を値に当てて、違反本文 or None を返す
- normalize_text(raw): 取得本文の正規化（fetch-log の照合用）
- contrast_ratio(hex_a, hex_b): WCAG の相対輝度式によるコントラスト比
- deck_fact_totals(facts) / auto_trigger_holds(trigger, totals) / deck_condition_errors(pid, cond):
  資料単位の適用条件（practice の applies_when.deck）の事実の集計・判定・書式の検査（2026-11 追加）
check_deck.py（pptx 側）と validate_slide_data.py deck-spec（構成仕様側）の両方が同じ判定を使う。
"""
import html
import json
import re

SCOPES = ("deck", "deck-spec")
DECK_METRICS = ("body_chars", "bullet_count", "min_font_pt", "title",
                "left_edge_count", "distinct_colors", "min_contrast",
                "empty_placeholder_count", "partial_overlap_count")
SPEC_METRICS = ("points_count", "action_title_chars", "closing_present", "content_source_present",
                "focal_element_present", "raw_color_absent")
OPS = ("max", "min", "required")
# applies_when.deck.auto_trigger で使える、deck-facts.json から計算する集計の名前と演算子
DECK_FACTS = ("slide_count", "section_count", "citation_marker_total", "hyperlink_total",
              "url_text_total", "source_label_total")
FACT_OPS = (">=", ">", "==")

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


# ---------------------------------------------------------------- 資料単位の適用条件（applies_when.deck）
def deck_fact_totals(facts):
    """deck-facts.json から、auto_trigger で使う集計を計算する（DECK_FACTS と同じ名前）。"""
    slides = facts.get("slides", [])

    def total(key):
        return sum((s.get("citation_markers") or {}).get(key, 0) for s in slides)

    return {
        "slide_count": facts.get("slide_count", len(slides)),
        "section_count": len(facts.get("sections") or []),
        "citation_marker_total": sum(len((s.get("citation_markers") or {}).get("markers", [])) for s in slides),
        "hyperlink_total": sum(len(s.get("hyperlinks") or []) for s in slides),
        "url_text_total": total("url_text_count"),
        "source_label_total": total("source_label_count"),
    }


def _compare(left, op, right):
    return {">=": left >= right, ">": left > right, "==": left == right}[op]


def auto_trigger_holds(trigger, totals):
    """auto_trigger（{"any_of": [{fact, op, value}]}）が事実で成り立つなら、成り立った条件の文字列を返す。"""
    for c in (trigger or {}).get("any_of", []):
        if _compare(totals[c["fact"]], c["op"], c["value"]):
            return "%s %s %s" % (c["fact"], c["op"], fmt(c["value"]))
    return None


def deck_condition_errors(pid, cond):
    """applies_when.deck の書式の検査。違反の文の一覧を返す。"""
    errors = []
    if not isinstance(cond, dict):
        return ["%s: applies_when.deck must be an object" % pid]
    if not isinstance(cond.get("condition"), str) or not cond["condition"].strip():
        errors.append("%s: applies_when.deck.condition missing" % pid)
    unknown = set(cond) - {"condition", "auto_trigger"}
    if unknown:
        errors.append("%s: applies_when.deck unknown key: %s" % (pid, ", ".join(sorted(unknown))))
    if "auto_trigger" in cond:
        trig = cond["auto_trigger"]
        items = trig.get("any_of") if isinstance(trig, dict) else None
        if not isinstance(items, list) or not items or set(trig) != {"any_of"}:
            errors.append("%s: auto_trigger must be {any_of: [...]}" % pid)
            return errors
        for c in items:
            if not isinstance(c, dict) or c.get("fact") not in DECK_FACTS:
                errors.append("%s: auto_trigger unknown fact: %s" % (pid, c.get("fact") if isinstance(c, dict) else c))
            elif c.get("op") not in FACT_OPS:
                errors.append("%s: auto_trigger unknown op: %s" % (pid, c.get("op")))
            elif isinstance(c.get("value"), bool) or not isinstance(c.get("value"), (int, float)):
                errors.append("%s: auto_trigger value must be a number" % pid)
    return errors
