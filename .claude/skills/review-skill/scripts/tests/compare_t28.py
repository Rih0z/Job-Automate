#!/usr/bin/env python
"""T28（regression）の前後比較。標準ライブラリのみ。unittest の対象外（ファイル名が test で始まらない）。

使い方:
  python compare_t28.py --capture 出力ログ     既存の検査 5 つを実行し、同じ形式のログを保存する（実装後の t28-after.log を作るのに使う）
  python compare_t28.py before.log after.log   前後のログを比べる。FAIL・WARN 等の件数が増えていれば、または検査が消えていれば非ゼロ

比べる指標（各検査の節ごと）: FAIL_lines・WARN_lines・NG_lines。after が before より大きければ NG。
before の終了コードが 0 なのに after が 0 でなければ NG。before にあった検査（節）が after に無ければ NG。
「基準ログと同じか少ない」が close の条件で、t28-after.log は close 時の必須。
"""
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
COMMANDS = [
    [sys.executable, ".claude/skills/_shared/scripts/check_compliance_status.py"],
    ["bash", ".claude/skills/harness-compliance-audit/scripts/harness_check.sh", ".claude/skills/review-skill/SKILL.md", "CLAUDE.md"],
    ["bash", ".claude/skills/agent-harness-bootstrap/scripts/provenance-check.sh"],
    ["bash", ".claude/skills/agent-harness-bootstrap/scripts/hook-stop-setup-gate.test.sh"],
    [sys.executable, ".claude/skills/_shared/scripts/list_review_records.py", "--target", "review-skill"],
]
TIMEOUT = 1500
METRICS = ("FAIL_lines", "WARN_lines", "NG_lines")


def header(cmd):
    return "## " + " ".join(["python" if c == sys.executable else c for c in cmd])


def capture(out):
    head = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True).stdout.decode().strip()
    lines = ["# T28 実装後のログ（compare_t28.py --capture）", "date: %s" % time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "HEAD: %s" % head]
    for cmd in COMMANDS:
        t0 = time.time()
        try:
            p = subprocess.run(cmd, capture_output=True, cwd=str(REPO), timeout=TIMEOUT)
            text = (p.stdout + b"\n" + p.stderr).decode("utf-8", "replace")
            code = p.returncode
        except subprocess.TimeoutExpired:
            text, code = "", 124
        lines.append(header(cmd))
        lines.append("exit=%d time=%ds" % (code, time.time() - t0))
        lines.append("FAIL_lines=%d WARN_lines=%d NG_lines=%d" % (
            len(re.findall(r"FAIL", text, re.I)), len(re.findall(r"WARN", text, re.I)), len(re.findall(r"^NG", text, re.M))))
        lines.extend(text.strip().splitlines()[-5:])
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("saved", out)
    return 0


def parse(path):
    sections = {}
    cur = None
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            cur = re.sub(r"（.*", "", line[3:]).strip()  # 括弧書きの注記は比較に使わない
            sections[cur] = {}
            continue
        if cur is None:
            continue
        m = re.match(r"exit=(\d+)", line)
        if m:
            sections[cur]["exit"] = int(m.group(1))
        for k, v in re.findall(r"\b(FAIL_lines|WARN_lines|NG_lines)=(\d+)", line):
            sections[cur][k] = int(v)
    return sections


def compare(before, after):
    b, a = parse(before), parse(after)
    bad = []
    for sec, bm in b.items():
        am = a.get(sec)
        if am is None:
            bad.append("検査が after に無い: %s" % sec)
            continue
        for k in METRICS:
            if k in bm and k in am and am[k] > bm[k]:
                bad.append("%s: %s が増えた（before %d → after %d）" % (sec, k, bm[k], am[k]))
        if bm.get("exit") == 0 and am.get("exit", 0) != 0:
            bad.append("%s: before は exit 0 だったが after は exit %s" % (sec, am.get("exit")))
    for line in bad:
        print("NG:", line)
    print("RESULT:", "NG" if bad else "OK（基準と同じか少ない）")
    return 1 if bad else 0


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(argv) == 2 and argv[0] == "--capture":
        return capture(argv[1])
    if len(argv) == 2:
        return compare(*argv)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
