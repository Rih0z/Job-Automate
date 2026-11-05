#!/usr/bin/env python3
"""スライド文面の機械検査（標準ライブラリのみ）。

入力: slide-clarity-review の extract_deck.py が出す deck-facts.json
出力: 指摘の一覧（すべて should 扱い。採点はしない。ブロッカーは「候補」を出すだけで、判定は別エージェントが行う）

検査:
- mixed-register: 1 枚の本文で、敬体（です・ます）の文と、常体（だ・である＋句点）の文が混在。
  体言止めは、敬体とも常体とも比較しない（スライドの普通の書き方）
- duplicate: ほぼ同じ内容の段落（正規化後 8 字以上、類似度 0.85 以上）。同じスライド内の完全一致も拾う
- mixed-paren: デッキ内で、全角の括弧と半角の括弧が混在
- number-only-ref: 「1 → 2 → 3」のような番号だけの段落（各番号の名前が同じスライドにあるか要確認）。同じスライドに「4 枚目の番号」のように定義の場所を明示した文があれば、検出しない
- fullwidth-dash: 全角ダッシュ（―・—）の使用（日本語の文章では、長い横線を使わない運用の確認用）
- b2-candidate: criteria/memo-words.json の語（作業メモ・プレースホルダー・指示文）を含む段落。ブロッカー B2 の候補で、判定は人が行う
- stock-phrase: criteria/memo-words.json の常套句を含む段落（軸 5 の参考情報）
使い方: python check_ja_slide.py deck-facts.json -o ja-auto.json
"""
import argparse
import difflib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORDS = os.path.join(HERE, "..", "criteria", "memo-words.json")

for _s in (sys.stdout, sys.stderr):  # Windows の既定の文字コードで日本語の出力が落ちないようにする
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8")

POLITE = re.compile(r"(です|ます|ません|ください|でした|ました|でしょう)[。！!]?$")
PLAIN_SENTENCE = re.compile(r"(だ|である|ない|した|する|いる|ある)。$")
NUMBER_REF = re.compile(r"^[\d０-９]+(\s*[→⇒>＞-]\s*[\d０-９]+)+$")


def norm(t):
    return re.sub(r"[\s、。，．,.・「」『』（）()：:；;\-–—―→]", "", t)


def load_words():
    try:
        return json.load(open(WORDS, encoding="utf-8"))
    except (OSError, ValueError):
        return {"memo_words": [], "stock_phrases": []}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("facts")
    ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()
    d = json.load(open(a.facts, encoding="utf-8"))
    words = load_words()
    findings = []
    all_paras = []  # (slide_no, text)
    has_full_paren = has_half_paren = False

    for s in d["slides"]:
        no = s["no"]
        title = (s.get("title") or "").strip()
        blocks = s.get("text_blocks")
        if blocks:  # 位置順の文面。表のセルも読む
            raw = []
            for blk in blocks:
                if blk.get("kind") == "table":
                    for row in blk.get("rows", []):
                        raw.extend(row)
                else:
                    raw.extend(blk.get("paragraphs", []))
        else:
            raw = s.get("paragraphs", [])
        paras = [p.strip() for p in raw if p and p.strip()]
        body = [p for p in paras if p != title]
        for p in paras:
            all_paras.append((no, p))
            if re.search(r"[（）]", p):
                has_full_paren = True
            if re.search(r"[()]", p):
                has_half_paren = True
            if NUMBER_REF.match(p.replace(" ", "")) and not any(re.search(r"枚目の番号|番号は\s*[0-9０-９]+\s*枚目|番号）", q) for q in paras):
                findings.append({"slide": no, "check": "number-only-ref", "severity": "should",
                                 "detail": f"番号だけの参照: 「{p}」。各番号の名前が同じスライドにあるか確認する"})
            if re.search(r"[―—]", p):
                findings.append({"slide": no, "check": "fullwidth-dash", "severity": "should",
                                 "detail": f"全角ダッシュ: 「{p[:40]}」"})
            for w in words.get("memo_words", []):
                if w in p:
                    findings.append({"slide": no, "check": "b2-candidate", "severity": "candidate",
                                     "detail": f"作業メモ・プレースホルダー・指示文の候補「{w}」: 「{p[:40]}」。人が判定する"})
            for w in words.get("stock_phrases", []):
                if w in p:
                    findings.append({"slide": no, "check": "stock-phrase", "severity": "should",
                                     "detail": f"常套句「{w}」: 「{p[:40]}」"})
        polite = [p for p in body if POLITE.search(p)]
        plain = [p for p in body if PLAIN_SENTENCE.search(p) and not POLITE.search(p)]
        if polite and plain:
            findings.append({"slide": no, "check": "mixed-register", "severity": "should",
                             "detail": f"敬体 {len(polite)} 段落と、常体 {len(plain)} 段落が混在。例: 「{polite[0][:30]}」／「{plain[0][:30]}」"})

    # 重複: 位置（添字）で自己比較を除外し、同じスライド内の完全一致も拾う
    normed = [(no, p, norm(p)) for no, p in all_paras]
    reported = set()
    for i, (no, p, n) in enumerate(normed):
        if len(n) < 8:
            continue
        for j in range(i):
            no2, p2, n2 = normed[j]
            if len(n2) < 8:
                continue
            if n == n2 or difflib.SequenceMatcher(None, n, n2).ratio() >= 0.85:
                key = (j, i)
                if key not in reported:
                    reported.add(key)
                    where = "同じスライド内" if no == no2 else f"slide {no2}"
                    findings.append({"slide": no, "check": "duplicate", "severity": "should",
                                     "detail": f"{where}の「{p2[:40]}」とほぼ同じ内容: 「{p[:40]}」"})
                break

    if has_full_paren and has_half_paren:
        findings.append({"slide": None, "check": "mixed-paren", "severity": "should",
                         "detail": "デッキ内で、全角の括弧と半角の括弧が混在"})

    out = {"file": d.get("file"), "slide_count": d.get("slide_count"), "findings": findings,
           "note": "機械検査は should 扱い（b2-candidate は候補）。採点と合否は別エージェントが行う"}
    json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"findings: {len(findings)}")
    for f in findings:
        print(f"slide {f['slide']}: [{f['check']}] {f['detail']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
