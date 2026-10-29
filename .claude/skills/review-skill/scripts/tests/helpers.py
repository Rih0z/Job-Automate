"""review-skill の gate 一式の試験で使う共通の補助。標準ライブラリのみ。

TDD の Red 工程で先に書いた試験であり、本ファイルと各 test_*.py 冒頭のコメントが、被試験物の仕様の補完（計画書 §3 D1〜D4 に
書かれていない細部）を集約している。実装者はこれを仕様として読むこと。実 repo のパスは書き込まない
（一時ディレクトリに偽の repo を作る。実 repo を指すのは「被試験 script の場所」だけで、読み取り専用）。

=== 仕様の補完（計画書にない細部。決めた内容） ===
[リポジトリのルートの決め方]  引数 --repo-root > 環境変数 SKILL_REVIEW_REPO_ROOT > 環境変数 CLAUDE_PROJECT_DIR > script の位置から計算。
[現在日時]  環境変数 SKILL_REVIEW_NOW（例 2026-10-20T00:00:00Z。UTC・秒精度）。未設定なら実時刻。gate（期限切れ判定）と
            保存 script（reviewed_at）の両方が使う。
[試験用の継ぎ目（2 つ。T30 のためだけ）]  SKILL_REVIEW_TIMEOUT_SEC（hook が gate を待つ秒数。既定 20）、
            SKILL_REVIEW_TEST_DELAY_SEC（gate が起動直後にこの秒数 sleep する。既定 0）。
[偽 repo の構成]  <root>/.claude/skills/<skill>/SKILL.md ほか、_shared/anthropic-best-practices.json（principles は
            {"id": ...} のリスト・fetched・max_age_days）、_shared/skill-review-record.schema.json（required キー列）、
            review-skill/criteria/skill-quality.json、.claude/review-history/skill-review/<skill>/*.json（記録）、
            .claude/review-history/skill-review/baseline-unreviewed.json（負債台帳）、.claude/settings.json、
            workflows/software-development/review-skill.md（生成区間を持つ）。review-skill 自身も偽 repo では 1 つの skill であり、
            criteria を持つので criteria を変えると review-skill の hash も変わる。
[記録 JSON（skill-review-record/v1）]  schema・skill・reviewed_at（YYYY-MM-DDTHH:MM:SSZ）・
            target{files[{path,sha256}], content_hash}・criteria{file,sha256}・best_practices_snapshot{fetched,max_age_days}・
            reviewer{kind,subagent_type,agent_id,model}・result{axes[{id,score}],score,verdict,must_pass_failures[],
            findings[{criterion_id,severity,location,comment}]}。
[hash の表記]  64 桁の小文字 hex（接頭辞なし）。criteria.sha256 は criteria ファイルの内容（先頭 8000 バイトに NUL が無ければ
            CRLF を LF に正規化）の sha256。ref_content_hash が計画書 D2 の content_hash の実行可能な定義（走査経路）。
[criteria JSON]  {"schema","axes":[{"id","name","weight","criteria":[{"id","name","weight","must_pass","checks":[str],
            "principles":[str]}]}], "pass_rule":{"min_score":90,"must_pass_all":true}, "reviewer_requirements":{...}}。
            axes は 5 つ（structure・description・instructions・output・practicality）で各 weight 20。
[終了コード]  gate: --strict は 0（PASS と BASELINE_DEBT のみ）/1。--all と --json は常に 0。--hash は 64 桁 hex だけを出して 0
            （未知の skill は 2）。--verify-ledger は 0/1/2（計画書どおり）。
            保存 script: 0=保存または記録済み、1=検査で拒否（記録ファイルを作らない・stderr に理由）、2=引数不備（argparse）。
            整合検査: 0=全項目 OK、1=1 項目でも NG。render: 0=成功、1=失敗（区間マーカー欠落・--check の不一致）。
[出力の形]  gate --all: 1 行 1 skill で「<skill>: <STATE>」と、末尾に「PASS=n BASELINE_DEBT=m NEEDS_REVIEW=k」。
            台帳から外せる skill には行に「台帳から外せる」を付ける。期限切れは「WARN: best-practices SoT expired」の行。
            gate --json: {"skills":{name:{"state":...,"notes":[...]}},"counts":{"PASS","BASELINE_DEBT","NEEDS_REVIEW"},
            "warnings":[str]}。notes は「ledger_removable」「agent_id_unavailable」等。NEEDS_REVIEW は
            FAIL・INVALID・STALE・UNREVIEWED の合計。
            gate --verify-ledger: 改ざんは「TAMPERED <skill>」を 1 行ずつ、検証不能は「UNVERIFIABLE: <理由>」を stdout に出す。
            保存 script: 保存したら「SAVED <repo 相対パス>」、記録済みなら「ALREADY_RECORDED <repo 相対パス>」を stdout 1 行目に出す。
            整合検査 --json: {"ok":bool,"checks":[{"id","ok","message"}]}。id は render・principles・ledger・hook_registration・
            schema・criteria（計画書 D4 の ①〜⑥ に対応）。人間向けの標準出力には NG の項目名を含める。
            hook: Stop の block は {"decision":"block","reason":...}、通すときは何も出さないか {"systemMessage":...}。
            SessionStart は {"systemMessage":"PASS n／未レビューの負債 m（台帳）／要レビュー k"}（整合検査が失敗したら
            「整合検査: 失敗（<id>…）」を同じ message に足す。改行を含めない 1 行）。
[保存 script の CLI]  --repo-root R --skill NAME --expected-hash H --result-file F --agent-id ID --subagent-type T --model M
            [--reviewer-kind KIND（既定 subagent。空文字・subagent 以外は拒否）]。--reviewed-at・--content-hash は存在しない
            （渡すと argparse が exit 2）。
[render の CLI]  render_review_skill_md.py --repo-root R [--write | --check]。無指定は生成区間を stdout に出す。
            区間は md 内の【生成ここから】【生成ここまで】の行（行全体がそのマーカー）。生成区間には axis の name・weight、各 criterion の
            name・checks[] の文をすべて含める。--write は区間の外を 1 バイトも変えない。
[期限切れの境界]  SoT が期限切れ = 現在日（UTC の日付）が fetched + max_age_days 日の日付より後。当日（2026-10-25）は期限内、翌日（2026-10-26）から期限切れ。
[hash の境界]  「テキスト」= 先頭 8000 バイトに NUL を含まない（index 7999 の NUL は含む=バイナリ、index 8000 の NUL は含まない=テキスト）。BOM は特別扱いしない
            （BOM 付きと無しは別 hash、BOM 付きの CRLF と LF は同じ hash）。core.autocrlf=true で commit・checkout した作業ツリー（CRLF）でも
            LF の作業ツリーと同じ hash。
[壊れた記録]  記録ファイルが JSON として読めない: gate は例外を出さず、その記録は無視し（skill の hash と結びつけられない）、--json の warnings に
            ファイル名を入れる。JSON として読めて target.content_hash が現在の hash と一致するが、必須キー欠落・型違い・整合不一致
            （PASS なのに must_pass_failures が空でない等）・reviewer.kind 不正のものは INVALID の候補（判定表の行 3）。INVALID は台帳より優先（行 3 が行 4 に優先）。
[render の妥当性]  render は criteria の weight 合計を検査しない（検査は整合検査の criteria の役目）。合計が 100 でなくても生成して exit 0。
[T15 の前提]  浅い clone の判定（git rev-parse --is-shallow-repository が true なら UNVERIFIABLE）が実装に暗黙に必要。git の無い・実行できない環境も同じく UNVERIFIABLE。
[T26 の前提]  標準出力・標準エラーを UTF-8 に再設定する（sys.stdout.reconfigure(encoding="utf-8")）必要がある。PYTHONIOENCODING=cp1252 でも落ちない。
[計画外の追加（実装レビューで残すか判断）]  SKILL_REVIEW_TEST_DELAY_SEC（gate の起動直後の sleep）、SKILL_REVIEW_TIMEOUT_SEC の名前、
            --reviewer-kind（保存 script）、記録の best_practices_snapshot の細かいキー、SKILL_REVIEW_SCRIPTS_DIR（試験の側の機構。下記）。
[SKILL_REVIEW_SCRIPTS_DIR（試験側の機構）]  変異試験用。設定すると、そのディレクトリに同名の script があればそれを使い、無ければ既定の scripts/ を使う。
[試験の入口]  run_tests.py（skip が 1 件でもあれば非ゼロ。SKILL_REVIEW_TEST_ALLOW_SKIP=1 のときだけ許す）、run_mutants.py（変異体ごとに試験が落ちることを確かめる）。
            Git Bash が無い環境は skip でなく失敗にする。
[台帳の基準（計画書 改訂 5）]  --verify-ledger の基準 = 台帳を「最後に追加した commit」（旧台帳を削除する commit の後に新台帳を追加する commit を足すと、
            その新台帳が基準になる = 再基準化）。基準 commit の後の in-place 編集（エントリの追加・hash の書き換え）は検出する。
[gate の内部エラー（改訂 5）]  gate の終了コードは 0（問題なし）・1（--strict で要レビュー）・3（内部エラー）。hook は 1 だけを block に使い、
            3 や想定外の終了コード（2・7・139 など）では block せず、systemMessage に「評価不能」を出して通す。
[SKILL_REVIEW_TEST_MARK_DIR（T30 の注入用。計画外の追加。実装レビューで残すか判断）]  設定されていて SKILL_REVIEW_TEST_DELAY_SEC が 0 より大きいとき、
            gate は sleep に入る直前にこのディレクトリへ started を、sleep が終わったら finished を作る。hook が gate の完了を待たずに返ったことを、
            絶対時間でなく finished が無いことで確かめるための印。
[試験の注入用の継ぎ目]  --reviewer-kind と SKILL_REVIEW_TEST_DELAY_SEC と SKILL_REVIEW_TEST_MARK_DIR は試験の注入用で、本番の公開引数にするかは実装レビューで判断する。
[hook の state]  <root>/.tmp/skill-review-gate/state.json の stop_blocks = この turn で本 hook が block した回数。
            新 turn（stop_hook_active false）で 0 に戻して評価し、block したら +1。active のとき stop_blocks が 3 以上なら通す。
"""
import atexit
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent  # 被試験物の既定の置き場（実装後に存在する）。読み取り専用で参照するだけ。
REAL_REPO = HERE.parents[4]  # この repo のルート（ログの既定の保存先を決めるためだけに使う。偽 repo の作成には使わない）
CLOSE_VERIFY = REAL_REPO / ".tmp" / "close-verify" / "skill-review-gate"


