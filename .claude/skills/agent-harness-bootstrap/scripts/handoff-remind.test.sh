#!/usr/bin/env bash
# handoff-remind.sh の試験。実行: bash .claude/skills/agent-harness-bootstrap/scripts/handoff-remind.test.sh
#   H1 未受領で古い handoff があれば名前が出て exit 0
#   H2 .tmp/handoffs が無ければ出力なしで exit 0
#   H3 python が見つからなければ出力なしで exit 0
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$HERE/handoff-remind.sh"
BASH_BIN="$BASH"
PASS=0; FAIL=0
t() { if [[ "$2" == "$3" ]]; then echo "ok - $1"; PASS=$((PASS+1)); else echo "NOT OK - $1 (expect=[$2] got=[$3])"; FAIL=$((FAIL+1)); fi; }
FIX="$(mktemp -d)"; trap 'rm -rf "$FIX"' EXIT

mkdir -p "$FIX/p1/.tmp/handoffs"
printf '# old\nBODY-MARKER-XYZ\n' > "$FIX/p1/.tmp/handoffs/old-one.md"
touch -d '40 days ago' "$FIX/p1/.tmp/handoffs/old-one.md"
out="$(CLAUDE_PROJECT_DIR="$FIX/p1" "$BASH_BIN" "$HOOK" 2>/dev/null)"; rc=$?
t "H1 exit 0" 0 "$rc"
t "H1 名前が出る" 1 "$(grep -c 'old-one.md' <<<"$out")"
t "H1 本文は出ない" 0 "$(grep -c 'BODY-MARKER-XYZ' <<<"$out")"

mkdir -p "$FIX/p2"
out="$(CLAUDE_PROJECT_DIR="$FIX/p2" "$BASH_BIN" "$HOOK" 2>&1)"; rc=$?
t "H2 exit 0" 0 "$rc"
t "H2 出力なし" "" "$out"

out="$(PATH="/nonexistent" CLAUDE_PROJECT_DIR="$FIX/p1" "$BASH_BIN" "$HOOK" 2>&1)"; rc=$?
t "H3 exit 0" 0 "$rc"
t "H3 出力なし" "" "$out"

echo "---"
echo "PASS=$PASS FAIL=$FAIL"
[[ $FAIL -eq 0 ]]
