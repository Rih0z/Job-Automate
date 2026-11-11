#!/usr/bin/env python3
"""article.json（記事 HTML の正本）から HTML を決定的に生成する。修正は指摘台帳（fix-ledger.json）つきで JSON に反映してから再生成する。

標準ライブラリのみ。外部通信なし。ブロック定義・インライン HTML の許可タグ・台帳の条件は
../criteria/article-schema.json が正本で、この script はそれを読んで検査する。

使い方（どこから実行してもよい。パスは実行時の作業ディレクトリ基準）:
  render_article.py check       <article.json>                        JSON と台帳の検査（書込なし）
  render_article.py render      <article.json> [--year YYYY] [--out PATH]
                                                                     台帳ゲート → 生成 → 検査 → meta.output へ書込 → 台帳に記録
                                                                     （--out に別の名前を渡すと試し出力。台帳に記録しない）
  render_article.py verify      <article.json> [--html PATH] [--year YYYY]
                                                                     再生成した結果と既存 HTML のバイト一致（手編集・未再生成の検出）
  render_article.py compare     <a.html> <b.html>                     空白差を無視した比較
  render_article.py init-ledger <article.json>                        空の台帳を作る（出力 HTML が既にあれば拒否）

終了コード: 0 = 成功 / 1 = 検査で問題あり（理由は stderr）/ 2 = 使い方の誤り
"""
import datetime
import hashlib
import html as htmllib
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

CRITERIA = Path(__file__).resolve().parent.parent / "criteria" / "article-schema.json"
EMOJI_RX = re.compile("[☀-➿⭐⭕\U0001F000-\U0001FAFF]")
VOID = {"br"}
YEAR_TOKEN = "{{YEAR}}"


def load_criteria():
    return json.loads(CRITERIA.read_text(encoding="utf-8"))


C = load_criteria()
ART, LED = C["article"], C["ledger"]
BLOCKS = ART["block_types"]
ALLOWED = {t: set(a) for t, a in ART["inline_html"]["allowed_tags"].items()}
BID_RX = re.compile(ART["bid_pattern"])


def setup_stdio():
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8")


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


# ------------------------------------------------------------ 検査

