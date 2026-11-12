#!/usr/bin/env python3
"""issue_tracker.py — 起票の前に関連する issue を探し、要望を記録し、重複を統合し、新規の起票に「関連:」欄があるかを確かめる。

設定は .claude/issue-tracker.json（--config で指定。無ければ cwd から上へ探す）。相対パスは .claude/ の親が基準。
source は 2 種類:
  md_dirs       : <root>/<状態>/*.md を issue とみなす（active / closed / merged_dir の直下だけ。exclude は除く）
  json_findings : JSON の配列（array）の各要素を issue とみなす（id / title / status のキー名を指定。closed_values は終わったもの）

使い方:
  related --text "<題名や要約>" [--limit 8] [--include-closed] [--deadline 10]
      入力を ASCII 語と日本語の 2-gram に分け、題名に含まれる割合 0.7 と本文先頭 8KB に含まれる割合 0.3 で並べる。
      出力は「score  state  path  title」。exit は常に 0（判断材料で、gate しない）。closed は --include-closed の時だけ。
      UTF-8 で読めない file は飛ばして警告を出す。--deadline 秒を超えたら途中までの結果と警告を出す。
  request <issue のパス | finding の id> --text "<原文>" [--now ISO]
      md は「## 利用者の要望」節（無ければ末尾に作る）へ「- <日時> <原文>」を足す。json は requests: [{at, text}] に足す。
      同じ原文が既にあれば足さずに already を出す。BOM と改行（CRLF）は保つ。
  merge <src のパス> --into <dst のパス>
      md_dirs だけ。dst に「## 統合: <src の題名>」節を足し、src の冒頭に「統合先: <dst>」を書き、状態欄（status_line）を
      merged_state にして merged_dir へ移す。git で追跡していれば rename を stage する。索引（index_files）と、src を指す
      handoff の候補を一覧に出す（書き換えない）。拒否（exit 2・何も変えない）: src と dst が同じ / dst が closed・merged にある /
      merged_dir に同名がある / merged_dir が無い source / json_findings。
  check-new [--base <git ref>]
      git の index で新しく足された issue に「関連:」欄（related_field）があるかを見る。md は追加（A）だけを拾い、rename・
      状態の移動・base の同じ source の別の状態に同じ file 名があるものは新規に数えない。json は base と index の id の差で
      増えた要素に related キー（list。空なら確認済み）があるかを見る。欠けていれば exit 1 と一覧。

  triage [--now YYYY-MM-DD] [--stale-days 30] [--dup-threshold 0.5] [--json]
      active な issue の棚卸しの候補を出す（読み取り専用。exit は常に 0、引数・設定の不正だけ 2）。節は
      優先度順（priority → severity → 起票日 → id の自然順）/ 前提が崩れた候補（premise のファイル・文言が無い、
      本文の backtick のパスが無い）/ 確認が古い（reviewed、無ければ起票日から stale-days 日を超えた）/
      欄の欠け（priority・関連）/ 重複の候補（題名の token の Jaccard 係数が閾値以上の組）。
      起票日の欄名は source の created（既定 created）。md は frontmatter の行の値（ # 以降と引用符を外す）を読み、
      premise は json だけ。判定はしない（終端・priority・reviewed の更新はエージェントか人が行う）。

終了コード: 0 正常 / 1 check-new で欠けがある / 2 引数・設定・対象が不正（何も変えない。例外は merge の「統合済みだが統合元が残った」）
"""
import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import date, datetime
from pathlib import Path, PurePosixPath

# 本文は先頭 8KB だけを related の得点に使う。題名と冒頭の症状で近さは決まり、長い記録や出力の貼り付けで
# 語が増えて無関係な issue の得点が上がるのを抑えるため。
BODY_BYTES = 8 * 1024
# related の時間上限（秒）。commit 前の hook（1 検査 20 秒）の中でも使われるので、それより短くする。
DEFAULT_DEADLINE = 10.0
REQUEST_HEADING = "## 利用者の要望"
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
_ASCII_WORD = re.compile(r"[a-z0-9_]+")
_JA_RUN = re.compile(r"[぀-ヿ㐀-䶿一-鿿豈-﫿ｦ-ﾟ々〆ー]+")
_HEADING = re.compile(r"^# (.+)$", re.M)
# 「関連:」の値として認めるもの: パスに見える語（.md で終わる・/ を含む）か id（CR-12・#12 の形）
_REF_VALUE = re.compile(r"\S+\.md\b|\S/\S|\b[A-Z][A-Z0-9]*-\d+\b|#\d+")
_FM_TITLE = re.compile(r"^title:\s*(.+)$", re.M)
HANDOFF_FIELDS = [re.compile(r"最新\s*handoff[^:：\n]*[:：]\s*(.+)$", re.M | re.I),
                  re.compile(r"^latest_handoff:\s*(.+)$", re.M)]


class CliError(Exception):
    def __init__(self, code, msg):
        super().__init__(msg)
        self.code = code


def warn(msg):
    print(f"警告: {msg}", file=sys.stderr)


# ---------- 設定 ----------

def _find_config(given):
    if given:
        return Path(given).resolve()
    d = Path.cwd().resolve()
    for p in [d, *d.parents]:
        c = p / ".claude" / "issue-tracker.json"
        if c.is_file():
            return c
    raise CliError(2, "設定 .claude/issue-tracker.json が見つからない（--config で指定する）")


