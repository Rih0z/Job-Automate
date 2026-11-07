"""slide-composition-planner / slide-clarity-review 周りの単体テスト（stdlib の unittest）。

対象: slide_checks.py / validate_slide_data.py / append_review_record.py の検査（_shared/scripts）、
      extract_deck.py / check_deck.py / gate.py / finalize_review.py / render_deck.py（slide-clarity-review/scripts）、
      check_ja_slide.py（slide-japanese-review/scripts）。
fixture は全てテスト内で生成する（実データの practice id・閾値には依存しない: id は fx- 接頭辞）。
実行: python -m unittest .claude/skills/_shared/scripts/test_slide_skills.py -v
依存: python-pptx（fixture の生成に必要。extract_deck 自体は標準ライブラリのみ）。
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS = os.path.abspath(os.path.join(HERE, "..", ".."))  # .claude/skills
REVIEW_SCRIPTS = os.path.join(SKILLS, "slide-clarity-review", "scripts")
for _p in (HERE, REVIEW_SCRIPTS):
    if _p not in sys.path:
        sys.path.insert(0, _p)

VALIDATE = os.path.join(HERE, "validate_slide_data.py")
EXTRACT = os.path.join(REVIEW_SCRIPTS, "extract_deck.py")
CHECK = os.path.join(REVIEW_SCRIPTS, "check_deck.py")


def run(script, *args):
    p = subprocess.run([sys.executable, script, *args], capture_output=True, text=True, encoding="utf-8")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def write_json(directory, name, obj):
    path = os.path.join(directory, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
    return path


# ---------------------------------------------------------------- fixtures: practices
def source(sid="s1", verification="fetched", **kw):
    d = {"id": sid, "title": "Source " + sid, "url": "https://example.com/" + sid, "kind": "article",
         "authors": ["A. Author"], "organization": "Example Org", "year": 2020,
         "verification": verification, "checked_on": "2026-10-01", "max_age_days": 365}
    d.update(kw)
    return d


def practice(pid="fx-p1", severity="should", method="llm", sid="s1", quote="a sufficiently long quote text", **kw):
    check = {"method": method, "how": "how to check"}
    d = {"id": pid, "category": "text", "title": "Title " + pid, "rule": "A rule without numbers",
         "rationale": "because", "severity": severity, "check": check,
         "evidence": [{"source_id": sid, "locator": "section 1", "quote": quote}], "adaptation": "none"}
    d.update(kw)
    return d


def auto(pid, scope, metric, op, threshold=None, severity="should", **kw):
    chk = {"method": "auto", "how": "h", "scope": scope, "metric": metric, "op": op}
    if threshold is not None:
        chk["threshold"] = threshold
        chk["threshold_origin"] = "adaptation"
    return practice(pid, severity=severity, check=chk, **kw)


def practices_doc(practices=None, sources=None):
    return {"schema": "slide-best-practices/v1", "sources": sources or [source()],
            "practices": practices or [practice()]}


def fx_deck_practices():
    """deck-spec 検査用の fx practices 一式。"""
    return [
        auto("fx-points-limit", "deck-spec", "points_count", "max", 5),
        auto("fx-closing", "deck-spec", "closing_present", "required"),
        auto("fx-content-source", "deck-spec", "content_source_present", "required",
             applies_when={"evidence_type_not_in": ["opinion", "proposal"]}),
        auto("fx-title-nonempty", "deck-spec", "action_title_chars", "min", 1),
        auto("fx-assertion-title-length", "deck-spec", "action_title_chars", "max", 40),
        auto("fx-focal", "deck-spec", "focal_element_present", "required",
             applies_when={"role_in": ["content"]}),
        auto("fx-raw-color", "deck-spec", "raw_color_absent", "required"),
    ]


def good_slide(no, role="content", **kw):
    d = {"no": no, "role": role, "action_title": "Sales grew twenty percent", "key_message": "m",
         "evidence_type": "chart", "points": ["a", "b"], "layout_hint": "content-1col",
         "content_source": "https://example.com/data", "focal_element": "figure",
         "emphasis_role": "neutral", "text_size_class": "body"}
    d.update(kw)
    return d


def good_spec():
    return {"audience": "managers", "goal": "decide", "key_message": "Adopt it", "storyline": "problem-solution",
            "slides": [good_slide(1, "title", focal_element="title", evidence_type="opinion", content_source=None),
                       good_slide(2), good_slide(3),
                       good_slide(4, "closing", evidence_type="proposal", content_source=None, focal_element="title")]}


# ---------------------------------------------------------------- fixtures: pptx
def build_pptx(path, kind):
    from pptx import Presentation
    from pptx.util import Inches, Pt
    prs = Presentation()
    blank = prs.slide_layouts[6]
    title_only = prs.slide_layouts[5]

    def tb(slide, text, size=None, left=1, top=1):
        box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(6), Inches(2))
        tf = box.text_frame
        tf.text = text
        if size:
            for r in tf.paragraphs[0].runs:
                r.font.size = Pt(size)
        return box

    if kind == "dense":          # slide1: ok / slide2: タイトル無し・300 文字・12pt
        s1 = prs.slides.add_slide(title_only)
        s1.shapes.title.text = "Good title"
        tb(s1, "short body", 20)
        s2 = prs.slides.add_slide(blank)
        tb(s2, "あ" * 300, 12)
    elif kind == "good":
        s1 = prs.slides.add_slide(title_only)
        s1.shapes.title.text = "Good title"
        tb(s1, "short body", 20)
    elif kind == "inherited":
        s1 = prs.slides.add_slide(blank)
        tb(s1, "no explicit size")
    elif kind == "counts":       # 段落 4（空 1）・画像 2（うち 1 はグループ内）・ノート
        from PIL import Image
        png = path + ".png"
        Image.new("RGB", (4, 4), (10, 20, 30)).save(png)
        s1 = prs.slides.add_slide(blank)
        box = tb(s1, "a", 18)
        for t in ("b", "", "c"):
            box.text_frame.add_paragraph().text = t
        s1.shapes.add_picture(png, Inches(1), Inches(4))
        grp = s1.shapes.add_group_shape()
        grp.shapes.add_picture(png, Inches(3), Inches(4))
        s1.notes_slide.notes_text_frame.text = "note"
        s2 = prs.slides.add_slide(blank)
        tb(s2, "x", 18)
    elif kind == "table_group":  # 表セル + グループ内テキスト
        s1 = prs.slides.add_slide(blank)
        tbl = s1.shapes.add_table(2, 2, Inches(1), Inches(1), Inches(4), Inches(2)).table
        for i, t in enumerate(("aa", "bb", "cc", "dd")):
            tbl.cell(i // 2, i % 2).text = t
        grp = s1.shapes.add_group_shape()
        gb = grp.shapes.add_textbox(Inches(1), Inches(4), Inches(3), Inches(1))
        gb.text_frame.text = "group text"
    elif kind in ("contrast_bad", "contrast_good", "colors_many", "edges", "theme_color", "bg_fill"):
        from pptx.dml.color import RGBColor
        from pptx.enum.dml import MSO_THEME_COLOR
        s1 = prs.slides.add_slide(blank)

        def colored(text, left, top, fill=None, color=None, theme=False):
            box = tb(s1, text, 18, left=left, top=top)
            if fill:
                box.fill.solid()
                box.fill.fore_color.rgb = RGBColor(*fill)
            run = box.text_frame.paragraphs[0].runs[0]
            if theme:
                run.font.color.theme_color = MSO_THEME_COLOR.ACCENT_1
            elif color:
                run.font.color.rgb = RGBColor(*color)
            return box

        if kind == "contrast_bad":      # 暗い地に暗い文字（比 ≈1.0）
            colored("dark on dark", 1, 1, fill=(31, 41, 55), color=(30, 40, 50))
        elif kind == "contrast_good":   # 暗い地に白（比 ≈14.7）
            colored("white on dark", 1, 1, fill=(31, 41, 55), color=(255, 255, 255))
        elif kind == "colors_many":     # 明示色 6 種（文字色 3 + 塗り 3）
            for i, c in enumerate([(10, 20, 30), (200, 30, 30), (30, 200, 30)]):
                colored("c%d" % i, 1, 1 + i, fill=(240 - i * 5, 240, 240), color=c)
        elif kind == "edges":           # 左端 5 種（1.0 / 1.3 / 2.0 / 2.7 / 3.4 インチ）
            for i, left in enumerate((1.0, 1.3, 2.0, 2.7, 3.4)):
                tb(s1, "e%d" % i, 18, left=left, top=1 + i)
        elif kind == "theme_color":
            colored("theme colored", 1, 1, theme=True)
        elif kind == "bg_fill":         # スライド背景を明示（濃色）+ 薄い文字（比が低い）
            s1.background.fill.solid()
            s1.background.fill.fore_color.rgb = RGBColor(20, 20, 20)
            colored("light on bg", 1, 1, color=(30, 30, 30))
    prs.save(path)


# ================================================================ validate practices (T01-T17)
class ValidatePractices(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def v(self, doc, *extra):
        path = write_json(self.d, "p.json", doc)
        return run(VALIDATE, "practices", path, *extra)

    def test_T01_valid(self):
        code, out = self.v(practices_doc())
        self.assertEqual(code, 0, out)

    def test_T02_evidence_missing(self):
        p = practice()
        p["evidence"] = []
        code, out = self.v(practices_doc([p]))
        self.assertEqual(code, 1)
        self.assertIn("fx-p1: evidence missing", out)

    def test_T03_url_missing(self):
        s = source()
        del s["url"]
        code, out = self.v(practices_doc(sources=[s]))
        self.assertEqual(code, 1)
        self.assertIn("s1: url missing", out)

    def test_T04_unknown_source(self):
        code, out = self.v(practices_doc([practice(sid="nope")]))
        self.assertEqual(code, 1)
        self.assertIn("unknown source_id", out)

    def test_T05_must_requires_fetched(self):
        doc = practices_doc([practice(severity="must", sid="s2")], [source("s1"), source("s2", "secondary")])
        code, out = self.v(doc)
        self.assertEqual(code, 1)
        self.assertIn("must requires fetched evidence", out)

    def test_T06_threshold_origin_missing(self):
        p = auto("fx-a", "deck", "body_chars", "max", 10)
        del p["check"]["threshold_origin"]
        code, out = self.v(practices_doc([p]))
        self.assertEqual(code, 1)
        self.assertIn("threshold_origin missing", out)

    def test_T07_stale_warning(self):
        code, out = self.v(practices_doc(), "--today", "2030-01-01")
        self.assertEqual(code, 0, out)
        self.assertIn("stale source", out)

    def test_T08_locator_quote_empty(self):
        p = practice()
        p["evidence"][0]["locator"] = ""
        code, out = self.v(practices_doc([p]))
        self.assertEqual(code, 1)
        self.assertIn("locator empty", out)
        p = practice()
        p["evidence"][0]["quote"] = ""
        code, out = self.v(practices_doc([p]))
        self.assertEqual(code, 1)
        self.assertIn("quote empty", out)

    def test_T09_numeric_in_rule(self):
        p = practice(rule="Keep text under 200 文字 per slide")
        code, out = self.v(practices_doc([p]))
        self.assertEqual(code, 1)
        self.assertIn("numeric in rule requires threshold_origin=source", out)
        p = practice(rule="Keep text under 200 文字 per slide", numeric_in_rule_ok=True)
        code, out = self.v(practices_doc([p]))
        self.assertEqual(code, 0, out)

    def test_T10_source_required_keys(self):
        s = source()
        del s["title"]
        code, out = self.v(practices_doc(sources=[s]))
        self.assertEqual(code, 1)
        self.assertIn("s1: title missing", out)

    def test_T11_check_spec(self):
        cases = {
            "scope missing": lambda c: c.pop("scope"),
            "unknown metric": lambda c: c.update(metric="nope"),
            "metric not allowed for scope": lambda c: c.update(metric="points_count"),
            "unknown op": lambda c: c.update(op="between"),
            "threshold required": lambda c: c.pop("threshold"),
        }
        for msg, mutate in cases.items():
            p = auto("fx-a", "deck", "body_chars", "max", 10)
            mutate(p["check"])
            code, out = self.v(practices_doc([p]))
            self.assertEqual(code, 1, msg)
            self.assertIn(msg, out)

    def test_T12_enums_and_duplicates(self):
        code, out = self.v(practices_doc([practice("fx-a"), practice("fx-a")]))
        self.assertEqual((code, "duplicate practice id" in out), (1, True), out)
        code, out = self.v(practices_doc([practice(severity="critical")]))
        self.assertEqual((code, "invalid severity" in out), (1, True), out)
        code, out = self.v(practices_doc([practice(method="magic")]))
        self.assertEqual((code, "invalid method" in out), (1, True), out)

    def test_T13_count_warning(self):
        ps = [practice("fx-%02d" % i) for i in range(50)]
        code, out = self.v(practices_doc(ps))
        self.assertEqual(code, 0, out)
        self.assertIn("practice count 50 outside 10-40", out)

    def _fetch_fixture(self, body_html=None, quote="a sufficiently long quote text"):
        body = body_html or ("<html><body><script>x()</script><p>%s</p>" % ("filler text " * 30) +
                             "<p>a sufficiently&nbsp;long\n quote   text</p></body></html>")
        os.makedirs(os.path.join(self.d, "src"), exist_ok=True)
        with open(os.path.join(self.d, "src", "s1.html"), "wb") as f:
            f.write(body.encode("utf-8"))
        sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
        log = {"entries": [{"source_id": "s1", "url": "https://example.com/s1", "fetched_on": "2026-10-30",
                            "method": "raw-http", "sha256": sha, "excerpts": [quote]}]}
        return log

    def test_T14_fetch_log_entry(self):
        base = self._fetch_fixture()
        cases = {
            "fetch-log entry missing": {"entries": []},
            "method must be raw-http": {"entries": [dict(base["entries"][0], method="webfetch-summary")]},
            "sha256 missing": {"entries": [{k: v for k, v in base["entries"][0].items() if k != "sha256"}]},
            "fetch-log url mismatch": {"entries": [dict(base["entries"][0], url="https://other.example/")]},
        }
        for msg, log in cases.items():
            lp = write_json(self.d, "log.json", log)
            code, out = self.v(practices_doc(), "--fetch-log", lp)
            self.assertEqual(code, 1, msg)
            self.assertIn(msg, out)

    def test_T15_quote_in_log(self):
        log = self._fetch_fixture(quote="something else entirely different")
        lp = write_json(self.d, "log.json", log)
        code, out = self.v(practices_doc(), "--fetch-log", lp)
        self.assertEqual(code, 1)
        self.assertIn("quote not found in fetch-log", out)
        short = "x" * 14
        log = self._fetch_fixture(quote=short)
        lp = write_json(self.d, "log.json", log)
        code, out = self.v(practices_doc([practice(quote=short)]), "--fetch-log", lp)
        self.assertEqual(code, 1)
        self.assertIn("quote shorter than 15", out)

    def test_T16_sources_dir(self):
        log = self._fetch_fixture()
        lp = write_json(self.d, "log.json", log)
        sd = os.path.join(self.d, "src")
        code, out = self.v(practices_doc(), "--fetch-log", lp, "--sources-dir", sd)
        self.assertEqual(code, 0, out)  # タグ・実体参照・改行を含む本文でも正規化後に一致
        bad = json.loads(json.dumps(log))
        bad["entries"][0]["sha256"] = "0" * 64
        code, out = self.v(practices_doc(), "--fetch-log", write_json(self.d, "log.json", bad), "--sources-dir", sd)
        self.assertEqual(code, 1)
        self.assertIn("sha256 mismatch", out)
        fake = self._fetch_fixture(quote="a fabricated sentence not in the page")
        code, out = self.v(practices_doc([practice(quote="a fabricated sentence not in the page")]),
                           "--fetch-log", write_json(self.d, "log.json", fake), "--sources-dir", sd)
        self.assertEqual(code, 1)
        self.assertIn("excerpt not in source body", out)

    def test_T17_body_too_short(self):
        log = self._fetch_fixture(body_html="<p>a sufficiently long quote text</p>")
        code, out = self.v(practices_doc(), "--fetch-log", write_json(self.d, "log.json", log),
                           "--sources-dir", os.path.join(self.d, "src"))
        self.assertEqual(code, 1)
        self.assertIn("body too short for fetched", out)

    def test_T43_threshold_in_quote(self):
        p = auto("fx-a", "deck", "body_chars", "max", 5)
        p["check"]["threshold_origin"] = "source"
        p["evidence"][0]["quote"] = "limit is about 15 items in total"
        code, out = self.v(practices_doc([p]))
        self.assertEqual(code, 1)
        self.assertIn("threshold not in quote", out)
        p["evidence"][0]["quote"] = "limit is about 5 items in total"
        code, out = self.v(practices_doc([p]))
        self.assertEqual(code, 0, out)


# ================================================================ clarity / deck-spec / palette
class ValidateOthers(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def clarity(self, axes):
        ps = [practice("fx-a"), practice("fx-b")]
        pp = write_json(self.d, "p.json", practices_doc(ps))
        cp = write_json(self.d, "c.json", {"schema": "slide-clarity-criteria/v1", "axes": axes})
        return run(VALIDATE, "clarity", cp, "--practices", pp)

    @staticmethod
    def axes5(refs=None, weights=None):
        weights = weights or [20] * 5
        return [{"id": "ax%d" % i, "title": "t", "weight": w, "practice_ids": refs or ["fx-a"]}
                for i, w in enumerate(weights)]

    def test_T18_clarity(self):
        code, out = self.clarity(self.axes5())
        self.assertEqual(code, 0, out)
        code, out = self.clarity(self.axes5(refs=["fx-zzz"]))
        self.assertEqual(code, 1)
        self.assertIn("unknown practice_id", out)
        code, out = self.clarity(self.axes5()[:4])
        self.assertIn("axes must be 5", out)
        code, out = self.clarity(self.axes5(weights=[20, 20, 20, 20, 10]))
        self.assertIn("weights must sum to 100", out)

    def spec(self, spec, practices=None):
        pp = write_json(self.d, "p.json", practices_doc(practices or fx_deck_practices()))
        sp = write_json(self.d, "s.json", spec)
        return run(VALIDATE, "deck-spec", sp, "--practices", pp)

    def test_T19_valid_spec(self):
        code, out = self.spec(good_spec())
        self.assertEqual(code, 0, out)

    def test_T20_required_keys(self):
        s = good_spec()
        del s["slides"]
        code, out = self.spec(s)
        self.assertEqual(code, 1)
        self.assertIn("missing key: slides", out)
        s = good_spec()
        del s["slides"][1]["role"]
        code, out = self.spec(s)
        self.assertEqual(code, 1)
        self.assertIn("slide 2: missing key: role", out)

    def test_T21_points_limit(self):
        s = good_spec()
        s["slides"][1]["points"] = list("abcdef")
        code, out = self.spec(s)
        self.assertEqual(code, 1)
        self.assertIn("slide 2: fx-points-limit violated (6 > 5)", out)

    def test_T22_closing(self):
        s = good_spec()
        s["slides"][3]["role"] = "content"
        code, out = self.spec(s)
        self.assertEqual(code, 1)
        self.assertIn("fx-closing violated (closing_present required)", out)

    def test_T23_content_source(self):
        s = good_spec()
        s["slides"][2]["content_source"] = None
        code, out = self.spec(s)
        self.assertEqual(code, 1)
        self.assertIn("slide 3: fx-content-source violated (content_source_present required)", out)
        s = good_spec()
        s["slides"][2]["content_source"] = None
        s["slides"][2]["evidence_type"] = "opinion"
        code, out = self.spec(s)
        self.assertEqual(code, 0, out)

    def test_T24_title_rules(self):
        s = good_spec()
        s["slides"][1]["action_title"] = ""
        code, out = self.spec(s)
        self.assertEqual(code, 1)
        self.assertIn("slide 2: fx-title-nonempty violated (0 < 1)", out)
        s = good_spec()
        s["slides"][1]["action_title"] = "x" * 41
        code, out = self.spec(s)
        self.assertIn("slide 2: fx-assertion-title-length violated (41 > 40)", out)

    def test_T47_raw_color(self):
        s = good_spec()
        s["slides"][1]["key_message"] = "use #123456 as background"
        code, out = self.spec(s)
        self.assertEqual(code, 1)
        self.assertIn("raw color not allowed", out)

    def test_T48_focal_element(self):
        s = good_spec()
        s["slides"][1]["focal_element"] = "none"
        code, out = self.spec(s)
        self.assertEqual(code, 1)
        self.assertIn("slide 2: fx-focal violated (focal_element_present required)", out)
        s = good_spec()
        s["slides"][0]["focal_element"] = "none"  # title スライドは対象外
        code, out = self.spec(s)
        self.assertEqual(code, 0, out)

    def palette(self, roles):
        return run(VALIDATE, "palette", write_json(self.d, "pal.json", {"roles": roles}))

    GOOD_ROLES = {"focus": "#1F3FBF", "surface-1": "#F2F4F8", "surface-2": "#E1E5EC", "border": "#C3CAD6",
                  "text-primary": "#1E2330", "text-secondary": "#4A5060", "emphasis-mid": "#4F5563",
                  "functional": "#0A7F6F"}

    def test_T44_palette_valid(self):
        code, out = self.palette(dict(self.GOOD_ROLES))
        self.assertEqual(code, 0, out)

    def test_T45_palette_shape(self):
        roles = dict(self.GOOD_ROLES)
        del roles["border"]
        code, out = self.palette(roles)
        self.assertEqual(code, 1)
        self.assertIn("role missing: border", out)
        roles = dict(self.GOOD_ROLES, focus="blue")
        code, out = self.palette(roles)
        self.assertEqual(code, 1)
        self.assertIn("invalid color: focus", out)

    def test_T46_palette_contrast(self):
        for role, color, msg in (("text-primary", "#E0E4EC", "contrast too low: text-primary/surface-1"),
                                 ("text-secondary", "#D0D4DC", "contrast too low: text-secondary/surface-1"),
                                 ("focus", "#F0F2F6", "contrast too low: focus/surface-1")):
            code, out = self.palette(dict(self.GOOD_ROLES, **{role: color}))
            self.assertEqual(code, 1, role)
            self.assertIn(msg, out)

    def test_contrast_function(self):
        import slide_checks
        self.assertAlmostEqual(slide_checks.contrast_ratio("#000000", "#FFFFFF"), 21.0, places=1)


# ================================================================ slide_checks / extract / check
class SlideChecks(unittest.TestCase):
    def test_T25_required_semantics(self):
        import slide_checks
        p = auto("fx-r", "deck-spec", "closing_present", "required")
        self.assertIsNone(slide_checks.evaluate_check(p, 0))
        self.assertIsNone(slide_checks.evaluate_check(p, "x"))
        for bad in ("", None, False):
            self.assertIsNotNone(slide_checks.evaluate_check(p, bad), repr(bad))


class Extract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def facts(self, kind):
        pptx = os.path.join(self.d, kind + ".pptx")
        build_pptx(pptx, kind)
        out = os.path.join(self.d, kind + ".json")
        code, text = run(EXTRACT, pptx, "-o", out)
        self.assertEqual(code, 0, text)
        with open(out, encoding="utf-8") as f:
            return json.load(f)

    def test_T26_dense(self):
        f = self.facts("dense")
        s2 = f["slides"][1]
        self.assertEqual((s2["no"], s2["body_chars"], s2["min_font_pt"], s2["title"]), (2, 300, 12, None))
        self.assertEqual(f["slides"][0]["title"], "Good title")

    def test_T27_counts(self):
        f = self.facts("counts")
        s1, s2 = f["slides"]
        self.assertEqual((s1["bullet_count"], s1["image_count"], s1["has_notes"]), (3, 2, True))
        self.assertFalse(s2["has_notes"])
        self.assertEqual(f["slide_count"], 2)

    def test_T28_table_and_group(self):
        s = self.facts("table_group")["slides"][0]
        self.assertEqual(s["body_chars"], len("aabbccdd") + len("group text"))
        self.assertEqual(s["bullet_count"], 1)

    def test_T29_inherited_font(self):
        f = self.facts("inherited")
        self.assertIsNone(f["slides"][0]["min_font_pt"])
        self.assertIn("font inherited: 1 slides", f["limitations"])
        self.assertIn("font checked: 0/1 slides", f["limitations"])


class ExtractDesign(unittest.TestCase):
    """色・位置の抽出（デザインレビューの入力）。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def facts(self, kind):
        pptx = os.path.join(self.d, kind + ".pptx")
        build_pptx(pptx, kind)
        out = os.path.join(self.d, kind + ".json")
        code, text = run(EXTRACT, pptx, "-o", out)
        self.assertEqual(code, 0, text)
        with open(out, encoding="utf-8") as f:
            return json.load(f)

    def test_T55_contrast_low_and_high(self):
        low = self.facts("contrast_bad")["slides"][0]["min_contrast"]
        high = self.facts("contrast_good")["slides"][0]["min_contrast"]
        self.assertLess(low, 1.5)
        self.assertGreater(high, 10)

    def test_T56_background_fill_used_when_explicit(self):
        s = self.facts("bg_fill")["slides"][0]
        self.assertIsNotNone(s["min_contrast"])
        self.assertLess(s["min_contrast"], 2)

    def test_T57_unknown_background_is_not_judged(self):
        f = self.facts("inherited")  # 色も背景も明示なし
        self.assertIsNone(f["slides"][0]["min_contrast"])
        self.assertIn("color checked: 0/1 slides", f["limitations"])

    def test_T58_distinct_colors_and_edges(self):
        self.assertEqual(self.facts("colors_many")["slides"][0]["distinct_colors"], 6)
        self.assertEqual(self.facts("edges")["slides"][0]["left_edge_count"], 5)
        self.assertEqual(self.facts("good")["slides"][0]["distinct_colors"], 0)

    def test_T59_theme_colors_reported_not_resolved(self):
        f = self.facts("theme_color")
        self.assertIsNone(f["slides"][0]["min_contrast"])
        self.assertIn("color theme-based: 1 slides", f["limitations"])

    def test_T60_shapes_geometry_for_reviewer(self):
        shapes = self.facts("edges")["slides"][0]["shapes"]
        self.assertEqual(len(shapes), 5)
        self.assertEqual(shapes[0]["left"], 1.0)
        self.assertEqual({"kind", "left", "top", "width", "height"}, set(shapes[0]) & {"kind", "left", "top", "width", "height"})

    def test_T61_new_metrics_accepted_and_checked(self):
        ps = [auto("fx-edges", "deck", "left_edge_count", "max", 4),
              auto("fx-colors", "deck", "distinct_colors", "max", 5),
              auto("fx-contrast", "deck", "min_contrast", "min", 4.5, severity="must")]
        pp = write_json(self.d, "p.json", practices_doc(ps))
        code, out = run(VALIDATE, "practices", pp)
        self.assertEqual(code, 0, out)
        pptx = os.path.join(self.d, "bad.pptx")
        build_pptx(pptx, "contrast_bad")
        facts = os.path.join(self.d, "bad.facts.json")
        self.assertEqual(run(EXTRACT, pptx, "-o", facts)[0], 0)
        res = os.path.join(self.d, "bad.auto.json")
        code, out = run(CHECK, facts, "--practices", pp, "-o", res)
        self.assertEqual(code, 1)
        with open(res, encoding="utf-8") as f:
            msgs = [v["message"] for v in json.load(f)["violations"]]
        self.assertTrue(any(m.startswith("slide 1: fx-contrast violated (1") and "< 4.5" in m for m in msgs), msgs)
        self.assertEqual(len(msgs), 1)


