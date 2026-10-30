---
name: avoid-ai-generated-design-look
description: "Reference guide for making a web/app UI look human-designed instead of AI-generated: identifies telltale 'AI slop' visual/UX patterns to avoid (perfect symmetry, generic Material/Bootstrap colors, emoji icons, robotic copy) and prescribes counter-patterns (organic shapes, bold custom typography pairs, Neo-Brutalism, persona-derived brand tokens, micro-interactions, Nielsen's 10 usability heuristics). Use when the user says 'このデザインAIっぽい', 'テンプレ感をなくして', 'もっと人間らしいデザインにして', 'AI生成っぽさを消して', or asks for design inspiration/references before building a frontend. Not for: emoji/accessibility implementation checklists (ui-design-guidelines), design-token definitions of a specific system (ibm-carbon-design-system), or deriving brand colors from personas (customer-persona-design)."
metadata:
  provenance: domain-prompt
  version: 1.3.0
---

# デザインリサーチ — AIっぽくないデザイン・優れたUX

## 目的

AIコーディングで生成されるプロダクトが「AIっぽい」「テンプレート感がある」と感じられないよう、優れたデザイン・UXの原則を体系的にまとめる。

## 使い方（手順）

入力: 対象の UI（HTML/CSS/コンポーネントのファイルパス、またはデザイン案の説明）。無ければユーザーに 1 回だけ対象を聞く。

制約（診断か適用か）: 既定は診断のみで、ファイルは編集しない。ユーザーが「直して」「適用して」と明示したときだけ、診断で挙げた該当箇所に限って編集する。それ以外のファイルや無関係な箇所は変えない。報告の「変更内容」は適用した場合だけ書く。

1. 下記「AIっぽいデザインの特徴」を対象と照合し、該当箇所を `ファイル:行` またはセクション名つきで列挙する（見つけた証拠のない指摘は書かない）。次のいずれかを満たす箇所を「該当」と数える（1 箇所が複数に当たる場合も 1 件）:
   - 色: `--primary` / `--secondary` / `--accent` のような汎用名の変数、または Material・Bootstrap・Tailwind の既定色（例 `#0070f3`、`#1976d2`、`#007bff`）をそのまま使っている
   - 形状: 3 つ以上のカードやボタンが同一の `border-radius` と同一の余白で並び、`border-radius: 50%` の円や完全な左右対称だけで構成されている
   - 書体: 見出しと本文の両方が Inter / Roboto / Arial / システム既定フォントのみ
   - アイコン: UI の文言やボタンに絵文字を使っている
   - 文言: ボタンが「送信」「キャンセル」「OK」だけ、プレースホルダーが "Enter your email" のような汎用文
   - 動き: hover や状態変化に何の反応も無い（`transition` / `animation` の記述が対象全体で 0 件）
2. 該当ごとに下の「原則の要点」（CSS 例は [references/principles.md](references/principles.md)）から対応する 1 つの対策（CSS 例つき）を選ぶ。複数原則を一度に全部入れない。
3. 修正後、検証する: 該当箇所が 0 件になったか、WCAG コントラスト（通常テキスト 4.5:1 以上）とフォーカス表示が保たれているか。満たさなければ 2 に戻る。
4. 次の形式で報告する。

```
## 診断
- [該当箇所] 特徴: <どの特徴に当たるか> / 対策: <原則N>
## 変更内容（適用した場合）
- <ファイル>: <変更の要点>
## 検証結果
- AI っぽさの該当: 修正前 N 件 → 修正後 M 件 / コントラスト・フォーカス: OK or NG
```

例1: 「このランディングページ AI っぽいからテンプレ感をなくして」 → `hero.css` の `--primary: #0070f3` と全カード同一の `border-radius` を指摘 → 原則4（ブランドトークン）と原則1（形状）を適用 → 該当 2 件 → 0 件を報告。

