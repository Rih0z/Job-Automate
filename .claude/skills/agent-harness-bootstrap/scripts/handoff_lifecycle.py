#!/usr/bin/env python3
"""handoff_lifecycle.py — handoff の受領を記録し、使い終わったら消し、古い残りを知らせる。

handoff の本体は書き換えない。受領の記録は .tmp/handoff-ledger.json（台帳）に持つ。
対象は、resolve 後に「.tmp/handoffs/ 直下の .md の通常ファイル」であるものだけ。

使い方（cwd 基準の相対パスも可）:
  receive <path> [--now ISO]                  受領を台帳に記録する（sha256 も記録）
  receive --title T [--dir DIR] [--now ISO]   最初の見出しが T と一致する 1 件を受領する
  done <path> [--force] [--confirmed]         受領済みのものを削除し、台帳から外す
  done <path> --config CFG                    config が git_tracked の時、追跡中なら削除を stage する（staged: 行）
  remind [--dir DIR] [--hours 4] [--days 30] [--now ISO] [--config CFG] [--keep-referenced DIR]...
         [--only-main-worktree]               受領済みの残りと、未受領で古いものをファイル名だけで出す
  sweep [--dir DIR] [--days 30] [--now ISO] [--apply] [--config CFG] [--keep-referenced DIR]...
                                              未受領で古いものを一覧する。--apply で .tmp/archive/handoffs/ へ退避する
                                              （退避は標準動作で確認は要らない。移動なので archive から戻せる）

除外: --keep-referenced（または config の keep_referenced）の配下（再帰、.md .json .yaml .yml .txt）の本文に
      ファイル名か拡張子なしの名前が出てくるもの（大文字・小文字は区別しない）、先頭 60 行に
      work_status: in_progress があるもの、受領済みのもの。
config（.claude/handoff-lifecycle.json）: script / source / source_sha256 / handoffs_dir /
      keep_referenced [{"path", "required"}] / days / git_tracked。相対パスは config のある .claude/ の親が基準。
git_tracked: true の時、sweep --apply と done は追跡中のファイルをその場で stage し（rename / 削除）、
      staged: 行にパスを出す。commit と push はしない（そのパスだけを利用者側で commit する）。

終了コード: 0 正常 / 2 パス・引数が不正 / 3 未受領 / 4 見出しの一致なし / 5 見出しの一致が複数
            / 6 見出しで受領したものは --confirmed が要る / 7 受領した後に本体が変わった
--force は利用者が指示した時だけ使う（未受領・変更・確認の検査を飛ばして削除する）。
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
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
    load_config(a)  # --dir が無ければ config の handoffs_dir、それも無ければ .tmp/handoffs
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
    load_config(a)
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
    tracked = _git_tracked(target) if a.git_tracked else False
    target.unlink()
    if entry is not None:
        del rec[k]
        save_ledger(lp, rec)
    print(f"deleted: {target}")
    if a.git_tracked and tracked is None:
        print("警告: git を呼べないので stage しない", file=sys.stderr)
    if tracked:
        try:
            r = _git(target.parent, "rm", "--cached", "-q", "--", target.name)
            if r.returncode == 0:
                print(f"staged: {target}")
            else:
                print(f"警告: git で stage できなかった: {r.stderr.strip()}", file=sys.stderr)
        except OSError as ex:
            print(f"警告: git で stage できなかった: {ex}", file=sys.stderr)
    return 0


REF_SUFFIXES = {".md", ".json", ".yaml", ".yml", ".txt"}
REF_MAX_BYTES = 2 * 1024 * 1024  # remind ではこれより大きいファイルを読まない（sweep は全部読む）
LOCK_STALE_SECONDS = 600
_TOKEN = re.compile(r"[\w.\-]+")
_TOKEN_ASCII = re.compile(r"[\w.\-]+", re.ASCII)  # 日本語が直に続く「a.mdを参照」も拾う
_IN_PROGRESS = re.compile(r"^\s*work_status:\s*in_progress\b")


class _Timeout(Exception):
    pass


def load_config(a):
    """--config を読み、未指定の引数を埋める。相対パスの基準は config が置かれた .claude/ の親。"""
    a.keep = []  # [(Path, required, 表示名)]
    a.git_tracked = False
    cfg = {}
    if getattr(a, "config", None):
        cp = _abs(a.config)
        try:
            cfg = json.loads(cp.read_text(encoding="utf-8"))
            if not isinstance(cfg, dict):
                raise ValueError
        except (OSError, ValueError) as ex:
            raise CliError(2, f"config を読めない: {a.config}（{ex}）")
        base = cp.resolve().parent.parent
        if getattr(a, "dir", None) is None and cfg.get("handoffs_dir"):
            a.dir = str(base / cfg["handoffs_dir"])
        if getattr(a, "days", "absent") is None and isinstance(cfg.get("days"), int) and not isinstance(cfg.get("days"), bool):
            a.days = cfg["days"]
        for e in cfg.get("keep_referenced", []):
            if isinstance(e, str):
                e = {"path": e, "required": True}
            if not isinstance(e, dict) or "path" not in e:
                raise CliError(2, f"config の keep_referenced が不正: {e}")
            a.keep.append((base / e["path"], bool(e.get("required", True)), e["path"]))
        a.git_tracked = bool(cfg.get("git_tracked", False))
    for k in getattr(a, "keep_referenced", None) or []:
        a.keep.append((_abs(k), True, k))
    if hasattr(a, "dir") and a.dir is None:
        a.dir = ".tmp/handoffs"
    if hasattr(a, "days") and a.days is None:
        a.days = DEFAULT_DAYS
    return cfg


def _check_keep_dirs(a, strict):
    """参照先のディレクトリを確かめ、使えるものだけを返す。strict なら required の欠落で exit 2。"""
    dirs = []
    for p, required, label in a.keep:
        if p.is_dir():
            dirs.append(p)
        elif required and strict:
            raise CliError(2, f"参照を確かめるディレクトリが無い: {label}（退避しない）")
        else:
            print(f"警告: 参照を確かめるディレクトリが無いので飛ばす: {label}", file=sys.stderr)
    return dirs


def _referenced_tokens(dirs, max_bytes=None, deadline=None):
    """参照先の本文から、handoff 名の形の語を集める（小文字、末尾の . を除く）。"""
    tokens = set()
    for d in dirs:
        for root, _, files in os.walk(d):
            for name in files:
                if deadline is not None and time.monotonic() >= deadline:
                    raise _Timeout()
                p = Path(root) / name
                if p.suffix.casefold() not in REF_SUFFIXES:
                    continue
                try:
                    if max_bytes is not None and p.stat().st_size > max_bytes:
                        print(f"警告: 大きいので参照の検査で読まない: {p}", file=sys.stderr)
                        continue
                    text = p.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                for pat in (_TOKEN, _TOKEN_ASCII):
                    for t in pat.findall(text):
                        tokens.add(t.rstrip(".").casefold())
    return tokens


def _is_referenced(p, tokens):
    return p.name.casefold() in tokens or p.stem.casefold() in tokens


def _in_progress(p):
    try:
        with p.open(encoding="utf-8-sig", errors="replace") as f:
            for i, line in enumerate(f):
                if i >= 60:
                    break
                if _IN_PROGRESS.match(line):
                    return True
    except OSError:
        pass
    return False


def _old_unreceived(d, rec, now, days, tokens=None):
    limit = now - timedelta(days=days)
    out = []
    for p in md_files(d):
        if key_of(p.resolve()) in rec:
            continue
        mt = datetime.fromtimestamp(p.stat().st_mtime, tz=now.tzinfo)
        if mt >= limit:
            continue
        if tokens is not None and _is_referenced(p, tokens):
            continue
        if _in_progress(p):
            continue
        out.append(p)
    return out


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def _is_linked_worktree(cwd):
    """git の worktree（main 以外）の中なら True。git の外・git が無い時は False（main として扱う）。"""
    try:
        p = _git(cwd, "rev-parse", "--path-format=absolute", "--git-dir", "--git-common-dir")
    except OSError:
        return False
    if p.returncode != 0:
        return False
    lines = [l for l in p.stdout.splitlines() if l.strip()]
    if len(lines) != 2:
        return False
    a, b = (os.path.normcase(str(Path(x).resolve())) for x in lines)
    return a != b


def _git_tracked(path):
    try:
        p = _git(path.parent, "ls-files", "--error-unmatch", "--", path.name)
    except OSError:
        return None
    if p.returncode == 0:
        return True
    if p.returncode == 1:  # repo の中だが追跡されていない
        return False
    return None  # git repo ではない等


def _stage_move(old, new, was_tracked):
    """追跡中だったものを rename として stage する。失敗しても移動は取り消さない。"""
    if not was_tracked:
        return
    try:
        r1 = _git(old.parent, "rm", "--cached", "-q", "--", old.name)
        r2 = _git(new.parent, "add", "-f", "--", new.name)
    except OSError as ex:
        print(f"警告: git で stage できなかった: {ex}", file=sys.stderr)
        return
    if r1.returncode or r2.returncode:
        try:  # 片方だけ index に残らないよう戻す
            _git(old.parent, "reset", "-q", "--", old.name)
            _git(new.parent, "reset", "-q", "--", new.name)
        except OSError:
            pass
        print(f"警告: git で stage できなかった（index は戻した）: {(r1.stderr + r2.stderr).strip()}", file=sys.stderr)
        return
    print(f"staged: {old}")
    print(f"staged: {new}")


def _q(s):
    s = str(s)
    return f'"{s}"' if any(c in s for c in " \t\"'") else s


def _sweep_cmd(a, days_given):
    parts = ["sweep"]
    if getattr(a, "config", None):
        parts += ["--config", _q(a.config)]
    for k in a.keep_referenced or []:
        parts += ["--keep-referenced", _q(k)]
    if days_given:
        parts += ["--days", str(a.days)]
    parts.append("--apply")
    return " ".join(parts)


def cmd_remind(a):
    started = time.monotonic()
    days_given = a.days is not None and not getattr(a, "config", None) and a.days != DEFAULT_DAYS
    if getattr(a, "config", None) and a.days is not None:
        days_given = True
    try:
        load_config(a)
    except CliError as e:
        print(f"警告: {e}", file=sys.stderr)
        return 0
    if a.only_main_worktree and _is_linked_worktree(Path.cwd()):
        return 0
    now = parse_now(a.now)
    try:
        d = check_dir(a.dir)
    except CliError as e:
        print(str(e), file=sys.stderr)
        return 2
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
        tokens = None
        timed_out = False
        dirs = _check_keep_dirs(a, strict=False)
        if dirs:
            try:
                tokens = _referenced_tokens(dirs, max_bytes=REF_MAX_BYTES,
                                            deadline=started + a.ref_timeout)
            except _Timeout:
                timed_out = True
        cmd = _sweep_cmd(a, days_given)
        if timed_out:
            lines.append(f"[handoff] 参照の検査が時間内に終わらなかった。{cmd.replace(' --apply', '')} で一覧を確かめてから --apply する")
        else:
            old = _old_unreceived(d, rec, now, a.days, tokens)
            if old:
                names = ", ".join(p.name for p in old[:REMIND_LIMIT])
                more = " ほか" if len(old) > REMIND_LIMIT else ""
                lines.append(f"[handoff] 未受領で {a.days} 日を超えたもの: {len(old)} 件（{names}{more}）。"
                             f"本文は読まない。確認なしで {cmd} を実行して .tmp/archive/handoffs/ へ退避する"
                             f"（archive から戻せる。exit 2 なら退避せず報告する。staged: が出たらそのパスだけを commit・push する）")
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


def _acquire_lock(lock):
    lock.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(2):
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return
        except FileExistsError:
            try:
                age = time.time() - lock.stat().st_mtime
            except OSError:
                continue
            if age > LOCK_STALE_SECONDS:
                print(f"警告: 古いロックを外した: {lock}", file=sys.stderr)
                try:
                    lock.unlink()
                except OSError:
                    pass
                continue
            raise CliError(2, f"別の sweep が実行中（ロック: {lock}）。終わってからやり直す")
    raise CliError(2, f"ロックを取れない: {lock}")


def cmd_sweep(a):
    load_config(a)
    now = parse_now(a.now)
    d = check_dir(a.dir)
    if not d.is_dir():
        return 0
    dirs = _check_keep_dirs(a, strict=True)
    if not a.apply:
        rec, _ = load_ledger(ledger_path(d))
        tokens = _referenced_tokens(dirs) if dirs else None
        old = _old_unreceived(d, rec, now, a.days, tokens)
        print(f"退避の候補（未受領で {a.days} 日超）: {len(old)} 件")
        for p in old:
            print(f"  {p.name}")
        return 0
    lock = d.parent / "handoff-sweep.lock"
    _acquire_lock(lock)
    try:
        rec, ok = load_ledger(ledger_path(d))
        if not ok:
            raise CliError(2, "台帳が壊れているので退避しない（受領済みのものを動かすおそれがある）")
        tokens = _referenced_tokens(dirs) if dirs else None
        old = _old_unreceived(d, rec, now, a.days, tokens)
        arch = d.parent / "archive" / "handoffs"
        arch.mkdir(parents=True, exist_ok=True)
        for p in old:
            if not p.exists():
                print(f"警告: もう無いので飛ばす: {p}", file=sys.stderr)
                continue
            tracked = _git_tracked(p) if a.git_tracked else False
            dest = _unique_dest(arch, p.name)
            shutil.move(str(p), str(dest))
            print(f"moved: {p} -> {dest}")
            if a.git_tracked:
                if tracked is None:
                    print("警告: git を呼べないので stage しない", file=sys.stderr)
                else:
                    _stage_move(p, dest, tracked)
    finally:
        try:
            lock.unlink()
        except OSError:
            pass
    return 0


def build_parser():
    ap = argparse.ArgumentParser(description="handoff の受領・削除・通知")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("receive")
    r.add_argument("path", nargs="?")
    r.add_argument("--title")
    r.add_argument("--dir", default=None)
    r.add_argument("--now")
    r.add_argument("--config")
    dn = sub.add_parser("done")
    dn.add_argument("path")
    dn.add_argument("--force", action="store_true")
    dn.add_argument("--confirmed", action="store_true")
    dn.add_argument("--config")
    rm = sub.add_parser("remind")
    rm.add_argument("--dir", default=None)
    rm.add_argument("--hours", type=float, default=4)
    rm.add_argument("--days", type=int, default=None)
    rm.add_argument("--now")
    rm.add_argument("--config")
    rm.add_argument("--keep-referenced", action="append")
    rm.add_argument("--only-main-worktree", action="store_true")
    rm.add_argument("--ref-timeout", type=float, default=10.0, help=argparse.SUPPRESS)
    sw = sub.add_parser("sweep")
    sw.add_argument("--dir", default=None)
    sw.add_argument("--days", type=int, default=None)
    sw.add_argument("--now")
    sw.add_argument("--apply", action="store_true")
    sw.add_argument("--config")
    sw.add_argument("--keep-referenced", action="append")
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
