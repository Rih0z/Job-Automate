---
name: ui-design-guidelines
description: "Applies a strict, anti-'AI slop' UI implementation checklist to new or existing web/app frontends: emoji ban with Lucide Icons replacement, WCAG 2.2 AA accessibility (contrast, focus indicators, touch targets), dark mode implementation, mobile-first responsive breakpoints, and a pre-deploy quality checklist. Use when the user asks to 'デザインガイドラインに従って実装して', 'UIの品質チェックリストを適用して', '絵文字をアイコンに置き換えて', 'ダークモード対応して', 'アクセシビリティ対応して', or references design-guidelines.md. Not for choosing a design system's tokens (use ibm-carbon-design-system), researching why a design looks AI-generated (use avoid-ai-generated-design-look), or persona analysis (use customer-persona-design)."
metadata:
  provenance: domain-prompt
  version: "1.2"
---

# Design Guidelines

**前提**: 使用前に `customer-persona-design` Skill（顧客ペルソナ分析）でペルソナ分析を完了してください。ペルソナが無い小さな修正（絵文字の置換だけ等）では、この前提を省略してよい。

## 使用例

| ユーザーの発言 | 行うこと | 結果 |
|---|---|---|
| 「このページの絵文字をアイコンに置き換えて」 | ソース内の絵文字を検索し、下記マッピング表の Lucide Icon に置換。表に無いものは意味に近いアイコンを選ぶ | 絵文字ゼロ。アイコンは 2px ストローク・16/24/32px |
| 「ダークモード対応して」 | カラー変数を `:root` / `prefers-color-scheme` / `data-theme` の 3 経路で定義し、ThemeToggle を追加 | OS 設定とユーザー選択の両方が効く |
| 「アクセシビリティをチェックして」 | 末尾の品質チェックリストを上から順に確認し、未達項目を修正 | 未達項目ゼロ、または残項目を理由付きで報告 |

### 前提とブランド変数

- 下のコード例が使う CSS 変数はブランド色の変数で、この skill は値を定義しない。値はペルソナ分析（`customer-persona-design`）の結果、または対象プロジェクトの既存のデザイントークンから決める。ペルソナ分析もトークンも無いときは、ユーザーに色を尋ねる。推測で色を決めない。

| 変数 | 意味 |
|---|---|
| `--brand-primary` | 主色（フォーカス枠・塗りボタン等）。ライト・ダーク両方の背景に対して 3:1 以上 |
| `--brand-primary-light` | ダークモードでの主色の明るい版（枠線等） |
| `--brand-dark` | ライトモードの文字・枠線に使う濃色 |
| `--brand-light` | ライトモードの二次背景に使う淡色 |

- このファイルの末尾にある「原文」「関連 Skill」は、元のリポジトリ内の文書を指す。他のリポジトリにコピーして使うときは、`customer-persona-design` などの関連 Skill が無くても、上の変数を自分で決めれば本文の手順は実行できる。

エッジケース: ブランドカラーが白文字で 4.5:1 に届かない場合は、色を濃くするか文字色を変える（コントラストを満たさない配色をそのまま採用しない）。

---

## 絵文字禁止ポリシー（最重要）

**絵文字の使用は全面禁止。SVGアイコン・ロゴで代替する。**

### なぜ絵文字はダメなのか
- **プラットフォーム依存**: iOS/Android/Windowsで見た目が異なる
- **AIっぽさ**: 即座に「テンプレ感」「AI生成感」を与える
- **ブランディング不可**: 色・太さ・デザインをコントロールできない
- **アクセシビリティ**: スクリーンリーダーが「ロケット絵文字」と読み上げる（意味が伝わらない）
- **プロフェッショナル性の欠如**: Linear、Vercel、Stripe等の一流SaaSは絵文字を使わない

### 代替手段
1. **Lucide Icons**（第一選択）— React/Vue/HTMLで使える無料SVGアイコンライブラリ
2. **AI生成カスタムアイコン**（カスタム必要時）— ブランド固有のアイコンをAI生成（プロンプトは [references/brand-identity.md](references/brand-identity.md)）
3. **ブランドロゴ**（長期）— 独自ロゴシステムの構築（同上）

---

## Accessibility — WCAG 2.2 AA準拠

### 必須基準

#### 1. コントラスト比

