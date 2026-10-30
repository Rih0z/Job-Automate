# 優れたデザインの原則（CSS 例つき）

## 目次
- 1. 人間らしいディテール
- 2. 大胆なタイポグラフィ
- 3. Neo-Brutalism
- 4. デザイントークンシステム
- 5. マイクロインタラクション

## 1. 人間らしいディテール

**特徴**:
- 有機的な形状（完璧な円ではなく、わずかに歪んだ楕円）
- 意図的な不完全性（完璧すぎない配置）

**実装例**:
```css
/* 完璧な円（AI的） */
border-radius: 50%;

/* 有機的な形状（人間的） */
border-radius: 48% 52% 51% 49% / 53% 47% 53% 47%;
```

## 2. 大胆なタイポグラフィ

**特徴**:
- カスタムフォントの組み合わせ（見出し用セリフ + 本文用サンセリフ）
- 特大の見出し（80px〜120px）

**推奨フォントペア**（Inter など広く使われる書体は、見出し側で個性を出す前提の本文用。本文・見出しの両方を汎用書体にしない）:
| 見出し | 本文 | 用途 |
|--------|------|------|
| Playfair Display | Inter | エレガント・プロフェッショナル |
| Poppins | Roboto | モダン・クリーン |
| Montserrat | Open Sans | 汎用性高い |
| Space Grotesk | Inter | テック・開発者向け |

```css
h1 {
  font-family: 'Playfair Display', serif;
  font-size: clamp(3rem, 8vw, 7rem);
  font-weight: 700;
  line-height: 1.1;
}

p {
  font-family: 'Inter', sans-serif;
  font-size: 1.125rem;
  line-height: 1.7;
}
```

## 3. Neo-Brutalism（近年のトレンド）

**特徴**:
- 厚いボーダー（2px〜4px）
- ハイコントラストな色の組み合わせ
- フラットな影（box-shadow: 4px 4px 0 black）

```css
.button {
  border: 3px solid black;
  box-shadow: 4px 4px 0 black;
  background: #FFD700;
  transition: transform 0.1s;
}

.button:hover {
  transform: translate(2px, 2px);
  box-shadow: 2px 2px 0 black;
}
```

## 4. デザイントークンシステム

**目的**: 汎用的なCSS変数ではなく、ブランド固有のトークンを使用

**悪い例（AI的）**:
```css
:root {
  --primary: #0070f3;
  --secondary: #1a1a1a;
  --accent: #ff0080;
}
```

**良い例（人間的）— ペルソナ分析から導出したブランドトークン**:
```css
:root {
  /* Brand Identity — customer-persona-design Skill Phase 4-1 の結果を設定 */
  --brand-dark: #1a1f36;        /* メインテキスト */
  --brand-primary: #0b5fa5;    /* プライマリアクション（例。実値はペルソナ分析で決める） */
  --brand-accent: #ff6b35;     /* CTA、強調 */
  --brand-light: #f4f6f9;      /* 背景 */

  /* Semantic Tokens */
  --color-primary: var(--brand-primary);
  --color-surface: var(--brand-light);
  --color-text: var(--brand-dark);
  --color-accent: var(--brand-accent);

  /* Spacing Scale (8px base) */
  --space-1: 0.25rem; /* 4px */
  --space-2: 0.5rem;  /* 8px */
  --space-4: 1rem;    /* 16px */
  --space-6: 1.5rem;  /* 24px */
  --space-8: 2rem;    /* 32px */

  /* Shadows (Elevation) */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.07);
  --shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
}
```

## 5. マイクロインタラクション

```css
/* Spring Physics (not linear) */
.button {
  transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

/* Stagger Animation for Lists */
.list-item {
  animation: fadeInUp 0.5s ease-out backwards;
  animation-delay: calc(var(--index) * 0.1s);
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
```
