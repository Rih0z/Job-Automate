---
name: mcp-server-setup
description: "Adds Serena MCP (semantic codebase analysis via uvx) or a Windows build-server MCP (node-based, for allowed build paths and dev commands) to a project's .mcp.json, without overwriting existing entries, and checks that the server is recognized. Use when the user asks to 'Serena MCPをセットアップして', 'Windowsビルドサーバーmcpを設定して', '.mcp.jsonにMCPサーバーを追加して', or references serena.md / windows-setup.md. 使わない場面: Playwright MCP とそれを使う E2E テスト（playwright-mcp-e2e-testing）、MCP サーバー自体の新規実装や既存サーバーの不具合修正。"
allowed-tools: Read Write Edit Glob Bash
metadata:
  provenance: domain-prompt
  version: "1.1"
  updated: "2026-10-30"
---

# MCPツール セットアップ

プロジェクトの `.mcp.json` に Serena MCP または Windows Build Server MCP を追加する。

## 手順

1. **前提の確認**: 追加するサーバーに必要なコマンドが使えるかを確認する。Serena は `uvx`（`uvx --version`）、Windows Build Server は `node`（`node --version`）。無ければ追加を止め、不足しているコマンドをユーザーに伝える。
2. **既存ファイルの確認**: プロジェクトルートの `.mcp.json` を Read する。
   - 無い場合: 下のスニペットを新規ファイルとして作る。
   - ある場合: 編集前に `.mcp.json.bak` へコピーしてバックアップを取り、既存の `mcpServers` に追加するサーバーのエントリだけを足す。同名のエントリがあるときは上書きせず、ユーザーに確認する。
3. **プレースホルダの置換**: スニペット内の置換が必要な値を、実際の値に置き換えてから書き込む（下の各節を参照）。置換前のプレースホルダ文字列を残したまま書き込まない。
4. **JSON の検証**: 書き込み後に `.mcp.json` を Read し、JSON として正しい（カンマ、括弧の閉じ漏れがない）ことを確認する。
5. **認識の確認**: `claude mcp list` を実行するか、Claude Code を再起動して `/mcp` を開き、追加したサーバーが一覧に出て接続済みになるかを確認する。この確認はユーザーの環境でしかできない場合がある。実行できなければ、確認していないことを報告に明記する。

## Serena MCP（コードベース分析）

`mcpServers` の中に次のエントリを追加する。

```json
{
  "mcpServers": {
    "serena": {
      "command": "uvx",
      "args": [
        "--from", "git+https://github.com/oraios/serena",
        "serena", "start-mcp-server",
        "--project", "__PROJECT_ABSOLUTE_PATH__",
        "--context", "ide-assistant",
        "--log-level", "INFO"
      ]
    }
  }
}
```

- `__PROJECT_ABSOLUTE_PATH__` は、解析対象プロジェクトの絶対パス（または serena が認識できるプロジェクト識別子）に置き換える。パスが分からないときは、ユーザーに聞く。推測して入れない。
- 取得元は固定バージョンではなく、取得時点のデフォルトブランチになる。再現性が要る場合は、確認済みのタグ（`git+https://github.com/oraios/serena@タグ名`）に固定する。

## Windows Build Server MCP

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

- `ALLOWED_BUILD_PATHS` はビルドを許可するパスに置き換える。
- `./server/src/server.js` は、実際の MCP サーバー実装への相対パスに置き換える。そのファイルが存在することを Glob で確認する。無ければ追加を止めて報告する。
- `ENABLE_DEV_COMMANDS` を `true` にすると開発コマンドの実行が有効になる。信頼できる環境でのみ `true` にし、それ以外は `false` にする。
- `MCP_SERVER_PORT` は元の手順にある値で、stdio 接続では通常使われない。`server.js` がこの変数を読むか確認し、読まなければ削除してよい。

## 使用例

- 依頼: 「Serena MCP をセットアップして」。`uvx` を確認し、`.mcp.json` が無ければ新規作成、あれば `.bak` を作って `serena` だけを追記する。`--project` に現在のプロジェクトの絶対パスを入れ、`claude mcp list` で確認する。
- 依頼: 「.mcp.json にビルドサーバーを足して」で `windows-build-server` が既にある場合。上書きせず、既存の設定内容を示して置き換えてよいかをユーザーに聞く。

## 失敗時の対処

- `uvx` / `node` が無い: 追加を止め、どのコマンドが無いかを報告する。インストールは、ユーザーの了承を得てから行う。
- Serena の取得に失敗する（git の取得エラー、ネットワーク）: 取得元 URL とエラー文を報告し、`.mcp.json` の変更が残っていれば、`.mcp.json.bak` から元に戻す。
- `/mcp` に出ない、または接続に失敗する: `.mcp.json` の JSON 構文、ファイルの配置場所（プロジェクトルート）、パスの置換漏れを順に確認する。直らなければ `.mcp.json.bak` から元に戻して報告する。
- 元に戻す手順: `.mcp.json.bak` を `.mcp.json` に戻す。新規作成した場合は、作った `.mcp.json` を削除する。

## カスタムツール実装時のエラー応答設計

`server.js` 側にカスタムツールを実装する場合、ツールの応答はエージェントにとっての唯一の情報源になる。以下を区別できる構造でエラーを返すこと（フィールド名自体はMCP仕様で固定ではなく、「エージェントが自己修正・判断できる情報を渡す」という設計原則が重要）:

- **エラー種別**: 入力バリデーションエラー（修正して再試行可）/ 権限エラー（エスカレーション要）/ 一時的エラー（タイムアウト等、しばらく待って再試行可）を区別する
- **「本当に失敗した」vs「正常処理したが結果が空」を混同しない**: タイムアウト（`isError: true`）と「該当データなし」（`isError: false` + 空の結果）を同じ形式で返すと、エージェントが「対象が存在しない」という誤った結論を出す
- **リトライ可否 (`isRetryable`) を明示する**: フォーマットエラーはリトライで直るが、権限エラーやデータ不存在はリトライしても無駄

### カスタムツールの入力スキーマ設計（`inputSchema` の `required`）

エラー応答（出力側）だけでなく、ツールの**入力スキーマ**側も同じ理由で設計を誤りやすい。分類・抽出系のカスタムツールで、あるカテゴリの時だけ意味を持つフィールド（例: `category` が「スパム」の時は本来存在しない `target_demographic`）を `required` に含めると、モデルは値の生成を強制され「一般大衆」のようなそれらしい値を捏造する（ハルシネーション誘発）。該当しない場合に正当に「無い」と表明できるよう、条件付きで適用されるフィールドは `required` から外し nullable / optional にする。詳細は `skill-authoring-guide` の「構造化出力スキーマの設計」参照。

## 報告に含める内容

追加したサーバー名、`.mcp.json` の変更点（追加したエントリ）、バックアップの有無、手順 5 の確認結果（確認した／できなかった）。

## 出典

原文: `workflows/software-development/mcp/serena.md`, `workflows/software-development/mcp/windows-setup.md`。E2Eテスト実行を伴う Playwright MCP のセットアップは `playwright-mcp-e2e-testing` Skill を参照。