| 対象 | 最小比 | 備考 |
|---|---|---|
| 本文テキスト | 4.5:1 | AA（WCAG 1.4.3） |
| 大きいテキスト | 3:1 | 24px 以上、または 18.66px 以上の太字（約 18pt / 14pt bold） |
| UI 部品（ボタン枠・入力欄枠・アイコン） | 3:1 | AA（WCAG 1.4.11。2.1 から存在する基準で 2.2 の新規ではない） |
| フォーカス枠 | 3:1 | 隣接色に対して。フォーカス表示の AA 要件は 1.4.11 と 2.4.7 |

**実装チェック（参考値 — ペルソナ分析で上書き可。比は WCAG の相対輝度式で算出）**:
```css
/* ライトモード */
background: #ffffff; color: #1a1f36; /* 16.2:1（AAA） */
background: #0066cc; color: #ffffff; /* 5.6:1（AA） */

/* ダークモード */
background: #0f1117; color: #e4e6eb; /* 15.1:1（AAA） */
background: #1a6fc4; color: #ffffff; /* 5.1:1（AA） */
/* 注意: #3385db に白文字は 3.8:1 で AA 不合格。ダークモードの塗りボタンにそのまま使わない */
```

別の色を使うときは、必ず [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/) 等で比を測ってから採用する。「見た目で十分」で通さない。

#### 2. Focus Indicators

```css
/* 最小2pxアウトライン + 高コントラスト */
*:focus-visible {
  outline: 2px solid var(--brand-primary);
  outline-offset: 2px;
  border-radius: 4px;
}

/* キーボードナビゲーション専用（マウスクリックでは表示しない） */
button:focus:not(:focus-visible) {
  outline: none;
}
```

`--brand-primary` が背景に対して 3:1 を満たすことを、ライト・ダーク両方で確認する。

#### 3. Touch Target Size

WCAG 2.2 の AA 基準（2.5.8）は最小 24x24 CSS px。本 skill は余裕を取り、より厳しい 44x44px（AAA 2.5.5 相当・Apple HIG 準拠）を標準とする。

```css
/* 標準 44x44px */
.icon-button {
  padding: 10px; /* 24px icon + 20px padding = 44px */
  min-width: 44px;
  min-height: 44px;
}

/* モバイルで48x48px推奨 */
@media (max-width: 768px) {
  .icon-button {
    padding: 12px; /* 24px icon + 24px padding = 48px */
    min-width: 48px;
    min-height: 48px;
  }
}
```

---

## Dark Mode — ダークモード実装パターン

### カラーシステム（Light/Dark両対応）

ユーザーが選んだテーマ（`data-theme`）を OS 設定より優先する。OS がダークでもユーザーがライトを選べるよう、`prefers-color-scheme` 側は `data-theme='light'` を除外する。

```css
:root {
  /* Light Mode (デフォルト) */
  --bg-primary: #ffffff;
  --bg-secondary: var(--brand-light);
  --text-primary: var(--brand-dark);
  --text-secondary: #6b7280; /* 白背景で 4.8:1 */
  --border-primary: var(--brand-dark);
  --shadow-color: rgba(26, 31, 54, 1);
}

/* OS がダークで、ユーザーが明示的にライトを選んでいない場合 */
@media (prefers-color-scheme: dark) {
  :root:not([data-theme='light']) {
    --bg-primary: #0f1117;
    --bg-secondary: #1a1f36;
    --text-primary: #e4e6eb;
    --text-secondary: #9ca3af; /* #0f1117 上で 7.4:1 */
    --border-primary: var(--brand-primary-light);
    --shadow-color: rgba(51, 133, 219, 0.5);
  }
}

/* ユーザーが明示的にダークを選んだ場合 */
[data-theme='dark'] {
  --bg-primary: #0f1117;
  --bg-secondary: #1a1f36;
  --text-primary: #e4e6eb;
  --text-secondary: #9ca3af;
  --border-primary: var(--brand-primary-light);
  --shadow-color: rgba(51, 133, 219, 0.5);
}

/* [data-theme='light'] は :root の既定値がそのまま効く（上のメディアクエリが除外するため） */
```

### ダークモードトグル実装

