"""hook-skill-review-gate.sh（D4）の試験: T19〜T23・T29・T30・T32〜T34。標準ライブラリの unittest。

実物の hook script を Git Bash で起動し、stdin に hook イベントの JSON、環境変数 CLAUDE_PROJECT_DIR に偽 repo、
SKILL_REVIEW_NOW に日時を渡す。hook は gate を「自分の置き場所の隣の skill_review_gate.py」として呼び、リポジトリのルートは
SKILL_REVIEW_REPO_ROOT > CLAUDE_PROJECT_DIR の順で決める（stub は使わない）。
仕様の補完は helpers.py の冒頭コメントに集約。要点:
  - block 回数の state は <root>/.tmp/skill-review-gate/state.json の stop_blocks（この turn で本 hook が block した回数）。
    新 turn（stop_hook_active false）で 0 に戻してから評価し、block したら +1。active のとき 3 以上なら通す（1〜3 回目 block・4 回目で通す）。
  - 通す（block しない）ときの出力は、何も無いか {"systemMessage": ...}。
  - 試験用の継ぎ目: SKILL_REVIEW_TIMEOUT_SEC（hook が gate を待つ秒数）・SKILL_REVIEW_TEST_DELAY_SEC（gate の起動直後の sleep）。
"""
import json
import os
import re
import shutil
import time
import unittest
from pathlib import Path

import helpers as h
from helpers import RepoTestCase, STOP_ACTIVE, STOP_NEW, SESSION_START


class HookBase(RepoTestCase):
    def state(self):
        p = self.repo / h.STATE_REL
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    def blocks(self):
        s = self.state()
        return None if s is None else s.get("stop_blocks")

    def assertBlocks(self, r, *names):
        self.assertEqual(r.code, 0, r)
        self.assertIsInstance(r.data, dict, r)
        self.assertEqual(r.data.get("decision"), "block", r)
        for n in names:
            self.assertIn(n, r.data["reason"], r)

    def assertPasses(self, r):
        self.assertEqual(r.code, 0, r)
        self.assertNotEqual(r.data, "__PARSE_ERROR__", r)
        self.assertTrue(r.data is None or "decision" not in r.data, r)

    def sys_message(self, r):
        self.assertIsInstance(r.data, dict, r)
        self.assertIn("systemMessage", r.data, r)
        return r.data["systemMessage"]


