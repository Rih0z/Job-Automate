#!/usr/bin/env python3
"""list_review_records.py — .claude/review-history/ 配下の review-record/v1 を横断検索する。

使い方:
  python list_review_records.py --target "<対象を特定する文字列(タイトル/パス/URLの部分一致)>" [--skill <skill-name>]

--skill を省略すると全 skill 配下を横断検索する(別のレビュー系skillが過去に同じ対象を
レビューした結果も拾える)。target.description / target.path_or_url の部分一致(大小無視)で
フィルタし、reviewed_at 降順で一覧を出す。

出力(該当なしなら "NO_PRIOR_RECORDS" のみ、終了コード0):
  <path>\t<skill>\t<reviewed_at>\t<verdict>\t<score or ->\t<summaryの先頭80文字>

依存: Python標準ライブラリのみ。
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Optional

# Windows のコンソールコードページ(cp1252等)だと日本語 print() で UnicodeEncodeError になるため強制 UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parents[4]
HISTORY_ROOT = REPO_ROOT / ".claude" / "review-history"


def iter_records(skill: Optional[str]):
    if not HISTORY_ROOT.exists():
        return
    dirs = [HISTORY_ROOT / skill] if skill else [d for d in HISTORY_ROOT.iterdir() if d.is_dir()]
    for d in dirs:
        if not d.exists():
            continue
        for f in sorted(d.glob("*.json")):
            try:
                yield f, json.loads(f.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue


def matches(record: dict, target_query: str) -> bool:
    q = target_query.lower()
    target = record.get("target") or {}
    desc = (target.get("description") or "").lower()
    path_or_url = (target.get("path_or_url") or "").lower()
    return q in desc or q in path_or_url


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--skill", default=None)
    args = parser.parse_args()

    hits = []
    for path, record in iter_records(args.skill):
        if matches(record, args.target):
            hits.append((path, record))

    hits.sort(key=lambda pr: pr[1].get("reviewed_at", ""), reverse=True)

    if not hits:
        print("NO_PRIOR_RECORDS")
        return 0

    for path, record in hits:
        summary = (record.get("summary") or "")[:80].replace("\n", " ")
        score = record.get("score")
        score_str = str(score) if score is not None else "-"
        print(
            f"{path}\t{record.get('skill', '?')}\t{record.get('reviewed_at', '?')}\t"
            f"{record.get('verdict', '?')}\t{score_str}\t{summary}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
