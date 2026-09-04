---
name: thumbnail-generation
description: >
  ブラウザ操作可能な画像生成AI(Gemini等)とClaude Codeの役割分担で、ブログ/動画のサムネイル画像を
  3ラウンド構成(Round1土台生成→Round2創造的仕上げ→Round3 CTRフック追加+レビュー修正・毎回必須)で
  生成する。ラウンドごとに新規チャットセッション・ブランド要素の単体参照画像を毎回添付、という
  実測ベースの運用ルールを含む。生成物のレビューは review-thumbnail skill を使う。
  Trigger phrases: 'サムネイル生成して', '魅力的なサムネを作って', 'Geminiでサムネ作成',
  'thumbnail generation', 'CTR重視のサムネイル', 'ブログのアイキャッチ作って'.
allowed-tools: Read
metadata:
  provenance: domain-prompt
---

# サムネイル画像生成 (Gemini + Claude 3ラウンド方式)

原本（完全な手順・落とし穴・フォールバック運用の一次ソース）:
`workflows/content-creation/thumbnail-generation.md`

原本を Read し、そこに記載された3ラウンドの手順・添付ルール・サーキットブレーカー規則を省略・改変せず適用すること。

**要点（progressive disclosure・詳細は原本参照）**:
- Round 1: 実写真/素材 + ブランド要素参照画像を統合し見出しまで焼き込んだマスター画像を生成
- Round 2: 短い指示でコンテンツの魅力を仕上げ直す（新規チャット・参照画像を再添付）
- Round 3: 「見ると何が分かるか」のCTRフック文言追加(毎回必須) + レビュー修正（新規チャット）
- 各ラウンドは必ず新規チャットセッションで実行し、ブランド要素の単体参照画像を毎回添付する
- フック文言等の固有情報はClaude側が一次情報から確定してから書き込む(生成AIへの丸投げ・捏造禁止)

生成後は必ず `review-thumbnail` skill (または `workflows/content-creation/review-thumbnail.md`) でチェックリスト評価を通す。自己レビューのみでの採用は禁止。

**実際の画像生成には、Claude Code から操作可能なブラウザ自動化ツール(Playwright MCP等)経由で対象の画像生成AIサービスを操作する。API直叩き(認証情報を要する専用SDK等)がある場合はプロジェクトのポリシーに従う。**
