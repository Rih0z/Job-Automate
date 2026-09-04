---
name: server-windows-standard
description: |
  Windows サーバー/マシンのクラッシュダンプを WinDBG (mcp_server_windbg) + Microsoft公式ドキュメント
  検索 (microsoft.docs.mcp) を統合活用して解析し、バグを埋め込んだ原因関数・原因コード行を特定して
  修正支援する。Phase0 (ダンプ確認・MS公式情報収集) → Phase1 (初期トリアージ・既知脆弱性照合) →
  Phase2 (障害カテゴリ別 [特権昇格/メモリ安全性/競合状態/IO] の追跡) → Phase3 (原因関数のコード
  レベル解析) → Phase4 (再現実験・根本原因レポート) → Phase5 (100点満点の解決度評価と最終レポート)
  の5フェーズで進める。
  Trigger phrases: 'Windows クラッシュダンプ解析', 'WinDBG で原因特定', 'BSOD 原因調査',
  'カーネルクラッシュ 解析', 'windows crash dump analysis', 'stop code 解析'.
metadata:
  provenance: domain-prompt
---

# Windows クラッシュダンプ解析 — 原因関数特定・修正支援 (MCP版)

## 前提: 利用可能なMCPツール

- **WinDBG解析**: `open_windbg_dump`, `run_windbg_cmd`, `list_windbg_dumps`, `close_windbg_dump`
- **Microsoft公式情報**: `microsoft_docs_search`, `microsoft_docs_fetch`

## 最終目標

バグを埋め込んだ原因関数を特定し、修正支援する。40年のWindows内部構造解析のエキスパートとして、
接続されたMCPサーバー (WinDBG + Microsoft公式ドキュメント) を駆使し、Microsoft公式ドキュメント・
KB記事・Security Advisory・既知のCVE情報を参照しながら分析する。

## Phase 0: 情報収集 — ダンプ確認とMS公式データベース検索

### 0-1. ダンプファイル確認
最新のクラッシュダンプファイルを見つけて開き、`!analyze -v`, `vertarget`, `.time`, `lm t n` の結果を表示する。

即座に実行すべきMS公式情報検索 (MCPサーバー経由):
- **A. Microsoft公式技術情報**: WinDBG出力から得られたSTOP_CODE、MODULE_NAME、FUNCTION_NAMEについて
  Microsoft Learnから公式ドキュメントを検索 (kernel debugging / driver development / error handling)
- **B. MSRC情報**: 特定されたモジュール名とエラーパターンについてCVE情報・security bulletin・
  vulnerability情報を検索
- **C. Microsoft Knowledge Base**: STOP_CODEとOS_VERSIONについてKB記事と既知の問題情報を検索
- **D. Windows内部構造の公式ドキュメント**: 関連サブシステム名とAPI名についてWindows Internals /
  WDK公式ドキュメントを取得

### 0-2. 統合分析
WinDBG出力とMicrosoft公式ドキュメントを照合し、既知の問題か新規の問題かを判定する (WDKドキュメント・
WHQL要件・関連KB記事との整合性チェックを含む)。

## Phase 1: 初期トリアージ — MCP公式情報クロスリファレンス

### 1-1. 犯行現場確保
`!analyze -v`, `!analyze -show`, `.bugcheck`, `.lastevent`, `!sysinfo machineid`, `!sysinfo cpuinfo`
を実行し、以下をMS公式情報で照合する:
- 既知の脆弱性 (CVE履歴・kernel security vulnerabilities・security advisory)
- Microsoft公式バグレポート (feedback / known issues / bug reports)
- 開発者向け公式ガイダンス (driver development best practices / kernel programming guidelines)

### 1-2. 障害カテゴリ分類 (STOP CODEによる自動分岐)

| カテゴリ | STOP CODE 例 | 次アクション | 犯人候補 |
|---|---|---|---|
| 特権昇格系 | 0x3B, 0xD1, 0xA | Phase 2-A | 特権チェック回避犯、KASLR回避犯、CFG回避犯 |
| メモリ安全性違反系 | 0x1A, 0xC2, 0x50 | Phase 2-B | ヒープスプレー犯、ROP/JOP攻撃犯、UAF悪用犯 |
| 競合状態・同期系 | 0x25, 0xC4, 0x133 | Phase 2-C | レースコンディション犯、デッドロック犯、優先度逆転犯 |
| I/O・ファイルシステム系 | 0x7A, 0x77, 0x24 | Phase 2-D | IRPスタック破壊犯、ファイルシステムメタデータ破壊犯 |

各カテゴリで、該当するMODULE_NAME/API_NAMEについてMicrosoft公式ドキュメントを検索する
(例: "Windows kernel privilege escalation", "Windows kernel memory safety" + CFG/CFI情報,
"Windows synchronization primitives", "Windows I/O subsystem" + NTFS internals)。

## Phase 2: 障害カテゴリ別 犯人追跡

