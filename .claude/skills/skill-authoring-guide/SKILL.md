---
name: skill-authoring-guide
description: "Reference manual (based on Anthropic's official 'The Complete Guide to Building Skills for Claude') for designing, structuring, and testing SKILL.md files and Claude Code slash commands: folder structure, YAML frontmatter rules, progressive disclosure, instruction-quality patterns, and a pre-publish checklist. Use when the user asks to 'Skillを作りたい', 'SKILL.mdの書き方を教えて', 'スキル作成のベストプラクティスを確認して', 'descriptionの書き方', 'frontmatterに何を書く？', 'スキルを新規設計したい', or is the evaluation basis for /review-skill. Not for: auditing a just-edited skill against official practices (use harness-compliance-audit), scoring a skill or command after an update (use /review-skill), or whole skill-system audits (use skills-audit); this guide is a reference to consult while writing, not an executor."
metadata:
  provenance: official-derived
  version: "1.0"
---

# Claude Skills 作成マニュアル

> **出典**: Anthropic "The Complete Guide to Building Skills for Claude" (PDF)
> **構造化データ**: 公式原則の要約は `.claude/skills/_shared/anthropic-best-practices.json`（`category: skills`）が SoT。本文と食い違う場合は構造化データ側を正とし、`refetch_when` に該当すれば公式 docs を WebFetch して更新する。
> **目次**: 1 基本構造 / 2 Progressive Disclosure / 3 YAML フロントマター / 4 命令の書き方 / 5 詳細リファレンス（references/） / 6 Claude Code での扱い / 困ったとき / 出典・関連
> **用途**: Skills の設計・作成・テスト・配布のリファレンス。`/review-skill` の評価基準として参照する。

> **この guide の使い方と出力**: 質問への回答の形式は「回答テンプレートと完了条件」の 4 見出し固定が唯一の指定。新規 skill の設計相談だけは、4 見出しの代わりに `## 4` の推奨構造に沿った SKILL.md の骨子を示す。
> **行動原則**: 公式原則の出典 (本文または構造化データ) に無いことを「公式の決まり」として断定しない。分からない点は `refetch_when` に従って公式 docs を確認する。他の skill や設定ファイルは、依頼されない限り編集しない。
> **前提・他プロジェクトで使う場合**: 本リポジトリ固有の参照は下の「前提と代替」にまとめた。コピー先に無ければ代替で読み替え、存在しないパスは案内しない。

## 前提と代替（本リポジトリ固有の参照）

| 本文に出る参照 | 役割 | 無い環境での代替 |
|---|---|---|
| `.claude/skills/_shared/anthropic-best-practices.json` | 公式原則の要約（SoT）。`skills.*` の principle id と `refetch_when` を持つ | Anthropic 公式の Skills docs と Best practices を直接確認し、principle id は節番号に読み替える |
| `workflows/software-development/skills-building-guide.md` | 本 guide の原文 | 不要（本文だけで完結する） |
| `.claude/agents/readonly-reviewer.md` | 書き込み禁止のレビュー用 subagent の定義例 | 自分の環境で `tools` に読み取り系だけを許可した subagent を作る |
| `skills-audit`、`/review-skill`、`harness-compliance-audit` | 監査・採点を担当する別 skill | 無ければ「公開前チェックリスト」（references/testing-and-checklist.md）で自己点検する |

---

## 回答テンプレートと完了条件

この guide は参照マニュアルなので、同じ質問には同じ構造で答える。質問への回答は次の 4 見出し固定で書く。

```
### 結論
（どう書くか。1〜3 文）
### 根拠
（本 guide の節番号、または `skills.*` principle の id。両方あれば両方）
### 良い例 / 悪い例
（各 1 組。コードブロックで示す）
### 次に確認すること
（公開前チェックリストのうち該当する 1〜3 項目。無ければ「なし」）
```

