#!/usr/bin/env python3
"""test_make_square_cards.py — make_square_cards.py の試験（unittest）。

実行: python3 .claude/skills/sns-square-slides/scripts/test_make_square_cards.py
期待値は criteria/card-rules.json の数値と、設計（検査 C1〜C7・投稿文の数え方・画像化の手順・終了コード）から導く。
偽の道具（実行可能な shell script）を使う試験は Windows では skip する。実物の soffice・pdftoppm・python-pptx が無い時は、
それを要る試験だけ skip する。
"""
import copy
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
SCRIPT = os.path.join(HERE, "make_square_cards.py")
RULES_PATH = os.path.join(SKILL, "criteria", "card-rules.json")
EXAMPLE_PATH = os.path.join(SKILL, "examples", "cards.example.json")
RENDER_DECK = os.path.normpath(os.path.join(SKILL, "..", "slide-clarity-review", "scripts", "render_deck.py"))

spec = importlib.util.spec_from_file_location("make_square_cards", SCRIPT)
msc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(msc)

with open(RULES_PATH, encoding="utf-8") as f:
    RULES = json.load(f)
with open(EXAMPLE_PATH, encoding="utf-8") as f:
    EXAMPLE = json.load(f)

try:
    import pptx  # noqa: F401
    HAS_PPTX = True
except ImportError:
    HAS_PPTX = False

IS_WINDOWS = os.name == "nt"
REAL_SOFFICE = shutil.which("soffice") or os.environ.get("SOFFICE")
REAL_PDFTOPPM = shutil.which("pdftoppm") or os.environ.get("PDFTOPPM")


def ex():
    return copy.deepcopy(EXAMPLE)


def codes(violations):
    return [v.split(" ", 1)[0] for v in violations]


def check(cfg, ref_roles=None, rules=RULES):
    return msc.check_config(cfg, rules, ref_roles)


def minimal_jpeg(width, height, marker=0xC0):
    """SOI + APP0 + SOFn（高さ・幅）+ EOI の最小のバイト列（復号はできないが、大きさの読み取りには足りる）。"""
    app0 = b"\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    sof = bytes([0xFF, marker, 0x00, 0x11, 0x08]) + height.to_bytes(2, "big") + width.to_bytes(2, "big") \
        + b"\x03\x01\x22\x00\x02\x11\x01\x03\x11\x01"
    return b"\xff\xd8" + app0 + sof + b"\xff\xd9"


# ---------------------------------------------------------------- 7.1 検査
def kinds(violations):
    """違反の記号の種類（重複を除き並べたもの）。1 か所の変更で複数行が正当に出る配色の C4 の試験だけに使う。"""
    return sorted(set(codes(violations)))