```tsx
// components/ThemeToggle.tsx
import { Moon, Sun } from 'lucide-react'
import { useEffect, useState } from 'react'

export function ThemeToggle() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light')

  useEffect(() => {
    const stored = localStorage.getItem('theme') as 'light' | 'dark' | null
    const system = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    const initial = stored ?? system
    setTheme(initial)
    document.documentElement.setAttribute('data-theme', initial)
  }, [])

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light'
    setTheme(newTheme)
    document.documentElement.setAttribute('data-theme', newTheme)
    localStorage.setItem('theme', newTheme)
  }

  return (
    <button
      onClick={toggleTheme}
      aria-label={`${theme === 'light' ? 'ダーク' : 'ライト'}モードに切り替え`}
      className="icon-button"
    >
      {theme === 'light' ? <Moon size={24} /> : <Sun size={24} />}
    </button>
  )
}
```

SSR / SSG では初回描画でテーマが一瞬ちらつく。気になる場合は、`<head>` に同じ判定を行う小さなインラインスクリプトを置いて描画前に `data-theme` を設定する。

---

## Responsive Design — レスポンシブ実装詳細

### ブレークポイント定義

```css
:root {
  --breakpoint-xs: 320px;   /* モバイル最小 */
  --breakpoint-sm: 640px;   /* モバイル大 */
  --breakpoint-md: 768px;   /* タブレット */
  --breakpoint-lg: 1024px;  /* デスクトップ小 */
  --breakpoint-xl: 1280px;  /* デスクトップ大 */
  --breakpoint-2xl: 1536px; /* ワイドスクリーン */
}
```

注意: CSS 変数は `@media` の条件内では使えない。下の例のように数値を直接書く。この変数は JS 側や文書としての基準値用。

### モバイルファースト設計

```css
/* 基本: モバイル */
.container {
  padding: 1rem;
}

.grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

/* タブレット（768px+） */
@media (min-width: 768px) {
  .container { padding: 2rem; }
  .grid { grid-template-columns: repeat(2, 1fr); gap: 1.5rem; }
}

/* デスクトップ（1024px+） */
@media (min-width: 1024px) {
  .container {
    padding: 3rem;
    max-width: 1280px;
    margin: 0 auto;
  }
  .grid { grid-template-columns: repeat(3, 1fr); gap: 2rem; }
}
```

---

## Iconography — アイコンシステム

### 使用するアイコンライブラリ

