#!/usr/bin/env python
"""資料の種類に応じて、stop-ai-slop-jp の観点を選んで JSON で返す。標準ライブラリのみ。

使い方:
  python select_viewpoints.py --list
  python select_viewpoints.py --doc-type <種類の id> [--output <path>]
  python select_viewpoints.py --validate
オプション:
  --criteria-dir <dir>   viewpoints.json・axes.json・doc-types.json を置いた場所（既定: この skill の criteria/）
  --stop-slop-dir <dir>  stop-ai-slop-jp の skill のフォルダ（既定: この skill と同じ階層の stop-ai-slop-jp/）
  doc-types.local.json   criteria-dir にあれば、そのリポジトリ固有の種類として合流する（汎用の id と衝突したら不合格）
終了コード: 0 成功 / 1 検査の不合格（--validate） / 2 使い方の誤り・未知の種類・入力が読めない。
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
SKILL = Path(__file__).resolve().parents[1]
REQUIRED_BLOCKERS = ("misattribution", "audience_underassertion")
BASE_AXES = ("stance", "rhythm", "agency", "concreteness", "reduction")
SKIP_CAP = 5                                   # max_skip の上限（viewpoints.json の limits をこれより緩めて通さない）
NEVER_SKIP_MIN = ("R01", "R11", "R12", "R14")  # never_skip が必ず含む規則（apply 以外にできない）
REPLACEMENT_FIELDS = ("ground", "keeps", "counter_examples")
OVERRIDE_FIELDS = ("question", "anchors", "ground", "keeps", "counter_examples")
DOC_TYPE_KEYS = ("id", "name", "description", "recognize", "rules", "axes", "blockers")


class Fail(Exception):
    pass


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as ex:
        raise Fail("読めない: %s（%s）" % (path, ex))


class Catalog:
    def __init__(self, criteria_dir, stop_slop_dir):
        self.cd = Path(criteria_dir)
        self.ss = Path(stop_slop_dir)
        self.vp = load_json(self.cd / "viewpoints.json")
        self.axes_extra = {a["id"]: a for a in load_json(self.cd / "axes.json").get("axes", [])}
        self.scoring = load_json(self.ss / "criteria/scoring.json")
        try:
            self.skill_md = (self.ss / "SKILL.md").read_text(encoding="utf-8")
        except OSError as ex:
            raise Fail("読めない: %s（%s）" % (self.ss / "SKILL.md", ex))
        base = load_json(self.cd / "doc-types.json").get("doc_types", [])
        self.base_ids = [t.get("id") for t in base]
        local_path = self.cd / "doc-types.local.json"
        local = load_json(local_path).get("doc_types", []) if local_path.is_file() else []
        self.local_ids = [t.get("id") for t in local]
        self.doc_types = base + local
        self.rules = {r["id"]: r for r in self.vp["rules"]}
        self.blockers = {b["id"]: b for b in self.vp["blockers"]}
        self.pass_rule = self.scoring["pass_rule"]

    def axis(self, axis_id):
        """軸の完全な定義と出どころ。scoring.json の criteria → axes.json → 各 profile の replaced_criteria の順に引く。
        axes.json を profile より先にするのは、scoring.json の持つ profile の有無（repo ごとの差）で、同じ軸の定義が変わらないようにするため。"""
        for c in self.scoring.get("criteria", []):
            if c.get("id") == axis_id:
                return dict(c), "stop-ai-slop-jp/criteria/scoring.json の criteria"
        if axis_id in self.axes_extra:
            return dict(self.axes_extra[axis_id]), "select-slop-viewpoints/criteria/axes.json"
        for pname, prof in (self.scoring.get("profiles") or {}).items():
            for c in prof.get("replaced_criteria", []) or []:
                if c.get("id") == axis_id:
                    return dict(c), "stop-ai-slop-jp/criteria/scoring.json の profiles.%s.replaced_criteria" % pname
        return None, None

    def find(self, doc_type_id):
        return next((t for t in self.doc_types if t.get("id") == doc_type_id), None)

    # ---- 検査 ----
    def validate(self):
        errs = []
        lim = self.vp.get("limits", {})
        # 目録
        if [r["id"] for r in self.vp["rules"]] != ["R%02d" % i for i in range(1, 15)]:
            errs.append("viewpoints: 規則は R01〜R14 を順に重複なく持つ")
        for r in self.vp["rules"]:
            pat = r"^%d\. \*\*%s\*\*" % (r.get("number", 0), re.escape(str(r.get("source_title"))))
            if not re.search(pat, self.skill_md, flags=re.M):
                errs.append("viewpoints: %s（%s 番）の見出し語 %s が stop-ai-slop-jp/SKILL.md の同じ番号に無い（上流の見出し・番号が変わった）" % (r["id"], r.get("number"), r.get("source_title")))
        if lim.get("max_skip", 99) > SKIP_CAP:
            errs.append("limits: max_skip が上限 %d を超える（緩めた）: %s" % (SKIP_CAP, lim.get("max_skip")))
        if not set(NEVER_SKIP_MIN) <= set(lim.get("never_skip", [])):
            errs.append("limits: never_skip は %s を含む（外した）" % ", ".join(NEVER_SKIP_MIN))
        for b in REQUIRED_BLOCKERS:
            if b not in self.blockers:
                errs.append("viewpoints: blocker %s の定義が無い" % b)
        for b in (self.scoring.get("blocker_checks") or {}).get("items", []):
            if b.get("id") not in self.blockers:
                errs.append("viewpoints: scoring.json の blocker %s が目録に無い" % b.get("id"))
        # id 重複
        seen = set()
        for tid in self.base_ids + self.local_ids:
            if tid in seen:
                errs.append("doc-types: id が重複: %s（局所の種類は汎用の id と衝突させない）" % tid)
            seen.add(tid)
        # 種類ごと
        max_total = self.pass_rule["max_total"]
        for t in self.doc_types:
            tid = t.get("id", "?")
            for k in DOC_TYPE_KEYS:
                if k not in t:
                    errs.append("%s: 必須キー %s が無い" % (tid, k))
            rules = t.get("rules", {})
            for rid in self.rules:
                if rid not in rules:
                    errs.append("%s: 規則 %s の扱いが無い" % (tid, rid))
            skips = 0
            for rid, spec in rules.items():
                tr = spec.get("treatment")
                if rid not in self.rules:
                    errs.append("%s: 知らない規則 %s" % (tid, rid))
                if tr not in lim.get("treatments", []):
                    errs.append("%s: %s の treatment が不正: %s" % (tid, rid, tr))
                if tr in ("modify", "conditional") and not str(spec.get("condition", "")).strip():
                    errs.append("%s: %s は %s なので condition（条件）が要る" % (tid, rid, tr))
                if rid in NEVER_SKIP_MIN and tr != "apply":
                    errs.append("%s: %s は never_skip の規則で、apply 以外（%s）にできない" % (tid, rid, tr))
                if tr == "skip":
                    skips += 1
                    if not str(spec.get("covered_by", "")).strip():
                        errs.append("%s: %s を skip するには受け持ち先 covered_by が要る" % (tid, rid))
            if skips > lim.get("max_skip", 5):
                errs.append("%s: skip が %d 件で上限 max_skip=%d を超える" % (tid, skips, lim.get("max_skip", 5)))
            axes = t.get("axes", [])
            if len(axes) != 5:
                errs.append("%s: 軸は 5 つ（現在 %d）" % (tid, len(axes)))
            if len(set(axes)) != len(axes):
                errs.append("%s: 軸が重複している: %s" % (tid, axes))
            defs = {}
            for a in axes:
                d, _ = self.axis(a)
                if d is None:
                    errs.append("%s: 軸 %s が scoring.json にも axes.json にも無い" % (tid, a))
                else:
                    defs[a] = d
            # 基本の 5 軸は、そのまま使うか、根拠付き（axis_replacements）で置き換える
            reps = t.get("axis_replacements") or {}
            for base in BASE_AXES:
                if base in axes:
                    continue
                rep = [a for a, d in defs.items() if d.get("replaces") == base]
                if not rep:
                    errs.append("%s: 基本の軸 %s も、それを置き換える軸も無い" % (tid, base))
                    continue
                spec = reps.get(rep[0])
                if not isinstance(spec, dict) or spec.get("replaces") != base or not all(spec.get(f) for f in REPLACEMENT_FIELDS):
                    errs.append("%s: 軸 %s が %s を置き換えるには axis_replacements[%s] に replaces=%s と %s が要る（根拠の無い置き換えは認めない）" % (tid, rep[0], base, rep[0], base, "・".join(REPLACEMENT_FIELDS)))
                elif len(spec.get("counter_examples", [])) < 2:
                    errs.append("%s: axis_replacements[%s] の counter_examples は 2 件以上" % (tid, rep[0]))
            for a, d in defs.items():
                if a not in BASE_AXES and d.get("replaces") not in BASE_AXES:
                    errs.append("%s: 軸 %s は基本の軸を置き換えない（余計な軸）" % (tid, a))
            if len(axes) and max_total % len(axes):
                errs.append("%s: 軸の数 %d で max_total %d を割り切れない" % (tid, len(axes), max_total))
            for b in REQUIRED_BLOCKERS:
                if b not in t.get("blockers", []):
                    errs.append("%s: blocker %s が無い（全ての種類で残す）" % (tid, b))
            for b in t.get("blockers", []):
                if b not in self.blockers:
                    errs.append("%s: 知らない blocker %s" % (tid, b))
            ip = t.get("inherit_profile")
            if ip and ip not in (self.scoring.get("profiles") or {}):
                errs.append("%s: inherit_profile %s が scoring.json の profiles に無い" % (tid, ip))
            # agency・concreteness は読み替えない規定（G3）がある repo では、調整を scoring.json の G3.exceptions に残す
            g3 = [g for prof in (self.scoring.get("profiles") or {}).values() for g in (prof.get("guards") or []) if g.get("id") == "G3"]
            for aid in ("agency", "concreteness"):
                if g3 and aid in (t.get("axis_overrides") or {}) and not any(tid in (g.get("exceptions") or []) for g in g3):
                    errs.append("%s: %s を調整するには、scoring.json の G3（読み替えない規定）の exceptions に %s を根拠付きで残す（G3）" % (tid, aid, tid))
            for aid, ov in (t.get("axis_overrides") or {}).items():
                if aid not in axes:
                    errs.append("%s: axis_overrides の軸 %s は、この種類の axes に無い" % (tid, aid))
                for f in OVERRIDE_FIELDS:
                    if f not in ov or not ov[f]:
                        errs.append("%s: axis_overrides[%s] に %s が要る（根拠の無い調整は認めない）" % (tid, aid, f))
                if len(ov.get("counter_examples", [])) < 2:
                    errs.append("%s: axis_overrides[%s] の counter_examples は 2 件以上（調整後も減点が残る例）" % (tid, aid))
                if not isinstance(ov.get("keeps", []), list):
                    errs.append("%s: axis_overrides[%s].keeps は配列" % (tid, aid))
                if "anchors" in ov and not all(k in ov["anchors"] for k in ("1", "5", "10")):
                    errs.append("%s: axis_overrides[%s].anchors は 1・5・10 の 3 点を持つ" % (tid, aid))
        return errs

    # ---- 選択 ----
    def select(self, doc_type_id):
        t = self.find(doc_type_id)
        if t is None:
            raise KeyError(doc_type_id)
        n = len(t["axes"])
        weight = self.pass_rule["max_total"] // n
        out_axes = []
        for aid in t["axes"]:
            d, src = self.axis(aid)
            ov = (t.get("axis_overrides") or {}).get(aid)
            ax = {"id": aid, "name": d.get("name", aid), "weight": weight, "source": src,
                  "question": d.get("question"), "anchors": d.get("anchors"), "note": d.get("note")}
            if "replaces" in d:
                ax["replaces"] = d["replaces"]
            if ov:
                ax["question"], ax["anchors"] = ov["question"], ov["anchors"]
                ax["override"] = {k: ov[k] for k in ("ground", "keeps", "counter_examples")}
            out_axes.append(ax)
        rules = []
        for rid, r in self.rules.items():
            spec = t["rules"][rid]
            item = {"id": rid, "number": r["number"], "group": r["group"], "name": r["name"], "summary": r["summary"],
                    "treatment": spec["treatment"]}
            for k in ("condition", "covered_by"):
                if spec.get(k):
                    item[k] = spec[k]
            rules.append(item)
        sel = {
            "schema": "slop-viewpoints-selection/v1",
            "doc_type": {k: t[k] for k in ("id", "name", "description", "recognize")},
            "rules": rules,
            "axes": out_axes,
            "blockers": [self.blockers[b] for b in t["blockers"]],
            "pass_rule": self.pass_rule,
            "procedure": self.vp.get("procedure"),
            "notes": t.get("notes", []),
            "instructions_for_scorers": [
                "treatment が skip の規則は指摘しない（covered_by が受け持つ）。modify と conditional は condition の範囲だけで適用する。",
                "軸は axes の question と anchor で採点する。override がある軸は、override の question と anchor を使い、keeps の点は緩めない。inherited_profile がある時は、その guards・finding_labels・scope・rebuttal_rule も守る（この JSON を唯一の入力にする）。",
                "blockers は点に関わらず最優先で是正を求める。",
                "合否は pass_rule.min_total との比較で、procedure.verdict_rule（独立 3 回の中央値）に従う。採点の範囲は procedure.scoring_scope に従う。",
            ],
        }
        for k in ("layout", "parameters"):
            if t.get(k):
                sel[k] = t[k]
        ip = t.get("inherit_profile")
        if ip:
            prof = self.scoring["profiles"][ip]
            sel["inherited_profile"] = {"name": ip, **{k: prof[k] for k in ("guards", "finding_labels", "scope", "rebuttal_rule", "verdict_rule") if k in prof}}
        return sel


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="資料の種類に応じて stop-ai-slop-jp の観点を選び、JSON で返す")
    ap.add_argument("--doc-type")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--output")
    ap.add_argument("--criteria-dir", default=str(SKILL / "criteria"))
    ap.add_argument("--stop-slop-dir", default=str(SKILL.parent / "stop-ai-slop-jp"))
    a = ap.parse_args(argv)
    if not (a.doc_type or a.list or a.validate):
        ap.print_usage(sys.stderr)
        return 2
    try:
        cat = Catalog(a.criteria_dir, a.stop_slop_dir)
    except Fail as ex:
        print("ERROR: %s" % ex, file=sys.stderr)
        return 2
    if a.validate:
        errs = cat.validate()
        for e in errs:
            print("ERROR %s" % e)
        print("%s: %d 種類を検査（%d 件の違反）" % ("NG" if errs else "OK", len(cat.doc_types), len(errs)))
        return 1 if errs else 0
    if a.list:
        print(json.dumps([{"id": t["id"], "name": t["name"], "description": t["description"]} for t in cat.doc_types], ensure_ascii=False, indent=2))
        return 0
    errs = cat.validate()
    if errs:
        print("ERROR: 基準の検査が不合格のため選択しない（--validate で確認する）: %s" % errs[0], file=sys.stderr)
        return 2
    try:
        sel = cat.select(a.doc_type)
    except KeyError:
        print("ERROR: 未知の資料の種類: %s。使える種類: %s" % (a.doc_type, ", ".join(t["id"] for t in cat.doc_types)), file=sys.stderr)
        return 2
    text = json.dumps(sel, ensure_ascii=False, indent=2)
    if a.output:
        Path(a.output).write_text(text + "\n", encoding="utf-8", newline="\n")
        print("OK: %s" % a.output)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