class TestCheckConfig(unittest.TestCase):
    def assertOnly(self, cfg, expected, ref_roles=None, rules=RULES):
        """1 か所だけを変えた入力の違反の記号の列を、重複も含めて完全一致で確かめる。"""
        v, _ = check(cfg, ref_roles=ref_roles, rules=rules)
        self.assertEqual(codes(v), expected, v)

    def assertKinds(self, cfg, expected):
        """配色のように 1 か所の変更で複数行の違反が正当に出る時だけ、記号の種類で確かめる。"""
        v, _ = check(cfg)
        self.assertEqual(kinds(v), expected, v)

    def assertClean(self, cfg, ref_roles=None):
        v, _ = check(cfg, ref_roles=ref_roles)
        self.assertEqual(v, [])

    def test_見本の設定は違反なしで通る(self):
        v, w = check(ex())
        self.assertEqual(v, [])
        self.assertEqual(w, [])

    def test_カードが3枚のときC1(self):
        c = ex(); del c["cards"][3]
        self.assertOnly(c, ["C1"])

    def test_カードが5枚のときC1(self):
        c = ex(); c["cards"].append(copy.deepcopy(c["cards"][1]))
        self.assertOnly(c, ["C1"])

    def test_cardsが配列でなければC1(self):
        c = ex(); c["cards"] = {}
        self.assertOnly(c, ["C1"])

    def test_cardsが空ならC1(self):
        c = ex(); c["cards"] = []
        self.assertOnly(c, ["C1"])

    def test_C1があればC2は出ない(self):
        c = ex(); del c["cards"][3]; c["cards"][2]["role"] = "close"
        self.assertOnly(c, ["C1"])

    def test_roleの並びが違うときC2(self):
        c = ex(); c["cards"][3]["role"] = "evidence"
        self.assertOnly(c, ["C2"])

    def test_titleが空のときC3(self):
        c = ex(); c["cards"][1]["title"] = ""
        self.assertOnly(c, ["C3"])

    def test_titleキーが無いとC3(self):
        c = ex(); del c["cards"][1]["title"]
        self.assertOnly(c, ["C3"])

    def test_bodyは省略できる(self):
        c = ex(); del c["cards"][3]["body"]
        self.assertClean(c)

    def test_titleは上限ちょうどで通り1字超えるとC3(self):
        n = RULES["limits"]["title_max"]
        c = ex(); c["cards"][0]["title"] = "あ" * n
        self.assertClean(c)
        c["cards"][0]["title"] = "あ" * (n + 1)
        self.assertOnly(c, ["C3"])
        v = check(c)[0]
        self.assertIn("card 1", v[0]); self.assertIn("title", v[0])

    def test_改行は文字数に数えない(self):
        c = ex(); c["cards"][0]["title"] = "あ" * RULES["limits"]["title_max"] + "\n"
        self.assertClean(c)

    def test_NFCに正規化して数える(self):
        n = RULES["limits"]["title_max"]
        c = ex(); c["cards"][0]["title"] = "か\u3099" * n
        self.assertClean(c)
        c["cards"][0]["title"] = "か\u3099" * (n + 1)
        self.assertOnly(c, ["C3"])

    def test_bodyは上限ちょうどで通り1字超えるとC3(self):
        n = RULES["limits"]["body_max"]
        c = ex(); c["cards"][0]["body"] = "あ" * n
        self.assertClean(c)
        c["cards"][0]["body"] = "あ" * (n + 1)
        self.assertOnly(c, ["C3"])

    def test_noteは上限ちょうどで通り1字超えるとC3(self):
        n = RULES["limits"]["note_max"]
        c = ex(); c["cards"][1]["note"] = "あ" * n
        self.assertClean(c)
        c["cards"][1]["note"] = "あ" * (n + 1)
        self.assertOnly(c, ["C3"])

    def test_labelは上限ちょうどで通り1字超えるとC3(self):
        n = RULES["limits"]["label_max"]
        c = ex(); c["label"] = "a" * n
        self.assertClean(c)
        c["label"] = "a" * (n + 1)
        self.assertOnly(c, ["C3"])

    def test_titleが目安を超え上限以下なら警告だけ(self):
        c = ex(); c["cards"][0]["title"] = "あ" * (RULES["limits"]["title_recommended"] + 1)
        v, w = check(c)
        self.assertEqual(v, [])
        self.assertEqual(len(w), 1, w)
        self.assertIn("card 1", w[0]); self.assertIn("title", w[0])

    def test_bodyが目安を超え上限以下なら警告だけ(self):
        c = ex(); c["cards"][0]["body"] = "あ" * (RULES["limits"]["body_recommended"] + 1)
        v, w = check(c)
        self.assertEqual(v, [])
        self.assertEqual(len(w), 1, w)
        self.assertIn("card 1", w[0]); self.assertIn("body", w[0])

    def test_明暗差が足りない配色はC4(self):
        c = ex(); c["palette"] = {"text-primary": "#777777", "surface-1": "#888888"}
        self.assertKinds(c, ["C4"])

    def test_白黒の配色は通る(self):
        c = ex(); c["palette"] = {"text-primary": "#000000", "surface-1": "#FFFFFF", "surface-2": "#FFFFFF",
                                  "text-secondary": "#000000", "focus": "#FFFFFF"}
        self.assertClean(c)

    def test_暗い地のラベルだけ明暗差が足りないとC4(self):
        c = ex(); c["palette"] = {"focus": "#1F3FBF"}
        v = check(c)[0]
        self.assertEqual(codes(v), ["C4"], v)

    def test_既定の配色で使う役割が欠けるとC5(self):
        rules = copy.deepcopy(RULES); del rules["default_palette"]["roles"]["focus"]
        self.assertOnly(ex(), ["C5"], rules=rules)

    def test_色がRRGGBBでないとC5でC4は出ない(self):
        c = ex(); c["palette"] = {"surface-1": "white"}
        self.assertOnly(c, ["C5"])

    def test_paletteはpalette_refの上に重なる(self):
        ref = dict(RULES["default_palette"]["roles"]); ref["focus"] = "#111111"
        c = ex(); c["palette"] = {"focus": "#222222"}
        roles, v = msc.resolve_palette(c, ref, RULES)
        self.assertEqual(v, [])
        self.assertEqual(roles["focus"], "#222222")
        self.assertEqual(roles["surface-1"], ref["surface-1"])

    def test_palette_refがあると既定を混ぜない(self):
        ref = dict(RULES["default_palette"]["roles"]); del ref["focus"]
        self.assertOnly(ex(), ["C5"], ref_roles=ref)

    def test_palette_refの使わない役割は無視する(self):
        ref = dict(RULES["default_palette"]["roles"]); ref["border"] = "#C3CAD6"
        self.assertClean(ex(), ref_roles=ref)

    def test_palette_refが無いと入力の誤り(self):
        d = tempfile.mkdtemp(prefix="sns_cards_ref_")
        try:
            c = ex(); c["palette_ref"] = "no-such-palette.json"
            with self.assertRaises(msc.InputError):
                msc.load_palette_ref(c, d)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_palette_refが壊れたJSONなら入力の誤り(self):
        d = tempfile.mkdtemp(prefix="sns_cards_ref_")
        try:
            with open(os.path.join(d, "p.json"), "w") as f:
                f.write("{")
            c = ex(); c["palette_ref"] = "p.json"
            with self.assertRaises(msc.InputError):
                msc.load_palette_ref(c, d)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_許されないキーはC7(self):
        cases = {"card": lambda c: c["cards"][0].__setitem__("titel", "x"),
                 "top": lambda c: c.__setitem__("bg_color", "#000000"),
                 "palette": lambda c: c.__setitem__("palette", {"border": "#000000"})}
        for name, mutate in cases.items():
            with self.subTest(name):
                c = ex(); mutate(c)
                self.assertOnly(c, ["C7"])

    def test_型の誤りはC7でその項目の他の検査は出ない(self):
        cases = {"page_numbers": lambda c: c.__setitem__("page_numbers", "yes"),
                 "title": lambda c: c["cards"][0].__setitem__("title", 123),
                 "post.text": lambda c: c["post"].__setitem__("text", ["a"])}
        for name, mutate in cases.items():
            with self.subTest(name):
                c = ex(); mutate(c)
                self.assertOnly(c, ["C7"])

    def test_objectでないカードはC7だけ(self):
        c = ex(); c["cards"][2] = "a"
        self.assertOnly(c, ["C7"])

    def test_postのtextが空ならC6(self):
        c = ex(); c["post"]["text"] = ""
        self.assertOnly(c, ["C6"])

    def test_補足の所在が無いとC6(self):
        c = ex(); del c["post"]["supplement_source"]
        self.assertOnly(c, ["C6"])

    def test_countが未知ならC6で長さは数えない(self):
        c = ex(); c["post"]["count"] = "threads"; c["post"]["text"] = "あ" * 200
        v = check(c)[0]
        self.assertEqual(codes(v), ["C6"], v)

    def test_countにdefaultは使えない(self):
        c = ex(); c["post"]["count"] = "default"
        self.assertOnly(c, ["C6"])

    def _post(self, text, count=None):
        c = ex(); c["post"]["text"] = text
        if count:
            c["post"]["count"] = count
        return check(c)[0]

    def test_xで上限ちょうどは通り超えるとC6(self):
        self.assertEqual(self._post("あ" * 140), [])
        self.assertEqual(codes(self._post("あ" * 141)), ["C6"])

    def test_xでは半角は1と数える(self):
        self.assertEqual(self._post("a" * 280), [])
        self.assertEqual(codes(self._post("a" * 281)), ["C6"])

    def test_xの投稿文もNFCで数える(self):
        self.assertEqual(self._post("か\u3099" * 140), [])

    def test_xではURLを23と数える(self):
        url = "https://example.com/" + "a" * 100
        self.assertEqual(self._post("あ" * 128 + " " + url), [])
        self.assertEqual(codes(self._post("あ" * 129 + " " + url)), ["C6"])

    def test_行数はCRLFを1つと数え末尾の改行も数える(self):
        c = ex(); c["cards"][0]["title"] = "あ\r\nい\r\nう"
        self.assertClean(c)
        c["cards"][0]["title"] = "あ\nい\nう\n"
        self.assertOnly(c, ["C3"])

    def test_titleの行数は上限ちょうどで通り超えるとC3(self):
        n = RULES["limits"]["title_max_lines"]
        c = ex(); c["cards"][0]["title"] = "\n".join("あいうえおか"[:n])
        self.assertClean(c)
        c["cards"][0]["title"] = "\n".join("あいうえおか"[:n + 1])
        self.assertOnly(c, ["C3"])

    def test_bodyの行数は上限ちょうどで通り超えるとC3(self):
        n = RULES["limits"]["body_max_lines"]
        c = ex(); c["cards"][0]["body"] = "\n".join(["あ"] * n)
        self.assertClean(c)
        c["cards"][0]["body"] = "\n".join(["あ"] * (n + 1))
        self.assertOnly(c, ["C3"])

    def test_charsで上限ちょうどは通り超えるとC6(self):
        self.assertEqual(self._post("あ" * 140, "chars"), [])
        self.assertEqual(codes(self._post("あ" * 141, "chars")), ["C6"])
        self.assertEqual(self._post("あ" * 139 + "\n", "chars"), [])
        self.assertEqual(codes(self._post("あ" * 140 + "\n", "chars")), ["C6"])

    def test_投稿文がカードのtitleを丸ごと含むとC6(self):
        c = ex(); c["post"]["text"] = c["cards"][0]["title"] + c["post"]["text"]
        self.assertOnly(c, ["C6"])

    def test_noteの写しもC6(self):
        c = ex(); c["post"]["text"] = c["post"]["text"] + c["cards"][1]["note"]
        self.assertOnly(c, ["C6"])

    def test_bodyの1行の写しもC6(self):
        c = ex(); c["cards"][2]["body"] = "4月: 平均5.0日\n受付から完了の登録までの平均"
        c["post"]["text"] = "受付から完了の登録までの平均を見ました。" + c["post"]["text"]
        self.assertOnly(c, ["C6"])

    def test_改行と空白は除いて照合する(self):
        c = ex(); c["cards"][1]["body"] = "受付 担当を\n1人に固定"
        c["post"]["text"] = "受付担当を1人に固定しました。" + c["post"]["text"]
        self.assertOnly(c, ["C6"])

    def test_copy_min_charsちょうどの一致はC6で1字少なければ違反にしない(self):
        n = RULES["copy_min_chars"]
        c = ex(); c["cards"][3]["title"] = "い" * n
        c["post"]["text"] = "い" * n + c["post"]["text"]
        self.assertOnly(c, ["C6"])
        c = ex(); c["cards"][3]["title"] = "い" * (n - 1)
        c["post"]["text"] = "い" * (n - 1) + c["post"]["text"]
        self.assertClean(c)

    def test_postが無ければ投稿文の検査をしない(self):
        c = ex(); del c["post"]
        self.assertClean(c)

    def test_schemeの無いドメイン名は警告(self):
        c = ex(); c["post"]["text"] = c["post"]["text"] + "example.com"
        v, w = check(c)
        self.assertEqual(v, [])
        self.assertEqual(len(w), 1, w)
        self.assertIn("URL", w[0])


