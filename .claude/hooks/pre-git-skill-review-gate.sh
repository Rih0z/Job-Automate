#!/usr/bin/env bash
# pre-git-skill-review-gate.sh — git push / git commit の前に、skill のレビュー記録を確かめる（PreToolUse, Bash）
#
# 規則の本体: CLAUDE.md「YOU MUST: skill の作成・変更は review-skill を通す」。
# Stop hook（review-skill/scripts/hook-skill-review-gate.sh）は commit と push を止めないので、その穴を埋める。
#
# 動作:
#   - Bash ツール以外、または git push / git commit を含まないコマンドは何もしない（何も出力しない）。
#     判定は 2 段。まずシェルだけで「git・push/commit の語を含むか」を見て（python を起動しない）、含む時だけ python で正確に判定する。
#   - git push        : skill_review_gate.py --strict が exit 1（未レビュー・要再レビューの skill がある）なら止める。
#                       `git commit ... && git push` のように 1 つのコマンドに複数の git があれば、push が 1 つでもあれば push として扱う。
#   - git commit      : 変更に .claude/skills/ 配下が含まれる時だけ、同じ gate を確かめる。含まれるとみなす範囲:
#                       staged の変更 / -a・--all を付けた時の未ステージの追跡ファイルの変更 /
#                       コマンドに .claude/skills のパスを直接書いた時 / --amend（直前の内容を含むので常に確かめる）。
#   - 止める時は {"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":...}} を出す。
#   - 評価できない時（python が無い・gate が exit 0/1 以外・時間切れ・入力が壊れている）は止めず、
#     systemMessage で通知して通す（無音で通さない。入力が壊れている場合と、対象外のコマンドは無音）。
# 既知の限界（コマンド文字列の照合なので、次は見ない／広めに止める）:
#   - 引用符・バッククォートの中の `git push` も対象にする（bash -c "git push" を塞ぐため）。gate が失敗している間は
#     `grep "git push" README.md` のような読み取りも止まる。gate が通っていれば影響なし。
#   - 見ない: git の別名（alias）・変数で組み立てたコマンド・スクリプトの中の push・`git -C 別のリポジトリ` の中身。
#     gate が見るのは常にこのリポジトリなので、別のリポジトリへの push でも、このリポジトリの gate が失敗していれば止まる。
#   - commit の「skill の変更を含む」判定は、このリポジトリの `git status` で行う。
# リポジトリのルート: SKILL_REVIEW_REPO_ROOT > CLAUDE_PROJECT_DIR > この script の位置から計算。
# 試験用の継ぎ目: SKILL_REVIEW_TIMEOUT_SEC（gate を待つ総秒数。既定 20）。
# 緊急時に外すのは人（リポジトリの管理者）が行う手順: .claude/settings.json の PreToolUse にある本 hook の登録を外す。
#   エージェントが自分の判断でこの登録を外したり、hook を回避したりしてはならない（CLAUDE.md の規則に反する。止まったらレビューを通す）。

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && (pwd -W 2>/dev/null || pwd))"

# 全 Bash 呼び出しの前に動くため、無関係なコマンドは python を起動せずに即座に通す（python の起動が遅い環境でも作業を遅らせない）。
# ここで落とすのは「git という語か、push / commit という語を含まない」入力だけ。含むものは下の python で正確に判定する。
INPUT="$(cat)"
case "$INPUT" in *git*) ;; *) exit 0 ;; esac
case "$INPUT" in *push*|*commit*) ;; *) exit 0 ;; esac

