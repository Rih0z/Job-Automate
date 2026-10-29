#!/usr/bin/env bash
# 変異体 9（ほぼ正しい hook・1 箇所だけ違う）: 新しい turn でカウンタを 0 に戻さない（stop_hook_active を常に true として本物の hook に渡す）。
# 本物の hook が必要。狙う試験: test_stop_hook_blocks_up_to_three_times_per_turn_then_allows_on_the_fourth
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REAL="$DIR/../../../hook-skill-review-gate.sh"
[ -f "$REAL" ] || { echo "MUTANT_NEEDS_REAL: 本物の実装が無い: $REAL" >&2; exit 97; }
input="$(cat 2>/dev/null || true)"
printf '%s' "$input" | sed 's/"stop_hook_active": *false/"stop_hook_active": true/' | bash "$REAL"
