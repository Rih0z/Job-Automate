#!/usr/bin/env python3
"""append_review_record.py — review-record/v1 を検証し .claude/review-history/ へ追記保存する。

使い方:
  python append_review_record.py <input.json>   # ファイルから読む
  python append_review_record.py -               # stdin から読む(JSON文字列をpipe)

検証NG(必須キー欠落・型不一致)の場合は書き込まず、非ゼロ終了 + 欠落/不正フィールド一覧を stderr に出す。
検証OKの場合のみ .claude/review-history/<skill>/<YYYYMMDD-HHMMSS>__<target-slug>.json に書き込み、
書き込み先の絶対パスを stdout に1行で出す(呼び出し元スキルはこの標準出力をもって永続化完了とみなす)。

依存: Python標準ライブラリのみ(jsonschema等の外部パッケージを追加しない)。
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Windows のコンソールコードページ(cp1252等)だと日本語 print() で UnicodeEncodeError になるため強制 UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

SCHEMA_CONST = "review-record/v1"
REQUIRED_TOP = ["schema", "skill", "reviewed_at", "target", "verdict", "summary"]
REPO_ROOT = Path(__file__).resolve().parents[4]  # .claude/skills/_shared/scripts/<this file> -> repo root
HISTORY_ROOT = REPO_ROOT / ".claude" / "review-history"


def load_input(arg: str) -> str:
    if arg == "-":
        return sys.stdin.read()
    return Path(arg).read_text(encoding="utf-8")


def validate(record: dict) -> list:
    errors = []
    for key in REQUIRED_TOP:
        if key not in record or record[key] in (None, ""):
            errors.append(f"missing required field: {key}")

    if record.get("schema") not in (None, SCHEMA_CONST):
        errors.append(f"schema must be '{SCHEMA_CONST}', got: {record.get('schema')!r}")

    skill = record.get("skill")
    if skill is not None and not isinstance(skill, str):
        errors.append("skill must be a string")

    target = record.get("target")
    if target is not None:
        if not isinstance(target, dict):
            errors.append("target must be an object")
        else:
            if "description" not in target or not target.get("description"):
                errors.append("target.description is required and must be non-empty")
            if not isinstance(target.get("description"), (str, type(None))):
                errors.append("target.description must be a string")
            path_or_url = target.get("path_or_url")
            if path_or_url is not None and not isinstance(path_or_url, str):
                errors.append("target.path_or_url must be a string or null")

    reviewed_at = record.get("reviewed_at")
    if reviewed_at is not None:
        try:
            datetime.fromisoformat(str(reviewed_at).replace("Z", "+00:00"))
        except ValueError:
            errors.append(f"reviewed_at must be ISO8601, got: {reviewed_at!r}")

    verdict = record.get("verdict")
    if verdict is not None and not isinstance(verdict, str):
        errors.append("verdict must be a string")

    summary = record.get("summary")
    if summary is not None and not isinstance(summary, str):
        errors.append("summary must be a string")

    score = record.get("score")
    if score is not None and (isinstance(score, bool) or not isinstance(score, (int, float))):
        errors.append("score must be a number or null")

    for str_array_field in ("sources_cited", "prior_records_referenced"):
        if str_array_field in record and isinstance(record[str_array_field], list):
            for i, v in enumerate(record[str_array_field]):
                if not isinstance(v, str):
                    errors.append(f"{str_array_field}[{i}] must be a string")
        elif str_array_field in record and not isinstance(record[str_array_field], list):
            errors.append(f"{str_array_field} must be an array if present")

    if "criteria" in record and not isinstance(record["criteria"], list):
        errors.append("criteria must be an array if present")
    elif "criteria" in record and isinstance(record["criteria"], list):
        for i, c in enumerate(record["criteria"]):
            if not isinstance(c, dict):
                errors.append(f"criteria[{i}] must be an object")
                continue
            if "id" not in c or not c.get("id"):
                errors.append(f"criteria[{i}].id is required")
            if not isinstance(c.get("id"), (str, type(None))):
                errors.append(f"criteria[{i}].id must be a string")
            if "result" not in c or c.get("result") in (None, ""):
                errors.append(f"criteria[{i}].result is required")
            source_urls = c.get("source_urls")
            if source_urls is not None:
                if not isinstance(source_urls, list):
                    errors.append(f"criteria[{i}].source_urls must be an array if present")
                else:
                    for j, u in enumerate(source_urls):
                        if not isinstance(u, str):
                            errors.append(f"criteria[{i}].source_urls[{j}] must be a string")

    return errors


def slugify(text: str, max_len: int = 60) -> str:
    slug = re.sub(r"[^a-zA-Z0-9\-]+", "-", text.strip()).strip("-").lower()
    slug = re.sub(r"-{2,}", "-", slug)
    return (slug or "untitled")[:max_len]


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: append_review_record.py <input.json|->", file=sys.stderr)
        return 2

    raw = load_input(sys.argv[1])
    try:
        record = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"INVALID_JSON: {e}", file=sys.stderr)
        return 1

    errors = validate(record)
    if errors:
        print("REJECTED: review-record/v1 validation failed:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    record.setdefault("schema", SCHEMA_CONST)
    record.setdefault("criteria", [])
    record.setdefault("sources_cited", [])
    record.setdefault("prior_records_referenced", [])
    record.setdefault("score", None)

    skill = record["skill"]
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    slug = slugify(record["target"].get("description") or record["target"].get("path_or_url") or "target")
    out_dir = HISTORY_ROOT / skill
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{ts}__{slug}.json"
    out_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(str(out_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
