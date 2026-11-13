#!/usr/bin/env python3
"""finalize_review.py — reviewer の返却 JSON を検査し、ゲート判定と review-record を出す。

使い方（採点）:
  python finalize_review.py --deck <deck.pptx> --auto <auto-results.json> --review <reviewer.json> \
      --practices <slide-best-practices.json> --clarity <clarity.json> [--facts <deck-facts.json>] \
      [--reviewed-at ISO8601] [--write] [--history-root <dir>] [--score-mode min|derived|reviewer]
使い方（最終版の確認。採点の引数とは一緒に使えない）:
  python finalize_review.py --verify-latest <deck.pptx> [--history-root <dir>]
      同じハッシュ（sha256）の PASS の record があれば終了コード 0、無ければ 1。

reviewer.json: {"axes":[{id,score,citations}], "llm_results":[{practice_id,passed} | {practice_id,applicable:false,reason}], "fixes":[...],
  "story_findings":[{slide,kind,problem,fix}]}
  story_findings（話の流れの指摘。必須・空配列可。全ての --score-mode で検査）は点数・ゲートに入れず、record の
  story_findings と summary の末尾「話の流れの指摘 N 件」に出す。形は gate.validate_story_findings。
  applicable:false（対象外）にできるのは applies_when.deck を持つ practice だけ。auto_trigger を持つ practice を
  対象外にするには --facts が要り、機械の条件が成り立つ資料では対象外にできない。
  citations の先頭に任意で [practice-id] を付けられる。対象外にした practice を接頭辞にした引用は不正。
手順: validate_axes → validate_llm_results → validate_not_applicable → validate_axis_citations → compute_gate → build_record。
  record には target.sha256（点検した .pptx のハッシュ。読めなければ null と limitations の "hash not computed"）と
  not_applicable（対象外にした practice と理由）を足す。
  --write: record を保存する。--history-root が無ければ _shared/scripts/append_review_record.py に渡し、
  このスクリプトのあるリポジトリの .claude/review-history/ に保存する。--history-root <dir> を付けると
  <dir>/slide-clarity-review/ にこのスクリプトが自分で保存する（同じ項目を検査し、不正なら保存しない）。
標準出力: record の JSON。終了コード: 0=PASS / 1=FAIL / 3=reviewer の出力が不正（再出力を依頼する）/ 2=読込エラー・引数の誤り・保存の拒否。
"""
import argparse
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
SHARED = os.path.join(HERE, "..", "..", "_shared", "scripts")
sys.path.insert(0, HERE)
sys.path.insert(0, SHARED)
import gate  # noqa: E402
import slide_checks as sc  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8")

SKILL = "slide-clarity-review"
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))  # .claude/skills/<skill>/scripts -> repo root
DEFAULT_HISTORY = os.path.join(REPO_ROOT, ".claude", "review-history")
SCORING_ARGS = ("deck", "auto", "review", "practices", "clarity", "facts", "reviewed_at")


def file_sha256(path):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except OSError:
        return None


# ---- record の検査と保存（--history-root のとき。_shared/scripts/append_review_record.py の validate() と同じ項目）
def record_errors(record):
    errors = []
    for key in ("schema", "skill", "reviewed_at", "target", "verdict", "summary"):
        if key not in record or record[key] in (None, ""):
            errors.append("missing required field: %s" % key)
    if record.get("schema") not in (None, "review-record/v1"):
        errors.append("schema must be 'review-record/v1'")
    for key in ("skill", "verdict", "summary"):
        if record.get(key) is not None and not isinstance(record[key], str):
            errors.append("%s must be a string" % key)
    target = record.get("target")
    if target is not None:
        if not isinstance(target, dict):
            errors.append("target must be an object")
        else:
            if not target.get("description"):
                errors.append("target.description is required and must be non-empty")
            if not isinstance(target.get("description"), (str, type(None))):
                errors.append("target.description must be a string")
            if target.get("path_or_url") is not None and not isinstance(target["path_or_url"], str):
                errors.append("target.path_or_url must be a string or null")
    if record.get("reviewed_at") is not None:
        try:
            datetime.fromisoformat(str(record["reviewed_at"]).replace("Z", "+00:00"))
        except ValueError:
            errors.append("reviewed_at must be ISO8601")
    score = record.get("score")
    if score is not None and (isinstance(score, bool) or not isinstance(score, (int, float))):
        errors.append("score must be a number or null")
    for field in ("sources_cited", "prior_records_referenced"):
        if field in record:
            if not isinstance(record[field], list):
                errors.append("%s must be an array if present" % field)
            else:
                errors += ["%s[%d] must be a string" % (field, i) for i, v in enumerate(record[field]) if not isinstance(v, str)]
    if "criteria" in record:
        if not isinstance(record["criteria"], list):
            errors.append("criteria must be an array if present")
        else:
            for i, c in enumerate(record["criteria"]):
                if not isinstance(c, dict):
                    errors.append("criteria[%d] must be an object" % i)
                    continue
                if not c.get("id"):
                    errors.append("criteria[%d].id is required" % i)
                if not isinstance(c.get("id"), (str, type(None))):
                    errors.append("criteria[%d].id must be a string" % i)
                if c.get("result") in (None, ""):
                    errors.append("criteria[%d].result is required" % i)
                urls = c.get("source_urls")
                if urls is not None and (not isinstance(urls, list) or not all(isinstance(u, str) for u in urls)):
                    errors.append("criteria[%d].source_urls must be an array of strings" % i)
    return errors


