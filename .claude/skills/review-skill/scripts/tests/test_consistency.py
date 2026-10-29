"""check_skill_review_consistency.py（D4 の整合検査 ①〜⑥）の試験: T24・T25・T27 と補足 3 件。標準ライブラリの unittest。

仕様の補完は helpers.py の冒頭コメントに集約。要点: 整合検査 --json は {"ok","checks":[{"id","ok","message"}]}、id は
render（①）・principles（②）・ledger（③）・hook_registration（④）・schema（⑤）・criteria（⑥）。1 項目でも NG なら exit 1。
③ ledger は UNVERIFIABLE（git が無い等）を失敗にしない（偽 repo は git 無しなので ok になる）。
"""
import json
import os
import re
import sys
import unittest
from pathlib import Path

import helpers as h
from helpers import RepoTestCase


class ConsistencyBase(RepoTestCase):
    def check(self, repo=None):
        r = h.run_consistency(repo or self.repo, "--json")
        self.assertIn(r.code, (0, 1), r)
        data = r.json()
        return r.code, {c["id"]: c for c in data["checks"]}

    def failing(self, repo=None):
        code, by = self.check(repo)
        return code, sorted(k for k, v in by.items() if not v["ok"])

    def edit_json(self, rel, fn):
        p = self.repo / rel
        d = json.loads(p.read_text(encoding="utf-8"))
        fn(d)
        h.write_json(p, d)


