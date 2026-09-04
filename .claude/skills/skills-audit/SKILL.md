---
name: skills-audit
description: Audit all custom skills in a repo for quality, structure, and Anthropic best practices. Checks frontmatter, descriptions, content organization, and argument handling. Complements single-skill scoring reviews by scanning every skill at once and tiering them (GOOD/MIGRATE/IMPROVE/SPLIT).
disable-model-invocation: true
allowed-tools: Glob Grep Read Agent
argument-hint: "[skill-name or blank for all]"
metadata:
  provenance: official-derived
---

# Skill Quality Audit

> **本スキルは各 skill ファイルの監査を Agent ツールで別エージェントに独立実行させる。現在のセッションでは各ファイルを直接読み込んで採点しない（self-review 禁止）。**
> 呼び出し元セッションの会話履歴・実装意図・設計判断は監査エージェントに渡さない。監査は対象ファイルの内容のみを根拠とする proof-by-presence（実際に Read した記述への具体的言及）で行う。

対象: $ARGUMENTS (省略時は全スキルを監査)

## Anthropic公式ベストプラクティス基準

> 基準の SoT は `.claude/skills/_shared/anthropic-best-practices.json`（`category: skills` の principle 群。取得日 `fetched` と再取得条件 `refetch_when` 付き）。監査開始時に `fetched` を確認し、`refetch_when` に該当すれば `source_url` を WebFetch して現行版と突合してから採点する。下記チェックリストは同ファイルの要約であり、食い違う場合は構造化データ側を正とする。

### 1. ファイル形式チェック
- [ ] 新形式 `.claude/skills/<name>/SKILL.md` を使用しているか（旧形式 `.claude/commands/*.md` は非推奨）
- [ ] YAMLフロントマター (`---` で囲まれた設定) が存在するか
- [ ] SKILL.md が500行以下か（超過時は reference.md / examples.md に分割）
- [ ] `name` に `claude` / `anthropic` が含まれていないか

### 2. フロントマター品質
- [ ] `description` が存在し、明確か（先頭にユースケース、250文字以内）
- [ ] 副作用のあるワークフローに `disable-model-invocation: true` が設定されているか
- [ ] バックグラウンド知識には `user-invocable: false` が設定されているか
- [ ] 必要なツールが `allowed-tools` で事前承認されているか
- [ ] 引数を受け取る場合 `argument-hint` が設定されているか

### 3. コンテンツ品質
- [ ] 単一責任（1スキル = 1ワークフロー）
- [ ] 指示が明確でアクション可能か
- [ ] `$ARGUMENTS` / `$N` による動的入力が適切に使われているか
- [ ] 曖昧な記述や汎用すぎる説明がないか
- [ ] 特定の企業名・製品名・非公開プロジェクト名がハードコードされていないか（公開リポジトリの場合は必須確認）