def script_path(name):
    """被試験物の場所。環境変数 SKILL_REVIEW_SCRIPTS_DIR にその名前の script があればそれ（変異体）、無ければ既定の scripts/。"""
    overlay = os.environ.get("SKILL_REVIEW_SCRIPTS_DIR")
    if overlay and (Path(overlay) / name).exists():
        return Path(overlay) / name
    return SCRIPTS / name


GATE = script_path("skill_review_gate.py")
APPEND = script_path("append_skill_review_record.py")
HOOK_SH = script_path("hook-skill-review-gate.sh")
CONSISTENCY = script_path("check_skill_review_consistency.py")
RENDER = script_path("render_review_skill_md.py")

NOW = "2026-10-20T00:00:00Z"  # SoT（fetched 2026-09-25 + 30 日）の期限内
EXPIRED_NOW = "2026-10-27T00:00:00Z"  # 期限（2026-10-25）の後
SOT_FETCHED = "2026-09-25"
SOT_MAX_AGE = 30

SKILLS_REL = ".claude/skills"
HISTORY_REL = ".claude/review-history/skill-review"
LEDGER_REL = HISTORY_REL + "/baseline-unreviewed.json"
CRITERIA_REL = SKILLS_REL + "/review-skill/criteria/skill-quality.json"
SOT_REL = SKILLS_REL + "/_shared/anthropic-best-practices.json"
SCHEMA_REL = SKILLS_REL + "/_shared/skill-review-record.schema.json"
SETTINGS_REL = ".claude/settings.json"
MD_REL = "workflows/software-development/review-skill.md"
STATE_REL = ".tmp/skill-review-gate/state.json"
SETUP_STATE_REL = ".tmp/harness-setup/state.json"
MARK_BEGIN = "【生成ここから】"
MARK_END = "【生成ここまで】"

