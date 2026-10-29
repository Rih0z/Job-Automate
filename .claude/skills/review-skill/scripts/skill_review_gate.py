#!/usr/bin/env python3
"""skill_review_gate.py — 全 skill について、現在の内容に対応する合格のレビュー記録があるかを検査する（D3）。

使い方:
  python skill_review_gate.py [--repo-root R] --strict          PASS と BASELINE_DEBT 以外が 1 件でもあれば exit 1
  python skill_review_gate.py [--repo-root R] --all             一覧と件数（常に exit 0）
  python skill_review_gate.py [--repo-root R] --json            機械可読（常に exit 0）
  python skill_review_gate.py [--repo-root R] --hash SKILL      content_hash だけを出す（未知の skill は exit 2）
  python skill_review_gate.py [--repo-root R] --verify-ledger   負債台帳の検証（0 = 問題なし / 1 = 改ざん / 2 = UNVERIFIABLE）
終了コード: 0 / 1（--strict で要レビュー、--verify-ledger で改ざん）/ 2（引数不備・UNVERIFIABLE）/ 3（内部エラー）。
判定表（上から順に最初に当たる行）: PASS / FAIL / INVALID / BASELINE_DEBT / STALE / UNREVIEWED。
標準ライブラリのみ。出力は UTF-8。環境変数 SKILL_REVIEW_REPO_ROOT・CLAUDE_PROJECT_DIR・SKILL_REVIEW_NOW でルート・現在日時を差し替えられる。
"""
import argparse
import json
import os
import sys
import time
import traceback
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import skill_review_lib as lib  # noqa: E402

NEEDS_REVIEW_STATES = ("FAIL", "INVALID", "STALE", "UNREVIEWED")


def decide(cur_hash, records, ledger_entry, crit_sha, axes, min_score):
    """判定表を上から順に当てる純粋関数。records は [(ファイル名, オブジェクト)]。(state, notes) を返す。"""
    applicable, invalid_match, any_record = [], False, False
    for fname, rec in records:
        any_record = True
        errs = lib.validate_record(rec, None, None)  # 形の検査（criteria に依らない）
        t = rec.get("target") if isinstance(rec, dict) else None
        th = t.get("content_hash") if isinstance(t, dict) else None
        if not errs and crit_sha is not None and rec["criteria"]["sha256"] == crit_sha:
            # 現行 criteria の axes・min_score による整合検査は、criteria の sha256 が一致する記録だけに当てる。
            # sha256 が違う記録は旧 criteria で作られたものなので INVALID でなく行 5 の STALE にする。
            errs = lib.validate_record(rec, axes, min_score)
        if not errs:
            if th == cur_hash and crit_sha is not None and rec["criteria"]["sha256"] == crit_sha:
                applicable.append((rec["reviewed_at"], fname, rec))
        elif th == cur_hash:
            invalid_match = True
    notes = []
    if applicable:
        _, _, latest = max(applicable, key=lambda x: (x[0], x[1]))
        if latest["reviewer"]["agent_id"] == "unavailable":
            notes.append("agent_id_unavailable")
        if latest["result"]["verdict"] == "PASS":
            if ledger_entry is not None:
                notes.append("ledger_removable")
            return "PASS", notes
        return "FAIL", notes
    if invalid_match:
        return "INVALID", notes
    if isinstance(ledger_entry, dict) and ledger_entry.get("content_hash") == cur_hash:
        return "BASELINE_DEBT", notes
    if any_record:
        return "STALE", notes
    return "UNREVIEWED", notes


def evaluate(root):
    now = lib.now_utc()
    warnings = []
    crit_sha, crit_data, err = lib.criteria_info(root)
    if err:
        warnings.append("WARN: %s" % err)
    axes, min_score = lib.criteria_axes(crit_data) if crit_data is not None else (None, None)
    ledger, lw = lib.load_ledger(root)
    if lw:
        warnings.append(lw)
    _, _, expired, serr = lib.sot_status(root, now)
    if serr:
        warnings.append("WARN: %s" % serr)
    elif expired:
        warnings.append("WARN: best-practices SoT expired")
    skills = {}
    for name in lib.skill_names(root):
        cur, _files, unreadable = lib.skill_content(root, name)
        records, rw = lib.load_records(root, name)
        warnings.extend(rw)
        state, notes = decide(cur, records, ledger.get(name), crit_sha, axes, min_score)
        if unreadable:
            warnings.append("WARN: %s に読めないファイル %d 件（追跡済みで作業ツリーに無い、または読めない。hash から除外した）" % (name, unreadable))
        skills[name] = {"state": state, "notes": notes, "content_hash": cur}
    counts = {"PASS": 0, "BASELINE_DEBT": 0, "NEEDS_REVIEW": 0}
    for v in skills.values():
        counts[v["state"] if v["state"] in ("PASS", "BASELINE_DEBT") else "NEEDS_REVIEW"] += 1
    return {"skills": skills, "counts": counts, "warnings": warnings}


def counts_line(c):
    return "PASS=%d BASELINE_DEBT=%d NEEDS_REVIEW=%d" % (c["PASS"], c["BASELINE_DEBT"], c["NEEDS_REVIEW"])


def print_all(res):
    for name, v in res["skills"].items():
        extra = ""
        if "ledger_removable" in v["notes"]:
            extra += "（台帳から外せる）"
        if "agent_id_unavailable" in v["notes"]:
            extra += "（WARN: reviewer.agent_id unavailable）"
        print("%s: %s%s" % (name, v["state"], extra))
    for w in res["warnings"]:
        print(w)
    print(counts_line(res["counts"]))


def main(argv):
    lib.reconfigure_stdio()
    ap = argparse.ArgumentParser(description="skill のレビュー記録の gate")
    ap.add_argument("--repo-root")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--hash", metavar="SKILL")
    ap.add_argument("--verify-ledger", action="store_true")
    a = ap.parse_args(argv)

    # 試験用の継ぎ目（T30）: 起動直後に sleep する。本番では未設定（0）。
    delay = float(os.environ.get("SKILL_REVIEW_TEST_DELAY_SEC") or 0)
    if delay > 0:
        mark = os.environ.get("SKILL_REVIEW_TEST_MARK_DIR")
        if mark:
            Path(mark).mkdir(parents=True, exist_ok=True)
            (Path(mark) / "started").write_text("1", encoding="utf-8")
        time.sleep(delay)
        if mark:
            (Path(mark) / "finished").write_text("1", encoding="utf-8")

    root = lib.resolve_root(a.repo_root, __file__)
    if a.hash is not None:
        if a.hash not in lib.skill_names(root):
            print("skill が見つからない: %s" % a.hash, file=sys.stderr)
            return 2
        print(lib.skill_content(root, a.hash)[0])
        return 0
    if a.verify_ledger:
        code, lines = lib.verify_ledger(root)
        for ln in lines:
            print(ln)
        return code
    res = evaluate(root)
    if a.json:
        print(json.dumps(res, ensure_ascii=False))
        return 0
    if a.strict:
        bad = [(n, v["state"]) for n, v in res["skills"].items() if v["state"] in NEEDS_REVIEW_STATES]
        for n, s in bad:
            print("NEEDS_REVIEW: %s %s" % (n, s))
        for w in res["warnings"]:
            print(w)
        print(counts_line(res["counts"]))
        return 1 if bad else 0
    print_all(res)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception:  # 内部エラーは exit 3（hook は評価不能として通知して通す）
        sys.stderr.write("skill_review_gate: 内部エラー\n" + traceback.format_exc())
        sys.exit(3)
