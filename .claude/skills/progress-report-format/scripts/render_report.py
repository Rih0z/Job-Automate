#!/usr/bin/env python3
"""進捗報告データ（progress-report/v1）を検証し、criteria/report-format.json の形式で整形して出力する。

使い方: python render_report.py <report.json> [--spec <report-format.json>] [-o <out.txt>]
終了コード: 0=出力した / 1=データが形式に合わない（理由は stderr、stdout は空） / 2=読み込み・引数の誤り
"""
import argparse
import json
import os
import re
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SPEC = os.path.join(os.path.dirname(HERE), "criteria", "report-format.json")
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LEADING_MARKS = ("・", "■", "-", "*", "•")


def _parse_date(s):
    if not isinstance(s, str) or not ISO.match(s):
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def _bad_text(v):
    """1 行の文字列として使えない理由を返す。使えるなら None。"""
    if not isinstance(v, str) or not v.strip():
        return "空、または文字列でない"
    if "\n" in v or "\r" in v:
        return "改行を含む"
    if v.lstrip().startswith(LEADING_MARKS):
        return "先頭に記号がある（記号は整形で付く）"
    return None


def validate(report, spec):
    errs = []
    if not isinstance(report, dict) or report.get("schema") != "progress-report/v1":
        return ["schema は progress-report/v1 にする"]
    period = report.get("period")
    start = _parse_date(period.get("start")) if isinstance(period, dict) else None
    end = _parse_date(period.get("end")) if isinstance(period, dict) else None
    if start is None or end is None:
        errs.append("period.start / period.end は YYYY-MM-DD の実在する日付にする")
    elif end < start:
        errs.append("period.end は period.start 以降にする")

    sections = report.get("sections")
    if not isinstance(sections, dict):
        return errs + ["sections がオブジェクトでない"]
    ids = [s["id"] for s in spec["sections"]]
    for sid in sections:
        if sid not in ids:
            errs.append("未定義の章: %s（定義: %s）" % (sid, ", ".join(ids)))
    for sec in spec["sections"]:
        sid = sec["id"]
        items = sections.get(sid)
        if items is None:
            if sec.get("required"):
                errs.append("必須の章がない: %s" % sid)
            continue
        if not isinstance(items, list) or not items:
            errs.append("%s: 1 件以上の配列にする（無い時は「なし」と書く）" % sid)
            continue
        for i, it in enumerate(items):
            where = "%s[%d]" % (sid, i)
            if sec["kind"] == "bullets":
                why = _bad_text(it)
                if why:
                    errs.append("%s: %s" % (where, why))
            else:
                if not isinstance(it, dict):
                    errs.append("%s: オブジェクトにする" % where)
                    continue
                why = _bad_text(it.get("name"))
                if why:
                    errs.append("%s.name: %s" % (where, why))
                if it.get("stage") not in spec["stages"]:
                    errs.append("%s.stage は %s のいずれか" % (where, "・".join(spec["stages"])))
                if it.get("progress") not in spec["progress_phrases"]:
                    errs.append("%s.progress は %s のいずれか" % (where, "・".join(spec["progress_phrases"])))
                if "note" in it and it["note"] is not None:
                    why = _bad_text(it["note"])
                    if why:
                        errs.append("%s.note: %s" % (where, why))
    return errs


def render(report, spec):
    p = report["period"]
    out = [spec["title_template"].format(start=p["start"], end=p["end"]), ""]
    bullet = spec["bullet_prefix"]
    left, right = spec["note_wrap"]
    stages = "→".join(spec["stages"])
    for sec in spec["sections"]:
        out.append(spec["heading_prefix"] + sec["heading"].format(stages=stages))
        for it in report["sections"][sec["id"]]:
            if sec["kind"] == "bullets":
                out.append(bullet + it.strip())
            else:
                phrase = spec["progress_phrases"][it["progress"]].format(stage=it["stage"])
                note = (left + it["note"].strip() + right) if it.get("note") else ""
                out.append(bullet + spec["initiative_line"].format(name=it["name"].strip(), phrase=phrase, note=note))
        out.append("")
    return "\n".join(out).rstrip("\n") + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("report")
    ap.add_argument("--spec", default=DEFAULT_SPEC)
    ap.add_argument("-o", "--output")
    args = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    try:
        with open(args.spec, encoding="utf-8") as f:
            spec = json.load(f)
        with open(args.report, encoding="utf-8") as f:
            report = json.load(f)
    except (OSError, ValueError) as e:
        print("読み込めない: %s" % e, file=sys.stderr)
        return 2
    errs = validate(report, spec)
    if errs:
        for e in errs:
            print("形式に合わない: " + e, file=sys.stderr)
        return 1
    text = render(report, spec)
    if args.output:
        with open(args.output, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
