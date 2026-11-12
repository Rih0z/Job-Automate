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


GIT = shutil.which("git")


def git(cwd, *args, check=True):
    p = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
                       cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    if check and p.returncode != 0:
        raise AssertionError(f"git {args}: {p.stderr}")
    return p.stdout


class TestReferencedAndConfig(Base):
    """V: issue から参照されている handoff を退避しない・repo ごとの config・案内文。"""

    def issue(self, rel, text):
        f = self.root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8")
        return f

    def test_V1_referenced_by_full_path_is_kept(self):
        kept = self.mk("2026-09-01-a.md", age_days=60)
        gone = self.mk("2026-09-01-b.md", age_days=60)
        self.issue("issues/open/0001.md", f"最新 handoff: {kept}\n")
        rc, out, err = self.run_cli("sweep", "--apply", "--keep-referenced", "issues", "--now", NOW_S)
        self.assertEqual(rc, 0, err)
        self.assertTrue(kept.exists())
        self.assertFalse(gone.exists())

    def test_V2_name_stem_case_and_nested_references_are_kept(self):
        a = self.mk("20260901_handoff_alpha.md", age_days=60)
        b = self.mk("20260901_handoff_beta.md", age_days=60)
        c = self.mk("20260901_handoff_gamma.md", age_days=60)
        d = self.mk("20260901_handoff_delta.md", age_days=60)
        self.issue("issues/open/x.md", "see 20260901_handoff_alpha.md.\n")
        self.issue("issues/open/sub/fromX/y.yaml", "latest_handoff: .tmp\\handoffs\\20260901_handoff_beta\n")
        self.issue("issues/open/z.json", '{"h": "20260901_HANDOFF_GAMMA.MD"}')
        rc, out, err = self.run_cli("sweep", "--apply", "--keep-referenced", "issues", "--now", NOW_S)
        self.assertEqual(rc, 0, err)
        self.assertTrue(a.exists()); self.assertTrue(b.exists()); self.assertTrue(c.exists())
        self.assertFalse(d.exists())

    def test_V3_missing_keep_dir(self):
        f = self.mk("a.md", age_days=60)
        rc, out, err = self.run_cli("sweep", "--apply", "--keep-referenced", "nope", "--now", NOW_S)
        self.assertEqual(rc, 2)
        self.assertTrue(f.exists())
        rc, out, err = self.run_cli("remind", "--keep-referenced", "nope", "--now", NOW_S)
        self.assertEqual(rc, 0)
        self.assertIn("nope", err)

    def mk_config(self, base, **kw):
        cfg = base / ".claude" / "handoff-lifecycle.json"
        cfg.parent.mkdir(parents=True, exist_ok=True)
        cfg.write_text(json.dumps(kw), encoding="utf-8")
        return cfg

    def test_V4_config_paths_are_relative_to_parent_of_dot_claude(self):
        base = self.root / "repo" / "docs" / "sub"
        hd = base / ".tmp" / "handoffs"; hd.mkdir(parents=True)
        kept = hd / "k.md"; kept.write_text(body(), encoding="utf-8")
        gone = hd / "g.md"; gone.write_text(body(), encoding="utf-8")
        t = (NOW - timedelta(days=60)).timestamp()
        for p in (kept, gone):
            os.utime(p, (t, t))
        (base / "1_issue").mkdir(); (base / "1_issue" / "i.md").write_text("k.md", encoding="utf-8")
        cfg = self.mk_config(base, handoffs_dir=".tmp/handoffs",
                             keep_referenced=[{"path": "1_issue", "required": True}])
        rc, out, err = self.run_cli("sweep", "--apply", "--config", str(cfg), "--now", NOW_S)
        self.assertEqual(rc, 0, err)
        self.assertTrue(kept.exists()); self.assertFalse(gone.exists())

    def test_V5_optional_missing_warns_and_string_means_required(self):
        f = self.mk("a.md", age_days=60)
        cfg = self.mk_config(self.root, handoffs_dir=".tmp/handoffs",
                             keep_referenced=[{"path": "other/1_issue", "required": False}])
        rc, out, err = self.run_cli("sweep", "--config", str(cfg), "--now", NOW_S)
        self.assertEqual(rc, 0, err)
        self.assertIn("other", err)
        cfg2 = self.mk_config(self.root, handoffs_dir=".tmp/handoffs", keep_referenced=["nope"])
        rc, out, err = self.run_cli("sweep", "--apply", "--config", str(cfg2), "--now", NOW_S)
        self.assertEqual(rc, 2)
        self.assertTrue(f.exists())

    def test_V6_cli_days_overrides_config(self):
        self.mk("d40.md", age_days=40)
        cfg = self.mk_config(self.root, handoffs_dir=".tmp/handoffs", days=60)
        rc, out, err = self.run_cli("sweep", "--config", str(cfg), "--now", NOW_S)
        self.assertNotIn("d40.md", out)
        rc, out, err = self.run_cli("sweep", "--config", str(cfg), "--days", "30", "--now", NOW_S)
        self.assertIn("d40.md", out)

    def test_V7_remind_with_config_names_config_and_excludes_referenced(self):
        self.mk("ref.md", age_days=60); self.mk("free.md", age_days=60)
        self.issue("issues/open/i.md", "ref.md")
        cfg = self.mk_config(self.root, handoffs_dir=".tmp/handoffs", keep_referenced=["issues"])
        rc, out, err = self.run_cli("remind", "--config", str(cfg), "--now", NOW_S)
        self.assertEqual(rc, 0, err)
        self.assertIn(f"sweep --config {cfg} --apply", out)
        self.assertIn(": 1 件", out)
        self.assertNotIn("ref.md", out)

    def test_V8_remind_without_config_repeats_keep_referenced(self):
        self.mk("free.md", age_days=60)
        self.issue("issues/open/i.md", "x")
        rc, out, err = self.run_cli("remind", "--keep-referenced", "issues", "--now", NOW_S)
        self.assertIn("sweep --keep-referenced issues --apply", out)

    def test_V9_in_progress_is_kept(self):
        f = self.mk("w.md", text="---\nwork_status: in_progress\n---\n" + body(), age_days=60)
        rc, out, err = self.run_cli("sweep", "--apply", "--now", NOW_S)
        self.assertEqual(rc, 0, err)
        self.assertTrue(f.exists())

    def test_V10_lock(self):
        f = self.mk("a.md", age_days=60)
        lock = self.root / ".tmp" / "handoff-sweep.lock"
        lock.write_text("x", encoding="utf-8")
        rc, out, err = self.run_cli("sweep", "--apply", "--now", NOW_S)
        self.assertEqual(rc, 2)
        self.assertTrue(f.exists())
        old = time.time() - 20 * 60
        os.utime(lock, (old, old))
        rc, out, err = self.run_cli("sweep", "--apply", "--now", NOW_S)
        self.assertEqual(rc, 0, err)
        self.assertFalse(f.exists())
        self.assertFalse(lock.exists())

    def test_V15_remind_reference_timeout_message(self):
        self.mk("a.md", age_days=60)
        self.issue("issues/open/i.md", "x")
        rc, out, err = self.run_cli("remind", "--keep-referenced", "issues", "--ref-timeout", "0", "--now", NOW_S)
        self.assertEqual(rc, 0)
        self.assertIn("時間内に終わらなかった", out)

    def test_V16_remind_is_fast_on_large_issue_text(self):
        for i in range(500):
            self.mk(f"20260801_handoff_n{i:03d}.md", age_days=60)
        chunk = ("lorem ipsum 20260801_handoff_n001.md " * 30000)[:1000000]
        for j in range(30):
            self.issue(f"issues/open/big{j}.md", chunk)
        t0 = time.time()
        rc, out, err = self.run_cli("remind", "--keep-referenced", "issues", "--now", NOW_S)
        self.assertEqual(rc, 0, err)
        self.assertLess(time.time() - t0, 10)
        self.assertIn(": 499 件", out)

    def test_V17_sweep_reads_large_files_remind_skips(self):
        f = self.mk("big-ref.md", age_days=60)
        self.issue("issues/open/huge.log.txt", "x" * (3 * 1024 * 1024) + " big-ref.md")
        rc, out, err = self.run_cli("remind", "--keep-referenced", "issues", "--now", NOW_S)
        self.assertIn("huge.log.txt", err)
        rc, out, err = self.run_cli("sweep", "--apply", "--keep-referenced", "issues", "--now", NOW_S)
        self.assertEqual(rc, 0, err)
        self.assertTrue(f.exists())


