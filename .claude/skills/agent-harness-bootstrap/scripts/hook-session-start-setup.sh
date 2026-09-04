#!/usr/bin/env bash
# hook-session-start-setup.sh — SessionStart hook: 進行中の別プロジェクト setup があればポインタのみ通知する
#
# 発火: この移植元 clone での SessionStart（startup / resume / clear / compact）。
# 出力: state.json の target / phase / 次の手順を 1〜3 行（本文は注入しない）。state が無ければ何も出さない。

set -uo pipefail
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="${PROVENANCE_ROOT:-$(cd "$SKILL_DIR/../../.." && pwd)}"
STATE="${HARNESS_SETUP_STATE_DIR:-$ROOT/.tmp/harness-setup}/state.json"
[[ -f "$STATE" ]] || exit 0
command -v python3 >/dev/null 2>&1 || exit 0
python3 - "$STATE" <<'PY'
import json, sys
try:
    s = json.load(open(sys.argv[1], encoding="utf-8"))
except Exception:
    sys.exit(0)
phase = s.get("phase")
if phase == "done":
    sys.exit(0)
print(f"[harness-setup] 進行中の別プロジェクト setup があります: target={s.get('target')} phase={phase} "
      f"(started {s.get('started')}, fail_count={s.get('fail_count', 0)})。"
      "phase=selecting なら Step 0 の選択から、generated なら harness-setup-review から再開する。"
      "やり直す場合は `bash .claude/skills/agent-harness-bootstrap/scripts/harness-setup-state.sh clear`。")
PY
