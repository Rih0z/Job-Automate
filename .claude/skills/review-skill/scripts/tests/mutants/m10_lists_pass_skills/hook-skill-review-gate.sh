#!/usr/bin/env bash
# 変異体 10（ほぼ正しい hook・1 箇所だけ違う）: PASS 済みの skill まで block の reason に列挙する（全 skill 名を reason に足す）。
# 本物の hook が必要。狙う試験: test_stop_hook_blocks_with_skill_names_and_one_at_a_time_instruction
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REAL="$DIR/../../../hook-skill-review-gate.sh"
[ -f "$REAL" ] || { echo "MUTANT_NEEDS_REAL: 本物の実装が無い: $REAL" >&2; exit 97; }
ROOT="${SKILL_REVIEW_REPO_ROOT:-$CLAUDE_PROJECT_DIR}"
NAMES="$(ls "$ROOT/.claude/skills" 2>/dev/null | grep -v '^_' | tr '\n' ' ')"
out="$(bash "$REAL")"
printf '%s' "$out" | sed "s/\"reason\": *\"/&$NAMES/"
