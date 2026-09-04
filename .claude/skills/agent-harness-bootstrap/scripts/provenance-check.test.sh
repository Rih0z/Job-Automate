#!/usr/bin/env bash
# provenance-check.test.sh — regression test（隔離 fixture repo 方式）
#
# カバー範囲:
#   T1 整合した台帳 → PASS exit 0
#   T2 台帳が指す skill が存在しない → FAIL (C3)
#   T3 depends_on の参照先 id が無い → FAIL (C4)
#   T4 rubric に無い項目番号 → FAIL (C5)
#   T5 SKILL.md の metadata.provenance が台帳と不一致 → FAIL (C6)
#   T6 台帳未登録の skill に metadata.provenance がある → FAIL (C6)
#   T7 --report は常に exit 0
#   T8 未定義の provenance level → FAIL (C2)
#   T9 id 重複 → FAIL (C7)
#   T10 同一 skill を異なる provenance の element が二重所有 → FAIL (C8)
#   T11 related_skills 経由の参照は所有とみなさない → PASS
#   T12-T14 rubric の要素 id 列と台帳の双方向整合 (C9)
#   T15-T17 operational-knowhow.md の provenance 行と台帳の整合 (C10)
#   T18 同一 provenance でも skill の二重所有は FAIL (C8 強化)
#   T19-T20 files[] の実在検査 (C3)
#   T21-T25 --selection での harness-selection.json 検証 (C11)
#   T26 metadata.provenance: mixed は agent-harness-bootstrap 以外で FAIL (C6)
#   T27 C10 は複数ファイル（コロン区切り）を検査
#   T28-T30 skill-group の部分選択（skills[] 必須・部分集合）(C11)
#   T31-T32 decided_by:excluded ⇔ repo-specific の対応 (C11)
#   T33 cwd 非依存（別ディレクトリから絶対パスで実行）
#   T34-T44 --target の契約検査 (C12): マーカー残存・混入・paths:・import・.setup-automate gitignore・official 必須・抜け
#   T45 実台帳の契約自己検査（contract-selfcheck.sh が default 選択で PASS）
# 実行: bash .claude/skills/agent-harness-bootstrap/scripts/provenance-check.test.sh

set -uo pipefail
CHECK="$(cd "$(dirname "$0")" && pwd)/provenance-check.sh"
PASS=0; FAIL=0
t() { # $1=name $2=expect $3=actual
  if [[ "$2" == "$3" ]]; then PASS=$((PASS+1)); echo "ok - $1"
  else FAIL=$((FAIL+1)); echo "NOT OK - $1 (expect=$2 got=$3)"; fi
}

FIX=$(mktemp -d) || { echo "FATAL: mktemp failed"; exit 1; }
trap 'rm -rf "$FIX"' EXIT
cd "$FIX" || { echo "FATAL: cd fixture failed"; exit 1; }
export PROVENANCE_ROOT="$FIX"   # 既定の skills / commands / files[] 解決先を fixture に向ける
export PROVENANCE_KNOWHOW="$FIX/harness/knowhow.md"   # 既定（移植元の operational-knowhow.md 等）を fixture 側に向ける（無ければ C10 はスキップ）
mkdir -p .claude/skills/alpha .claude/skills/beta .claude/commands harness

write_skill() { # $1=name $2=provenance or "" (no metadata)
  if [[ -n "$2" ]]; then
    printf -- '---\nname: %s\ndescription: x\nmetadata:\n  provenance: %s\n---\n# %s\n' "$1" "$2" "$1" > ".claude/skills/$1/SKILL.md"
  else
    printf -- '---\nname: %s\ndescription: x\n---\n# %s\n' "$1" "$1" > ".claude/skills/$1/SKILL.md"
  fi
}
write_skill alpha author-preference
write_skill beta ""
echo "# cmd" > .claude/commands/rev.md
write_rubric() { # $1 = 全行に付ける要素 id
  cat > harness/rubric.md <<EOF
| # | 項目 | 要素 id | Y/N |
|---|------|--------|-----|
| 1 | a | $1 |  |
| 2 | b | $1 |  |
| 28b | c | $1 |  |
EOF
}
write_rubric core

