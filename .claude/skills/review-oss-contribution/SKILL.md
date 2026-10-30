---
name: review-oss-contribution
description: "OSS 貢献候補（候補ごとに 1 つの .md ファイルにまとめたもの）を、独自性・先行技術・実現可能性・戦略の 4 基準で審査し、候補ごとに GO / HOLD / REJECT を返す。Audit OSS contribution candidates in a candidates directory. 別エージェントを起動して審査する（自己審査しない）。Use when: 「OSS 貢献候補を審査して」「コントリビューション候補をレビューして」「contribution review」「どの OSS 貢献を進めるか判定して」。Do not use for: 提案書（review-proposal）、ブログ記事（review-blog）、スライド（review-slides）、コード差分（review-changes）、実装の総合評価（review-implementation）。"
disable-model-invocation: true
allowed-tools: Read Grep Glob Agent
argument-hint: "[candidates-dir] (省略時は ./oss-contributions/open/)"
metadata:
  provenance: author-preference
  version: "1.2"
---

# OSS貢献候補の審査（エージェント分離実行）

> **このスキルは別エージェントを起動して審査を行う。現在のセッションでは直接判定しない。**
> 作成時の思考過程・設計判断・会話履歴を審査エージェントに渡さないことで客観性を確保する
> （`review-proposal` / `review-blog` と同型のパターン）。

指定ディレクトリ（省略時は `./oss-contributions/open/`）に配置されたOSS貢献候補を審査し、以下の基準で判定する。

## 前提と環境依存

- 候補ディレクトリ（既定 `./oss-contributions/open/`）は Job-Automate repo には最初から無く、利用者が用意する。引数で別のディレクトリも指定できる。
- `criteria/oss-contribution.json`（この skill に同梱）は必須。
- `.claude/skills/_shared/review-rubrics.yaml` と `.claude/agents/readonly-reviewer.md` は Job-Automate repo 固有で、あればそれを使う。無い環境では `references/rubric.md`（4基準・判定規則・共通原則・重大度・審査エージェントの条件）で代替でき、SKILL.md と references/ と `criteria/` だけで動く。
- 出力形式と、出力に含めない情報は `references/output-format.md` にある。
- 必要なツール: Read / Grep / Glob（収集）、Agent（審査起動）。候補ファイルの編集はしない。

## 実行手順

### ステップ1: 情報収集（この実装セッションで行う）

以下の事実情報のみを収集する。候補の採否に関する自分の意見・推測は**含めない**。

```
収集対象:
1. `$ARGUMENTS`（省略時は `./oss-contributions/open/`）配下の全 `.md` ファイル（`_` で始まるものを除く）の完全パス一覧
2. 各ファイルの全文
3. `.claude/skills/_shared/review-rubrics.yaml` の完全パス（審査エージェントが自ら Read する。無ければ `references/rubric.md` の完全パスを渡す）
4. `.claude/skills/review-oss-contribution/criteria/oss-contribution.json` の完全パス（審査エージェントが自ら Read する。4基準の checks・判定ルールの SoT）
5. `.claude/skills/review-oss-contribution/references/output-format.md` の完全パス（出力形式と出力に含めない情報。審査エージェントが自ら Read する）
```

収集で次のいずれかになったら、エージェントを起動せず状況を報告して止まる:
- 指定ディレクトリが存在しない → パスの誤りを伝え、正しいパスをユーザーに聞く
- 対象の `.md` が 0 件 → 「候補が無い」と報告する（空の審査結果を作らない）
- `oss-contribution.json` が読めない → skill の配置が壊れているので、不足ファイルを報告する（`review-rubrics.yaml` が無い場合は止まらず前提の代替で進める）

### ステップ2: 審査エージェント起動

**Agent ツール**を使い、候補ファイルごとに以下の設定で別エージェントを起動する:

```
Agent ツールの設定:
- subagent_type: "readonly-reviewer"（`.claude/agents/readonly-reviewer.md`。書き込み系ツールを持たない。定義が無い環境・新設直後で未読込のセッションでは "general-purpose" で起動し、prompt 冒頭に「ファイルを作成・変更・削除しない」と明記する）
- description: "Audit OSS contribution candidate objectively"
- prompt: 以下のテンプレートに候補ファイルの完全パスを埋め込む
```

**プロンプトテンプレート（審査エージェントに渡す内容）:**