def _strs(v):
    return isinstance(v, list) and all(isinstance(x, str) and x for x in v)


def load_config(given):
    cp = _find_config(given)
    try:
        cfg = json.loads(cp.read_text(encoding="utf-8"))
    except (OSError, ValueError) as ex:
        raise CliError(2, f"設定を読めない: {cp}（{ex}）")
    if not isinstance(cfg, dict) or not isinstance(cfg.get("sources"), list) or not cfg["sources"]:
        raise CliError(2, f"設定の sources が空でない配列ではない: {cp}")
    base = cp.parent.parent
    for i, s in enumerate(cfg["sources"]):
        where = f"sources[{i}]"
        if not isinstance(s, dict):
            raise CliError(2, f"設定の {where} が object でない")
        t = s.get("type")
        if t == "md_dirs":
            if not isinstance(s.get("root"), str) or not _strs(s.get("active")) or not _strs(s.get("closed")):
                raise CliError(2, f"設定の {where}（md_dirs）は root（文字列）と active・closed（文字列の配列）が要る")
            if "merged_dir" in s and not (isinstance(s["merged_dir"], str) and s["merged_dir"]):
                raise CliError(2, f"設定の {where} の merged_dir が文字列でない")
            sl = s.get("status_line")
            if sl is not None:
                if not (isinstance(sl, dict) and isinstance(sl.get("regex"), str) and isinstance(sl.get("template"), str)):
                    raise CliError(2, f"設定の {where} の status_line は regex と template（文字列）が要る")
                try:
                    re.compile(sl["regex"], re.M)
                except re.error as ex:
                    raise CliError(2, f"設定の {where} の status_line.regex が不正: {ex}")
            for k in ("exclude", "index_files"):
                if k in s and not (isinstance(s[k], list) and all(isinstance(x, str) for x in s[k])):
                    raise CliError(2, f"設定の {where} の {k} が文字列の配列でない")
            s["_root"] = (base / s["root"]).resolve()
        elif t == "json_findings":
            for k in ("path", "array", "id", "title", "status"):
                if not isinstance(s.get(k), str) or not s[k]:
                    raise CliError(2, f"設定の {where}（json_findings）に {k}（文字列）が要る")
            if not isinstance(s.get("closed_values"), list):
                raise CliError(2, f"設定の {where}（json_findings）に closed_values（配列）が要る")
            s["_path"] = (base / s["path"]).resolve()
        else:
            raise CliError(2, f"設定の {where} の type が md_dirs / json_findings でない: {t}")
    for i, s in enumerate(cfg["sources"]):
        if "created" in s and not (isinstance(s["created"], str) and s["created"]):
            raise CliError(2, f"設定の sources[{i}] の created が文字列でない")
    field = cfg.get("related_field", "関連:")
    if not isinstance(field, str) or not field.strip():
        raise CliError(2, "設定の related_field が文字列でない")
    cfg["related_field"] = field
    cfg["_base"] = base
    return cfg


def _rel(base, p):
    try:
        return Path(p).resolve().relative_to(base).as_posix()
    except ValueError:
        return str(p)


def _excluded(rel_to_root, patterns):
    parts = PurePosixPath(rel_to_root).parts
    name = parts[-1]
    for pat in patterns or []:
        if pat.endswith("/**"):
            prefix = pat[:-3]
            if any(fnmatch.fnmatchcase(x, prefix) for x in parts[:-1]) or fnmatch.fnmatchcase(rel_to_root, prefix + "/*"):
                return True
        elif fnmatch.fnmatchcase(name, pat) or fnmatch.fnmatchcase(rel_to_root, pat):
            return True
    return False


def _state_dirs(s):
    out = [(d, "active") for d in s["active"]] + [(d, "closed") for d in s["closed"]]
    if s.get("merged_dir") and s["merged_dir"] not in s["closed"]:
        out.append((s["merged_dir"], "merged"))
    return out


def _state_of_path(cfg, path):
    """md の issue のパスから (source, 状態ディレクトリ名, 種類) を返す。どの source にも無ければ (None, None, None)。"""
    r = Path(path).resolve()
    for s in cfg["sources"]:
        if s["type"] != "md_dirs":
            continue
        for d, kind in _state_dirs(s):
            if r.parent == (s["_root"] / d).resolve():
                if s.get("merged_dir") == d:
                    kind = "merged"
                return s, d, kind
    return None, None, None


# ---------- 読み取り ----------

def _decode(raw):
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw[3:].decode("utf-8") if bom else raw.decode("utf-8")
    crlf = "\r\n" in text
    return text.replace("\r\n", "\n"), bom, crlf


