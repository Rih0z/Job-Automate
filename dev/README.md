# dev/ — 開発プロンプト集

コーディング・開発に関するプロンプトをまとめたディレクトリ。

## サブディレクトリ

| ディレクトリ | 説明 |
|---|---|
| [three-agent/](three-agent/) | リーダー・実行・レビューの3エージェント開発システム |
| [rules/](rules/) | AIコーディング原則・汎用コード規則 |
| [mcp/](mcp/) | MCPツール（Playwright・Serena・Windows設定） |
| [old/](old/) | 旧プロンプト群（試行錯誤の過程で生まれたもの） |

## 基本的な使い方

### すべての開発の起点: three-agent/

**コーディングを含むすべての開発は [`three-agent/`](three-agent/) をベースに進めてください。**

1. `three-agent/leader.md` をリーダーエージェントに設定
2. `three-agent/executor.md` を実行エージェントに設定
3. `three-agent/reviewer.md` をレビューエージェントに設定