AXIS_IDS = ["structure", "description", "instructions", "output", "practicality"]
PRINCIPLE_IDS = ["skills.p1", "skills.p2", "hooks.p1"]
REQUIRED_TOP = ["schema", "skill", "reviewed_at", "target", "criteria", "best_practices_snapshot", "reviewer", "result"]

_FAKE_HOME = None


def fake_home():
    """git の global 設定・HOME 系を実環境から遮断するための空ディレクトリ。プロセス終了時に消す。"""
    global _FAKE_HOME
    if _FAKE_HOME is None:
        _FAKE_HOME = Path(tempfile.mkdtemp(prefix="srg-gitcfg-"))
        (_FAKE_HOME / "gitconfig").write_text("", encoding="utf-8")
        atexit.register(lambda: shutil.rmtree(_FAKE_HOME, ignore_errors=True))
    return _FAKE_HOME


def base_env(**extra):
    """利用者の環境（git の global 設定・HOME 系・SKILL_REVIEW_*・CLAUDE_PROJECT_DIR）を遮断した子プロセス用の環境。"""
    env = dict(os.environ)
    for k in list(env):
        if (k.startswith("SKILL_REVIEW_") and k != "SKILL_REVIEW_SCRIPTS_DIR") or k == "CLAUDE_PROJECT_DIR":
            del env[k]
    home = str(fake_home())
    env["HOME"] = home
    env["USERPROFILE"] = home
    env["XDG_CONFIG_HOME"] = home
    env["PYTHONUTF8"] = "1"
    env["SKILL_REVIEW_NOW"] = NOW
    env["GIT_CONFIG_GLOBAL"] = str(fake_home() / "gitconfig")
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_TERMINAL_PROMPT"] = "0"
    for k, v in extra.items():
        if v is None:
            env.pop(k, None)
        else:
            env[k] = v
    return env


