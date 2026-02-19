# dev/ — 開発プロンプト集

コーディング・開発に関するプロンプトをまとめたディレクトリ。

## サブディレクトリ

| ディレクトリ | 説明 |
|---|---|
| [three-agent/](three-agent/) | リーダー・実行・レビューの3エージェント開発システム |
| [bugfix/](bugfix/) | バグ修正・機能追加の6ステップワークフロー |
| [architecture/](architecture/) | コードベース分析・アーキテクチャ文書化 |
| [workflow/](workflow/) | 開発フロー各フェーズのプロンプト |
| [rules/](rules/) | AIコーディング原則・汎用コード規則 |
| [testing/](testing/) | テスト基盤・Jest設定・テスト計画 |
| [mcp/](mcp/) | MCPツール（Playwright・Serena・Windows設定） |

## 基本的な使い方

新規プロジェクトでは `three-agent/` のシステムをベースに開発を進め、
各フェーズで `workflow/` のプロンプトを参照する。

詳細なバグ修正や機能追加は `bugfix/` の6ステップに従って実施する。
