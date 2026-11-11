---
name: article-html-from-json
description: "記事の HTML を、構造化した article.json を正本にして決定的に生成する。HTML は直接直さず、修正の依頼は指摘台帳（fix-ledger.json）に原文で記録して JSON に反映し、全件を反映してから再生成する。変換器・JSON の形・台帳の書式・試験を同梱（Python 標準ライブラリのみ）。Use when the user asks 'HTML を JSON から作って', '記事の HTML を JSON で管理したい', '修正指示を台帳に記録して反映して', 'HTML を直接直さずに直して', '指摘を全部反映してから HTML を作り直して', '記事 HTML の正本を JSON にして'. 使わない場面: スライドの作成（slide-composition-planner など）、ブログ記事の採点（review-blog）、HTML 以外の文書形式への変換。"
allowed-tools: Read Write Edit Glob Grep Bash
argument-hint: "<article.json の絶対パス（無ければ作る記事フォルダ）> [render | check | verify]"
metadata:
  provenance: domain-prompt
  version: "1.0.0"
---

# 記事 HTML を JSON から作る（指摘台帳つき）

**最重要: HTML を直接編集しない。** 直すのは常に `article.json` で、HTML は `scripts/render_article.py` が作る。依頼された修正は、受けた時点で `fix-ledger.json` に依頼者の原文のまま記録し、依頼者が「指示は以上」と示すまで HTML を作り直さない。

ブロックの種類・インライン HTML の許可タグ・台帳の項目・再生成を止める条件の正本は `criteria/article-schema.json`。この SKILL.md に同じ内容を重ねて書かない。形の見本は `examples/`（`article.example.json`・`fix-ledger.json`・`partials/`）。

## 前提

- Python 3.8 以上（標準ライブラリだけで動く）。Windows では `python -X utf8` で実行する（日本語の出力で落ちないため）。`-B` を付けると `__pycache__` を作らない。
- 記事フォルダの構成: `article.json`（正本）・`fix-ledger.json`（台帳）・`partials/<名前>.html`（組織の定型文など、逐語で差し込む部品。任意）・出力 HTML（`meta.output`）。
- コマンドの書き方（以下 `R` と略す）: `python -X utf8 -B .claude/skills/article-html-from-json/scripts/render_article.py`

## 手順

### A. 新しい記事を作る

1. 原稿（Markdown など）から `article.json` を書く。形は `criteria/article-schema.json` と `examples/article.example.json` に合わせる。全ブロックに固定の `bid` を付ける。組織や案件で決まった定型文は本文に書き写さず、`partials/` に置いて `include` ブロックで差し込む。
2. `R init-ledger <article.json>` で台帳を作る（最初の記録は `draft`。最初の render までは執筆中として、変更と台帳の照合をしない）。
3. `R check <article.json>` が終了コード 0 になるまで JSON を直す。
4. `R render <article.json>` で `meta.output` に HTML を書く。終了コード 0 と「生成 …」の行を確認する。
5. 必要なら HTML をブラウザで開いて見た目を確認する。気になる点も HTML ではなく JSON を直す。

### B. 修正の依頼を受けた（本体）

1. 依頼を受けたら、`fix-ledger.json` の `fixes` に追記する: `id`（`F-001` から連番）・`received`（日付）・`request`（**原文のまま**。要約・言い換えをしない。1 つの発言に複数の依頼があれば分ける）・`status: "open"`。
2. `article.json` を直す。同じ種類の箇所が他にもあれば全部直す。
3. 台帳を更新する: 直したら `status: "applied"`・`targets`（直したブロックの bid を全部）・`change`（何をどう変えたか）・`applied`（日付）・`source_sync`（JSON 以外に同じ本文を持つ原稿があり、そちらにも反映したら `done`、無ければ `not-needed`）。直さないと決めたら `status: "rejected"` と `reason`。
4. 依頼者が「指示は以上」と示すまで 1〜3 を繰り返す。その間は render しない。
5. `R check <article.json>` → `R render <article.json>`。
6. 依頼者に、反映した指摘の id と、出力 HTML のパスを伝える。

render は次の時に止まる（理由は stderr）。止まったら JSON か台帳の記録を正しく直す。台帳の記録を事実と違う内容に書き換えて通すことはしない。

- 台帳が無い / `open` が残る / `applied` に必要な項目が無い / `rejected` に理由が無い
- `targets` の bid が存在しない / applied にしたのに targets のブロックが変わっていない
- 台帳に書かれていない変更がある（前回の記録から変わったブロックが、どの指摘の targets にも入っていない）

