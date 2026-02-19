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

### すべての開発の起点: three-agent/

**コーディングを含むすべての開発は [`three-agent/`](three-agent/) をベースに進めてください。**

1. `three-agent/leader.md` をリーダーエージェントに設定
2. `three-agent/executor.md` を実行エージェントに設定
3. `three-agent/reviewer.md` をレビューエージェントに設定

### 詳細な実装が必要な場合

特定のタスクで詳細なプロンプトが必要になったら、以下を参照してください：

| やりたいこと | 参照先 |
|---|---|
| バグ修正・機能追加の手順を細かく進めたい | [bugfix/](bugfix/) 1〜6ステップ |
| コードベースの分析・設計文書を作りたい | [architecture/](architecture/) |
| 実装の各フェーズ（要件定義・デプロイ等）を進めたい | [workflow/](workflow/) |
| コーディング規約を参照したい | [rules/coding-principles.md](rules/coding-principles.md) |
| テスト環境を整備したい | [testing/](testing/) |
| Playwright/SerenaなどMCPを使いたい | [mcp/](mcp/) |