class TestReviewFixes(Base):
    """W: 成果物レビュー・review-skill の指摘への対応。"""

    def issue(self, rel, text):
        f = self.root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8")
        return f

    def test_W1_reference_adjacent_to_japanese_is_kept(self):
        a = self.mk("2026-09-01-a.md", age_days=60)
        b = self.mk("20260901_handoff_beta.md", age_days=60)
        c = self.mk("2026-09-01-c.md", age_days=60)
        self.issue("issues/open/i.md", "最新は2026-09-01-a.mdを参照。20260901_handoff_betaの続き\n")
        rc, out, err = self.run_cli("sweep", "--apply", "--keep-referenced", "issues", "--now", NOW_S)
        self.assertEqual(rc, 0, err)
        self.assertTrue(a.exists()); self.assertTrue(b.exists()); self.assertFalse(c.exists())

    def test_W2_candidate_vanishing_before_lock_is_skipped(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("hl", SCRIPT)
        hl = importlib.util.module_from_spec(spec); spec.loader.exec_module(hl)
        gone = self.mk("a.md", age_days=60); other = self.mk("b.md", age_days=60)
        real = hl._acquire_lock

        def racing(lock):
            gone.unlink()  # 別の sweep が先に動かした状況
            real(lock)
        hl._acquire_lock = racing
        cwd = os.getcwd(); os.chdir(self.root)
        try:
            rc = hl.main(["sweep", "--apply", "--now", NOW_S])
        finally:
            os.chdir(cwd)
        self.assertEqual(rc, 0)
        self.assertFalse(other.exists())
        self.assertTrue((self.root / ".tmp" / "archive" / "handoffs" / "b.md").exists())

    def test_W3_paths_with_spaces_are_quoted_in_message(self):
        self.mk("a.md", age_days=60)
        base = self.root
        cfgdir = base / ".claude"; cfgdir.mkdir()
        cfg = cfgdir / "handoff lifecycle.json"
        cfg.write_text(json.dumps({"handoffs_dir": ".tmp/handoffs"}), encoding="utf-8")
        rc, out, err = self.run_cli("remind", "--config", str(cfg), "--now", NOW_S)
        self.assertIn(f'sweep --config "{cfg}" --apply', out)

    def test_W4_config_and_cli_keep_both_in_message(self):
        self.mk("a.md", age_days=60)
        self.issue("issues/open/i.md", "x"); self.issue("more/i.md", "x")
        cfgdir = self.root / ".claude"; cfgdir.mkdir()
        cfg = cfgdir / "handoff-lifecycle.json"
        cfg.write_text(json.dumps({"handoffs_dir": ".tmp/handoffs", "keep_referenced": ["issues"]}), encoding="utf-8")
        rc, out, err = self.run_cli("remind", "--config", str(cfg), "--keep-referenced", "more", "--now", NOW_S)
        self.assertIn(f"sweep --config {cfg} --keep-referenced more --apply", out)

    def test_W5_receive_title_uses_config_handoffs_dir(self):
        base = self.root / "sub"
        hd = base / ".tmp" / "handoffs"; hd.mkdir(parents=True)
        (hd / "t.md").write_text(body("見出しW5"), encoding="utf-8")
        cfgdir = base / ".claude"; cfgdir.mkdir()
        cfg = cfgdir / "handoff-lifecycle.json"
        cfg.write_text(json.dumps({"handoffs_dir": ".tmp/handoffs"}), encoding="utf-8")
        rc, out, err = self.run_cli("receive", "--title", "見出しW5", "--config", str(cfg), "--now", NOW_S)
        self.assertEqual(rc, 0, err)
        self.assertIn("t.md", out)

    def test_W6_bool_days_in_config_is_ignored(self):
        self.mk("d40.md", age_days=40)
        cfgdir = self.root / ".claude"; cfgdir.mkdir()
        cfg = cfgdir / "handoff-lifecycle.json"
        cfg.write_text(json.dumps({"handoffs_dir": ".tmp/handoffs", "days": True}), encoding="utf-8")
        rc, out, err = self.run_cli("sweep", "--config", str(cfg), "--now", NOW_S)
        self.assertIn("30 日超", out)
        self.assertIn("d40.md", out)

    def test_W7_in_progress_after_line_60_is_not_excluded(self):
        f = self.mk("late.md", text=body() + "\n" * 70 + "work_status: in_progress\n", age_days=60)
        rc, out, err = self.run_cli("sweep", "--apply", "--now", NOW_S)
        self.assertEqual(rc, 0, err)
        self.assertFalse(f.exists())


@unittest.skipUnless(GIT, "git が無い")
class TestGit(Base):
    def setUp(self):
        super().setUp()
        git(self.root, "init", "-q")
        (self.root / ".gitignore").write_text(".tmp/\n", encoding="utf-8")

    def cfg(self, **kw):
        c = self.root / ".claude" / "handoff-lifecycle.json"
        c.parent.mkdir(exist_ok=True)
        c.write_text(json.dumps(dict(handoffs_dir=".tmp/handoffs", git_tracked=True, **kw)), encoding="utf-8")
        return c

    def test_V11_only_main_worktree(self):
        self.mk("a.md", age_days=60)
        git(self.root, "add", "-f", ".gitignore", ".tmp/handoffs/a.md"); git(self.root, "commit", "-qm", "x")
        rc, out, err = self.run_cli("remind", "--only-main-worktree", "--now", NOW_S)
        self.assertIn("a.md", out)
        sub = self.root / "docs" / "sub"; (sub / ".tmp" / "handoffs").mkdir(parents=True)
        f = sub / ".tmp" / "handoffs" / "s.md"; f.write_text(body(), encoding="utf-8")
        t = (NOW - timedelta(days=60)).timestamp(); os.utime(f, (t, t))
        env = dict(os.environ, PYTHONUTF8="1")
        p = subprocess.run([sys.executable, str(SCRIPT), "remind", "--only-main-worktree", "--now", NOW_S],
                           cwd=sub, capture_output=True, text=True, encoding="utf-8", env=env)
        self.assertIn("s.md", p.stdout)
        wt = Path(tempfile.mkdtemp()) / "wt"
        git(self.root, "worktree", "add", "-q", str(wt))
        try:
            (wt / ".tmp" / "handoffs").mkdir(parents=True, exist_ok=True)
            g = wt / ".tmp" / "handoffs" / "w.md"; g.write_text(body(), encoding="utf-8"); os.utime(g, (t, t))
            p = subprocess.run([sys.executable, str(SCRIPT), "remind", "--only-main-worktree", "--now", NOW_S],
                               cwd=wt, capture_output=True, text=True, encoding="utf-8", env=env)
            self.assertEqual(p.stdout, "")
        finally:
            git(self.root, "worktree", "remove", "--force", str(wt), check=False)
        outside = Path(tempfile.mkdtemp())
        try:
            (outside / ".tmp" / "handoffs").mkdir(parents=True)
            h = outside / ".tmp" / "handoffs" / "o.md"; h.write_text(body(), encoding="utf-8"); os.utime(h, (t, t))
            p = subprocess.run([sys.executable, str(SCRIPT), "remind", "--only-main-worktree", "--now", NOW_S],
                               cwd=outside, capture_output=True, text=True, encoding="utf-8",
                               env=dict(env, GIT_CEILING_DIRECTORIES=str(outside.parent)))
            self.assertIn("o.md", p.stdout)
        finally:
            shutil.rmtree(outside, ignore_errors=True)

    def test_V12_sweep_stages_tracked_as_rename_and_commit_works(self):
        tr = self.mk("tracked.md", age_days=60)
        un = self.mk("untracked.md", age_days=60)
        git(self.root, "add", "-f", ".gitignore", ".tmp/handoffs/tracked.md"); git(self.root, "commit", "-qm", "x")
        c = self.cfg()
        rc, out, err = self.run_cli("sweep", "--apply", "--config", str(c), "--now", NOW_S)
        self.assertEqual(rc, 0, err)
        staged = [l.split(" ", 1)[1] for l in out.splitlines() if l.startswith("staged: ")]
        self.assertEqual(len(staged), 2, out)
        st = git(self.root, "status", "--porcelain")
        self.assertRegex(st, r"(?m)^R  .tmp/handoffs/tracked.md -> .tmp/archive/handoffs/tracked.md$")
        self.assertNotIn("untracked.md", st)
        git(self.root, "commit", "-qm", "sweep", "--", *staged)
        self.assertIn(".tmp/archive/handoffs/tracked.md", git(self.root, "ls-files"))

    def test_V13_done_stages_deletion_of_tracked(self):
        f = self.mk("a.md")
        git(self.root, "add", "-f", ".gitignore", ".tmp/handoffs/a.md"); git(self.root, "commit", "-qm", "x")
        c = self.cfg()
        self.receive_at(f, 1)
        rc, out, err = self.run_cli("done", str(f), "--config", str(c))
        self.assertEqual(rc, 0, err)
        self.assertIn("staged: ", out)
        self.assertRegex(git(self.root, "status", "--porcelain"), r"(?m)^D  .tmp/handoffs/a.md$")

    def test_V14_git_failure_still_moves(self):
        shutil.rmtree(self.root / ".git")
        f = self.mk("a.md", age_days=60)
        c = self.cfg()
        rc, out, err = self.run_cli("sweep", "--apply", "--config", str(c), "--now", NOW_S)
        self.assertEqual(rc, 0, err)
        self.assertFalse(f.exists())
        self.assertIn("警告", err)


def hbody(issue=None, title="引継ぎ: テスト用", extra=""):
    fm = f"---\nissue: {issue}\n---\n" if issue is not None else ""
    return fm + body(title, extra)


class ReleaseBase(Base):
    """H: release --issue（1.6.0）。計画 2026-11-11-issue-handoff-knowhow-redesign.md r3 の D2.2。"""

    def setUp(self):
        super().setUp()
        self.env_extra = {"GIT_CEILING_DIRECTORIES": str(self.root.parent)}
        self.cfg = self.mk_cfg()

    def run_cli(self, *args, cwd=None):
        env = dict(os.environ, PYTHONUTF8="1", **self.env_extra)
        p = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd or self.root,
                           capture_output=True, text=True, encoding="utf-8", env=env)
        return p.returncode, p.stdout, p.stderr

    def mk_cfg(self, base=None, **kw):
        base = base or self.root
        d = dict(handoffs_dir=".tmp/handoffs", keep_referenced=[{"path": "issues/open", "required": False}],
                 release={"closed_dirs": ["closed", "withdrawn"]})
        d.update(kw)
        c = base / ".claude" / "handoff-lifecycle.json"
        c.parent.mkdir(parents=True, exist_ok=True)
        c.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        return c

    def issue(self, rel, text):
        f = self.root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8")
        return f

    def release(self, issue_rel, *extra):
        return self.run_cli("release", "--issue", issue_rel, "--config", str(self.cfg), *extra)

    @property
    def released_dir(self):
        return self.root / ".tmp" / "archive" / "handoffs" / "released"


