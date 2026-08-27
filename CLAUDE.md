# Job-Automate — Claude Code リファレンス

このリポジトリはAI活用業務自動化のためのプロンプトライブラリです。
Claude Code でプロンプトを開発・改善するときのガイドです。

プロンプトは成果物の種類ではなく**業務ワークフロー単位**で `workflows/<name>/` に束ねる（ハーネスの考え方は [workflows/README.md](workflows/README.md)）。Claude Code が自動検出する実行可能な Skills/Commands はリポジトリ直下 `.claude/` に置く。

---

## アップロードポリシー（公開リポジトリ）

このリポジトリは公開 GitHub リポジトリである。**汎用的に再利用できるプロンプト・スキルのみ**をアップロードし、**特定の企業名・製品名・顧客名・社内プロジェクト名など、特定の企業やプロジェクトに紐づく情報を含むものはアップロードしない**。

- 他プロジェクト由来の設計パターンを本リポジトリに取り込む場合、そのプロジェクト固有の名称・識別子・条文番号・実装詳細を引用せず、一般化した設計原則として書き直す
- 既存ファイルを更新する際も、意図せず固有名詞が混入していないか確認する（コミット前に企業名・製品名で grep する等）
- 該当する社内知見・非公開プロジェクトの情報が必要な場合は、このリポジトリでなく非公開のリポジトリ/ドキュメントで管理する

---

## 応答ルール

作業完了を報告する際は、編集・作成した全ファイルの完全パスを応答に明記する。

バグ修正時: エラーメッセージが修正箇所を明確に示している単純な修正はそのまま直接修正する。依存関係や他ファイルとの整合確認が必要な修正は、着手前にその旨を明示し、計画とレビューが必要であることを示す。

---

## レビュースキル一覧

### プロジェクトスキル（このリポジトリをクローンすれば誰でも使える）

> `.claude/commands/` に置かれており、このリポジトリを Claude Code で開けば誰でも使える。
> git で共有されるため、チーム全員が同じスキルを使える。

| コマンド | 用途 | 評価軸 |
|---------|------|--------|
| `/review-implementation` | **実装コードの総合レビュー** | テスト品質・処理の正確性・マネタイズ整合性・ペルソナ適合・UX（5軸・100点満点） |
| `/review-changes` | **変更差分のテスト・実装レビュー（エージェント分離）** | 実装正確性・テストカバレッジ・テスト品質/戦略・追跡可能性（4軸・100点満点） |
| `/review-skill` | **Skills品質レビュー** | 構造・トリガー設計・命令品質・出力設計・実用性（5軸・100点満点） |

### 自動発動するSkills（`.claude/skills/`）

このリポジトリの `workflows/` 配下のプロンプトは全て `.claude/skills/<name>/SKILL.md` として skill 化されている。このリポジトリを Claude Code で開けば、該当する話題を話した時に自動発動するか、`/<name>` で直接呼び出せる（一覧は `.claude/skills/` を `ls` するか `/skills` コマンドで確認。個別の説明・トリガー文言は各 SKILL.md の frontmatter `description` に集約されており、本表では重複記載しない）。

