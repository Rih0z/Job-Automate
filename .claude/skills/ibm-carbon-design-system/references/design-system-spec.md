# デザインシステム仕様（自己完結版）

IBM Carbon の「役割（role）でトークンを定義し、コンポーネントを Usage / Style / Code / Accessibility で記述する」構造を土台に、Neo-Brutalist な見た目・Lucide アイコン・Inter + JetBrains Mono を組み合わせた独自仕様。Neo-Brutalist 仕様・Lucide・Inter / JetBrains Mono・ThemeProvider は Carbon 公式の一部ではなく、この仕様が定めるもの。色の値（`--brand-*`）は例であり、ペルソナ分析の結果で置き換える。

## 目次

- 設計原則
- Color Roles
- コントラスト要件
- Typography
- Spacing とレイアウト
- Iconography
- 絵文字を使わない方針
- Dark Mode と ThemeProvider
- Components（Button / Card）
- Loading States
- WCAG 2.2 チェックリスト
- 適用手順とデプロイ前チェック

## 設計原則

1. Accessibility by Default: アクセシビリティを後付けにせず、全コンポーネントに組み込む。WCAG 2.2 AA を最低基準にする。
2. No Emoji, Only Icons: UI の絵文字は環境ごとに見た目が変わり、テンプレート感も出るため、統一したアイコンだけを使う。
3. Brutalist Minimalism: 太い枠線、ずらしたべた塗りの影、はっきりした色で視認性を上げ、装飾を削る。

## Color Roles

色は用途（役割）で名前を付け、Light / Dark で役割ごとに値を切り替える。

```css
:root {
  /* Brand Tokens: ペルソナ分析から導出した値に置き換える */
  --brand-primary: #0066cc;
  --brand-dark: #1a1f36;
  --brand-accent: #ff6b35;
  --brand-light: #f4f6f9;
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
  --color-error: #dc2626;     --color-on-error: #ffffff;
  --color-success: #16a34a;   --color-on-success: #ffffff;
  --color-warning: #ea580c;   --color-on-warning: #ffffff;
}
```

Dark 側は同じ役割名で値だけを差し替える。`@media (prefers-color-scheme: dark) { :root { ... } }` と `[data-theme='dark'] { ... }` の 2 か所に同じ値を書く（OS 設定に従う場合と、手動切り替えの場合）。

| 役割 | Dark の値 |
|---|---|
| `--color-primary` / `--color-secondary` / `--color-outline` | `var(--brand-primary-light)` |
| `--color-on-primary` | `#ffffff` |
| `--color-on-secondary` | `#0f1117` |
| `--color-surface` | `#0f1117` |
| `--color-on-surface` | `#e4e6eb` |
| `--color-surface-variant` | `#1a1f36` |
| `--color-on-surface-variant` | `#9ca3af` |
| `--color-shadow` | `rgba(51, 133, 219, 0.5)` |

## コントラスト要件

| 要素 | 最小比 | 検証方法 |
|---|---|---|
| 通常テキスト（18px 未満） | 4.5:1 | コントラストチェッカー |
| 大型テキスト（18px 以上、または 14px 太字以上） | 3:1 | 同上 |
| UI 要素（ボタン、入力欄）・グラフィック | 3:1 | ブラウザの開発者ツール |
| フォーカスインジケーター | 3:1 | 手動 |

## Typography

- 本文・UI: Inter（フォールバックに `-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`）。可変フォントなら 1 ファイルで 400〜700 を賄える。
- コード: JetBrains Mono（フォールバックに `'Fira Code', 'Courier New', monospace`）。
- フォントが使えない環境では上記フォールバックで代替し、報告に書く。

```css
:root {
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;

  --type-display-large: clamp(3.5rem, 6vw, 5rem);
  --type-display-medium: clamp(3rem, 5vw, 4rem);
  --type-display-small: clamp(2.5rem, 4vw, 3rem);
  --type-headline-large: clamp(2rem, 3.5vw, 2.5rem);
  --type-headline-medium: clamp(1.75rem, 3vw, 2rem);
  --type-headline-small: clamp(1.5rem, 2.5vw, 1.75rem);
  --type-body-large: 1.125rem;
  --type-body-medium: 1rem;
  --type-body-small: 0.875rem;
  --type-label-large: 1rem;
  --type-label-medium: 0.875rem;
  --type-label-small: 0.75rem;

  --leading-tight: 1.2;
  --leading-normal: 1.5;
  --leading-relaxed: 1.75;
}
```

