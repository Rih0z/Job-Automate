"""render_report.py の試験。実行: python .claude/skills/progress-report-format/scripts/test_render_report.py"""
import copy
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
SCRIPT = os.path.join(HERE, "render_report.py")
SPEC = os.path.join(SKILL, "criteria", "report-format.json")
EXAMPLE = os.path.join(SKILL, "examples", "report.example.json")


def load_module():
    s = importlib.util.spec_from_file_location("render_report", SCRIPT)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


class T(unittest.TestCase):
    def setUp(self):
        self.m = load_module()
        self.spec = load(SPEC)
        self.report = load(EXAMPLE)

    def test_R1_spec_shape(self):
        self.assertEqual([s["id"] for s in self.spec["sections"]],
                         ["achieved", "remaining", "initiatives", "external", "next_week"])
        self.assertEqual(self.spec["stages"], ["設計", "実装", "部品テスト", "実機確認"])
        self.assertEqual(set(self.spec["progress_phrases"]), {"未着手", "途中", "ほぼ完了", "完了", "完走せず"})

    def test_R2_example_is_valid_and_renders_in_order(self):
        self.assertEqual(self.m.validate(self.report, self.spec), [])
        lines = self.m.render(self.report, self.spec).splitlines()
        self.assertEqual(lines[0], "【今週の進捗（2026-01-05〜2026-01-18）】")
        heads = [l for l in lines if l.startswith("■ ")]
        self.assertEqual(heads, ["■ 今回できるようになったこと", "■ まだ課題として残っていること",
                                 "■ 取り組み別の状況（設計→実装→部品テスト→実機確認）", "■ 対外活動", "■ 来週の予定"])
        self.assertIn("・今期・来週とも対外面談なし", lines)

    def test_R3_initiative_phrases(self):
        cases = {"途中": "設計の途中", "未着手": "設計は未着手", "完走せず": "設計で完走せず",
                 "ほぼ完了": "ほぼ完了", "完了": "完了"}
        for prog, want in cases.items():
            with self.subTest(prog=prog):
                r = copy.deepcopy(self.report)
                r["sections"]["initiatives"] = [{"name": "A", "stage": "設計", "progress": prog}]
                self.assertIn("・A: " + want, self.m.render(r, self.spec).splitlines())

    def test_R4_note_is_wrapped(self):
        r = copy.deepcopy(self.report)
        r["sections"]["initiatives"] = [{"name": "A", "stage": "設計", "progress": "途中", "note": "実装は未着手"}]
        self.assertIn("・A: 設計の途中（実装は未着手）", self.m.render(r, self.spec).splitlines())

    def test_R5_invalid_inputs_are_reported(self):
        def bad(mutate):
            r = copy.deepcopy(self.report)
            mutate(r)
            return self.m.validate(r, self.spec)
        cases = {
            "missing section": lambda r: r["sections"].pop("remaining"),
            "empty list": lambda r: r["sections"].__setitem__("achieved", []),
            "unknown section": lambda r: r["sections"].__setitem__("extra", ["x"]),
            "bad date": lambda r: r["period"].__setitem__("start", "10/1"),
            "end before start": lambda r: r["period"].update(start="2026-02-01", end="2026-01-01"),
            "leading bullet": lambda r: r["sections"]["achieved"].__setitem__(0, "・x"),
            "newline": lambda r: r["sections"]["achieved"].__setitem__(0, "a\nb"),
            "unknown stage": lambda r: r["sections"]["initiatives"][0].__setitem__("stage", "企画"),
            "unknown progress": lambda r: r["sections"]["initiatives"][0].__setitem__("progress", "順調"),
            "wrong schema": lambda r: r.__setitem__("schema", "x"),
            "empty name": lambda r: r["sections"]["initiatives"][0].__setitem__("name", " "),
        }
        for name, mut in cases.items():
            with self.subTest(case=name):
                self.assertTrue(bad(mut), name)

    def run_cli(self, *args):
        env = dict(os.environ, PYTHONUTF8="1")
        return subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True,
                              encoding="utf-8", env=env)

    def test_R6_cli_exit_codes(self):
        p = self.run_cli(EXAMPLE)
        self.assertEqual(p.returncode, 0)
        self.assertTrue(p.stdout.startswith("【今週の進捗"))
        with tempfile.TemporaryDirectory() as d:
            bad = os.path.join(d, "bad.json")
            r = copy.deepcopy(self.report)
            r["sections"].pop("next_week")
            with open(bad, "w", encoding="utf-8") as f:
                json.dump(r, f, ensure_ascii=False)
            p = self.run_cli(bad)
            self.assertEqual(p.returncode, 1)
            self.assertEqual(p.stdout, "")
            self.assertIn("next_week", p.stderr)
            p = self.run_cli(os.path.join(d, "none.json"))
            self.assertEqual(p.returncode, 2)

    def test_R7_no_company_marker_in_shared_files(self):
        # 禁止語は公開リポジトリに書かない。環境変数 REPORT_FORBIDDEN_WORDS（カンマ区切り）か、
        # gitignore 済みの <repo>/.tmp/forbidden-words.txt（1 行 1 語）から読む。どちらも無ければ skip。
        words = [w.strip() for w in os.environ.get("REPORT_FORBIDDEN_WORDS", "").split(",") if w.strip()]
        local = os.path.join(SKILL, "..", "..", "..", ".tmp", "forbidden-words.txt")
        if not words and os.path.isfile(local):
            with open(local, encoding="utf-8") as f:
                words = [l.strip() for l in f if l.strip() and not l.startswith("#")]
        if not words:
            self.skipTest("禁止語の一覧が無い（REPORT_FORBIDDEN_WORDS か .tmp/forbidden-words.txt）")
        raw = open(EXAMPLE, encoding="utf-8").read() + open(SPEC, encoding="utf-8").read()
        for w in words:
            self.assertNotIn(w, raw)


if __name__ == "__main__":
    unittest.main()
