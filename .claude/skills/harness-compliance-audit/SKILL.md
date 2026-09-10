---
name: harness-compliance-audit
description: "CLAUDE.md・.claude/rules・.claude/skills・.claude/commands・.claude/agents・hooks 設定を新規作成または編集した直後に、その変更分が Anthropic 公式ベストプラクティス（リポジトリ内の構造化キャッシュ anthropic-best-practices.yaml|json）に従っているかを監査する。機械検査 script と、変更ファイルごとの独立エージェント判定（principle id 付き）の 2 段で PASS/FAIL を出す。skill 新規作成直後・CLAUDE.md や rules の編集直後に使う。全 skill の一括監査（skills-audit または audit-skill-system）と単一 skill の 5 軸採点（/review-skill）は別 skill で、本 skill は直近の変更分に限定する。"
when_to_use: >
  skill を新しく作った直後、CLAUDE.md・rules・commands・agents・hooks 設定を編集した直後、
  「ベストプラクティスに沿っているか確認して」「公式準拠監査」「harness-compliance-audit」と言われたとき、
  PostToolUse hook が公式レビューを促したとき。
argument-hint: "[git ref（省略時は未 commit 変更 + 直近 1 commit）| ファイルパス...]"
allowed-tools: Read, Glob, Grep, Bash, Agent
metadata:
  provenance: official-derived
---

# harness-compliance-audit — 変更分の公式ベストプラクティス監査

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
- SoT の `fetched` が `max_age_days` を超えていれば WARN が出る。その場合は先に SoT の `refetch_when` 手順（各 `source` の URL を WebFetch し差分を principle 単位で反映して `fetched` を進める）を実行する。

### 2. 独立エージェント判定（変更ファイルごと）

手順 1 が列挙した変更ファイル 1 件につき `Agent` を 1 本起動する（複数は同一メッセージで並列可）。`subagent_type` は `general-purpose`（軽量モデルの executor があればそれでよい）。渡すのは次の 3 点だけ:

```
対象ファイルの絶対パス:
公式原則 SoT の絶対パス:
出力形式: review-result/v1（下記）
指示: 対象を Read し、SoT の principles のうち対象種別に該当するもの（skills / claude-md / memory / sub-agents / hooks / best-practices）を全件照合する。指摘には principle id と quote の逐語、対象の file:line を必ず付ける。id を付けられない指摘は出さない。会話履歴や作成意図は与えられていない前提で、書かれている内容だけで判定する。編集はしない。
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
- 種別ごとの必須観点（reviewer が最低限見る項目）は [reference/checks.md](reference/checks.md) の「エージェント判定の観点」。

### 3. 統合（このセッションで実行）

- 手順 1 の FAIL/WARN と手順 2 の JSON をそのまま並べる。判定をやり直さない・上書きしない（矛盾があれば「判定不能」と書く）。
- 全ファイルが PASS（機械検査 FAIL 0・blocker 0）なら監査 PASS。1 件でも FAIL なら監査 FAIL とし、修正 → 手順 1 から再実行。3 回連続 FAIL で中断し、残る指摘を issue/課題として起票する（起票先はリポジトリの規約に従う）。
- 報告は `.tmp/harness-audit/<YYYY-MM-DD>-<short-sha>.md` に保存する（`.tmp/` が無いリポジトリでは応答本文のみ）。

## 出力形式

```
# harness-compliance-audit（対象: <ref または paths> / SoT fetched: YYYY-MM-DD）
## 機械検査: PASS|FAIL — FAIL n / WARN m
| id | 結果 | file | detail |
## エージェント判定
| file | score | verdict | blocker | major | 主な finding（principle id + file:line） |
## 総合: PASS|FAIL（修正が必要な項目の一覧）
```

## やらないこと

- 対象ファイルの編集（監査のみ）。
- 公式に無い著者の運用嗜好を「非準拠」として減点すること（由来台帳 `provenance` が author-preference と分類する要素は、公式原則との矛盾がない限り指摘しない）。
- 全 skill の一括監査・単一 skill の 5 軸採点（それぞれ `skills-audit`／`audit-skill-system`・`/review-skill`）。
