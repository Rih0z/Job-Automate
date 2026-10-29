#!/usr/bin/env python3
"""render_review_skill_md.py — criteria（skill-quality.json）から review-skill.md の生成区間を作る（D1 の二重管理の解消）。

使い方:
  python render_review_skill_md.py [--repo-root R]            生成区間（マーカー行を含む）を stdout に出す
  python render_review_skill_md.py [--repo-root R] --write    workflows/software-development/review-skill.md の生成区間を置き換える（区間の外は 1 バイトも変えない）
  python render_review_skill_md.py [--repo-root R] --check    現ファイルの生成区間が再生成と一致するか（一致 0 / 不一致・マーカー欠落 1）
生成区間 = md 内の【生成ここから】の行から【生成ここまで】の行まで（行全体がマーカー）。
終了コード: 0 = 成功 / 1 = 失敗（criteria を読めない・マーカー欠落・--check の不一致）。
"""
import argparse
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import skill_review_lib as lib  # noqa: E402


def find_section(lines):
    """行リスト（改行 LF で分割済み・末尾の CR は残す）から (開始 index, 終了 index) を探す。無ければ None。"""
    b = e = None
    for i, ln in enumerate(lines):
        s = ln.rstrip("\r")
        if b is None and s == lib.MARK_BEGIN:
            b = i
        elif b is not None and s == lib.MARK_END:
            e = i
            break
    return (b, e) if b is not None and e is not None else None


def main(argv):
    lib.reconfigure_stdio()
    ap = argparse.ArgumentParser(description="review-skill.md の生成区間を criteria から作る")
    ap.add_argument("--repo-root")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    root = lib.resolve_root(a.repo_root, __file__)

    _sha, data, err = lib.criteria_info(root)
    if data is None:
        print("失敗: %s" % err, file=sys.stderr)
        return 1
    section = lib.render_section(data)
    if not (a.write or a.check):
        sys.stdout.write("\n".join(section) + "\n")
        return 0

    md = root / lib.MD_REL
    try:
        raw = md.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as e:
        print("失敗: %s を UTF-8 で読めない: %s" % (lib.MD_REL, e), file=sys.stderr)
        return 1
    lines = raw.split("\n")
    pos = find_section(lines)
    if pos is None:
        print("失敗: %s に %s ／ %s の行が無い" % (lib.MD_REL, lib.MARK_BEGIN, lib.MARK_END), file=sys.stderr)
        return 1
    b, e = pos
    cr = "\r" if lines[b].endswith("\r") else ""  # 区間の改行を、マーカー行の改行に合わせる（CRLF の作業ツリーでも区間の外を変えない）
    if a.check:
        current = [ln.rstrip("\r") for ln in lines[b:e + 1]]
        if current == section:
            print("OK: 生成区間は criteria と一致する")
            return 0
        print("失敗: 生成区間が criteria の再生成と一致しない（render_review_skill_md.py --write で再生成する）", file=sys.stderr)
        return 1
    new_lines = lines[:b] + [s + cr for s in section] + lines[e + 1:]
    md.write_bytes("\n".join(new_lines).encode("utf-8"))
    print("OK: 生成区間を再生成した（%s）" % lib.MD_REL)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
