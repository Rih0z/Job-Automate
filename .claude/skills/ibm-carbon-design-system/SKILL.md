---
name: ibm-carbon-design-system
description: "Generates or applies a design system for a new or existing frontend project, structured the way IBM Carbon is (role-based color tokens, type scale, 8px spacing grid, Usage/Style/Code/Accessibility component specs), with this skill's own Neo-Brutalist styling, Lucide iconography, Inter/JetBrains Mono fonts and an optional dark-mode ThemeProvider (these are house choices, not part of Carbon itself). Use when the user asks to 'IBM Carbon準拠のデザインシステムを作って', 'デザイントークンを定義して', 'デザインシステムをセットアップして', or references design-system.md. Not for choosing brand colors or fonts without persona analysis (use customer-persona-design first) and not for emoji/accessibility checklist only (use ui-design-guidelines)."
allowed-tools: Read, WebFetch
metadata:
  provenance: domain-prompt
  version: "1.2"
---

# Design System (IBM Carbon 構造準拠) — Skill 概要

**前提**: 仕様の実体は本 skill 内の `references/design-system-spec.md` にあり、他のプロジェクトへコピーしてもそのまま使える。カラー・フォントの決定はペルソナ分析の結果に基づくため、使用前に `customer-persona-design` Skill でペルソナ分析を完了してください。

## このSkillが提供するもの

`references/design-system-spec.md` に、次が値とコードつきで収録されている。

1. **設計原則** — Accessibility by Default / No Emoji Only Icons / Brutalist Minimalism
2. **Foundations** — Color Roles（Light/Dark）、Typography（Inter + JetBrains Mono の Type Scale）、8px グリッドの Spacing、Lucide のアイコンサイズ基準
3. **Guidelines** — 絵文字禁止、Dark Mode（ThemeProvider 実装つき）
4. **Components** — Button（Primary/Secondary/Ghost）、Card の Usage/Style/Code/Accessibility
5. **Patterns** — Loading States（スケルトン優先）
6. **Accessibility** — WCAG 2.2 のレベル A/AA チェックリスト
7. **Implementation** — Phase 1〜3 の適用手順とデプロイ前チェック

何に由来するか: トークンを役割で定義し、コンポーネントを 4 点セットで記述する「構造」は IBM Carbon に倣う。Neo-Brutalist の見た目、Lucide、Inter / JetBrains Mono、ThemeProvider は Carbon 公式にはなく、仕様ファイルが定める。Carbon の公式トークン値そのものを求められた場合は、公式サイトから取得して値を差し替える。

## 使い方

実装に着手する前に `references/design-system-spec.md` を Read し、CSS 変数・コンポーネントコード・チェックリストをそのまま適用する（要約や省略をしない）。

### 手順

1. 入力を確認する: 対象プロジェクトのフロントエンドの種類（React/TSX か素の CSS か）、ペルソナ分析の結果（カラー・フォントの根拠）、ダークモードの要否。ペルソナ分析が無い場合は先に `customer-persona-design` を実行するようユーザーに伝え、着手しない。
2. `references/design-system-spec.md` を Read する。リポジトリ側に原文 `workflows/software-development/design/design-system.md` がある場合は、仕様ファイルとの差異を確認し、差異があれば原文が新しいかをユーザーに尋ねる（無くても作業は進められる）。
3. Phase 1（Foundations）: 仕様ファイルの CSS 変数・Type Scale・Spacing をプロジェクトのスタイルファイル（既存の CSS/テーマファイルがあればそこ、無ければ新規にトークン用 CSS）へ適用する。ダークモード不要なら Dark 側の定義と ThemeProvider は入れない。
4. Phase 2（Components）: Button・Card・Loading を仕様ファイルのコードで追加する。既存プロジェクトでは既存コンポーネントを上書きせず、差分をユーザーに示してから置き換える。
5. Phase 3（アクセシビリティ検証）: 仕様ファイルの WCAG 2.2 チェックリストを 1 項目ずつ確認し、結果を「項目 / 合否 / 根拠（ファイルと行）」の表で報告する。不合格が残る間は完了と言わない。

各 Phase の終わりに、適用したファイルの一覧をユーザーに示して次へ進む。成果物は、トークン定義ファイル・コンポーネントファイル・Phase 3 の検証表。報告・トークンファイル・検証表・差分提示のひな形は `references/output-templates.md` を使う。

## エラー時の対処

| 状況 | 対処 |
|---|---|
| ペルソナ分析が無い | 着手せず、`customer-persona-design` の実施をユーザーに依頼する。仮の `--brand-*` 値で進めてよいと言われた場合は、仮値であることを成果物に注記する |
| 仕様ファイルが読めない（コピー漏れ等） | 作業を止め、ファイルの復元をユーザーに依頼する。値やコードを推測で作らない |
| Inter / JetBrains Mono / Lucide が使えない（ライセンス・ネットワーク・既存の別ライブラリ） | 仕様のフォールバックフォント、または既存のアイコンライブラリで代替し、代替した項目を報告に書く |
| Carbon 公式の値を求められた | 公式サイトを WebFetch で取得し、取得元 URL を報告に書く。取得できなければ、仕様ファイルは Carbon 構造に倣った独自仕様であり公式値ではないと伝えて止める |
| 既存コンポーネントとスタイルが衝突する | 上書きせず、`references/output-templates.md` の差分表を示してユーザーの了承を得る |
| Phase 3 で不合格が出た | 修正案を先頭に示して該当ファイルを直し、同じ項目を再検証する。直せない項目は理由つきで「保留」と報告し、完了と言わない |

## 使用例

- ユーザー「新規の Web アプリに IBM Carbon 準拠のデザイントークンを定義して」→ ペルソナ分析の有無を確認 → 仕様ファイルを Read → CSS 変数と Type Scale を適用 → Button/Card を追加 → WCAG 検証表を出力。
- ユーザー「既存プロジェクトにダークモードは要らない」→ Light 側のみ適用し、ThemeProvider と `data-theme` 切り替えは入れない。
- ユーザー「Carbon 公式の色コードをそのまま使って」→ 本 skill の値は Carbon 公式値ではないと伝え、公式サイトを WebFetch して取得元つきでトークンを差し替える。取得できなければ止める。

## 関連 Skill

- `customer-persona-design` — 本Skill適用前の前提（カラー・フォント選定根拠）
- `ui-design-guidelines` — 絵文字禁止・アクセシビリティの実装チェックリスト（本Skillと一部重複、実装時のチェックリストとして併用）
- `avoid-ai-generated-design-look` — 「AIっぽさ」を避けるデザイン原則のリファレンス
- `/review-implementation` コマンド — 本Skillの成果物を含む実装全体をレビューする際の評価基準（`references/design-system-spec.md` を基準として参照）

## 更新履歴

- 1.2: 仕様の実体を `references/design-system-spec.md` に自己完結で収録（外部ファイル依存を解消）。Neo-Brutalist・Lucide・フォント・ThemeProvider が Carbon 公式にない独自仕様であることを description と本文に明記。エラー時の対処表と使用例を追加。
- 1.1: 原文が無い環境の代替手順、出力テンプレート（`references/output-templates.md`）、version と更新履歴を追加。