write_manifest() { # $1 = elements JSON array body
  cat > harness/provenance.json <<EOF
{
  "schema": "harness-provenance/v1",
  "provenance_levels": {
    "official": {"default_selection": "include"},
    "author-preference": {"default_selection": "ask"},
    "repo-specific": {"default_selection": "exclude"}
  },
  "elements": [ $1 ]
}
EOF
}
run() { PROVENANCE_MANIFEST=harness/provenance.json PROVENANCE_RUBRIC=harness/rubric.md bash "$CHECK" "$@" >/dev/null 2>&1; echo $?; }

GOOD='{"id":"core","provenance":"official","rubric_items":[1,2,"28b"],"depends_on":[]},
       {"id":"skill-alpha","provenance":"author-preference","skills":["alpha"],"commands":["rev"],"depends_on":["core"]}'

write_manifest "$GOOD"
t "T1 整合した台帳は PASS" 0 "$(run)"

write_manifest '{"id":"core","provenance":"official","skills":["ghost"]}'
t "T2 存在しない skill 参照は FAIL" 1 "$(run)"

write_manifest '{"id":"core","provenance":"official","depends_on":["nowhere"]}'
t "T3 存在しない depends_on は FAIL" 1 "$(run)"

write_manifest '{"id":"core","provenance":"official","rubric_items":[99]}'
t "T4 rubric に無い項目番号は FAIL" 1 "$(run)"

write_manifest '{"id":"skill-alpha","provenance":"official","skills":["alpha"]}'
t "T5 metadata.provenance 不一致は FAIL" 1 "$(run)"

write_manifest "$GOOD"
write_skill beta author-preference
t "T6 台帳未登録 skill の metadata.provenance は FAIL" 1 "$(run)"
write_skill beta ""

write_manifest '{"id":"core","provenance":"official","skills":["ghost"]}'
t "T7 --report は常に exit 0" 0 "$(run --report)"

write_manifest '{"id":"core","provenance":"unknown-level"}'
t "T8 未定義 level は FAIL" 1 "$(run)"

write_manifest '{"id":"core","provenance":"official"},{"id":"core","provenance":"official"}'
t "T9 id 重複は FAIL" 1 "$(run)"

write_manifest '{"id":"a","provenance":"author-preference","skills":["alpha"]},{"id":"b","provenance":"official","skills":["alpha"]}'
t "T10 同一 skill を異なる provenance で二重所有は FAIL" 1 "$(run)"

write_rubric a
write_manifest '{"id":"a","provenance":"author-preference","skills":["alpha"],"rubric_items":[1,2,"28b"]},{"id":"b","provenance":"official","related_skills":["alpha"]}'
t "T11 related_skills 経由の参照は所有とみなさず PASS" 0 "$(run)"

# C9: rubric の id 列（逆方向）。以降の台帳は alpha を所有しないので metadata を外して C6 を切り離す
write_skill alpha ""
cat > harness/rubric.md <<'EOF'
| # | 項目 | 要素 id | Y/N |
|---|------|--------|-----|
| 1 | a | core |  |
| 2 | b（`x\|y` を含む） | core / extra |  |
EOF
write_manifest '{"id":"core","provenance":"official","rubric_items":[1,2]},{"id":"extra","provenance":"official","rubric_items":[2]}'
t "T12 rubric id 列と台帳が双方向に整合すれば PASS（エスケープ済み \\| はセル区切り扱いしない）" 0 "$(run)"
write_manifest '{"id":"core","provenance":"official","rubric_items":[1,2]},{"id":"extra","provenance":"official","rubric_items":[]}'
t "T13 rubric id 列にあるが台帳の rubric_items に無い（片方向 drift）は FAIL" 1 "$(run)"
write_manifest '{"id":"core","provenance":"official","rubric_items":[1,2]}'
t "T14 rubric id 列に台帳に無い id があれば FAIL" 1 "$(run)"