# ---------------------------------------------------------------- 7.2 長さと明暗差
class TestLengthAndContrast(unittest.TestCase):
    def test_全角1字は2で半角1字は1(self):
        self.assertEqual(msc.post_length("あ", "x", RULES), 2)
        self.assertEqual(msc.post_length("a", "x", RULES), 1)

    def test_xではURLの後に続く日本語をURLに含めない(self):
        self.assertEqual(msc.post_length("詳細は" + "https://example.com/a" + "を見てください", "x", RULES), 3 * 2 + 23 + 7 * 2)

    def test_U2010の記号は1(self):
        self.assertEqual(msc.post_length("‐", "x", RULES), 1)

    def test_charsは改行も1と数える(self):
        self.assertEqual(msc.post_length("あ\nい", "chars", RULES), 3)

    def test_黒と白の明暗差は21(self):
        self.assertAlmostEqual(msc.contrast_ratio("#000000", "#FFFFFF"), 21.0, places=6)

    def test_777777と888888の明暗差は約126(self):
        self.assertAlmostEqual(msc.contrast_ratio("#777777", "#888888"), 1.26, places=2)


# ---------------------------------------------------------------- 7.6 jpeg_size
class TestJpegSize(unittest.TestCase):
    def test_SOF0の幅と高さを読む(self):
        self.assertEqual(msc.jpeg_size(minimal_jpeg(1080, 1080)), (1080, 1080))

    def test_SOF2も読む(self):
        self.assertEqual(msc.jpeg_size(minimal_jpeg(300, 200, marker=0xC2)), (300, 200))

    def test_DHTをSOFと取り違えない(self):
        dht = b"\xff\xc4\x00\x05\x00\x00\x00"
        data = minimal_jpeg(20, 10)
        data = data[:2] + dht + data[2:]
        self.assertEqual(msc.jpeg_size(data), (20, 10))

    def test_JPGとDACもSOFと取り違えない(self):
        for marker in (0xC8, 0xCC):
            with self.subTest(hex(marker)):
                seg = bytes([0xFF, marker, 0x00, 0x05, 0x00, 0x00, 0x00])
                data = minimal_jpeg(20, 10)
                data = data[:2] + seg + data[2:]
                self.assertEqual(msc.jpeg_size(data), (20, 10))

    def test_SOFの無いバイト列はNone(self):
        self.assertIsNone(msc.jpeg_size(b"\xff\xd8\xff\xd9"))

    def test_JPEGでないバイト列はNone(self):
        self.assertIsNone(msc.jpeg_size(b"\x89PNG\r\n\x1a\n"))


