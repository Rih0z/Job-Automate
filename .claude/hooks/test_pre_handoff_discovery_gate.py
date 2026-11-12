"""pre-handoff-discovery-gate.sh（handoff を書く前に discovery-log の queued を止める）の結合試験。

一時ディレクトリに .tmp/discovery-log.md を作り、PreToolUse の入力 JSON を stdin で hook に渡す。
対応: 計画 2026-11-12-issue-bp-alignment.md r2 の B（H1〜H10）。
実行: python .claude/hooks/test_pre_handoff_discovery_gate.py
"""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOOK = HERE / "pre-handoff-discovery-gate.sh"


def find_bash():
    for cand in ("C:/Program Files/Git/bin/bash.exe", "C:/Program Files (x86)/Git/bin/bash.exe"):
        if os.path.exists(cand):
            return os.path.normpath(cand)
    return shutil.which("bash") or "bash"


BASH = find_bash()


def entry(summary, status):
    return json.dumps({"ts": "2026-11-12T00:00:00-08:00", "summary": summary, "location": "a/b.md:1",
                       "status": status}, ensure_ascii=False)


class TestHandoffDiscoveryGate(unittest.TestCase):
    def setUp(self):
        self.top = Path(tempfile.mkdtemp())
        self.root = self.top / "proj"
        (self.root / ".tmp" / "handoffs").mkdir(parents=True)
        self.env = dict(os.environ, PYTHONUTF8="1", CLAUDE_PROJECT_DIR=str(self.root))

    def tearDown(self):
        shutil.rmtree(self.top, ignore_errors=True)

    def log(self, *lines, raw=None):
        f = self.root / ".tmp" / "discovery-log.md"
        f.write_bytes(raw if raw is not None else ("\n".join(lines) + "\n").encode("utf-8"))

    def run_hook(self, file_path, tool="Write"):
        payload = {"tool_name": tool, "tool_input": {"file_path": file_path, "content": "x"},
                   "hook_event_name": "PreToolUse"}
        p = subprocess.run([BASH, str(HOOK)], input=json.dumps(payload), cwd=self.root, capture_output=True,
                           text=True, encoding="utf-8", env=self.env, timeout=60)
        out = p.stdout.strip()
        return p.returncode, (json.loads(out) if out else None), p.stderr

    def denied(self, out):
        return bool(out) and out.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"

    def reason(self, out):
        return out["hookSpecificOutput"]["permissionDecisionReason"]

    def handoff(self, name="2026-11-12-x.md"):
        return str(self.root / ".tmp" / "handoffs" / name)

    def test_H1_queued_denies_with_count_and_summaries(self):
        self.log(entry("一つ目の気づき", "queued"), entry("済んだもの", "done"), entry("二つ目の気づき", "queued"))
        rc, out, err = self.run_hook(self.handoff())
        self.assertEqual(rc, 0, err)
        self.assertTrue(self.denied(out), (out, err))
        r = self.reason(out)
        self.assertIn("2 件", r)
        self.assertIn("一つ目の気づき", r)
        self.assertIn("二つ目の気づき", r)
        self.assertNotIn("済んだもの", r)

    def test_H2_no_queued_is_silent(self):
        self.log(entry("a", "done"), entry("b", "issued"), entry("c", "knowhow"))
        rc, out, err = self.run_hook(self.handoff())
        self.assertEqual(rc, 0, err)
        self.assertIsNone(out, out)

    def test_H3_other_paths_are_ignored(self):
        self.log(entry("a", "queued"))
        for p in (str(self.root / "docs" / "x.md"), str(self.root / ".tmp" / "plans" / "handoffs-note.md")):
            rc, out, err = self.run_hook(p)
            self.assertIsNone(out, p)

    def test_H4_no_discovery_log_is_silent(self):
        rc, out, err = self.run_hook(self.handoff())
        self.assertEqual(rc, 0, err)
        self.assertIsNone(out, out)

    def test_H5_unreadable_line_denies_with_line_number_and_fix(self):
        self.log(entry("a", "done"), '{"summary": "x", "location": "C:\\Users\\a", "status": "done"}')
        rc, out, err = self.run_hook(self.handoff())
        self.assertTrue(self.denied(out), (out, err))
        r = self.reason(out)
        self.assertIn("2 行目", r)
        self.assertIn("/", r)

    def test_H5c_non_object_and_undecodable_lines_deny(self):
        self.log(raw=(entry("a", "done") + "\n" + '"queued"' + "\n").encode("utf-8") + b"\xff\xfe bad\n")
        rc, out, err = self.run_hook(self.handoff())
        self.assertTrue(self.denied(out), (out, err))
        r = self.reason(out)
        self.assertIn("2, 3 行目", r)

    def test_H11_python_crash_passes_with_system_message(self):
        self.log(entry("a", "queued"))
        bad = self.top / "badpy"
        bad.mkdir()
        (bad / "json.py").write_text("raise RuntimeError('壊れた json')\n", encoding="utf-8")
        self.env["PYTHONPATH"] = str(bad)
        rc, out, err = self.run_hook(self.handoff())
        self.assertEqual(rc, 0, err)
        self.assertFalse(self.denied(out), out)
        self.assertIn("終了コード", (out or {}).get("systemMessage", ""))

    def test_H12_unreadable_input_passes_with_system_message(self):
        p = subprocess.run([BASH, str(HOOK)], input="{not json .tmp/handoffs/x.md", cwd=self.root,
                           capture_output=True, text=True, encoding="utf-8", env=self.env, timeout=60)
        self.assertEqual(p.returncode, 0, p.stderr)
        out = json.loads(p.stdout) if p.stdout.strip() else {}
        self.assertIn("入力", out.get("systemMessage", ""))

    def test_H5b_blank_lines_crlf_and_bom_are_allowed(self):
        text = "\r\n".join([entry("a", "done"), "", entry("b", "issued")]) + "\r\n"
        self.log(raw=b"\xef\xbb\xbf" + text.encode("utf-8"))
        rc, out, err = self.run_hook(self.handoff())
        self.assertEqual(rc, 0, err)
        self.assertIsNone(out, out)

    def test_H6_edit_and_multiedit_are_gated(self):
        self.log(entry("a", "queued"))
        for tool in ("Edit", "MultiEdit"):
            rc, out, err = self.run_hook(self.handoff(), tool=tool)
            self.assertTrue(self.denied(out), (tool, out))

    def test_H7_relative_and_backslash_paths(self):
        self.log(entry("a", "queued"))
        for p in (".tmp/handoffs/x.md", str(self.root / ".tmp" / "handoffs" / "x.md").replace("/", "\\")):
            rc, out, err = self.run_hook(p)
            self.assertTrue(self.denied(out), (p, out))

    def test_H8_dotdot_path_is_normalized(self):
        self.log(entry("a", "queued"))
        rc, out, err = self.run_hook(str(self.root / "docs" / ".." / ".tmp" / "handoffs" / "x.md"))
        self.assertTrue(self.denied(out), out)
        rc, out, err = self.run_hook(str(self.root / ".tmp" / "handoffs" / ".." / "x.md"))
        self.assertIsNone(out, "handoffs の外に出るパスは対象外")

    @unittest.skipUnless(os.name == "nt", "大文字小文字を区別しないのは Windows だけ")
    def test_H9_case_insensitive_on_windows(self):
        self.log(entry("a", "queued"))
        rc, out, err = self.run_hook(str(self.root / ".TMP" / "Handoffs" / "x.md"))
        self.assertTrue(self.denied(out), out)

    def test_H10_no_python_passes_with_system_message(self):
        usr_bin = Path(BASH).parent.parent / "usr" / "bin"
        if not (usr_bin / "cat.exe").exists() and not (usr_bin / "cat").exists():
            self.skipTest("Git の usr/bin が無い")
        env = dict(self.env, PATH=str(usr_bin))
        probe = subprocess.run([BASH, "-c", "command -v python3 || command -v python || command -v py"],
                               capture_output=True, text=True, env=env)
        if probe.stdout.strip():
            self.skipTest("usr/bin に python がある")
        self.log(entry("a", "queued"))
        payload = {"tool_name": "Write", "tool_input": {"file_path": self.handoff()}, "hook_event_name": "PreToolUse"}
        p = subprocess.run([BASH, str(HOOK)], input=json.dumps(payload), cwd=self.root, capture_output=True,
                           text=True, encoding="utf-8", env=env, timeout=60)
        self.assertEqual(p.returncode, 0, p.stderr)
        out = json.loads(p.stdout) if p.stdout.strip() else {}
        self.assertFalse(self.denied(out), out)
        self.assertIn("評価できない", out.get("systemMessage", ""))


if __name__ == "__main__":
    unittest.main(verbosity=1)