class Result:
    def __init__(self, code, out, err, elapsed=0.0):
        self.code, self.out, self.err, self.elapsed = code, out, err, elapsed

    def json(self):
        return json.loads(self.out)

    def __repr__(self):
        return "Result(code=%r, out=%r, err=%r)" % (self.code, self.out[:400], self.err[:400])


SUBPROCESS_TIMEOUT = 30  # 全ての子プロセスの打ち切り（秒）。python の起動が遅い環境でも Red が速く終わるようにする


def kill_tree(pid):
    """pid とその子孫を止める（Windows は taskkill /T /F）。"""
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(pid)], capture_output=True)
    else:
        try:
            os.killpg(pid, 9)
        except OSError:
            pass


def kill_leftovers(marker):
    """コマンドラインに marker（偽 repo の一時パス）を含む自分の試験由来のプロセスを止める。打ち切り後に残った孫プロセスの後始末用。"""
    if os.name == "nt":
        ps = ("Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine.Contains('%s') -and $_.ProcessId -ne %d } "
              "| ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }" % (marker.replace("'", "''"), os.getpid()))
        subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, timeout=120)
    else:
        subprocess.run(["pkill", "-f", marker], capture_output=True)


def run_proc(cmd, env=None, input_text=None, cwd=None, timeout=SUBPROCESS_TIMEOUT):
    """出力は一時ファイルへ受ける（孫プロセスが pipe を握っていても、親の終了で戻る。所要時間も親の終了で測る）。"""
    out, err = tempfile.TemporaryFile(), tempfile.TemporaryFile()
    t0 = time.time()
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=out, stderr=err, env=env or base_env(), cwd=str(cwd) if cwd else None)
    try:
        try:
            p.stdin.write((input_text or "").encode("utf-8"))
            p.stdin.close()
        except OSError:
            pass
        p.wait(timeout=min(timeout, SUBPROCESS_TIMEOUT))
    except subprocess.TimeoutExpired:
        kill_tree(p.pid)
        raise AssertionError("子プロセスが %d 秒で終わらない（打ち切り）: %s" % (SUBPROCESS_TIMEOUT, " ".join(map(str, cmd))[:200]))
    elapsed = time.time() - t0
    out.seek(0)
    err.seek(0)
    r = Result(p.returncode, out.read().decode("utf-8", "replace"), err.read().decode("utf-8", "replace"), elapsed)
    out.close()
    err.close()
    return r