# ---------------------------------------------------------------- CLI の共通
class CliBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sns_cards_test_")
        self.cwd = os.path.join(self.tmp, "cwd"); os.makedirs(self.cwd)
        self.empty_path = os.path.join(self.tmp, "emptybin"); os.makedirs(self.empty_path)
        self.out = os.path.join(self.tmp, "out"); os.makedirs(self.out)
        self.bin = os.path.join(self.tmp, "bin"); os.makedirs(self.bin)
        self.cfg = os.path.join(self.tmp, "cards.json")
        self.write_cfg(ex())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write_cfg(self, cfg):
        with open(self.cfg, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False)

    def run_cli(self, *args, env_extra=None, path=None, timeout=120):
        env = {k: v for k, v in os.environ.items()
               if k not in ("SOFFICE", "PDFTOPPM", "FC_LIST") and not k.startswith("SNS_CARDS_")}
        env["PATH"] = path if path is not None else self.empty_path
        env["SNS_CARDS_PROFILE"] = os.path.join(self.tmp, "profile")
        if env_extra:
            env.update(env_extra)
        self.last_env = env
        return subprocess.run([sys.executable, SCRIPT] + list(args), cwd=self.cwd, env=env,
                              capture_output=True, text=True, timeout=timeout)

    def fake(self, name, body):
        p = os.path.join(self.bin, name)
        with open(p, "w") as f:
            f.write("#!/bin/sh\n" + body + "\n")
        os.chmod(p, 0o755)
        return p

    def fake_soffice(self, mode="ok"):
        """--outdir の後と最後の引数から、<outdir>/<名前>.pdf を作る偽の soffice。引数は args.log に書く。"""
        log = os.path.join(self.tmp, "soffice-args.log")
        if mode == "fail":
            return self.fake("soffice", "exit 1")
        if mode == "sleep":
            return self.fake("soffice", "exec /bin/sleep 5")
        script = (
            'printf "%s\\n" "$@" > "' + log + '"\n'
            'out=""; prev=""; last=""\n'
            'for a in "$@"; do if [ "$prev" = "--outdir" ]; then out="$a"; fi; prev="$a"; last="$a"; done\n'
            'b="${last##*/}"; b="${b%.pptx}"\n'  # PATH を空にするので外部コマンド（basename）は使わない
            'printf "%%PDF-1.4 fake" > "$out/$b.pdf"'
        )
        return self.fake("soffice", script)

    def fake_pdftoppm(self, n=4, size=1080, mode="ok"):
        """最後の引数を接頭辞として <接頭辞>-1.jpg〜-n.jpg（最小の JPEG）を作る偽の pdftoppm。"""
        if mode == "sleep":
            return self.fake("pdftoppm", "exec /bin/sleep 5")
        data = minimal_jpeg(size, size).hex()
        script = (
            'for a in "$@"; do last="$a"; done\n'
            '"' + sys.executable + '" -c "import sys; d=bytes.fromhex(\'' + data + '\'); '
            '[open(sys.argv[1] + \'-%d.jpg\' % i, \'wb\').write(d) for i in range(1, ' + str(n + 1) + ')]" "$last"'
        )
        return self.fake("pdftoppm", script)

    def jpgs(self):
        return sorted(f for f in os.listdir(self.out) if f.endswith(".jpg"))