PYTHON=""
for cand in python3 python py; do
  p="$(command -v "$cand" 2>/dev/null)" || continue
  case "$p" in
    */WindowsApps/*|*\\WindowsApps\\*) continue ;;
  esac
  if "$cand" -S -c "print(1)" >/dev/null 2>&1; then
    PYTHON="$cand"; break
  fi
done
if [[ -z "$PYTHON" ]]; then
  echo '{"systemMessage": "[skill-review-gate] python が見つからないため、git push / commit の前の skill のレビュー確認を評価不能です（止めていません）。python を使える状態にしてから、gate を手動で実行してください: skill_review_gate.py --all --strict"}'
  exit 0
fi
export PYTHONUTF8=1

IFS= read -r -d '' PYSCRIPT <<'PY'
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

script_dir = Path(sys.argv[1])
try:
    raw = sys.stdin.buffer.read().decode("utf-8", "replace")
except Exception:
    raw = ""
PFX = "[skill-review-gate] "


def emit(obj):
    print(json.dumps(obj))
    sys.exit(0)


def silent():
    sys.exit(0)


try:
    ev = json.loads(raw) if raw.strip() else {}
except ValueError:
    ev = {}
if not isinstance(ev, dict) or ev.get("tool_name") != "Bash":
    silent()
tool_input = ev.get("tool_input")
command = tool_input.get("command") if isinstance(tool_input, dict) else None
if not isinstance(command, str) or not command.strip():
    silent()

VAL = r"""(?:"[^"]*"|'[^']*'|\S+)"""
GIT = re.compile(
    r"(?:^|[\s;&|(`\"'])git"
    r"((?:\s+(?:-[Cc]\s+" + VAL + r"|-c\s+\S+|--(?:git-dir|work-tree|namespace)\s+" + VAL + r"|--?[\w-]+(?:=\S+)?))*)"
    r"\s+(push|commit)(?![\w-])")
matches = list(GIT.finditer(command))
if not matches:
    silent()
push_match = next((x for x in matches if x.group(2) == "push"), None)
commit_match = next((x for x in matches if x.group(2) == "commit"), None)
kind = "push" if push_match else "commit"

try:
    timeout_total = float(os.environ.get("SKILL_REVIEW_TIMEOUT_SEC") or 20)
except ValueError:
    timeout_total = 20.0
deadline = time.time() + timeout_total
root = Path(os.environ.get("SKILL_REVIEW_REPO_ROOT") or os.environ.get("CLAUDE_PROJECT_DIR") or str(script_dir.parents[1]))
GATE = root / ".claude" / "skills" / "review-skill" / "scripts" / "skill_review_gate.py"


def unevaluable(why):
    emit({"systemMessage": PFX + "git %s の前の skill のレビュー確認は評価不能です（%s）。止めずに通します。手動で確認してください: skill_review_gate.py --all --strict" % (kind, why)})


def touches_skills():
    """commit の対象に .claude/skills/ 配下の変更が含まれるか。"""
    rest = command[commit_match.end():]
    if "--amend" in rest or ".claude/skills" in rest:
        return True  # amend は直前の内容を含む。パスを直接書いた commit は未ステージの変更をコミットする
    include_unstaged = bool(re.search(r"(?:^|\s)(?:-[A-Za-z]*a[A-Za-z]*|--all)(?:\s|$)", rest))
    try:
        p = subprocess.run(["git", "status", "--porcelain"], cwd=str(root), capture_output=True, timeout=10)
    except Exception:
        return True  # 変更を調べられない時は安全側（gate を確かめる）
    for line in p.stdout.decode("utf-8", "replace").splitlines():
        if len(line) < 4 or ".claude/skills/" not in line[3:]:
            continue
        x, y = line[0], line[1]
        if x not in " ?" or (include_unstaged and y not in " ?"):
            return True
    return False


if kind == "commit" and not touches_skills():
    silent()

if not GATE.exists():
    unevaluable("gate が見つからない: %s" % GATE)
left = deadline - time.time()
try:
    p = subprocess.run([sys.executable, "-S", str(GATE), "--repo-root", str(root), "--all", "--strict"],
                       capture_output=True, timeout=max(left, 0.1))
except subprocess.TimeoutExpired:
    unevaluable("時間切れ")
except Exception as e:
    unevaluable("起動できない: %s" % type(e).__name__)

if p.returncode == 0:
    silent()
if p.returncode != 1:
    unevaluable("gate が終了コード %s で終わった" % p.returncode)

cr = chr(13)
lines = [l for l in p.stdout.decode("utf-8", "replace").replace(cr, "").splitlines() if l.strip() and ": PASS" not in l]
detail = " / ".join(lines)[:600]
emit({"hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": PFX + "git %s の前に、未レビューまたは要再レビューの skill があります: %s。"
    "review-skill で別エージェントのレビューを通し、PASS の記録を保存してからやり直してください"
    "（CLAUDE.md「YOU MUST: skill の作成・変更は review-skill を通す」）。" % (kind, detail or "（gate の出力なし）")}})
PY

"$PYTHON" -S -c "$PYSCRIPT" "$SCRIPT_DIR" <<<"$INPUT"
