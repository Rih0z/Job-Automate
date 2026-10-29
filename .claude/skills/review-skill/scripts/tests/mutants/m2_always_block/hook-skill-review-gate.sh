#!/usr/bin/env bash
# 変異体 2: 常に block する hook（skill 名も出さず、上限も数えず、SessionStart でも block する）。試験が検出できなければならない誤った実装。
cat >/dev/null 2>&1 || true
echo '{"decision":"block","reason":"always block"}'
exit 0
