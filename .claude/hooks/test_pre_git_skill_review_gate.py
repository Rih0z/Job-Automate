"""pre-git-skill-review-gate.sh の単体テスト（標準ライブラリの unittest）。

一時ディレクトリに git リポジトリと、終了コードを制御できる偽の gate を作り、hook を subprocess で実行する。
hook は stdin の PreToolUse JSON を読み、止める時だけ permissionDecision=deny の JSON を stdout に出す。
実行: python .claude/hooks/test_pre_git_skill_review_gate.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
HOOK = ".claude/hooks/pre-git-skill-review-gate.sh"  # プロジェクトのルートからの相対パス（実際の登録と同じ呼び方）
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))


def find_bash():
    """Windows では PATH 上の bash が WSL のものになることがある（Linux の python を使い、Windows のパスも見えない）。
    実際の hook は Git の bash で動くので、テストでも Git の bash を優先して使う。
    パスは区切りをスラッシュで書き、normpath で OS の形にする（文字列中のバックスラッシュの解釈を避ける）。"""
    for cand in ("C:/Program Files/Git/bin/bash.exe", "C:/Program Files (x86)/Git/bin/bash.exe"):
        if os.path.exists(cand):
            return os.path.normpath(cand)
    return shutil.which("bash") or "bash"


BASH = find_bash()
GIT_USR_BIN = os.path.normpath(os.path.join(os.path.dirname(os.path.dirname(BASH)), "usr", "bin"))

FAKE_GATE = """import sys, time, pathlib
root = pathlib.Path(__file__).resolve().parents[4]
code = int((root / "gate-exit.txt").read_text().strip())
if (root / "gate-sleep.txt").exists():
    time.sleep(float((root / "gate-sleep.txt").read_text().strip()))
