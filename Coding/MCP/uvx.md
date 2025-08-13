.mcp.json に次の内容を追記して。

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
