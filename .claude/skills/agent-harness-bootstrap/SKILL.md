---
name: agent-harness-bootstrap
description: 任意のプロジェクトに対し、Anthropic 公式 Best Practices（"Write an effective CLAUDE.md"）に準拠した CLAUDE.md と、それを支える運用 harness（rules ファイル群 + hooks）を生成・剪定する。公式準拠の核と、独自の運用ノウハウをラベル分離して適用する。要素ごとの由来（公式 / 著者嗜好）を provenance.json で分け、別プロジェクトへ適用する時は著者嗜好をデフォルト非採用にしてユーザーが取捨選択する。
when_to_use: 「CLAUDE.md を作って」「`/init` の代わりに公式準拠で生成して」「既存の CLAUDE.md を公式 Best Practices で書き直して」「CLAUDE.md が肥大化したので剪定して」「(Job-Automate の) 仕組みを別プロジェクト `<対象>` にも入れて」「このリポジトリのノウハウで `<対象ディレクトリ>` をセットアップして」等、**対象(このリポジトリ以外の別ディレクトリ/別リポジトリ) が明示された**依頼全般 (2026-09-01 拡張、Job-Automate CLAUDE.md「他プロジェクトのセットアップ依頼への対応」と同期。対象が明示されない曖昧な「セットアップして」は対象外)
metadata:
  provenance: mixed
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
| `criteria/porting-reconciliation.json` | 移植完了後の突合レビュー観点（review-gate 形式: 記録の完全性 / 抜けゼロ / 混入ゼロ / 依存整合 / 報告の開示） | Step 0 突合レビュー |
| `template.md` | CLAUDE.md 本体の出力テンプレート（雛形・ブロックごとに要素 id マーカー付き） | Step 4 |
| `rubric.md` | 自己評価ルーブリック 36 項目（Y/N・要素 id 列付き。非選択要素の項目は opt-out 宣言で Y） | Step 5 / Step 7 |
| `hooks-reference.md` | hooks 化判断・参考 6 hook 構成・settings.json 例・hook script 雛形（PowerShell / bash） | Step 8-3 |
| `operational-knowhow.md` | 本スキル独自の運用ノウハウの詳細本文（スケール調整・標準セット・governance.md 項目群・handoff/issue 運用・レビューサイクル等、下記索引の全項目） | Step 1〜8 全般。索引だけで足りない時に参照 |
| `maintainer-checklist.md` | 本スキル更新者向けメンテ checklist（生成物評価には無関係） | 本スキル改修時 |

---

## 公式準拠の核（実行時 WebFetch 必須・本スキルに焼き込まない）

> Anthropic 公式は随時更新される。**公式の文言・テーブル・数値・API 契約を本スキルに転記（焼き込み）しない**。生成・レビュー開始時に下記を WebFetch で取得し、その時点の現行版で判定する（記憶・過去の引用で代替しない。WebFetch 失敗時は焼き込み版で代替せず、取得できるまで生成を中断する）。
>
> 焼き込み禁止の根拠は公式 Exclude 項目「Information that changes frequently」と同根。過去に転記した Include/Exclude テーブルが現行公式とドリフトした実例があり、転記は腐る。

### 取得対象と確認項目（名称のみ列挙・本文/テーブル/数値は取得して読む）

| URL | 取得時に現行版を確認する項目 |
|---|---|
| `https://code.claude.com/docs/en/best-practices`（"Write an effective CLAUDE.md" / "Avoid common failure patterns" / "Add an adversarial review step"） | 行の要否判定基準の文言（**固定の名称ではなく都度の言い回しを確認する**。2026-09-02 確認時点では「削除したら Claude がミスするか」という問い掛け形式）/ Include・Exclude テーブルの現行内容 / サイズ・行数の記述（数値閾値の有無）/ emphasis ガイダンス / 5 配置 + `@path` import / hooks（advisory との対比）/ Writer-Reviewer・adversarial review の注意（reviewer は gap を過剰報告しがち → correctness と明示要件に関わる gap のみ採用） |
| `https://code.claude.com/docs/en/skills` | SKILL.md 必須・frontmatter（`name` 任意 / `description` 推奨 / `description`+`when_to_use` の文字数上限）/ 本文の recurring token cost と簡潔性 / progressive disclosure（supporting files で参照分離）/ SKILL.md 行数の目安 / commands と skills の統合 / `disable-model-invocation` 等 |
| `https://code.claude.com/docs/en/hooks`・`https://code.claude.com/docs/en/hooks-guide` | hook イベント別の出力契約（どの stdout が context 注入されるか / `exit 2` の意味 / `additionalContext` JSON / Stop の連続 block 上限など、hook 生成直前に現行仕様を確認） |

