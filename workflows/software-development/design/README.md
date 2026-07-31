# dev/design/ — デザインシステム

IBM Carbon準拠のデザインシステム。顧客ペルソナ分析からデザイン方針を導出し、一貫性・アクセシビリティ・品質でプロダクトを差別化する。

## ワークフロー

```
1. persona.md で顧客ペルソナ分析（年齢・ニーズ・フラストレーション）
      ↓
2. design-system.md でデザイントークン・コンポーネント定義
      ↓
3. design-guidelines.md でガイドライン適用・品質チェック
```

## ファイル一覧

| ファイル | 説明 |
|---|---|
| [persona.md](persona.md) | 顧客ペルソナ分析 → デザイン決定フレームワーク（必ず最初に実施） |
| [design-system.md](design-system.md) | IBM Carbon準拠デザインシステム（トークン・コンポーネント） |
| [design-guidelines.md](design-guidelines.md) | デザインガイドライン（絵文字禁止・ダークモード・レスポンシブ） |
| [design-research.md](design-research.md) | UXリサーチ・優れたデザイン原則リファレンス |

## 3つの設計原則（IBM Carbon準拠）

1. **Accessibility by Default** — アクセシビリティはすべての基盤。WCAG 2.2 AA準拠を最低基準
2. **No Emoji, Only Icons** — 絵文字禁止。Lucide Icons等のSVGアイコンで代替
3. **Persona-Driven Design** — ペルソナ分析から導出したデザインのみ採用
