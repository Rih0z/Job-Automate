# Neo-Brutalism Design Language

`SKILL.md` のカラー変数（`--bg-primary` `--border-primary` `--shadow-color` 等）を前提にした、ライト/ダーク両対応の実装例。

## 特徴

- 太い黒枠 (4-6px): `border: 4px solid var(--border-primary)`
- ドロップシャドウ (右下オフセット): `box-shadow: 8px 8px 0 var(--shadow-color)`
- 鮮やかな色: アクセントカラーを大胆に使う
- タイポグラフィ重視: 大きな見出し、明確な階層

## 実装例

```css
.neo-card {
  background: var(--bg-primary);
  border: 4px solid var(--border-primary);
  box-shadow: 8px 8px 0 var(--shadow-color);
  padding: 2rem;
  transition: transform 0.2s, box-shadow 0.2s;
}

.neo-card:hover {
  transform: translate(-4px, -4px);
  box-shadow: 12px 12px 0 var(--shadow-color);
}

.neo-button {
  background: var(--brand-primary); /* 白文字とのコントラスト 4.5:1 以上の濃さにする */
  color: white;
  border: 3px solid var(--border-primary);
  padding: 1rem 2rem;
  font-weight: 600;
  box-shadow: 4px 4px 0 var(--border-primary);
  min-width: 44px;
  min-height: 44px;
}
```

アニメーションは `prefers-reduced-motion: reduce` のとき無効にする（`transition: none`）。