def _encode(text, bom, crlf):
    if crlf:
        text = text.replace("\n", "\r\n")
    return (b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8")


def _split_front(text):
    """frontmatter（--- で囲んだ先頭）があれば (frontmatter を含む先頭部分, 残り) を返す。"""
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[:end + 5], text[end + 5:]
    return "", text


def _decode_head(raw, truncated):
    """先頭 8KB を UTF-8 で読む。8KB の境目で多バイト文字が切れた時は、末尾の 1〜3 バイトを落として読み直す。"""
    for cut in (range(4) if truncated else range(1)):
        try:
            return (raw[:-cut] if cut else raw).decode("utf-8-sig")
        except UnicodeDecodeError:
            continue
    return None


def md_title(text, fallback):
    front, rest = _split_front(text)
    m = _FM_TITLE.search(front) if front else None
    if m:
        return m.group(1).strip().strip("'\"")
    m = _HEADING.search(rest)
    return m.group(1).strip() if m else fallback


def iter_issues(cfg, include_closed, deadline=None, counter=None):
    """(state, path 表示, title, body) を返す。deadline を過ぎたら止めて counter['timed_out'] を立てる。"""
    base = cfg["_base"]
    for s in cfg["sources"]:
        if s["type"] == "md_dirs":
            if not s["_root"].is_dir():
                warn(f"source の root が無いので飛ばす: {s['root']}")
                continue
            for d, kind in _state_dirs(s):
                if kind != "active" and not include_closed:
                    continue
                sd = s["_root"] / d
                if not sd.is_dir():
                    continue
                for p in sorted(sd.iterdir()):
                    if not p.is_file() or p.suffix.casefold() != ".md":
                        continue
                    if _excluded(f"{d}/{p.name}", s.get("exclude")):
                        continue
                    if deadline is not None and counter["n"] > 0 and time.monotonic() >= deadline:
                        counter["timed_out"] = True
                        return
                    counter["n"] += 1
                    try:
                        with p.open("rb") as f:
                            raw = f.read(BODY_BYTES)
                    except OSError as ex:
                        warn(f"読めないので飛ばす: {_rel(base, p)}（{ex}）")
                        continue
                    text = _decode_head(raw, len(raw) == BODY_BYTES)
                    if text is None:
                        warn(f"UTF-8 で読めないので飛ばす: {_rel(base, p)}")
                        continue
                    yield d, _rel(base, p), md_title(text, p.stem), text
        else:
            data = _load_json_source(s, warn_missing=True)
            if data is None:
                continue
            for item in data:
                if not isinstance(item, dict):
                    continue
                closed = item.get(s["status"]) in s["closed_values"]
                if closed and not include_closed:
                    continue
                counter["n"] += 1
                title = str(item.get(s["title"], ""))
                body = " ".join(str(v) for v in item.values() if isinstance(v, str))[:BODY_BYTES]
                yield (f"findings:{item.get(s['status'])}", f"{s['path']}#{item.get(s['id'])}", title, body)


def _load_json_source(s, warn_missing=False, text=None, strict=False):
    """JSON source の配列を返す。読めなければ、strict なら exit 2、そうでなければ警告して None。

    strict は台帳の形を確かめる場面（check-new・request）で使う。読めない台帳を飛ばして通すと、
    検査が黙って OK になるため。related・triage は一覧なので、読める source だけで続ける。
    """
    def bad(msg):
        if strict:
            raise CliError(2, f"{msg}（台帳を直してから再実行する）")
        warn(f"{msg}ので飛ばす")
        return None

    if text is not None:
        text = text[1:] if text.startswith("\ufeff") else text  # git show の出力は BOM を残す
    if text is None:
        if not s["_path"].is_file():
            if warn_missing:
                warn(f"source の path が無いので飛ばす: {s['path']}")
            return None
        try:
            text = s["_path"].read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError) as ex:
            return bad(f"source を読めない: {s['path']}（{ex}）")
    try:
        doc = json.loads(text)
    except ValueError as ex:
        return bad(f"source の JSON を読めない: {s['path']}（{ex}）")
    arr = doc.get(s["array"]) if isinstance(doc, dict) else None
    if not isinstance(arr, list):
        return bad(f"source に配列 {s['array']} が無い: {s['path']}")
    return arr


# ---------- related ----------

def tokens(text):
    t = text.casefold()
    out = set(w for w in _ASCII_WORD.findall(t) if len(w) >= 2)
    for run in _JA_RUN.findall(t):
        if len(run) == 1:
            continue
        out.update(run[i:i + 2] for i in range(len(run) - 1))
    return out


def cmd_related(a):
    cfg = load_config(a.config)
    q = tokens(a.text)
    if not q:
        print("候補なし（入力から語を取れない）")
        return 0
    counter = {"n": 0, "timed_out": False}
    deadline = time.monotonic() + max(a.deadline, 0)
    scored = []
    for state, path, title, body in iter_issues(cfg, a.include_closed, deadline, counter):
        tt = tokens(title)
        bl = body.casefold()
        tc = sum(1 for w in q if w in tt) / len(q)
        bc = sum(1 for w in q if w in bl) / len(q)
        score = 0.7 * tc + 0.3 * bc  # 題名を重く見る: 題名は 1 文の要約で、本文には周辺の語が多く混じる
        if score > 0:
            scored.append((score, state, path, title))
    if counter["timed_out"]:
        warn(f"時間上限（{a.deadline:g} 秒）に達したので、途中まで（{counter['n']} 件）の結果を出す")
    scored.sort(key=lambda x: (-x[0], x[2]))
    if not scored:
        print("候補なし")
    for score, state, path, title in scored[:a.limit]:
        print(f"{score:.2f}  {state}  {path}  {title}")
    return 0


# ---------- request ----------

def _find_finding(cfg, ident):
    for s in cfg["sources"]:
        if s["type"] != "json_findings" or not s["_path"].is_file():
            continue
        arr = _load_json_source(s, strict=True)
        for item in arr:
            if isinstance(item, dict) and str(item.get(s["id"])) == ident:
                return s
    return None


def _one_line(text):
    return " ".join(text.split())


