---
name: agent-harness-bootstrap
description: 任意のプロジェクトに対し、Anthropic 公式 Best Practices（"Write an effective CLAUDE.md"）に準拠した CLAUDE.md と、それを支える運用 harness（rules ファイル群 + hooks）を生成・剪定する。公式準拠の核と、独自の運用ノウハウをラベル分離して適用する。要素ごとの由来（公式 / 著者嗜好）を provenance.json で分け、別プロジェクトへ適用する時は著者嗜好をデフォルト非採用にしてユーザーが取捨選択する。単発の SKILL.md 作成・採点、コード実装、README 執筆には使わない（skill-authoring-guide / review-skill 等を使う）。
when_to_use: 「CLAUDE.md を作って」「`/init` の代わりに公式準拠で生成して」「既存の CLAUDE.md を公式 Best Practices で書き直して」「CLAUDE.md が肥大化したので剪定して」「(この repo の) 仕組みを別プロジェクト 対象 にも入れて」「このリポジトリのノウハウで 対象ディレクトリ をセットアップして」等、**対象(このリポジトリ以外の別ディレクトリ/別リポジトリ) が明示された**依頼全般 (2026-09-01 拡張、リポジトリ CLAUDE.md「他プロジェクトのセットアップ依頼への対応」と同期。対象が明示されない曖昧な「セットアップして」は対象外)
metadata:
  provenance: mixed
  version: 1.1.0
---

# CLAUDE.md 生成 harness

