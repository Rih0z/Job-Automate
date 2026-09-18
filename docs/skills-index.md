# Skills 索引

[← README.md](../README.md)

このリポジトリをクローンして Claude Code で開くだけで、リポジトリ直下の `.claude/` が自動検出されて使える。全 skill が判定基準として参照する公式ベストプラクティスの構造化データは [anthropic-best-practices.json](../.claude/skills/_shared/anthropic-best-practices.json)（34原則・取得日と再取得条件付き）。

## 主要スラッシュコマンド

| コマンド | Skill本体 | 何をするか |
|---------|-------------|-----------|
| `/review-implementation` | [.claude/skills/review-implementation/SKILL.md](../.claude/skills/review-implementation/SKILL.md) | 実装を5軸（テスト・正確性・マネタイズ・ペルソナ・UX）で100点満点評価 |
| `/review-changes` | [.claude/skills/review-changes/SKILL.md](../.claude/skills/review-changes/SKILL.md) | 直近の変更差分を4軸（実装正確性・テストカバレッジ・テスト品質/戦略・追跡可能性）で100点満点評価。**別エージェントで実行**し客観性を確保 |
| `/review-skill` | [.claude/skills/review-skill/SKILL.md](../.claude/skills/review-skill/SKILL.md) | 作成済みSkillsを構造化データ基準で5軸（構造・トリガー・命令品質・出力設計・実用性）で100点満点評価 |
| `/debate-proposal` | [.claude/skills/debate-proposal/SKILL.md](../.claude/skills/debate-proposal/SKILL.md) | 新規実装案・設計提案・方針転換案を採用前に、推進側/反対側/OSS前例調査+中立裁定の3本の独立エージェントに同じ一次資料だけを渡して議論させ、既存実装との重複・前提の事実検証・OSS前例・5観点で採否を裁定。**別エージェントで実行**し実装は行わない |

`/review-changes` は実装セッションとは別のエージェントを自動起動してレビューする（詳細は [agents.md](../agents.md)）。すべて `disable-model-invocation: true` のため自動発動せず、スラッシュコマンドとしてのみ起動する。

他のプロジェクトでもこの3件だけ使いたい場合:
```bash
mkdir -p ~/.claude/skills
cp -r .claude/skills/review-changes .claude/skills/review-implementation .claude/skills/review-skill ~/.claude/skills/
```
詳細な評価基準（`workflows/software-development/review-*.md` / `skills-building-guide.md`）も一緒にコピーすると、埋め込みの簡易基準ではなく詳細なチェックリストを使って評価する。

## 自動発動するSkills（ドメイン別）

`workflows/` 配下のプロンプトは全て `.claude/skills/<name>/SKILL.md` として skill 化されている。該当する話題を話した時に自動発動するか、`/<name>` で直接呼び出せる。個別の説明・トリガー文言は各 SKILL.md の frontmatter `description` に集約されており、本表では重複記載しない。

| ドメイン | 例 |
|---|---|
| 汎用ガバナンス | `agent-harness-bootstrap`（CLAUDE.md/rules/hooks 一式生成。由来台帳 `provenance.json` と構造化データ `_shared/anthropic-best-practices.json` を参照）・`harness-setup-review`（setup 後の抜け・混入検査）・`harness-compliance-audit`（直近変更分の機械検査 + 別エージェント判定）・`review-oss-contribution`・`skills-audit`・`skill-authoring-guide`・`stop-ai-slop-jp`（[iKora128/stop-ai-slop-jp](https://github.com/iKora128/stop-ai-slop-jp) 着想・MIT・vendoring）・`review-gate`（工程別レビューゲート）・`single-session-tdd`・`repo-hygiene-patrol`・`blind-eval-harness`・`issue-lifecycle-tracking`・`workflow-coverage-and-structure`（README/workflows 追記漏れの機械検査。本リポジトリ固有・移植不可） |
| business-planning | `business-idea` / `business-proposal` / `generic-proposal` / `it-proposal` / `specification` / `ai-automation` とそれぞれの `review-*`・`multi-tenant-template-injector` |
| content-creation | `creative-text-art` / `slides-pro` / `review-blog` / `review-slides` / `thumbnail-generation` / `review-thumbnail` |
| ops-management | `year-end-adjustment-csv` / `server-automation` / `server-init` / `server-windows-standard` / `review-ops` |
| research-intelligence | `craft-beer-news-research` / `it-tech-news-research` / `general-news-research` / `investment-portfolio-analysis` / `seo-keyword-article-planner` / `blog-seo-growth-planner` / `research-deliverable-review` / `source-verification-scan` / `staged-investigation-workflow` |
| software-development (design/mcp/その他) | `ui-design-guidelines` / `ibm-carbon-design-system` / `avoid-ai-generated-design-look` / `customer-persona-design` / `review-persona-analysis` / `playwright-mcp-e2e-testing` / `mcp-server-setup` / `model-cost-optimization-routing` / `three-agent-tdd-workflow`（単一セッション版は `single-session-tdd`） |

上表は用途別の索引であり、移植時の採否を表すものではない。「汎用ガバナンス」のうち `agent-harness-bootstrap` / `harness-setup-review` / `harness-compliance-audit` / `skills-audit` / `skill-authoring-guide` / `review-gate` は公式由来として既定で移植される。それ以外（TDD運用の各流儀・`repo-hygiene-patrol` 等の著者嗜好、`workflow-coverage-and-structure` のような本リポジトリ固有のもの、および business-planning / content-creation / research-intelligence / ops-management と software-development 内デザイン系の業務ドメインプロンプト）は既定では移植されない**サンプル**である。このリポジトリの実運用から生まれた実例として同梱しているだけで、[provenance.json](../.claude/skills/agent-harness-bootstrap/provenance.json) の由来台帳に従いユーザーが選んだものだけ採用される。汎用的な harness 基盤だけが目的なら無視してよい。

既知の公式ベストプラクティス逸脱・改善バックログと再監査手順は [.claude/skills/_shared/compliance-roadmap.md](../.claude/skills/_shared/compliance-roadmap.md) を参照。

## workflows/ ごとの推奨AIサービス

| カテゴリ | 推奨サービス |
|---|---|
| 全般（`workflows/content-creation` / `business-planning` / `ops-management`） | [Claude](https://claude.ai) / [ChatGPT](https://chatgpt.com) / [Gemini](https://gemini.google.com) |
| リサーチ・ニュース収集（`workflows/research-intelligence`） | [Perplexity](https://www.perplexity.ai) / [Grok](https://grok.com) / [Gemini](https://gemini.google.com) |
| 開発（`workflows/software-development`） | [Claude Code](https://docs.anthropic.com/ja/docs/claude-code/overview) / [Cursor](https://www.cursor.com) / [Cline](https://cline.bot) |

各 workflow の個別プロンプト一覧・使用順序・レビュー基準は [workflows/README.md](../workflows/README.md) から各 `workflows/<name>/README.md` を参照。
