# workflows/ — 業務ワークフロー単位のハーネス

このリポジトリは成果物の種類（プレゼン／文書／コード等）ではなく、**業務ワークフロー単位**でプロンプトを束ねる。1つの `workflows/<name>/` フォルダが1つの「ハーネス」であり、次を必ず含む：

| 構成要素 | 内容 |
|---|---|
| `README.md` | そのワークフローの目的・使用プロンプトの順序（作成→レビュー）・関連する `.claude/skills` / `.claude/commands` |
| 作成プロンプト | ゴール・制約・品質基準のみを簡潔に示す `.md`（詳細手順はAIに委ねる設計思想。詳しくは[ルートREADME](../README.md#このプロンプト集の設計思想)） |
| レビュープロンプト | 利用者の実力・チームのノウハウ・失敗経験を凝縮した評価基準（`review-*.md`） |

Claude Code から自動検出される実行可能な Skills（`.claude/skills/`）・Commands（`.claude/commands/`）はリポジトリ直下に置き、各ワークフローの `README.md` からリンクする（Claude Code は `<repo>/.claude/` 配下のみを自動検出するため、ワークフロー配下には置かない）。

## 一覧

| ワークフロー | 目的 |
|---|---|
| [content-creation/](content-creation/README.md) | プレゼン資料・ブログ記事などコンテンツの作成とレビュー |
| [business-planning/](business-planning/README.md) | ビジネスアイデア→提案書→技術仕様書の一連の事業企画 |
| [research-intelligence/](research-intelligence/README.md) | ニュース収集・SEO分析などのリサーチ |
| [software-development/](software-development/README.md) | コーディング・3エージェント開発システム・デザインシステム・Skills品質レビュー |
| [ops-management/](ops-management/README.md) | サーバー運用・HR等の管理業務 |

## 新しいワークフローを追加する手順

1. `workflows/<workflow-name>/` を作成する
2. 作成プロンプト（ゴール・制約・品質基準を簡潔に）を置く
3. 対応するレビュープロンプト（`review-*.md`）をペアで作成する
4. `workflows/<workflow-name>/README.md` に目的・使用順序・関連skills/commandsを書く
5. 本ファイル（`workflows/README.md`）の一覧表と、ルート [README.md](../README.md) に追記する
6. 汎用的に自動判定・自動レビューさせたい場合のみ、リポジトリ直下 `.claude/skills/` or `.claude/commands/` に対応する Skill/Command を追加する（[software-development/README.md](software-development/README.md#claude-code-harness-構築claudeskills) 参照）

---

[← リポジトリ全体に戻る](../README.md)
