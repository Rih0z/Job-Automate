# Brand Identity — ロゴ・アイコン・OGP 画像の生成プロンプト

Lucide Icons に適切なアイコンがない場合のみ、画像生成 AI でカスタム生成する。生成物は SVG 化・最適化（SVGO 等）してから組み込み、`SKILL.md` の品質チェックリスト（アイコン実装の節）で確認する。

## プロフェッショナルアイコン生成プロンプト

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

## ロゴ生成プロンプト（汎用）

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

## OGP/ソーシャルメディア画像プロンプト

```
Create a professional Open Graph image for [SITE_NAME].
Purpose: Social media sharing preview (Twitter, LinkedIn, Facebook)
Dimensions: Landscape 1200x630 aspect ratio
Content: Site logo/icon (left), tagline "[YOUR_TAGLINE]" (center/right)
Background: Gradient ([--brand-primary] to [--brand-primary-light]), subtle noise texture
Typography: Bold sans-serif, high contrast white text
Style: Modern SaaS aesthetic, clean composition, professional brand
```

OGP 画像のグラデーション上の白文字も、本文は 4.5:1 以上を満たすか確認する（グラデーションの最も明るい位置で測る）。
