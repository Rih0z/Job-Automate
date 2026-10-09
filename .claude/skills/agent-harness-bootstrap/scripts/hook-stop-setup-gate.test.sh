#!/usr/bin/env bash
# hook-stop-setup-gate.test.sh — Stop hook（hook-stop-setup-gate.sh）の block 回数制御と通知の回帰テスト
#
# カバー範囲（仕様: 1 turn あたり最大 3 回 block。新しい turn（stop_hook_active=false）でカウンタを 0 に戻す）:
#   A1-A2  state 無し / phase=done → 出力なし
#   A3-A5  新 turn で 1/3、継続で 2/3・3/3（stop_blocks 0→1→2）
#   A6     3 回 block 後は通過し、stdout に systemMessage（decision なし）
#   A7     前 turn で上限到達（stop_blocks=5）でも、新 turn では再び block（回帰: 永続無効化バグ）
#   A8     python 不在でも無音で通過せず systemMessage を出す
#   A9     空 stdin は新 turn 扱い
#   A10    A3-A9 の stdout はすべて JSON として parse できる
#   A11    phase=selecting でも block
#   A12    state.json が壊れていれば出力なしで通過
#   A13    stop_blocks が非数値でも落ちずに 0 扱い
# 実行: bash .claude/skills/agent-harness-bootstrap/scripts/hook-stop-setup-gate.test.sh

