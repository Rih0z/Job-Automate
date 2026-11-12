---
name: source-verification-scan
description: "調査・レポート・記事の成果物に、非公開情報・裏取り不能な伝聞・実在しない参照先(捏造ナビゲーション)・未確認のフレーミング(位置付け)が混入していないかをゼロ・トレランスで検査し、PASS/FAIL の判定と hit(行番号・原文の引用・カテゴリ・推奨処置)の一覧を返して、結果を review-record として保存する。research-deliverable-review / general-news-research / it-tech-news-research / review-blog 等、外部公開する調査系成果物の確定前に使う。Use when the user asks to 'ソース検証して', '非公開情報が混ざっていないか確認', '出典スキャン', 'source verification scan', '公開前チェック'. 内部限定の文書、品質全般の採点(research-deliverable-review を使う)、文章表現の推敲には使わない。"
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, WebFetch, Agent, Write, Bash(python .claude/skills/_shared/scripts/list_review_records.py:*), Bash(python .claude/skills/_shared/scripts/append_review_record.py:*), Bash(python3 .claude/skills/_shared/scripts/list_review_records.py:*), Bash(python3 .claude/skills/_shared/scripts/append_review_record.py:*)
argument-hint: "[検査対象ファイルのパス(複数可)]"
metadata:
  provenance: author-preference
  version: "1.1"
---

# ソース検証スキャン(非公開情報・伝聞・捏造導線チェック)

## 目的

外部公開する調査・レポート・記事に、公開情報で裏付けられない記述が残っていないかを系統的に検査する。**「事実は正しいが、位置付け・フレーミングが未確認」というパターン**を含めて検出する。

## ゼロ・トレランス原則

公開情報にない情報は、フレーミング・位置付け・推測・要約も含めて一切の混入を許さない。「未確認」「要追加確認」等の注記付きでも保持不可。出典で literal 確認できないものは削除、または裏付けの取れる公開出典への置換のみ許容する。

## 前提条件

- Python 3 が実行できること。本 skill は同一リポジトリの `.claude/skills/_shared/scripts/`(`list_review_records.py` / `append_review_record.py`)と `.claude/skills/_shared/review-record.schema.json` に依存する。他リポジトリへ移す場合は `_shared` も一緒に配置する。`_shared` が無い環境では、過去記録の検索と永続化を省き、その旨を最終報告に書く(検査そのものは `criteria/categories.json` だけで行える)
- 検査対象はローカルのファイル。URL の裏取りには WebFetch を使う
- コマンド例の `python` は Python 3 を指す。`python` が無く `python3` だけがある環境(macOS の標準など)では `python3` に置き換えて実行する。2 つのスクリプトの実行(Bash)と一時 JSON の保存(Write)は `allowed-tools` で事前に許可している

## 禁止対象カテゴリ

観点定義 (SoT) = `.claude/skills/source-verification-scan/criteria/categories.json`。7カテゴリ(A-G)の検査方法・許容出典・出力形式を保持する(本文へ prose 重複記載しない)。dispatch 先エージェントには対象ファイルのパスと本 JSON のパスのみ渡す。

## launder禁止の原則(取得手段が変わっても不変)

非公開ソースが禁止されている理由は「取得手段」ではなく「ソースが非公開であること」自体にある。WebFetchで直接取得できないからと別の技術的手段(スクレイピング・HTML dump等)で取得しても、非公開ソースを「引用可能な公開ソース」に変えることはできない。公開一次ソースへのアクセスが技術的に失敗した場合のみ、別の取得手段を試みてよい(非公開ソースへの適用は不可)。

## スキャン手順(別エージェント実行)

コマンドはリポジトリ直下をカレントディレクトリにして実行する。

1. 過去記録を検索する: 同一対象の過去レビュー記録(このskillに限らず research-deliverable-review 等の記録も含む)を検索する。ヒットした場合は該当ファイルを Read し、前回の BLOCKER と指摘を控える。

   ```bash
   python .claude/skills/_shared/scripts/list_review_records.py --target "<対象ファイル名またはタイトルの一部>"
   ```

2. 検査を別エージェントに任せる: 対象ファイルのパスと `criteria/categories.json` のパスだけを渡す(自己レビュー禁止)。呼び出し元セッションの意図・執筆過程は渡さない。例外は 1 で控えた前回の BLOCKER と指摘で、これだけはプロンプトに含めてよい。検査エージェントは読むだけで、対象ファイルを作成・変更・削除しない(書き込み系ツールを持たない `readonly-reviewer` があればそれで起動する)。出力形式は同 JSON の `output_format` に従わせる。
3. 判定を読む: BLOCKER は、`per_hit` の判定が「非公開NG」になった hit を指す(`output_format.blocker_definition`)。BLOCKER が 0 件なら 6 へ進む。
4. 処置する: 下の「対応アクション」で、BLOCKER ごとに削除、公開出典への置換、表現の中立化のどれかを行う。
5. 再検査する: 処置後のファイルで 2 と 3 をやり直す。処置と再検査を 3 回繰り返しても BLOCKER が残る場合は、公開せず、残った hit の一覧を最終報告に書いて止める。
6. 記録を残して報告する: 下の「永続化」で記録を保存し、「最終報告の形式」で報告する。BLOCKER が 0 件になるまで公開しない。