```
あなたは作成者とは別の客観的な OSS コントリビューション審査担当です。
以下の候補ファイルを読み、独自性・先行技術・実現可能性・戦略の4基準で審査してください。

## 行動原則
`.claude/skills/_shared/review-rubrics.yaml`（リポジトリルートからの相対パス）
の `common_principles` と `severity` を Read して適用すること。同ファイルが無い場合は `references/rubric.md` の共通原則と重大度を適用すること。

## 審査対象ファイル
[ここに候補ファイルの完全パスを埋め込む。ファイル内容は自分で Read すること]

## 審査基準・判定基準
[criteria/oss-contribution.json の完全パスを埋め込む。4基準の checks・reject_rule・severity_note を自分で Read すること。判定語彙(GO/HOLD/REJECT)の詳細は `.claude/skills/_shared/review-rubrics.yaml` の `verdict_scales.go3` を参照]

## 重要な制約
- 対象ファイルを絶対に編集しない（審査のみ、修正案は「提案」として記載）
- 結果は `references/output-format.md` の「出力形式」に従い、同ファイルの「出力に含めない情報」は書かない。逐語引用で理由を示す（候補ファイルの該当箇所をファイル名と行番号つきで引く。行番号が分からない場合は節見出し名で代える）
```

### ステップ3: 結果の報告

審査エージェントから返却された結果を、そのままユーザーに表示する。要約や解釈を加えない
（審査の客観性を維持するため）。

エージェントが失敗・空応答を返した、または出力形式に沿っていない（判定が無い）場合は、結果を補完・推測せず、その候補だけ同じプロンプトで 1 回再起動する。再度失敗したら、候補名と失敗した事実を報告する。

## 審査基準

観点定義 (SoT) = `.claude/skills/review-oss-contribution/criteria/oss-contribution.json`（4基準: 独自性/先行技術/実現可能性/戦略の checks・汚染検知grep手順・severity付与ルールを保持、本文へ prose 重複記載しない）。判定語彙(GO/HOLD/REJECT)の詳細ルールは `.claude/skills/_shared/review-rubrics.yaml` の `verdict_scales.go3` が SoT。

要点（詳細は上記2ファイルが SoT）:
- 独自性が ❌ → 無条件で REJECT
- 独自性が ✅ かつ残り3基準が全て ✅ → GO
- 独自性が ✅ かつ残り3基準のいずれかに❌ → REJECT（❌ = 重大な懸念、△ = 軽微な懸念、✅ = クリア。`review-rubrics.yaml` の `verdict_scales.go3` の定義）
- 独自性が ✅ かつ❌はないが1つ以上△ → HOLD

## 出力形式

詳細は `references/output-format.md`。各候補について、4基準（独自性・先行技術・実現可能性・戦略）の ✅/△/❌ と理由、判定（GO / HOLD / REJECT）、1〜2行の理由を出す。

出力に含めない情報（同ファイルに全項目）: 候補ファイル全文の転載、候補に書かれていない事実の推測、4基準と無関係な所感、書き換えた版の候補、判定語彙以外の総合判定、候補同士の順位づけ。

## 使用例

- 「OSS 貢献候補を審査して」（引数なし）→ `./oss-contributions/open/` の `.md` を列挙 → 候補ごとに readonly-reviewer を起動 → 各候補の 4 基準と判定をそのまま表示。
- `/review-oss-contribution drafts/oss` → そのディレクトリを対象にする。`_template.md` のように `_` で始まるファイルは対象外。
- 独自性が❌（既存の同等機能が見つかった）候補 → 他の 3 基準が ✅ でも REJECT。
- 指定ディレクトリに `.md` が 1 件も無い → エージェントを起動せず「候補が無い」と報告して止まる（失敗系。空の審査結果は作らない）。
- 先行技術に △（似た提案はあるが方向性が違う）があり、他は ✅ の候補 → HOLD。懸念点を解消してから再提出する。

## 更新履歴

- 1.2: 4基準・判定規則・共通原則・重大度を `references/rubric.md`、出力形式と出力に含めない情報を `references/output-format.md` に分離。repo 固有ファイルが無い環境の代替を明記。`criteria/oss-contribution.json` の日付注記を削除。
- 1.1: 自己審査をやめ、別エージェントを起動して審査する方式に変更。前提・環境依存の節と、`review-rubrics.yaml` が無い場合の代替を追加。