| ドメイン | 例 |
|---|---|
| 汎用ガバナンス | `agent-harness-bootstrap`（CLAUDE.md/rules/hooks 一式生成）・`review-oss-contribution`・`skills-audit`・`skill-authoring-guide`・`stop-ai-slop-jp`（[iKora128/stop-ai-slop-jp](https://github.com/iKora128/stop-ai-slop-jp) 着想・MIT・vendoring） |
| business-planning | `business-idea` / `business-proposal` / `generic-proposal` / `it-proposal` / `specification` / `ai-automation` とそれぞれの `review-*` |
| content-creation | `creative-text-art` / `slides-pro` / `review-blog` / `review-slides` |
| ops-management | `year-end-adjustment-csv` / `server-automation` / `server-init` / `server-windows-standard` / `review-ops` |
| research-intelligence | `craft-beer-news-research` / `it-tech-news-research` / `general-news-research` / `investment-portfolio-analysis` / `seo-keyword-article-planner` / `blog-seo-growth-planner` / `research-deliverable-review` |
| software-development (design/mcp/その他) | `ui-design-guidelines` / `ibm-carbon-design-system` / `avoid-ai-generated-design-look` / `customer-persona-design` / `review-persona-analysis` / `playwright-mcp-e2e-testing` / `mcp-server-setup` / `model-cost-optimization-routing` / `three-agent-tdd-workflow` |

### グローバルスキル（どのプロジェクトでも使える・任意セットアップ）

> `~/.claude/commands/` にコピーすると、他のプロジェクトでも使える。
> `.claude/commands/` と同じ内容。個人環境に展開したい場合に使う。

```bash
# このリポジトリのスキルを個人のグローバルスキルにコピーする
mkdir -p ~/.claude/commands
cp .claude/commands/*.md ~/.claude/commands/
```

**使い方:**
```
（開発中のプロジェクトで）
/review-implementation          ← プロジェクト全体の総合レビュー
/review-changes                 ← 直近の変更差分をテスト・実装観点でレビュー
/review-changes path/to/file    ← 特定ファイルの変更をレビュー
```
→ `/review-implementation`: プロジェクトのコード・テスト・デザイン定義・ペルソナ情報を自動で収集して評価する。
→ `/review-changes`: **別エージェントを自動起動**し、テスト基盤を自動検出して変更に対する実装正確性・テスト網羅性を評価する。実装コンテキストを遮断して客観性を確保する。

**詳細な評価基準:**
- `workflows/software-development/review-implementation.md` — `/review-implementation` の詳細基準
- `workflows/software-development/review-changes.md` — `/review-changes` の詳細基準

**エージェント分離アーキテクチャ:** `agents.md` を参照

---

### 手動で使うレビュープロンプト（Claude Code 外・貼り付けて使う場合のフォールバック）

> 以下は全て `.claude/skills/` 配下に対応する skill があるため、Claude Code 環境では上表の skill を使う方が推奨（自動発動 + エージェント分離が組込済み）。Claude.ai 等 Claude Code 以外の環境で使う場合のみ、元プロンプトを直接貼り付ける。

| プロンプトファイル | 用途 | 評価軸 |
|----------------|------|--------|
| `workflows/software-development/review-implementation.md` | 実装レビューの詳細基準（`/review-implementation` の参照元） | テスト・正確性・マネタイズ・ペルソナ・UX |
| `workflows/software-development/review-changes.md` | 変更レビューの詳細基準（`/review-changes` の参照元） | 実装正確性・テストカバレッジ・テスト品質/戦略・追跡可能性 |
| `workflows/software-development/review-skill.md` | Skills品質レビューの詳細基準（`/review-skill` の参照元） | 構造・トリガー設計・命令品質・出力設計・実用性 |
| `workflows/software-development/skills-building-guide.md` | Anthropic公式Skills作成マニュアル（`/review-skill` の評価根拠） | — |
| `workflows/business-planning/review-business-idea.md` | ビジネスアイデアのレビュー | 独自性・競合克服戦略・市場性・実現可能性・ペルソナ明確性・エンゲージメント/リテンション設計・展開計画（6軸・100点満点） |
| `workflows/business-planning/review-proposal.md` | 提案書・企画書のレビュー | 構成・市場分析/競合克服戦略・ペルソナ適合性・根拠・エンゲージメント/リテンション設計・説得力（6軸・100点満点） |
| `workflows/business-planning/review-specification.md` | 技術仕様書のレビュー | 要件網羅性・アーキテクチャ・API/データ設計・テスト戦略・実装/運用計画（5軸・100点満点） |
| `workflows/research-intelligence/review-research.md` | リサーチ・ニュース収集・SEO分析のレビュー | 正確性・網羅性・分析深度・構成・実用性（5軸・100点満点） |
| `workflows/business-planning/ideas/review-ai-automation.md` | AI自動化ビジネスモデルのレビュー | 実現可能性・収益性・自動化・競合モート・エンゲージメント・リスク（6軸・100点満点） |
| `workflows/software-development/design/review-persona.md` | ペルソナ分析のレビュー | 具体性・課題深掘り・デザイン整合性・セグメント分類・検証可能性（5軸・100点満点） |
| `workflows/ops-management/review-ops.md` | 運用スクリプト・サーバー設定のレビュー | セキュリティ・冪等性・エラーハンドリング・運用性・パフォーマンス（5軸・100点満点） |
| `workflows/content-creation/review-blog.md` | ブログ記事（note / Qiita / Zenn / Medium / 企業ブログ等）のレビュー | わかりやすさ・独自性・有益性・事実正確性・事実所感分離・冒頭サマリ・冗長性一貫性・読みやすさ文体・コンプライアンス・第三者配慮・技術評価妥当性（11軸・110点満点／100点換算で判定） |
| `workflows/software-development/three-agent/reviewer.md` | TDDコードレビュー（three-agentシステム専用） | TDD証跡・カバレッジ・実装整合性・ドキュメント |

**手動での使い方:**
```
（Claude Code または Claude.ai で）
workflows/software-development/review-implementation.md の内容 + 対象コードを貼り付けて「レビューしてください」と依頼
```

---

## `/review-implementation` を使う前に準備しておくと精度が上がるもの

| 準備 | ファイル例 | なければ |
|------|-----------|---------|
| ペルソナ定義 | `workflows/software-development/design/persona.md` | 推定ユーザーを仮定して評価（スコアに注記あり） |
| 収益モデル | README に記載 | マネタイズ観点をN/Aとして除外し80点満点に換算 |
| テスト戦略 | `jest.config.*` 等 | テストファイルを探して判断 |
| デザインガイドライン | `workflows/software-development/design/design-guidelines.md` | 一般的なUXベストプラクティスで評価 |

---

## 新しいワークフロー・スキルを追加するルール

**追加前チェック（共通）**: 既存の `workflows/` 一覧・`.claude/commands/` 一覧を検索し、目的が重複する既存プロンプト/スキルがないか確認する（重複なら新設せず既存を拡張する）。作成後は別エージェント（`/review-skill` 等）によるレビューを最低 1 回受け、指摘が収束してからマージする。

### 業務ワークフローとして追加（プロンプトの本体）

1. `workflows/<workflow-name>/` を作成する
2. 対応する作成プロンプト（`<対象>.md`）とレビュープロンプト（`review-<対象>.md`）をペアで管理する
3. `workflows/<workflow-name>/README.md` に目的・使用順序・関連skills/commandsを書く
4. `workflows/README.md` の一覧表と `README.md` のテーブルに追記する

### Claude Code プロジェクトスキルとして追加（推奨 — git 共有される）

1. `.claude/commands/[コマンド名].md` を作成する
2. コマンドを自己完結にする（他ワークフローのパスをハードコードしない）
3. このファイル（`CLAUDE.md`）のプロジェクトスキルテーブルに追記する
4. 詳細な評価基準は該当ワークフローの `review-[対象].md` に分離して記述する
5. エージェント分離が必要な場合は `agents.md` のエージェント一覧にも追記する
6. 他プロジェクトでも使いたい場合は `~/.claude/commands/` にもコピーする

---

## プロジェクト構成

トップレベルは `CLAUDE.md` / `README.md` / `agents.md` / `.claude/`（commands・skills）/ `workflows/`（業務ワークフロー単位のハーネス）/ `archive/`（旧プロンプト）。ワークフローごとの内訳・各ファイルの所在は [workflows/README.md](workflows/README.md) と [README.md](README.md) を参照（このファイルでは重複記載しない）。
