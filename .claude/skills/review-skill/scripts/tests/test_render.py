"""render_review_skill_md.py（D1 の二重管理の解消）の試験: 補足 4 件（計画書の T24 は test_consistency.py）。標準ライブラリの unittest。

仕様の補完（helpers.py 冒頭にも記載）: CLI は --repo-root R [--write | --check]。無指定は生成区間（マーカー行を含む）を stdout に出す。
生成区間 = workflows/software-development/review-skill.md の中の、【生成ここから】の行から【生成ここまで】の行まで（行全体がマーカー）。
生成区間には axis の name・weight、各 criterion の name・weight・checks[] の文をすべて含み、山括弧のタグ（<x> 形式）を使わない。
--write は区間の外を 1 バイトも変えない。--check は現ファイルと再生成が一致なら 0、違えば 1。マーカーが無ければ 1。
"""
import json
import re
import unittest

import helpers as h
from helpers import RepoTestCase


class Render(RepoTestCase):
    def test_generated_section_contains_every_axis_criterion_and_check(self):
        repo = self.mk(("alpha",), consistent=False)
        r = h.run_render(repo)
        self.assertEqual(r.code, 0, r)
        lines = r.out.splitlines()
        self.assertEqual(lines[0], h.MARK_BEGIN)
        self.assertEqual(lines[-1], h.MARK_END)
        crit = json.loads((repo / h.CRITERIA_REL).read_text(encoding="utf-8"))
        for axis in crit["axes"]:
            self.assertIn(axis["name"], r.out)
            for c in axis["criteria"]:
                self.assertIn(c["name"], r.out)
                for chk in c["checks"]:
                    self.assertIn(chk, r.out)  # 項目の脱落が無い
        self.assertIn("20", r.out)  # 配点
        self.assertIsNone(re.search(r"</?[A-Za-z][^>]*>", r.out), "山括弧のタグを使わない")
        self.assertEqual(h.run_render(repo).out, r.out)  # 決定的

    def test_write_replaces_only_the_generated_section_and_is_idempotent(self):
        repo = self.mk(("alpha",), consistent=False)
        md = repo / h.MD_REL
        before = md.read_bytes().decode("utf-8")
        head, rest = before.split(h.MARK_BEGIN, 1)
        tail = rest.split(h.MARK_END, 1)[1]
        r = h.run_render(repo, "--write")
        self.assertEqual(r.code, 0, r)
        after = md.read_bytes().decode("utf-8")  # UTF-8 で読める
        self.assertTrue(after.startswith(head + h.MARK_BEGIN))
        self.assertTrue(after.endswith(h.MARK_END + tail))  # 区間の外は 1 バイトも変わらない
        self.assertNotIn("(placeholder)", after)
        self.assertIn("確認項目1-a", after)
        self.assertEqual(h.run_render(repo, "--write").code, 0)
        self.assertEqual(md.read_bytes().decode("utf-8"), after)  # 冪等

    def test_check_mode_reports_drift_with_exit_code(self):
        repo = self.mk(("alpha",), consistent=False)
        self.assertEqual(h.run_render(repo, "--check").code, 1)  # 生成前（placeholder のまま）は不一致
        h.run_render(repo, "--write")
        self.assertEqual(h.run_render(repo, "--check").code, 0)
        md = repo / h.MD_REL
        md.write_text(md.read_text(encoding="utf-8").replace("確認項目1-a", "確認項目1-A"), encoding="utf-8", newline="\n")
        self.assertEqual(h.run_render(repo, "--check").code, 1)

    def test_missing_markers_fail_without_modifying_the_file(self):
        repo = self.mk(("alpha",), consistent=False)
        md = repo / h.MD_REL
        md.write_text("# マーカー無し\n本文\n", encoding="utf-8", newline="\n")
        before = md.read_bytes()
        for args in (["--write"], ["--check"]):
            r = h.run_render(repo, *args)
            self.assertEqual(r.code, 1, r)
            self.assertTrue(r.err.strip())
        self.assertEqual(md.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
