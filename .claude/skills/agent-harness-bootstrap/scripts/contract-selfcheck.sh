#!/usr/bin/env bash
# contract-selfcheck.sh — 台帳の target_contract が「デフォルト選択で満たせる・矛盾しない」ことの自己検査
#
# 目的: provenance.json の各要素の when_selected / when_unselected 契約は、生成物に対する決定的な要件だが、
#   契約同士が矛盾していると（例: 選択要素 A が語句 X を要求し、非選択要素 B が同じ語句 X を禁止）どんな生成物も
#   --target 検査を通らない。本スクリプトは default_selection（official + recommend）で選択記録を作り、
#   選択要素の when_selected を機械的に満たす最小の生成物を scratch に組み立て、provenance-check.sh --target を
#   実行して PASS することを確認する（= 契約が満たせる・非選択契約が誤発火しない）。
#
# usage: bash .claude/skills/agent-harness-bootstrap/scripts/contract-selfcheck.sh            # PASS で exit 0
#        SELFCHECK_KEEP=1 ... で scratch を残す（既定は削除）

set -uo pipefail
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$(cd "$SKILL_DIR/../../.." && pwd)"
MANIFEST="$SKILL_DIR/provenance.json"
CHECK="$SKILL_DIR/scripts/provenance-check.sh"
command -v python3 >/dev/null 2>&1 || { echo "FAIL: python3 が必要" >&2; exit 1; }

SCRATCH="$(mktemp -d)"
[[ "${SELFCHECK_KEEP:-0}" == "1" ]] || trap 'rm -rf "$SCRATCH"' EXIT

python3 - "$MANIFEST" "$SCRATCH" "$ROOT" <<'PY'
import json, os, re, sys, shutil
manifest, tgt, root = sys.argv[1:4]
d = json.load(open(manifest, encoding="utf-8"))
levels = d["provenance_levels"]
def tp(p): return os.path.join(tgt, p)
def ensure_dir(p): os.makedirs(os.path.dirname(p), exist_ok=True)
def append(p, text):
    ensure_dir(p)
    with open(p, "a", encoding="utf-8") as f:
        f.write(text + "\n")
def ensure_file(p, body="# generated\n"):
    if not os.path.exists(p):
        ensure_dir(p); open(p, "w", encoding="utf-8").write(body)
def ensure_frontmatter_paths(p):
    ensure_file(p, "")
    txt = open(p, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", txt, re.S)
    if m:
        if not re.search(r"^paths:", m.group(1), re.M):
            txt = "---\n" + m.group(1) + '\npaths:\n  - "**/*"\n---\n' + txt[m.end():]
    else:
        txt = '---\ndescription: generated\npaths:\n  - "**/*"\n---\n' + txt
    open(p, "w", encoding="utf-8").write(txt)
def literal_from_pattern(pat):
    # 正規表現の最小の具体例（alternation は先頭、`5 ?KB` は 5KB、エスケープ解除）
    first = pat.split("|")[0]
    first = first.replace(" ?", "").replace("\\", "")
    return first
# 1) デフォルト選択記録
sel = {}
for e in d["elements"]:
    isd = e["provenance"] == "repo-specific" or e.get("portable") is False
    ds = e.get("default_selection_override", levels[e["provenance"]]["default_selection"])
    selected = (ds in ("include", "recommend")) and not isd
    ent = {"selected": selected, "decided_by": "excluded" if isd else "default"}
    if selected and e.get("kind") == "skill-group":
        ent["skills"] = list(e.get("skills", []))
    sel[e["id"]] = ent
ensure_dir(tp(".claude/harness-selection.json"))
json.dump({"schema": "harness-selection/v1", "source": "selfcheck", "decided_at": d.get("updated"),
           "decided_by": "default", "selections": sel}, open(tp(".claude/harness-selection.json"), "w", encoding="utf-8"), indent=1)
# 2) 選択要素の when_selected を機械的に満たす
ensure_file(tp("CLAUDE.md"), "# CLAUDE.md - selfcheck\n")
for e in d["elements"]:
    if not sel[e["id"]]["selected"]:
        continue
    for c in e.get("target_contract", {}).get("when_selected", []):
        t, p, pat = c.get("type"), c.get("path", ""), c.get("pattern", "")
        if t == "file_exists":
            body = '---\ndescription: generated\n---\n# generated\n' if p.startswith(".claude/rules/") else ("{}\n" if p.endswith(".json") else "# generated\n")
            ensure_file(tp(p), body)
        elif t == "grep":
            lit = literal_from_pattern(pat)
            if os.path.isdir(tp(p)) or (not os.path.exists(tp(p)) and not p.endswith((".md", ".json"))):
                ensure_file(tp(os.path.join(p, "generated.md")), "# generated\n"); append(tp(os.path.join(p, "generated.md")), lit)
            else:
                if p.endswith(".json") and not os.path.exists(tp(p)):
                    ensure_file(tp(p), "{}\n")
                    open(tp(p), "w", encoding="utf-8").write(json.dumps({"hooks": {lit: []}}) + "\n")
                elif p.endswith(".json"):
                    obj = json.load(open(tp(p), encoding="utf-8")) if os.path.getsize(tp(p)) else {}
                    obj.setdefault("hooks", {})[lit] = []
                    open(tp(p), "w", encoding="utf-8").write(json.dumps(obj) + "\n")
                else:
                    ensure_file(tp(p)); append(tp(p), lit)
        elif t == "import":
            ensure_file(tp(p), '---\ndescription: generated\n---\n# generated\n'); append(tp("CLAUDE.md"), "@" + p)
        elif t == "frontmatter_paths":
            ensure_frontmatter_paths(tp(p))
        elif t == "gitignore":
            append(tp(".gitignore"), pat)
    for s in e.get("skills", []):
        if e.get("kind") == "skill-group" and s not in sel[e["id"]].get("skills", []):
            continue
        ensure_file(tp(f".claude/skills/{s}/SKILL.md"), "---\nname: %s\n---\n" % s)
    for cmd in e.get("commands", []):
        ensure_file(tp(f".claude/commands/{cmd}.md"), "# cmd\n")
    for f in e.get("files", []):
        src = os.path.join(root, f)
        if os.path.isfile(src):
            ensure_dir(tp(f)); shutil.copyfile(src, tp(f))
        else:
            ensure_file(tp(f))
print("selfcheck target built:", tgt, "selected:", sum(1 for v in sel.values() if v["selected"]), "/", len(sel))
PY
[[ $? -eq 0 ]] || { echo "FAIL: scratch の組み立てに失敗"; exit 1; }

if bash "$CHECK" --target "$SCRATCH"; then
  echo "PASS: default 選択の契約は満たせる・非選択契約の誤発火なし"
  exit 0
else
  echo "FAIL: 契約に矛盾または満たせない要件がある（上記 C12 行を見て provenance.json の target_contract か template / Step 8 表を直す）"
  [[ "${SELFCHECK_KEEP:-0}" == "1" ]] && echo "scratch: $SCRATCH"
  exit 1
fi