### C. 手で直された疑いがある・作り直しを忘れていないか確かめる

- `R verify <article.json>`: JSON から作り直した結果と、今の HTML がバイト単位で同じか。違えば終了コード 1。手で直した HTML の変更は、内容を article.json と台帳に移してから render し直す。年は台帳の最後の記録の年を使う（`--year` で上書き可）。
- `R compare <a.html> <b.html>`: 空白の差を無視して比べる（既存の HTML を JSON に移した時の確認など）。

### D. 既に HTML だけがある記事を移す

変換器は HTML の取り込みを持たない（HTML の書き方が記事ごとに違うため）。HTML を読み、同じ内容の `article.json` を手で書く。`R render <article.json> --out <別名>.html` で試し出力（台帳に記録しない）し、`R compare <元>.html <別名>.html` で差を確かめる。差が意図どおりなら、元の HTML が無い状態で `init-ledger` を作るか、`fix-ledger.json` を `examples/fix-ledger.json` の形で作り、最初の記録の `kind` を `baseline` にする（以後の JSON の変更はすべて台帳の指摘が要る）。

## 出力（render の HTML）

- `meta.template` が `fragment`（既定）なら本文だけ、`page` なら `<!doctype html>` から始まる 1 ページ。
- 表は `<table><thead>`、コードは `<pre><code class="language-…">`、Q&A は `<dl class="qa">`、用語解説は `<dl class="glossary">`、注記は `<p class="note">`。外部リンクには `target="_blank" rel="noopener"` を付ける。
- 用語解説があると、それより前の本文で用語の全出現を `#term-N` へのリンクにする（見出し・コード・既存リンク・表の見出しセル・`include` の中は除く）。`meta.glossary_links: false` で止められる。
- `include` の HTML は逐語で差し込む。例外は `{{YEAR}}` を生成時の西暦にすることだけ。
- 同じ JSON・同じ partials・同じ年なら、出力は同じバイト列。

## 試験

`python -X utf8 -B .claude/skills/article-html-from-json/scripts/test_render_article.py`（各ブロックの出力・目次・用語リンク・検査・台帳ゲート・verify・compare・同梱の見本）。

## エラーと対処

| 症状 | 原因 | 対処 |
|---|---|---|
| `fix-ledger.json が無い` | 台帳を作っていない | 新規なら `init-ledger`。出力 HTML が既にある記事では init-ledger は拒否される（台帳を作り直してゲートを避けられないように）。台帳を失った時は依頼者に確認し、D の手順で作り直す |
| `許可外のタグ` / `許可外の属性` | インライン HTML に許可外の要素 | 対応するブロック type を使う（表なら `table` など）。どうしても表せない要素だけ `raw_html` |
| `台帳の指摘に紐づかない変更がある` | 台帳に書かずに JSON を直した | その変更を指摘として台帳に記録し、targets に入れる |
| `applied だが targets のブロックが…変わっていない` | targets の bid の書き間違い、または直し忘れ | 実際に直したブロックの bid を書く |
| `include …: partials に … が無い` | 部品ファイルが無い | `partials/<名前>.html` を置く（`meta.partials_dir` で場所を変えられる） |
| `UnicodeEncodeError` | Windows で `-X utf8` を付けていない | `python -X utf8` で実行する |

## 例

- 「この記事の HTML を JSON で管理したい」→ D の手順で `article.json` と台帳を作り、試し出力と compare で差を報告する。
- 「表の 2 行目の数字を直して。あと見出しを短く」→ 台帳に 2 件（原文のまま）追記 → JSON を直す → applied → 依頼者の「以上です」を待って render。
- 「HTML の誤字だけ直接直しておいて」→ HTML は直さず、同じ手順で JSON と台帳に反映して render する旨を伝えて進める。

## 制約

- 変換器が検査するのは形（タグ・台帳・アンカー・絵文字）だけで、文章の正しさ・事実かどうかは検査しない。内容の点検は別のレビュー（例: review-blog）で行う。
- 本文の文言を JSON 以外の原稿（Markdown など）にも持つ場合、両方を同じに保つのは書く側の責任（台帳の `source_sync` で記録する）。
- 他プロジェクトでの使い方・CLAUDE.md へ貼るルールは `docs/article-html-kit.md`。