class TestReleaseCandidates(ReleaseBase):
    def test_H1_candidates_from_handoff_field_and_issue_frontmatter_only(self):
        a = self.mk("a.md")
        b = self.mk("b.md")
        c = self.mk("c.md", hbody(issue="issues/closed/0001.md"))
        d = self.mk("d.md", hbody(issue="0001.md"))
        e = self.mk("e.md", body(extra="issue 0001 の続き。0001.md を参照\n"))
        self.issue("issues/closed/0001.md",
                   f"---\nlatest_handoff: .tmp/handoffs/b.md\n---\n# Issue 0001\n\n"
                   f"**最新 handoff**: {a}\n\n本文で e.md に触れる\n")
        rc, out, err = self.release("issues/closed/0001.md")
        self.assertEqual(rc, 0, err)
        for f in (a, b, c, d):
            self.assertFalse(f.exists(), f.name)
            self.assertTrue((self.released_dir / f.name).exists(), f.name)
        self.assertTrue(e.exists())
        self.assertFalse((self.released_dir / "e.md").exists())

    def test_H1b_other_repo_path_is_not_candidate_and_quoted_paths_are_parsed(self):
        other = Path(tempfile.mkdtemp())
        try:
            ohd = other / ".tmp" / "handoffs"; ohd.mkdir(parents=True)
            ox = ohd / "x.md"; ox.write_text(body(), encoding="utf-8")
            sp = self.mk("with space.md")
            bt = self.mk("bt.md")
            qt = self.mk("qt.md")
            self.issue("issues/closed/0002.md",
                       f"# Issue 0002\n\n最新 handoff: {ox}\n最新 handoff（前回）: <.tmp/handoffs/with space.md>\n"
                       f"最新 handoff: `.tmp/handoffs/bt.md`\n最新 handoff: \".tmp/handoffs/qt.md\"\n")
            rc, out, err = self.release("issues/closed/0002.md")
            self.assertEqual(rc, 0, err)
            self.assertTrue(ox.exists())
            self.assertIn("別 repo", out)
            self.assertFalse(sp.exists())
            self.assertFalse(bt.exists())
            self.assertFalse(qt.exists())
            self.assertTrue((self.released_dir / "with space.md").exists())
        finally:
            shutil.rmtree(other, ignore_errors=True)

    def test_H1c_bare_file_name_in_handoff_field_is_resolved_in_handoffs_dir(self):
        h = self.mk("2026-11-01-x.md")
        self.issue("issues/closed/0012.md", "# x\n\n最新 handoff: 2026-11-01-x.md\n")
        rc, out, err = self.release("issues/closed/0012.md")
        self.assertEqual(rc, 0, err)
        self.assertFalse(h.exists())
        self.assertNotIn("対象外", out)

    def test_H2_referenced_in_progress_and_received_are_kept_with_reason(self):
        r = self.mk("ref.md")
        w = self.mk("wip.md", "---\nwork_status: in_progress\n---\n" + body())
        g = self.mk("got.md")
        self.receive_at(g, 1)
        self.issue("issues/open/0005.md", "# 別の active な issue\n\n最新 handoff: .tmp/handoffs/ref.md\n")
        self.issue("issues/closed/0003.md",
                   "# Issue 0003\n\n最新 handoff: .tmp/handoffs/ref.md\n最新 handoff: .tmp/handoffs/wip.md\n"
                   "最新 handoff: .tmp/handoffs/got.md\n")
        rc, out, err = self.release("issues/closed/0003.md")
        self.assertEqual(rc, 0, err)
        for f in (r, w, g):
            self.assertTrue(f.exists(), f.name)
        kept = {n: [l for l in out.splitlines() if l.startswith("残す") and l.endswith(": " + n)]
                for n in ("ref.md", "wip.md", "got.md")}
        self.assertEqual(kept["ref.md"], ["残す（別の active な issue から参照されている）: ref.md"], out)
        self.assertEqual(kept["wip.md"], ["残す（work_status: in_progress）: wip.md"], out)
        self.assertEqual(kept["got.md"], [f"残す（受領済みで done していない。使い終わったなら done {g.resolve()} を実行する）: got.md"], out)
        self.assertFalse(self.released_dir.exists())

    def test_H3_issue_must_be_in_closed_dirs(self):
        h = self.mk("a.md")
        self.issue("issues/open/0004.md", "# open\n\n最新 handoff: .tmp/handoffs/a.md\n")
        rc, out, err = self.release("issues/open/0004.md")
        self.assertEqual(rc, 2)
        self.assertTrue(h.exists())
        self.assertFalse(self.released_dir.exists())

    def test_H3b_closed_dir_name_comes_from_config(self):
        self.cfg = self.mk_cfg(release={"closed_dirs": ["close"]})
        h = self.mk("a.md")
        self.issue("issues/closed/0006.md", "# x\n\n最新 handoff: .tmp/handoffs/a.md\n")
        rc, out, err = self.release("issues/closed/0006.md")
        self.assertEqual(rc, 2)
        self.assertTrue(h.exists())
        self.issue("issues/close/0006.md", "# x\n\n最新 handoff: .tmp/handoffs/a.md\n")
        rc, out, err = self.release("issues/close/0006.md")
        self.assertEqual(rc, 0, err)
        self.assertFalse(h.exists())

    def test_H4_untracked_goes_to_released_with_unique_name(self):
        h = self.mk("a.md")
        self.released_dir.mkdir(parents=True)
        (self.released_dir / "a.md").write_text("先にあった", encoding="utf-8")
        self.issue("issues/closed/0007.md", "# x\n\n最新 handoff: .tmp/handoffs/a.md\n")
        rc, out, err = self.release("issues/closed/0007.md")
        self.assertEqual(rc, 0, err)
        self.assertFalse(h.exists())
        self.assertEqual((self.released_dir / "a.md").read_text(encoding="utf-8"), "先にあった")
        self.assertEqual((self.released_dir / "a-1.md").read_text(encoding="utf-8"), body())

    @unittest.skipUnless(GIT, "git が無い")
    def test_H4b_git_tracked_is_deleted_and_staged(self):
        self.cfg = self.mk_cfg(git_tracked=True)
        git(self.root, "init", "-q")
        (self.root / ".gitignore").write_text(".tmp/handoff-ledger.json\n", encoding="utf-8")
        h = self.mk("a.md")
        self.issue("issues/closed/0008.md", "# x\n\n最新 handoff: .tmp/handoffs/a.md\n")
        git(self.root, "add", "-A"); git(self.root, "commit", "-qm", "x")
        rc, out, err = self.release("issues/closed/0008.md")
        self.assertEqual(rc, 0, err)
        self.assertFalse(h.exists())
        self.assertRegex(git(self.root, "status", "--porcelain"), r"(?m)^D  .tmp/handoffs/a.md$")
        self.assertIn("staged:", out)

    def test_H4c_git_unavailable_with_git_tracked_still_moves(self):
        self.cfg = self.mk_cfg(git_tracked=True)
        h = self.mk("a.md")
        self.issue("issues/closed/0009.md", "# x\n\n最新 handoff: .tmp/handoffs/a.md\n")
        rc, out, err = self.release("issues/closed/0009.md")
        self.assertEqual(rc, 0, err)
        self.assertFalse(h.exists())
        self.assertTrue((self.released_dir / "a.md").exists())
        self.assertIn("警告", err)

    def test_H3c_missing_issue_is_exit_2(self):
        rc, out, err = self.release("issues/closed/nope.md")
        self.assertEqual(rc, 2)

    def write_tracker(self, sources):
        t = self.root / ".claude" / "issue-tracker.json"
        t.write_text(json.dumps({"sources": sources}, ensure_ascii=False), encoding="utf-8")

    def test_H7_closed_names_come_from_issue_tracker_when_present(self):
        self.cfg = self.mk_cfg(release={"closed_dirs": ["closed"]})
        self.write_tracker([{"type": "md_dirs", "root": "issues", "active": ["open"], "closed": ["close"],
                             "merged_dir": "withdrawn"}])
        h = self.mk("a.md")
        self.issue("issues/closed/0010.md", "# x\n\n最新 handoff: .tmp/handoffs/a.md\n")
        rc, out, err = self.release("issues/closed/0010.md")
        self.assertEqual(rc, 2, "issue-tracker.json があれば release.closed_dirs は使わない")
        self.assertTrue(h.exists())
        self.issue("issues/withdrawn/0011.md", "# x\n\n最新 handoff: .tmp/handoffs/a.md\n")
        rc, out, err = self.release("issues/withdrawn/0011.md")
        self.assertEqual(rc, 0, err)
        self.assertFalse(h.exists())

    def test_H7b_two_sources_are_judged_by_the_owning_source(self):
        self.write_tracker([
            {"type": "md_dirs", "root": "issuesA", "active": ["open"], "closed": ["closed"]},
            {"type": "md_dirs", "root": "issuesB", "active": ["open"], "closed": ["done"]},
        ])
        h = self.mk("a.md")
        for rel in ("issuesB/closed/x.md", "issuesA/done/z.md"):
            self.issue(rel, "# x\n\n最新 handoff: .tmp/handoffs/a.md\n")
            rc, out, err = self.release(rel)
            self.assertEqual(rc, 2, rel)
            self.assertTrue(h.exists(), rel)
        self.issue("issuesB/done/y.md", "# y\n\n最新 handoff: .tmp/handoffs/a.md\n")
        rc, out, err = self.release("issuesB/done/y.md")
        self.assertEqual(rc, 0, err)
        self.assertFalse(h.exists())


