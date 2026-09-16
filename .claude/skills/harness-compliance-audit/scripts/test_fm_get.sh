#!/usr/bin/env bash
# test_fm_get.sh — fm_get()/frontmatter() (harness_check.sh) の単体テスト（CR-09）。
# harness_check.sh から frontmatter()/fm_get() の定義だけを抽出して読み込み、
# 実行時に生成する合成フィクスチャ + 本リポジトリの実SKILL.mdに対して抽出結果を検証する。
# 使い方: bash test_fm_get.sh
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../../.." && pwd)"
SCRIPT="$HERE/harness_check.sh"
PASS=0; FAIL=0

# frontmatter()/fm_get() の定義だけを抽出（次の関数 count_lines() の手前まで）
eval "$(awk '/^frontmatter\(\)/{p=1} /^count_lines\(\)/{p=0} p' "$SCRIPT")"
if ! command -v fm_get >/dev/null 2>&1 || ! command -v frontmatter >/dev/null 2>&1; then
  echo "FATAL: harness_check.sh からの frontmatter()/fm_get() 抽出に失敗した（関数境界マーカーがずれている可能性）"
  exit 2
fi

assert_eq() { # name actual expected
  if [ "$2" = "$3" ]; then PASS=$((PASS+1)); echo "PASS: $1"
  else FAIL=$((FAIL+1)); echo "FAIL: $1"; printf '  actual:   [%s]\n' "$2"; printf '  expected: [%s]\n' "$3"; fi
}
assert_contains() { # name haystack needle
  case "$2" in
    *"$3"*) PASS=$((PASS+1)); echo "PASS: $1" ;;
    *) FAIL=$((FAIL+1)); echo "FAIL: $1"; printf '  missing needle: [%s]\n' "$3"; printf '  in: [%s]\n' "$2" ;;
  esac
}

TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

# ---- 合成フィクスチャ ----
cat > "$TMPDIR/block-colon.md" <<'EOF'
---
name: fixture-block-colon
description: |
  Trigger: 'foo', 'bar'.
  Second line without colon.
---
body
EOF

cat > "$TMPDIR/block-strip.md" <<'EOF'
---
name: fixture-block-strip
description: |-
  Line one.
  Line two.
---
EOF

cat > "$TMPDIR/quoted.md" <<'EOF'
---
name: fixture-quoted
description: "Quoted single line text."
---
EOF

cat > "$TMPDIR/missing-desc.md" <<'EOF'
---
name: fixture-missing-desc
---
EOF

cat > "$TMPDIR/nested-metadata.md" <<'EOF'
---
name: fixture-nested-metadata
description: >
  Folded description line one
  continues here.
metadata:
  provenance: author-preference
---
EOF

cat > "$TMPDIR/name-block.md" <<'EOF'
---
name: |
  weird
  name
description: "ok"
---
EOF

cat > "$TMPDIR/empty-line-block.md" <<'EOF'
---
name: fixture-empty-line
description: |
  First paragraph.

  Second paragraph.
---
EOF

cat > "$TMPDIR/rules-style.md" <<'EOF'
---
description: |
  Rule description line one
  line two.
paths:
  - "src/**/*.ts"
---
EOF

cat > "$TMPDIR/commands-style.md" <<'EOF'
---
description: "Command description text"
---
EOF

cat > "$TMPDIR/agents-style.md" <<'EOF'
---
name: my-agent
description: >
  Agent does X and Y
  across multiple lines.
---
EOF

cat > "$TMPDIR/block-plus.md" <<'EOF'
---
name: fixture-block-plus
description: |+
  Kept line one.
  Kept line two.
---
EOF

cat > "$TMPDIR/folded-strip.md" <<'EOF'
---
name: fixture-folded-strip
description: >-
  Folded line one.
  Folded line two.
---
EOF

echo "== 合成フィクスチャ =="
assert_eq "block scalar(|)・コロン混入は空白区切りで連結される" \
  "$(fm_get "$TMPDIR/block-colon.md" description)" \
  "Trigger: 'foo', 'bar'. Second line without colon."

assert_eq "block scalar(|-)でも本文を収集する" \
  "$(fm_get "$TMPDIR/block-strip.md" description)" \
  "Line one. Line two."

assert_eq "quoted 1行値は従来どおりクォートを外して返す（回帰）" \
  "$(fm_get "$TMPDIR/quoted.md" description)" \
  "Quoted single line text."

assert_eq "description 欠落時は空文字列を返す" \
  "$(fm_get "$TMPDIR/missing-desc.md" description)" \
  ""

assert_eq "block scalar(>)の直後の metadata: ネストキーを本文に混入させない" \
  "$(fm_get "$TMPDIR/nested-metadata.md" description)" \
  "Folded description line one continues here."

assert_eq "name に block scalar が来てもクラッシュせず決定的な値を返す" \
  "$(fm_get "$TMPDIR/name-block.md" name)" \
  "weird name"