## Spacing とレイアウト

8px グリッド。余白は「16px から 24px へ」のように数値で指定する。

```css
:root {
  --spacing-1: 0.5rem;  --spacing-2: 1rem;    --spacing-3: 1.5rem;
  --spacing-4: 2rem;    --spacing-5: 2.5rem;  --spacing-6: 3rem;
  --spacing-8: 4rem;    --spacing-10: 5rem;   --spacing-12: 6rem;

  --container-sm: 640px;  --container-md: 768px;  --container-lg: 1024px;
  --container-xl: 1280px; --container-2xl: 1536px;
}
```

ブレークポイントはコンテナ幅と同じ 640 / 768 / 1024 / 1280 / 1536px（sm〜2xl）。

## Iconography

Lucide を標準にする（全アイコンが 2px ストロークで統一され、使うものだけをバンドルできる。MIT ライセンス）。導入は `npm install lucide-react`。Lucide が使えない場合は、ストローク幅が統一された別の SVG アイコン集で代替し、理由を報告に書く。

```css
:root {
  --icon-size-sm: 16px;
  --icon-size-md: 24px;   /* 標準 */
  --icon-size-lg: 32px;
  --icon-stroke: 2px;
  --icon-padding-mobile: 12px;   /* 24 + 24 = 48px のタッチ領域 */
  --icon-padding-desktop: 10px;  /* 24 + 20 = 44px */
}
```

装飾だけのアイコンには `aria-hidden="true"`、意味を持つアイコンには `aria-label` を付ける。

## 絵文字を使わない方針

UI の文言・アイコン・ボタンに絵文字を使わず、上のアイコンで代替する。理由は、環境ごとに見た目が変わること、スクリーンリーダーが絵文字の名前を読み上げて意味が伝わりにくいこと、テンプレート感が出ること。代替の優先順は、Lucide、ブランド固有のカスタムアイコン、ロゴ。

## Dark Mode と ThemeProvider

優先順位は、保存済みの選択（localStorage）、OS 設定の順。ダークモードが不要なプロジェクトでは Dark 側の定義と ThemeProvider を入れない。

```tsx
// components/ThemeProvider.tsx
import { createContext, useEffect, useState } from 'react'

type Theme = 'light' | 'dark'
export const ThemeContext = createContext<{ theme: Theme; toggleTheme: () => void }>({
  theme: 'light',
  toggleTheme: () => {},
})

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>('light')

  useEffect(() => {
    const stored = localStorage.getItem('theme') as Theme | null
    const system = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    const initial = stored ?? system
    setTheme(initial)
    document.documentElement.setAttribute('data-theme', initial)
  }, [])

  const toggleTheme = () => {
    const next = theme === 'light' ? 'dark' : 'light'
    setTheme(next)
    document.documentElement.setAttribute('data-theme', next)
    localStorage.setItem('theme', next)
  }

  return <ThemeContext.Provider value={{ theme, toggleTheme }}>{children}</ThemeContext.Provider>
}
```

## Components

### Button

Usage:

| 種別 | 使う場面 | 制限 |
|---|---|---|
| Primary | そのページで最も重要な操作（送信、保存、次へ） | 1 ページに 1 つ |
| Secondary | Primary の補助（キャンセル、戻る） | Primary と並べるときは Primary の右側 |
| Ghost | 破壊的操作（削除、リセット） | 誤クリックを避けるため視覚的な重みを軽くする |

Style（Primary。Secondary / Ghost は背景と枠の色を役割に合わせて変える）:

```css
.button-primary {
  background: var(--color-primary);
  color: var(--color-on-primary);
  border: 3px solid var(--color-outline);
  padding: 0.75rem 1.5rem;
  font-family: var(--font-sans);
  font-size: var(--type-label-large);
  font-weight: 600;
  box-shadow: 4px 4px 0 var(--color-outline);
  min-width: 44px;
  min-height: 44px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}
.button-primary:hover { transform: translate(-2px, -2px); box-shadow: 6px 6px 0 var(--color-outline); }
.button-primary:active { transform: translate(0, 0); box-shadow: 2px 2px 0 var(--color-outline); }
.button-primary:focus-visible { outline: 2px solid var(--color-primary); outline-offset: 2px; }
.button-primary:disabled { opacity: 0.5; cursor: not-allowed; transform: none; box-shadow: 4px 4px 0 var(--color-outline); }
```

