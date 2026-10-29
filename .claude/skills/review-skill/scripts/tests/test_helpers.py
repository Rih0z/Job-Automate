"""補助コード（helpers.py）の自己試験。被試験物（gate・hook など）が無くても単独で合格する。

Red 工程の証跡の一部: これが合格し、他の試験が「被試験物の不在」だけで失敗していれば、失敗の原因は補助コードの不具合ではない。
"""
import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

import helpers as h
from helpers import RepoTestCase


class FakeRepoBuilders(RepoTestCase):
    def test_make_repo_builds_the_documented_layout_without_any_script_under_test(self):
        repo = self.mk(("alpha", "bravo"))
        for rel in (h.SKILLS_REL + "/alpha/SKILL.md", h.SKILLS_REL + "/bravo/SKILL.md", h.SKILLS_REL + "/review-skill/SKILL.md",
                    h.CRITERIA_REL, h.SOT_REL, h.SCHEMA_REL, h.SETTINGS_REL, h.MD_REL, ".gitignore"):
            self.assertTrue((repo / rel).is_file(), rel)
        sot = json.loads((repo / h.SOT_REL).read_text(encoding="utf-8"))
        self.assertEqual((sot["fetched"], sot["max_age_days"]), (h.SOT_FETCHED, h.SOT_MAX_AGE))
        self.assertEqual([p["id"] for p in sot["principles"]], h.PRINCIPLE_IDS)
        md = (repo / h.MD_REL).read_text(encoding="utf-8")
        self.assertIn(h.MARK_BEGIN, md)
        self.assertIn(h.MARK_END, md)

    def test_make_repo_with_git_creates_a_committed_clean_repo_with_local_identity_only(self):
        repo = self.mk(("alpha",), git=True)
        self.assertEqual(h.git(repo, "status", "--porcelain").out.strip(), "")
        self.assertTrue(h.git(repo, "rev-parse", "HEAD").out.strip())
        self.assertEqual(h.git(repo, "config", "--local", "user.name").out.strip(), "tester")
        self.assertEqual(h.git(repo, "config", "--global", "--get", "user.name", check=False).out.strip(), "")  # global に漏れていない

    def test_criteria_fixture_matches_the_documented_shape(self):
        c = h.make_criteria()
        self.assertEqual([a["id"] for a in c["axes"]], h.AXIS_IDS)
        self.assertEqual(sum(a["weight"] for a in c["axes"]), 100)
        self.assertEqual(c["pass_rule"], {"min_score": 90, "must_pass_all": True})
        for a in c["axes"]:
            self.assertEqual(sum(x["weight"] for x in a["criteria"]), a["weight"])
            for x in a["criteria"]:
                self.assertTrue(x["checks"] and set(x["principles"]) <= set(h.PRINCIPLE_IDS))

    def test_make_result_is_internally_consistent(self):
        for verdict in ("PASS", "FAIL"):
            r = h.make_result(verdict)
            self.assertEqual(sum(a["score"] for a in r["axes"]), r["score"])
            self.assertEqual([a["id"] for a in r["axes"]], h.AXIS_IDS)
        self.assertGreaterEqual(h.make_result("PASS")["score"], 90)
        self.assertLess(h.make_result("FAIL")["score"], 90)


class ReferenceHash(RepoTestCase):
    def test_reference_hash_follows_the_documented_definition(self):
        repo = self.mk(("alpha",))
        d = h.write_skill(repo, "alpha", {"SKILL.md": b"a\r\nb\r\n", "z.bin": b"\0\r\n", "é.md": "e\n", "B.md": "b\n"})
        files = sorted(["SKILL.md", "z.bin", "é.md", "B.md"], key=lambda s: s.encode("utf-8"))
        self.assertEqual(h.ref_files(d), files)
        import hashlib
        m = hashlib.sha256()
        for rel in files:
            raw = (d / rel).read_bytes()
            data = raw.replace(b"\r\n", b"\n") if b"\0" not in raw[:8000] else raw
            m.update(rel.encode("utf-8") + b"\0" + data + b"\0")
        self.assertEqual(h.ref_content_hash(d), m.hexdigest())

    def test_reference_hash_exclusions_and_crlf_normalization(self):
        repo = self.mk(("alpha",))
        d = repo / h.SKILLS_REL / "alpha"
        base = h.ref_content_hash(d)
        (d / "__pycache__").mkdir()
        (d / "__pycache__" / "x.pyc").write_bytes(b"1")
        (d / ".DS_Store").write_bytes(b"1")
        (d / "scripts" / "tests").mkdir(parents=True)
        (d / "scripts" / "tests" / "t.py").write_text("x", encoding="utf-8")
        self.assertEqual(h.ref_content_hash(d), base)
        (d / "SKILL.md").write_bytes((d / "SKILL.md").read_bytes().replace(b"\n", b"\r\n"))
        self.assertEqual(h.ref_content_hash(d), base)
        (d / "SKILL.md").write_bytes((d / "SKILL.md").read_bytes() + b"x")
        self.assertNotEqual(h.ref_content_hash(d), base)

    def test_criteria_sha_normalizes_crlf(self):
        repo = self.mk(("alpha",))
        a = h.criteria_sha(repo)
        p = repo / h.CRITERIA_REL
        p.write_bytes(p.read_bytes().replace(b"\n", b"\r\n"))
        self.assertEqual(h.criteria_sha(repo), a)


