.mcp.jsonファイルに次の内容を追記して。

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
