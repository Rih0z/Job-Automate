#!/usr/bin/env bash
# pre-git-ledger-gate.sh — git commit の前に、起票の「関連:」欄と knowhow 台帳の反映を確かめる（PreToolUse, Bash）
#
# 規則の本体: CLAUDE.md「応答ルール」（要望の反映・discovery-log の drain）と、issue-lifecycle-tracking の起票の手順。
# skill のレビュー記録の gate（pre-git-skill-review-gate.sh）とは別の hook にして、止めた理由を分ける。
#
# 動作:
#   - Bash ツール以外、または git commit を含まないコマンドは何もしない（シェルだけで先に落とし、python を起動しない）。
#   - .claude/issue-tracker.json があれば issue_tracker.py check-new（index で新しく足された issue に「関連:」欄があるか）、
#     .claude/knowhow.json があれば knowhow_check.py（queued が残っていない・反映先にアンカーがある）を実行する。
#     どちらも無い repo では何もしない。
#   - どちらかが exit 1（欠け）か exit 2（台帳・設定が不正）なら止める:
#     {"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":...}}
#   - 評価できない時（python が無い・時間切れ・その他の終了コード）は止めず、systemMessage で知らせて通す。
# 既知の限界: コマンド文字列の照合なので、git の別名・変数で組み立てたコマンド・スクリプトの中の commit は見ない。
#   見るのは常にこの repo の台帳なので、`git -C <別の repo> commit` でも、この repo の検査が失敗していれば止まる。
#   check-new は index（staged）を見るので、commit -a で未ステージの新規 file が入ることはない（新規 file は add が要る）。
# 試験用の継ぎ目: LEDGER_GATE_TIMEOUT_SEC（検査 1 つを待つ秒数。既定 20）。
# リポジトリのルート: CLAUDE_PROJECT_DIR > この script の位置（.claude/hooks/ の 2 つ上）。script の場所は先頭の ISSUE_TRACKER・KNOWHOW_CHECK（既定はこの hook の隣の .claude/skills/ の中）。
# 緊急時に外すのは人（リポジトリの管理者）が行う: .claude/settings.json の PreToolUse にある本 hook の登録を外す。

set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 呼ぶ script の完全パス。移植先で script を別の場所（例: .claude/scripts/）に置いた時は、この 2 行だけを書き換える
ISSUE_TRACKER="$HERE/../skills/issue-lifecycle-tracking/scripts/issue_tracker.py"
KNOWHOW_CHECK="$HERE/../skills/agent-harness-bootstrap/scripts/knowhow_check.py"
ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$HERE/../.." && pwd)}"
INPUT="$(cat)"
case "$INPUT" in *git*) ;; *) exit 0 ;; esac
case "$INPUT" in *commit*) ;; *) exit 0 ;; esac
[[ -f "$ROOT/.claude/issue-tracker.json" || -f "$ROOT/.claude/knowhow.json" ]] || exit 0

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
  echo '{"systemMessage": "[ledger-gate] python が見つからないため、git commit の前の「関連:」欄と knowhow 台帳の確認を評価できません（止めていません）。"}'
  exit 0
fi
export PYTHONUTF8=1

"$PYTHON" - "$ROOT" "$ISSUE_TRACKER" "$KNOWHOW_CHECK" "$INPUT" <<'PY'
import json, os, re, subprocess, sys
root, issue_tracker, knowhow_check, raw = sys.argv[1:5]
PFX = "[ledger-gate] "
try:
    ev = json.loads(raw) if raw.strip() else {}
except ValueError:
    sys.exit(0)
if not isinstance(ev, dict) or ev.get("tool_name") != "Bash":
    sys.exit(0)
ti = ev.get("tool_input")
cmd = ti.get("command") if isinstance(ti, dict) else None
if not isinstance(cmd, str):
    sys.exit(0)
VAL = r"""(?:"[^"]*"|'[^']*'|\S+)"""
GIT = re.compile(r"(?:^|[\s;&|(`\"'])git"
                 r"(?:\s+(?:-[Cc]\s+" + VAL + r"|-c\s+\S+|--(?:git-dir|work-tree|namespace)\s+" + VAL + r"|--?[\w-]+(?:=\S+)?))*"
                 r"\s+commit(?![\w-])")
if not GIT.search(cmd):
    sys.exit(0)

checks = []
if os.path.isfile(os.path.join(root, ".claude", "issue-tracker.json")):
    checks.append(("issue の「関連:」欄（issue_tracker.py check-new）",
                   [issue_tracker, "check-new",
                    "--config", os.path.join(root, ".claude", "issue-tracker.json")]))
if os.path.isfile(os.path.join(root, ".claude", "knowhow.json")):
    checks.append(("knowhow 台帳の反映（knowhow_check.py）",
                   [knowhow_check,
                    "--config", os.path.join(root, ".claude", "knowhow.json")]))
try:
    TIMEOUT = float(os.environ.get("LEDGER_GATE_TIMEOUT_SEC") or 20)
except ValueError:
    TIMEOUT = 20.0
denies, notes = [], []
for label, args in checks:
    if not os.path.isfile(args[0]):
        notes.append(f"{label} の script が無いので評価できない: {args[0]}")
        continue
    try:
        p = subprocess.run([sys.executable, *args], cwd=root, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=TIMEOUT)
    except Exception as ex:
        notes.append(f"{label} を評価できない（{type(ex).__name__}）")
        continue
    if p.returncode in (1, 2):
        detail = " / ".join(l for l in (p.stdout + "\n" + p.stderr).splitlines() if l.strip())[:700]
        denies.append(f"{label}: {detail}")
    elif p.returncode != 0:
        notes.append(f"{label} が終了コード {p.returncode} で終わった")
if denies:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "deny",
        "permissionDecisionReason": PFX + "git commit の前に直すものがあります。" + " ／ ".join(denies)
        + "（起票は related で関連 issue を確かめて「関連:」欄を書く。knowhow は反映してから reflected にする）"}},
        ensure_ascii=False))
elif notes:
    print(json.dumps({"systemMessage": PFX + " / ".join(notes) + "（止めていません）"}, ensure_ascii=False))
sys.exit(0)
PY
exit 0
