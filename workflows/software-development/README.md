# workflows/software-development/ — 開発プロンプト集

業務ワークフロー「ソフトウェア開発」のハーネス。Claude Code 向け harness 構築ノウハウ・3エージェント開発システム・デザインシステム・コーディング規約・MCPツール・実装/Skills品質レビューをまとめる。

> **コーディングを含むすべての開発は [three-agent/](three-agent/) から始めてください。**

## Claude Code harness 構築（`.claude/skills/`）

実際に自動検出される Skills はリポジトリ直下 [`.claude/skills/`](../../.claude/skills/) に配置している（本ワークフロー配下ではない。Claude Code は `<repo>/.claude/skills/` のみを自動検出するため）。

| Skill | 何をするか |
|---|---|
| [agent-harness-bootstrap](../../.claude/skills/agent-harness-bootstrap/SKILL.md) | 任意のプロジェクトに Anthropic ベストプラクティス準拠の `CLAUDE.md` + `.claude/rules/` + hooks 一式を生成・剪定する |
| [review-oss-contribution](../../.claude/skills/review-oss-contribution/SKILL.md) | OSS貢献候補を独自性・先行技術・実現可能性・戦略の4基準で審査しGO/HOLD/REJECTを判定する |
| [skills-audit](../../.claude/skills/skills-audit/SKILL.md) | リポジトリ内の全Skillsを一括監査しGOOD/MIGRATE/IMPROVE/SPLITを判定する |
| [stop-ai-slop-jp](../../.claude/skills/stop-ai-slop-jp/SKILL.md) | AIで書いた日本語を人間の文章に戻す（[iKora128/stop-ai-slop-jp](https://github.com/iKora128/stop-ai-slop-jp) 着想・MIT・Daichi Nagashima 作、vendoring） |

## three-agent/ — 3エージェント開発システム

3つのAIセッションを使い分け、TDDで品質を担保しながら開発する。

| ファイル | 役割 | 用途 |
|---|---|---|
| [three-agent/README.md](three-agent/README.md) | — | システム全体の使い方・ロール説明 |
| [three-agent/leader.md](three-agent/leader.md) | リーダー（ターミナル1） | ゴール設定・テスト方針・タスク分解・次イテレーション指示 |
| [three-agent/executor.md](three-agent/executor.md) | 実行（ターミナル2） | テスト→実装→リファクタのTDDサイクルを回す |
| [three-agent/reviewer.md](three-agent/reviewer.md) | レビュー（ターミナル3） | テストと実装の品質評価・改善指示 |

## design/ — デザインシステム（IBM Carbon準拠）

ペルソナ分析からデザイン方針を導出するフレームワーク。

| ファイル | レビュー | 用途 |
|---|---|---|
| [design/persona.md](design/persona.md) | [design/review-persona.md](design/review-persona.md) | 顧客の年齢・ニーズ・フラストレーションを分析→カラー・フォント・UXパターンを決定（最初に実施） |
| [design/design-system.md](design/design-system.md) | — | IBM Carbon準拠のデザイントークン・コンポーネント仕様 |
| [design/design-guidelines.md](design/design-guidelines.md) | — | 絵文字禁止・ダークモード・レスポンシブ・品質チェックリスト |
| [design/design-research.md](design/design-research.md) | — | 優れたUX原則・AIっぽくないデザイン手法のリファレンス |

## rules/ — コーディング規約

| ファイル | 用途 |
|---|---|
| [rules/coding-principles.md](rules/coding-principles.md) | AIコーディング時に守るべき規則（過剰実装禁止・セキュリティ・テスト方針など） |

## mcp/ — MCPツール

| ファイル | 用途 |
|---|---|
| [mcp/playwright.md](mcp/playwright.md) | Playwright MCPのセットアップ手順とE2Eテスト実行方法 |
| [mcp/serena.md](mcp/serena.md) | Serena MCP（コードベース分析）のセットアップ手順 |
| [mcp/windows-setup.md](mcp/windows-setup.md) | Windows環境でのMCP設定手順 |

## 実装・Skills品質レビュー

| プロンプト/コマンド | 用途 |
|---|---|
| [review-implementation.md](review-implementation.md) | 実装コードの総合レビュー（5軸100点満点）。ルート `/review-implementation` コマンドの評価基準本体 |
| [review-changes.md](review-changes.md) | 変更差分のレビュー（4軸100点満点、別エージェント実行）。ルート `/review-changes` コマンドの評価基準本体 |
| [review-skill.md](review-skill.md) | Skills品質レビュー（5軸100点満点）。ルート `/review-skill` コマンドの評価基準本体 |
| [skills-building-guide.md](skills-building-guide.md) | Anthropic公式Skills作成マニュアル（`review-skill.md` の評価根拠） |

## その他

| ファイル | 用途 |
|---|---|
| [cost-optimization.md](cost-optimization.md) | モデル選択・委任のコスト最適化方針 |

## archive/old-prompts/

試行錯誤の過程で生まれた旧世代プロンプト群は [archive/old-prompts/](../../archive/old-prompts/) に退避してある（現行ワークフローでは非使用・履歴参照専用）。

---

[← ワークフロー一覧に戻る](../README.md) ／ エージェント分離アーキテクチャは [agents.md](../../agents.md) を参照
