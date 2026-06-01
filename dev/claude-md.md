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

## 公式準拠の核（実行時 WebFetch 必須・本プロンプトに焼き込まない）

> Anthropic 公式は随時更新される。**公式の文言・テーブル・数値・API 契約を本プロンプトに転記（焼き込み）しない**。生成・レビュー開始時に下記を必ず WebFetch で取得し、その時点の現行版で判定する（記憶・過去の引用で代替しない。WebFetch 失敗時は焼き込み版で代替せず、取得できるまで生成を中断する）。
>
> 焼き込み禁止の理由は公式 Exclude 項目「Information that changes frequently」と同根。実際、本プロンプトが過去に転記した Include/Exclude テーブルは現行公式とドリフトした（行の増減・例示変更）。転記は必ず腐る。

### 取得対象と確認項目（名称のみ列挙・本文/テーブル/数値は取得して読む）

| URL | 取得時に現行版を確認する項目 |
|---|---|
| `https://code.claude.com/docs/en/best-practices`（"Write an effective CLAUDE.md" / "Avoid common failure patterns" / "Add an adversarial review step"） | Litmus Test の文言 / Include・Exclude テーブルの現行内容 / サイズ・行数の記述（数値閾値の有無）/ emphasis ガイダンス / 5 配置 + `@path` import / hooks（advisory との対比）/ Writer-Reviewer・adversarial review の注意（reviewer は gap を過剰報告しがち → correctness と明示要件に関わる gap のみ採用） |
| `https://code.claude.com/docs/en/skills` | SKILL.md 必須・frontmatter（`name` 任意 / `description` 推奨 / `description`+`when_to_use` の文字数上限）/ 本文の recurring token cost と簡潔性 / progressive disclosure（supporting files で参照分離）/ SKILL.md 行数の目安 / commands と skills の統合 / `disable-model-invocation` 等 |
| `https://code.claude.com/docs/en/hooks`・`https://code.claude.com/docs/en/hooks-guide` | hook イベント別の出力契約（どの stdout が context 注入されるか / `exit 2` の意味 / `additionalContext` JSON / Stop の連続 block 上限など、hook 生成直前に現行仕様を確認） |

取得後、冒頭に「取得日時 + 確認した現行原則の要点」を出力してから生成・レビューに進む。この WebFetch は省略不可。

### 本プロンプト由来の独自運用基準（公式転記ではない・保持する）

公式の文言ではなく本プロンプト由来の運用判断。公式が変わっても独自基準として有効だが、取得時に公式と矛盾しないか都度突合する:

- **emphasis（IMPORTANT / YOU MUST）は最大 5 件目安**。それ以外の語気強め（必須・禁止・絶対）は平叙文化する（公式 emphasis 許容を運用上引き締めた独自基準）
- **行数による出力拒否ゲートを設けない**。公式が数値閾値を持たないことを取得時に確認した上で、剪定判断は "rules getting lost in the noise" の兆候を主基準にする（数値は参考値）

---

## 本プロンプト独自の運用ノウハウ

> 公式には記述がない。本プロンプト由来の運用判断であり、プロジェクトに合わせて緩めて良い。

### 独自運用: サイズの目安（参考値・硬性基準ではない）

| レベル | 対象 | 目安 | 対応 |
|------|------|------|------|
| 剪定検討 | CLAUDE.md 本体 | 概ね 100 行 / 10KB を超え始めたら | Litmus Test で再評価。挙動が変わらないルールが埋もれていないか観察 |
| 分割推奨 | CLAUDE.md 本体 | Claude が指示を無視し始める兆候が出たら | rules / skills / docs へ分割 |
| **常時 load rules 個別 cap** | `meta.md` / `@import` で常時 load される rules ファイル個別 | **5KB soft cap**（AIServer v4 第24条 F 項由来の独自強化） | cap を超えたら条文を path-scope rules に逃がすか、長文化した条文を docs/ 配下に分離してリンク化 |

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

rules 6 ファイル + オプション 1 ファイルの内訳:

| ファイル | 役割 | load 戦略 |
|---|---|---|
| `meta.md` | 条番号インデックス・既知の制約（Issue #23478 等） | 常時 load |
| `code-quality.md` | コード変更時の規約 | `@import` で常時 load |
| `test-verify.md` | テスト・自検証規約 | `@import` で常時 load |
| `issue-workflow.md` | Issue 起票・handoff・`/clear` | `paths:` で path-scope |
| `review.md` | 別エージェントレビュー規約 | `paths:` で path-scope |
| `governance.md` | 肥大化防止・新項目追加（第24条 A〜F の 6 項目構造） | `paths:` で path-scope |
| `docs-management.md`（**オプション**: `docs/` 体系を持つプロジェクトのみ） | docs 配置 mapping / 新 docs 配置 flow / 全 section README 必須化 + 4 箇所同期更新義務 / 過時マーカー（"as of YYYY-MM-DD"）強制 | `paths:` で path-scope（`docs/**`, `CLAUDE.md`, `.claude/rules/governance.md` 編集時） |

`docs-management.md` 採用判定: `docs/` 配下に **複数 section（5 以上）**があり、section README / inventory / validation script など複数箇所で同じ section リストを SoT として保持しているプロジェクトでのみ採用する。単一 `docs/README.md` で完結する小規模プロジェクトは不要（AIServer v4 のような 17 section + auto-generation pipeline がある大規模 docs 体系で価値が出る）。

