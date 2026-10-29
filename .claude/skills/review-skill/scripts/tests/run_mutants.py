#!/usr/bin/env python
"""変異試験: 誤った実装（mutants/ 配下）に差し替えたとき、狙った試験が「アサーション失敗」で落ちることを確かめる。標準ライブラリのみ。

使い方: python run_mutants.py [--log パス] [--require-all] [--only 変異体名]
仕組み:
  - 環境変数 SKILL_REVIEW_SCRIPTS_DIR に変異体のディレクトリを指す。変異体にある script だけが差し替わり、他は既定の scripts/ のもの。
  - 変異体は 2 種類。m1〜m4 は粗い（定数を返す・台帳を見ない）。m5〜m11 は「本物の実装を呼び、結果を 1 箇所だけ誤らせる」型で、
    本物の実装が scripts/ に無い間は検証できないので PENDING（未検証）にする。実装後は --require-all で PENDING を失敗にして再実行する。
  - 全試験は回さず、変異体ごとに狙った試験だけを -k で回す（数分に収める）。
  - 狙った試験が FAIL（アサーション）で落ちれば検出。ERROR（script 不在・例外）は検出に数えない。helpers 由来の AssertionError
    （子プロセスの打ち切り・script 不在・Git Bash が無い）も検出に数えず、別集計にする。
環境変数: SKILL_REVIEW_MUTANT_TIMEOUT（変異体 1 件あたりの秒数。既定 300）。
終了コード: 0 = 検出できなかった変異体が無い（--require-all なら PENDING も無い）/ 1 = ある。
"""
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent
REAL_REPO = HERE.parents[4]
PER_MUTANT_TIMEOUT = int(os.environ.get("SKILL_REVIEW_MUTANT_TIMEOUT", "300"))
HELPER_MARKERS = ("子プロセスが", "被試験物が存在しない", "Git Bash が見つからない", "gate --json が exit", "git ")

# (名前, 説明, 狙った試験, 必要な本物の script)
MUTANTS = [
    ("m1_always_pass", "常に PASS を返す gate（粗い）",
     ["test_stale_after_any_file_in_the_skill_dir_changes", "test_decision_table_rows_resolve_in_documented_order"], []),
    ("m2_always_block", "常に block する hook（粗い）", ["test_stop_hook_blocks_with_skill_names_and_one_at_a_time_instruction"], []),
    ("m3_save_nothing", "何も保存しない保存 script（粗い）", ["test_saved_hash_and_reviewed_at_are_computed_by_the_script"], []),
    ("m4_no_ledger_check", "台帳を検証しない gate（--verify-ledger が常に 0）", ["test_ledger_edits_after_the_anchor_commit_are_detected"], []),
    ("m5_ledger_first", "台帳を FAIL / INVALID より先に見る gate",
     ["test_fail_and_invalid_take_precedence_over_a_matching_ledger_entry"], ["skill_review_gate.py"]),
    ("m6_name_only", "skill 名だけで記録を照合し content_hash を見ない gate",
     ["test_stale_after_any_file_in_the_skill_dir_changes"], ["skill_review_gate.py"]),
    ("m7_ignore_criteria_sha", "criteria.sha256 を見ない gate", ["test_criteria_change_makes_all_passes_stale"], ["skill_review_gate.py"]),
    ("m8_no_expected_hash_check", "--expected-hash の不一致を検査せず保存する script",
     ["test_save_rejects_when_hash_changed_during_review"], ["append_skill_review_record.py"]),
    ("m9_counter_not_reset", "新 turn でカウンタを 0 に戻さない hook",
     ["test_stop_hook_blocks_up_to_three_times_per_turn_then_allows_on_the_fourth"], ["hook-skill-review-gate.sh", "skill_review_gate.py"]),
    ("m10_lists_pass_skills", "PASS 済み skill まで block の reason に列挙する hook",
     ["test_stop_hook_blocks_with_skill_names_and_one_at_a_time_instruction"], ["hook-skill-review-gate.sh", "skill_review_gate.py"]),
    ("m11_session_start_blocks", "SessionStart でも block する hook",
     ["test_session_start_hook_reports_counts_without_blocking"], ["hook-skill-review-gate.sh", "skill_review_gate.py"]),
]


