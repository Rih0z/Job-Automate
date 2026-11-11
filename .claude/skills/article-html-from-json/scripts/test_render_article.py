#!/usr/bin/env python3
"""render_article.py の試験（標準ライブラリ unittest。一時ディレクトリの合成データだけを使う）。

実行: python -X utf8 -B .claude/skills/article-html-from-json/scripts/test_render_article.py
"""
import copy
import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import render_article as R  # noqa: E402

EXAMPLES = HERE.parent / "examples"


def doc():
    return {
        "schema": "article-json/v1",
        "meta": {"title": "試験の記事", "output": "out.html"},
        "blocks": [
            {"bid": "a", "type": "p", "html": "前置き。ワークフローを使う。"},
            {"bid": "toc", "type": "toc"},
            {"bid": "h1", "type": "heading", "level": 2, "id": "one", "html": "一つ目"},
            {"bid": "h1s", "type": "heading", "level": 3, "id": "one-a", "html": "小見出し"},
            {"bid": "p1", "type": "p", "html": '本文の<a href="https://example.com/x">外部リンク</a>と<code>ワークフロー</code>。'},
            {"bid": "t1", "type": "table", "columns": ["名前", "値"], "rows": [["ワークフロー", "ワークフロー"]], "row_header": True},
            {"bid": "h2", "type": "heading", "level": 2, "id": "hidden", "html": "目次に出さない", "toc": False},
            {"bid": "g", "type": "glossary", "terms": [{"term": "ワークフロー", "desc": "手順のつながり"}]},
            {"bid": "r", "type": "references", "items": [{"id": "ref-1", "html": "資料"}]},
            {"bid": "inc", "type": "include", "name": "footer"},
        ],
    }


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        (self.dir / "partials").mkdir()
        (self.dir / "partials" / "footer.html").write_text("<footer>\n  <p>&copy; {{YEAR}} 例 ワークフロー</p>\n</footer>\n", encoding="utf-8")
        self.path = self.dir / "article.json"

    def tearDown(self):
        self.tmp.cleanup()

    def put(self, d, ledger="new"):
        R.write_json(self.path, d)
        lp = self.dir / "fix-ledger.json"
        if ledger == "new":
            R.write_json(lp, R.new_ledger(d))
        elif ledger is None:
            if lp.exists():
                lp.unlink()
        else:
            R.write_json(lp, ledger)

    def cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = R.main(["render_article.py"] + [str(a) for a in args])
        return code, out.getvalue(), err.getvalue()

    def render(self, d, year=2040):
        return R.render_doc(d, R.load_partials(self.path, d), year)