# ---------------------------------------------------------------- 7.1 の CLI
class TestCliCheck(CliBase):
    def test_checkの終了コード_見本は0(self):
        self.assertEqual(self.run_cli("--config", self.cfg, "--check").returncode, 0)

    def test_checkの終了コード_違反は1(self):
        c = ex(); del c["cards"][3]; self.write_cfg(c)
        r = self.run_cli("--config", self.cfg, "--check")
        self.assertEqual(r.returncode, 1)
        self.assertIn("C1", r.stdout + r.stderr)

    def test_checkの終了コード_壊れたJSONは2(self):
        with open(self.cfg, "w") as f:
            f.write("{")
        self.assertEqual(self.run_cli("--config", self.cfg, "--check").returncode, 2)

    def test_checkの終了コード_引数なしは2(self):
        self.assertEqual(self.run_cli().returncode, 2)

    def test_設定の最上位が配列なら入力の誤り(self):
        with open(self.cfg, "w") as f:
            f.write("[]")
        self.assertEqual(self.run_cli("--config", self.cfg, "--check").returncode, 2)

    def test_palette_refが無いとexit2(self):
        c = ex(); c["palette_ref"] = "missing.json"; self.write_cfg(c)
        self.assertEqual(self.run_cli("--config", self.cfg, "--check").returncode, 2)

    def test_既定のモードでout_dirが無いと入力の誤り(self):
        self.assertEqual(self.run_cli("--config", self.cfg).returncode, 2)

    def test_criteriaが壊れていると入力の誤り(self):
        bad = os.path.join(self.tmp, "rules.json")
        with open(bad, "w") as f:
            f.write("{")
        self.assertEqual(self.run_cli("--config", self.cfg, "--check", "--rules", bad).returncode, 2)

    def test_criteriaに必須のキーが無いと入力の誤り(self):
        rules = copy.deepcopy(RULES); del rules["limits"]
        bad = os.path.join(self.tmp, "rules.json")
        with open(bad, "w", encoding="utf-8") as f:
            json.dump(rules, f, ensure_ascii=False)
        self.assertEqual(self.run_cli("--config", self.cfg, "--check", "--rules", bad).returncode, 2)

    def test_criteriaのschemaが違うと入力の誤り(self):
        rules = copy.deepcopy(RULES); rules["schema"] = "sns-square-cards-rules/v1"
        bad = os.path.join(self.tmp, "rules.json")
        with open(bad, "w", encoding="utf-8") as f:
            json.dump(rules, f, ensure_ascii=False)
        self.assertEqual(self.run_cli("--config", self.cfg, "--check", "--rules", bad).returncode, 2)

    def test_palette_refは設定ファイルの位置から読みその配色が効く(self):
        roles = dict(RULES["default_palette"]["roles"])
        with open(os.path.join(self.tmp, "brand.json"), "w", encoding="utf-8") as f:
            json.dump({"roles": roles}, f)
        c = ex(); c["palette_ref"] = "brand.json"; self.write_cfg(c)
        r = self.run_cli("--config", self.cfg, "--check")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        roles["surface-1"] = "#1E2330"  # 明るい地を暗い地と同じ色にする → C4
        with open(os.path.join(self.tmp, "brand.json"), "w", encoding="utf-8") as f:
            json.dump({"roles": roles}, f)
        r = self.run_cli("--config", self.cfg, "--check")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("C4", r.stdout + r.stderr)

    def _rules_file(self, mutate):
        rules = copy.deepcopy(RULES); mutate(rules)
        path = os.path.join(self.tmp, "rules.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rules, f, ensure_ascii=False)
        return path

    def test_criteriaの入れ子の必須キーが無いと入力の誤り(self):
        cases = {"limits.title_max": lambda r: r["limits"].pop("title_max"),
                 "post_count.x.scale": lambda r: r["post_count"]["x"].pop("scale")}
        for name, mutate in cases.items():
            with self.subTest(name):
                r = self.run_cli("--config", self.cfg, "--check", "--rules", self._rules_file(mutate))
                self.assertEqual(r.returncode, 2, r.stdout + r.stderr)

    def test_criteriaのv3の必須キーが無いと入力の誤り(self):
        cases = {"layout_in": lambda r: r.pop("layout_in"),
                 "line_spacing": lambda r: r.pop("line_spacing"),
                 "palette_roles_used.note_on_dark": lambda r: r["palette_roles_used"].pop("note_on_dark"),
                 "default_font.other": lambda r: r["default_font"].pop("other")}
        for name, mutate in cases.items():
            with self.subTest(name):
                r = self.run_cli("--config", self.cfg, "--check", "--rules", self._rules_file(mutate))
                self.assertEqual(r.returncode, 2, r.stdout + r.stderr)

    def test_criteriaの型が違うと入力の誤り(self):
        cases = {"card_count": lambda r: r.__setitem__("card_count", "four"),
                 "cards_layout.bg": lambda r: r["cards_layout"][0].pop("bg"),
                 "ranges": lambda r: r["post_count"]["x"]["ranges"].__setitem__(0, [0, 4351]),
                 "layout_in.title": lambda r: r["layout_in"].__setitem__("title", [1, 2]),
                 "page_number_format": lambda r: r.__setitem__("page_number_format", "page")}
        for name, mutate in cases.items():
            with self.subTest(name):
                r = self.run_cli("--config", self.cfg, "--check", "--rules", self._rules_file(mutate))
                self.assertEqual(r.returncode, 2, r.stdout + r.stderr)

    def test_nameに許されない文字は入力の誤り(self):
        self.assertEqual(self.run_cli("--config", self.cfg, "--out-dir", self.out, "--name", "a/b").returncode, 2)


# ---------------------------------------------------------------- 7.3 生成
@unittest.skipUnless(HAS_PPTX, "python-pptx が無い")
class TestBuildPptx(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sns_cards_pptx_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def build(self, cfg):
        from pptx import Presentation
        roles, v = msc.resolve_palette(cfg, None, RULES)
        self.assertEqual(v, [])
        p = os.path.join(self.tmp, "c.pptx")
        msc.build_pptx(cfg, roles, RULES, p)
        return Presentation(p)

    @staticmethod
    def texts(slide):
        """文字のある図形の文字（行の区切りは段落でも改行でも \\n にそろえる）。"""
        return [s.text_frame.text.replace("\v", "\n") for s in slide.shapes if s.has_text_frame and s.text_frame.text]

    @staticmethod
    def font_of(slide, text):
        """text を持つ図形の最初の文字の大きさ（pt）とフォント名。run に無ければ段落の値を読む。"""
        for s in slide.shapes:
            if s.has_text_frame and s.text_frame.text.replace("\v", "\n") == text:
                para = s.text_frame.paragraphs[0]
                run = para.runs[0] if para.runs else None
                size = (run.font.size if run is not None and run.font.size is not None else para.font.size)
                name = (run.font.name if run is not None and run.font.name else para.font.name)
                return (size.pt if size is not None else None), name
        raise AssertionError("図形が無い: %r" % text)

    def test_pptxは4枚で正方形(self):
        prs = self.build(ex())
        self.assertEqual(len(prs.slides), 4)
        self.assertEqual(prs.slide_width, 9144000)
        self.assertEqual(prs.slide_height, 9144000)

    def test_各スライドにtitleとbodyの文字がある(self):
        cfg = ex(); prs = self.build(cfg)
        for slide, card in zip(prs.slides, cfg["cards"]):
            joined = "\n".join(self.texts(slide))
            self.assertIn(card["title"], joined)
            self.assertIn(card["body"], joined)

    def test_labelを省略するとラベルの図形は無い(self):
        prs = self.build(ex())
        self.assertEqual(len(self.texts(prs.slides[0])), 3)

    def test_labelを書くと各スライドに出る(self):
        cfg = ex(); cfg["label"] = "sample"
        for slide in self.build(cfg).slides:
            self.assertIn("sample", self.texts(slide))

    def test_page_numbersがfalseならページ番号は出ない(self):
        cfg = ex(); cfg["page_numbers"] = False
        prs = self.build(cfg)
        for i, slide in enumerate(prs.slides, 1):
            self.assertNotIn("%d / 4" % i, self.texts(slide))
        self.assertEqual(len(self.texts(prs.slides[0])), 2)

    def test_ページ番号の形はn_4(self):
        self.assertIn("2 / 4", self.texts(self.build(ex()).slides[1]))

    def test_暗い地の背景はtext_primaryで明るい地はsurface_1(self):
        prs = self.build(ex())
        self.assertEqual(str(prs.slides[0].background.fill.fore_color.rgb), "1E2330")
        self.assertEqual(str(prs.slides[1].background.fill.fore_color.rgb), "F2F4F8")

    def test_目安を超えたtitleは小さい方のpt(self):
        n = RULES["limits"]["title_recommended"]
        for length, pt in ((n + 1, RULES["font_pt"]["title_small"]), (n, RULES["font_pt"]["title"])):
            with self.subTest(length):
                cfg = ex(); cfg["cards"][0]["title"] = "あ" * length
                self.assertEqual(self.font_of(self.build(cfg).slides[0], "あ" * length)[0], pt)

    def test_目安を超えたbodyは小さい方のpt(self):
        n = RULES["limits"]["body_recommended"]
        for length, pt in ((n + 1, RULES["font_pt"]["body_small"]), (n, RULES["font_pt"]["body"])):
            with self.subTest(length):
                cfg = ex(); cfg["cards"][0]["body"] = "あ" * length
                self.assertEqual(self.font_of(self.build(cfg).slides[0], "あ" * length)[0], pt)

    def test_fontを省略すると既定のフォント(self):
        cfg = ex()
        want = RULES["default_font"]["darwin" if sys.platform == "darwin" else "other"]
        self.assertEqual(self.font_of(self.build(cfg).slides[0], cfg["cards"][0]["title"])[1], want)

    def test_fontを書くとそのフォント(self):
        cfg = ex(); cfg["font"] = "Test Font"
        self.assertEqual(self.font_of(self.build(cfg).slides[0], cfg["cards"][0]["title"])[1], "Test Font")

    def test_bodyを省略したカードも作れる(self):
        cfg = ex(); del cfg["cards"][3]["body"]
        self.assertEqual(sorted(self.texts(self.build(cfg).slides[3])), sorted([cfg["cards"][3]["title"], "4 / 4"]))

    def test_noteはそのカードに描かれる(self):
        cfg = ex(); prs = self.build(cfg)
        self.assertIn(cfg["cards"][1]["note"], self.texts(prs.slides[1]))
        self.assertIn(cfg["cards"][2]["note"], self.texts(prs.slides[2]))


# ---------------------------------------------------------------- 7.4 画像化（偽の道具）
@unittest.skipIf(IS_WINDOWS, "偽の道具は shell script")
class TestRenderFakeTools(CliBase):
    def gen(self, soffice, pdftoppm, env_extra=None, name="cards"):
        env = {"SOFFICE": soffice, "PDFTOPPM": pdftoppm}
        if env_extra:
            env.update(env_extra)
        return self.run_cli("--config", self.cfg, "--out-dir", self.out, "--name", name, env_extra=env)

    @unittest.skipUnless(HAS_PPTX, "python-pptx が無い")
    def test_sofficeが失敗するとexit4でJPEGを残さない(self):
        r = self.gen(self.fake_soffice("fail"), self.fake_pdftoppm())
        self.assertEqual(r.returncode, 4, r.stderr)
        self.assertEqual(self.jpgs(), [])

    @unittest.skipUnless(HAS_PPTX, "python-pptx が無い")
    def test_sofficeが時間切れならexit4(self):
        r = self.gen(self.fake_soffice("sleep"), self.fake_pdftoppm(), {"SNS_CARDS_SOFFICE_TIMEOUT": "1"})
        self.assertEqual(r.returncode, 4, r.stderr)
        self.assertIn("秒で終わらない", r.stderr)
        self.assertEqual(self.jpgs(), [])

    @unittest.skipUnless(HAS_PPTX, "python-pptx が無い")
    def test_pdftoppmが時間切れならexit4(self):
        r = self.gen(self.fake_soffice(), self.fake_pdftoppm(mode="sleep"), {"SNS_CARDS_PDFTOPPM_TIMEOUT": "1"})
        self.assertEqual(r.returncode, 4, r.stderr)
        self.assertIn("秒で終わらない", r.stderr)
        self.assertEqual(self.jpgs(), [])

    @unittest.skipUnless(HAS_PPTX, "python-pptx が無い")
    def test_作った出力先は失敗したら消す(self):
        fresh = os.path.join(self.tmp, "fresh-out")
        r = self.run_cli("--config", self.cfg, "--out-dir", fresh,
                         env_extra={"SOFFICE": self.fake_soffice("fail"), "PDFTOPPM": self.fake_pdftoppm()})
        self.assertEqual(r.returncode, 4, r.stderr)
        self.assertFalse(os.path.exists(fresh))

    @unittest.skipUnless(HAS_PPTX, "python-pptx が無い")
    def test_JPEGの大きさが違うとexit4でJPEGを残さない(self):
        r = self.gen(self.fake_soffice(), self.fake_pdftoppm(size=100))
        self.assertEqual(r.returncode, 4, r.stderr)
        self.assertEqual(self.jpgs(), [])

    @unittest.skipUnless(HAS_PPTX, "python-pptx が無い")
    def test_JPEGが3枚しかないとexit4(self):
        r = self.gen(self.fake_soffice(), self.fake_pdftoppm(n=3))
        self.assertEqual(r.returncode, 4, r.stderr)
        self.assertEqual(self.jpgs(), [])

    @unittest.skipUnless(HAS_PPTX, "python-pptx が無い")
    def test_正しいJPEGが出れば4枚を名前をそろえて置く(self):
        r = self.gen(self.fake_soffice(), self.fake_pdftoppm(), name="post1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(sorted(os.listdir(self.out)),
                         ["post1-1.jpg", "post1-2.jpg", "post1-3.jpg", "post1-4.jpg", "post1.pptx"])
        with open(os.path.join(self.tmp, "soffice-args.log")) as f:
            self.assertTrue(any(a.startswith("-env:UserInstallation=") for a in f.read().splitlines()))

    @unittest.skipUnless(HAS_PPTX, "python-pptx が無い")
    def test_既にある同じ名前の出力は置き換える(self):
        old = os.path.join(self.out, "cards-1.jpg")
        with open(old, "wb") as f:
            f.write(b"old")
        r = self.gen(self.fake_soffice(), self.fake_pdftoppm())
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(old, "rb") as f:
            self.assertEqual(f.read(), minimal_jpeg(1080, 1080))

    @unittest.skipUnless(HAS_PPTX, "python-pptx が無い")
    def test_失敗しても前回の出力はそのまま残る(self):
        before = {}
        for i in range(1, 5):
            before["cards-%d.jpg" % i] = ("old%d" % i).encode()
        before["cards.pptx"] = b"oldp"
        for k, v in before.items():
            with open(os.path.join(self.out, k), "wb") as f:
                f.write(v)
        r = self.gen(self.fake_soffice("fail"), self.fake_pdftoppm())
        self.assertEqual(r.returncode, 4, r.stderr)
        self.assertEqual(sorted(os.listdir(self.out)), sorted(before))
        for k, v in before.items():
            with open(os.path.join(self.out, k), "rb") as f:
                self.assertEqual(f.read(), v)

    @unittest.skipUnless(HAS_PPTX, "python-pptx が無い（別の理由の exit 3 と区別できない）")
    def test_pdftoppmが見つからないとexit3でJPEGを残さない(self):
        r = self.gen(self.fake_soffice(), os.path.join(self.tmp, "no-pdftoppm"))
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertIn("pdftoppm", r.stdout + r.stderr)
        self.assertEqual(self.jpgs(), [])

    @unittest.skipUnless(HAS_PPTX, "python-pptx が無い（別の理由の exit 3 と区別できない）")
    def test_sofficeが見つからないとpreflightはexit3(self):
        r = self.run_cli("--preflight", env_extra={"SOFFICE": os.path.join(self.tmp, "no-soffice"),
                                                    "PDFTOPPM": self.fake_pdftoppm()})
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertIn("soffice", r.stdout + r.stderr)

    def test_python_pptxが無いとexit3(self):
        code = ("import runpy, sys; sys.modules['pptx'] = None; sys.argv = sys.argv[1:]; "
                "runpy.run_path(sys.argv[0], run_name='__main__')")
        self.run_cli("--check", "--config", self.cfg)  # 環境（self.last_env）を作る
        env = dict(self.last_env, SOFFICE=self.fake_soffice(), PDFTOPPM=self.fake_pdftoppm())
        r = subprocess.run([sys.executable, "-c", code, SCRIPT, "--config", self.cfg, "--out-dir", self.out],
                           cwd=self.cwd, env=env, capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertIn("python-pptx", r.stdout + r.stderr)
        self.assertEqual(os.listdir(self.out), [])

    def test_検査で違反があれば生成しない(self):
        c = ex(); del c["cards"][3]; self.write_cfg(c)
        r = self.gen(self.fake_soffice(), self.fake_pdftoppm())
        self.assertEqual(r.returncode, 1)
        self.assertIn("C1", r.stdout + r.stderr)
        self.assertEqual(os.listdir(self.out), [])
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "soffice-args.log")))

    @unittest.skipUnless(HAS_PPTX, "python-pptx が無い（別の理由の exit 3 と区別できない）")
    def test_render_deckをimportできないとexit3(self):
        r = self.run_cli("--preflight", env_extra={"SOFFICE": self.fake_soffice(), "PDFTOPPM": self.fake_pdftoppm(),
                                                    "SNS_CARDS_RENDER_DECK": os.path.join(self.tmp, "nowhere", "render_deck.py")})
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertIn("render_deck", r.stdout + r.stderr)


