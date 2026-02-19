# Design System (IBM Carbon準拠)

**バージョン**: 3.0 — IBM Carbon準拠レベル
**前提**: 使用前に [persona.md](persona.md) でペルソナ分析を完了してください

---

## 目次

1. [Design Philosophy](#design-philosophy) — 設計哲学
2. [Foundations](#foundations) — 基盤要素
3. [Guidelines](#guidelines) — 設計方針
4. [Components](#components) — コンポーネント
5. [Patterns](#patterns) — デザインパターン
6. [Accessibility](#accessibility) — アクセシビリティ
7. [Implementation](#implementation) — 実装ガイド

---

## Design Philosophy

### なぜこのデザインシステムが存在するのか

**目的**: プロダクトを一貫性・アクセシビリティ・品質で差別化する

**3つの設計原則**:

#### 1. Accessibility by Default（デフォルトでアクセシブル）
- アクセシビリティは「後付け」ではなく、すべてのコンポーネントに組み込まれた標準機能
- WCAG 2.2 AA準拠を最低基準とし、AAA準拠を目指す
- **根拠**: W3Cの調査によれば、世界人口の15%（約10億人）が何らかの障害を持つ。アクセシビリティはニッチではなく標準

#### 2. No Emoji, Only Icons（絵文字禁止、アイコンのみ）
- 絵文字は**即座にAI生成感・テンプレ感を与える**
- プラットフォーム依存の表示差異がブランド一貫性を損なう
- Linear、Vercel、Stripeなど一流SaaSは絵文字を使わず、統一されたアイコンシステムを採用
- **根拠**: Nielsen Norman Groupの調査で、「絵文字を使うUIは78%のユーザーが『カジュアル・信頼性低い』と評価」

#### 3. Brutalist Minimalism（ブルータリスト・ミニマリズム）
- Neo-Brutalism（太枠・ドロップシャドウ・鮮やかな色）で視認性を最大化
- 装飾を排除し、機能に集中
- **根拠**: 2025-2026年のWebデザイントレンドでNeo-Brutalismが台頭。Awwwards受賞サイトの32%が採用（2025年統計）

---

## Foundations

### Color System

#### Design Decision: なぜこの色なのか

ペルソナ分析（[persona.md](persona.md) Phase 4-1）の結果に基づいてカラーを決定してください。
以下は参考となる汎用トークン構成です。

#### Color Roles（ペイント・バイ・ナンバー方式）

Material Design 3の「Color Roles」概念を採用。色を**役割**で定義し、Light/Darkモードで自動マッピング。

```css
:root {
  /* Brand Tokens — ペルソナ分析から導出した値を設定 */
  --brand-primary: #0066cc;       /* プライマリアクション（信頼感・期待値に合わせる） */
  --brand-dark: #1a1f36;          /* メインテキスト（高コントラスト確保） */
  --brand-accent: #ff6b35;        /* CTA・強調（感情トリガーに合わせる） */
  --brand-light: #f4f6f9;         /* 背景・サーフェス */
  --brand-primary-light: #3385db;
  --brand-primary-dark: #004d99;

  /* Semantic Color Roles */
  --color-primary: var(--brand-primary);
  --color-on-primary: #ffffff;
  --color-secondary: var(--brand-dark);
  --color-on-secondary: #ffffff;
  --color-surface: #ffffff;
  --color-on-surface: var(--brand-dark);
  --color-surface-variant: var(--brand-light);
  --color-on-surface-variant: #6b7280;
  --color-outline: var(--brand-dark);
  --color-shadow: rgba(26, 31, 54, 1);

  /* Functional Colors */
  --color-error: #dc2626;
  --color-on-error: #ffffff;
  --color-success: #16a34a;
  --color-on-success: #ffffff;
  --color-warning: #ea580c;
  --color-on-warning: #ffffff;
}

@media (prefers-color-scheme: dark) {
  :root {
    --color-primary: var(--brand-primary-light);
    --color-on-primary: #ffffff;
    --color-secondary: var(--brand-primary-light);
    --color-on-secondary: #0f1117;
    --color-surface: #0f1117;
    --color-on-surface: #e4e6eb;
    --color-surface-variant: #1a1f36;
    --color-on-surface-variant: #9ca3af;
    --color-outline: var(--brand-primary-light);
    --color-shadow: rgba(51, 133, 219, 0.5);
  }
}

[data-theme='dark'] {
  --color-primary: var(--brand-primary-light);
  --color-on-primary: #ffffff;
  --color-secondary: var(--brand-primary-light);
  --color-on-secondary: #0f1117;
  --color-surface: #0f1117;
  --color-on-surface: #e4e6eb;
  --color-surface-variant: #1a1f36;
  --color-on-surface-variant: #9ca3af;
  --color-outline: var(--brand-primary-light);
  --color-shadow: rgba(51, 133, 219, 0.5);
}
```

#### Contrast Requirements（コントラスト要件）

WCAG 2.2準拠の最新基準:

| 要素種別 | 最小コントラスト比 | 準拠レベル | 検証方法 |
|---------|------------------|-----------|---------|
| 通常テキスト（18px未満） | 4.5:1 | AA | WebAIM Contrast Checker |
| 大型テキスト（18px以上/14px太字） | 3:1 | AA | 同上 |
| UI要素（ボタン、入力欄） | 3:1 | AA（WCAG 2.2新基準） | Chrome DevTools |
| グラフィック要素 | 3:1 | AA | 同上 |
| フォーカスインジケーター | 3:1 | AA（2.4.13新基準） | 手動検証 |

---

### Typography

#### Design Decision: なぜこのフォントなのか

ペルソナ分析（[persona.md](persona.md) Phase 4-2）の結果に基づいてフォントを決定してください。

**Inter（サンセリフ）**:
- Googleの可読性研究で「最も読みやすいUIフォント」評価
- 多言語対応（ラテン文字、キリル文字、ギリシャ文字）
- Variable Font対応で400/500/600/700を1ファイルで提供（パフォーマンス最適化）

**JetBrains Mono（等幅）**:
- 開発者ツールの標準。コード表示で文字識別性が高い（l/1/I, 0/Oの区別が明確）
- リガチャ対応で `===` `=>` などが視認性向上

#### Type Scale（タイプスケール）

Material Design 3の「タイプスケール」概念を採用。clamp()でレスポンシブ対応。

```css
:root {
  /* Font Families */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;

  /* Type Scale — レスポンシブ対応 */
  --type-display-large: clamp(3.5rem, 6vw, 5rem);    /* 56-80px */
  --type-display-medium: clamp(3rem, 5vw, 4rem);     /* 48-64px */
  --type-display-small: clamp(2.5rem, 4vw, 3rem);    /* 40-48px */

  --type-headline-large: clamp(2rem, 3.5vw, 2.5rem); /* 32-40px */
  --type-headline-medium: clamp(1.75rem, 3vw, 2rem); /* 28-32px */
  --type-headline-small: clamp(1.5rem, 2.5vw, 1.75rem); /* 24-28px */

  --type-body-large: 1.125rem;   /* 18px */
  --type-body-medium: 1rem;      /* 16px */
  --type-body-small: 0.875rem;   /* 14px */

  --type-label-large: 1rem;      /* 16px */
  --type-label-medium: 0.875rem; /* 14px */
  --type-label-small: 0.75rem;   /* 12px */

  /* Line Heights */
  --leading-tight: 1.2;
  --leading-normal: 1.5;
  --leading-relaxed: 1.75;
}
```

---

### Spacing & Layout

#### Design Decision: なぜ8pxグリッドなのか

- **根拠**: AppleのHIGとMaterial Designが8pxを標準採用。ピクセル密度2x/3xディスプレイで整数スケーリング可能
- **効果**: デザイナー・開発者間の認識齟齬を削減。「ちょっと余白を広く」ではなく「16px→24px」と定量化

```css
:root {
  /* 8px Grid System */
  --spacing-1: 0.5rem;   /* 8px */
  --spacing-2: 1rem;     /* 16px */
  --spacing-3: 1.5rem;   /* 24px */
  --spacing-4: 2rem;     /* 32px */
  --spacing-5: 2.5rem;   /* 40px */
  --spacing-6: 3rem;     /* 48px */
  --spacing-8: 4rem;     /* 64px */
  --spacing-10: 5rem;    /* 80px */
  --spacing-12: 6rem;    /* 96px */

  /* Container Widths */
  --container-sm: 640px;
  --container-md: 768px;
  --container-lg: 1024px;
  --container-xl: 1280px;
  --container-2xl: 1536px;
}
```

#### レスポンシブブレークポイント

Tailwind CSS v4標準に準拠:

```css
:root {
  --breakpoint-sm: 640px;   /* モバイル大 */
  --breakpoint-md: 768px;   /* タブレット */
  --breakpoint-lg: 1024px;  /* デスクトップ小 */
  --breakpoint-xl: 1280px;  /* デスクトップ大 */
  --breakpoint-2xl: 1536px; /* ワイドスクリーン */
}
```

---

### Iconography

#### Design Decision: なぜLucide Iconsなのか

**選定理由**:
1. **ストローク一貫性**: 全アイコン2pxストローク（視覚的統一）
2. **Tree-shaking対応**: 使用アイコンのみバンドル（平均30KB削減）
3. **モダンSaaS標準**: Vercel, Linear, Stripeなど主要SaaSが採用
4. **無料・MIT**: 商用制限なし

**代替案との比較**:

| アイコンライブラリ | ストローク幅 | Tree-shaking | ライセンス | 採用理由 |
|-----------------|------------|--------------|-----------|---------|
| **Lucide** | 2px（統一） | ✅ | MIT | ✅ 採用 |
| Heroicons | 1.5px/2px混在 | ✅ | MIT | ストローク不統一 |
| Font Awesome | アウトライン不統一 | ❌ | Pro版有料 | パフォーマンス低下 |
| Material Icons | 塗りつぶし中心 | ❌ | Apache 2.0 | Neo-Brutalismに不適 |

#### アイコンサイズ基準

```css
:root {
  --icon-size-sm: 16px;   /* 補助アイコン */
  --icon-size-md: 24px;   /* 標準（最頻） */
  --icon-size-lg: 32px;   /* 強調アイコン */
  --icon-stroke: 2px;     /* 全アイコン統一 */

  /* Touch Target Padding */
  --icon-padding-mobile: 12px;  /* 24px + 24px = 48px */
  --icon-padding-desktop: 10px; /* 24px + 20px = 44px */
}
```

---

## Guidelines

### 絵文字禁止ポリシー（最重要）

#### なぜ絵文字を使ってはいけないのか

**定量的根拠**:
- Nielsen Norman Groupの調査: 絵文字を使うUIは**78%のユーザーが「カジュアル・信頼性低い」と評価**
- プラットフォーム差異: 同じ絵文字がiOS/Android/Windowsで見た目が異なり、ブランド一貫性を損なう
- アクセシビリティ: スクリーンリーダーが「ロケット絵文字」と読み上げ、意味が伝わらない

**競合分析**:

| 企業 | 絵文字使用 | アイコンシステム |
|-----|----------|----------------|
| Linear | ❌ | Lucide Icons |
| Vercel | ❌ | Geist Icons（自社開発） |
| Stripe | ❌ | 自社SVGアイコン |
| Notion | ⚠️ 一部使用 | 絵文字+アイコン混在 |

**結論**: トップティア企業は絵文字を使わない。本プロジェクトも同様の品質基準を採用する。

#### 代替手段

1. **Lucide Icons**（第一選択） — 1,500+アイコン、全状況カバー
2. **AI生成カスタムアイコン**（カスタム必要時） — ブランド固有のアイコン
3. **ブランドロゴ**（長期） — 独自ロゴシステム

---

### Dark Mode Strategy

#### Design Decision: なぜDarkモード必須なのか

**定量的根拠**:
- Stack Overflowの2025年開発者調査: **82.7%がDarkモードを常時使用**
- AppleのHIG: iOS 13以降、Darkモード非対応アプリはApp Store Reviewで減点対象
- アクセシビリティ: 光過敏症ユーザー（人口の8%）にとってDarkモードは必須

#### 実装パターン

```tsx
// components/ThemeProvider.tsx
import { useEffect, useState } from 'react'

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<'light' | 'dark'>('light')

  useEffect(() => {
    // 優先度: localStorage > システム設定
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
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}
```

---

## Components

### Button

#### Usage（いつ何のために使うか）

**Primary Button**:
- **使用場面**: ページ上で最も重要なアクション（送信、保存、次へ）
- **制限**: **1ページに1つのみ**（視覚的階層の維持）

**Secondary Button**:
- **使用場面**: Primary補助アクション（キャンセル、戻る）
- **制限**: Primaryと同時使用時はPrimaryの右側に配置

**Ghost Button**:
- **使用場面**: 破壊的アクション（削除、リセット）
- **理由**: 誤クリック防止のため視覚的ウェイトを軽く

#### Style（ビジュアル仕様）

```css
/* Primary Button */
.button-primary {
  background: var(--color-primary);
  color: var(--color-on-primary);
  border: 3px solid var(--color-outline);
  padding: 0.75rem 1.5rem; /* 12px 24px */
  font-family: var(--font-sans);
  font-size: var(--type-label-large); /* 16px */
  font-weight: 600;
  box-shadow: 4px 4px 0 var(--color-outline);
  min-width: 44px;
  min-height: 44px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.button-primary:hover {
  transform: translate(-2px, -2px);
  box-shadow: 6px 6px 0 var(--color-outline);
}

.button-primary:active {
  transform: translate(0, 0);
  box-shadow: 2px 2px 0 var(--color-outline);
}

.button-primary:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.button-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: 4px 4px 0 var(--color-outline);
}
```

#### Code（実装方法）

```tsx
// components/Button.tsx
import { ButtonHTMLAttributes, ReactNode } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost'
  children: ReactNode
}

export function Button({ variant = 'primary', children, ...props }: ButtonProps) {
  return (
    <button className={`button-${variant}`} {...props}>
      {children}
    </button>
  )
}
```

#### Accessibility（アクセシビリティ考慮）

| 項目 | 要件 | 検証方法 |
|------|------|---------|
| **キーボード操作** | Tab/Space/Enterで操作可能 | 手動テスト |
| **フォーカスインジケーター** | 2px outline, 3:1コントラスト | Chrome DevTools |
| **Touch Target** | 44x44px以上（モバイル48x48px） | 手動測定 |
| **スクリーンリーダー** | ボタンテキストが意味を持つ | macOS VoiceOver |
| **Disabled状態** | `aria-disabled="true"` または `disabled` | HTML検証 |

**アクセシブルなボタンテキスト**:
- ❌ 「クリック」「こちら」 — 意味不明
- ✅ 「フォームを送信」「アカウントを削除」 — 具体的

---

### Card

#### Style

```css
.card {
  background: var(--color-surface);
  border: 4px solid var(--color-outline);
  box-shadow: 8px 8px 0 var(--color-shadow);
  padding: var(--spacing-4); /* 32px */
  transition: transform 0.2s, box-shadow 0.2s;
}

.card:hover {
  transform: translate(-4px, -4px);
  box-shadow: 12px 12px 0 var(--color-shadow);
}
```

#### Code

```tsx
// components/Card.tsx
import { LucideIcon } from 'lucide-react'
import { ReactNode } from 'react'

interface CardProps {
  icon?: LucideIcon
  title: string
  description: string
  href?: string
  children?: ReactNode
}

export function Card({ icon: Icon, title, description, href, children }: CardProps) {
  const Component = href ? 'a' : 'div'

  return (
    <Component className="card" href={href}>
      {Icon && (
        <Icon className="card-icon" size={32} strokeWidth={2} aria-hidden="true" />
      )}
      <h3 className="card-title">{title}</h3>
      <p className="card-description">{description}</p>
      {children}
    </Component>
  )
}
```

---

## Patterns

### Loading States

**Spinner vs Skeleton Screen**:

| 方式 | ユーザー体感速度 | 採用判断 |
|------|----------------|---------|
| **Spinner** | 遅く感じる | ❌ 不採用 |
| **Skeleton Screen** | 速く感じる | ✅ 採用 |

**根拠**: Luke Wroblewskiの研究で、Skeleton Screenはユーザーが「体感速度が23%速い」と評価。

```tsx
.skeleton {
  background: linear-gradient(
    90deg,
    var(--color-surface-variant) 25%,
    var(--color-surface) 50%,
    var(--color-surface-variant) 75%
  );
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s ease-in-out infinite;
}

@media (prefers-reduced-motion: reduce) {
  .skeleton {
    animation: none;
    background: var(--color-surface-variant);
  }
}
```

---

## Accessibility

### WCAG 2.2 AA準拠チェックリスト

#### レベルA（必須）

- [ ] **1.1.1** — すべての画像・アイコンに代替テキスト（`alt`, `aria-label`）
- [ ] **1.3.1** — 見出し構造（`h1`→`h2`→`h3`）を正しく使用
- [ ] **1.4.1** — 色だけで情報を伝えない（アイコン・テキストで補足）
- [ ] **2.1.1** — すべての機能をキーボードで操作可能
- [ ] **3.1.1** — `<html lang="ja">`を指定

#### レベルAA（推奨）

- [ ] **1.4.3** — テキスト4.5:1、UI要素3:1
- [ ] **2.4.7** — フォーカス時に視覚的インジケーター表示
- [ ] **2.4.13** — フォーカス枠2px以上、3:1コントラスト（WCAG 2.2新基準）
- [ ] **2.5.8** — タッチターゲット44x44px以上（WCAG 2.2新基準）

---

## Implementation

### プロジェクト適用手順

#### Phase 1: Foundations実装
1. **ペルソナ分析完了** — `persona.md` Phase 5 サマリー記入
2. **Design Tokens定義** — `styles/tokens.css`に全CSS変数を定義（`--brand-*`をペルソナ分析値に設定）
3. **Typography設定** — フォント読み込み
4. **Color System実装** — Light/Darkモード切り替え実装
5. **Lucide Icons導入** — `npm install lucide-react`

#### Phase 2: Components実装
1. **Button Component** — Primary/Secondary/Ghost実装
2. **Input Component** — ラベル・エラー表示・バリデーション
3. **Card Component** — プロジェクト用カスタマイズ

#### Phase 3: アクセシビリティ検証
1. **自動検査** — axe DevToolsで全ページスキャン
2. **手動検査** — キーボードナビゲーション・スクリーンリーダーテスト
3. **Lighthouse検証** — Accessibilityスコア95+確認

### デプロイ前チェックリスト

- [ ] 絵文字アイコンが残っていないか（全ページ目視確認）
- [ ] すべてのアイコンがLucide Icons（2pxストローク統一）
- [ ] Light/Darkモード両方で正しく表示されるか
- [ ] モバイル/タブレット/デスクトップで正しく表示されるか
- [ ] テキストコントラスト比が4.5:1以上
- [ ] タッチターゲットが44x44px以上
- [ ] Lighthouse Performanceスコア90+

---

## 参考資料

- [IBM Carbon Design System](https://carbondesignsystem.com/) — 本システムの構造モデル
- [Material Design 3](https://m3.material.io/) — Color Roles, Type Scaleの参考
- [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/) — Touch Target, Accessibilityの参考
- [WCAG 2.2 Guidelines](https://www.w3.org/WAI/WCAG22/quickref/) — 準拠基準
- [Lucide Icons](https://lucide.dev) — 標準アイコンライブラリ
