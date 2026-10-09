# hooks 参考構成・hook script 雛形（cross-platform）

> provenance: official-derived · id: hooks-promotion-judgement（「hooks 化候補の判断基準」「hooks 設計指針」「hooks 監査」の各節）
> provenance: author-preference · id: hooks-reference-set（「参考 hook 構成（6 hook）」「settings.json への登録」「hook scripts」「外部規約のキャッシュ運用」の各節。Step 0 で選択された時のみ生成。個々の hook はさらに `session-restore-hook` / `handoff-management` 等の要素に依存するので、非選択要素に対応する hook は生成しない）

## 目次

- [hooks 化候補の判断基準](#hooks-化候補の判断基準) / [hooks 設計指針](#hooks-設計指針) / [hooks のセキュリティと信頼](#hooks-のセキュリティと信頼)
- [出力の使い分け（通知・継続・block）](#出力の使い分け通知継続block)
- [参考 hook 構成](#参考-hook-構成6-hook-例すべて任意採用) / [外部規約のキャッシュ運用](#外部規約のキャッシュ運用任意posttooluse-レビュー系-hook-向け) / [hooks 監査](#hooks-監査定期点検)
- [settings.json への登録](#settingsjson-への登録step-8-3採用時のみ) / [hook scripts](#hook-scripts)

SKILL.md 本体「独自運用: 規約の hooks 化判断」と生成手順 Step 8-3 から参照する。**hooks は「確実に毎回実行したい規律」が実在する時だけ導入する**（単発・並走なしの小規模開発では省略してよい）。各 hook イベントの出力契約（どの stdout が context 注入されるか / `additionalContext` JSON の要否 / `systemMessage` / `exit 2` の意味 / Stop の連続 block 上限）は **hook 生成直前に hooks reference を WebFetch で確認**する（焼き込まず現行仕様に従う）。

## hooks 化候補の判断基準

次の規律は advisory では見落とされうるため hook 化候補にする（該当する規律が実在する時だけ導入）:

- 同じ動作を毎セッション・毎タスクで漏れなく実行したい（例: session 開始時の中断作業ポインタ通知、関連 docs 読込宣言）
- ファイル命名・配置の規約違反を物理的に防ぎたい（例: handoff ファイル名の検証）
- 重要ファイル（CLAUDE.md / skills / commands）の更新後に必ずレビューを起動したい
- session 終了時に成果物の保存・整理を促したい

## hooks 設計指針

- **OS に応じて shell 実装を選ぶ**。スクリプト本体は `.claude/scripts/` に分離して呼ぶ（settings.json の JSON エスケープを避け、debug しやすくする）。Windows は PowerShell（`pwsh -NoProfile -File <path>` + hook 設定に `"shell": "powershell"` 明示）、Mac / Linux は bash / sh（`bash <path>` + JSON パースは `jq` または `python3 -c ...`）。クロスプラットフォーム配布時は両方の script を用意し、OS 判定で振り分けるか、対象 OS 側の実装のみを生成する
- PreToolUse は `exit 2` + stderr で block。誤 reject を避けるため対象 path を厳密にフィルタする
- スクリプトは**絶対パス**で呼ぶ。shell form（`args` 無し）では `"$CLAUDE_PROJECT_DIR"/.claude/scripts/...` のように二重引用符で囲み、exec form（`args` あり）では `${CLAUDE_PROJECT_DIR}` を引用せずに使う。shell form の実行 shell は macOS/Linux が `sh -c`、Windows が Git Bash（無ければ PowerShell）で、どれも**非対話 shell**（ログイン shell ではない）。`"shell"` フィールドで明示できる。Windows の exec form は `.exe` を要し、`bash` が WSL の `System32\bash.exe` に解決される環境があるので、Git Bash を前提にするなら shell form が無難
- 外部プロセス（python / node / pwsh 等）を起動する hook には `"timeout"`（秒）を付ける。既定は 600 秒（UserPromptSubmit は 30 秒）で、起動がハングすると最悪その時間止まる
- JSON を返す shell form の hook は、shell profile（`.bashrc` 等）の無条件 `echo` が stdout の先頭に混ざると JSON として解釈されなくなる。profile 側を対話時のみに限定するか、exec form を使う
- 各 script の冒頭で標準入力から event data（JSON）を受け取り、`tool_input.file_path` でフィルタする。PowerShell は `[Console]::In.ReadToEnd() | ConvertFrom-Json`、bash は `input=$(cat); jq -r '.tool_input.file_path' <<<"$input"`（または `python3` で parse）
- エラー抑制は全域上書きせず局所化する（debug ログを潰さない）。PowerShell は各 cmdlet の `-ErrorAction SilentlyContinue`、bash は各コマンド末尾の `2>/dev/null`
- **reject 分岐は実際に reject を return/exit しているかをコードレベルで確認する**（CLI hook script は `exit 2` の有無、SDK ベースの custom hook 関数は deny の戻り値を実際に `return` しているかを確認する）。`if` ブロック内に `print`/ログ出力はあるが実際の reject を return し忘れ、ブロック外の末尾で空の許可応答（`exit 0` 相当 / 空オブジェクト等）に到達すると、ログ上は判定が動いているように見えても実際は素通りする。生成した hook をレビューする際は「ログの文言」ではなく「reject 経路が本当に return/exit されているか」を確認する

## hooks のセキュリティと信頼

公式 hooks reference の Security best practices を生成する hook すべてに適用する（現行の項目は生成直前に WebFetch で確認。観点の構造化データは `.claude/skills/_shared/anthropic-best-practices.json` の `hooks.security-best-practices` / `hooks.workspace-trust`）:

- 入力（stdin の JSON）を検証・無害化してから使う。shell 変数は必ず `"$VAR"` で引用する
- ファイルパスに `..` があれば拒否する（path traversal）
- `.env`・`.git/`・鍵ファイル等の機密ファイルを読まない・書かない
- 対話セッションでは workspace trust ダイアログの承認まで settings の hook は実行されない。`-p` / SDK 実行ではダイアログが出ず、リポジトリにコミットされた hook がそのまま走る。clone して使うハーネスは、同梱 hook が何をするかを README に明記する

## 出力の使い分け（通知・継続・block）

| 目的 | 出力 | 注意 |
|---|---|---|
| ユーザーに知らせるだけ（警告・上限到達・依存欠落） | stdout に JSON `{"systemMessage": "..."}`、exit 0 | exit 0 の stderr は debug log にしか行かず、ユーザーにも Claude にも見えない |
| Claude の context に情報を足す | SessionStart / UserPromptSubmit は plain stdout または `hookSpecificOutput.additionalContext`、PostToolUse は `hookSpecificOutput.additionalContext` | イベントごとに扱いが違うので WebFetch で確認 |
| Stop で作業を続けさせる | `{"decision": "block", "reason": "..."}`（エラー表示）または `hookSpecificOutput.additionalContext`（フィードバック表示） | どちらも会話が継続する。「通知だけ」のつもりで使わない。入力の `stop_hook_active` を読み、自前のカウンタは新しい turn（`stop_hook_active=false`）でリセットする |
| 操作を止める | PreToolUse は `exit 2` + stderr または `permissionDecision: "deny"` | Claude Code 自体の連続 block 上限（Stop は進展なしで 8 回）がある |

## 参考 hook 構成（6 hook 例・すべて任意採用）

| イベント | 用途 | reject/notify |
|---|---|---|
| `SessionStart` | **ポインタと verdict のみ注入**: `.tmp/handoffs/` 最新の**ファイル名** + `issues/processing/*.md` 全 scan（タイトル + handoff ファイル名）+ 並走 4 軸 **verdict**（clean / 痕跡あり）+ 作業中マーカー（`work_status: in_progress`）が閾値（既定 4h）超で残る handoff の**ファイル名**（中断の疑い）。**本文は注入しない**（汚染防止）。再開対象は user 選択後にその 1 件のみ Read | notify |
| `UserPromptSubmit` | `docs/*.md` 直近 3 ファイルを候補として注入し関連 docs 宣言を促す | notify |
| `PreToolUse(Write)` | `.tmp/handoffs/` への Write 時に命名規約 `[YYYY-MM-DD]-issue-[ID]-[kebab].md` を検証 | reject (`exit 2`) |
| `PostToolUse(Edit\|Write\|MultiEdit)` | CLAUDE.md / `.claude/skills/**` / `.claude/commands/**` 更新時に公式 WebFetch + 別エージェントレビューを促す | notify (additionalContext JSON) |
| `PostToolUse(Edit\|Write\|MultiEdit)`（派生成果物の自動再生成） | 監視対象ファイル（例: CLAUDE.md）の編集を検知し、そこから派生する成果物（生成 README / 目次 / 索引等）を **advisory reminder ではなく hook 自身が再生成する**。複数 generator を実行する場合は各 exit code を実行直後に退避し OR 結合する（後発の成功が先発の失敗を隠さないようにする） | notify（再生成結果 or 失敗詳細を additionalContext に含める） |
| `Stop` | 最新 handoff が 1 時間以上未更新なら更新リマインド。未 commit の handoff があれば終了を block して commit + push を促す | notify / block |

## 外部規約のキャッシュ運用（任意・PostToolUse レビュー系 hook 向け）

`PostToolUse` の公式 WebFetch レビュー hook は毎回 WebFetch する運用が基本（本 SKILL.md「公式準拠の核」参照・焼き込み禁止）。ただし hook 発火頻度が高く WebFetch コストが無視できない場合、または offline/低帯域環境向けに配布する場合は、以下条件を **すべて満たす時のみ** キャッシュ運用へ切替えてよい:

1. 参照元 URL から一度だけ WebFetch し、判定基準を構造化データ（JSON 等）として保存する
2. 保存データに **取得日** (`fetched` 等のフィールド) を必ず記録する
3. **再取得トリガー条件**（例: レビューで基準の陳腐化が疑われた時 / 定期棚卸し時）を保存データ自体に明記する
4. hook はこの保存データを読み込み判定基準を注入するのみとし、判定基準の生成・改変は行わない（焼き込み＝無断で古い基準を恒久化することの禁止であり、日付付き・再取得条件付きキャッシュはこれに該当しない）

**一般原則（本項に限らず適用）**: script / hook が確実にパースする必要があるデータ、または他ツールが機械チェックする対象になるデータ（判定基準・設定値・チェックリスト等）は、自由記述の散文に埋め込まず、フィールドが明示された構造化データ（JSON / YAML 等）として定義する。散文は人間が読んで解釈するには向くが、script が確実に取り出せる保証がない。

この運用は「毎回 WebFetch」と「一度焼き込んで放置」の中間案であり、**取得日と再取得条件が欠けたキャッシュは焼き込み禁止違反として扱う**。

## hooks 監査（定期点検）

- `enabledPlugins` で有効化された plugin と settings.json の hooks フィールドを照合し、**dead hooks**（marketplace 配下にあるが load されていない）と **無駄 hooks**（同じ動作の重複・効果薄）を検出する
- `/hooks` コマンドで現状確認、定期的に運用棚卸し

## settings.json への登録（Step 8-3・採用時のみ）

既存設定がある場合は `hooks` フィールドのみ追記（既存の permissions / model 等は保持）。先頭に `"$schema": "https://json.schemastore.org/claude-code-settings.json"` を置く（補完と検証が効く）。**OS に応じて shell を選ぶ**。スクリプトは `$CLAUDE_PROJECT_DIR` 起点の絶対パスで呼ぶ。

Windows（PowerShell）の例:

```json
{
  "hooks": {
    "SessionStart": [{ "matcher": "startup|resume|clear|compact|fork",
      "hooks": [{ "type": "command", "shell": "powershell", "timeout": 30,
        "command": "pwsh -NoProfile -File \"$env:CLAUDE_PROJECT_DIR/.claude/scripts/hook-session-start.ps1\"" }] }],
    "UserPromptSubmit": [{ "hooks": [{ "type": "command", "shell": "powershell", "timeout": 20,
      "command": "pwsh -NoProfile -File \"$env:CLAUDE_PROJECT_DIR/.claude/scripts/hook-user-prompt-submit.ps1\"" }] }],
    "PreToolUse": [{ "matcher": "Write",
      "hooks": [{ "type": "command", "shell": "powershell", "timeout": 30,
        "command": "pwsh -NoProfile -File \"$env:CLAUDE_PROJECT_DIR/.claude/scripts/hook-pre-tool-use-handoff.ps1\"" }] }],
    "PostToolUse": [{ "matcher": "Edit|Write|MultiEdit",
      "hooks": [{ "type": "command", "shell": "powershell", "timeout": 30,
        "command": "pwsh -NoProfile -File \"$env:CLAUDE_PROJECT_DIR/.claude/scripts/hook-post-tool-use.ps1\"" }] }],
    "Stop": [{ "hooks": [{ "type": "command", "shell": "powershell", "timeout": 30,
      "command": "pwsh -NoProfile -File \"$env:CLAUDE_PROJECT_DIR/.claude/scripts/hook-stop.ps1\"" }] }]
  }
}
```

Mac / Linux（bash）の例 — 各 command を bash script 呼び出しに置き換える（`"shell"` 指定は不要。shell form は `sh -c` で非対話実行される。ログイン shell ではないので profile の PATH 設定に依存しない）:

```json
{
  "hooks": {
    "SessionStart": [{ "matcher": "startup|resume|clear|compact|fork",
      "hooks": [{ "type": "command", "timeout": 30,
        "command": "bash \"$CLAUDE_PROJECT_DIR\"/.claude/scripts/hook-session-start.sh" }] }]
  }
}
```

（他イベントも同様に `bash "$CLAUDE_PROJECT_DIR"/.claude/scripts/hook-*.sh` へ置き換える。matcher の `fork` は既存セッションから fork した時の発火で、不要なら外す）

## hook scripts

`.claude/scripts/hook-*` の 6 ファイルを対象 OS の言語で生成する（派生成果物の自動再生成 hook は該当する監視対象がある時のみ）。

役割は言語共通:

- `hook-session-start` — ポインタ（handoff ファイル名 + `issues/processing/*.md` のタイトル）と並走 4 軸 verdict のみ注入（**本文は Read/注入しない**）。検出時は (a)hold+確認 (b)引継ぎ切替 (c)scope 弁別 (d)handoff 明示を促す。本文は user 選択後にその 1 件のみ Read（PC 再起動復元 + 並走衝突防止 + context 汚染防止）
- `hook-user-prompt-submit` — `docs/*.md` 直近 3 ファイルを context 注入
- `hook-pre-tool-use-handoff` — handoff 命名規約 `[YYYY-MM-DD]-issue-[ID]-[kebab].md` 検証、違反なら `exit 2` + stderr で reject
- `hook-post-tool-use` — CLAUDE.md / `.claude/skills/**` / `.claude/commands/**` 編集時に `hookSpecificOutput.additionalContext` JSON で公式 WebFetch レビュー reminder
- `hook-post-tool-use-regen`（**任意**・監視対象ファイルから派生成果物を生成している時のみ） — 監視対象の編集を検知し派生成果物を実際に再生成、各 generator の exit code を OR 結合して失敗を隠さず報告
- `hook-stop` — 1 時間以上未更新 handoff があれば更新リマインド。`git status --porcelain --untracked-files=all -- .tmp/handoffs` に出る未 commit の handoff があれば block

各 script 冒頭で標準入力の JSON から `tool_name` / `tool_input.file_path` を取り、エラー抑制は個別コマンド単位で局所化する（PowerShell: `[Console]::In.ReadToEnd() | ConvertFrom-Json` + `-ErrorAction SilentlyContinue` / bash: `input=$(cat)` + `jq` または `python3` で parse + 各コマンド `2>/dev/null`）。