Code:

```tsx
// components/Button.tsx
import { ButtonHTMLAttributes, ReactNode } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost'
  children: ReactNode
}

export function Button({ variant = 'primary', children, ...props }: ButtonProps) {
  return <button className={`button-${variant}`} {...props}>{children}</button>
}
```

Accessibility: Tab / Space / Enter で操作できる。フォーカス枠は 2px 以上で 3:1 のコントラスト。タッチ領域は 44x44px 以上（モバイルは 48x48px）。無効状態は `disabled` か `aria-disabled="true"`。ボタンの文言は「こちら」ではなく「フォームを送信」「アカウントを削除」のように結果が分かるものにする。

### Card

```css
.card {
  background: var(--color-surface);
  border: 4px solid var(--color-outline);
  box-shadow: 8px 8px 0 var(--color-shadow);
  padding: var(--spacing-4);
  transition: transform 0.2s, box-shadow 0.2s;
}
.card:hover { transform: translate(-4px, -4px); box-shadow: 12px 12px 0 var(--color-shadow); }
```

```tsx
// components/Card.tsx
import { LucideIcon } from 'lucide-react'
import { ReactNode } from 'react'

interface CardProps { icon?: LucideIcon; title: string; description: string; href?: string; children?: ReactNode }

export function Card({ icon: Icon, title, description, href, children }: CardProps) {
  const Component = href ? 'a' : 'div'
  return (
    <Component className="card" href={href}>
      {Icon && <Icon className="card-icon" size={32} strokeWidth={2} aria-hidden="true" />}
      <h3 className="card-title">{title}</h3>
      <p className="card-description">{description}</p>
      {children}
    </Component>
  )
}
```

## Loading States

スピナーよりスケルトン画面を優先する（読み込み後のレイアウトが先に見えるため）。動きを減らす設定の利用者には、アニメーションを止める。

```css
.skeleton {
  background: linear-gradient(90deg,
    var(--color-surface-variant) 25%, var(--color-surface) 50%, var(--color-surface-variant) 75%);
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s ease-in-out infinite;
}
@keyframes skeleton-loading { from { background-position: 200% 0; } to { background-position: -200% 0; } }
@media (prefers-reduced-motion: reduce) {
  .skeleton { animation: none; background: var(--color-surface-variant); }
}
```

## WCAG 2.2 チェックリスト

レベル A:

- 1.1.1 すべての画像・アイコンに代替テキスト（`alt`, `aria-label`）
- 1.3.1 見出し構造（h1、h2、h3）を正しく使う
- 1.4.1 色だけで情報を伝えない
- 2.1.1 すべての機能をキーボードで操作できる
- 3.1.1 `<html lang="ja">` などで言語を指定する

レベル AA:

- 1.4.3 テキスト 4.5:1、UI 要素 3:1
- 2.4.7 フォーカス時に視覚的なインジケーターを出す
- 2.4.13 フォーカス枠 2px 以上、3:1（WCAG 2.2 の基準）
- 2.5.8 タッチターゲット 44x44px 以上（WCAG 2.2 の基準）

## 適用手順とデプロイ前チェック

1. Phase 1 Foundations: ペルソナ分析の値を `--brand-*` に入れ、トークン CSS（例 `styles/tokens.css`）に上のトークンを定義し、フォントを読み込み、必要なら Dark と Lucide を導入する。
2. Phase 2 Components: Button（3 種）、Input（ラベル・エラー表示・バリデーション）、Card を追加する。
3. Phase 3 検証: axe DevTools などの自動検査、キーボード操作とスクリーンリーダーの手動確認、Lighthouse の Accessibility 95 以上（目標値）を確認する。

デプロイ前に確認する項目:

- 絵文字アイコンが残っていない
- アイコンがすべて同一ライブラリ（2px ストローク）
- Light / Dark の両方で正しく表示される
- モバイル、タブレット、デスクトップで崩れない
- テキストコントラストが 4.5:1 以上
- タッチターゲットが 44x44px 以上
- Lighthouse Performance 90 以上（目標値）

## 参考

- IBM Carbon Design System: https://carbondesignsystem.com/（役割ベースのトークンとコンポーネント記述の構造モデル）
- WCAG 2.2: https://www.w3.org/WAI/WCAG22/quickref/
- Lucide: https://lucide.dev