- 新規 skill の設計相談では、上の 4 見出しの代わりに `## 4` の推奨構造に沿った SKILL.md の骨子を示し、その後に「根拠」だけ添える。
- 含めない情報: 質問と無関係な節の要約、本 guide に出典のない「公式の決まり」、依頼されていない他 skill の編集案。
- 完了条件(次の 4 つがすべて真なら回答完了。1 つでも偽なら書き直す):
  1. 回答に節番号または principle id が 1 つ以上ある
  2. 良い例と悪い例が各 1 件ある
  3. 出典の無い内容を「公式」と断定していない
  4. 回答中のファイル名・パスが、`## 1` の命名規則と矛盾していない
- 採点目安(自分の回答を見直すときの 5 段階。3 以下は書き直す): 5 = 4 見出しすべて・完了条件 4 つ全真 / 4 = 1 見出しが薄い / 3 = 根拠か例が欠ける / 2 = 結論のみ / 1 = 質問に答えていない。

## 使用例

- 正常系: 「description の書き方を教えて」→ `## 3` の「description の書き方」を根拠に、上のテンプレートで結論(何をするか + いつ使うか + 主な機能の順)・良い例 1 件・悪い例 1 件を返す。
- 設計相談: 「議事録整形の skill を新しく作りたい」→ `## 4` の推奨構造に沿って name / description / Step 1〜 / Examples / Troubleshooting の骨子を示す。description は 1024 文字以下、山括弧を含めない。
- 失敗系: 「この skill を採点して」→ 採点は /review-skill、直近変更の監査は harness-compliance-audit の担当と伝え、この guide では採点しない。「公式ではこう決まっている」と本 guide に無い内容を聞かれたら、断定せず `refetch_when` に従って公式 docs の確認を勧める。

---

## 1. Skills の基本構造

### Skill とは

Skill はフォルダとして構成され、Claude に特定のタスクやワークフローを教える命令セット。

### フォルダ構成

```
your-skill-name/
├── SKILL.md          # 必須 — メインの命令ファイル
├── scripts/          # 任意 — 実行可能コード（Python, Bash等）
├── references/       # 任意 — 必要に応じて読み込むドキュメント
└── assets/           # 任意 — テンプレート、フォント、アイコン等
```

### 命名規則

| ルール | 正 | 誤 |
|--------|-----|-----|
| kebab-case | `notion-project-setup` | `Notion Project Setup` |
| スペース禁止 | `my-skill` | `my skill` |
| アンダースコア禁止 | `my-skill` | `my_skill` |
| 大文字禁止 | `my-skill` | `MySkill` |

### 禁止事項

- SKILL.md 以外の名前（`skill.md`, `SKILL.MD` 等）は不可
- フォルダ内に `README.md` を含めない（ドキュメントは SKILL.md か references/ に記載）
- スキル名に `claude` や `anthropic` を含めない（予約語）
- YAML フロントマターに XML タグ（`<` `>`）を含めない

### 個人用にカスタマイズする場合

既存の共有 skill（project 直下 `.claude/skills/`）を個人用に調整したい時は、**ゼロから作り直さず**、SKILL.md を別名で `~/.claude/skills/` にコピーしてから変更する。既存の動作する実装を土台にでき、車輪の再発明を避けられる。**別名にすること**でチーム共有 skill との名前衝突（shadowing、同名なら user-level が project-level を覆い隠す）も避けられる。

---

## 2. Progressive Disclosure（段階的開示）

Skills は3段階の情報開示構造を持つ:

| レベル | 内容 | 読み込みタイミング |
|--------|------|---------------------|
| **第1層: YAML フロントマター** | スキルの名前・説明・トリガー条件 | 常時（システムプロンプトに含まれる） |
| **第2層: SKILL.md 本文** | 完全な命令・ガイダンス | スキルが関連すると判断された時 |
| **第3層: リンクファイル** | references/ 等の追加ドキュメント | 必要に応じて参照 |

**設計原則**: トークン消費を最小化しつつ、専門的な知識を維持する。

---

## 3. YAML フロントマター

### 必須フィールド

```yaml
---
name: your-skill-name
description: What it does. Use when user asks to [specific phrases].
---
```

### フィールド仕様

| フィールド | 必須 | 仕様 |
|-----------|------|------|
| `name` | 必須 | kebab-case、スペース・大文字不可、フォルダ名と一致 |
| `description` | 必須 | 「何をするか」+「いつ使うか（トリガー条件）」を含む。1024文字以下 |
| `license` | 任意 | MIT, Apache-2.0 等 |
| `compatibility` | 任意 | 環境要件。1-500文字 |
| `metadata` | 任意 | カスタムキーバリューペア（author, version, mcp-server 等） |