class StopHook(HookBase):
    def unreviewed_repo(self, skills=("alpha", "bravo"), git=False):
        repo = self.mk(skills, git=git)
        h.pass_records(repo, names=["review-skill"])
        return repo

    def test_stop_hook_blocks_with_skill_names_and_one_at_a_time_instruction(self):  # T19
        repo = self.unreviewed_repo(("alpha", "bravo", "charlie", "delta"))
        h.pass_records(repo, names=["charlie"])  # PASS 済み
        h.write_ledger(repo, {"delta": None})  # 負債台帳（BASELINE_DEBT）
        r = h.run_hook(repo, STOP_NEW)
        self.assertBlocks(r, "alpha", "bravo")
        reason = r.data["reason"]
        self.assertIn("readonly-reviewer", reason)
        self.assertIn("review-skill", reason)
        self.assertIn("1 skill ずつ", reason)
        self.assertNotIn("charlie", reason)  # PASS 済みの skill は列挙しない
        self.assertNotIn("delta", reason)  # BASELINE_DEBT の skill も列挙しない
        self.assertEqual(h.run_gate(repo, "--strict").code, 1)  # 前提: gate が strict で exit 1
        # 全て PASS なら block しない
        h.pass_records(repo)
        self.assertPasses(h.run_hook(repo, STOP_NEW))

    def test_stop_hook_blocks_up_to_three_times_per_turn_then_allows_on_the_fourth(self):  # T20
        repo = self.unreviewed_repo(("alpha",))
        r1 = h.run_hook(repo, STOP_NEW)
        self.assertBlocks(r1, "alpha")
        self.assertEqual(self.blocks(), 1)
        r2 = h.run_hook(repo, STOP_ACTIVE)
        self.assertBlocks(r2, "alpha")
        self.assertEqual(self.blocks(), 2)
        r3 = h.run_hook(repo, STOP_ACTIVE)
        self.assertBlocks(r3, "alpha")
        self.assertEqual(self.blocks(), 3)
        r4 = h.run_hook(repo, STOP_ACTIVE)  # 4 回目は通す
        self.assertPasses(r4)
        msg = self.sys_message(r4)
        self.assertIn("alpha", msg)  # 未レビュー skill 名を列挙して通す
        self.assertEqual(self.blocks(), 3)
        r5 = h.run_hook(repo, STOP_NEW)  # 新しい turn でカウンタが 0 に戻り、再び block
        self.assertBlocks(r5, "alpha")
        self.assertEqual(self.blocks(), 1)

    def test_hook_reports_when_python_is_unavailable(self):  # T21
        repo = self.unreviewed_repo(("alpha",))
        bash = h.find_bash()
        self.assertIsNotNone(bash, "Git Bash が見つからない（skip にせず失敗にする）")
        # bash と coreutils は残し、python を含むディレクトリだけを PATH から外す（hook が使う道具を暗に制限しない）
        names = ("python", "python3", "py")
        kept = []
        for d in os.environ.get("PATH", "").split(os.pathsep):
            if d and not any((Path(d) / (n + ext)).exists() for n in names for ext in (".exe", "")):
                kept.append(d)
        usr_bin = str(Path(bash).resolve().parents[1] / "usr" / "bin")
        if usr_bin not in kept:
            kept.append(usr_bin)
        env = h.base_env(PATH=os.pathsep.join(kept))
        probe = h.run_proc([bash, "-c", "command -v python python3 py"], env=env)
        self.assertNotEqual(probe.code, 0, "前提: この PATH では python が見つからない（見つかった: %r）" % probe.out)
        self.assertEqual(probe.out.strip(), "")
        r = h.run_hook(repo, STOP_NEW, env=env, bash=bash)
        self.assertEqual(r.code, 0, r)
        self.assertPasses(r)  # block しない
        msg = self.sys_message(r)  # 無音で通さない
        self.assertIn("python", msg)
        self.assertIn("評価", msg)

    def test_hook_state_is_independent_of_setup_gate_state(self):  # T22
        repo = self.unreviewed_repo(("alpha",))
        setup = repo / h.SETUP_STATE_REL
        setup.parent.mkdir(parents=True)
        setup.write_text('{"phase": "generated", "target": "/x", "stop_blocks": 2}', encoding="utf-8")
        before = (setup.read_bytes(), setup.stat().st_mtime_ns)
        r = h.run_hook(repo, STOP_NEW)
        self.assertBlocks(r, "alpha")
        self.assertEqual((setup.read_bytes(), setup.stat().st_mtime_ns), before)  # 既存 state を読み書きしない
        self.assertEqual(self.blocks(), 1)  # setup 側の stop_blocks=2 に影響されない
        self.assertTrue((repo / h.STATE_REL).exists())
        # setup state が無くても動き、勝手に作らない
        shutil.rmtree(repo / ".tmp" / "harness-setup")
        self.assertBlocks(h.run_hook(repo, STOP_ACTIVE), "alpha")
        self.assertFalse((repo / ".tmp" / "harness-setup").exists())

    def test_stop_hook_blocks_on_ledger_tampering_and_warns_only_when_unverifiable(self):  # T29
        repo = self.mk(("alpha", "bravo"), git=True)
        h.pass_records(repo, names=["review-skill"])
        h.write_ledger(repo, {"alpha": None})
        h.git_commit_paths(repo, [h.LEDGER_REL], "ledger anchor")
        led = h.read_ledger(repo)
        led["skills"]["bravo"] = {"content_hash": h.skill_hash(repo, "bravo"), "registered": "2026-10-28", "reason": "後から足した"}
        h.write_json(repo / h.LEDGER_REL, led)
        self.assertEqual(h.run_gate(repo, "--strict").code, 0)  # 免除の hash は一致しているので strict は通る
        self.assertEqual(h.run_gate(repo, "--verify-ledger").code, 1)
        r = h.run_hook(repo, STOP_NEW)
        self.assertBlocks(r, "bravo")  # reason に該当エントリ名
        # UNVERIFIABLE（台帳が未 commit）は WARN で通す
        repo2 = self.tmp / "repo2"
        h.make_repo(repo2, skills=("alpha",), git=True)
        h.pass_records(repo2, names=["review-skill"])
        h.write_ledger(repo2, {"alpha": None})
        r2 = h.run_hook(repo2, STOP_NEW)
        self.assertPasses(r2)
        self.assertIn("UNVERIFIABLE", self.sys_message(r2))

    def test_hook_times_out_with_a_notice_and_passes(self):  # T30
        repo = self.unreviewed_repo(("alpha",))
        marks = self.tmp / "marks"
        delay = 25  # gate の遅延（秒）。hook が打ち切りを持たなければ、gate の完了（finished）まで待つことになる
        env = h.base_env(SKILL_REVIEW_TIMEOUT_SEC="10", SKILL_REVIEW_TEST_DELAY_SEC=str(delay), SKILL_REVIEW_TEST_MARK_DIR=marks.as_posix())
        self.addCleanup(h.kill_leftovers, str(self.tmp))  # 打ち切り後に残った gate（孫プロセス）を確実に止める
        r = h.run_hook(repo, STOP_NEW, env=env, timeout=30)  # 出力は一時ファイルで受けるので、孫が残っていても hook の終了で戻る
        self.assertPasses(r)
        self.assertIn("時間切れ", self.sys_message(r))
        # 絶対時間でなく副作用ファイルで判定する: gate は sleep に入る前に started を作り、sleep が終わると finished を作る
        self.assertTrue((marks / "started").exists(), "gate が sleep に入っていない（打ち切りの試験にならない）")
        self.assertFalse((marks / "finished").exists(), "hook が gate の完了を待ってから返っている（打ち切りが効いていない）")
        print("T30 参考: hook の所要 %.1f 秒（打ち切り 10 秒・gate の遅延 %d 秒）" % (r.elapsed, delay))

    def test_hook_does_not_block_and_reports_unevaluable_when_the_gate_fails_internally(self):  # T35
        real_hook = h.HOOK_SH
        h.require_exists(real_hook)
        for n, code in enumerate((3, 2, 7, 139)):  # 3 = 内部エラー。他は想定外の終了コード。1（--strict の要レビュー）とは区別される
            with self.subTest(gate_exit=code):
                d = self.tmp / ("hookcopy-%d" % n)
                d.mkdir()
                shutil.copy(real_hook, d / "hook-skill-review-gate.sh")
                cons = h.CONSISTENCY
                if cons.exists():
                    shutil.copy(cons, d / cons.name)
                (d / "skill_review_gate.py").write_text("import sys\nsys.stderr.write('internal error')\nsys.exit(%d)\n" % code, encoding="utf-8", newline="\n")
                repo = h.make_repo(self.tmp / ("r35-%d" % n), skills=("alpha",))  # alpha は未レビュー（本物の gate なら block になる）
                r = h.run_hook(repo, STOP_NEW, hook=d / "hook-skill-review-gate.sh")
                self.assertPasses(r)  # block しない
                self.assertIn("評価不能", self.sys_message(r))
                r2 = h.run_hook(repo, SESSION_START, hook=d / "hook-skill-review-gate.sh")
                self.assertPasses(r2)
                self.assertIn("評価不能", self.sys_message(r2))
        with self.subTest(gate_exit=1, note="--strict の exit 1 は評価不能ではなく block"):
            d = self.tmp / "hookcopy-strict"
            d.mkdir()
            shutil.copy(real_hook, d / "hook-skill-review-gate.sh")
            (d / "skill_review_gate.py").write_text("import sys\nsys.stdout.write('NEEDS_REVIEW: alpha\\n')\nsys.exit(1)\n", encoding="utf-8", newline="\n")
            repo = h.make_repo(self.tmp / "r35-strict", skills=("alpha",))
            r = h.run_hook(repo, STOP_NEW, hook=d / "hook-skill-review-gate.sh")
            self.assertEqual(r.code, 0, r)
            self.assertIsInstance(r.data, dict, r)
            self.assertEqual(r.data.get("decision"), "block", r)

    def test_stop_hook_blocks_end_to_end_on_a_committed_unreviewed_change(self):  # T32
        repo = self.mk(("alpha",), git=True)
        h.pass_records(repo)
        h.git_commit_all(repo, "reviewed")
        self.assertPasses(h.run_hook(repo, STOP_NEW))
        (repo / h.SKILLS_REL / "alpha" / "SKILL.md").write_text("---\nname: alpha\n---\n未レビューの変更\n", encoding="utf-8", newline="\n")
        h.git_commit_all(repo, "change without review")
        self.assertEqual(h.git(repo, "status", "--porcelain").out.strip(), "")  # .tmp/ は gitignore 済み
        # 優先順位: SKILL_REVIEW_REPO_ROOT が CLAUDE_PROJECT_DIR に勝つ。CLAUDE_PROJECT_DIR は全 PASS のおとり repo を指す
        decoy = h.make_repo(self.tmp / "decoy", skills=("alpha",))
        h.pass_records(decoy)
        self.assertPasses(h.run_hook(decoy, STOP_NEW))  # おとり単独なら通る（前提）
        env = h.base_env(SKILL_REVIEW_REPO_ROOT=repo.as_posix(), SKILL_REVIEW_NOW=h.NOW)
        r = h.run_hook(decoy, STOP_NEW, env=env)  # run_hook は CLAUDE_PROJECT_DIR に第 1 引数（おとり）を入れる
        self.assertBlocks(r, "alpha")  # 実物の gate と実物の hook の結合（SKILL_REVIEW_REPO_ROOT の repo が評価された）
        self.assertIn("1 skill ずつ", r.data["reason"])
        self.assertTrue((repo / h.STATE_REL).exists())  # state も優先された repo 側に書かれる
        self.assertEqual(self.blocks(), 1)

    def test_stop_hook_does_not_pass_silently_when_the_state_file_is_broken_or_missing(self):  # T20 の補足
        for n, (label, content) in enumerate((("壊れた JSON", "{ broken"), ("stop_blocks が非数値", '{"stop_blocks": "x"}'), ("stop_blocks が負数", '{"stop_blocks": -5}'))):
            with self.subTest(state=label):
                repo = h.make_repo(self.tmp / ("st-%d" % n), skills=("alpha",))
                h.pass_records(repo, names=["review-skill"])
                p = repo / h.STATE_REL
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding="utf-8")
                r = h.run_hook(repo, STOP_ACTIVE)  # 無音で通さない: 0 扱いで数え直して block する
                self.assertBlocks(r, "alpha")
                self.assertEqual(json.loads(p.read_text(encoding="utf-8")).get("stop_blocks"), 1)
        with self.subTest(state=".tmp ディレクトリが無い"):
            repo = h.make_repo(self.tmp / "st-notmp", skills=("alpha",))
            h.pass_records(repo, names=["review-skill"])
            self.assertFalse((repo / ".tmp").exists())
            self.assertBlocks(h.run_hook(repo, STOP_NEW), "alpha")
            self.assertEqual(json.loads((repo / h.STATE_REL).read_text(encoding="utf-8")).get("stop_blocks"), 1)

    def test_stop_hook_handles_a_forty_thousand_char_last_assistant_message_without_silent_failure(self):  # T36
        big = {"hook_event_name": "Stop", "stop_hook_active": False, "last_assistant_message": "あ" * 40000}
        repo = self.unreviewed_repo(("alpha",))
        r = h.run_hook(repo, big)
        self.assertBlocks(r, "alpha")  # 引数の長さ上限で無音に落ちず、未レビューがあれば block する
        self.assertNotIn("Argument list too long", r.err)
        h.pass_records(repo)
        r = h.run_hook(repo, big)
        self.assertPasses(r)  # 全て PASS なら通る（block も無音の失敗もない）
        self.assertNotIn("Argument list too long", r.err)

    def test_hook_counter_increments_only_when_this_hook_blocks(self):  # T34
        repo = self.unreviewed_repo(("alpha",))
        self.assertBlocks(h.run_hook(repo, STOP_NEW), "alpha")
        self.assertEqual(self.blocks(), 1)
        h.pass_records(repo)  # 本 hook の検査は通る状態にする（以降の Stop の block は他の hook のもの）
        for _ in range(3):
            r = h.run_hook(repo, STOP_ACTIVE)
            self.assertPasses(r)
            self.assertEqual(self.blocks(), 1)  # 本 hook が block していないので加算されない
        r = h.run_hook(repo, STOP_NEW)  # 新しい turn で 0 に戻る
        self.assertPasses(r)
        self.assertEqual(self.blocks(), 0)
        # 上限消費の誤りがないこと: 他 hook の継続後に本 hook が初めて block するときも 1 から数える
        (repo / h.SKILLS_REL / "alpha" / "SKILL.md").write_bytes(b"changed\n")
        r = h.run_hook(repo, STOP_ACTIVE)
        self.assertBlocks(r, "alpha")
        self.assertEqual(self.blocks(), 1)