def _request_md(path, text, now):
    raw = path.read_bytes()
    try:
        body, bom, crlf = _decode(raw)
    except UnicodeDecodeError:
        raise CliError(2, f"UTF-8 で読めない: {path}")
    lines = body.split("\n")
    start = next((i for i, l in enumerate(lines) if l.strip() == REQUEST_HEADING), None)
    entry = f"- {now} {text}"
    if start is None:
        if body and not body.endswith("\n"):
            body += "\n"
        if body and not body.endswith("\n\n"):
            body += "\n"
        body += f"{REQUEST_HEADING}\n\n{entry}\n"
    else:
        end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
        for l in lines[start + 1:end]:
            m = re.match(r"^- \S+ (.*)$", l)
            if m and m.group(1).strip() == text:
                return False
        ins = end
        while ins > start + 1 and lines[ins - 1].strip() == "":
            ins -= 1
        lines.insert(ins, entry)
        body = "\n".join(lines)
    _atomic_write(path, _encode(body, bom, crlf))
    return True


def _atomic_write(path, data):
    """一時ファイルに書いてから置き換える（途中で失敗しても元の file が壊れない）。"""
    fd, tmp = tempfile.mkstemp(prefix="." + path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def _rewrite_json(s, mutate):
    """JSON source を書き換える。先頭の BOM と改行（CRLF）の形は元のまま保つ。"""
    try:
        raw = s["_path"].read_bytes()
        bom = raw.startswith(b"\xef\xbb\xbf")
        text = raw[3:].decode("utf-8") if bom else raw.decode("utf-8")
        doc = json.loads(text)
        arr = doc[s["array"]]
    except (OSError, UnicodeDecodeError, ValueError, KeyError, TypeError) as ex:
        raise CliError(2, f"source を読めない: {s['path']}（{ex}）")
    mutate(arr)
    out = json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
    if "\r\n" in text:
        out = out.replace("\n", "\r\n")
    _atomic_write(s["_path"], (b"\xef\xbb\xbf" if bom else b"") + out.encode("utf-8"))


def cmd_request(a):
    cfg = load_config(a.config)
    text = _one_line(a.text)
    if not text:
        raise CliError(2, "--text が空")
    now = a.now or datetime.now().astimezone().isoformat(timespec="seconds")
    cand = Path(a.issue)
    cand = cand if cand.is_absolute() else Path.cwd() / cand
    if cand.is_file():
        s, d, kind = _state_of_path(cfg, cand)
        if s is None:
            raise CliError(2, f"どの source の状態ディレクトリにも無い: {a.issue}")
        added = _request_md(cand, text, now)
        shown = _rel(cfg["_base"], cand)
    else:
        s = _find_finding(cfg, a.issue)
        if s is None:
            raise CliError(2, f"issue のファイルも finding の id も見つからない: {a.issue}")
        state = {"added": False}

        def mutate(arr):
            for item in arr:
                if isinstance(item, dict) and str(item.get(s["id"])) == a.issue:
                    reqs = item.setdefault("requests", [])
                    if any(isinstance(r, dict) and r.get("text") == text for r in reqs):
                        return
                    reqs.append({"at": now, "text": text})
                    state["added"] = True
                    return
        _rewrite_json(s, mutate)
        added = state["added"]
        shown = f"{s['path']}#{a.issue}"
    print(("requested: " if added else "already: ") + shown)
    return 0


# ---------- merge ----------

def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def _git_tracked(path):
    try:
        p = _git(path.parent, "ls-files", "--error-unmatch", "--", path.name)
    except OSError:
        return None
    if p.returncode == 0:
        return True
    if p.returncode == 1:
        return False
    return None


def _stage_move(old, new):
    try:
        r1 = _git(old.parent, "rm", "--cached", "-q", "--", old.name)
        r2 = _git(new.parent, "add", "-f", "--", new.name)
    except OSError as ex:
        warn(f"git で stage できなかった: {ex}")
        return
    if r1.returncode or r2.returncode:
        try:
            _git(old.parent, "reset", "-q", "--", old.name)
            _git(new.parent, "reset", "-q", "--", new.name)
        except OSError:
            pass
        warn(f"git で stage できなかった（index は戻した）: {(r1.stderr + r2.stderr).strip()}")
        return
    print(f"staged: {old}")
    print(f"staged: {new}")


def _requests_block(text):
    lines = text.split("\n")
    start = next((i for i, l in enumerate(lines) if l.strip() == REQUEST_HEADING), None)
    if start is None:
        return []
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return [l for l in lines[start + 1:end] if l.startswith("- ")]


def _clean_value(v):
    v = v.strip()
    while len(v) >= 2 and (v[0], v[-1]) in {("`", "`"), ("<", ">"), ('"', '"'), ("'", "'")}:
        v = v[1:-1].strip()
    return v


def _handoff_config(base):
    """handoff-lifecycle.json から (handoffs_dir, handoff 欄の正規表現) を返す。release と同じ正本を使う。
    config が無ければ既定値。壊れている・正規表現が不正な時は警告を出して既定値を使う。"""
    cp = base / ".claude" / "handoff-lifecycle.json"
    hd, pats = base / ".tmp" / "handoffs", HANDOFF_FIELDS
    if not cp.is_file():
        return hd, pats
    try:
        cfg = json.loads(cp.read_text(encoding="utf-8-sig"))
        if isinstance(cfg.get("handoffs_dir"), str) and cfg["handoffs_dir"]:
            hd = base / cfg["handoffs_dir"]
        rel = cfg.get("release") or {}
        given = [re.compile(x, re.M | re.I) for x in rel.get("handoff_field_regex") or []]
        pats = given or HANDOFF_FIELDS
    except (OSError, ValueError, AttributeError, TypeError, re.error) as ex:
        warn(f"handoff-lifecycle.json を読めないので既定の置き場と正規表現を使う（{ex}）")
    return hd, pats


def _handoff_candidates(base, src_path, src_text):
    out = []
    hd, pats = _handoff_config(base)
    for pat in pats:
        for m in pat.finditer(src_text):
            out.append(_clean_value(m.group(1)))
    if hd.is_dir():
        for p in sorted(hd.glob("*.md")):
            try:
                # frontmatter は先頭にあり、60 行あれば足りる（本文全体は読まない）
                head = p.read_text(encoding="utf-8-sig", errors="replace").split("\n")[:60]
            except OSError:
                continue
            if not head or head[0].strip() != "---":
                continue
            for l in head[1:]:
                if l.strip() == "---":
                    break
                m = re.match(r"^issue:\s*(.+)$", l)
                if m and PurePosixPath(_clean_value(m.group(1)).replace("\\", "/")).name == src_path.name:
                    out.append(_rel(base, p))
    return list(dict.fromkeys(out))


def cmd_merge(a):
    cfg = load_config(a.config)
    base = cfg["_base"]

    def resolve_md(arg, role):
        p = Path(arg)
        p = p if p.is_absolute() else Path.cwd() / p
        if not p.is_file():
            if _find_finding(cfg, arg) is not None:
                raise CliError(2, "json_findings の要素は merge しない。統合先の note に統合元の id と理由を書く")
            raise CliError(2, f"{role} のファイルが無い: {arg}")
        return p.resolve()

    src = resolve_md(a.src, "src")
    dst = resolve_md(a.into, "dst")
    if src == dst:
        raise CliError(2, "src と dst が同じ")
    ss, sd, skind = _state_of_path(cfg, src)
    ds, dd, dkind = _state_of_path(cfg, dst)
    if ss is None:
        raise CliError(2, f"src がどの source の状態ディレクトリにも無い: {a.src}")
    if ds is None:
        raise CliError(2, f"dst がどの source の状態ディレクトリにも無い: {a.into}")
    if not ss.get("merged_dir"):
        raise CliError(2, f"src の source（root: {ss['root']}）に merged_dir が無いので merge しない")
    if skind != "active":
        raise CliError(2, f"src が active な状態に無い（{sd}）")
    if dkind != "active":
        raise CliError(2, f"dst が closed・merged にある（{dd}）。統合先は active な issue にする")
    mdir = ss["_root"] / ss["merged_dir"]
    dest = mdir / src.name
    if dest.exists():
        raise CliError(2, f"merged_dir に同名がある: {_rel(base, dest)}")
    try:
        s_text, s_bom, s_crlf = _decode(src.read_bytes())
        d_text, d_bom, d_crlf = _decode(dst.read_bytes())
    except UnicodeDecodeError:
        raise CliError(2, "src か dst を UTF-8 で読めない")
    tracked = _git_tracked(src)

    title = md_title(s_text, src.stem)
    dst_rel = _rel(base, dst)
    dest_rel = _rel(base, dest)
    block = [f"## 統合: {title}", "", f"- 統合元: {dest_rel}"]
    reqs = _requests_block(s_text)
    if reqs:
        block += ["- 統合元の利用者の要望:"] + ["  " + r for r in reqs]
    d_new = d_text if d_text.endswith("\n") else d_text + "\n"
    d_new += "\n" + "\n".join(block) + "\n"

    front, rest = _split_front(s_text)
    s_new = front + f"統合先: {dst_rel}\n\n" + rest.lstrip("\n") if front else f"統合先: {dst_rel}\n\n" + s_text
    sl = ss.get("status_line")
    if sl:
        state = ss.get("merged_state") or ss["merged_dir"]
        repl = sl["template"].replace("{state}", state)
        s_new, n = re.subn(sl["regex"], lambda m: repl, s_new, count=1, flags=re.M)
        if n == 0:
            warn(f"src に状態欄（{sl['regex']}）が無いので書き換えない")

    mdir.mkdir(parents=True, exist_ok=True)
    try:
        with open(dest, "xb") as f:
            f.write(_encode(s_new, s_bom, s_crlf))
    except OSError as ex:
        raise CliError(2, f"merged_dir に書けない: {dest_rel}（{ex}）。何も変えていない")
    try:
        _atomic_write(dst, _encode(d_new, d_bom, d_crlf))
    except OSError as ex:
        dest.unlink()
        raise CliError(2, f"dst を書き換えられない: {dst_rel}（{ex}）。何も変えていない")
    try:
        src.unlink()
    except OSError as ex:
        raise CliError(2, f"統合済みだが統合元が残った: {_rel(base, src)}（{ex}）。統合先 {dst_rel} と移動先 {dest_rel} は"
                          "書き終えているので、統合元だけを手で消す（再実行すると移動先の同名で拒否される）。git で追跡している時は stage していないので、"
                          "統合元の削除と移動先の add を手で stage する")
    print(f"merged: {_rel(base, src)} -> {dest_rel}（統合先: {dst_rel}）")
    if tracked is None:
        warn("git を呼べないか git の管理外なので stage しない")
    elif tracked:
        _stage_move(src, dest)
    for f in ss.get("index_files") or []:
        print(f"索引の更新が要る（自動では書き換えない）: {f}")
    for h in _handoff_candidates(base, src, s_text):
        print(f"src を指す handoff の候補: {h}")
    print(f"次に handoff_lifecycle.py release --issue {dest_rel} で、この issue の handoff を片付ける")
    return 0


# ---------- check-new ----------

def _git_root(base):
    try:
        p = _git(base, "rev-parse", "--show-toplevel")
    except OSError as ex:
        raise CliError(2, f"git を呼べない: {ex}")
    if p.returncode != 0:
        raise CliError(2, f"git の管理下ではない: {base}（{p.stderr.strip()}）")
    return Path(p.stdout.strip()).resolve()


def _resolve_base_ref(top, ref):
    p = _git(top, "rev-parse", "--verify", "--quiet", f"{ref}^{{tree}}")
    if p.returncode == 0:
        return p.stdout.strip()
    if ref == "HEAD":
        return EMPTY_TREE  # 最初の commit の前
    raise CliError(2, f"--base の ref が無い: {ref}")


def _related_ok(text, field):
    name = field.strip().rstrip(":：").strip()
    pat = re.compile(r"^[\s>*\-]*\**" + re.escape(name) + r"\**\s*[:：]\**\s*(.*)$", re.M)
    for m in pat.finditer(text):
        v = m.group(1).strip()
        if v.startswith("なし"):
            if "確認済み" in v:
                return True
            continue
        if _REF_VALUE.search(v):
            return True
    return False


def cmd_check_new(a):
    cfg = load_config(a.config)
    base = cfg["_base"]
    top = _git_root(base)
    tree = _resolve_base_ref(top, a.base)
    missing = []
    md_sources = []
    for s in cfg["sources"]:
        if s["type"] == "md_dirs":
            if not s["_root"].is_dir():
                warn(f"source の root が無いので飛ばす: {s['root']}")
                continue
            md_sources.append(s)
        else:
            if not s["_path"].is_file():
                warn(f"source の path が無いので飛ばす: {s['path']}")
                continue
            rel = _rel(top, s["_path"])
            old = _git(top, "show", f"{tree}:{rel}")
            new = _git(top, "show", f":{rel}")
            if new.returncode != 0:
                continue  # index に無い（追跡していない）
            # 読めない台帳は exit 2（飛ばすと検査が黙って OK になる）。base に無い時（初回）は空と比べる
            old_arr = _load_json_source(s, text=old.stdout, strict=True) if old.returncode == 0 else []
            new_arr = _load_json_source(s, text=new.stdout, strict=True)
            old_ids = {str(x.get(s["id"])) for x in (old_arr or []) if isinstance(x, dict)}
            for item in new_arr:
                if not isinstance(item, dict):
                    continue
                iid = str(item.get(s["id"]))
                if iid not in old_ids and not isinstance(item.get("related"), list):
                    missing.append(f"related キーが無い新規 finding: {iid}（{s['path']}）")
    if md_sources:
        p = _git(top, "diff", "--cached", "-M", "--name-status", "--diff-filter=A", tree)
        if p.returncode != 0:
            raise CliError(2, f"git diff に失敗: {p.stderr.strip()}")
        added = [l.split("\t", 1)[1] for l in p.stdout.splitlines() if "\t" in l]
        for rel in added:
            path = (top / rel).resolve()
            if path.suffix.casefold() != ".md":
                continue
            s, d, kind = _state_of_path(cfg, path)
            if s is None or s not in md_sources or _excluded(f"{d}/{path.name}", s.get("exclude")):
                continue
            moved = False
            for od, _k in _state_dirs(s):
                if od == d:
                    continue
                orel = _rel(top, s["_root"] / od / path.name)
                if _git(top, "cat-file", "-e", f"{tree}:{orel}").returncode == 0:
                    moved = True
                    break
            if moved:
                continue
            shown = _git(top, "show", f":{rel}")
            if not _related_ok(shown.stdout if shown.returncode == 0 else "", cfg["related_field"]):
                missing.append(f"「{cfg['related_field']}」欄が無い新規 issue: {rel}")
    if missing:
        for m in missing:
            print(m)
        print(f"起票の前に issue_tracker.py related --text \"<題名>\" で関連 issue を確かめ、md は「{cfg['related_field']} <関連 issue のパス>（別にした理由）」"
              f"か「{cfg['related_field']} なし（related 確認済み）」を、json は related: [<id>...]（無ければ []）を書く")
        return 1
    print("check-new: OK")
    return 0


# ---------- triage ----------

TRIAGE_SECTIONS = [("order", "優先度順"), ("premise_broken", "前提が崩れた候補"), ("stale", "確認が古い"),
                   ("missing", "欄の欠け"), ("duplicates", "重複の候補")]
_PRIORITY_RANK = {"P1": 0, "P2": 1, "P3": 2}
_SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2}
_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
_BACKTICK = re.compile(r"`([^`\n]+)`")
_LINE_SUFFIX = re.compile(r":\d+(?:-\d+)?$")


