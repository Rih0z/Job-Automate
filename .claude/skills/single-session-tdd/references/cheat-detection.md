# ハードコード・テストごまかしの検出

SKILL.md から分離した詳細。

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

