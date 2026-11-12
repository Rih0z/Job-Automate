"""pre-git-ledger-gate.sh（git commit の前の、起票の「関連:」欄と knowhow 台帳の検査）の結合試験。

一時ディレクトリに git repo・.claude/issue-tracker.json・.claude/knowhow.json を作り、PreToolUse の入力 JSON を
stdin で hook に渡す。script（issue_tracker.py・knowhow_check.py）はこのリポジトリの実物を使う。
対応: 計画 2026-11-11-issue-handoff-knowhow-redesign.md r3 の J3。
実行: python .claude/hooks/test_pre_git_ledger_gate.py
"""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOOK = HERE / "pre-git-ledger-gate.sh"
GIT = shutil.which("git")


def find_bash():
    for cand in ("C:/Program Files/Git/bin/bash.exe", "C:/Program Files (x86)/Git/bin/bash.exe"):
        if os.path.exists(cand):
            return os.path.normpath(cand)
    return shutil.which("bash") or "bash"


BASH = find_bash()


def git(cwd, *args):
    p = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
                       cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    if p.returncode != 0:
        raise AssertionError(f"git {args}: {p.stderr}")


def kh(status):
    return {"id": "KH-0001", "added": "2026-11-11", "source": "user", "statement": "s", "why": "w",
            "reflect_to": [{"path": "CLAUDE.md"}], "status": status, "retired_reason": None}


@unittest.skipUnless(GIT, "git が無い")
class TestLedgerGate(unittest.TestCase):
    def setUp(self):
        self.top = Path(tempfile.mkdtemp())
        self.root = self.top / "proj"
        (self.root / ".claude").mkdir(parents=True)
        (self.root / "issues" / "open").mkdir(parents=True)
        (self.root / ".claude" / "issue-tracker.json").write_text(json.dumps({
            "sources": [{"type": "md_dirs", "root": "issues", "active": ["open"], "closed": ["closed"]}],
            "related_field": "関連:"}, ensure_ascii=False), encoding="utf-8")
        (self.root / "CLAUDE.md").write_text("<!-- KH-0001 -->\n", encoding="utf-8")
        self.ledger("reflected")
        (self.root / "issues" / "open" / "0001.md").write_text("# 既存\n", encoding="utf-8")
        git(self.root, "init", "-q"); git(self.root, "add", "-A"); git(self.root, "commit", "-qm", "base")
        self.env = dict(os.environ, PYTHONUTF8="1", CLAUDE_PROJECT_DIR=str(self.root),
                        GIT_CEILING_DIRECTORIES=str(self.top))

    def tearDown(self):
        shutil.rmtree(self.top, ignore_errors=True)

    def ledger(self, status):
        (self.root / ".claude" / "knowhow.json").write_text(
            json.dumps({"schema": "knowhow/v1", "entries": [kh(status)]}, ensure_ascii=False), encoding="utf-8")

    def run_hook(self, command):
        payload = {"tool_name": "Bash", "tool_input": {"command": command}, "hook_event_name": "PreToolUse"}
        p = subprocess.run([BASH, str(HOOK)], input=json.dumps(payload), cwd=self.root, capture_output=True,
                           text=True, encoding="utf-8", env=self.env, timeout=60)
        out = p.stdout.strip()
        return p.returncode, (json.loads(out) if out else None), p.stderr

    def denied(self, out):
        return bool(out) and out.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"

    def test_J3_passes_when_both_checks_pass(self):
        rc, out, err = self.run_hook("git commit -m x")
        self.assertEqual(rc, 0, err)
        self.assertIsNone(out, out)
        self.ledger("queued")
        rc, out, err = self.run_hook("git commit -m x")
        self.assertTrue(self.denied(out), "検査が失敗すれば止める（対の確認）")

    def test_J3b_denies_new_issue_without_related_line(self):
        (self.root / "issues" / "open" / "0002.md").write_text("# 新規\n", encoding="utf-8")
        git(self.root, "add", "-A")
        rc, out, err = self.run_hook("git commit -m x")
        self.assertEqual(rc, 0, err)
        self.assertTrue(self.denied(out), out)
        reason = out["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("issues/open/0002.md", reason)
        self.assertIn("related", reason)
        (self.root / "issues" / "open" / "0002.md").write_text("# 新規\n\n関連: なし（related 確認済み）\n",
                                                             encoding="utf-8")
        git(self.root, "add", "-A")
        rc, out, err = self.run_hook("git commit -m x")
        self.assertIsNone(out, out)

    def test_J3c_denies_queued_knowhow(self):
        self.ledger("queued")
        rc, out, err = self.run_hook('git add -A && git commit -m "x"')
        self.assertTrue(self.denied(out), out)
        self.assertIn("KH-0001", out["hookSpecificOutput"]["permissionDecisionReason"])

    def test_J3d_other_commands_are_ignored(self):
        self.ledger("queued")
        for cmd in ("git status", "ls -la", "echo commit", "git push origin main"):
            rc, out, err = self.run_hook(cmd)
            self.assertIsNone(out, cmd)
        rc, out, err = self.run_hook("git commit -m x")
        self.assertTrue(self.denied(out), "同じ状態で git commit なら止める")

    def test_J3e_broken_ledger_is_denied(self):
        (self.root / ".claude" / "knowhow.json").write_text("{broken", encoding="utf-8")
        rc, out, err = self.run_hook("git commit -m x")
        self.assertEqual(rc, 0, err)
        self.assertTrue(self.denied(out), out)
        self.assertIn("knowhow", out["hookSpecificOutput"]["permissionDecisionReason"])

    def test_J3g_timeout_passes_with_system_message(self):
        self.ledger("queued")
        self.env["LEDGER_GATE_TIMEOUT_SEC"] = "0.001"
        rc, out, err = self.run_hook("git commit -m x")
        self.assertEqual(rc, 0, err)
        self.assertFalse(self.denied(out), out)
        self.assertIn("評価できない", (out or {}).get("systemMessage", ""))

    def test_J3h_missing_scripts_pass_with_system_message(self):
        self.ledger("queued")
        hooks = self.root / ".claude" / "hooks"
        hooks.mkdir()
        copy = hooks / "pre-git-ledger-gate.sh"
        shutil.copy(HOOK, copy)  # 隣に .claude/skills/ が無い場所で動かす
        payload = {"tool_name": "Bash", "tool_input": {"command": "git commit -m x"}, "hook_event_name": "PreToolUse"}
        p = subprocess.run([BASH, str(copy)], input=json.dumps(payload), cwd=self.root, capture_output=True,
                           text=True, encoding="utf-8", env=self.env, timeout=60)
        out = json.loads(p.stdout) if p.stdout.strip() else None
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertFalse(self.denied(out), out)
        self.assertIn("評価できない", (out or {}).get("systemMessage", ""))

    def test_J3f_repo_without_ledgers_is_ignored(self):
        (self.root / ".claude" / "knowhow.json").unlink()
        (self.root / ".claude" / "issue-tracker.json").unlink()
        (self.root / "issues" / "open" / "0002.md").write_text("# 新規\n", encoding="utf-8")
        git(self.root, "add", "-A")
        rc, out, err = self.run_hook("git commit -m x")
        self.assertEqual(rc, 0, err)
        self.assertIsNone(out, out)
        self.ledger("queued")
        rc, out, err = self.run_hook("git commit -m x")
        self.assertTrue(self.denied(out), "台帳を置けば検査する（対の確認）")


if __name__ == "__main__":
    unittest.main(verbosity=1)
