---
name: review-oss-contribution
description: "Audit OSS contribution candidates in a candidates directory. Checks originality, prior art, feasibility, and strategy."
disable-model-invocation: true
allowed-tools: Read Grep Glob
argument-hint: "<candidates-dir> (省略時は ./oss-contributions/open/)"
---

# OSS貢献候補の審査

指定ディレクトリ（省略時は `./oss-contributions/open/`）に配置されたOSS貢献候補を審査し、以下の基準で判定する。

## 審査基準

### 1. 独自性チェック（最重要）

アイデアの出所を確認:
- ✅ **自プロジェクトの独自開発で発見・実装した知見** → 貢献可能
- ✅ **他のOSSから学んだ知見を応用**（ライセンス互換性を確認済み） → 貢献可能
- ❌ **ライセンス上再配布・改変が認められないソース**（非公開コードのリーク、閲覧のみ許諾されたソース等）を参照して得た設計パターン → 貢献不可

出所確認の観点:
- 参照禁止ソースのファイルを直接参照していないか
- 参照禁止ソース固有の実装パターン（変数名・アーキテクチャ用語がそのまま一致する等）ではないか
- **禁止理由**: 再配布が許諾されていないソースから得たコードを他OSSに持ち込むのはライセンス・倫理リスクを伴う

### 2. 先行技術チェック

対象OSSの既存Issue/PRで:
- 同じアプローチが既に提案されていないか
- 既にマージ済みの修正で解決されていないか
- 活発な議論が進行中で割り込む余地がないか

### 3. 実現可能性チェック

- PRが小規模（初回貢献の場合は目安 +50行以内）に収まるか
- 対象OSSの言語で実装可能か
- CI/テストを通せるか

### 4. 戦略チェック

- Issue + 最小PR を同時に出す計画か
- Issue で手の内を見せすぎていないか
- PRが1目的に絞られているか

## 出力形式

各候補について以下を出力:

```
## [ファイル名]
- 独自性: ✅/❌ + 理由
- 先行技術: あり/なし
- 実現可能性: 高/中/低
- 判定: **GO** / **HOLD** / **REJECT**
- 理由: 1行
```

## 実行

`$ARGUMENTS`（省略時は `./oss-contributions/open/`）の全 `.md` ファイル（`_` で始まるものを除く）を読み、上記基準で審査せよ。
