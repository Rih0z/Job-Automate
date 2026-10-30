#!/usr/bin/env python3
"""validate_slide_data.py — スライド系 skill のデータ検査（標準ライブラリのみ）。

  practices <slide-best-practices.json> [--fetch-log F] [--sources-dir D] [--today YYYY-MM-DD]
  deck-spec <deck-spec.json> --practices <slide-best-practices.json>
  clarity   <clarity.json>   --practices <slide-best-practices.json>
  palette   <palette.json>

終了コード: 0=合格（警告は WARN: として出る）/ 1=検査違反 / 2=引数・読込エラー。
違反は stderr、警告は stdout に出す。
"""
import argparse
import hashlib
import os
import re
import sys
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import slide_checks as sc  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8")

SOURCE_KEYS = ("id", "title", "url", "kind", "year", "verification", "checked_on", "max_age_days")
PRACTICE_KEYS = ("id", "category", "title", "rule", "rationale", "severity", "check", "evidence", "adaptation")
KINDS = ("standard", "book", "paper", "article")
VERIFICATIONS = ("fetched", "secondary")
SEVERITIES = ("must", "should")
METHODS = ("auto", "llm")
ORIGINS = ("source", "adaptation")
NUMERIC_RULE = re.compile(r"\d+(?:\.\d+)?\s*(?:pt|px|文字|項目|行|枚|%)")
NUMBER_TOKEN = re.compile(r"(?<![\d.])\d+(?:\.\d+)?(?![\d.])")
RAW_COLOR = re.compile(r"#[0-9A-Fa-f]{6}\b|rgb\(", re.I)
ROLES_OK = ("title", "agenda", "section", "content", "closing")
EVIDENCE_TYPES = ("chart", "diagram", "image", "table", "quote", "list", "opinion", "proposal")
LAYOUTS = ("title", "section", "content-1col", "content-2col", "chart", "image", "closing")
FOCALS = ("title", "figure", "number", "image", "none")
EMPHASIS = ("focus", "neutral", "functional", None)
SIZE_CLASSES = ("title", "body", "note")
TOP_KEYS = ("audience", "goal", "key_message", "storyline", "slides")
SLIDE_KEYS = ("no", "role", "action_title", "key_message", "evidence_type", "points", "layout_hint",
              "content_source", "focal_element", "emphasis_role", "text_size_class")
PALETTE_ROLES = ("focus", "surface-1", "surface-2", "border", "text-primary", "text-secondary",
                 "emphasis-mid", "functional")


