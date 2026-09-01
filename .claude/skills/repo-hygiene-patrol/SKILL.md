---
name: repo-hygiene-patrol
description: "プロジェクトのファイル構造衛生を自動検査する。バージョン番号付きファイル(_v2/_old/_backup等)、OS由来のゴミファイル、肥大化ファイル、.gitignore漏れ、ルート直下の散らかりを検出する。汎用skillのため、対象プロジェクトのディレクトリ規約は実行時に確認する。Trigger phrases: 'ファイル構造をチェックして', 'リポジトリの衛生チェック', 'repo-hygiene-patrol', '散らかりを検出して'."
disable-model-invocation: true
allowed-tools: Read Grep Glob Bash
---

# リポジトリ衛生パトロール

## 概要

プロジェクトのファイル構造が乱れていないかを検査する。個別プロジェクトの配置規約(ディレクトリ構成)は事前に把握できないため、規約に依存しない一般的な散らかりパターンのみを機械的に検出する。特定プロジェクトの規約(root allowlist等)に照らした検査が必要な場合は、そのプロジェクト固有の validator を先に確認しそちらを優先する。

## 検査項目

### 1. バージョン番号付きファイル名

同一ファイルの複数版が Git 管理下ではなくファイル名で管理されていないか:

```bash
find . -not -path "*/node_modules/*" -not -path "*/.git/*" \
  \( -name "*_v[0-9]*" -o -name "*_new.*" -o -name "*_old.*" -o -name "*_backup*" -o -name "*_copy*" -o -name "* (1).*" -o -name "* (2).*" \)
```

検出されたら **HIGH**（Git がバックアップ機能を提供するため、ファイル名でのバージョン管理は不要かつ紛れの元）。

### 2. OS由来のゴミファイル

```bash
# Windows: nul ファイル(リダイレクトミス)、コロン付きディレクトリ名
find . -iname "nul" -not -path "*/node_modules/*" -not -path "*/.git/*"
ls -d C:* 2>/dev/null
# macOS: .DS_Store
find . -name ".DS_Store" -not -path "*/node_modules/*" -not -path "*/.git/*"
```

検出されたら **HIGH**。`.DS_Store` は `.gitignore` への追記も併せて提案する。

### 3. テスト・ビルドの残骸がルートに漏れていないか

```bash
ls -d htmlcov/ coverage/ dist/ build/ __pycache__/ 2>/dev/null | grep -v node_modules
ls coverage.xml .coverage 2>/dev/null
```

ルート直下にあり、かつプロジェクトの通常のビルド出力先として明示的に規約化されていない場合 **MEDIUM**。

### 4. 肥大化ファイル

```bash
find . -size +50M -not -path "./.git/*" -not -path "*/node_modules/*"
```

検出されたら **WARN**（Git LFS の使用や `.gitignore` 追加を検討する余地の指摘のみ、削除は提案しない）。

### 5. `.gitignore` 漏れ

以下がトラッキングされていないか確認:

```bash
git ls-files | grep -E "\.pyc$|__pycache__/|\.coverage$|htmlcov/|\.log$|node_modules/"
```

1件以上ヒットしたら **MEDIUM**（`.gitignore` への追記とトラッキング解除を提案）。

### 6. ルート直下の散らかり(判断支援・機械判定しない)

ルート直下のファイル一覧を `ls` で取得し、プロジェクトの README/CLAUDE.md に明記された「トップレベル構成」と照合する。規約が見つからない場合は、種類の異なるファイルが無秩序に増えていないか(例: 一時的な `.md` メモ・スクリプトの試作がルートに放置)を目視で確認し、**WARN** として報告する(規約不在のため機械的 HIGH/MEDIUM 判定はしない)。

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
