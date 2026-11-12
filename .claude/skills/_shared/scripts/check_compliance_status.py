"""公式原則キャッシュ（anthropic-best-practices.json）と採用状況（compliance-status.json）の整合を機械検査する。

違反コード:
  V1 cache の principle id と status の principles のキーが全単射でない
  V2 status の値が enum 外
  V3 evidence のパスがリポジトリに実在しない、またはリポジトリ相対パスでない（絶対パス・.. でルート外を指す）
  V4 backlog / partial なのに cr が無い、または cr が findings に無い
  V5 findings の id 重複、severity / status が enum 外
  V6 cache の principle が必須キーを欠く、source が sources に無い、または id が重複している
  V7 findings の requests（利用者の要望の記録）が [{"at": 文字列, "text": 文字列}] でない、
     または related（起票時に確かめた関連 finding の id）が文字列の配列でない。どちらも任意のキー
  V8 棚卸しの欄（任意）の不正: priority が P1/P2/P3 でない、reviewed が YYYY-MM-DD でない、
     premise が [{"path": リポジトリ相対か ~/ 始まり, "contains"?: 文字列}] でない、status obsolete なのに
     resolution が空、superseded_by が obsolete 以外に付いている・実在しない・自分、principle の cr が
     obsolete の finding を指している（principle の status を問わない）、enums.finding_status /
     enums.finding_priority が定数と食い違う（enums かそのキーが無ければ比べない）
違反が 1 件でもあれば exit 1、無ければ exit 0。

使い方:
  python .claude/skills/_shared/scripts/check_compliance_status.py \
      [--cache <anthropic-best-practices.json>] [--status <compliance-status.json>] [--root <repo root>]
"""
import argparse
import json
import os
import re
from datetime import date
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))

PRINCIPLE_STATUS = {"adopted", "partial", "not-applicable", "backlog"}
NEEDS_CR = {"partial", "backlog"}
FINDING_SEVERITY = {"High", "Medium", "Low"}
FINDING_STATUS = {"open", "backlog", "done", "false-positive", "obsolete"}
FINDING_PRIORITY = {"P1", "P2", "P3"}
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
REQUIRED_KEYS = ("id", "category", "source", "section", "statement", "quote", "check", "verified", "used_by")


def check(cache, status, root):
    v = []
    sources = cache.get("sources") or {}
    principles = cache.get("principles") or []
    seen_p = set()
    for p in principles:
        pid = p.get("id", "<id なし>")
        if pid in seen_p:
            v.append(f"V6 principle id {pid} が重複している")
        seen_p.add(pid)
        for k in REQUIRED_KEYS:
            if k not in p:
                v.append(f"V6 principle {pid} に必須キー {k} が無い")
        if "source" in p and p["source"] not in sources:
            v.append(f"V6 principle {pid} の source {p['source']} が sources に無い")

    cache_ids = {p.get("id") for p in principles if p.get("id")}
    st = status.get("principles") or {}
    for pid in sorted(cache_ids - set(st)):
        v.append(f"V1 cache の principle {pid} が status に無い")
    for pid in sorted(set(st) - cache_ids):
        v.append(f"V1 status の {pid} が cache に無い")

    findings = status.get("findings") or []
    seen, finding_ids = set(), set()
    for f in findings:
        fid = f.get("id")
        if fid in seen:
            v.append(f"V5 findings の id {fid} が重複している")
        seen.add(fid)
        finding_ids.add(fid)
        if f.get("severity") not in FINDING_SEVERITY:
            v.append(f"V5 finding {fid} の severity {f.get('severity')} が enum 外（{sorted(FINDING_SEVERITY)}）")
        if f.get("status") not in FINDING_STATUS:
            v.append(f"V5 finding {fid} の status {f.get('status')} が enum 外（{sorted(FINDING_STATUS)}）")
        if "requests" in f:
            reqs = f["requests"]
            if not isinstance(reqs, list) or not all(
                    isinstance(r, dict) and isinstance(r.get("at"), str) and isinstance(r.get("text"), str) for r in reqs):
                v.append(f"V7 finding {fid} の requests が [{{\"at\": 文字列, \"text\": 文字列}}] の形でない")
        if "related" in f:
            rel = f["related"]
            if not isinstance(rel, list) or not all(isinstance(x, str) for x in rel):
                v.append(f"V7 finding {fid} の related が文字列の配列でない")

    by_id = {f.get("id"): f for f in findings}
    for f in findings:
        v.extend(_check_triage_fields(f, finding_ids, root))
    enums = status.get("enums")
    if isinstance(enums, dict):
        for key, const in (("finding_status", FINDING_STATUS), ("finding_priority", FINDING_PRIORITY)):
            if key in enums and (not isinstance(enums[key], list) or set(enums[key]) != const):
                v.append(f"V8 enums.{key} {enums[key]} が検査の定数 {sorted(const)} と食い違う")

    for pid, e in sorted(st.items()):
        s = e.get("status")
        cr_f = by_id.get(e["cr"]) if isinstance(e.get("cr"), str) else None
        if cr_f is not None and cr_f.get("status") == "obsolete":
            v.append(f"V8 {pid} の cr {e.get('cr')} が obsolete の finding を指している（principle の status と cr を見直す）")
        if s not in PRINCIPLE_STATUS:
            v.append(f"V2 {pid} の status {s} が enum 外（{sorted(PRINCIPLE_STATUS)}）")
        for path in e.get("evidence") or []:
            full = os.path.normpath(os.path.join(root, path))
            try:
                inside = os.path.commonpath([os.path.abspath(root), os.path.abspath(full)]) == os.path.abspath(root)
            except ValueError:  # Windows で別ドライブのパス
                inside = False
            if os.path.isabs(path) or not inside:
                v.append(f"V3 {pid} の evidence {path} はリポジトリ相対パスでない")
            elif not os.path.exists(full):
                v.append(f"V3 {pid} の evidence {path} が実在しない")
        cr = e.get("cr")
        if s in NEEDS_CR and not cr:
            v.append(f"V4 {pid} は {s} なのに cr が無い")
        if cr and cr not in finding_ids:
            v.append(f"V4 {pid} の cr {cr} が findings に無い")
    return v


