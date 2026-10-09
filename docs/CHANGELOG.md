# CHANGELOG

[← README.md](../README.md)

harness（`CLAUDE.md` / `.claude/rules/` / `.claude/skills/`）への変更を、日付付きの1行で記録する。本文中に「(2026-09-XX 追加)」のような日付注記を散在させる代わりに、変更履歴はここに一元化する。この運用自体は Anthropic 公式ベストプラクティスに直接の根拠を持たない、著者の運用嗜好（`changelog-practice`、`provenance.json` 登録）。

Anthropic 公式ベストプラクティスへの逸脱・改善バックログ（公式原則ごとの採用状況と CR-01〜）は構造化データ → [.claude/skills/_shared/compliance-status.json](../.claude/skills/_shared/compliance-status.json)、再監査手順 → [.claude/skills/_shared/compliance-roadmap.md](../.claude/skills/_shared/compliance-roadmap.md)。

## 2026-10

- **10-07**: `stop-ai-slop-jp` に、採点基準と採点対象（ディレクトリ・生成物）の条件が矛盾することがあり、その場合は矛盾しない設計に見直す、という原則を追加した（`criteria/scoring.json` の `conflict_policy`、SKILL.md の節、CLAUDE.md の追加ルール）。
- **10-06**: `anthropic-best-practices.json` を公式 docs（best-practices・skills・hooks・hooks-guide・memory）の現行版で再取得し、取得日を 2026-10-06 に進めた。9 principle を更新した（CLAUDE.md の行数の目安 200 行未満、Stop hook の連続 block の上限、PreToolUse の permissionDecision、skills の frontmatter 項目など）。principle の数は 34 のまま
- **10-04**: `stop-ai-slop-jp` に「採点範囲」節を追加（文体だけを採点し、事実の実測・突合は別エージェントのレビューへ分離。気づいた食い違いは範囲外メモで返す）。`issue-lifecycle-tracking` に、close 時の検証記録を条件で書き、件数・列挙・コマンド出力を記録ファイルへ置く指針を追加。

## 2026-09

- **09-25**: 顧客対応チャットボット運用のワークフロー `workflows/customer-support/` と skill `chatbot-operation-design` / `review-chatbot-operation-design` を追加（`domain-prompt`）。有人への引き継ぎ（お客様のフラストレーション・感情悪化の検知、「人と話したい」、解決できない試行の繰り返し、権限外の依頼）、引き継ぎ手順、ガードレール、成功基準と評価、運用監視など 43 観点を、Anthropic 公式資料の出典つき JSON（由来: official / official-derived / practice）で保持。
- **09-25**: 公式 docs（best-practices / memory / skills / sub-agents / hooks / settings / permissions / skill authoring）の現行版と再突合し、公式原則キャッシュを 34 → 85 件に拡充（観点はすべて JSON の構造化データで保持）。原則ごとの採用状況・CR を `compliance-status.json` に移設し、整合検査 `check_compliance_status.py` を追加。Stop ゲートが一度上限に達すると以後効かなくなる不具合を修正。rules の load 仕様（paths のみ読まれる・paths 無しは起動時に自動 load・@import 不要）、CLAUDE.md の 200 行目標、AGENTS.md の取り込み、hooks のセキュリティ・通知・timeout、permissions の deny、subagent によるツール制限（`.claude/agents/readonly-reviewer.md`）、skill authoring（評価先行・目次・MCP 完全修飾名 等）を生成器・検査・ガイドに反映。`harness_check.sh` に R01 改訂・A02/A03/S12/H03/H04 を追加し、check と原則の対応を `reference/checks.json` に構造化。評価シナリオ作成（CR-27）・モデル別試験（CR-28）・日付注記の点検（CR-29）は backlog。
- **09-17**: README.md を `docs/` へ分割し、最小限のポインタに縮小。変更履歴の一元化（`changelog-practice`）を制定し、移植先プロジェクトにも `CHANGELOG.md` として伝播するようにした。
- **09-17**: `debate-proposal` skill を追加（新規提案を推進側/反対側/OSS前例調査+中立裁定の3エージェントで議論・裁定。`author-preference`、`provenance.json` 登録、`agents.md` / `docs/skills-index.md` に追記）。
- **09-16**: `harness_check.sh` の `fm_get()` に残っていた BSD sed 非互換（macOS で全 skills が誤って FAIL 判定される不具合）を修正。README.md に AI 文体レビュー（`stop-ai-slop-jp`）を適用し、業務ドメイン系 skills がサンプルである旨を明記。
- **09-15**: `fm_get()` を YAML block scalar（`description: |` 等）対応に修正。
- **09-11〜09-14**: `harness-setup-review` / `harness-compliance-audit` を追加。マルチエージェント設計原則（クラッシュ耐性 manifest・メタデータ保持・ツールスコープ限定）を移植先へ伝播する `agent-design.md` の仕組みを追加。移植先の継続的な実質再監査ロードマップ（`harness-compliance-roadmap-seed`）を追加。`.claude/commands/*` の3コマンドを `.claude/skills/*/SKILL.md` 形式へ移行。discovery-log の JSON 構造化・レビュー結果永続化機構（review-record）を追加。
- **09-04**: 由来台帳（`provenance.json`）による取捨選択の仕組みを追加。セットアップ依頼への対応の発火条件を拡張。数値目標の単一 SoT 化条文を `author-preference`（recommend）へ再分類。サムネイル生成・レビュー skill（`thumbnail-generation` / `review-thumbnail`）を追加。
- **09-02**: `workflow-coverage-and-structure` による README/workflows 追記漏れの機械検査を追加。
- **09-01**: 別プロジェクトへのセットアップ対応（`.setup-automate/` clone 方式・由来別選択ルール）を制定。数値目標の単一 SoT 化の条文を追加。

## 2026-08

- **08-31**: 根拠明記の推奨（研究・提案・報告成果物の事実主張への出典近接記載、advisory）を追加。
