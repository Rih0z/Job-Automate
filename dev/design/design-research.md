# デザインリサーチ — AIっぽくないデザイン・優れたUX

## 目的

AIコーディングで生成されるプロダクトが「AIっぽい」「テンプレート感がある」と感じられないよう、優れたデザイン・UXの原則を体系的にまとめる。

---

## AIっぽいデザインの特徴（避けるべき）

### 視覚的特徴
- **無機質な完璧さ**: 完全に左右対称、機械的に整列されたレイアウト
- **テンプレート感**: どこかで見たようなカードグリッド、予測可能な構造
- **汎用的な色**: Material DesignやBootstrapのデフォルト色をそのまま使用
- **個性の欠如**: 手描き要素、カスタムイラスト、独自のタイポグラフィがない
- **絵文字アイコン多用**: UIに絵文字を頼りすぎ（**全面禁止 — design-guidelines.md参照**）

### UX的特徴
- **予測可能すぎる導線**: 驚きや発見がない
- **機械的な文言**: 「送信」「キャンセル」など最低限の言葉のみ
- **一般的なプレースホルダー**: "Enter your email"など工夫のない文言

---

## 優れたデザインの原則

### 1. 人間らしいディテール

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

### 2. 大胆なタイポグラフィ

**特徴**:
- カスタムフォントの組み合わせ（見出し用セリフ + 本文用サンセリフ）
- 特大の見出し（80px〜120px）

**推奨フォントペア**:
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

### 3. Neo-Brutalism（2026年トレンド）

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

### 4. デザイントークンシステム

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
  /* Brand Identity — persona.md Phase 4-1 の結果を設定 */
  --brand-dark: #1a1f36;        /* メインテキスト */
  --brand-primary: #0066cc;    /* プライマリアクション */
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

### 5. マイクロインタラクション

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

---

## 優れたデザインシステム事例

### 1. IBM Carbon Design System
- **特徴**: 企業向け、包括的、アクセシビリティ重視
- **学べる点**: デザイントークン体系、コンポーネントドキュメント
- **URL**: https://carbondesignsystem.com/

### 2. Radix UI / Shadcn UI
- **特徴**: アクセシビリティファースト、カスタマイズ可能、無スタイル
- **学べる点**: コンポーネントの汎用性、ARIA属性の使い方

### 3. Vercel Design System (Geist)
- **特徴**: ミニマル、モダン、開発者向け
- **学べる点**: タイポグラフィスケール、スペーシングルール

### 4. Tailwind UI
- **特徴**: 実践的、プロダクションレディ、レスポンシブ
- **学べる点**: レイアウトパターン、実用的なコンポーネント

### 5. Polaris (Shopify)
- **特徴**: Eコマース特化、UXガイドライン充実
- **学べる点**: ユーザーフローの設計、エラーハンドリング

---

## UX原則（Jakob Nielsenの10ヒューリスティック）

### 1. システム状態の可視性
ユーザーが今何が起きているかを常に把握できるようにする。
- ローディングインジケーター
- 成功/エラー通知

### 2. システムと現実世界の一致
ユーザーの言語・慣習に従う。
- 技術用語を避け、平易な言葉を使う
- 日本語UIなら日本の文化・慣習に合わせる

### 3. エラー防止
エラーが起きにくい設計にする。
- 制約・バリデーション（入力フォーム）
- 破壊的操作の確認

### 4. 美的ミニマリズム
不要な要素を排除する。
- 1画面1目的
- ホワイトスペースの活用

### 5. エラーからの回復
```
悪い例: 「エラーが発生しました」
良い例: 「メールアドレスの形式が正しくありません。@を含めてください。」
```

---

## アクセシビリティ基準（WCAG 2.2）

### AA基準（必須）

#### 色のコントラスト
- **通常テキスト**: 4.5:1以上
- **大きなテキスト**: 3:1以上（18pt以上 or 14pt太字以上）

#### キーボード操作
```css
/* 明確なフォーカス */
a:focus, button:focus {
  outline: 3px solid var(--color-accent);
  outline-offset: 2px;
}

/* フォーカス非表示禁止 */
/* 悪い例 */
*:focus { outline: none; /* NG! */ }
```

---

## 参考資料

### デザインシステム
- [IBM Carbon Design System](https://carbondesignsystem.com/)
- [Best Design Systems in 2025 | Adham Dannaway](https://www.adhamdannaway.com/blog/design-systems/design-system-examples)

### AIっぽくないデザイン
- [Top Web Design Trends for 2026 | Figma](https://www.figma.com/resource-library/web-design-trends/)
- [20 Top Web Design Trends 2026 | TheeDigital](https://www.theedigital.com/blog/web-design-trends)

### SaaS UX
- [Essential SaaS Design Principles | Index.dev](https://www.index.dev/blog/saas-design-principles-ui-ux)

### Nielsen's Heuristics
- [10 Usability Heuristics | NN/g](https://www.nngroup.com/articles/ten-usability-heuristics/)

### デザイントークン
- [Design Tokens Explained | Contentful](https://www.contentful.com/blog/design-token-system/)
