#!/usr/bin/env python3
"""check_deck.py — deck-facts.json を scope=deck の auto practice で検査し、auto-results.json を出す。

使い方: python check_deck.py <deck-facts.json> --practices <slide-best-practices.json> -o <auto-results.json>
終了コード: 0=違反なし / 1=違反あり / 2=読込エラー。
判定ロジックは _shared/scripts/slide_checks.py の evaluate_check（構成仕様の検査と共通）。
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "_shared", "scripts"))
import slide_checks as sc  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("facts")
    ap.add_argument("--practices", required=True)
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args(argv)
    try:
        facts = sc.load_json(args.facts)
        practices = sc.load_json(args.practices).get("practices", [])
    except (OSError, ValueError) as e:
        print("ERROR: %s" % e, file=sys.stderr)
        return 2
    autos = [p for p in practices if p["check"].get("method") == "auto" and p["check"].get("scope") == "deck"]
    violations = []
    for slide in facts.get("slides", []):
        for p in autos:
            msg = sc.evaluate_check(p, slide.get(p["check"]["metric"]))
            if msg:
                violations.append({"practice_id": p["id"], "slide": slide["no"], "severity": p["severity"],
                                   "message": "slide %s: %s" % (slide["no"], msg)})
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"violations": violations, "limitations": facts.get("limitations", [])}, f,
                  ensure_ascii=False, indent=2)
    for v in violations:
        print(v["message"], file=sys.stderr)
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
