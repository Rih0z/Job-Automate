---
name: skills-audit
description: Audit all custom skills in a repo against Anthropic best practices via subagents and tier each GOOD/MIGRATE/IMPROVE/SPLIT. Manual-only (/skills-audit [name]); e.g. skill を一括点検, 品質監査. Single skill: review-skill.
disable-model-invocation: true
allowed-tools: Glob Grep Read Agent
argument-hint: "[skill-name or blank for all]"
metadata:
  provenance: official-derived
  version: 1.2.0
  history: "1.2.0 基準とテンプレートを references/ に分離、出力例・JSON 形式・基準古化時の手順を追加"
---

# Skill Quality Audit

> **本スキルは各 skill ファイルの監査を Agent ツールで別エージェントに独立実行させる。現在のセッションでは各ファイルを直接読み込んで採点しない（self-review 禁止）。**
> 呼び出し元セッションの会話履歴・実装意図・設計判断は監査エージェントに渡さない。監査は対象ファイルの内容のみを根拠とする proof-by-presence（実際に Read した記述への具体的言及）で行う。

対象: $ARGUMENTS (省略時は全スキルを監査)

## 前提

- `.claude/skills/_shared/anthropic-best-practices.json`（基準の構造化データ）が存在すること
- `.claude/agents/readonly-reviewer.md`（書き込みツールを持たない監査用 agent）があると望ましい（無くても下記 fallback で動く）
- Agent ツールが使える環境であること
- 他リポジトリへコピーする場合は上記 2 ファイルも併せて用意する

## 参照ファイル

- [references/criteria.md](references/criteria.md): 基準チェックリスト（1〜4）と判定区分の閾値・優先順位。本スキル内の唯一の正本
- [references/audit-prompt.md](references/audit-prompt.md): 監査エージェントへ渡すプロンプトのテンプレートと出力形式

## 使用例

- `/skills-audit` → 全 skill と command を検出し、1 件ずつ別エージェントで監査して判定表を返す
- `/skills-audit review-skill` → 名前が一致する 1 件だけを監査し、判定表を返す（記入例は「出力形式」参照）
- 対象が 0 件（該当名なし・skill 未作成）→ 監査エージェントを起動せず「対象 0 件」と報告して終了する。指定名の綴りを確認するよう促す

## 監査手順（エージェント分離実行）

**現在のセッション（この監査スキルを起動した側）が行うのは、対象ファイルの検出・Agent ツールへの dispatch・結果の統合のみ。個々の skill/command ファイルの内容を読み込んで自ら採点することはしない。**

### ステップ1: 対象ファイルの検出（このセッションで行う）

1. `.claude/skills/*/SKILL.md` と `.claude/commands/*.md` を Glob で全検出し、絶対パスの一覧を作る
2. `$ARGUMENTS` が指定されている場合はその skill 名に一致するファイルのみに絞る
3. 各ファイルの中身は読み込まない（読み込みは監査エージェント側の役割）
4. 一覧が 0 件なら終了する（使用例参照）。`_shared/anthropic-best-practices.json` が無ければ監査を始めず、不在を報告して止める（基準なしで採点しない）
5. 同 JSON の `fetched` と `refetch_when` を確認する。再取得条件に該当（基準が古い）なら `source_url` を WebFetch して現行版と突合してから進める。WebFetch できない場合は JSON を正として続行し、出力表の末尾に「基準が古い可能性あり（取得日 fetched の値）」と注記する

### ステップ2: 監査エージェントの起動

検出した対象ファイル1件（または関連の深いファイル群、例: SKILL.md と同一ディレクトリの reference.md）ごとに、**Agent ツール**で独立した subagent を起動して監査させる。複数ファイルを監査する場合は、複数の Agent 呼び出しを同一メッセージ内で並列起動してよい。

```
Agent ツールの設定:
- subagent_type: "readonly-reviewer"（書き込み系ツールを持たない。定義が無い環境・新設直後で未読込のセッションでは "general-purpose" で起動し、prompt 冒頭に「ファイルを作成・変更・削除しない」と明記する）
- description: "Audit skill file (対象ファイル名)"
- prompt: references/audit-prompt.md のテンプレートに、対象ファイルの絶対パスと references/criteria.md の本文を埋め込んだもの
```

**エラー時の手順:**

- Agent の起動に失敗した: 同じ対象を 1 回だけ再起動する。再失敗したらその対象は「監査未実施（起動失敗）」と表に記載し、他の対象の監査は続ける。このセッションで代わりに採点しない
- 判定が返らない（出力が空・4 段階のどれでもない）: 同じ prompt で 1 回だけ再依頼し、なお不明なら「判定不能」と記載する
- readonly-reviewer が無い: 上記の general-purpose fallback を使う

### ステップ3: 結果の統合（このセッションで行う）

各監査エージェントから返却された判定を、そのまま統合して下記の表にまとめる。**このセッションが判定をやり直す・上書きすることはしない**（自己レビュー禁止）。判定に迷いや矛盾がある場合も、独自に再採点せず、判定不能である旨をそのまま記載する。

## 出力形式

列の記入規則:

- 形式: `SKILL.md` または `command`
- description: 基準 2 の description 項目の結果。`OK`、または `未達（字数・理由）`
- frontmatter: 基準 2 のその他項目の結果。`OK`、または未達の項目名
- 行数: 整数
- 判定: GOOD / MIGRATE / IMPROVE / SPLIT のいずれか 1 つ
- 改善点: 監査エージェントの suggestions を優先度順に最大 3 件、1 件 1 文。GOOD なら `なし`

記入例（架空のスキル名）:

| スキル名 | 形式 | description | frontmatter | 行数 | 判定 | 改善点 |
|---------|------|------------|-------------|------|------|-------|
| example-report | SKILL.md | 未達（280 字） | OK | 120 | IMPROVE | description を 250 字以内にする |
| example-old | command | OK | 未達（allowed-tools なし） | 60 | MIGRATE | .claude/skills/example-old/SKILL.md へ移行する |
