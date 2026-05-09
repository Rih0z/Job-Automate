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

---

## 本プロンプト独自の運用ノウハウ

> 公式には記述がない。本プロンプト由来の運用判断であり、プロジェクトに合わせて緩めて良い。

### 独自運用: サイズの目安（参考値・硬性基準ではない）

| レベル | 目安 | 対応 |
|------|------|------|
| 剪定検討 | 概ね 100 行 / 10KB を超え始めたら | Litmus Test で再評価。挙動が変わらないルールが埋もれていないか観察 |
| 分割推奨 | Claude が指示を無視し始める兆候が出たら | rules / skills / docs へ分割 |

公式の質的 *"concise"* を実運用上の参考値に落とした AIServer v4 起源の目安。「N 行で出力拒否」のような硬性基準ではない。プロジェクト規模に応じて自由に緩めてよい（200 行でも問題ないプロジェクトはある）。判定は数値より「公式 *"rules getting lost in the noise"* 兆候の有無」を主基準にする。

### 独自構造: 軽量 path / 重量 path

| path | 形式 | 採用条件 | 参考実装 |
|------|------|---------|---------|
| 軽量（縮約版） | CLAUDE.md 単体 | 単独運用 / 6 ヶ月以内 / 規約数が少ない | Job-Automate `CLAUDE.md` |
| 重量（rules 分離） | CLAUDE.md + `.claude/rules/*.md` 6 ファイル | 複数人 / 長期 / 規約数が多い | AIServer v4 `CLAUDE.md`（41 行） |

**default は軽量 path**。軽量 path で剪定の目安（概ね 100 行）を超えても挙動が安定していれば継続して良い。Claude が指示を無視し始めたら重量 path への移行を検討する。

重量 path の rules セット（採用時に揃えるファイル群）:

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

### 独自運用: handoff 管理（命名・保持・issue 連携）

- ファイル名: `[YYYY-MM-DD]-issue-[ID]-[識別単語].md`（issue 紐付けあり）／ `[YYYY-MM-DD]-[識別単語].md`（紐付けなし）。識別単語は 2〜4 語 kebab-case、作業内容が一目で分かるもの
- 保持: 次の handoff を新規作成するまで前 handoff は削除しない。次 handoff 作成時に削除またはアーカイブする（次セッションが連続して読み戻せるようにするため）
- issue 連携: `issues/open/[ID].md` および `issues/processing/[ID].md` の本文冒頭に「進行中 handoff: [完全パス]」を記載。handoff 更新時は issue 側も同期更新する
- 構成: ゴール / 完了したこと / 残課題 / 関連ファイル（path:line）/ 落とし穴

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
| CLAUDE.md | Anthropic 公式「Write an effective CLAUDE.md」 | `/review-skill` 相当・Step 8 の WebFetch レビュー |
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

### 軽量 path（default・公式 `/init` 相当）

公式推奨は「`/init` で生成 → 反復改善」。次の **3 ステップ**で済む場合これを default とする:

1. `/init` で起動 or 出力テンプレ A（縮約版）を埋める
2. 自己評価ルーブリック（14 項目）で全 Y を確認
3. 別エージェント skills レビュー合格 → 出力

採用条件: 単独 or 短期、規約数が少なく CLAUDE.md 単体で剪定の目安（概ね 100 行）程度に収まる見込み。

### 重量 path（rules 分離・条文方式）

複数人 / 長期 / 規約数が多い場合のみ採用。下記 9 ステップを通す。

#### Step 1: 採用構造宣言

「軽量 path（縮約版）」または「重量 path（rules 分離・条文方式）」のいずれかを宣言する。Step 5 自己評価と Step 8 関連ファイル提案に伝搬する。

#### Step 2: 事実収集

推測・捏造はしない。不明箇所は `> [要確認]` で残す:

- 言語・FW・ランタイム
- ディレクトリ責務（1 行ずつ）
- 起動・テスト・ビルド・型チェック・lint コマンド（実在のみ）
- テスト戦略（ランナー名）
- デプロイ方法
- 環境変数・OS 依存・既知の落とし穴
- gitignore 例外（意図的に追跡しているもの）

#### Step 3: 候補セクション生成 + Litmus Test 適用

各セクションに公式 Litmus Test を適用:

- `# Architecture` 直下 `This project uses TypeScript.` → `package.json` で分かる → 削除
- `テスト実行は npm run test:single -- <file>` → 推測で `npm test` 実行されると全テスト走る → 残す
- 「コードは綺麗に書きましょう」 → 自明 → 削除

#### Step 4: 段階的開示への分離

CLAUDE.md に直接書かない:

| 内容 | 逃がし先 |
|------|---------|
| 全タスク共通の規約 | `.claude/rules/[name].md`（重量 path 採用時） |
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

#### Step 5: テンプレートで組み立て

下記「出力テンプレート」（A 軽量 / B 重量）から採用構造に応じて選択。該当しないセクションは削除可、ただし削除理由を明示。

#### Step 6: 自己評価（14 項目ルーブリック）

下記ルーブリックで Y/N 評価。N が 1 つでもあれば書き直す。

#### Step 7: サイズ確認

`(Get-Content <path>).Count` と `(Get-Item <path>).Length` を実行（PowerShell）／ Bash では `wc -l` `wc -c`。実測値を末尾の `*[行数] 行 / [KB] KB*` に転記する（推定値は書かない）。剪定の目安（概ね 100 行）を超えていたら Step 3 へ戻って剪定するか検討する。**ただし行数を理由に出力拒否はしない**（公式は数値閾値を持たない。出力拒否は「Claude が指示を無視している」観察可能な兆候があった時のみ）。

#### Step 8: 別エージェント公式準拠レビュー

生成 CLAUDE.md（重量 path 時は併設 rules も）を別エージェントに渡してレビューを受ける。

レビュアが必ず実施すること:

1. **YOU MUST** `WebFetch` で `https://code.claude.com/docs/en/best-practices` を取得する（記憶ベースで判定しない）。冒頭に取得日時と主要原則の引用を出力する
2. 公式 Include/Exclude / Litmus Test / 5 配置 / `@import` / emphasis に対し 1 項目ずつ Y/N 評価
3. （重量 path 時）rules 6 ファイルが実在するか・条番号が通し管理されているかを Read で確認
4. 公式該当箇所と生成 CLAUDE.md 該当行を並べて示す

レビュアに渡すもの: 生成 CLAUDE.md 中身・rules ファイル絶対パス（重量 path 時）・公式 URL のみ。渡さないもの: 本プロンプト・公式の引用や要約・生成過程・会話履歴。

合格基準: 公式項目全 Y かつ 90 点以上、かつ冒頭で WebFetch 取得日時引用がある。Web 取得していないレビューは無効、再依頼する。

不合格時: 修正して再レビュー。**3 回 FAIL で `issues/open/[YYYY-MM-DD]-claude-md-generation.md` 起票・中断・ユーザーに報告**。

#### Step 9: 出力 & 引継ぎ

レビュー合格後、ユーザーに伝える:

- 生成内容の要約（3 行以内）
- `> [要確認]` 残項目
- 関連ファイル提案（重量 path 時は rules 6 ファイルセット）
- レビュア合格スコア

大タスク完了のため `/clear` を促す。`/clear` 前に handoff を保存する（命名・保持・issue 連携の規約本体は本プロンプト「独自運用: handoff 管理」を正本とし、ここでは参照のみ）。handoff 内容: ゴール / 完了したこと（行数・スコア）/ 残課題 / 関連ファイル（path:line）/ 落とし穴。

---

## 出力テンプレート

### A. 軽量 path（縮約版）— Job-Automate `CLAUDE.md` 形式

````markdown
# CLAUDE.md - [プロジェクト名]

> [一行サマリ — 何を、誰のために、どんな技術で作るか]

## よく使うコマンド

- 起動: `[コマンド]`
- テスト: `[コマンド]`（単一テスト優先 / 全実行回避 など方針も）
- ビルド: `[コマンド]`
- 型チェック / Lint: `[コマンド]`

## ルート構成

`[entry]` / `[dir1]/` [責務] / `[dir2]/` [責務] / 一時: `.tmp/` `.history/`（gitignore 推奨）。git 完全追跡の例外があれば明記。

## コード規約（デフォルトと異なる点のみ）

- [例: ES Modules を使う / CommonJS 禁止]
- [例: import は destructure する]

## 環境・落とし穴

- [必須環境変数、OS 依存、絶対 NG など 3〜5 項目]

## YOU MUST NOT（過去の失敗から）

- [3〜5 項目。新規プロジェクトでは省略可]

## 何を使うか（decision tree）

```
[判断軸]
├─ [選択肢 A] → [対応コマンド]
└─ [選択肢 B] → [対応コマンド]
```

## レビュー受領サイクル

- 全成果物（実装・**CLAUDE.md**・**skills**・docs）は別エージェント skills レビュー最低 1 回
- 対応 skill: 実装→`/review-changes`、skills/commands→`/review-skill`、CLAUDE.md→公式 Best Practices WebFetch レビュー
- 合格まで反復、3 回失敗で `issues/open/` 起票・中断
- レビュアには diff と評価基準のみ（実装意図・会話履歴は渡さない）