def head():
    try:
        return subprocess.run(["git", "-C", str(REAL_REPO), "rev-parse", "HEAD"], capture_output=True, timeout=30).stdout.decode().strip()
    except Exception:
        return "?"


def failure_blocks(text):
    """unittest の出力から (種別, 試験名, 最初のアサーション行) を取り出す。"""
    out = []
    for m in re.finditer(r"^={70}\n(FAIL|ERROR): (test_\w+)[^\n]*\n-{70}\n(.*?)(?=^={70}\n|^-{70}\nRan |\Z)", text, re.M | re.S):
        kind, name, body = m.group(1), m.group(2), m.group(3)
        first = ""
        for line in body.splitlines():
            if re.match(r"^(AssertionError|FileNotFoundError|\w+Error|\w+Exception)\b", line):
                first = line.strip()
                break
        out.append((kind, name, first))
    return out


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    log = Path(argv[argv.index("--log") + 1]) if "--log" in argv else None
    only = argv[argv.index("--only") + 1] if "--only" in argv else None
    require_all = "--require-all" in argv
    lines = []

    def say(s):
        print(s)
        lines.append(s)

    say("# 変異試験")
    say("command: %s %s" % (sys.executable, " ".join(["run_mutants.py"] + argv)))
    say("date: %s" % time.strftime("%Y-%m-%dT%H:%M:%S%z"))
    say("HEAD: %s" % head())
    say("変異体 1 件あたりの timeout: %d 秒（SKILL_REVIEW_MUTANT_TIMEOUT で変更）" % PER_MUTANT_TIMEOUT)
    ng = pending = ok = 0
    for name, desc, targets, needs in MUTANTS:
        if only and name != only:
            continue
        missing = [n for n in needs if not (SCRIPTS / n).exists()]
        if missing:
            pending += 1
            say("PENDING %s（%s）: 本物の実装が無いので未検証（%s）。実装後に --require-all で再実行する。狙う試験: %s" % (name, desc, ", ".join(missing), targets))
            continue
        env = dict(os.environ)
        env["SKILL_REVIEW_SCRIPTS_DIR"] = str(HERE / "mutants" / name)
        env["PYTHONUTF8"] = "1"
        cmd = [sys.executable, "-m", "unittest", "discover", "-s", str(HERE), "-v"]
        for t in targets:
            cmd += ["-k", t]
        t0 = time.time()
        try:
            p = subprocess.run(cmd, capture_output=True, env=env, timeout=PER_MUTANT_TIMEOUT)
            text = (p.stdout + b"\n" + p.stderr).decode("utf-8", "replace").replace("\r\n", "\n")
        except subprocess.TimeoutExpired:
            ng += 1
            say("NG      %s（%s）: %d 秒で終わらない" % (name, desc, PER_MUTANT_TIMEOUT))
            continue
        blocks = failure_blocks(text)
        detected, helper_origin, errors = [], [], []
        for kind, tname, first in blocks:
            if tname not in targets:
                continue
            if kind == "ERROR":
                errors.append((tname, first))
            elif any(mk in first for mk in HELPER_MARKERS):
                helper_origin.append((tname, first))
            else:
                detected.append((tname, first))
        missed = [t for t in targets if t not in {d[0] for d in detected}]
        if missed:
            ng += 1
        else:
            ok += 1
        say("%s %s（%s）: %.0f 秒" % ("NG     " if missed else "OK     ", name, desc, time.time() - t0))
        for tname, first in detected[:3]:
            say("   検出: %s: %s" % (tname, first[:200]))
        if helper_origin:
            say("   （別集計・検出に数えない）helpers 由来の AssertionError: %d 件 例: %s" % (len(helper_origin), helper_origin[0][1][:120]))
        if errors:
            say("   （別集計・検出に数えない）ERROR（例外・script 不在）: %d 件 例: %s" % (len(errors), errors[0][1][:120]))
        if missed:
            say("   検出できなかった狙いの試験: %s" % missed)
    bad = ng + (pending if require_all else 0)
    say("RESULT: %s（検出 %d・未検出 %d・未検証 PENDING %d%s）" % ("OK" if not bad else "NG", ok, ng, pending, "。--require-all で PENDING も失敗扱い" if require_all else ""))
    if log:
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