class TestRender(Base):
    def test_deterministic_and_formats(self):
        h1, p1 = self.render(doc())
        h2, _ = self.render(doc())
        self.assertEqual(p1, [])
        self.assertEqual(h1, h2)
        self.assertIn('<th scope="row">ワークフロー</th>', h1)  # 見出しセルはリンクにしない
        self.assertIn('<td><a class="term" href="#term-1">ワークフロー</a></td>', h1)
        self.assertIn('<a href="https://example.com/x" target="_blank" rel="noopener">外部リンク</a>', h1)
        self.assertIn("<code>ワークフロー</code>", h1)  # コードはリンクにしない
        self.assertIn("&copy; 2040 例 ワークフロー", h1)  # include は逐語（リンクにしない）
        self.assertIn('<dt id="term-1">ワークフロー</dt>', h1)

    def test_toc(self):
        h, _ = self.render(doc())
        toc = h[h.index('<nav class="toc">'):h.index("</nav>")]
        self.assertEqual([x for x in ("#one", "#glossary", "#references") if x in toc], ["#one", "#glossary", "#references"])
        self.assertNotIn("#one-a", toc)
        self.assertNotIn("#hidden", toc)

    def test_page_template(self):
        d = doc()
        d["meta"]["template"] = "page"
        h, p = self.render(d)
        self.assertEqual(p, [])
        self.assertTrue(h.startswith("<!doctype html>"))
        self.assertIn("<title>試験の記事</title>", h)

    def test_validation_failures(self):
        cases = [
            (lambda d: d["blocks"][0].update(html="<div>x</div>"), "許可外のタグ"),
            (lambda d: d["blocks"][0].update(html='<a href="#x" onclick="y">x</a>'), "許可外の属性"),
            (lambda d: d["blocks"][0].update(html="<strong>x"), "閉じていない"),
            (lambda d: d["blocks"][0].update(html="ok ✅"), "絵文字"),
            (lambda d: d["blocks"][0].pop("bid"), "bid"),
            (lambda d: d["blocks"][1].update(bid="a"), "bid の重複"),
            (lambda d: d["blocks"][5]["rows"].append(["1"]), "列数"),
            (lambda d: d["blocks"].append({"bid": "x", "type": "toc"}), "toc は 1 つまで"),
            (lambda d: d["blocks"].append({"bid": "y", "type": "nope"}), "不明な type"),
            (lambda d: d["blocks"].insert(0, d["blocks"].pop(8)), "references より前"),
        ]
        for mutate, msg in cases:
            d = doc()
            mutate(d)
            probs = R.validate_article(d)
            self.assertTrue(any(msg in p for p in probs), (msg, probs))

    def test_include_before_glossary_is_not_linked(self):
        d = doc()
        d["blocks"].insert(0, {"bid": "top", "type": "include", "name": "footer"})
        d["blocks"].pop()
        h, p = self.render(d)
        self.assertEqual(p, [])
        self.assertIn("&copy; 2040 例 ワークフロー</p>", h)
        self.assertIn('前置き。<a class="term" href="#term-1">ワークフロー</a>', h)

    def test_include_failures(self):
        d = doc()
        d["blocks"][-1]["name"] = "missing"
        h, p = self.render(d)
        self.assertIsNone(h)
        self.assertTrue(any("missing.html が無い" in x for x in p), p)
        (self.dir / "partials" / "bad.html").write_text("<p>{{NAME}}</p>", encoding="utf-8")
        d["blocks"][-1]["name"] = "bad"
        h, p = self.render(d)
        self.assertTrue(any("プレースホルダ" in x for x in p), p)

    def test_anchor_check(self):
        d = doc()
        d["blocks"][0]["html"] = '<a href="#nowhere">x</a>'
        h, p = self.render(d)
        self.assertTrue(any("#nowhere" in x for x in p), p)