# C10: operational-knowhow.md の provenance 行
cat > harness/rubric.md <<'EOF'
| # | 項目 | 要素 id | Y/N |
|---|------|--------|-----|
| 1 | a | core |  |
EOF
write_manifest '{"id":"core","provenance":"official","rubric_items":[1]},{"id":"pref","provenance":"author-preference"}'
printf '### x\n\n> provenance: author-preference · id: pref\n\n### y\n\n> provenance: official · id: core（補足）\n' > harness/knowhow.md
runk() { PROVENANCE_MANIFEST=harness/provenance.json PROVENANCE_RUBRIC=harness/rubric.md PROVENANCE_KNOWHOW=harness/knowhow.md bash "$CHECK" "$@" >/dev/null 2>&1; echo $?; }
t "T15 knowhow の provenance 行が台帳と一致すれば PASS" 0 "$(runk)"
printf '### x\n\n> provenance: official · id: pref\n' > harness/knowhow.md
t "T16 knowhow の provenance 行の level が台帳と不一致なら FAIL" 1 "$(runk)"
printf '### x\n\n> provenance: author-preference · id: ghost\n' > harness/knowhow.md
t "T17 knowhow の provenance 行の id が台帳に無ければ FAIL" 1 "$(runk)"
rm -f harness/knowhow.md   # 以降のテストに C10 の残骸を持ち込まない

# C8 強化: provenance が同じでも二重所有は FAIL
write_rubric core
write_skill alpha author-preference
write_manifest '{"id":"core","provenance":"official","rubric_items":[1,2,"28b"]},{"id":"a","provenance":"author-preference","skills":["alpha"]},{"id":"b","provenance":"author-preference","skills":["alpha"]}'
t "T18 同一 provenance でも skill の二重所有は FAIL" 1 "$(run)"

# C3: files[]
write_manifest '{"id":"core","provenance":"official","rubric_items":[1,2,"28b"]},{"id":"a","provenance":"author-preference","skills":["alpha"],"files":["shared/rubric.yaml"]}'
t "T19 files[] のパスが存在しなければ FAIL" 1 "$(run)"
mkdir -p shared && echo "x: 1" > shared/rubric.yaml
t "T20 files[] のパスが存在すれば PASS" 0 "$(run)"

# C11: --selection
write_manifest '{"id":"core","provenance":"official","rubric_items":[1,2,"28b"]},{"id":"a","provenance":"author-preference","skills":["alpha"],"files":["shared/rubric.yaml"],"depends_on":["core"],"soft_depends_on":["rs"]},{"id":"rs","provenance":"repo-specific"}'
write_sel() { printf '{"schema":"harness-selection/v1","decided_by":"user","selections":{%s}}' "$1" > harness/sel.json; }
runs() { PROVENANCE_MANIFEST=harness/provenance.json PROVENANCE_RUBRIC=harness/rubric.md bash "$CHECK" --selection harness/sel.json >/dev/null 2>&1; echo $?; }
write_sel '"core":{"selected":true,"decided_by":"default"},"a":{"selected":true,"decided_by":"user"},"rs":{"selected":false,"decided_by":"excluded"}'
t "T21 全要素を網羅し依存も満たす selection は PASS（soft_depends_on 欠落は WARN のみ）" 0 "$(runs)"
write_sel '"core":{"selected":true,"decided_by":"default"},"a":{"selected":true,"decided_by":"user"}'
t "T22 selection に無い要素があれば FAIL" 1 "$(runs)"
write_sel '"core":{"selected":false,"decided_by":"user"},"a":{"selected":true,"decided_by":"user"},"rs":{"selected":false,"decided_by":"excluded"}'
t "T23 depends_on が非選択なら FAIL" 1 "$(runs)"
write_sel '"core":{"selected":true,"decided_by":"default"},"a":{"selected":false,"decided_by":"scale"},"rs":{"selected":true,"decided_by":"user"}'
t "T24 repo-specific を selected:true にすると FAIL" 1 "$(runs)"
write_sel '"core":{"selected":true,"decided_by":"maybe"},"a":{"selected":false,"decided_by":"scale"},"rs":{"selected":false,"decided_by":"excluded"}'
t "T25 decided_by の値域外は FAIL" 1 "$(runs)"

# C6: mixed は台帳保持者のみ / C10: 複数ファイル
write_rubric core
write_manifest '{"id":"core","provenance":"official","rubric_items":[1,2,"28b"]}'
write_skill alpha mixed
t "T26 agent-harness-bootstrap 以外の metadata.provenance: mixed は FAIL" 1 "$(run)"
write_skill alpha ""
printf '> provenance: official · id: core\n' > harness/k1.md
printf '> provenance: author-preference · id: core\n' > harness/k2.md
runk2() { PROVENANCE_MANIFEST=harness/provenance.json PROVENANCE_RUBRIC=harness/rubric.md PROVENANCE_KNOWHOW=harness/k1.md:harness/k2.md bash "$CHECK" >/dev/null 2>&1; echo $?; }
t "T27 C10 はコロン区切りの複数ファイルを検査する（2 つ目の不一致で FAIL）" 1 "$(runk2)"