class TestRenderDeckContract(unittest.TestCase):
    def test_render_deckの2つの関数は呼べる(self):
        rspec = importlib.util.spec_from_file_location("render_deck_contract", RENDER_DECK)
        rd = importlib.util.module_from_spec(rspec)
        rspec.loader.exec_module(rd)
        for fn in (rd.find_soffice, rd.find_pdftoppm):
            got = fn()
            self.assertTrue(got is None or isinstance(got, str), got)


# ---------------------------------------------------------------- 7.7 フォントの事前確認
@unittest.skipIf(IS_WINDOWS, "偽の道具は shell script")
@unittest.skipUnless(HAS_PPTX, "python-pptx が無い（preflight は python-pptx も確かめる）")
class TestPreflightFont(CliBase):
    def env(self, fc):
        return {"SOFFICE": self.fake_soffice(), "PDFTOPPM": self.fake_pdftoppm(), "FC_LIST": fc}

    def test_fc_listがフォントを返せば合格(self):
        fc = self.fake("fc-list", 'printf "Hiragino Sans\\nNoto Sans CJK JP\\n"')
        r = self.run_cli("--preflight", env_extra=self.env(fc))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_fc_listが返さなければexit3(self):
        fc = self.fake("fc-list", "exit 0")
        r = self.run_cli("--preflight", env_extra=self.env(fc))
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        font = RULES["default_font"]["darwin" if sys.platform == "darwin" else "other"]
        self.assertIn(font, r.stdout + r.stderr)

    def test_フォント名は完全一致で照合する(self):
        c = ex(); c["font"] = "Sans"; self.write_cfg(c)
        fc = self.fake("fc-list", 'printf "Hiragino Sans\\n"')
        r = self.run_cli("--preflight", "--config", self.cfg, env_extra=self.env(fc))
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertIn("NG font Sans", r.stdout + r.stderr)

    def test_FC_LISTが無効ならPATHのfc_listを使う(self):
        pathdir = os.path.join(self.tmp, "fcbin"); os.makedirs(pathdir)
        fc = os.path.join(pathdir, "fc-list")
        with open(fc, "w") as f:
            f.write('#!/bin/sh\nprintf "Hiragino Sans\\nNoto Sans CJK JP\\n"\n')
        os.chmod(fc, 0o755)
        r = self.run_cli("--preflight", env_extra=self.env(os.path.join(self.tmp, "no-fc-list")), path=pathdir)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("未確認", r.stdout + r.stderr)

    def test_設定のfontを確かめる(self):
        c = ex(); c["font"] = "Foo Sans"; self.write_cfg(c)
        fc = self.fake("fc-list", 'printf "Hiragino Sans\\n"')
        r = self.run_cli("--preflight", "--config", self.cfg, env_extra=self.env(fc))
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertIn("Foo Sans", r.stdout + r.stderr)

    def test_fc_listが無ければフォントは未確認でexitを変えない(self):
        r = self.run_cli("--preflight", env_extra=self.env(os.path.join(self.tmp, "no-fc-list")))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("未確認", r.stdout + r.stderr)


# ---------------------------------------------------------------- 7.5 画像化（実物）
@unittest.skipUnless(HAS_PPTX and REAL_SOFFICE and REAL_PDFTOPPM, "python-pptx・soffice・pdftoppm のどれかが無い")
class TestRenderReal(CliBase):
    def test_見本からJPEGが4枚でき1080x1080(self):
        cache = os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache")
        profile = os.path.join(cache, "sns-square-cards", "lo_profile")  # 既定と同じ場所を使い回す（初回の作成を避ける）
        r = self.run_cli("--config", self.cfg, "--out-dir", self.out, "--name", "real",
                         env_extra={"SOFFICE": REAL_SOFFICE, "PDFTOPPM": REAL_PDFTOPPM, "SNS_CARDS_PROFILE": profile},
                         path=os.environ.get("PATH", ""), timeout=900)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.jpgs(), ["real-1.jpg", "real-2.jpg", "real-3.jpg", "real-4.jpg"])
        for name in self.jpgs():
            with open(os.path.join(self.out, name), "rb") as f:
                self.assertEqual(msc.jpeg_size(f.read()), (1080, 1080))
        self.assertFalse(any(f.endswith(".pdf") for f in os.listdir(self.out)))


if __name__ == "__main__":
    unittest.main()