def require_exists(path):
    """被試験物が無いときは子プロセスを起動せず即失敗にする（Red を速くする。種別は FileNotFoundError = 未実装）。"""
    if not Path(path).exists():
        raise FileNotFoundError("被試験物が存在しない（未実装）: %s" % path)


def run_py(script, args, env=None, input_text=None, timeout=SUBPROCESS_TIMEOUT):
    require_exists(script)
    return run_proc([sys.executable, str(script)] + [str(a) for a in args], env=env, input_text=input_text, timeout=timeout)


def run_gate(repo, *args, env=None):
    return run_py(GATE, ["--repo-root", str(repo)] + list(args), env=env)


def gate_json(repo, env=None):
    r = run_gate(repo, "--json", env=env)
    if r.code != 0:
        raise AssertionError("gate --json が exit %s: %r" % (r.code, r))
    return r.json()


def states(repo, env=None):
    return {k: v["state"] for k, v in gate_json(repo, env)["skills"].items()}


def run_append(repo, skill, expected_hash, result_file, agent_id="agent-1", subagent_type="readonly-reviewer",
               model="test-model", extra=None, env=None, omit=()):
    args = ["--repo-root", str(repo), "--skill", skill, "--expected-hash", expected_hash, "--result-file", str(result_file),
            "--agent-id", agent_id, "--subagent-type", subagent_type, "--model", model]
    if "expected-hash" in omit:
        i = args.index("--expected-hash")
        del args[i:i + 2]
    return run_py(APPEND, args + list(extra or []), env=env)


def run_consistency(repo, *args, env=None):
    return run_py(CONSISTENCY, ["--repo-root", str(repo)] + list(args), env=env)


def run_render(repo, *args, env=None):
    return run_py(RENDER, ["--repo-root", str(repo)] + list(args), env=env)


def find_bash():
    cands = [os.environ.get("SKILL_REVIEW_TEST_BASH"), r"C:\Program Files\Git\bin\bash.exe", r"C:\Program Files\Git\usr\bin\bash.exe"]
    git = shutil.which("git")
    if git:
        cands.append(str(Path(git).resolve().parents[1] / "bin" / "bash.exe"))
    for c in cands:
        if c and Path(c).exists():
            return c
    w = shutil.which("bash")
    if w and "system32" not in w.lower():  # WSL の bash.exe は使わない
        return w
    return None


def run_hook(repo, event_json, env=None, bash=None, timeout=SUBPROCESS_TIMEOUT, hook=None):
    """hook を実物で起動する。event_json は stdin に渡す dict（または文字列）。"""
    hook = Path(hook) if hook else HOOK_SH  # hook= で、落ちる gate を隣に置いた hook の複製を指せる（T35）
    require_exists(hook)
    bash = bash or find_bash()
    if bash is None:
        raise AssertionError("Git Bash が見つからない。hook の試験は skip にせず失敗にする（緑に見えるのを防ぐ）")
    e = env or base_env()
    e = dict(e)
    e["CLAUDE_PROJECT_DIR"] = Path(repo).as_posix()
    text = event_json if isinstance(event_json, str) else json.dumps(event_json)
    r = run_proc([bash, hook.as_posix()], env=e, input_text=text, timeout=timeout)
    try:
        r.data = json.loads(r.out) if r.out.strip() else None
    except ValueError:
        r.data = "__PARSE_ERROR__"
    return r


STOP_NEW = {"hook_event_name": "Stop", "stop_hook_active": False}
STOP_ACTIVE = {"hook_event_name": "Stop", "stop_hook_active": True}
SESSION_START = {"hook_event_name": "SessionStart"}