class TestLedger(Base):
    def fix(self, **kw):
        f = {"id": "F-001", "received": "2040-01-01", "request": "直して", "status": "applied", "targets": ["p1"],
             "change": "文言", "applied": "2040-01-01", "source_sync": "done"}
        f.update(kw)
        return f

    def test_gate_conditions(self):
        d = doc()
        base = R.new_ledger(d, kind="baseline")
        cases = [({"status": "open"}, "open"), ({"source_sync": "pending"}, "source_sync"), ({"targets": []}, "targets"),
                 ({"status": "rejected"}, "reason"), ({"targets": ["zz"]}, "存在しない bid"), ({}, "変わっていない"),
                 ({"request": ""}, "request")]
        for kw, msg in cases:
            led = copy.deepcopy(base)
            led["fixes"] = [self.fix(**kw)]
            self.assertTrue(any(msg in p for p in R.validate_ledger(led, d)), (msg, R.validate_ledger(led, d)))
        self.assertTrue(any("無い" in p for p in R.validate_ledger(None, d)))

    def test_render_with_applied_fix_and_record(self):
        d = doc()
        led = R.new_ledger(d, kind="baseline")
        d["blocks"][4]["html"] = "直した本文。"
        led["fixes"] = [self.fix(), {"id": "F-002", "received": "2040-01-01", "request": "消して", "status": "rejected", "reason": "要る"}]
        self.put(d, led)
        code, _, err = self.cli("render", self.path, "--year", 2040)
        self.assertEqual(code, 0, err)
        rec = json.loads((self.dir / "fix-ledger.json").read_text(encoding="utf-8"))["renders"][-1]
        self.assertEqual((rec["year"], rec["fixes"]), (2040, ["F-001", "F-002"]))
        self.assertIn("直した本文", (self.dir / "out.html").read_text(encoding="utf-8"))
        self.assertEqual(self.cli("render", self.path, "--year", 2040)[0], 0)  # 記録済みの指摘は再検査しない

    def test_missing_ledger_and_open_block_render(self):
        self.put(doc(), ledger=None)
        code, _, err = self.cli("render", self.path)
        self.assertEqual(code, 1)
        self.assertIn("台帳", err)
        led = R.new_ledger(doc())
        led["fixes"] = [self.fix(status="open")]
        self.put(doc(), led)
        self.assertEqual(self.cli("render", self.path)[0], 1)
        self.assertFalse((self.dir / "out.html").exists())

    def test_init_ledger_refused_when_output_exists(self):
        self.put(doc())
        self.assertEqual(self.cli("render", self.path, "--year", 2040)[0], 0)
        (self.dir / "fix-ledger.json").unlink()
        code, _, err = self.cli("init-ledger", self.path)
        self.assertEqual(code, 1)
        self.assertIn("init-ledger を使わない", err)

    def test_unrecorded_change_blocks_render(self):
        d = doc()
        self.put(d)
        self.assertEqual(self.cli("render", self.path, "--year", 2040)[0], 0)  # draft は照合しない
        led = json.loads((self.dir / "fix-ledger.json").read_text(encoding="utf-8"))
        d["blocks"][0]["html"] = "台帳に書かずに変えた。"
        self.put(d, led)
        code, _, err = self.cli("render", self.path, "--year", 2040)
        self.assertEqual(code, 1)
        self.assertIn("紐づかない変更", err)

    def test_preview_out_does_not_record(self):
        self.put(doc())
        self.assertEqual(self.cli("render", self.path, "--out", self.dir / "preview.html")[0], 0)
        self.assertEqual(len(json.loads((self.dir / "fix-ledger.json").read_text(encoding="utf-8"))["renders"]), 1)


class TestVerifyCompareExamples(Base):
    def test_verify_detects_hand_edit(self):
        self.put(doc())
        self.assertEqual(self.cli("render", self.path, "--year", 2040)[0], 0)
        self.assertEqual(self.cli("verify", self.path)[0], 0)  # 記録の年を使う
        p = self.dir / "out.html"
        p.write_text(p.read_text(encoding="utf-8").replace("前置き。", "前置き!"), encoding="utf-8", newline="\n")
        code, _, err = self.cli("verify", self.path)
        self.assertEqual(code, 1)
        self.assertIn("不一致", err)

    def test_compare_whitespace_only(self):
        h, _ = self.render(doc())
        a, b = self.dir / "a.html", self.dir / "b.html"
        a.write_text(h, encoding="utf-8")
        b.write_text(h.replace("\n  <li>", "\n<li>"), encoding="utf-8")
        self.assertEqual(self.cli("compare", a, b)[0], 0)
        b.write_text(h.replace("前置き。", "前置き!"), encoding="utf-8")
        self.assertEqual(self.cli("compare", a, b)[0], 1)

    def test_bundled_example_passes_check_and_renders(self):
        work = self.dir / "ex"
        shutil.copytree(EXAMPLES, work)
        self.assertEqual(self.cli("check", work / "article.example.json")[0], 0)
        code, _, err = self.cli("render", work / "article.example.json", "--year", 2040, "--out", work / "preview.html")
        self.assertEqual(code, 0, err)


if __name__ == "__main__":
    unittest.main(verbosity=1)
