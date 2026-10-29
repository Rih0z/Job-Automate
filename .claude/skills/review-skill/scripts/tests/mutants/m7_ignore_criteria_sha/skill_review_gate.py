#!/usr/bin/env python
"""変異体 7（ほぼ正しい gate・1 箇所だけ違う）: criteria.sha256 を見ない（skill の hash が一致する PASS の記録があれば、criteria が変わっていても PASS）。
本物の gate が必要。狙う試験: test_criteria_change_makes_all_passes_stale。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _common as c  # noqa: E402
import helpers as h  # noqa: E402


def mutate(data, root):
    for name, v in data["skills"].items():
        if v["state"] == "STALE":
            now = h.skill_hash(root, name)
            if any(r.get("target", {}).get("content_hash") == now and r.get("result", {}).get("verdict") == "PASS" for r in c.records(root, name)):
                v["state"] = "PASS"


c.gate_main(sys.argv[1:], mutate)
