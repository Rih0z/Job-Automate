"""handoff_lifecycle.py の試験（unittest、標準ライブラリだけ）。

実行: python .claude/skills/agent-harness-bootstrap/scripts/test_handoff_lifecycle.py
各試験は一時ディレクトリに .tmp/handoffs/ を作り、そこを cwd にして script を subprocess で呼ぶ。
時刻は --now と os.utime で固定する。本文には印 BODY-MARKER-XYZ を入れ、出力に本文が出ないことを確かめる。
"""
import hashlib
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

SCRIPT = Path(__file__).resolve().parent / "handoff_lifecycle.py"
NOW = datetime(2026, 11, 11, 12, 0, 0, tzinfo=timezone(timedelta(hours=-8)))
NOW_S = NOW.isoformat()
MARK = "BODY-MARKER-XYZ"


def body(title="引継ぎ: テスト用", extra=""):
    return f"# {title}\n\nこのファイル: x\n\n{MARK}\n{extra}"


class Base(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.hd = self.root / ".tmp" / "handoffs"
        self.hd.mkdir(parents=True)
        self.ledger = self.root / ".tmp" / "handoff-ledger.json"

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def run_cli(self, *args):
        env = dict(os.environ, PYTHONUTF8="1")
        p = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=self.root,
                           capture_output=True, text=True, encoding="utf-8", env=env)
        return p.returncode, p.stdout, p.stderr

    def mk(self, name, text=None, age_days=None, newline="\n", bom=False):
        f = self.hd / name
        data = (text if text is not None else body()).replace("\n", newline)
        raw = data.encode("utf-8")
        if bom:
            raw = b"\xef\xbb\xbf" + raw
        f.write_bytes(raw)
        if age_days is not None:
            t = (NOW - timedelta(days=age_days)).timestamp()
            os.utime(f, (t, t))
        return f

    def load_ledger(self):
        return json.loads(self.ledger.read_text(encoding="utf-8"))

    def receive_at(self, f, hours_ago):
        now = (NOW - timedelta(hours=hours_ago)).isoformat()
        rc, out, err = self.run_cli("receive", str(f), "--now", now)
        self.assertEqual(rc, 0, err)