class RecordAndLedgerWriters(RepoTestCase):
    def test_write_record_places_a_json_file_with_the_documented_keys(self):
        repo = self.mk(("alpha",))
        p = h.write_record(repo, "alpha", reviewed_at="2026-10-10T01:02:03Z", suffix="abcdef01")
        self.assertEqual(p.name, "20261010T010203Z-abcdef01.json")
        rec = json.loads(p.read_text(encoding="utf-8"))
        for k in h.REQUIRED_TOP:
            self.assertIn(k, rec)
        self.assertEqual(rec["target"]["content_hash"], h.skill_hash(repo, "alpha"))
        self.assertEqual(rec["criteria"]["sha256"], h.criteria_sha(repo))
        self.assertEqual(h.record_files(repo, "alpha"), [p])
        no_kind = json.loads(h.write_record(repo, "alpha", kind=None, reviewed_at="2026-10-11T00:00:00Z").read_text(encoding="utf-8"))
        self.assertNotIn("kind", no_kind["reviewer"])

    def test_pass_records_and_ledger_writers(self):
        repo = self.mk(("alpha", "bravo"))
        h.pass_records(repo, names=["alpha"])
        self.assertEqual(len(h.record_files(repo, "alpha")), 1)
        self.assertEqual(h.record_files(repo, "bravo"), [])
        h.write_ledger(repo, {"bravo": None})
        led = h.read_ledger(repo)
        self.assertEqual(led["skills"]["bravo"]["content_hash"], h.skill_hash(repo, "bravo"))
        self.assertEqual(set(led["skills"]["bravo"]), {"content_hash", "registered", "reason"})


class ProcessHelpers(unittest.TestCase):
    def test_base_env_isolates_user_settings(self):
        with mock.patch.dict(os.environ, {"SKILL_REVIEW_NOW": "1999-01-01T00:00:00Z", "CLAUDE_PROJECT_DIR": "C:/should/not/leak"}):
            env = h.base_env()
        self.assertEqual(env["SKILL_REVIEW_NOW"], h.NOW)
        self.assertNotIn("CLAUDE_PROJECT_DIR", env)
        home = Path(h.fake_home())
        for k in ("HOME", "USERPROFILE", "XDG_CONFIG_HOME"):
            self.assertEqual(Path(env[k]), home)
        self.assertEqual(env["GIT_CONFIG_NOSYSTEM"], "1")

    def test_missing_script_fails_fast_without_starting_a_process(self):
        with self.assertRaises(FileNotFoundError):
            h.run_py(h.SCRIPTS / "no_such_script_for_helpers_selftest.py", [])

    def test_run_proc_returns_output_exit_code_and_elapsed(self):
        r = h.run_proc([sys.executable, "-c", "import sys;print('日本語');sys.stderr.write('e');sys.exit(3)"])
        self.assertEqual((r.code, r.out.strip(), r.err.strip()), (3, "日本語", "e"))
        self.assertGreaterEqual(r.elapsed, 0)

    def test_run_proc_times_out_and_raises_instead_of_hanging(self):
        old = h.SUBPROCESS_TIMEOUT
        h.SUBPROCESS_TIMEOUT = 3
        try:
            with self.assertRaises(AssertionError):
                h.run_proc([sys.executable, "-c", "import time;time.sleep(60)"], timeout=3)
        finally:
            h.SUBPROCESS_TIMEOUT = old

    def test_script_path_prefers_the_overlay_directory_only_when_the_file_exists(self):
        import tempfile
        d = Path(tempfile.mkdtemp(prefix="srg-overlay-"))
        self.addCleanup(h.rmtree_force, d)
        (d / "skill_review_gate.py").write_text("x", encoding="utf-8")
        with mock.patch.dict(os.environ, {"SKILL_REVIEW_SCRIPTS_DIR": str(d)}):
            self.assertEqual(h.script_path("skill_review_gate.py"), d / "skill_review_gate.py")
            self.assertEqual(h.script_path("append_skill_review_record.py"), h.SCRIPTS / "append_skill_review_record.py")

    def test_git_bash_is_available_for_the_hook_tests(self):
        self.assertIsNotNone(h.find_bash(), "Git Bash が無いと hook の試験を実行できない（skip でなく失敗にする）")


class ResultFixtures(unittest.TestCase):
    def test_inconsistent_results_fixture_has_six_distinct_cases(self):
        cases = h.inconsistent_results()
        self.assertEqual(len(cases), 6)
        for res in cases.values():
            self.assertEqual(set(res), {"axes", "score", "verdict", "must_pass_failures", "findings"})


if __name__ == "__main__":
    unittest.main()
