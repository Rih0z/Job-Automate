"""check_compliance_status.py の単体テスト。

一時ディレクトリに最小の cache（anthropic-best-practices.json 相当）/ status（compliance-status.json 相当）/
evidence 用の実在ファイルを作り、スクリプトを subprocess で実行して終了コードと出力を検証する。
C11 だけは本リポジトリの実データで走らせる（受け入れ）。
実行: python .claude/skills/_shared/scripts/test_check_compliance_status.py
"""
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "check_compliance_status.py")
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))

BASE_CACHE = {
    "schema": "anthropic-best-practices/v1",
    "sources": {"best-practices": {"url": "https://example.invalid/bp", "fetched": "2026-09-25"}},
    "principles": [
        {"id": "a.one", "category": "a", "source": "best-practices", "section": "S", "statement": "s",
         "quote": "q", "check": "c", "verified": True, "used_by": ["x"]},
        {"id": "a.two", "category": "a", "source": "best-practices", "section": "S", "statement": "s",
         "quote": "q", "check": "c", "verified": True, "used_by": ["x"]},
        {"id": "a.three", "category": "a", "source": "best-practices", "section": "S", "statement": "s",
         "quote": "q", "check": "c", "verified": True, "used_by": ["x"]},
        {"id": "a.four", "category": "a", "source": "best-practices", "section": "S", "statement": "s",
         "quote": "q", "check": "c", "verified": True, "used_by": ["x"]},
    ],
}
BASE_STATUS = {
    "schema": "compliance-status/v1",
    "principles": {
        "a.one": {"status": "adopted", "evidence": ["ev.md"], "cr": None, "note": ""},
        "a.two": {"status": "backlog", "evidence": [], "cr": "CR-01", "note": ""},
        "a.three": {"status": "not-applicable", "evidence": [], "cr": None, "note": "reason"},
        "a.four": {"status": "partial", "evidence": ["ev.md"], "cr": "CR-01", "note": ""},
    },
    "findings": [
        {"id": "CR-01", "date": "2026-09-25", "finding": "f", "principles": ["a.two"],
         "severity": "Low", "status": "open", "note": ""},
    ],
    "audit_log": [],
}


class CheckComplianceStatusTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        with open(os.path.join(self.root, "ev.md"), "w", encoding="utf-8") as f:
            f.write("x\n")
        self.cache = copy.deepcopy(BASE_CACHE)
        self.status = copy.deepcopy(BASE_STATUS)

    def tearDown(self):
        self.tmp.cleanup()

    def run_check(self, cache=None, status=None, root=None):
        cp = os.path.join(self.root, "cache.json")
        sp = os.path.join(self.root, "status.json")
        with open(cp, "w", encoding="utf-8") as f:
            json.dump(self.cache if cache is None else cache, f)
        with open(sp, "w", encoding="utf-8") as f:
            json.dump(self.status if status is None else status, f)
        env = dict(os.environ, PYTHONUTF8="1")
        return subprocess.run([sys.executable, SCRIPT, "--cache", cp, "--status", sp, "--root", root or self.root],
                              capture_output=True, text=True, encoding="utf-8", env=env)

    def assertViolation(self, r, code, needle):
        """違反コード（V1〜V6）と、違反の対象（id・値・パス）の両方が出力に含まれることを確かめる。"""
        out = r.stdout + r.stderr
        self.assertEqual(r.returncode, 1, out)
        self.assertIn(code, out)
        self.assertIn(needle, out)

    def test_c1_valid_minimal(self):
        r = self.run_check()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_c2_cache_id_missing_in_status(self):
        del self.status["principles"]["a.one"]
        self.assertViolation(self.run_check(), "V1", "a.one")

    def test_c3_status_only_id(self):
        self.status["principles"]["ghost.id"] = {"status": "adopted", "evidence": [], "cr": None, "note": ""}
        self.assertViolation(self.run_check(), "V1", "ghost.id")

    def test_c4_status_enum(self):
        self.status["principles"]["a.one"]["status"] = "maybe"
        self.assertViolation(self.run_check(), "V2", "maybe")

    def test_c5_evidence_missing(self):
        self.status["principles"]["a.one"]["evidence"] = ["nope/missing.md"]
        self.assertViolation(self.run_check(), "V3", "nope/missing.md")

    def test_c6_backlog_without_cr(self):
        self.status["principles"]["a.two"]["cr"] = None
        self.assertViolation(self.run_check(), "V4", "a.two")

    def test_c7_cr_not_in_findings(self):
        self.status["principles"]["a.two"]["cr"] = "CR-99"
        self.assertViolation(self.run_check(), "V4", "CR-99")

    def test_c8_duplicate_finding_id(self):
        self.status["findings"].append(copy.deepcopy(self.status["findings"][0]))
        self.assertViolation(self.run_check(), "V5", "CR-01")

    def test_c9_principle_missing_key(self):
        del self.cache["principles"][0]["quote"]
        self.assertViolation(self.run_check(), "V6", "quote")

    def test_c10_unknown_source(self):
        self.cache["principles"][0]["source"] = "nowhere"
        self.assertViolation(self.run_check(), "V6", "nowhere")

    def test_c10b_finding_enum(self):
        self.status["findings"][0]["severity"] = "Critical!"
        self.assertViolation(self.run_check(), "V5", "Critical!")
        self.status["findings"][0]["severity"] = "Low"
        self.status["findings"][0]["status"] = "whatever"
        self.assertViolation(self.run_check(), "V5", "whatever")

    def test_c10c_partial_without_cr(self):
        self.status["principles"]["a.four"]["cr"] = None
        self.assertViolation(self.run_check(), "V4", "a.four")

    def test_c12_duplicate_principle_id(self):
        self.cache["principles"].append(dict(self.cache["principles"][0]))
        self.assertViolation(self.run_check(), "V6", "a.one")

    def test_c13_absolute_evidence_path(self):
        abs_path = os.path.join(self.root, "ev.md")
        self.status["principles"]["a.one"]["evidence"] = [abs_path]
        self.assertViolation(self.run_check(), "V3", "ev.md")

    def test_c11_real_repository_data(self):
        cache = os.path.join(REPO, ".claude", "skills", "_shared", "anthropic-best-practices.json")
        status = os.path.join(REPO, ".claude", "skills", "_shared", "compliance-status.json")
        env = dict(os.environ, PYTHONUTF8="1")
        r = subprocess.run([sys.executable, SCRIPT, "--cache", cache, "--status", status, "--root", REPO],
                           capture_output=True, text=True, encoding="utf-8", env=env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
