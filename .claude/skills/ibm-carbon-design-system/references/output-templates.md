# 出力テンプレート

## 目次

- 各 Phase 終了時の報告
- トークン定義ファイルのひな形
- Phase 3 検証表
- 差分提示（既存プロジェクト）

## 各 Phase 終了時の報告

```
Phase {1|2|3} 完了
適用したファイル:
- {パス}: {追加・変更した内容を 1 行}
未対応・保留:
- {項目と理由}（無ければ「なし」）
次の Phase: {名前}
```

## トークン定義ファイルのひな形

ひな形の構造のみ。値は `references/design-system-spec.md`（Carbon 公式値を求められたときは公式サイト）とペルソナ分析の結果から埋める。

```css
:root {
  /* Color Roles（Light） */
  --color-bg: ;
  --color-text: ;
  --color-primary: ;
  /* Typography */
  --font-sans: "Inter", sans-serif;
  --font-mono: "JetBrains Mono", monospace;
  /* Spacing（8px グリッド） */
  --space-1: 8px;
  --space-2: 16px;
}
[data-theme="dark"] { /* ダークモード要のときのみ */ }
```

## Phase 3 検証表

| 項目 | 合否 | 根拠（ファイル:行） |
|---|---|---|
| 1.1.1 非テキストコンテンツ | 合 / 否 / 対象外 | |

不合格が 1 件でも残る間は「完了」と言わず、不合格項目と修正案を先頭に示す。

## 差分提示（既存プロジェクト）

置き換え前に、変更するコンポーネントごとに「ファイル / 現状 / 変更後 / 影響範囲」を 4 列の表で示し、ユーザーの了承を得てから上書きする。
