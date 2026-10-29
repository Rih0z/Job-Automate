---
name: harness-compliance-audit
description: "CLAUDE.md・rules・skills・commands・agents・hooks 設定を新規作成または編集した直後のとき、その変更分が Anthropic 公式ベストプラクティスに従っているかを、機械検査 script と変更ファイルごとの独立エージェント判定の 2 段で監査し PASS/FAIL を出す。全 skill の一括監査（skills-audit または audit-skill-system）と単一 skill の 5 軸採点（/review-skill）には使わない。"
when_to_use: >
  skill を新しく作った直後、CLAUDE.md・rules・commands・agents・hooks 設定を編集した直後、
  「ベストプラクティスに沿っているか確認して」「公式準拠監査」「harness-compliance-audit」と言われたとき、
  PostToolUse hook が公式レビューを促したとき。
argument-hint: "[git ref（省略時は未 commit 変更 + 直近 1 commit）| ファイルパス...]"
allowed-tools: Read, Write, Glob, Grep, Bash, Agent
metadata:
  provenance: official-derived
  version: "1.1.0"
  history: "1.1.0 使用例・エラー処理・前提を追加し、description の重複を削減"
---

# harness-compliance-audit — 変更分の公式ベストプラクティス監査

**前提**: 本 skill は次の repo 固有の配置を前提にする。判定の SoT `.claude/skills/_shared/`、reviewer 定義 `.claude/agents/readonly-reviewer.md`（無ければ手順 2 の代替）、報告の保存先 `.tmp/`（無ければ応答本文のみ）。他 repo へ移す場合はこの 3 点を差し替える。
**何をするか**: 直近に変更した「ハーネス」ファイル（CLAUDE.md・`.claude/rules/**`・`.claude/skills/**`・`.claude/commands/**`・`.claude/agents/**`・`.claude/settings*.json`）だけを対象に、公式原則との適合を判定する。全体監査ではない（それはリポジトリの一括監査 skill＝`skills-audit` または `audit-skill-system`）。
**判定の SoT**: `.claude/skills/_shared/anthropic-best-practices.yaml` または `.json`（取得日 `fetched`・再取得条件 `refetch_when` 付き）。本文に基準を再掲しない。SoT と本 skill の記述が食い違えば SoT を正とする。
**実行主体**: 手順 2 の判定は、変更を行ったセッションではなく `Agent` tool で起動した別エージェントが行う（自己レビュー禁止）。呼び出し元は対象パスと SoT のパスだけを渡し、会話履歴・変更意図を渡さない。

## 手順

### 1. 機械検査（決定的・このセッションで実行）

```bash
bash .claude/skills/harness-compliance-audit/scripts/harness_check.sh $ARGUMENTS
```

- 引数なし: 未 commit 変更 + 直近 1 commit の変更ファイルを対象にする。git ref（例 `HEAD~3`）を渡すとその ref 以降、ファイルパスを渡すとそのファイルのみ。
- 出力は 1 行 1 検査（`CHECK <id> <PASS|WARN|FAIL> <file> <detail>`）。check id と対応する公式原則の対応表は [reference/checks.md](reference/checks.md)。
- FAIL が 1 件でもあれば終了コード 1。FAIL は手順 2 に進む前に修正するか、修正しない理由を報告に書く。
- 対象 0 件と表示されたときは `git log -1 --format='%h %ci'` と `git status --short` を報告に併記する（別 session の commit で差分が先に取り込まれたケースと「本当に変更なし」を見分けるため）。
- SoT の `fetched` が `max_age_days` を超えていれば WARN が出る。その場合は先に SoT の `refetch_when` 手順（各 `source` の URL を WebFetch し差分を principle 単位で反映して `fetched` を進める）を実行する。
- SoT が無い場合は `CHECK BP01 FAIL` が出る。手順 2 に進まず、SoT の作成または取得（`refetch_when` 手順）を呼び出し元へ依頼して、監査 FAIL として終える。

### 2. 独立エージェント判定（変更ファイルごと）

手順 1 が列挙した変更ファイル 1 件につき `Agent` を 1 本起動する（複数は同一メッセージで並列可）。`subagent_type` は `readonly-reviewer`（`.claude/agents/readonly-reviewer.md`。定義が無い環境・未読込のセッションでは `general-purpose` で起動し、prompt 冒頭に「ファイルを作成・変更・削除しない」と明記する）（リポジトリにモデル振り分け規約があればそれに従う）。渡すのは次の 4 点だけ:

```
対象ファイルの絶対パス:
公式原則 SoT の絶対パス:
観点の絶対パス: 本 skill の reference/checks.md（「エージェント判定の観点」節）
出力形式: review-result/v1（下記）
指示: 対象を Read し、SoT の principles のうち対象種別に該当するもの（skills / claude-md / memory / sub-agents / hooks / best-practices）を全件照合する。指摘には principle id と quote の逐語、対象の file:line を必ず付ける。id を付けられない指摘は出さない。correctness と明示要件に関わる gap のみ blocker/major とし、それ以外は minor/info（optional）にする。会話履歴や作成意図は与えられていない前提で、書かれている内容だけで判定する。編集はしない。
```

reviewer の出力（JSON のみ）:

```json
{
  "schema": "review-result/v1",
  "target": "<path>",
  "criteria_file": "<SoT path>",
  "score": 0,
  "total": 100,
  "verdict": "PASS | FAIL",
  "must_pass_failures": ["<principle id>"],
  "findings": [{"criterion_id": "<principle id>", "severity": "blocker|major|minor|info", "quote": "<公式 quote>", "location": "<file:line>", "comment": ""}],
  "missing_perspectives": []
}
```

- `verdict` は blocker が 0 件で PASS。score は 100 から blocker 20・major 10・minor 3 を減じた値（info は減点しない）。
- reviewer が JSON 以外を返した、または `review-result/v1` の必須キーを欠く場合は、その file を「判定不能」として表に載せ、同じ file だけ 1 回起動し直す。再度不正なら判定不能のまま報告し、総合は FAIL にする。
- `Agent` の起動自体に失敗した場合は、該当 file を「判定不能（起動失敗）」とし、機械検査の結果だけを報告して総合は FAIL にする。自分で代わりに判定しない。
- 種別ごとの必須観点（reviewer が最低限見る項目）は [reference/checks.md](reference/checks.md) の「エージェント判定の観点」。

### 3. 統合（このセッションで実行）

- 手順 1 の FAIL/WARN と手順 2 の JSON をそのまま並べる。判定をやり直さない・上書きしない（矛盾があれば「判定不能」と書く）。
- 全ファイルが PASS（機械検査 FAIL 0・blocker 0）なら監査 PASS。1 件でも FAIL なら監査 FAIL とし、呼び出し元が対象を修正してから手順 1 から再実行する（本 skill 自身は対象を編集しない。監査だけを依頼された run では修正せず FAIL を報告して終える）。3 回連続 FAIL で中断し、残る指摘を issue/課題として起票する（起票先はリポジトリの規約に従う）。
- 報告は `.tmp/harness-audit/<YYYY-MM-DD>-<short-sha>.md` に保存する（`.tmp/` が無いリポジトリでは応答本文のみ）。Write は、この報告ファイルの保存にだけ使う。

## 使用例とエッジケース

- 例: ユーザーが「skill を 1 本書いたので公式準拠を確認して」と言う。→ 手順 1 が未 commit の変更 1 件を列挙し、機械検査は FAIL 0・WARN 1。→ 手順 2 で別エージェントが blocker 0・major 1 を返す。→ 総合は PASS とし、major の principle id と file:line を表に載せて報告する。
- 例外: 対象が 0 件のときは手順 1 の記述どおり `git log` と `git status` を併記する。変更が `.claude/` 外だけなら「対象外」と報告して終える。
- 例外: 機械検査が FAIL のまま reviewer が blocker 0 を返した場合は、判定を上書きせず総合 FAIL とする。

## 出力形式

```
# harness-compliance-audit（対象: <ref または paths> / SoT fetched: YYYY-MM-DD）
## 機械検査: PASS|FAIL — FAIL n / WARN m
| id | 結果 | file | detail |
## エージェント判定
| file | score | verdict | blocker | major | 主な finding（blocker → major の順に最大 2 件・principle id + file:line） |
## 総合: PASS|FAIL（修正が必要な項目の一覧）
```

## やらないこと

- 対象ファイルの編集（監査のみ）。
- 公式に無い著者の運用嗜好を「非準拠」として減点すること（由来台帳 `provenance` が author-preference と分類する要素は、公式原則との矛盾がない限り指摘しない）。
- 全 skill の一括監査・単一 skill の 5 軸採点（それぞれ `skills-audit`／`audit-skill-system`・`/review-skill`）。
