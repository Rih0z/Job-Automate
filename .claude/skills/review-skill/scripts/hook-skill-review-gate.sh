#!/usr/bin/env bash
# hook-skill-review-gate.sh — skill のレビュー記録の gate（Stop と SessionStart の両方を 1 本で扱う）
#
# イベントは stdin の hook_event_name で判別する。
#   Stop         : skill_review_gate.py --strict が exit 1（未レビュー・要再レビューの skill がある）、または
#                  --verify-ledger が exit 1（負債台帳の改ざん）なら {"decision":"block","reason":...} を返す。
#                  block は 1 turn に最大 3 回。上限に達したら block せず systemMessage に未レビュー skill 名を列挙して通す。
#                  カウンタは独自の state（<root>/.tmp/skill-review-gate/state.json の stop_blocks）。本 hook が block したときだけ加算し、
#                  新しい turn（stop_hook_active が false）で 0 に戻す。既存の setup gate の state は読み書きしない。
#                  --verify-ledger が UNVERIFIABLE（exit 2）のときは systemMessage で WARN を出して通す。
#   SessionStart : block しない。「PASS n／未レビューの負債 m（台帳）／要レビュー k」を 1 行の systemMessage で出し、
#                  あわせて check_skill_review_consistency.py を実行して失敗があれば要約を足す。
# 評価できないとき（python が無い・gate が exit 0/1 以外・20 秒の打ち切り）は、block せず systemMessage で通知して通す（無音で通さない）。
# リポジトリのルート: SKILL_REVIEW_REPO_ROOT > CLAUDE_PROJECT_DIR > この script の位置から計算。
# 試験用の継ぎ目: SKILL_REVIEW_TIMEOUT_SEC（gate を待つ総秒数。既定 20）。
# 参照: .claude/skills/_shared/anthropic-best-practices.json の hooks.stop-json-decision-block / hooks.stop-hook-active-loop-guard / hooks.stop-gate-and-block-cap

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && (pwd -W 2>/dev/null || pwd))"

# python は -S（site を読まない）で起動する。gate 一式は標準ライブラリだけで動き、.pth を多数読む環境では site の読み込みに 1 回 8 秒以上かかって
# 20 秒の打ち切りに間に合わなくなるため。
# python3 / python / py のうち、実際に動くものを使う。WindowsApps 配下のスタブは実行自体がハングし得るので文字列一致で避ける。
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
  echo '{"systemMessage": "[skill-review-gate] python が見つからないため skill のレビュー記録を評価できません（この終了は block していません）。python を使える状態にしてから、gate を手動で実行してください: skill_review_gate.py --strict"}'
  exit 0
fi
export PYTHONUTF8=1
# 入力 JSON（last_assistant_message が非常に長いことがある）は引数でなく stdin で python に渡す（引数の長さ上限で無音に落ちるのを避ける）。
# python の本体は -c で渡す（約 10K 文字。引数の上限に十分収まる）。
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
CAP = 3  # 1 turn あたりの block 上限（既存 setup gate と同じ値）


def emit(obj):
    print(json.dumps(obj))  # ensure_ascii 既定（cp1252 のコンソールでも壊れない）。受け取り側は JSON として復号する
    sys.exit(0)


def notice(msg):
    emit({"systemMessage": PFX + msg})


try:
    timeout_total = float(os.environ.get("SKILL_REVIEW_TIMEOUT_SEC") or 20)
except ValueError:
    timeout_total = 20.0
deadline = time.time() + timeout_total

root = Path(os.environ.get("SKILL_REVIEW_REPO_ROOT") or os.environ.get("CLAUDE_PROJECT_DIR") or str(script_dir.parents[3]))
GATE = script_dir / "skill_review_gate.py"
CONS = script_dir / "check_skill_review_consistency.py"


class Timeout(Exception):
    pass


def run(script, *args):
    """子 script を打ち切り付きで実行する。(終了コード, stdout, stderr) を返す。時間切れは Timeout。"""
    left = deadline - time.time()
    if left <= 0:
        raise Timeout()
    try:
        p = subprocess.run([sys.executable, "-S", str(script), "--repo-root", str(root)] + list(args), capture_output=True, timeout=left)
    except subprocess.TimeoutExpired:
        raise Timeout()
    cr = chr(13)  # CRLF の gate 出力の CR を取り除く
    return p.returncode, p.stdout.decode("utf-8", "replace").replace(cr, ""), p.stderr.decode("utf-8", "replace").replace(cr, "")


def summary(err):
    s = " ".join(err.split())
    return s[-200:] if s else "（stderr なし）"


def unevaluable(what, code, err):
    notice("%s の評価不能（gate が終了コード %s で終わった: %s）。block せず通します。gate を手動で実行して確認してください。" % (what, code, summary(err)))


try:
    ev = json.loads(raw) if raw.strip() else {}
    if not isinstance(ev, dict):
        ev = {}
except ValueError:
    ev = {}
event = ev.get("hook_event_name")

