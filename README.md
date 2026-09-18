# Job-Automate

**このリポジトリの本質は「他のプロジェクトの `CLAUDE.md` / rules / skills を、Anthropic 公式ベストプラクティスに準拠した状態へセットアップできること」である。** 対象プロジェクト直下に clone し、Claude Code から「セットアップして」と伝えるだけで、公式基準への準拠を別エージェントが検証しながら CLAUDE.md と harness 一式を生成する（[docs/setup-guide.md](docs/setup-guide.md)）。

副次的に、このリポジトリ自身も AI活用業務自動化のためのプロンプトライブラリとして機能する（[workflows/README.md](workflows/README.md)）。

公式ベストプラクティスは取得日・再取得条件付きの構造化データ [anthropic-best-practices.json](.claude/skills/_shared/anthropic-best-practices.json) として保持し、著者独自の運用嗜好は由来台帳 [provenance.json](.claude/skills/agent-harness-bootstrap/provenance.json) で公式由来と分けて管理する。別プロジェクトへは、公式由来をデフォルトで入れ、著者の運用嗜好はあなたが選んだものだけを入れる。

## ディレクトリ構成

```
Job-Automate/
├── .claude/skills/    Claude Code Skills（自動検出）
├── workflows/         業務ワークフロー単位のハーネス（詳細: workflows/README.md）
├── docs/              このリポジトリ自身のドキュメント（下表）
├── archive/           現行ワークフロー非採用の旧プロンプト（履歴参照用）
├── agents.md          エージェント分離アーキテクチャ
└── CLAUDE.md          Claude Code 向けリファレンスマニュアル
```

## ドキュメント

| ファイル | 何が書いてあるか |
|---|---|
| [docs/setup-guide.md](docs/setup-guide.md) | 別プロジェクトへの移植手順・品質の保証範囲・検証と再同期 |
| [docs/skills-index.md](docs/skills-index.md) | 同梱スラッシュコマンド／Skills の一覧、移植時にサンプル扱いになるものの区別 |
| [docs/design-philosophy.md](docs/design-philosophy.md) | 作成/レビュープロンプトの設計思想、ハーネス自体の組み立て方 |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | 変更履歴 |
| [workflows/README.md](workflows/README.md) | 業務ワークフロー（プロンプト本体）の一覧・追加手順 |
| [CLAUDE.md](CLAUDE.md) | Claude Code 向けリファレンスマニュアル。アップロードポリシー・応答ルールもここ |
| [agents.md](agents.md) | エージェント分離アーキテクチャ（レビューの客観性確保） |

## ライセンス

[MIT License](LICENSE)。ただし `.claude/skills/stop-ai-slop-jp/` は第三者OSSのvendoringであり、同ディレクトリ内は同梱の独自MITライセンス・著作権表記（[LICENSE](.claude/skills/stop-ai-slop-jp/LICENSE)）が適用される。

## 運営者

[Koki Riho（Rih0z）](https://github.com/Rih0z) — GitHub / Twitter: [@rihobeer2](https://x.com/rihobeer2)
