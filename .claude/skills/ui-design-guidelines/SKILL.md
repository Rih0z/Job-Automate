---
name: ui-design-guidelines
description: "Applies a strict, anti-'AI slop' UI implementation checklist to new or existing web/app frontends: emoji ban with Lucide Icons replacement, WCAG 2.2 AA accessibility (contrast, focus indicators, touch targets), dark mode implementation, mobile-first responsive breakpoints, and a pre-deploy quality checklist. Use when the user asks to 'デザインガイドラインに従って実装して', 'UIの品質チェックリストを適用して', '絵文字をアイコンに置き換えて', 'ダークモード対応して', 'アクセシビリティ対応して', or references design-guidelines.md."
---

# Design Guidelines

**前提**: 使用前に `customer-persona-design` Skill（顧客ペルソナ分析）でペルソナ分析を完了してください。

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
2. **AI生成カスタムアイコン**（カスタム必要時）— ブランド固有のアイコンをAI生成
3. **ブランドロゴ**（長期）— 独自ロゴシステムの構築

---

## Accessibility — WCAG 2.2 AA準拠

### 必須基準

#### 1. コントラスト比

```css
/* テキスト */
--contrast-normal-text: 4.5:1;    /* 本文 */
--contrast-large-text: 3:1;       /* 18px以上 or 14px太字 */

/* UI要素（WCAG 2.2新基準） */
--contrast-ui-components: 3:1;    /* ボタン、入力欄、アイコン */
--contrast-focus-indicator: 3:1;  /* フォーカス枠 */
```

**実装チェック（参考値 — ペルソナ分析で上書き可）**:
```css
/* ライトモード */
background: #ffffff; color: #1a1f36; /* 12.5:1（AAA準拠） */
background: #0066cc; color: #ffffff; /* 4.6:1（AA準拠） */

/* ダークモード */
background: #0f1117; color: #e4e6eb; /* 12.1:1（AAA準拠） */
background: #3385db; color: #ffffff; /* 5.2:1（AA準拠） */
```

#### 2. Focus Indicators（WCAG 2.2新基準）

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

#### 3. Touch Target Size（WCAG 2.2新基準）

```css
/* 最小44x44px */
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

```css
:root {
  /* Light Mode (デフォルト) */
  --bg-primary: #ffffff;
  --bg-secondary: var(--brand-light);
  --text-primary: var(--brand-dark);
  --text-secondary: #6b7280;
  --border-primary: var(--brand-dark);
  --shadow-color: rgba(26, 31, 54, 1);
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg-primary: #0f1117;
    --bg-secondary: #1a1f36;
    --text-primary: #e4e6eb;
    --text-secondary: #9ca3af;
    --border-primary: var(--brand-primary-light);
    --shadow-color: rgba(51, 133, 219, 0.5);
  }
}

[data-theme='dark'] {
  --bg-primary: #0f1117;
  --bg-secondary: #1a1f36;
  --text-primary: #e4e6eb;
  --text-secondary: #9ca3af;
  --border-primary: var(--brand-primary-light);
  --shadow-color: rgba(51, 133, 219, 0.5);
}
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

# 静的HTML（CDN）
<script src="https://unpkg.com/lucide@latest"></script>
```

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

---

## Brand Identity — ロゴ生成

Lucide Iconsに適切なアイコンがない場合のみ、AIでカスタム生成する。

### プロフェッショナルアイコン生成プロンプト

```
Create a minimalist, professional icon for [TOOL_NAME].
Purpose: [WHAT IT DOES]
Style: Line-art icon, 2px stroke width, no fill, rounded line caps
Colors: Single color (#1a1f36) on transparent background
Composition: Centered, simple geometric shapes, recognizable at small sizes
Technical: 24x24px canvas with 2px padding, clean paths suitable for SVG conversion
Design language: Match Linear/Vercel/Stripe modern SaaS aesthetic
Output: High-contrast, crisp lines, professional feel
```

### ロゴ生成プロンプト（汎用）

```
Create a modern, minimal logo for "[YOUR_COMPANY_NAME]".
Style: Geometric, abstract, professional SaaS branding
Symbol: Abstract letterform combined with relevant symbolism
Colors: Primary [--brand-primary], dark [--brand-dark], on white/transparent background
Composition: Icon-text combination OR standalone logomark
Requirements: Works at small sizes (32px), recognizable in monochrome, timeless not trendy
Reference aesthetic: Linear app logo, Vercel triangle, Stripe stripes - geometric simplicity
Format: Square 1024x1024, centered logo with breathing room
```

### OGP/ソーシャルメディア画像プロンプト

```
Create a professional Open Graph image for [SITE_NAME].
Purpose: Social media sharing preview (Twitter, LinkedIn, Facebook)
Dimensions: Landscape 1200x630 aspect ratio
Content: Site logo/icon (left), tagline "[YOUR_TAGLINE]" (center/right)
Background: Gradient ([--brand-primary] to [--brand-primary-light]), subtle noise texture
Typography: Bold sans-serif, high contrast white text
Style: Modern SaaS aesthetic, clean composition, professional brand
```

---

## Neo-Brutalism Design Language

### 特徴
- **太い黒枠** (4-6px) — `border: 4px solid var(--border-primary)`
- **ドロップシャドウ** (右下オフセット) — `box-shadow: 8px 8px 0 var(--shadow-color)`
- **鮮やかな色** — アクセントカラーを大胆に使用
- **タイポグラフィ重視** — 大きな見出し、明確な階層

### 実装例（Light/Dark対応）

```css
.neo-card {
  background: var(--bg-primary);
  border: 4px solid var(--border-primary);
  box-shadow: 8px 8px 0 var(--shadow-color);
  padding: 2rem;
  transition: transform 0.2s, box-shadow 0.2s;
}

.neo-card:hover {
  transform: translate(-4px, -4px);
  box-shadow: 12px 12px 0 var(--shadow-color);
}

.neo-button {
  background: var(--brand-primary);
  color: white;
  border: 3px solid var(--border-primary);
  padding: 1rem 2rem;
  font-weight: 600;
  box-shadow: 4px 4px 0 var(--border-primary);
  min-width: 44px;
  min-height: 44px;
}
```

---

## 品質チェックリスト（デプロイ前必須）

### アクセシビリティ（WCAG 2.2準拠）
- [ ] テキストコントラスト比が4.5:1以上（本文）、3:1以上（UI要素）
- [ ] フォーカスインジケーターが2px以上、3:1コントラスト
- [ ] タッチターゲットが44x44px以上（モバイル48x48px推奨）
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
- [ ] テーマ設定がlocalStorageに保存されているか

### パフォーマンス
- [ ] Tree-shakingが有効か（使用アイコンのみバンドル）
- [ ] Lighthouse Performanceスコアが90+か
- [ ] Lighthouse Accessibilityスコアが95+か

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