if event == "SessionStart":
    try:
        code, out, err = run(GATE, "--json")
        if code != 0:
            unevaluable("skill のレビュー記録", code, err)
        try:
            c = json.loads(out)["counts"]
            msg = "PASS %d／未レビューの負債 %d（台帳）／要レビュー %d" % (c["PASS"], c["BASELINE_DEBT"], c["NEEDS_REVIEW"])
        except (ValueError, KeyError, TypeError):
            unevaluable("skill のレビュー記録", code, "gate の出力を JSON として読めない")
        if CONS.exists():
            code, out, err = run(CONS, "--json")
            try:
                bad = [x["id"] for x in json.loads(out)["checks"] if not x["ok"]]
                if bad:
                    msg += " 整合検査: 失敗（%s）" % "・".join(bad)
            except (ValueError, KeyError, TypeError):
                msg += " 整合検査: 評価不能（終了コード %s: %s）" % (code, summary(err))
        else:
            msg += " 整合検査: 評価不能（check_skill_review_consistency.py が無い）"
        notice(msg.replace("\n", " "))
    except Timeout:
        notice("skill のレビュー記録の評価が時間切れ（%g 秒）のため、評価せずに通します。" % timeout_total)

# ---- Stop（イベント名が不明な場合も Stop として扱う）
active = bool(ev.get("stop_hook_active"))
sid = re.sub(r"[^A-Za-z0-9_-]", "", str(ev.get("session_id") or ""))[:64]
state_path = root / ".tmp" / "skill-review-gate" / ("state-%s.json" % sid if sid else "state.json")  # session ごとに分ける（session_id が無ければ従来のキー）


def read_blocks():
    try:
        v = int(json.loads(state_path.read_text(encoding="utf-8")).get("stop_blocks", 0))
        return v if v > 0 else 0
    except (OSError, ValueError, TypeError, AttributeError):
        return 0


def write_blocks(n):
    try:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps({"stop_blocks": n}), encoding="utf-8")
    except OSError:
        pass


blocks = read_blocks() if active else 0
if not active:
    write_blocks(0)  # 新しい turn: カウンタを 0 に戻してから評価する

try:
    code, out, err = run(GATE, "--strict")
    if code not in (0, 1):
        unevaluable("skill のレビュー記録", code, err)
except Timeout:
    notice("skill のレビュー記録の評価が時間切れ（%g 秒）のため、評価せずに通します。" % timeout_total)
needs = re.findall(r"^NEEDS_REVIEW: (\S+)(?: (\S+))?", out, re.M)
# 台帳の検証。gate の block（code == 1）が確定している場合は、台帳側が評価不能・時間切れでも block を捨てず、reason に注記する。
lcode, lout, lerr = 0, "", ""
warn = ""
try:
    lcode, lout, lerr = run(GATE, "--verify-ledger")
except Timeout:
    if code != 1:
        notice("負債台帳の検証が時間切れ（%g 秒）のため、評価せずに通します。" % timeout_total)
    lcode, warn = 0, "負債台帳の検証は時間切れ。"
if lcode not in (0, 1, 2):
    if code != 1:
        unevaluable("負債台帳の検証", lcode, lerr)
    warn = "負債台帳の検証は評価不能（終了コード %s: %s）。" % (lcode, summary(lerr))
    lcode = 0
tampered = re.findall(r"^TAMPERED (.+)$", lout, re.M) if lcode == 1 else []
if lcode == 2:
    warn = "負債台帳は検証不能（UNVERIFIABLE）。理由は skill_review_gate.py --verify-ledger で確認する。"

if code == 0 and lcode != 1:
    if warn:
        notice(warn.strip())
    sys.exit(0)

names = ", ".join("%s（%s）" % (n, s) if s else n for n, s in needs)
parts = []
if code == 1:
    parts.append("レビュー記録が無い・失効している・FAIL の skill: %s" % (names or "（gate の出力を参照）"))
if lcode == 1:
    parts.append("負債台帳に基準 commit と矛盾するエントリ: %s" % (", ".join(tampered) or "（台帳そのものを読めない）"))

if active and blocks >= CAP:
    notice("この turn で %d 回 block したため終了を許可します。%s。%s次の turn で再び block されます。" % (CAP, "／".join(parts), warn))

blocks += 1
write_blocks(blocks)
steps = ""
if code == 1:
    steps = ("readonly-reviewer に review-skill を実行させ（事前に skill_review_gate.py --hash で content_hash を得て、"
             "結果を append_skill_review_record.py --expected-hash 付きで保存する）、記録が保存されてから終了する。"
             "1 turn に 1 skill ずつ進める（複数をまとめて依頼しない）。")
if lcode == 1:
    steps += "台帳の不正は利用者の承認なしに直さず、利用者に報告する。"
emit({"decision": "block", "reason": "%s%s。%s%s（block %d/%d）" % (PFX, "／".join(parts), steps, (" " + warn) if warn else "", blocks, CAP)})
PY

# 何があっても block か systemMessage のどちらかが出る形にする: python が異常終了したら固定文字列で通知して通す（無音で通さない）
out="$("$PYTHON" -S -c "$PYSCRIPT" "$SCRIPT_DIR")"
rc=$?
if [[ $rc -ne 0 ]]; then
  echo '{"systemMessage": "[skill-review-gate] hook の内部エラーで skill のレビュー記録を評価できませんでした（評価不能。この終了は block していません）。gate を手動で実行して確認してください: skill_review_gate.py --strict"}'
  exit 0
fi
[[ -n "$out" ]] && printf '%s
' "$out"
exit 0
