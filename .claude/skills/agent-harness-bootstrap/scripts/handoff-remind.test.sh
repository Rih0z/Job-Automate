#!/usr/bin/env bash
# handoff-remind.sh の試験。実行: bash .claude/skills/agent-harness-bootstrap/scripts/handoff-remind.test.sh
#   H0 fixture の mtime を 40 日前にできている（以降のケースの前提）
#   H1 未受領で古い handoff があれば名前が出て exit 0
#   H2 .tmp/handoffs が無ければ出力なしで exit 0
#   H3 python が見つからなければ出力なしで exit 0
#   H4 .claude/handoff-lifecycle.json があれば --config を渡し、案内にも入る
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$HERE/handoff-remind.sh"
BASH_BIN="$BASH"
PASS=0; FAIL=0
t() { if [[ "$2" == "$3" ]]; then echo "ok - $1"; PASS=$((PASS+1)); else echo "NOT OK - $1 (expect=[$2] got=[$3])"; FAIL=$((FAIL+1)); fi; }
FIX="$(mktemp -d)"; trap 'rm -rf "$FIX"' EXIT
# mtime を N 日前にする。touch -d の相対日時は GNU だけなので、python の os.utime を先に使う
PY=""
for cand in python3 python py; do
  p="$(command -v "$cand" 2>/dev/null)" || continue
  case "$p" in */WindowsApps/*|*\\WindowsApps\\*) continue ;; esac
  if "$cand" -c "print(1)" >/dev/null 2>&1; then PY="$cand"; break; fi
done
age_days() { # $1=file $2=days
  if [[ -n "$PY" ]]; then
    "$PY" -c 'import os,sys,time; t=time.time()-int(sys.argv[2])*86400; os.utime(sys.argv[1],(t,t))' "$1" "$2"
  else
    touch -d "$2 days ago" "$1"
  fi
}
older_than_days() { # $1=file $2=days → 1 / 0
  if [[ -n "$PY" ]]; then
    "$PY" -c 'import os,sys,time; print(1 if os.stat(sys.argv[1]).st_mtime < time.time()-int(sys.argv[2])*86400 else 0)' "$1" "$2"
  else
    find "$1" -mtime +"$2" | grep -c .
  fi
}

mkdir -p "$FIX/p1/.tmp/handoffs"
printf '# old\nBODY-MARKER-XYZ\n' > "$FIX/p1/.tmp/handoffs/old-one.md"
age_days "$FIX/p1/.tmp/handoffs/old-one.md" 40
t "H0 fixture の mtime が 30 日より前になっている" 1 "$(older_than_days "$FIX/p1/.tmp/handoffs/old-one.md" 30)"
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

mkdir -p "$FIX/p4/.tmp/handoffs" "$FIX/p4/.claude" "$FIX/p4/issues"
printf '# old
' > "$FIX/p4/.tmp/handoffs/old-four.md"
age_days "$FIX/p4/.tmp/handoffs/old-four.md" 40
printf '{"handoffs_dir": ".tmp/handoffs", "keep_referenced": ["issues"]}' > "$FIX/p4/.claude/handoff-lifecycle.json"
out="$(CLAUDE_PROJECT_DIR="$FIX/p4" "$BASH_BIN" "$HOOK" 2>/dev/null)"; rc=$?
t "H4 exit 0" 0 "$rc"
t "H4 config があれば案内に --config が入る" 1 "$(grep -c 'sweep --config' <<<"$out")"

echo "---"
echo "PASS=$PASS FAIL=$FAIL"
[[ $FAIL -eq 0 ]]
