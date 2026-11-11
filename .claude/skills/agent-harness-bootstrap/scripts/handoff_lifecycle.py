#!/usr/bin/env python3
"""handoff_lifecycle.py — handoff の受領を記録し、使い終わったら消し、古い残りを知らせる。

handoff の本体は書き換えない。受領の記録は .tmp/handoff-ledger.json（台帳）に持つ。
対象は、resolve 後に「.tmp/handoffs/ 直下の .md の通常ファイル」であるものだけ。

使い方（cwd 基準の相対パスも可）:
  receive <path> [--now ISO]                  受領を台帳に記録する（sha256 も記録）
  receive --title T [--dir DIR] [--now ISO]   最初の見出しが T と一致する 1 件を受領する
  done <path> [--force] [--confirmed]         受領済みのものを削除し、台帳から外す
  remind [--dir DIR] [--hours 4] [--days 30] [--now ISO]
                                              受領済みの残りと、未受領で古いものをファイル名だけで出す
  sweep [--dir DIR] [--days 30] [--now ISO] [--apply]
                                              未受領で古いものを一覧する。--apply で .tmp/archive/handoffs/ へ退避する
                                              （退避は標準動作で確認は要らない。移動なので archive から戻せる）

終了コード: 0 正常 / 2 パス・引数が不正 / 3 未受領 / 4 見出しの一致なし / 5 見出しの一致が複数
            / 6 見出しで受領したものは --confirmed が要る / 7 受領した後に本体が変わった
--force は利用者が指示した時だけ使う（未受領・変更・確認の検査を飛ばして削除する）。
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

REMIND_LIMIT = 5
DEFAULT_DAYS = 30  # remind と sweep で同じ日数を使う（未受領で古いものの退避は確認なしの標準動作）


class CliError(Exception):
    def __init__(self, code, msg):
        super().__init__(msg)
        self.code = code


def parse_now(s):
    if not s:
        return datetime.now().astimezone()
    try:
        d = datetime.fromisoformat(s)
    except ValueError:
        raise CliError(2, f"--now の値が不正: {s}")
    return d if d.tzinfo else d.astimezone()


def _abs(p):
    p = Path(p)
    return p if p.is_absolute() else Path.cwd() / p


def _is_handoffs_dir(d):
    return d.name.casefold() == "handoffs" and d.parent.name.casefold() == ".tmp"


def check_file(p, must_exist=True):
    """対象の handoff ファイルを検証して resolve 後のパスを返す。外れたら CliError(2)。"""
    path = _abs(p)
    try:
        r = path.resolve(strict=must_exist)
    except (FileNotFoundError, OSError):
        raise CliError(2, f"ファイルが無い: {p}")
    if must_exist and not r.is_file():
        raise CliError(2, f"通常のファイルではない: {p}")
    if r.suffix.casefold() != ".md" or not _is_handoffs_dir(r.parent):
        raise CliError(2, f".tmp/handoffs/ 直下の .md ではない: {p}")
    return r


def check_dir(d):
    r = _abs(d).resolve(strict=False)
    if not _is_handoffs_dir(r):
        raise CliError(2, f"--dir は .tmp/handoffs でなければならない: {d}")
    return r


def key_of(path):
    return os.path.normcase(str(path))


def ledger_path(handoffs_dir):
    return handoffs_dir.parent / "handoff-ledger.json"


def load_ledger(lp, backup=False):
    """台帳を読む。(entries, ok) を返す。壊れていれば ok=False。backup=True なら .bak-<時刻> へ移す。"""
    if not lp.exists():
        return {}, True
    try:
        data = json.loads(lp.read_text(encoding="utf-8"))
        rec = data["received"]
        if not isinstance(rec, dict) or not all(isinstance(v, dict) for v in rec.values()):
            raise ValueError
        return rec, True
    except (ValueError, KeyError, TypeError, OSError):
        print(f"警告: 台帳が壊れている: {lp}", file=sys.stderr)
        if backup:
            bak = lp.with_name(lp.name + ".bak-" + datetime.now().strftime("%Y%m%d%H%M%S%f"))
            os.replace(lp, bak)
            print(f"警告: 壊れた台帳を退避した: {bak}", file=sys.stderr)
        return {}, False


def save_ledger(lp, rec):
    lp.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".handoff-ledger-", dir=str(lp.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"received": rec}, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, lp)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def sha256_of(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def first_heading(path):
    lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    i = 0
    if lines and lines[0].strip() == "---":
        for j in range(1, len(lines)):
            if lines[j].strip() == "---":
                i = j + 1
                break
    for line in lines[i:]:
        if line.startswith("# "):
            return line[2:].strip()
    return None


def md_files(d):
    return sorted(p for p in d.iterdir() if p.is_file() and p.suffix.casefold() == ".md")


def cmd_receive(a):
    now = parse_now(a.now)
    if a.title is not None:
        d = check_dir(a.dir)
        if not d.is_dir():
            raise CliError(4, "見出しの一致なし（ディレクトリが無い）")
        hits = [p for p in md_files(d) if first_heading(p) == a.title.strip()]
        if not hits:
            raise CliError(4, f"見出しの一致なし: {a.title}")
        if len(hits) > 1:
            print("見出しの一致が複数ある。利用者に対象を確かめる:")
            for p in hits:
                print(f"  {p.name}")
            raise CliError(5, "見出しの一致が複数")
        target, how = check_file(hits[0]), "title"
    elif a.path:
        target, how = check_file(a.path), "path"
    else:
        raise CliError(2, "receive には <path> か --title が要る")
    lp = ledger_path(target.parent)
    rec, _ = load_ledger(lp, backup=True)
    rec[key_of(target)] = {
        "path": str(target),
        "received_at": now.isoformat(timespec="seconds"),
        "sha256": sha256_of(target),
        "mtime": target.stat().st_mtime,
        "matched_by": how,
    }
    save_ledger(lp, rec)
    print(f"received: {target}" + ("（見出しで特定。done の前に利用者に確かめる）" if how == "title" else ""))
    return 0


def cmd_done(a):
    target = check_file(a.path, must_exist=False)
    lp = ledger_path(target.parent)
    rec, _ = load_ledger(lp, backup=True)
    k = key_of(target)
    entry = rec.get(k)
    if not target.exists():
        if entry is not None:
            del rec[k]
            save_ledger(lp, rec)
            print(f"台帳から外した（本体は既に無い）: {target}")
            return 0
        raise CliError(2, f"ファイルが無い: {a.path}")
    target = check_file(a.path)
    if not a.force:
        if entry is None:
            raise CliError(3, "未受領の handoff は消さない（利用者の指示がある時だけ --force）")
        if entry.get("sha256") != sha256_of(target):
            raise CliError(7, "受領した後に本体が変わった。自分で更新したなら receive をやり直してから done する")
        if entry.get("matched_by") == "title" and not a.confirmed:
            raise CliError(6, "見出しで特定して受領したもの。利用者に確かめてから --confirmed を付ける")
    target.unlink()
    if entry is not None:
        del rec[k]
        save_ledger(lp, rec)
    print(f"deleted: {target}")
    return 0


def _old_unreceived(d, rec, now, days):
    limit = now - timedelta(days=days)
    out = []
    for p in md_files(d):
        if key_of(p.resolve()) in rec:
            continue
        mt = datetime.fromtimestamp(p.stat().st_mtime, tz=now.tzinfo)
        if mt < limit:
            out.append(p)
    return out


def cmd_remind(a):
    now = parse_now(a.now)
    d = check_dir(a.dir)
    if not d.is_dir():
        return 0
    try:
        rec, _ = load_ledger(ledger_path(d))
        lines = []
        for e in rec.values():
            p = Path(e.get("path", ""))
            if not p.is_file():
                continue
            try:
                ra = datetime.fromisoformat(e["received_at"])
            except (KeyError, ValueError, TypeError):
                continue
            if ra.tzinfo is None:
                ra = ra.astimezone()
            hours = (now - ra).total_seconds() / 3600
            note = "・中断の疑い（作業が終わっていれば done で消す）" if hours > a.hours else ""
            lines.append(f"[handoff] 受領済みで残っている: {p.name}（受領 {hours:.1f} 時間前{note}）")
        old = _old_unreceived(d, rec, now, a.days)
        if old:
            names = ", ".join(p.name for p in old[:REMIND_LIMIT])
            more = " ほか" if len(old) > REMIND_LIMIT else ""
            days_opt = "" if a.days == DEFAULT_DAYS else f"--days {a.days} "
            lines.append(f"[handoff] 未受領で {a.days} 日を超えたもの: {len(old)} 件（{names}{more}）。"
                         f"本文は読まない。確認なしで sweep {days_opt}--apply を実行して .tmp/archive/handoffs/ へ退避する"
                         f"（archive から戻せる。exit 2 なら退避せず報告する）")
        for l in lines:
            print(l)
    except Exception as ex:  # 通知は失敗しても session を止めない
        print(f"警告: remind に失敗: {ex}", file=sys.stderr)
    return 0


def _unique_dest(dest_dir, name):
    dest = dest_dir / name
    stem, suf = Path(name).stem, Path(name).suffix
    n = 1
    while dest.exists():
        dest = dest_dir / f"{stem}-{n}{suf}"
        n += 1
    return dest


def cmd_sweep(a):
    now = parse_now(a.now)
    d = check_dir(a.dir)
    if not d.is_dir():
        return 0
    rec, ok = load_ledger(ledger_path(d))
    if a.apply and not ok:
        raise CliError(2, "台帳が壊れているので退避しない（受領済みのものを動かすおそれがある）")
    old = _old_unreceived(d, rec, now, a.days)
    if not a.apply:
        print(f"退避の候補（未受領で {a.days} 日超）: {len(old)} 件")
        for p in old:
            print(f"  {p.name}")
        return 0
    arch = d.parent / "archive" / "handoffs"
    arch.mkdir(parents=True, exist_ok=True)
    for p in old:
        dest = _unique_dest(arch, p.name)
        shutil.move(str(p), str(dest))
        print(f"moved: {p} -> {dest}")
    return 0


def build_parser():
    ap = argparse.ArgumentParser(description="handoff の受領・削除・通知")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("receive")
    r.add_argument("path", nargs="?")
    r.add_argument("--title")
    r.add_argument("--dir", default=".tmp/handoffs")
    r.add_argument("--now")
    dn = sub.add_parser("done")
    dn.add_argument("path")
    dn.add_argument("--force", action="store_true")
    dn.add_argument("--confirmed", action="store_true")
    rm = sub.add_parser("remind")
    rm.add_argument("--dir", default=".tmp/handoffs")
    rm.add_argument("--hours", type=float, default=4)
    rm.add_argument("--days", type=int, default=DEFAULT_DAYS)
    rm.add_argument("--now")
    sw = sub.add_parser("sweep")
    sw.add_argument("--dir", default=".tmp/handoffs")
    sw.add_argument("--days", type=int, default=DEFAULT_DAYS)
    sw.add_argument("--now")
    sw.add_argument("--apply", action="store_true")
    return ap


def main(argv=None):
    a = build_parser().parse_args(argv)
    fn = {"receive": cmd_receive, "done": cmd_done, "remind": cmd_remind, "sweep": cmd_sweep}[a.cmd]
    try:
        return fn(a)
    except CliError as e:
        print(str(e), file=sys.stderr)
        return e.code


if __name__ == "__main__":
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
