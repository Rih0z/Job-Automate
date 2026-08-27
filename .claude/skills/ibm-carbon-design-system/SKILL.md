---
name: ibm-carbon-design-system
description: "Generates or applies an IBM Carbon Design System-compliant design token set (color roles, typography scale, 8px spacing grid, Lucide iconography) plus Neo-Brutalist component specs (Button, Card, Loading states) for a new or existing frontend project. Use when the user asks to 'IBM Carbon準拠のデザインシステムを作って', 'デザイントークンを定義して', 'デザインシステムをセットアップして', or references design-system.md."
---

# Design System (IBM Carbon準拠) — Skill 概要

**前提**: 使用前に `customer-persona-design` Skill でペルソナ分析を完了してください。カラー・フォントの決定はペルソナ分析の結果に基づく。

## このSkillが提供するもの

1. **Design Philosophy** — Accessibility by Default / No Emoji Only Icons / Brutalist Minimalism の3原則
2. **Foundations** — Color Roles（Light/Dark自動マッピング）、Typography（Inter + JetBrains Mono のType Scale）、8pxグリッドのSpacing、Lucide Iconsサイズ基準
3. **Guidelines** — 絵文字禁止ポリシー、Dark Mode Strategy（ThemeProvider実装込み）
4. **Components** — Button（Primary/Secondary/Ghost）、Card の Usage/Style/Code/Accessibility 4点セット仕様
5. **Patterns** — Loading States（Skeleton Screen優先）
6. **Accessibility** — WCAG 2.2 AA準拠チェックリスト（レベルA/AA）
7. **Implementation** — Phase 1(Foundations)→2(Components)→3(アクセシビリティ検証) の適用手順 + デプロイ前チェックリスト

## 使い方

本ファイルは概要のみを保持する（Progressive Disclosure）。実装に着手する際は、必ず以下の原文を Read してから CSS変数・コンポーネントコード・チェックリストをそのまま適用すること（要約や省略をせず、原文のコード例を使う）。

**原文（完全版・583行）**: `workflows/software-development/design/design-system.md`

原文には以下が全文収録されている:
- Color Roles の完全な CSS変数定義（Light/Dark両対応、`prefers-color-scheme` + `data-theme` 属性切り替え）
- Typography の Type Scale（`clamp()` によるレスポンシブ対応）
- 8px Spacing Grid とコンテナ幅定義
- Iconography の代替案比較表（Lucide vs Heroicons vs Font Awesome vs Material Icons）
- Button / Card コンポーネントの CSS + React(TSX) 実装コード
- ThemeProvider の React実装
- WCAG 2.2 チェックリスト（`1.1.1` 等の達成基準番号付き）
- Phase別実装手順とデプロイ前チェックリスト

## 関連 Skill

- `customer-persona-design` — 本Skill適用前の前提（カラー・フォント選定根拠）
- `ui-design-guidelines` — 絵文字禁止・アクセシビリティの実装チェックリスト（本Skillと一部重複、実装時のチェックリストとして併用）
- `avoid-ai-generated-design-look` — 「AIっぽさ」を避けるデザイン原則のリファレンス
- `/review-implementation` コマンド — 本Skillの成果物を含む実装全体をレビューする際の評価基準（`dev/design/design-system.md` として参照）