# ---------------------------------------------------------------- 内容 hash の参照実装（計画書 D2 の走査経路）
def _is_text(data):
    return b"\0" not in data[:8000]


def normalize_bytes(data):
    return data.replace(b"\r\n", b"\n") if _is_text(data) else data


def sha256_hex(data):
    return hashlib.sha256(data).hexdigest()


def ref_files(skill_dir):
    skill_dir = Path(skill_dir)
    out = []
    for p in skill_dir.rglob("*"):
        if p.is_symlink() or not p.is_file():
            continue
        rel = p.relative_to(skill_dir).as_posix()
        parts = rel.split("/")
        if "__pycache__" in parts or rel.endswith(".pyc") or parts[-1] == ".DS_Store" or rel.startswith("scripts/tests/"):
            continue
        out.append(rel)
    return sorted(out, key=lambda s: s.encode("utf-8"))


def ref_content_hash(skill_dir):
    skill_dir = Path(skill_dir)
    h = hashlib.sha256()
    for rel in ref_files(skill_dir):
        data = normalize_bytes((skill_dir / rel).read_bytes())
        h.update(rel.encode("utf-8") + b"\0" + data + b"\0")
    return h.hexdigest()


def skill_hash(repo, name):
    return ref_content_hash(Path(repo) / SKILLS_REL / name)


def criteria_sha(repo):
    return sha256_hex(normalize_bytes((Path(repo) / CRITERIA_REL).read_bytes()))


# ---------------------------------------------------------------- 偽 repo の部品
def make_criteria():
    axes = []
    for i, aid in enumerate(AXIS_IDS):
        axes.append({
            "id": aid, "name": "軸%d・%s" % (i + 1, aid), "weight": 20,
            "criteria": [{
                "id": "C%d" % (i + 1), "name": "基準%d" % (i + 1), "weight": 20, "must_pass": i == 0,
                "checks": ["確認項目%d-a" % (i + 1), "確認項目%d-b" % (i + 1)],
                "principles": [PRINCIPLE_IDS[i % 2]],
            }],
        })
    return {
        "schema": "skill-quality/v1",
        "axes": axes,
        "pass_rule": {"min_score": 90, "must_pass_all": True},
        "reviewer_requirements": {
            "separate_agent": True, "subagent_type": "readonly-reviewer",
            "pass_to_reviewer": ["target_abs_path", "criteria_abs_path"],
            "forbid_to_reviewer": ["作成意図", "会話履歴"],
            "fixed_prompt": "固定の依頼文（試験用）",
            "output_schema": {"axes": "[{id,score}]", "score": "int", "verdict": "PASS|FAIL",
                              "must_pass_failures": "[str]", "findings": "[{criterion_id,severity,location,comment}]"},
        },
    }


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return path


def write_text(path, text, newline="\n"):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline=newline)
    return path


def write_skill(repo, name, files=None):
    d = Path(repo) / SKILLS_REL / name
    files = files or {"SKILL.md": "---\nname: %s\ndescription: 試験用 skill\n---\n本文\n" % name}
    for rel, content in files.items():
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            p.write_bytes(content)
        else:
            p.write_text(content, encoding="utf-8", newline="\n")
    return d


def write_settings(repo, stop=True, session=True):
    cmd = 'bash "$CLAUDE_PROJECT_DIR"/.claude/skills/review-skill/scripts/hook-skill-review-gate.sh'
    other = 'bash "$CLAUDE_PROJECT_DIR"/.claude/skills/agent-harness-bootstrap/scripts/hook-stop-setup-gate.sh'
    hooks = {"SessionStart": [{"matcher": "startup", "hooks": [{"type": "command", "command": other, "timeout": 30}]}],
             "Stop": [{"hooks": [{"type": "command", "command": other, "timeout": 30}]}]}
    if stop:
        hooks["Stop"].append({"hooks": [{"type": "command", "command": cmd, "timeout": 30}]})
    if session:
        hooks["SessionStart"].append({"matcher": "startup|resume|clear|compact|fork",
                                      "hooks": [{"type": "command", "command": cmd, "timeout": 30}]})
    return write_json(Path(repo) / SETTINGS_REL, {"hooks": hooks})


