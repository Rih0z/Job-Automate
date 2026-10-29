#!/usr/bin/env python3
"""append_skill_review_record.py — 別 agent（readonly-reviewer）のレビュー結果を skill-review-record/v1 として保存する（D2）。

使い方（メイン session が、レビュー開始前に skill_review_gate.py --hash SKILL で得た値を --expected-hash に渡す）:
  python append_skill_review_record.py --skill NAME --expected-hash HASH --result-file F \\
      --agent-id ID --subagent-type readonly-reviewer --model M [--repo-root R]

- reviewed_at は本 script が保存時の現在の UTC で付ける（呼び出し元は渡せない）。content_hash も保存時に実ファイルから再計算し、
  --expected-hash と違えば拒否する（レビュー中に編集された内容に PASS を付けない）。渡された値は保存しない。
- result は criteria の output_schema に沿った JSON。整合しない結果（PASS なのに must_pass_failures がある等）は拒否する。
- 同一性キー（skill 名・content_hash・criteria の sha256・agent_id・result の sha256）が既存記録と同じなら「記録済み」として成功扱い。
- 保存先: .claude/review-history/skill-review/SKILL/UTC日時-キー先頭8桁.json（排他作成）。
終了コード: 0 = 保存または記録済み / 1 = 検査で拒否（記録ファイルを作らない） / 2 = 引数不備。
stdout の 1 行目: SAVED 相対パス または ALREADY_RECORDED 相対パス。agent_id が unavailable のときは stderr に WARN を出す。
"""
import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import skill_review_lib as lib  # noqa: E402


def reject(msg):
    print("拒否: %s" % msg, file=sys.stderr)
    return 1


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def identity_key(skill, content_hash, crit_sha, agent_id, result):
    return lib.sha256_hex(canonical([skill, content_hash, crit_sha, agent_id, lib.sha256_hex(canonical(result).encode("utf-8"))]).encode("utf-8"))


def main(argv):
    lib.reconfigure_stdio()
    ap = argparse.ArgumentParser(description="skill のレビュー記録を保存する")
    ap.add_argument("--repo-root")
    ap.add_argument("--skill", required=True)
    ap.add_argument("--expected-hash", required=True, help="レビュー開始時に skill_review_gate.py --hash で得た content_hash（必須）")
    ap.add_argument("--result-file", required=True)
    ap.add_argument("--agent-id", required=True, help="Agent ツールの結果から転記する。取得できなければ unavailable")
    ap.add_argument("--subagent-type", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--reviewer-kind", default="subagent")
    a = ap.parse_args(argv)

    root = lib.resolve_root(a.repo_root, __file__)
    if not lib._NAME_RE.match(a.skill):
        return reject("skill 名が不正: %r" % a.skill)
    if a.skill not in lib.skill_names(root):
        return reject("skill が見つからない: %s" % a.skill)
    if a.reviewer_kind != "subagent":
        return reject("reviewer.kind は subagent のみ（自己レビュー・人手の記録は保存しない）: %r" % a.reviewer_kind)
    for flag, val in (("--agent-id", a.agent_id), ("--subagent-type", a.subagent_type), ("--model", a.model)):
        if not val.strip():
            return reject("%s が空" % flag)
    try:
        result = json.loads(Path(a.result_file).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return reject("result ファイルを UTF-8 の JSON として読めない: %s" % e)

    cur_hash, files, unreadable = lib.skill_content(root, a.skill)
    if cur_hash != a.expected_hash:
        return reject("content_hash が --expected-hash と違う（レビュー中に skill が編集された、または引数の誤り）。"
                      "現在の値で再レビューしてから保存する")
    crit_sha, crit_data, err = lib.criteria_info(root)
    if err or crit_data is None:
        return reject(err or "criteria を読めない")
    axes, min_score = lib.criteria_axes(crit_data)
    if axes is None:
        return reject("criteria に axes / pass_rule が無い")
    fetched, max_age, _expired, serr = lib.sot_status(root, lib.now_utc())
    if serr:
        return reject(serr)

    reviewed_at = lib.now_utc().strftime("%Y-%m-%dT%H:%M:%SZ")
    rec = {
        "schema": lib.RECORD_SCHEMA,
        "skill": a.skill,
        "reviewed_at": reviewed_at,
        "target": {"files": [{"path": p, "sha256": s} for p, s in files], "content_hash": cur_hash},
        "criteria": {"file": lib.CRITERIA_REL, "sha256": crit_sha},
        "best_practices_snapshot": {"fetched": fetched, "max_age_days": max_age},
        "reviewer": {"kind": a.reviewer_kind, "subagent_type": a.subagent_type, "agent_id": a.agent_id, "model": a.model},
        "result": result,
    }
    errs = lib.validate_record(rec, axes, min_score)
    if errs:
        return reject("; ".join(errs))

    key = identity_key(a.skill, cur_hash, crit_sha, a.agent_id, result)
    d = Path(root) / lib.HISTORY_REL / a.skill
    for f in sorted(d.glob("*.json")) if d.is_dir() else []:
        try:
            old = json.loads(f.read_text(encoding="utf-8"))
            if identity_key(old["skill"], old["target"]["content_hash"], old["criteria"]["sha256"],
                            old["reviewer"]["agent_id"], old["result"]) == key:
                print("ALREADY_RECORDED %s" % f.relative_to(root).as_posix())
                return 0
        except (OSError, ValueError, KeyError, TypeError):
            continue
    d.mkdir(parents=True, exist_ok=True)
    name = "%s-%s.json" % (reviewed_at.replace("-", "").replace(":", ""), key[:8])
    path = d / name
    try:
        with open(str(path), "x", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False, indent=2) + "\n")
    except FileExistsError:
        return reject("同名の記録ファイルが既にある: %s" % name)
    print("SAVED %s" % path.relative_to(root).as_posix())
    if a.agent_id == "unavailable":
        print("WARN: reviewer.agent_id が unavailable（Agent の結果から転記できなかった）。gate --all に WARN が出る", file=sys.stderr)
    if unreadable:
        print("WARN: 読めないファイル %d 件を hash から除外した" % unreadable, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
