# Job-Automate プロンプト集

AIを活用した業務自動化・開発効率化のためのプロンプトライブラリ。

---

## このプロンプト集の設計思想

### 作成プロンプトは短く、AIに自由を与える

作成（実行）プロンプトを細かく指示しすぎると、**AIの可能性を狭めて結果を悪化させるリスクがある**。AIは日々進化しており、昨日まで必要だった細かな指示が、今日のモデルでは足かせになることがある。

作成プロンプトでは、**ゴール・制約・品質基準を簡潔に示し、具体的な手順はAIに委ねる**。文字数を削って余白を残すことで、AIがあらゆるアプローチを探索できる状態を作る。これが最良の成果物を引き出す設計原則である。

### レビュープロンプトこそが本質

**本当に価値があるのはレビュープロンプトである。**

レビュープロンプトには以下が凝縮される：

- **利用者の実力と経験** — 何が良い成果物で何がダメかを見分ける目
- **チームのノウハウ** — 過去のプロジェクトで蓄積した判断基準
- **失敗経験** — 「これをやるとこうなる」という痛みから得た知見
- **業界・ドメインの知見** — AI単体では持ち得ない現場の文脈

AIがどれだけ進化しても、**「何を良しとするか」の基準を決めるのは人間**である。作成プロンプトはAIの進化に合わせて陳腐化するが、レビュープロンプトは人間の知見が詰まっているからこそ価値が持続する。

### レビュープロンプトはチームで練り上げる

レビュープロンプトは個人で完結させず、**チームで共有し、議論し、継続的に改善する**べきものである。

```
新しい失敗が起きた → レビュー基準に追加
業界の基準が変わった → 評価軸を更新
メンバーの知見が増えた → チェック項目を洗練
```

このリポジトリのレビュープロンプト群（`review-*.md`）は、そのための共有資産として設計されている。

---

## 対応AIサービス

