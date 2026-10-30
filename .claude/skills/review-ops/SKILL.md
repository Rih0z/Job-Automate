---
name: review-ops
description: |
  運用スクリプト・サーバー初期設定・自動化構成・標準化手順 (server-init / server-automation /
  server-windows-standard skill、または workflows/ops-management/server/*.md 系プロンプトで生成された成果物) を、セキュリティ・冪等性/再現性・
  エラーハンドリング/ロバスト性・運用性/保守性・パフォーマンス/スケーラビリティ の5軸・100点満点で
  独立エージェントに客観評価させる。現在のセッションでは直接採点せず、別エージェントへ dispatch する。
  Trigger phrases: '運用スクリプトをレビューして', 'サーバー設定を評価して', 'review-ops',
  '運用スクリプト 品質レビュー', 'init.md/automation.md/windows-standard.md の成果物レビュー'.
  Do not use for: 運用スクリプトを新規に作る・直す (server-init / server-automation /
  server-windows-standard)、直近の変更差分のレビュー (review-changes)、アプリ実装の総合評価 (review-implementation)。
disable-model-invocation: true
allowed-tools: Read Glob Grep Agent
argument-hint: "[レビュー対象スクリプト/設定ファイルのパス]"
metadata:
  provenance: domain-prompt
  version: "1.1"
---

# 運用スクリプト・サーバー設定 品質レビュー（エージェント分離実行）

> **このスキルは別エージェントを起動してレビューを行う。現在のセッションでは直接レビューしない。**
> 実装コンテキスト（思考過程・設計判断・会話履歴）をレビューエージェントに渡さないことで客観性を確保する。

対象: $ARGUMENTS

> **対象**: `workflows/ops-management/server/*.md` プロンプト (`server-init`, `server-automation`, `server-windows-standard` skill)
> で生成されたサーバー運用スクリプト・初期設定・自動化構成・標準化手順。
> **目的**: 「セキュリティ」「冪等性・再現性」「エラーハンドリング・ロバスト性」「運用性・保守性」
> 「パフォーマンス・スケーラビリティ」の5軸でサーバー運用成果物を100点満点で評価する。

## 前提と環境依存

- この repo 固有のパス: `workflows/ops-management/`、`.claude/skills/_shared/review-rubrics.yaml`、`.claude/agents/readonly-reviewer.md`、`server-*` skill。無い環境では、rubrics は下記ステップ3 の代替表、エージェントは `general-purpose` で代替し、SKILL.md と `references/` だけで動かす。
- 必要なツール: Read / Glob / Grep（収集）、Agent（レビュー起動）。対象ファイルの編集・スクリプトの実行はしない。
- 観点は Linux（bash）の例が中心。Windows 等が対象のときは `references/rubric.md` の「6. OS 別の読み替え」を使う。

## 実行手順

### ステップ1: 情報収集（この実装セッションで行う）

以下の事実情報のみを収集する。実装の意図・目的・設計判断の説明は**含めない**（レビューエージェントに渡さない）。

| 確認項目 | 確認内容 |
|----------|----------|
| **対象サーバーの環境** | OS（ディストリビューション・バージョン）、クラウド/オンプレミス、レンタルサーバー等 |
| **生成に使ったプロンプト** | `init.md`（初期設定）/ `automation.md`（自動化）/ `windows-standard.md`（Windows標準化）等（`workflows/ops-management/server/` 配下） |
| **適用先** | テスト環境のみ / ステージング / 本番環境のいずれか |
| **既存の運用ルール・制約** | 社内セキュリティポリシー、ネットワーク制約、利用禁止ツール等 |

これらはスクリプト・設定ファイルの記載から読み取る。読み取れない項目は「不明」と明記したまま進めてよい（適用先が不明なら本番扱いで厳しく評価するよう、エージェントへ伝える）。スクリプトの目的は、事実情報として冒頭コメントや README に書かれている範囲だけを渡し、作成者に言語化を求めない。

対象スクリプト・設定ファイルの内容一式を収集する（引数でパス指定がある場合はそのファイル、範囲指定がある場合はその範囲）。

### ステップ2: レビューエージェント起動

**Agent ツール**を使い、以下の設定で別エージェントを起動する:

```
Agent ツールの設定:
- subagent_type: "readonly-reviewer"（`.claude/agents/readonly-reviewer.md`。書き込み系ツールを持たない。定義が無い環境・新設直後で未読込のセッションでは "general-purpose" で起動し、prompt 冒頭に「ファイルを作成・変更・削除しない」と明記する）
- description: "Review ops script/config objectively"
- prompt: 以下のテンプレートに収集した情報を埋め込む
```

**プロンプトテンプレート（レビューエージェントに渡す内容）:**

````
あなたは実装者とは別の客観的なシニアSRE/インフラエンジニアです。
以下の運用スクリプト・サーバー設定を、5項目・各20点・合計100点満点で評価してください。

## レビュー観点（5項目・各20点・合計100点）

[references/rubric.md の本文（1〜6 の各節。採点目安の表を含む）をそのまま埋め込む]

## 行動原則
`.claude/skills/_shared/review-rubrics.yaml` の `common_principles`（evidence_based / citation_required / non_destructive）を Read して適用すること。加えて本 skill 固有の原則として:
- セキュリティ指摘は最優先で報告する: 秘密情報のハードコード、過剰な権限設定、未暗号化通信等の
  セキュリティリスクを発見した場合は、スコアに関わらず「セキュリティ上の緊急指摘事項」セクションに
  即座に記載すること
- 本番環境への影響を常に意識する: テスト環境でのみ検証されたスクリプトであっても、本番適用時の
  リスクを想定してレビューすること。特に冪等性・ロールバック・エラーハンドリングは本番障害に
  直結するため厳しく評価する

## レビュー対象
[ここに対象スクリプト・設定ファイルの内容一式を埋め込む]

## 基本情報
- 対象スクリプト/設定：
- 対象環境（OS・サーバー種別）：
- 使用したプロンプト（server-init / server-automation / server-windows-standard）：
- 適用先（テスト / ステージング / 本番）：

## 採点方法（総合点：100点満点）

`.claude/skills/_shared/review-rubrics.yaml` を Read し、`verdict_scales.rank5_100` の bands/meaning に従って S/A/B/C/D を判定すること（点数帯・各段階の対応方針は同ファイルが SoT）。

## 出力

[references/output-format.md の本文（markdown ブロックの中身）をそのまま埋め込む]
````

### ステップ3: 結果の報告

レビューエージェントから返却された結果を、そのままユーザーに表示する。
要約や解釈を加えない（レビューの客観性を維持するため）。

次の場合は結果を補完・推測せず対処する:

| 状況 | 対処 |
|------|------|
| 対象パスが存在しない・空 | エージェントを起動せず、ユーザーに正しいパスを聞く |
| エージェントが失敗・空応答、または出力フォーマットに沿わない（総合点・観点別採点が無い） | 同じプロンプトで 1 回だけ再起動。再度失敗したら、その事実と返却内容をそのまま報告する |
| `.claude/skills/_shared/review-rubrics.yaml` が無い（他プロジェクトへコピーした場合） | 共通原則は「証拠に基づく・該当箇所を引用する・ファイルを変更しない」とし、判定は S 90〜100 / A 80〜89 / B 70〜79 / C 60〜69 / D 59 以下で行うよう prompt に明記する |

## 参照ファイル（1階層）

| ファイル | 内容 |
|----------|------|
| [references/rubric.md](references/rubric.md) | 5軸のチェック項目・採点目安・OS 別の読み替え |
| [references/output-format.md](references/output-format.md) | レビュー結果の出力テンプレート |

## 注意事項

- **絶対に実装セッション内で直接レビューしない**。必ず Agent ツールで別エージェントを起動すること
- レビューエージェントに渡す情報は事実（スクリプト・設定内容）のみ。実装の意図・設計判断は渡さない
- **レビュワーは元ファイルを絶対に編集してはならない**。レビューはあくまで「フィードバックの提供」
  であり、修正作業は作成者自身が行う。改善点は具体的に指摘し、修正案は「提案」として記載すること

## 使用例

- 「サーバー初期設定スクリプトをレビューして」→ ステップ1 でスクリプトから OS・生成プロンプト・適用先（本番か）を読み取る → スクリプト一式を埋め込んだ prompt で別エージェントを起動 → 5 軸の得点表・S〜D 判定・セキュリティ上の緊急指摘をそのまま表示。
- `/review-ops ops/backup.sh` → 引数のファイルのみを対象にする。適用先が書かれていなければ「不明」とし、本番扱いで厳しく評価させる。
- 対象が Windows の標準化スクリプト → 観点は `references/rubric.md` の「6. OS 別の読み替え」で評価させる。
- B以下の判定 → 改善提案を反映してから再レビューする。S/A 判定なら本番環境への適用を検討する。

## 参照ドキュメント

- サーバー初期設定 skill: `.claude/skills/server-init/SKILL.md`
- サーバー自動化 skill: `.claude/skills/server-automation/SKILL.md`
- Windows標準化 skill: `.claude/skills/server-windows-standard/SKILL.md`
- 元プロンプト (SoT): `workflows/ops-management/review-ops.md`（リポジトリルートからの相対パス）
- 共通原則・判定帯: `.claude/skills/_shared/review-rubrics.yaml`（Job-Automate リポジトリの配置。無い環境のフォールバックはステップ3 の表）

## 更新履歴

- 1.1: 5軸のチェック項目・出力テンプレートを `references/` に分離。ステップ1 の確認項目から「目的」を外し、前提・環境依存と OS 別の読み替えを追加。
