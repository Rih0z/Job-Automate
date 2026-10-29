#!/usr/bin/env python
"""変異体 4: 台帳を検証しない gate。--verify-ledger は常に exit 0。それ以外の引数は、既定の scripts/ の本物の gate に渡す
（本物がまだ無ければ exit 2）。試験が検出できなければならない誤った実装。"""
import subprocess
import sys
from pathlib import Path

if "--verify-ledger" in sys.argv:
    sys.exit(0)
real = Path(__file__).resolve().parents[3] / "skill_review_gate.py"
if not real.exists():
    sys.stderr.write("本物の gate が無い: %s\n" % real)
    sys.exit(2)
sys.exit(subprocess.call([sys.executable, str(real)] + sys.argv[1:]))