class SessionStartHook(HookBase):
    def test_session_start_hook_reports_counts_without_blocking(self):  # T23
        repo = self.mk(("alpha", "bravo", "charlie", "delta", "echo"), consistent=True)
        h.pass_records(repo, names=["review-skill", "alpha"])
        h.write_ledger(repo, {"bravo": None, "charlie": None})
        r = h.run_hook(repo, SESSION_START)
        self.assertPasses(r)
        msg = self.sys_message(r)
        self.assertRegex(msg, r"PASS 2／未レビューの負債 2（台帳）／要レビュー 2")  # review-skill と alpha が PASS、delta・echo が要レビュー
        self.assertNotIn("\n", msg)  # 1 行
        self.assertNotIn("整合検査: 失敗", msg)

    def test_session_start_hook_runs_consistency_check_and_reports_failures(self):  # T33
        repo = self.mk(("alpha",), consistent=True)
        h.pass_records(repo)
        crit = json.loads((repo / h.CRITERIA_REL).read_text(encoding="utf-8"))
        crit["axes"][0]["weight"] = 25  # weight 合計 105 ≠ 100
        h.write_json(repo / h.CRITERIA_REL, crit)
        self.assertEqual(h.run_render(repo, "--write").code, 0)  # md を再生成して、失敗が weight 合計だけになるようにする
        self.assertEqual(h.run_consistency(repo).code, 1)  # 前提: 整合検査単体も失敗する
        by = {c["id"]: c["ok"] for c in h.run_consistency(repo, "--json").json()["checks"]}
        self.assertEqual(sorted(k for k, ok in by.items() if not ok), ["criteria"])
        r = h.run_hook(repo, SESSION_START)
        self.assertPasses(r)  # block しない
        msg = self.sys_message(r)
        self.assertIn("整合検査: 失敗", msg)
        self.assertIn("（criteria）", msg)
        self.assertNotIn("\n", msg)


if __name__ == "__main__":
    unittest.main()
