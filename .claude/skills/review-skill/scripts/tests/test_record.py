"""append_skill_review_record.py（D2）と記録の検査の試験: T7〜T10・T17・T31 と補足 1 件。標準ライブラリの unittest。

仕様の補完は helpers.py の冒頭コメントに集約（CLI 引数・終了コード・SAVED / ALREADY_RECORDED の出力・記録 JSON の形）。
決めた点の要約: 保存 script は --repo-root / --skill / --expected-hash（必須）/ --result-file / --agent-id / --subagent-type /
--model / --reviewer-kind（既定 subagent）を取り、--reviewed-at と --content-hash は持たない。拒否は exit 1 で記録ファイルを作らない。
"""
import json
import re
import unittest

import helpers as h
from helpers import RepoTestCase

NOW_SAVE = "2026-10-27T12:34:56Z"


class SaveBase(RepoTestCase):
    def setUp(self):
        super().setUp()
        self.mk(("alpha",))
        self.env = h.base_env(SKILL_REVIEW_NOW=NOW_SAVE)

    def save(self, result=None, expected=None, **kw):
        rf = self.result_file(result if result is not None else h.make_result("PASS"))
        exp = expected if expected is not None else h.skill_hash(self.repo, "alpha")
        return h.run_append(self.repo, "alpha", exp, rf, env=kw.pop("env", self.env), **kw)

    def files(self, skill="alpha"):
        return h.record_files(self.repo, skill)


