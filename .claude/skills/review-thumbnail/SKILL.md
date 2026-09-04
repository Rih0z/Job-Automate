---
name: review-thumbnail
description: >
  thumbnail-generation skillで生成したサムネイル画像(または任意のサムネイル画像)を、整合性チェック
  (ブランド要素の破綻・実在文字の誤生成・架空要素の創作等・CRITICAL)とCTR(クリック率)観点チェック
  (視覚要素数・伝達力・表情の強さ・見出し文字量・縮小視認性)の2軸でレビューし、
  PASS/REVISE/REGENERATEを判定する。自己レビューではなくチェックリストでの突き合わせを必須とする。
  Trigger phrases: 'サムネイルをレビューして', 'このサムネCTR的にどう', 'サムネイル品質チェック',
  'review thumbnail', 'サムネの整合性確認'.
allowed-tools: Read
metadata:
  provenance: domain-prompt
---

# サムネイル画像レビュー

原本（完全なチェックリスト・採点目安の一次ソース）:
`workflows/content-creation/review-thumbnail.md`

原本を Read し、A(整合性・CRITICAL)・B(CTR観点)・C(機械チェック補助) の全項目を省略せず1項目ずつ突き合わせて評価すること。

**判定**:
- A全クリア + B4項目以上クリア → PASS
- A全クリアだがB3項目以下 → REVISE（コンテンツフック追加ラウンドで改善）
- Aに1項目でも該当 → REGENERATE（該当ラウンドからの再生成、多くはRound1から）

対象の生成手順は `thumbnail-generation` skill (`workflows/content-creation/thumbnail-generation.md`)。
