#!/usr/bin/env bash
# harness-setup-state.sh — 別プロジェクトへの setup の進行状態（移植元 clone 側の .tmp/ に保持）
#
# 目的: agent-harness-bootstrap の Step 0（選択）→ Step 8（生成）→ harness-setup-review（検証）の
#   進行を state.json に記録し、Stop hook（hook-stop-setup-gate.sh）が「検証前の終了」を block する根拠にする。
#   状態は移植元 clone の .tmp/harness-setup/state.json（.gitignore 済み）。対象側には書かない。
#
# usage:
#   harness-setup-state.sh start <対象の絶対パス>            # phase=selecting（Step 0 開始時）
#   harness-setup-state.sh phase <selecting|generated>       # phase 更新（Step 8 生成完了時に generated）
#   harness-setup-state.sh verify --machine <PASS|FAIL> --review <PASS|FAIL>
#                                                            # 両方 PASS なら phase=verified、それ以外は fail_count++
#   harness-setup-state.sh done                              # phase=verified の時のみ done にする
#   harness-setup-state.sh show                              # 現在の state を表示（無ければ "none"）
#   harness-setup-state.sh clear                             # state を削除（中断・やり直し時）
#
# phases: selecting → generated → verified → done

set -uo pipefail
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="${PROVENANCE_ROOT:-$(cd "$SKILL_DIR/../../.." && pwd)}"
STATE_DIR="${HARNESS_SETUP_STATE_DIR:-$ROOT/.tmp/harness-setup}"
STATE="$STATE_DIR/state.json"
# python3 という名前の実行ファイルが PATH にあっても動作するとは限らない（Windows の
# Microsoft Store App Execution Alias スタブ等、実行自体がハングし `timeout` でも kill
# できないケースが実機で確認された）。解決済みパスが既知の壊れた stub 配置（WindowsApps 配下）
# でないかを文字列一致だけで判定し、危険な実行を避けてから `-c "print(1)"` で動作確認する。
resolve_python() {
  local cand p
  for cand in python3 python py; do
    p="$(command -v "$cand" 2>/dev/null)" || continue
    case "$p" in
      */WindowsApps/*|*\\WindowsApps\\*) continue ;;
    esac
    if "$cand" -c "print(1)" >/dev/null 2>&1; then
      printf '%s' "$cand"; return 0
    fi
  done
  return 1
}
PYTHON="$(resolve_python)" || { echo "FAIL: 動作する python (python3 / python / py) が見つからない" >&2; exit 1; }
# Windows のコンソールコードページ (cp1252 等) だと日本語 print() で UnicodeEncodeError になるため強制 UTF-8
export PYTHONUTF8=1

cmd="${1:-show}"; shift || true
mkdir -p "$STATE_DIR"

_pyrun() { "$PYTHON" - "$STATE" "$@" <<'PY'
import json, os, sys, datetime
state, cmd, *args = sys.argv[1:]
now = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
def load():
    if not os.path.isfile(state):
        return None
    try:
        return json.load(open(state, encoding="utf-8"))
    except Exception:
        return None
def save(s):
    s["updated"] = now
    json.dump(s, open(state, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    open(state, "a").write("\n")
s = load()
if cmd == "show":
    print(json.dumps(s, ensure_ascii=False, indent=2) if s else "none"); sys.exit(0)
if cmd == "clear":
    if os.path.isfile(state): os.remove(state)
    print("cleared"); sys.exit(0)
if cmd == "start":
    if not args or not os.path.isabs(args[0]):
        print("FAIL: start には対象の絶対パスが必要", file=sys.stderr); sys.exit(1)
    if not os.path.isdir(args[0]):
        print(f"FAIL: 対象 {args[0]} がディレクトリでない", file=sys.stderr); sys.exit(1)
    s = {"schema": "harness-setup-state/v1", "target": args[0], "phase": "selecting",
         "started": now, "fail_count": 0, "stop_blocks": 0, "verification": None}
    save(s); print(f"started: target={args[0]} phase=selecting"); sys.exit(0)
if s is None:
    print("FAIL: state が無い。先に start <対象の絶対パス> を実行する", file=sys.stderr); sys.exit(1)
if cmd == "phase":
    if not args or args[0] not in ("selecting", "generated"):
        print("FAIL: phase は selecting / generated のいずれか（verified は verify、done は done で遷移）", file=sys.stderr); sys.exit(1)
    s["phase"] = args[0]; save(s); print(f"phase={args[0]}"); sys.exit(0)
if cmd == "verify":
    opts = dict(zip(args[0::2], args[1::2]))
    m, r = opts.get("--machine"), opts.get("--review")
    if m not in ("PASS", "FAIL") or r not in ("PASS", "FAIL"):
        print("FAIL: verify --machine <PASS|FAIL> --review <PASS|FAIL>", file=sys.stderr); sys.exit(1)
    s["verification"] = {"machine": m, "review": r, "at": now}
    if m == "PASS" and r == "PASS":
        s["phase"] = "verified"; save(s); print("phase=verified"); sys.exit(0)
    s["fail_count"] = int(s.get("fail_count", 0)) + 1
    save(s)
    print(f"verification FAIL (machine={m}, review={r}) fail_count={s['fail_count']}" +
          ("。3 回 FAIL: 中断してユーザーに報告する" if s["fail_count"] >= 3 else ""))
    sys.exit(2)
if cmd == "done":
    if s.get("phase") != "verified":
        print(f"FAIL: phase={s.get('phase')} は done にできない（verified が必要 = harness-setup-review を PASS させる）", file=sys.stderr); sys.exit(1)
    s["phase"] = "done"; save(s); print("phase=done"); sys.exit(0)
print(f"FAIL: 不明なコマンド {cmd}", file=sys.stderr); sys.exit(1)
PY
}
_pyrun "$cmd" "$@"
