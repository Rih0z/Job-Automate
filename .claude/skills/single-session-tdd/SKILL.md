---
name: single-session-tdd
description: "単一セッションで回すテスト駆動開発(TDD)ワークフロー。仕様確認→(曖昧ならユーザーに質問)→失敗するテスト(Red)→最小実装(Green)→リファクタの順を強制し、各工程の完了時に review-gate skill で別エージェントの独立レビューを受ける。ハードコード・テストごまかしの検出例つき。Use when the user asks to 'TDDで進めて', 'テスト駆動で開発して', 'テストファーストで実装して', or when starting implementation work in a project that mandates TDD. 3ターミナル分離で回す場合は three-agent-tdd-workflow を使う。"
---

# single-session-tdd — 単一セッションTDDワークフロー

3ターミナル分離(`three-agent-tdd-workflow`)を使わず、1つのClaude Codeセッションで開発を回すときのTDDプロトコル。レビューの客観性は `Agent` ツールによる別エージェント委譲(`review-gate` skill)で担保する。

## 必須の順序(実装タスクごとに繰り返す)

1. **仕様確認**: 仕様書・設計書の該当箇所を読み、期待される振る舞いを特定する。仕様に書かれていない・曖昧な点があれば、**実装で勝手に決めずユーザーに質問して仕様を確定させる**。仕様を書いた/変えたら → review-gate: spec
2. **設計**: 設計・スキーマ・APIを書いた/変えたら → review-gate: design
3. **テストを先に書く(Red)**: 確認した仕様をもとに失敗するテストを書き、失敗することを確認する。テスト名は仕様の文として読めるようにする。→ review-gate: test(PASSしてから実装に入る)
4. **実装(Green→Refactor)**: テストを通す最小限の実装をし、テストが通ったままコードを整理する。→ review-gate: implementation(PASSしてからコミット)
5. **デプロイ前**: → review-gate: release

禁止事項:
- テストを書かずに実装コードを先に書き始めること。後付けテストはTDDとみなさない。
- 自分の成果物を自分でレビューして通過扱いにすること。
- 実装をまとめて書いてからテストをまとめて書くこと(機能単位で小さくRed→Green→Refactorを回す)。

## テストカバレッジの最低ライン

- 正常系(ハッピーパス)
- 異常系(バリデーション失敗・認可失敗・外部依存の失敗)
- 境界値(ゼロ件・空データ・上限・期間や数量の端・ドメイン固有の境界)
- 副作用(DB・API呼び出し等)はモック/スタブで分離する

## ハードコード・テストごまかしの検出

実装とテストを書いたあと、必ず次のパターンがないか見直す。

```ts
// NG: テストケースの値をそのまま返している
function calculateFee(amount: number) {
  if (amount === 1000) return 100
  return 0
}

// OK: 実際のロジックで計算する
function calculateFee(amount: number) {
  if (amount <= 0) return 0
  return amount * FEE_RATE
}
```

```ts
// NG: アサーションを緩めて無理やり通している
expect(results.length).toBeGreaterThan(0)

// OK: 期待値を厳密に書く
expect(results).toEqual([{ start: "09:00", end: "10:00" }])
```

## 独立レビューの回し方

- 各工程の完了時に `review-gate` skill の手順で `Agent` ツール(`general-purpose`)を起動し、観点JSON(criteria/*.json)に基づくレビューを受ける。
- レビュアーには対象ファイルのパスだけを渡し、自分の実装意図・言い訳を渡さない。
- FAILなら修正して再レビュー。PASSするまで次工程に進まない。
- レビュアーが観点定義の抜け漏れを指摘したら、criteria JSONを更新してコミットする(スキルは育てるもの)。