### `context: fork` の分離範囲（誤解しやすい）

`context` frontmatter フィールドに `fork` を指定すると、そのskillは分離された会話コンテキストで実行される（冗長な出力をメインセッションのコンテキストに残さない用途）。上表は必須/主要フィールドのみを列挙しており `context` を含まないが、実在するオプションフィールドである。**分離されるのはモデルの会話コンテキスト（記憶）のみ**であり、**ファイルシステムは分離しない**。fork内で `Write` / `Edit` 等のツールを実行すると、その結果は実際のファイルシステムに直接反映される。

- **誤り**: fork内で処理した結果を一度メインセッションの応答として返し、メイン側で改めてファイルへ書き出す（不要な回り道）
- **正しい**: fork内で直接ファイルへ書く（会話コンテキストが分離されていても、書き込みは即座に反映される）。確認プロンプトを減らしたい時は `allowed-tools` に書き込み系ツールを入れるが、これは**事前承認であってツールの制限・付与ではない**（使えるツールを絞りたい時は subagent 定義の `tools` / `disallowedTools` か permissions の deny を使う）
- **既定は background 実行**: fork した subagent は既定で background で走り、結果は完了時に会話へ届く。呼んだ turn で結果を待って続きの手順に使うなら frontmatter に `background: false` を書く。background の fork の編集は checkpoint の外で行われ `/rewind` では戻らない（git で戻す）

### skill 本文のライフサイクル（常設の指示として書く）

呼ばれた skill の本文は 1 つのメッセージとして会話に残り、以後の turn で再読込されない。「最初の 1 回だけ」を前提にした書き方ではなく、作業全体に効く**常設の指示**として書く。auto-compaction 後は各 skill の最新呼び出しが先頭から一定量だけ再添付されるので、重要な指示は本文の先頭に置く。本文中の `` !`command` `` は失敗すると skill の起動全体が中断されるので、失敗し得るコマンドは `|| true` 等で吸収する。skill のディレクトリ名に予約名（`anthropic-skills` など）を使わない。（観点の SoT: `anthropic-best-practices.json` の `skills.content-persists-standing-instructions` / `skills.dynamic-context-and-arguments` / `skills.reserved-names` / `skills.allowed-tools-is-preapproval` / `skills.context-fork-runs-in-background`）

### description の書き方

**構造**: `[何をするか] + [いつ使うか] + [主な機能]`

**良い例**:
```yaml
# 具体的でアクション可能
description: Analyzes Figma design files and generates developer handoff documentation. Use when user uploads .fig files, asks for "design specs", "component documentation", or "design-to-code handoff".

# トリガーフレーズを含む
description: Manages Linear project workflows including sprint planning, task creation, and status tracking. Use when user mentions "sprint", "Linear tasks", "project planning", or asks to "create tickets".
```

**悪い例**:
```yaml
# 曖昧すぎる
description: Helps with projects.

# トリガーがない
description: Creates sophisticated multi-page documentation systems.

# 技術的すぎてユーザートリガーがない
description: Implements the Project entity model with hierarchical relationships.
```

---

## 4. 命令の書き方ベストプラクティス

### 推奨構造

```markdown
---
name: your-skill
description: [...]
---

# Your Skill Name

## Instructions

### Step 1: [First Major Step]
Clear explanation of what happens.

### Step 2: [Next Step]
...

## Examples

### Example 1: [common scenario]
User says: "..."
Actions: ...
Result: ...

## Troubleshooting

### Error: [Common error message]
Cause: [Why it happens]
Solution: [How to fix]
```

### 命令の品質基準

| 原則 | 良い例 | 悪い例 |
|------|--------|--------|
| 具体的・アクション可能 | `Run python scripts/validate.py --input {filename}` | `Validate the data before proceeding.` |
| エラーハンドリング含む | 具体的なエラーと対処法を列挙 | エラー対処の記載なし |
| 参照ファイルを明示 | `references/api-patterns.md を参照` | 暗黙の前提知識 |
| Progressive Disclosure | SKILL.md はコア命令のみ、詳細は references/ | すべてを SKILL.md に記載 |