各カテゴリで共通のパターン:
1. 該当するWinDBGコマンド群を実行して容疑者を特定する
2. Microsoft公式セキュリティ/技術情報と照合する (MCP経由)
3. 統合分析で、関数・STOP Code・Exception Address・IRQL等の技術分析とMS公式ドキュメントを
   突き合わせ、以下を要求する: 制約事項の確認・WDF仕様との整合性・CFG/CET対応状況・最新の
   Security Mitigationとの関係・類似CVE事例。犯人特定要求として、コード行レベルの問題箇所・
   セキュリティ境界の違反パターン・Attack surface・修正すべき具体的API呼び出しを求める。

### Phase 2-A: 特権昇格
`!process 0 7`, `!thread`, `!token`, `!acl`, `!sd`, `!privileges`, `kv`, `!irql` を実行。
Windows Security Model / access control / TOKEN_TYPE、Exploit Guard / Kernel CFG / セキュリティ
緩和策をMS公式ドキュメントで照合する。追加コマンド: `!analyze -v -f`, `uf /c <suspect_function>`,
`!analyze -hang -v`, `!locks -v`, `dt <structure> -r3`。

### Phase 2-B: メモリ安全性
`!heap -p -a <address>`, `!heap -flt s <size>`, `!poolused 2`, `!poolfind <tag> -v`,
`!analyze -v -hang`, `!verifier 4` を実行。Windows memory management / heap corruption detection /
CFI / Intel CET Windows support、secure coding practicesをMS公式ドキュメントで照合する。
Heap Manager内部動作・LFH・Segment Heap・Pool corruption detection・CET/ARM Pointer Authentication
対応状況を確認し、メモリ破壊を引き起こす具体的コード行 (不正ポインタ演算・Double-free/UAF・
integer overflow/underflow) を特定する。

### Phase 2-C: 競合状態・同期
`!locks -v`, `!critical_section`, `!mutex -v`, `!for_each_thread "!runaway 7"`, `!ready`, `!running`
を実行。Windows synchronization primitives / dispatcher objects / concurrent programming /
lock-free programmingをMS公式ドキュメントで照合する。Dispatcher Objects内部状態・ERESOURCE・
Fast Mutex vs Mutex vs Critical Section・IRQLレベル遷移・Spin Lockを確認し、デッドロックの
lock acquisition順序・race conditionの発生箇所・priority inversion・lock-free実装ミスを特定する。

### Phase 2-D: I/O・ファイルシステム
`!irp`, `!devobj`, `!drvobj`, `!devstack`, `!fileobj`, `!process 0 7 System` を実行。
Windows I/O architecture / NTFS internals / WDF / IRP processingをMS公式ドキュメントで照合する。
I/O Manager・IRP completion routine・Fast I/O vs Standard I/O・Filter Driver・VSSを確認し、
IRPを破壊するfilter driver処理・file system metadataを破壊するアクセスパターン・Cache Manager
との整合性を破るI/O操作・Memory Mapped I/Oでのページング競合箇所を特定する。

## Phase 3: 原因関数の完全解体 — コードレベル解析

`uf /c <criminal_function>`, `uf /o <criminal_function>`, `dt <criminal_structure> -rv3`,
`!analyze -show -v` を実行。

特定された関数名とAPI名についてMicrosoft公式ドキュメントからAPI仕様・parameters requirements・
return values error codesを検索し、kernel programming / driver development guidelinesの最新情報
を取得する。

技術的証拠 (犯人関数・逆アセンブル結果・データ構造・メモリ状態・スタックトレース) とMS公式技術
文書を統合し、以下を提示する:
1. この関数が確実にバグを含む決定的証拠
2. 問題となる具体的なC/C++/Assembly行
3. なぜこのバグが埋め込まれたかの技術的理由
4. 具体的な修正パッチコード
5. 修正後のテスト方法
6. 他システムへの波及可能性評価
7. Exploitability評価
8. Microsoftの公式対応状況

## Phase 4: 証拠固めと再現実験

`!analyze -show -v`, `!uptime`, `!sysinfo`, `!vm`, `!handle 0 f` を実行し、Windows testing
framework / WHQL testing requirements / stress testingをMS公式ドキュメントで照合する。

完全解析結果から、以下の形式で根本原因レポートを作成する:
1. Executive Summary (C-level向け1分要約)
2. Technical Details (エンジニア向け詳細分析)
3. Root Cause Analysis (5-Why分析)
4. Impact Assessment (ビジネス影響評価)
5. Remediation Plan (段階的修正計画)
6. Prevention Strategy (再発防止戦略)
7. Timeline (対応スケジュール)
8. Risk Assessment (リスク評価マトリックス)

## Phase 5: 最終評価 — 100点満点の解決度評価

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

## 活用度の目標

- WinDBG分析: 全コマンド実行・結果解析
- MS公式情報: 関連ドキュメント完全検索
- 統合分析: 技術証拠と公式情報の完全照合

成功基準: 「この関数の、この行で、この理由により、このバグが発生し、この方法で修正される」を
MCP統合分析で証明すること。