assert_eq "block scalar 中の空行を含めても破綻しない" \
  "$(fm_get "$TMPDIR/empty-line-block.md" description)" \
  "First paragraph.  Second paragraph."

assert_eq "rules形式(description block, R01と同パターン)でも抽出できる" \
  "$(fm_get "$TMPDIR/rules-style.md" description)" \
  "Rule description line one line two."

assert_eq "commands形式(description 1行, K01と同パターン)でも抽出できる" \
  "$(fm_get "$TMPDIR/commands-style.md" description)" \
  "Command description text"

assert_eq "agents形式(name 1行, A01と同パターン)でも抽出できる" \
  "$(fm_get "$TMPDIR/agents-style.md" name)" \
  "my-agent"
assert_eq "agents形式(description block, A01と同パターン)でも抽出できる" \
  "$(fm_get "$TMPDIR/agents-style.md" description)" \
  "Agent does X and Y across multiple lines."

assert_eq "block scalar(|+)でも本文を収集する（indicator 6種の網羅）" \
  "$(fm_get "$TMPDIR/block-plus.md" description)" \
  "Kept line one. Kept line two."

assert_eq "block scalar(>-)でも本文を収集する（indicator 6種の網羅）" \
  "$(fm_get "$TMPDIR/folded-strip.md" description)" \
  "Folded line one. Folded line two."

echo "== 実ファイル回帰 =="
D_REVIEW_OPS="$(fm_get "$ROOT/.claude/skills/review-ops/SKILL.md" description)"
assert_contains "review-ops: description(block, コロン含有)の先頭が取れる" "$D_REVIEW_OPS" "運用スクリプト・サーバー初期設定・自動化構成・標準化手順"
assert_contains "review-ops: description(block)の末尾が取れる（本文欠落なし）" "$D_REVIEW_OPS" "init.md/automation.md/windows-standard.md の成果物レビュー'."

D_NENMATSU="$(fm_get "$ROOT/.claude/skills/year-end-adjustment-csv/SKILL.md" description)"
assert_contains "year-end-adjustment-csv: description(block, インデント幅違い)の先頭が取れる" "$D_NENMATSU" "給与明細データ・社員基本情報・企業独自項目情報を解析し"
assert_contains "year-end-adjustment-csv: description(block)の末尾が取れる" "$D_NENMATSU" "'year-end adjustment csv'."

D_MCP="$(fm_get "$ROOT/.claude/skills/mcp-server-setup/SKILL.md" description)"
assert_eq "mcp-server-setup: description(quoted 1行)は従来どおり返す（回帰）" "$D_MCP" \
  "Adds Serena MCP (semantic codebase analysis via uvx) or a Windows build-server MCP (node-based, for allowed build paths and dev commands) to a project's .mcp.json. Use when the user asks to 'Serena MCPをセットアップして', 'Windowsビルドサーバーmcpを設定して', '.mcp.jsonにMCPサーバーを追加して', or references serena.md / windows-setup.md."

D_SKILLGUIDE="$(fm_get "$ROOT/.claude/skills/skill-authoring-guide/SKILL.md" description)"
assert_contains "skill-authoring-guide: description(quoted 1行)は従来どおり返す（回帰）" "$D_SKILLGUIDE" "Reference manual (based on Anthropic's official 'The Complete Guide to Building Skills for Claude')"

# 注意: このテストは fm_get() 単体を直接呼んでおり、harness_check.sh:82 の旧 when_to_use
# 専用awk（`next` で1行値を欠落させる既知バグ）の経路は通らない。その旧経路をfm_get()呼び出しに
# 一本化した後、本番コードパス(S05判定)でも同じ値が得られることは実装フェーズでの
# harness_check.sh 全体diff確認（手動）で担保する（このテストは fm_get() 側の前提条件のみ検証する）。
W_BOOTSTRAP="$(fm_get "$ROOT/.claude/skills/agent-harness-bootstrap/SKILL.md" when_to_use)"
assert_contains "agent-harness-bootstrap: fm_get が when_to_use の1行値の先頭を返す（line82一本化後の前提）" "$W_BOOTSTRAP" "CLAUDE.md を作って"
assert_contains "agent-harness-bootstrap: fm_get が when_to_use の1行値の末尾まで欠落させない（line82一本化後の前提）" "$W_BOOTSTRAP" "対象が明示されない曖昧な「セットアップして」は対象外"

W_AUDIT="$(fm_get "$ROOT/.claude/skills/harness-compliance-audit/SKILL.md" when_to_use)"
assert_contains "harness-compliance-audit: when_to_use(block >)の先頭が取れる" "$W_AUDIT" "skill を新しく作った直後"
assert_contains "harness-compliance-audit: when_to_use(block >)の末尾が取れる" "$W_AUDIT" "PostToolUse hook が公式レビューを促したとき。"

echo "SUMMARY PASS=$PASS FAIL=$FAIL"
[ "$FAIL" -gt 0 ] && exit 1 || exit 0
