---
name: skill-authoring-guide
description: "Reference manual (based on Anthropic's official 'The Complete Guide to Building Skills for Claude') for designing, structuring, and testing SKILL.md files and Claude Code slash commands: folder structure, YAML frontmatter rules, progressive disclosure, instruction-quality patterns, and a pre-publish checklist. Use when the user asks to 'Skillを作りたい', 'SKILL.mdの書き方を教えて', 'スキル作成のベストプラクティスを確認して', or is the evaluation basis for /review-skill."
metadata:
  provenance: official-derived
---

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
- **正しい**: `allowed-tools` に書き込み系ツールを含め、fork内で直接ファイルへ書く（会話コンテキストが分離されていても、書き込みは即座に反映される）

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

### 決定的な強制 vs 確率的な依頼

「絶対に守ってほしい」規律ほど、**モデルへの指示文だけ（確率的な依頼）に頼らず、スクリプト・バリデーション・スキーマ等の構造で強制（決定的な強制）できないか**を先に検討する。指示文は従わない実行が起こりうるが、プログラム的な検証・ゲート・スキーマは物理的に迂回できない。

| 迂回されうる（確率的） | 迂回されない（決定的） |
|---|---|
| 「JSON形式で出力してください」という指示文のみ | 出力スキーマ検証 + 不一致時は reject して再生成させる |
| few-shot 例で望ましい形式を示すだけ | 後続処理側で構造チェック（フィールド欠落・型不一致を機械的に検出） |
| コメントで「このフィールドは変更しないで」と書く | 該当フィールドを書き込み不能にする / 変更検出スクリプトを別途走らせる |

「より丁寧・より慎重に見える指示文」を追加するだけでは、結局モデル任せの依頼に留まる場合がある。本当に保証したい規律は、`## 7. テストと反復` の検証ゲートやスクリプト実行ステップに落とし込む。

### Few-shot 例（Examples セクション）の設計

- **個数は 2〜4 個を目安にする**。それ以上増やしても効果は逓減しやすく、個数より**シナリオの多様性**（似た例の量産でなく異なるケースの網羅）の方が重要
- **全ての例で共通フィールドが常に値で埋まっている状態を避ける**。欠損・null・不明値を一度も見せないと、モデルは「常に全項目埋まっているべき」という誤ったパターンを学習し、実際に値が無い場面でそれらしい値を捏造しやすくなる（ハルシネーション誘発）。少なくとも1例は欠損値を含むケースを用意する
- 複数言語・複数フォーマットにまたがる skill では、例を1つのパターンに集中させず**種別ごとに最低1例ずつ配分**し、かつ全例で同じ出力構造を示す（フォーマットの一貫性と網羅性を両立させる）

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

### Pattern 6: Router + Content-free Skills(2026-09-01 追加)
ナレッジベースが大きい場合、1つの巨大なSKILL.mdに全知識を詰めない。ルーター役のskillは「どのトピックがどの参照ファイル/セクションにあるか」の索引のみを持ち、本文コンテンツは持たない。個別トピックのskill(または`references/`配下のファイル)は本文コンテンツのみを持ち、ルーティングロジックを持たない。効果: ①関連トピックだけがcontextに載る(token節約) ②本文更新時にルーターを触らずに済む(疎結合)。副作用: ルーター経由の間接呼び出しはprompt injectionの経路になりうるため、ルーターが外部入力(取得したWebコンテンツ等)をそのまま次のskill呼び出し先の判断に使わないよう明示的にガードする。

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

### 保守(2026-09-01 追加)
- [ ] `metadata.version` 等のバージョン表記を持つskillは、内容(振る舞い)を変えない編集(typo修正・言い回し調整)でバージョンを自動的に繰り上げない。繰り上げは振る舞いが変わる変更時のみ、変更前後の差分をchangelogに残す。

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

---

## 出典・関連

原文: `workflows/software-development/skills-building-guide.md`。`.claude/commands/review-skill.md`（`/review-skill`）の評価基準本体としても参照される。本リポジトリの `.claude/skills/skills-audit/SKILL.md` と役割が近接するため、重複が疑われる場合はメンテナンスIssueで整理すること。