set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
HOOK="$HERE/hook-stop-setup-gate.sh"
BASH_BIN="$(command -v bash)"
PASS=0; FAIL=0
PY=""
for c in python3 python py; do
  p="$(command -v "$c" 2>/dev/null)" || continue
  case "$p" in */WindowsApps/*|*\\WindowsApps\\*) continue ;; esac
  "$c" -c "print(1)" >/dev/null 2>&1 && { PY="$c"; break; }
done
[ -n "$PY" ] || { echo "FATAL: テスト実行に python が必要"; exit 2; }
export PYTHONUTF8=1

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export HARNESS_SETUP_STATE_DIR="$TMP/state"
mkdir -p "$HARNESS_SETUP_STATE_DIR"
STATE="$HARNESS_SETUP_STATE_DIR/state.json"
OUTS=()

ok() { PASS=$((PASS+1)); echo "ok - $1"; }
ng() { FAIL=$((FAIL+1)); echo "NG - $1"; [ -n "${2:-}" ] && printf '    %s\n' "$2"; }
check() { # name cond(0/1) detail
  if [ "$2" = 0 ]; then ok "$1"; else ng "$1" "${3:-}"; fi
}
write_state() { # phase stop_blocks(json literal)
  printf '{"phase": "%s", "target": "/tmp/tgt", "stop_blocks": %s}' "$1" "$2" > "$STATE"
}
run_hook() { # stdin-json → stdout を $OUT に
  OUT="$(printf '%s' "$1" | "$BASH_BIN" "$HOOK" 2>/dev/null)"; RC=$?
  OUTS+=("$OUT")
}
jget() { # json key → 値（無ければ空）
  "$PY" -c 'import json,sys
try: d=json.loads(sys.argv[1])
except Exception: print("__PARSE_ERROR__"); sys.exit()
v=d.get(sys.argv[2]); print("" if v is None else v)' "$1" "$2"
}
blocks() { "$PY" -c 'import json,sys; print(json.load(open(sys.argv[1],encoding="utf-8")).get("stop_blocks"))' "$STATE"; }
has() { case "$1" in *"$2"*) echo 0;; *) echo 1;; esac; }

ACTIVE='{"stop_hook_active": true}'
NEW='{"stop_hook_active": false}'

# A1
rm -f "$STATE"; run_hook "$NEW"
check "A1 state 無し → 出力なし・exit 0" "$([ -z "$OUT" ] && [ $RC -eq 0 ] && echo 0 || echo 1)" "out=[$OUT] rc=$RC"
# A2
write_state done 0; run_hook "$NEW"
check "A2 phase=done → 出力なし" "$([ -z "$OUT" ] && echo 0 || echo 1)" "out=[$OUT]"

# A3
write_state generated 0; run_hook "$NEW"
check "A3 新 turn → block（exit 0）" "$([ "$(jget "$OUT" decision)" = block ] && [ $RC -eq 0 ] && echo 0 || echo 1)" "out=[$OUT] rc=$RC"
check "A3 表示 1/3" "$(has "$OUT" '1/3')" "out=[$OUT]"
check "A3 stop_blocks=0" "$([ "$(blocks)" = 0 ] && echo 0 || echo 1)" "blocks=$(blocks)"
# A4
run_hook "$ACTIVE"
check "A4 継続 1 回目 → block 2/3" "$([ "$(jget "$OUT" decision)" = block ] && [ "$(has "$OUT" '2/3')" = 0 ] && echo 0 || echo 1)" "out=[$OUT]"
check "A4 stop_blocks=1" "$([ "$(blocks)" = 1 ] && echo 0 || echo 1)" "blocks=$(blocks)"
# A5
run_hook "$ACTIVE"
check "A5 継続 2 回目 → block 3/3" "$([ "$(jget "$OUT" decision)" = block ] && [ "$(has "$OUT" '3/3')" = 0 ] && echo 0 || echo 1)" "out=[$OUT]"
check "A5 stop_blocks=2" "$([ "$(blocks)" = 2 ] && echo 0 || echo 1)" "blocks=$(blocks)"
# A6
run_hook "$ACTIVE"
check "A6 上限到達 → decision なし（exit 0）" "$([ -z "$(jget "$OUT" decision)" ] && [ $RC -eq 0 ] && echo 0 || echo 1)" "out=[$OUT] rc=$RC"
sm="$(jget "$OUT" systemMessage)"
check "A6 上限到達 → systemMessage で通知" "$([ -n "$sm" ] && [ "$sm" != "__PARSE_ERROR__" ] && echo 0 || echo 1)" "out=[$OUT]"
check "A6 stop_blocks=3" "$([ "$(blocks)" = 3 ] && echo 0 || echo 1)" "blocks=$(blocks)"

# A7（回帰）
write_state generated 5; run_hook "$NEW"
check "A7 前 turn で上限到達でも新 turn では block" "$([ "$(jget "$OUT" decision)" = block ] && [ "$(has "$OUT" '1/3')" = 0 ] && [ $RC -eq 0 ] && echo 0 || echo 1)" "out=[$OUT] rc=$RC"
check "A7 stop_blocks を 0 にリセット" "$([ "$(blocks)" = 0 ] && echo 0 || echo 1)" "blocks=$(blocks)"

# A8: python の無い PATH（必要な coreutils だけを置いた一時ディレクトリ）。
#   前提: hook の python 不在時の分岐は cat / dirname 以外の外部コマンドを使わず、固定文字列の JSON を echo するだけ（計画 D2）
NOPY="$TMP/nopy"; mkdir -p "$NOPY"
for b in cat dirname; do
  src="$(command -v "$b")"; [ -n "$src" ] && cp "$src" "$NOPY/" 2>/dev/null
done
# Git Bash の coreutils は msys-2.0.dll 等に依存するため同梱 DLL もコピー
for dll in "$(dirname "$(command -v cat)")"/msys-*.dll; do [ -f "$dll" ] && cp "$dll" "$NOPY/" 2>/dev/null; done
write_state generated 0
OUT="$(printf '%s' "$NEW" | PATH="$NOPY" "$BASH_BIN" "$HOOK" 2>/dev/null)"; RC=$?; OUTS+=("$OUT")
sm="$(jget "$OUT" systemMessage)"
check "A8 python 不在でも systemMessage を出す" "$([ -n "$sm" ] && [ "$sm" != "__PARSE_ERROR__" ] && [ $RC -eq 0 ] && echo 0 || echo 1)" "out=[$OUT] rc=$RC"

# A9
write_state generated 0; run_hook ""
check "A9 空 stdin は新 turn 扱いで block 1/3" "$([ "$(jget "$OUT" decision)" = block ] && [ "$(has "$OUT" '1/3')" = 0 ] && echo 0 || echo 1)" "out=[$OUT]"

# A11
write_state selecting 0; run_hook "$NEW"
check "A11 phase=selecting でも block" "$([ "$(jget "$OUT" decision)" = block ] && echo 0 || echo 1)" "out=[$OUT]"

# A13
write_state generated '"x"'; run_hook "$ACTIVE"
check "A13 stop_blocks 非数値でも落ちず block 2/3" "$([ "$(jget "$OUT" decision)" = block ] && [ "$(has "$OUT" '2/3')" = 0 ] && echo 0 || echo 1)" "out=[$OUT] rc=$RC"

# A10（A12 の前に集計: A12 は出力なしが正）
bad=0
for o in "${OUTS[@]}"; do
  [ -z "$o" ] && continue
  [ "$(jget "$o" decision)" = "__PARSE_ERROR__" ] && bad=$((bad+1))
done
check "A10 出力はすべて JSON" "$([ $bad -eq 0 ] && echo 0 || echo 1)" "parse 失敗 $bad 件"

# A12
printf '{broken' > "$STATE"; run_hook "$NEW"
check "A12 壊れた state.json → 出力なし・exit 0" "$([ -z "$OUT" ] && [ $RC -eq 0 ] && echo 0 || echo 1)" "out=[$OUT] rc=$RC"

echo "---"
echo "PASS=$PASS FAIL=$FAIL"
[ "$FAIL" -eq 0 ]
