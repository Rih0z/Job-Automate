---
name: claude-md
description: 任意のプロジェクトに対し、Anthropic 公式 Best Practices（"Write an effective CLAUDE.md"）に準拠した CLAUDE.md を生成・剪定する。「CLAUDE.md を作って」「`/init` の代わりに公式準拠で」「CLAUDE.md を書き直して」「肥大化したので剪定」などで発動。公式準拠の核と独自運用ノウハウをラベル分離して適用する。
---

# CLAUDE.md 生成プロンプト

任意のプロジェクトに対し、Anthropic 公式 Best Practices（[Write an effective CLAUDE.md](https://code.claude.com/docs/en/best-practices#write-an-effective-claude-md) / [Skills](https://code.claude.com/docs/en/skills)）に準拠した `CLAUDE.md` を生成する。**公式準拠の核**と**本プロンプト独自の運用ノウハウ**をラベル分離して適用する。

## 使うタイミング

- 「CLAUDE.md を作って」「`/init` の代わりに公式準拠で生成して」
- 「既存の CLAUDE.md を公式 Best Practices で書き直して」
- 「CLAUDE.md が肥大化したので剪定して」

**使わない時**: コード自体を書く時、Skills (`.claude/skills/`) を作る時、README を書く時。

---

## 公式準拠の核（Anthropic 公式 verbatim）

> 出典: `https://code.claude.com/docs/en/best-practices` "Write an effective CLAUDE.md" セクション。本セクションの主張はすべて同 URL から WebFetch で再取得し検証可能。

### Litmus Test（公式）

> 公式 verbatim: *"Keep it concise. For each line, ask: 'Would removing this cause Claude to make mistakes?' If not, cut it."* / *"Bloated CLAUDE.md files cause Claude to ignore your actual instructions!"* （出典: [best-practices#write-an-effective-claude-md](https://code.claude.com/docs/en/best-practices#write-an-effective-claude-md)）

合格しない行は削除する。「親切で書いておく」「念のため」の行は残さない。

### Include / Exclude（公式テーブル）

| ✅ Include | ❌ Exclude |
|---------|---------|
| Bash commands Claude can't guess | Anything Claude can figure out by reading code |
| Code style rules that differ from defaults | Standard language conventions Claude already knows |
| Testing instructions and preferred test runners | Detailed API documentation (link to docs instead) |
| Repository etiquette (branch naming, PR conventions) | Information that changes frequently |
| Architectural decisions specific to your project | Long explanations or tutorials |
| Developer environment quirks (required env vars) | File-by-file descriptions of the codebase |
| Common gotchas or non-obvious behaviors | Self-evident practices |
| | Domain knowledge / workflows that are only relevant sometimes → use **Skills** (`.claude/skills/`) |

### 公式推奨サイクル

- 新規は `/init` で初期生成 → 反復改善
- 公式 verbatim: *"Treat CLAUDE.md like code: review it when things go wrong, prune it regularly, and test changes by observing whether Claude's behavior actually shifts."* （出典: [best-practices#write-an-effective-claude-md](https://code.claude.com/docs/en/best-practices#write-an-effective-claude-md)）
- 公式 verbatim: *"If your CLAUDE.md is too long, Claude ignores half of it because important rules get lost in the noise. Fix: Ruthlessly prune. If Claude already does something correctly without the instruction, delete it or convert it to a hook."* （出典: [best-practices#avoid-common-failure-patterns](https://code.claude.com/docs/en/best-practices#avoid-common-failure-patterns)）
- ルール追加後に挙動が変わらないなら、そのルールが他に埋もれていることを疑う

### emphasis（公式記述）

> 公式 verbatim: *"You can tune instructions by adding emphasis (e.g., 'IMPORTANT' or 'YOU MUST') to improve adherence."* （出典: [best-practices#write-an-effective-claude-md](https://code.claude.com/docs/en/best-practices#write-an-effective-claude-md)）

公式は使用を許容するが、濫用すると無効化される（公式 *"rules getting lost in the noise"* と同種の現象）。本プロンプトの独自運用基準は次の 1 本化:

- **生成 CLAUDE.md・本プロンプト本体ともに、emphasis（IMPORTANT / YOU MUST）は最大 5 件目安**。それ以外の語気強め（必須・禁止・削除不可・絶対）は平叙文に書き換える

### サイズ（公式記述・数値閾値なし）

> 公式 verbatim: *"keep it short and human-readable"* / *"Keep it concise. For each line, ask: 'Would removing this cause Claude to make mistakes?' If not, cut it."* （出典: [best-practices#write-an-effective-claude-md](https://code.claude.com/docs/en/best-practices#write-an-effective-claude-md)）

公式は数値閾値を持たない。「N 行で fail」のような硬性基準は公式に存在しないため、本プロンプトでも CLAUDE.md に行数による出力拒否を求めない。本プロンプトの「サイズの目安」は剪定タイミングの参考値であり、硬性基準ではない。プロジェクト規模・読み手の慣れに応じて自由に緩めて良い。

### 5 配置（公式 verbatim）

| 配置 | 役割 |
|------|------|
| `~/.claude/CLAUDE.md` | applies to all Claude sessions |
| `./CLAUDE.md` | check into git to share with your team |
| `./CLAUDE.local.md` | personal project-specific notes（gitignore） |
| Parent directories | useful for monorepos |
| Child directories | pulled in on demand when working in those subdirs |

`@path/to/import` 構文で他ファイル import 可能（公式 verbatim）。

### hooks（公式記述）

> 公式 verbatim: *"Use hooks for actions that must happen every time with zero exceptions."* / *"Hooks run scripts automatically at specific points in Claude's workflow. Unlike CLAUDE.md instructions which are advisory, hooks are deterministic and guarantee the action happens."* / *"Edit `.claude/settings.json` directly to configure hooks by hand, and run `/hooks` to browse what's configured."* （出典: [best-practices#set-up-hooks](https://code.claude.com/docs/en/best-practices#set-up-hooks)）

CLAUDE.md は advisory（埋もれると Claude が無視する）。**確実に毎回実行させたい動作は hook 化する**のが公式推奨。設定先は `~/.claude/settings.json`（user）または `.claude/settings.json`（project）の `hooks` フィールド。詳細仕様は [hooks-guide](https://code.claude.com/docs/en/hooks-guide) / [hooks reference](https://code.claude.com/docs/en/hooks)。

主要イベントと出力契約（出典: [hooks reference](https://code.claude.com/docs/en/hooks)）:

- `SessionStart`（matcher: `startup|resume|clear|compact`）— `exit 0` の stdout が Claude の context に追加される
- `UserPromptSubmit` — `exit 0` の stdout が context に追加される。`exit 2` でプロンプト送信を block 可
- `PreToolUse` — `exit 2` + stderr で tool 実行を block。context 注入は `hookSpecificOutput.additionalContext` JSON 形式
- `PostToolUse` — **plain stdout は context 注入されない**（公式 verbatim: *"PostToolUse, PostToolBatch, PreToolUse: Use additionalContext inside hookSpecificOutput"*）。`{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"..."}}` JSON で出力する
- `Stop` / `SubagentStop` — `exit 0` の stdout は debug log のみ（context 注入されない）。`exit 2` で停止を block しタスク継続を強制可（公式: *"Prevents Claude from stopping, continues the conversation"*）

---

## 本プロンプト独自の運用ノウハウ

> 公式には記述がない。本プロンプト由来の運用判断であり、プロジェクトに合わせて緩めて良い。

### 独自運用: サイズの目安（参考値・硬性基準ではない）

| レベル | 目安 | 対応 |
|------|------|------|
| 剪定検討 | 概ね 100 行 / 10KB を超え始めたら | Litmus Test で再評価。挙動が変わらないルールが埋もれていないか観察 |
| 分割推奨 | Claude が指示を無視し始める兆候が出たら | rules / skills / docs へ分割 |

公式の質的 *"concise"* を実運用上の参考値に落とした AIServer v4 起源の目安。「N 行で出力拒否」のような硬性基準ではない。プロジェクト規模に応じて自由に緩めてよい（200 行でも問題ないプロジェクトはある）。判定は数値より「公式 *"rules getting lost in the noise"* 兆候の有無」を主基準にする。

**warning / fail の二段運用パターン**: AIServer v4 では「40 行 / 5KB warning、80 行 / 10KB fail」を二段で持つことで、剪定検討の早期トリガーと分割の閾値を分けている。本プロンプトでは数値を硬性化しないが、**「早期気付き warning + 構造見直し fail の二段構え」設計概念**は汎用的に有効。標準セット採用時に独自の二段閾値を設定する場合の参考にしてよい。

### 独自構造: 標準セット 4 種（規模を問わず default）

CLAUDE.md は単体ではなく、次の 4 セットで構成する。プロジェクト規模に関係なく**最初から AIServer v4 級の品質**で揃える。軽量・縮約版は採用しない。

| セット | 役割 | 参考実装 |
|---|---|---|
| `CLAUDE.md` 本体 | インデックス + 起動時必須手順 + ルール参照テーブル + ルート構成 + 末尾入口リンク | AIServer v4 `CLAUDE.md`（41 行） |
| `.claude/rules/*.md` 6 ファイル | 規約本文（条文方式・通し番号管理） | AIServer v4 `.claude/rules/` |
| `.claude/settings.json` の `hooks` | advisory ルールの deterministic 化（5 hook 構成） | 本リポジトリ `~/.claude/settings.json` |
| `.claude/scripts/hook-*.ps1` 5 ファイル | hooks 本体スクリプト | 本リポジトリ `~/.claude/scripts/` |

rules 6 ファイルの内訳:

| ファイル | 役割 | load 戦略 |
|---|---|---|
| `meta.md` | 条番号インデックス・既知の制約 | 常時 load |
| `code-quality.md` | コード変更時の規約 | `@import` で常時 load |
| `test-verify.md` | テスト・自検証規約 | `@import` で常時 load |
| `issue-workflow.md` | Issue 起票・handoff・`/clear` | `paths:` で path-scope |
| `review.md` | 別エージェントレビュー規約 | `paths:` で path-scope |
| `governance.md` | 肥大化防止・新項目追加 | `paths:` で path-scope |

`paths:` frontmatter を `@import` と併用する理由は、Claude Code の path-scope rules auto-load が Read 時のみ発火する既知挙動への補償（重要 rules を確実に常時 load させる汎用パターン）。

### 独自運用: 関連 docs 読込宣言

採用時、Claude はタスク開始時に関連 docs を最低 1 つ読み、宣言末尾に **完全パス + 1 文要約 + タスク関連性 1 文** を出力する（AIServer v4 第23条由来の汎用パターン）。

### 独自運用: session 開始時 handoff 自動 Read

新規 chat / `/clear` 直後、chat paste 引継ぎが無ければ `.tmp/handoffs/` の最新ファイルを Read。受領した役割のみ実施・scope creep を避け、関連気付きは別 Issue 起票する。

### 独自運用: issue ライフサイクル管理（open → processing → closed）

タスク・問題は `issues/` 配下の 3 段階フォルダで状態管理する:

| フォルダ | 状態 | 配置タイミング |
|---|---|---|
| `issues/open/[ID].md` | 未着手 | 問題発見・新タスク要求時の起票先 |
| `issues/processing/[ID].md` | 着手中 | open から `git mv` で移動。冒頭に進行中 handoff の完全パスを記載 |
| `issues/closed/[ID].md` | 完了 | processing から `git mv` で移動。受入基準達成・テストパス・lint 通過を本文末に宣言 |

**問題発見即起票ルール**: タスク中に別バグ・改善・気付きを発見しても**現タスクで触らない**。発見した事実だけを `issues/open/[ID].md` に起票して終わり、元のタスクに戻る。理由: 現タスク差分の肥大とロールバック困難を防ぎ、レビュー単位を 1 issue = 1 目的に保つため。

**1 issue = 1 目的**: 1 つの issue に複数目的を混ぜない。関連する別目的を発見したら新 issue として起票する。

**handoff と issue の関係**:
- issue = タスクの正本（要件・受入基準・履歴。状態遷移は git mv で記録）
- handoff = 進行中の引継ぎメモ（次セッションへの context 連続性）
- `issues/processing/[ID].md` 冒頭に進行中 handoff の完全パスを記載し、handoff のファイル名も `issue-[ID]` を含めて相互参照する

**各 issue ファイル冒頭の標準ヘッダ**（open / processing / closed すべて共通）:

```markdown
# Issue [ID]: [短いタイトル]

**概要**: [1〜2 行の説明 — 何の問題か、何を達成するか]
**状態**: open / processing / closed
**最新 handoff**: [完全パス・例: C:/Users/.../.tmp/handoffs/2026-05-09-issue-42-claude-md-pruning.md]
**起票日**: YYYY-MM-DD
**関連 issue**: [#N1, #N2 ...] （あれば）

## 受入基準
- [ ] ...

## 履歴・メモ
...
```

handoff 更新のたびに該当 issue ファイルの「最新 handoff」行も同期更新する。これにより issue ファイル単独で再開可能（issue を開けば説明と最新 handoff の場所が即座に分かる）。

### 独自運用: PC 再起動・session 復元の自動化

PC 再起動 / session 切断後に進行中タスクを自動検出し、User に通知して並列委任できる仕組み。

**SessionStart hook の責務**（matcher: `startup|resume|clear|compact`）:
1. `.tmp/handoffs/` 最新ファイルを検出して context 注入
2. `issues/processing/*.md` を全 scan し、各 issue の「タイトル」「最新 handoff の完全パス」を抽出して context 注入
3. context 末尾に「中断作業 N 件あり。User に通知し、再開対象を確認するか、それぞれ別 Agent に並列委任するか提示せよ」と指示

**User 通知フォーマット例**（Claude が User に伝える形）:
```
PC 再起動を検出。中断中の作業 N 件:
  1. issue [42] - claude-md 剪定 (handoff: .tmp/handoffs/2026-05-09-issue-42-claude-md-pruning.md)
  2. issue [43] - hooks 監査 (handoff: .tmp/handoffs/2026-05-09-issue-43-hooks-audit.md)
どれを再開しますか？ それぞれを別 Agent に並列委任しますか？
```

**並列委任パターン**: 各 issue を個別 Agent に渡す場合、`Agent` ツールで以下のみ提供する:
- handoff の完全パス（再解釈・補完なしで本文をそのまま信頼させる）
- issue の完全パス
- 役割範囲（scope creep を避ける指示）

これにより PC 再起動でも作業の context 連続性が保たれ、複数 issue の並列処理が安全に行える。

### 独自運用: handoff 管理（命名・保持・issue 連携）

- ファイル名: `[YYYY-MM-DD]-issue-[ID]-[識別単語].md`（issue 紐付けあり）／ `[YYYY-MM-DD]-[識別単語].md`（紐付けなし）。識別単語は 2〜4 語 kebab-case、作業内容が一目で分かるもの
- 保持: 次の handoff を新規作成するまで前 handoff は削除しない。次 handoff 作成時に削除またはアーカイブする（次セッションが連続して読み戻せるようにするため）
- issue 連携: `issues/open/[ID].md` および `issues/processing/[ID].md` の本文冒頭に「進行中 handoff: [完全パス]」を記載。handoff 更新時は issue 側も同期更新する
- 構成: ゴール / 完了したこと / 残課題 / 関連ファイル（path:line）/ 落とし穴

### 独自運用: 規約の hooks 化判断（advisory → deterministic 昇格）

CLAUDE.md / 本プロンプトに書いた規約は advisory なので、Claude が長文の中で見落とす可能性がある。次の判断基準で「確実に毎回動かしたい」規約は hook 化する。

**hooks 化候補の判断基準**:
- 同じ動作を毎セッション・毎タスクで漏れなく実行したい（例: session 開始時の handoff Read、関連 docs 読込宣言）
- ファイル命名・配置の規約違反を物理的に防ぎたい（例: handoff ファイル名の検証）
- 重要ファイル（CLAUDE.md / skills / commands）の更新後に必ずレビューを起動したい
- session 終了時に成果物の保存・整理を促したい

**hooks 設計指針**:
- スクリプト本体は `.claude/scripts/` に分離して `pwsh -NoProfile -File <path>` で呼ぶ（settings.json の JSON エスケープを避け、debug しやすくする）
- Windows 環境では各 hook 設定に `"shell": "powershell"` を明示する
- PostToolUse の context 注入は `hookSpecificOutput.additionalContext` JSON 形式（plain stdout は注入されない）
- PreToolUse は `exit 2` + stderr で block。誤 reject を避けるため対象 path を厳密にフィルタする
- 各 script の冒頭で `[Console]::In.ReadToEnd() | ConvertFrom-Json` で event data を受け取り、`tool_input.file_path` でフィルタ
- `$ErrorActionPreference` は全域上書きせず、各 cmdlet の `-ErrorAction SilentlyContinue` で局所化（debug ログを潰さない）

**参考実装（5 hook 構成）**:

| イベント | 用途 | reject/notify |
|---|---|---|
| `SessionStart` | `.tmp/handoffs/` 最新パス + `issues/processing/*.md` 全 scan（タイトル + 最新 handoff 完全パス）を context 注入し、PC 再起動復元・並列委任を促す | notify |
| `UserPromptSubmit` | `docs/*.md` 直近 3 ファイルを候補として注入し関連 docs 宣言を促す | notify |
| `PreToolUse(Write)` | `.tmp/handoffs/` への Write 時に命名規約 `[YYYY-MM-DD]-issue-[ID]-[kebab].md` を検証 | reject (`exit 2`) |
| `PostToolUse(Edit\|Write\|MultiEdit)` | CLAUDE.md / `.claude/skills/**` / `.claude/commands/**` 更新時に公式 WebFetch + 別エージェントレビューを促す | notify (additionalContext JSON) |
| `Stop` | 最新 handoff が 1 時間以上未更新なら更新リマインド | notify |

**hooks 監査（定期点検）**:
- `enabledPlugins` で有効化された plugin と settings.json の hooks フィールドを照合し、**dead hooks**（marketplace 配下にあるが load されていない）と **無駄 hooks**（同じ動作の重複・効果薄）を検出する
- `/hooks` コマンドで現状確認、定期的に運用棚卸し

### 独自運用: 別エージェントレビューサイクル

成果物（実装・設計・docs・**CLAUDE.md・skills**）は実行後に別エージェントから skills レビューを最低 1 回受ける。

```
[実行] → [別エージェント skills レビュー] → 合格?
                                     ├─ Yes → 完了
                                     └─ No  → 修正して再レビュー（最大 3 回）
                                                  3 回 FAIL → issues/open/[ID].md 起票・中断
```

レビュアに渡すのは **diff と評価基準のみ**。実装意図・会話履歴は渡さない。公式が紹介する Writer/Reviewer pattern と整合する独自強化。

**対象別の評価基準**:

| 成果物 | 公式 / 評価基準 | 推奨 skill |
|------|--------------|----------|
| CLAUDE.md | Anthropic 公式「Write an effective CLAUDE.md」 | `/review-skill` 相当・Step 7 の WebFetch レビュー |
| `.claude/skills/*/SKILL.md` | Anthropic 公式 Skills 作成ガイド（`docs/skills-building-guide.md`） | `/review-skill` |
| `.claude/commands/*.md`（slash command） | 同上 Skills 作成ガイド + 公式 commands 仕様 | `/review-skill` |
| 実装コード | プロジェクト規約 + テスト戦略 | `/review-changes` / `/review-implementation` |
| 提案書・docs | プロジェクト個別の評価基準（`docs/review-*.md`） | 該当 review プロンプト |

**IMPORTANT** — skills 更新時のレビュー要件:
- skills（`.claude/skills/`、`~/.claude/skills/`、`.claude/commands/` 含む）を新規作成または更新したら、別エージェントに `/review-skill` 相当のレビューを依頼する
- レビュアは Anthropic 公式 Skills 作成ガイド（[skills](https://code.claude.com/docs/en/skills)）を WebFetch で取得して判定する（記憶ベースで判定しない）。構造・トリガー設計・命令品質・出力設計・実用性の 5 軸で 100 点満点採点
- 90 点以上で合格。3 回 FAIL で `issues/open/[ID].md` 起票・中断

---

## 入力

- プロジェクトディレクトリ（`ls -R` / `tree` / 主要ファイル中身）
- マニフェスト（`README.md`, `package.json`, `pyproject.toml`, `go.mod` 等）
- 既存 CLAUDE.md（更新時）

---

## 生成手順

規模を問わず、最初から標準セット 4 種（CLAUDE.md + rules 6 + settings.json hooks + hook scripts 5）を揃える。下記 8 ステップで進める。

#### Step 1: 事実収集

推測・捏造はしない。不明箇所は `> [要確認]` で残す:

- 言語・FW・ランタイム
- ディレクトリ責務（1 行ずつ）
- 起動・テスト・ビルド・型チェック・lint コマンド（実在のみ）
- テスト戦略（ランナー名）
- デプロイ方法
- 環境変数・OS 依存・既知の落とし穴
- gitignore 例外（意図的に追跡しているもの）

#### Step 2: 候補セクション生成 + Litmus Test 適用

各セクションに公式 Litmus Test を適用:

- `# Architecture` 直下 `This project uses TypeScript.` → `package.json` で分かる → 削除
- `テスト実行は npm run test:single -- <file>` → 推測で `npm test` 実行されると全テスト走る → 残す
- 「コードは綺麗に書きましょう」 → 自明 → 削除

#### Step 3: 段階的開示への分離

CLAUDE.md 本体に直接書かず、規約本文は rules 6 ファイルに分離する:

| 内容 | 逃がし先 |
|------|---------|
| 全タスク共通の規約（コード品質・テスト方針） | `.claude/rules/code-quality.md` / `test-verify.md`（`@import` 常時 load） |
| 特定タスク時のみのルール（Issue・review・governance） | `.claude/rules/issue-workflow.md` / `review.md` / `governance.md`（`paths:` path-scope） |
| 条番号インデックスと既知の制約 | `.claude/rules/meta.md`（常時 load） |
| 詳細手順・長文 | `docs/[topic].md` → リンクのみ |
| 時々しか使わない知識・ワークフロー | `.claude/skills/[name]/SKILL.md`（公式推奨） |
| 個人ノート | `CLAUDE.local.md`（gitignore） |

`paths:` frontmatter 例:

```yaml
---
name: review
description: commit 直前に適用するレビュー規約
paths:
  - "**/*.ts"
  - "**/*.tsx"
---
[ルール本文]
```

`paths:` match した file Read 時のみ auto-load。常時 load させたい場合は `paths:` 省略 + CLAUDE.md から `@import`。

#### Step 4: テンプレートで組み立て

下記「出力テンプレート」に project 固有値を埋める。該当しないセクションは削除可、ただし削除理由を明示。

#### Step 5: 自己評価（17 項目ルーブリック）

下記ルーブリックで Y/N 評価。N が 1 つでもあれば書き直す。

#### Step 6: サイズ確認

`(Get-Content <path>).Count` と `(Get-Item <path>).Length` を実行（PowerShell）／ Bash では `wc -l` `wc -c`。実測値を末尾の `*[行数] 行 / [KB] KB*` に転記する（推定値は書かない）。剪定の目安（概ね 100 行）を超えていたら Step 3 へ戻って剪定するか検討する。**ただし行数を理由に出力拒否はしない**（公式は数値閾値を持たない。出力拒否は「Claude が指示を無視している」観察可能な兆候があった時のみ）。

#### Step 7: 別エージェント公式準拠レビュー

生成 CLAUDE.md と併設 rules 6 ファイル（および生成済み settings.json hooks）を別エージェントに渡してレビューを受ける。

レビュアが必ず実施すること:

1. **YOU MUST** `WebFetch` で `https://code.claude.com/docs/en/best-practices` を取得する（記憶ベースで判定しない）。冒頭に取得日時と主要原則の引用を出力する
2. 公式 Include/Exclude / Litmus Test / 5 配置 / `@import` / emphasis に対し 1 項目ずつ Y/N 評価
3. rules 6 ファイルが実在するか・条番号が通し管理されているかを Read で確認
4. 公式該当箇所と生成 CLAUDE.md 該当行を並べて示す

レビュアに渡すもの: 生成 CLAUDE.md 中身・rules 6 ファイル絶対パス・settings.json hooks（生成済みであれば）・公式 URL のみ。渡さないもの: 本プロンプト・公式の引用や要約・生成過程・会話履歴。

合格基準: 公式項目全 Y かつ 90 点以上、かつ冒頭で WebFetch 取得日時引用がある。Web 取得していないレビューは無効、再依頼する。

不合格時: 修正して再レビュー。**3 回 FAIL で `issues/open/[YYYY-MM-DD]-claude-md-generation.md` 起票・中断・ユーザーに報告**。

#### Step 8: 出力 & 標準セット 4 種の実生成 + 引継ぎ

レビュー合格後、project の事実に合わせて **標準セット 4 種を実生成**する（Step 1 で集めた事実から条文・規約・hook を埋める）:

1. **CLAUDE.md 本体** — 出力テンプレートに project 固有値（プロジェクト名・一行サマリ・コマンド・ルート構成・末尾入口リンク）を埋めて生成

2. **`.claude/rules/*.md` 6 ファイル** — Step 1 事実から条文を抽出して生成（条番号は通し管理・ファイル間で重複させない）:

   | ファイル | 内容 | YAML frontmatter | load |
   |---|---|---|---|
   | `meta.md` | 第1〜N条インデックス（条見出し + 所在ファイル）+ 既知の制約 | なし | 常時 |
   | `code-quality.md` | コード変更規約（命名・import・型）の条文 | `description` のみ | `@import` で常時 |
   | `test-verify.md` | テスト・自検証規約（ランナー・lint・受入基準）の条文 | `description` のみ | `@import` で常時 |
   | `issue-workflow.md` | Issue 起票・handoff・/clear 規約の条文 | `paths: ["issues/**", ".tmp/**"]` | path-scope |
   | `review.md` | 別エージェントレビュー規約の条文 | `paths: ["**/*.<lang>", ".claude/commands/**"]` | path-scope |
   | `governance.md` | 肥大化防止・新項目追加規約の条文 | `paths: ["CLAUDE.md", ".claude/**"]` | path-scope |

3. **`~/.claude/settings.json`（または project の `.claude/settings.json`）の hooks セット** — 5 hook 構成。既存設定がある場合は `hooks` フィールドのみ追記（permissions / model 等は保持）:

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

   **hook scripts も併せて生成**（`<scripts>/hook-*.ps1` 5 ファイル）:
   - `hook-session-start.ps1` — `.tmp/handoffs/` 最新 + `issues/processing/*.md` 全 scan を context 注入（PC 再起動復元）
   - `hook-user-prompt-submit.ps1` — `docs/*.md` 直近 3 ファイルを context 注入
   - `hook-pre-tool-use-handoff.ps1` — handoff 命名規約 `[YYYY-MM-DD]-issue-[ID]-[kebab].md` 検証、違反なら `exit 2` + stderr で reject
   - `hook-post-tool-use.ps1` — CLAUDE.md / `.claude/skills/**` / `.claude/commands/**` 編集時に `hookSpecificOutput.additionalContext` JSON で公式 WebFetch レビュー reminder
   - `hook-stop.ps1` — 1 時間以上未更新 handoff があれば更新リマインド

   各 script 冒頭で `[Console]::In.ReadToEnd() | ConvertFrom-Json` から `tool_name` / `tool_input.file_path` を取り、`-ErrorAction SilentlyContinue` は cmdlet 単位で局所化する。

**ユーザーへの最終報告**:
- 生成内容の要約（3 行以内）
- `> [要確認]` 残項目
- **生成したファイル一覧（フルパス）**: CLAUDE.md / rules 6 / settings.json / hook scripts 5
- レビュア合格スコア

大タスク完了のため `/clear` を促す。`/clear` 前に handoff を保存する（命名・保持・issue 連携の規約本体は「独自運用: handoff 管理」を正本とし、ここでは参照のみ）。

---

## 出力テンプレート — AIServer v4 形式（rules 分離・条文方式・標準セット 4 種）

````markdown
# CLAUDE.md - [プロジェクト名]

> [一行サマリ]

## 起動時手順

1. 関連 docs 読込宣言（第23条等）: 該当 docs を最低 1 つ Read し「完全パス + 1 文要約 + タスク関連性 1 文」を宣言末尾に出力する
2. 条文宣言: タスク該当ルール（下表）を宣言してから着手する
3. 作業 → 自検証 → 他者レビュー（別エージェント）を作業節目で実施する。CLAUDE.md / skills 更新時は公式準拠を WebFetch ベースでレビュー（skills→`/review-skill` 90 点合格／3 回 FAIL で `issues/open/[ID].md` 起票・中断）
4. session 開始時（新規 chat / `/clear` 直後）: chat paste 引継ぎが無ければ `.tmp/handoffs/` 最新を Read。役割のみ実施・scope creep を避ける
5. handoff 規約: ファイル名 `[YYYY-MM-DD]-issue-[ID]-[識別単語].md`、次 handoff 作成まで保持、`issues/open|processing/[ID].md` 冒頭に進行中 handoff の完全パス記載（詳細 `issue-workflow.md`）

## ルール一覧

`meta.md` は常時 load。下記は CLAUDE.md `@import` で常時 load（path-scope auto-load 不安定への補償）。他は YAML `paths:` で Read 時のみ load:

@.claude/rules/code-quality.md
@.claude/rules/test-verify.md

| タスク種別 | rules | 含む条 |
|-----------|-------|-------|
| コード/ファイル変更 | `code-quality.md` (常時) | 第3, 7, 11 条 |
| テスト/Issue close | `test-verify.md` (常時) | 第9, 13, 17 条 |
| Issue/.tmp 作業 | `issue-workflow.md` (path-scope) | 第6, 20, 22 条 |
| commit 直前/作業節目 | `review.md` (path-scope) | 第18 条 |
| CLAUDE.md/.claude 編集 | `governance.md` (path-scope) | 第24 条 |

## ルート構成

`[entry]` / `[dir1]/` / `[dir2]/` / 一時: `.tmp/` `.history/`（gitignore 推奨）。git 完全追跡の例外: [明記]

## サイズ運用

公式は数値閾値を持たない（"Keep it concise"）。本プロジェクトは概ね 100 行を剪定検討の目安とする。新項目は rules / docs / skills / .tmp に振り分け、CLAUDE.md 直接記入は避ける（詳細 `.claude/rules/governance.md`）。

セットアップ: [quick_start](docs/...) / 検証: [...](docs/...) / ロードマップ: [...](docs/...)

---
*[行数] 行 / [KB] KB*
*[Optional: チーム鼓舞 1 行 — 例: "Ultrathink. Don't hold back. Give it your all!"]*
````

該当しないセクションは削除可（理由明示）。

---

## 自己評価ルーブリック（17 項目）

ゴールドスタンダード `~/CLAUDE.md`(67 行) と `AIServer_v4/CLAUDE.md`(41 行) の両方が全 Y を満たすことを実証済み。

| # | 項目 | Y/N |
|---|------|-----|
| 1 | 公式 Litmus Test に各行が合格（消したら Claude がミスする行のみ残っている）。行数による硬性ゲートはなし |  |
| 2 | プロジェクト固有の事実のみ（一般論ゼロ） |  |
| 3 | 全コマンド・全パスが実在（推測ゼロ・捏造ゼロ） |  |
| 4 | 各行が公式 Litmus Test に合格 |  |
| 5 | ルート構成 1 行サマリがある |  |
| 6 | デフォルトと異なるコード規約・テスト方針が `code-quality.md` / `test-verify.md` に記載されている |  |
| 7 | 環境・落とし穴 / YOU MUST NOT が rules に記載されている（新規プロジェクトでは YOU MUST NOT 省略可） |  |
| 8 | 別エージェントレビューサイクルが `review.md` に記載されている |  |
| 9a | session 開始時 handoff 自動 Read 運用が `issue-workflow.md` に明記されている |  |
| 9b | handoff 命名規約（`[YYYY-MM-DD]-issue-[ID]-[識別単語].md`、識別単語は 2〜4 語 kebab-case）が明記 |  |
| 9c | handoff 保持規約（次 handoff 作成まで前 handoff を削除しない）が明記 |  |
| 9d | issue ファイル連携（`issues/open|processing/[ID].md` 冒頭に進行中 handoff の完全パス記載）が明記 |  |
| 9e | 各 issue ファイル冒頭ヘッダ（タイトル / 概要 1〜2 行 / 状態 / 最新 handoff 完全パス / 起票日）の標準形式が明記され、handoff 更新時の同期更新ルールがある |  |
| 9f | issues/ 3 段階フォルダ管理（open → processing → closed の git mv 遷移）と問題発見即起票（scope creep 禁止・現タスクで触らない）が独立セクションとして明記されている |  |
| 16 | PC 再起動・session 復元の自動化（SessionStart hook で `issues/processing/*.md` 全 scan + 各 issue の最新 handoff 完全パス抽出 → User 通知 + 並列委任パターン）が独立セクションで明記されている |  |
| 17 | Step 8 で標準セット 4 種（CLAUDE.md + rules 6 ファイル + settings.json hooks + hook scripts 5）の **実生成手順** が明記され、雛形が示されている |  |
| 10 | 詳細ルールは別ファイルに分離 or リンクのみ |  |
| 11 | 意思決定支援（decision tree / 前提条件表 / ルール参照テーブル）が 1 つ以上 |  |
| 12 | 「新しい○○を追加する手順」のガバナンスがある |  |
| 13 | emphasis（IMPORTANT / YOU MUST）出現が 5 件以下に絞られている（公式 emphasis ガイダンスに沿う） |  |
| 14 | 進行中タスク・TODO・バージョン番号など陳腐化情報なし |  |
| 15 | 確実に毎回実行したい advisory ルールが hooks 化候補として識別され、settings.json の hooks に登録されている（または該当なしと宣言されている） |  |

N が残れば書き直して再評価する。Litmus Test に合格しない行は削る。

---

## ゴールドスタンダード参照

- 標準参考実装: AIServer v4 `CLAUDE.md`（41 行）— rules 分離・条文方式・`@import` 併用・第24条肥大化防止
- 自律化参考実装: 本リポジトリの `~/.claude/settings.json` + `~/.claude/scripts/` の 5 hook 構成

両者を組み合わせた標準セット 4 種が 17 項目ルーブリックで全 Y を実証する基盤となる。

---

## 含めてはいけないもの

- 一般的開発常識（「テストを書きましょう」「セキュリティに注意」）
- ツール自体の長文（公式 docs リンクのみ）
- バージョン番号・進行中タスク・TODO（陳腐化）
- README に書くべき導入文・売り文句（CLAUDE.md は AI 向け）
- 装飾的見出し階層（h4 以下を多用しない）
- 時々しか使わない知識・ワークフロー（Skills へ）

---

## 本プロンプトのメンテ checklist（プロンプト管理者向け・生成 CLAUDE.md とは無関係）

本プロンプトを更新する人向け。生成 CLAUDE.md の評価には関係しない:

- [ ] Step 7 で WebFetch が要件化されているか
- [ ] Step 8 で `/clear` + handoff 保存が指示されているか
- [ ] handoff 規約（ファイル名 `[YYYY-MM-DD]-issue-[ID]-[識別単語].md`、次 handoff 作成まで保持、issue ファイルへの完全パス記載）が一貫しているか
- [ ] skills 更新時の公式 Skills ガイド WebFetch レビューが要件化されているか
- [ ] 「公式準拠の核」と「独自運用」のラベル分離が崩れていないか
- [ ] emphasis（IMPORTANT / YOU MUST）が本プロンプト全体で 5 件以下か（語気強め「必須・禁止・削除不可・絶対」も平叙文化されているか）
- [ ] 公式 verbatim 引用に出典 URL + セクション名が付いているか
- [ ] 行数による出力拒否ゲートが残っていないか（公式は数値閾値を持たない）
- [ ] hooks 化判断セクションがあり、5 hook 参考構成と監査手順（dead/無駄 hooks 検出）が含まれているか
- [ ] PC 再起動・session 復元（SessionStart hook の processing scan + User 通知 + 並列委任）が含まれているか
- [ ] Step 8 で標準セット 4 種（CLAUDE.md / rules 6 / settings.json hooks + hook scripts 5）の実生成手順と雛形が含まれているか

---
*準拠ソース: https://code.claude.com/docs/en/best-practices "Write an effective CLAUDE.md"*
