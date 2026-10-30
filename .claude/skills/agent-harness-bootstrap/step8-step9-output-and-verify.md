# Step 8 の採用セット実生成 / Step 9 setup 後レビュー

SKILL.md の Step 8・Step 9 の詳細。Step 7 合格後に参照する。

## 目次

- Step 8 採用セットの実生成（1. CLAUDE.md 本体 / 2. rules / 3. hooks / 4. roadmap / 5. CHANGELOG）
- ユーザーへの最終報告
- Step 9 setup 後レビュー（機械検査・突合レビュー・/clear）

---

レビュー合格後、project の事実に合わせて **採用セットを実生成**する（Step 1 で集めた事実から条文・規約・hook を埋める。スケール調整で落とした要素は生成しない）:

**1. CLAUDE.md 本体** — `template.md` に project 固有値（プロジェクト名・一行サマリ・コマンド・ルート構成・末尾入口リンク）を埋めて生成

**2. `.claude/rules/*.md`** — Step 1 事実から条文を抽出して生成（条番号は通し管理・ファイル間で重複させない）。**各行・各条文は Step 0 で `selected: true` の要素（「要素 id」列）に対応するものだけ生成する**。id 列の要素が全て非選択のファイルは作らない（条文ゼロのファイルを空作成しない）。「選択依存」と付けた行は author-preference 要素で構成され、デフォルトでは生成されない:

