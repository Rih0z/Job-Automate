"""gate.py — 修正ループの合否判定と review-record の組み立て（純関数。ファイルには書かない）。

呼び出し順: validate_axes → validate_llm_results → validate_not_applicable → validate_axis_citations
          → compute_gate → build_record
- ランク: 総合点を review-rubrics.yaml の rank5_100（90/80/70/60）で S〜D に割り当てる
- ゲート: must の auto 違反、llm の must 不合格、総合 80 点未満（ランク A 未満）のどれかで FAIL。
  ランクとゲートは別物（95 点でも must 違反があれば「ランク S・FAIL」）
- llm 判定の severity は reviewer の申告を使わず、practices の定義から id で引く
- 対象外（2026-11 追加）: llm_results の要素 {"practice_id", "applicable": false, "reason"} は、資料が
  practice の適用条件（applies_when.deck）に当たらないことを表す。減点せず、must の不合格にも数えない。
  対象外にできるのは applies_when.deck を持つ practice だけ。applicable が無い要素は「当たる」とみなす（旧形式）
"""
import os
import re

import slide_checks as sc

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


# 点数の決め方（2026-11 追加）: 軸の点数を、点検員の自由な数字にせず、practice の合否から決める。
# 軸の点数 = 重み(20) - 失敗した practice の減点の合計（下限 0）。
#   must の失敗: -6 / should の失敗（llm の判定）: -3 / should の失敗（機械検査）: 違反のスライドが 1〜2 枚なら -2、3 枚以上なら -4
# 減点の大きさは暫定値（実績で見直す）。点検員が付ける軸の点数は参考情報として残す。
PENALTY_MUST = 6
PENALTY_SHOULD_LLM = 3
PENALTY_SHOULD_AUTO_FEW = 2
PENALTY_SHOULD_AUTO_MANY = 4
MANY_SLIDES = 3


def applicable(result):
    """llm_results の要素が「当たる」か（applicable が無い旧形式は当たるとみなす）。"""
    return result.get("applicable", True) is not False


def failed_llm(result):
    return applicable(result) and not result["passed"]


def derive_axes(violations, llm_results, practices, clarity):
    """practice の合否から軸の点数を導く。practices は id/severity を持つ定義の一覧。対象外は減点しない。"""
    severity = {p["id"]: p["severity"] for p in practices}
    auto_slides = {}
    for v in violations:
        auto_slides.setdefault(v["practice_id"], set()).add(v.get("slide"))
    failed = {pid: ("auto", len(slides)) for pid, slides in auto_slides.items()}
    for r in llm_results:
        if failed_llm(r):
            failed[r["practice_id"]] = ("llm", 1)
    out = []
    for a in clarity["axes"]:
        weight = a.get("weight", AXIS_MAX)
        penalty, basis = 0, []
        for pid in a.get("practice_ids", []):
            if pid not in failed:
                continue
            kind, n = failed[pid]
            if severity.get(pid) == "must":
                pen = PENALTY_MUST
            elif kind == "llm":
                pen = PENALTY_SHOULD_LLM
            else:
                pen = PENALTY_SHOULD_AUTO_MANY if n >= MANY_SLIDES else PENALTY_SHOULD_AUTO_FEW
            penalty += pen
            basis.append("%s(-%d)" % (pid, pen))
        out.append({"id": a["id"], "score": max(0, weight - penalty), "basis": basis})
    return out


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


def deck_condition(practice):
    return (practice.get("applies_when") or {}).get("deck")


def validate_llm_results(llm_results, practices):
    ids = [p["id"] for p in practices]
    by_id = {p["id"]: p for p in practices}
    errors, seen = [], set()
    for r in llm_results:
        pid = r.get("practice_id")
        if pid in seen:
            errors.append("duplicate practice_id: %s" % pid)
        seen.add(pid)
        if pid not in ids:
            errors.append("unknown practice_id: %s" % pid)
        if "applicable" in r and not isinstance(r["applicable"], bool):
            errors.append("applicable must be bool: %s" % pid)
        elif r.get("applicable") is False:
            if pid in by_id and deck_condition(by_id[pid]) is None:
                errors.append("not applicable not allowed: %s" % pid)
            if not isinstance(r.get("reason"), str) or not r["reason"].strip():
                errors.append("reason required for not applicable: %s" % pid)
            if "passed" in r:
                errors.append("passed must be omitted when not applicable: %s" % pid)
        elif not isinstance(r.get("passed"), bool):
            errors.append("passed must be bool: %s" % pid)
    for pid in ids:
        if pid not in seen:
            errors.append("llm_results missing: %s" % pid)
    return errors


def not_applicable_ids(llm_results):
    return [r.get("practice_id") for r in llm_results if r.get("applicable") is False]


def validate_not_applicable(llm_results, practices, totals):
    """機械の条件（auto_trigger）と矛盾する対象外を不正にする。totals は deck_fact_totals の結果（--facts が無ければ None）。"""
    by_id = {p["id"]: p for p in practices}
    errors = []
    for pid in not_applicable_ids(llm_results):
        trig = (deck_condition(by_id.get(pid, {})) or {}).get("auto_trigger")
        if not trig:
            continue
        if totals is None:
            errors.append("--facts required to mark %s not applicable (it has auto_trigger)" % pid)
            continue
        hit = sc.auto_trigger_holds(trig, totals)
        if hit:
            errors.append("%s cannot be not applicable (auto_trigger holds: %s)" % (pid, hit))
    return errors


CITATION_PREFIX = re.compile(r"^\[([a-z][a-z0-9-]*)\]\s")


def validate_axis_citations(axes, llm_results, known_ids):
    """軸の citations の任意の接頭辞 [practice-id] を照合する。対象外にした practice を理由にした引用と、
    practices に無い id の接頭辞を不正にする。接頭辞の形に合わない引用（例: "[1] の出典…"）はそのまま通す。"""
    na = set(not_applicable_ids(llm_results))
    errors = []
    for a in axes:
        for c in a.get("citations") or []:
            m = CITATION_PREFIX.match(c) if isinstance(c, str) else None
            if not m:
                continue
            pid = m.group(1)
            if pid not in known_ids:
                errors.append("unknown practice in citation prefix: %s (%s)" % (pid, a.get("id")))
            elif pid in na:
                errors.append("citation cites not-applicable practice: %s (%s)" % (pid, a.get("id")))
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
        if severity[r["practice_id"]] == "must" and failed_llm(r):
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
