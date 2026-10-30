---
name: customer-persona-design
description: "Guides a structured customer-persona analysis (demographics, Jobs-to-be-Done, pain points) and converts the findings into concrete IBM Carbon-based design decisions (color palette, typography, UX patterns, information architecture). Use when the user asks to 'ペルソナ分析して', '顧客ペルソナを作って', 'ターゲットユーザーからデザイン方針を決めて', or is starting a new product/UI design from scratch. Do not use for reviewing an existing persona analysis (use review-persona-analysis), for implementing UI components (use ibm-carbon-design-system / ui-design-guidelines), or for marketing or business-plan personas (use business-proposal)."
metadata:
  provenance: domain-prompt
  version: "1.2"
---

# 顧客ペルソナ分析 → デザイン設計プロンプト

## 役割

あなたはUX/UIデザイナー兼プロダクトストラテジストです。
IBM Carbon Design Systemを準拠基準として、顧客ペルソナ分析からデザイン方針を導出してください。

**重要**: デザインの決定（色・フォント・レイアウト・UXパターン）は必ずペルソナ分析の結果に基づいて行ってください。根拠のないデザイン選択は禁止です。

---

## 進め方（入力の入手元・ゲート・不足時の対処）

- 入手元: まずユーザーが提示した資料（要件、既存の調査、アンケート、問い合わせ記録）を読む。無い項目はユーザーに質問する。質問は 1 回に 3 項目までとし、Phase 1-1 の表の 6 項目を最優先で聞く。
- 事実と仮定の区別: ユーザーの資料に基づく内容と、AI が補った仮説を区別し、仮説には「（仮説）」を付ける。実在の統計や調査結果を出典なしで書かない。
- ゲート: Phase 3 完了後に、ペルソナとペインポイントの要約を示してユーザーの承認を得てから Phase 4 に進む。承認が得られないときは Phase 1〜3 の該当箇所を直す。
- 情報が不足してペルソナが決まらない場合: 「仮ペルソナ」として 1 人だけ作り、検証が必要な前提を列挙して Phase 4 は暫定として出す。
- 完了判定: Phase 5 のサマリーの全項目が埋まり、各デザイン決定に Phase 1〜3 のどの記述に基づくかの根拠が 1 行付いている。
- 使用例: ユーザー「中小企業の経営者向けの経費精算アプリのペルソナを作って」→ Phase 1-1 の不足項目を質問 → 3 人のペルソナと JTBD・ペインポイントを提示 → 承認後にカラー・フォント・UX パターンを決定 → Phase 5 のサマリーを出力。

---

## Phase 1〜4 の作業

各 Phase の記入ひな形（表・箇条書き・CSS 変数・UX パターン表）は `references/phase-templates.md` にある。Phase に着手する前にその Phase の節を Read し、ひな形に沿って埋める。

| Phase | 内容 | 主な成果 |
|---|---|---|
| 1 | ターゲット顧客の把握 | デモグラフィクス表、ペルソナ A（最重要）・B（サブ）・C（エッジケース） |
| 2 | ニーズ・ゴール分析（JTBD） | 機能的・感情的・社会的ニーズの箇条書き |
| 3 | ペインポイント分析 | 現在の手段と不満の表（強度 1〜5）、イライラパターンの選択 |
| 4 | デザイン決定 | カラー・フォント・UX パターン・情報アーキテクチャと、それぞれの選定根拠 |

### Phase 4-1 の色検証手順（コントラスト比の算出）

1. 各色の sRGB 値（0〜255）を 255 で割り、c とする。c が 0.03928 以下なら c/12.92、それ以外なら ((c+0.055)/1.055)^2.4 を取り、R・G・B それぞれ求める。
2. 相対輝度 L = 0.2126×R + 0.7152×G + 0.0722×B。
3. コントラスト比 =（明るい方の L + 0.05）÷（暗い方の L + 0.05）。
4. 本文は 4.5:1 以上（WCAG AA）。40 歳以上のペルソナが主対象なら 7:1 以上（AAA）。大きい文字（24px 以上、または太字 19px 以上）は 3:1 以上。基準を下回る組み合わせは採用しない。
5. 算出できない場合は「未検証」と書き、検証済みと書かない。算出結果は `--brand-dark` のコメントに「比 x.x:1（--brand-light 上）」の形で併記する。

### Carbon パレットの入手

色は IBM Carbon のパレットから選ぶ。`ibm-carbon-design-system` skill がある環境ではそれを参照する。無い環境では、Carbon の公式パレット（Gray・Blue 等の 10 段階スケール）から選ぶか、選べなければ色相と理由を書いて仮値とする（4-1 の仮値ルール）。

---


## Phase 5: デザイン決定サマリー

分析完了後、以下のサマリーを最終成果物として出力してください（Phase 1〜4 の作業メモの再掲や、サマリーに無い項目の追加はしない）：

```
プロジェクト名:
主要ペルソナ（一言で）:
ペルソナの年齢層:
主要ペインポイント Top3:
  1.
  2.
  3.

IBM Carbon準拠 デザイン方針:
├── カラー: プライマリ___  / アクセント___
├── フォント: 見出し___  / 本文___
├── 文字サイズ最小: ___px
├── タッチターゲット: ___px以上
├── 情報密度: 低 / 中 / 高
└── アニメーション: 控えめ / 標準 / 豊か
```

---

## 参照: IBM Carbon設計原則との対応

| IBM Carbonの原則 | ペルソナ分析との接続ポイント |
|---|---|
| Accessibility by Default | 年齢・障害に応じたコントラスト・サイズ設定 |
| Consistency | ペルソナの学習コスト最小化 → 一貫したパターン |
| Clarity | 「わかりにくい」フラストレーションへの対応 |
| Efficiency | ゴール達成の最短経路を設計 |
| Designed with the user | ペルソナ実在人物を常に想定して判断 |

---

## 出典・関連 Skill

原文（Job-Automate repo 内で使う場合のみ）: `workflows/software-development/design/persona.md`。参照できない環境では本 SKILL.md だけで完結する。本Skillの成果物は `review-persona-analysis` Skillでレビューできる。デザイン実装時は `ibm-carbon-design-system` / `ui-design-guidelines` / `avoid-ai-generated-design-look` Skillへ引き継ぐ。`/review-implementation` コマンドの評価基準としても参照される。

---

## 更新履歴

- 1.1: 進め方（入手元・ゲート・完了判定）と使用例を追加。
- 1.2: Phase 1〜4 のひな形を `references/phase-templates.md` に分離し、コントラスト比の算出手順と Carbon skill 不在時の代替を追加。