class CheckDeck(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = self.tmp.name
        ps = [auto("fx-text-density", "deck", "body_chars", "max", 200),
              auto("fx-min-font", "deck", "min_font_pt", "min", 18),
              auto("fx-title", "deck", "title", "required")]
        self.pp = write_json(self.d, "p.json", practices_doc(ps))

    def tearDown(self):
        self.tmp.cleanup()

    def check(self, kind):
        pptx = os.path.join(self.d, kind + ".pptx")
        build_pptx(pptx, kind)
        facts = os.path.join(self.d, kind + ".facts.json")
        self.assertEqual(run(EXTRACT, pptx, "-o", facts)[0], 0)
        out = os.path.join(self.d, kind + ".auto.json")
        code, text = run(CHECK, facts, "--practices", self.pp, "-o", out)
        with open(out, encoding="utf-8") as f:
            return code, json.load(f), text

    def test_T30_violations(self):
        code, res, text = self.check("dense")
        msgs = [v["message"] for v in res["violations"]]
        self.assertIn("slide 2: fx-text-density violated (300 > 200)", msgs)
        self.assertIn("slide 2: fx-min-font violated (12 < 18)", msgs)
        self.assertIn("slide 2: fx-title violated (title required)", msgs)
        self.assertEqual(len(msgs), 3)
        self.assertEqual(code, 1)
        code, res, text = self.check("good")
        self.assertEqual((code, res["violations"]), (0, []))

    def test_T31_inherited_font_not_violation(self):
        code, res, text = self.check("inherited")
        self.assertFalse([v for v in res["violations"] if v["practice_id"] == "fx-min-font"])

    def test_T40_externally_made_deck(self):
        code, res, text = self.check("good")
        self.assertEqual(code, 0, text)
        self.assertIn("font checked: 1/1 slides", res["limitations"])


# ================================================================ gate
AXIS_IDS = ["ax0", "ax1", "ax2", "ax3", "ax4"]
CLARITY = {"axes": [{"id": i, "weight": 20, "practice_ids": ["fx-a"]} for i in AXIS_IDS]}
LLM_PRACTICES = [practice("fx-llm-must", severity="must"), practice("fx-llm-should", severity="should")]
SPLITS = {95: [19] * 5, 90: [18] * 5, 80: [16] * 5, 79: [16, 16, 16, 16, 15], 89.5: [18, 18, 18, 18, 17.5],
          69: [14, 14, 14, 14, 13], 59: [12, 12, 12, 12, 11], 85: [17] * 5}


def axes_of(total):
    return [{"id": i, "score": sc, "citations": ["slide 1"]} for i, sc in zip(AXIS_IDS, SPLITS[total])]


def llm_ok():
    return [{"practice_id": "fx-llm-must", "passed": True}, {"practice_id": "fx-llm-should", "passed": True}]


class Gate(unittest.TestCase):
    def gate(self, total, violations=None, llm=None):
        import gate
        return gate.compute_gate(violations or [], llm if llm is not None else llm_ok(), LLM_PRACTICES, axes_of(total))

    def test_T32_must_violation_fails_even_at_95(self):
        r = self.gate(95, [{"practice_id": "fx-x", "slide": 2, "severity": "must", "message": "m"}])
        self.assertEqual((r["verdict"], r["rank"]), ("FAIL", "S"))
        self.assertTrue(any("must" in x for x in r["reasons"]))

    def test_T33_pass_at_90_and_80(self):
        self.assertEqual((self.gate(90)["verdict"], self.gate(90)["rank"]), ("PASS", "S"))
        self.assertEqual((self.gate(80)["verdict"], self.gate(80)["rank"]), ("PASS", "A"))

    def test_T34_boundary_79_and_89_5(self):
        r = self.gate(79)
        self.assertEqual((r["verdict"], r["rank"]), ("FAIL", "B"))
        r = self.gate(89.5)
        self.assertEqual((r["verdict"], r["rank"]), ("PASS", "A"))

    def test_T35_low_ranks(self):
        self.assertEqual((self.gate(69)["verdict"], self.gate(69)["rank"]), ("FAIL", "C"))
        self.assertEqual((self.gate(59)["verdict"], self.gate(59)["rank"]), ("FAIL", "D"))

    def test_T36_llm_must_failure(self):
        llm = [{"practice_id": "fx-llm-must", "passed": False}, {"practice_id": "fx-llm-should", "passed": True}]
        r = self.gate(90, llm=llm)
        self.assertEqual((r["verdict"], r["rank"]), ("FAIL", "S"))
        self.assertTrue(any("llm" in x for x in r["reasons"]))

    def test_T37_validate_axes(self):
        import gate
        self.assertEqual(gate.validate_axes(axes_of(90), CLARITY), [])
        a = axes_of(90)
        errs = gate.validate_axes(a[:4] + [{"id": "zzz", "score": 18, "citations": ["x"]}], CLARITY)
        self.assertTrue(any("axes mismatch" in e for e in errs) and any("unknown axis id" in e for e in errs), errs)
        a = axes_of(90)
        a[0]["score"] = 21
        self.assertTrue(any("score out of range" in e for e in gate.validate_axes(a, CLARITY)))
        a = axes_of(90)
        a[0]["score"] = True
        self.assertTrue(any("score out of range" in e for e in gate.validate_axes(a, CLARITY)))
        a = axes_of(90)
        a[0]["citations"] = []
        self.assertTrue(any("citations empty" in e for e in gate.validate_axes(a, CLARITY)))

    def test_T38_build_record(self):
        import gate
        import append_review_record
        g = gate.compute_gate([], llm_ok(), LLM_PRACTICES, axes_of(90))
        rec = gate.build_record("C:/decks/sales2025.pptx", axes_of(90), g, ["https://example.com/s1"],
                                ["font inherited: 1 slides"], "2026-10-30T10:00:00+09:00")
        self.assertEqual(append_review_record.validate(rec), [])
        self.assertEqual(rec["schema"], "review-record/v1")
        self.assertEqual(rec["skill"], "slide-clarity-review")
        self.assertTrue(rec["summary"].startswith("ランク "))
        self.assertEqual(rec["score"], 90)
        self.assertEqual(rec["criteria"][0], {"id": "ax0", "result": "18/20"})
        self.assertEqual(rec["sources_cited"], ["https://example.com/s1"])
        self.assertEqual(rec["verdict"], "PASS")

    def test_T39_description_ascii_stem(self):
        import gate
        g = gate.compute_gate([], llm_ok(), LLM_PRACTICES, axes_of(90))
        r1 = gate.build_record("C:/d/提案資料.pptx", axes_of(90), g, [], [], "2026-10-30T10:00:00+09:00")
        self.assertTrue(r1["target"]["description"].startswith("slide-clarity-deck"))
        r2 = gate.build_record("C:/d/営業2025.pptx", axes_of(90), g, [], [], "2026-10-30T10:00:00+09:00")
        self.assertEqual(r2["target"]["description"], "slide-clarity-2025: 営業2025")

    def test_T41_validate_llm_results(self):
        import gate
        self.assertEqual(gate.validate_llm_results(llm_ok(), LLM_PRACTICES), [])
        errs = gate.validate_llm_results(llm_ok()[:1], LLM_PRACTICES)
        self.assertIn("llm_results missing: fx-llm-should", errs)
        errs = gate.validate_llm_results(llm_ok() + [{"practice_id": "fx-zzz", "passed": True}], LLM_PRACTICES)
        self.assertIn("unknown practice_id: fx-zzz", errs)
        errs = gate.validate_llm_results(llm_ok() + [llm_ok()[0]], LLM_PRACTICES)
        self.assertIn("duplicate practice_id: fx-llm-must", errs)
        bad = llm_ok()
        bad[0]["passed"] = "yes"
        self.assertIn("passed must be bool: fx-llm-must", gate.validate_llm_results(bad, LLM_PRACTICES))

    def test_T42_gate_rejects_incomplete_and_ignores_reviewer_severity(self):
        with self.assertRaises(ValueError):
            self.gate(85, llm=[])
        tampered = [{"practice_id": "fx-llm-must", "passed": False, "severity": "should"},
                    {"practice_id": "fx-llm-should", "passed": True}]
        r = self.gate(90, llm=tampered)
        self.assertEqual(r["verdict"], "FAIL")


class Finalize(unittest.TestCase):
    """finalize_review.py: reviewer の返却 JSON を検査し、ゲート判定と record を出す。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = self.tmp.name
        self.practices = write_json(self.d, "p.json", practices_doc(
            [practice("fx-llm-must", severity="must"), practice("fx-llm-should")]))
        self.clarity = write_json(self.d, "c.json", {"axes": [
            {"id": i, "weight": 20, "practice_ids": ["fx-llm-must", "fx-llm-should"]} for i in AXIS_IDS]})
        self.auto = write_json(self.d, "a.json", {"violations": [], "limitations": ["font checked: 1/1 slides"]})

    def tearDown(self):
        self.tmp.cleanup()

    def finalize(self, review):
        rv = write_json(self.d, "r.json", review)
        return run(os.path.join(REVIEW_SCRIPTS, "finalize_review.py"), "--deck", "C:/d/sales2025.pptx",
                   "--auto", self.auto, "--review", rv, "--practices", self.practices, "--clarity", self.clarity,
                   "--reviewed-at", "2026-10-30T10:00:00+09:00")

    def test_T51_pass(self):
        code, out = self.finalize({"axes": axes_of(90), "llm_results": llm_ok(), "fixes": []})
        self.assertEqual(code, 0, out)
        rec = json.loads(out[out.index("{"):])
        self.assertEqual((rec["verdict"], rec["score"], rec["skill"]), ("PASS", 90, "slide-clarity-review"))
        self.assertIn("font checked: 1/1 slides", rec["summary"])

    def test_T52_fail_exit_1(self):
        llm = [{"practice_id": "fx-llm-must", "passed": False}, {"practice_id": "fx-llm-should", "passed": True}]
        code, out = self.finalize({"axes": axes_of(90), "llm_results": llm, "fixes": []})
        self.assertEqual(code, 1, out)
        self.assertIn('"verdict": "FAIL"', out)

    def test_T53_invalid_reviewer_output_exit_3(self):
        code, out = self.finalize({"axes": axes_of(90)[:4], "llm_results": llm_ok()[:1], "fixes": []})
        self.assertEqual(code, 3, out)
        self.assertIn("axes mismatch: missing ax4", out)
        self.assertIn("llm_results missing: fx-llm-should", out)

    def test_T54_extract_includes_paragraphs(self):
        pptx = os.path.join(self.d, "good.pptx")
        build_pptx(pptx, "good")
        facts = os.path.join(self.d, "f.json")
        self.assertEqual(run(EXTRACT, pptx, "-o", facts)[0], 0)
        with open(facts, encoding="utf-8") as f:
            self.assertEqual(json.load(f)["slides"][0]["paragraphs"], ["short body"])


# ================================================================ 点数の導出・text_blocks・日本語の機械検査（2026-11 追加）
JA_CHECK = os.path.join(SKILLS, "slide-japanese-review", "scripts", "check_ja_slide.py")
RENDER = os.path.join(REVIEW_SCRIPTS, "render_deck.py")


class DerivedScoring(unittest.TestCase):
    PRACTICES = [{"id": "fx-must", "severity": "must"}, {"id": "fx-should", "severity": "should"},
                 {"id": "fx-auto", "severity": "should"}]
    CLARITY = {"axes": [{"id": "ax0", "weight": 20, "practice_ids": ["fx-must", "fx-should"]},
                        {"id": "ax1", "weight": 20, "practice_ids": ["fx-auto"]},
                        {"id": "ax2", "weight": 20, "practice_ids": []}]}

    def derive(self, violations, llm):
        import gate
        return {a["id"]: a for a in gate.derive_axes(violations, llm, self.PRACTICES, self.CLARITY)}

    def test_T62_penalties_by_severity_and_kind(self):
        llm = [{"practice_id": "fx-must", "passed": False}, {"practice_id": "fx-should", "passed": False}]
        few = [{"practice_id": "fx-auto", "slide": s} for s in (1, 2)]
        r = self.derive(few, llm)
        self.assertEqual((r["ax0"]["score"], r["ax1"]["score"], r["ax2"]["score"]), (11, 18, 20))
        self.assertEqual(r["ax0"]["basis"], ["fx-must(-6)", "fx-should(-3)"])
        self.assertEqual(r["ax1"]["basis"], ["fx-auto(-2)"])
        many = [{"practice_id": "fx-auto", "slide": s} for s in (1, 2, 3)]
        self.assertEqual(self.derive(many, [])["ax1"]["score"], 16)
        # 同じスライドの重複違反は 1 枚として数える
        dup = [{"practice_id": "fx-auto", "slide": 1}] * 3
        self.assertEqual(self.derive(dup, [])["ax1"]["score"], 18)

    def test_T63_score_never_below_zero(self):
        import gate
        clarity = {"axes": [{"id": "ax0", "weight": 5, "practice_ids": ["fx-must", "fx-should"]}]}
        llm = [{"practice_id": "fx-must", "passed": False}, {"practice_id": "fx-should", "passed": False}]
        self.assertEqual(gate.derive_axes([], llm, self.PRACTICES, clarity)[0]["score"], 0)


class FinalizeScoreMode(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = self.tmp.name
        self.practices = write_json(self.d, "p.json", practices_doc(
            [practice("fx-llm-must", severity="must"), practice("fx-llm-should")]))
        self.clarity = write_json(self.d, "c.json", {"axes": [
            {"id": i, "weight": 20, "practice_ids": ["fx-llm-must", "fx-llm-should"]} for i in AXIS_IDS]})
        self.auto = write_json(self.d, "a.json", {"violations": [], "limitations": []})

    def tearDown(self):
        self.tmp.cleanup()

    def finalize(self, review, *extra):
        rv = write_json(self.d, "r.json", review)
        code, out = run(os.path.join(REVIEW_SCRIPTS, "finalize_review.py"), "--deck", "C:/d/sales2025.pptx",
                        "--auto", self.auto, "--review", rv, "--practices", self.practices, "--clarity", self.clarity,
                        "--reviewed-at", "2026-10-30T10:00:00+09:00", *extra)
        return code, out, json.loads(out[out.index("{"):])

    def llm_should_fail(self):
        return [{"practice_id": "fx-llm-must", "passed": True}, {"practice_id": "fx-llm-should", "passed": False}]

    def test_T64_min_mode_caps_reviewer_score_at_derived(self):
        code, out, rec = self.finalize({"axes": axes_of(95), "llm_results": self.llm_should_fail(), "fixes": []})
        self.assertEqual(rec["score_mode"], "min")
        self.assertEqual(rec["derived_axis_scores"]["ax0"], 17)
        self.assertEqual(rec["reviewer_axis_scores"]["ax0"], 19)
        self.assertEqual(rec["score"], 85)
        self.assertEqual(rec["axis_basis"]["ax0"], ["fx-llm-should(-3)"])
        self.assertIn("導出点を採用した", rec["summary"])
        self.assertEqual(code, 0, out)

    def test_T65_min_mode_keeps_lower_reviewer_score(self):
        code, out, rec = self.finalize({"axes": axes_of(69), "llm_results": self.llm_should_fail(), "fixes": []})
        self.assertEqual(rec["score"], 69)
        self.assertNotIn("導出点を採用した", rec["summary"])
        self.assertEqual(code, 1, out)

    def test_T66_reviewer_mode_is_previous_behaviour(self):
        code, out, rec = self.finalize({"axes": axes_of(95), "llm_results": self.llm_should_fail(), "fixes": []},
                                       "--score-mode", "reviewer")
        self.assertEqual(rec["score"], 95)
        self.assertNotIn("axis_basis", rec)


class TextBlocksAndJapanese(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_T67_text_blocks_include_table_cells_in_position_order(self):
        pptx = os.path.join(self.d, "tg.pptx")
        build_pptx(pptx, "table_group")
        facts = os.path.join(self.d, "f.json")
        self.assertEqual(run(EXTRACT, pptx, "-o", facts)[0], 0)
        with open(facts, encoding="utf-8") as f:
            blocks = json.load(f)["slides"][0]["text_blocks"]
        self.assertEqual([b["kind"] for b in blocks], ["table", "text"])
        self.assertEqual(blocks[0]["rows"], [["aa", "bb"], ["cc", "dd"]])
        self.assertEqual(blocks[1]["paragraphs"], ["group text"])

    def ja(self, slides):
        facts = write_json(self.d, "facts.json", {"file": "x.pptx", "slide_count": len(slides), "slides": slides})
        out = os.path.join(self.d, "ja.json")
        code, text = run(JA_CHECK, facts, "-o", out)
        with open(out, encoding="utf-8") as f:
            return code, {x["check"] for x in json.load(f)["findings"]}, text

    def test_T68_ja_checks_detect_and_stay_quiet(self):
        bad = [{"no": 1, "title": "見出し", "text_blocks": [
                   {"kind": "text", "paragraphs": ["導入を進めます。", "効果が大きいことは確かである。", "TODO 数値を入れる"]},
                   {"kind": "table", "rows": [["(注) 半角", "（注）全角"]]}]},
               {"no": 2, "title": "次の見出し",
                "paragraphs": ["導入の効果を毎月確認しています。", "導入の効果を毎月確認しています。"]}]
        code, checks, text = self.ja(bad)
        self.assertEqual(code, 0, text)
        self.assertTrue({"mixed-register", "b2-candidate", "mixed-paren", "duplicate"} <= checks, checks)
        good = [{"no": 1, "title": "見出し", "text_blocks": [
                    {"kind": "text", "paragraphs": ["月次集計の自動化", "確認作業の削減"]}]}]
        code, checks, text = self.ja(good)
        self.assertEqual((code, checks), (0, set()), text)

    def test_T69_render_reports_missing_renderer_with_exit_2(self):
        env = dict(os.environ, SOFFICE=os.path.join(self.d, "none.exe"), PDFTOPPM=os.path.join(self.d, "none.exe"),
                   PATH=self.d)
        pptx = os.path.join(self.d, "g.pptx")
        build_pptx(pptx, "good")
        p = subprocess.run([sys.executable, RENDER, pptx, "-o", os.path.join(self.d, "img")], capture_output=True,
                           text=True, encoding="utf-8", env=env, cwd=self.d)
        if p.returncode == 0:
            self.skipTest("標準の導入先の描画ソフトで描画できた（欠落の再現はできない）")
        self.assertEqual(p.returncode, 2, p.stderr)
        self.assertIn("描画未確認", p.stderr)


# ================================================================ 適用条件のある観点・設計図 v2・機械検査の追加（2026-11 追加。T70〜）
FINALIZE = os.path.join(REVIEW_SCRIPTS, "finalize_review.py")
COND = {"deck": {"condition": "the deck shows examples"}}
TRIG = {"deck": {"condition": "the deck uses external sources",
                 "auto_trigger": {"any_of": [{"fact": "citation_marker_total", "op": ">=", "value": 1}]}}}


def build_pptx2(path, kind):
    """2026-11 追加の事実（空の枠・重なり・出典番号・章・表の高さ）を確かめる fixture。"""
    from pptx import Presentation
    from pptx.util import Inches, Pt
    prs = Presentation()
    blank, title_only, title_body = prs.slide_layouts[6], prs.slide_layouts[5], prs.slide_layouts[1]

    def tb(slide, text, left, top, width=4, height=1, size=18):
        box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
        box.text_frame.text = text
        for r in box.text_frame.paragraphs[0].runs:
            r.font.size = Pt(size)
        return box

    def titled(title):
        s = prs.slides.add_slide(title_only)
        s.shapes.title.text = title
        return s

    if kind == "placeholders":       # slide1: 本文の枠が空 / slide2: 本文の枠に文字あり
        s1 = prs.slides.add_slide(title_body)
        s1.shapes.title.text = "Empty body"
        s2 = prs.slides.add_slide(title_body)
        s2.shapes.title.text = "Filled body"
        s2.placeholders[1].text = "body text"
    elif kind == "overlap":          # slide1: 文字と表が部分的に重なる / slide2: 包含 / slide3: 文字の無い地の上の文字
        from pptx.enum.shapes import MSO_SHAPE
        s1 = prs.slides.add_slide(blank)
        tb(s1, "partly covered text", 1, 1, 4, 2)
        tbl = s1.shapes.add_table(2, 2, Inches(3), Inches(2), Inches(4), Inches(2)).table
        tbl.cell(0, 0).text = "x"
        s2 = prs.slides.add_slide(blank)
        tb(s2, "outer card text", 1, 1, 6, 4)
        tb(s2, "inner", 2, 2, 2, 1)
        s3 = prs.slides.add_slide(blank)
        s3.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1), Inches(1), Inches(4), Inches(3))
        tb(s3, "text on a plain box", 1.5, 1.5, 4, 2)
    elif kind == "citations":
        s1 = titled("Sales grew")
        tb(s1, "Sales grew last year [1]", 1, 2)
        s2 = titled("Code sample")
        tb(s2, "value = items[1];", 1, 2)
        s3 = titled("Located claim")
        tb(s3, "Costs fell [2]", 1, 2)
        tb(s3, "出典: https://example.com/a", 1, 4)
        s4 = titled("References")
        tb(s4, "[3] Example report, 2025", 1, 2)
        s5 = titled("Listed claim")
        tb(s5, "Usage doubled [3]", 1, 2)
        s6 = titled("Linked claim")
        box = tb(s6, "See the report", 1, 2)
        box.text_frame.paragraphs[0].runs[0].hyperlink.address = "https://example.com/report"
    elif kind == "sections":         # 章 2 つ。「承認」「フロー」が両方の章の見出しに出る
        for t in ("承認フローの基本", "見積もりの作り方", "納品の段取り", "承認フローの例外"):
            titled(t)
        from pptx.oxml import parse_xml
        ids = [s.slide_id for s in prs.slides]
        p14 = "http://schemas.microsoft.com/office/powerpoint/2010/main"
        secs = "".join('<p14:section name="%s" id="{%08d-0000-0000-0000-000000000000}"><p14:sldIdLst>%s</p14:sldIdLst></p14:section>'
                       % (n, i, "".join('<p14:sldId id="%d"/>' % x for x in grp))
                       for i, (n, grp) in enumerate((("A", ids[:2]), ("B", ids[2:]))))
        ext = parse_xml('<p:extLst xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:p14="%s">'
                        '<p:ext uri="{521415D9-36F7-43E2-AB2F-B90AF26B5E84}"><p14:sectionLst>%s</p14:sectionLst></p:ext>'
                        '</p:extLst>' % (p14, secs))
        prs.part._element.append(ext)
    elif kind == "two_slides":
        titled("承認フローの基本")
        titled("承認フローの例外")
    elif kind == "table_overflow":   # 狭い列に長い文 → 推定の高さが下の図形を超える
        s1 = prs.slides.add_slide(blank)
        frame = s1.shapes.add_table(1, 1, Inches(1), Inches(4), Inches(2), Inches(1))
        cell = frame.table.cell(0, 0)
        cell.text = "あ" * 60
        cell.text_frame.paragraphs[0].runs[0].font.size = Pt(18)
        tb(s1, "note below the table", 1, 5.2, 4, 0.5)
    prs.save(path)


class DeckConditionFormat(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def v(self, *ps):
        return run(VALIDATE, "practices", write_json(self.d, "p.json", practices_doc(list(ps))))

    def test_T70_applies_when_deck_format(self):
        self.assertEqual(self.v(practice("fx-a", applies_when=COND), practice("fx-b", applies_when=TRIG))[0], 0)
        for bad, msg in (({"deck": {"condition": " "}}, "applies_when.deck.condition missing"),
                         ({"deck": {"condition": "c", "auto_trigger": {"any_of": [{"fact": "zzz", "op": ">=", "value": 1}]}}},
                          "auto_trigger unknown fact: zzz"),
                         ({"deck": {"condition": "c", "auto_trigger": {"any_of": [{"fact": "slide_count", "op": "<", "value": 1}]}}},
                          "auto_trigger unknown op: <"),
                         ({"deck": {"condition": "c", "auto_trigger": {"any_of": [{"fact": "slide_count", "op": ">=", "value": "8"}]}}},
                          "auto_trigger value must be a number"),
                         ({"deck": {"condition": "c", "extra": 1}}, "applies_when.deck unknown key: extra")):
            code, out = self.v(practice("fx-a", applies_when=bad))
            self.assertEqual(code, 1, out)
            self.assertIn(msg, out)
        code, out = self.v(auto("fx-auto", "deck", "body_chars", "max", 200, applies_when=COND))
        self.assertEqual(code, 1)
        self.assertIn("applies_when.deck is only for llm practices", out)
        # 既存の applies_when（スライド単位）は deck の検査に影響しない
        self.assertEqual(self.v(auto("fx-cs", "deck-spec", "content_source_present", "required",
                                     applies_when={"evidence_type_not_in": ["opinion"]}))[0], 0)

    def test_T71_new_deck_metrics_accepted(self):
        ps = [auto("fx-empty", "deck", "empty_placeholder_count", "max", 0),
              auto("fx-overlap", "deck", "partial_overlap_count", "max", 0)]
        self.assertEqual(self.v(*ps)[0], 0)


class ExtractNewFacts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def facts(self, kind):
        pptx = os.path.join(self.d, kind + ".pptx")
        build_pptx2(pptx, kind)
        out = os.path.join(self.d, kind + ".json")
        code, text = run(EXTRACT, pptx, "-o", out)
        self.assertEqual(code, 0, text)
        with open(out, encoding="utf-8") as f:
            return json.load(f)

    def check(self, kind, practices=None):
        f = os.path.join(self.d, kind + ".json")
        self.facts(kind)
        pp = write_json(self.d, "p.json", practices_doc(practices or [
            auto("fx-empty", "deck", "empty_placeholder_count", "max", 0),
            auto("fx-overlap", "deck", "partial_overlap_count", "max", 0)]))
        out = os.path.join(self.d, kind + ".auto.json")
        code, text = run(CHECK, f, "--practices", pp, "-o", out)
        with open(out, encoding="utf-8") as fh:
            return code, json.load(fh), text

    def test_T72_empty_placeholder(self):
        f = self.facts("placeholders")
        self.assertEqual([s["empty_placeholder_count"] for s in f["slides"]], [1, 0])
        self.assertEqual((f["slide_width"], f["slide_height"]), (10.0, 7.5))
        code, res, text = self.check("placeholders")
        self.assertEqual(code, 1, text)
        self.assertEqual([v["message"] for v in res["violations"]], ["slide 1: fx-empty violated (1 > 0)"])
        self.assertEqual([(c["kind"], c["slide"]) for c in res["candidates"]], [("empty_placeholder", 1)])

    def test_T73_partial_overlap_excludes_containment_and_textless_shapes(self):
        f = self.facts("overlap")
        self.assertEqual([s["partial_overlap_count"] for s in f["slides"]], [1, 0, 0])
        pair = f["slides"][0]["overlap_pairs"][0]
        self.assertEqual((pair["a"].split(":")[0], pair["b"].split(":")[0]), ("text", "table"))
        self.assertEqual(pair["ratio"], 0.25)
        self.assertTrue(any(x.startswith("group shapes not checked for overlap") for x in f["limitations"]))
        code, res, text = self.check("overlap")
        self.assertEqual([(c["kind"], c["slide"]) for c in res["candidates"]], [("partial_overlap", 1)])

    def test_T74_citations_locators_and_orphan_candidates(self):
        f = self.facts("citations")
        cm = [s["citation_markers"] for s in f["slides"]]
        self.assertEqual(cm[0]["markers"], ["[1]"])
        self.assertFalse(cm[0]["has_locator"])
        self.assertEqual(cm[1]["markers"], [])          # コードの中の番号は数えない
        self.assertEqual((cm[2]["url_text_count"], cm[2]["source_label_count"], cm[2]["has_locator"]), (1, 1, True))
        self.assertEqual(f["slides"][5]["hyperlinks"], ["https://example.com/report"])
        self.assertTrue(cm[5]["has_locator"])
        import slide_checks
        totals = slide_checks.deck_fact_totals(f)
        self.assertEqual((totals["citation_marker_total"], totals["hyperlink_total"], totals["url_text_total"],
                          totals["slide_count"], totals["section_count"]), (4, 1, 1, 6, 0))
        code, res, text = self.check("citations")
        orphans = [(c["slide"], c["detail"].split()[0]) for c in res["candidates"] if c["kind"] == "orphan_citations"]
        self.assertEqual(orphans, [(1, "[1]")])         # [3] は参考文献のページにある、[2] は同じページに所在がある

    def test_T75_sections_and_repeated_topic_terms(self):
        f = self.facts("sections")
        self.assertEqual([(s["name"], s["slides"]) for s in f["sections"]], [("A", [1, 2]), ("B", [3, 4])])
        code, res, text = self.check("sections")
        terms = sorted(c["detail"].split("'")[1] for c in res["candidates"] if c["kind"] == "repeated_topic_terms")
        self.assertEqual(terms, ["フロー", "承認"])
        code, res, text = self.check("two_slides")       # 章が無く、2 枚しか離れていない
        self.assertEqual([c for c in res["candidates"] if c["kind"] == "repeated_topic_terms"], [])

    def test_T76_candidates_do_not_change_exit_code(self):
        code, res, text = self.check("placeholders", [auto("fx-body", "deck", "body_chars", "max", 2000)])
        self.assertEqual((code, res["violations"]), (0, []), text)
        self.assertTrue(res["candidates"])
        code, res, text = self.check("sections")
        self.assertTrue(res["candidates"])
        self.assertEqual((code, res["violations"]), (0, []), text)

    def test_T77_table_overflow_candidate(self):
        f = self.facts("table_overflow")
        est = f["slides"][0]["table_estimates"][0]
        self.assertGreater(est["estimated_height"], est["frame_height"])
        self.assertFalse(est["font_assumed"])
        code, res, text = self.check("table_overflow")
        self.assertEqual([c["kind"] for c in res["candidates"]], ["table_overflow"])
        self.assertEqual(res["violations"], [])           # 候補は点数に入れない（表は枠の高さで重なりを判定）


class NotApplicable(unittest.TestCase):
    PRACTICES = [practice("fx-plain"), practice("fx-cond", applies_when=COND),
                 practice("fx-trig", applies_when=TRIG), practice("fx-must-cond", severity="must", applies_when=COND)]

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = self.tmp.name
        self.practices = write_json(self.d, "p.json", practices_doc(self.PRACTICES))
        self.clarity = write_json(self.d, "c.json", {"axes": [
            {"id": i, "weight": 20, "practice_ids": [p["id"] for p in self.PRACTICES]} for i in AXIS_IDS]})
        self.auto = write_json(self.d, "a.json", {"violations": [], "limitations": []})

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def ok(**over):
        res = {p["id"]: {"practice_id": p["id"], "passed": True} for p in NotApplicable.PRACTICES}
        res.update(over)
        return list(res.values())

    @staticmethod
    def na(pid, reason="the deck has no examples"):
        return {"practice_id": pid, "applicable": False, "reason": reason}

    def finalize(self, llm, *extra, axes=None):
        rv = write_json(self.d, "r.json", {"axes": axes or axes_of(95), "llm_results": llm, "fixes": []})
        code, out = run(FINALIZE, "--deck", os.path.join(self.d, "none.pptx"), "--auto", self.auto, "--review", rv,
                        "--practices", self.practices, "--clarity", self.clarity,
                        "--reviewed-at", "2026-11-06T10:00:00+09:00", *extra)
        return code, out

    def facts(self, markers):
        return write_json(self.d, "f.json", {"slide_count": 2, "slides": [
            {"no": 1, "citation_markers": {"markers": markers, "url_text_count": 0, "source_label_count": 0,
                                           "has_locator": False}}]})

    def test_T78_only_conditional_practices_and_reason_required(self):
        import gate
        errs = gate.validate_llm_results(self.ok(**{"fx-plain": self.na("fx-plain")}), self.PRACTICES)
        self.assertIn("not applicable not allowed: fx-plain", errs)
        errs = gate.validate_llm_results(self.ok(**{"fx-cond": self.na("fx-cond", " ")}), self.PRACTICES)
        self.assertIn("reason required for not applicable: fx-cond", errs)
        bad = dict(self.na("fx-cond"), passed=True)
        self.assertIn("passed must be omitted when not applicable: fx-cond",
                      gate.validate_llm_results(self.ok(**{"fx-cond": bad}), self.PRACTICES))
        self.assertIn("applicable must be bool: fx-cond", gate.validate_llm_results(
            self.ok(**{"fx-cond": {"practice_id": "fx-cond", "applicable": "no", "reason": "r"}}), self.PRACTICES))
        self.assertEqual(gate.validate_llm_results(self.ok(**{"fx-cond": self.na("fx-cond")}), self.PRACTICES), [])
        code, out = self.finalize(self.ok(**{"fx-plain": self.na("fx-plain")}))
        self.assertEqual(code, 3, out)

    def test_T79_auto_trigger_is_checked_against_facts(self):
        llm = self.ok(**{"fx-trig": self.na("fx-trig", "no external sources")})
        code, out = self.finalize(llm)
        self.assertEqual(code, 3, out)
        self.assertIn("--facts required to mark fx-trig not applicable", out)
        code, out = self.finalize(llm, "--facts", self.facts(["[1]"]))
        self.assertEqual(code, 3, out)
        self.assertIn("fx-trig cannot be not applicable (auto_trigger holds: citation_marker_total >= 1)", out)
        code, out = self.finalize(llm, "--facts", self.facts([]))
        self.assertEqual(code, 0, out)

    def test_T80_not_applicable_is_not_penalized_and_recorded(self):
        import gate
        llm = self.ok(**{"fx-cond": self.na("fx-cond"), "fx-must-cond": self.na("fx-must-cond")})
        derived = gate.derive_axes([], llm, self.PRACTICES, {"axes": [{"id": "ax0", "weight": 20,
                                                                        "practice_ids": ["fx-cond", "fx-must-cond"]}]})
        self.assertEqual((derived[0]["score"], derived[0]["basis"]), (20, []))
        g = gate.compute_gate([], llm, self.PRACTICES, axes_of(95))
        self.assertEqual(g["verdict"], "PASS")           # must の対象外は must の不合格に数えない
        code, out = self.finalize(llm)
        self.assertEqual(code, 0, out)
        rec = json.loads(out[out.index("{"):])
        self.assertEqual(rec["not_applicable"], [{"practice_id": "fx-cond", "reason": "the deck has no examples"},
                                                 {"practice_id": "fx-must-cond", "reason": "the deck has no examples"}])
        self.assertEqual(rec["derived_axis_scores"]["ax0"], 20)
        self.assertIn("対象外: fx-cond, fx-must-cond", rec["summary"])
        # 同じ観点を不合格にすると減点される（対象外と合格は同じ点、不合格だけが下がる）
        code, out = self.finalize(self.ok(**{"fx-cond": {"practice_id": "fx-cond", "passed": False}}))
        self.assertEqual(json.loads(out[out.index("{"):])["derived_axis_scores"]["ax0"], 17)

    def test_T81_citation_prefix(self):
        llm = self.ok(**{"fx-cond": self.na("fx-cond")})
        axes = axes_of(95)
        axes[0]["citations"] = ["[fx-cond] slide 4: the improved screen comes first"]
        self.assertEqual(self.finalize(llm, axes=axes)[0], 3)
        axes[0]["citations"] = ["[fx-zzz] slide 4: unknown"]
        code, out = self.finalize(self.ok(), axes=axes)
        self.assertEqual(code, 3, out)
        self.assertIn("unknown practice in citation prefix: fx-zzz", out)
        for ok_cite in ("[1] has no locator on slide 3", "slide 4: plain citation", "[fx-plain] slide 2: fine"):
            axes[0]["citations"] = [ok_cite]
            code, out = self.finalize(llm, axes=axes)
            self.assertEqual(code, 0, ok_cite + out)


class RecordHashAndHistory(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = self.tmp.name
        self.practices = write_json(self.d, "p.json", practices_doc(
            [practice("fx-llm-must", severity="must"), practice("fx-llm-should")]))
        self.clarity = write_json(self.d, "c.json", {"axes": [
            {"id": i, "weight": 20, "practice_ids": ["fx-llm-must", "fx-llm-should"]} for i in AXIS_IDS]})
        self.auto = write_json(self.d, "a.json", {"violations": [], "limitations": []})
        self.deck = os.path.join(self.d, "deck.pptx")
        build_pptx(self.deck, "good")
        self.history = os.path.join(self.d, "history")

    def tearDown(self):
        self.tmp.cleanup()

    def finalize(self, deck, llm, *extra):
        rv = write_json(self.d, "r.json", {"axes": axes_of(90), "llm_results": llm, "fixes": []})
        return run(FINALIZE, "--deck", deck, "--auto", self.auto, "--review", rv, "--practices", self.practices,
                   "--clarity", self.clarity, "--reviewed-at", "2026-11-06T10:00:00+09:00", *extra)

    def saved(self):
        folder = os.path.join(self.history, "slide-clarity-review")
        return sorted(os.listdir(folder)) if os.path.isdir(folder) else []

    def test_T82_sha256_in_record_or_hash_not_computed(self):
        code, out = self.finalize(self.deck, llm_ok())
        rec = json.loads(out[out.index("{"):])
        with open(self.deck, "rb") as f:
            self.assertEqual(rec["target"]["sha256"], hashlib.sha256(f.read()).hexdigest())
        self.assertEqual(rec["not_applicable"], [])
        self.assertNotIn("hash not computed", rec["summary"])
        code, out = self.finalize(os.path.join(self.d, "missing.pptx"), llm_ok())
        self.assertEqual(code, 0, out)                     # 読めなくても終了コードは変えない
        rec = json.loads(out[out.index("{"):])
        self.assertIsNone(rec["target"]["sha256"])
        self.assertIn("hash not computed", rec["summary"])

    def test_T83_history_root_and_verify_latest(self):
        code, out = self.finalize(self.deck, llm_ok(), "--write", "--history-root", self.history)
        self.assertEqual(code, 0, out)
        self.assertEqual(len(self.saved()), 1)
        self.assertRegex(self.saved()[0], r"^\d{8}-\d{6}__slide-clarity-deck-deck\.json$")
        code, out = run(FINALIZE, "--verify-latest", self.deck, "--history-root", self.history)
        self.assertEqual(code, 0, out)
        self.assertIn("PASS record found", out)
        other = os.path.join(self.d, "other.pptx")
        build_pptx(other, "dense")
        code, out = run(FINALIZE, "--verify-latest", other, "--history-root", self.history)
        self.assertEqual(code, 1, out)
        self.assertIn("no record for this version", out)
        fail = [{"practice_id": "fx-llm-must", "passed": False}, {"practice_id": "fx-llm-should", "passed": True}]
        self.assertEqual(self.finalize(other, fail, "--write", "--history-root", self.history)[0], 1)
        code, out = run(FINALIZE, "--verify-latest", other, "--history-root", self.history)
        self.assertEqual(code, 1, out)
        self.assertIn("only FAIL", out)
        # 採点の引数と一緒には使えない（終了コード 2）。採点の必須引数が欠けても 2
        self.assertEqual(run(FINALIZE, "--verify-latest", self.deck, "--deck", self.deck)[0], 2)
        self.assertEqual(run(FINALIZE, "--verify-latest", self.deck, "--write")[0], 2)
        self.assertEqual(run(FINALIZE, "--deck", self.deck)[0], 2)

    def test_T84_both_save_paths_reject_the_same_invalid_record(self):
        import append_review_record
        import finalize_review
        bad = {"schema": "review-record/v1", "skill": "slide-clarity-review", "reviewed_at": "2026-11-06T10:00:00+09:00",
               "target": {"description": ""}, "verdict": "PASS", "summary": "s", "criteria": [{"id": "ax0"}]}
        self.assertTrue(append_review_record.validate(bad))
        path, errors = finalize_review.save_record(bad, self.history)
        self.assertIsNone(path)
        self.assertEqual(sorted(errors), sorted(append_review_record.validate(bad)))
        self.assertEqual(self.saved(), [])
        p = subprocess.run([sys.executable, os.path.join(HERE, "append_review_record.py"), "-"],
                           input=json.dumps(bad), capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(p.returncode, 1, p.stderr)
        self.assertIn("REJECTED", p.stderr)


class DeckSpecV2(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def spec(self, spec):
        pp = write_json(self.d, "p.json", practices_doc(fx_deck_practices()))  # 新しい観点の practice は無い
        return run(VALIDATE, "deck-spec", write_json(self.d, "s.json", spec), "--practices", pp)

    @staticmethod
    def v2(**top):
        s = good_spec()
        s["spec_version"] = 2
        for sl in s["slides"]:
            if sl["role"] == "content":
                sl["intent"] = "show how the numbers changed in the trial"
        s.update(top)
        return s

    def test_T85_v1_is_unchanged_and_empty_source_list_is_missing(self):
        s = good_spec()
        self.assertNotIn("intent", s["slides"][1])
        self.assertEqual(self.spec(s)[0], 0)                       # v1: 構造の検査は動かない
        s["slides"][1]["example"] = {"id": "e1", "steps": ["after"]}
        self.assertEqual(self.spec(s)[0], 0)
        for empty in ([], ["", " "]):
            s = good_spec()
            s["slides"][2]["content_source"] = empty
            code, out = self.spec(s)
            self.assertEqual(code, 1, empty)
            self.assertIn("slide 3: fx-content-source violated (content_source_present required)", out)
        s = good_spec()
        s["slides"][2]["content_source"] = ["https://example.com/a", "https://example.com/b"]
        self.assertEqual(self.spec(s)[0], 0)
        s["spec_version"] = 3
        self.assertIn("invalid spec_version", self.spec(s)[1])

    def test_T86_v2_intent_required_on_content_only(self):
        self.assertEqual(self.spec(self.v2())[0], 0)
        s = self.v2()
        s["slides"][1]["intent"] = " "
        code, out = self.spec(s)
        self.assertEqual(code, 1)
        self.assertIn("slide 2: intent missing (purpose-and-premise)", out)
        self.assertNotIn("slide 1: intent", out)
        s = self.v2()
        s["slides"][1]["content_source"] = ["https://example.com/a", ""]
        self.assertIn("slide 2: content_source has an empty entry (source-locator-visible)", self.spec(s)[1])

    def test_T87_v2_sections(self):
        s = self.v2(sections=[{"id": "s1", "theme": "Approval steps"}, {"id": "s2", "theme": "approval  steps"}])
        s["slides"][1]["section"] = "s9"
        code, out = self.spec(s)
        self.assertEqual(code, 1)
        self.assertIn("sections: duplicate theme 'approval  steps' in s1 and s2 (one-topic-one-place)", out)
        self.assertIn("slide 2: unknown section s9 (one-topic-one-place)", out)
        s = self.v2(sections=[{"id": "s1", "theme": "Approval steps"}, {"id": "s2", "theme": "Cost"}])
        s["slides"][1]["section"] = "s1"
        self.assertEqual(self.spec(s)[0], 0)

    def test_T88_v2_examples(self):
        def with_examples(e2, e3):
            s = self.v2()
            s["slides"][1]["example"], s["slides"][2]["example"] = e2, e3
            return s
        good = with_examples({"id": "e1", "pattern": "before-after", "steps": ["before", "result"],
                              "conditions": "ten offices, one month", "cause": "new form"},
                             {"id": "e1", "steps": ["after", "effect"], "effect": "inquiries halved",
                              "cause": "new form"})
        self.assertEqual(self.spec(good)[0], 0, self.spec(good)[1])
        cases = [
            (with_examples({"id": "e1", "pattern": "before-after", "steps": ["after"]},
                           {"id": "e1", "steps": ["before", "result"], "conditions": "c", "effect": "x"}),
             "example e1: before must come before after (before-after-order)"),
            (with_examples({"id": "e1", "pattern": "good-bad", "steps": ["before", "after"]}, None),
             "example e1: effect missing (before-after-order)"),
            (with_examples({"id": "e1", "pattern": "before-after", "steps": ["before", "after"], "effect": "x"}, None),
             "example e1: result required for before-after (before-after-order)"),
            (with_examples({"id": "e1", "pattern": "good-bad", "steps": ["before"], "cause": "form"},
                           {"id": "e1", "steps": ["after"], "effect": "x", "cause": "reviewer"}),
             "example e1: multiple causes (one-example-one-cause)"),
            (with_examples({"id": "e1", "pattern": "before-after", "steps": ["before", "result"]},
                           {"id": "e1", "steps": ["after"], "effect": "x"}),
             "slide 2: example e1 conditions missing (example-matches-conditions)"),
        ]
        for spec, msg in cases:
            code, out = self.spec(spec)
            self.assertEqual(code, 1, msg)
            self.assertIn(msg, out)
        # good-bad では result を求めない
        ok = with_examples({"id": "e1", "pattern": "good-bad", "steps": ["before", "after"], "effect": "x"}, None)
        self.assertEqual(self.spec(ok)[0], 0)

    def test_T89_v2_exhibits(self):
        s = self.v2(exhibits=[{"id": "x1", "kind": "config", "full_text_at": 9}, {"id": "x2", "kind": "prompt"}])
        s["slides"][1]["exhibit_ref"] = "x3"
        code, out = self.spec(s)
        self.assertEqual(code, 1)
        self.assertIn("exhibit x1: full_text_at slide 9 not found (reproducible-material-complete)", out)
        self.assertIn("exhibit x2: full_text_at missing (reproducible-material-complete)", out)
        self.assertIn("slide 2: unknown exhibit x3 (reproducible-material-complete)", out)
        s = self.v2(exhibits=[{"id": "x1", "kind": "config", "full_text_at": "handout: settings file"}])
        s["slides"][1]["exhibit_ref"] = ["x1"]
        self.assertEqual(self.spec(s)[0], 0)

    def test_T90_v2_appendix_order_and_reference_section(self):
        def deck(roles):
            s = self.v2()
            slides = []
            for i, r in enumerate(roles, 1):
                role, _, kind = r.partition(":")
                sl = good_slide(i, role, intent="i")
                if kind:
                    sl["kind"] = kind
                if role in ("closing", "section", "appendix"):
                    sl.update(evidence_type="proposal", content_source=None, focal_element="title")
                slides.append(sl)
            s["slides"] = slides
            return self.spec(s)
        self.assertEqual(deck(["content", "closing", "section:reference", "appendix", "appendix"])[0], 0)
        for roles, msg in (
                (["content", "closing", "appendix", "content"], "slide 4: content after appendix (main-before-reference)"),
                (["content", "appendix", "closing"], "closing must come before the first appendix (main-before-reference)"),
                (["content", "closing", "section:reference"], "slide 3: reference section without appendix"),
                (["content", "section:reference", "closing", "appendix"],
                 "slide 2: reference section must be after the last closing and before the first appendix"),
                (["content:main", "closing"], "slide 1: kind is only for role section")):
            code, out = deck(roles)
            self.assertEqual(code, 1, roles)
            self.assertIn(msg, out)

    def test_T91_v2_glossary_first_use(self):
        s = self.v2(glossary=[{"term": "Sales", "definition": "revenue", "first_slide": 3}])
        code, out = self.spec(s)
        self.assertEqual(code, 1)
        self.assertIn("glossary 'Sales': used on slide 1 before first_slide 3 (terms-and-references)", out)
        s = self.v2(glossary=[{"term": "Sales", "definition": "revenue", "first_slide": 1}])
        self.assertEqual(self.spec(s)[0], 0)
        s = self.v2(glossary=[{"term": "Sales", "first_slide": 1}])
        self.assertIn("glossary: term, definition and first_slide required", self.spec(s)[1])


# ================================================================ 公開リポジトリのポリシー
class PublicRepoPolicy(unittest.TestCase):
    TARGETS = ["slide-composition-planner", "slide-clarity-review", "slide-japanese-review", "_shared/slide-sources"]
    FILES = ["_shared/slide-best-practices.json", "_shared/scripts/slide_checks.py",
             "_shared/scripts/validate_slide_data.py"]

    def files(self):
        out = []
        for t in self.TARGETS:
            for root, _, names in os.walk(os.path.join(SKILLS, t)):
                out += [os.path.join(root, n) for n in names if n.endswith((".md", ".json", ".py"))]
        out += [os.path.join(SKILLS, f) for f in self.FILES if os.path.exists(os.path.join(SKILLS, f))]
        return out

    def test_T49_no_brand_hex_colors(self):
        pat = re.compile(r"#(?!(?:FFFFFF|000000)\b)[0-9A-Fa-f]{6}\b", re.I)  # 白・黒は中立色なので対象外
        for p in self.files():
            if p.endswith("palette.example.json") or os.path.basename(p) == "fetch-log.json":
                continue
            with open(p, encoding="utf-8") as f:
                self.assertIsNone(pat.search(f.read()), p)

    def test_T50_no_internal_skill_or_company_names(self):
        # 公開リポジトリに社名の綴りを残さないため、禁止語は分割して組み立てる（社内向け生成 skill 名・社名・略称が対象）
        pat = re.compile("|".join(["n" + "ec-", r"\b" + "N" + "EC" + r"\b", "日本" + "電気"]), re.I)
        for p in self.files():
            with open(p, encoding="utf-8") as f:
                self.assertIsNone(pat.search(f.read()), p)


if __name__ == "__main__":
    unittest.main()
