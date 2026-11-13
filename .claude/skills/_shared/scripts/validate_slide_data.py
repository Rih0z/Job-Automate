#!/usr/bin/env python3
"""validate_slide_data.py — スライド系 skill のデータ検査（標準ライブラリのみ）。

  practices <slide-best-practices.json> [--fetch-log F] [--sources-dir D] [--today YYYY-MM-DD]
  deck-spec <deck-spec.json> --practices <slide-best-practices.json>
            spec_version 2 の設計図では、practice と無関係に「設計図の構造の検査」（check_structure_v2）も行う
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
ROLES_OK = ("title", "agenda", "section", "content", "closing", "appendix")
SECTION_KINDS = ("main", "reference")
EXAMPLE_PATTERNS = ("before-after", "good-bad")
EXAMPLE_STEPS = ("before", "result", "after", "effect")
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
        deck_cond = (p.get("applies_when") or {}).get("deck")
        if deck_cond is not None:
            for e in sc.deck_condition_errors(pid, deck_cond):
                rep.err(e)
            if chk.get("method") != "llm":
                rep.err("%s: applies_when.deck is only for llm practices" % pid)
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
def source_value(value):
    """content_source の値を、required の判定用に正規化する。文字列の配列も受け付ける（2026-11）。
    空の配列・空文字だけの配列は「無い」（None）とする。evaluate_check の required は空の配列を
    「ある」と判定してしまうため、ここで変換する（v1 の設計図にも同じく適用する。不具合の修正）。"""
    if isinstance(value, list):
        return value if any(isinstance(v, str) and v.strip() for v in value) else None
    return value


def spec_metrics(slide, spec):
    fe = slide.get("focal_element")
    return {
        "points_count": len(slide.get("points") or []),
        "action_title_chars": len(str(slide.get("action_title") or "").strip()),
        "content_source_present": source_value(slide.get("content_source")),
        "focal_element_present": None if fe in (None, "", "none") else fe,
    }


def applies(practice, slide):
    cond = practice.get("applies_when") or {}
    if "evidence_type_not_in" in cond and slide.get("evidence_type") in cond["evidence_type_not_in"]:
        return False
    if "role_in" in cond and slide.get("role") not in cond["role_in"]:
        return False
    return True


def _norm(text):
    return squash(str(text)).casefold()


def _nonempty(v):
    return (isinstance(v, str) and bool(v.strip())) or (isinstance(v, int) and not isinstance(v, bool))


def check_structure_v2(spec, slides, rep):
    """設計図の構造の検査（spec_version 2 のときだけ動く）。practice の有無に関係なく同じに動かす。
    メッセージの括弧内の id は、関係する観点の名前（参考）。practice でない観点も、手順の運用上の注意の名前として残す。"""
    nos = [s.get("no") for s in slides]
    # 章立て（one-topic-one-place）
    section_ids, themes = [], {}
    for sec in spec.get("sections") or []:
        sid = sec.get("id") if isinstance(sec, dict) else None
        if not _nonempty(sid) or not _nonempty(sec.get("theme")):
            rep.err("sections: id and theme required (one-topic-one-place)")
            continue
        if sid in section_ids:
            rep.err("sections: duplicate id %s (one-topic-one-place)" % sid)
        section_ids.append(sid)
        key = _norm(sec["theme"])
        if key in themes:
            rep.err("sections: duplicate theme '%s' in %s and %s (one-topic-one-place)" % (sec["theme"], themes[key], sid))
        else:
            themes[key] = sid
    # 素材（reproducible-material-complete）
    exhibit_ids = []
    for ex in spec.get("exhibits") or []:
        eid = ex.get("id") if isinstance(ex, dict) else None
        if not _nonempty(eid):
            rep.err("exhibits: id required (reproducible-material-complete)")
            continue
        exhibit_ids.append(eid)
        at = ex.get("full_text_at")
        if not _nonempty(at):
            rep.err("exhibit %s: full_text_at missing (reproducible-material-complete)" % eid)
        elif isinstance(at, int) and at not in nos:
            rep.err("exhibit %s: full_text_at slide %s not found (reproducible-material-complete)" % (eid, at))

    examples = {}
    for idx, s in enumerate(slides):
        no = s.get("no")
        if s.get("role") == "content" and not _nonempty(s.get("intent")):
            rep.err("slide %s: intent missing (purpose-and-premise)" % no)
        if "section" in s and s["section"] not in section_ids:
            rep.err("slide %s: unknown section %s (one-topic-one-place)" % (no, s["section"]))
        if "kind" in s:
            if s.get("role") != "section":
                rep.err("slide %s: kind is only for role section (main-before-reference)" % no)
            elif s["kind"] not in SECTION_KINDS:
                rep.err("slide %s: invalid kind (main-before-reference)" % no)
        refs = s.get("exhibit_ref")
        for r in (refs if isinstance(refs, list) else [refs] if refs is not None else []):
            if r not in exhibit_ids:
                rep.err("slide %s: unknown exhibit %s (reproducible-material-complete)" % (no, r))
        cs = s.get("content_source")
        if isinstance(cs, list) and not all(isinstance(v, str) and v.strip() for v in cs):
            rep.err("slide %s: content_source has an empty entry (source-locator-visible)" % no)
        ex = s.get("example")
        if ex is None:
            continue
        if not isinstance(ex, dict) or not _nonempty(ex.get("id")):
            rep.err("slide %s: example id required (before-after-order)" % no)
            continue
        steps = ex.get("steps")
        if not isinstance(steps, list) or not steps or any(x not in EXAMPLE_STEPS for x in steps):
            rep.err("slide %s: example steps must be a list of %s (before-after-order)" % (no, "/".join(EXAMPLE_STEPS)))
            steps = [x for x in steps if x in EXAMPLE_STEPS] if isinstance(steps, list) else []
        if "result" in steps and not _nonempty(ex.get("conditions")):
            rep.err("slide %s: example %s conditions missing (example-matches-conditions)" % (no, ex["id"]))
        e = examples.setdefault(ex["id"], {"patterns": set(), "steps": {}, "effect": False, "causes": set()})
        if "pattern" in ex:
            e["patterns"].add(ex["pattern"])
        for x in steps:
            e["steps"].setdefault(x, idx)
        e["effect"] = e["effect"] or _nonempty(ex.get("effect"))
        cause = ex.get("cause")
        if isinstance(cause, list):
            if len(cause) != 1:
                rep.err("slide %s: example %s cause must be one (one-example-one-cause)" % (no, ex["id"]))
            cause = cause[0] if cause else None
        if _nonempty(cause):
            e["causes"].add(_norm(cause))
    for eid, e in examples.items():
        pattern = next(iter(e["patterns"])) if len(e["patterns"]) == 1 else None
        if pattern not in EXAMPLE_PATTERNS:
            rep.err("example %s: pattern must be one of %s (before-after-order)" % (eid, "/".join(EXAMPLE_PATTERNS)))
        st = e["steps"]
        if "before" not in st or "after" not in st:
            rep.err("example %s: before and after required (before-after-order)" % eid)
        elif st["before"] > st["after"]:
            rep.err("example %s: before must come before after (before-after-order)" % eid)
        if pattern == "before-after" and "result" not in st:
            rep.err("example %s: result required for before-after (before-after-order)" % eid)
        if not e["effect"]:
            rep.err("example %s: effect missing (before-after-order)" % eid)
        if len(e["causes"]) > 1:
            rep.err("example %s: multiple causes (one-example-one-cause)" % eid)

    # 本編と参考の順序（main-before-reference）
    roles = [s.get("role") for s in slides]
    appendix = [i for i, r in enumerate(roles) if r == "appendix"]
    closing = [i for i, r in enumerate(roles) if r == "closing"]
    ref_sections = [i for i, s in enumerate(slides) if s.get("role") == "section" and s.get("kind") == "reference"]
    if appendix:
        first_app = appendix[0]
        for i in range(first_app + 1, len(slides)):
            if roles[i] in ("content", "closing"):
                rep.err("slide %s: %s after appendix (main-before-reference)" % (nos[i], roles[i]))
        if closing and closing[0] > first_app:
            rep.err("closing must come before the first appendix (main-before-reference)")
    for i in ref_sections:
        if not appendix:
            rep.err("slide %s: reference section without appendix (main-before-reference)" % nos[i])
        elif (closing and i < closing[-1]) or i > appendix[0]:
            rep.err("slide %s: reference section must be after the last closing and before the first appendix "
                    "(main-before-reference)" % nos[i])

    # 用語の一覧（日本語点検の軸 terms-and-references の、作成前の対）
    for g in spec.get("glossary") or []:
        g = g if isinstance(g, dict) else {}
        term, first = g.get("term"), g.get("first_slide")
        if not _nonempty(term) or not _nonempty(g.get("definition")) or isinstance(first, bool) or not isinstance(first, int):
            rep.err("glossary: term, definition and first_slide required (terms-and-references)")
            continue
        for s in slides:
            if isinstance(s.get("no"), int) and s["no"] < first:
                text = " ".join(_strings([s.get("action_title"), s.get("key_message"), s.get("points")]))
                if term in text:
                    rep.err("glossary '%s': used on slide %s before first_slide %s (terms-and-references)"
                            % (term, s["no"], first))
                    break


def check_structure_v3(spec, slides, rep):
    """設計図 v3 の検査（話の組み立て: 聞き手・持ち帰り・各スライドが支えるもの・つながり・同じ型の繰り返し・目次）。
    出典の無い運用上の規則（2026-11、人の手直しの観察から）。括弧内は構造の id で practice id ではない。"""
    raw = spec.get("sections")
    secs = [x for x in (raw if isinstance(raw, list) else []) if isinstance(x, dict) and _nonempty(x.get("id"))]
    if not secs:
        rep.err("sections missing (sections-v3)")
    kind_of = {x.get("id"): x.get("kind", "main") for x in secs}
    main_ids = [x.get("id") for x in secs if x.get("kind", "main") == "main"]
    nar = spec.get("narrative") if isinstance(spec.get("narrative"), dict) else {}
    prof = nar.get("audience_profile") if isinstance(nar.get("audience_profile"), dict) else {}
    if not _nonempty(prof.get("uses")):
        rep.err("narrative.audience_profile.uses missing (audience-profile)")
    tks = nar.get("takeaways") if isinstance(nar.get("takeaways"), list) else []
    if not 1 <= len(tks) <= 3:
        rep.err("takeaways: count %d not in 1..3 (takeaways)" % len(tks))
    tk_ids = []
    for t in tks:
        tid = t.get("id") if isinstance(t, dict) else None
        if not _nonempty(tid) or not _nonempty(t.get("text")):
            rep.err("takeaways: id and text required (takeaways)")
            continue
        if tid in tk_ids:
            rep.err("takeaways: duplicate id %s (takeaways)" % tid)
        tk_ids.append(tid)
    nos = [s.get("no") for s in slides]
    supported, first_tk, premises, closing_at, ctas = set(), None, [], None, []
    patterns, prev_section, seen_content, agenda_listed, agenda_seen = {}, None, False, set(), False
    for idx, s in enumerate(slides):
        no, role = s.get("no"), s.get("role")
        if role in ("content", "closing", "appendix", "section") and not _nonempty(s.get("section")):
            rep.err("slide %s: section missing (sections-v3)" % no)
        if role == "section" and _nonempty(s.get("section")) and s["section"] in kind_of:
            if s.get("kind", "main") != kind_of[s["section"]]:
                rep.err("slide %s: section kind does not match sections[] (sections-v3)" % no)
        if role == "closing" and closing_at is None:
            closing_at = idx
        sup = s.get("supports")
        if role == "content":
            if not isinstance(sup, list) or not sup:
                rep.err("slide %s: supports missing (supports-takeaway)" % no)
            elif any(x in ("premise", "cta") for x in sup) and len(sup) > 1:
                rep.err("slide %s: supports mixes premise/cta with other values (supports-takeaway)" % no)
            elif sup == ["premise"]:
                premises.append((idx, no))
            elif sup == ["cta"]:
                ctas.append((idx, no))
            else:
                for x in sup:
                    if x in tk_ids:
                        supported.add(x)
                        first_tk = idx if first_tk is None else first_tk
                    else:
                        rep.err("slide %s: supports unknown takeaway %s (supports-takeaway)" % (no, x))
        elif role == "closing" and sup is not None:
            if not isinstance(sup, list) or any(x not in tk_ids for x in sup):
                rep.err("slide %s: closing supports must be takeaway ids (supports-takeaway)" % no)
        if role == "content":
            starts = seen_content and s.get("section") != prev_section
            b = s.get("builds_on")
            if "builds_on" in s and (isinstance(b, bool) or not isinstance(b, int) or b not in nos
                                     or nos.index(b) >= idx):
                rep.err("slide %s: builds_on must point to an earlier slide (bridge)" % no)
            if (starts or "builds_on" in s) and not _nonempty(s.get("bridge")):
                rep.err("slide %s: bridge missing (bridge)" % no)
            prev_section, seen_content = s.get("section"), True
            pat = s.get("repeat_pattern")
            if _nonempty(pat):
                patterns[pat] = patterns.get(pat, 0) + 1
                if patterns[pat] >= 3 and not _nonempty(s.get("new_point")):
                    rep.err("slide %s: new_point missing for 3rd+ use of pattern %s (pattern-repeat)" % (no, pat))
        if role == "agenda":
            agenda_seen = True
            ids = s.get("agenda_sections")
            if not isinstance(ids, list) or not ids:
                rep.err("slide %s: agenda_sections missing (agenda-sections)" % no)
                continue
            for x in ids:
                if not _nonempty(x) or x not in main_ids:
                    rep.err("slide %s: agenda lists unknown or reference section %s (agenda-sections)" % (no, x))
                    continue
                agenda_listed.add(x)
    for t in tk_ids:
        if t not in supported:
            rep.err("takeaways: %s not supported by any content slide (supports-takeaway)" % t)
    for idx, no in premises:
        if first_tk is not None and idx > first_tk:
            rep.err("slide %s: premise after takeaway slides (supports-takeaway)" % no)
    for idx, no in ctas:
        if closing_at is not None and idx > closing_at:
            rep.err("slide %s: cta after closing (cta-before-closing)" % no)
    if agenda_seen:
        for x in main_ids:
            if x not in agenda_listed:
                rep.err("agenda: main section %s not listed (agenda-sections)" % x)


def check_deck_spec(spec, practices, rep):
    version = spec.get("spec_version", 1)
    if version not in (1, 2, 3) or isinstance(version, bool):
        rep.err("invalid spec_version (1, 2 or 3)")
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
    if version in (2, 3):                              # 2.0 も 2 と同じに扱う（変更前と同じ）
        check_structure_v2(spec, valid_slides, rep)
    if version == 3:
        check_structure_v3(spec, valid_slides, rep)

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
