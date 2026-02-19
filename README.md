# Job-Automate プロンプト集

AIを活用した業務自動化・開発効率化のためのプロンプトライブラリ。

## ディレクトリ構成

```
Job-Automate/
├── dev/          開発プロンプト集
├── docs/         ドキュメント生成プロンプト
├── business/     ビジネス・リサーチ
├── content/      コンテンツ制作
└── ops/          運用・管理
```

---

## dev/ — 開発プロンプト集

### dev/three-agent/ — 3エージェント開発システム
| ファイル | 説明 |
|---|---|
| [README.md](dev/three-agent/README.md) | システム概要 |
| [leader.md](dev/three-agent/leader.md) | リーダープロンプト |
| [executor.md](dev/three-agent/executor.md) | 実行プロンプト |
| [reviewer.md](dev/three-agent/reviewer.md) | レビュープロンプト |

### dev/bugfix/ — バグ修正・機能追加
| ファイル | 説明 |
|---|---|
| [1.analyze.md](dev/bugfix/1.analyze.md) | 問題分析 |
| [2.plan.md](dev/bugfix/2.plan.md) | 修正計画 |
| [3.check.md](dev/bugfix/3.check.md) | チェック |
| [4.eval.md](dev/bugfix/4.eval.md) | 評価 |
| [5.do.md](dev/bugfix/5.do.md) | 実行 |
| [6.fin.md](dev/bugfix/6.fin.md) | 完了 |

### dev/architecture/ — アーキテクチャ文書化
| ファイル | 説明 |
|---|---|
| [codebase-analysis.md](dev/architecture/codebase-analysis.md) | コードベース分析 |
| [design.md](dev/architecture/design.md) | アーキテクチャ設計 |
| [docs-update.md](dev/architecture/docs-update.md) | ドキュメント更新 |
| [readme-update.md](dev/architecture/readme-update.md) | README更新 |
| [git-push.md](dev/architecture/git-push.md) | Gitプッシュ |

### dev/workflow/ — 開発フロー各フェーズ
| ファイル | 説明 |
|---|---|
| [init.md](dev/workflow/init.md) | プロジェクト初期化 |
| [requirements.md](dev/workflow/requirements.md) | 要件定義 |
| [implementation-start.md](dev/workflow/implementation-start.md) | 実装開始 |
| [pre-implement.md](dev/workflow/pre-implement.md) | 実装前確認 |
| [implement.md](dev/workflow/implement.md) | 実装 |
| [test.md](dev/workflow/test.md) | テスト実行 |
| [refactor.md](dev/workflow/refactor.md) | リファクタリング |
| [deploy.md](dev/workflow/deploy.md) | デプロイ (Cloudflare Pages) |
| [document.md](dev/workflow/document.md) | ドキュメント更新 |
| [design.md](dev/workflow/design.md) | UI/UXデザイン |
| [uiux.md](dev/workflow/uiux.md) | UIUX設計指針 |
| [prompt-maker.md](dev/workflow/prompt-maker.md) | プロンプト作成 |
| [prompt-importer.md](dev/workflow/prompt-importer.md) | プロンプトインポート |
| [artifact.md](dev/workflow/artifact.md) | アーティファクト生成 |
| [client-server.md](dev/workflow/client-server.md) | クライアント・サーバー構成 |
| [gemini.md](dev/workflow/gemini.md) | Gemini連携 |
| [app-readme.md](dev/workflow/app-readme.md) | アプリREADME更新 |

### dev/rules/ — コーディング規約
| ファイル | 説明 |
|---|---|
| [coding-principles.md](dev/rules/coding-principles.md) | AIコーディング原則 + 汎用コード規則 |

### dev/testing/ — テスト基盤
| ファイル | 説明 |
|---|---|
| [README.md](dev/testing/README.md) | テスト概要 |
| [test-plan.md](dev/testing/test-plan.md) | テスト計画 |
| [jest.config.js](dev/testing/jest.config.js) | Jest設定 |
| [jest.setup.js](dev/testing/jest.setup.js) | Jestセットアップ |
| [custom-reporter.js](dev/testing/custom-reporter.js) | カスタムレポーター |
| [generate-coverage-chart.js](dev/testing/generate-coverage-chart.js) | カバレッジチャート生成 |
| [__tests__/](dev/testing/__tests__/) | テストファイル群 |
| [scripts/](dev/testing/scripts/) | テスト実行スクリプト |
| [document/test-plan.md](dev/testing/document/test-plan.md) | 詳細テスト計画書 |

### dev/mcp/ — MCPツール
| ファイル | 説明 |
|---|---|
| [playwright.md](dev/mcp/playwright.md) | Playwright MCP セットアップ＋テストガイド |
| [serena.md](dev/mcp/serena.md) | Serena MCP |
| [windows-setup.md](dev/mcp/windows-setup.md) | Windows MCP設定 |

---

## docs/ — ドキュメント生成プロンプト

| ファイル | 説明 |
|---|---|
| [business-proposal.md](docs/business-proposal.md) | 事業提案書 |
| [it-proposal.md](docs/it-proposal.md) | IT提案書 |
| [generic-proposal.md](docs/generic-proposal.md) | 汎用提案書 |
| [business-idea.md](docs/business-idea.md) | ビジネスアイデア |
| [specification.md](docs/specification.md) | 仕様書 |

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

## content/ — コンテンツ制作

### スライド生成
| ファイル | 説明 |
|---|---|
| [slides.md](content/slides.md) | HTMLスライド自動生成（汎用版） |
| [slides-pro.md](content/slides-pro.md) | HTMLスライド自動生成（プロフェッショナル版 v4.1） |

### レビュー・品質評価
| ファイル | 説明 |
|---|---|
| [review-slides.md](content/review-slides.md) | スライド品質レビュー（100点評価） |

### その他
| ファイル | 説明 |
|---|---|
| [creative.md](content/creative.md) | クリエイティブ制作 |
| [examples/beer-project-blog.md](content/examples/beer-project-blog.md) | ビールプロジェクトブログ例 |

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