def natural_key(s):
    return [(0, int(x), "") if x.isdigit() else (1, 0, x) for x in re.split(r"(\d+)", str(s)) if x != ""]


def parse_day(v):
    """YYYY-MM-DD を date にする。形が違う・日付として読めない時は None。"""
    if not isinstance(v, str) or not _DATE_RE.fullmatch(v):
        return None
    try:
        return date.fromisoformat(v)
    except ValueError:
        return None


def _front_value(front, key):
    """frontmatter の「key: 値」を読む。最初の「 #」以降（行末のコメント）と前後の空白・引用符を外す。"""
    m = re.search(r"^" + re.escape(key) + r":[ \t]*(.*)$", front, re.M)
    if not m:
        return None
    v = m.group(1)
    if " #" in v:
        v = v[:v.index(" #")]
    v = v.strip().strip("'\"").strip()
    return v or None


def _str_or_none(v):
    return v if isinstance(v, str) and v else None


def collect_triage_items(cfg):
    """active な issue を、triage の判定に要る欄の dict にする（ファイルは書かない）。"""
    base = cfg["_base"]
    items = []
    for s in cfg["sources"]:
        created_key = s.get("created", "created")
        if s["type"] == "md_dirs":
            if not s["_root"].is_dir():
                warn(f"source の root が無いので飛ばす: {s['root']}")
                continue
            for d in s["active"]:
                sd = s["_root"] / d
                if not sd.is_dir():
                    continue
                for p in sorted(sd.iterdir()):
                    if not p.is_file() or p.suffix.casefold() != ".md" or _excluded(f"{d}/{p.name}", s.get("exclude")):
                        continue
                    try:
                        with p.open("rb") as f:
                            raw = f.read(BODY_BYTES)
                    except OSError as ex:
                        warn(f"読めないので飛ばす: {_rel(base, p)}（{ex}）")
                        continue
                    text = _decode_head(raw, len(raw) == BODY_BYTES)
                    if text is None:
                        warn(f"UTF-8 で読めないので飛ばす: {_rel(base, p)}")
                        continue
                    text = text.replace("\r\n", "\n")
                    front, _ = _split_front(text)
                    reviewed = _front_value(front, "reviewed")
                    items.append({
                        "id": _front_value(front, "id") or p.stem, "path": _rel(base, p),
                        "title": md_title(text, p.stem), "body": text,
                        "priority": _front_value(front, "priority"), "severity": _front_value(front, "severity"),
                        "created": _front_value(front, created_key),
                        "reviewed": reviewed, "has_reviewed": reviewed is not None,
                        "premise": [], "related_ok": _related_ok(text, cfg["related_field"]), "sort_id": _rel(base, p)})
        else:
            data = _load_json_source(s, warn_missing=True)
            for it in data or []:
                if not isinstance(it, dict) or it.get(s["status"]) in s["closed_values"]:
                    continue
                fid = str(it.get(s["id"], ""))
                premise = it.get("premise") if isinstance(it.get("premise"), list) else []
                items.append({
                    "id": fid, "path": f"{s['path']}#{fid}", "title": str(it.get(s["title"], "")),
                    "body": " ".join(v for v in it.values() if isinstance(v, str)),
                    "priority": _str_or_none(it.get("priority")), "severity": _str_or_none(it.get("severity")),
                    "created": _str_or_none(it.get(created_key)),
                    "reviewed": it.get("reviewed"), "has_reviewed": "reviewed" in it,
                    "premise": premise, "related_ok": "related" in it, "sort_id": fid})
    return items