任意のプロジェクトに対し、Anthropic 公式 Best Practices（[Write an effective CLAUDE.md](https://code.claude.com/docs/en/best-practices#write-an-effective-claude-md) / [Skills](https://code.claude.com/docs/en/skills)）に準拠した `CLAUDE.md` を生成する。**公式準拠の核**と**本スキル独自の運用ノウハウ**をラベル分離して適用する。

ラベル分離の SoT は `provenance.json`（由来台帳）。本スキルが扱う全要素（原則・rules・hooks・skills・CLAUDE.md セクション）を `official` / `official-derived` / `author-preference` / `third-party` / `domain-prompt` / `repo-specific` のいずれかに分類し、別プロジェクトへ適用する時は **著者嗜好（author-preference）をデフォルト非採用**にして Step 0 でユーザーに取捨選択させる。公式由来と著者嗜好を混ぜたまま他環境へ写さないための仕組みで、台帳と実体の整合は `scripts/provenance-check.sh` で機械検査する。

> 本スキルが提示する運用構造（rules 分離・条文の通し番号管理・hooks による自動化）は、特定のプロダクトを前提としない**一般的な設計原則**として整理したものである。特定の社内実装を「実証済みの参照実装」として引用しない。設計判断の根拠は、外部実装の存在や実績ではなく、各原則自身の合理性（公式ドキュメントとの整合・観察可能な失敗パターンの回避）に置く。

**使わない時**: コード自体を書く時、Skills (`.claude/skills/`) を作る時、README を書く時。

## 参照ファイル（progressive disclosure）

詳細な素材は同ディレクトリの supporting files に分離する。本体からは以下を参照する:

| ファイル | 内容 | 使う場面 |
|---|---|---|
| `provenance.json` | 由来台帳（SoT）。全要素の provenance / default_selection / depends_on / rubric_items / 対応 skills | Step 0 / Step 5 / Step 7 / 本スキル改修時 |
| `selection-flow.md` | Step 0 の手順: 由来別の提示・ユーザー選択の取り方・依存検証・対象への `harness-selection.json` 記録・突合レビュー | Step 0 |
| `scripts/provenance-check.sh` | 台帳と実体（skills / commands / 付随 files の存在・rubric 番号と id 列の双方向・operational-knowhow の provenance 行・各 SKILL.md の `metadata.provenance`）の整合検査。`--selection <path>` で対象の `harness-selection.json` も検証（regression: `provenance-check.test.sh`） | Step 0-6 / 本スキル改修時 |
| `scripts/contract-selfcheck.sh` | 台帳の `target_contract` が default 選択で満たせて矛盾しないことの自己検査（生成物の最小雛形を scratch に組み立てて `--target` を通す） | 本スキル改修時 |
| `criteria/porting-reconciliation.json` | 移植完了後の突合レビュー観点（review-gate 形式: 記録の完全性 / 抜けゼロ / 混入ゼロ / 依存整合 / 報告の開示） | Step 9（`harness-setup-review`） |
| `../_shared/anthropic-best-practices.json` | Anthropic 公式ベストプラクティスの構造化データ（取得日 + 再取得条件付き。全 skill 共通の判定基準 SoT） | 公式準拠の核 / Step 2 / Step 7 |
| `scripts/harness-setup-state.sh` | 別プロジェクト setup の進行状態（selecting → generated → verified → done）。Stop hook の block 根拠 | Step 0 / Step 8 / Step 9 |
| `scripts/hook-stop-setup-gate.sh` / `scripts/hook-session-start-setup.sh` | このリポジトリの `.claude/settings.json` に登録された hook。検証前の終了を block / 進行中 setup のポインタ通知 | 自動 |
| `template.md` | CLAUDE.md 本体の出力テンプレート（雛形・ブロックごとに要素 id マーカー付き） | Step 4 |
| `rubric.md` | 自己評価ルーブリック 36 項目（Y/N・要素 id 列付き。非選択要素の項目は opt-out 宣言で Y） | Step 5 / Step 7 |
| `hooks-reference.md` | hooks 化判断・参考 6 hook 構成・settings.json 例・hook script 雛形（PowerShell / bash） | Step 8-3 |
| `operational-knowhow.md` | 本スキル独自の運用ノウハウの詳細本文（スケール調整・標準セット・governance.md 項目群・handoff/issue 運用・レビューサイクル等、下記索引の全項目） | Step 1〜8 全般。索引だけで足りない時に参照 |
| `official-sources.md` | 公式 URL ごとの確認項目表と構造化データの再取得条件 | 公式準拠の核 |
| `operational-knowhow-index.md` | 独自運用ノウハウの項目一覧（索引） | Step 1 / Step 2 |
| `step7-reviewer-procedure.md` | Step 7 のレビュアの実施事項・受け渡し・合格基準 | Step 7 |
| `step8-step9-output-and-verify.md` | 採用セットの実生成・最終報告・Step 9 の手順 | Step 8 / Step 9 |
| `maintainer-checklist.md` | 本スキル更新者向けメンテ checklist（生成物評価には無関係） | 本スキル改修時 |

---

## 公式準拠の核（実行時 WebFetch 必須・本スキルに焼き込まない）

> Anthropic 公式は随時更新される。**公式の文言・テーブル・数値・API 契約を本スキルに転記（焼き込み）しない**。生成・レビュー開始時に下記を WebFetch で取得し、その時点の現行版で判定する（記憶・過去の引用で代替しない。WebFetch 失敗時は焼き込み版で代替せず、取得できるまで生成を中断する）。
>
> 焼き込み禁止の根拠は公式 Exclude 項目「Information that changes frequently」と同根。過去に転記した Include/Exclude テーブルが現行公式とドリフトした実例があり、転記は腐る。

URL 表（`best-practices` / `memory` / `skills` / `hooks` / `sub-agents` / `permissions`・`settings` の各確認項目）と構造化データ `_shared/anthropic-best-practices.json`（`fetched` / `refetch_when` / `max_age_days` による再取得条件）の詳細は `official-sources.md`。生成・レビュー開始時に必ず読み、WebFetch で現行版を取得する。取得失敗時は焼き込み版で代替せず、`fetched` が `max_age_days` 以内なら構造化データで判定を続けて報告に「公式現行版との突合未実施」と明記する。超過していれば取得できるまで中断する。

取得後、冒頭に「取得日時 + 確認した現行原則の要点」を出力してから生成・レビューに進む。

### 本スキル由来の独自運用基準（公式転記ではない・保持する）

公式の文言ではなく本スキル由来の運用判断。公式が変わっても独自基準として有効だが、取得時に公式と矛盾しないか都度突合する:

- **emphasis（IMPORTANT / YOU MUST）は最大 5 件目安**。それ以外の語気強め（必須・禁止・絶対）は平叙文化する（公式 emphasis 許容を運用上引き締めた独自基準）
- **行数による出力拒否ゲートを設けない**。公式の行数は『目標』（memory docs の Size 記述。取得時に現行値を確認する）であって出力拒否の閾値ではない。超過時は分割先（rules / skills）を検討し、剪定判断は "rules getting lost in the noise" の兆候も合わせて見る

---

## 本スキル独自の運用ノウハウ（索引）

公式には記述がない本スキルの設計判断で、プロジェクトに合わせて緩めてよい。項目一覧（規模調整 / サイズ目安 / 標準セット / 振り分け規約 / 宣言 / governance / handoff / 並走 recheck / issue / hooks 化 / 品質基準継承 / マルチエージェント / レビューサイクル / 収束型自律前進 / 生成主体明示）は `operational-knowhow-index.md`、詳細本文は `operational-knowhow.md`。

---

## 前提（この repo 固有の依存と代替）

次はこの repo 固有の構成に依存する。無い環境では代替で進める。

| 依存 | 無い環境での代替 |
|---|---|
| repo ルート `CLAUDE.md` の「他プロジェクトのセットアップ依頼への対応」節 | 本 SKILL.md の Step 0〜9 と `selection-flow.md` だけで進める（移植チェックリストは `provenance.json` の全要素から作る） |
| この repo の `.claude/settings.json` に登録された Stop hook / SessionStart hook | state 更新は省略してよい。Step 9 の機械検査（`provenance-check.sh --target`）と突合レビューを手動で実行し、結果を最終報告に載せる |
| `harness-setup-review` skill・`skills-audit` skill・`_shared/anthropic-best-practices.json` | 無い場合は別エージェントに `criteria/porting-reconciliation.json` と `rubric.md` を渡して同じ観点で突合させ、公式 URL は WebFetch で直接確認する |
| 移植元 clone の置き場 `.setup-automate/` と handoff 用 `.tmp/` | 実際に使った置き場を対象の `.gitignore` に追記する |

---

## 入力

- プロジェクトディレクトリ（`ls -R` / `tree` / 主要ファイル中身）
- マニフェスト（`README.md`, `package.json`, `pyproject.toml`, `go.mod` 等）
- 既存 CLAUDE.md（更新時）

> このリポジトリのノウハウを土台にした別プロジェクトのセットアップ依頼では、先にこのリポジトリのルート `CLAUDE.md` の「他プロジェクトのセットアップ依頼への対応 — 完全列挙 + 由来別選択ルール」を適用する。`provenance.json` の全要素と CLAUDE.md の全セクションを列挙した移植チェックリストを作り、Step 0（`selection-flow.md`）でユーザーに由来別の取捨選択をさせてから Step 1 以降に入る。移植後は別エージェントによる突合レビューで「選択済み要素の抜けゼロ」と「非選択要素の混入ゼロ」の両方を確認する。

---

## 生成手順

Step 0 で由来別の選択を確定し、次に**選択済み要素の範囲内で**「規模に応じたスケール調整」を行い（フル装備を上限に、該当条文の無い rules・毎回実行したい規律の無い hooks・採用判定を通らないオプションを落とす。落とした要素は `harness-selection.json` に `selected: false, decided_by: "scale"` で追記し、選択記録と生成物を一致させる）、Step 1〜8 で生成し、Step 9 の検証を PASS させて完了とする。対象が別プロジェクトの時、Step 0 の冒頭で `bash <本スキル dir>/scripts/harness-setup-state.sh start <対象の絶対パス>` を実行して state を作る（この clone の Stop hook が、Step 9 を PASS するまで終了を block する）。

### Step 0: 由来別の取捨選択（対象が別プロジェクトの時）

手順の本体は `selection-flow.md`。要点:

1. `provenance.json` を Read し、要素を 4 群で提示する: A `official`（**必ず採用・外せない**。`provenance-check.sh` C11 が `selected: false` を拒否する）/ B `official-derived`、および `default_selection_override: recommend` を持つ要素（推奨・事前チェック済み・外せる）/ C それ以外の `author-preference` `third-party` `domain-prompt`（**デフォルト非採用**・選んだものだけ）/ D `repo-specific`（移植不可・提示のみ）
2. 対話可能なら `AskUserQuestion`（multiSelect）で C から取り込む要素を選ばせ、B から外す要素の有無を聞く（A は聞かない）。対話不可なら `default_selection` のみ採用し、その旨を最終報告の冒頭に明記する（ユーザーの好みを推測で補わない）
3. `depends_on` を欠く選択は成立しないことを示して再確認する
4. 決定を対象の `.claude/harness-selection.json` に**全要素分**（非選択も `selected: false` で）記録する
5. 以降の Step は選択済み要素だけを対象にする。非選択の author-preference 要素は rules 条文・hooks・template ブロック・skills コピー・付随 `files` のいずれにも現れてはならない。逆に選択した要素は台帳の `target_contract`（契約語句・ファイル・`@import`・`paths:`）を生成物に必ず含める（Step 9 の `provenance-check.sh --target` が決定的に検査する）
6. 記録を `bash <本スキル dir>/scripts/provenance-check.sh --selection <対象の絶対パス>/.claude/harness-selection.json` で機械検証する（全要素の網羅・`decided_by` の値域・`depends_on` の充足・repo-specific の非選択・skill-group の `skills[]`。cwd に依存しないので任意の場所から実行できる）

Step 0 は省略しない。対話が取れない場合も `default_selection` で `harness-selection.json` を生成する（省略 = 非対話扱い）。rubric の opt-out 判定はこの記録だけを根拠にするため、記録の無い生成では author-preference 要素を全て検査対象として扱う（事実上の必須化）。唯一の例外はこのリポジトリ自身の CLAUDE.md 剪定（新しい生成物を作らない）。

### Step 1: 事実収集

推測・捏造はしない。不明箇所は `> [要確認]` で残す:

- 言語・FW・ランタイム
- ディレクトリ責務（1 行ずつ）
- 起動・テスト・ビルド・型チェック・lint コマンド（実在のみ）
- テスト戦略（ランナー名）
- デプロイ方法
- 環境変数・OS 依存・既知の落とし穴
- gitignore 例外（意図的に追跡しているもの）
- **汎用規律条文の採否**（候補メニュー。各々を「削除したら Claude が間違えるか」の基準に照らし、プロジェクトが実際に採る規律だけを `code-quality.md` の条文にする）: モック / ハードコード禁止・バージョン番号付きファイル（`v2`/`_new`/`_old`）禁止・ルート直下への新規ファイル作成抑制・設定値の一元管理・一時しのぎでなく超長期的な根本解決・**レガシー排除**（後方互換シム・二重経路・旧スクリプトを残さず、置換が完了した旧経路は同一作業内で削除する。Git 履歴がバックアップになるため保険的に残さない）
- **実行主体の使い分けの有無**（複数の AI エージェント / モデル格 / 人手を振り分ける運用があるか → あれば `execution-routing.md` 採用）
- **独自 skill / MCP ツールの新規作成有無**（該当すれば「自作 skill / MCP ツールの品質基準の継承」を Step 7 レビュー観点に追加）
- **`AGENTS.md` の有無**（対象ルートに `AGENTS.md` があれば、生成 CLAUDE.md の先頭に `@AGENTS.md` を置く。CLAUDE.md があると既定では AGENTS.md が読まれなくなるため。言葉で「AGENTS.md を読め」と書くだけでは読まれる保証が無い）
- **機密ファイルの有無**（`.env`・`secrets/`・鍵ファイル等。`permissions-deny-sensitive` 選択時は、実在の有無にかかわらず `settings.json` の `permissions.deny` に `Read(./.env)` / `Read(./.env.*)` / `Read(./secrets/**)` を置き、実在する鍵ファイル等があれば追加する。CLAUDE.md の「読むな」は advisory で、強制は permissions が行う）
- **複数 subagent / マルチエージェント構成の新規実装有無**（対象プロジェクトが複数 subagent を並列・逐次で起動するオーケストレーション機能を新規実装するか → あれば `agent-design.md` 採用。単一エージェント運用のみのプロジェクトでは非採用）
- **changelog 運用を望むか**（既存の `CHANGELOG.md` があれば追記運用に合流、無ければ `changelog-practice` 採用時のみ新規作成）
- **プロジェクトの目的**（何を解決しようとしているのか — 1〜2 文の課題定義）
- **進捗状況**（現在のフェーズ・主要マイルストーン達成状況・既知の未完了領域 — README / 外部 Issue トラッカー / commit 履歴、`issue-lifecycle` 採用時は `issues/processing/*.md` からも、事実ベースで抽出）

### Step 2: 候補セクション生成 + 要否判定

各セクションに「削除したら Claude が間違えるか」の基準を適用:

- `# Architecture` 直下 `This project uses TypeScript.` → `package.json` で分かる → 削除
- `テスト実行は npm run test:single -- <file>` → 推測で `npm test` されると全テスト走る → 残す
- 「コードは綺麗に書きましょう」 → 自明 → 削除

### Step 3: 段階的開示への分離

CLAUDE.md 本体に直接書かず、規約本文は採用した rules ファイルに分離する:

| 内容 | 逃がし先 |
|------|---------|
| 全タスク共通の規約（コード品質・テスト方針） | `.claude/rules/code-quality.md` / `test-verify.md`（frontmatter に `paths:` 無し = 起動時に常時 load） |
| 特定タスク時のみのルール（Issue・review・governance・マルチエージェント設計） | `.claude/rules/issue-workflow.md` / `review.md` / `governance.md` / `agent-design.md`（採用時のみ・`paths:` path-scope） |
| 実行主体・モデル格の振り分け規約（採用時） | `.claude/rules/execution-routing.md`（`paths:` 無し = 常時 load） |
| 条番号インデックスと既知の制約 | `.claude/rules/meta.md`（常時 load） |
| 詳細手順・長文 | `docs/[topic].md` → リンクのみ |
| 時々しか使わない知識・ワークフロー | `.claude/skills/[name]/SKILL.md`（公式推奨。commands は skills に統合済 = `.claude/commands/x.md` と `.claude/skills/x/SKILL.md` は同じ `/x` を作る。frontmatter `name` は任意・`description` 推奨。現行仕様は skills docs を WebFetch で確認） |
| 個人ノート | `CLAUDE.local.md`（`.gitignore` に追記する） |

`paths:` frontmatter 例:

```yaml
---
paths:
  - "**/*.ts"
  - "**/*.tsx"
---
[ルール本文]
```

rules の frontmatter で Claude Code が読むのは `paths` だけ（`name` / `description` 等は無視されるので書かない。用途の説明は本文の 1 行目に書く）。`paths:` に一致するファイルを Claude が Read した時に load される（公式仕様）。常時 load させたい場合は `paths:` を省略する（起動時に自動で読まれるので `@import` は不要）。

### Step 4: テンプレートで組み立て

`template.md` の出力テンプレートに project 固有値を埋める。該当しないセクションは削除可、ただし削除理由を明示する。

### Step 5: 自己評価ルーブリック

`rubric.md` の 36 項目で Y/N 評価する。N が 1 つでもあれば書き直す。opt-out の根拠は対象の `harness-selection.json` だけに置く: 要素 id 列の**全要素**が `selected: false`（`decided_by` は `user` か `scale`）の項目は「opt-out 記録済み」として Y、1 つでも選択済みならその id の観点で判定する（rubric.md 冒頭の規則）。スケール調整で落とした hooks / execution-routing.md / docs-management.md 等も `decided_by: "scale"` で記録してから Y にする（口頭の「不要宣言」では Y にしない）。逆に非選択要素が生成物に現れていれば、その項目は N（混入）。

### Step 6: サイズ確認

PowerShell では `(Get-Content <path>).Count` と `(Get-Item <path>).Length`、Bash では `wc -l` `wc -c` を実行する。実測値を末尾の `*[行数] 行 / [KB] KB*` に転記する（推定値は書かない）。公式目標（memory docs の Size 記述）を超えていたら Step 3 へ戻って分割を検討する。`size-guideline-100-lines` 採用時はさらに剪定の目安（概ね 100 行）も使う。**ただし行数を理由に出力拒否はしない**（公式の行数は目標であって出力拒否の閾値ではない。出力拒否は「Claude が指示を無視している」観察可能な兆候があった時のみ）。

### Step 7: 別エージェント公式準拠レビュー

生成物（CLAUDE.md + 採用 rules + settings.json hooks + hook scripts）を別エージェントに渡してレビューを受ける。渡すのは**対象の完全パスとレビュー用 skill / コマンドの 2 点のみ**。

レビュアの実施事項（WebFetch 取得・公式項目との突合・rules 実在確認・該当箇所の並置）、レビュアに渡す 2 点、合格基準（公式項目全 Y かつ `rubric.md` 全 Y）、不合格時の扱い（3 回 FAIL で中断・ユーザーに報告）は `step7-reviewer-procedure.md`。

### Step 8: 出力 & 採用セットの実生成 + 引継ぎ

採用セットの実生成（CLAUDE.md 本体・`.claude/rules/*.md`・hooks・roadmap・CHANGELOG）と最終報告の項目は `step8-step9-output-and-verify.md`。最終報告は次の項目を必ず含める: プロジェクト概要（大まかな説明・細かな説明・進捗状況）/ 生成内容の要約 3 行以内 / `> [要確認]` 残項目 / 生成ファイルのフルパス一覧 / 対象側のコミット・gitignore の区分 / 由来別の選択結果 / スケール調整で落とした要素と理由 / レビュア合格の事実と WebFetch 取得日時。

### Step 9: setup 後レビュー（対象が別プロジェクトの時は必須・省略不可）

生成後は `bash <本スキル dir>/scripts/harness-setup-state.sh phase generated` を実行し、`harness-setup-review` skill で機械検査（`provenance-check.sh --target`）と別エージェントの突合レビューを両方 PASS させてから `done` にする（3 回 FAIL で中断してユーザーに報告）。詳細手順と最終報告への記載事項は `step8-step9-output-and-verify.md`。

大タスク完了のため `/clear` を促す。対象で `handoff-management` が選択済みなら `/clear` 前に handoff を保存する（規約本体は「独自運用: handoff 管理」）。非選択なら handoff は作らず、最終報告を引継ぎとする。

## 使用例

| ユーザー発言 | 動作 | 結果 |
|---|---|---|
| 「`<別ディレクトリ>` に、この repo の仕組みを入れて」 | `harness-setup-state.sh start` → Step 0 で由来別に取捨選択 → Step 1〜8 で生成 → Step 9 の `harness-setup-review` | `CLAUDE.md` + 採用 rules + `.claude/harness-selection.json` が生成され、`provenance-check.sh --target` が PASS |
| 「CLAUDE.md が肥大化したので剪定して」（このリポジトリ内） | Step 0 を省略（新規生成物なし）し、Step 2・3・6 で要否判定・rules への分離・実測サイズ確認 | 剪定後の `CLAUDE.md` と、移した先の rules の一覧 |
| 「セットアップして」（対象の記載なし） | 起動しない。対象ディレクトリを 1 回だけ聞き返す | 対象が明示されてから本スキルを開始 |

## エラー時の対処

| 状況 | 対処 |
|---|---|
| 公式 URL の WebFetch 失敗 | 焼き込み版で代替しない。`_shared/anthropic-best-practices.json` の `fetched` が `max_age_days` 以内なら続行し、報告に「公式現行版との突合未実施」と明記。超過なら取得できるまで中断 |
| `provenance-check.sh` が FAIL | 出力された検査 id の指摘（台帳と実体の不整合）を直して再実行。台帳を書き換えて通すのは、実体が正しいと確認できた場合のみ |
| `--selection` / `--target` 検証が FAIL | 非選択要素の混入か選択要素の欠落。`harness-selection.json` と生成物を突き合わせて修正し再検証 |
| 対話不可で `AskUserQuestion` が使えない | `default_selection` のみ採用し、最終報告の冒頭に明記（好みを推測で補わない） |
| Step 7 / Step 9 のレビューが 3 回 FAIL | 中断してユーザーに報告（Step 7 末尾の起票条件に従う） |
| Stop hook が終了を block | `harness-setup-state.sh` の現在 phase を確認し、Step 9 を PASS させて `done` にする |

## 更新履歴

- 2026-09-01: when_to_use を「対象が明示された別プロジェクトのセットアップ依頼」へ拡張
- 1.1.0: 本文を supporting files へ分離（公式取得先・索引・Step 7〜9 の詳細）、前提節（repo 固有の依存と代替）を追加
- 以降の改修は `maintainer-checklist.md` の手順に従い、ここに 1 行で追記する

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
*準拠ソース: https://code.claude.com/docs/en/best-practices "Write an effective CLAUDE.md" — 由来台帳=`provenance.json` / 取捨選択=`selection-flow.md` / 出力テンプレート=`template.md` / ルーブリック=`rubric.md` / hooks=`hooks-reference.md` / メンテ=`maintainer-checklist.md`*
