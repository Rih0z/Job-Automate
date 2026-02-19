# docs/ — 新規事業・提案書作成

ビジネス文書・提案書・仕様書を自動生成するプロンプト集。各プロンプトに対応するレビュープロンプトがあります。

| プロンプト | レビュー | 用途 |
|---|---|---|
| [business-idea.md](business-idea.md) | [review-business-idea.md](review-business-idea.md) | ビジネスアイデア発展 |
| [business-proposal.md](business-proposal.md) | [review-proposal.md](review-proposal.md) | 事業提案書・事業計画書 |
| [it-proposal.md](it-proposal.md) | [review-proposal.md](review-proposal.md) | IT企画書・技術提案書 |
| [generic-proposal.md](generic-proposal.md) | [review-proposal.md](review-proposal.md) | 汎用提案書 |
| [specification.md](specification.md) | — | 技術仕様書 |

## 推奨ワークフロー

```
1. business-idea.md でアイデアを発展させる
       ↓
2. review-business-idea.md でアイデアを評価（S/A判定で次へ）
       ↓
3. business-proposal.md / it-proposal.md で提案書を作成
       ↓
4. review-proposal.md で提案書の品質を評価
```