取得後、冒頭に「取得日時 + 確認した現行原則の要点」を出力してから生成・レビューに進む。この WebFetch は省略しない。

### 本スキル由来の独自運用基準（公式転記ではない・保持する）

公式の文言ではなく本スキル由来の運用判断。公式が変わっても独自基準として有効だが、取得時に公式と矛盾しないか都度突合する:

- **emphasis（IMPORTANT / YOU MUST）は最大 5 件目安**。それ以外の語気強め（必須・禁止・絶対）は平叙文化する（公式 emphasis 許容を運用上引き締めた独自基準）
- **行数による出力拒否ゲートを設けない**。公式が数値閾値を持たないことを取得時に確認した上で、剪定判断は "rules getting lost in the noise" の兆候を主基準にする（数値は参考値）

---

## 本スキル独自の運用ノウハウ（索引）

> 公式には記述がない本スキルの設計判断。プロジェクトに合わせて緩めてよい。詳細本文は `operational-knowhow.md` を参照（各項目名で検索可）。各項目の由来は `provenance.json` に登録済みで、`official-derived`（公式原則の具体化・推奨）と `author-preference`（著者の運用嗜好・**デフォルト非採用**）に分かれる。author-preference の項目は、別プロジェクトへの適用時に Step 0 でユーザーが選んだ場合のみ生成する:

