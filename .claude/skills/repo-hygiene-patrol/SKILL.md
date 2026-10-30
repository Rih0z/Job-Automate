---
name: repo-hygiene-patrol
description: "プロジェクトのファイル構造衛生を自動検査する。バージョン番号付きファイル(_v2/_old/_backup等)、OS由来のゴミファイル、肥大化ファイル、.gitignore漏れ、ルート直下の散らかりを検出する。汎用skillのため、対象プロジェクトのディレクトリ規約は実行時に確認する。Trigger phrases: 'ファイル構造をチェックして', 'リポジトリの衛生チェック', 'repo-hygiene-patrol', '散らかりを検出して'. 使わない場面: 変更差分のレビュー(review-changes)、skill 定義の品質採点(review-skill)、skill 体系の監査(skills-audit)。"
disable-model-invocation: true
allowed-tools: Read Grep Glob Bash
metadata:
  provenance: author-preference
  version: "1.2.0"
---

# リポジトリ衛生パトロール

## 概要

プロジェクトのファイル構造が乱れていないかを検査する。個別プロジェクトの配置規約(ディレクトリ構成)は事前に把握できないため、規約に依存しない一般的な散らかりパターンのみを機械的に検出する。特定プロジェクトの規約(root allowlist等)に照らした検査が必要な場合は、そのプロジェクト固有の validator を先に確認しそちらを優先する。

## 前提条件

- POSIX 互換シェル(bash / Git Bash 等)で `find`・`grep`・`ls`・`git` が使えること。Bash ツールで実行する。Windows の素の PowerShell/cmd では checks.json のコマンドが動かない。
- カレントディレクトリが検査対象プロジェクトのルートであること。実行前に `pwd` で確認する。
- `gitignore_gaps` は git 管理下でのみ意味がある(下記「失敗時の対処」参照)。

## 検査項目

観点定義 (SoT) = このスキルのフォルダ内の `criteria/checks.json`(`SKILL.md` と同じフォルダ基準の相対パス。この repo では `.claude/skills/repo-hygiene-patrol/criteria/checks.json`。他の場所へ置いた環境ではそのパスに読み替える)。7項目それぞれの検査コマンド・severity判定ルールを保持する(本文へ prose 重複記載しない)。各 `id` を上から順に実行し、ヒットした場合は対応する `severity`(HIGH/MEDIUM/WARN)で報告する。`root_clutter` と `numeric_target_drift` は機械コマンドだけで判定できない部分を含むため `rationale`/`severity_rules` を Read してから判断する。

## 失敗時の対処

- 検査コマンドが「command not found」等で失敗: その項目を `[WARN] 検査不能(理由)` として出力に載せ、他の項目は続行する。出力が空なのは「ヒット無し」であり、失敗と区別する(終了コードではなく標準エラー出力の有無で見る)。
- git 管理外のディレクトリ: `gitignore_gaps`(`git ls-files`)は「対象外(git 管理外)」として報告し、他の項目は実行する。
- `numeric_target_drift` の対象パス(`CLAUDE.md`・`.claude/`・`docs/`)が無いプロジェクト: 存在するパスだけを対象にする。全て無ければ「対象外」と報告する。
- ヒットが数百件を超えるとき: 先頭 20 件程度を示し、総件数を併記する。
- `os_artifacts` の `find . -iname "nul"` は Git Bash(MSYS)前提の検査。成否は「出力があるか」だけで判定し、出力が無ければ「ヒット無し」、`find` 自体がエラーを返せば `[WARN] 検査不能(理由)` とする。

## 出力フォーマット

```text
=== Repo Hygiene Patrol ===
Date: YYYY-MM-DD

[HIGH] (件数)
- id: パス（根拠: 検査コマンドの出力行をそのまま引用）

[MEDIUM] (件数)
- id: パス（根拠: 同上）

[WARN] (件数)
- id: パス（根拠: 同上。検査不能の場合は失敗理由）

[OK] 問題なし (件数)

Total: X issues found
```

各指摘には、検査コマンドの出力から該当行をそのまま引用して根拠にする（出力に無いパスや件数を推測で書かない）。出力が空の項目は「ヒット無し」と書き、指摘にしない。

## 使用例

```text
ユーザー: 「リポジトリの衛生チェックして」
→ カレントがプロジェクトルートか確認し、checks.json の 7 項目を上から順に実行
→ 例: report_v2.md を検出 → [HIGH] versioned_filenames、docs/ 内に「80点以上」が 3 箇所 → [MEDIUM] numeric_target_drift
→ 上記フォーマットで報告し、削除・移動は実施前にユーザー確認を取る
```

```text
ユーザー: 「散らかりを検出して」(git 管理外のディレクトリで実行)
→ gitignore_gaps は「対象外(git 管理外)」と報告し、残り 6 項目を実行
→ `.DS_Store` を検出 → [HIGH] os_artifacts（根拠: find の出力 `./assets/.DS_Store`）。削除と .gitignore 追記はユーザー確認後
```

```text
ユーザー: 「リポジトリの衛生チェック」(Windows の素の PowerShell で実行)
→ find / grep が動かず、各項目が command not found
→ 各項目を [WARN] 検査不能(理由) として載せ、Git Bash で再実行するよう案内する(結果を推測で埋めない)
```

```text
ユーザー: 「ファイル構造をチェックして」(問題が無いプロジェクト)
→ 全項目の出力が空 → [OK] 問題なし (7) と Total: 0 issues found を報告する
```

エッジケース: `*_copy*` に一致しても、意図的な名前(例: ライブラリ名の一部)の場合がある。ヒットは「候補」として示し、断定しない。

## 対応アクション

- **HIGH**: 即時修正を提案(バージョン番号付きファイルは Git 履歴への統合、OS由来ゴミは削除+`.gitignore`追記)
- **MEDIUM**: 報告後にユーザー確認を取って削除/移動
- **WARN**: 報告のみ(ユーザー判断)
- **OK**: 報告不要(問題なしカテゴリはサマリーのみ)

HIGH または MEDIUM の問題が検出された場合、修正を実施してよいかユーザーに確認すること。ファイルの削除・移動は必ずユーザー確認後に行う(本 skill 自身は非破壊のレポート生成に徹する)。

---

## 更新履歴

- 1.0.0 (2026-08-31): 作成。
- 1.1.0: checks.json の参照を skill フォルダ基準に変更。os_artifacts の判定方法を失敗時の対処へ追記。version を追加。
- 1.2.0: 使用例を 4 件に増やし、出力に検査コマンド出力の引用（根拠）を求める記述を追加。更新履歴の形式を版数基準に統一。
