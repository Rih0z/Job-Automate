#!/usr/bin/env bash
# handoff-remind.sh — SessionStart hook: 受領済みで残っている handoff と、未受領で古い handoff をファイル名だけで知らせる。
#
# 本文は出さない（handoff は利用者が貼るか指定した時だけ読む）。.tmp/handoffs が無い・python が無い時は何も出さない。
# 常に exit 0（通知が失敗しても session を止めない）。
set -uo pipefail
HERE="${BASH_SOURCE[0]%/*}"
[[ "$HERE" == "${BASH_SOURCE[0]}" ]] && HERE="."
ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
[[ -d "$ROOT/.tmp/handoffs" ]] || exit 0
# WindowsApps 配下の python stub は実行するとハングすることがあるので避ける（hook-session-start-setup.sh と同じ方法）
PYTHON=""
for cand in python3 python py; do
  p="$(command -v "$cand" 2>/dev/null)" || continue
  case "$p" in
    */WindowsApps/*|*\\WindowsApps\\*) continue ;;
  esac
  if "$cand" -c "print(1)" >/dev/null 2>&1; then
    PYTHON="$cand"; break
  fi
done
[[ -n "$PYTHON" ]] || exit 0
export PYTHONUTF8=1
"$PYTHON" "$HERE/handoff_lifecycle.py" remind --dir "$ROOT/.tmp/handoffs" || true
exit 0
