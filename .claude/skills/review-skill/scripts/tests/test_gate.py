"""skill_review_gate.py（D3）の試験: T1〜T6・T11〜T16・T18・T26。標準ライブラリの unittest。

仕様の補完は helpers.py の冒頭コメントに集約している（出力の形・終了コード・環境変数・記録 JSON の形）。
本ファイルの試験は、被試験物が存在しない間は FileNotFoundError 相当（python が script を開けず exit 2）で落ちる = Red。
"""
import os
import re
import shutil
import unittest
from pathlib import Path

import helpers as h
from helpers import RepoTestCase


def alpha_files():
    return {"SKILL.md": "---\nname: alpha\ndescription: 試験\n---\n本文\n",
            "criteria/c.json": "{}\n", "scripts/run.py": "print(1)\n", "references/r.md": "参照\n",
            "scripts/tests/t.py": "pass\n"}


class GateStates(RepoTestCase):
    def fresh(self, name, skills=("alpha",), git=False):
        return h.make_repo(self.tmp / name, skills=skills, git=git)

    def test_pass_when_the_latest_applicable_record_passes(self):  # T1
        repo = self.mk(("alpha",))
        h.pass_records(repo)
        self.assertEqual(h.states(repo), {"alpha": "PASS", "review-skill": "PASS"})
        self.assertEqual(h.run_gate(repo, "--strict").code, 0)

    def test_stale_after_any_file_in_the_skill_dir_changes(self):  # T2
        for i, rel in enumerate(["SKILL.md", "criteria/c.json", "scripts/run.py", "references/r.md"]):
            with self.subTest(file=rel):
                repo = h.make_repo(self.tmp / ("r%d" % i), skills=("alpha",))
                h.write_skill(repo, "alpha", alpha_files())
                h.pass_records(repo)
                self.assertSkillState(repo, "alpha", "PASS")
                p = repo / h.SKILLS_REL / "alpha" / rel
                p.write_bytes(p.read_bytes() + b"x")
                self.assertSkillState(repo, "alpha", "STALE")
                self.assertEqual(h.run_gate(repo, "--strict").code, 1)
        with self.subTest(file="scripts/tests/t.py（影響しない）"):
            repo = h.make_repo(self.tmp / "rt", skills=("alpha",))
            h.write_skill(repo, "alpha", alpha_files())
            h.pass_records(repo)
            p = repo / h.SKILLS_REL / "alpha" / "scripts/tests/t.py"
            p.write_bytes(p.read_bytes() + b"x")
            self.assertSkillState(repo, "alpha", "PASS")
            self.assertEqual(h.run_gate(repo, "--strict").code, 0)

    def test_committed_but_unreviewed_change_is_still_detected(self):  # T3
        repo = self.mk(("alpha",), git=True)
        h.pass_records(repo)
        h.git_commit_all(repo, "reviewed")
        self.assertEqual(h.run_gate(repo, "--strict").code, 0)
        (repo / h.SKILLS_REL / "alpha" / "SKILL.md").write_text("---\nname: alpha\n---\n変更\n", encoding="utf-8", newline="\n")
        h.git_commit_all(repo, "change without review")
        self.assertEqual(h.git(repo, "status", "--porcelain").out.strip(), "")  # 作業ツリーは clean
        self.assertSkillState(repo, "alpha", "STALE")
        self.assertEqual(h.run_gate(repo, "--strict").code, 1)

    def test_new_untracked_skill_without_record_is_unreviewed(self):  # T4
        for use_git in (False, True):
            with self.subTest(git=use_git):
                repo = h.make_repo(self.tmp / ("g%d" % use_git), skills=("alpha",), git=use_git)
                h.pass_records(repo)
                h.write_skill(repo, "newone")  # 未追跡
                self.assertSkillState(repo, "newone", "UNREVIEWED")
                self.assertEqual(h.run_gate(repo, "--strict").code, 1)

    def test_deleted_or_renamed_skill_leaves_no_stale_entry(self):  # T5
        repo = self.mk(("alpha", "bravo"))
        h.pass_records(repo)
        shutil.rmtree(repo / h.SKILLS_REL / "alpha")
        st = h.states(repo)
        self.assertNotIn("alpha", st)
        shutil.move(str(repo / h.SKILLS_REL / "bravo"), str(repo / h.SKILLS_REL / "bravo2"))
        st = h.states(repo)
        self.assertNotIn("bravo", st)
        self.assertEqual(st.get("bravo2"), "UNREVIEWED")  # 記録は skill 名に紐づくので改名後は未レビュー

    def test_decision_table_rows_resolve_in_documented_order(self):  # T6
        with self.subTest(row=1, why="PASS と台帳が両方 → PASS・「台帳から外せる」"):
            repo = self.fresh("row1")
            h.pass_records(repo)
            h.write_ledger(repo, {"alpha": None})
            self.assertSkillState(repo, "alpha", "PASS")
            self.assertIn("台帳から外せる", h.run_gate(repo, "--all").out)
            self.assertIn("ledger_removable", h.gate_json(repo)["skills"]["alpha"]["notes"])
        with self.subTest(row=2, why="最新が FAIL → FAIL"):
            repo = self.fresh("row2")
            h.pass_records(repo, names=["review-skill"])
            h.write_record(repo, "alpha", result=h.make_result("FAIL"))
            self.assertSkillState(repo, "alpha", "FAIL")
        with self.subTest(row=3, why="kind 欠落で hash 一致のみ → INVALID"):
            repo = self.fresh("row3")
            h.pass_records(repo, names=["review-skill"])
            h.write_record(repo, "alpha", kind=None)
            self.assertSkillState(repo, "alpha", "INVALID")
        with self.subTest(row=4, why="記録なし・台帳 hash 一致 → BASELINE_DEBT"):
            repo = self.fresh("row4")
            h.pass_records(repo, names=["review-skill"])
            h.write_ledger(repo, {"alpha": None})
            self.assertSkillState(repo, "alpha", "BASELINE_DEBT")
        with self.subTest(row=5, why="別 hash の記録のみ → STALE"):
            repo = self.fresh("row5")
            h.pass_records(repo, names=["review-skill"])
            h.write_record(repo, "alpha", content_hash="a" * 64)
            self.assertSkillState(repo, "alpha", "STALE")
        with self.subTest(row=6, why="記録なし → UNREVIEWED"):
            repo = self.fresh("row6")
            h.pass_records(repo, names=["review-skill"])
            self.assertSkillState(repo, "alpha", "UNREVIEWED")
        with self.subTest(order="古い hash の新しい FAIL は無視され、現在の PASS が勝つ"):
            repo = self.fresh("ord1")
            h.pass_records(repo, names=["review-skill"])
            h.write_record(repo, "alpha", reviewed_at="2026-10-10T00:00:00Z")
            h.write_record(repo, "alpha", reviewed_at="2026-10-15T00:00:00Z", content_hash="b" * 64, result=h.make_result("FAIL"))
            self.assertSkillState(repo, "alpha", "PASS")
        with self.subTest(order="編集を元に戻すと過去の PASS が再び適用される"):
            repo = self.fresh("ord2")
            h.pass_records(repo, names=["review-skill"])
            sk = repo / h.SKILLS_REL / "alpha" / "SKILL.md"
            original = sk.read_bytes()
            h.write_record(repo, "alpha")
            sk.write_bytes(original + b"edit\n")
            self.assertSkillState(repo, "alpha", "STALE")
            sk.write_bytes(original)
            self.assertSkillState(repo, "alpha", "PASS")
        with self.subTest(order="INVALID が最新でも、より前の有効な PASS が適用される"):
            repo = self.fresh("ord3")
            h.pass_records(repo, names=["review-skill"])
            h.write_record(repo, "alpha", reviewed_at="2026-10-10T00:00:00Z")
            h.write_record(repo, "alpha", reviewed_at="2026-10-18T00:00:00Z", kind=None)
            self.assertSkillState(repo, "alpha", "PASS")
        with self.subTest(order="同時刻はファイル名順（後ろが最新）"):
            repo = self.fresh("ord4")
            h.pass_records(repo, names=["review-skill"])
            h.write_record(repo, "alpha", reviewed_at="2026-10-10T00:00:00Z", suffix="aaaaaaaa")
            h.write_record(repo, "alpha", reviewed_at="2026-10-10T00:00:00Z", suffix="bbbbbbbb", result=h.make_result("FAIL"))
            self.assertSkillState(repo, "alpha", "FAIL")
        with self.subTest(order="最新が FAIL で、より古い PASS もある（どちらも現在の hash）→ FAIL"):
            repo = self.fresh("ord5")
            h.pass_records(repo, names=["review-skill"])
            h.write_record(repo, "alpha", reviewed_at="2026-10-10T00:00:00Z")
            h.write_record(repo, "alpha", reviewed_at="2026-10-18T00:00:00Z", result=h.make_result("FAIL"))
            self.assertSkillState(repo, "alpha", "FAIL")

    def test_fail_and_invalid_take_precedence_over_a_matching_ledger_entry(self):  # T6 の補足（台帳を先に見る誤実装を捕まえる）
        with self.subTest(case="最新が FAIL かつ台帳の hash 一致 → FAIL（BASELINE_DEBT ではない）"):
            repo = self.fresh("pf1")
            h.pass_records(repo, names=["review-skill"])
            h.write_record(repo, "alpha", result=h.make_result("FAIL"))
            h.write_ledger(repo, {"alpha": None})
            self.assertSkillState(repo, "alpha", "FAIL")
            self.assertEqual(h.run_gate(repo, "--strict").code, 1)
        with self.subTest(case="hash が一致しない不正記録だけの skill は STALE（INVALID にならない）"):
            repo = self.fresh("pf2")
            h.pass_records(repo, names=["review-skill"])
            h.write_record(repo, "alpha", kind=None, content_hash="d" * 64)
            self.assertSkillState(repo, "alpha", "STALE")
        with self.subTest(case="hash が一致しない不正記録だけで、台帳の hash は一致 → BASELINE_DEBT（行 3 に入らず行 4）"):
            repo = self.fresh("pf3")
            h.pass_records(repo, names=["review-skill"])
            h.write_record(repo, "alpha", kind=None, content_hash="d" * 64)
            h.write_ledger(repo, {"alpha": None})
            self.assertSkillState(repo, "alpha", "BASELINE_DEBT")

    def test_broken_records_never_crash_the_gate_and_invalid_beats_the_ledger(self):  # T7/T6 の補足（壊れた記録）
        def new(name):
            repo = self.fresh(name)
            h.pass_records(repo, names=["review-skill"])
            return repo

        broken = {
            "必須キー欠落（best_practices_snapshot が無い）": dict(drop=("best_practices_snapshot",)),
            "型違い（score が文字列）": dict(result=dict(h.make_result("PASS"), score="95")),
            "reviewer.kind 不正": dict(kind="human"),
        }
        for label, res in h.inconsistent_results().items():  # 保存時 T10 と同じ 6 種の整合不一致の手書き記録
            broken["整合不一致: " + label] = dict(result=res)
        for n, (label, kw) in enumerate(broken.items()):
            with self.subTest(case=label):
                repo = new("b-%d" % n)
                h.write_record(repo, "alpha", **kw)  # hash は現在の hash と一致
                r = h.run_gate(repo, "--json")
                self.assertEqual(r.code, 0, r)
                self.assertNotIn("Traceback", r.err)
                self.assertEqual(r.json()["skills"]["alpha"]["state"], "INVALID")
                self.assertEqual(h.run_gate(repo, "--strict").code, 1)
                h.write_ledger(repo, {"alpha": None})  # 台帳にも載せる: 行 3（INVALID）が行 4（BASELINE_DEBT）に優先
                self.assertSkillState(repo, "alpha", "INVALID")
        with self.subTest(case="JSON 構文エラーの記録ファイル: 例外にならず、その記録は無視して警告する"):
            repo = new("b-syntax")
            bad = repo / h.HISTORY_REL / "alpha" / "20261001T000000Z-deadbeef.json"
            bad.parent.mkdir(parents=True, exist_ok=True)
            bad.write_text("{ broken", encoding="utf-8", newline="\n")
            r = h.run_gate(repo, "--json")
            self.assertEqual(r.code, 0, r)
            self.assertNotIn("Traceback", r.err)
            data = r.json()
            self.assertEqual(data["skills"]["alpha"]["state"], "UNREVIEWED")
            self.assertTrue(any("deadbeef" in w for w in data["warnings"]), data["warnings"])

    def test_criteria_change_makes_all_passes_stale(self):  # T12
        repo = self.mk(("alpha", "bravo"))
        h.write_skill(repo, "alpha", alpha_files())
        h.pass_records(repo)
        self.assertEqual(set(h.states(repo).values()), {"PASS"})
        before = h.criteria_sha(repo)
        crit = repo / h.CRITERIA_REL
        crit.write_text(crit.read_text(encoding="utf-8").replace("基準1", "基準1改"), encoding="utf-8", newline="\n")
        self.assertNotEqual(before, h.criteria_sha(repo))
        st = h.states(repo)
        self.assertEqual(st["alpha"], "STALE")  # alpha 自体の内容は同じ。criteria の sha256 だけが違う
        self.assertEqual(st["bravo"], "STALE")
        self.assertEqual(h.run_gate(repo, "--strict").code, 1)

    def test_records_made_under_old_criteria_are_stale_not_invalid(self):  # T37
        import json
        edits = {
            "min_score を上げた": lambda d: d["pass_rule"].__setitem__("min_score", 95),
            "axis id を変えた": lambda d: d["axes"][0].__setitem__("id", "structure2"),
        }
        for n, (label, fn) in enumerate(edits.items()):
            with self.subTest(change=label):
                repo = self.fresh("t37-%d" % n)
                h.write_record(repo, "alpha", result=h.make_result("PASS", score=90, axes=[{"id": a, "score": 18} for a in h.AXIS_IDS]))
                crit = repo / h.CRITERIA_REL
                d = json.loads(crit.read_text(encoding="utf-8"))
                fn(d)
                h.write_json(crit, d)
                self.assertSkillState(repo, "alpha", "STALE")  # sha256 が違う記録に現行 criteria の検査を当てない（INVALID にならない）
                h.write_ledger(repo, {"alpha": None})  # 台帳の hash が一致しても、INVALID（行 3）でなく行 4 が先に当たる
                self.assertSkillState(repo, "alpha", "BASELINE_DEBT")

    def test_baseline_debt_is_exempt_only_while_hash_matches(self):  # T13
        repo = self.mk(("alpha", "bravo"))
        h.pass_records(repo, names=["review-skill"])
        h.write_ledger(repo, {"alpha": None, "bravo": None})
        self.assertEqual(h.states(repo), {"alpha": "BASELINE_DEBT", "bravo": "BASELINE_DEBT", "review-skill": "PASS"})
        self.assertEqual(h.run_gate(repo, "--strict").code, 0)
        # 記録なしの skill を編集 → UNREVIEWED
        b = repo / h.SKILLS_REL / "bravo" / "SKILL.md"
        b.write_bytes(b.read_bytes() + b"edit\n")
        self.assertSkillState(repo, "bravo", "UNREVIEWED")
        self.assertEqual(h.run_gate(repo, "--strict").code, 1)
        # 別 hash の記録がある skill: 台帳が現在の hash と一致する間は免除（行 4 が行 5 に優先）、編集すると STALE
        repo2 = h.make_repo(self.tmp / "r2", skills=("alpha",))
        h.pass_records(repo2, names=["review-skill"])
        h.write_record(repo2, "alpha", content_hash="c" * 64)
        h.write_ledger(repo2, {"alpha": None})
        self.assertSkillState(repo2, "alpha", "BASELINE_DEBT")
        a = repo2 / h.SKILLS_REL / "alpha" / "SKILL.md"
        a.write_bytes(a.read_bytes() + b"edit\n")
        self.assertSkillState(repo2, "alpha", "STALE")
        self.assertEqual(h.run_gate(repo2, "--strict").code, 1)

    def test_expired_best_practices_sot_adds_warning_without_changing_verdict(self):  # T16
        repo = self.mk(("alpha",))
        h.pass_records(repo)
        fresh = h.run_gate(repo, "--all")
        self.assertNotIn("WARN: best-practices SoT expired", fresh.out)
        env = h.base_env(SKILL_REVIEW_NOW=h.EXPIRED_NOW)
        expired = h.run_gate(repo, "--all", env=env)
        self.assertEqual(expired.code, 0)
        self.assertIn("WARN: best-practices SoT expired", expired.out)
        self.assertEqual(h.states(repo, env), {"alpha": "PASS", "review-skill": "PASS"})  # 判定は変わらない
        self.assertTrue(any("expired" in w for w in h.gate_json(repo, env)["warnings"]))
        self.assertEqual(h.run_gate(repo, "--strict", env=env).code, 0)
        # 境界: 期限の当日（fetched 2026-09-25 + 30 日 = 2026-10-25）は期限内、翌日から期限切れ
        last_day = h.run_gate(repo, "--all", env=h.base_env(SKILL_REVIEW_NOW="2026-10-25T23:59:59Z"))
        self.assertNotIn("WARN: best-practices SoT expired", last_day.out)
        next_day = h.run_gate(repo, "--all", env=h.base_env(SKILL_REVIEW_NOW="2026-10-26T00:00:00Z"))
        self.assertIn("WARN: best-practices SoT expired", next_day.out)

    def test_all_mode_exits_zero_and_json_output_is_valid(self):  # T18
        repo = self.mk(("alpha", "bravo", "charlie"))
        h.pass_records(repo, names=["review-skill", "alpha"])
        h.write_ledger(repo, {"bravo": None})
        allr = h.run_gate(repo, "--all")
        self.assertEqual(allr.code, 0)  # 未レビューがあっても常に 0
        self.assertIn("alpha: PASS", allr.out)
        self.assertIn("bravo: BASELINE_DEBT", allr.out)
        self.assertIn("charlie: UNREVIEWED", allr.out)
        self.assertIn("PASS=2 BASELINE_DEBT=1 NEEDS_REVIEW=1", allr.out)
        js = h.run_gate(repo, "--json")
        self.assertEqual(js.code, 0)
        data = js.json()
        self.assertEqual(data["counts"], {"PASS": 2, "BASELINE_DEBT": 1, "NEEDS_REVIEW": 1})
        self.assertEqual(data["skills"]["charlie"]["state"], "UNREVIEWED")
        self.assertEqual(h.run_gate(repo, "--strict").code, 1)


