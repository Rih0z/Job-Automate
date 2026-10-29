#!/usr/bin/env python
"""変異体 5（ほぼ正しい gate・1 箇所だけ違う）: 台帳を FAIL / INVALID より先に見る。台帳の hash が現在の hash と一致すると、
FAIL・INVALID でも BASELINE_DEBT にする。本物の gate が必要（実装前は検証できない）。狙う試験: test_fail_and_invalid_take_precedence_over_a_matching_ledger_entry。"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _common as c  # noqa: E402
import helpers as h  # noqa: E402


def mutate(data, root):
    ledger = Path(root) / h.LEDGER_REL
    if not ledger.exists():
        return
    entries = json.loads(ledger.read_text(encoding="utf-8")).get("skills", {})
    for name, v in data["skills"].items():
        if v["state"] in ("FAIL", "INVALID") and name in entries and entries[name].get("content_hash") == h.skill_hash(root, name):
            v["state"] = "BASELINE_DEBT"


c.gate_main(sys.argv[1:], mutate)
