#!/usr/bin/env python3
"""check_skill_review_consistency.py — skill レビュー gate の構成の整合検査（D4 の ①〜⑥）。

  render            ① review-skill.md の生成区間が criteria の再生成と一致する
  principles        ② criteria の principles[] が anthropic-best-practices.json に実在する
  ledger            ③ 負債台帳の検証（gate --verify-ledger と同じ。UNVERIFIABLE は失敗にしない）
  hook_registration ④ settings.json に hook が Stop と SessionStart の両方で登録されている
  schema            ⑤ スキーマの required と、保存 script・gate の検査（skill_review_lib.REQUIRED_TOP）が一致する
  criteria          ⑥ criteria 自体の妥当性（axes 5 つ・weight 合計 100・必須キー・pass_rule）

使い方: python check_skill_review_consistency.py [--repo-root R] [--json]
終了コード: 0 = 全項目 OK / 1 = 1 項目でも NG。SessionStart hook が自動で呼ぶ。手動でも実行できる。
"""
import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import skill_review_lib as lib  # noqa: E402


def chk_render(root, data, cerr):
    if data is None:
        return False, cerr
    md = root / lib.MD_REL
    try:
        text = md.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return False, "%s を読めない: %s" % (lib.MD_REL, e)
    lines = text.split("\n")
    b = e = None
    for i, ln in enumerate(lines):
        s = ln.rstrip("\r")
        if b is None and s == lib.MARK_BEGIN:
            b = i
        elif b is not None and s == lib.MARK_END:
            e = i
            break
    if b is None or e is None:
        return False, "%s に生成区間のマーカーが無い" % lib.MD_REL
    if [ln.rstrip("\r") for ln in lines[b:e + 1]] != lib.render_section(data):
        return False, "%s の生成区間が criteria の再生成と一致しない（render_review_skill_md.py --write）" % lib.MD_REL
    return True, "生成区間は criteria と一致"


def chk_principles(root, data, cerr):
    if data is None:
        return False, cerr
    try:
        sot = lib.read_json(root / lib.SOT_REL)
        ids = {p["id"] for p in sot["principles"]}
    except (OSError, ValueError, KeyError, TypeError) as e:
        return False, "best-practices SoT を読めない: %s" % e
    used = []
    for a in data.get("axes", []) if isinstance(data, dict) else []:
        for c in a.get("criteria", []) if isinstance(a, dict) else []:
            used += [p for p in (c.get("principles", []) if isinstance(c, dict) else []) if isinstance(p, str)]
    missing = sorted(set(p for p in used if p not in ids))
    if missing:
        return False, "SoT に無い principle id: %s" % ", ".join(missing)
    return True, "principles %d 件はすべて SoT に実在" % len(set(used))


def chk_ledger(root, *_):
    code, lines = lib.verify_ledger(root)
    if code == 1:
        return False, "; ".join(lines)
    return True, "; ".join(lines)


def chk_hook(root, *_):
    try:
        hooks = lib.read_json(root / lib.SETTINGS_REL).get("hooks", {})
    except (OSError, ValueError, AttributeError) as e:
        return False, "settings.json を読めない: %s" % e
    missing = []
    for ev in ("Stop", "SessionStart"):
        cmds = []
        for blk in hooks.get(ev, []) if isinstance(hooks, dict) else []:
            for h in blk.get("hooks", []) if isinstance(blk, dict) else []:
                if isinstance(h, dict):
                    cmds.append(str(h.get("command", "")))
        if not any(lib.HOOK_NAME in c for c in cmds):
            missing.append(ev)
    if missing:
        return False, "settings.json に %s の登録が無い: %s" % (lib.HOOK_NAME, "・".join(missing))
    return True, "Stop・SessionStart の両方に登録済み"


def chk_schema(root, *_):
    try:
        sc = lib.read_json(root / lib.SCHEMA_REL)
        req = sc["required"]
    except (OSError, ValueError, KeyError, TypeError) as e:
        return False, "スキーマを読めない: %s" % e
    if not isinstance(req, list) or set(req) != set(lib.REQUIRED_TOP):
        only_schema = sorted(set(req) - set(lib.REQUIRED_TOP)) if isinstance(req, list) else []
        only_code = sorted(set(lib.REQUIRED_TOP) - set(req)) if isinstance(req, list) else []
        return False, "スキーマの required と保存 script の検査がずれている（スキーマのみ: %s / 検査のみ: %s）" % (only_schema, only_code)
    # 入れ子の required も比べる。スキーマが properties を持つときだけ（トップレベルの required だけの簡易スキーマは対象外）。
    if isinstance(sc.get("properties"), dict):
        for path, want in lib.NESTED_REQUIRED.items():
            node = sc
            try:
                for step in path.split("."):
                    if step.endswith("[]"):
                        node = node["properties"][step[:-2]]["items"]
                    else:
                        node = node["properties"][step]
                got = node["required"]
            except (KeyError, TypeError):
                return False, "スキーマに %s の required が無い" % path
            if not isinstance(got, list) or set(got) != set(want):
                return False, "スキーマの %s の required と保存 script の検査がずれている（スキーマ: %s / 検査: %s）" % (path, got, want)
    return True, "スキーマの required は保存 script・gate の検査と一致"


def chk_criteria(root, data, cerr):
    if data is None:
        return False, cerr
    errs = lib.check_criteria_validity(data)
    return (False, "; ".join(errs)) if errs else (True, "criteria は妥当")


def main(argv):
    lib.reconfigure_stdio()
    ap = argparse.ArgumentParser(description="skill レビュー gate の整合検査")
    ap.add_argument("--repo-root")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    root = lib.resolve_root(a.repo_root, __file__)
    _sha, data, cerr = lib.criteria_info(root)
    checks = []
    for cid, fn in (("render", chk_render), ("principles", chk_principles), ("ledger", chk_ledger),
                    ("hook_registration", chk_hook), ("schema", chk_schema), ("criteria", chk_criteria)):
        try:
            ok, msg = fn(root, data, cerr)
        except Exception as e:  # 1 項目の例外で他の検査を止めない
            ok, msg = False, "検査中に例外: %s: %s" % (type(e).__name__, e)
        checks.append({"id": cid, "ok": bool(ok), "message": msg})
    allok = all(c["ok"] for c in checks)
    if a.json:
        print(json.dumps({"ok": allok, "checks": checks}, ensure_ascii=False))
    else:
        for c in checks:
            print("%s %s: %s" % ("OK" if c["ok"] else "NG", c["id"], c["message"]))
        print("整合検査: %s" % ("全項目 OK" if allok else "NG あり（%s）" % "・".join(c["id"] for c in checks if not c["ok"])))
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
