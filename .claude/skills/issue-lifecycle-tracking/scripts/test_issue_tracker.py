"""issue_tracker.py の試験（unittest、標準ライブラリだけ）。

実行: python .claude/skills/issue-lifecycle-tracking/scripts/test_issue_tracker.py
各試験は一時ディレクトリに .claude/issue-tracker.json と issues/ を作り、script を subprocess で呼ぶ。
対応: 計画 2026-11-11-issue-handoff-knowhow-redesign.md r3 の I1〜I13（r2・r3 の追加分を含む）。
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "issue_tracker.py"
GIT = shutil.which("git")
NOW_S = "2026-11-11T12:00:00-08:00"


def md_source(**over):
    s = {"type": "md_dirs", "root": "issues",
         "active": ["open", "processing", "pending"], "closed": ["closed"],
         "merged_dir": "withdrawn", "merged_state": "withdrawn",
         "status_line": {"regex": "^status:\\s*\\S+", "template": "status: {state}"},
         "exclude": ["README.md", "_TEMPLATE*.md", "_evidence/**", "_generated/**"],
         "index_files": ["issues/README.md"]}
    s.update(over)
    return s


def json_source(**over):
    s = {"type": "json_findings", "path": "data/findings.json", "array": "findings",
         "id": "id", "title": "finding", "status": "status",
         "closed_values": ["done", "false-positive"]}
    s.update(over)
    return s


def issue_text(title, body="", status="open", extra_front=""):
    return f"---\nid: x\ntitle: {title}\nstatus: {status}\n{extra_front}---\n\n# {title}\n\n{body}\n"


def git(cwd, *args, check=True):
    p = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid",
                        "-c", "core.autocrlf=false", *args],
                       cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    if check and p.returncode != 0:
        raise AssertionError(f"git {args}: {p.stderr}")
    return p.stdout


def _force_remove(func, path, _exc):
    """Windows で git の object（読み取り専用）を消すために、属性を外してから消し直す。"""
    os.chmod(path, 0o666)
    func(path)


class Base(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.env = dict(os.environ, PYTHONUTF8="1", GIT_CEILING_DIRECTORIES=str(self.root.parent))
        self.write_config([md_source(), json_source()])

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def write_config(self, sources, base=None, **extra):
        base = base or self.root
        cfg = base / ".claude" / "issue-tracker.json"
        cfg.parent.mkdir(parents=True, exist_ok=True)
        cfg.write_text(json.dumps(dict(sources=sources, related_field="関連:", **extra), ensure_ascii=False),
                       encoding="utf-8")
        self.cfg = cfg
        return cfg

    def put(self, rel, text, raw=None):
        f = self.root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        if raw is not None:
            f.write_bytes(raw)
        else:
            f.write_bytes(text.encode("utf-8"))
        return f

    def findings(self, items):
        return self.put("data/findings.json", json.dumps({"findings": items}, ensure_ascii=False, indent=2) + "\n")

    def run_cli(self, *args, cwd=None, config=True):
        cmd = [sys.executable, str(SCRIPT), *args]
        if config:
            cmd += ["--config", str(self.cfg)]
        p = subprocess.run(cmd, cwd=cwd or self.root, capture_output=True, text=True,
                           encoding="utf-8", env=self.env)
        return p.returncode, p.stdout, p.stderr

    def result_lines(self, out):
        return [l for l in out.splitlines() if l.strip() and l[0].isdigit()]

    def snapshot(self):
        return {str(p.relative_to(self.root)): p.read_bytes()
                for p in self.root.rglob("*") if p.is_file() and ".git" not in p.parts}


class TestRelated(Base):
    def test_I1_similar_title_ranks_first_unrelated_is_low_and_exit_is_zero(self):
        self.put("issues/open/0002-font.md", issue_text("Slide font color is wrong"))
        rc, out, err = self.run_cli("related", "--text", "login 500 error")
        self.assertEqual(rc, 0, err)
        self.assertEqual(self.result_lines(out), [], "無関係なものだけなら候補に出さない")
        self.assertIn("候補なし", out)
        self.put("issues/open/0001-login.md", issue_text("Login page returns 500 error"))
        rc, out, err = self.run_cli("related", "--text", "login 500 error")
        self.assertEqual(rc, 0, err)
        lines = self.result_lines(out)
        self.assertEqual(len(lines), 1, out)
        self.assertEqual(lines[0].split()[1:3], ["open", "issues/open/0001-login.md"])
        self.assertEqual(float(lines[0].split()[0]), 1.0)  # 題名 3/3 × 0.7 + 本文 3/3 × 0.3

    def test_I1b_empty_input_no_issues_and_default_limit(self):
        for text in ("", "あ"):
            rc, out, err = self.run_cli("related", "--text", text)
            self.assertEqual(rc, 0, err)
            self.assertIn("候補なし", out)
        rc, out, err = self.run_cli("related", "--text", "handoff release")
        self.assertEqual((rc, self.result_lines(out)), (0, []))
        for i in range(10):
            self.put(f"issues/open/{i:04d}.md", issue_text(f"handoff release {i}"))
        rc, out, err = self.run_cli("related", "--text", "handoff release")
        self.assertEqual(len(self.result_lines(out)), 8)

    def test_I2_japanese_bigrams_and_closed_only_with_flag(self):
        self.put("issues/open/0001.md", issue_text("ログイン画面で500エラーが出る"))
        self.put("issues/closed/0009.md", issue_text("ログイン画面のエラー（旧）", status="closed"))
        rc, out, err = self.run_cli("related", "--text", "ログイン画面のエラー")
        self.assertEqual(rc, 0, err)
        self.assertIn("issues/open/0001.md", out)
        self.assertNotIn("0009.md", out)
        rc, out, err = self.run_cli("related", "--text", "ログイン画面のエラー", "--include-closed")
        self.assertIn("issues/closed/0009.md", out)

    def test_I3_excluded_files_are_not_listed_and_non_utf8_is_skipped_with_warning(self):
        self.put("issues/open/0001.md", issue_text("handoff release command"))
        self.put("issues/open/README.md", issue_text("handoff release command"))
        self.put("issues/open/_TEMPLATE_issue.md", issue_text("handoff release command"))
        self.put("issues/open/_evidence/e.md", issue_text("handoff release command"))
        self.put("issues/README.md", issue_text("handoff release command"))
        self.put("issues/open/bad.md", None, raw=b"# handoff release \xff\xfe\x00\x81\n")
        rc, out, err = self.run_cli("related", "--text", "handoff release")
        self.assertEqual(rc, 0, err)
        self.assertIn("issues/open/0001.md", out)
        for name in ("README.md", "_TEMPLATE_issue.md", "_evidence", "bad.md"):
            self.assertNotIn(name, out)
        self.assertIn("bad.md", err)
        self.assertIn("警告", err)

    def test_I3b_multibyte_char_cut_at_8kb_boundary_is_still_read(self):
        for shift in range(3):  # 8KB の境目が 3 バイト文字の 1・2・3 バイト目に来るようにずらす
            head = "# 境目の試験\n" + "x" * shift
            self.put(f"issues/open/b{shift}.md", head + "あ" * 4000)
        rc, out, err = self.run_cli("related", "--text", "境目の試験")
        self.assertEqual(rc, 0, err)
        self.assertNotIn("UTF-8 で読めない", err)
        self.assertEqual(sorted(l.split()[2] for l in self.result_lines(out)),
                         [f"issues/open/b{i}.md" for i in range(3)])

    def test_I4_title_match_beats_long_body_match(self):
        self.put("issues/open/0001.md", issue_text("handoff release command", body="short"))
        long_body = ("handoff release " * 400) + ("lorem ipsum " * 500)
        self.put("issues/open/0002.md", issue_text("misc cleanup", body=long_body))
        rc, out, err = self.run_cli("related", "--text", "handoff release")
        self.assertEqual(rc, 0, err)
        lines = self.result_lines(out)
        self.assertIn("0001.md", lines[0])
        self.assertIn("0002.md", lines[1])
        self.assertGreater(float(lines[0].split()[0]), float(lines[1].split()[0]))

    def test_I5_deadline_gives_partial_result_and_warning_and_1500_issues_finish(self):
        self.put("issues/open/0000.md", issue_text("handoff zero"))  # 入力 3 語のうち 1 語だけが重なる
        for i in range(1, 1500):
            self.put(f"issues/open/{i:04d}.md", issue_text(f"topic number {i}", body="filler text " * 300))
        self.put("issues/open/9999.md", issue_text("handoff release target"))
        rc, out, err = self.run_cli("related", "--text", "handoff release target", "--deadline", "0")
        self.assertEqual(rc, 0, err)
        self.assertIn("時間上限", err)
        self.assertIn("途中まで", err)
        lines = self.result_lines(out)
        self.assertEqual([l.split()[2] for l in lines], ["issues/open/0000.md"], "途中までに読んだものだけを出す")
        rc, out, err = self.run_cli("related", "--text", "handoff release target", "--deadline", "600")
        self.assertEqual(rc, 0, err)
        self.assertNotIn("時間上限", err)
        self.assertEqual(self.result_lines(out)[0].split()[2], "issues/open/9999.md")

    def test_I6_json_findings_use_finding_as_title_and_hide_closed_values(self):
        self.findings([
            {"id": "CR-01", "finding": "handoff release の対象を絞る", "status": "backlog"},
            {"id": "CR-02", "finding": "handoff release の古い案", "status": "done"},
            {"id": "CR-03", "finding": "handoff release の誤検知", "status": "false-positive"},
        ])
        rc, out, err = self.run_cli("related", "--text", "handoff release")
        self.assertEqual(rc, 0, err)
        self.assertIn("CR-01", out)
        self.assertNotIn("CR-02", out)
        self.assertNotIn("CR-03", out)
        rc, out, err = self.run_cli("related", "--text", "handoff release", "--include-closed")
        self.assertIn("CR-02", out)
        self.assertIn("CR-03", out)


class TestRequest(Base):
    def test_I7_md_request_creates_section_dedupes_and_keeps_bom_crlf(self):
        f = self.put("issues/open/0001.md", issue_text("A", body="本文"))
        rc, out, err = self.run_cli("request", "issues/open/0001.md", "--text", "要望A", "--now", NOW_S)
        self.assertEqual(rc, 0, err)
        t = f.read_text(encoding="utf-8")
        self.assertIn("## 利用者の要望", t)
        self.assertIn(f"- {NOW_S} 要望A", t)
        before = f.read_bytes()
        rc, out, err = self.run_cli("request", "issues/open/0001.md", "--text", "要望A", "--now", "2026-11-12T00:00:00-08:00")
        self.assertEqual(rc, 0, err)
        self.assertIn("already", out)
        self.assertEqual(f.read_bytes(), before)
        rc, out, err = self.run_cli("request", "issues/open/0001.md", "--text", "要望B", "--now", NOW_S)
        t = f.read_text(encoding="utf-8")
        self.assertEqual(t.count("## 利用者の要望"), 1)
        self.assertLess(t.index("要望A"), t.index("要望B"))
        g = self.put("issues/open/0002.md", None,
                     raw=b"\xef\xbb\xbf" + issue_text("B", body="x").replace("\n", "\r\n").encode("utf-8"))
        rc, out, err = self.run_cli("request", "issues/open/0002.md", "--text", "要望C", "--now", NOW_S)
        self.assertEqual(rc, 0, err)
        raw = g.read_bytes()
        self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))
        self.assertNotIn(b"\n", raw.replace(b"\r\n", b""))
        self.assertIn("要望C".encode("utf-8"), raw)

    def test_I8_json_request_appends_to_requests(self):
        f = self.findings([{"id": "CR-01", "finding": "x", "status": "backlog"}])
        rc, out, err = self.run_cli("request", "CR-01", "--text", "要望D", "--now", NOW_S)
        self.assertEqual(rc, 0, err)
        item = json.loads(f.read_text(encoding="utf-8"))["findings"][0]
        self.assertEqual(item["requests"], [{"at": NOW_S, "text": "要望D"}])
        rc, out, err = self.run_cli("request", "CR-01", "--text", "要望D", "--now", NOW_S)
        self.assertIn("already", out)
        item = json.loads(f.read_text(encoding="utf-8"))["findings"][0]
        self.assertEqual(len(item["requests"]), 1)
        rc, out, err = self.run_cli("request", "CR-99", "--text", "x", "--now", NOW_S)
        self.assertEqual(rc, 2)
        rc, out, err = self.run_cli("request", "issues/open/nope.md", "--text", "x", "--now", NOW_S)
        self.assertEqual(rc, 2)


SRC_BODY = "\n".join(f"本文の行 {i} は統合元の内容" for i in range(40))


class TestMerge(Base):
    def mk_pair(self):
        dst = self.put("issues/open/0001-main.md", issue_text("本命の issue", body="本命の本文"))
        src = self.put("issues/open/0002-dup.md",
                       issue_text("重複した issue", body=SRC_BODY + f"\n\n## 利用者の要望\n\n- {NOW_S} 要望E\n"))
        return src, dst

    def test_I9_merge_appends_section_marks_src_rewrites_status_and_moves(self):
        src, dst = self.mk_pair()
        self.put(".tmp/handoffs/ho-src.md", "---\nissue: issues/open/0002-dup.md\n---\n# h\n")
        self.put(".tmp/handoffs/ho-other.md", "---\nissue: issues/open/0001-main.md\n---\n# h\n")
        rc, out, err = self.run_cli("merge", "issues/open/0002-dup.md", "--into", "issues/open/0001-main.md")
        self.assertEqual(rc, 0, err)
        self.assertFalse(src.exists())
        moved = self.root / "issues" / "withdrawn" / "0002-dup.md"
        self.assertTrue(moved.exists())
        mt = moved.read_text(encoding="utf-8")
        self.assertIn("統合先: issues/open/0001-main.md", mt)
        self.assertRegex(mt, r"(?m)^status: withdrawn$")
        self.assertTrue(mt.startswith("---\n"))
        dt = dst.read_text(encoding="utf-8")
        self.assertIn("## 統合: 重複した issue", dt)
        self.assertIn("issues/withdrawn/0002-dup.md", dt)
        self.assertIn("要望E", dt)
        self.assertIn("issues/README.md", out)
        self.assertIn("ho-src.md", out, "src を指す handoff を一覧に出す")
        self.assertNotIn("ho-other.md", out)

    def test_I9b_merged_state_is_written_to_status_line(self):
        self.write_config([md_source(merged_dir="closed", merged_state="closed（統合）"), json_source()])
        self.mk_pair()
        rc, out, err = self.run_cli("merge", "issues/open/0002-dup.md", "--into", "issues/open/0001-main.md")
        self.assertEqual(rc, 0, err)
        mt = (self.root / "issues" / "closed" / "0002-dup.md").read_text(encoding="utf-8")
        self.assertRegex(mt, r"(?m)^status: closed（統合）$")

    @unittest.skipUnless(GIT, "git が無い")
    def test_I9c_git_tracked_merge_is_staged_as_rename(self):
        self.mk_pair()
        git(self.root, "init", "-q")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "base")
        rc, out, err = self.run_cli("merge", "issues/open/0002-dup.md", "--into", "issues/open/0001-main.md")
        self.assertEqual(rc, 0, err)
        st = git(self.root, "status", "--porcelain")
        self.assertRegex(st, r"(?m)^R. issues/open/0002-dup.md -> issues/withdrawn/0002-dup.md$")

    def test_I10_merge_rejections_change_nothing(self):
        self.mk_pair()
        self.put("issues/closed/0003-done.md", issue_text("終わった issue", status="closed"))
        self.findings([{"id": "CR-01", "finding": "x", "status": "backlog"},
                       {"id": "CR-02", "finding": "y", "status": "backlog"}])
        cases = [
            ("issues/open/0002-dup.md", "issues/open/0002-dup.md"),
            ("issues/open/0002-dup.md", "issues/closed/0003-done.md"),
            ("CR-01", "CR-02"),
        ]
        before = self.snapshot()
        for s, d in cases:
            rc, out, err = self.run_cli("merge", s, "--into", d)
            self.assertEqual(rc, 2, (s, d, out, err))
            self.assertEqual(self.snapshot(), before, (s, d))
        self.put("issues/withdrawn/0002-dup.md", issue_text("先にあった", status="withdrawn"))
        before = self.snapshot()
        rc, out, err = self.run_cli("merge", "issues/open/0002-dup.md", "--into", "issues/open/0001-main.md")
        self.assertEqual(rc, 2, out + err)
        self.assertEqual(self.snapshot(), before)
        src = md_source(); del src["merged_dir"]
        self.write_config([src, json_source()])
        before = self.snapshot()
        rc, out, err = self.run_cli("merge", "issues/open/0002-dup.md", "--into", "issues/open/0001-main.md")
        self.assertEqual(rc, 2, out + err)
        self.assertEqual(self.snapshot(), before)

    def test_I9d_merge_lists_handoffs_from_config_handoffs_dir(self):
        self.mk_pair()
        (self.root / ".claude" / "handoff-lifecycle.json").write_text(
            json.dumps({"handoffs_dir": "work/.tmp/handoffs"}), encoding="utf-8")
        self.put("work/.tmp/handoffs/ho-cfg.md", "---\nissue: issues/open/0002-dup.md\n---\n# h\n")
        self.put(".tmp/handoffs/ho-default.md", "---\nissue: issues/open/0002-dup.md\n---\n# h\n")
        rc, out, err = self.run_cli("merge", "issues/open/0002-dup.md", "--into", "issues/open/0001-main.md")
        self.assertEqual(rc, 0, err)
        self.assertIn("ho-cfg.md", out)
        self.assertNotIn("ho-default.md", out)

    @unittest.skipUnless(os.name == "nt", "読み取り専用の file を置き換えられないのは Windows だけ")
    def test_I10b_merge_dst_write_failure_changes_nothing(self):
        src, dst = self.mk_pair()
        before = self.snapshot()
        os.chmod(dst, 0o444)
        try:
            rc, out, err = self.run_cli("merge", "issues/open/0002-dup.md", "--into", "issues/open/0001-main.md")
        finally:
            os.chmod(dst, 0o666)
        self.assertEqual(rc, 2, out + err)
        self.assertEqual(self.snapshot(), before)

    @unittest.skipUnless(os.name == "nt", "読み取り専用の file を消せないのは Windows だけ")
    def test_I10c_merge_src_unlink_failure_reports_leftover(self):
        src, dst = self.mk_pair()
        os.chmod(src, 0o444)
        try:
            rc, out, err = self.run_cli("merge", "issues/open/0002-dup.md", "--into", "issues/open/0001-main.md")
        finally:
            os.chmod(src, 0o666)
        self.assertEqual(rc, 2, out + err)
        self.assertIn("統合元が残った", err)
        self.assertIn("## 統合: 重複した issue", dst.read_text(encoding="utf-8"))
        self.assertTrue((self.root / "issues" / "withdrawn" / "0002-dup.md").exists())

    def test_I11_merge_outside_git_is_plain_move(self):
        self.mk_pair()
        rc, out, err = self.run_cli("merge", "issues/open/0002-dup.md", "--into", "issues/open/0001-main.md")
        self.assertEqual(rc, 0, err)
        self.assertNotIn("staged:", out)
        self.assertTrue((self.root / "issues" / "withdrawn" / "0002-dup.md").exists())


@unittest.skipUnless(GIT, "git が無い")
class TestCheckNew(Base):
    def setUp(self):
        super().setUp()
        self.put("issues/open/0001.md", issue_text("古い issue（関連欄なし）"))
        self.findings([{"id": "CR-01", "finding": "x", "status": "backlog"}])
        git(self.root, "init", "-q")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "base")

    def stage(self, *paths):
        git(self.root, "add", "-A", "--", *paths)

    def test_I12_new_md_needs_related_line(self):
        self.put("issues/open/0002.md", issue_text("新しい issue"))
        self.stage("issues")
        rc, out, err = self.run_cli("check-new")
        self.assertEqual(rc, 1, out + err)
        self.assertIn("issues/open/0002.md", out)
        self.put("issues/open/0002.md", issue_text("新しい issue", body="関連:"))
        self.stage("issues")
        rc, out, err = self.run_cli("check-new")
        self.assertEqual(rc, 1, "空の関連欄は欠けている扱い")
        self.put("issues/open/0002.md", issue_text("新しい issue", body="関連: 適当"))
        self.stage("issues")
        rc, out, err = self.run_cli("check-new")
        self.assertEqual(rc, 1, "パスでも『なし（related 確認済み）』でもない値は欠けている扱い")
        self.put("issues/open/0002.md", issue_text("新しい issue", body="関連: なし（related 確認済み）"))
        self.stage("issues")
        rc, out, err = self.run_cli("check-new")
        self.assertEqual(rc, 0, out + err)
        self.put("issues/open/0002.md", issue_text("新しい issue", body="関連: issues/open/0001.md（別の症状なので分けた）"))
        self.stage("issues")
        rc, out, err = self.run_cli("check-new")
        self.assertEqual(rc, 0, out + err)

    def test_I12b_existing_and_moved_files_are_not_new(self):
        self.put("issues/open/0001.md", issue_text("古い issue（関連欄なし）", body="追記"))
        self.stage("issues")
        rc, out, err = self.run_cli("check-new")
        self.assertEqual(rc, 0, out + err)
        (self.root / "issues" / "processing").mkdir(parents=True, exist_ok=True)
        git(self.root, "mv", "issues/open/0001.md", "issues/processing/0001.md")
        rc, out, err = self.run_cli("check-new")
        self.assertEqual(rc, 0, out + err)

    def test_I12c_heavily_rewritten_move_is_not_new(self):
        (self.root / "issues" / "open" / "0001.md").unlink()
        self.put("issues/processing/0001.md", "# 全く違う本文\n" + "\n".join(f"新しい行 {i}" for i in range(50)))
        self.stage("issues")
        rc, out, err = self.run_cli("check-new")
        self.assertEqual(rc, 0, out + err)

    def test_I12d_new_template_and_evidence_are_out_of_scope(self):
        self.put("issues/open/_TEMPLATE_new.md", "# テンプレート\n")
        self.put("issues/open/_evidence/e.md", "# 証跡\n")
        self.put("issues/_evidence/f.md", "# 証跡\n")
        self.put("issues/notes.md", "# 状態ディレクトリの外\n")
        self.stage("issues")
        rc, out, err = self.run_cli("check-new")
        self.assertEqual(rc, 0, out + err)

    def test_I12e_json_new_finding_needs_related_key_by_id_difference(self):
        self.findings([{"id": "CR-01", "finding": "x", "status": "backlog"},
                       {"id": "CR-02", "finding": "y", "status": "backlog"}])
        self.stage("data")
        rc, out, err = self.run_cli("check-new")
        self.assertEqual(rc, 1, out + err)
        self.assertIn("CR-02", out)
        self.assertNotIn("CR-01", out)
        self.findings([{"id": "CR-01", "finding": "x", "status": "backlog"},
                       {"id": "CR-02", "finding": "y", "status": "backlog", "related": []}])
        self.stage("data")
        rc, out, err = self.run_cli("check-new")
        self.assertEqual(rc, 0, out + err)


    def test_I12f_base_ref_and_git_errors(self):
        self.put("issues/open/0002.md", issue_text("二つ目", body="関連: なし（related 確認済み）"))
        self.stage("issues"); git(self.root, "commit", "-qm", "second")
        self.put("issues/open/0003.md", issue_text("三つ目"))
        self.stage("issues")
        rc, out, err = self.run_cli("check-new", "--base", "HEAD~1")
        self.assertEqual(rc, 1, out + err)
        self.assertIn("0003.md", out)
        self.assertNotIn("0002.md", out)
        rc, out, err = self.run_cli("check-new", "--base", "no-such-ref")
        self.assertEqual(rc, 2, out + err)
        shutil.rmtree(self.root / ".git", onerror=_force_remove)
        rc, out, err = self.run_cli("check-new")
        self.assertEqual(rc, 2, out + err)


@unittest.skipUnless(GIT, "git が無い")
class TestCheckNewFirstCommit(Base):
    def test_I12g_before_first_commit_compares_with_empty_tree(self):
        git(self.root, "init", "-q")
        self.put("issues/open/0001.md", issue_text("最初の issue"))
        git(self.root, "add", "-A")
        rc, out, err = self.run_cli("check-new")
        self.assertEqual(rc, 1, out + err)
        self.assertIn("issues/open/0001.md", out)


class TestConfig(Base):
    def test_I13_relative_paths_are_from_parent_of_dot_claude(self):
        base = self.root / "repo" / "sub"
        cfg = self.write_config([md_source()], base=base)
        f = base / "issues" / "open" / "0001.md"
        f.parent.mkdir(parents=True)
        f.write_text(issue_text("handoff release command"), encoding="utf-8")
        rc, out, err = self.run_cli("related", "--text", "handoff release", cwd=self.root)
        self.assertEqual(rc, 0, err)
        self.assertIn("issues/open/0001.md", out)

    def test_I13b_invalid_config_is_exit_2(self):
        bad = [
            "{broken",
            json.dumps({"sources": "x"}),
            json.dumps({"sources": []}),
            json.dumps({"sources": [{"type": "unknown"}]}),
            json.dumps({"sources": [{"type": "md_dirs", "root": "issues"}]}),
            json.dumps({"sources": [{"type": "json_findings", "path": "a.json"}]}),
        ]
        for text in bad:
            self.cfg.write_text(text, encoding="utf-8")
            rc, out, err = self.run_cli("related", "--text", "x")
            self.assertEqual(rc, 2, text)

    def test_I13c_missing_source_root_warns_and_is_skipped(self):
        self.write_config([md_source(root="nope"), json_source()])
        self.findings([{"id": "CR-01", "finding": "handoff release", "status": "backlog"}])
        rc, out, err = self.run_cli("related", "--text", "handoff release")
        self.assertEqual(rc, 0, err)
        self.assertIn("nope", err)
        self.assertIn("CR-01", out)

    @unittest.skipUnless(GIT, "git が無い")
    def test_I13d_check_new_missing_source_warns_and_keeps_exit(self):
        self.write_config([md_source(root="nope"), json_source()])
        self.findings([{"id": "CR-01", "finding": "x", "status": "backlog"}])
        git(self.root, "init", "-q"); git(self.root, "add", "-A"); git(self.root, "commit", "-qm", "b")
        rc, out, err = self.run_cli("check-new")
        self.assertEqual(rc, 0, out + err)
        self.assertIn("nope", err)


if __name__ == "__main__":
    unittest.main(verbosity=1)
