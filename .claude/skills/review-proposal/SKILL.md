---
name: review-proposal
description: "business-proposal / it-proposal / generic-proposal skill で作成された提案書・企画書を、構成・論理性/市場分析・競合克服戦略/ペルソナ適合性/根拠の明確性/エンゲージメント・リテンション設計/説得力・表現品質の6軸・100点満点で客観的に採点し、S/A/B/C/D 判定とレビュー結果レポートを返す。別エージェントを起動してレビューする（自己レビューしない）。「この提案書をレビューして」「企画書を採点して」「提案書の品質チェック」「企画書にフィードバックがほしい」「提案書を評価して」等で使用。提案書の新規作成・書き直しには使わない（business-proposal / it-proposal / generic-proposal を使う）。技術仕様書のレビューは review-specification、事業アイデアのレビューは review-business-idea を使う。"
allowed-tools: Read Glob Grep Agent
argument-hint: "[レビュー対象の提案書ファイルの絶対パス]"
metadata:
  provenance: domain-prompt
  version: "1.1.0"
---

# /review-proposal — 提案書 品質レビュー（エージェント分離実行）

> **このスキルは別エージェントを起動してレビューを行う。現在のセッションでは直接レビューしない。**
> 作成時の思考過程・設計判断・会話履歴をレビューエージェントに渡さないことで客観性を確保する。

対象: `business-proposal` / `it-proposal` / `generic-proposal` skill をもとに作成された提案書・企画書
目的: 「構成・論理性」「市場分析・競合克服戦略」「ペルソナ適合性」「根拠の明確性」「エンゲージメント・リテンション設計」「説得力・表現品質」の6軸で提案書品質を100点満点で評価する。

## 前提と環境依存

- この repo 固有: `.claude/agents/readonly-reviewer.md`、`.claude/skills/_shared/review-rubrics.yaml`、`workflows/business-planning/review-proposal.md`。無い環境では、エージェントは `general-purpose` で代替し、判定帯は下記「エラー時の対処」の代替に従う。SKILL.md と `references/` だけで最低限動く。
- 必要なツール: Read / Glob / Grep（収集）、Agent（レビュー起動）。対象文書の編集はしない。
- 他リポジトリへコピーする場合は `references/` も一緒に移す。

## 実行手順

### ステップ1: 情報収集（この実装セッションで行う）

以下の事実情報のみを収集する。作成の意図・設計判断の説明は**含めない**。

```
収集対象:
1. レビュー対象の提案書・企画書の全文
2. 以下の「レビュー前の必須確認事項」（直下の箇条書き 4 項目）が文書内または作成者からの回答で判明しているか
   - この提案書で最も伝えたいことは何か（主張・結論を1〜2文で言語化できるか）
   - 提案先（読者・意思決定者）は誰か（経営層・担当者・投資家など）
   - 読者がこの提案書を読んだ後に何を「決断する」か（求める行動が明示されているか）
   - どの skill で作成したか（business-proposal / it-proposal / generic-proposal）
```

上記が不明瞭な場合は、レビュー開始前に作成者へ確認すること。確認できない項目は「不明」と明記したままレビューを続行してよい（対象文書が提案書・企画書でない場合は、実行せずその旨をユーザーに伝える）。

### ステップ2: レビューエージェント起動

**Agent ツール**を使い、以下の設定で別エージェントを起動する:

```
Agent ツールの設定:
- subagent_type: "readonly-reviewer"（`.claude/agents/readonly-reviewer.md`。書き込み系ツールを持たない。定義が無い環境・新設直後で未読込のセッションでは "general-purpose" で起動し、prompt 冒頭に「ファイルを作成・変更・削除しない」と明記する）
- description: "Review proposal document objectively"
- prompt: 以下のテンプレートに収集した情報を埋め込む
```

**プロンプトテンプレート（レビューエージェントに渡す内容）:**

````
あなたは作成者とは別の客観的な事業提案の専門家です。
以下の提案書・企画書を、6項目・合計100点で評価してください。

## 行動原則
`.claude/skills/_shared/review-rubrics.yaml` の `common_principles`（evidence_based / citation_required / non_destructive）を Read して適用すること。

## レビュー対象文書
[ここに対象提案書・企画書の全文を埋め込む]

## 基本情報（ステップ1で判明した範囲。不明は「不明」と書く）
[提案先 / 求める行動 / 使用 skill を埋め込む]

## レビュー観点（6項目・合計100点）

[references/rubric.md の本文（1〜6 の各節。採点目安の表を含む）をそのまま埋め込む]

## 採点方法（総合点：100点満点）

`.claude/skills/_shared/review-rubrics.yaml` を Read し、`verdict_scales.rank5_100` の bands/meaning に従って S/A/B/C/D を判定すること（点数帯・各段階の対応方針は同ファイルが SoT）。

## 出力（レビュー結果出力フォーマット）

[references/output-format.md の本文（markdown ブロックの中身）をそのまま埋め込む]
````

### ステップ3: 結果の報告

レビューエージェントから返却された結果を、そのままユーザーに表示する。
要約や解釈を加えない（レビューの客観性を維持するため）。

## エラー時の対処

| 状況 | 対処 |
|------|------|
| 対象文書のパスが無い・読めない | 実行せず、対象ファイルの絶対パス（または全文）の提示をユーザーに求める |
| `.claude/skills/_shared/review-rubrics.yaml` が読めない | レビューエージェントには、読めなかった旨を伝え、`references/rubric.md` の採点目安のみで採点させる。判定は S 90〜100 / A 80〜89 / B 70〜79 / C 60〜69 / D 59 以下とし、報告時に「rubrics 未参照」と明記する |
| Agent の起動に失敗した | `readonly-reviewer` が無ければ `general-purpose` で再試行。それでも起動できなければレビューは未実施とし、現セッションで代替レビューはしない |
| 返却結果が出力フォーマットに沿わない | 同じ入力でレビューエージェントを 1 回だけ再起動し、フォーマット遵守を明記する。なお崩れる場合は返却内容をそのまま表示し、崩れている旨を添える |

## 参照ファイル（1階層）

| ファイル | 内容 |
|----------|------|
| [references/rubric.md](references/rubric.md) | 6軸のチェック項目・採点目安 |
| [references/output-format.md](references/output-format.md) | レビュー結果の出力テンプレート |

## 使用例

- 「`docs/plan.md` の提案書をレビューして」 → ステップ1で全文と確認事項を収集 → ステップ2で readonly-reviewer を起動 → 6軸の採点表と S/A/B/C/D 判定をそのまま表示
- 提案先が書かれていない提案書 → 基本情報の「提案先」を「不明」とし、ペルソナ適合性の観点では「読者が特定できない」ことを減点理由として扱わせる
- 「提案書を書き直して」 → このスキルの対象外。`business-proposal` 等を案内する

## 注意事項

- **絶対に実装セッション内で直接レビューしない**。必ず Agent ツールで別エージェントを起動すること
- レビュワーは元ファイルを絶対に編集してはならない。改善点は具体的に指摘し、修正案は「提案」として記載する
- 上記「レビュー前の必須確認事項」が文書から読み取れない場合は、作成者へ確認する

## 参照ドキュメント

- 元プロンプト（詳細確認用）: `workflows/business-planning/review-proposal.md`
- 前ステップ（提案書作成）: `business-proposal` / `it-proposal` / `generic-proposal` skill
- 次ステップ（技術仕様書化）: `specification` skill

## 更新履歴

- 1.1.0: 6軸の観点・出力テンプレートを `references/` に分離し、前提・環境依存の節を追加。見出しをステップ順に整理。
