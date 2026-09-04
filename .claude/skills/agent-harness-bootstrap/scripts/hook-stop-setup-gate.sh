#!/usr/bin/env bash
# hook-stop-setup-gate.sh — Stop hook: 別プロジェクトへの setup が検証前なら終了を block する
#
# 発火: この移植元 clone で Claude Code を起動している時の Stop イベント（.claude/settings.json で登録）。
# 判定: .tmp/harness-setup/state.json の phase が selecting / generated（= harness-setup-review 未 PASS）なら
#   stdout に {"decision":"block","reason":"..."} を返して block し、Claude に検証を続けさせる
#   （Stop の block は公式どおり JSON decision で返す。exit 2 + stderr は Stop では Claude に届く保証が無い）。
#   verified / done / state 無しなら何も出さず exit 0。
# 無限ループ防止: 公式ガイダンスに従い stdin の stop_hook_active（= 既に本 hook の block で継続中）を parse し、
#   その回数を state の stop_blocks に数えて 3 回を超えたら block せず終了を許す（Claude Code 自体も連続 8 回で上書きする）。
#   公式例は stop_hook_active が true なら即 early-exit。本 hook は有界（3 回）に引き締めている（著者判断）。
# 参照: .claude/skills/_shared/anthropic-best-practices.json の hooks.stop-json-decision-block / hooks.stop-hook-active-loop-guard

set -uo pipefail
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="${PROVENANCE_ROOT:-$(cd "$SKILL_DIR/../../.." && pwd)}"
STATE="${HARNESS_SETUP_STATE_DIR:-$ROOT/.tmp/harness-setup}/state.json"
[[ -f "$STATE" ]] || exit 0
command -v python3 >/dev/null 2>&1 || exit 0
input=$(cat 2>/dev/null || true)

python3 - "$STATE" "$input" <<'PY'
import json, sys
state_path, raw = sys.argv[1], sys.argv[2]
try:
    s = json.load(open(state_path, encoding="utf-8"))
except Exception:
    sys.exit(0)
phase = s.get("phase")
if phase in ("verified", "done", None):
    sys.exit(0)
try:
    active = bool(json.loads(raw).get("stop_hook_active")) if raw.strip() else False
except Exception:
    active = False
blocks = int(s.get("stop_blocks", 0))
if active:
    blocks += 1
    s["stop_blocks"] = blocks
    json.dump(s, open(state_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
if blocks > 3:
    # 有界化: これ以上 block しない。理由は debug ログ（stderr）に残す
    print(f"[harness-setup-gate] 検証未完了のまま {blocks} 回 block したため終了を許可する。phase={phase} target={s.get('target')}", file=sys.stderr)
    sys.exit(0)
target = s.get("target")
nxt = {
    "selecting": "Step 0 の選択を完了し harness-selection.json を書いてから Step 1〜8 で生成し、`harness-setup-state.sh phase generated` を実行する",
    "generated": "harness-setup-review skill を実行し（機械検査 provenance-check.sh --target と別エージェント突合レビューの両方）、PASS なら `harness-setup-state.sh verify --machine PASS --review PASS` → `done` を実行する",
}.get(phase, "harness-setup-review を実行して verified にする")
reason = (f"[harness-setup-gate] 別プロジェクト setup が検証前（phase={phase}, target={target}, block {blocks + 1}/3）。"
          f"終了せず次を行う: {nxt}。中断する場合はユーザーにその旨を報告し `harness-setup-state.sh clear` で state を消す。")
print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
sys.exit(0)
PY
