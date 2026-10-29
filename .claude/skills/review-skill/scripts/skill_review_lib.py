#!/usr/bin/env python3
"""skill_review_lib.py — skill レビュー gate 一式（gate・保存・整合検査・render）の共通部品。標準ライブラリのみ。

単体では実行しない。skill_review_gate.py / append_skill_review_record.py / check_skill_review_consistency.py /
render_review_skill_md.py が import する。仕様の正本は .tmp/plans/2026-10-27-skill-review-gate.md（§3 D1〜D4）と、
scripts/tests/helpers.py 冒頭の「仕様の補完」。
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

SKILLS_REL = ".claude/skills"
HISTORY_REL = ".claude/review-history/skill-review"
LEDGER_REL = HISTORY_REL + "/baseline-unreviewed.json"
CRITERIA_REL = SKILLS_REL + "/review-skill/criteria/skill-quality.json"
SOT_REL = SKILLS_REL + "/_shared/anthropic-best-practices.json"
SCHEMA_REL = SKILLS_REL + "/_shared/skill-review-record.schema.json"
SETTINGS_REL = ".claude/settings.json"
MD_REL = "workflows/software-development/review-skill.md"
HOOK_NAME = "hook-skill-review-gate.sh"
MARK_BEGIN = "【生成ここから】"
MARK_END = "【生成ここまで】"

RECORD_SCHEMA = "skill-review-record/v1"
# 保存 script と gate が検査する必須キー。スキーマ（skill-review-record.schema.json）の required と一致していることを整合検査 ⑤ が確かめる。
REQUIRED_TOP = ["schema", "skill", "reviewed_at", "target", "criteria", "best_practices_snapshot", "reviewer", "result"]

# 入れ子の必須キー（validate_record が検査するもの）。パスの "[]" は配列の要素。スキーマの required との一致を整合検査 ⑤ が確かめる。
NESTED_REQUIRED = {
    "target": ["files", "content_hash"],
    "target.files[]": ["path", "sha256"],
    "criteria": ["file", "sha256"],
    "best_practices_snapshot": ["fetched", "max_age_days"],
    "reviewer": ["kind", "subagent_type", "agent_id", "model"],
    "result": ["axes", "score", "verdict", "must_pass_failures", "findings"],
    "result.axes[]": ["id", "score"],
    "result.findings[]": ["criterion_id", "severity", "location", "comment"],
}

_TIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SEVERITIES = ("high", "medium", "low")


def reconfigure_stdio():
    """cp1252 のコンソールでも日本語を出せるようにする（T26）。"""
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, "reconfigure"):
            try:
                s.reconfigure(encoding="utf-8")
            except Exception:
                pass


def resolve_root(arg, script_file):
    """リポジトリのルート: 引数 > SKILL_REVIEW_REPO_ROOT > CLAUDE_PROJECT_DIR > script の位置から計算。"""
    for v in (arg, os.environ.get("SKILL_REVIEW_REPO_ROOT"), os.environ.get("CLAUDE_PROJECT_DIR")):
        if v:
            return Path(v)
    return Path(script_file).resolve().parents[4]


def now_utc():
    """現在日時（UTC・秒精度）。SKILL_REVIEW_NOW（例 2026-10-20T00:00:00Z）で差し替え可能。"""
    v = os.environ.get("SKILL_REVIEW_NOW")
    if v:
        try:
            return datetime.strptime(v, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        except ValueError:
            try:
                d = datetime.fromisoformat(v.replace("Z", "+00:00"))
                return (d if d.tzinfo else d.replace(tzinfo=timezone.utc)).astimezone(timezone.utc).replace(microsecond=0)
            except ValueError:
                pass
    return datetime.now(timezone.utc).replace(microsecond=0)


# ------------------------------------------------------------------ hash
def sha256_hex(data):
    return hashlib.sha256(data).hexdigest()


def normalize_bytes(data):
    """先頭 8000 バイトに NUL を含まないテキストだけ CRLF を LF に正規化する。バイナリは無変換。BOM は特別扱いしない。"""
    if b"\0" in data[:8000]:
        return data
    return data.replace(b"\r\n", b"\n")


def excluded(rel):
    parts = rel.split("/")
    return ("__pycache__" in parts or rel.endswith(".pyc") or parts[-1] == ".DS_Store" or rel.startswith("scripts/tests/"))


def skill_names(root):
    base = Path(root) / SKILLS_REL
    if not base.is_dir():
        return []
    return sorted(d.name for d in base.iterdir() if not d.name.startswith("_") and d.is_dir() and (d / "SKILL.md").is_file())


def _git_exe(root):
    if not (Path(root) / ".git").exists():
        return None
    return shutil.which("git")


def _scan_files(skill_dir):
    out = []
    for dirpath, dirnames, filenames in os.walk(str(skill_dir), followlinks=False):
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            if os.path.islink(p) or not os.path.isfile(p):
                continue
            out.append(os.path.relpath(p, str(skill_dir)).replace(os.sep, "/"))
    return out


_GIT_CACHE = {}


def _git_files(root, name, git):
    """git ls-files を 1 プロセスにつき 1 回だけ呼び（skill が 60 個あると 1 回 1〜2 秒かかる環境がある）、skill ごとに振り分ける。"""
    key = (str(root), git)
    if key not in _GIT_CACHE:
        r = subprocess.run([git, "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", SKILLS_REL],
                           cwd=str(root), capture_output=True, timeout=60)
        if r.returncode != 0:
            _GIT_CACHE[key] = None
        else:
            by = {}
            base = SKILLS_REL + "/"
            for raw in r.stdout.split(b"\0"):
                if not raw:
                    continue
                s = raw.decode("utf-8", "replace")
                if not s.startswith(base):
                    continue
                skill, _, rel = s[len(base):].partition("/")
                if rel:
                    by.setdefault(skill, set()).add(rel)
            _GIT_CACHE[key] = by
    by = _GIT_CACHE[key]
    return None if by is None else sorted(by.get(name, ()))


def skill_content(root, name):
    """(content_hash, [(rel, sha256 of normalized bytes)], unreadable_count)。

    ファイル集合: git があれば git ls-files -z --cached --others --exclude-standard（追跡 + 未追跡で gitignore されないもの）。
    git が無ければ走査（.gitignore は適用しない）。作業ツリーに無い・読めないファイルは除外して件数を返す。"""
    skill_dir = Path(root) / SKILLS_REL / name
    rels = None
    git = _git_exe(root)
    if git:
        try:
            rels = _git_files(root, name, git)
        except (OSError, subprocess.SubprocessError):
            rels = None
    if rels is None:
        rels = _scan_files(skill_dir)
    unreadable = 0
    items = []
    for rel in set(rels):
        if excluded(rel):
            continue
        p = skill_dir / rel
        if p.is_symlink():
            continue
        try:
            if not p.is_file():
                unreadable += 1
                continue
            data = p.read_bytes()
        except OSError:
            unreadable += 1
            continue
        items.append((rel, normalize_bytes(data)))
    items.sort(key=lambda t: t[0].encode("utf-8"))
    h = hashlib.sha256()
    files = []
    for rel, data in items:
        h.update(rel.encode("utf-8") + b"\0" + data + b"\0")
        files.append((rel, sha256_hex(data)))
    return h.hexdigest(), files, unreadable


# ------------------------------------------------------------------ JSON の読み込み
def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def criteria_info(root):
    """(sha256 または None, data または None, error または None)。"""
    p = Path(root) / CRITERIA_REL
    try:
        raw = p.read_bytes()
    except OSError as e:
        return None, None, "criteria を読めない: %s" % e
    sha = sha256_hex(normalize_bytes(raw))
    try:
        return sha, json.loads(raw.decode("utf-8")), None
    except (ValueError, UnicodeDecodeError) as e:
        return sha, None, "criteria が JSON として読めない: %s" % e


def criteria_axes(data):
    """criteria から ({axis id: weight}, min_score)。壊れていれば (None, None)。"""
    try:
        axes = {a["id"]: a["weight"] for a in data["axes"]}
        return axes, data["pass_rule"]["min_score"]
    except (KeyError, TypeError):
        return None, None


def sot_status(root, now):
    """(fetched, max_age_days, expired(bool|None), error)。期限切れ = 現在日（UTC）> fetched + max_age_days 日。"""
    try:
        d = read_json(Path(root) / SOT_REL)
        fetched, age = d["fetched"], int(d["max_age_days"])
        due = date.fromisoformat(str(fetched)) + timedelta(days=age)
        return fetched, age, now.date() > due, None
    except (OSError, ValueError, KeyError, TypeError) as e:
        return None, None, None, "best-practices SoT を読めない: %s" % e


# ------------------------------------------------------------------ 記録の検査
def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _nonempty_str(v):
    return isinstance(v, str) and v.strip() != ""


def validate_record(rec, axes=None, min_score=None):
    """記録（skill-review-record/v1）の検査。エラー文字列のリストを返す（空なら有効）。
    axes は {axis id: weight}（criteria 由来。None なら軸の網羅・配点の検査を省く）、min_score は合格点。"""
    errs = []
    if not isinstance(rec, dict):
        return ["記録が JSON オブジェクトでない"]
    for k in REQUIRED_TOP:
        if k not in rec:
            errs.append("必須キー欠落: %s" % k)
    if errs:
        return errs
    if rec["schema"] != RECORD_SCHEMA:
        errs.append("schema が %s でない" % RECORD_SCHEMA)
    if not _nonempty_str(rec["skill"]):
        errs.append("skill が文字列でない")
    if not (isinstance(rec["reviewed_at"], str) and _TIME_RE.match(rec["reviewed_at"])):
        errs.append("reviewed_at が YYYY-MM-DDTHH:MM:SSZ でない")
    t = rec["target"]
    if not isinstance(t, dict):
        errs.append("target がオブジェクトでない")
    else:
        if not isinstance(t.get("content_hash"), str) or not t.get("content_hash"):
            errs.append("target.content_hash が文字列でない")
        files = t.get("files")
        if not isinstance(files, list) or not all(isinstance(f, dict) and isinstance(f.get("path"), str) and isinstance(f.get("sha256"), str) for f in files):
            errs.append("target.files の形が不正")
    c = rec["criteria"]
    if not (isinstance(c, dict) and isinstance(c.get("file"), str) and isinstance(c.get("sha256"), str) and c.get("sha256")):
        errs.append("criteria の形が不正（file・sha256 が文字列）")
    b = rec["best_practices_snapshot"]
    if not (isinstance(b, dict) and isinstance(b.get("fetched"), str) and _is_int(b.get("max_age_days"))):
        errs.append("best_practices_snapshot の形が不正")
    r = rec["reviewer"]
    if not isinstance(r, dict):
        errs.append("reviewer がオブジェクトでない")
    else:
        if r.get("kind") != "subagent":
            errs.append("reviewer.kind が subagent でない（%r）" % (r.get("kind"),))
        for k in ("subagent_type", "agent_id", "model"):
            if not _nonempty_str(r.get(k)):
                errs.append("reviewer.%s が空または文字列でない" % k)
    res = rec["result"]
    if not isinstance(res, dict):
        errs.append("result がオブジェクトでない")
        return errs
    ax = res.get("axes")
    ax_ok = (isinstance(ax, list) and all(isinstance(a, dict) and isinstance(a.get("id"), str) and _is_int(a.get("score")) for a in ax))
    if not ax_ok:
        errs.append("result.axes の形が不正（id と整数 score の配列）")
    if not _is_int(res.get("score")):
        errs.append("result.score が整数でない")
    verdict = res.get("verdict")
    if verdict not in ("PASS", "FAIL"):
        errs.append("result.verdict が PASS / FAIL でない")
    mpf = res.get("must_pass_failures")
    if not (isinstance(mpf, list) and all(isinstance(x, str) for x in mpf)):
        errs.append("result.must_pass_failures が文字列の配列でない")
    fnd = res.get("findings")
    f_ok = isinstance(fnd, list) and all(
        isinstance(f, dict) and f.get("severity") in SEVERITIES and isinstance(f.get("criterion_id"), str)
        and isinstance(f.get("location"), str) and isinstance(f.get("comment"), str) for f in fnd)
    if not f_ok:
        errs.append("result.findings の形が不正")
    if errs:
        return errs
    # 整合
    if sum(a["score"] for a in ax) != res["score"]:
        errs.append("result.axes の得点合計が result.score と合わない")
    ids = [a["id"] for a in ax]
    if len(set(ids)) != len(ids):
        errs.append("result.axes に重複した axis id がある")
    if axes is not None:
        if set(ids) != set(axes):
            errs.append("result.axes が criteria の全 axis id と一致しない")
        else:
            for a in ax:
                w = axes[a["id"]]
                if a["score"] < 0 or (isinstance(w, (int, float)) and a["score"] > w):
                    errs.append("axis %s の得点が 0〜配点の範囲外" % a["id"])
    if verdict == "PASS":
        if mpf:
            errs.append("verdict が PASS なのに must_pass_failures が空でない")
        if min_score is not None and res["score"] < min_score:
            errs.append("verdict が PASS なのに score が合格点（%s）未満" % min_score)
        if any(f["severity"] == "high" for f in fnd):
            errs.append("verdict が PASS なのに high の finding が残っている")
    return errs


def load_records(root, skill):
    """([(ファイル名, オブジェクト)], [警告])。JSON として読めない記録は無視して警告にする。"""
    d = Path(root) / HISTORY_REL / skill
    recs, warns = [], []
    if not d.is_dir():
        return recs, warns
    for f in sorted(d.glob("*.json")):
        try:
            recs.append((f.name, json.loads(f.read_text(encoding="utf-8"))))
        except (OSError, ValueError):
            warns.append("WARN: 記録ファイルを JSON として読めない（無視）: %s/%s" % (skill, f.name))
    return recs, warns


def load_ledger(root):
    """(skills 辞書, 警告または None)。"""
    p = Path(root) / LEDGER_REL
    if not p.exists():
        return {}, None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        sk = d.get("skills", {})
        if not isinstance(sk, dict):
            raise ValueError("skills が辞書でない")
        return sk, None
    except (OSError, ValueError, AttributeError) as e:
        return {}, "WARN: 負債台帳を読めない（無視）: %s" % e


# ------------------------------------------------------------------ 台帳の検証
def verify_ledger(root):
    """(終了コード, 出力行)。0 = 問題なし、1 = 改ざん、2 = UNVERIFIABLE。"""
    root = Path(root)
    ledger = root / LEDGER_REL
    if not ledger.exists():
        return 0, ["OK: 負債台帳なし"]
    git = _git_exe(root)
    if not git:
        return 2, ["UNVERIFIABLE: git が使えない（git が無い、または .git が無い）"]

    def g(*args):
        r = subprocess.run([git] + list(args), cwd=str(root), capture_output=True, timeout=60)
        return r.returncode, r.stdout

    try:
        rc, out = g("rev-parse", "--is-shallow-repository")
        if rc == 0 and out.decode("utf-8", "replace").strip() == "true":
            return 2, ["UNVERIFIABLE: 浅い clone で台帳の基準 commit を取れない"]
        rc, out = g("log", "--diff-filter=A", "--format=%H", "--", LEDGER_REL)
        anchors = [x for x in out.decode("utf-8", "replace").splitlines() if x.strip()] if rc == 0 else []
        if not anchors:
            return 2, ["UNVERIFIABLE: 台帳を追加した commit が無い（未 commit、または履歴を取れない）"]
        anchor = anchors[0]  # 最新の追加 commit（旧台帳の削除 → 新台帳の追加で基準が取り直される）
        rc, out = g("show", "%s:%s" % (anchor, LEDGER_REL))
        if rc != 0:
            return 2, ["UNVERIFIABLE: 基準 commit %s の台帳を読めない" % anchor[:8]]
    except (OSError, subprocess.SubprocessError) as e:
        return 2, ["UNVERIFIABLE: git を実行できない: %s" % e]
    try:
        base = json.loads(out.decode("utf-8")).get("skills", {})
    except (ValueError, AttributeError):
        return 2, ["UNVERIFIABLE: 基準 commit の台帳が JSON として読めない"]
    try:
        cur = json.loads(ledger.read_text(encoding="utf-8")).get("skills", {})
        if not isinstance(cur, dict) or not isinstance(base, dict):
            raise ValueError("skills が辞書でない")
    except (OSError, ValueError, AttributeError):
        return 1, ["TAMPERED (台帳そのもの): 作業ツリーの台帳が JSON として読めない"]
    lines = ["TAMPERED %s" % name for name in sorted(cur) if name not in base or base[name] != cur[name]]
    if lines:
        return 1, lines
    return 0, ["OK: 台帳のエントリは基準 commit %s と矛盾しない" % anchor[:8]]


# ------------------------------------------------------------------ render
def render_section(data):
    """criteria（dict）から生成区間（マーカー行を含む）の行リストを作る。決定的。山括弧のタグは使わない。"""
    pr = data.get("pass_rule") if isinstance(data, dict) else None
    min_score = pr.get("min_score") if isinstance(pr, dict) else None
    lines = [MARK_BEGIN, "", "（この区間は criteria の skill-quality.json から render_review_skill_md.py が生成する。手で編集しない）", ""]
    head = "## 評価軸と採点目安"
    if min_score is not None:
        head += "（合格: %s 点以上かつ必須基準をすべて満たす）" % min_score
    lines += [head, ""]
    for n, axis in enumerate(data.get("axes", []) if isinstance(data, dict) else [], 1):
        lines.append("### %d. %s 【配点：%s 点】" % (n, axis.get("name", axis.get("id", "")), axis.get("weight", "")))
        lines.append("")
        for c in axis.get("criteria", []):
            tag = "・必須" if c.get("must_pass") else ""
            lines.append("#### %s（%s 点%s）" % (c.get("name", c.get("id", "")), c.get("weight", ""), tag))
            for chk in c.get("checks", []):
                lines.append("- [ ] %s" % chk)
            lines.append("")
        guide = axis.get("scoring_guide")
        if guide:
            lines += ["採点目安", "", "| 点数 | 基準 |", "|------|------|"]
            lines += ["| %s | %s |" % (g.get("range", ""), g.get("criterion", "")) for g in guide]
            lines.append("")
    lines.append(MARK_END)
    return lines


# ------------------------------------------------------------------ 整合検査の部品
def check_criteria_validity(data):
    """criteria JSON の妥当性（整合検査 ⑥）。エラー文字列のリスト。"""
    errs = []
    if not isinstance(data, dict):
        return ["criteria がオブジェクトでない"]
    axes = data.get("axes")
    if not isinstance(axes, list) or len(axes) != 5:
        errs.append("axes が 5 つでない")
        axes = axes if isinstance(axes, list) else []
    total = 0
    for a in axes:
        if not isinstance(a, dict) or not isinstance(a.get("id"), str) or not isinstance(a.get("name"), str) or not isinstance(a.get("weight"), (int, float)):
            errs.append("axis の必須キー（id・name・weight）が不正")
            continue
        total += a["weight"]
        cs = a.get("criteria")
        if not isinstance(cs, list) or not cs:
            errs.append("axis %s に criteria が無い" % a["id"])
            continue
        wsum = 0
        for c in cs:
            if not isinstance(c, dict):
                errs.append("axis %s の criterion がオブジェクトでない" % a["id"])
                continue
            cid = c.get("id", "?")
            if not isinstance(c.get("id"), str) or not isinstance(c.get("name"), str) or not isinstance(c.get("weight"), (int, float)) \
                    or not isinstance(c.get("must_pass"), bool):
                errs.append("criterion %s の必須キー（id・name・weight・must_pass）が不正" % cid)
                continue
            if not isinstance(c.get("checks"), list) or not c["checks"] or not all(isinstance(x, str) for x in c["checks"]):
                errs.append("criterion %s に checks（文字列の配列）が無い" % cid)
            if not isinstance(c.get("principles"), list) or not all(isinstance(x, str) for x in c["principles"]):
                errs.append("criterion %s に principles（文字列の配列）が無い" % cid)
            wsum += c["weight"]
        if wsum != a["weight"]:
            errs.append("axis %s の criterion の配点合計 %s が axis の配点 %s と合わない" % (a["id"], wsum, a["weight"]))
    if total != 100:
        errs.append("axes の weight 合計が 100 でない（%s）" % total)
    ids = [a.get("id") for a in axes if isinstance(a, dict)]
    if len(set(ids)) != len(ids):
        errs.append("axis id が重複している")
    pr = data.get("pass_rule")
    if not (isinstance(pr, dict) and _is_int(pr.get("min_score")) and isinstance(pr.get("must_pass_all"), bool)):
        errs.append("pass_rule（min_score・must_pass_all）が無いか不正")
    rr = data.get("reviewer_requirements")
    if not isinstance(rr, dict):
        errs.append("reviewer_requirements が無い")
    else:
        for k in ("separate_agent", "subagent_type", "pass_to_reviewer", "forbid_to_reviewer", "fixed_prompt", "output_schema"):
            if k not in rr:
                errs.append("reviewer_requirements.%s が無い" % k)
    return errs