def _inside(root, path):
    full = os.path.normpath(os.path.join(root, path))
    try:
        return os.path.commonpath([os.path.abspath(root), os.path.abspath(full)]) == os.path.abspath(root)
    except ValueError:  # Windows で別ドライブのパス
        return False


def _premise_path_ok(root, path):
    if not isinstance(path, str) or not path:
        return False
    if path.startswith("~/"):
        return True
    if os.path.isabs(path) or path.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", path):
        return False
    return _inside(root, path)


def _check_triage_fields(f, finding_ids, root):
    v = []
    fid = f.get("id")
    if "priority" in f and f["priority"] not in FINDING_PRIORITY:
        v.append(f"V8 finding {fid} の priority {f['priority']} が enum 外（{sorted(FINDING_PRIORITY)}）")
    if "reviewed" in f:
        r = f["reviewed"]
        ok = isinstance(r, str) and _DATE.fullmatch(r) is not None
        if ok:
            try:
                date.fromisoformat(r)
            except ValueError:
                ok = False
        if not ok:
            v.append(f"V8 finding {fid} の reviewed {r} が YYYY-MM-DD の日付でない")
    if "premise" in f:
        pr = f["premise"]
        good = isinstance(pr, list) and all(
            isinstance(x, dict) and _premise_path_ok(root, x.get("path"))
            and ("contains" not in x or isinstance(x["contains"], str)) for x in pr)
        if not good:
            v.append(f"V8 finding {fid} の premise が [{{\"path\": リポジトリ相対か ~/ 始まり, \"contains\"?: 文字列}}] の形でない")
    if f.get("status") == "obsolete":
        res = f.get("resolution")
        if not isinstance(res, str) or not res.strip():
            v.append(f"V8 finding {fid} は obsolete なのに resolution（何が変わって不要になったか）が無い")
    if "superseded_by" in f:
        sb = f["superseded_by"]
        if f.get("status") != "obsolete":
            v.append(f"V8 finding {fid} の superseded_by は status が obsolete の時だけ書ける")
        elif sb == fid or sb not in finding_ids:
            v.append(f"V8 finding {fid} の superseded_by {sb} が自分か、findings に無い")
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=os.path.join(DEFAULT_ROOT, ".claude", "skills", "_shared", "anthropic-best-practices.json"))
    ap.add_argument("--status", default=os.path.join(DEFAULT_ROOT, ".claude", "skills", "_shared", "compliance-status.json"))
    ap.add_argument("--root", default=DEFAULT_ROOT)
    a = ap.parse_args()
    try:
        cache = json.load(open(a.cache, encoding="utf-8"))
        status = json.load(open(a.status, encoding="utf-8"))
    except (OSError, ValueError) as ex:
        print(f"ERROR 入力を読めない: {ex}")
        return 2
    v = check(cache, status, a.root)
    for line in v:
        print(line)
    n = len(cache.get("principles") or [])
    print(f"SUMMARY principles={n} findings={len(status.get('findings') or [])} violations={len(v)}")
    return 1 if v else 0


if __name__ == "__main__":
    sys.exit(main())