# C11: skill-group の部分選択 / excluded の対応 / cwd 非依存
write_manifest '{"id":"core","provenance":"official","rubric_items":[1,2,"28b"]},{"id":"grp","kind":"skill-group","provenance":"author-preference","skills":["alpha"]},{"id":"rs","provenance":"repo-specific"}'
write_skill alpha author-preference
write_sel '"core":{"selected":true,"decided_by":"default"},"grp":{"selected":true,"decided_by":"user"},"rs":{"selected":false,"decided_by":"excluded"}'
t "T28 skill-group を selected:true にして skills[] が無ければ FAIL" 1 "$(runs)"
write_sel '"core":{"selected":true,"decided_by":"default"},"grp":{"selected":true,"decided_by":"user","skills":["ghost"]},"rs":{"selected":false,"decided_by":"excluded"}'
t "T29 skills[] に要素に無い skill があれば FAIL" 1 "$(runs)"
write_sel '"core":{"selected":true,"decided_by":"default"},"grp":{"selected":true,"decided_by":"user","skills":["alpha"]},"rs":{"selected":false,"decided_by":"excluded"}'
t "T30 skills[] が部分集合なら PASS" 0 "$(runs)"
write_sel '"core":{"selected":false,"decided_by":"excluded"},"grp":{"selected":false,"decided_by":"user","skills":["alpha"]},"rs":{"selected":false,"decided_by":"excluded"}'
t "T31 群 D 以外に decided_by:excluded を使うと FAIL" 1 "$(runs)"
write_sel '"core":{"selected":true,"decided_by":"default"},"grp":{"selected":false,"decided_by":"user"},"rs":{"selected":false,"decided_by":"user"}'
t "T32 群 D が excluded 以外なら FAIL" 1 "$(runs)"
write_sel '"core":{"selected":true,"decided_by":"default"},"grp":{"selected":true,"decided_by":"user","skills":["alpha"]},"rs":{"selected":false,"decided_by":"excluded"}'
t "T33 別 cwd（/）から絶対パス指定で実行しても PASS（cwd 非依存）" 0 "$(cd / && PROVENANCE_MANIFEST="$FIX/harness/provenance.json" PROVENANCE_RUBRIC="$FIX/harness/rubric.md" bash "$CHECK" --selection "$FIX/harness/sel.json" >/dev/null 2>&1; echo $?)"