| ファイル | 内容 | 要素 id | YAML frontmatter | load |
|---|---|---|---|---|
| `meta.md` | 条インデックス（条見出し + 所在ファイル）+ **load 戦略**（`paths:` 無し = 起動時に常時 load / `paths:` 付き = 一致ファイルを Read した時に load する公式仕様のため、Write 前に効かせたい条文は常時 load 側に置く / `/compact` 後にディスクから再注入されるのはルート CLAUDE.md で、path-scope rules は該当ファイルを再び読むまで戻らない）。`always-load-5kb-cap` 採用時のみ **常時 load ファイル 5KB soft cap 宣言** を加える | rules-split-progressive-disclosure / always-load-5kb-cap | なし | 常時 |
| `code-quality.md` | コード変更規約（命名・import・型）の条文。`generic-discipline-menu` 採用時は Step 1 で採否判定を通った汎用規律条文を加える | rules-split-progressive-disclosure / generic-discipline-menu | なし（`paths:` を書かない） | 起動時に常時 |
| `test-verify.md` | テスト・自検証規約（ランナー・lint・受入基準）+ **機械検査対象データの構造化**［script / hook / レビュアが検査する閾値・基準・チェックリストは散文でなく構造化データ（JSON / YAML）で定義し検証スクリプトで強制する・`deterministic-enforcement-structured-data`］。採用時のみ加える条文: **close 前検証 4 段**［再現→pass / negative test / regression smoke / 証拠アーカイブ・`close-verification-4-steps`］・**成果物の生成主体明示**［LLM 生成物 vs script/lib 生成物の厳格区別・`artifact-generator-attribution`］・**数値目標の単一 SoT 化**［カバレッジ%・合格率等の閾値を prose に手書きせず、閾値を強制する設定ファイル（CI workflow・validator script 等）を唯一の SoT とする。宣言値と実際の強制値が食い違う／複数箇所に重複記載されて片方だけ更新され stale 化する、という観察済みの失敗パターンを防ぐ条文。`numeric-target-single-sot`・author-preference だが default `recommend`（事前チェック済み・ユーザーが外せる）。実コードのカバレッジ計測対象がないプロジェクトでは「合格率」「品質スコア」等の類似閾値に読み替える］ | rules-split-progressive-disclosure / deterministic-enforcement-structured-data / close-verification-4-steps / artifact-generator-attribution / numeric-target-single-sot | なし（`paths:` を書かない） | 起動時に常時 |
| `issue-workflow.md`（**選択依存**） | Issue 起票・handoff・/clear 規約の条文（`issue-lifecycle`）+ handoff 命名・保持・user 明示指示受領・stale handoff 誤受領防止・archive（`handoff-management`）+ **並走 agent 痕跡 4 軸 recheck**（`concurrent-agent-4-axis-recheck`）。選択された要素の条文だけを載せる | issue-lifecycle / handoff-management / concurrent-agent-4-axis-recheck | `paths: ["issues/**", ".tmp/**"]` | path-scope |
| `review.md` | 別エージェントレビュー規約の条文（**渡すのは対象完全パス + レビュー用 skill のみ**・自己レビュー不可・skills 更新時の公式 Skills ガイド WebFetch レビュー = `separate-agent-review-cycle`）。`review-cycle-parameters` 採用時のみ **2〜4 本並列 + converged findings**・**TDD test-first**・ループ上限［計画 3 周 / 実装 1 周］・90 点合格・3 回 FAIL 中断を加える | separate-agent-review-cycle / official-adversarial-review / official-skills-core / review-cycle-parameters | `paths: ["**/*.<lang>", ".claude/commands/**"]` | path-scope |
| `governance.md`（**選択依存**） | 肥大化防止・新項目追加規約の条文を **複数観点の項目群**（サイズ閾値 / 新項目ルーティング / 公式準拠 / 定期レビュー / 自動検証 / 常時 load ファイル cap 等・増減可）で記述。`harness-compliance-roadmap-seed` 採用時は「定期レビュー」「自動検証」の各項目に、同要素が生成する `harness-compliance-roadmap.md` の二段 cadence（軽量 `harness_check.sh` スイープ / 四半期 `skills-audit`・`harness-compliance-audit` フル判定）を参照する一文を加える（非採用時は公式ドリフト検出・サイズ/命名 hook のみを指す従来の記述のまま）。非採用時（governance.md 自体）は official 由来の「新しい○○を追加する手順」（rubric 18）を CLAUDE.md 本体の 2〜3 行の節として残す | governance-multi-aspect / harness-compliance-roadmap-seed | `paths: ["CLAUDE.md", ".claude/**"]` | path-scope |
| `execution-routing.md`（**選択依存**） | 司令塔の 3 責務 + 振り分け表（定型→低コスト / 高難度→高コスト / 方針→司令塔）+ 高コスト主体抑制（dispatch 5 点明示）+ escalation protocol | execution-routing | なし（`paths:` を書かない） | 起動時に常時 |
| `docs-management.md`（**選択依存**: `docs/` 配下に概ね 5 section 以上） | docs 配置 mapping + 新 docs 配置 flow + 全 section README 必須化 + **同期更新義務**（構造的事実を複数箇所に重複保持せざるを得ない時は、コピー先を rule 本文に全て列挙し、コピー間の自動 diff/整合チェックを用意する — 単一 SoT を宣言して残りを放置しない）+ 過時マーカー "as of YYYY-MM-DD" 強制 | docs-management | `paths: ["docs/**/README.md", "docs/**/*.md", "CLAUDE.md", ".claude/rules/governance.md"]` | path-scope |
| `agent-design.md`（**選択依存**: 複数 subagent 構成を新規実装するプロジェクトのみ） | 複数 subagent / マルチエージェント構成向けの設計原則の条文: **クラッシュ耐性 state manifest**［長時間・並列 subagent 運用でコーディネーターが再起動しても、各 subagent が進捗を `<作業ディレクトリ>/<subagent 名>.json`（manifest）へ節目ごとに書き出していれば未完了分だけ再開できる（Workflow ツールの `resumeFromRunId` と併用）・`agent-design-crash-resilient-manifest`］・**コーディネーター中継のメタデータ保持**［複数の調査系 subagent の結果を統合エージェントへ中継する時、出典（URL・ファイルパス）をメタデータとして本文と分離保持したまま渡す（平文要約に潰さない）・`agent-design-metadata-preserving-handoff`］・**ツールスコープの限定**［1 エージェントのツール（subagent 定義の `tools`。skill の `allowed-tools` は事前承認であって制限ではない）は 4〜5 個・単一ロールを目安にし、複数専門領域は対象単位ごとの別エージェントに分割する・`agent-design-tool-scope-limit`］。冒頭に、レビュー時の実装コンテキスト遮断・並列アンカリング防止は `review.md`（`separate-agent-review-cycle` / `official-adversarial-review`）を参照する旨を一行明記し重複させない。選択された要素の条文だけを載せる | agent-design-crash-resilient-manifest / agent-design-metadata-preserving-handoff / agent-design-tool-scope-limit | `paths: [".claude/agents/**", ".claude/skills/**/SKILL.md"]` | path-scope |

**3. `settings.json` の hooks セット + hook scripts**（採用時のみ） — 参考 6 hook 構成・settings.json 例（Windows PowerShell / Mac・Linux bash）・hook script（該当するもののみ生成）の役割と生成方法は **`hooks-reference.md` を参照**する。既存設定がある場合は `hooks` フィールドのみ追記（既存の permissions / model 等は保持）。あわせて `"$schema": "https://json.schemastore.org/claude-code-settings.json"` の行と、`permissions-deny-sensitive` 選択時の `permissions.deny`（`Read(./.env)` 等）を入れる。外部プロセスを起動する hook には `timeout` を付ける。`.gitignore` に `CLAUDE.local.md` と `.claude/settings.local.json` を追記する。

