---
name: review-oss-contribution
description: "Audit OSS contribution candidates in a candidates directory. Checks originality, prior art, feasibility, and strategy. 別エージェントを起動してレビューする（自己レビューしない）。"
disable-model-invocation: true
allowed-tools: Read Grep Glob Agent
argument-hint: "<candidates-dir> (省略時は ./oss-contributions/open/)"
metadata:
  provenance: author-preference
---

# OSS貢献候補の審査（エージェント分離実行、2026-08-31 是正）

> **このスキルは別エージェントを起動して審査を行う。現在のセッションでは直接判定しない。**
> 作成時の思考過程・設計判断・会話履歴を審査エージェントに渡さないことで客観性を確保する
> （`review-proposal` / `review-blog` と同型のパターン、2026-08-31 是正 — 従来は self-review だった）。

指定ディレクトリ（省略時は `./oss-contributions/open/`）に配置されたOSS貢献候補を審査し、以下の基準で判定する。

## 実行手順

### ステップ1: 情報収集（この実装セッションで行う）

以下の事実情報のみを収集する。候補の採否に関する自分の意見・推測は**含めない**。

```
収集対象:
1. `$ARGUMENTS`（省略時は `./oss-contributions/open/`）配下の全 `.md` ファイル（`_` で始まるものを除く）の完全パス一覧
2. 各ファイルの全文
3. `.claude/skills/_shared/review-rubrics.yaml` の完全パス（審査エージェントが自ら Read する）
4. `.claude/skills/review-oss-contribution/criteria/oss-contribution.json` の完全パス（審査エージェントが自ら Read する。4基準の checks・判定ルールの SoT）
```

### ステップ2: 審査エージェント起動

**Agent ツール**を使い、候補ファイルごとに以下の設定で別エージェントを起動する:

```
Agent ツールの設定:
- subagent_type: "general-purpose"
- description: "Audit OSS contribution candidate objectively"
- prompt: 以下のテンプレートに候補ファイルの完全パスを埋め込む
```

**プロンプトテンプレート（審査エージェントに渡す内容）:**

```
あなたは作成者とは別の客観的な OSS コントリビューション審査担当です。
以下の候補ファイルを読み、独自性・先行技術・実現可能性・戦略の4基準で審査してください。

## 行動原則
`.claude/skills/_shared/review-rubrics.yaml`（リポジトリルートからの相対パス）
の `common_principles` と `severity` を Read して適用すること。

## 審査対象ファイル
[ここに候補ファイルの完全パスを埋め込む。ファイル内容は自分で Read すること]

## 審査基準・判定基準
[criteria/oss-contribution.json の完全パスを埋め込む。4基準の checks・reject_rule・severity_note を自分で Read すること。判定語彙(GO/HOLD/REJECT)の詳細は `.claude/skills/_shared/review-rubrics.yaml` の `verdict_scales.go3` を参照]

## 重要な制約
- 対象ファイルを絶対に編集しない（審査のみ、修正案は「提案」として記載）
- 結果は下記「出力形式」に従い、逐語引用で理由を示す
```

### ステップ3: 結果の報告

審査エージェントから返却された結果を、そのままユーザーに表示する。要約や解釈を加えない
（審査の客観性を維持するため）。

## 審査基準

観点定義 (SoT) = `.claude/skills/review-oss-contribution/criteria/oss-contribution.json`（4基準: 独自性/先行技術/実現可能性/戦略の checks・汚染検知grep手順・severity付与ルールを保持、本文へ prose 重複記載しない）。判定語彙(GO/HOLD/REJECT)の詳細ルールは `.claude/skills/_shared/review-rubrics.yaml` の `verdict_scales.go3` が SoT。

要点（詳細は上記2ファイルが SoT）:
- 独自性が ❌ → 無条件で REJECT
- 独自性が ✅ かつ残り3基準が全て ✅ → GO
- 独自性が ✅ かつ残り3基準のいずれかに重大な ❌ → REJECT
- 独自性が ✅ かつ重大な❌はないが1つ以上△ → HOLD

## 出力形式

各候補について以下を出力:

```
## [ファイル名]
- 独自性: ✅/△/❌ + 理由
- 先行技術: ✅/△/❌ + 理由
- 実現可能性: ✅/△/❌ + 理由
- 戦略: ✅/△/❌ + 理由
- 判定: **GO** / **HOLD** / **REJECT**
- 理由: 上記4基準の判定に基づく1〜2行（どの基準がどう効いて当該判定になったかを明記）
```

## 実行

`$ARGUMENTS`（省略時は `./oss-contributions/open/`）の全 `.md` ファイル（`_` で始まるものを除く）を読み、上記基準で審査せよ。
