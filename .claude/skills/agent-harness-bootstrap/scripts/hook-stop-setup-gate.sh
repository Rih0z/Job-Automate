#!/usr/bin/env bash
# hook-stop-setup-gate.sh — Stop hook: 別プロジェクトへの setup が検証前なら終了を block する
#
# 発火: この移植元 clone で Claude Code を起動している時の Stop イベント（.claude/settings.json で登録）。
# 判定: .tmp/harness-setup/state.json の phase が selecting / generated（= harness-setup-review 未 PASS）なら
#   stdout に {"decision":"block","reason":"..."} を返して block し、Claude に検証を続けさせる
#   （Stop の block は JSON decision で返す。exit 2 + stderr でも reason と同じ経路で Claude に届くが、1 つの hook では一方に揃える）。
#   verified / done / state 無しなら何も出さず exit 0。
# 無限ループ防止: stdin の stop_hook_active を parse する。false（= 新しい turn）なら state の stop_blocks を 0 に戻し、
#   true（= 本 hook の block で継続中）なら 1 加算する。1 turn の block は最大 3 回で、上限に達したら block せず
#   systemMessage でユーザーに「検証未完了のまま終了を許可した」と伝える（exit 0 の stderr は debug log にしか出ないため）。
#   カウンタを turn ごとに数え直すので、一度上限に達しても次の turn ではゲートが再び働く。
#   公式例は stop_hook_active が true なら即 early-exit。本 hook は 1 turn 3 回まで継続させる（著者判断。Claude Code 自体も進展なし連続 8 回で上書きする）。
# python が見つからない時は評価できない旨を systemMessage で出して終了を許す（無音で通過しない）。
# 参照: .claude/skills/_shared/anthropic-best-practices.json の hooks.stop-json-decision-block / hooks.stop-hook-active-loop-guard

set -uo pipefail
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="${PROVENANCE_ROOT:-$(cd "$SKILL_DIR/../../.." && pwd)}"
STATE="${HARNESS_SETUP_STATE_DIR:-$ROOT/.tmp/harness-setup}/state.json"
[[ -f "$STATE" ]] || exit 0
# python3 という名前の実行ファイルが PATH にあっても動作するとは限らない（Windows の
# Microsoft Store App Execution Alias スタブ等、実行自体がハングし `timeout` でも kill
# できないケースが実機で確認された。これを怠ると本 gate が「常に無音で通過」する
# = 検証未完了のまま Stop できてしまう静かな機能欠落になる）。解決済みパスが既知の壊れた
# stub 配置（WindowsApps 配下）でないかを文字列一致だけで判定し、危険な実行を避ける。
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
if [[ -z "$PYTHON" ]]; then
  # python 無しでは state.json を解釈できない。cat / dirname 以外の外部コマンドを使わず固定文字列で通知する
  echo '{"systemMessage": "[harness-setup-gate] python が見つからないため setup の検証ゲートを評価できません。harness-setup-review を実行してから終了してください（この終了は block していません）。"}'
  exit 0
fi
# Windows のコンソールコードページ (cp1252 等) だと日本語 print() で UnicodeEncodeError になるため強制 UTF-8
export PYTHONUTF8=1
input=$(cat 2>/dev/null || true)

"$PYTHON" - "$STATE" "$input" <<'PY'
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
CAP = 3  # 1 turn あたりの block 上限（Claude Code 自体の上限 8 より小さく、検証 1 周分の猶予として著者が決めた値）
try:
    blocks = int(s.get("stop_blocks", 0))
except (TypeError, ValueError):
    blocks = 0
blocks = blocks + 1 if active else 0
s["stop_blocks"] = blocks
json.dump(s, open(state_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
if blocks >= CAP:
    # 上限到達: これ以上 block しない。stderr は debug log にしか出ないので systemMessage でユーザーに伝える
    msg = (f"[harness-setup-gate] 別プロジェクト setup の検証（harness-setup-review）が未完了のまま、"
           f"この turn で {CAP} 回 block したため終了を許可しました（phase={phase}, target={s.get('target')}）。"
           f"続ける場合は harness-setup-review を実行し、中断する場合は `harness-setup-state.sh clear` で state を消してください。")
    print(json.dumps({"systemMessage": msg}, ensure_ascii=False))
    sys.exit(0)
target = s.get("target")
nxt = {
    "selecting": "Step 0 の選択を完了し harness-selection.json を書いてから Step 1〜8 で生成し、`harness-setup-state.sh phase generated` を実行する",
    "generated": "harness-setup-review skill を実行し（機械検査 provenance-check.sh --target と別エージェント突合レビューの両方）、PASS なら `harness-setup-state.sh verify --machine PASS --review PASS` → `done` を実行する",
}.get(phase, "harness-setup-review を実行して verified にする")
reason = (f"[harness-setup-gate] 別プロジェクト setup が検証前（phase={phase}, target={target}, block {blocks + 1}/{CAP}）。"
          f"終了せず次を行う: {nxt}。中断する場合はユーザーにその旨を報告し `harness-setup-state.sh clear` で state を消す。")
print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
sys.exit(0)
PY
