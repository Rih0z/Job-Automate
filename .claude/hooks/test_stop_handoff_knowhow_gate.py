"""stop-handoff-knowhow-gate.sh と、SessionStart の開始時刻の記録（hook-session-start-setup.sh）の結合試験。

hook には stdin の JSON（Stop / SessionStart の入力）を渡し、stdout の JSON を確かめる。
データの置き場は CLAUDE_PROJECT_DIR で一時ディレクトリに向け、script はこのリポジトリの実物を使う。
対応: 計画 2026-11-11-issue-handoff-knowhow-redesign.md r3 の J1・J2（r2 の追加を含む）。
実行: python .claude/hooks/test_stop_handoff_knowhow_gate.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
HOOK = HERE / "stop-handoff-knowhow-gate.sh"
SESSION_START = REPO / ".claude" / "skills" / "agent-harness-bootstrap" / "scripts" / "hook-session-start-setup.sh"
HL = REPO / ".claude" / "skills" / "agent-harness-bootstrap" / "scripts" / "handoff_lifecycle.py"
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


def kh(i, status):
    return {"id": i, "added": "2026-11-11", "source": "user", "statement": "s", "why": "w",
            "reflect_to": [{"path": "CLAUDE.md"}], "status": status, "retired_reason": None}


class Base(unittest.TestCase):
    def setUp(self):
        self.top = Path(tempfile.mkdtemp())
        self.root = self.top / "proj"
        (self.root / ".tmp" / "handoffs").mkdir(parents=True)
        (self.root / ".claude").mkdir()
        self.env = dict(os.environ, PYTHONUTF8="1", CLAUDE_PROJECT_DIR=str(self.root),
                        GIT_CEILING_DIRECTORIES=str(self.top))
        self.env.pop("PROVENANCE_ROOT", None)

    def tearDown(self):
        shutil.rmtree(self.top, ignore_errors=True)

    def run_hook(self, hook, payload):
        p = subprocess.run([BASH, str(hook)], input=json.dumps(payload), cwd=self.root, capture_output=True,
                           text=True, encoding="utf-8", env=self.env, timeout=60)
        out = p.stdout.strip()
        return p.returncode, (json.loads(out) if out else None), p.stderr

    def stop(self, sid="S1", active=False):
        return self.run_hook(HOOK, {"session_id": sid, "stop_hook_active": active, "hook_event_name": "Stop"})

    def start(self, sid="S1", source="startup"):
        return self.run_hook(SESSION_START, {"session_id": sid, "source": source, "hook_event_name": "SessionStart"})

    def session_file(self, sid):
        return self.root / ".tmp" / "session-start" / f"{sid}.json"

    def set_start(self, sid, when):
        f = self.session_file(sid)
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps({"session_id": sid, "started_at": when.isoformat(timespec="seconds")}), encoding="utf-8")

    def receive(self, name, when):
        f = self.root / ".tmp" / "handoffs" / name
        f.write_text("---\nissue: none\n---\n# 引継ぎ\n", encoding="utf-8")
        p = subprocess.run([sys.executable, str(HL), "receive", str(f), "--now", when.isoformat(timespec="seconds")],
                           cwd=self.root, capture_output=True, text=True, encoding="utf-8", env=self.env)
        self.assertEqual(p.returncode, 0, p.stderr)
        return f


class TestSessionStartTime(Base):
    def test_J1c_session_start_records_time_once_and_cleans_old_files(self):
        old = self.session_file("OLD")
        old.parent.mkdir(parents=True, exist_ok=True)
        old.write_text("{}", encoding="utf-8")
        t = time.time() - 8 * 86400
        os.utime(old, (t, t))
        recent = self.session_file("RECENT")
        recent.write_text("{}", encoding="utf-8")
        t6 = time.time() - 6 * 86400
        os.utime(recent, (t6, t6))
        rc, out, err = self.start("S2", "startup")
        self.assertEqual(rc, 0, err)
        f = self.session_file("S2")
        self.assertTrue(f.exists())
        first = f.read_bytes()
        self.assertIn("started_at", json.loads(first))
        time.sleep(1.1)
        for src in ("compact", "resume", "clear"):
            rc, out, err = self.start("S2", src)
            self.assertEqual(rc, 0, err)
        self.assertEqual(f.read_bytes(), first, "再発火で開始時刻を上書きしない")
        self.assertFalse(old.exists(), "7 日を超えた file は消す")
        self.assertTrue(recent.exists(), "7 日以内の file は残す")

    def test_J1d_unsafe_session_id_is_ignored_safe_one_is_recorded(self):
        rc, out, err = self.start("../evil", "startup")
        self.assertEqual(rc, 0, err)
        self.assertFalse((self.root / ".tmp" / "evil.json").exists())
        self.assertEqual(list((self.root / ".tmp").glob("**/*evil*")), [])
        rc, out, err = self.start("abc-123_DEF", "startup")
        self.assertEqual(rc, 0, err)
        self.assertTrue(self.session_file("abc-123_DEF").exists())


class TestStopHandoff(Base):
    def test_J1_blocks_once_for_handoff_received_in_this_session(self):
        now = datetime.now(timezone.utc).astimezone()
        self.set_start("S1", now - timedelta(hours=1))
        self.receive("mine.md", now - timedelta(minutes=30))
        rc, out, err = self.stop("S1", active=False)
        self.assertEqual(rc, 0, err)
        self.assertEqual(out and out.get("decision"), "block", out)
        self.assertIn("mine.md", out["reason"])
        self.assertIn("done", out["reason"])
        rc, out, err = self.stop("S1", active=True)
        self.assertIsNone(out, "stop_hook_active=true では block しない")

    def test_J1b_handoff_received_before_session_start_does_not_block(self):
        now = datetime.now(timezone.utc).astimezone()
        self.set_start("S1", now - timedelta(hours=1))
        self.receive("older.md", now - timedelta(hours=3))
        rc, out, err = self.stop("S1")
        self.assertEqual(rc, 0, err)
        self.assertIsNone(out, "開始前の受領では止めない")
        self.receive("mine.md", now - timedelta(minutes=30))
        rc, out, err = self.stop("S1")
        self.assertEqual(out and out.get("decision"), "block", out)
        self.assertIn("mine.md", out["reason"])
        self.assertNotIn("older.md", out["reason"])

    def test_J1e_no_session_file_does_nothing(self):
        now = datetime.now(timezone.utc).astimezone()
        self.receive("mine.md", now - timedelta(minutes=30))
        rc, out, err = self.stop("S-unknown")
        self.assertEqual(rc, 0, err)
        self.assertIsNone(out)
        self.set_start("S-unknown", now - timedelta(hours=1))
        rc, out, err = self.stop("S-unknown")
        self.assertEqual(out and out.get("decision"), "block", "開始時刻の file があれば判定する")

    def test_J1f_missing_scripts_pass_with_system_message(self):
        now = datetime.now(timezone.utc).astimezone()
        self.set_start("S1", now - timedelta(hours=1))
        self.receive("mine.md", now - timedelta(minutes=30))
        hooks = self.root / ".claude" / "hooks"
        hooks.mkdir()
        copy = hooks / "stop-handoff-knowhow-gate.sh"
        shutil.copy(HOOK, copy)  # 隣に .claude/skills/ が無い場所で動かす
        rc, out, err = self.run_hook(copy, {"session_id": "S1", "stop_hook_active": False})
        self.assertEqual(rc, 0, err)
        self.assertIsNotNone(out)
        self.assertNotIn("decision", out)
        self.assertIn("評価できない", out.get("systemMessage", ""))

    def test_J12_other_hook_blocked_first_then_fires_next_turn(self):
        now = datetime.now(timezone.utc).astimezone()
        self.set_start("S1", now - timedelta(hours=1))
        self.receive("mine.md", now - timedelta(minutes=30))
        rc, out, err = self.stop("S1", active=True)
        self.assertIsNone(out, "別の hook の block で継続中の turn では発火しない")
        rc, out, err = self.stop("S1", active=False)
        self.assertEqual(out and out.get("decision"), "block", out)


@unittest.skipUnless(GIT, "git が無い")
class TestStopKnowhow(Base):
    def setUp(self):
        super().setUp()
        (self.root / "CLAUDE.md").write_text("<!-- KH-0001 --> <!-- KH-0002 -->\n", encoding="utf-8")
        self.ledger([kh("KH-0001", "queued")])
        git(self.root, "init", "-q"); git(self.root, "add", "-A"); git(self.root, "commit", "-qm", "base")

    def ledger(self, entries):
        (self.root / ".claude" / "knowhow.json").write_text(
            json.dumps({"schema": "knowhow/v1", "entries": entries}, ensure_ascii=False), encoding="utf-8")

    def test_J2_new_queued_blocks_once(self):
        self.ledger([kh("KH-0001", "queued"), kh("KH-0002", "queued")])
        rc, out, err = self.stop("S1", active=False)
        self.assertEqual(rc, 0, err)
        self.assertEqual(out and out.get("decision"), "block", out)
        self.assertIn("KH-0002", out["reason"])
        self.assertNotIn("KH-0001", out["reason"], "前からある queued は block の理由に入れない")
        rc, out, err = self.stop("S1", active=True)
        self.assertIsNone(out)

    # 計画 2026-11-12-issue-bp-alignment.md r2 の S-long・S-crash
    def test_S_long_input_is_still_checked(self):
        self.ledger([kh("KH-0001", "queued"), kh("KH-0002", "queued")])
        rc, out, err = self.run_hook(HOOK, {"session_id": "S1", "stop_hook_active": False,
                                            "hook_event_name": "Stop", "padding": "a" * 200000})
        self.assertEqual(rc, 0, err)
        self.assertEqual(out and out.get("decision"), "block", (out, err[-500:]))

    def test_S_crash_passes_with_system_message(self):
        self.ledger([kh("KH-0001", "queued"), kh("KH-0002", "queued")])
        bad = self.top / "badpy"
        bad.mkdir()
        (bad / "json.py").write_text("raise RuntimeError('壊れた json')\n", encoding="utf-8")
        self.env["PYTHONPATH"] = str(bad)
        payload = {"session_id": "S1", "stop_hook_active": False, "hook_event_name": "Stop"}
        p = subprocess.run([BASH, str(HOOK)], input=json.dumps(payload), cwd=self.root, capture_output=True,
                           text=True, encoding="utf-8", env=self.env, timeout=60)
        rc, err = p.returncode, p.stderr
        out = json.loads(p.stdout) if p.stdout.strip() else None  # python は -S で起動するので .pth の出力は混ざらない
        self.assertEqual(rc, 0, err)
        self.assertNotEqual((out or {}).get("decision"), "block", out)
        self.assertIn("評価できない", (out or {}).get("systemMessage", ""))
        self.assertIn("終了コード", (out or {}).get("systemMessage", ""))

    def test_J2b_only_old_queued_passes_with_system_message(self):
        rc, out, err = self.stop("S1", active=False)
        self.assertEqual(rc, 0, err)
        self.assertIsNotNone(out)
        self.assertNotIn("decision", out)
        self.assertIn("KH-0001", out.get("systemMessage", ""))

    def test_J2c_other_hook_blocked_first_then_fires_next_turn(self):
        self.ledger([kh("KH-0001", "queued"), kh("KH-0002", "queued")])
        rc, out, err = self.stop("S1", active=True)
        self.assertIsNone(out)
        rc, out, err = self.stop("S1", active=False)
        self.assertEqual(out and out.get("decision"), "block", out)


if __name__ == "__main__":
    unittest.main(verbosity=1)
