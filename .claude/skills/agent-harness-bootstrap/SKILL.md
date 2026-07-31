---
name: agent-harness-bootstrap
description: 任意のプロジェクトに対し、Anthropic 公式 Best Practices（"Write an effective CLAUDE.md"）に準拠した CLAUDE.md と、それを支える運用 harness（rules ファイル群 + hooks）を生成・剪定する。「CLAUDE.md を作って」「`/init` の代わりに公式準拠で」「CLAUDE.md を書き直して」「肥大化したので剪定」などで発動。公式準拠の核と、独自の運用ノウハウをラベル分離して適用する。
---

# CLAUDE.md 生成 harness

任意のプロジェクトに対し、Anthropic 公式 Best Practices（[Write an effective CLAUDE.md](https://code.claude.com/docs/en/best-practices#write-an-effective-claude-md) / [Skills](https://code.claude.com/docs/en/skills)）に準拠した `CLAUDE.md` を生成する。**公式準拠の核**と**本スキル独自の運用ノウハウ**をラベル分離して適用する。

> 本スキルが提示する運用構造（rules 分離・条文の通し番号管理・hooks による自動化）は、特定のプロダクトを前提としない**一般的な設計原則**として整理したものである。特定の社内実装を「実証済みの参照実装」として引用しない。設計判断の根拠は、外部実装の存在や実績ではなく、各原則自身の合理性（公式ドキュメントとの整合・観察可能な失敗パターンの回避）に置く。

## 使うタイミング

- 「CLAUDE.md を作って」「`/init` の代わりに公式準拠で生成して」
- 「既存の CLAUDE.md を公式 Best Practices で書き直して」
- 「CLAUDE.md が肥大化したので剪定して」

**使わない時**: コード自体を書く時、Skills (`.claude/skills/`) を作る時、README を書く時。

## 参照ファイル（progressive disclosure）

詳細な素材は同ディレクトリの supporting files に分離する。本体からは以下を参照する:

| ファイル | 内容 | 使う場面 |
|---|---|---|
| `template.md` | CLAUDE.md 本体の出力テンプレート（雛形） | Step 4 |
| `rubric.md` | 自己評価ルーブリック 35 項目（Y/N） | Step 5 / Step 7 |
| `hooks-reference.md` | hooks 化判断・参考 5 hook 構成・settings.json 例・hook script 雛形（PowerShell / bash） | Step 8-3 |
| `maintainer-checklist.md` | 本スキル更新者向けメンテ checklist（生成物評価には無関係） | 本スキル改修時 |

---

## 公式準拠の核（実行時 WebFetch 必須・本スキルに焼き込まない）

> Anthropic 公式は随時更新される。**公式の文言・テーブル・数値・API 契約を本スキルに転記（焼き込み）しない**。生成・レビュー開始時に下記を WebFetch で取得し、その時点の現行版で判定する（記憶・過去の引用で代替しない。WebFetch 失敗時は焼き込み版で代替せず、取得できるまで生成を中断する）。
>
> 焼き込み禁止の根拠は公式 Exclude 項目「Information that changes frequently」と同根。過去に転記した Include/Exclude テーブルが現行公式とドリフトした実例があり、転記は腐る。

### 取得対象と確認項目（名称のみ列挙・本文/テーブル/数値は取得して読む）

| URL | 取得時に現行版を確認する項目 |
|---|---|
| `https://code.claude.com/docs/en/best-practices`（"Write an effective CLAUDE.md" / "Avoid common failure patterns" / "Add an adversarial review step"） | Litmus Test の文言 / Include・Exclude テーブルの現行内容 / サイズ・行数の記述（数値閾値の有無）/ emphasis ガイダンス / 5 配置 + `@path` import / hooks（advisory との対比）/ Writer-Reviewer・adversarial review の注意（reviewer は gap を過剰報告しがち → correctness と明示要件に関わる gap のみ採用） |
| `https://code.claude.com/docs/en/skills` | SKILL.md 必須・frontmatter（`name` 任意 / `description` 推奨 / `description`+`when_to_use` の文字数上限）/ 本文の recurring token cost と簡潔性 / progressive disclosure（supporting files で参照分離）/ SKILL.md 行数の目安 / commands と skills の統合 / `disable-model-invocation` 等 |
| `https://code.claude.com/docs/en/hooks`・`https://code.claude.com/docs/en/hooks-guide` | hook イベント別の出力契約（どの stdout が context 注入されるか / `exit 2` の意味 / `additionalContext` JSON / Stop の連続 block 上限など、hook 生成直前に現行仕様を確認） |

取得後、冒頭に「取得日時 + 確認した現行原則の要点」を出力してから生成・レビューに進む。この WebFetch は省略しない。

### 本スキル由来の独自運用基準（公式転記ではない・保持する）

公式の文言ではなく本スキル由来の運用判断。公式が変わっても独自基準として有効だが、取得時に公式と矛盾しないか都度突合する:

- **emphasis（IMPORTANT / YOU MUST）は最大 5 件目安**。それ以外の語気強め（必須・禁止・絶対）は平叙文化する（公式 emphasis 許容を運用上引き締めた独自基準）
- **行数による出力拒否ゲートを設けない**。公式が数値閾値を持たないことを取得時に確認した上で、剪定判断は "rules getting lost in the noise" の兆候を主基準にする（数値は参考値）

---

## 本スキル独自の運用ノウハウ

> 公式には記述がない本スキルの設計判断。プロジェクトに合わせて緩めてよい。各項目は「何をするか」を主体に記す。

### 独自運用: 規模に応じたスケール調整（過剰生成を避ける）

本スキルの構造は「フル装備」の上限像である。生成の最初に、以下のスケールダウン判断を明示的に行う（消したら Claude がミスする / 規律が失われる要素だけを残す）:

- **rules ファイルは、該当する条文が実際に存在するものだけ生成する**（条文ゼロのファイルを空作成しない。後で必要になったら追加する）
- **hooks は「確実に毎回実行したい規律」が実在する時だけ導入する**（単発・並走なしの個人開発では SessionStart hook や並走痕跡検出は不要）
- **オプションファイル（`docs-management.md` / `execution-routing.md`）は採用判定に通ったものだけ生成する**

標準セットは**上限（あり得る最大構成）**であって**必須の下限ではない**。

### 独自運用: サイズの目安（参考値・硬性基準ではない）

| レベル | 対象 | 目安 | 対応 |
|------|------|------|------|
| 剪定検討 | CLAUDE.md 本体 | 概ね 100 行 / 10KB を超え始めたら | Litmus Test で再評価。挙動が変わらないルールが埋もれていないか観察 |
| 分割推奨 | CLAUDE.md 本体 | Claude が指示を無視し始める兆候が出たら | rules / skills / docs へ分割 |
| 常時 load rules 個別 cap | `meta.md` / `@import` で常時 load される rules 個別 | **5KB soft cap**（独自強化） | cap 超過時は条文を path-scope rules に逃がすか、長文条文を docs/ に分離してリンク化 |

判定は数値より「公式 *"rules getting lost in the noise"* 兆候の有無」を主基準にする。閾値を設定する場合は「早期気付き warning + 構造見直し fail の二段構え」が汎用的に有効（数値は硬性化しない）。

### 独自構造: 標準セット（フル装備・規模に応じて間引く）

CLAUDE.md は単体ではなく次のセットで構成しうる（あり得る最大構成・不要要素は落とす）:

| セット | 役割 | 採用の目安 |
|---|---|---|
| `CLAUDE.md` 本体 | インデックス + 起動時必須手順 + ルール参照テーブル + ルート構成 + 末尾入口リンク | 常に生成 |
| `.claude/rules/*.md`（コア） | 規約本文（条文方式・通し番号管理） | 該当条文が存在するものだけ生成 |
| `.claude/settings.json` の `hooks` | advisory ルールの deterministic 化 | 「毎回確実に実行したい規律」がある時のみ |
| `.claude/scripts/hook-*` | hooks 本体スクリプト（OS に応じ PowerShell / bash） | hooks を採用する時のみ |

コア rules ファイルとオプションファイルの内訳:

| ファイル | 役割 | load 戦略 |
|---|---|---|
| `meta.md` | 条番号インデックス・既知の制約（下記 Issue #23478 等） | 常時 load |
| `code-quality.md` | コード変更時の規約 | `@import` で常時 load |
| `test-verify.md` | テスト・自検証規約 | `@import` で常時 load |
| `issue-workflow.md` | Issue 起票・handoff・`/clear` | `paths:` で path-scope |
| `review.md` | 別エージェントレビュー規約 | `paths:` で path-scope |
| `governance.md` | 肥大化防止・新項目追加規約 | `paths:` で path-scope |
| `execution-routing.md`（**オプション**） | タスクをどの実行主体・モデル格に振るかの規約 | `@import` で常時 load |
| `docs-management.md`（**オプション**） | docs 配置 mapping / 新 docs 配置 flow / 全 section README 必須化 + 同期更新義務 / 過時マーカー強制 | `paths:` で path-scope |

**`execution-routing.md` 採用判定**: 複数の実行主体（人手 / 複数 AI エージェント / 異なるモデル格）に振り分ける運用があるプロジェクトで採用する。単一実行主体の小規模プロジェクトは不要。

**`docs-management.md` 採用判定**: `docs/` 配下に **複数 section（概ね 5 以上）**があり、複数箇所で同じ section リストを SoT として保持するプロジェクトでのみ採用する。単一 `docs/README.md` で完結する小規模は不要。

`paths:` frontmatter を `@import` と併用する理由: path-scope rules auto-load が **Read 時のみ発火、Write/Create 時には発火しない**既知 bug（[claude-code Issue #23478](https://github.com/anthropics/claude-code/issues/23478)）への補償。`@import` を一次防御、タスク開始時の手動 Read を二次防御とする二重防壁にする。生成 rules の `meta.md` 末尾「既知の制約」にも Issue URL を明記する。

### 独自運用: 実行主体・モデル格の振り分け規約（`execution-routing.md`）

複数の実行主体・モデル格を使い分けるプロジェクトでは、採用時に以下の骨子を条文化する（命名・段階数は実態に合わせる）:

- **司令塔の役割定義**: (1) 方針決定・複数案比較・設定変更・成果物統合は司令塔が直轄、(2) 実行作業は分解して下位主体へ委任、(3) 委任成果物は必ず司令塔が確認してから統合、の 3 責務を明記する
- **振り分け表**: 「定型・低難度 → 低コスト実行主体」「高難度実行 → 高コスト実行主体」「方針・統合 → 司令塔自身」を、実際に使う主体名で表にする
- **高コスト主体の抑制**: 単純編集・要約・定型変換・初期ドラフト・既存ルール準拠作業に高コスト主体を使わない。高コスト委任時は dispatch に「なぜ低コストでは不十分か / 範囲 / 期待成果物 / 完了条件 / 司令塔の最終確認観点」を明示させる（証跡化）
- **escalation protocol**: 委任先が設計変更・セキュリティ・複数ファイル間矛盾・影響拡大に遭遇したら作業を止めて司令塔へ返す。契約（目的 / 範囲 / 完了条件）が欠落した dispatch を受けた主体は作業せず「契約不備」だけを返す
- **default**: 迷ったら低コスト主体を先に試し、行き詰まった時のみ上位へ escalation する

「全部直轄」「全部高コスト主体」判定は本規約の趣旨（コスト最適化）に反するため gameability 防壁として禁止する。

### 独自運用: 関連 docs 読込宣言

Claude はタスク開始時に関連 docs を最低 1 つ読み、**宣言の最初と最後の両方**に **完全パス + 1 文要約 + タスク関連性 1 文** を出力する。最初 = 「何の根拠で動くか」、最後 = 「実際に何を踏まえたか」の証跡二重化。片方だけだと「宣言はしたが読んでいない / 途中で逸脱した」ケースを検出できない。

### 独自運用: 条文宣言の lazy load 運用

「タスク該当ルールを宣言してから着手」と書く時、**全条一括宣言は不要**にする。`meta.md` の条番号インデックスを参照し、タスクに該当する条のみ宣言する。「念のため全条宣言」は宣言を長文化させ、Claude が自分の宣言を無視する原因になる。

### 独自運用: governance.md の項目群

`governance.md` を生成する時、肥大化防止規約は「サイズ」以外の腐敗経路も塞ぐよう複数観点を項目立てる（項目数は必要に応じ増減）:

| 観点 | 内容 | 例 |
|---|---|---|
| サイズ閾値 | CLAUDE.md 本体の warning / fail 行数・KB | 早期 warning + 分割 fail の二段 |
| 新項目ルーティング | 「CLAUDE.md に書きたくなった」時の振り分け先 | 原則→rules / 手順→docs / オンデマンド→skills / 過渡→`.tmp/` / 全タスク必須のみ CLAUDE.md 直接記入可 |
| 公式準拠 | 新 `.claude/` subdir は公式定義（rules/skills/commands/agents）のいずれかに限定 | `docs/`, `tmp/` 等を `.claude/` 直下に作らない |
| 定期レビュー | 公式 docs ドリフト検出のための定期点検 | 定期的に公式 Best Practices を WebFetch + ドリフト改修計画 |
| 自動検証 | サイズ閾値・命名規約の hook / CI 検証 | `PreToolUse(Write)` で命名検証、`PostToolUse(Edit)` でサイズ警告 |
| 常時 load ファイルの cap | `meta.md` + `@import` で常時 load される rules 個別の cap | 各 5KB soft cap、超えたら path-scope rules に逃がす |

サイズ閾値だけでは `@import` 常時 load rules 経由の context 汚染を防げない。「常時 load ファイルの cap」観点が context 汚染を構造的に塞ぐ最も効く一手になる。

### 独自運用: handoff 受領（user 明示指示駆動・本文は自動 Read しない）

handoff は **user の明示指示でのみ受領**する（① user が chat に paste、または ② 「handoff X を読んで」と指示）。**最新 handoff の本文を session 開始時に自動 Read しない**（無関係な最新 handoff の誤受領と、本文の毎 session 注入による context 汚染を防ぐ）。受領後は役割のみ実施・scope creep を避け、関連気付きは別 Issue 起票する。

SessionStart hook は**本文を注入せず、ポインタと verdict のみ通知する**: 中断作業の一覧（issue タイトル + handoff ファイル名のみ）と並走 4 軸 verdict（clean / 痕跡あり）を提示し「どれを再開しますか？」と問う。**本文 Read は user が再開対象を選択した後にその 1 件だけ**行う。

**stale handoff 誤受領防止**: 提示する handoff のうち **7 日以上前 / 既に「## 完了」marker 済 / 「次 session 不要」明記**のものは "stale" と注記する。**archive ローテーション**: 一定期間（例: 90 日）経過した handoff は `.tmp/archive/handoffs/` に退避し context 肥大化を防ぐ。

### 独自運用: 並走 agent 痕跡 4 軸 recheck（並走衝突防止）

複数 agent / session が同一リポジトリで並走する運用では、着手前に並走痕跡を検出して衝突（同一作業の重複着手・成果物の相互破壊）を防ぐ。並走が起こり得ない単発運用では省略してよい。

**検出する 2 境界**: (A) session 開始時 / handoff 受領直後（新規 chat・`/clear` 直後、条文宣言の前）、(B) plan 起票前（`.tmp/plans/<id>.md` Write 前）。

**4 軸 literal command**（bash / PowerShell 両対応。shell redirect は環境に合わせる: bash `2>/dev/null` / PowerShell `2>$null` または `-ErrorAction SilentlyContinue`）:

| 軸 | 検出対象 | command（bash 例） |
|---|---|---|
| axis 1 | 同 Issue の並走 commit | `git log -10 --all --oneline -- <issue_path>` |
| axis 2 | 同 Issue の handoff / plan | `ls -t .tmp/handoffs/*<id>*.md`、`ls -t .tmp/plans/*<id>*.md` |
| axis 3 | 並走 worktree | `git branch --show-current && git worktree list` |
| axis 4 | 別 session の uncommitted Edit | `git status --short` |

**痕跡検出時の action**: (a) 着手 hold + User 確認 / (b) 既存 work 引継ぎへ切替（自分の plan 撤回）/ (c) scope 重複 vs complementary 弁別 / (d) handoff index に並走痕跡を明示。

**読込宣言への統合**: 証跡 3 要素（完全パス + 1 文要約 + タスク関連性）に「**並走痕跡 4 軸 clean 確認済**」を 4th 要素として加える。4 軸全 clean 確認後のみ着手を継続する。enforcement は SessionStart hook（hook + 手動宣言の二重防壁）。

### 独自運用: issue ライフサイクル管理（open → processing → closed）

タスク・問題は `issues/` 配下の 3 段階フォルダで状態管理する:

| フォルダ | 状態 | 配置タイミング |
|---|---|---|
| `issues/open/[ID].md` | 未着手 | 問題発見・新タスク要求時の起票先 |
| `issues/processing/[ID].md` | 着手中 | open から `git mv` で移動。冒頭に進行中 handoff の完全パスを記載 |
| `issues/closed/[ID].md` | 完了 | processing から `git mv` で移動。下記 close 検証 4 段を本文末に証拠付きで宣言 |

**close 前検証 4 段**（「修正したつもり」「regression 未確認 close」を構造的に排除する）:
1. **再現 → 修正後 pass**: 元 bug の再現条件で修正後に再実行し、症状消失を ログ / 出力 / スクショ / テスト結果ファイル のいずれかで証拠記録
2. **negative test（regression 防壁化）**: 修正を意図的に外す or 旧 commit に戻して fail することを確認し、test が真に bug を捕捉する保証を残す。可能なら自動テストとして永続化
3. **他機能 regression smoke**: 影響範囲の関連機能を実機で run し症状ゼロを確認（unit / integration smoke のみでは close 不可）
4. **証拠アーカイブ**: `issues/closed/[ID].md` に コマンド出力 / ログ抜粋 / スクショパス / 実行時刻 / 関連 commit hash を添付。「目視確認した」「unit test PASS のみ」だけでは close 不可

**問題発見即起票ルール**: タスク中に別バグ・改善・気付きを発見しても**現タスクで触らない**。事実だけを `issues/open/[ID].md` に起票して元のタスクに戻る（現タスク差分の肥大とロールバック困難を防ぎ、レビュー単位を 1 issue = 1 目的に保つ）。

**1 issue = 1 目的**: 1 つの issue に複数目的を混ぜない。関連する別目的は新 issue として起票する。

**handoff と issue の関係**: issue = タスクの正本（要件・受入基準・履歴。状態遷移は git mv で記録）、handoff = 進行中の引継ぎメモ。`issues/processing/[ID].md` 冒頭に進行中 handoff の完全パスを記載し、handoff ファイル名も `issue-[ID]` を含めて相互参照する。

**各 issue ファイル冒頭の標準ヘッダ**（open / processing / closed 共通）:

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

handoff 更新のたびに該当 issue の「最新 handoff」行も同期更新する（issue を開けば説明と最新 handoff の場所が即分かる = issue ファイル単独で再開可能）。

### 独自運用: PC 再起動・session 復元の自動化

PC 再起動 / session 切断後に進行中タスクを自動検出し、User に通知して並列委任できる仕組み。

**SessionStart hook の責務**（matcher: `startup|resume|clear|compact`）:
1. `.tmp/handoffs/` 最新ファイルの**ファイル名のみ**を検出（本文は Read/注入しない）
2. `issues/processing/*.md` を全 scan し、各 issue の「タイトル」「最新 handoff のファイル名」を抽出（**本文は注入しない・ポインタのみ**）
3. 並走 4 軸 verdict と合わせ「中断作業 N 件あり。再開対象を user に確認し、選択された 1 件のみ本文 Read、または別 Agent に並列委任せよ（stale は注記）」と指示

**並列委任パターン**: 各 issue を個別 Agent に渡す場合、`Agent` ツールで以下のみ提供する: handoff の完全パス（再解釈・補完なしで本文をそのまま信頼させる）/ issue の完全パス / 役割範囲（scope creep を避ける指示）。

### 独自運用: handoff 管理（命名・保持・issue 連携）

- ファイル名: `[YYYY-MM-DD]-issue-[ID]-[識別単語].md`（issue 紐付けあり）／ `[YYYY-MM-DD]-[識別単語].md`（紐付けなし）。識別単語は 2〜4 語 kebab-case、作業内容が一目で分かるもの
- 保持: 次の handoff を新規作成するまで前 handoff は削除しない。次 handoff 作成時に削除またはアーカイブする
- issue 連携: `issues/open|processing/[ID].md` 本文冒頭に「進行中 handoff: [完全パス]」を記載。handoff 更新時は issue 側も同期更新する
- 受領: handoff は user 明示指示でのみ受領し、本文は再開対象に選ばれた 1 件のみ Read する
- 構成: ゴール / 完了したこと / 残課題 / 関連ファイル（path:line）/ 落とし穴

### 独自運用: 規約の hooks 化判断（advisory → deterministic 昇格）

CLAUDE.md に書いた規約は advisory なので Claude が長文中で見落としうる。「確実に毎回動かしたい」規約は hook 化する。ただしスケール調整に従い、**該当する規律が実在する時だけ導入**する（単発・並走なしの小規模開発では省略してよい）。hooks 化候補の判断基準・設計指針・参考 5 hook 構成・監査手順・OS 別 shell 実装・hook script 雛形は **`hooks-reference.md` を参照**する。

### 独自運用: 別エージェントレビューサイクル

成果物（実装・設計・docs・**CLAUDE.md・skills**）は実行後に別エージェントからレビューを最低 1 回受ける。

```
[実行] → [別エージェント レビュー] → 合格?
                                     ├─ Yes → 完了
                                     └─ No  → 修正して再レビュー（最大 3 回）
                                                  3 回 FAIL → issues/open/[ID].md 起票・中断
```

レビュアに渡すのは **レビュー対象の完全パスと、適用するレビュー用 skill / コマンドの 2 点のみ**。レビュアは対象を自分で Read し（proof-by-presence で客観性確保）、評価基準は skill から取得する。実装意図・会話履歴・生成過程・本スキルは渡さない。公式の Writer/Reviewer pattern と整合する独自強化。

**レビュー強度の運用基準**:
- **並列本数**: 重要成果物（CLAUDE.md / skills / 破壊的変更）は独立エージェント **2〜4 本を並列起動**し、**converged findings（複数エージェントで一致した指摘）**を抽出する。Blocker は次工程前に修正。軽微な変更は 1 本で可
- **TDD test-first**: 実装コードを書く前に test を書き、修正前 test が **fail することを確認**してから実装に着手する
- **ループ上限**: 計画レビュー最大 3 周・実装レビュー別カウントで最大 1 周。合計 4 周で収束しなければ scope 削減 or 別 Issue 分割に切替（上図フローの skills レビュー「3 回 FAIL」とは別カウント — 上図は単一成果物の周回、本項は計画+実装を含む広義サイクルの上限）
- **自己レビュー不可**: 必ず別 subagent に分離する
- **過剰報告の抑制**（公式 adversarial review の注意・取得時に現行文言を確認）: reviewer は「gap を探せ」と指示されると健全な成果物でも何か報告しがち。**correctness と明示要件に関わる gap のみ採用**し、それ以外は optional 扱いとして over-engineering を避ける

**対象別の評価基準**:

| 成果物 | 公式 / 評価基準 | 推奨レビュー手段 |
|------|--------------|----------|
| CLAUDE.md | Anthropic 公式「Write an effective CLAUDE.md」 | プロジェクトのレビュー用 skill / コマンド・Step 7 の WebFetch レビュー |
| `.claude/skills/*/SKILL.md` | Anthropic 公式 Skills 作成ガイド | 同上（skill レビュー用コマンド） |
| `.claude/commands/*.md`（slash command） | 同上 + 公式 commands 仕様 | 同上 |
| 実装コード | プロジェクト規約 + テスト戦略 | コード変更レビュー用コマンド |
| 提案書・docs | プロジェクト個別の評価基準（`docs/review-*.md`） | 該当 review プロンプト |

**IMPORTANT** — skills 更新時のレビュー要件:
- skills（`.claude/skills/`、`~/.claude/skills/`、`.claude/commands/` 含む）を新規作成または更新したら、別エージェントに skill レビュー用の skill / コマンドでレビューを依頼する
- レビュアは公式 Skills 作成ガイド（[skills](https://code.claude.com/docs/en/skills)）を WebFetch で取得して判定する（記憶ベースで判定しない）。構造・トリガー設計・命令品質・出力設計・実用性の 5 軸で 100 点満点採点
- 90 点以上で合格。3 回 FAIL で `issues/open/[ID].md` 起票・中断

### 独自運用: 収束型自律前進（採用時のみ・オプション）

継続的に自律進行させたい運用（人手確認の都度待ちを減らしたいプロジェクト）でのみ採用する。単発・小規模で都度確認を好む運用では不要。

計画（`.tmp/plans/` 等）を立て、上記の別エージェントレビューを **独立 2 本以上** 実施して観点が収束した（同じ懸念を指摘していない・重大な不一致がない）後は、以降の着手・続行について逐次の user 確認を待たずに進めてよい。ただし次の場合は都度 user 確認を必須とする例外として明記する（規律を弱める方向にのみ緩めない）:

1. **破壊的・不可逆な操作**（force push・履歴改変・大量削除等）
2. **認証情報・秘密情報を扱う変更**
3. **外部コストが発生する操作**（有償API呼び出し・課金を伴うデプロイ等）
4. **純粋な好み判断**（複数の妥当な選択肢があり優劣が技術的に決まらない場合）
5. **対象範囲外への大方針転換**（当初計画のスコープを超える設計変更）
6. **レビューが収束しなかった場合**（2 本以上のレビューで見解が割れた・上記ループ上限に到達した）

この 6 類の例外は「全部直轄に戻す」「全部自律に倒す」のいずれの極端化も禁止する gameability 防壁として機能させる。

### 独自運用: 成果物の生成主体明示（誤認防止）

テスト結果・成果物について、**LLM が生成したもの**か **script / template / library（pptxgenjs 等）が生成したもの**かを厳格に区別する:

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

まず「規模に応じたスケール調整」で採用要素を決め（フル装備を上限に、不要な rules / hooks / オプションファイルを落とす）、下記 8 ステップで進める。

### Step 1: 事実収集

推測・捏造はしない。不明箇所は `> [要確認]` で残す:

- 言語・FW・ランタイム
- ディレクトリ責務（1 行ずつ）
- 起動・テスト・ビルド・型チェック・lint コマンド（実在のみ）
- テスト戦略（ランナー名）
- デプロイ方法
- 環境変数・OS 依存・既知の落とし穴
- gitignore 例外（意図的に追跡しているもの）
- **汎用規律条文の採否**（候補メニュー。各々を公式 Litmus Test に通し、プロジェクトが実際に採る規律だけを `code-quality.md` の条文にする）: モック / ハードコード禁止・バージョン番号付きファイル（`v2`/`_new`/`_old`）禁止・ルート直下への新規ファイル作成抑制・設定値の一元管理・一時しのぎでなく超長期的な根本解決・**レガシー排除**（後方互換シム・二重経路・旧スクリプトを残さず、置換が完了した旧経路は同一作業内で削除する。Git 履歴がバックアップになるため保険的に残さない）
- **実行主体の使い分けの有無**（複数の AI エージェント / モデル格 / 人手を振り分ける運用があるか → あれば `execution-routing.md` 採用）
- **プロジェクトの目的**（何を解決しようとしているのか — 1〜2 文の課題定義）
- **進捗状況**（現在のフェーズ・主要マイルストーン達成状況・既知の未完了領域 — README / Issue / commit 履歴 / `issues/processing/*.md` から事実ベースで抽出）

### Step 2: 候補セクション生成 + Litmus Test 適用

各セクションに公式 Litmus Test を適用:

- `# Architecture` 直下 `This project uses TypeScript.` → `package.json` で分かる → 削除
- `テスト実行は npm run test:single -- <file>` → 推測で `npm test` されると全テスト走る → 残す
- 「コードは綺麗に書きましょう」 → 自明 → 削除

### Step 3: 段階的開示への分離

CLAUDE.md 本体に直接書かず、規約本文は採用した rules ファイルに分離する:

| 内容 | 逃がし先 |
|------|---------|
| 全タスク共通の規約（コード品質・テスト方針） | `.claude/rules/code-quality.md` / `test-verify.md`（`@import` 常時 load） |
| 特定タスク時のみのルール（Issue・review・governance） | `.claude/rules/issue-workflow.md` / `review.md` / `governance.md`（`paths:` path-scope） |
| 実行主体・モデル格の振り分け規約（採用時） | `.claude/rules/execution-routing.md`（`@import` 常時 load） |
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

### Step 4: テンプレートで組み立て

`template.md` の出力テンプレートに project 固有値を埋める。該当しないセクションは削除可、ただし削除理由を明示する。

### Step 5: 自己評価ルーブリック

`rubric.md` の 35 項目で Y/N 評価する。N が 1 つでもあれば書き直す。採用しなかったオプション要素（hooks / execution-routing.md / docs-management.md 等）は「該当なし・不要」と明示宣言すれば Y 扱いにできる。

### Step 6: サイズ確認

PowerShell では `(Get-Content <path>).Count` と `(Get-Item <path>).Length`、Bash では `wc -l` `wc -c` を実行する。実測値を末尾の `*[行数] 行 / [KB] KB*` に転記する（推定値は書かない）。剪定の目安（概ね 100 行）を超えていたら Step 3 へ戻って剪定を検討する。**ただし行数を理由に出力拒否はしない**（公式は数値閾値を持たない。出力拒否は「Claude が指示を無視している」観察可能な兆候があった時のみ）。

### Step 7: 別エージェント公式準拠レビュー

生成物（CLAUDE.md + 採用 rules + settings.json hooks + hook scripts）を別エージェントに渡してレビューを受ける。渡すのは**対象の完全パスとレビュー用 skill / コマンドの 2 点のみ**。

レビュアが必ず実施すること（= review skill が内包する評価手順）:

1. **YOU MUST** `WebFetch` で `https://code.claude.com/docs/en/best-practices` を取得する（記憶ベースで判定しない）。冒頭に取得日時と主要原則の引用を出力する
2. 公式 Include/Exclude / Litmus Test / 5 配置 / `@import` / emphasis に対し 1 項目ずつ Y/N 評価
3. 採用した rules ファイルが実在するか・条番号が通し管理されているかを Read で確認
4. 公式該当箇所と生成 CLAUDE.md 該当行を並べて示す

レビュアに渡すもの（**2 点のみ**）: ① レビュー対象の**完全パス**（絶対パス。中身はインライン貼付せずレビュアが自分で Read する）② 適用する **レビュー用 skill / コマンド名**。渡さないもの: ファイル中身のインライン貼付・公式 URL や引用・本スキル・生成過程・会話履歴。

合格基準: 公式項目全 Y、かつ `rubric.md` の 35 項目も全 Y（部分合格・点数換算はしない。Step 5 と同一基準）、かつ冒頭で WebFetch 取得日時引用がある。Web 取得していないレビューは無効、再依頼する。

不合格時: 修正して再レビュー。**3 回 FAIL で `issues/open/[YYYY-MM-DD]-claude-md-generation.md` 起票・中断・ユーザーに報告**。

### Step 8: 出力 & 採用セットの実生成 + 引継ぎ

レビュー合格後、project の事実に合わせて **採用セットを実生成**する（Step 1 で集めた事実から条文・規約・hook を埋める。スケール調整で落とした要素は生成しない）:

**1. CLAUDE.md 本体** — `template.md` に project 固有値（プロジェクト名・一行サマリ・コマンド・ルート構成・末尾入口リンク）を埋めて生成

**2. `.claude/rules/*.md`（コア + 採用オプション）** — Step 1 事実から条文を抽出して生成（条番号は通し管理・ファイル間で重複させない）:

| ファイル | 内容 | YAML frontmatter | load |
|---|---|---|---|
| `meta.md` | 条インデックス（条見出し + 所在ファイル）+ **既知の制約（[claude-code Issue #23478](https://github.com/anthropics/claude-code/issues/23478) の path-scope auto-load Read 時のみ発火 bug を URL 付きで明記）** + **常時 load ファイル 5KB soft cap 宣言** | なし | 常時 |
| `code-quality.md` | コード変更規約（命名・import・型）の条文 | `description` のみ | `@import` で常時 |
| `test-verify.md` | テスト・自検証規約（ランナー・lint・受入基準・**close 前検証 4 段**［再現→pass / negative test / regression smoke / 証拠アーカイブ］・**成果物の生成主体明示**［LLM 生成物 vs script/lib 生成物の厳格区別］）の条文 | `description` のみ | `@import` で常時 |
| `issue-workflow.md` | Issue 起票・handoff・/clear 規約の条文（**並走 agent 痕跡 4 軸 recheck**・stale handoff 誤受領防止・古い handoff の archive 含む） | `paths: ["issues/**", ".tmp/**"]` | path-scope |
| `review.md` | 別エージェントレビュー規約の条文（**2〜4 本並列 + converged findings**・**TDD test-first**・ループ上限［計画 3 周 / 実装 1 周］・自己レビュー不可・**渡すのは対象完全パス + レビュー用 skill のみ**） | `paths: ["**/*.<lang>", ".claude/commands/**"]` | path-scope |
| `governance.md` | 肥大化防止・新項目追加規約の条文を **複数観点の項目群**（サイズ閾値 / 新項目ルーティング / 公式準拠 / 定期レビュー / 自動検証 / 常時 load ファイル cap 等・増減可）で記述 | `paths: ["CLAUDE.md", ".claude/**"]` | path-scope |
| `execution-routing.md`（**オプション**） | 司令塔の 3 責務 + 振り分け表（定型→低コスト / 高難度→高コスト / 方針→司令塔）+ 高コスト主体抑制（dispatch 5 点明示）+ escalation protocol | `description` のみ | `@import` で常時 |
| `docs-management.md`（**オプション**: `docs/` 配下に概ね 5 section 以上） | docs 配置 mapping + 新 docs 配置 flow + 全 section README 必須化 + **同期更新義務**（rule mapping / validate script / INDEX / generator）+ 過時マーカー "as of YYYY-MM-DD" 強制 | `paths: ["docs/**/README.md", "docs/**/*.md", "CLAUDE.md", ".claude/rules/governance.md"]` | path-scope |

**3. `settings.json` の hooks セット + hook scripts**（採用時のみ） — 参考 5 hook 構成・settings.json 例（Windows PowerShell / Mac・Linux bash）・hook script 5 ファイルの役割と生成方法は **`hooks-reference.md` を参照**する。既存設定がある場合は `hooks` フィールドのみ追記（permissions / model 等は保持）。

**ユーザーへの最終報告**:
- **プロジェクト概要**（プロジェクト未読の第三者が読んでも理解できるレベルで書く。Step 1 で収集した事実のみを使い推測・捏造はしない）:
  - **大まかな説明** — 何を解決しようとしているのか（1〜2 文の課題定義 + 解決アプローチの要点）
  - **細かな説明** — 主要機能・技術スタック・想定ユーザー・スコープ境界（箇条書き 5〜10 項目）
  - **進捗状況** — 現在のフェーズ（PoC / α / β / 本番運用 等）・直近マイルストーン・既知の未完了領域・進行中 Issue 件数（`issues/processing/*.md` の実数）
- 生成内容の要約（3 行以内）
- `> [要確認]` 残項目
- **生成したファイル一覧（フルパス）**: CLAUDE.md / 採用 rules / settings.json / hook scripts
- **スケール調整で意図的に落とした要素**（採用しなかった rules / hooks / オプションファイルと、その理由を 1 行ずつ）
- レビュア合格スコア

大タスク完了のため `/clear` を促す。`/clear` 前に handoff を保存する（命名・保持・issue 連携の規約本体は「独自運用: handoff 管理」を正本とし、ここでは参照のみ）。

---

## 含めてはいけないもの

- 一般的開発常識（「テストを書きましょう」「セキュリティに注意」）
- ツール自体の長文（公式 docs リンクのみ）
- バージョン番号・進行中タスク・TODO（陳腐化）
- README に書くべき導入文・売り文句（CLAUDE.md は AI 向け）
- 装飾的見出し階層（h4 以下を多用しない）
- 時々しか使わない知識・ワークフロー（Skills へ）
- 特定の社内プロダクト名・実在企業/製品名（本スキルの生成物は汎用・匿名で保つ）

---
*準拠ソース: https://code.claude.com/docs/en/best-practices "Write an effective CLAUDE.md" — 出力テンプレート=`template.md` / ルーブリック=`rubric.md` / hooks=`hooks-reference.md` / メンテ=`maintainer-checklist.md`*
