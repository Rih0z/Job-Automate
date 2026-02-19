# Job-Automate プロンプト集

AIを活用した業務自動化・開発効率化のためのプロンプトライブラリ。

## ディレクトリ構成

```
Job-Automate/
├── content/      プレゼン資料作成・レビュー
├── docs/         新規事業・提案書作成
├── business/     ビジネス・リサーチ
├── dev/          開発プロンプト集
└── ops/          運用・管理
```

---

## content/ — プレゼン資料作成・レビュー

### スライド生成

| プロンプト | レビュー | 何をするか |
|---|---|---|
| [slides-pro.md](content/slides-pro.md) | [review-slides.md](content/review-slides.md) | mdファイルを渡す → ブラウザで動くHTMLスライドを生成（← →キー操作・PDF出力・16:9対応） |

### その他コンテンツ

| ファイル | 何をするか |
|---|---|
| [creative.md](content/creative.md) | ゴンベ顔文字など装飾的なテキストアートを生成する |
| [examples/beer-project-blog.md](content/examples/beer-project-blog.md) | ビールプロジェクトのブログ記事例 |

---

## docs/ — 新規事業・提案書作成

アイデアの発展から提案書完成・品質評価まで一貫して使える。

```
1. business-idea.md でアイデアを対話形式で発展
      ↓
2. review-business-idea.md でS/A/B判定（次に進めるか確認）
      ↓
3. 提案書プロンプトで文書化
      ↓
4. review-proposal.md で品質評価
```

| プロンプト | レビュー | 何をするか |
|---|---|---|
| [business-idea.md](docs/business-idea.md) | [review-business-idea.md](docs/review-business-idea.md) | ひと言のアイデアを話す → 対話形式で市場・ペルソナ・収益モデルを整理し事業計画へ発展 |
| [business-proposal.md](docs/business-proposal.md) | [review-proposal.md](docs/review-proposal.md) | ビジネスコンセプト＋チーム情報を入力 → 事業提案書・事業計画書を生成（ペルソナ・TAM/SAM分析含む） |
| [it-proposal.md](docs/it-proposal.md) | [review-proposal.md](docs/review-proposal.md) | IT課題・システム概要を入力 → 体験価値重視のIT企画書・技術提案書を生成 |
| [generic-proposal.md](docs/generic-proposal.md) | [review-proposal.md](docs/review-proposal.md) | 商品・サービスの情報を入力 → 業界問わず使える汎用提案書を生成 |
| [specification.md](docs/specification.md) | — | 企画書のmdファイルを渡す → 開発者が実装できる技術仕様書を生成 |

### レビュープロンプトの違い

| ファイル | 対象 | 評価軸（5軸・100点満点） |
|---|---|---|
| [review-business-idea.md](docs/review-business-idea.md) | アイデア文書 | 独自性・市場性・実現可能性・ペルソナ明確性・展開計画 |
| [review-proposal.md](docs/review-proposal.md) | 提案書・企画書 | 構成・論理性／市場分析・実現可能性／ペルソナ適合性／根拠の明確性／説得力 |

---

## business/ — ビジネス・リサーチ

### business/ideas/

| ファイル | 何をするか |
|---|---|
| [ai-automation.md](business/ideas/ai-automation.md) | 無料ツール（Gemini API・Cloudflare等）で月収10万円を目指すAI自動化ビジネスを10案提案させる |

### business/news/

| ファイル | 何をするか |
|---|---|
| [it.md](business/news/it.md) | ITニュースを収集・要約する |
| [craft-beer.md](business/news/craft-beer.md) | クラフトビール業界のニュースを収集・要約する |
| [trends.md](business/news/trends.md) | 指定分野のトレンドをリサーチする |
| [investment.md](business/news/investment.md) | 投資関連情報を収集・整理する |

### business/seo/

| ファイル | 何をするか |
|---|---|
| [base.md](business/seo/base.md) | サイト・コンテンツのSEO基盤を設計する |
| [trend-keywords.md](business/seo/trend-keywords.md) | 今トレンドのSEOキーワードを収集・分析する |

---

## dev/ — 開発プロンプト集

> **コーディングを含むすべての開発は [dev/three-agent/](dev/three-agent/) から始めてください。**

### dev/three-agent/ — 3エージェント開発システム

3つのAIセッションを使い分け、TDD（テスト駆動開発）で品質を担保しながら開発する。

| ファイル | 役割 | 何をするか |
|---|---|---|
| [README.md](dev/three-agent/README.md) | — | システム全体の使い方・ロール説明 |
| [leader.md](dev/three-agent/leader.md) | リーダー（ターミナル1） | ゴール設定・テスト方針・タスク分解・次イテレーション指示 |
| [executor.md](dev/three-agent/executor.md) | 実行（ターミナル2） | テスト→実装→リファクタのTDDサイクルを回す |
| [reviewer.md](dev/three-agent/reviewer.md) | レビュー（ターミナル3） | テストと実装の品質評価・改善指示 |

### dev/design/ — デザインシステム（IBM Carbon準拠）

ペルソナ分析からデザイン方針を導出するフレームワーク。

| ファイル | 何をするか |
|---|---|
| [persona.md](dev/design/persona.md) | 顧客の年齢・ニーズ・フラストレーションを分析 → カラー・フォント・UXパターンを決定する（最初に実施） |
| [design-system.md](dev/design/design-system.md) | IBM Carbon準拠のデザイントークン・コンポーネント仕様を参照する |
| [design-guidelines.md](dev/design/design-guidelines.md) | 絵文字禁止・ダークモード・レスポンシブ・品質チェックリストを参照する |
| [design-research.md](dev/design/design-research.md) | 優れたUX原則・AIっぽくないデザイン手法のリファレンス |

### dev/rules/ — コーディング規約

| ファイル | 何をするか |
|---|---|
| [coding-principles.md](dev/rules/coding-principles.md) | AIコーディング時に守るべき規則（過剰実装禁止・セキュリティ・テスト方針など）を参照する |

### dev/mcp/ — MCPツール

| ファイル | 何をするか |
|---|---|
| [playwright.md](dev/mcp/playwright.md) | Playwright MCPのセットアップ手順とE2Eテスト実行方法 |
| [serena.md](dev/mcp/serena.md) | Serena MCP（コードベース分析）のセットアップ手順 |
| [windows-setup.md](dev/mcp/windows-setup.md) | Windows環境でのMCP設定手順 |

---

## ops/ — 運用・管理

### ops/server/

| ファイル | 何をするか |
|---|---|
| [automation.md](ops/server/automation.md) | サーバー作業を自動化するスクリプトを生成する |
| [init.md](ops/server/init.md) | 新規サーバーの初期設定手順を生成する |
| [windows-standard.md](ops/server/windows-standard.md) | Windows環境の標準化手順を生成する |

### ops/hr/

| ファイル | 何をするか |
|---|---|
| [year-end-adjustment.md](ops/hr/year-end-adjustment.md) | 年末調整用のCSVファイルを生成する |

---

## 運営者

[Koki Riho（Rih0z）](https://github.com/Rih0z) — GitHub / Twitter: [@rihobeer2](https://x.com/rihobeer2)
