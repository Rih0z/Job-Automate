#!/usr/bin/env python
"""変異体 1: 常に PASS を返す gate（--strict は常に exit 0、--all / --json は全 skill が PASS）。試験が検出できなければならない誤った実装。"""
import json
import sys
from pathlib import Path

args = sys.argv[1:]
root = Path(args[args.index("--repo-root") + 1]) if "--repo-root" in args else Path.cwd()
skills = sorted(d.name for d in (root / ".claude" / "skills").iterdir() if (d / "SKILL.md").exists()) if (root / ".claude" / "skills").is_dir() else []
if "--hash" in args:
    print("0" * 64)
elif "--verify-ledger" in args:
    pass
elif "--json" in args:
    print(json.dumps({"skills": {s: {"state": "PASS", "notes": []} for s in skills},
                      "counts": {"PASS": len(skills), "BASELINE_DEBT": 0, "NEEDS_REVIEW": 0}, "warnings": []}))
else:
    for s in skills:
        print("%s: PASS" % s)
    print("PASS=%d BASELINE_DEBT=0 NEEDS_REVIEW=0" % len(skills))
sys.exit(0)