**4. `.claude/skills/_shared/harness-compliance-roadmap.md`**（**選択依存**: `harness-compliance-roadmap-seed`） — セットアップ完了直後に、対象自身の `.claude/harness-selection.json` を読み、`selected: true` の選択依存ファイル生成要素（`governance-multi-aspect` / `agent-design-*` 3件 / `issue-lifecycle` 系 3件 / `review-cycle-parameters` / `execution-routing` / `docs-management` 等）を1行ずつ拾い、各要素自身の `target_contract.when_selected` の grep パターンをそのまま「再検証すべき契約語句」列に転記した findings 表を生成する（新しい語彙は作らない）。冒頭に二段 cadence（軽量 `harness_check.sh` 全ファイルスイープ / 四半期 `skills-audit`・`harness-compliance-audit` フル判定）を明記し、末尾に setup 完了日 + `provenance-check.sh --target PASS`（Step 9）の1行を監査ログの初期エントリとして入れる。**生成先ファイル名は、このリポジトリ自身の `.claude/skills/_shared/compliance-roadmap.md` とは意図的に別名にする**（同名だと非選択の `shared-compliance-roadmap` 要素側で C12 が「非選択要素の混入」を誤検知するため）。非採用時はファイルを作らない。

**5. `CHANGELOG.md`**（**選択依存**: `changelog-practice`） — 対象の**リポジトリルート**に生成する（`docs/` を採用しているかに依存させない）。ヘッダー1行 + setup 完了日を種として1エントリ（例:「<日付>: harness セットアップ完了」）を記す。既存の `CHANGELOG.md` があれば新規作成せずそこへ追記する運用に合流する。非採用時はファイルを作らない。

**ユーザーへの最終報告**:
- **プロジェクト概要**（プロジェクト未読の第三者が読んでも理解できるレベルで書く。Step 1 で収集した事実のみを使い推測・捏造はしない）:
  - **大まかな説明** — 何を解決しようとしているのか（1〜2 文の課題定義 + 解決アプローチの要点）
  - **細かな説明** — 主要機能・技術スタック・想定ユーザー・スコープ境界（箇条書き 5〜10 項目）
  - **進捗状況** — 現在のフェーズ（PoC / α / β / 本番運用 等）・直近マイルストーン・既知の未完了領域・進行中 Issue 件数（`issue-lifecycle` 採用時は `issues/processing/*.md` の実数。非採用時は外部トラッカーの件数か「該当なし」）
- 生成内容の要約（3 行以内）
- `> [要確認]` 残項目
- **生成したファイル一覧（フルパス）**: CLAUDE.md / 採用 rules / settings.json / hook scripts / `.claude/harness-selection.json`（Step 0 実施時）/ コピーした skills・commands・`files[]`
- **対象側のコミット / gitignore の区分**: 上記生成物はコミット対象。移植元 clone（`.setup-automate/`）と handoff 採用時の `.tmp/` は `.gitignore` に追記済みか（未追記なら追記して報告）
- **由来別の選択結果**（Step 0 実施時）: 群 C（著者嗜好・第三者・業務プロンプト）で採用した要素の一覧、群 A・B で外した要素と理由、対話不可で default のみ採用した場合はその旨
- **スケール調整で意図的に落とした要素**（採用しなかった rules / hooks / オプションファイルと、その理由を 1 行ずつ）
- レビュア合格の事実（公式項目 + rubric 全 Y）と、レビュアが冒頭に出力した WebFetch 取得日時

## Step 9 setup 後レビュー

生成が終わったら `bash <本スキル dir>/scripts/harness-setup-state.sh phase generated` を実行し、**`harness-setup-review` skill を実行する**。同 skill は (1) `provenance-check.sh --target <対象>` による決定的な契約検査（選択要素の抜け・非選択要素の混入・マーカー残存・`@import` と `paths:`）、(2) `criteria/porting-reconciliation.json` による別エージェントの突合レビュー、(3) 対象に既存 skills があれば `skills-audit` による公式ベストプラクティス準拠の監査、(4) 対象で新しいセッションを開いて `/context` を実行し、Memory files に CLAUDE.md と常時 load の rules が載っていることを確認する手順の案内（対話操作のためユーザーに依頼し、最終報告に含める）、を行い、(1)(2) が両方 PASS した時だけ `harness-setup-state.sh verify --machine PASS --review PASS` → `done` で state を閉じる。この clone の Stop hook は `done` 前の終了を block する（3 回 FAIL で中断してユーザーに報告）。最終報告には Step 9 の機械検査出力・レビュー verdict・既存 skills の tier を含める。

大タスク完了のため `/clear` を促す。対象で `handoff-management` が選択済みなら `/clear` 前に handoff を保存する（命名・保持・issue 連携の規約本体は「独自運用: handoff 管理」を正本とし、ここでは参照のみ）。非選択なら handoff は作らず、最終報告を引継ぎとする。