class TestReceive(Base):
    def test_U1_receive_records_without_touching_file(self):
        f = self.mk("a.md", age_days=1)
        before = f.read_bytes(); mt = f.stat().st_mtime
        rc, out, err = self.run_cli("receive", str(f), "--now", NOW_S)
        self.assertEqual(rc, 0, err)
        self.assertIn("received:", out)
        led = self.load_ledger()["received"]
        self.assertEqual(list(led), [os.path.normcase(str(f.resolve()))])
        e = list(led.values())[0]
        self.assertEqual(e["sha256"], hashlib.sha256(before).hexdigest())
        self.assertEqual(e["matched_by"], "path")
        self.assertTrue(e["received_at"].startswith("2026-11-11T12:00:00"))
        self.assertEqual(f.read_bytes(), before)
        self.assertEqual(f.stat().st_mtime, mt)

    def test_U2_receive_twice_keeps_one_entry_and_updates_time(self):
        f = self.mk("a.md")
        self.receive_at(f, 5)
        self.receive_at(f, 0)
        led = self.load_ledger()["received"]
        self.assertEqual(len(led), 1)
        self.assertTrue(list(led.values())[0]["received_at"].startswith("2026-11-11T12:00:00"))

    def test_U3_receive_rejects_paths_outside_handoffs(self):
        (self.root / "docs").mkdir()
        outside = self.root / "docs" / "x.md"; outside.write_text("x", encoding="utf-8")
        txt = self.hd / "x.txt"; txt.write_text("x", encoding="utf-8")
        (self.hd / "sub").mkdir(); sub = self.hd / "sub" / "x.md"; sub.write_text("x", encoding="utf-8")
        up = self.root / ".tmp" / "x.md"; up.write_text("x", encoding="utf-8")
        dotdot = str(self.hd) + os.sep + ".." + os.sep + "x.md"
        mddir = self.hd / "d.md"; mddir.mkdir()
        for p in [str(outside), str(txt), str(sub), dotdot, str(mddir)]:
            rc, out, err = self.run_cli("receive", p, "--now", NOW_S)
            self.assertEqual(rc, 2, p)
        self.assertFalse(self.ledger.exists())

    def test_U4_receive_rejects_symlink_to_outside(self):
        (self.root / "docs").mkdir()
        target = self.root / "docs" / "t.md"; target.write_text("x", encoding="utf-8")
        link = self.hd / "link.md"
        try:
            os.symlink(target, link)
        except (OSError, NotImplementedError):
            self.skipTest("シンボリックリンクを作れない環境")
        rc, out, err = self.run_cli("receive", str(link), "--now", NOW_S)
        self.assertEqual(rc, 2)

    def test_U5_receive_by_title(self):
        self.mk("a.md", body("引継ぎ: A"))
        self.mk("b.md", body("引継ぎ: B"))
        self.mk("b2.md", body("引継ぎ: B"))
        rc, out, err = self.run_cli("receive", "--title", "引継ぎ: A", "--now", NOW_S)
        self.assertEqual(rc, 0, err)
        e = list(self.load_ledger()["received"].values())[0]
        self.assertEqual(e["matched_by"], "title")
        rc, out, err = self.run_cli("receive", "--title", "引継ぎ: Z", "--now", NOW_S)
        self.assertEqual(rc, 4)
        rc, out, err = self.run_cli("receive", "--title", "引継ぎ: B", "--now", NOW_S)
        self.assertEqual(rc, 5)
        self.assertIn("b.md", out + err); self.assertIn("b2.md", out + err)

    def test_U6_title_in_body_only_does_not_match(self):
        self.mk("a.md", body("別の見出し", extra="# 本文の中\n引継ぎ: A\n"))
        rc, out, err = self.run_cli("receive", "--title", "引継ぎ: A", "--now", NOW_S)
        self.assertEqual(rc, 4)

    def test_U18_bom_crlf_japanese_title_and_frontmatter(self):
        f = self.mk("a.md", "---\ncreated_at: 2026-11-01\n---\n" + body("引継ぎ: 日本語"),
                    newline="\r\n", bom=True)
        before = f.read_bytes()
        rc, out, err = self.run_cli("receive", "--title", "引継ぎ: 日本語", "--now", NOW_S)
        self.assertEqual(rc, 0, err)
        self.assertEqual(f.read_bytes(), before)

    def test_U19_invalid_now(self):
        f = self.mk("a.md")
        rc, out, err = self.run_cli("receive", str(f), "--now", "not-a-date")
        self.assertEqual(rc, 2)


class TestDone(Base):
    def test_U7_done_deletes_received(self):
        f = self.mk("a.md"); self.receive_at(f, 1)
        rc, out, err = self.run_cli("done", str(f))
        self.assertEqual(rc, 0, err)
        self.assertFalse(f.exists())
        self.assertIn("deleted:", out); self.assertIn(str(f.resolve()), out)
        self.assertEqual(self.load_ledger()["received"], {})

    def test_U8_done_refuses_unreceived(self):
        f = self.mk("a.md")
        rc, out, err = self.run_cli("done", str(f))
        self.assertEqual(rc, 3)
        self.assertTrue(f.exists())

    def test_U9_done_force_deletes_unreceived(self):
        f = self.mk("a.md")
        rc, out, err = self.run_cli("done", str(f), "--force")
        self.assertEqual(rc, 0, err)
        self.assertFalse(f.exists())

    def test_U10_done_missing_path(self):
        rc, out, err = self.run_cli("done", str(self.hd / "nope.md"))
        self.assertEqual(rc, 2)
        f = self.mk("gone.md"); self.receive_at(f, 1); f.unlink()
        rc, out, err = self.run_cli("done", str(f))
        self.assertEqual(rc, 0, err)
        self.assertEqual(self.load_ledger()["received"], {})

    def test_U20_done_refuses_changed_after_receipt(self):
        f = self.mk("a.md"); self.receive_at(f, 1)
        f.write_text(body(extra="追記\n"), encoding="utf-8")
        rc, out, err = self.run_cli("done", str(f))
        self.assertEqual(rc, 7)
        self.assertTrue(f.exists())
        self.assertIn("receive", err)

    def test_U20b_done_ok_when_only_mtime_changed(self):
        f = self.mk("a.md"); self.receive_at(f, 1)
        t = time.time() + 100; os.utime(f, (t, t))
        rc, out, err = self.run_cli("done", str(f))
        self.assertEqual(rc, 0, err)

    def test_U21_done_title_matched_needs_confirmed(self):
        f = self.mk("a.md", body("引継ぎ: A"))
        rc, out, err = self.run_cli("receive", "--title", "引継ぎ: A", "--now", NOW_S)
        self.assertEqual(rc, 0, err)
        rc, out, err = self.run_cli("done", str(f))
        self.assertEqual(rc, 6)
        self.assertTrue(f.exists())
        rc, out, err = self.run_cli("done", str(f), "--confirmed")
        self.assertEqual(rc, 0, err)
        self.assertFalse(f.exists())

    @unittest.skipUnless(os.name == "nt", "大文字小文字を区別しない Windows だけ")
    def test_U23_done_case_insensitive_path(self):
        f = self.mk("a.md"); self.receive_at(f, 1)
        rc, out, err = self.run_cli("done", str(f).upper())
        self.assertEqual(rc, 0, err)
        self.assertFalse(f.exists())