| カテゴリ | 推奨サービス |
|---|---|
| 全般（docs / business / content / ops） | [Claude](https://claude.ai) / [ChatGPT](https://chatgpt.com) / [Gemini](https://gemini.google.com) |
| リサーチ・ニュース収集（business/news） | [Perplexity](https://www.perplexity.ai) / [Grok](https://grok.com) / [Gemini](https://gemini.google.com) |
| 開発（dev/） | [Claude Code](https://docs.anthropic.com/ja/docs/claude-code/overview) / [Cursor](https://www.cursor.com) / [Cline](https://cline.bot) |

---

## Claude Code スラッシュコマンド

このリポジトリをクローンして Claude Code で開くだけで使えるスキル：

| コマンド | コマンド本体 | 何をするか |
|---------|-------------|-----------|
| `/review-implementation` | [.claude/commands/review-implementation.md](.claude/commands/review-implementation.md) | 実装を5軸（テスト・正確性・マネタイズ・ペルソナ・UX）で100点満点評価 |
| `/review-changes` | [.claude/commands/review-changes.md](.claude/commands/review-changes.md) | 直近の変更差分を4軸（実装正確性・テストカバレッジ・テスト品質/戦略・追跡可能性）で100点満点評価。**別エージェントで実行**し客観性を確保 |
| `/review-skill` | [.claude/commands/review-skill.md](.claude/commands/review-skill.md) | 作成済みSkillsをAnthropicベストプラクティスに基づき5軸（構造・トリガー・命令品質・出力設計・実用性）で100点満点評価 |

> `/review-changes` は実装セッションとは別のエージェントを自動起動してレビューする。詳細は [agents.md](agents.md) 参照。

**他のプロジェクトでもスキルを使いたい場合:**
```bash
mkdir -p ~/.claude/commands
cp .claude/commands/*.md ~/.claude/commands/
```

> 詳細は `CLAUDE.md` を参照。

---

## ルートファイル

| ファイル | 何をするか |
|---|---|
| [CLAUDE.md](CLAUDE.md) | Claude Code 向けリファレンスマニュアル（スキル一覧・追加ルール・プロジェクト構成） |
| [agents.md](agents.md) | エージェント分離アーキテクチャ（レビューの客観性確保・分離ルール・制約と限界） |

## ディレクトリ構成

```
Job-Automate/
├── .claude/commands/  Claude Code スラッシュコマンド（クローンすれば誰でも使える）
├── agents.md          エージェント分離アーキテクチャ
├── content/           プレゼン資料作成・レビュー
├── docs/              新規事業・提案書作成・レビュー基準
├── business/          ビジネス・リサーチ
├── dev/               開発プロンプト集
└── ops/               運用・管理
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
| [business-idea.md](docs/business-idea.md) | [review-business-idea.md](docs/review-business-idea.md) | ひと言のアイデアを話す → 対話形式で市場・ペルソナ・収益モデル・**競合克服戦略・エンゲージメント設計**を整理し事業計画へ発展 |
| [business-proposal.md](docs/business-proposal.md) | [review-proposal.md](docs/review-proposal.md) | ビジネスコンセプト＋チーム情報を入力 → 事業提案書を生成（ペルソナ・TAM/SAM・競合分析・**習慣ループ・リテンション設計**含む） |
| [it-proposal.md](docs/it-proposal.md) | [review-proposal.md](docs/review-proposal.md) | IT課題・システム概要を入力 → 体験価値重視のIT企画書を生成（**エンゲージメント設計・モート分析**含む） |
| [generic-proposal.md](docs/generic-proposal.md) | [review-proposal.md](docs/review-proposal.md) | 商品・サービスの情報を入力 → 業界問わず使える汎用提案書を生成（**エンゲージメント・リテンション設計**含む） |
| [specification.md](docs/specification.md) | [review-specification.md](docs/review-specification.md) | 企画書のmdファイルを渡す → 開発者が実装できる技術仕様書を生成 |

### レビュープロンプトの違い

| ファイル | 対象 | 評価軸（100点満点） |
|---|---|---|
| [review-business-idea.md](docs/review-business-idea.md) | アイデア文書 | **6軸**: 独自性・競合克服戦略(20)／市場性(15)／実現可能性(15)／ペルソナ(15)／**エンゲージメント・リテンション設計(20)**／展開計画(15) |
| [review-proposal.md](docs/review-proposal.md) | 提案書・企画書 | **6軸**: 構成(15)／市場分析・競合克服戦略(20)／ペルソナ適合性(15)／根拠(15)／**エンゲージメント・リテンション設計(20)**／説得力(15) |
| [review-implementation.md](docs/review-implementation.md) | 実装コード | 5軸: テスト品質／処理の正確性／マネタイズ整合性／ペルソナ適合実装／UX品質 |
| [review-changes.md](docs/review-changes.md) | 変更差分 | 4軸: 実装正確性／テストカバレッジ／テスト品質・戦略／追跡可能性 |
| [review-specification.md](docs/review-specification.md) | 技術仕様書 | 5軸: 要件網羅性／アーキテクチャ／API・データ設計／テスト戦略／実装・運用計画 |
| [review-skill.md](docs/review-skill.md) | Skills品質 | 5軸: 構造・命名／トリガー設計／命令品質／出力設計／実用性・保守性 |
| [review-research.md](business/review-research.md) | リサーチ・ニュース・SEO | 5軸: 正確性／網羅性／分析深度／構成／実用性 |
| [review-ai-automation.md](business/ideas/review-ai-automation.md) | AI自動化ビジネスモデル | 6軸: 実現可能性／収益性／自動化／競合モート／エンゲージメント／リスク |
| [review-persona.md](dev/design/review-persona.md) | ペルソナ分析 | 5軸: 具体性／課題深掘り／デザイン整合性／セグメント分類／検証可能性 |
| [review-ops.md](ops/review-ops.md) | 運用スクリプト・サーバー設定 | 5軸: セキュリティ／冪等性／エラーハンドリング／運用性／パフォーマンス |

---

## business/ — ビジネス・リサーチ

### business/ideas/

| ファイル | レビュー | 何をするか |
|---|---|---|
| [ai-automation.md](business/ideas/ai-automation.md) | [review-ai-automation.md](business/ideas/review-ai-automation.md) | 無料ツール（Gemini API・Cloudflare等）で月収10万円を目指すAI自動化ビジネスを10案提案させる |

### business/news/

> レビューは [review-research.md](business/review-research.md) を使用（ニュース・SEO共通）

| ファイル | 何をするか |
|---|---|
| [it.md](business/news/it.md) | ITニュースを収集・要約する |
| [craft-beer.md](business/news/craft-beer.md) | クラフトビール業界のニュースを収集・要約する |
| [trends.md](business/news/trends.md) | 指定分野のトレンドをリサーチする |
| [investment.md](business/news/investment.md) | 投資関連情報を収集・整理する |

### business/seo/

> レビューは [review-research.md](business/review-research.md) を使用（ニュース・SEO共通）

| ファイル | 何をするか |
|---|---|
| [base.md](business/seo/base.md) | サイト・コンテンツのSEO基盤を設計する |
| [trend-keywords.md](business/seo/trend-keywords.md) | 今トレンドのSEOキーワードを収集・分析する |

---

## dev/ — 開発プロンプト集

> **コーディングを含むすべての開発は [dev/three-agent/](dev/three-agent/) から始めてください。**

### Claude Code セットアップ

| ファイル | 何をするか |
|---|---|
| [claude-md.md](dev/claude-md.md) | 任意のプロジェクトに対して Anthropic ベストプラクティス準拠の `CLAUDE.md` を生成する（80行/10KB上限・段階的開示・条文番号方式オプション含む） |

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

| ファイル | レビュー | 何をするか |
|---|---|---|
| [persona.md](dev/design/persona.md) | [review-persona.md](dev/design/review-persona.md) | 顧客の年齢・ニーズ・フラストレーションを分析 → カラー・フォント・UXパターンを決定する（最初に実施） |
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

> レビューは [review-ops.md](ops/review-ops.md) を使用

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