class Consistency(ConsistencyBase):
    def test_consistent_repo_passes_all_six_checks(self):  # 補足（対照）
        self.mk(("alpha",), consistent=True)
        code, by = self.check()
        self.assertEqual(code, 0, by)
        self.assertEqual(sorted(by), ["criteria", "hook_registration", "ledger", "principles", "render", "schema"])
        self.assertTrue(all(v["ok"] for v in by.values()), by)

    def test_rendered_review_skill_md_matches_json_and_detects_drift(self):  # T24
        repo = self.mk(("alpha",), consistent=True)
        md = repo / h.MD_REL
        self.assertEqual(self.failing(), (0, []))
        # 生成区間を手で変える → exit 1（render が NG）
        text = md.read_text(encoding="utf-8")
        md.write_text(text.replace(h.MARK_END, "手で足した行\n" + h.MARK_END), encoding="utf-8", newline="\n")
        code, bad = self.failing()
        self.assertEqual((code, bad), (1, ["render"]))
        self.assertEqual(h.run_consistency(repo).code, 1)
        # 再生成すると exit 0
        self.assertEqual(h.run_render(repo, "--write").code, 0)
        self.assertEqual(self.failing(), (0, []))
        with self.subTest(case="生成区間の外の編集は検査対象外"):
            t = md.read_text(encoding="utf-8")
            md.write_text(t.replace("前置き", "前置きを書き換えた"), encoding="utf-8", newline="\n")
            self.assertEqual(self.failing(), (0, []))
        with self.subTest(case="criteria JSON を変えて再生成しなければずれを検出"):
            self.edit_json(h.CRITERIA_REL, lambda d: d["axes"][1]["criteria"][0]["checks"].append("追加した確認項目"))
            self.assertEqual(self.failing(), (1, ["render"]))
            self.assertEqual(h.run_render(repo, "--write").code, 0)
            self.assertEqual(self.failing(), (0, []))

    def test_consistency_check_detects_missing_principle_and_unregistered_hook(self):  # T25
        with self.subTest(case="criteria の principles[] に存在しない id"):
            self.mk(("alpha",), consistent=True)
            self.edit_json(h.CRITERIA_REL, lambda d: d["axes"][0]["criteria"][0]["principles"].append("no.such.principle"))
            h.run_render(self.repo, "--write")
            code, bad = self.failing()
            self.assertEqual((code, bad), (1, ["principles"]))
            code, by = self.check()
            self.assertIn("no.such.principle", by["principles"]["message"])
        for n, (label, kw) in enumerate((("Stop の登録が無い", {"stop": False}), ("SessionStart の登録が無い", {"session": False}))):
            with self.subTest(case=label):
                repo = h.make_repo(self.tmp / ("hk-%d" % n), skills=("alpha",), consistent=True)
                h.write_settings(repo, **kw)
                code, bad = self.failing(repo)
                self.assertEqual((code, bad), (1, ["hook_registration"]))

    def test_removing_the_hook_registration_is_detected_only_when_the_consistency_check_is_run_manually(self):  # T27（negative）
        repo = self.mk(("alpha",), consistent=True)
        self.assertEqual(self.failing(), (0, []))  # 登録あり: 整合
        h.write_settings(repo, stop=False, session=False)  # settings.json から本 hook の登録を外す
        settings = json.loads((repo / h.SETTINGS_REL).read_text(encoding="utf-8"))
        commands = [x.get("command", "") for ev in settings["hooks"].values() for blk in ev for x in blk.get("hooks", [])]
        # 注意: 次の assert は被試験物を通らない（試験が書いた偽の settings.json の内容の確認）。「登録を外した状態を正しく再現できた」前提の確認に
        # 限る。hook が自動で起動しないことの根拠は、Claude Code の hook 機構（登録が無ければ起動しない）であり、本試験では検証しない（残余リスクとして D7 B に記載）。
        self.assertFalse(any("hook-skill-review-gate.sh" in c for c in commands), commands)
        # 手動で整合検査④を実行すると exit 1
        r = h.run_consistency(repo)
        self.assertEqual(r.code, 1, r)
        code, bad = self.failing()
        self.assertEqual((code, bad), (1, ["hook_registration"]))
        # 実際に走らせたコマンドと、その実際の終了コード・失敗項目を記録する。既定の保存先は一時ディレクトリ（試験が実 repo を書き換えない）。
        # 証跡を取るときだけ、環境変数 SKILL_REVIEW_T27_LOG で実 repo の .tmp/close-verify/skill-review-gate/t27.log を指す。
        # 記録するだけで、記録した文字列を assert はしない。
        log = Path(os.environ.get("SKILL_REVIEW_T27_LOG") or (self.tmp / "t27.log"))
        log.parent.mkdir(parents=True, exist_ok=True)
        with open(log, "w", encoding="utf-8", newline="\n") as f:
            f.write("T27 negative: settings.json から hook 登録を外した偽 repo で、整合検査を手動実行した結果\n")
            f.write("command: %s %s --repo-root <偽 repo> --json\n" % (sys.executable, h.CONSISTENCY))
            f.write("actual exit code: %d\nactual failing checks: %s\n" % (r.code, bad))
            f.write("settings.json に残った command: %s\n" % commands)

    def test_ledger_check_fails_on_tampering_and_stays_ok_when_unverifiable(self):  # 補足（D4 ③ の NG 側）
        repo = self.mk(("alpha", "bravo"), git=True, consistent=True)
        h.write_ledger(repo, {"alpha": None})
        h.git_commit_paths(repo, [h.LEDGER_REL], "ledger anchor")
        self.assertEqual(self.failing(), (0, []))  # 基準どおり
        led = h.read_ledger(repo)
        led["skills"]["bravo"] = {"content_hash": h.skill_hash(repo, "bravo"), "registered": "2026-10-28", "reason": "後から足した"}
        h.write_json(repo / h.LEDGER_REL, led)
        code, bad = self.failing()
        self.assertEqual((code, bad), (1, ["ledger"]))  # エントリの追加を検出して整合検査が失敗する
        self.assertEqual(h.run_consistency(repo).code, 1)
        with self.subTest(case="UNVERIFIABLE（台帳が未 commit）は ok のまま"):
            repo2 = h.make_repo(self.tmp / "unver", skills=("alpha",), git=True, consistent=True)
            h.write_ledger(repo2, {"alpha": None})
            self.assertEqual(h.run_gate(repo2, "--verify-ledger").code, 2)  # 前提
            self.assertEqual(self.failing(repo2), (0, []))

    def test_schema_required_keys_must_match_the_save_script_checks(self):  # 補足（D4 ⑤）
        self.mk(("alpha",), consistent=True)
        self.assertEqual(self.failing(), (0, []))
        self.edit_json(h.SCHEMA_REL, lambda d: d["required"].remove("reviewer"))  # スキーマだけ緩める → 保存 script の検査とずれる
        self.assertEqual(self.failing(), (1, ["schema"]))

    def test_nested_schema_required_keys_must_match_the_save_script_checks(self):  # 補足（D4 ⑤ の入れ子）
        import shutil
        self.mk(("alpha",), consistent=True)
        shutil.copyfile(str(h.REAL_REPO / h.SCHEMA_REL), str(self.repo / h.SCHEMA_REL))  # 実物のスキーマ（properties を持つ）
        self.assertEqual(self.failing(), (0, []))
        for path in (("reviewer",), ("result",), ("result", "findings")):
            def loosen(d, path=path):
                node = d["properties"]
                for step in path[:-1]:
                    node = node[step]["properties"]
                last = path[-1]
                if last == "findings":
                    node[last]["items"]["required"].remove("severity")
                else:
                    node[last]["required"].remove("kind" if last == "reviewer" else "verdict")
            with self.subTest(path=".".join(path)):
                self.mk(("alpha",), consistent=True)
                shutil.copyfile(str(h.REAL_REPO / h.SCHEMA_REL), str(self.repo / h.SCHEMA_REL))
                self.edit_json(h.SCHEMA_REL, loosen)
                self.assertEqual(self.failing(), (1, ["schema"]))

    def test_criteria_json_validity_is_checked(self):  # 補足（D4 ⑥）
        self.mk(("alpha",), consistent=True)
        p = self.repo / h.CRITERIA_REL
        good = p.read_text(encoding="utf-8")
        cases = {
            "weight 合計が 100 でない": lambda d: d["axes"][0].__setitem__("weight", 25),
            "pass_rule が無い": lambda d: d.pop("pass_rule"),
            "axes が 5 つでない": lambda d: d.__setitem__("axes", d["axes"][:4]),
            "criterion に checks が無い": lambda d: d["axes"][0]["criteria"][0].pop("checks"),
        }
        for name, fn in cases.items():
            with self.subTest(case=name):
                p.write_text(good, encoding="utf-8", newline="\n")
                self.edit_json(h.CRITERIA_REL, fn)
                code, bad = self.failing()
                self.assertEqual(code, 1)
                self.assertIn("criteria", bad)
        with self.subTest(case="JSON の構文エラーでも落ちずに criteria の NG として報告する"):
            p.write_text("{ broken", encoding="utf-8", newline="\n")
            r = h.run_consistency(self.repo, "--json")
            self.assertEqual(r.code, 1, r)
            self.assertNotIn("Traceback", r.err)
            by = {c["id"]: c for c in r.json()["checks"]}
            self.assertFalse(by["criteria"]["ok"])


if __name__ == "__main__":
    unittest.main()
