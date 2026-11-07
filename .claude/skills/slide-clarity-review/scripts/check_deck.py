#!/usr/bin/env python3
"""check_deck.py — deck-facts.json を scope=deck の auto practice で検査し、auto-results.json を出す。

使い方: python check_deck.py <deck-facts.json> --practices <slide-best-practices.json> -o <auto-results.json>
終了コード: 0=違反なし / 1=違反あり / 2=読込エラー。候補（candidates）は終了コードに影響しない。
判定ロジックは _shared/scripts/slide_checks.py の evaluate_check（構成仕様の検査と共通）。

候補（2026-11 追加。点数に入れない。点検員が画像で確かめるための手がかり。0 件でも問題が無いとは限らない）:
  repeated_topic_terms  見出しから取り出した語（カタカナ 3 字以上・漢字 2 字以上・英数字 3 字以上の連続。一般語は除く）が、
                        2 つ以上の章の見出しに出る（章が無ければ、3 枚以上離れたページの見出しに出る）
  orphan_citations      出典番号があり、同じページに所在の手がかりが無く、参考文献らしいページ（見出しに
                        「参考」「出典」「References」「Sources」）にもその番号が無い（参考文献のページ自体は数えない）
  empty_placeholder     文字も画像も無いプレースホルダーがある（deck-facts の empty_placeholder_count）
  partial_overlap       文字・表・画像の図形が部分的に重なる（deck-facts の overlap_pairs。枠が重なるだけで見た目に
                        重ならないものが多い。2026-11 の実測で、点数に入れる精度に届かなかったため候補にした）
  table_overflow        表の推定の高さ（deck-facts の table_estimates）が、スライドの下端か、下にある図形の上端を 0.1 インチ超える
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "_shared", "scripts"))
import slide_checks as sc  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8")

TERM = re.compile(r"[ァ-ヴー]{3,}|[一-龥々]{2,}|[A-Za-z0-9]{3,}")
COMMON_TERMS = {
    "まとめ", "目次", "概要", "本日", "参考", "付録", "資料", "結果", "方法", "説明", "内容", "課題", "対策", "事例",
    "比較", "次回", "質問", "今回", "全体", "一覧", "背景", "目的", "前提", "補足", "詳細", "効果", "導入", "実演",
    "以下", "以上", "場合", "例題", "要点", "提案", "報告", "確認", "最後", "最初", "章末", "本編",
    "the", "and", "for", "with", "how", "what", "why", "you", "your", "our", "are", "from", "this", "that",
    "summary", "agenda", "appendix", "overview", "introduction", "conclusion", "next", "step", "steps",
}
REFERENCE_TITLE = re.compile(r"参考|出典|references?|sources?", re.I)
OVERFLOW_MARGIN = 0.1  # インチ（運用上の値）
SPREAD_SLIDES = 3


def title_terms(title):
    return {t.lower() if t.isascii() else t for t in TERM.findall(title or "")} - COMMON_TERMS


def repeated_topic_terms(facts):
    slides = facts.get("slides", [])
    section_of = {}
    for i, sec in enumerate(facts.get("sections") or []):
        for no in sec.get("slides", []):
            section_of[no] = i
    use_sections = len(facts.get("sections") or []) >= 2
    where = {}
    for s in slides:
        for t in title_terms(s.get("title")):
            where.setdefault(t, []).append(s["no"])
    out = []
    for term, nos in sorted(where.items()):
        if len(nos) < 2:
            continue
        if use_sections:
            secs = {section_of.get(n) for n in nos} - {None}
            hit = len(secs) >= 2
            detail = "term '%s' in titles of %d sections" % (term, len(secs))
        else:
            hit = max(nos) - min(nos) >= SPREAD_SLIDES
            detail = "term '%s' in titles of slides %s" % (term, ", ".join(map(str, nos)))
        if hit:
            out.append({"kind": "repeated_topic_terms", "slide": nos, "detail": detail})
    return out


def slide_lines(s):
    lines = [s.get("title") or ""]
    for b in s.get("text_blocks") or []:
        lines += b.get("paragraphs") or [c for row in b.get("rows", []) for c in row]
    return lines


def orphan_citations(facts):
    slides = facts.get("slides", [])
    refs = [s for s in slides if REFERENCE_TITLE.search(s.get("title") or "")]
    out = []
    for s in slides:
        cm = s.get("citation_markers") or {}
        if cm.get("has_locator") or any(r is s for r in refs):  # 参考文献のページ自体の番号は一覧なので数えない
            continue
        for marker in cm.get("markers", []):
            num = re.sub(r"\D", "", marker)
            listed = any(marker in line or re.match(r"^\s*\[?%s[\].)、:：\s]" % num, line)
                         for r in refs if r is not s for line in slide_lines(r))
            if not listed:
                out.append({"kind": "orphan_citations", "slide": s["no"],
                            "detail": "%s has no locator on this slide or a reference slide" % marker})
    return out


def table_overflow(facts):
    height = facts.get("slide_height")
    out = []
    for s in facts.get("slides", []):
        for t in s.get("table_estimates") or []:
            if t.get("top") is None or t.get("estimated_height") is None:
                continue
            bottom = t["top"] + t["estimated_height"]
            frame_bottom = t["top"] + (t.get("frame_height") or 0)
            limits = [("slide bottom", height)] if height else []
            for sh in s.get("shapes") or []:
                if None in (sh.get("top"), sh.get("left"), sh.get("width")) or sh.get("kind") == "table" and \
                        sh.get("top") == t["top"] and sh.get("left") == t["left"]:
                    continue
                overlaps_x = sh["left"] < t["left"] + t["width"] and sh["left"] + sh["width"] > t["left"]
                if overlaps_x and sh["top"] >= frame_bottom - 0.01:
                    limits.append(("shape below", sh["top"]))
            for name, edge in limits:
                if bottom > edge + OVERFLOW_MARGIN:
                    out.append({"kind": "table_overflow", "slide": s["no"],
                                "detail": "estimated bottom %.2f in > %s %.2f in%s" % (
                                    bottom, name, edge, " (font assumed 18pt)" if t.get("font_assumed") else "")})
                    break
    return out


def layout_candidates(facts):
    out = []
    for s in facts.get("slides", []):
        if s.get("empty_placeholder_count"):
            out.append({"kind": "empty_placeholder", "slide": s["no"],
                        "detail": "%d empty placeholder(s)" % s["empty_placeholder_count"]})
        for pair in s.get("overlap_pairs") or []:
            out.append({"kind": "partial_overlap", "slide": s["no"],
                        "detail": "%s / %s (ratio %s)" % (pair["a"], pair["b"], pair["ratio"])})
    return out


def candidates(facts):
    return (layout_candidates(facts) + repeated_topic_terms(facts) + orphan_citations(facts)
            + table_overflow(facts))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("facts")
    ap.add_argument("--practices", required=True)
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args(argv)
    try:
        facts = sc.load_json(args.facts)
        practices = sc.load_json(args.practices).get("practices", [])
    except (OSError, ValueError) as e:
        print("ERROR: %s" % e, file=sys.stderr)
        return 2
    autos = [p for p in practices if p["check"].get("method") == "auto" and p["check"].get("scope") == "deck"]
    violations = []
    for slide in facts.get("slides", []):
        for p in autos:
            msg = sc.evaluate_check(p, slide.get(p["check"]["metric"]))
            if msg:
                violations.append({"practice_id": p["id"], "slide": slide["no"], "severity": p["severity"],
                                   "message": "slide %s: %s" % (slide["no"], msg)})
    cands = candidates(facts)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"violations": violations, "candidates": cands, "limitations": facts.get("limitations", [])}, f,
                  ensure_ascii=False, indent=2)
    for v in violations:
        print(v["message"], file=sys.stderr)
    if cands:
        print("candidates (not scored): %d" % len(cands), file=sys.stderr)
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