def _body_paths(text):
    out = []
    for m in _BACKTICK.finditer(text):
        v = m.group(1).strip()
        if not v or any(c in v for c in "<>* \t") or "/" not in v:
            continue
        if v.startswith(("~", "/", "\\")) or re.match(r"^[A-Za-z]:", v):
            continue
        v = _LINE_SUFFIX.sub("", v)
        if v not in out:
            out.append(v)
    return out


def _premise_reasons(it, repo_root, home):
    reasons = []
    for e in it["premise"]:
        if not isinstance(e, dict) or not isinstance(e.get("path"), str) or not e["path"]:
            continue
        path = e["path"]
        if ".." in PurePosixPath(path.replace("\\", "/")).parts:
            reasons.append(f"前提のパスが不正（.. を含む）: {path}")
            continue
        full = (home / path[2:]) if path.startswith("~/") else (repo_root / path)
        if not full.is_file():
            reasons.append(f"前提のファイルが無い: {path}")
            continue
        c = e.get("contains")
        if isinstance(c, str) and c:
            try:
                content = full.read_text(encoding="utf-8-sig", errors="replace")
            except OSError:
                content = ""
            if c not in content:
                reasons.append(f"前提の文言が無い: {path}")
    for path in _body_paths(f"{it['title']}\n{it['body']}"):
        top = path.split("/", 1)[0]
        if top in ("", ".", "..") or not (repo_root / top).exists():
            continue
        if not (repo_root / path).exists():
            reasons.append(f"本文のパスが無い: {path}")
    return reasons