def make_repo(root, skills=("alpha",), git=False, consistent=False):
    """偽 repo を作る。review-skill（criteria を持つ）は常に含まれる。git=True なら git init（user 設定は偽 repo 内のみ）して
    全体を 1 commit する。consistent=True なら（既定 False: python の起動が遅い環境で試験時間を縮めるため） review-skill.md の生成区間を render で最新にする（hook の SessionStart 試験用）。"""
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    write_skill(root, "review-skill")
    write_json(root / CRITERIA_REL, make_criteria())
    for s in skills:
        write_skill(root, s)
    write_json(root / SOT_REL, {"schema": "anthropic-best-practices/v1", "fetched": SOT_FETCHED, "max_age_days": SOT_MAX_AGE,
                                "principles": [{"id": i, "statement": "試験用"} for i in PRINCIPLE_IDS]})
    write_json(root / SCHEMA_REL, {"$id": "skill-review-record/v1", "type": "object", "required": list(REQUIRED_TOP)})
    write_settings(root)
    write_text(root / MD_REL, "# review-skill 手順（試験用）\n\n前置き\n\n%s\n(placeholder)\n%s\n\n後書き\n" % (MARK_BEGIN, MARK_END))
    (root / ".gitignore").write_text(".tmp/\n__pycache__/\nignored.txt\n", encoding="utf-8", newline="\n")
    if consistent:
        run_render(root, "--write")
    if git:
        git_init(root)
        git_commit_all(root, "initial")
    return root


# ---------------------------------------------------------------- 記録・台帳の部品
def make_result(verdict="PASS", score=None, axes=None, must_pass_failures=None, findings=None):
    if score is None:
        score = 95 if verdict == "PASS" else 70
    per = score // len(AXIS_IDS)
    if axes is None:
        axes = [{"id": a, "score": per} for a in AXIS_IDS]
    return {"axes": axes, "score": score, "verdict": verdict,
            "must_pass_failures": must_pass_failures or [], "findings": findings or []}


def inconsistent_results():
    """保存時（T10）にも gate の INVALID 判定にも使う、整合不一致の result 6 種。各ケースは「その 1 点だけ」が原因になるように整えてある。"""
    ok5 = [{"id": a, "score": 19} for a in AXIS_IDS]  # 合計 95
    high = [{"criterion_id": "C1", "severity": "high", "location": "SKILL.md:1", "comment": "重大"}]
    return {
        "must_pass_failures だけが原因（PASS・95 点・axes 整合）": make_result("PASS", score=95, axes=ok5, must_pass_failures=["C1"]),
        "score < min_score だけが原因（PASS・85 点・axes は 17×5 で整合）": make_result(
            "PASS", score=85, axes=[{"id": a, "score": 17} for a in AXIS_IDS]),
        "high の finding だけが原因（PASS・95 点・axes 整合）": make_result("PASS", score=95, axes=ok5, findings=high),
        "axes の欠落だけが原因（FAIL・76 点・4 軸の合計 76 で整合・verdict も整合）": make_result("FAIL", score=76, axes=ok5[:4]),
        "axes の合計が score と合わないことだけが原因（PASS・95 点・axes は 18×5=90）": make_result(
            "PASS", score=95, axes=[{"id": a, "score": 18} for a in AXIS_IDS]),
        "未知の axis id（criteria の軸の欠落を伴う。PASS・95 点・合計 95）": make_result(
            "PASS", score=95, axes=ok5[:4] + [{"id": "unknown", "score": 19}]),
    }


def write_result_file(dirpath, result, name="result.json"):
    return write_json(Path(dirpath) / name, result)