class ContentHash(RepoTestCase):
    def hash_of(self, repo, name="alpha"):
        r = h.run_gate(repo, "--hash", name)
        self.assertEqual(r.code, 0, r)
        self.assertRegex(r.out.strip(), r"^[0-9a-f]{64}$")
        return r.out.strip()

    def test_content_hash_is_identical_across_crlf_lf_and_worktree_vs_git_tree(self):  # T11
        text = "---\nname: alpha\n---\n日本語の本文\n2 行目\n"
        with self.subTest(case="CRLF 版と LF 版は同じ hash・参照実装と一致"):
            a = h.make_repo(self.tmp / "lf", skills=("alpha",))
            b = h.make_repo(self.tmp / "crlf", skills=("alpha",))
            h.write_skill(a, "alpha", {"SKILL.md": text.encode("utf-8")})
            h.write_skill(b, "alpha", {"SKILL.md": text.replace("\n", "\r\n").encode("utf-8")})
            self.assertEqual(self.hash_of(a), self.hash_of(b))
            self.assertEqual(self.hash_of(a), h.skill_hash(a, "alpha"))
        with self.subTest(case="git 経路と走査経路が同じ hash（gitignore 対象ファイルが無い skill）"):
            g = h.make_repo(self.tmp / "gitrepo", skills=("alpha",), git=True)
            h.write_skill(g, "alpha", {"SKILL.md": text, "references/é.md": "x\n", "references/B.md": "b\n", "references/a.md": "a\n"})
            h.git_commit_all(g, "files")
            scan = self.tmp / "scan"
            shutil.copytree(g, scan, ignore=shutil.ignore_patterns(".git"))
            self.assertEqual(self.hash_of(g), self.hash_of(scan))
            self.assertEqual(self.hash_of(g), h.skill_hash(g, "alpha"))  # パスは UTF-8 バイト順（B.md < a.md < é.md）
        with self.subTest(case="__pycache__・*.pyc・.DS_Store・シンボリックリンクは無視"):
            r = h.make_repo(self.tmp / "ign", skills=("alpha",))
            base = self.hash_of(r)
            d = r / h.SKILLS_REL / "alpha"
            (d / "__pycache__").mkdir()
            (d / "__pycache__" / "x.cpython-311.pyc").write_bytes(b"\0\1")
            (d / "scripts").mkdir(exist_ok=True)
            (d / "scripts" / "m.pyc").write_bytes(b"\0\1")
            (d / ".DS_Store").write_bytes(b"junk")
            self.assertEqual(self.hash_of(r), base)
        with self.subTest(case="走査経路（git なし）は .gitignore を適用しない（gitignore に載るファイルも hash に入る）"):
            r = h.make_repo(self.tmp / "scan-ignore", skills=("alpha",), git=False)
            base = self.hash_of(r)
            (r / h.SKILLS_REL / "alpha" / "ignored.txt").write_text("gitignore に載る名前\n", encoding="utf-8", newline="\n")
            self.assertNotEqual(self.hash_of(r), base)
            self.assertEqual(self.hash_of(r), h.skill_hash(r, "alpha"))  # 参照実装（走査経路）は ignored.txt を含める
        with self.subTest(case="git 経路: 未追跡は含み、gitignore 済みは含まず、追跡済みで作業ツリーに無いものは除外して件数を出す"):
            g = h.make_repo(self.tmp / "gitrules", skills=("alpha",), git=True)
            d = g / h.SKILLS_REL / "alpha"
            (d / "references").mkdir()
            (d / "references" / "r.md").write_text("r\n", encoding="utf-8", newline="\n")
            h.git_commit_all(g, "add r")
            base = self.hash_of(g)
            (d / "ignored.txt").write_text("gitignore 済み\n", encoding="utf-8", newline="\n")
            self.assertEqual(self.hash_of(g), base)  # gitignore 済みは含まない
            (d / "new.md").write_text("未追跡\n", encoding="utf-8", newline="\n")
            self.assertNotEqual(self.hash_of(g), base)  # 未追跡（ignore されていない）は含む
            (d / "new.md").unlink()
            (d / "references" / "r.md").unlink()  # 追跡済みだが作業ツリーに無い
            (d / "ignored.txt").unlink()  # 参照実装は gitignore を適用しない走査なので、比べる前に消す
            r = h.run_gate(g, "--hash", "alpha")
            self.assertEqual(r.code, 0)
            self.assertEqual(r.out.strip(), h.skill_hash(g, "alpha"))
            self.assertIn("読めないファイル", h.run_gate(g, "--all").out)
        with self.subTest(case="バイナリは無変換（NUL を含む先頭 8000 バイト）"):
            r1 = h.make_repo(self.tmp / "bin1", skills=("alpha",))
            r2 = h.make_repo(self.tmp / "bin2", skills=("alpha",))
            h.write_skill(r1, "alpha", {"SKILL.md": "x\n", "assets/d.bin": b"\0\r\n\1"})
            h.write_skill(r2, "alpha", {"SKILL.md": "x\n", "assets/d.bin": b"\0\n\1"})
            self.assertNotEqual(self.hash_of(r1), self.hash_of(r2))
            self.assertEqual(self.hash_of(r1), h.skill_hash(r1, "alpha"))
        with self.subTest(case="先頭 8000 バイトの NUL 判定の境界（CRLF 版・LF 版とも NUL が先頭 8000 バイトの内 = バイナリ、外 = テキスト）"):
            def blob(eol, nul_at):
                # nul_at は LF 版の NUL の位置。x の個数は eol によらず同じなので、CRLF 版の NUL は 1 バイト後ろにずれる
                return b"l1" + eol + b"x" * (nul_at - 3) + b"\0" + b"tail" + eol
            # 7998: LF 版 7998・CRLF 版 7999（どちらも先頭 8000 バイトの内 = バイナリ）/ 8000: LF 版 8000・CRLF 版 8001（どちらも外 = テキスト）
            for nul_at, expect_equal in ((7998, False), (8000, True)):
                ra = h.make_repo(self.tmp / ("nb-a%d" % nul_at), skills=("alpha",))
                rb = h.make_repo(self.tmp / ("nb-b%d" % nul_at), skills=("alpha",))
                h.write_skill(ra, "alpha", {"SKILL.md": "x\n", "assets/d.dat": blob(b"\r\n", nul_at)})
                h.write_skill(rb, "alpha", {"SKILL.md": "x\n", "assets/d.dat": blob(b"\n", nul_at)})
                same = self.hash_of(ra) == self.hash_of(rb)
                self.assertEqual(same, expect_equal, "NUL の位置 %d" % nul_at)
                self.assertEqual(self.hash_of(ra), h.skill_hash(ra, "alpha"))
        with self.subTest(case="BOM は特別扱いしない（BOM 付きと無しは別 hash、BOM 付きの CRLF と LF は同じ hash）"):
            bom = b"\xef\xbb\xbf"
            r1 = h.make_repo(self.tmp / "bom1", skills=("alpha",))
            r2 = h.make_repo(self.tmp / "bom2", skills=("alpha",))
            r3 = h.make_repo(self.tmp / "bom3", skills=("alpha",))
            h.write_skill(r1, "alpha", {"SKILL.md": bom + b"a\r\nb\r\n"})
            h.write_skill(r2, "alpha", {"SKILL.md": bom + b"a\nb\n"})
            h.write_skill(r3, "alpha", {"SKILL.md": b"a\nb\n"})
            self.assertEqual(self.hash_of(r1), self.hash_of(r2))
            self.assertNotEqual(self.hash_of(r2), self.hash_of(r3))
            self.assertEqual(self.hash_of(r1), h.skill_hash(r1, "alpha"))
        with self.subTest(case="core.autocrlf=true で commit・checkout した作業ツリー（CRLF）でも、LF の作業ツリーと同じ hash"):
            lf = h.make_repo(self.tmp / "ac-lf", skills=("alpha",), git=True)
            ac = h.make_repo(self.tmp / "ac-crlf", skills=("alpha",), git=False)
            h.git_init(ac)
            h.git(ac, "config", "core.autocrlf", "true")
            h.git_commit_all(ac, "initial")
            d = ac / h.SKILLS_REL / "alpha"
            (d / "SKILL.md").unlink()
            h.git(ac, "checkout", "--", ".")  # autocrlf=true なので CRLF で書き戻される
            self.assertIn(b"\r\n", (d / "SKILL.md").read_bytes())
            self.assertEqual(self.hash_of(ac), h.skill_hash(lf, "alpha"))  # lf 側と内容は同じ（LF）
        with self.subTest(case="scripts/tests/ は除外"):
            r = h.make_repo(self.tmp / "exc", skills=("alpha",))
            base = self.hash_of(r)
            h.write_skill(r, "alpha", {"scripts/tests/t.py": "pass\n"})
            self.assertEqual(self.hash_of(r), base)

    def test_hash_of_unknown_skill_is_an_error(self):  # 補足
        repo = self.mk(("alpha",))
        r = h.run_gate(repo, "--hash", "no-such-skill")
        self.assertEqual(r.code, 2, r)
        self.assertIn("no-such-skill", r.out + r.err)  # script 不在の exit 2 と区別する（Red で偽の合格にならないように）


