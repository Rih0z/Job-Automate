"""公式原則キャッシュ（anthropic-best-practices.json）と採用状況（compliance-status.json）の整合を機械検査する。

違反コード:
  V1 cache の principle id と status の principles のキーが全単射でない
  V2 status の値が enum 外
  V3 evidence のパスがリポジトリに実在しない、またはリポジトリ相対パスでない（絶対パス・.. でルート外を指す）
  V4 backlog / partial なのに cr が無い、または cr が findings に無い
  V5 findings の id 重複、severity / status が enum 外
  V6 cache の principle が必須キーを欠く、source が sources に無い、または id が重複している
違反が 1 件でもあれば exit 1、無ければ exit 0。

使い方:
  python .claude/skills/_shared/scripts/check_compliance_status.py \
      [--cache <anthropic-best-practices.json>] [--status <compliance-status.json>] [--root <repo root>]
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))

PRINCIPLE_STATUS = {"adopted", "partial", "not-applicable", "backlog"}
NEEDS_CR = {"partial", "backlog"}
FINDING_SEVERITY = {"High", "Medium", "Low"}
FINDING_STATUS = {"open", "backlog", "done", "false-positive"}
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

    for pid, e in sorted(st.items()):
        s = e.get("status")
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