### 4. コンテキスト効率
- [ ] 動的コンテキスト注入 (`!`<command>```) を活用しているか
- [ ] 不要な定型文が含まれていないか
- [ ] description がClaude自動起動の判断に十分な情報を含むか

## 監査手順（エージェント分離実行）

**現在のセッション（この監査スキルを起動した側）が行うのは、対象ファイルの検出・Agent ツールへの dispatch・結果の統合のみ。個々の skill/command ファイルの内容を読み込んで自ら採点することはしない。**

### ステップ1: 対象ファイルの検出（このセッションで行う）

1. `.claude/skills/*/SKILL.md` と `.claude/commands/*.md` を Glob で全検出し、絶対パスの一覧を作る
2. `$ARGUMENTS` が指定されている場合はその skill 名に一致するファイルのみに絞る
3. 各ファイルの中身は読み込まない（読み込みは監査エージェント側の役割）

### ステップ2: 監査エージェントの起動

検出した対象ファイル1件（または関連の深いファイル群、例: SKILL.md と同一ディレクトリの reference.md）ごとに、**Agent ツール**で独立した subagent を起動して監査させる。複数ファイルを監査する場合は、複数の Agent 呼び出しを同一メッセージ内で並列起動してよい。

```
Agent ツールの設定:
- subagent_type: "general-purpose"
- description: "Audit skill file <対象ファイル名>"
- prompt: 以下のテンプレートに対象ファイルの絶対パスを埋め込む
```

**プロンプトテンプレート（監査エージェントに渡す内容）:**

```
あなたは Anthropic 公式ベストプラクティスに基づき Claude Code の skill/command ファイルを
独立監査する客観的なレビュアーです。

## 行動原則
- proof-by-presence: 対象ファイルを Read ツールで実際に読み込み、そこに書かれている記述のみを根拠に判定する
- 会話履歴・呼び出し元セッションの実装意図・設計判断は一切与えられていない。それらを根拠にした推測をしない
- 判定根拠には該当箇所の引用（行番号または該当テキスト）を必ず含める
- 非破壊: 監査のみ行い、対象ファイルの編集は行わない

## 監査対象
[ここに対象ファイルの絶対パスを埋め込む]

## Anthropic公式ベストプラクティス基準

> 基準の SoT は `.claude/skills/_shared/anthropic-best-practices.json`（`category: skills` の principle 群。取得日 `fetched` と再取得条件 `refetch_when` 付き）。監査開始時に `fetched` を確認し、`refetch_when` に該当すれば `source_url` を WebFetch して現行版と突合してから採点する。下記チェックリストは同ファイルの要約であり、食い違う場合は構造化データ側を正とする。

### 1. ファイル形式チェック
- [ ] 新形式 `.claude/skills/<name>/SKILL.md` を使用しているか（旧形式 `.claude/commands/*.md` は非推奨）
- [ ] YAMLフロントマター (`---` で囲まれた設定) が存在するか
- [ ] SKILL.md が500行以下か（超過時は reference.md / examples.md に分割）
- [ ] `name` に `claude` / `anthropic` が含まれていないか

### 2. フロントマター品質
- [ ] `description` が存在し、明確か（先頭にユースケース、250文字以内）
- [ ] 副作用のあるワークフローに `disable-model-invocation: true` が設定されているか
- [ ] バックグラウンド知識には `user-invocable: false` が設定されているか
- [ ] 必要なツールが `allowed-tools` で事前承認されているか
- [ ] 引数を受け取る場合 `argument-hint` が設定されているか

### 3. コンテンツ品質
- [ ] 単一責任（1スキル = 1ワークフロー）
- [ ] 指示が明確でアクション可能か
- [ ] `$ARGUMENTS` / `$N` による動的入力が適切に使われているか
- [ ] 曖昧な記述や汎用すぎる説明がないか
- [ ] 特定の企業名・製品名・非公開プロジェクト名がハードコードされていないか（公開リポジトリの場合は必須確認）

### 4. コンテキスト効率
- [ ] 動的コンテキスト注入 (`!`<command>```) を活用しているか
- [ ] 不要な定型文が含まれていないか
- [ ] description がClaude自動起動の判断に十分な情報を含むか

## 判定区分（4段階、いずれか1つを選ぶ）
- GOOD: ベストプラクティス準拠
- MIGRATE: 旧形式→新形式への移行が必要
- IMPROVE: 品質改善が必要（description不明確、フロントマター不足、固有名詞混入等）
- SPLIT: 責務過多で分割が必要

## 出力
以下を含む構造化レポートを返すこと:
- スキル名 / 形式 / 行数
- 4段階判定とその根拠（引用付き）
- 基準1〜4それぞれのチェック結果
- 具体的な修正提案
```

### ステップ3: 結果の統合（このセッションで行う）

各監査エージェントから返却された判定を、そのまま統合して以下の出力形式にまとめる。**このセッションが判定をやり直す・上書きすることはしない**（自己レビュー禁止）。判定に迷いや矛盾がある場合も、独自に再採点せず、判定不能である旨をそのまま記載する。

## 出力形式

| スキル名 | 形式 | description | frontmatter | 行数 | 判定 | 改善点 |
|---------|------|------------|-------------|------|------|-------|
