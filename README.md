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
| プロンプト | レビュー | 説明 |
|---|---|---|
| [slides-pro.md](content/slides-pro.md) | [review-slides.md](content/review-slides.md) | HTMLスライド自動生成 v4.1 |

### その他コンテンツ
| ファイル | 説明 |
|---|---|
| [creative.md](content/creative.md) | クリエイティブ制作 |
| [examples/beer-project-blog.md](content/examples/beer-project-blog.md) | ビールプロジェクトブログ例 |

---

## docs/ — 新規事業・提案書作成

| プロンプト | レビュー | 説明 |
|---|---|---|
| [business-idea.md](docs/business-idea.md) | [review-business-idea.md](docs/review-business-idea.md) | ビジネスアイデア発展 |
| [business-proposal.md](docs/business-proposal.md) | [review-proposal.md](docs/review-proposal.md) | 事業提案書・事業計画書 |
| [it-proposal.md](docs/it-proposal.md) | [review-proposal.md](docs/review-proposal.md) | IT企画書・技術提案書 |
| [generic-proposal.md](docs/generic-proposal.md) | [review-proposal.md](docs/review-proposal.md) | 汎用提案書 |
| [specification.md](docs/specification.md) | — | 技術仕様書 |

---

## business/ — ビジネス・リサーチ

### business/ideas/
| ファイル | 説明 |
|---|---|
| [ai-automation.md](business/ideas/ai-automation.md) | AI自動化ビジネスアイデア |

### business/news/
| ファイル | 説明 |
|---|---|
| [it.md](business/news/it.md) | ITニュース収集 |
| [craft-beer.md](business/news/craft-beer.md) | クラフトビールニュース |
| [trends.md](business/news/trends.md) | トレンドリサーチ |
| [investment.md](business/news/investment.md) | 投資情報 |

### business/seo/
| ファイル | 説明 |
|---|---|
| [base.md](business/seo/base.md) | SEO基盤作成 |
| [trend-keywords.md](business/seo/trend-keywords.md) | SEOトレンドキーワード |

---

## dev/ — 開発プロンプト集

> コーディングを含むすべての開発は [dev/three-agent/](dev/three-agent/) をベースに進めてください。
> リーダー・実行・レビューの3エージェント構成でレビュー機能が内蔵されています。

### dev/three-agent/ — 3エージェント開発システム
| ファイル | 説明 |
|---|---|
| [README.md](dev/three-agent/README.md) | システム概要 |
| [leader.md](dev/three-agent/leader.md) | リーダープロンプト |
| [executor.md](dev/three-agent/executor.md) | 実行プロンプト |
| [reviewer.md](dev/three-agent/reviewer.md) | レビュープロンプト |

### dev/rules/ — コーディング規約
| ファイル | 説明 |
|---|---|
| [coding-principles.md](dev/rules/coding-principles.md) | AIコーディング原則 + 汎用コード規則 |

### dev/mcp/ — MCPツール
| ファイル | 説明 |
|---|---|
| [playwright.md](dev/mcp/playwright.md) | Playwright MCP セットアップ＋テストガイド |
| [serena.md](dev/mcp/serena.md) | Serena MCP |
| [windows-setup.md](dev/mcp/windows-setup.md) | Windows MCP設定 |

---

## ops/ — 運用・管理

### ops/server/
| ファイル | 説明 |
|---|---|
| [automation.md](ops/server/automation.md) | サーバー自動化 |
| [init.md](ops/server/init.md) | サーバー初期設定 |
| [windows-standard.md](ops/server/windows-standard.md) | Windows標準手順 |

### ops/hr/
| ファイル | 説明 |
|---|---|
| [year-end-adjustment.md](ops/hr/year-end-adjustment.md) | 年末調整CSV生成 |

---

## 運営者

[Koki Riho（Rih0z）](https://github.com/Rih0z) — GitHub / Twitter: [@rihobeer2](https://x.com/rihobeer2)