class Report:
    def __init__(self):
        self.errors, self.warnings = [], []

    def err(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append("WARN: " + msg)

    def finish(self):
        for w in self.warnings:
            print(w)
        for e in self.errors:
            print(e, file=sys.stderr)
        return 1 if self.errors else 0


def squash(text):
    return re.sub(r"\s+", " ", text).strip()


def number_tokens(text):
    return [float(t) for t in NUMBER_TOKEN.findall(text)]


# ------------------------------------------------------------------ practices
def check_practices(doc, rep, today):
    sources = {s.get("id"): s for s in doc.get("sources", [])}
    for s in doc.get("sources", []):
        sid = s.get("id", "?")
        for k in SOURCE_KEYS:
            if k not in s or s[k] in (None, ""):
                rep.err("%s: %s missing" % (sid, k))
        if not s.get("authors") and not s.get("organization"):
            rep.err("%s: authors or organization missing" % sid)
        if s.get("kind") not in KINDS and "kind" in s:
            rep.err("%s: invalid kind" % sid)
        if s.get("verification") not in VERIFICATIONS and "verification" in s:
            rep.err("%s: invalid verification" % sid)
        try:
            due = datetime.strptime(s["checked_on"], "%Y-%m-%d").date() + timedelta(days=int(s["max_age_days"]))
            if due < today:
                rep.warn("%s: stale source (checked_on %s, max_age_days %s)" % (sid, s["checked_on"], s["max_age_days"]))
        except (KeyError, ValueError, TypeError):
            pass

    seen = set()
    for p in doc.get("practices", []):
        pid = p.get("id", "?")
        if pid in seen:
            rep.err("duplicate practice id: %s" % pid)
        seen.add(pid)
        for k in PRACTICE_KEYS:
            if k not in p:
                rep.err("%s: %s missing" % (pid, k))
        if p.get("severity") not in SEVERITIES and "severity" in p:
            rep.err("%s: invalid severity" % pid)
        chk = p.get("check", {})
        if chk.get("method") not in METHODS:
            rep.err("%s: invalid method" % pid)
        if chk.get("method") == "auto":
            scope = chk.get("scope")
            if scope not in sc.SCOPES:
                rep.err("%s: scope missing" % pid)
            metric = chk.get("metric")
            if metric not in sc.DECK_METRICS + sc.SPEC_METRICS:
                rep.err("%s: unknown metric" % pid)
            elif scope in sc.SCOPES and metric not in (sc.DECK_METRICS if scope == "deck" else sc.SPEC_METRICS):
                rep.err("%s: metric not allowed for scope" % pid)
            if chk.get("op") not in sc.OPS:
                rep.err("%s: unknown op" % pid)
            elif chk["op"] in ("max", "min") and not isinstance(chk.get("threshold"), (int, float)):
                rep.err("%s: threshold required" % pid)
        if "threshold" in chk:
            origin = chk.get("threshold_origin")
            if origin not in ORIGINS:
                rep.err("%s: threshold_origin missing" % pid)
        origin_ok = chk.get("threshold_origin") == "source" and "threshold" in chk
        if NUMERIC_RULE.search(p.get("rule", "")) and not (origin_ok or p.get("numeric_in_rule_ok")):
            rep.err("%s: numeric in rule requires threshold_origin=source" % pid)

        evidence = p.get("evidence") or []
        if not evidence:
            rep.err("%s: evidence missing" % pid)
        has_fetched = False
        quotes = []
        for ev in evidence:
            src = sources.get(ev.get("source_id"))
            if src is None:
                rep.err("%s: unknown source_id %s" % (pid, ev.get("source_id")))
            elif src.get("verification") == "fetched":
                has_fetched = True
            if not str(ev.get("locator", "")).strip():
                rep.err("%s: locator empty" % pid)
            q = str(ev.get("quote", "")).strip()
            if not q:
                rep.err("%s: quote empty" % pid)
            elif len(q) < 15:
                rep.err("%s: quote shorter than 15" % pid)
            quotes.append(q)
        if p.get("severity") == "must" and evidence and not has_fetched:
            rep.err("%s: must requires fetched evidence" % pid)
        if chk.get("threshold_origin") == "source" and isinstance(chk.get("threshold"), (int, float)):
            wanted = float(chk["threshold"])
            if not any(wanted in number_tokens(q) for q in quotes):
                rep.err("%s: threshold not in quote" % pid)

    n = len(doc.get("practices", []))
    if not 10 <= n <= 40:
        rep.warn("practice count %d outside 10-40" % n)


def check_fetch_log(doc, log, rep, sources_dir):
    entries = {e.get("source_id"): e for e in log.get("entries", [])}
    fetched = {s["id"]: s for s in doc.get("sources", []) if s.get("verification") == "fetched"}
    for sid, src in fetched.items():
        e = entries.get(sid)
        if e is None:
            rep.err("%s: fetch-log entry missing" % sid)
            continue
        if e.get("method") != "raw-http":
            rep.err("%s: method must be raw-http" % sid)
        if not e.get("sha256"):
            rep.err("%s: sha256 missing" % sid)
        if e.get("url") != src.get("url"):
            rep.err("%s: fetch-log url mismatch" % sid)
        excerpts = [squash(x) for x in e.get("excerpts", [])]
        for p in doc.get("practices", []):
            for ev in p.get("evidence", []):
                if ev.get("source_id") == sid and not any(squash(ev.get("quote", "")) in x for x in excerpts):
                    rep.err("%s: quote not found in fetch-log" % p["id"])
        if sources_dir:
            path = os.path.join(sources_dir, sid + ".html")
            if not os.path.exists(path):
                rep.err("%s: source body missing" % sid)
                continue
            with open(path, "rb") as f:
                raw = f.read()
            if e.get("sha256") and hashlib.sha256(raw).hexdigest() != e["sha256"]:
                rep.err("%s: sha256 mismatch" % sid)
            body = sc.normalize_text(raw.decode("utf-8", errors="replace"))
            if len(body) < 200:
                rep.err("%s: body too short for fetched" % sid)
            for x in e.get("excerpts", []):
                if sc.normalize_text(x) not in body:
                    rep.err("%s: excerpt not in source body" % sid)


# ------------------------------------------------------------------ deck-spec
def spec_metrics(slide, spec):
    fe = slide.get("focal_element")
    return {
        "points_count": len(slide.get("points") or []),
        "action_title_chars": len(str(slide.get("action_title") or "").strip()),
        "content_source_present": slide.get("content_source"),
        "focal_element_present": None if fe in (None, "", "none") else fe,
    }


def applies(practice, slide):
    cond = practice.get("applies_when") or {}
    if "evidence_type_not_in" in cond and slide.get("evidence_type") in cond["evidence_type_not_in"]:
        return False
    if "role_in" in cond and slide.get("role") not in cond["role_in"]:
        return False
    return True


def check_deck_spec(spec, practices, rep):
    for k in TOP_KEYS:
        if k not in spec:
            rep.err("missing key: %s" % k)
    if not isinstance(spec.get("slides"), list):
        return
    raw_color = False
    valid_slides = []
    for i, s in enumerate(spec["slides"], 1):
        no = s.get("no", i)
        missing = [k for k in SLIDE_KEYS if k not in s]
        for k in missing:
            rep.err("slide %s: missing key: %s" % (no, k))
        if missing:
            continue
        valid_slides.append(s)
        if s["role"] not in ROLES_OK:
            rep.err("slide %s: invalid role" % no)
        if s["evidence_type"] not in EVIDENCE_TYPES:
            rep.err("slide %s: invalid evidence_type" % no)
        if s["layout_hint"] not in LAYOUTS:
            rep.err("slide %s: invalid layout_hint" % no)
        if s["focal_element"] not in FOCALS:
            rep.err("slide %s: invalid focal_element" % no)
        if s["emphasis_role"] not in EMPHASIS:
            rep.err("slide %s: invalid emphasis_role" % no)
        if s["text_size_class"] not in SIZE_CLASSES:
            rep.err("slide %s: invalid text_size_class" % no)
        if any(RAW_COLOR.search(str(v)) for v in _strings(s)):
            raw_color = True
            rep.err("slide %s: raw color not allowed (use emphasis_role)" % no)
    if any(RAW_COLOR.search(v) for k in TOP_KEYS[:4] for v in _strings(spec.get(k))):
        raw_color = True
        rep.err("raw color not allowed")

    autos = [p for p in practices if p["check"].get("method") == "auto" and p["check"].get("scope") == "deck-spec"]
    for p in autos:
        metric = p["check"]["metric"]
        if metric == "closing_present":
            msg = sc.evaluate_check(p, any(s.get("role") == "closing" for s in valid_slides))
            if msg:
                rep.err(msg)
        elif metric == "raw_color_absent":
            msg = sc.evaluate_check(p, not raw_color)
            if msg:
                rep.err(msg)
        else:
            for s in valid_slides:
                if not applies(p, s):
                    continue
                msg = sc.evaluate_check(p, spec_metrics(s, spec)[metric])
                if msg:
                    rep.err("slide %s: %s" % (s["no"], msg))


def _strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)