class TestRemindSweep(Base):
    def test_U11_remind_received_suspected_interruption_without_body(self):
        a = self.mk("old-received.md"); self.receive_at(a, 5)
        b = self.mk("new-received.md"); self.receive_at(b, 1)
        rc, out, err = self.run_cli("remind", "--now", NOW_S)
        self.assertEqual(rc, 0)
        lines = out.splitlines()
        la = [l for l in lines if "old-received.md" in l]
        lb = [l for l in lines if "new-received.md" in l]
        self.assertTrue(la and "中断の疑い" in la[0], out)
        self.assertTrue(lb and "中断の疑い" not in lb[0], out)
        self.assertNotIn(MARK, out)

    def test_U12_remind_unreceived_old_only(self):
        self.mk("d40.md", age_days=40)
        self.mk("d10.md", age_days=10)
        r = self.mk("r40.md", age_days=40); self.receive_at(r, 1)
        rc, out, err = self.run_cli("remind", "--now", NOW_S)
        self.assertEqual(rc, 0)
        self.assertIn("d40.md", out)
        self.assertNotIn("d10.md", out)
        unrec = [l for l in out.splitlines() if "未受領" in l]
        self.assertTrue(unrec)
        self.assertFalse(any("r40.md" in l for l in unrec), out)

    def test_U13_remind_caps_names(self):
        for i in range(7):
            self.mk(f"old{i}.md", age_days=40)
        rc, out, err = self.run_cli("remind", "--now", NOW_S)
        self.assertIn("7 件", out)
        self.assertEqual(sum(out.count(f"old{i}.md") for i in range(7)), 5)

    def test_U14_remind_silent_cases(self):
        rc, out, err = self.run_cli("remind", "--now", NOW_S)
        self.assertEqual((rc, out), (0, ""))
        shutil.rmtree(self.hd)
        rc, out, err = self.run_cli("remind", "--now", NOW_S)
        self.assertEqual((rc, out), (0, ""))
        self.hd.mkdir()
        self.ledger.write_text("{broken", encoding="utf-8")
        rc, out, err = self.run_cli("remind", "--now", NOW_S)
        self.assertEqual((rc, out), (0, ""))
        self.assertTrue(err)

    def test_U15_dir_must_be_tmp_handoffs(self):
        (self.root / "docs").mkdir()
        (self.root / "docs" / "x.md").write_text("x", encoding="utf-8")
        for cmd in (["remind"], ["sweep"], ["sweep", "--apply"]):
            rc, out, err = self.run_cli(*cmd, "--dir", str(self.root / "docs"), "--now", NOW_S)
            self.assertEqual(rc, 2, cmd)
        self.assertTrue((self.root / "docs" / "x.md").exists())

    def test_U16_sweep_default_lists_only(self):
        f = self.mk("d100.md", age_days=100)
        self.mk("d40.md", age_days=40)
        self.mk("d10.md", age_days=10)
        rc, out, err = self.run_cli("sweep", "--now", NOW_S)
        self.assertEqual(rc, 0, err)
        self.assertIn("d100.md", out)
        self.assertIn("d40.md", out)  # 既定は remind と同じ 30 日
        self.assertNotIn("d10.md", out)
        self.assertTrue(f.exists())

    def test_U17_sweep_apply_archives_only_old_unreceived(self):
        old = self.mk("d100.md", age_days=100)
        new = self.mk("d10.md", age_days=10)
        rec = self.mk("r100.md", age_days=100); self.receive_at(rec, 1)
        arch = self.root / ".tmp" / "archive" / "handoffs"
        arch.mkdir(parents=True); (arch / "d100.md").write_text("先にあった", encoding="utf-8")
        rc, out, err = self.run_cli("sweep", "--apply", "--now", NOW_S)
        self.assertEqual(rc, 0, err)
        self.assertFalse(old.exists())
        self.assertTrue(new.exists()); self.assertTrue(rec.exists())
        self.assertEqual((arch / "d100.md").read_text(encoding="utf-8"), "先にあった")
        self.assertEqual((arch / "d100-1.md").read_text(encoding="utf-8"), body())

    def test_U17b_sweep_days_option(self):
        self.mk("d40.md", age_days=40)
        rc, out, err = self.run_cli("sweep", "--days", "30", "--now", NOW_S)
        self.assertIn("d40.md", out)

    def test_U22_corrupt_ledger_backed_up_on_write(self):
        self.ledger.write_text("{broken", encoding="utf-8")
        f = self.mk("a.md")
        rc, out, err = self.run_cli("receive", str(f), "--now", NOW_S)
        self.assertEqual(rc, 0, err)
        baks = list((self.root / ".tmp").glob("handoff-ledger.json.bak-*"))
        self.assertEqual(len(baks), 1)
        self.assertEqual(baks[0].read_text(encoding="utf-8"), "{broken")
        self.assertEqual(len(self.load_ledger()["received"]), 1)

    def test_U22b_sweep_apply_refuses_with_corrupt_ledger(self):
        old = self.mk("d100.md", age_days=100)
        self.ledger.write_text("{broken", encoding="utf-8")
        rc, out, err = self.run_cli("sweep", "--apply", "--now", NOW_S)
        self.assertEqual(rc, 2)
        self.assertTrue(old.exists())

    def test_U24_remind_names_sweep_days_that_matches(self):
        self.mk("d40.md", age_days=40)
        rc, out, err = self.run_cli("remind", "--now", NOW_S)
        self.assertIn("sweep --apply", out)
        self.assertNotIn("利用者の指示", out)
        rc, out2, err = self.run_cli("sweep", "--now", NOW_S)
        self.assertIn("d40.md", out2)

    def test_U29_remind_nondefault_days_names_same_days(self):
        self.mk("d70.md", age_days=70)
        rc, out, err = self.run_cli("remind", "--days", "60", "--now", NOW_S)
        self.assertIn("sweep --days 60 --apply", out)

    def test_U25_remind_skips_received_entry_whose_file_is_gone(self):
        f = self.mk("gone.md"); self.receive_at(f, 5); f.unlink()
        rc, out, err = self.run_cli("remind", "--now", NOW_S)
        self.assertEqual((rc, out), (0, ""))

    def test_U26_receive_title_rejects_bad_dir(self):
        (self.root / "docs").mkdir()
        rc, out, err = self.run_cli("receive", "--title", "x", "--dir", str(self.root / "docs"), "--now", NOW_S)
        self.assertEqual(rc, 2)

    def test_U27_ledger_entry_not_dict_is_treated_as_corrupt(self):
        f = self.mk("a.md")
        key = os.path.normcase(str(f.resolve()))
        self.ledger.write_text(json.dumps({"received": {key: "oops"}}), encoding="utf-8")
        rc, out, err = self.run_cli("done", str(f))
        self.assertEqual(rc, 3)
        self.assertTrue(f.exists())
        rc, out, err = self.run_cli("remind", "--now", NOW_S)
        self.assertEqual(rc, 0)

    def test_U28_naive_received_at_still_reminds(self):
        f = self.mk("a.md")
        key = os.path.normcase(str(f.resolve()))
        e = {"path": str(f.resolve()), "received_at": "2026-11-10T06:00:00", "sha256": "x", "mtime": 0, "matched_by": "path"}
        self.ledger.write_text(json.dumps({"received": {key: e}}), encoding="utf-8")
        rc, out, err = self.run_cli("remind", "--now", NOW_S)
        self.assertIn("a.md", out)
        self.assertIn("中断の疑い", out)


if __name__ == "__main__":
    unittest.main(verbosity=1)
