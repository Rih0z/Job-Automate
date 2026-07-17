# hooks 参考構成・hook script 雛形（cross-platform）

SKILL.md 本体「独自運用: 規約の hooks 化判断」と生成手順 Step 8-3 から参照する。**hooks は「確実に毎回実行したい規律」が実在する時だけ導入する**（単発・並走なしの小規模開発では省略してよい）。各 hook イベントの出力契約（どの stdout が context 注入されるか / `additionalContext` JSON の要否 / `exit 2` の意味 / Stop の連続 block 上限）は **hook 生成直前に hooks reference を WebFetch で確認**する（焼き込まず現行仕様に従う）。

## hooks 化候補の判断基準

次の規律は advisory では見落とされうるため hook 化候補にする（該当する規律が実在する時だけ導入）:

- 同じ動作を毎セッション・毎タスクで漏れなく実行したい（例: session 開始時の中断作業ポインタ通知、関連 docs 読込宣言）
- ファイル命名・配置の規約違反を物理的に防ぎたい（例: handoff ファイル名の検証）
- 重要ファイル（CLAUDE.md / skills / commands）の更新後に必ずレビューを起動したい
- session 終了時に成果物の保存・整理を促したい

## hooks 設計指針

- **OS に応じて shell 実装を選ぶ**。スクリプト本体は `.claude/scripts/` に分離して呼ぶ（settings.json の JSON エスケープを避け、debug しやすくする）。Windows は PowerShell（`pwsh -NoProfile -File <path>` + hook 設定に `"shell": "powershell"` 明示）、Mac / Linux は bash / sh（`bash <path>` + JSON パースは `jq` または `python3 -c ...`）。クロスプラットフォーム配布時は両方の script を用意し、OS 判定で振り分けるか、対象 OS 側の実装のみを生成する
- PreToolUse は `exit 2` + stderr で block。誤 reject を避けるため対象 path を厳密にフィルタする
- 各 script の冒頭で標準入力から event data（JSON）を受け取り、`tool_input.file_path` でフィルタする。PowerShell は `[Console]::In.ReadToEnd() | ConvertFrom-Json`、bash は `input=$(cat); jq -r '.tool_input.file_path' <<<"$input"`（または `python3` で parse）
- エラー抑制は全域上書きせず局所化する（debug ログを潰さない）。PowerShell は各 cmdlet の `-ErrorAction SilentlyContinue`、bash は各コマンド末尾の `2>/dev/null`

## 参考 hook 構成（5 hook 例・すべて任意採用）

| イベント | 用途 | reject/notify |
|---|---|---|
| `SessionStart` | **ポインタと verdict のみ注入**: `.tmp/handoffs/` 最新の**ファイル名** + `issues/processing/*.md` 全 scan（タイトル + handoff ファイル名）+ 並走 4 軸 **verdict**（clean / 痕跡あり）。**本文は注入しない**（汚染防止）。再開対象は user 選択後にその 1 件のみ Read | notify |
| `UserPromptSubmit` | `docs/*.md` 直近 3 ファイルを候補として注入し関連 docs 宣言を促す | notify |
| `PreToolUse(Write)` | `.tmp/handoffs/` への Write 時に命名規約 `[YYYY-MM-DD]-issue-[ID]-[kebab].md` を検証 | reject (`exit 2`) |
| `PostToolUse(Edit\|Write\|MultiEdit)` | CLAUDE.md / `.claude/skills/**` / `.claude/commands/**` 更新時に公式 WebFetch + 別エージェントレビューを促す | notify (additionalContext JSON) |
| `Stop` | 最新 handoff が 1 時間以上未更新なら更新リマインド | notify |

## hooks 監査（定期点検）

- `enabledPlugins` で有効化された plugin と settings.json の hooks フィールドを照合し、**dead hooks**（marketplace 配下にあるが load されていない）と **無駄 hooks**（同じ動作の重複・効果薄）を検出する
- `/hooks` コマンドで現状確認、定期的に運用棚卸し

## settings.json への登録（Step 8-3・採用時のみ）

既存設定がある場合は `hooks` フィールドのみ追記（permissions / model 等は保持）。**OS に応じて shell を選ぶ**。

Windows（PowerShell）の例:

```json
{
  "hooks": {
    "SessionStart": [{ "matcher": "startup|resume|clear|compact",
      "hooks": [{ "type": "command", "shell": "powershell",
        "command": "pwsh -NoProfile -File <scripts>/hook-session-start.ps1" }] }],
    "UserPromptSubmit": [{ "hooks": [{ "type": "command", "shell": "powershell",
      "command": "pwsh -NoProfile -File <scripts>/hook-user-prompt-submit.ps1" }] }],
    "PreToolUse": [{ "matcher": "Write",
      "hooks": [{ "type": "command", "shell": "powershell",
        "command": "pwsh -NoProfile -File <scripts>/hook-pre-tool-use-handoff.ps1" }] }],
    "PostToolUse": [{ "matcher": "Edit|Write|MultiEdit",
      "hooks": [{ "type": "command", "shell": "powershell",
        "command": "pwsh -NoProfile -File <scripts>/hook-post-tool-use.ps1" }] }],
    "Stop": [{ "hooks": [{ "type": "command", "shell": "powershell",
      "command": "pwsh -NoProfile -File <scripts>/hook-stop.ps1" }] }]
  }
}
```

Mac / Linux（bash）の例 — 各 command を bash script 呼び出しに置き換える（`"shell"` 指定は不要・`type: command` はログイン shell で実行される）:

```json
{
  "hooks": {
    "SessionStart": [{ "matcher": "startup|resume|clear|compact",
      "hooks": [{ "type": "command",
        "command": "bash <scripts>/hook-session-start.sh" }] }]
  }
}
```

（他イベントも同様に `bash <scripts>/hook-*.sh` へ置き換える）

## hook scripts（`<scripts>/hook-*` 5 ファイル・対象 OS の言語で生成）

役割は言語共通:

- `hook-session-start` — ポインタ（handoff ファイル名 + `issues/processing/*.md` のタイトル）と並走 4 軸 verdict のみ注入（**本文は Read/注入しない**）。検出時は (a)hold+確認 (b)引継ぎ切替 (c)scope 弁別 (d)handoff 明示を促す。本文は user 選択後にその 1 件のみ Read（PC 再起動復元 + 並走衝突防止 + context 汚染防止）
- `hook-user-prompt-submit` — `docs/*.md` 直近 3 ファイルを context 注入
- `hook-pre-tool-use-handoff` — handoff 命名規約 `[YYYY-MM-DD]-issue-[ID]-[kebab].md` 検証、違反なら `exit 2` + stderr で reject
- `hook-post-tool-use` — CLAUDE.md / `.claude/skills/**` / `.claude/commands/**` 編集時に `hookSpecificOutput.additionalContext` JSON で公式 WebFetch レビュー reminder
- `hook-stop` — 1 時間以上未更新 handoff があれば更新リマインド

各 script 冒頭で標準入力の JSON から `tool_name` / `tool_input.file_path` を取り、エラー抑制は個別コマンド単位で局所化する（PowerShell: `[Console]::In.ReadToEnd() | ConvertFrom-Json` + `-ErrorAction SilentlyContinue` / bash: `input=$(cat)` + `jq` または `python3` で parse + 各コマンド `2>/dev/null`）。