`paths:` frontmatter を `@import` と併用する理由は、Claude Code の path-scope rules auto-load が **Read 時のみ発火、Write/Create 時には発火しない**既知 bug（[claude-code Issue #23478](https://github.com/anthropics/claude-code/issues/23478)）への補償。`@import` を一次防御、第23条手動 Read を二次防御とする二重防壁が AIServer v4 で実証済みのパターン。生成 rules ファイルの `meta.md` 末尾「既知の制約」セクションにも Issue URL を明記し、なぜ二重防壁が必要かを伝える。

### 独自運用: 関連 docs 読込宣言

採用時、Claude はタスク開始時に関連 docs を最低 1 つ読み、**宣言の最初と最後の両方**に **完全パス + 1 文要約 + タスク関連性 1 文** を出力する（AIServer v4 第15条「ドキュメント参照記録」+ 第23条「関連 docs 読込」由来の汎用パターン）。最初に宣言することで「これから何の根拠で動くか」、最後に再掲することで「実際に何を踏まえたか」の証跡を二重化する。

### 独自運用: 条文宣言の lazy load 運用

「タスク該当ルールを宣言してから着手」と書く時、**全条一括宣言は不要**（AIServer v4 第1条由来）。タスクに該当する条のみ宣言する。`meta.md` の条番号インデックスを参照して必要分のみ拾う lazy load 運用にする。「念のため全条宣言」を許すと宣言が長文化して Claude が自分の宣言を無視する原因になる。

### 独自運用: governance.md の 6 項目構造（第24条 A〜F）

`governance.md` を生成する時、肥大化防止規約は **AIServer v4 第24条由来の A〜F の 6 項目構造**で記述する。これにより「サイズが大きい」以外の腐敗経路も構造的に塞ぐ:

| 項 | 内容 | 例 |
|---|---|---|
| **A** サイズ閾値 | CLAUDE.md 本体の warning / fail 行数・KB | 40 行 / 5KB warning, 80 行 / 10KB fail |
| **B** 新項目ルーティング | 「CLAUDE.md に書きたくなった」時の振り分け先 | 原則→rules / 手順→docs / オンデマンド→skills / 過渡→`.tmp/` / 全タスク必須のみ CLAUDE.md 直接記入可 |
| **C** 公式準拠 | 新 `.claude/` subdir は公式定義（rules/skills/commands/agents）のいずれかに限定 | `docs/`, `tmp/` 等の独自 subdir は `.claude/` 直下に作らない |
| **D** 定期レビュー | 公式 docs ドリフト検出のための定期点検 | 四半期ごとに公式 Best Practices を WebFetch + ドリフト改修計画 |
| **E** 自動検証 | サイズ閾値・命名規約の hook / CI による自動検証 | hooks の `PreToolUse(Write)` で命名規約検証、`PostToolUse(Edit)` でサイズ警告 |
| **F** 常時 load ファイル 5KB cap | `meta.md` + `@import` で常時 load される rules 個別の cap | 各ファイル 5KB soft cap、超えたら条文を path-scope rules に逃がす |

A〜D だけだと CLAUDE.md 本体の肥大化は防げても、`@import` で常時 load される rules ファイル経由の context 汚染を防げない。F が AIServer 独自の最も効く改良点。

### 独自運用: handoff 受領（user 明示指示駆動・本文は自動 Read しない）

handoff は **user の明示指示でのみ受領**する: ① user が chat に paste、または ② user が「handoff X を読んで」と指示。**最新 handoff の本文を session 開始時に自動 Read しない**（無関係な最新 handoff の誤受領と、本文を毎 session 注入する context 汚染を防ぐ）。受領後は役割のみ実施・scope creep を避け、関連気付きは別 Issue 起票する。

SessionStart hook は**本文を注入せず、ポインタと verdict のみ通知する**: 中断作業の一覧（issue タイトル + handoff ファイル名のみ）と並走 4 軸 verdict（clean / 痕跡あり）を提示し「どれを再開しますか？」と user に問う。**本文 Read は user が再開対象を選択した後に、その 1 件だけ**行う。

**stale handoff 誤受領防止**: 提示する handoff のうち **7 日以上前 / 既に「## 完了」marker 済 / 「次 session 不要」明記**のものは "stale" と注記し、user が誤って選ばないようにする。**90 日 archive ローテーション**: 90 日経過した handoff は `.tmp/archive/handoffs/` に退避し context 肥大化を防ぐ（AIServer v4 第22条由来）。

### 独自運用: 並走 agent 痕跡 4 軸 recheck（並走衝突防止）

複数 agent / 複数 session が同一リポジトリで並走する運用では、着手前に並走痕跡を検出して衝突を防ぐ（AIServer v4 第22条 V 由来。同条は「6 回連続の並走衝突」という実損失から生まれた高優先機構）。

**検出する 2 境界**（この時点で 4 軸を literal 実行）:
- (A) session 開始時 / handoff 受領直後（新規 chat・`/clear` 直後、条文宣言の前）
- (B) plan 起票前（`.tmp/plans/<id>.md` Write 前）

**4 軸 literal command**（bash / PowerShell 両対応。shell redirect は環境に合わせる: bash `2>/dev/null` / PowerShell `2>$null` または `-ErrorAction SilentlyContinue`）:

| 軸 | 検出対象 | command（bash 例） |
|---|---|---|
| axis 1 | 同 Issue の並走 commit | `git log -10 --all --oneline -- <issue_path>` |
| axis 2 | 同 Issue の handoff / plan | `ls -t .tmp/handoffs/*<id>*.md`、`ls -t .tmp/plans/*<id>*.md` |
| axis 3 | 並走 worktree | `git branch --show-current && git worktree list` |
| axis 4 | 別 session の uncommitted Edit | `git status --short` |

**痕跡検出時の action**: (a) 着手 hold + User 確認 / (b) 既存 work 引継ぎへ切替（自分の plan 撤回）/ (c) scope 重複 vs complementary 弁別 / (d) handoff index に並走痕跡を明示。

**関連 docs 読込宣言への統合**: 第23条の証跡 3 要素（完全パス + 1 文要約 + タスク関連性）に「**並走痕跡 4 軸 clean 確認済**」を 4th 要素として加える。4 軸全 clean を確認後のみ着手を継続する。enforcement は SessionStart hook の自動実行（hook + 手動宣言の二重防壁）。

### 独自運用: issue ライフサイクル管理（open → processing → closed）

タスク・問題は `issues/` 配下の 3 段階フォルダで状態管理する:

| フォルダ | 状態 | 配置タイミング |
|---|---|---|
| `issues/open/[ID].md` | 未着手 | 問題発見・新タスク要求時の起票先 |
| `issues/processing/[ID].md` | 着手中 | open から `git mv` で移動。冒頭に進行中 handoff の完全パスを記載 |
| `issues/closed/[ID].md` | 完了 | processing から `git mv` で移動。下記 close 検証 4 段を本文末に証拠付きで宣言 |

**close 前検証 4 段**（AIServer v4 第21条由来。「修正したつもり」「regression 未確認 close」を構造的に排除）:
1. **再現 → 修正後 pass**: 元 bug の再現条件で修正後に再実行し、症状消失を ログ / 出力 / スクショ / テスト結果ファイル のいずれかで証拠記録
2. **negative test（regression 防壁化）**: 修正を意図的に外す or 旧 commit に戻して fail することを確認し、test が真に bug を捕捉する保証を残す。可能なら自動テストとして永続化
3. **他機能 regression smoke**: 影響範囲の関連機能を実機で run し症状ゼロを確認（unit / integration smoke のみでは close 不可）
4. **証拠アーカイブ**: `issues/closed/[ID].md` に コマンド出力 / ログ抜粋 / スクショパス / 実行時刻 / 関連 commit hash を添付。「目視確認した」「unit test PASS のみ」だけでは close 不可

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
1. `.tmp/handoffs/` 最新ファイルの**ファイル名のみ**を検出（本文は Read/注入しない）
2. `issues/processing/*.md` を全 scan し、各 issue の「タイトル」「最新 handoff のファイル名」を抽出（**本文は注入しない・ポインタのみ**）
3. 並走 4 軸 verdict（clean / 痕跡あり）と合わせ「中断作業 N 件あり。再開対象を user に確認し、選択された 1 件のみ本文 Read、または別 Agent に並列委任せよ（stale なものは注記）」と指示

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
- 受領: handoff は user 明示指示でのみ受領し、本文は再開対象に選ばれた 1 件のみ Read する（自動最新 Read はしない）
- 構成: ゴール / 完了したこと / 残課題 / 関連ファイル（path:line）/ 落とし穴

### 独自運用: 規約の hooks 化判断（advisory → deterministic 昇格）

CLAUDE.md / 本プロンプトに書いた規約は advisory なので、Claude が長文の中で見落とす可能性がある。次の判断基準で「確実に毎回動かしたい」規約は hook 化する。

**hooks 化候補の判断基準**:
- 同じ動作を毎セッション・毎タスクで漏れなく実行したい（例: session 開始時の中断作業ポインタ通知、関連 docs 読込宣言）
- ファイル命名・配置の規約違反を物理的に防ぎたい（例: handoff ファイル名の検証）
- 重要ファイル（CLAUDE.md / skills / commands）の更新後に必ずレビューを起動したい
- session 終了時に成果物の保存・整理を促したい

**hooks 設計指針**:
- スクリプト本体は `.claude/scripts/` に分離して `pwsh -NoProfile -File <path>` で呼ぶ（settings.json の JSON エスケープを避け、debug しやすくする）
- Windows 環境では各 hook 設定に `"shell": "powershell"` を明示する
- 各 hook イベントの出力契約（どの stdout が context 注入されるか / `additionalContext` JSON の要否 / `exit 2` の意味 / Stop の連続 block 上限）は **hook 生成直前に hooks reference を WebFetch で確認**する（焼き込まず現行仕様に従う）
- PreToolUse は `exit 2` + stderr で block。誤 reject を避けるため対象 path を厳密にフィルタする
- 各 script の冒頭で `[Console]::In.ReadToEnd() | ConvertFrom-Json` で event data を受け取り、`tool_input.file_path` でフィルタ
- `$ErrorActionPreference` は全域上書きせず、各 cmdlet の `-ErrorAction SilentlyContinue` で局所化（debug ログを潰さない）

**参考実装（5 hook 構成）**:

| イベント | 用途 | reject/notify |
|---|---|---|
| `SessionStart` | **ポインタと verdict のみ注入**: `.tmp/handoffs/` 最新の**ファイル名** + `issues/processing/*.md` 全 scan（タイトル + handoff ファイル名）+ 並走 4 軸 **verdict**（clean / 痕跡あり）。**本文は注入しない**（汚染防止）。再開対象は user 選択後にその 1 件のみ Read | notify |
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

レビュアに渡すのは **レビュー対象の完全パスと review skill の 2 点のみ**。レビュアは対象を自分で Read し（proof-by-presence で客観性確保）、評価基準は skill から取得する。実装意図・会話履歴・生成過程・本プロンプトは渡さない。公式が紹介する Writer/Reviewer pattern と整合する独自強化。

**レビュー強度の運用基準**（AIServer v4 第18条由来）:
- **並列本数**: 重要成果物（CLAUDE.md / skills / 破壊的変更）は独立エージェント **2〜4 本を並列起動**し、**converged findings（複数エージェントで一致した指摘）**を抽出する。Blocker は次工程前に修正。軽微な変更は 1 本で可
- **TDD test-first**: 実装コードを書く前に test を書き、修正前 test が **fail することを確認**してから実装に着手する（negative test の永続化を test 作成段階で保証）
- **ループ上限**: 計画レビュー最大 3 周・実装レビュー別カウントで最大 1 周。合計 4 周で収束しなければ scope 削減 or 別 Issue 分割に切替（iteration 発散防止。上図フローの skills レビュー「3 回 FAIL」とは別カウント — 上図は単一成果物の skills レビュー周回、本項は計画+実装を含む広義サイクルの上限）
- **自己レビュー不可**: 必ず別 subagent に分離する
- **過剰報告の抑制**（公式 adversarial review の注意・取得時に現行文言を確認）: reviewer は「gap を探せ」と指示されると健全な成果物でも何か報告しがち。**correctness と明示要件に関わる gap のみ採用**し、それ以外は optional 扱いとして over-engineering を避ける

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

### 独自運用: 成果物の生成主体明示（誤認防止）

テスト結果・成果物について、**LLM が生成したもの**か **script / template / library（pptxgenjs 等）が生成したもの**かを厳格に区別する（AIServer v4 第17条由来。汎用的な誠実性規律）。

- ファイル名・レポート・commit message・記事で生成主体を正確に記述する
- 複数ステージのテストは各ステージの成功 / 失敗を独立に記録する
- LLM が失敗し代替手段（script 直接実行等）で補完した場合は「LLM は失敗・代替手段で成功」と明記し、LLM の成功として扱わない
- 成果物のメタデータ（PPTX の `dc:creator`、生成ログ等）と主張内容を突合して検証する

曖昧な記述・ごまかしを避け、「動かさずにできたと言わない」（自検証）と対で運用する。

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
- **汎用規律条文の採否**（AIServer v4 由来の候補メニュー。各々を公式 Litmus Test に通し、プロジェクトが実際に採る規律だけを `code-quality.md` の条文にする）: モック / ハードコード禁止・バージョン番号付きファイル（`v2`/`_new`/`_old`）禁止・ルート直下への新規ファイル作成抑制・設定値の一元管理・一時しのぎでなく超長期的な根本解決
- **プロジェクトの目的**（このプロジェクトは何を解決しようとしているのか — 1〜2 文の課題定義）
- **進捗状況**（現在のフェーズ・主要マイルストーン達成状況・既知の未完了領域 — README / Issue / commit 履歴 / `issues/processing/*.md` から事実ベースで抽出）

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
| 時々しか使わない知識・ワークフロー | `.claude/skills/[name]/SKILL.md`（公式推奨。commands は skills に統合済 = `.claude/commands/x.md` と `.claude/skills/x/SKILL.md` は同じ `/x` を作る。frontmatter `name` は任意・`description` 推奨。現行仕様は skills docs を WebFetch で確認） |
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

生成物（CLAUDE.md + rules 6〜7 + settings.json hooks + hook scripts）を別エージェントに渡してレビューを受ける。渡すのは**対象の完全パスと review skill の 2 点のみ**（下記参照）。

レビュアが必ず実施すること（= review skill が内包する評価手順）:

1. **YOU MUST** `WebFetch` で `https://code.claude.com/docs/en/best-practices` を取得する（記憶ベースで判定しない）。冒頭に取得日時と主要原則の引用を出力する
2. 公式 Include/Exclude / Litmus Test / 5 配置 / `@import` / emphasis に対し 1 項目ずつ Y/N 評価
3. rules 6 ファイルが実在するか・条番号が通し管理されているかを Read で確認
4. 公式該当箇所と生成 CLAUDE.md 該当行を並べて示す

上記 1〜4 が **review skill が内包する評価手順**である（WebFetch 指示と評価基準は skill 側に含まれるため、URL や引用を別途渡さない）。レビュアに渡すもの（**2 点のみ**）: ① レビュー対象の**完全パス**（生成 CLAUDE.md + rules 6〜7 + settings.json + hook scripts の絶対パス。中身はインライン貼付せず、レビュアが自分で Read する）② 適用する **review skill 名**。渡さないもの: ファイル中身のインライン貼付・公式 URL や引用・本プロンプト・生成過程・会話履歴。

合格基準: 公式項目全 Y かつ 90 点以上、かつ冒頭で WebFetch 取得日時引用がある。Web 取得していないレビューは無効、再依頼する。

不合格時: 修正して再レビュー。**3 回 FAIL で `issues/open/[YYYY-MM-DD]-claude-md-generation.md` 起票・中断・ユーザーに報告**。

#### Step 8: 出力 & 標準セット 4 種の実生成 + 引継ぎ

レビュー合格後、project の事実に合わせて **標準セット 4 種を実生成**する（Step 1 で集めた事実から条文・規約・hook を埋める）:

1. **CLAUDE.md 本体** — 出力テンプレートに project 固有値（プロジェクト名・一行サマリ・コマンド・ルート構成・末尾入口リンク）を埋めて生成

2. **`.claude/rules/*.md` 6 ファイル + オプション 1 ファイル** — Step 1 事実から条文を抽出して生成（条番号は通し管理・ファイル間で重複させない）:

   | ファイル | 内容 | YAML frontmatter | load |
   |---|---|---|---|
   | `meta.md` | 第1〜N条インデックス（条見出し + 所在ファイル）+ **既知の制約（[claude-code Issue #23478](https://github.com/anthropics/claude-code/issues/23478) の path-scope auto-load Read 時のみ発火 bug を URL 付きで明記）** + **常時 load ファイル 5KB soft cap 宣言**（第24条 F 項） | なし | 常時 |
   | `code-quality.md` | コード変更規約（命名・import・型）の条文 | `description` のみ | `@import` で常時 |
   | `test-verify.md` | テスト・自検証規約（ランナー・lint・受入基準・**close 前検証 4 段**［再現→pass / negative test / regression smoke / 証拠アーカイブ］・**成果物の生成主体明示**［LLM 生成物 vs script/lib 生成物の厳格区別］）の条文 | `description` のみ | `@import` で常時 |
   | `issue-workflow.md` | Issue 起票・handoff・/clear 規約の条文（**並走 agent 痕跡 4 軸 recheck**・stale handoff 誤受領防止・90 日 archive 含む） | `paths: ["issues/**", ".tmp/**"]` | path-scope |
   | `review.md` | 別エージェントレビュー規約の条文（**2〜4 本並列 + converged findings**・**TDD test-first**・ループ上限［計画 3 周 / 実装 1 周］・自己レビュー不可・**渡すのは対象完全パス + review skill のみ**） | `paths: ["**/*.<lang>", ".claude/commands/**"]` | path-scope |
   | `governance.md` | 肥大化防止・新項目追加規約の条文を **第24条 A〜F の 6 項目構造**（A サイズ閾値 / B 新項目ルーティング / C 公式準拠 / D 定期レビュー / E 自動検証 / F 常時 load 5KB cap）で記述 | `paths: ["CLAUDE.md", ".claude/**"]` | path-scope |
   | `docs-management.md`（**オプション**: `docs/` 配下に 5 section 以上ある場合のみ） | docs 配置 mapping（section リスト + 各 section の対象範囲）+ 新 docs 配置 flow（既存 section 該当判定 → なければ Issue 起票で section 配置を converge）+ 全 section README 必須化 + **4 箇所同期更新義務**（rule mapping / validate script / INDEX / generator）+ 過時マーカー "as of YYYY-MM-DD" 強制 | `paths: ["docs/**/README.md", "docs/**/*.md", "CLAUDE.md", ".claude/rules/governance.md"]` | path-scope |

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
   - `hook-session-start.ps1` — ポインタ（handoff ファイル名 + `issues/processing/*.md` のタイトル）と並走 4 軸 verdict のみ注入（**本文は Read/注入しない**）。検出時は (a)hold+確認 (b)引継ぎ切替 (c)scope 弁別 (d)handoff 明示を促す。本文は user 選択後にその 1 件のみ Read（PC 再起動復元 + 並走衝突防止 + context 汚染防止）
   - `hook-user-prompt-submit.ps1` — `docs/*.md` 直近 3 ファイルを context 注入
   - `hook-pre-tool-use-handoff.ps1` — handoff 命名規約 `[YYYY-MM-DD]-issue-[ID]-[kebab].md` 検証、違反なら `exit 2` + stderr で reject
   - `hook-post-tool-use.ps1` — CLAUDE.md / `.claude/skills/**` / `.claude/commands/**` 編集時に `hookSpecificOutput.additionalContext` JSON で公式 WebFetch レビュー reminder
   - `hook-stop.ps1` — 1 時間以上未更新 handoff があれば更新リマインド

   各 script 冒頭で `[Console]::In.ReadToEnd() | ConvertFrom-Json` から `tool_name` / `tool_input.file_path` を取り、`-ErrorAction SilentlyContinue` は cmdlet 単位で局所化する。

**ユーザーへの最終報告**:
- **プロジェクト概要**（プロジェクト未読の第三者が読んでも内容を理解できるレベルで書く。Step 1 で収集した事実のみを使い、推測・捏造はしない）:
  - **大まかな説明** — このプロジェクトは何を解決しようとしているのか（1〜2 文の課題定義 + 解決アプローチの要点）
  - **細かな説明** — 主要機能・技術スタック・想定ユーザー・スコープ境界（箇条書き 5〜10 項目）
  - **進捗状況** — 現在のフェーズ（PoC / α / β / 本番運用 等）・直近で達成したマイルストーン・既知の未完了領域・進行中 Issue 件数（`issues/processing/*.md` の実数）
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

1. 関連 docs 読込宣言（第15条 + 第23条）: 該当 docs を最低 1 つ Read し「完全パス + 1 文要約 + タスク関連性 1 文」を**宣言の最初と最後の両方**に出力する（最初 = 根拠表明、最後 = 実際に踏まえた証跡）
2. 条文宣言（第1条 lazy load 運用）: タスク該当ルール（下表）のみ宣言してから着手する。**全条一括宣言は不要**
3. 作業 → 自検証 → 他者レビュー（別エージェント）を作業節目で実施する。CLAUDE.md / skills 更新時は公式準拠を WebFetch ベースでレビュー（skills→`/review-skill` 90 点合格／3 回 FAIL で `issues/open/[ID].md` 起票・中断）
4. session 開始時（新規 chat / `/clear` 直後）: handoff は **user 明示指示でのみ受領**（最新を自動 Read しない）。hook が提示するポインタ + 並走 4 軸 verdict を見て、user が再開対象を選んだら**その 1 件のみ本文 Read**（stale = 7 日以上前 / 完了済 / 次 session 不要 は選ばない）。受領後は役割のみ実施・scope creep を避ける
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
| 9a | handoff は user 明示指示で受領し本文は選択 1 件のみ Read（最新を自動 Read しない）運用が `issue-workflow.md` に明記されている |  |
| 9b | handoff 命名規約（`[YYYY-MM-DD]-issue-[ID]-[識別単語].md`、識別単語は 2〜4 語 kebab-case）が明記 |  |
| 9c | handoff 保持規約（次 handoff 作成まで前 handoff を削除しない）が明記 |  |
| 9d | issue ファイル連携（`issues/open|processing/[ID].md` 冒頭に進行中 handoff の完全パス記載）が明記 |  |
| 9e | 各 issue ファイル冒頭ヘッダ（タイトル / 概要 1〜2 行 / 状態 / 最新 handoff 完全パス / 起票日）の標準形式が明記され、handoff 更新時の同期更新ルールがある |  |
| 9f | issues/ 3 段階フォルダ管理（open → processing → closed の git mv 遷移）と問題発見即起票（scope creep 禁止・現タスクで触らない）が独立セクションとして明記されている |  |
| 16 | PC 再起動・session 復元の自動化（SessionStart hook はポインタ + verdict のみ注入＝本文を注入しない、`issues/processing/*.md` 全 scan で User 通知 → 選択後 1 件のみ Read + 並列委任）が独立セクションで明記されている |  |
| 17 | Step 8 で標準セット 4 種（CLAUDE.md + rules 6 ファイル + settings.json hooks + hook scripts 5）の **実生成手順** が明記され、雛形が示されている |  |
| 10 | 詳細ルールは別ファイルに分離 or リンクのみ |  |
| 11 | 意思決定支援（decision tree / 前提条件表 / ルール参照テーブル）が 1 つ以上 |  |
| 12 | 「新しい○○を追加する手順」のガバナンスがある |  |
| 13 | emphasis（IMPORTANT / YOU MUST）出現が 5 件以下に絞られている（公式 emphasis ガイダンスに沿う） |  |
| 14 | 進行中タスク・TODO・バージョン番号など陳腐化情報なし |  |
| 15 | 確実に毎回実行したい advisory ルールが hooks 化候補として識別され、settings.json の hooks に登録されている（または該当なしと宣言されている） |  |
| 18 | `meta.md` 末尾「既知の制約」に [claude-code Issue #23478](https://github.com/anthropics/claude-code/issues/23478) が URL 付きで明記され、`@import` 一次防御 + 第23条手動 Read 二次防御の二重防壁の理由が説明されている |  |
| 19 | `governance.md` が **第24条 A〜F の 6 項目構造**（A サイズ閾値 / B 新項目ルーティング / C 公式準拠 / D 定期レビュー / E 自動検証 / F 常時 load 5KB cap）で記述されている |  |
| 20 | `meta.md` / `@import` で常時 load される rules ファイル個別に **5KB soft cap**（第24条 F 項）が宣言されている |  |
| 21 | 関連 docs 読込宣言が**最初と最後の両方**に「完全パス + 1 文要約 + タスク関連性 1 文」を出力する形（第15条 + 第23条）になっている |  |
| 22 | 条文宣言が **lazy load 運用**（タスク該当条のみ宣言・全条一括宣言は不要・第1条）になっている |  |
| 23 | `docs/` 配下に 5 section 以上ある場合は **`docs-management.md` 7 ファイル目**（docs 配置 mapping / 新 docs 配置 flow / 全 section README 必須化 + 4 箇所同期更新義務 / 過時マーカー）が生成されている。該当しない小規模プロジェクトでは「不要」と明示宣言されている |  |

| 24 | 並走 agent 痕跡 4 軸 recheck（git log / handoff・plan / worktree / git status の 2 境界実行 + 検出時 action a〜d）が `issue-workflow.md` に明記され、SessionStart hook に **verdict のみ注入**の形で組込まれている |  |
| 25 | 成果物の生成主体明示（LLM 生成物 vs script/lib 生成物の厳格区別・メタデータ突合）が `test-verify.md` に明記されている |  |
| 26 | close 前検証 4 段（再現→pass / negative test / regression smoke / 証拠アーカイブ）が `test-verify.md` または issue lifecycle に明記されている |  |
| 27 | 別エージェントレビューが 2〜4 本並列 + converged findings 抽出・TDD test-first・ループ上限（計画 3 / 実装 1）で `review.md` に明記され、レビュアに渡すのは**対象完全パス + review skill のみ**になっている |  |
| 28 | stale handoff（7 日以上前 / 完了済 / 次 session 不要）を提示時に注記し user が誤選択しないようにする設計が明記されている |  |
| 29 | 公式（best-practices / skills / hooks）の文言・テーブル・数値・API 契約を本プロンプトに焼き込まず、生成・レビュー開始時に WebFetch で取得し現行版で判定する設計（焼き込み版が残っていない） |  |
| 30 | reviewer への過剰報告抑制（reviewer は gap を過剰報告しがち → correctness と明示要件に関わる gap のみ採用）が明記されている |  |

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
- [ ] 公式内容（文言・テーブル・数値・API 契約）を焼き込まず実行時 WebFetch 取得に統一されているか（verbatim・テーブル転記が残っていないか）
- [ ] handoff 受領が user 明示指示駆動で、SessionStart hook がポインタ + verdict のみ注入（本文を注入しない）になっているか
- [ ] reviewer 過剰報告抑制（correctness / 明示要件に関わる gap のみ採用）が含まれているか
- [ ] 行数による出力拒否ゲートが残っていないか（公式は数値閾値を持たない）
- [ ] hooks 化判断セクションがあり、5 hook 参考構成と監査手順（dead/無駄 hooks 検出）が含まれているか
- [ ] PC 再起動・session 復元（SessionStart hook は processing scan をポインタ + verdict のみ注入＝本文非注入 → User 通知 + 選択後 1 件のみ Read + 並列委任）が含まれているか
- [ ] Step 8 で標準セット 4 種（CLAUDE.md / rules 6 / settings.json hooks + hook scripts 5）の実生成手順と雛形が含まれているか
- [ ] [claude-code Issue #23478](https://github.com/anthropics/claude-code/issues/23478) の path-scope auto-load Read 時のみ発火 bug が URL 付きで明示されているか
- [ ] `governance.md` 生成指示が第24条 A〜F の 6 項目構造で記述されているか
- [ ] 常時 load rules ファイル個別の 5KB soft cap（第24条 F 項）が明示されているか
- [ ] `docs-management.md` のオプション扱い（採用判定基準と生成内容）が明示されているか
- [ ] 関連 docs 読込宣言が「最初と最後の両方」（第15条 + 第23条）になっているか
- [ ] 条文宣言の lazy load 運用（全条一括宣言は不要・第1条）が明示されているか
- [ ] 並走 agent 痕跡 4 軸 recheck（第22条 V）が独自運用 + hook 仕様 + テンプレートに含まれているか
- [ ] 成果物の生成主体明示（第17条）が独自運用 + test-verify.md 生成指示に含まれているか
- [ ] close 前検証 4 段（第21条: 再現→pass / negative test / regression smoke / 証拠アーカイブ）が含まれているか
- [ ] 別エージェントレビューが 2〜4 本並列 + TDD test-first + ループ上限（第18条）で記述され、レビュアに渡すのが対象完全パス + review skill のみになっているか
- [ ] stale handoff 誤受領防止（第22条 V）が含まれているか

---
*準拠ソース: https://code.claude.com/docs/en/best-practices "Write an effective CLAUDE.md"*
