#!/usr/bin/env python
"""変異体 6（ほぼ正しい gate・1 箇所だけ違う）: skill 名だけで記録を照合し、content_hash を見ない（PASS の記録が 1 件でもあれば PASS）。
本物の gate が必要。狙う試験: test_stale_after_any_file_in_the_skill_dir_changes。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _common as c  # noqa: E402


def mutate(data, root):
    for name, v in data["skills"].items():
        if v["state"] != "PASS" and any(r.get("result", {}).get("verdict") == "PASS" for r in c.records(root, name)):
            v["state"] = "PASS"


c.gate_main(sys.argv[1:], mutate)