# ------------------------------------------------------------------ clarity / palette
def check_clarity(clarity, practices, rep):
    axes = clarity.get("axes", [])
    ids = {p["id"] for p in practices}
    if len(axes) != 5:
        rep.err("axes must be 5")
    if sum(a.get("weight", 0) for a in axes) != 100:
        rep.err("weights must sum to 100")
    for a in axes:
        for pid in a.get("practice_ids", []):
            if pid not in ids:
                rep.err("%s: unknown practice_id %s" % (a.get("id", "?"), pid))


def check_palette(pal, rep):
    roles = pal.get("roles", {})
    for r in PALETTE_ROLES:
        if r not in roles:
            rep.err("role missing: %s" % r)
        elif not sc.HEX_COLOR.match(str(roles[r])):
            rep.err("invalid color: %s" % r)
    if rep.errors:
        return
    pairs = [("text-primary", "surface-1", 4.5), ("text-primary", "surface-2", 4.5),
             ("text-secondary", "surface-1", 4.5), ("focus", "surface-1", 3.0)]
    for fg, bg, need in pairs:
        if sc.contrast_ratio(roles[fg], roles[bg]) < need:
            rep.err("contrast too low: %s/%s (< %s)" % (fg, bg, need))
    if sc.contrast_ratio("#FFFFFF", roles["focus"]) < 4.5:
        rep.err("contrast too low: white/focus (< 4.5)")


# ------------------------------------------------------------------ main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["practices", "deck-spec", "clarity", "palette"])
    ap.add_argument("path")
    ap.add_argument("--practices")
    ap.add_argument("--fetch-log")
    ap.add_argument("--sources-dir")
    ap.add_argument("--today")
    args = ap.parse_args(argv)
    rep = Report()
    try:
        data = sc.load_json(args.path)
        today = datetime.strptime(args.today, "%Y-%m-%d").date() if args.today else date.today()
        if args.command == "practices":
            check_practices(data, rep, today)
            if args.fetch_log:
                check_fetch_log(data, sc.load_json(args.fetch_log), rep, args.sources_dir)
        elif args.command == "palette":
            check_palette(data, rep)
        else:
            if not args.practices:
                print("--practices is required", file=sys.stderr)
                return 2
            practices = sc.load_json(args.practices).get("practices", [])
            (check_deck_spec if args.command == "deck-spec" else check_clarity)(data, practices, rep)
    except (OSError, ValueError) as e:
        print("ERROR: %s" % e, file=sys.stderr)
        return 2
    return rep.finish()


if __name__ == "__main__":
    sys.exit(main())
