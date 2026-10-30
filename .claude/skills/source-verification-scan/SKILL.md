---
name: source-verification-scan
description: "調査・レポート・記事の成果物に、非公開情報・裏取り不能な伝聞・実在しない参照先(捏造ナビゲーション)・未確認のフレーミング(位置付け)が混入していないかをゼロ・トレランスで検査する。research-deliverable-review / general-news-research / it-tech-news-research / review-blog 等、外部公開する調査系成果物の確定前に使う。Use when the user asks to 'ソース検証して', '非公開情報が混ざっていないか確認', '出典スキャン', 'source verification scan', '公開前チェック'. 内部限定の文書、品質全般の採点(research-deliverable-review を使う)、文章表現の推敲には使わない。"
disable-model-invocation: true
allowed-tools: Read Grep Glob WebFetch Agent
argument-hint: "<検査対象ファイルのパス(複数可)>"
metadata:
  provenance: author-preference
  version: "1.0"
---

# ソース検証スキャン(非公開情報・伝聞・捏造導線チェック)

## 目的

外部公開する調査・レポート・記事に、公開情報で裏付けられない記述が残っていないかを系統的に検査する。**「事実は正しいが、位置付け・フレーミングが未確認」というパターン**を含めて検出する。

## ゼロ・トレランス原則

公開情報にない情報は、フレーミング・位置付け・推測・要約も含めて一切の混入を許さない。「未確認」「要追加確認」等の注記付きでも保持不可。出典で literal 確認できないものは削除、または裏付けの取れる公開出典への置換のみ許容する。

## 前提条件

- Python 3 が実行できること。本 skill は同一リポジトリの `.claude/skills/_shared/scripts/`(`list_review_records.py` / `append_review_record.py`)と `.claude/skills/_shared/review-record.schema.json` に依存する。他リポジトリへ移す場合は `_shared` も一緒に配置する。`_shared` が無い環境では、過去記録の検索と永続化を省き、その旨を最終報告に書く(検査そのものは `criteria/categories.json` だけで行える)
- 検査対象はローカルのファイル。URL の裏取りには WebFetch を使う

## 禁止対象カテゴリ

観点定義 (SoT) = `.claude/skills/source-verification-scan/criteria/categories.json`。7カテゴリ(A-G)の検査方法・許容出典・出力形式を保持する(本文へ prose 重複記載しない)。dispatch 先エージェントには対象ファイルのパスと本 JSON のパスのみ渡す。

## launder禁止の原則(取得手段が変わっても不変)

非公開ソースが禁止されている理由は「取得手段」ではなく「ソースが非公開であること」自体にある。WebFetchで直接取得できないからと別の技術的手段(スクレイピング・HTML dump等)で取得しても、非公開ソースを「引用可能な公開ソース」に変えることはできない。公開一次ソースへのアクセスが技術的に失敗した場合のみ、別の取得手段を試みてよい(非公開ソースへの適用は不可)。

## スキャン手順(別エージェント実行)

**過去レビュー記録の参照**: スキャン起動前に以下を実行し、同一対象の過去レビュー記録（このskillに限らず research-deliverable-review 等の記録も含む）を検索する。ヒットした場合は該当ファイルを Read し、前回の BLOCKER/指摘内容を検査エージェントへのプロンプトに含める。

```bash
python .claude/skills/_shared/scripts/list_review_records.py --target "<対象ファイル名またはタイトルの一部>"
```

呼び出し元セッションの意図・執筆過程は渡さず、対象ファイルのパスと `criteria/categories.json` のパスのみを渡して別エージェントに検査させる(自己レビュー禁止)。出力形式(hit単位のフォーマット・converged BLOCKER要件)は同 JSON の `output_format` を参照。BLOCKERが0件になるまで公開しない。

## 使用例

- ユーザー: 「この記事 `reports/xxx.md` を公開前にソース検証して」 → 過去記録を検索 → 対象パスと `categories.json` のパスだけを別エージェントに渡して検査 → hit が出たカテゴリ(例: 出典 URL が実在しない)を行ごと削除または公開出典へ置換 → 再検査して BLOCKER 0 件を確認 → 記録を永続化
- 判定が割れる例: 事実は公開情報で確認できるが「社内で採用が進んでいる」と位置付けた一文 → 位置付けに公開出典が無いので hit とし、削除か中立表現へ置換する

## 失敗時の対処

- 別エージェントを起動できない・出力に JSON が無い: 自分で代行せず、起動条件を直して再実行する(自己レビュー禁止)
- WebFetch が失敗した出典: 到達不能を hit の根拠にせず、別の公開一次情報で再確認する。取れなければ「裏付け不能」として削除対象にする
- `list_review_records.py` が該当なし: 過去記録なしとして進めてよい
- `append_review_record.py` が非ゼロ終了: 標準エラーの内容(必須フィールド欠落等)に従って JSON を直し再実行する

## 永続化

検査エージェントには `output_format.persisted_record` が指す review-record/v1 JSON（`skill: "source-verification-scan"`, `verdict`: BLOCKER 0件なら `"PASS"`、1件以上残るなら `"FAIL"`, `criteria` にカテゴリA-Gごとのhit有無を記録）も出力させる。受け取ったJSONを一時ファイルに保存し、以下を実行して永続化する:

```bash
python .claude/skills/_shared/scripts/append_review_record.py <一時JSONファイルのパス>
```

このスクリプトが成功するまで公開判断（BLOCKER 0件の確定報告）を完了として扱わない。検証エラー時はエラー内容に従いJSONを修正して再実行する（強制の限界: プロンプト指示による実行そのものは確率的だが、スクリプト自体のスキーマ検証は決定的）。

## 最終報告の形式(ユーザーへ返す内容)

検査エージェントの出力を受けて、呼び出し元は次の順で報告する。LLM が判定した内容と、スクリプトが出力した内容(記録の保存結果)を区別して書く。

1. 判定: PASS(BLOCKER 0 件)または FAIL(BLOCKER 1 件以上)
2. BLOCKER 一覧: hit ごとに「行番号 + 原文の引用 / カテゴリ A-G / 推奨処置」(`categories.json` の `per_hit` のとおり)。0 件なら「なし」
3. 実施した処置: 行ごと削除・公開出典への置換・表現の中立化のどれを何件行ったか
4. 再検査の結果: 処置後に BLOCKER 0 件を確認したか
5. 記録の保存先: `append_review_record.py` が成功したときの保存先パス(未実行・失敗なら理由)

対応アクションの選び方: 同内容が公開一次情報で確認できれば置換、確認できなければ削除、自組織の内部情報なら中立化する。

## 対応アクション

- **行ごと削除**: 裏付けが取れないものはそのまま消す(訂正注記を残して保持しない)
- **公開出典への置換**: 同内容が公開一次情報で確認できる場合はURLに置換
- **表現の中立化**: 自組織の内部情報は削除し、業界一般化した表現に置き換える

---

*作成: 2026-09-01(非公開情報スキャナの設計から汎用パターンを抽出)。更新履歴: 1.0 = 初版。以降の変更は version を上げた時点でここに追記する。*
