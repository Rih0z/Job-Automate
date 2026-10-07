#!/usr/bin/env python
"""select-slop-viewpoints の試験。標準ライブラリのみ。

使い方: python run_tests.py            終了コード: 0 全件が期待どおり / 1 期待と違うものがある。
試験の設計:
  1. criteria/viewpoints.json: コアルール R01〜R14 の source_title が stop-ai-slop-jp/SKILL.md に含まれる（上流の更新で意味がずれたら落ちる）
  2. criteria/doc-types.json: 汎用の 4 種類（blog・event-report・analysis-report・tech-doc）が検査を通る
  3. select_viewpoints.py の出力: 14 規則・5 軸・軸の点の合計=max_total・合格点が scoring.json と同値・blocker が残る
  4. 緩めない保証: 検査が、根拠の無い調整・受け持ち先の無い skip・skip してはいけない規則・skip の過多を落とす
  5. 未知の種類は exit 2、--list、--local の合流と id 衝突、--output
  6. 公開リポジトリ用の版（doc-types.local.json が無い版）に固有名詞が無い
"""
import contextlib
import io
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SKILL = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
import select_viewpoints as sv  # noqa: E402  (実装前は ImportError で落ちる = Red)

STOP_SLOP = SKILL.parent / "stop-ai-slop-jp"
BASE_TYPES = ("blog", "event-report", "analysis-report", "tech-doc")
BANNED_TOKENS = ("N" + "EC", "Micro" + "soft", "Pe" + "ter", "session" + ".html", "ef_" + "fall", "One" + "N" + "EC")

results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print("%s %s %s" % ("ok  " if ok else "NG  ", name, "" if ok else str(detail)[:300]))


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = sv.main(argv)
        except SystemExit as ex:
            code = ex.code
    return (code or 0), out.getvalue(), err.getvalue()


def copy_criteria(tmp):
    dst = Path(tmp) / "criteria"
    shutil.copytree(SKILL / "criteria", dst)
    (dst / "doc-types.local.json").unlink(missing_ok=True)
    return dst