class RecordSaving(SaveBase):
    def test_record_without_subagent_kind_is_rejected_on_save_and_invalid_in_gate(self):  # T7
        # 偽の kind を書いた記録は検出できない（D7 B）。この試験は kind の「欠落・不正」だけを扱う。
        for kind in ("human", "", "main"):
            with self.subTest(save_kind=kind):
                r = self.save(extra=["--reviewer-kind", kind])
                self.assertEqual(r.code, 1, r)
                self.assertEqual(self.files(), [])
        h.pass_records(self.repo, names=["review-skill"])
        h.write_record(self.repo, "alpha", kind=None)  # 手で置いた記録（kind 欠落）
        self.assertSkillState(self.repo, "alpha", "INVALID")
        self.assertEqual(h.run_gate(self.repo, "--strict").code, 1)
        h.write_record(self.repo, "alpha", kind="human", reviewed_at="2026-10-21T00:00:00Z")  # kind 不正
        self.assertSkillState(self.repo, "alpha", "INVALID")

    def test_save_rejects_when_hash_changed_during_review(self):  # T8
        before = h.skill_hash(self.repo, "alpha")
        with self.subTest(case="expected-hash が違う"):
            r = self.save(expected="0" * 64)
            self.assertEqual(r.code, 1, r)
            self.assertTrue(r.err.strip())
            self.assertEqual(self.files(), [])
        with self.subTest(case="レビュー開始後に編集された"):
            p = self.repo / h.SKILLS_REL / "alpha" / "SKILL.md"
            p.write_bytes(p.read_bytes() + "レビュー中の編集\n".encode("utf-8"))
            r = self.save(expected=before)
            self.assertEqual(r.code, 1, r)
            self.assertEqual(self.files(), [])
        with self.subTest(case="一致すれば保存される（対照）"):
            r = self.save(expected=h.skill_hash(self.repo, "alpha"))
            self.assertEqual(r.code, 0, r)
            self.assertEqual(len(self.files()), 1)

    def test_saved_hash_and_reviewed_at_are_computed_by_the_script(self):  # T9
        r = self.save(extra=[])
        self.assertEqual(r.code, 0, r)
        self.assertTrue(r.out.splitlines()[0].startswith("SAVED "), r)
        files = self.files()
        self.assertEqual(len(files), 1)
        self.assertRegex(files[0].name, r"^20261027T123456Z-[0-9a-f]{8}\.json$")  # UTC 日時 + 同一性キーの sha256 先頭 8 桁
        rec = json.loads(files[0].read_text(encoding="utf-8"))
        self.assertEqual(rec["schema"], "skill-review-record/v1")
        self.assertEqual(rec["skill"], "alpha")
        self.assertEqual(rec["reviewed_at"], NOW_SAVE)  # script が付けた現在の UTC
        self.assertEqual(rec["target"]["content_hash"], h.skill_hash(self.repo, "alpha"))  # script が実ファイルから計算
        self.assertEqual([f["path"] for f in rec["target"]["files"]], h.ref_files(self.repo / h.SKILLS_REL / "alpha"))
        d = self.repo / h.SKILLS_REL / "alpha"
        for f in rec["target"]["files"]:  # 各ファイルの sha256 = 実ファイルの（CRLF を LF に正規化した後の）sha256
            self.assertEqual(f["sha256"], h.sha256_hex(h.normalize_bytes((d / f["path"]).read_bytes())), f["path"])
        self.assertEqual(rec["criteria"]["sha256"], h.criteria_sha(self.repo))
        self.assertEqual(rec["best_practices_snapshot"], {"fetched": h.SOT_FETCHED, "max_age_days": h.SOT_MAX_AGE})
        self.assertEqual(rec["reviewer"], {"kind": "subagent", "subagent_type": "readonly-reviewer", "agent_id": "agent-1", "model": "test-model"})
        self.assertEqual(rec["result"], h.make_result("PASS"))  # result はそのまま
        for k in h.REQUIRED_TOP:
            self.assertIn(k, rec)
        # 呼び出し元は reviewed_at・content_hash を渡せない
        for flag, val in (("--reviewed-at", "2099-01-01T00:00:00Z"), ("--content-hash", "a" * 64)):
            with self.subTest(flag=flag):
                self.assertEqual(self.save(extra=[flag, val], env=h.base_env(SKILL_REVIEW_NOW="2026-10-28T00:00:00Z")).code, 2)
                self.assertEqual(len(self.files()), 1)
        # 保存した記録を gate が適用する（往復）
        h.pass_records(self.repo, names=["review-skill"])
        self.assertSkillState(self.repo, "alpha", "PASS", env=self.env)

    def test_inconsistent_result_is_rejected_on_save(self):  # T10
        # 各ケースは「その 1 点だけ」が拒否の原因になるように、他の条件を整合させてある（helpers.inconsistent_results。gate の INVALID 判定の試験と共通）
        for name, res in h.inconsistent_results().items():
            with self.subTest(case=name):
                r = self.save(result=res)
                self.assertEqual(r.code, 1, r)
                self.assertTrue(r.err.strip())
                self.assertEqual(self.files(), [])
        with self.subTest(case="整合した PASS は保存できる（対照）"):
            self.assertEqual(self.save(result=h.make_result("PASS")).code, 0)
        with self.subTest(case="整合した FAIL も保存できる"):
            self.assertEqual(self.save(result=h.make_result("FAIL"), agent_id="agent-2").code, 0)

    def test_duplicate_save_is_idempotent_by_identity_key(self):  # T17
        r1 = self.save()
        self.assertEqual(r1.code, 0, r1)
        self.assertTrue(r1.out.startswith("SAVED "))
        later = h.base_env(SKILL_REVIEW_NOW="2026-10-27T13:00:00Z")  # 時刻が違っても同一性キーは同じ
        r2 = self.save(env=later)
        self.assertEqual(r2.code, 0, r2)
        self.assertTrue(r2.out.startswith("ALREADY_RECORDED "), r2)
        self.assertEqual(len(self.files()), 1)
        r3 = self.save(agent_id="agent-2", env=later)  # agent_id が違えば別記録
        self.assertEqual(r3.code, 0, r3)
        self.assertTrue(r3.out.startswith("SAVED "))
        self.assertEqual(len(self.files()), 2)
        r4 = self.save(result=h.make_result("PASS", score=90, axes=[{"id": a, "score": 18} for a in h.AXIS_IDS]), env=later)  # result が違えば別記録
        self.assertEqual(r4.code, 0, r4)
        self.assertEqual(len(self.files()), 3)
        with self.subTest(case="skill の内容 hash が変われば別記録"):
            p = self.repo / h.SKILLS_REL / "alpha" / "SKILL.md"
            p.write_bytes(p.read_bytes() + b"edit\n")
            r = self.save(env=later)
            self.assertTrue(r.out.startswith("SAVED "), r)
            self.assertEqual(len(self.files()), 4)
        with self.subTest(case="criteria の sha256 が変われば別記録"):
            crit = self.repo / h.CRITERIA_REL
            crit.write_text(crit.read_text(encoding="utf-8").replace("基準1", "基準1改"), encoding="utf-8", newline="\n")
            r = self.save(env=later)
            self.assertTrue(r.out.startswith("SAVED "), r)
            self.assertEqual(len(self.files()), 5)
        with self.subTest(case="同一性キーは既存ファイルの中身で探す（ファイル名が違っても記録済み）"):
            newest = max(self.files(), key=lambda f: f.stat().st_mtime_ns)
            renamed = newest.with_name("renamed-by-hand.json")
            newest.rename(renamed)
            r = self.save(env=later)
            self.assertEqual(r.code, 0, r)
            self.assertTrue(r.out.startswith("ALREADY_RECORDED "), r)
            self.assertEqual(len(self.files()), 5)

    def test_save_without_expected_hash_is_rejected(self):  # T31
        rf = self.result_file(h.make_result("PASS"))
        r = h.run_append(self.repo, "alpha", "unused", rf, env=self.env, omit=("expected-hash",))
        self.assertNotEqual(r.code, 0, r)
        self.assertIn("expected-hash", r.err)  # 欠落した引数名を示す（script 不在の失敗と区別する）
        self.assertEqual(self.files(), [])

    def test_unavailable_agent_id_is_accepted_and_warned_in_all(self):  # 補足（D2: 取得できなければ unavailable を許し --all に WARN）
        r = self.save(agent_id="unavailable")
        self.assertEqual(r.code, 0, r)
        h.pass_records(self.repo, names=["review-skill"])
        self.assertSkillState(self.repo, "alpha", "PASS", env=self.env)
        allr = h.run_gate(self.repo, "--all", env=self.env)
        self.assertEqual(allr.code, 0)
        self.assertIn("unavailable", allr.out)
        self.assertIn("agent_id_unavailable", h.gate_json(self.repo, self.env)["skills"]["alpha"]["notes"])


if __name__ == "__main__":
    unittest.main()