## handoff 管理

- ファイル名: `.tmp/handoffs/[YYYY-MM-DD]-issue-[ID]-[識別単語].md`（issue 紐付けあり）／ `[YYYY-MM-DD]-[識別単語].md`（紐付けなし）。識別単語は 2〜4 語 kebab-case
- 次の handoff を作るまで前 handoff は削除しない（タスク完了直後でも保持）
- `issues/open/[ID].md` / `issues/processing/[ID].md` の冒頭に「進行中 handoff: [完全パス]」を記載

## 新しい○○を追加するルール

1. [規約ファイルを置く場所]
2. [CLAUDE.md / README への追記要否]
3. [自己完結性などの設計原則]

---
*[行数] 行 / [KB] KB*
````

### B. 重量 path（rules 分離・条文方式）— AIServer v4 `CLAUDE.md` 形式

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
````

該当しないセクションは削除可（理由明示）。

---

## 自己評価ルーブリック（14 項目）

ゴールドスタンダード `~/CLAUDE.md`(67 行) と `AIServer_v4/CLAUDE.md`(41 行) の両方が全 Y を満たすことを実証済み。

| # | 項目 | Y/N |
|---|------|-----|
| 1 | 公式 Litmus Test に各行が合格（消したら Claude がミスする行のみ残っている）。行数による硬性ゲートはなし |  |
| 2 | プロジェクト固有の事実のみ（一般論ゼロ） |  |
| 3 | 全コマンド・全パスが実在（推測ゼロ・捏造ゼロ） |  |
| 4 | 各行が公式 Litmus Test に合格 |  |
| 5 | ルート構成 1 行サマリがある |  |
| 6 | デフォルトと異なるコード規約・テスト方針が記載（重量 path: rules への分離で可） |  |
| 7 | 環境・落とし穴 / YOU MUST NOT がある（重量 path: rules への分離で可・新規プロジェクトでは YOU MUST NOT 省略可） |  |
| 8 | 別エージェントレビューサイクルが記載（重量 path: `review.md` への分離で可） |  |
| 9a | session 開始時 handoff 自動 Read 運用が明記（重量 path: `issue-workflow.md` で可） |  |
| 9b | handoff 命名規約（`[YYYY-MM-DD]-issue-[ID]-[識別単語].md`、識別単語は 2〜4 語 kebab-case）が明記 |  |
| 9c | handoff 保持規約（次 handoff 作成まで前 handoff を削除しない）が明記 |  |
| 9d | issue ファイル連携（`issues/open|processing/[ID].md` 冒頭に進行中 handoff の完全パス記載）が明記 |  |
| 10 | 詳細ルールは別ファイルに分離 or リンクのみ |  |
| 11 | 意思決定支援（decision tree / 前提条件表 / ルール参照テーブル）が 1 つ以上 |  |
| 12 | 「新しい○○を追加する手順」のガバナンスがある |  |
| 13 | emphasis（IMPORTANT / YOU MUST）出現が 5 件以下に絞られている（公式 emphasis ガイダンスに沿う） |  |
| 14 | 進行中タスク・TODO・バージョン番号など陳腐化情報なし |  |

N が残れば書き直して再評価する。Litmus Test に合格しない行は削る。

---

## ゴールドスタンダード参照

- 重量 path 参考: AIServer v4 `CLAUDE.md`（41 行）— rules 分離・条文方式・`@import` 併用・第24条肥大化防止
- 軽量 path 参考: Job-Automate `CLAUDE.md` — 縮約版・decision tree + ガバナンス・CLAUDE.md 単体完結

両方とも上 14 項目ルーブリックで全 Y を実証済み。

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

- [ ] Step 8 で WebFetch が要件化されているか
- [ ] Step 9 で `/clear` + handoff 保存が指示されているか
- [ ] handoff 規約（ファイル名 `[YYYY-MM-DD]-issue-[ID]-[識別単語].md`、次 handoff 作成まで保持、issue ファイルへの完全パス記載）が一貫しているか
- [ ] skills 更新時の公式 Skills ガイド WebFetch レビューが要件化されているか
- [ ] 「公式準拠の核」と「独自運用」のラベル分離が崩れていないか
- [ ] emphasis（IMPORTANT / YOU MUST）が本プロンプト全体で 5 件以下か（語気強め「必須・禁止・削除不可・絶対」も平叙文化されているか）
- [ ] 公式 verbatim 引用に出典 URL + セクション名が付いているか
- [ ] 行数による出力拒否ゲートが残っていないか（公式は数値閾値を持たない）

---
*準拠ソース: https://code.claude.com/docs/en/best-practices "Write an effective CLAUDE.md"*
