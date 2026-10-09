#!/usr/bin/env bash
# test_new_checks.sh — harness_check.sh の R01（rules は paths のみ）/ A02・A03（subagent）/ S12（長い参照ファイルの目次）/
# H03（settings の $schema）/ H04（hook timeout）と、reference/checks.json ⇔ harness_check.sh の check id 対応の回帰テスト。
# 一時ディレクトリに fixture を作り、そこを cwd にして harness_check.sh にパスを渡す（git 管理外なので pwd がルートになる）。
# 使い方: bash test_new_checks.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
SCRIPT="$HERE/harness_check.sh"
CHECKS_JSON="$HERE/../reference/checks.json"
PASS=0; FAIL=0
ok() { PASS=$((PASS+1)); echo "PASS: $1"; }
ng() { FAIL=$((FAIL+1)); echo "FAIL: $1"; [ -n "${2:-}" ] && printf '  %s\n' "$2"; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
cd "$TMP" || exit 2
export GIT_CEILING_DIRECTORIES="$(dirname "$TMP")"   # 上位の git リポジトリを拾わない
PY=""; for c in python3 python py; do command -v "$c" >/dev/null 2>&1 && "$c" -c 'print(1)' >/dev/null 2>&1 && { PY="$c"; break; }; done
mkdir -p .claude/rules .claude/agents .claude/skills/demo/references

run() { bash "$SCRIPT" "$@" 2>/dev/null; }
# expect <name> <id> <status> <file> — 該当行がちょうど存在するか
expect() {
  local out; out="$(run "$4" | awk -F'\t' -v id="$2" -v f="$4" '$2==id && $4==f {print $3}')"
  if [ "$out" = "$3" ]; then ok "$1"; else ng "$1" "id=$2 file=$4 expected=$3 actual=[$out]"; fi
}
# expect_none <name> <id> <file> — 該当 id の行が出ない
expect_none() {
  local out; out="$(run "$3" | awk -F'\t' -v id="$2" '$2==id')"
  if [ -z "$out" ]; then ok "$1"; else ng "$1" "unexpected: $out"; fi
}
lines() { for i in $(seq 1 "$1"); do echo "line $i"; done; }

# ---- R01: rules frontmatter は paths のみ ----
printf -- '---\npaths:\n  - "src/**/*.ts"\n---\n# r\n' > .claude/rules/p.md
expect "B1 rules frontmatter が paths のみ → R01 PASS" R01 PASS .claude/rules/p.md
printf -- '---\ndescription: x\npaths:\n  - "a"\n---\n# r\n' > .claude/rules/d.md
expect "B2 rules frontmatter に description → R01 WARN" R01 WARN .claude/rules/d.md
printf '# no frontmatter\n' > .claude/rules/n.md
expect "B3 rules frontmatter 無し → R01 PASS" R01 PASS .claude/rules/n.md

# ---- A01/A02/A03: subagent ----
printf -- '---\nname: x:y\ndescription: d\ntools: Read\n---\nbody\n' > .claude/agents/colon.md
expect "B4 agent name に ':' → A02 FAIL" A02 FAIL .claude/agents/colon.md
expect "B4 A01 は PASS のまま" A01 PASS .claude/agents/colon.md
printf -- '---\nname: all\ndescription: d\n---\nbody\n' > .claude/agents/all.md
expect "B5 tools も disallowedTools も無し → A03 WARN" A03 WARN .claude/agents/all.md
printf -- '---\nname: ro\ndescription: d\ntools: Read, Grep\n---\nbody\n' > .claude/agents/ro.md
expect "B6 tools あり → A03 PASS" A03 PASS .claude/agents/ro.md
printf -- '---\nname: dis\ndescription: d\ndisallowedTools: Write\n---\nbody\n' > .claude/agents/dis.md
expect "B6b disallowedTools のみ → A03 PASS" A03 PASS .claude/agents/dis.md

# ---- S12: 100 行超の参照ファイルの目次 ----
R=.claude/skills/demo/references
lines 120 > $R/long.md
expect "B7 120 行・目次なし → S12 WARN" S12 WARN $R/long.md
{ echo "# T"; echo "## 目次"; lines 118; } > $R/toc.md
expect "B8 120 行・目次見出しあり → S12 PASS" S12 PASS $R/toc.md
lines 80 > $R/short.md
expect "B9 80 行 → S12 PASS" S12 PASS $R/short.md
lines 100 > $R/hundred.md
expect "B9b 100 行ちょうど → S12 PASS" S12 PASS $R/hundred.md
lines 101 > $R/h101.md
expect "B9c 101 行・目次なし → S12 WARN" S12 WARN $R/h101.md
{ echo "# T"; echo "- [A](#a)"; echo "- [B](#b)"; echo "- [C](#c)"; lines 117; } > $R/links.md
expect "B9d 先頭にリンク列挙 3 行 → S12 PASS" S12 PASS $R/links.md
lines 120 > .claude/skills/demo/README.md
expect_none "B10 README.md は S12 対象外" S12 .claude/skills/demo/README.md
{ lines 31; echo "## 目次"; lines 90; } > $R/late.md
expect "B9e 目次見出しが 31 行目以降 → S12 WARN" S12 WARN $R/late.md
{ echo "# T"; echo "## Contents"; lines 118; } > $R/en.md
expect "B9f '## Contents' 見出し → S12 PASS" S12 PASS $R/en.md
{ echo "# T"; echo "## Table of Contents"; lines 118; } > $R/en2.md
expect "B9g '## Table of Contents' 見出し → S12 PASS" S12 PASS $R/en2.md
{ printf -- '---
name: demo
description: Use when testing.
---
'; lines 120; } > .claude/skills/demo/SKILL.md
expect_none "B10b SKILL.md は S12 対象外" S12 .claude/skills/demo/SKILL.md

# ---- H03/H04: settings ----
printf '{"hooks":{"Stop":[{"hooks":[{"type":"command","command":"echo hi"}]}]}}' > .claude/settings.json
expect "B11 \$schema なし → H03 WARN" H03 WARN .claude/settings.json
expect "B13 hook に timeout なし → H04 WARN" H04 WARN .claude/settings.json
printf '{"$schema":"https://json.schemastore.org/claude-code-settings.json","hooks":{"Stop":[{"hooks":[{"type":"command","command":"echo hi","timeout":30}]}]}}' > .claude/settings.json
expect "B12 \$schema あり → H03 PASS" H03 PASS .claude/settings.json
expect "B14 全 hook に timeout → H04 PASS" H04 PASS .claude/settings.json
printf '{"$schema":"x","hooks":{"Stop":[{"hooks":[{"type":"command","command":"echo a","timeout":30}]}],"SessionStart":[{"hooks":[{"type":"command","command":"echo b"}]}]}}' > .claude/settings.json
expect "B14b 一部の hook だけ timeout → H04 WARN" H04 WARN .claude/settings.json

# ---- B15: checks.json ⇔ harness_check.sh ----
if [ ! -f "$CHECKS_JSON" ]; then
  ng "B15 reference/checks.json が存在する" "missing: $CHECKS_JSON"
else
  js="$("$PY" -c 'import json,sys; print("\n".join(sorted(c["id"] for c in json.load(open(sys.argv[1],encoding="utf-8"))["checks"])))' "$CHECKS_JSON" 2>/dev/null | tr -d '\r')"
  sh="$(grep -oE 'emit [A-Z]+[0-9]{2}' "$SCRIPT" | awk '{print $2}' | sort -u)"
  if [ -n "$js" ] && [ "$js" = "$sh" ]; then ok "B15 checks.json と harness_check.sh の check id が一致"
  else ng "B15 checks.json と harness_check.sh の check id が一致" "diff: $(diff <(echo "$js") <(echo "$sh") | tr '\n' ' ')"; fi
fi

echo "SUMMARY PASS=$PASS FAIL=$FAIL"
[ "$FAIL" -eq 0 ]
