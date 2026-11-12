#!/usr/bin/env bash
# pre-handoff-discovery-gate.sh — 引継ぎ資料（.tmp/handoffs/）を書く前に、discovery-log の queued を止める（PreToolUse, Write|Edit|MultiEdit）
#
# 規則の本体: CLAUDE.md「応答ルール」の discovery-log の「引継ぎ資料作成時の gate」（queued を残したまま handoff を作らない）。
# 例外の無い決まりで、合否を機械で判定できるので hook にした。
#
# 動作:
#   - 入力に handoffs を含まなければ何もしない（シェルだけで先に落とし、Write・Edit のたびに python を起動しない）。
#   - tool_input.file_path を正規化して（相対パスはリポジトリのルート基準、.. を解決、Windows では大文字小文字を区別しない）、
#     リポジトリの .tmp/handoffs/ の下なら .tmp/discovery-log.md を 1 行ずつ JSON で読む。
#   - status が queued の行があれば止める（件数と summary の先頭 3 件）。JSON として読めない行があっても止める（行番号と直し方）。
#     空行・CRLF・先頭の BOM は許す。discovery-log が無ければ何もしない。
#   - 新規作成だけでなく既存の handoff の更新（Edit）も止める。queued を残したまま引継ぎを書き足させないため。
#   - 評価できない時（python が無い・python が途中で落ちた）は止めず、systemMessage で知らせて通す。
# 既知の限界: Bash（cat > や echo >>）で handoff を書く経路は見ない。
# handoff の置き場は .tmp/handoffs/ に固定（このリポジトリの CLAUDE.md が置き場を決めている）。移植先で置き場が違う時は、
#   下の HANDOFF_DIR・DISCOVERY_LOG だけを書き換える。
# リポジトリのルート: CLAUDE_PROJECT_DIR > この script の位置（.claude/hooks/ の 2 つ上）。
# 緊急時に外すのは人（リポジトリの管理者）が行う: .claude/settings.json の PreToolUse にある本 hook の登録を外す。

set -uo pipefail
HANDOFF_DIR=".tmp/handoffs"
DISCOVERY_LOG=".tmp/discovery-log.md"
INPUT="$(cat)"
shopt -s nocasematch
[[ "$INPUT" == *handoffs* ]] || exit 0
shopt -u nocasematch

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && (pwd -W 2>/dev/null || pwd))"
ROOT="${CLAUDE_PROJECT_DIR:-$HERE/../..}"

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
  echo '{"systemMessage": "[handoff-discovery-gate] python が見つからないため、handoff を書く前の discovery-log の queued を評価できない（止めていません）。"}'
  exit 0
fi
export PYTHONUTF8=1

# heredoc を $( ) の中に書くと古い bash（3.2）が本文の括弧や引用符を誤解析するので、read で受ける
IFS= read -r -d '' PYSCRIPT <<'PY'
import json, os, sys
root, handoff_dir, discovery_log = sys.argv[1:4]
PFX = "[handoff-discovery-gate] "
try:
    ev = json.loads(sys.stdin.read() or "{}")
except ValueError:
    print(json.dumps({"systemMessage": PFX + "hook の入力を JSON として読めないため評価できない（止めていません）"},
                     ensure_ascii=False))
    sys.exit(0)
ti = ev.get("tool_input") if isinstance(ev, dict) else None
path = ti.get("file_path") if isinstance(ti, dict) else None
if not isinstance(path, str) or not path:
    sys.exit(0)


def norm(p):
    return os.path.normcase(os.path.normpath(p))


if os.sep == "/":  # POSIX では \ も区切りとして扱う（isabs・join の前に置き換える）
    path = path.replace("\\", "/")
root = os.path.abspath(root)
full = path if os.path.isabs(path) or (os.name == "nt" and path.replace("\\", "/").startswith("/")) \
    else os.path.join(root, path)
target = norm(os.path.abspath(full))
base = norm(os.path.join(root, handoff_dir))
if not target.startswith(base + os.sep):
    sys.exit(0)

log = os.path.join(root, discovery_log)
if not os.path.isfile(log):
    sys.exit(0)
with open(log, "rb") as f:
    data = f.read()
if data.startswith(b"\xef\xbb\xbf"):
    data = data[3:]
bad, queued = [], []
for i, raw_line in enumerate(data.splitlines(), 1):
    try:
        line = raw_line.decode("utf-8")
    except UnicodeDecodeError:
        bad.append(i)
        continue
    if not line.strip():
        continue
    try:
        e = json.loads(line)
    except ValueError:
        bad.append(i)
        continue
    if not isinstance(e, dict):
        bad.append(i)
        continue
    if e.get("status") == "queued":
        queued.append(str(e.get("summary", ""))[:80])
reasons = []
if bad:
    reasons.append(f"{discovery_log} の {', '.join(map(str, bad[:5]))} 行目を JSON として読めない"
                   "（パスの \\ を / に直すなど、1 行 1 つの JSON にする）")
if queued:
    reasons.append(f"{discovery_log} に queued が {len(queued)} 件ある: " + " ／ ".join(queued[:3])
                   + "。done・issued・knowhow のどれかにしてから handoff を書く")
if reasons:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "deny",
        "permissionDecisionReason": PFX + " ／ ".join(reasons)}}, ensure_ascii=False))
sys.exit(0)
PY
# -S: site（.pth）を読まない。標準ライブラリだけを使い、環境の .pth が stdout に出す行を混ぜないため
"$PYTHON" -S -c "$PYSCRIPT" "$ROOT" "$HANDOFF_DIR" "$DISCOVERY_LOG" <<<"$INPUT"
rc=$?
if [[ $rc -ne 0 ]]; then
  echo "{\"systemMessage\": \"[handoff-discovery-gate] 検査の python が終了コード $rc で終わったため、discovery-log の queued を評価できない（止めていません）。\"}"
fi
exit 0