def validate_with(criteria_dir):
    code, out, err = run(["--validate", "--criteria-dir", str(criteria_dir), "--stop-slop-dir", str(STOP_SLOP)])
    return code, out + err


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    vp = json.loads((SKILL / "criteria/viewpoints.json").read_text(encoding="utf-8"))
    skill_md = (STOP_SLOP / "SKILL.md").read_text(encoding="utf-8")
    scoring = json.loads((STOP_SLOP / "criteria/scoring.json").read_text(encoding="utf-8"))

    # 1 規則の目録
    rules = vp["rules"]
    check("viewpoints: R01〜R14 が重複なくそろう", [r["id"] for r in rules] == ["R%02d" % i for i in range(1, 15)])
    missing = [r["id"] for r in rules if r["source_title"] not in skill_md]
    check("viewpoints: 全ての source_title が stop-ai-slop-jp/SKILL.md に含まれる", not missing, missing)
    ids = {b["id"] for b in vp["blockers"]}
    check("viewpoints: blocker 3 種（帰属誤り・過小断定・指示文のメモ書き化）がある", {"misattribution", "audience_underassertion", "instruction_echo"} <= ids)
    sb = {b["id"] for b in (scoring.get("blocker_checks") or {}).get("items", [])}
    check("viewpoints: scoring.json の blocker は目録の部分集合", sb <= ids, sb - ids)

    # 2 汎用の 4 種類の検査
    code, out, err = run(["--validate"])
    check("--validate: 同梱の基準が合格（exit 0）", code == 0, out + err)
    code, out, err = run(["--list"])
    listed = json.loads(out) if code == 0 else []
    have = {d["id"] for d in listed}
    check("--list: 汎用の 4 種類が出る", set(BASE_TYPES) <= have, have)

    # 3 出力の中身
    for t in BASE_TYPES:
        code, out, err = run(["--doc-type", t])
        try:
            d = json.loads(out)
        except ValueError:
            check("select %s: JSON を返す" % t, False, out + err)
            continue
        axes = d["axes"]
        check("select %s: 14 規則・5 軸・点の合計が max_total" % t,
              len(d["rules"]) == 14 and len(axes) == 5 and sum(a["weight"] for a in axes) == scoring["pass_rule"]["max_total"], (len(d["rules"]), len(axes)))
        check("select %s: 合格点が scoring.json と同値" % t, d["pass_rule"]["min_total"] == scoring["pass_rule"]["min_total"])
        check("select %s: blocker が残る" % t, {"misattribution", "audience_underassertion"} <= {b["id"] for b in d["blockers"]})
        check("select %s: 全ての軸に質問文と anchor がある" % t, all(a.get("question") and a.get("anchors") for a in axes))
        check("select %s: 全ての規則に扱い（apply/skip/modify/conditional）がある" % t,
              all(r["treatment"] in ("apply", "skip", "modify", "conditional") for r in d["rules"]))

    # 種類ごとの期待
    code, out, _ = run(["--doc-type", "event-report"])
    er = json.loads(out)
    tr = {r["id"]: r for r in er["rules"]}
    check("event-report: 帰属と限定の軸を使い、stance は使わない",
          "attribution" in [a["id"] for a in er["axes"]] and "stance" not in [a["id"] for a in er["axes"]])
    check("event-report: R02（反証可能な主張）は所感・示唆の節だけ（conditional）",
          tr["R02"]["treatment"] == "conditional" and "所感" in tr["R02"].get("condition", ""))
    check("event-report: skip した規則に受け持ち先がある", all(r.get("covered_by") for r in er["rules"] if r["treatment"] == "skip"))
    code, out, _ = run(["--doc-type", "blog"])
    check("blog: 規則が全て apply", all(r["treatment"] == "apply" for r in json.loads(out)["rules"]))

    # 4 緩めない保証（検査が落とす）
    def mutate(label, fn, want):
        with tempfile.TemporaryDirectory() as tmp:
            cd = copy_criteria(tmp)
            p = cd / "doc-types.json"
            d = json.loads(p.read_text(encoding="utf-8"))
            fn(d)
            p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
            code, text = validate_with(cd)
            check("検査: %s は不合格（exit 1）" % label, code == 1 and want in text, text)

    def er_idx(d):
        return next(i for i, x in enumerate(d["doc_types"]) if x["id"] == "event-report")

    mutate("skip に受け持ち先が無い", lambda d: d["doc_types"][er_idx(d)]["rules"]["R10"].pop("covered_by"), "covered_by")
    mutate("skip してはいけない規則（R01）を skip", lambda d: d["doc_types"][er_idx(d)]["rules"]["R01"].update(treatment="skip", covered_by="x"), "never_skip")

    def too_many(d):
        for r in ("R03", "R04", "R06", "R07", "R09", "R10"):
            d["doc_types"][er_idx(d)]["rules"][r].update(treatment="skip", covered_by="x")
    mutate("skip が上限（max_skip）を超える", too_many, "max_skip")
    mutate("規則 R05 が欠ける", lambda d: d["doc_types"][er_idx(d)]["rules"].pop("R05"), "R05")
    mutate("modify に条件が無い", lambda d: d["doc_types"][er_idx(d)]["rules"]["R03"].pop("condition", None), "condition")
    mutate("blocker（misattribution）が欠ける", lambda d: d["doc_types"][er_idx(d)]["blockers"].remove("misattribution"), "misattribution")
    mutate("知らない軸を使う", lambda d: d["doc_types"][er_idx(d)]["axes"].__setitem__(0, "no_such_axis"), "no_such_axis")

    def override_without(field):
        def f(d):
            t = d["doc_types"][er_idx(d)]
            t["axis_overrides"] = {"rhythm": {"question": "q", "anchors": {"1": "a", "5": "b", "10": "c"},
                                              "ground": "g", "keeps": ["k"], "counter_examples": ["e1", "e2"]}}
            t["axis_overrides"]["rhythm"].pop(field)
        return f

    for fld in ("ground", "keeps", "counter_examples"):
        mutate("axis_overrides に %s が無い" % fld, override_without(fld), fld)

    def one_counter(d):
        override_without("ground")(d)
        o = d["doc_types"][er_idx(d)]["axis_overrides"]["rhythm"]
        o.update(ground="g", counter_examples=["e1"])
    mutate("axis_overrides の counter_examples が 1 件", one_counter, "counter_examples")

    # 4b 緩めない保証の抜け穴（レビューで見つかったもの）
    def replacing_without_ground(d):
        d["doc_types"][er_idx(d)].pop("axis_replacements", None)
    mutate("軸の差し替え（stance→attribution）に根拠（axis_replacements）が無い", replacing_without_ground, "axis_replacements")
    mutate("同じ軸を重複して使う", lambda d: d["doc_types"][er_idx(d)]["axes"].__setitem__(1, "attribution"), "重複")
    mutate("使わない軸（stance 相当）が欠ける", lambda d: d["doc_types"][er_idx(d)].update(axes=["attribution", "rhythm", "agency", "concreteness", "concreteness"]), "reduction")
    mutate("never_skip の規則（R01）を conditional にして実質外す", lambda d: d["doc_types"][er_idx(d)]["rules"]["R01"].update(treatment="conditional", condition="適用しない"), "never_skip")
    mutate("never_skip の規則（R11）を modify にして実質外す", lambda d: d["doc_types"][er_idx(d)]["rules"]["R11"].update(treatment="modify", condition="使ってよい"), "never_skip")

    def mutate_vp(label, fn, want):
        with tempfile.TemporaryDirectory() as tmp:
            cd = copy_criteria(tmp)
            p = cd / "viewpoints.json"
            d = json.loads(p.read_text(encoding="utf-8"))
            fn(d)
            p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
            code, text = validate_with(cd)
            check("検査: %s は不合格（exit 1）" % label, code == 1 and want in text, text)

    mutate_vp("limits の max_skip を 14 に緩める", lambda d: d["limits"].update(max_skip=14), "limits")
    mutate_vp("limits の never_skip を空にする", lambda d: d["limits"].update(never_skip=[]), "limits")

    def swap_numbers(d):
        d["rules"][0]["source_title"], d["rules"][1]["source_title"] = d["rules"][1]["source_title"], d["rules"][0]["source_title"]
    mutate_vp("規則の番号と見出し語が stop-ai-slop-jp とずれる", swap_numbers, "R01")
    mutate_vp("instruction_echo の定義が無い", lambda d: d.__setitem__("blockers", [b for b in d["blockers"] if b["id"] != "instruction_echo"]), "instruction_echo")

    # 4c 全ての汎用の種類が blocker 3 種を持つ・手順と採点範囲が出力に入る・技術文書の例外
    for t in BASE_TYPES:
        _, out, _ = run(["--doc-type", t])
        sel = json.loads(out)
        check("select %s: blocker 3 種（instruction_echo を含む）" % t, {b["id"] for b in sel["blockers"]} == {"misattribution", "audience_underassertion", "instruction_echo"})
        check("select %s: 手順（独立 3 回の中央値）と採点範囲（文体のみ・範囲外メモ）が入る" % t,
              sel["procedure"]["verdict_rule"]["runs"] == 3 and sel["procedure"]["verdict_rule"]["method"] == "median" and sel["procedure"]["scoring_scope"], sel.get("procedure"))
    _, out, _ = run(["--doc-type", "tech-doc"])
    td = json.loads(out)
    rh = next((a for a in td["axes"] if a["id"] == "rhythm"), {})
    check("tech-doc: R09 を skip する種類は、rhythm 軸の問いも根拠付きで調整している（軸と規則の整合）",
          td["rules"][8]["treatment"] != "skip" or bool(rh.get("override")), rh.get("override"))
    notes = " ".join(td["notes"])
    check("tech-doc: 技術文書モードの 2 つの例外（本書・本章、山場の体言止め）が notes にある", "本書" in notes and "山場" in notes, notes)
    _, out, _ = run(["--doc-type", "event-report"])
    lay = json.loads(out).get("layout") or {}
    check("event-report: 報告された内容の節と所感・示唆の節の分け方（layout）がある", len(lay.get("sections", [])) == 2, lay)

    # 軸の調整が出力に反映される
    with tempfile.TemporaryDirectory() as tmp:
        cd = copy_criteria(tmp)
        p = cd / "doc-types.json"
        d = json.loads(p.read_text(encoding="utf-8"))
        d["doc_types"][er_idx(d)]["axis_overrides"] = {"rhythm": {"question": "調整後の問い", "anchors": {"1": "a", "5": "b", "10": "c"},
                                                                 "ground": "根拠", "keeps": ["合格点"], "counter_examples": ["例 1", "例 2"]}}
        p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        code, out, err = run(["--doc-type", "event-report", "--criteria-dir", str(cd), "--stop-slop-dir", str(STOP_SLOP)])
        rh = next(a for a in json.loads(out)["axes"] if a["id"] == "rhythm") if code == 0 else {}
        check("axis_overrides: 出力の軸に調整後の問いと根拠が入る", rh.get("question") == "調整後の問い" and rh.get("override", {}).get("ground") == "根拠", out + err)

        # parameters の受け渡しと、軸の定義の引き方（採点基準 → axes.json → profile の順。どの repo でも同じ結果にする）
        d = json.loads(p.read_text(encoding="utf-8"))
        d["doc_types"][er_idx(d)]["parameters"] = {"x": 1}
        p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        code, out, err = run(["--doc-type", "event-report", "--criteria-dir", str(cd), "--stop-slop-dir", str(STOP_SLOP)])
        sel = json.loads(out) if code == 0 else {}
        check("parameters: 種類の parameters が出力に渡る", sel.get("parameters") == {"x": 1}, out + err)
        att = next((a for a in sel.get("axes", []) if a["id"] == "attribution"), {})
        check("軸の定義: attribution は axes.json から引く（profile の同名の軸より先）", "axes.json" in att.get("source", ""), att.get("source"))

        # 5 未知の種類・--local・--output
        code, out, err = run(["--doc-type", "no-such-type", "--criteria-dir", str(cd), "--stop-slop-dir", str(STOP_SLOP)])
        check("未知の種類は exit 2 で、種類の一覧を示す", code == 2 and "blog" in (out + err), out + err)
        local = {"doc_types": [{"id": "local-x", "name": "局所", "description": "d", "recognize": "r",
                                "rules": {r["id"]: {"treatment": "apply"} for r in vp["rules"]},
                                "axes": ["stance", "rhythm", "agency", "concreteness", "reduction"],
                                "blockers": ["misattribution", "audience_underassertion", "instruction_echo"]}]}
        (cd / "doc-types.local.json").write_text(json.dumps(local, ensure_ascii=False), encoding="utf-8")
        code, out, err = run(["--list", "--criteria-dir", str(cd), "--stop-slop-dir", str(STOP_SLOP)])
        check("--local: 局所の種類が一覧に合流する", code == 0 and "local-x" in out, out + err)
        local["doc_types"][0]["id"] = "blog"
        (cd / "doc-types.local.json").write_text(json.dumps(local, ensure_ascii=False), encoding="utf-8")
        code, text = validate_with(cd)
        check("--local: 汎用の種類と id が衝突したら不合格", code == 1 and "blog" in text, text)
        outp = Path(tmp) / "sel.json"
        (cd / "doc-types.local.json").unlink()
        code, out, err = run(["--doc-type", "blog", "--output", str(outp), "--criteria-dir", str(cd), "--stop-slop-dir", str(STOP_SLOP)])
        check("--output: ファイルに JSON を書く",
              code == 0 and outp.is_file() and json.loads(outp.read_text(encoding="utf-8"))["doc_type"]["id"] == "blog", out + err)

    # 6 公開リポジトリ用の版に固有名詞が無い（doc-types.local.json が無い版だけ）
    if not (SKILL / "criteria/doc-types.local.json").exists():
        hits = []
        for f in SKILL.rglob("*"):
            if f.is_file() and f.suffix in (".md", ".json", ".py"):
                t = f.read_text(encoding="utf-8", errors="ignore")
                hits += ["%s:%s" % (f.name, tok) for tok in BANNED_TOKENS if tok in t]
        check("公開版: 固有名詞が含まれない", not hits, hits)

    skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    check("SKILL.md: 存在しない verdict_rule を stop-ai-slop-jp のものとして参照しない",
          "stop-ai-slop-jp` の `verdict_rule`" not in skill_text and "stop-ai-slop-jp の verdict_rule" not in skill_text)

    # 7 この repo 固有の種類の試験（run_local_tests.py がある版だけ。公開リポジトリ用の版には置かない）
    local_tests = HERE / "run_local_tests.py"
    if local_tests.exists():
        import importlib.util
        spec = importlib.util.spec_from_file_location("run_local_tests", local_tests)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.run_local(check=check, run=run, SKILL=SKILL, STOP_SLOP=STOP_SLOP, scoring=scoring, BASE_TYPES=BASE_TYPES)

    bad = results.count(False)
    print("RESULT: %s" % ("all as expected" if not bad else "%d NG" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
