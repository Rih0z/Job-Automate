# workflows/business-planning/ — 新規事業・提案書作成

業務ワークフロー「事業企画」のハーネス。アイデアの発展から提案書・技術仕様書の完成・品質評価まで一貫して使う。

```
1. business-idea.md でアイデアを対話形式で発展
      ↓
2. review-business-idea.md でS/A/B判定（次に進めるか確認）
      ↓
3. business-proposal.md / it-proposal.md / generic-proposal.md で提案書を作成
      ↓
4. review-proposal.md で提案書の品質を評価
      ↓
5. specification.md で技術仕様書に落とし込む
      ↓
6. review-specification.md で仕様書の品質を評価
```

| プロンプト | レビュー | 用途 |
|---|---|---|
| [business-idea.md](business-idea.md) | [review-business-idea.md](review-business-idea.md) | ひと言のアイデア→対話形式で市場・ペルソナ・収益モデル・競合克服戦略・エンゲージメント設計を整理し事業計画へ発展 |
| [business-proposal.md](business-proposal.md) | [review-proposal.md](review-proposal.md) | ビジネスコンセプト＋チーム情報→事業提案書（ペルソナ・TAM/SAM・競合分析・習慣ループ・リテンション設計含む） |
| [it-proposal.md](it-proposal.md) | [review-proposal.md](review-proposal.md) | IT課題・システム概要→体験価値重視のIT企画書（エンゲージメント設計・モート分析含む） |
| [generic-proposal.md](generic-proposal.md) | [review-proposal.md](review-proposal.md) | 商品・サービス情報→業界問わず使える汎用提案書 |
| [specification.md](specification.md) | [review-specification.md](review-specification.md) | 企画書のmdファイル→開発者が実装できる技術仕様書 |

## ideas/ — AI自動化ビジネスモデル

| ファイル | レビュー | 用途 |
|---|---|---|
| [ideas/ai-automation.md](ideas/ai-automation.md) | [ideas/review-ai-automation.md](ideas/review-ai-automation.md) | 無料ツールで収益化を目指すAI自動化ビジネスを複数案提案させる |

---

[← ワークフロー一覧に戻る](../README.md)
