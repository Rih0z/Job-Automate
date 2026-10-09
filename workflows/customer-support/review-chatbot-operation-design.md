# 顧客対応チャットボット 運用設計レビュープロンプト

運用設計書を、作成者とは別の担当（別のセッション・別のエージェント）が採点するためのプロンプト。評価基準の本体は JSON（`.claude/skills/review-chatbot-operation-design/criteria/chatbot-operation.json`）で、このファイルには採点の手順だけを書く。Claude Code では `review-chatbot-operation-design` skill を使う。Claude.ai 等では、下の本文を貼り、設計書と JSON の 2 つを添付する。

---

あなたは作成者とは別の客観的なレビュー担当です。添付の「顧客対応チャットボット運用設計書」を、添付の評価基準 JSON に従って採点してください。

## 採点のしかた

- JSON の `criteria` ごとに、各 check を「満たす / 一部 / 満たさない / 該当なし」で判定し、根拠として設計書の該当箇所を逐語で引用する（無ければ「記述なし」）
- criterion の得点 = weight ×（満たす 1・一部 0.5・満たさない 0 の平均。該当なしは母数から除く）
- 該当なしにできるのは次の 2 つだけ。どちらも理由を書く: (1) その check の前提が設計の範囲に無い（例: ツール連携をしないボットの tools.*）、(2) provenance が practice の check を、設計書が理由を書いたうえで採らないと決めている（理由の妥当性は任意の提案として扱う）。official / official-derived の check を採らないのは「満たさない」
- criterion 内の check がすべて該当なしなら、その criterion は採点から外し、合計は残りの weight の合計を 100 に換算する
- `must_pass: true` の criterion に「満たさない」が 1 つでもあれば、その criterion は不合格
- 判定: must_pass の criterion がすべて合格、かつ合計が `pass_rule.min_score` 以上なら PASS
- 指摘には check の `id` を付ける。`provenance` が `practice` の check への指摘は「公式根拠なし（運用慣行）」と明記する
- correctness と明示された要件に関わる指摘だけを必須にし、好みの提案は任意として分ける
- 設計書は編集しない。修正案は提案として書く

## 出力形式

```
## 判定: PASS / FAIL（合計 xx / 100、must_pass: 合格 / 不合格の criterion 名）

| criterion | 得点 / weight | must_pass | 主な不足（check id） |
|---|---|---|---|

### 必須の指摘
- [check id] 設計書の該当箇所（逐語）→ 何が不足か → 修正案

### 任意の提案
- [check id]（practice の場合は「公式根拠なし」）…
```
