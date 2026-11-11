# 記事 HTML キット: HTML を JSON から作り、修正は台帳つきで反映する

[← README.md](../README.md)

記事の HTML を、構造化した JSON（`article.json`）を正本にして作るための手引きです。この文書だけで、仕組み・運用の流れ・他のプロジェクトへの入れ方が分かるように書いています。使う skill は `article-html-from-json` です。

## 1. 目的

AI に HTML を書かせ、修正のたびに HTML を直接直していると、次のことが起きがちです。

- 依頼した修正の一部が反映されないまま残る（どこまで直したか追えない）
- 同じ修正が二重にかかる、または前の修正が後の修正で消える
- 組織の定型文（免責や連絡先など）が、修正のついでに少しずつ書き換わる

このキットは、次の 3 点でそれを防ぎます。

- **正本は JSON**: HTML は JSON から変換器（`render_article.py`）が毎回同じ形で作る。HTML は直接直さない
- **指摘台帳**: 修正の依頼を `fix-ledger.json` に原文のまま記録し、どのブロックをどう直したかを残す
- **全件反映してから再生成**: 台帳に未反映の依頼が残っている間、変換器は HTML を作らない

## 2. 3 つのファイル

| ファイル | 役割 | 誰が書くか |
|---|---|---|
| `article.json` | 記事の正本。見出し・段落・表・コード・用語解説・参考文献などをブロックの配列で持つ。各ブロックに固定の `bid` を付ける | AI（依頼者の指示で） |
| `fix-ledger.json` | 指摘台帳。依頼の原文・状態（open / applied / rejected）・直したブロック・変更内容・作り直しの記録 | AI（依頼を受けるたび） |
| `partials/<名前>.html` | 組織の定型文など、記事をまたいで同じ文面を使う部品。`include` ブロックで逐語のまま差し込む | 組織の担当者 |

ブロックの種類と台帳の書式の正本は `.claude/skills/article-html-from-json/criteria/article-schema.json`、見本は同じ skill の `examples/` です。

## 3. 運用の流れ

```
最初の版:  原稿 → article.json → init-ledger → check → render → HTML
修正:      依頼を受ける → 台帳に原文で追記（open）→ JSON を直す → 台帳を applied
           （直さないなら rejected と理由）→ …依頼が一通り終わるまで繰り返す…
           → check → render（未反映が 1 件でもあれば止まる）→ HTML
```

- 依頼者は修正点を自由な言葉で伝えればよく、JSON を読む必要はありません。AI が台帳と JSON を管理します
- 変換器は次の時に HTML を作りません: 台帳が無い、未反映（open）がある、反映済みなのに直したブロックの記録が無い、台帳に書かれていない変更が JSON にある
- `verify` で、今の HTML が JSON から作ったものと同じかを確かめられます（手で直された HTML を見つける）

## 4. 何が保証され、何が保証されないか

| 保証されること | 保証されないこと |
|---|---|
| 同じ JSON・同じ部品・同じ年なら、同じバイト列の HTML ができる | 文章の正しさ・事実かどうか（別のレビューで点検する） |
| 台帳の依頼がすべて反映済みか理由つきで却下されるまで、HTML を作り直さない | 依頼者の原文を AI が正しく台帳に写したか（台帳を依頼者が読み返せる形で残す） |
| 部品（partials）の文面は逐語で入る（年号の置き換えだけが例外） | JSON 以外の原稿（Markdown など）との本文の一致（台帳の `source_sync` で記録するだけ） |
| HTML に許可外のタグ・絵文字・行き先の無いアンカーが入らない | 見た目の好み（CSS は `page` テンプレートの最小限だけ） |

## 5. 他のプロジェクトへ入れる

### 依頼して入れる（推奨）

1. 入れたいプロジェクトの直下に、このリポジトリを `.setup-automate/` という名前で clone し、`.gitignore` に登録します（手順の詳細は [setup-guide.md](setup-guide.md)）
2. `.setup-automate/` の中で Claude Code を起動し、「親ディレクトリに、HTML を JSON から作るキットを入れて」のように依頼します
3. 取り込む要素の選択で「記事 HTML キット」（由来台帳 `provenance.json` の `article-html-kit`）を選びます。次が対象に入ります
   - `.claude/skills/article-html-from-json/`（変換器・試験・見本を含む）
   - この文書（`docs/article-html-kit.md`）
   - 下の「そのまま貼れるルール」を、対象の `CLAUDE.md` に貼ったもの

### 手でコピーする

| コピーするもの | 用途 |
|---|---|
| `.claude/skills/article-html-from-json/` | skill 一式（SKILL.md・criteria・scripts・examples） |
| `docs/article-html-kit.md` | この文書 |

コピーしたら Claude Code を起動し直します（起動中に足した skill は読み込まれません）。依存は Python 3.8 以上だけです（標準ライブラリのみ）。試験は `python -X utf8 -B .claude/skills/article-html-from-json/scripts/test_render_article.py` です。組織固有の HTML の形（決まった class 名や定型の箱）が要る場合は、変換器を書き換えるより先に `partials/` と `raw_html` で足りるかを確かめてください。

## 6. そのまま貼れるルール

```markdown
## 記事の HTML を作る・直すとき

- 記事の HTML は article.json を正本にし、`article-html-from-json` skill の変換器で作る（手順の詳細は docs/article-html-kit.md）
- HTML を直接編集しない。直すのは article.json
- 修正の依頼は、受けた時点で fix-ledger.json に原文のまま記録する。依頼者が「以上」と示すまで HTML を作り直さない
- 全件を反映（applied）か理由つきで却下（rejected）にしてから render する。render が止まったら、台帳を事実どおりに直して通す（記録をごまかして通さない）
```

---

注: このキットは、記事を作ってから修正の依頼をまとめて受ける運用を想定しています。依頼が 1 件ずつすぐ反映されればよい場合も、同じ手順（台帳に 1 件追記して render）で使えます。