def slugify(text, max_len=60):
    slug = re.sub(r"[^a-zA-Z0-9\-]+", "-", text.strip()).strip("-").lower()
    slug = re.sub(r"-{2,}", "-", slug)
    return (slug or "untitled")[:max_len]


def save_record(record, history_root):
    """--history-root のときの保存。不正なら保存せず None と理由を返す。"""
    errors = record_errors(record)
    if errors:
        return None, errors
    rec = dict(record)
    for key, default in (("schema", "review-record/v1"), ("criteria", []), ("sources_cited", []),
                         ("prior_records_referenced", []), ("score", None)):
        rec.setdefault(key, default)
    out_dir = os.path.join(history_root, rec["skill"])
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    slug = slugify(rec["target"].get("description") or rec["target"].get("path_or_url") or "target")
    path = os.path.join(out_dir, "%s__%s.json" % (ts, slug))
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False, indent=2) + "\n")
    return path, []


# ---- 最終版の確認
def verify_latest(deck, history_root):
    digest = file_sha256(deck)
    if digest is None:
        print("ERROR: cannot read %s" % deck, file=sys.stderr)
        return 2
    folder = os.path.join(history_root or DEFAULT_HISTORY, SKILL)
    matched = []
    for path in sorted(glob.glob(os.path.join(folder, "*.json"))):
        try:
            rec = sc.load_json(path)
        except (OSError, ValueError):
            continue
        if (rec.get("target") or {}).get("sha256") == digest:
            matched.append((rec.get("reviewed_at") or "", path, rec.get("verdict")))
    passed = [m for m in matched if m[2] == "PASS"]
    if passed:
        print("PASS record found: %s" % max(passed)[1])
        return 0
    if matched:
        print("no PASS record for this version (only %s): %s" % (", ".join(sorted({m[2] or "?" for m in matched})), digest),
              file=sys.stderr)
    else:
        print("no record for this version (sha256 %s) in %s. Treat it as not reviewed." % (digest, folder), file=sys.stderr)
    return 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verify-latest", metavar="DECK")
    ap.add_argument("--deck")
    ap.add_argument("--auto")
    ap.add_argument("--review")
    ap.add_argument("--practices")
    ap.add_argument("--clarity")
    ap.add_argument("--facts", help="deck-facts.json（機械の適用条件 auto_trigger との照合に使う）")
    ap.add_argument("--reviewed-at")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--history-root", help="record の保存先・探し先（<dir>/slide-clarity-review/）。無ければこのリポジトリの .claude/review-history/")
    ap.add_argument("--score-mode", choices=("min", "derived", "reviewer"),
                    help="min（既定）: 軸の点数 = min(practice の合否から導いた点数, 点検員が付けた点数)。点検員は引用つきで下げられるが、上げられない。derived: 導出のみ。reviewer: 点検員の点数のみ（旧方式）")
    args = ap.parse_args(argv)
    if args.verify_latest:
        used = [a for a in SCORING_ARGS if getattr(args, a)] + (["write"] if args.write else []) + \
               (["score_mode"] if args.score_mode else [])
        if used:
            ap.error("--verify-latest cannot be combined with: %s" % ", ".join("--" + u.replace("_", "-") for u in used))
        return verify_latest(args.verify_latest, args.history_root)
    missing = [a for a in ("deck", "auto", "review", "practices", "clarity") if not getattr(args, a)]
    if missing:
        ap.error("the following arguments are required: %s" % ", ".join("--" + m for m in missing))
    score_mode = args.score_mode or "min"
    try:
        auto = sc.load_json(args.auto)
        review = sc.load_json(args.review)
        doc = sc.load_json(args.practices)
        clarity = sc.load_json(args.clarity)
        totals = sc.deck_fact_totals(sc.load_json(args.facts)) if args.facts else None
    except (OSError, ValueError) as e:
        print("ERROR: %s" % e, file=sys.stderr)
        return 2

    practices = {p["id"]: p for p in doc["practices"]}
    referenced = {pid for a in clarity["axes"] for pid in a.get("practice_ids", [])}
    llm_practices = [p for pid, p in practices.items() if pid in referenced and p["check"].get("method") == "llm"]

    axes, llm_results = review.get("axes", []), review.get("llm_results", [])
    errors = gate.validate_axes(axes, clarity) + gate.validate_llm_results(llm_results, llm_practices)
    if not errors:
        errors = gate.validate_not_applicable(llm_results, llm_practices, totals) + \
            gate.validate_axis_citations(axes, llm_results, set(practices))
    story = review.get("story_findings")
    errors += gate.validate_story_findings(story)
    if errors:
        print("reviewer 出力が不正です。再出力を依頼してください:", file=sys.stderr)
        for e in errors:
            print("  - " + e, file=sys.stderr)
        return 3

    violations = auto.get("violations", [])
    reviewer_axes = axes
    derived_axes = None
    if score_mode in ("derived", "min"):
        referenced_practices = [p for pid, p in practices.items() if pid in referenced]
        derived_axes = gate.derive_axes(violations, llm_results, referenced_practices, clarity)
        axes = derived_axes
        if score_mode == "min":
            rv = {a["id"]: a["score"] for a in reviewer_axes}
            axes = [{"id": d["id"], "score": min(d["score"], rv[d["id"]]), "basis": d["basis"]} for d in derived_axes]
    result = gate.compute_gate(violations, llm_results, llm_practices, axes)

    # 違反に関係した practice の出典 URL を sources_cited に載せる（対象外は関係しない）
    sources = {s["id"]: s["url"] for s in doc["sources"]}
    involved = [v["practice_id"] for v in violations] + [r["practice_id"] for r in llm_results if gate.failed_llm(r)]
    urls = []
    for pid in involved:
        for ev in practices.get(pid, {}).get("evidence", []):
            url = sources.get(ev["source_id"])
            if url and url not in urls:
                urls.append(url)

    digest = file_sha256(args.deck)
    limitations = list(auto.get("limitations", []))
    if digest is None:
        limitations.append("hash not computed")
    reviewed_at = args.reviewed_at or datetime.now().astimezone().isoformat(timespec="seconds")
    record = gate.build_record(args.deck, axes, result, urls, limitations, reviewed_at)
    record["target"]["sha256"] = digest
    record["not_applicable"] = [{"practice_id": r["practice_id"], "reason": r["reason"]}
                                for r in llm_results if r.get("applicable") is False]
    record["score_mode"] = score_mode
    record["reviewer_axis_scores"] = {a["id"]: a["score"] for a in reviewer_axes}
    if derived_axes is not None:
        record["axis_basis"] = {a["id"]: a["basis"] for a in derived_axes}
        record["derived_axis_scores"] = {a["id"]: a["score"] for a in derived_axes}
        raised = [a["id"] for a in reviewer_axes if a["score"] > {d["id"]: d["score"] for d in derived_axes}[a["id"]]]
        if raised and score_mode == "min":
            record["summary"] += " 点検員の点数が導出点より高い軸は、導出点を採用した: %s。" % ", ".join(raised)
    if record["not_applicable"]:
        record["summary"] += " 対象外: %s。" % ", ".join(n["practice_id"] for n in record["not_applicable"])
    record["story_findings"] = story
    record["summary"] += " 話の流れの指摘 %d 件" % len(story)
    print(json.dumps(record, ensure_ascii=False, indent=2))
    if args.write:
        if args.history_root:
            path, rec_errors = save_record(record, args.history_root)
            if path is None:
                print("REJECTED: review-record/v1 validation failed:", file=sys.stderr)
                for e in rec_errors:
                    print("  - " + e, file=sys.stderr)
                return 2
            print("saved: " + path, file=sys.stderr)
        else:
            p = subprocess.run([sys.executable, os.path.join(SHARED, "append_review_record.py"), "-"],
                               input=json.dumps(record, ensure_ascii=False), capture_output=True, text=True,
                               encoding="utf-8")
            sys.stderr.write(p.stderr)
            if p.returncode != 0:
                return 2
            print("saved: " + p.stdout.strip(), file=sys.stderr)
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