- **規模に応じたスケール調整** — 標準セットは上限像。該当する条文・確実に毎回実行したい規律・採用判定を通ったオプションファイルだけ生成する
- **サイズの目安** — CLAUDE.md 本体 100 行 / 10KB で剪定検討、常時 load rules は個別 5KB soft cap（数値は参考値、"rules getting lost in the noise" 兆候を主基準にする）
- **標準セット構成** — `CLAUDE.md` 本体 + `.claude/rules/*.md`（公式原則由来のコア + Step 0 の選択に依存する author-preference 由来のファイル）+ hooks。`paths:` + `@import` の二重防壁の理由（[Issue #23478](https://github.com/anthropics/claude-code/issues/23478)）
- **実行主体・モデル格の振り分け規約**（`execution-routing.md`）— 司令塔の 3 責務・振り分け表・高コスト主体抑制・escalation protocol
- **関連 docs 読込宣言** — タスク開始時に関連 docs を読み、宣言の最初と最後の両方に証跡を出力
- **条文宣言の lazy load 運用** — 該当条のみ宣言、全条一括宣言はしない
- **governance.md の項目群** — サイズ閾値・新項目ルーティング・公式準拠・定期レビュー・自動検証・常時 load cap・新条文追加手順（5 段チェックリスト）・advisory→hook 昇格判断（zero-exception 語気の条文は hook 化候補か判定）
- **handoff 受領** — user 明示指示でのみ受領、本文は自動 Read しない。stale 誤受領防止・archive ローテーション
- **並走 agent 痕跡 4 軸 recheck** — session 開始時 / plan 起票前に commit・handoff/plan・worktree・uncommitted Edit の 4 軸を確認
- **issue ライフサイクル管理**（open → processing → closed）— close 前検証 4 段、問題発見即起票ルール、1 issue = 1 目的
- **PC 再起動・session 復元の自動化** — SessionStart hook でポインタのみ通知、本文 Read は user 選択後
- **handoff 管理** — 命名規約・保持・issue 連携
- **規約の hooks 化判断** — advisory → deterministic 昇格の判断基準（詳細は `hooks-reference.md`）
- **自作 skill / MCP ツールの品質基準の継承**（該当時のみ）— 対象プロジェクトが独自 skill / MCP ツールを新規作成する場合、`skill-authoring-guide`（few-shot 設計・決定的強制・個人カスタマイズ）/ `mcp-server-setup`（構造化エラー応答設計）の観点をレビュー基準に含める
- **別エージェントレビューサイクル** — 対象完全パス + レビュー用 skill のみ渡す、並列本数・TDD test-first・ループ上限・自己レビュー不可・過剰報告の抑制
- **収束型自律前進**（オプション）— 独立レビュー 2 本以上収束後は user 確認を待たず進行可。6 類の例外は必須確認
- **成果物の生成主体明示** — LLM 生成物 vs script/lib 生成物を厳格に区別

---

## 入力

- プロジェクトディレクトリ（`ls -R` / `tree` / 主要ファイル中身）
- マニフェスト（`README.md`, `package.json`, `pyproject.toml`, `go.mod` 等）
- 既存 CLAUDE.md（更新時）

> このリポジトリのノウハウを土台にした別プロジェクトのセットアップ依頼では、先にリポジトリ CLAUDE.md の「他プロジェクトのセットアップ依頼への対応 — 完全列挙 + 由来別選択ルール」を適用する。`provenance.json` の全要素と CLAUDE.md の全セクションを列挙した移植チェックリストを作り、Step 0（`selection-flow.md`）でユーザーに由来別の取捨選択をさせてから Step 1 以降に入る。移植後は別エージェントによる突合レビューで「選択済み要素の抜けゼロ」と「非選択要素の混入ゼロ」の両方を確認する。

---

## 生成手順

Step 0 で由来別の選択を確定し、次に**選択済み要素の範囲内で**「規模に応じたスケール調整」を行い（フル装備を上限に、該当条文の無い rules・毎回実行したい規律の無い hooks・採用判定を通らないオプションを落とす。落とした要素は `harness-selection.json` に `selected: false, decided_by: "scale"` で追記し、選択記録と生成物を一致させる）、Step 1〜8 へ進む。

### Step 0: 由来別の取捨選択（対象が別プロジェクトの時）

手順の本体は `selection-flow.md`。要点:

1. `provenance.json` を Read し、要素を 4 群で提示する: A `official`（デフォルト採用）/ B `official-derived`、および `default_selection_override: recommend` を持つ要素（推奨・事前チェック済み・外せる）/ C それ以外の `author-preference` `third-party` `domain-prompt`（**デフォルト非採用**・選んだものだけ）/ D `repo-specific`（移植不可・提示のみ）
2. 対話可能なら `AskUserQuestion`（multiSelect）で C から取り込む要素を選ばせ、A・B から外す要素の有無を聞く。対話不可なら `default_selection` のみ採用し、その旨を最終報告の冒頭に明記する（ユーザーの好みを推測で補わない）
3. `depends_on` を欠く選択は成立しないことを示して再確認する
4. 決定を対象の `.claude/harness-selection.json` に**全要素分**（非選択も `selected: false` で）記録する
5. 以降の Step は選択済み要素だけを対象にする。非選択の author-preference 要素は rules 条文・hooks・template ブロック・skills コピー・付随 `files` のいずれにも現れてはならない
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

`rubric.md` の 36 項目で Y/N 評価する。N が 1 つでもあれば書き直す。opt-out の根拠は対象の `harness-selection.json` だけに置く: 要素 id 列の**全要素**が `selected: false`（`decided_by` は `user` か `scale`）の項目は「opt-out 記録済み」として Y、1 つでも選択済みならその id の観点で判定する（rubric.md 冒頭の規則）。スケール調整で落とした hooks / execution-routing.md / docs-management.md 等も `decided_by: "scale"` で記録してから Y にする（口頭の「不要宣言」では Y にしない）。逆に非選択要素が生成物に現れていれば、その項目は N（混入）。

### Step 6: サイズ確認

PowerShell では `(Get-Content <path>).Count` と `(Get-Item <path>).Length`、Bash では `wc -l` `wc -c` を実行する。実測値を末尾の `*[行数] 行 / [KB] KB*` に転記する（推定値は書かない）。`size-guideline-100-lines` 採用時は剪定の目安（概ね 100 行）を超えていたら Step 3 へ戻って剪定を検討する（非採用時は公式の簡潔さ基準と "rules getting lost in the noise" 兆候のみで判断する）。**ただし行数を理由に出力拒否はしない**（公式は数値閾値を持たない。出力拒否は「Claude が指示を無視している」観察可能な兆候があった時のみ）。

### Step 7: 別エージェント公式準拠レビュー

生成物（CLAUDE.md + 採用 rules + settings.json hooks + hook scripts）を別エージェントに渡してレビューを受ける。渡すのは**対象の完全パスとレビュー用 skill / コマンドの 2 点のみ**。

レビュアが必ず実施すること（= review skill が内包する評価手順）:

1. **YOU MUST** `WebFetch` で `https://code.claude.com/docs/en/best-practices` を取得する（記憶ベースで判定しない）。冒頭に取得日時と主要原則の引用を出力する
2. 公式 Include/Exclude / 行の要否判定基準 / 5 配置 / `@import` / emphasis に対し 1 項目ずつ Y/N 評価
3. 採用した rules ファイルが実在するか・条番号が通し管理されているかを Read で確認
4. 公式該当箇所と生成 CLAUDE.md 該当行を並べて示す

レビュアに渡すもの（**2 点のみ**）: ① レビュー対象の**完全パス**（絶対パス。中身はインライン貼付せずレビュアが自分で Read する）② 適用する **レビュー用 skill / コマンド名**。Step 0 を経た生成では、対象の `.claude/harness-selection.json` の完全パスを①に含める（レビュアはこれを読んで非選択要素の項目を opt-out 判定し、非選択要素の混入を N と判定する）。渡さないもの: ファイル中身のインライン貼付・本スキルの生成手順（Step 0〜6・8）・生成過程・会話履歴。対象プロジェクトに CLAUDE.md レビュー用の skill / コマンドが無い場合は、②の代わりに**上記「レビュアが必ず実施すること」の 4 項目（公式 URL を含む）をそのままレビュー指示として渡す**（これだけが本スキルからレビュアへ渡してよい部分）。

合格基準: 公式項目全 Y、かつ `rubric.md` の 36 項目も全 Y（部分合格・点数換算はしない。Step 5 と同一基準・opt-out 判定も同一）、かつ冒頭で WebFetch 取得日時引用がある。Web 取得していないレビューは無効、再依頼する。

不合格時: 修正して再レビュー。**3 回 FAIL で中断・ユーザーに報告**。対象で `issue-lifecycle` が選択済みなら `issues/open/[YYYY-MM-DD]-claude-md-generation.md` に起票し、非選択なら起票せず報告のみ（非選択要素のディレクトリを本スキル自身が作らない）。

### Step 8: 出力 & 採用セットの実生成 + 引継ぎ

レビュー合格後、project の事実に合わせて **採用セットを実生成**する（Step 1 で集めた事実から条文・規約・hook を埋める。スケール調整で落とした要素は生成しない）:

**1. CLAUDE.md 本体** — `template.md` に project 固有値（プロジェクト名・一行サマリ・コマンド・ルート構成・末尾入口リンク）を埋めて生成

**2. `.claude/rules/*.md`** — Step 1 事実から条文を抽出して生成（条番号は通し管理・ファイル間で重複させない）。**各行・各条文は Step 0 で `selected: true` の要素（「要素 id」列）に対応するものだけ生成する**。id 列の要素が全て非選択のファイルは作らない（条文ゼロのファイルを空作成しない）。「選択依存」と付けた行は author-preference 要素で構成され、デフォルトでは生成されない:

| ファイル | 内容 | 要素 id | YAML frontmatter | load |
|---|---|---|---|---|
| `meta.md` | 条インデックス（条見出し + 所在ファイル）+ **既知の制約（[claude-code Issue #23478](https://github.com/anthropics/claude-code/issues/23478) の path-scope auto-load Read 時のみ発火 bug を URL 付きで明記）**。`always-load-5kb-cap` 採用時のみ **常時 load ファイル 5KB soft cap 宣言** を加える | rules-split-progressive-disclosure / always-load-5kb-cap | なし | 常時 |
| `code-quality.md` | コード変更規約（命名・import・型）の条文。`generic-discipline-menu` 採用時は Step 1 で採否判定を通った汎用規律条文を加える | rules-split-progressive-disclosure / generic-discipline-menu | `description` のみ | `@import` で常時 |
| `test-verify.md` | テスト・自検証規約（ランナー・lint・受入基準）。採用時のみ加える条文: **close 前検証 4 段**［再現→pass / negative test / regression smoke / 証拠アーカイブ・`close-verification-4-steps`］・**成果物の生成主体明示**［LLM 生成物 vs script/lib 生成物の厳格区別・`artifact-generator-attribution`］・**数値目標の単一 SoT 化**［カバレッジ%・合格率等の閾値を prose に手書きせず、閾値を強制する設定ファイル（CI workflow・validator script 等）を唯一の SoT とする。宣言値と実際の強制値が食い違う／複数箇所に重複記載されて片方だけ更新され stale 化する、という観察済みの失敗パターンを防ぐ条文。`numeric-target-single-sot`・author-preference だが default `recommend`（事前チェック済み・ユーザーが外せる）。実コードのカバレッジ計測対象がないプロジェクトでは「合格率」「品質スコア」等の類似閾値に読み替える］ | rules-split-progressive-disclosure / close-verification-4-steps / artifact-generator-attribution / numeric-target-single-sot | `description` のみ | `@import` で常時 |
| `issue-workflow.md`（**選択依存**） | Issue 起票・handoff・/clear 規約の条文（`issue-lifecycle`）+ handoff 命名・保持・user 明示指示受領・stale handoff 誤受領防止・archive（`handoff-management`）+ **並走 agent 痕跡 4 軸 recheck**（`concurrent-agent-4-axis-recheck`）。選択された要素の条文だけを載せる | issue-lifecycle / handoff-management / concurrent-agent-4-axis-recheck | `paths: ["issues/**", ".tmp/**"]` | path-scope |
| `review.md` | 別エージェントレビュー規約の条文（**渡すのは対象完全パス + レビュー用 skill のみ**・自己レビュー不可・skills 更新時の公式 Skills ガイド WebFetch レビュー = `separate-agent-review-cycle`）。`review-cycle-parameters` 採用時のみ **2〜4 本並列 + converged findings**・**TDD test-first**・ループ上限［計画 3 周 / 実装 1 周］・90 点合格・3 回 FAIL 中断を加える | separate-agent-review-cycle / official-adversarial-review / official-skills-core / review-cycle-parameters | `paths: ["**/*.<lang>", ".claude/commands/**"]` | path-scope |
| `governance.md`（**選択依存**） | 肥大化防止・新項目追加規約の条文を **複数観点の項目群**（サイズ閾値 / 新項目ルーティング / 公式準拠 / 定期レビュー / 自動検証 / 常時 load ファイル cap 等・増減可）で記述。非採用時は official 由来の「新しい○○を追加する手順」（rubric 18）を CLAUDE.md 本体の 2〜3 行の節として残す | governance-multi-aspect | `paths: ["CLAUDE.md", ".claude/**"]` | path-scope |
| `execution-routing.md`（**選択依存**） | 司令塔の 3 責務 + 振り分け表（定型→低コスト / 高難度→高コスト / 方針→司令塔）+ 高コスト主体抑制（dispatch 5 点明示）+ escalation protocol | execution-routing | `description` のみ | `@import` で常時 |
| `docs-management.md`（**選択依存**: `docs/` 配下に概ね 5 section 以上） | docs 配置 mapping + 新 docs 配置 flow + 全 section README 必須化 + **同期更新義務**（構造的事実を複数箇所に重複保持せざるを得ない時は、コピー先を rule 本文に全て列挙し、コピー間の自動 diff/整合チェックを用意する — 単一 SoT を宣言して残りを放置しない）+ 過時マーカー "as of YYYY-MM-DD" 強制 | docs-management | `paths: ["docs/**/README.md", "docs/**/*.md", "CLAUDE.md", ".claude/rules/governance.md"]` | path-scope |

**3. `settings.json` の hooks セット + hook scripts**（採用時のみ） — 参考 6 hook 構成・settings.json 例（Windows PowerShell / Mac・Linux bash）・hook script（該当するもののみ生成）の役割と生成方法は **`hooks-reference.md` を参照**する。既存設定がある場合は `hooks` フィールドのみ追記（permissions / model 等は保持）。

**ユーザーへの最終報告**:
- **プロジェクト概要**（プロジェクト未読の第三者が読んでも理解できるレベルで書く。Step 1 で収集した事実のみを使い推測・捏造はしない）:
  - **大まかな説明** — 何を解決しようとしているのか（1〜2 文の課題定義 + 解決アプローチの要点）
  - **細かな説明** — 主要機能・技術スタック・想定ユーザー・スコープ境界（箇条書き 5〜10 項目）
  - **進捗状況** — 現在のフェーズ（PoC / α / β / 本番運用 等）・直近マイルストーン・既知の未完了領域・進行中 Issue 件数（`issue-lifecycle` 採用時は `issues/processing/*.md` の実数。非採用時は外部トラッカーの件数か「該当なし」）
- 生成内容の要約（3 行以内）
- `> [要確認]` 残項目
- **生成したファイル一覧（フルパス）**: CLAUDE.md / 採用 rules / settings.json / hook scripts / `.claude/harness-selection.json`（Step 0 実施時）
- **由来別の選択結果**（Step 0 実施時）: 群 C（著者嗜好・第三者・業務プロンプト）で採用した要素の一覧、群 A・B で外した要素と理由、対話不可で default のみ採用した場合はその旨
- **スケール調整で意図的に落とした要素**（採用しなかった rules / hooks / オプションファイルと、その理由を 1 行ずつ）
- レビュア合格の事実（公式項目 + rubric 全 Y）と、レビュアが冒頭に出力した WebFetch 取得日時

大タスク完了のため `/clear` を促す。対象で `handoff-management` が選択済みなら `/clear` 前に handoff を保存する（命名・保持・issue 連携の規約本体は「独自運用: handoff 管理」を正本とし、ここでは参照のみ）。非選択なら handoff は作らず、最終報告を引継ぎとする。

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
