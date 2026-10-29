#!/usr/bin/env python
"""review-skill の gate 一式の試験の入口。標準ライブラリのみ。

使い方: python run_tests.py [-k 部分文字列]
終了コード: 0 = 全件合格かつ skip 0 件 / 1 = 失敗・エラーがある、または skip がある。
skip を許すのは、環境変数 SKILL_REVIEW_TEST_ALLOW_SKIP=1 を明示したときだけ（skip で緑に見えるのを防ぐ）。
"""
import os
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.path.insert(0, str(HERE))
    loader = unittest.TestLoader()
    if "-k" in argv:
        loader.testNamePatterns = ["*%s*" % argv[argv.index("-k") + 1]]
    suite = loader.discover(str(HERE))
    result = unittest.TextTestRunner(verbosity=2, stream=sys.stdout).run(suite)
    skipped = len(result.skipped)
    print("SUMMARY run=%d failures=%d errors=%d skipped=%d" % (result.testsRun, len(result.failures), len(result.errors), skipped))
    for test, reason in result.skipped:
        print("SKIPPED: %s: %s" % (test, reason))
    if skipped:
        print("注意: skip の多くは、権限が無く symlink を作れない環境（Windows の開発者モード無効など）で起きる。skip は緑ではなく未確認として扱う。")
    import tempfile
    left = sorted(d.name for d in Path(tempfile.gettempdir()).glob("srg-test-*"))
    print("残留した一時ディレクトリ srg-test-*: %d 件%s" % (len(left), "（後始末の失敗。手で消してよい）" if left else ""))
    if not result.wasSuccessful():
        return 1
    if skipped and os.environ.get("SKILL_REVIEW_TEST_ALLOW_SKIP") != "1":
        print("skip が %d 件ある。skip で緑に見えるのを防ぐため非ゼロで終了する（許すなら SKILL_REVIEW_TEST_ALLOW_SKIP=1）。" % skipped)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
