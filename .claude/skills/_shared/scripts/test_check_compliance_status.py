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

    def test_c14_requests_and_related_valid(self):
        self.status["findings"][0]["requests"] = [{"at": "2026-11-11T12:00:00-08:00", "text": "利用者の要望"}]
        self.status["findings"][0]["related"] = ["CR-02"]
        r = self.run_check()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.status["findings"][0]["related"] = []
        r = self.run_check()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.status["findings"][0]["related"] = "CR-02"
        self.assertViolation(self.run_check(), "V7", "CR-01")  # 対の確認: 形が違えば違反

    def test_c15_requests_malformed(self):
        for bad in ("text", [{"at": "2026-11-11"}], [{"text": "x"}], [{"at": 1, "text": "x"}], ["x"]):
            self.status["findings"][0]["requests"] = bad
            self.assertViolation(self.run_check(), "V7", "CR-01")

    def test_c16_related_malformed(self):
        for bad in ("CR-02", [1], [{"id": "CR-02"}]):
            self.status["findings"][0]["related"] = bad
            self.assertViolation(self.run_check(), "V7", "CR-01")

    # ---------- V8（棚卸しの欄。計画 2026-11-12-issue-triage.md r3 の C17〜C23b） ----------

    def add_cr02(self, **kw):
        f = {"id": "CR-02", "date": "2026-09-25", "finding": "g", "principles": [],
             "severity": "Low", "status": "obsolete", "note": "", "resolution": "前提が変わった"}
        f.update(kw)
        self.status["findings"].append(f)
        return f

    def assertNoViolation(self, r):
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_c17_priority_enum(self):
        self.status["findings"][0]["priority"] = "P1"
        self.assertNoViolation(self.run_check())
        self.status["findings"][0]["priority"] = "P9"
        self.assertViolation(self.run_check(), "V8", "CR-01")

    def test_c18_reviewed_format(self):
        self.status["findings"][0]["reviewed"] = "2026-11-12"
        self.assertNoViolation(self.run_check())
        for bad in ("2026/11/12", "2026-13-01"):
            self.status["findings"][0]["reviewed"] = bad
            self.assertViolation(self.run_check(), "V8", "CR-01")

    def test_c19_premise_shape(self):
        for good in ([{"path": "ev.md"}], [{"path": "~/x.md", "contains": "a"}]):
            self.status["findings"][0]["premise"] = good
            self.assertNoViolation(self.run_check())
        abs_path = os.path.join(self.root, "ev.md")
        for bad in ("ev.md", [{"contains": "a"}], [{"path": ""}], [{"path": "ev.md", "contains": 1}],
                    [{"path": abs_path}], [{"path": "../x.md"}], ["ev.md"]):
            self.status["findings"][0]["premise"] = bad
            self.assertViolation(self.run_check(), "V8", "CR-01")

    def test_c20_obsolete_requires_resolution(self):
        f = self.add_cr02()
        self.assertNoViolation(self.run_check())
        del f["resolution"]
        self.assertViolation(self.run_check(), "V8", "CR-02")
        f["resolution"] = ""
        self.assertViolation(self.run_check(), "V8", "CR-02")

    def test_c21_superseded_by(self):
        f = self.add_cr02(superseded_by="CR-01")
        self.assertNoViolation(self.run_check())
        for bad in ("CR-99", "CR-02"):
            f["superseded_by"] = bad
            self.assertViolation(self.run_check(), "V8", "CR-02")
        f["superseded_by"] = "CR-01"
        self.status["findings"][0]["superseded_by"] = "CR-02"  # CR-01 は open（obsolete でない）
        self.assertViolation(self.run_check(), "V8", "CR-01")

    def test_c22_principle_cr_pointing_to_obsolete(self):
        self.status["findings"][0]["status"] = "obsolete"
        self.status["findings"][0]["resolution"] = "r"
        self.assertViolation(self.run_check(), "V8", "a.two")  # backlog の principle
        self.status["findings"][0]["status"] = "open"
        self.add_cr02()
        self.status["principles"]["a.one"]["cr"] = "CR-02"
        self.assertViolation(self.run_check(), "V8", "a.one")  # adopted の principle

    def test_c23_enums_match_constants(self):
        self.status["enums"] = {"finding_status": ["open", "backlog", "done", "false-positive", "obsolete"],
                                "finding_priority": ["P1", "P2", "P3"]}
        self.assertNoViolation(self.run_check())
        self.status["enums"]["finding_status"] = ["open", "backlog", "done", "false-positive"]
        self.assertViolation(self.run_check(), "V8", "finding_status")
        self.status["enums"]["finding_status"] = ["open", "backlog", "done", "false-positive", "obsolete"]
        self.status["enums"]["finding_priority"] = ["P1", "P2"]
        self.assertViolation(self.run_check(), "V8", "finding_priority")

    def test_c23b_missing_enums_is_not_compared(self):
        self.status.pop("enums", None)
        self.assertNoViolation(self.run_check())
        self.status["enums"] = {"finding_status": ["open", "backlog", "done", "false-positive", "obsolete"]}
        self.assertNoViolation(self.run_check())

    def test_c11_real_repository_data(self):
        cache = os.path.join(REPO, ".claude", "skills", "_shared", "anthropic-best-practices.json")
        status = os.path.join(REPO, ".claude", "skills", "_shared", "compliance-status.json")
        env = dict(os.environ, PYTHONUTF8="1")
        r = subprocess.run([sys.executable, SCRIPT, "--cache", cache, "--status", status, "--root", REPO],
                           capture_output=True, text=True, encoding="utf-8", env=env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
