---
name: repo-hygiene-patrol
description: "プロジェクトのファイル構造衛生を自動検査する。バージョン番号付きファイル(_v2/_old/_backup等)、OS由来のゴミファイル、肥大化ファイル、.gitignore漏れ、ルート直下の散らかりを検出する。汎用skillのため、対象プロジェクトのディレクトリ規約は実行時に確認する。Trigger phrases: 'ファイル構造をチェックして', 'リポジトリの衛生チェック', 'repo-hygiene-patrol', '散らかりを検出して'."
disable-model-invocation: true
allowed-tools: Read Grep Glob Bash
metadata:
  provenance: author-preference
---

# リポジトリ衛生パトロール

## 概要

プロジェクトのファイル構造が乱れていないかを検査する。個別プロジェクトの配置規約(ディレクトリ構成)は事前に把握できないため、規約に依存しない一般的な散らかりパターンのみを機械的に検出する。特定プロジェクトの規約(root allowlist等)に照らした検査が必要な場合は、そのプロジェクト固有の validator を先に確認しそちらを優先する。

## 検査項目

観点定義 (SoT) = `.claude/skills/repo-hygiene-patrol/criteria/checks.json`。7項目それぞれの検査コマンド・severity判定ルールを保持する(本文へ prose 重複記載しない)。各 `id` を上から順に実行し、ヒットした場合は対応する `severity`(HIGH/MEDIUM/WARN)で報告する。`root_clutter` と `numeric_target_drift` は機械コマンドだけで判定できない部分を含むため `rationale`/`severity_rules` を Read してから判断する。

## 出力フォーマット

```
=== Repo Hygiene Patrol ===
Date: YYYY-MM-DD

[HIGH] (件数)
- ...

[MEDIUM] (件数)
- ...

[WARN] (件数)
- ...

[OK] 問題なし (件数)

Total: X issues found
```

## 対応アクション

- **HIGH**: 即時修正を提案(バージョン番号付きファイルは Git 履歴への統合、OS由来ゴミは削除+`.gitignore`追記)
- **MEDIUM**: 報告後にユーザー確認を取って削除/移動
- **WARN**: 報告のみ(ユーザー判断)
- **OK**: 報告不要(問題なしカテゴリはサマリーのみ)

HIGH または MEDIUM の問題が検出された場合、修正を実施してよいかユーザーに確認すること。ファイルの削除・移動は必ずユーザー確認後に行う(本 skill 自身は非破壊のレポート生成に徹する)。

---

*作成: 2026-08-31*