## 使用例

- ユーザー: 「この記事 `reports/xxx.md` を公開前にソース検証して」 → 過去記録を検索 → 対象パスと `categories.json` のパスだけを別エージェントに渡して検査 → hit が出たカテゴリ(例: 出典 URL が実在しない)を行ごと削除または公開出典へ置換 → 再検査して BLOCKER 0 件を確認 → 記録を永続化
- 判定が割れる例: 事実は公開情報で確認できるが「社内で採用が進んでいる」と位置付けた一文 → 位置付けに公開出典が無いので hit とし、削除か中立表現へ置換する

## 失敗時の対処

- 別エージェントを起動できない・出力に JSON が無い: 自分で代行せず、起動条件を直して再実行する(自己レビュー禁止)
- WebFetch が失敗した出典: 到達不能を hit の根拠にせず、別の公開一次情報で再確認する。取れなければ「裏付け不能」として削除対象にする
- `list_review_records.py` が該当なし: 過去記録なしとして進めてよい
- `append_review_record.py` が非ゼロ終了: 標準エラーの内容(必須フィールド欠落等)に従って JSON を直し再実行する

## 永続化

検査エージェントには `output_format.persisted_record` が指す review-record/v1 JSON（`skill: "source-verification-scan"`, `verdict`: BLOCKER 0件なら `"PASS"`、1件以上残るなら `"FAIL"`, `criteria` にカテゴリA-Gごとのhit有無を記録）も出力させる。受け取ったJSONを `.tmp/` 配下の一時ファイルに UTF-8 で保存し、以下を実行して永続化する:

```bash
python .claude/skills/_shared/scripts/append_review_record.py <一時JSONファイルのパス>
```

このスクリプトが成功するまで公開判断（BLOCKER 0件の確定報告）を完了として扱わない。検証エラー時はエラー内容に従いJSONを修正して再実行する（強制の限界: プロンプト指示による実行そのものは確率的だが、スクリプト自体のスキーマ検証は決定的）。

## 対応アクション

- **行ごと削除**: 裏付けが取れないものはそのまま消す(訂正注記を残して保持しない)
- **公開出典への置換**: 同内容が公開一次情報で確認できる場合はURLに置換
- **表現の中立化**: 自組織の内部情報は削除し、業界一般化した表現に置き換える

## 最終報告の形式(ユーザーへ返す内容)

検査エージェントの出力を受けて、呼び出し元は次の順で報告する。LLM が判定した内容と、スクリプトが出力した内容(記録の保存結果)を区別して書く。次の 5 項目以外(執筆の意図、BLOCKER でない所感、検査の経過の逐一)は書かない。

1. 判定: PASS(BLOCKER 0 件)または FAIL(BLOCKER 1 件以上)
2. BLOCKER 一覧: hit ごとに「行番号 + 原文の引用 / カテゴリ A-G / 推奨処置」(`categories.json` の `per_hit` のとおり)。0 件なら「なし」
3. 実施した処置: 行ごと削除・公開出典への置換・表現の中立化のどれを何件行ったか
4. 再検査の結果: 処置後に BLOCKER 0 件を確認したか
5. 記録の保存先: `append_review_record.py` が成功したときの保存先パス(未実行・失敗なら理由)

対応アクションの選び方: 同内容が公開一次情報で確認できれば置換、確認できなければ削除、自組織の内部情報なら中立化する。

---

*作成: 2026-09-01(非公開情報スキャナの設計から汎用パターンを抽出)。更新履歴: 1.0 = 初版。1.1 = `criteria/categories.json` のカテゴリ C（噂、伝聞、匿名 SNS 投稿）、D（一次に届かない二次解説だけの情報）、F（原文で確かめていない数値、日付、引用と、実在しない参照先）、G（位置付けや分類が公開情報で確かめられない記述）の検査方法に、報道に帰属させた因果の文の確認、転載ページの署名と同じ原データの再報道、要約や抽出ツールの出力を根拠にしないこと、不在の主張の探索範囲、範囲から点への言い換え、データ系列の題名の確認を加えた。前提条件に python の読み替えと事前許可のツールを書き、再検査の上限(3 回)と検査エージェントの読み取り専用を明記し、対応アクションの節を最終報告の前に移した。BLOCKER の定義を `categories.json` に置き、スキャン手順を番号付きの 6 段階にし、description に成果物、最終報告に書かないものを書いた。argument-hint の山括弧を角括弧に変えた。以降の変更は version を上げた時点でここに追記する。*
