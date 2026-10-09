---
name: review-chatbot-operation-design
description: "顧客対応チャットボットの運用設計書（chatbot-operation-design の出力、または同等の文書）を、対応範囲・回答の根拠・有人への引き継ぎ（フラストレーション検知を含む）・引き継ぎ手順・ガードレール・ツール操作・透明性・成功基準と評価・運用監視・障害時の縮退の 10 観点・100 点満点で採点する。観点は構造化 JSON（criteria/chatbot-operation.json）で、Anthropic 公式資料に出典のあるものと、公式根拠の無い運用慣行を区別して持つ。設計書を確定する前にレビューしたい時に使う。別エージェントを起動してレビューする（自己レビューしない）。"
when_to_use: "「チャットボットの運用設計をレビューして」「サポートボットのエスカレーション設計を確認して」「問い合わせ対応 AI の運用ルールを採点して」等、顧客対応チャットボットの運用設計書を確定する前"
argument-hint: "[運用設計書のパス]"
metadata:
  provenance: domain-prompt
---

# /review-chatbot-operation-design — 顧客対応チャットボット運用設計レビュー（エージェント分離実行）

> **このスキルは別エージェントを起動してレビューを行う。現在のセッションでは直接レビューしない。**
> 設計書を作った時の思考過程・会話履歴はレビューエージェントに渡さない。

対象: `chatbot-operation-design` skill の出力、または同等の顧客対応チャットボット運用設計書
観点の SoT: [criteria/chatbot-operation.json](criteria/chatbot-operation.json)（観点ごとに由来 `official` / `official-derived` / `practice` と、公式の出典 URL・原文の引用を持つ。本文へ観点を重複して書かない）

## 実行手順

### ステップ1: 情報収集（このセッションで行う）

事実だけを集める。設計の良し悪しについての自分の意見は含めない。

1. `$ARGUMENTS` の運用設計書の完全パス（省略時はユーザーに聞く）
2. 本 skill の `criteria/chatbot-operation.json` の完全パス

### ステップ2: レビューエージェント起動

```
Agent ツールの設定:
- subagent_type: "readonly-reviewer"（`.claude/agents/readonly-reviewer.md`。書き込み系ツールを持たない。定義が無い環境・新設直後で未読込のセッションでは "general-purpose" で起動し、prompt 冒頭に「ファイルを作成・変更・削除しない」と明記する）
- description: "Review chatbot operation design objectively"
- prompt: 以下のテンプレートに 2 つの完全パスを埋め込む
```

**プロンプトテンプレート:**

```
あなたは作成者とは別の客観的なレビュー担当です。顧客対応チャットボットの運用設計書を、観点定義 JSON に従って採点してください。

## 対象
[運用設計書の完全パス。内容は自分で Read すること]

## 観点定義
[criteria/chatbot-operation.json の完全パス。criteria ごとの weight / must_pass / checks と pass_rule を自分で Read すること]

## 採点のしかた
- 各 criterion を checks ごとに「満たす / 一部 / 満たさない / 該当なし」で判定し、根拠として設計書の該当箇所を逐語で引用する（無ければ「記述なし」）
- criterion の得点 = weight ×（満たす 1・一部 0.5・満たさない 0 の平均。該当なしは母数から除く）
- 該当なしにできるのは次の 2 つだけ。どちらも理由を書く: (1) その check の前提が設計の範囲に無い（例: ツール連携をしないボットの tools.*）、(2) provenance が practice の check を、設計書が理由を書いたうえで採らないと決めている（理由の妥当性は任意の提案として扱う）。official / official-derived の check を採らないのは「満たさない」
- criterion 内の check がすべて該当なしなら、その criterion は採点から外し、合計は残りの weight の合計を 100 に換算する
- must_pass の criterion に「満たさない」が 1 つでもあれば、その criterion は不合格
- 判定: must_pass の criterion がすべて合格、かつ合計が pass_rule.min_score 以上なら PASS
- 指摘には check の id を付ける。provenance が practice の check への指摘は「公式根拠なし（運用慣行）」と明記し、official / official-derived と区別する
- correctness と明示された要件に関わる指摘だけを必須にし、好みの提案は任意として分ける

## 制約
- 対象ファイルを編集しない。修正案は提案として書く
```

### ステップ3: 結果の報告

レビューエージェントの結果をそのまま表示する（要約・解釈を加えない）。

## 出力形式

```
## 判定: PASS / FAIL（合計 xx / 100、must_pass: 合格 / 不合格の criterion 名）

| criterion | 得点 / weight | must_pass | 主な不足（check id） |
|---|---|---|---|

### 必須の指摘
- [check id] 設計書の該当箇所（逐語）→ 何が不足か → 修正案

### 任意の提案
- [check id]（practice の場合は「公式根拠なし」）…
```

## Examples

- 「support-bot-design.md をレビューして」→ ステップ1 で完全パスと criteria JSON のパスを集め、ステップ2 で readonly-reviewer を起動
- 引き継ぎ条件に「フラストレーションの兆候」が無い設計書 → `escalation.frustration` が満たさない → escalation（must_pass）不合格で FAIL

元プロンプト（Claude.ai 等に貼る場合）: `workflows/customer-support/review-chatbot-operation-design.md`
