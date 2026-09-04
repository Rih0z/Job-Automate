---
name: workflow-coverage-and-structure
description: このリポジトリの「テストカバレッジ」「プロジェクト構成」に相当する質問に即答する。プロンプトライブラリのため実コードのカバレッジ%は測定せず、代わりに workflows/ 配下の各ファイルが category README にドキュメント化されているか（drift 検出）を機械検査する。Use when user asks "テストカバレッジは?", "test coverage", "プロジェクト構成は?", "project structure", "workflows の網羅性", or after adding a new workflow prompt file / category.
argument-hint: "<action: report|check> (省略時は report)"
allowed-tools: Read Bash
metadata:
  provenance: repo-specific
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

## 実行方針

- 読み取り専用・非破壊。実行前の確認は不要。
- `examples/` 配下（worked-example 集）は個別ファイルへのリンクを要求しない（README ではディレクトリ単位でリンクされる設計のため対象外）。
- 質問への回答は「直近実行結果が古い（または存在しない）なら再実行してから答える」— 常に鮮度を担保する。

## 関連ファイル

- `.claude/skills/workflow-coverage-and-structure/scripts/workflow-doc-coverage-check.sh` / `.test.sh`
- `workflows/README.md`（category 一覧・プロジェクト構成の一次回答先）
- 各 `workflows/<category>/README.md`（ファイル別のプロンプト/レビュー対応表）

## 既知の false-positive モード

新規ワークフロー .md ファイルが「作成プロンプトではない」性質のもの（例: CHANGELOG・変更履歴等）であっても、category README にリンクされていなければ「未記載」として検出される。これは意図的なトレードオフ——「workflows/ 配下の .md は何らかの形で discoverable であるべき」という設計方針であり、該当ファイルは README にディレクトリ単位または個別にリンクすることで解消する。
