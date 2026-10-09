# workflows/customer-support/ — 顧客対応チャットボットの運用設計

業務ワークフロー「お客様と直接対話する AI（サポートボット）の運用設計」のハーネス。対応範囲、回答の根拠づけ、有人への引き継ぎ（お客様のフラストレーション検知を含む）、引き継ぎ手順、ガードレール、成功基準と評価、運用監視を 1 つの設計書にまとめ、確定前にレビューする。

## 使う順序

| 順 | ファイル | 用途 | 対応する skill |
|---|---|---|---|
| 1 | [chatbot-operation-design.md](chatbot-operation-design.md) | 聞き取りから運用設計書（システムプロンプトの骨子つき）を作る | [chatbot-operation-design](../../.claude/skills/chatbot-operation-design/SKILL.md) |
| 2 | [review-chatbot-operation-design.md](review-chatbot-operation-design.md) | 設計書を 10 観点・100 点満点で採点する（別エージェント） | [review-chatbot-operation-design](../../.claude/skills/review-chatbot-operation-design/SKILL.md) |

## 評価基準の置き場所

評価基準（観点）の本体は構造化データ [criteria/chatbot-operation.json](../../.claude/skills/review-chatbot-operation-design/criteria/chatbot-operation.json) にある。観点ごとに由来を持つ:

- `official`: Anthropic 公式資料（顧客サポート向けユースケースガイド、ガードレール、評価の作り方）に明記。出典 URL と原文の引用つき
- `official-derived`: 公式の指標を運用手順に具体化したもの（例: 「お客様のフラストレーションが溜まったら人に回す」は、公式の成功基準「エスカレーション精度」「会話中の感情の維持」の具体化）
- `practice`: 公式根拠の無い一般的な運用慣行（例: 「人と話したい」と言われたら即座に引き継ぐ、引き継ぎ時に会話の要約を渡す）

リポジトリの規則では詳細な評価基準は `review-[対象].md` に書くが、このワークフローでは観点を JSON に一本化し、`review-chatbot-operation-design.md` はその JSON を参照する形にしている（観点をすべて構造化データで保持する方針のため）。

## 関連

- 観点の出典（公式資料の現行版は URL を開いて確認する）は JSON の `sources` を参照
- 実装コード・特定プラットフォームの設定・法規制の条文は範囲外（JSON の `out_of_scope`）

---

[← ワークフロー一覧に戻る](../README.md)
