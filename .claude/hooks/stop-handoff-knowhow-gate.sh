#!/usr/bin/env bash
# stop-handoff-knowhow-gate.sh — Stop hook: この session で受領して done していない handoff と、この作業で増えた
#   未反映の knowhow（queued）があれば、終了を 1 回だけ止めて Claude に片付けを促す。
#
# 規則の本体: CLAUDE.md「応答ルール」の discovery-log の drain・要望の反映と、「セッションの区切り方」。
# 動作:
#   - stdin の Stop 入力の stop_hook_active が true なら何もしない（block で継続中の turn。別の hook の block も含む）。
#     false の turn だけ判定するので、block は 1 turn に 1 回だけで、次の turn でまた判定する。
#   - handoff: SessionStart（hook-session-start-setup.sh）が書いた .tmp/session-start/<session_id>.json の開始時刻を読み、
#     handoff_lifecycle.py remind --received-since <開始時刻> で「この session の開始後に受領し、done していない」ものを出す。
#     開始時刻の file が無い session（hook の導入前に始まった等）では見ない。
#   - knowhow: .claude/knowhow.json があれば knowhow_check.py --new-since HEAD で、HEAD と比べて増えた queued を見る。
#     前からある queued だけなら止めず、systemMessage で知らせる（関係ない session を止めない）。
#   - どちらかがあれば {"decision":"block","reason":...} を出す。
# 限界: 同じ repo で並行する session の受領は時刻でしか分けられないので、別 session の受領が混じることがある。
#   block は 1 回だけなので、混じった時は Claude が「自分の受領でない」と判断して終われる（hooks-reference.md に記載）。
#   python が見つからない時は評価できない旨を systemMessage で出して通す。
# データの置き場（repo のルート）: CLAUDE_PROJECT_DIR > この script の位置（.claude/hooks/ の 2 つ上）。

set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 呼ぶ script の完全パス。移植先で script を別の場所（例: .claude/scripts/）に置いた時は、この 2 行だけを書き換える
HANDOFF_LIFECYCLE="$HERE/../skills/agent-harness-bootstrap/scripts/handoff_lifecycle.py"
KNOWHOW_CHECK="$HERE/../skills/agent-harness-bootstrap/scripts/knowhow_check.py"
ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$HERE/../.." && pwd)}"
INPUT="$(cat 2>/dev/null || true)"
# 継続中の turn は python を起動せずに通す
case "$INPUT" in *'"stop_hook_active": true'*|*'"stop_hook_active":true'*) exit 0 ;; esac

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
  if [[ -d "$ROOT/.tmp/session-start" || -f "$ROOT/.claude/knowhow.json" ]]; then
    echo '{"systemMessage": "[handoff-knowhow-gate] python が見つからないため、受領した handoff と knowhow の未反映を確かめられません（止めていません）。"}'
  fi
  exit 0
fi
export PYTHONUTF8=1

# 入力の JSON は stdin で python に渡す（argv だと長い入力で溢れ、黙って通るため）
# heredoc を $( ) の中に書くと古い bash（3.2）が本文の括弧や引用符を誤解析するので、read で受ける
IFS= read -r -d '' PYSCRIPT <<'PY'
import json, os, re, subprocess, sys
root, handoff_lifecycle, knowhow_check = sys.argv[1:4]
raw = sys.stdin.read()
PFX = "[handoff-knowhow-gate] "
try:
    ev = json.loads(raw) if raw.strip() else {}
except ValueError:
    ev = {}
if not isinstance(ev, dict) or ev.get("stop_hook_active"):
    sys.exit(0)
reasons, notes = [], []


def run(args):
    if not os.path.isfile(args[0]):
        notes.append(f"script が無いので評価できない: {args[0]}")
        return None
    try:
        return subprocess.run([sys.executable, *args], cwd=root, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=20)
    except Exception as ex:  # 評価できない時は止めない
        notes.append(f"{args[0]} を実行できない（{type(ex).__name__}）")
        return None


sid = ev.get("session_id")
if isinstance(sid, str) and re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", sid) and ".." not in sid:
    sf = os.path.join(root, ".tmp", "session-start", sid + ".json")
    started = None
    try:
        with open(sf, encoding="utf-8") as f:
            started = json.load(f).get("started_at")
    except (OSError, ValueError, AttributeError):
        started = None
    if isinstance(started, str) and started:
        cfg = os.path.join(root, ".claude", "handoff-lifecycle.json")
        args = [handoff_lifecycle, "remind", "--received-since", started]
        args += ["--config", cfg] if os.path.isfile(cfg) else ["--dir", os.path.join(root, ".tmp", "handoffs")]
        p = run(args)
        if p is not None:
            lines = [l for l in p.stdout.splitlines() if l.strip()]
            if lines:
                reasons.append("この session で受領し、done していない handoff があります: " + " / ".join(lines)
                               + "。使い終わったなら done、続くなら issue の次の一手に書いてから done してください"
                               "（自分の受領でなければ、そのまま終えてよい）。")

kh = os.path.join(root, ".claude", "knowhow.json")
if os.path.isfile(kh):
    p = run([knowhow_check, "--config", kh, "--new-since", "HEAD"])
    if p is not None:
        out = [l for l in p.stdout.splitlines() if l.strip()]
        if p.returncode in (0, 1):
            notes += [l for l in out if l.startswith("前からある queued")]
        if p.returncode == 1:
            reasons.append("この作業で増えた未反映の knowhow があります: "
                           + " / ".join(l for l in out if "増えた queued" in l)
                           + "。反映先に書いてアンカーを置き、status を reflected にしてください。")
        elif p.returncode != 0:
            notes.append("knowhow の検査を評価できない: " + (p.stderr.strip()[:200] or f"exit {p.returncode}"))

if reasons:
    print(json.dumps({"decision": "block", "reason": PFX + " ".join(reasons)}, ensure_ascii=False))
elif notes:
    print(json.dumps({"systemMessage": PFX + " / ".join(notes)}, ensure_ascii=False))
sys.exit(0)
PY
# -S: site（.pth）を読まない。標準ライブラリだけを使い、環境の .pth が stdout に出す行を混ぜないため
"$PYTHON" -S -c "$PYSCRIPT" "$ROOT" "$HANDOFF_LIFECYCLE" "$KNOWHOW_CHECK" <<<"$INPUT"
rc=$?
if [[ $rc -ne 0 ]]; then
  echo "{\"systemMessage\": \"[handoff-knowhow-gate] 検査の python が終了コード $rc で終わったため、受領した handoff と knowhow の未反映を評価できない（止めていません）。\"}"
fi
exit 0
