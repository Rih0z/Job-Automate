#!/usr/bin/env python
"""変異体 8（ほぼ正しい保存 script・1 箇所だけ違う）: --expected-hash の不一致を検査せず保存する（渡された値を、保存時に計算した現在の hash に差し替えて
本物へ渡す）。本物の保存 script が必要。狙う試験: test_save_rejects_when_hash_changed_during_review。"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _common as c  # noqa: E402
import helpers as h  # noqa: E402

argv = sys.argv[1:]
real = c.need("append_skill_review_record.py")
if "--expected-hash" in argv and "--repo-root" in argv and "--skill" in argv:
    i = argv.index("--expected-hash")
    argv[i + 1] = h.skill_hash(c.arg_value(argv, "--repo-root"), c.arg_value(argv, "--skill"))
r = subprocess.run([sys.executable, str(real)] + argv, capture_output=True)
sys.stdout.buffer.write(r.stdout)
sys.stderr.buffer.write(r.stderr)
sys.exit(r.returncode)
