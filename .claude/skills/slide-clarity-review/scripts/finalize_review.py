#!/usr/bin/env python3
"""finalize_review.py — reviewer の返却 JSON を検査し、ゲート判定と review-record を出す。

使い方:
  python finalize_review.py --deck <deck.pptx> --auto <auto-results.json> --review <reviewer.json> \
      --practices <slide-best-practices.json> --clarity <clarity.json> [--reviewed-at ISO8601] [--write]

reviewer.json: {"axes":[{id,score,citations}], "llm_results":[{practice_id,passed}], "fixes":[...]}
手順: validate_axes → validate_llm_results → compute_gate → build_record。
  --write を付けると _shared/scripts/append_review_record.py に record を渡して保存する（保存先パスを出力）。
標準出力: record の JSON。終了コード: 0=PASS / 1=FAIL / 3=reviewer の出力が不正（再出力を依頼する）/ 2=読込エラー。
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SHARED = os.path.join(HERE, "..", "..", "_shared", "scripts")
sys.path.insert(0, HERE)
sys.path.insert(0, SHARED)
import gate  # noqa: E402
import slide_checks as sc  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--deck", required=True)
    ap.add_argument("--auto", required=True)
    ap.add_argument("--review", required=True)
    ap.add_argument("--practices", required=True)
    ap.add_argument("--clarity", required=True)
    ap.add_argument("--reviewed-at")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args(argv)
    try:
        auto = sc.load_json(args.auto)
        review = sc.load_json(args.review)
        doc = sc.load_json(args.practices)
        clarity = sc.load_json(args.clarity)
    except (OSError, ValueError) as e:
        print("ERROR: %s" % e, file=sys.stderr)
        return 2

    practices = {p["id"]: p for p in doc["practices"]}
    referenced = {pid for a in clarity["axes"] for pid in a.get("practice_ids", [])}
    llm_practices = [p for pid, p in practices.items() if pid in referenced and p["check"].get("method") == "llm"]

    axes, llm_results = review.get("axes", []), review.get("llm_results", [])
    errors = gate.validate_axes(axes, clarity) + gate.validate_llm_results(llm_results, llm_practices)
    if errors:
        print("reviewer 出力が不正です。再出力を依頼してください:", file=sys.stderr)
        for e in errors:
            print("  - " + e, file=sys.stderr)
        return 3

    violations = auto.get("violations", [])
    result = gate.compute_gate(violations, llm_results, llm_practices, axes)

    # 違反に関係した practice の出典 URL を sources_cited に載せる
    sources = {s["id"]: s["url"] for s in doc["sources"]}
    involved = [v["practice_id"] for v in violations] + [r["practice_id"] for r in llm_results if not r["passed"]]
    urls = []
    for pid in involved:
        for ev in practices.get(pid, {}).get("evidence", []):
            url = sources.get(ev["source_id"])
            if url and url not in urls:
                urls.append(url)

    reviewed_at = args.reviewed_at or datetime.now().astimezone().isoformat(timespec="seconds")
    record = gate.build_record(args.deck, axes, result, urls, auto.get("limitations", []), reviewed_at)
    print(json.dumps(record, ensure_ascii=False, indent=2))
    if args.write:
        p = subprocess.run([sys.executable, os.path.join(SHARED, "append_review_record.py"), "-"],
                           input=json.dumps(record, ensure_ascii=False), capture_output=True, text=True,
                           encoding="utf-8")
        sys.stderr.write(p.stderr)
        if p.returncode != 0:
            return 2
        print("saved: " + p.stdout.strip(), file=sys.stderr)
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
