# CHANGELOG

[← README.md](../README.md)

harness（`CLAUDE.md` / `.claude/rules/` / `.claude/skills/`）への変更を、日付付きの1行で記録する。本文中に「(2026-09-XX 追加)」のような日付注記を散在させる代わりに、変更履歴はここに一元化する。この運用自体は Anthropic 公式ベストプラクティスに直接の根拠を持たない、著者の運用嗜好（`changelog-practice`、`provenance.json` 登録）。

Anthropic 公式ベストプラクティスへの逸脱・改善バックログの追跡は別ファイル → [.claude/skills/_shared/compliance-roadmap.md](../.claude/skills/_shared/compliance-roadmap.md)（CR-01〜）。

## 2026-09

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
