# Claude Skills 作成マニュアル

> **出典**: Anthropic "The Complete Guide to Building Skills for Claude" (PDF)
> **用途**: Skills の設計・作成・テスト・配布のリファレンス。`/review-skill` の評価基準として参照する。

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

---

## 5. ユースケースカテゴリ

### Category 1: Document & Asset Creation
ドキュメント・プレゼン・デザイン・コード等の一貫した高品質出力の作成。

**テクニック**: スタイルガイド埋め込み、テンプレート構造、品質チェックリスト

### Category 2: Workflow Automation
一貫した方法論で行うマルチステッププロセス。

**テクニック**: 検証ゲート付きステップ、テンプレート、レビュー・改善提案、反復ループ

### Category 3: MCP Enhancement
MCP サーバーが提供するツールアクセスを強化するワークフローガイダンス。

**テクニック**: MCP 呼び出しの順序制御、ドメイン知識埋め込み、エラーハンドリング

---

## 6. パターン集

### Pattern 1: Sequential Workflow Orchestration
マルチステッププロセスを特定の順序で実行。
- 明示的なステップ順序
- ステップ間の依存関係
- 各段階でのバリデーション
- 失敗時のロールバック

### Pattern 2: Multi-MCP Coordination
複数サービスにまたがるワークフロー。
- 明確なフェーズ分離
- MCP 間のデータ受け渡し
- 次フェーズ前のバリデーション

### Pattern 3: Iterative Refinement
反復で出力品質を向上。
- 明示的な品質基準
- バリデーションスクリプト
- 停止条件の明確化

### Pattern 4: Context-aware Tool Selection
コンテキストに応じて異なるツールを選択。
- 明確な判断基準
- フォールバック
- 選択理由の透明化

### Pattern 5: Domain-specific Intelligence
ツールアクセス以上の専門知識を付加。
- ロジックにドメイン知識を埋め込み
- アクション前のコンプライアンスチェック
- 監査証跡

---

## 7. テストと反復

### テストの3領域

#### 1. トリガーテスト
```
Should trigger:
- "Help me set up a new ProjectHub workspace"
- "I need to create a project in ProjectHub"

Should NOT trigger:
- "What's the weather?"
- "Help me write Python code"
```

#### 2. 機能テスト
- 正しい出力が生成されるか
- API 呼び出しが成功するか
- エラーハンドリングが機能するか
- エッジケースがカバーされているか

#### 3. パフォーマンス比較
スキルありとなしで比較:
- やりとり回数
- 失敗した API 呼び出し数
- 消費トークン数

### フィードバックに基づく反復

| シグナル | 原因 | 対処 |
|---------|------|------|
| アンダートリガー（発火しない） | description が曖昧 | キーワード・トリガーフレーズを追加 |
| オーバートリガー（関係ない時に発火） | description が広すぎる | ネガティブトリガー追加、スコープ明確化 |
| 命令が守られない | 命令が冗長/埋もれ/曖昧 | 簡潔に、重要事項を先頭に、具体的に |

---

## 8. クイックチェックリスト

### 開発前
- [ ] 2-3個の具体的ユースケースを特定
- [ ] 必要なツール（組み込み or MCP）を特定
- [ ] フォルダ構造を計画

### 開発中
- [ ] フォルダ名が kebab-case
- [ ] SKILL.md が正確な綴り
- [ ] YAML フロントマターに `---` デリミタ
- [ ] name: kebab-case、スペース・大文字なし
- [ ] description に「何を」と「いつ」の両方を含む
- [ ] XML タグ（`<` `>`）なし
- [ ] 命令が明確でアクション可能
- [ ] エラーハンドリング含む
- [ ] 例を提供
- [ ] 参照ファイルを明示

### テスト
- [ ] 明示的なタスクでトリガーされる
- [ ] 言い換えでもトリガーされる
- [ ] 無関係なトピックではトリガーされない
- [ ] 機能テストがパス

---

## 9. Claude Code コマンド形式との対応

本ガイドは Claude.ai の SKILL.md 形式について記述しているが、
Claude Code のスラッシュコマンド（`.claude/commands/*.md`）にも以下の原則が適用される:

| SKILL.md の原則 | Claude Code コマンドでの適用 |
|----------------|---------------------------|
| 具体的な description | コマンドファイル冒頭の説明文 |
| ステップバイステップ命令 | コマンド本文の手順 |
| エラーハンドリング | トラブルシューティングセクション |
| Progressive Disclosure | 詳細基準を `docs/review-*.md` に分離 |
| ユースケース定義 | コマンドの目的・対象を明確化 |

---

## 参考リンク

- Anthropic Skills Documentation
- GitHub: anthropics/skills（公式スキルリポジトリ）
- skill-creator skill（Claude.ai 内蔵）
