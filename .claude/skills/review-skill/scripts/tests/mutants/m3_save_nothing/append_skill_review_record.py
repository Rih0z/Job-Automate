#!/usr/bin/env python
"""変異体 3: 何も保存しない保存 script（検査もせず、SAVED と出して exit 0）。試験が検出できなければならない誤った実装。"""
import sys

sys.stdout.write("SAVED .claude/review-history/skill-review/none/none.json\n")
sys.exit(0)