print("slide-x: STALE" if code == 1 else "ok")
sys.exit(code)
"""


class Hook(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        gate_dir = os.path.join(self.root, ".claude", "skills", "review-skill", "scripts")
        os.makedirs(gate_dir)
        with open(os.path.join(gate_dir, "skill_review_gate.py"), "w", encoding="utf-8") as f:
            f.write(FAKE_GATE)
        self.git("init", "-q")
        self.git("config", "user.email", "t@example.invalid")
        self.git("config", "user.name", "t")
        self.write("README.md", "base\n")
        self.write(".claude/skills/foo/SKILL.md", "base\n")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "base")
        self.set_gate(0)

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)

    def write(self, rel, text):
        path = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    def set_gate(self, code, sleep=None):
        self.write("gate-exit.txt", str(code))
        sleep_path = os.path.join(self.root, "gate-sleep.txt")
        if sleep is None:
            if os.path.exists(sleep_path):
                os.remove(sleep_path)
        else:
            self.write("gate-sleep.txt", str(sleep))

    def run_hook(self, command, tool="Bash", raw=None, timeout_sec="20"):
        payload = raw if raw is not None else json.dumps(
            {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": {"command": command}})
        env = dict(os.environ, SKILL_REVIEW_REPO_ROOT=self.root, SKILL_REVIEW_TIMEOUT_SEC=timeout_sec)
        p = subprocess.run([BASH, HOOK], input=payload, capture_output=True, text=True, encoding="utf-8",
                           env=env, cwd=REPO)  # hook はプロジェクトのルートから起動される。検査対象のリポジトリは SKILL_REVIEW_REPO_ROOT で渡す
        return p.returncode, p.stdout.strip(), p.stderr.strip()

    def assert_allow(self, out, note=None):
        if note is None:
            self.assertEqual(out, "")
        else:
            data = json.loads(out)
            self.assertNotIn("hookSpecificOutput", data)
            self.assertIn(note, data["systemMessage"])

    def assert_deny(self, out):
        data = json.loads(out)
        hso = data["hookSpecificOutput"]
        self.assertEqual((hso["hookEventName"], hso["permissionDecision"]), ("PreToolUse", "deny"))
        self.assertIn("review-skill", hso["permissionDecisionReason"])
        return hso["permissionDecisionReason"]

    def test_H1_non_bash_tool_is_ignored(self):
        self.set_gate(1)
        code, out, _ = self.run_hook("git push", tool="Edit")
        self.assertEqual((code, out), (0, ""))

    def test_H2_unrelated_command_is_ignored(self):
        self.set_gate(1)
        code, out, _ = self.run_hook("ls -la && git status")
        self.assertEqual((code, out), (0, ""))

    def test_H3_push_denied_when_gate_fails(self):
        self.set_gate(1)
        code, out, _ = self.run_hook("git push origin main")
        self.assertEqual(code, 0)
        reason = self.assert_deny(out)
        self.assertIn("slide-x: STALE", reason)  # gate が挙げた未レビューの skill を理由に載せる

    def test_H4_push_allowed_when_gate_passes(self):
        self.set_gate(0)
        code, out, _ = self.run_hook("git push origin main")
        self.assertEqual((code, out), (0, ""))

    def test_H5_compound_and_option_forms_are_caught(self):
        self.set_gate(1)
        forms = (
            "cd sub && git push", "git -C . push -u origin x", "git add -A; git push", "(git push)",
            "git commit -m x && git push",                    # commit が前にあっても、後ろの push を見る
            "git add -A && git commit -am x && git push origin main",
            'bash -c "git push"', "echo `git push`", "sh -c 'git push'",   # 引用符・バッククォートの中
            'git -C "a b" push', "git --git-dir x push", "git -c core.x=y push",  # 値に空白がある・空白で分ける形
        )
        for cmd in forms:
            with self.subTest(cmd=cmd):
                code, out, _ = self.run_hook(cmd)
                self.assert_deny(out)

    def test_H6_commit_without_skill_changes_is_allowed(self):
        self.set_gate(1)
        self.write("README.md", "changed\n")
        self.git("add", "README.md")
        code, out, _ = self.run_hook('git commit -m "docs"')
        self.assertEqual((code, out), (0, ""))

    def test_H7_commit_with_staged_skill_change_is_denied(self):
        self.set_gate(1)
        self.write(".claude/skills/foo/SKILL.md", "changed\n")
        self.git("add", ".claude/skills/foo/SKILL.md")
        code, out, _ = self.run_hook('git commit -m "skill"')
        self.assert_deny(out)

    def test_H8_commit_a_flag_sees_unstaged_skill_change(self):
        self.set_gate(1)
        self.write(".claude/skills/foo/SKILL.md", "changed\n")  # add していない
        code, out, _ = self.run_hook('git commit -m "skill"')
        self.assertEqual((code, out), (0, ""))       # -a なしなら staged だけ見る
        code, out, _ = self.run_hook('git commit -am "skill"')
        self.assert_deny(out)                         # -a なら未ステージの変更も対象

    def test_H9_unevaluable_gate_passes_with_notice(self):
        self.set_gate(2)
        code, out, _ = self.run_hook("git push")
        self.assertEqual(code, 0)
        self.assert_allow(out, "評価不能")

    def test_H10_timeout_passes_with_notice(self):
        self.set_gate(0, sleep=5)
        code, out, _ = self.run_hook("git push", timeout_sec="1")
        self.assertEqual(code, 0)
        self.assert_allow(out, "評価不能")

    def test_H11_bad_input_passes_silently(self):
        for raw in ("", "not json", "[]", json.dumps({"tool_name": "Bash"})):
            code, out, _ = self.run_hook("", raw=raw)
            self.assertEqual((code, out), (0, ""), raw)

    def test_H12_quoted_mention_is_treated_as_git_command_but_similar_words_are_not(self):
        """gate が失敗している間は、引用符の中の `git push` も止める（bash -c 経由の抜けを塞ぐ代わりの割り切り）。
        別のサブコマンド（commit-tree など）や、語の一部は対象外。"""
        self.set_gate(1)
        code, out, _ = self.run_hook('grep "git push" README.md')
        self.assert_deny(out)
        for cmd in ("git commit-tree abc", "git commit-graph write", "git pushd", "mygit push"):
            with self.subTest(cmd=cmd):
                code, out, _ = self.run_hook(cmd)
                self.assertEqual((code, out), (0, ""))

    def run_hook_without_python(self, command):
        """PATH から python を除いて hook を起動する（Git の bash の標準コマンドだけを見せる）。"""
        payload = json.dumps({"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": command}})
        git_usr_bin = GIT_USR_BIN
        assert os.path.isdir(git_usr_bin), "Git の usr/bin が見つからない: %s" % git_usr_bin  # 試験の前提（cat・dirname を見せる）
        env = dict(os.environ, SKILL_REVIEW_REPO_ROOT=self.root, PATH=git_usr_bin)
        p = subprocess.run([BASH, HOOK], input=payload, capture_output=True, text=True, encoding="utf-8",
                           env=env, cwd=REPO)
        return p.returncode, p.stdout.strip()

    def test_H14_unrelated_commands_never_start_python(self):
        """無関係なコマンドは python を起動せずに通す（全 Bash 呼び出しの前に動くので、起動の遅い環境でも遅延させない）。"""
        for cmd in ("ls -la", "git status", "git log --oneline", "echo hello"):
            code, out = self.run_hook_without_python(cmd)
            self.assertEqual((code, out), (0, ""), cmd)

    def test_H15_python_missing_passes_with_notice_for_push(self):
        code, out = self.run_hook_without_python("git push origin main")
        self.assertEqual(code, 0)
        self.assertIn("python が見つからない", json.loads(out)["systemMessage"])

    def test_H16_commit_then_push_is_stopped_even_without_skill_changes(self):
        self.set_gate(1)
        self.write("README.md", "changed\n")
        self.git("add", "README.md")
        code, out, _ = self.run_hook('git commit -m "docs" && git push')
        reason = self.assert_deny(out)
        self.assertIn("git push", reason)  # commit ではなく push として止める

    def test_H17_commit_forms_that_include_skill_changes(self):
        self.set_gate(1)
        self.write(".claude/skills/foo/SKILL.md", "changed\n")  # add していない
        for cmd in ("git commit .claude/skills/foo/SKILL.md -m x",   # パス指定は未ステージの変更をコミットする
                    "git commit --amend --no-edit",                  # amend は直前の内容を含む（常に確かめる）
                    "git commit --all -m x"):
            with self.subTest(cmd=cmd):
                code, out, _ = self.run_hook(cmd)
                self.assert_deny(out)
        code, out, _ = self.run_hook("git commit -m x")  # 何もステージしていない・-a なし
        self.assertEqual((code, out), (0, ""))

    def test_H18_non_ascii_command(self):
        self.set_gate(1)
        self.write(".claude/skills/foo/SKILL.md", "changed\n")
        self.git("add", ".claude/skills/foo/SKILL.md")
        code, out, _ = self.run_hook('git commit -m "日本語のメッセージ 🚀"')
        self.assert_deny(out)

    def test_H20_real_gate_contract(self):
        """本物の gate の終了コードと hook の判定が一致する（偽の gate だけでは契約の誤りを見逃すため）。"""
        gate = os.path.join(REPO, ".claude", "skills", "review-skill", "scripts", "skill_review_gate.py")
        g = subprocess.run([sys.executable, "-S", gate, "--repo-root", REPO, "--all", "--strict"], capture_output=True)
        payload = json.dumps({"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "git push"}})
        env = dict(os.environ, SKILL_REVIEW_REPO_ROOT=REPO, SKILL_REVIEW_TIMEOUT_SEC="120")
        p = subprocess.run([BASH, HOOK], input=payload, capture_output=True, text=True, encoding="utf-8", env=env, cwd=REPO)
        self.assertEqual(p.returncode, 0)
        if g.returncode == 0:
            self.assertEqual(p.stdout.strip(), "")
        elif g.returncode == 1:
            self.assert_deny(p.stdout.strip())

    def test_H13_registered_in_settings(self):
        with open(os.path.join(REPO, ".claude", "settings.json"), encoding="utf-8") as f:
            pre = json.load(f)["hooks"]["PreToolUse"]
        entries = [h for group in pre for h in group["hooks"]]
        self.assertTrue(any("pre-git-skill-review-gate.sh" in h["command"] for h in entries))
        self.assertTrue(all(group.get("matcher") == "Bash" for group in pre
                            if any("pre-git-skill-review-gate.sh" in h["command"] for h in group["hooks"])))
        mine = [h for h in entries if "pre-git-skill-review-gate.sh" in h["command"]]
        self.assertTrue(all(h.get("type") == "command" and h.get("timeout") == 30 for h in mine))
        with open(os.path.join(REPO, ".claude", "settings.json"), encoding="utf-8") as f:
            hooks = json.load(f)["hooks"]
        for event in ("SessionStart", "Stop"):  # 既存の登録を壊していない
            cmds = [h["command"] for g in hooks[event] for h in g["hooks"]]
            self.assertTrue(any("hook-skill-review-gate.sh" in c for c in cmds), event)


if __name__ == "__main__":
    unittest.main()