def triage_report(items, now, stale_days, threshold, repo_root, home):
    """棚卸しの候補を dict で返す（判定だけ。ファイルは読むだけで書かない）。"""
    def order_key(it):
        c = parse_day(it["created"])
        return (_PRIORITY_RANK.get(it["priority"], 3),
                _SEVERITY_RANK.get((it["severity"] or "").casefold(), 3),
                (0, c) if c else (1, date.min), natural_key(it.get("sort_id", it["id"])))

    rep = {"now": now.isoformat(), "order": [], "premise_broken": [], "stale": [], "missing": [], "duplicates": []}
    ordered = sorted(items, key=order_key)
    for it in ordered:
        rep["order"].append({k: it[k] for k in ("id", "path", "priority", "severity", "created", "title")})
        for r in _premise_reasons(it, repo_root, home):
            rep["premise_broken"].append({"id": it["id"], "path": it["path"], "reason": r})
        raw = it["reviewed"] if it["has_reviewed"] else it["created"]
        if raw is None:
            reason = "日付なし"
        else:
            day = parse_day(raw)
            if day is None:
                reason = f"日付が読めない: {raw}"
            else:
                days = (now - day).days
                reason = f"確認から {days} 日" if days > stale_days else None
        if reason:
            rep["stale"].append({"id": it["id"], "path": it["path"], "reason": reason})
        fields = [f for f, ok in (("priority", it["priority"]), ("関連", it["related_ok"])) if not ok]
        if fields:
            rep["missing"].append({"id": it["id"], "path": it["path"], "fields": fields})
    toks = [(it, tokens(it["title"])) for it in ordered]
    pairs = []
    for i in range(len(toks)):
        for j in range(i + 1, len(toks)):
            a, ta = toks[i]
            b, tb = toks[j]
            if not ta or not tb:
                continue
            score = len(ta & tb) / len(ta | tb)
            if score + 1e-9 >= threshold:
                x, y = sorted((a["id"], b["id"]), key=natural_key)
                pairs.append({"a": x, "b": y, "score": round(score, 2)})
    pairs.sort(key=lambda q: (-q["score"], natural_key(q["a"]), natural_key(q["b"])))
    rep["duplicates"] = pairs
    return rep