class _Inline(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.problems, self.stack = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in ALLOWED:
            self.problems.append("許可外のタグ <%s>" % tag)
            return
        bad = [k for k, _ in attrs if k not in ALLOWED[tag]]
        if bad:
            self.problems.append("<%s> に許可外の属性 %s" % (tag, ",".join(bad)))
        if tag not in VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        if tag not in VOID:
            self.problems.append("<%s/> は使えない" % tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack or self.stack[-1] != tag:
            self.problems.append("閉じタグ </%s> の対応が取れない" % tag)
        else:
            self.stack.pop()

    def handle_comment(self, data):
        self.problems.append("インラインに HTML コメントは書けない")


def check_inline(s, where):
    if not isinstance(s, str):
        return ["%s: 文字列でない" % where]
    p = _Inline()
    p.feed(s)
    p.close()
    probs = p.problems + (["閉じていないタグ " + ",".join(p.stack)] if p.stack else [])
    if EMOJI_RX.search(s):
        probs.append("絵文字・記号アイコン")
    return ["%s: %s" % (where, x) for x in probs]


def inline_fields(b):
    """(場所, 文字列) — 限定インライン HTML として検査する項目。"""
    t = b.get("type")
    out = []
    if t in ("heading", "p", "note"):
        out.append(("html", b.get("html")))
    elif t == "list":
        def walk(items, w):
            for i, it in enumerate(items or []):
                if isinstance(it, dict):
                    out.append(("%s[%d].html" % (w, i), it.get("html")))
                    walk(it.get("list", {}).get("items"), "%s[%d].list.items" % (w, i))
                else:
                    out.append(("%s[%d]" % (w, i), it))
        walk(b.get("items"), "items")
    elif t == "table":
        out += [("columns[%d]" % i, c) for i, c in enumerate(b.get("columns") or [])]
        out += [("rows[%d][%d]" % (r, c), v) for r, row in enumerate(b.get("rows") or []) for c, v in enumerate(row)]
        if "caption" in b:
            out.append(("caption", b["caption"]))
    elif t == "quote":
        out += [("paragraphs[%d]" % i, p) for i, p in enumerate(b.get("paragraphs") or [])]
        if "cite" in b:
            out.append(("cite", b["cite"]))
    elif t == "qa":
        for i, qa in enumerate(b.get("items") or []):
            out += [("items[%d].q" % i, qa.get("q")), ("items[%d].a" % i, qa.get("a"))]
    elif t == "glossary":
        for i, tm in enumerate(b.get("terms") or []):
            out += [("terms[%d].term" % i, tm.get("term")), ("terms[%d].desc" % i, tm.get("desc"))]
    elif t == "references":
        out += [("items[%d].html" % i, it.get("html")) for i, it in enumerate(b.get("items") or [])]
    elif t == "image" and "caption" in b:
        out.append(("caption", b["caption"]))
    return out


def validate_article(doc):
    out = []
    if doc.get("schema") != ART["schema_id"]:
        out.append("schema が %s でない" % ART["schema_id"])
    meta = doc.get("meta") or {}
    for k in ("title", "output"):
        if not meta.get(k):
            out.append("meta.%s が無い" % k)
    if meta.get("template", "fragment") not in ("fragment", "page"):
        out.append("meta.template は fragment か page")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", meta.get("partials_dir", "partials")):
        out.append("meta.partials_dir は記事フォルダ直下の名前だけ")
    blocks = doc.get("blocks")
    if not isinstance(blocks, list):
        return out + ["blocks が配列でない"]
    bids, ids = [], []
    for i, b in enumerate(blocks):
        w = "blocks[%d]" % i
        if not isinstance(b, dict) or b.get("type") not in BLOCKS:
            out.append("%s: 不明な type %r" % (w, b.get("type") if isinstance(b, dict) else b))
            continue
        if not isinstance(b.get("bid"), str) or not BID_RX.fullmatch(b["bid"]):
            out.append("%s: bid が無いか不正" % w)
        bids.append(b.get("bid"))
        for k in BLOCKS[b["type"]]["required"]:
            if k not in b:
                out.append("%s(%s): %s が無い" % (w, b["type"], k))
        for where, s in inline_fields(b):
            out += check_inline(s, "%s.%s" % (w, where))
        t = b["type"]
        if t == "heading":
            if b.get("level") not in (2, 3, 4):
                out.append("%s: level は 2〜4" % w)
            if "id" in b:
                if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", b["id"]):
                    out.append("%s: id が不正" % w)
                ids.append(b["id"])
        elif t == "table":
            n = len(b.get("columns") or [])
            for r, row in enumerate(b.get("rows") or []):
                if len(row) != n:
                    out.append("%s: rows[%d] の列数 %d が columns の %d と違う" % (w, r, len(row), n))
        elif t == "code":
            if not re.fullmatch(r"[a-z0-9+-]+", str(b.get("language", ""))):
                out.append("%s: language が不正" % w)
            if EMOJI_RX.search(b.get("code", "")):
                out.append("%s: 絵文字・記号アイコン" % w)
        elif t == "image":
            if not str(b.get("alt", "")).strip():
                out.append("%s: alt が空" % w)
        elif t == "include":
            if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", str(b.get("name", ""))):
                out.append("%s: include の name は英小文字・数字・-" % w)
        elif t == "raw_html":
            h = b.get("html", "")
            if "<script" in h.lower() or EMOJI_RX.search(h):
                out.append("%s: raw_html に script・絵文字は書けない" % w)
    for t in ("toc", "glossary"):
        if sum(1 for b in blocks if isinstance(b, dict) and b.get("type") == t) > 1:
            out.append("%s は 1 つまで" % t)
    for name, seq in (("bid", bids), ("見出し id", ids)):
        dup = sorted({str(x) for x in seq if seq.count(x) > 1})
        if dup:
            out.append("%s の重複: %s" % (name, ",".join(dup)))
    types = [b.get("type") for b in blocks if isinstance(b, dict)]
    if "glossary" in types and "references" in types and types.index("glossary") > types.index("references"):
        out.append("glossary は references より前に置く")
    if EMOJI_RX.search(json.dumps(meta, ensure_ascii=False)):
        out.append("meta: 絵文字・記号アイコン")
    return out


# ------------------------------------------------------------ 台帳

def ledger_path(article):
    return Path(article).with_name(LED["file_name"])


def block_hashes(doc):
    h = lambda o: hashlib.sha256(json.dumps(o, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:16]  # noqa: E731
    out = {"meta": h(doc.get("meta", {}))}
    for b in doc.get("blocks", []):
        if isinstance(b, dict) and isinstance(b.get("bid"), str):
            out[b["bid"]] = h(b)
    return out


def new_ledger(doc, kind="draft"):
    """kind = draft（新規。最初の render までは執筆中として変更を照合しない）/ baseline（既存の記事を取り込んだ時点）。"""
    return {"schema": LED["schema_id"], "article": doc["meta"].get("output", ""), "fixes": [],
            "renders": [{"at": now_iso(), "kind": kind, "block_hashes": block_hashes(doc), "fixes": []}]}


def validate_ledger(led, doc):
    if led is None:
        return ["%s が無い（init-ledger で作る）" % LED["file_name"]]
    out = []
    if led.get("schema") != LED["schema_id"]:
        out.append("台帳の schema が %s でない" % LED["schema_id"])
    renders = led.get("renders", [])
    done = {f for r in renders for f in r.get("fixes", [])}
    last = renders[-1].get("block_hashes") if renders and renders[-1].get("kind") != "draft" else None
    cur = block_hashes(doc)
    covered, seen = set(), set()
    for i, f in enumerate(led.get("fixes", [])):
        fid = f.get("id")
        w = "fixes[%d](%s)" % (i, fid)
        if not fid or fid in seen:
            out.append("%s: id が無いか重複" % w)
        seen.add(fid)
        if not f.get("request"):
            out.append("%s: request（依頼者の原文）が空" % w)
        st = f.get("status")
        if st == "open":
            out.append("%s: 未反映（open）が残っている" % w)
        elif st == "applied":
            for k in ("targets", "change", "applied"):
                if not f.get(k):
                    out.append("%s: applied なのに %s が無い" % (w, k))
            if f.get("source_sync") not in ("done", "not-needed"):
                out.append("%s: source_sync が done / not-needed でない" % w)
            tg = f.get("targets") or []
            if fid not in done:
                covered |= set(tg)
                bad = [t for t in tg if t not in set(cur) | set(last or {})]
                if bad:
                    out.append("%s: targets に存在しない bid: %s" % (w, ",".join(bad)))
                elif last is not None and tg and not any(cur.get(t) != last.get(t) for t in tg):
                    out.append("%s: applied だが targets のブロックが前回の記録から変わっていない" % w)
        elif st == "rejected":
            if not f.get("reason"):
                out.append("%s: rejected の理由（reason）が無い" % w)
        else:
            out.append("%s: status は open / applied / rejected" % w)
    if last is not None:
        stray = sorted(k for k in set(cur) | set(last) if cur.get(k) != last.get(k) and k not in covered)
        if stray:
            out.append("台帳の指摘に紐づかない変更がある（前回の記録から変わったブロック: %s）" % ",".join(stray))
    return out


# ------------------------------------------------------------ 生成

def strip_tags(s):
    return htmllib.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def ext_links(s):
    """http(s) のリンクに target / rel を付ける（決定的）。"""
    return re.sub(r'<a href="(https?://[^"]*)"((?: title="[^"]*")?)>', r'<a href="\1"\2 target="_blank" rel="noopener">', s)


def label(doc, key):
    return (doc["meta"].get("labels") or {}).get(key) or ART["label_defaults"][key]


def render_list(b, ind):
    tag = "ol" if b.get("ordered") else "ul"
    L = ["%s<%s>" % (ind, tag)]
    for it in b.get("items", []):
        if isinstance(it, dict):
            L.append("%s  <li>%s" % (ind, it.get("html", "")))
            if "list" in it:
                L += render_list(it["list"], ind + "    ")
            L.append("%s  </li>" % ind)
        else:
            L.append("%s  <li>%s</li>" % (ind, it))
    return L + ["%s</%s>" % (ind, tag)]


def toc_entries(doc):
    out = []
    for b in doc["blocks"]:
        if b["type"] == "heading" and b["level"] == 2 and b.get("id") and b.get("toc", True):
            out.append((b["id"], strip_tags(b["html"])))
        elif b["type"] == "glossary":
            out.append(("glossary", label(doc, "glossary")))
        elif b["type"] == "references":
            out.append(("references", label(doc, "references")))
    return out


def render_block(b, doc, partials, year):
    t = b["type"]
    if t == "heading":
        idattr = ' id="%s"' % b["id"] if b.get("id") else ""
        return ["<h%d%s>%s</h%d>" % (b["level"], idattr, b["html"], b["level"])]
    if t == "p":
        return ["<p>%s</p>" % b["html"]]
    if t == "note":
        return ['<p class="note">%s</p>' % b["html"]]
    if t == "list":
        return render_list(b, "")
    if t == "table":
        L = ["<table>"]
        if b.get("caption"):
            L.append("  <caption>%s</caption>" % b["caption"])
        L += ["  <thead>", "    <tr>"] + ['      <th scope="col">%s</th>' % c for c in b["columns"]] + ["    </tr>", "  </thead>", "  <tbody>"]
        for row in b["rows"]:
            L.append("    <tr>")
            for j, cell in enumerate(row):
                L.append('      <th scope="row">%s</th>' % cell if b.get("row_header") and j == 0 else "      <td>%s</td>" % cell)
            L.append("    </tr>")
        return L + ["  </tbody>", "</table>"]
    if t == "quote":
        L = ["<blockquote>"] + ["  <p>%s</p>" % p for p in b["paragraphs"]]
        if b.get("cite"):
            L.append("  <footer>%s</footer>" % b["cite"])
        return L + ["</blockquote>"]
    if t == "code":
        return ['<pre><code class="language-%s">%s</code></pre>' % (b["language"], htmllib.escape(b["code"], quote=False))]
    if t == "qa":
        L = ['<dl class="qa">']
        for qa in b["items"]:
            L += ["  <dt>%s</dt>" % qa["q"], "  <dd>%s</dd>" % qa["a"]]
        return L + ["</dl>"]
    if t == "image":
        img = '<img src="%s" alt="%s">' % (htmllib.escape(b["src"]), htmllib.escape(b["alt"]))
        if b.get("caption"):
            return ["<figure>", "  " + img, "  <figcaption>%s</figcaption>" % b["caption"], "</figure>"]
        return [img]
    if t == "toc":
        L = ['<nav class="toc">', "  <h2>%s</h2>" % label(doc, "toc"), "  <ol>"]
        L += ['    <li><a href="#%s">%s</a></li>' % (a, htmllib.escape(x, quote=False)) for a, x in toc_entries(doc)]
        return L + ["  </ol>", "</nav>"]
    if t == "glossary":
        L = ['<h2 id="glossary">%s</h2>' % label(doc, "glossary"), '<dl class="glossary">']
        for n, tm in enumerate(b["terms"], 1):
            L += ['  <dt id="term-%d">%s</dt>' % (n, tm["term"]), "  <dd>%s</dd>" % tm["desc"]]
        return L + ["</dl>"]
    if t == "references":
        L = ['<h2 id="references">%s</h2>' % label(doc, "references"), "<ol>"]
        for it in b["items"]:
            L.append("  <li%s>%s</li>" % (' id="%s"' % it["id"] if it.get("id") else "", it["html"]))
        return L + ["</ol>"]
    if t == "include":
        if b["name"] not in partials:
            raise ValueError("include %s: partials に %s.html が無い" % (b["bid"], b["name"]))
        h = partials[b["name"]].rstrip("\n").replace(YEAR_TOKEN, str(year))
        if "{{" in h:
            raise ValueError("include %s: 置換されないプレースホルダが残る" % b["name"])
        return ["<!-- include:%s -->" % b["name"], h, "<!-- /include:%s -->" % b["name"]]
    if t == "raw_html":
        return [b["html"]]
    raise ValueError("未対応の type: %s" % t)


SKIP = {"a", "h1", "h2", "h3", "h4", "h5", "h6", "code", "pre", "th", "caption", "dt", "nav"}
TAG_RX = re.compile(r"(<!--.*?-->|<[^>]+>)", re.S)


def link_terms(html, terms):
    """用語解説より前の本文で、用語の全出現を #term-N へのリンクにする（長い語を優先。見出し・コード・既存リンク・include は除く）。"""
    if not terms:
        return html
    names = sorted(((tm, i + 1) for i, t in enumerate(terms) for tm in {strip_tags(t["term"])} if len(tm) >= 2), key=lambda x: -len(x[0]))
    mp = {n.casefold(): i for n, i in names}
    pats = []
    for n, _ in names:
        p = re.escape(n)
        if re.match(r"\w", n[0], re.A):
            p = r"(?<![A-Za-z0-9])" + p
        if re.match(r"\w", n[-1], re.A):
            p += r"(?![A-Za-z0-9])"
        pats.append(p)
    rx = re.compile("|".join(pats), re.I)
    end = html.find('<h2 id="glossary">')
    head, tail = (html[:end], html[end:]) if end >= 0 else (html, "")
    out, depth, in_inc = [], {}, 0
    for tok in TAG_RX.split(head):
        if not tok:
            continue
        if tok.startswith("<!--"):
            in_inc += 1 if tok.startswith("<!-- include:") else (-1 if tok.startswith("<!-- /include:") else 0)
            out.append(tok)
        elif tok.startswith("<"):
            m = re.match(r"</?\s*([A-Za-z0-9]+)", tok)
            n = m.group(1).lower() if m else ""
            if n in SKIP and not tok.endswith("/>"):
                depth[n] = depth.get(n, 0) + (-1 if tok.startswith("</") else 1)
            out.append(tok)
        elif in_inc or any(v > 0 for v in depth.values()):
            out.append(tok)
        else:
            out.append(rx.sub(lambda m: '<a class="term" href="#term-%d">%s</a>' % (mp[m.group(0).casefold()], m.group(0)), tok))
    return "".join(out) + tail


PAGE_CSS = ("body{font-family:system-ui,sans-serif;line-height:1.7;max-width:46rem;margin:2rem auto;padding:0 1rem;color:#1f2328;background:#fff}"
            "table{border-collapse:collapse}th,td{border:1px solid #d0d7de;padding:.4rem .6rem;text-align:left}"
            ".note{font-size:.9em;color:#57606a;border-left:3px solid #d0d7de;padding-left:.8rem}"
            "pre{background:#f6f8fa;padding:.8rem;overflow:auto}a.term{text-decoration:underline dotted}")


def load_partials(article_path, doc):
    d = Path(article_path).resolve().parent / doc["meta"].get("partials_dir", "partials")
    return {p.stem: p.read_text(encoding="utf-8") for p in sorted(d.glob("*.html"))} if d.is_dir() else {}


def render_doc(doc, partials, year):
    probs = validate_article(doc)
    if probs:
        return None, probs
    try:
        body = []
        for b in doc["blocks"]:
            body += render_block(b, doc, partials, year)
    except ValueError as e:
        return None, [str(e)]
    html = ext_links("\n".join(body) + "\n")
    if doc["meta"].get("glossary_links", True):
        terms = next((b["terms"] for b in doc["blocks"] if b["type"] == "glossary"), [])
        html = link_terms(html, terms)
    if doc["meta"].get("template", "fragment") == "page":
        html = ('<!doctype html>\n<html lang="%s">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
                "<title>%s</title>\n<style>%s</style>\n</head>\n<body>\n<article>\n<h1>%s</h1>\n%s</article>\n</body>\n</html>\n") % (
            doc["meta"].get("lang", "ja"), htmllib.escape(doc["meta"]["title"]), PAGE_CSS, htmllib.escape(doc["meta"]["title"]), html)
    return html, final_checks(html)


def final_checks(html):
    out = []
    if EMOJI_RX.search(html):
        out.append("絵文字・記号アイコンを検出")
    ids = set(re.findall(r'\sid="([^"]+)"', html))
    for a in sorted(set(re.findall(r'href="#([^"]+)"', html))):
        if a not in ids:
            out.append("アンカー #%s の行き先が無い" % a)
    if "{{" in html:
        out.append("置換されないプレースホルダが残っている")
    return out


def normalize(html):
    s = re.sub(r"\s+", " ", html)
    s = re.sub(r"\s*(</?(?:div|p|ul|ol|li|table|thead|tbody|tr|th|td|caption|h[1-6]|blockquote|pre|nav|dl|dt|dd|figure|figcaption|footer|header|section|article)(?:\s[^>]*)?>)\s*", r"\1", s, flags=re.I)
    return s.strip()


# ------------------------------------------------------------ CLI

def opt(argv, name):
    if name in argv:
        i = argv.index(name)
        if i + 1 < len(argv):
            return argv[i + 1]
        raise SystemExit(2)
    return None


def fail(probs):
    for p in probs:
        print("NG:", p, file=sys.stderr)
    return 1


def main(argv):
    setup_stdio()
    cmds = ("check", "render", "verify", "compare", "init-ledger")
    if len(argv) < 3 or argv[1] not in cmds:
        print(__doc__)
        return 2
    cmd, path = argv[1], argv[2]
    if cmd == "compare":
        if len(argv) < 4:
            print(__doc__)
            return 2
        a, b = (normalize(Path(p).read_text(encoding="utf-8")) for p in (path, argv[3]))
        if a == b:
            print("一致（空白差を除く）")
            return 0
        i = next((k for k in range(min(len(a), len(b))) if a[k] != b[k]), min(len(a), len(b)))
        print("不一致（正規化後 %d 文字目）\n  A: %s\n  B: %s" % (i, a[max(0, i - 60):i + 80], b[max(0, i - 60):i + 80]))
        return 1
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    lp = ledger_path(path)
    led = json.loads(lp.read_text(encoding="utf-8")) if lp.is_file() else None
    probs = validate_article(doc)
    out_default = Path(path).resolve().parent / (doc.get("meta") or {}).get("output", "")
    if cmd == "init-ledger":
        if led is not None:
            return fail(["%s は既にある" % LED["file_name"]])
        if probs:
            return fail(probs)
        if out_default.is_file():
            return fail(["%s が既にある記事には init-ledger を使わない（台帳を作り直してゲートを避けられないように）" % out_default.name])
        write_json(lp, new_ledger(doc))
        print("作成 %s" % lp.name)
        return 0
    if cmd == "check":
        probs += validate_ledger(led, doc) if not probs else []
        if probs:
            return fail(probs)
        print("OK（raw_html %d 個）" % sum(1 for b in doc["blocks"] if b["type"] == "raw_html"))
        return 0
    y = opt(argv, "--year")
    year = int(y) if y else datetime.date.today().year
    if cmd == "verify" and not y and led:
        year = next((r["year"] for r in reversed(led.get("renders", [])) if r.get("year")), year)
    if cmd == "render":
        if probs:
            return fail(probs)
        gate = validate_ledger(led, doc)
        if gate:
            return fail(["台帳: " + g for g in gate] + ["全件を applied か理由つき rejected にしてから render する"])
    html, probs = render_doc(doc, load_partials(path, doc), year)
    if probs:
        return fail(probs)
    if cmd == "verify":
        target = Path(opt(argv, "--html") or out_default)
        cur = target.read_text(encoding="utf-8") if target.is_file() else None
        if cur == html:
            print("一致: %s は article.json から生成したものと同じ" % target.name)
            return 0
        return fail(["不一致: %s（手編集か、article.json 更新後の未再生成。差分は compare で確認）" % target.name])
    out = Path(opt(argv, "--out") or out_default)
    out.write_text(html, encoding="utf-8", newline="\n")
    if out.resolve() == out_default.resolve():
        raw = Path(path).read_bytes().replace(b"\r\n", b"\n")
        led.setdefault("renders", []).append({
            "at": now_iso(), "kind": "render", "year": year, "json_sha256": hashlib.sha256(raw).hexdigest(),
            "output": out.name, "block_hashes": block_hashes(doc),
            "fixes": [f["id"] for f in led.get("fixes", []) if f.get("status") in ("applied", "rejected")]})
        write_json(lp, led)
    print("生成 %s: %d 文字" % (out.name, len(html)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
