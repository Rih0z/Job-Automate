#!/usr/bin/env python3
"""render_deck.py — .pptx をスライドごとの PNG 画像にする（点検員が画像を見て採点するため）。

使い方: python render_deck.py <deck.pptx> -o <出力フォルダ> [--dpi 70]
出力: <出力フォルダ>/<deck名>.pdf と <出力フォルダ>/slide-01.png, slide-02.png, …（標準出力に 1 行 1 枚で表示）

描画ソフトは次の順に探す（見つからなければ終了コード 2 で、理由を出す。画像なしで点検するときは「描画未確認」と報告する）:
  1. 環境変数 SOFFICE（LibreOffice の soffice の絶対パス）
  2. PATH 上の soffice
  3. 作業フォルダから上へたどった `00_vendor/libreoffice/program/soffice(.exe)`（持ち運び版）
  4. Windows の標準の導入先（Program Files の LibreOffice）
PDF を画像にする pdftoppm も同様（環境変数 PDFTOPPM、PATH、`00_vendor/poppler/Library/bin/`）。
注意: LibreOffice の描画は、PowerPoint の実機と、フォントの代替などで折り返しが少し違うことがある。初回の起動は、設定の作成のため数分かかることがある。
標準ライブラリのみ。
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys
import tempfile


for _s in (sys.stdout, sys.stderr):  # Windows の既定の文字コードで日本語の出力が落ちないようにする
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8")


def find_up(rel_paths, start):
    d = os.path.abspath(start)
    while True:
        for rel in rel_paths:
            p = os.path.join(d, *rel.split("/"))
            if os.path.isfile(p):
                return p
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def find_soffice():
    env = os.environ.get("SOFFICE")
    if env and os.path.isfile(env):
        return env
    w = shutil.which("soffice")
    if w:
        return w
    p = find_up(["00_vendor/libreoffice/program/soffice.exe", "00_vendor/libreoffice/program/soffice"], os.getcwd())
    if p:
        return p
    for c in glob.glob(r"C:\Program Files*\LibreOffice*\program\soffice.exe"):
        return c
    return None


def find_pdftoppm():
    env = os.environ.get("PDFTOPPM")
    if env and os.path.isfile(env):
        return env
    w = shutil.which("pdftoppm")
    if w:
        return w
    return find_up(["00_vendor/poppler/Library/bin/pdftoppm.exe", "00_vendor/poppler/bin/pdftoppm"], os.getcwd())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("deck")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--dpi", type=int, default=70)
    ap.add_argument("--timeout", type=int, default=600, help="PDF 化の待ち時間（秒）。初回は長くかかることがある")
    a = ap.parse_args()
    deck = os.path.abspath(a.deck)
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    soffice, pdftoppm = find_soffice(), find_pdftoppm()
    if not soffice or not pdftoppm:
        print("描画できません: soffice=%s pdftoppm=%s（環境変数 SOFFICE / PDFTOPPM で指定できる）。画像なしの点検は「描画未確認」と報告する" % (soffice, pdftoppm), file=sys.stderr)
        return 2
    # 日本語パスや記号で失敗しないよう、一時フォルダの ASCII 名にコピーして変換する
    tmp = tempfile.mkdtemp(prefix="render_deck_")
    try:
        src = os.path.join(tmp, "deck.pptx")
        shutil.copyfile(deck, src)
        # LibreOffice の設定フォルダは、初回の作成に時間がかかるため、毎回作らず使い回す
        prof_dir = os.environ.get("RENDER_DECK_PROFILE") or os.path.join(tempfile.gettempdir(), "render_deck_lo_profile")
        profile = "file:///" + prof_dir.replace("\\", "/")
        cmd = [soffice, "-env:UserInstallation=" + profile, "--headless", "--convert-to", "pdf", "--outdir", tmp, src]
        try:
            subprocess.run(cmd, check=True, timeout=a.timeout, capture_output=True)
        except (subprocess.SubprocessError, OSError) as e:
            print("PDF 化に失敗: %s" % e, file=sys.stderr)
            return 2
        pdf = os.path.join(tmp, "deck.pdf")
        if not os.path.isfile(pdf):
            print("PDF ができなかった", file=sys.stderr)
            return 2
        shutil.copyfile(pdf, os.path.join(out, os.path.splitext(os.path.basename(deck))[0] + ".pdf"))
        subprocess.run([pdftoppm, "-r", str(a.dpi), "-png", pdf, os.path.join(out, "slide")], check=True, capture_output=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    for f in sorted(glob.glob(os.path.join(out, "slide-*.png"))):
        print(f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
