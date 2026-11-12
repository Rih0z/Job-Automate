"""knowhow_check.py の試験（unittest、標準ライブラリだけ）。

実行: python .claude/skills/agent-harness-bootstrap/scripts/test_knowhow_check.py
各試験は一時ディレクトリに .claude/knowhow.json と反映先の file を作り、script を subprocess で呼ぶ。
対応: 計画 2026-11-11-issue-handoff-knowhow-redesign.md r3 の K1〜K11（r3 の K8 追加を含む）。
"""
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "knowhow_check.py"
SCHEMA = Path(__file__).resolve().parent / "knowhow.schema.json"
GIT = shutil.which("git")


def entry(i="KH-0001", status="reflected", reflect_to=None, **over):
    e = {"id": i, "added": "2026-11-11", "source": "user", "statement": "決まりを 1 文で",
         "why": "理由を 1 文で", "reflect_to": reflect_to if reflect_to is not None else [{"path": "CLAUDE.md"}],
         "status": status, "retired_reason": None}
    e.update(over)
    return e


def git(cwd, *args):
    p = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
                       cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    if p.returncode != 0:
        raise AssertionError(f"git {args}: {p.stderr}")
    return p.stdout


class Base(unittest.TestCase):
    def setUp(self):
        self.top = Path(tempfile.mkdtemp())
        self.root = self.top / "repo"
        (self.root / ".claude").mkdir(parents=True)
        self.cfg = self.root / ".claude" / "knowhow.json"
        self.env = dict(os.environ, PYTHONUTF8="1", GIT_CEILING_DIRECTORIES=str(self.top))
        self.put("CLAUDE.md", "# CLAUDE.md\n\n決まりの本文 <!-- KH-0001 -->\n")

    def tearDown(self):
        shutil.rmtree(self.top, ignore_errors=True)

    def put(self, rel, text):
        f = self.root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8")
        return f

    def ledger(self, entries, raw=None):
        if raw is not None:
            self.cfg.write_text(raw, encoding="utf-8")
        else:
            self.cfg.write_text(json.dumps({"schema": "knowhow/v1", "entries": entries}, ensure_ascii=False, indent=2),
                                encoding="utf-8")

    def run_cli(self, *args):
        p = subprocess.run([sys.executable, str(SCRIPT), "--config", str(self.cfg), *args], cwd=self.root,
                           capture_output=True, text=True, encoding="utf-8", env=self.env)
        return p.returncode, p.stdout, p.stderr