def _triage_text(rep):
    lines = []
    for key, name in TRIAGE_SECTIONS:
        lines.append(f"## {name}")
        rows = rep[key]
        if not rows:
            lines.append("（なし）")
        for r in rows:
            if key == "order":
                lines.append("  ".join([r["priority"] or "-", r["severity"] or "-", r["created"] or "-", r["id"], r["title"]]))
            elif key == "missing":
                lines.append(f"{r['id']}  {r['path']}  {', '.join(r['fields'])}")
            elif key == "duplicates":
                lines.append(f"{r['score']:.2f}  {r['a']}  {r['b']}")
            else:
                lines.append(f"{r['id']}  {r['path']}  {r['reason']}")
        lines.append("")
    return "\n".join(lines)


def cmd_triage(a):
    if a.now is None:
        now = date.today()
    else:
        now = parse_day(a.now)
        if now is None:
            raise CliError(2, f"--now が YYYY-MM-DD の日付でない: {a.now}")
    if a.stale_days < 0:
        raise CliError(2, f"--stale-days は 0 以上: {a.stale_days}")
    if not (0 < a.dup_threshold <= 1):
        raise CliError(2, f"--dup-threshold は 0 より大きく 1 以下: {a.dup_threshold}")
    cfg = load_config(a.config)
    rep = triage_report(collect_triage_items(cfg), now, a.stale_days, a.dup_threshold, cfg["_base"], Path.home())
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        print(_triage_text(rep))
    return 0


# ---------- main ----------

def build_parser():
    ap = argparse.ArgumentParser(description="関連 issue の確認・要望の記録・統合・起票の検査・棚卸しの候補")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("related")
    r.add_argument("--text", required=True)
    r.add_argument("--limit", type=int, default=8,
                   help="出す候補の数（既定 8: 起票の前に人が目で見比べられる数）")
    r.add_argument("--include-closed", action="store_true")
    r.add_argument("--deadline", type=float, default=DEFAULT_DEADLINE)
    r.add_argument("--config")
    q = sub.add_parser("request")
    q.add_argument("issue")
    q.add_argument("--text", required=True)
    q.add_argument("--now")
    q.add_argument("--config")
    m = sub.add_parser("merge")
    m.add_argument("src")
    m.add_argument("--into", required=True)
    m.add_argument("--config")
    c = sub.add_parser("check-new")
    c.add_argument("--base", default="HEAD")
    c.add_argument("--config")
    t = sub.add_parser("triage")
    t.add_argument("--now")
    t.add_argument("--stale-days", type=int, default=30,
                   help="確認が古いとみなす日数（既定 30: 月 1 回の棚卸しで一巡する間隔）")
    t.add_argument("--dup-threshold", type=float, default=0.5,
                   help="重複の候補にする題名の語の Jaccard の下限（既定 0.5: 題名の語の半分以上が重なる。"
                        "低いと言い換えの別 issue まで並び、高いと語順や助詞の違いだけの重複を落とす）")
    t.add_argument("--json", action="store_true")
    t.add_argument("--config")
    return ap


def main(argv=None):
    a = build_parser().parse_args(argv)
    fn = {"related": cmd_related, "request": cmd_request, "merge": cmd_merge, "check-new": cmd_check_new,
          "triage": cmd_triage}[a.cmd]
    try:
        return fn(a)
    except CliError as e:
        print(str(e), file=sys.stderr)
        return e.code
    except Exception as e:  # 1 は「欠け」専用。想定外の失敗を欠けと読ませない
        print(f"想定外のエラー: {type(e).__name__}: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    for st in (sys.stdout, sys.stderr):
        try:
            st.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
