# Phase 5 最終評価と最終レポートの出力形式

SKILL.md から分離した詳細。

## Phase 5: 最終評価 — 100点満点の解決度評価

点数は表の帯の要件を満たした項目数で決める。帯の要件をすべて満たす最上位の帯を選び、その帯の中では
満たした要件の割合で位置を決める (例: 85〜99点帯で要件 4 項目中 3 項目なら約 92 点)。選んだ帯と満たせなかった要件を必ず併記する。

| 判定 | 点数 | 要件 |
|---|---|---|
| 究極解決 | 100点 | 犯人関数(関数名+オフセット)・犯人コード行(C/C++/Assembly行レベル)・バグカテゴリ(CVE-xxxx形式)・完全再現手順・動作確認済み修正パッチ・MS公式見解確認・CVSS 3.1スコア・全Windowsバージョン影響調査・完全な防御策実装のすべてを満たす |
| 完全解決 | 85〜99点 | 犯人関数特定+問題箇所特定・MS公式情報との完全照合・具体的修正方法提示・セキュリティ影響評価完了 |
| 高度解決 | 70〜84点 | 犯人モジュール特定・バグカテゴリ分類・MS公式情報部分照合・一般的修正方針提示 |
| 部分解決 | 50〜69点 | 問題領域特定・症状分析完了・基本的対処法提示 |
| 解決失敗 | 49点以下 | 症状説明のみ・一般論での対処提案 |

### 出力フォーマット: 最終犯人特定レポート

```
## 主犯 (Primary Perpetrator)
関数名: <exact_function_name>
モジュール: <module_name.sys> v<version>
犯行住所: <base_address + offset> (RVA: <rva>)
犯行手口: <specific_bug_pattern>
使用凶器: <api_misuse_details>
犯行動機: <why_bug_exists>
共犯関係: <accomplice_functions>

## Microsoft公式証拠 (MCP取得)
公式文書: <ms_documentation_info>
技術仕様: <technical_specification>
CVE番号: <cve_number>
KB記事: <kb_article_number>
セキュリティ勧告: <msrc_advisory>
修正状況: <patch_status>

## 最終判定
分類: <detailed_bug_classification>
証拠確実性: <percentage>%
修正優先度: <critical_level>
対応期間目安: <timeline>
監視期間目安: <monitoring_period>
影響範囲: <impact_scope>

## 再発防止提案
1. コードレビュー強化
2. 静的解析ツール導入
3. ファジングテスト実装
4. セキュリティ監査義務化
5. 開発者教育プログラム
```

