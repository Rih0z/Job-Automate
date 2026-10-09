# Job-Automate — Anthropic 公式ベストプラクティス準拠ロードマップ

> Job-Automate 自身（このリポジトリ）の公式ベストプラクティス逸脱・改善バックログを追跡する living document。`.claude/skills/_shared/anthropic-best-practices.json`（公式原則。2026-09-25 時点 85 件）を判定基準の SoT とする。**原則ごとの採用状況・findings（CR-xx）・監査ログは構造化データ `.claude/skills/_shared/compliance-status.json` が SoT**（2026-09-25 に本ファイルの表から移設。本ファイルには手順だけを置き、表を重複して持たない）。ported プロジェクトはこのファイルの中身を持ち込まず、自分自身の監査を実行して自分の roadmap を作る（`provenance.json` の `shared-compliance-roadmap` 要素は `portable: false`）。

## 再監査手順

2 段階に分ける（毎回フル判定にすると one-subagent-per-file の fan-out コストが常に発生するため）。

- **軽量スイープ（機械検査のみ・頻繁に実行可）**: `.claude/` / `CLAUDE.md` に触れるセッション開始時、または最低月次で実行。
  ```bash
  bash .claude/skills/harness-compliance-audit/scripts/harness_check.sh $(find .claude CLAUDE.md -type f)
  ```
  純粋にパス・内容ベースの決定的チェックなので、全件実行しても軽い。実行日と FAIL/WARN 件数を `compliance-status.json` の `audit_log` に 1 件追加する。
- **フル判定スイープ（別エージェント判定つき・低頻度）**: 四半期に一度、または軽量スイープで新規 FAIL が出た時。`skills-audit`（リポジトリ全体）または `harness-compliance-audit`（特定ファイル指定）を実行し、新規の finding を `compliance-status.json` の `findings` に追加する。公式 docs を再取得して `anthropic-best-practices.json` に原則を足した時は、同じ id を `compliance-status.json` の `principles` にも追加する。

## 状況ファイルの整合検査

`compliance-status.json` を編集したら次を実行する（cache の全 principle と状況の全単射・evidence パスの実在・status / severity の enum・backlog と partial の cr 必須を検査。違反があれば exit 1）:

```bash
python .claude/skills/_shared/scripts/check_compliance_status.py
python .claude/skills/_shared/scripts/test_check_compliance_status.py   # 検査スクリプト自体の回帰テスト
```

## findings の書式と drain

- 1 件 = `findings[]` の 1 オブジェクト: `id`（CR-xx）/ `date` / `finding` / `principles`（関係する principle id）/ `severity`（High・Medium・Low）/ `status`（open・backlog・done・false-positive）/ `note`
- CLAUDE.md の discovery-log を drain する時、Issue 相当として切り出すものはここに新しい CR として追加する
- shell スクリプトの CR を done にする時は、GNU 実装依存（sed / awk）を疑い、可能なら BSD 環境（macOS）でも実行して確認する（CR-13 の教訓）