# C12: --target（生成物の契約検査）。beta は rs（repo-specific）が所有するので metadata を合わせる
mkdir -p tgt/.claude/rules tgt/.claude/skills
write_skill beta repo-specific
write_manifest '{"id":"core","provenance":"official","rubric_items":[1,2,"28b"],"target_contract":{"when_selected":[{"type":"file_exists","path":"CLAUDE.md"},{"type":"grep_absent","path":"CLAUDE.md","pattern":"<!-- id:"},{"type":"emphasis_max","path":"CLAUDE.md","max":5}],"when_unselected":[]}},{"id":"split","provenance":"official","target_contract":{"when_selected":[{"type":"file_exists","path":".claude/rules/code-quality.md"},{"type":"import","path":".claude/rules/code-quality.md"},{"type":"frontmatter_paths","path":".claude/rules/review.md"}],"when_unselected":[]}},{"id":"issue","provenance":"author-preference","target_contract":{"when_selected":[{"type":"grep","path":".claude/rules","pattern":"issues/open"}],"when_unselected":[{"type":"grep_absent","path":"CLAUDE.md","pattern":"issues/open"},{"type":"dir_absent","path":"issues"}]}},{"id":"grp","kind":"skill-group","provenance":"author-preference","skills":["alpha"]},{"id":"rs","provenance":"repo-specific","skills":["beta"]}'
write_sel_t() { printf '{"schema":"harness-selection/v1","decided_by":"user","selections":{%s}}' "$1" > tgt/.claude/harness-selection.json; }
runt() { PROVENANCE_MANIFEST=harness/provenance.json PROVENANCE_RUBRIC=harness/rubric.md bash "$CHECK" --target tgt >/dev/null 2>&1; echo $?; }
write_sel_t '"core":{"selected":true,"decided_by":"default"},"split":{"selected":true,"decided_by":"default"},"issue":{"selected":false,"decided_by":"user"},"grp":{"selected":false,"decided_by":"user"},"rs":{"selected":false,"decided_by":"excluded"}'
printf '# CLAUDE.md\n\n@.claude/rules/code-quality.md\n\n## ルート構成\nIMPORTANT: x\n' > tgt/CLAUDE.md
printf -- '---\ndescription: cq\n---\n# cq\n' > tgt/.claude/rules/code-quality.md
printf -- '---\ndescription: r\npaths:\n  - "**/*.ts"\n---\n# review\n' > tgt/.claude/rules/review.md
t "T34 契約を満たす生成物は PASS" 0 "$(runt)"
printf '# CLAUDE.md\n<!-- id: core -->\n@.claude/rules/code-quality.md\n' > tgt/CLAUDE.md
t "T35 id マーカーが残っていれば FAIL" 1 "$(runt)"
printf '# CLAUDE.md\n\n@.claude/rules/code-quality.md\n' > tgt/CLAUDE.md
mkdir -p tgt/issues
t "T36 非選択要素のディレクトリ（issues/）があれば FAIL（混入）" 1 "$(runt)"
rmdir tgt/issues
printf -- '---\ndescription: r\n---\n# review\n' > tgt/.claude/rules/review.md
t "T37 path-scope rules に paths: が無ければ FAIL" 1 "$(runt)"
printf -- '---\ndescription: r\npaths:\n  - "**/*.ts"\n---\n# review\n' > tgt/.claude/rules/review.md
mkdir -p tgt/.claude/skills/alpha && echo "---" > tgt/.claude/skills/alpha/SKILL.md
t "T38 非選択 skill が対象にあれば FAIL（混入）" 1 "$(runt)"
rm -rf tgt/.claude/skills/alpha
printf '# CLAUDE.md\n\n## x\n' > tgt/CLAUDE.md
t "T39 選択要素の import 行が無ければ FAIL（名ばかり常時 load）" 1 "$(runt)"
printf '# CLAUDE.md\n\n@.claude/rules/code-quality.md\n' > tgt/CLAUDE.md
mkdir -p tgt/.setup-automate
t "T40 .setup-automate/ があるのに .gitignore 未登録なら FAIL" 1 "$(runt)"
printf '.setup-automate/\n' > tgt/.gitignore
t "T41 .gitignore に登録すれば PASS" 0 "$(runt)"
write_sel_t '"core":{"selected":false,"decided_by":"user"},"split":{"selected":true,"decided_by":"default"},"issue":{"selected":false,"decided_by":"user"},"grp":{"selected":false,"decided_by":"user"},"rs":{"selected":false,"decided_by":"excluded"}'
t "T42 official 要素を selected:false にすると FAIL（公式由来は外せない）" 1 "$(runt)"
write_sel_t '"core":{"selected":true,"decided_by":"default"},"split":{"selected":true,"decided_by":"default"},"issue":{"selected":true,"decided_by":"user"},"grp":{"selected":false,"decided_by":"user"},"rs":{"selected":false,"decided_by":"excluded"}'
t "T43 選択した要素の契約語句（issues/open）が rules に無ければ FAIL（抜け）" 1 "$(runt)"
printf -- '---\ndescription: iw\npaths:\n  - "issues/**"\n---\n# issue-workflow\nissues/open に起票\n' > tgt/.claude/rules/issue-workflow.md
t "T44 契約語句を含めれば PASS" 0 "$(runt)"

# 実台帳の契約自己検査（default 選択で契約が満たせる・矛盾しない）。fixture ではなく本リポジトリの台帳で走る
t "T45 実台帳: default 選択の target_contract は満たせて矛盾しない（contract-selfcheck.sh）" 0 "$(env -u PROVENANCE_ROOT -u PROVENANCE_KNOWHOW bash "$(dirname "$CHECK")/contract-selfcheck.sh" >/dev/null 2>&1; echo $?)"

echo "---"
echo "PASS=$PASS FAIL=$FAIL"
[[ $FAIL -eq 0 ]]