class TestSessionAndIssueField(ReleaseBase):
    def test_H5_remind_received_since_lists_only_received_after_and_not_done(self):
        a = self.mk("before.md", hbody(issue="none")); self.receive_at(a, 5)
        b = self.mk("after.md", hbody(issue="none")); self.receive_at(b, 1)
        self.mk("old-unreceived.md", age_days=40)
        since = (NOW - timedelta(hours=2)).isoformat()
        rc, out, err = self.run_cli("remind", "--received-since", since, "--now", NOW_S)
        self.assertEqual(rc, 0, err)
        lines = [l for l in out.splitlines() if l.strip()]
        self.assertEqual(len(lines), 1, out)
        self.assertIn("after.md", lines[0])
        self.assertIn("done", lines[0])
        rc, out, err = self.run_cli("done", str(b))
        rc, out, err = self.run_cli("remind", "--received-since", since, "--now", NOW_S)
        self.assertEqual(out.strip(), "")

    def test_H5b_received_since_boundary_and_timezone(self):
        a = self.mk("same.md", hbody(issue="none")); self.receive_at(a, 2)
        since_same = (NOW - timedelta(hours=2)).isoformat()
        since_other_tz = (NOW - timedelta(hours=2)).astimezone(timezone(timedelta(hours=9))).isoformat()
        since_after = (NOW - timedelta(hours=2) + timedelta(seconds=1)).isoformat()
        for since, expect in ((since_same, 1), (since_other_tz, 1), (since_after, 0)):
            rc, out, err = self.run_cli("remind", "--received-since", since, "--now", NOW_S)
            self.assertEqual(rc, 0, err)
            self.assertEqual(len([l for l in out.splitlines() if "same.md" in l]), expect, since)

    def test_H6_receive_warns_without_issue_field_and_remind_marks_it(self):
        n = self.mk("noissue.md")
        rc, out, err = self.run_cli("receive", str(n), "--now", NOW_S)
        self.assertEqual(rc, 0, err)
        self.assertIn("issue:", err)
        y = self.mk("hasissue.md", hbody(issue="none"))
        rc, out, err = self.run_cli("receive", str(y), "--now", NOW_S)
        self.assertEqual(rc, 0, err)
        self.assertNotIn("issue:", err)
        rc, out, err = self.run_cli("remind", "--now", NOW_S)
        ln = [l for l in out.splitlines() if "noissue.md" in l]
        ly = [l for l in out.splitlines() if "hasissue.md" in l]
        self.assertTrue(ln and "issue 未記載" in ln[0], out)
        self.assertTrue(ly and "issue 未記載" not in ly[0], out)


