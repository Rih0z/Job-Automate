---
name: mcp-server-setup
description: "Adds Serena MCP (semantic codebase analysis via uvx) or a Windows build-server MCP (node-based, for allowed build paths and dev commands) to a project's .mcp.json. Use when the user asks to 'Serena MCPをセットアップして', 'Windowsビルドサーバーmcpを設定して', '.mcp.jsonにMCPサーバーを追加して', or references serena.md / windows-setup.md."
metadata:
  provenance: domain-prompt
---

# MCPツール セットアップ

## Serena MCP（コードベース分析）

.mcp.json に次の内容を追記して。

```json
"serena": {
    "command": "uvx",
    "args": [
      "--from", "git+https://github.com/oraios/serena",
      "serena", "start-mcp-server",
      "--project",
      "このプロジェクトに対応するように修正してください。",
      "--context", "ide-assistant",
      "--log-level", "INFO"
    ]
}
```

`--project` の値は実行対象プロジェクトの絶対パス、または serena が認識できるプロジェクト識別子に置き換えること。

---

## Windows Build Server MCP

.mcp.jsonファイルに次の内容を追記して。

```json
{
  "mcpServers": {
    "windows-build-server": {
      "type": "stdio",
      "command": "node",
      "args": ["./server/src/server.js"],
      "env": {
        "MCP_SERVER_PORT": "8080-8089",
        "ALLOWED_BUILD_PATHS": "C:\\builds\\",
        "ENABLE_DEV_COMMANDS": "true"
      }
    }
  }
}
```

`ALLOWED_BUILD_PATHS` はビルド許可パスに、`./server/src/server.js` は実際の MCP サーバー実装への相対パスに置き換えること。`ENABLE_DEV_COMMANDS` を `true` にすると開発コマンド実行が有効になるため、信頼できる環境でのみ使用する。

### カスタムツール実装時のエラー応答設計

`server.js` 側にカスタムツールを実装する場合、ツールの応答はエージェントにとっての唯一の情報源になる。以下を区別できる構造でエラーを返すこと（フィールド名自体はMCP仕様で固定ではなく、「エージェントが自己修正・判断できる情報を渡す」という設計原則が重要）:

- **エラー種別**: 入力バリデーションエラー（修正して再試行可）/ 権限エラー（エスカレーション要）/ 一時的エラー（タイムアウト等、しばらく待って再試行可）を区別する
- **「本当に失敗した」vs「正常処理したが結果が空」を混同しない**: タイムアウト（`isError: true`）と「該当データなし」（`isError: false` + 空の結果）を同じ形式で返すと、エージェントが「対象が存在しない」という誤った結論を出す
- **リトライ可否 (`isRetryable`) を明示する**: フォーマットエラーはリトライで直るが、権限エラーやデータ不存在はリトライしても無駄

---

## 出典

原文: `workflows/software-development/mcp/serena.md`, `workflows/software-development/mcp/windows-setup.md`。E2Eテスト実行を伴う Playwright MCP のセットアップは `playwright-mcp-e2e-testing` Skill を参照。
