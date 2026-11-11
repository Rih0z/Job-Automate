---
name: progress-report-format
description: "進捗報告（今週の進捗・週報・状況報告）を、固定の章立て（できるようになったこと／残った課題／取り組み別の状況／対外活動／来週の予定）で出力する。形式は criteria/report-format.json に構造化して保存してあり、データ（progress-report/v1）を検証して整形する。Use when the user asks '今週の進捗を出して', '進捗報告をまとめて', '週報を作って', '進捗を報告形式で'. 使わない場面: 応答末尾の 4 行の進捗サマリ（各 CLAUDE.md の別の規則）、議事録、成果物のレビュー。"
allowed-tools: Read Write Glob Grep Bash
argument-hint: "[期間 YYYY-MM-DD〜YYYY-MM-DD（省略時は直近 1 週間）]"
metadata:
  provenance: domain-prompt
  version: "1.1.0"
---

# 進捗報告の形式

進捗報告は最後に、この形式で出力する。形式の正本は `criteria/report-format.json`（章・見出し・行の書式・段階と状態の語・書き方の規則）。この SKILL.md に章や規則を重ねて書かない。

**出力例は型であって内容の雛形ではない。** 章の数・順序・見出し・行の書式を固定し、中身は毎回の作業の事実から書く。例の中身（件数・取り組み名）を流用しない。

## 手順（リポジトリのルートから実行）

1. 期間を決める。引数が無ければ直近 1 週間。事実は `git log --since=<開始日> --format='%h %ad %s' --date=short`、記録、会話で確かめられるものだけを使う。
2. `criteria/report-format.json` の `writing_rules` に従って、データを書く。形は `examples/report.example.json`（schema `progress-report/v1`）。作業用の置き場は `.tmp/reports/`（commit しない）。
   - 取り組みごとに `stage`（設計・実装・部品テスト・実機確認）と `progress`（未着手・途中・ほぼ完了・完了・完走せず）を選ぶ。補足は `note`。
   - 調べた不具合・解決した問題は、原因と直し方まで「今回できるようになったこと」に書く（規則 `w-issues`）。作業中の診断結果（ログ・応答・レビュー指摘）を会話と記録から洗い出し、書き漏らさない。原因が未確定のものは課題の章にも載せる。
   - 把握できない章（対外活動など）は推測で埋めず、「記録なし（要記入）」と書く。
3. 検証と整形: `python .claude/skills/progress-report-format/scripts/render_report.py .tmp/reports/<名前>.json`
   - 形式に合わなければ終了コード 1 で理由を stderr に出す（stdout は空）。直して再実行する。
4. 整形結果を、進捗報告の最後にそのまま出力する。

## 試験

`python .claude/skills/progress-report-format/scripts/test_render_report.py`（7 件）。

## 制約

- 整形は章立てと行の書式を機械で揃えるだけ。内容が事実かどうか、平易かどうかは検査しない（`writing_rules` は書く側と、別エージェントのレビューが守る）。
- 応答末尾の 4 行サマリ（問題・状態・次の一手・一般向け要約）は別の規則で、置き換えない。
