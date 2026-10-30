"""gate.py — 修正ループの合否判定と review-record の組み立て（純関数。ファイルには書かない）。

呼び出し順: validate_axes → validate_llm_results → compute_gate → build_record
- ランク: 総合点を review-rubrics.yaml の rank5_100（90/80/70/60）で S〜D に割り当てる
- ゲート: must の auto 違反、llm の must 不合格、総合 80 点未満（ランク A 未満）のどれかで FAIL。
  ランクとゲートは別物（95 点でも must 違反があれば「ランク S・FAIL」）
- llm 判定の severity は reviewer の申告を使わず、practices の定義から id で引く
"""
import os
import re

AXIS_MAX = 20
PASS_MIN_SCORE = 80
RANKS = ((90, "S"), (80, "A"), (70, "B"), (60, "C"))


def _num(x):
    return int(x) if float(x).is_integer() else x


def _is_number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def rank_of(score):
    for floor, label in RANKS:
        if score >= floor:
            return label
    return "D"


def validate_axes(axes, clarity):
    expected = [a["id"] for a in clarity["axes"]]
    weights = {a["id"]: a.get("weight", AXIS_MAX) for a in clarity["axes"]}
    errors, seen = [], set()
    for a in axes:
        aid = a.get("id")
        if aid in seen:
            errors.append("axes mismatch: duplicate %s" % aid)
        seen.add(aid)
        if aid not in expected:
            errors.append("unknown axis id: %s" % aid)
            continue
        score = a.get("score")
        if not _is_number(score) or not 0 <= score <= weights[aid]:
            errors.append("score out of range: %s" % aid)
        cites = a.get("citations")
        if not isinstance(cites, list) or not cites or not all(isinstance(c, str) and c.strip() for c in cites):
            errors.append("citations empty: %s" % aid)
    for aid in expected:
        if aid not in seen:
            errors.append("axes mismatch: missing %s" % aid)
    return errors


def validate_llm_results(llm_results, practices):
    ids = [p["id"] for p in practices]
    errors, seen = [], set()
    for r in llm_results:
        pid = r.get("practice_id")
        if pid in seen:
            errors.append("duplicate practice_id: %s" % pid)
        seen.add(pid)
        if pid not in ids:
            errors.append("unknown practice_id: %s" % pid)
        if not isinstance(r.get("passed"), bool):
            errors.append("passed must be bool: %s" % pid)
    for pid in ids:
        if pid not in seen:
            errors.append("llm_results missing: %s" % pid)
    return errors


def compute_gate(violations, llm_results, practices, axes):
    errors = validate_llm_results(llm_results, practices)
    if errors:
        raise ValueError("; ".join(errors))
    severity = {p["id"]: p["severity"] for p in practices}
    score = _num(sum(a["score"] for a in axes))
    reasons = []
    for v in violations:
        if v.get("severity") == "must":
            reasons.append("must violation: %s" % v.get("message", v.get("practice_id")))
    for r in llm_results:
        if severity[r["practice_id"]] == "must" and not r["passed"]:
            reasons.append("llm must not passed: %s" % r["practice_id"])
    if score < PASS_MIN_SCORE:
        reasons.append("score %s < %s (rank %s)" % (score, PASS_MIN_SCORE, rank_of(score)))
    return {"verdict": "FAIL" if reasons else "PASS", "rank": rank_of(score), "score": score, "reasons": reasons}


def build_record(deck_path, axes, gate, sources_cited, limitations, reviewed_at):
    stem = os.path.splitext(os.path.basename(deck_path))[0]
    m = re.search(r"[A-Za-z0-9_-]+", stem)
    tag = m.group(0) if m else "deck"
    summary = "ランク %s。判定 %s（%s点）。" % (gate["rank"], gate["verdict"], gate["score"])
    if gate["reasons"]:
        summary += " 理由: " + "; ".join(gate["reasons"]) + "。"
    if limitations:
        summary += " limitations: " + "; ".join(limitations)
    return {
        "schema": "review-record/v1",
        "skill": "slide-clarity-review",
        "reviewed_at": reviewed_at,
        "target": {"description": "slide-clarity-%s: %s" % (tag, stem), "path_or_url": deck_path},
        "verdict": gate["verdict"],
        "score": _num(sum(a["score"] for a in axes)),
        "summary": summary,
        "criteria": [{"id": a["id"], "result": "%s/%d" % (_num(a["score"]), AXIS_MAX)} for a in axes],
        "sources_cited": list(sources_cited),
    }
