---
name: workflow-coverage-and-structure
description: このリポジトリの「テストカバレッジ」「プロジェクト構成」に相当する質問に即答する。プロンプトライブラリのため実コードのカバレッジ%は測定せず、代わりに workflows/ 配下の各ファイルが category README にドキュメント化されているか（drift 検出）を機械検査する。Use when user asks "テストカバレッジは?", "test coverage", "プロジェクト構成は?", "project structure", "workflows の網羅性", or after adding a new workflow prompt file / category. Not for measuring real code coverage of an application (this repo has none), reviewing the quality of a skill (use review-skill), or auditing the skill system as a whole (use skills-audit).
argument-hint: "<action: report|check> (省略時は report)"
allowed-tools: Read Bash
metadata:
  provenance: repo-specific
  version: "1.1"
---

# ワークフロー ドキュメント網羅性・構成 Skill

「テストカバレッジは?」「プロジェクト構成は?」に相当する質問に既存の監査結果から即答する。このリポジトリはプロンプトライブラリであり実行コードがほぼ存在しないため、コードの line/branch coverage は測定対象にならない。代わりに、このリポジトリの実質的な品質指標である「workflows/ 配下の各ファイルが対応する category README.md にドキュメント化されているか」を機械検査する。

## なぜこの指標か

各 `workflows/<category>/README.md` は「プロンプト | レビュー | 用途」形式の表で作成プロンプトとレビュープロンプトの対応関係を人手で curate している。1つの `review-*.md` が複数の作成プロンプトをまとめて担当するケースがあり（例: `review-ops.md` が `server/automation.md`・`server/init.md`・`server/windows-standard.md` の3ファイルを担当）、ファイル名の類推だけでは正確な対応関係を機械判定できない。このため「対応する review が存在するか」ではなく「ファイルが README に記載されているか」という、より単純で誤検知の少ない指標を使う——これは「新規ファイルを追加したが README への追記を忘れた」というドキュメント drift を検出する。

## 適用シナリオ

| シナリオ | アクション |
|---------|-----------|
| user が「テストカバレッジは?」「網羅性は?」と聞く | `bash .claude/skills/workflow-coverage-and-structure/scripts/workflow-doc-coverage-check.sh --report` を実行し、結果をそのまま報告 |
| user が「プロジェクト構成は?」と聞く | `workflows/README.md`（category 一覧）+ 各 `workflows/<category>/README.md`（ファイル別詳細）+ ルート `README.md` を Read して報告 |
| 新規ワークフローファイル追加後 | `bash .claude/skills/workflow-coverage-and-structure/scripts/workflow-doc-coverage-check.sh` で該当 category README への追記漏れがないか確認 |
| 新規 category（`workflows/<name>/`）追加後 | 同上 + `workflows/README.md` の一覧表への追記漏れがないか確認（本 check が両方を検出する） |

## コマンド

```bash
# 現状レポート（ファイル数・review 数・skill 数・gap 件数・exit 常に 0）
bash .claude/skills/workflow-coverage-and-structure/scripts/workflow-doc-coverage-check.sh --report

# drift check（未記載ファイル/category があれば FAIL exit 1）
bash .claude/skills/workflow-coverage-and-structure/scripts/workflow-doc-coverage-check.sh
```

## 前提条件

- `bash`、`git`、`find`、`grep` が使えること（Windows では Git Bash）。
- git リポジトリ内で、`workflows/<category>/README.md` と `.claude/skills/` が存在すること。スクリプトはこのリポジトリ構成を前提にしており、他のリポジトリで使う場合はスクリプト内のパス（`workflows/`、`.claude/skills/`）を直す必要がある。

## 実行方針

- 読み取り専用・非破壊。実行前の確認は不要。
- `examples/` 配下（worked-example 集）は個別ファイルへのリンクを要求しない（README ではディレクトリ単位でリンクされる設計のため対象外）。
- 質問への回答は「直近実行結果が古い（または存在しない）なら再実行してから答える」— 常に鮮度を担保する。
- 根拠の示し方: 報告にはスクリプトの出力（PASS/FAIL と未記載ファイルのパス）をそのまま引用する。スクリプトの出力と、自分が読んだ README から推測した内容は区別して書く。
- `--report` の「category README 未記載ファイル数」は、未記載ファイルのほかに「README.md 自体が存在しない category」「workflows/README.md に未記載の category」の行も 1 件ずつ数える。件数と実際の未記載ファイル数が食い違って見えたら、無引数の check の出力で内訳を確認する。

## 報告の形式

| 質問 | 報告に含める項目 |
|---|---|
| テストカバレッジ / 網羅性 | 「実コードのカバレッジは測定対象外」の一文、`--report` の 4 件数、drift check の PASS/FAIL、FAIL なら未記載ファイルの一覧と対応（README への追記） |
| プロジェクト構成 | category ごとの 1 行説明（`workflows/README.md` の一覧表に基づく）、ルート `README.md` からの補足。コードは載せない |

## 使用例

- 「テストカバレッジは?」→ `--report` を実行 → 「このリポジトリはプロンプトライブラリなので line/branch カバレッジは対象外です。代わりに workflows の README 記載率を見ています: ファイル N 件、review M 件、skill K 件、未記載 0 件」と出力値を引用して回答。
- 「新しい workflow を追加した」→ 無引数で check → FAIL で `workflows/<category>/foo.md` が出たら、その category の README.md の表に行を追加して再実行し、PASS を確認する。

## エラー時の対処

| 出力・状況 | 対処 |
|---|---|
| `FAIL: not in a git repo` | git リポジトリの外で実行している。リポジトリ内へ移動して再実行する。リポジトリ自体が無いなら、この skill は使えないとユーザーに伝える |
| `bash` が見つからない / `workflows/` が無い | 環境（Git Bash）またはリポジトリ構成の前提が満たされていない。推測で数値を答えず、前提不足を報告する |
| `README.md 自体が存在しない` の行 | その category に README.md を作成する必要がある。作成するかはユーザーに確認する |
| `workflows/README.md に未記載の category` の行 | `workflows/README.md` の一覧表に category を追記する |
| FAIL で未記載ファイルが出た | 該当 category の README.md の表に追記して再実行。意図的に載せないファイルなら、ディレクトリ単位のリンクで解消するか、その旨をユーザーに確認する |

## 関連ファイル

- `.claude/skills/workflow-coverage-and-structure/scripts/workflow-doc-coverage-check.sh` / `.test.sh`
- `workflows/README.md`（category 一覧・プロジェクト構成の一次回答先）
- 各 `workflows/<category>/README.md`（ファイル別のプロンプト/レビュー対応表）

## 既知の false-positive モード

新規ワークフロー .md ファイルが「作成プロンプトではない」性質のもの（例: CHANGELOG・変更履歴等）であっても、category README にリンクされていなければ「未記載」として検出される。これは意図的なトレードオフ——「workflows/ 配下の .md は何らかの形で discoverable であるべき」という設計方針であり、該当ファイルは README にディレクトリ単位または個別にリンクすることで解消する。