class TestKnowhow(Base):
    def test_K1_all_reflected_is_exit_0(self):
        self.put(".claude/x.json", json.dumps({"knowhow": ["KH-0001"], "other": 1}))
        self.ledger([entry(reflect_to=[{"path": "CLAUDE.md"}, {"path": ".claude/x.json"}])])
        rc, out, err = self.run_cli()
        self.assertEqual(rc, 0, out + err)

    def test_K2_queued_is_exit_1(self):
        self.ledger([entry(status="queued")])
        rc, out, err = self.run_cli()
        self.assertEqual(rc, 1, out + err)
        self.assertIn("KH-0001", out)
        self.assertIn("queued", out)

    def test_K3_missing_anchor_is_exit_1(self):
        self.put("CLAUDE.md", "# CLAUDE.md\n\nアンカーなし\n")
        self.ledger([entry()])
        rc, out, err = self.run_cli()
        self.assertEqual(rc, 1, out + err)
        self.assertIn("CLAUDE.md", out)
        self.put(".claude/x.json", json.dumps({"other": ["KH-0001"]}))
        self.put("CLAUDE.md", "# CLAUDE.md\n\n<!-- KH-0001 -->\n")
        self.ledger([entry(reflect_to=[{"path": "CLAUDE.md"}, {"path": ".claude/x.json"}])])
        rc, out, err = self.run_cli()
        self.assertEqual(rc, 1, "json は knowhow 配列の値だけをアンカーに数える")

    def test_K4_must_contain(self):
        self.ledger([entry(reflect_to=[{"path": "CLAUDE.md", "must_contain": "必須の語句"}])])
        rc, out, err = self.run_cli()
        self.assertEqual(rc, 1, out + err)
        self.assertIn("必須の語句", out)
        self.put("CLAUDE.md", "# CLAUDE.md\n\n必須の語句 <!-- KH-0001 -->\n")
        rc, out, err = self.run_cli()
        self.assertEqual(rc, 0, out + err)

    def test_K5_missing_file_is_exit_1(self):
        self.ledger([entry(reflect_to=[{"path": "CLAUDE.md"}, {"path": "docs/nope.md"}])])
        rc, out, err = self.run_cli()
        self.assertEqual(rc, 1, out + err)
        self.assertIn("docs/nope.md", out)

    def test_K6_reflected_with_empty_reflect_to_is_exit_1(self):
        self.ledger([entry(reflect_to=[])])
        rc, out, err = self.run_cli()
        self.assertEqual(rc, 1, out + err)

    def test_K7_reflect_to_outside_repo_is_exit_1(self):
        (self.top / "outside.md").write_text("<!-- KH-0001 -->\n", encoding="utf-8")
        for p in ("../outside.md", str(self.top / "outside.md")):
            self.ledger([entry(reflect_to=[{"path": "CLAUDE.md"}, {"path": p}])])
            rc, out, err = self.run_cli()
            self.assertEqual(rc, 1, p)

    def test_K8_orphan_anchor_is_exit_1(self):
        self.put("CLAUDE.md", "# CLAUDE.md\n\n<!-- KH-0001 -->\n古い決まり <!-- KH-0009 -->\n")
        self.ledger([entry()])
        rc, out, err = self.run_cli()
        self.assertEqual(rc, 1, out + err)
        self.assertIn("KH-0009", out)

    def test_K8b_bare_ids_and_examples_are_not_anchors(self):
        self.put("CLAUDE.md", "# CLAUDE.md\n\nKH-0001 を本文で触れるだけ\n")
        self.ledger([entry()])
        rc, out, err = self.run_cli()
        self.assertEqual(rc, 1, "裸の ID はアンカーに数えない")
        self.put("CLAUDE.md", "# CLAUDE.md\n\n<!-- KH-0001 -->\n本文中の KH-0002 と書式の例 KH-xxxx と <!-- KH-xxxx -->\n")
        rc, out, err = self.run_cli()
        self.assertEqual(rc, 0, out + err)

    def test_K8c_anchor_in_file_not_listed_for_that_id_is_exit_1(self):
        self.put("docs/a.md", "<!-- KH-0002 -->\n")
        self.put("CLAUDE.md", "# CLAUDE.md\n\n<!-- KH-0001 --> <!-- KH-0002 -->\n")
        self.ledger([entry(), entry("KH-0002", reflect_to=[{"path": "docs/a.md"}])])
        rc, out, err = self.run_cli()
        self.assertEqual(rc, 1, out + err)
        self.assertIn("KH-0002", out)

    def test_K8d_retired_anchor_in_unlisted_file_is_allowed(self):
        self.put("CLAUDE.md", "# CLAUDE.md\n\n<!-- KH-0001 --> 廃止した決まりの名残 <!-- KH-0002 -->\n")
        self.ledger([entry(), entry("KH-0002", status="retired", reflect_to=[{"path": "docs/old.md"}],
                                    retired_reason="置き換えた")])
        rc, out, err = self.run_cli()
        self.assertEqual(rc, 0, out + err)
        self.put("docs/old.md", "<!-- KH-0002 -->\n")
        self.ledger([entry(), entry("KH-0002", reflect_to=[{"path": "docs/old.md"}])])
        rc, out, err = self.run_cli()
        self.assertEqual(rc, 1, "retired でなければ、reflect_to に無い CLAUDE.md のアンカーで失敗する（対の確認）")
        self.assertIn("reflect_to に無い", out)

    def test_K9_retired_is_not_checked(self):
        self.ledger([entry(), entry("KH-0002", status="retired", reflect_to=[{"path": "gone.md"}],
                                    retired_reason="別の決まりに置き換えた")])
        rc, out, err = self.run_cli()
        self.assertEqual(rc, 0, out + err)

    def test_K10_schema_violation_is_exit_2(self):
        base = entry()
        bad_entries = []
        e = copy.deepcopy(base); e["id"] = "KH-1"; bad_entries.append([e])
        e = copy.deepcopy(base); del e["statement"]; bad_entries.append([e])
        e = copy.deepcopy(base); e["status"] = "done"; bad_entries.append([e])
        e = copy.deepcopy(base); e["source"] = "guess"; bad_entries.append([e])
        e = copy.deepcopy(base); e["added"] = "11/11/2026"; bad_entries.append([e])
        e = copy.deepcopy(base); e["reflect_to"] = [{"must_contain": "x"}]; bad_entries.append([e])
        e = copy.deepcopy(base); e["status"] = "retired"; bad_entries.append([e])
        e = copy.deepcopy(base); del e["retired_reason"]; bad_entries.append([e])
        bad_entries.append([copy.deepcopy(base), copy.deepcopy(base)])
        for ents in bad_entries:
            self.ledger(ents)
            rc, out, err = self.run_cli()
            self.assertEqual(rc, 2, json.dumps(ents, ensure_ascii=False))
        for raw in ("{broken", json.dumps({"schema": "knowhow/v1"}), json.dumps({"schema": "x", "entries": []})):
            self.ledger(None, raw=raw)
            rc, out, err = self.run_cli()
            self.assertEqual(rc, 2, raw)

    def test_K10b_schema_file_lists_same_enums(self):
        s = json.loads(SCHEMA.read_text(encoding="utf-8"))
        props = s["$defs"]["entry"]["properties"]
        self.assertEqual(sorted(props["status"]["enum"]), ["queued", "reflected", "retired"])
        self.assertEqual(sorted(props["source"]["enum"]), ["incident", "review", "user"])

    @unittest.skipUnless(GIT, "git が無い")
    def test_K11_new_since_counts_only_new_queued(self):
        self.put("CLAUDE.md", "# CLAUDE.md\n\n<!-- KH-0001 --> <!-- KH-0002 -->\n")
        self.ledger([entry(status="queued")])
        git(self.root, "init", "-q"); git(self.root, "add", "-A"); git(self.root, "commit", "-qm", "base")
        rc, out, err = self.run_cli("--new-since", "HEAD")
        self.assertEqual(rc, 0, out + err)
        self.assertIn("前からある queued", out)
        self.assertIn("KH-0001", out)
        self.ledger([entry(status="queued"), entry("KH-0002", status="queued")])
        rc, out, err = self.run_cli("--new-since", "HEAD")
        self.assertEqual(rc, 1, out + err)
        new_lines = [l for l in out.splitlines() if "増えた queued" in l]
        self.assertTrue(new_lines and "KH-0002" in new_lines[0] and "KH-0001" not in new_lines[0], out)


class TestRealRepository(unittest.TestCase):
    def test_K12_real_repository_ledger_passes(self):
        """受け入れ: このリポジトリの .claude/knowhow.json が全件反映済みで検査を通る。"""
        repo = Path(__file__).resolve().parents[4]
        p = subprocess.run([sys.executable, str(SCRIPT), "--config", str(repo / ".claude" / "knowhow.json")],
                           cwd=repo, capture_output=True, text=True, encoding="utf-8",
                           env=dict(os.environ, PYTHONUTF8="1"))
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=1)
