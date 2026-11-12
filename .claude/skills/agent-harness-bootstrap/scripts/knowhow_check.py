#!/usr/bin/env python3
"""knowhow_check.py — ノウハウの台帳（.claude/knowhow.json）が、反映先の file に実際に入っているかを確かめる。

台帳の 1 件: id（KH-0001 の形）/ added（YYYY-MM-DD）/ source（user|review|incident）/ statement / why /
  reflect_to [{"path", "must_contain"?}] / status（queued|reflected|retired）/ retired_reason（retired の時は必須）。
  形の正本は同じディレクトリの knowhow.schema.json。相対パスは .claude/ の親（repo のルート）が基準。

アンカー: 反映先の各 file に ID を置く。数えるのは md 等の `<!-- KH-0001 -->` と、json の "knowhow" 配列の値だけ。
  本文中の裸の KH-0001 や、書式の例示 KH-xxxx はアンカーに数えない。

使い方:
  knowhow_check.py [--config <knowhow.json>]
      retired 以外の全件について次を確かめる。1 つでも欠ければ exit 1。
      - queued が残っていない（反映を済ませて reflected にしてから commit する）
      - reflect_to が空でない・各 path が repo の中（.. や絶対パスで外へ出ない）にあり、存在し、ID のアンカーを含む
        （must_contain があればその語句も含む）
      - 反映先の file にあるアンカーの ID が台帳にあり、その ID の reflect_to にその file が入っている（双方向）
  knowhow_check.py --new-since <git ref> [--config ...]
      Stop hook 用。<ref> の台帳と比べて、この作業で増えた queued（ref に無い・ref では queued でなかった）があれば exit 1。
      前からある queued は「前からある queued」の行で知らせるだけ（exit を変えない）。アンカーの検査はしない（commit gate の役目）。

終了コード: 0 合格 / 1 反映が欠けている・増えた queued がある / 2 台帳の形が不正・読めない・git を呼べない
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SCHEMA_ID = "knowhow/v1"
STATUSES = {"queued", "reflected", "retired"}
SOURCES = {"user", "review", "incident"}
_ID = re.compile(r"^KH-\d{4}$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_MD_ANCHOR = re.compile(r"<!--\s*(KH-\d{4})\s*-->")


class SchemaError(Exception):
    pass


def _find_config(given):
    if given:
        return Path(given).resolve()
    d = Path.cwd().resolve()
    for p in [d, *d.parents]:
        c = p / ".claude" / "knowhow.json"
        if c.is_file():
            return c
    raise SchemaError("台帳 .claude/knowhow.json が見つからない（--config で指定する）")


def validate(doc):
    """台帳の形を確かめて entries を返す。不正なら SchemaError。"""
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA_ID:
        raise SchemaError(f"schema が {SCHEMA_ID} でない")
    ents = doc.get("entries")
    if not isinstance(ents, list):
        raise SchemaError("entries が配列でない")
    seen = set()
    for i, e in enumerate(ents):
        where = f"entries[{i}]"
        if not isinstance(e, dict):
            raise SchemaError(f"{where} が object でない")
        eid = e.get("id")
        if not isinstance(eid, str) or not _ID.match(eid):
            raise SchemaError(f"{where} の id が KH-0000 の形でない: {eid}")
        where = eid
        if eid in seen:
            raise SchemaError(f"id が重複している: {eid}")
        seen.add(eid)
        if not isinstance(e.get("added"), str) or not _DATE.match(e["added"]):
            raise SchemaError(f"{where} の added が YYYY-MM-DD でない")
        if e.get("source") not in SOURCES:
            raise SchemaError(f"{where} の source が {sorted(SOURCES)} のどれでもない: {e.get('source')}")
        for k in ("statement", "why"):
            if not isinstance(e.get(k), str) or not e[k].strip():
                raise SchemaError(f"{where} の {k} が空か文字列でない")
        if e.get("status") not in STATUSES:
            raise SchemaError(f"{where} の status が {sorted(STATUSES)} のどれでもない: {e.get('status')}")
        rt = e.get("reflect_to")
        if not isinstance(rt, list):
            raise SchemaError(f"{where} の reflect_to が配列でない")
        for j, r in enumerate(rt):
            if not isinstance(r, dict) or not isinstance(r.get("path"), str) or not r["path"].strip():
                raise SchemaError(f"{where} の reflect_to[{j}] に path（文字列）が無い")
            if "must_contain" in r and not isinstance(r["must_contain"], str):
                raise SchemaError(f"{where} の reflect_to[{j}].must_contain が文字列でない")
        if "retired_reason" not in e:
            raise SchemaError(f"{where} に retired_reason が無い（retired でなければ null を書く）")
        rr = e["retired_reason"]
        if e["status"] == "retired":
            if not isinstance(rr, str) or not rr.strip():
                raise SchemaError(f"{where} は retired なのに retired_reason が無い")
        elif rr is not None and not isinstance(rr, str):
            raise SchemaError(f"{where} の retired_reason が文字列か null でない")
    return ents


def load(path):
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as ex:
        raise SchemaError(f"台帳を読めない: {path}（{ex}）")
    return validate(doc)


def _inside(base, rel):
    if Path(rel).is_absolute() or rel.startswith(("/", "\\")):
        return None
    p = (base / rel).resolve()
    try:
        p.relative_to(base)
    except ValueError:
        return None
    return p


def _json_anchors(node, out):
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "knowhow" and isinstance(v, list):
                out.update(x for x in v if isinstance(x, str) and _ID.match(x))
            else:
                _json_anchors(v, out)
    elif isinstance(node, list):
        for v in node:
            _json_anchors(v, out)


def anchors_of(path, text):
    if path.suffix.casefold() == ".json":
        try:
            doc = json.loads(text)
        except ValueError:
            return None
        out = set()
        _json_anchors(doc, out)
        return out
    return set(_MD_ANCHOR.findall(text))


def check_all(base, ents):
    problems = []
    ids = {e["id"] for e in ents}
    listed = {}  # 正規化した file パス -> その file を reflect_to に持つ ID
    files = {}   # 正規化した file パス -> (Path, 表示名)
    for e in ents:
        if e["status"] == "retired":
            continue
        if e["status"] == "queued":
            problems.append(f"queued が残っている: {e['id']}（反映先に書いてアンカーを置き、status を reflected にする）")
        if not e["reflect_to"]:
            problems.append(f"reflect_to が空: {e['id']}")
        for r in e["reflect_to"]:
            rel = r["path"]
            p = _inside(base, rel)
            if p is None:
                problems.append(f"reflect_to が repo の外を指す: {e['id']} → {rel}")
                continue
            if not p.is_file():
                problems.append(f"反映先の file が無い: {e['id']} → {rel}")
                continue
            key = str(p).casefold()
            files[key] = (p, rel)
            listed.setdefault(key, set()).add(e["id"])
            try:
                text = p.read_text(encoding="utf-8-sig")
            except (OSError, UnicodeDecodeError) as ex:
                problems.append(f"反映先を読めない: {e['id']} → {rel}（{ex}）")
                continue
            anc = anchors_of(p, text)
            if anc is None:
                problems.append(f"反映先の JSON が壊れている: {rel}")
                continue
            if e["id"] not in anc:
                kind = '"knowhow" 配列の値' if p.suffix.casefold() == ".json" else f"<!-- {e['id']} -->"
                problems.append(f"アンカーが無い: {e['id']} → {rel}（{kind} を置く）")
            mc = r.get("must_contain")
            if mc and mc not in text:
                problems.append(f"must_contain の語句が無い: {e['id']} → {rel}（{mc}）")
    retired = {e["id"] for e in ents if e["status"] == "retired"}
    for key, (p, rel) in sorted(files.items()):
        try:
            anc = anchors_of(p, p.read_text(encoding="utf-8-sig")) or set()
        except (OSError, UnicodeDecodeError):
            continue
        for a in sorted(anc):
            if a not in ids:
                problems.append(f"孤立したアンカー（台帳に無い ID）: {a} in {rel}")
            elif a not in retired and a not in listed.get(key, set()):
                problems.append(f"アンカーの file が台帳の reflect_to に無い: {a} in {rel}")
    return problems


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def check_new_since(cfg_path, ents, ref):
    try:
        top = _git(cfg_path.parent, "rev-parse", "--show-toplevel")
    except OSError as ex:
        raise SchemaError(f"git を呼べない: {ex}")
    if top.returncode != 0:
        raise SchemaError(f"git の管理下ではない: {cfg_path}")
    rel = cfg_path.resolve().relative_to(Path(top.stdout.strip()).resolve()).as_posix()
    old = _git(top.stdout.strip(), "show", f"{ref}:{rel}")
    old_queued = set()
    if old.returncode == 0:
        try:
            old_queued = {e["id"] for e in validate(json.loads(old.stdout)) if e["status"] == "queued"}
        except (ValueError, SchemaError):
            old_queued = set()  # 前の版が壊れていれば、全部をこの作業のものとして扱う
    queued = [e["id"] for e in ents if e["status"] == "queued"]
    new = [i for i in queued if i not in old_queued]
    before = [i for i in queued if i in old_queued]
    if before:
        print(f"前からある queued: {len(before)} 件（{', '.join(before)}）")
    if new:
        print(f"この作業で増えた queued: {', '.join(new)}（反映先に書いてアンカーを置き、status を reflected にする）")
        return 1
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="knowhow.json の反映を確かめる")
    ap.add_argument("--config")
    ap.add_argument("--new-since")
    a = ap.parse_args(argv)
    try:
        cfg = _find_config(a.config)
        ents = load(cfg)
        if a.new_since:
            return check_new_since(cfg, ents, a.new_since)
        problems = check_all(cfg.parent.parent.resolve(), ents)
    except SchemaError as ex:
        print(f"台帳が不正: {ex}", file=sys.stderr)
        return 2
    for p in problems:
        print(p)
    if problems:
        return 1
    n = {s: sum(1 for e in ents if e["status"] == s) for s in sorted(STATUSES)}
    print(f"knowhow: OK（{len(ents)} 件。reflected {n['reflected']} / retired {n['retired']}）")
    return 0


if __name__ == "__main__":
    for st in (sys.stdout, sys.stderr):
        try:
            st.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