### 曖昧な記述を避ける

```markdown
# 悪い
Make sure to validate things properly

# 良い
CRITICAL: Before calling create_project, verify:
- Project name is non-empty
- At least one team member assigned
- Start date is not in the past
```

## 5. 詳細リファレンス（references/、必要になった時だけ読む）

| 知りたいこと | 読むファイル |
|---|---|
| 決定的な強制 vs 確率的な依頼、Few-shot 例の個数と欠損値、出力スキーマの `required` 設計 | [references/instruction-design.md](references/instruction-design.md) |
| ユースケースカテゴリ 3 種、パターン 1〜6（ルーター型 skill を含む） | [references/use-case-patterns.md](references/use-case-patterns.md) |
| トリガー・機能・性能テスト、評価シナリオを先に作る手順、反復の表、公開前チェックリスト | [references/testing-and-checklist.md](references/testing-and-checklist.md) |

本当に守らせたい規律は、指示文の追加だけでなくスクリプト・スキーマ検証で強制する（詳細は instruction-design.md）。

---

## 6. Claude Code での扱い（commands は skills に統合済み）

Claude Code では custom commands は skills に統合されている。`.claude/commands/x.md` と `.claude/skills/x/SKILL.md` はどちらも `/x` を作るが、本リポジトリでは新規作成・移行ともに `.claude/skills/<name>/SKILL.md` に統一する（旧 `.claude/commands/*.md` は移行済み）。本ガイドの原則はそのまま適用される。Claude Code 固有の frontmatter（`argument-hint` / `arguments` / `disable-model-invocation` / `user-invocable` / `allowed-tools` / `model` / `effort` / `context: fork` + `agent` / `background` / `paths` / `hooks` 等）は skills docs の Frontmatter reference を参照する。

繰り返し起動するレビュアーや調査役は skill 本文に指示を毎回書くより、`.claude/agents/<name>.md` に subagent として定義し、`tools` / `disallowedTools` で書き込み等を禁止する（本リポジトリでは `.claude/agents/readonly-reviewer.md`）。

---

## 困ったとき (Troubleshooting)

| 症状 | 原因 | 対処 |
|------|------|------|
| skill がアップロード/読込できない | フォルダ・ファイル名が `SKILL.md` でない、フロントマターの `---` 欠落、name にスペース・大文字 | `## 1` の命名規則と `## 3` のフィールド仕様を再確認する |
| フロントマターのエラーになる | description に `<` `>` や YAML 的に危険な記号 (コロン等) を含む | 山括弧を外し、複数行は block scalar か引用符で囲む |
| 発火しない / 発火しすぎる | description のトリガー不足または広すぎる | references/testing-and-checklist.md の反復の表に従い、フレーズ追加またはネガティブトリガー追加 |
| 構造化データと本文が食い違う | 本文が古い | 構造化データ (`anthropic-best-practices.json`) を正とし、本文を直す |
| 参照パス (`_shared/...` 等) が無い | 他プロジェクトにコピーした | 上記「他プロジェクトで使う場合」のとおり公式 docs で読み替える |

---

## 参考リンク

- Anthropic Skills Documentation
- GitHub: anthropics/skills（公式スキルリポジトリ）
- skill-creator skill（Claude.ai 内蔵）

---

## 出典・関連

原文: `workflows/software-development/skills-building-guide.md`。`.claude/skills/review-skill/SKILL.md`（`/review-skill`）の評価基準本体としても参照される。本リポジトリの `.claude/skills/skills-audit/SKILL.md` と役割が近接するため、重複が疑われる場合はメンテナンスIssueで整理すること。

---

## 更新履歴

- 1.0（現行）: SKILL.md 本文（1 基本構造〜6 Claude Code での扱い、困ったとき）と references/ 3 ファイル（instruction-design.md / use-case-patterns.md / testing-and-checklist.md）で構成。回答は 4 見出し固定のテンプレートで返す。
- 2026-10-30: 回答テンプレート・完了条件・採点目安・使用例・前提と代替の表を追加（version は据え置き）