例2: 「ボタンの文言が味気ない」 → 「送信」「キャンセル」のみの文言を指摘 → 操作結果が分かる文言（例: 「この内容で申し込む」）に変更し、原則5（マイクロインタラクション）の hover 変化を 1 つ付ける → 該当 1 件 → 0 件を報告。

例3（失敗・例外）: 「ボタンを Neo-Brutalism にして」→ 原則3 を適用して背景を `#FFD700` にしたが文字色が既存の `#777` のまま → コントラスト約 3.2:1 で 4.5:1 を下回る → 文字色を `#000` に変えて再計測し、4.5:1 以上になったことを確認してから報告する（戻せないなら原則3 の適用を取り下げ、NG のまま報告する）。

## エラー時の対処

| 状況 | 対処 |
|---|---|
| 対象ファイルが無い／読めない | 設計相談として原則だけを提示し、「未検証」と明記する |
| ブランド色が未定 | ペルソナ由来の値を捏造せず、仮値であることを注記する。ペルソナ分析が要るなら `customer-persona-design` を案内する |
| Neo-Brutalism がブランドに合わない | 原則2・5 だけで構わない。原則3 を無理に入れない |
| 修正後にコントラストが 4.5:1（大きな文字は 3:1）未満 | 色変更を直前の状態に戻し、文字色または背景色の明度だけを調整して再計測する。2 回調整しても満たさなければ、その原則の適用を取り下げて「NG」と報告する |
| フォーカス表示が消えた（`outline: none` を入れた等） | 該当の記述を削除し、「アクセシビリティ基準」の `outline: 3px solid` を戻す（基準は [references/design-notes.md](references/design-notes.md) の WCAG 節） |
| ブラウザで表示確認ができない | CSS の値の計算（コントラスト比など）だけで検証し、見た目の確認は「未確認」と書く |
| 該当が 0 件のまま修正前の診断になった | 変更せず「該当なし」と報告し、無理に直さない |

---

## 原則の要点

CSS 例は [references/principles.md](references/principles.md)（目次つき）。

1. 人間らしいディテール: 完璧な円や完全な左右対称を避け、わずかに歪んだ形や意図的な不完全さを入れる。
2. 大胆なタイポグラフィ: 見出し用セリフと本文用サンセリフの組み合わせ、特大の見出し。見出し・本文の両方を汎用書体にしない。
3. Neo-Brutalism: 厚い枠線、高コントラスト、フラットな影。ブランドに合う場合だけ使う。
4. デザイントークン: `--primary` のような汎用名でなく、ブランド固有のトークンを使う。値はペルソナ分析で決め、未定なら仮値と注記する。
5. マイクロインタラクション: hover や状態変化に spring 的な動きや段階表示を付ける。

## 参照資料

- [references/design-notes.md](references/design-notes.md): AI っぽい特徴の詳細、デザインシステム事例、Nielsen の 10 ヒューリスティック、WCAG 2.2 基準、参考リンク（目次つき）。診断で根拠を示すときと、検証手順 3 の基準確認で読む。

## 他 skill との関係

この skill は単体で完結する。次の skill は無くても動く関連資料で、あれば併用してよい。UI に絵文字を使わない方針は、同 skill が無い環境でも守る。

- `ui-design-guidelines`: 絵文字禁止、アクセシビリティ実装チェックリスト
- `ibm-carbon-design-system`: デザイントークン本体
- `customer-persona-design`: ブランドトークンの導出元

更新履歴:
- 1.3.0: 検出条件の詳細・CSS 例・事例・基準を references/ に分離し、診断のみか適用までかの制約を明記（趣旨は変更なし）
- 1.2.0: 「該当」の判定条件を 6 種の検出条件に列挙、エラー時の対処表と失敗例（例3）を追加、時限性のある参考リンクを削除（趣旨は変更なし）
- 1.1.0: 使い方（手順・報告形式・対処・例2件）を追加、ヒューリスティックを 10 件に整備、時限表現を中立化（趣旨は変更なし）
- 1.0.0: 初版