class SymlinkHandling(RepoTestCase):
    """シンボリックリンクを作れない環境（権限が無い Windows など）では skip として記録される。run_tests.py は skip を非ゼロ終了にする
    （SKILL_REVIEW_TEST_ALLOW_SKIP=1 のときだけ許す）。別クラスにしてあるので、skip になっても他の hash の試験は実行される。"""

    def test_symlinks_are_not_followed_in_the_content_hash(self):  # T11 の一部
        r = h.make_repo(self.tmp / "sym", skills=("alpha",))
        base = h.run_gate(r, "--hash", "alpha").out.strip()
        d = r / h.SKILLS_REL / "alpha"
        try:
            os.symlink(str(d / "SKILL.md"), str(d / "link.md"))
        except (OSError, NotImplementedError) as e:
            self.skipTest("symlink を作れない環境（権限なし）: %s" % e)
        after = h.run_gate(r, "--hash", "alpha")
        self.assertEqual(after.code, 0, after)
        self.assertEqual(after.out.strip(), base)  # リンクは辿らず、hash に入らない
        self.assertEqual(after.out.strip(), h.skill_hash(r, "alpha"))


class LedgerVerification(RepoTestCase):
    def ledger_repo(self, name="ledger", skills=("alpha", "bravo", "charlie"), entries=("alpha", "bravo")):
        repo = h.make_repo(self.tmp / name, skills=skills, git=True)
        h.pass_records(repo, names=["review-skill"])
        h.write_ledger(repo, {n: None for n in entries})
        h.git_commit_paths(repo, [h.LEDGER_REL, h.HISTORY_REL + "/review-skill"], "ledger")
        return repo

    def verify(self, repo):
        return h.run_gate(repo, "--verify-ledger")

    def test_ledger_edits_after_the_anchor_commit_are_detected(self):  # T14
        repo = self.ledger_repo()
        original = h.read_ledger(repo)
        self.assertEqual(self.verify(repo).code, 0)
        with self.subTest(edit="エントリの追加"):
            led = h.read_ledger(repo)
            led["skills"]["charlie"] = {"content_hash": h.skill_hash(repo, "charlie"), "registered": "2026-10-28", "reason": "追加"}
            h.write_json(repo / h.LEDGER_REL, led)
            r = self.verify(repo)
            self.assertEqual(r.code, 1, r)
            self.assertIn("TAMPERED charlie", r.out)
            h.write_json(repo / h.LEDGER_REL, original)
        with self.subTest(edit="hash の書き換え"):
            led = h.read_ledger(repo)
            led["skills"]["alpha"]["content_hash"] = "f" * 64
            h.write_json(repo / h.LEDGER_REL, led)
            r = self.verify(repo)
            self.assertEqual(r.code, 1, r)
            self.assertIn("TAMPERED alpha", r.out)
            h.write_json(repo / h.LEDGER_REL, original)
        with self.subTest(edit="エントリ内の別の値（日付）の変更も、エントリ全体が基準と同一でなければ検出"):
            led = h.read_ledger(repo)
            led["skills"]["alpha"]["registered"] = "2026-11-01"
            h.write_json(repo / h.LEDGER_REL, led)
            r = self.verify(repo)
            self.assertEqual(r.code, 1, r)
            self.assertIn("TAMPERED alpha", r.out)
            h.write_json(repo / h.LEDGER_REL, original)
        with self.subTest(edit="エントリの削除は許される"):
            led = h.read_ledger(repo)
            del led["skills"]["bravo"]
            h.write_json(repo / h.LEDGER_REL, led)
            self.assertEqual(self.verify(repo).code, 0)
            h.write_json(repo / h.LEDGER_REL, original)
        with self.subTest(edit="改ざんを commit しても基準は最初に追加した commit のまま"):
            led = h.read_ledger(repo)
            led["skills"]["charlie"] = {"content_hash": h.skill_hash(repo, "charlie"), "registered": "2026-10-28", "reason": "追加"}
            h.write_json(repo / h.LEDGER_REL, led)
            h.git_commit_paths(repo, [h.LEDGER_REL], "tamper")
            r = self.verify(repo)
            self.assertEqual(r.code, 1, r)
            self.assertIn("TAMPERED charlie", r.out)
        with self.subTest(edit="基準 commit 自体に混ぜた不正エントリは検出対象外（D7 B）"):
            repo2 = h.make_repo(self.tmp / "anchor-dirty", skills=("alpha", "bravo"), git=True)
            h.write_ledger(repo2, {"alpha": None, "bravo": None})  # 初回に未レビュー skill をそのまま載せる
            h.git_commit_paths(repo2, [h.LEDGER_REL], "first ledger")
            self.assertEqual(self.verify(repo2).code, 0)

    def test_ledger_rebaselining_by_delete_then_add_commits_makes_the_new_ledger_the_anchor(self):  # 台帳の再基準化（計画書 改訂 5）
        repo = self.ledger_repo("rebase")
        # 旧台帳を in-place で書き換える（検出される）
        led = h.read_ledger(repo)
        led["skills"]["charlie"] = {"content_hash": h.skill_hash(repo, "charlie"), "registered": "2026-10-28", "reason": "追加"}
        h.write_json(repo / h.LEDGER_REL, led)
        self.assertEqual(self.verify(repo).code, 1)
        # 正当な修正: 旧台帳を削除する commit と、新台帳を追加する commit に分ける → 新台帳が基準になる
        new_ledger = h.read_ledger(repo)
        (repo / h.LEDGER_REL).unlink()
        h.git(repo, "add", "-A", "--", h.LEDGER_REL)
        h.git(repo, "commit", "-q", "-m", "remove old ledger", "--", h.LEDGER_REL)
        h.write_json(repo / h.LEDGER_REL, new_ledger)
        h.git_commit_paths(repo, [h.LEDGER_REL], "add new ledger")
        r = self.verify(repo)
        self.assertEqual(r.code, 0, r)  # 新台帳（charlie を含む）が基準
        # 新しい基準の後の in-place 編集は、やはり検出される
        led2 = h.read_ledger(repo)
        led2["skills"]["alpha"]["content_hash"] = "e" * 64
        h.write_json(repo / h.LEDGER_REL, led2)
        r = self.verify(repo)
        self.assertEqual(r.code, 1, r)
        self.assertIn("TAMPERED alpha", r.out)

    def test_ledger_verification_is_unverifiable_without_git_or_anchor(self):  # T15
        with self.subTest(case="台帳が未 commit"):
            repo = self.mk(("alpha",), git=True)
            h.write_ledger(repo, {"alpha": None})
            r = self.verify(repo)
            self.assertEqual(r.code, 2, r)
            self.assertIn("UNVERIFIABLE", r.out)
        with self.subTest(case="git 無し（.git が無い）"):
            repo = h.make_repo(self.tmp / "nogit", skills=("alpha",), git=False)
            h.write_ledger(repo, {"alpha": None})
            r = self.verify(repo)
            self.assertEqual(r.code, 2, r)
            self.assertIn("UNVERIFIABLE", r.out)
        with self.subTest(case="git が実行できない（PATH に無い）"):
            repo = self.ledger_repo("noexec")
            empty = self.tmp / "emptybin"
            empty.mkdir()
            env = h.base_env(PATH=str(empty))
            r = h.run_gate(repo, "--verify-ledger", env=env)
            self.assertEqual(r.code, 2, r)
            self.assertIn("UNVERIFIABLE", r.out)
        with self.subTest(case="浅い clone で基準 commit が取れない"):
            origin = self.ledger_repo("origin")
            led = h.read_ledger(origin)
            led["skills"]["alpha"]["reason"] = "後の変更"
            h.write_json(origin / h.LEDGER_REL, led)
            h.git_commit_paths(origin, [h.LEDGER_REL], "later ledger edit")
            clone = self.tmp / "shallow"
            r = h.run_proc(["git", "clone", "-q", "--depth", "1", origin.as_uri(), str(clone)])
            self.assertEqual(r.code, 0, r)
            self.assertEqual(h.git(clone, "rev-parse", "--is-shallow-repository").out.strip(), "true")
            r = h.run_gate(clone, "--verify-ledger")
            self.assertEqual(r.code, 2, r)
            self.assertIn("UNVERIFIABLE", r.out)


