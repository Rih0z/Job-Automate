#!/usr/bin/env bash
# 変異体 11（ほぼ正しい hook・1 箇所だけ違う）: SessionStart でも block する。Stop は本物へ渡す。
# 本物の hook が必要。狙う試験: test_session_start_hook_reports_counts_without_blocking
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REAL="$DIR/../../../hook-skill-review-gate.sh"
[ -f "$REAL" ] || { echo "MUTANT_NEEDS_REAL: 本物の実装が無い: $REAL" >&2; exit 97; }
input="$(cat 2>/dev/null || true)"
case "$input" in
  *SessionStart*) echo '{"decision":"block","reason":"SessionStart でも block する誤った実装"}' ;;
  *) printf '%s' "$input" | bash "$REAL" ;;
esac