class TestReferenceIndexCost(Base):
    """V18: 大きな repo で remind の参照検査が時間切れになる問題（discovery-log 2026-11-11T20:30）。
    handoff 名を含まない file は語に分けない（読むだけ）ことを、語に分けた回数で確かめる。"""

    def test_V18_files_without_candidate_names_are_not_tokenized(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("hl18", SCRIPT)
        hl = importlib.util.module_from_spec(spec); spec.loader.exec_module(hl)
        d = self.root / "issues" / "open"; d.mkdir(parents=True)
        for i in range(200):
            (d / f"{i:04d}.md").write_text("無関係な本文 lorem ipsum\n" * 50, encoding="utf-8")
        (d / "hit.md").write_text("最新 handoff: .tmp/handoffs/20261101_handoff_x.md\n", encoding="utf-8")
        calls = []

        class Counting:
            def __init__(self, pat):
                self.pat = pat

            def findall(self, text):
                calls.append(1)
                return self.pat.findall(text)
        hl._TOKEN = Counting(hl._TOKEN)
        hl._TOKEN_ASCII = Counting(hl._TOKEN_ASCII)
        tokens = hl._referenced_tokens([d], names={"20261101_handoff_x.md", "20261101_handoff_x"})
        self.assertTrue(hl._is_referenced(Path("20261101_handoff_x.md"), tokens))
        self.assertLessEqual(len(calls), 2, "語に分けるのは名前を含む file だけ")

    def test_V18d_prefilter_applies_up_to_32_names(self):
        d = self.root / "issues" / "open"; d.mkdir(parents=True)
        for i in range(5):
            (d / f"{i}.md").write_text("無関係な本文\n", encoding="utf-8")
        for n, expect_calls in ((32, 0), (33, 10)):
            hl = self._load()
            calls = []

            class Counting:
                def __init__(self, pat):
                    self.pat = pat

                def findall(self, text):
                    calls.append(1)
                    return self.pat.findall(text)
            hl._TOKEN = Counting(hl._TOKEN)
            hl._TOKEN_ASCII = Counting(hl._TOKEN_ASCII)
            names = hl._names_of([Path(f"h{i:03d}.md") for i in range(n)])
            hl._referenced_tokens([d], names=names)
            self.assertEqual(len(calls), expect_calls, n)

    def _load(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("hl18b", SCRIPT)
        hl = importlib.util.module_from_spec(spec); spec.loader.exec_module(hl)
        return hl

    def _remind_calls(self, hl):
        calls = []
        real = hl._referenced_tokens

        def spy(dirs, *args, **kw):
            calls.append(kw.get("names"))
            return real(dirs, *args, **kw)
        hl._referenced_tokens = spy
        cwd = os.getcwd(); os.chdir(self.root)
        try:
            rc = hl.main(["remind", "--keep-referenced", "issues", "--now", NOW_S])
        finally:
            os.chdir(cwd)
        return rc, calls

    def test_V18b_remind_without_old_candidates_does_not_read_references(self):
        d = self.root / "issues" / "open"; d.mkdir(parents=True)
        (d / "i.md").write_text("x", encoding="utf-8")
        self.mk("new.md", age_days=1)
        hl = self._load()
        rc, calls = self._remind_calls(hl)
        self.assertEqual((rc, calls), (0, []))

    def test_V18c_remind_looks_up_only_candidate_names(self):
        d = self.root / "issues" / "open"; d.mkdir(parents=True)
        (d / "i.md").write_text("old.md を参照", encoding="utf-8")
        self.mk("old.md", age_days=60); self.mk("free.md", age_days=60); self.mk("new.md", age_days=1)
        hl = self._load()
        rc, calls = self._remind_calls(hl)
        self.assertEqual(rc, 0)
        self.assertEqual(calls, [{"old.md", "old", "free.md", "free"}])


if __name__ == "__main__":
    unittest.main(verbosity=1)