def write_record(repo, skill, result=None, reviewed_at=NOW, content_hash=None, crit_sha=None, kind="subagent",
                 agent_id="agent-1", suffix=None, drop=()):
    """手で記録を置く（保存 script を通さない）。kind=None で reviewer.kind を欠落させる。"""
    repo = Path(repo)
    rec = {
        "schema": "skill-review-record/v1", "skill": skill, "reviewed_at": reviewed_at,
        "target": {"files": [{"path": "SKILL.md", "sha256": "0" * 64}],
                   "content_hash": content_hash if content_hash is not None else skill_hash(repo, skill)},
        "criteria": {"file": CRITERIA_REL, "sha256": crit_sha if crit_sha is not None else criteria_sha(repo)},
        "best_practices_snapshot": {"fetched": SOT_FETCHED, "max_age_days": SOT_MAX_AGE},
        "reviewer": {"kind": kind, "subagent_type": "readonly-reviewer", "agent_id": agent_id, "model": "test-model"},
        "result": result if result is not None else make_result("PASS"),
    }
    if kind is None:
        del rec["reviewer"]["kind"]
    for k in drop:
        rec.pop(k, None)
    stamp = reviewed_at.replace("-", "").replace(":", "")
    if suffix is None:
        suffix = sha256_hex(json.dumps(rec, sort_keys=True).encode("utf-8"))[:8]
    return write_json(repo / HISTORY_REL / skill / ("%s-%s.json" % (stamp, suffix)), rec)


def record_files(repo, skill):
    d = Path(repo) / HISTORY_REL / skill
    return sorted(d.glob("*.json")) if d.is_dir() else []


def pass_records(repo, names=None, **kw):
    """全 skill（または names）に、現在の hash に対する PASS 記録を置く。"""
    base = Path(repo) / SKILLS_REL
    for d in sorted(base.iterdir()):
        if d.name.startswith("_") or not (d / "SKILL.md").exists():
            continue
        if names is None or d.name in names:
            write_record(repo, d.name, **kw)


def write_ledger(repo, entries, registered="2026-10-27", reason="試験用の免除"):
    """entries: {skill: hash または None（None なら現在の hash）}。"""
    skills = {}
    for name, h in entries.items():
        skills[name] = {"content_hash": h if h is not None else skill_hash(repo, name), "registered": registered, "reason": reason}
    return write_json(Path(repo) / LEDGER_REL, {"schema": "skill-review-baseline/v1", "skills": skills})


def read_ledger(repo):
    return json.loads((Path(repo) / LEDGER_REL).read_text(encoding="utf-8"))


# ---------------------------------------------------------------- git
def git(repo, *args, check=True):
    r = run_proc(["git", "-C", str(repo)] + [str(a) for a in args])
    if check and r.code != 0:
        raise AssertionError("git %s 失敗: %r" % (" ".join(map(str, args)), r))
    return r


def git_init(repo):
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "tester@example.invalid")
    git(repo, "config", "user.name", "tester")
    git(repo, "config", "commit.gpgsign", "false")
    git(repo, "config", "core.autocrlf", "false")


def git_commit_all(repo, msg="c"):
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", msg)


def git_commit_paths(repo, paths, msg="c"):
    git(repo, "add", "--", *paths)
    git(repo, "commit", "-q", "-m", msg, "--", *paths)


# ---------------------------------------------------------------- 後始末と基底クラス
def _rm_readonly(func, path, _exc):
    os.chmod(path, stat.S_IWRITE)
    func(path)


def rmtree_force(path):
    for i in range(5):  # Windows は孫プロセスやウイルス対策がファイルを握っていると失敗するので、少し待って再試行する
        try:
            shutil.rmtree(path, onerror=_rm_readonly)
            return
        except OSError:
            time.sleep(1 + i)
    shutil.rmtree(path, ignore_errors=True)


class RepoTestCase(unittest.TestCase):
    """各試験に専用の一時ディレクトリ（self.tmp）を与え、終了時に消す。偽 repo は self.tmp / "repo"。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="srg-test-")).resolve()
        self.addCleanup(rmtree_force, self.tmp)
        self.repo = self.tmp / "repo"

    def mk(self, skills=("alpha",), git=False, consistent=False):
        return make_repo(self.repo, skills=skills, git=git, consistent=consistent)

    def result_file(self, result, name="result.json"):
        return write_result_file(self.tmp, result, name)

    def assertSkillState(self, repo, skill, expected, env=None):
        got = states(repo, env)
        self.assertEqual(got.get(skill), expected, "skill=%s states=%r" % (skill, got))
