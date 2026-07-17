---
name: skills-audit
description: Audit all custom skills in a repo for quality, structure, and Anthropic best practices. Checks frontmatter, descriptions, content organization, and argument handling. Complements single-skill scoring reviews by scanning every skill at once and tiering them (GOOD/MIGRATE/IMPROVE/SPLIT).
disable-model-invocation: true
allowed-tools: Glob Grep Read
argument-hint: "[skill-name or blank for all]"
---

# Skill Quality Audit

対象: $ARGUMENTS (省略時は全スキルを監査)

## Anthropic公式ベストプラクティス基準

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

## 監査手順

1. `.claude/skills/*/SKILL.md` と `.claude/commands/*.md` を全検出
2. 各ファイルのフロントマターとコンテンツを読み込み
3. 上記基準で4段階評価:
   - GOOD: ベストプラクティス準拠
   - MIGRATE: 旧形式→新形式への移行が必要
   - IMPROVE: 品質改善が必要（description不明確、フロントマター不足、固有名詞混入等）
   - SPLIT: 責務過多で分割が必要
4. 具体的な修正提案を出力

## 出力形式

| スキル名 | 形式 | description | frontmatter | 行数 | 判定 | 改善点 |
|---------|------|------------|-------------|------|------|-------|
