"""変異体 5〜8 の共通部品。「本物の実装を呼び、結果を 1 箇所だけ誤らせる」型の変異体（ほぼ正しいが 1 箇所だけ違う）を作るための補助。

本物の script（scripts/ にある実装）が無いときは、標準エラーに MUTANT_NEEDS_REAL を出して exit 97 で終わる（実装前は検証できない。
run_mutants.py はこれを「未検証（PENDING）」として扱う）。
"""
import json
import subprocess
import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parents[1]
SCRIPTS = TESTS.parent
NEEDS_REAL = 97
sys.path.insert(0, str(TESTS))
sys.dont_write_bytecode = True


def need(name):
    p = SCRIPTS / name
    if not p.exists():
        sys.stderr.write("MUTANT_NEEDS_REAL: 本物の実装が無い: %s\n" % p)
        sys.exit(NEEDS_REAL)
    return p


def arg_value(argv, flag):
    return argv[argv.index(flag) + 1] if flag in argv else None


def passthrough(name, argv):
    p = need(name)
    r = subprocess.run([sys.executable, str(p)] + argv, capture_output=True)
    sys.stdout.buffer.write(r.stdout)
    sys.stderr.buffer.write(r.stderr)
    sys.exit(r.returncode)


def real_gate_json(root):
    p = need("skill_review_gate.py")
    r = subprocess.run([sys.executable, str(p), "--repo-root", str(root), "--json"], capture_output=True)
    return json.loads(r.stdout.decode("utf-8"))


def emit_gate(argv, data):
    """本物の --json 出力を（誤らせた上で）--json / --all / --strict の形で出す。"""
    skills = data["skills"]
    counts = {"PASS": 0, "BASELINE_DEBT": 0, "NEEDS_REVIEW": 0}
    for v in skills.values():
        if v["state"] == "PASS":
            counts["PASS"] += 1
        elif v["state"] == "BASELINE_DEBT":
            counts["BASELINE_DEBT"] += 1
        else:
            counts["NEEDS_REVIEW"] += 1
    data["counts"] = counts
    sys.stdout.reconfigure(encoding="utf-8")
    if "--json" in argv:
        print(json.dumps(data, ensure_ascii=False))
        sys.exit(0)
    for name, v in sorted(skills.items()):
        print("%s: %s" % (name, v["state"]))
    print("PASS=%d BASELINE_DEBT=%d NEEDS_REVIEW=%d" % (counts["PASS"], counts["BASELINE_DEBT"], counts["NEEDS_REVIEW"]))
    if "--strict" in argv:
        sys.exit(1 if counts["NEEDS_REVIEW"] else 0)
    sys.exit(0)


def gate_main(argv, mutate):
    """--json / --all / --strict は、本物の --json を mutate(data, root) で 1 箇所だけ誤らせて出す。他の引数は本物へそのまま渡す。"""
    if not any(m in argv for m in ("--json", "--all", "--strict")):
        passthrough("skill_review_gate.py", argv)
    root = Path(arg_value(argv, "--repo-root") or ".")
    data = real_gate_json(root)
    mutate(data, root)
    emit_gate(argv, data)


def records(root, skill):
    d = Path(root) / ".claude" / "review-history" / "skill-review" / skill
    out = []
    for f in sorted(d.glob("*.json")) if d.is_dir() else []:
        try:
            out.append(json.loads(f.read_text(encoding="utf-8")))
        except ValueError:
            pass
    return out