class JapaneseUnderCp1252(RepoTestCase):
    def test_scripts_print_japanese_under_cp1252_console(self):  # T26
        env = h.base_env(PYTHONUTF8=None, PYTHONIOENCODING="cp1252")
        repo = self.mk(("alpha", "bravo"))
        h.pass_records(repo)
        h.write_ledger(repo, {"alpha": None})  # PASS と台帳の両方 →「台帳から外せる」（日本語）が出る
        cases = [
            ("gate --all", lambda: h.run_gate(repo, "--all", env=env), 0, "台帳から外せる"),
            ("gate --strict", lambda: h.run_gate(repo, "--strict", env=env), 0, None),
            ("append（拒否メッセージ）", lambda: h.run_append(repo, "alpha", "0" * 64, self.result_file(h.make_result("PASS")), env=env), 1, None),
            ("render（生成区間の標準出力）", lambda: h.run_render(repo, env=env), 0, "軸1"),
            ("consistency", lambda: h.run_consistency(repo, env=env), None, None),
        ]
        for name, fn, code, needle in cases:
            with self.subTest(script=name):
                r = fn()
                self.assertNotIn("UnicodeEncodeError", r.err, r)
                self.assertNotIn("Traceback", r.err, r)
                if code is not None:
                    self.assertEqual(r.code, code, r)
                if needle:
                    self.assertIn(needle, r.out)
        with self.subTest(script="hook SessionStart（日本語の systemMessage）"):
            r = h.run_hook(repo, h.SESSION_START, env=env)
            self.assertEqual(r.code, 0, r)
            self.assertNotIn("Traceback", r.err, r)
            self.assertIsInstance(r.data, dict, r)  # JSON として読める
            self.assertIn("要レビュー", r.data["systemMessage"])
        with self.subTest(script="append（日本語を必ず含む拒否理由）"):
            r = h.run_append(repo, "alpha", "0" * 64, self.result_file(h.make_result("PASS")), env=env)
            self.assertEqual(r.code, 1, r)
            self.assertNotIn("UnicodeEncodeError", r.err, r)
            self.assertTrue(re.search(r"[぀-ヿ一-鿿]", r.err), "拒否理由に日本語が含まれる: %r" % r.err)


if __name__ == "__main__":
    unittest.main()
