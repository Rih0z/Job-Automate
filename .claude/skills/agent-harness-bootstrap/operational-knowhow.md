# 本スキル独自の運用ノウハウ（詳細）

SKILL.md 本体「本スキル独自の運用ノウハウ」の索引から参照する supporting file。公式には記述がない本スキルの設計判断であり、プロジェクトに合わせて緩めてよい。各項目は「何をするか」を主体に記す。

### 独自運用: 規模に応じたスケール調整（過剰生成を避ける）

本スキルの構造は「フル装備」の上限像である。生成の最初に、以下のスケールダウン判断を明示的に行う（消したら Claude がミスする / 規律が失われる要素だけを残す）:

- **rules ファイルは、該当する条文が実際に存在するものだけ生成する**（条文ゼロのファイルを空作成しない。後で必要になったら追加する）
- **hooks は「確実に毎回実行したい規律」が実在する時だけ導入する**（単発・並走なしの個人開発では SessionStart hook や並走痕跡検出は不要）
- **オプションファイル（`docs-management.md` / `execution-routing.md`）は採用判定に通ったものだけ生成する**

標準セットは**上限（あり得る最大構成）**であって**必須の下限ではない**。

### 独自運用: サイズの目安（参考値・硬性基準ではない）

| レベル | 対象 | 目安 | 対応 |
|------|------|------|------|
| 剪定検討 | CLAUDE.md 本体 | 概ね 100 行 / 10KB を超え始めたら | 「削除したら Claude が間違えるか」の基準で再評価。挙動が変わらないルールが埋もれていないか観察 |
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
| 新条文追加手順 | 新しい規約を rules に足す前に踏む 5 段（既存条の重複・言い換えでないか確認 → 配置先を項目性質で判定 → 公式ドキュメントと矛盾しないか確認 → 影響する自動検証（hook/CI）があれば同時更新 → 独立レビュー 2 本以上を収束させてから確定）。重複ならまず既存条の拡張を優先し新設しない | 追加提案のたびにこの 5 段をチェックリストとして踏ませる |
| advisory → hook 昇格判断 | 公式は明記する: 「hooks are deterministic and guarantee the action happens... Use hooks for actions that must happen every time with zero exceptions」。rules 条文に「必ず」「例外なく」等の zero-exception 語気を使う時は、(a) 毎回・例外なく実行されるべきか (b) pass/fail が機械的に判定可能か の両方を満たす規律だけ hook 化を検討する（両方満たさない文脈依存の判断は advisory のまま rules に残してよい） | 既存規約の一斉 hook 化はしない。新条文追加時と定期レビュー時に候補判定するのみ |

サイズ閾値だけでは `@import` 常時 load rules 経由の context 汚染を防げない。「常時 load ファイルの cap」観点が context 汚染を構造的に塞ぐ最も効く一手になる。「新条文追加手順」観点は、規約が場当たり的に増殖し公式からドリフトする経路を構造的に塞ぐ。「advisory → hook 昇格判断」観点は、公式の zero-exception ガイダンスへの non-compliance (advisory 文言だけで済ませてしまう) を構造的に防ぐ。

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

タスク・問題は `issues/` 配下のフォルダで状態管理する。並走エージェント数・修正の重大度に応じて 3 段階（open→processing→closed）または 4 段階（下記オプション参照）を選ぶ:

| フォルダ | 状態 | 配置タイミング |
|---|---|---|
| `issues/open/[ID].md` | 未着手 | 問題発見・新タスク要求時の起票先 |
| `issues/processing/[ID].md` | 着手中 | open から `git mv` で移動。冒頭に進行中 handoff の完全パスを記載 |
| `issues/closed/[ID].md` | 完了 | processing から `git mv` で移動。下記 close 検証 4 段を本文末に証拠付きで宣言 |

**オプション: 4 段階化（pending＝検証待ちバッファ）** — 「修正した本人がその場で closed にする」を構造的に防ぎたい場合、processing と closed の間に `issues/pending/[ID].md`（修正完了・独立検証待ち）を挟む。状態遷移ツール（`git mv` を wrap するスクリプト等）側で pending を経由しない open/processing→closed の直行遷移を拒否し、明示的な override フラグ経由でのみ許可する。修正した本人と検証する主体が分離できる運用（別エージェント・別セッションでの再検証）でのみ効果があるため、単一セッション完結の小規模プロジェクトでは 3 段階のままで良い。

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

CLAUDE.md に書いた規約は advisory なので Claude が長文中で見落としうる。「確実に毎回動かしたい」規約は hook 化する。ただしスケール調整に従い、**該当する規律が実在する時だけ導入**する（単発・並走なしの小規模開発では省略してよい）。hooks 化候補の判断基準・設計指針・参考 6 hook 構成・監査手順・OS 別 shell 実装・hook script 雛形は **`hooks-reference.md` を参照**する。

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