**[Lucide Icons](https://lucide.dev)** — すべてのプロダクトで標準採用

```bash
# React/Next.js
npm install lucide-react
```

静的 HTML では CDN の `<script>` を使う。`lucide@latest` のような未固定指定は避け、バージョンを固定する（サプライチェーンと再現性のため）。固定するバージョンは導入時に [Lucide のリリース一覧](https://github.com/lucide-icons/lucide/releases) で確認して決める。

### アイコン実装パターン

```tsx
import { Ruler, Search, Lock, Globe } from 'lucide-react'

// 基本使用
<Ruler size={24} strokeWidth={2} />

// カラー継承（CSS変数から）
<Search size={24} strokeWidth={2} className="icon-primary" />
```

### Icon Component（推奨）

```tsx
// components/Icon.tsx
import { LucideIcon } from 'lucide-react'

interface IconProps {
  icon: LucideIcon
  size?: 'sm' | 'md' | 'lg'
  className?: string
  'aria-label'?: string
}

export function Icon({ icon: IconComponent, size = 'md', className = '', 'aria-label': ariaLabel }: IconProps) {
  const sizeMap = { sm: 16, md: 24, lg: 32 }

  return (
    <IconComponent
      size={sizeMap[size]}
      strokeWidth={2}
      className={className}
      aria-label={ariaLabel}
      role={ariaLabel ? 'img' : 'presentation'}
    />
  )
}
```

### アイコンマッピング例（絵文字 → Lucide Icons）

| 削除する絵文字 | 意味 | Lucide Icon |
|--------------|------|-------------|
| 📐 | 測定・単位 | `Ruler` |
| 🔍 | 検索 | `Search` |
| 🔗 | リンク・接続 | `Link2` |
| 📊 | 分析・グラフ | `BarChart3` |
| 🔐 | セキュリティ | `Lock` |
| 🌐 | URL・国際化 | `Globe` |
| 🎯 | 精密・ターゲット | `Target` |
| 🕐 | 時間 | `Clock` |
| 📝 | テキスト文書 | `FileText` |
| ⚙️ | 設定 | `Settings` |

アイコン名が Lucide に無い（バージョン差でリネームされている）場合は、[lucide.dev](https://lucide.dev) で検索して現行名を使う。

---

## 追加リファレンス（必要なときだけ読む）

- ロゴ・アイコン・OGP 画像を AI 生成するとき → [references/brand-identity.md](references/brand-identity.md)（Lucide に適切なアイコンがない場合のみ）
- Neo-Brutalism（太枠・オフセットシャドウ）で実装するとき → [references/neo-brutalism.md](references/neo-brutalism.md)

---

## 品質チェックリスト（デプロイ前必須）

### アクセシビリティ（WCAG 2.2準拠）
- [ ] テキストコントラスト比が4.5:1以上（本文）、3:1以上（UI要素）。ライト・ダーク両モードで実測した
- [ ] フォーカスインジケーターが2px以上、3:1コントラスト
- [ ] タッチターゲットが44x44px以上（モバイル48x48px推奨。WCAG 2.2 AA の最小は24x24px）
- [ ] キーボードナビゲーション完全対応
- [ ] スクリーンリーダーテスト（macOS VoiceOver/NVDA）
- [ ] `prefers-reduced-motion`に対応

### アイコン実装
- [ ] 絵文字アイコンが残っていないか
- [ ] すべてのアイコンのストローク幅が2pxで統一されているか
- [ ] アイコンサイズがデザイントークンに従っているか（16/24/32px）

### レスポンシブ
- [ ] モバイル（320px-640px）で正しく表示されるか
- [ ] タブレット（768px-1024px）で正しく表示されるか
- [ ] デスクトップ（1024px+）で正しく表示されるか
- [ ] 横スクロールが発生していないか

### ダークモード
- [ ] Light/Dark両モードでコントラスト基準を満たすか
- [ ] システム設定（prefers-color-scheme）に対応しているか
- [ ] OS がダークでも、ユーザーがライトを選ぶとライトになるか
- [ ] テーマ設定がlocalStorageに保存されているか

### パフォーマンス
- [ ] Tree-shakingが有効か（使用アイコンのみバンドル）
- [ ] Lighthouse Performanceスコアが90+か
- [ ] Lighthouse Accessibilityスコアが95+か

### 判定とエラー時の対処
- 全項目にチェックが付いたら完了。付かない項目は、直して再確認するか、理由と残リスクを報告に書く。
- Lighthouse が実行できない環境（ブラウザ無し・CI 制限）では、そのスコア項目を「未測定」と明記し、コントラストは手計算または Contrast Checker で代替する。
- コントラストが足りない色は、ペルソナ分析のブランド色を勝手に変えず、変更案（より濃い色）を提示して承認を得る。

### 結果報告の様式

作業が終わったら、次の見出し構成で報告する（見出し名と順序は固定。該当しない節は「対象外」と書く）。

```
## 適用結果
- 対象: 変更したファイル・画面
- 実施した内容: 絵文字置換 / ダークモード / アクセシビリティ / レスポンシブ のうち行ったもの
## チェックリスト結果
- 達成: 項目数と主な項目
- 未達・未測定: 項目名 / 理由 / 残リスク
## コントラスト実測
| 組み合わせ | 前景 / 背景 | 比 | 判定 |
## 要承認事項
- 色の変更案など、ユーザーの承認が要るもの（無ければ「なし」）
```

報告に含めない: 作業の経緯、変更していない箇所の説明。

---

## 参考資料

- [WCAG 2.2 Guidelines](https://www.w3.org/WAI/WCAG22/quickref/)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Lucide Icons](https://lucide.dev)
- [SVGO](https://github.com/svg/svgo) — SVG最適化
- [IBM Carbon Design System](https://carbondesignsystem.com/)

---

## 出典・関連 Skill

原文: `workflows/software-development/design/design-guidelines.md`。関連: `customer-persona-design`（前提）、`ibm-carbon-design-system`（デザイントークン本体）、`avoid-ai-generated-design-look`（AIっぽさ回避のリサーチ資料）。`/review-implementation` コマンドの評価基準としても参照される。

## 更新履歴

- 1.1 以前: 履歴の記録なし
- 1.2 (2026-10-30): ブランド変数の定義と前提、結果報告の様式を追加
