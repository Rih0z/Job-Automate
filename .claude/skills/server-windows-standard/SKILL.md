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
  'カーネルクラッシュ 解析', 'windows crash dump analysis', 'stop code 解析', 'ブルースクリーンの原因',
  '.dmp を調べて'.
  使わない場面: MCP サーバーの導入・登録そのもの (mcp-server-setup を使う)、ダンプを伴わない
  Windows の一般的な設定相談・イベントログ調査、アプリ開発側の単体テスト。
metadata:
  provenance: domain-prompt
  version: "1.1"
---

# Windows クラッシュダンプ解析 — 原因関数特定・修正支援 (MCP版)

## 前提条件
- WinDBG MCP サーバーと Microsoft Learn docs MCP サーバーが `.mcp.json` に登録済みで、`.dmp` が読めること。
- 表の STOP CODE と WinDbg コマンドは Microsoft 公式ドキュメントに載るものに限る。環境により出力が異なるので、実行して確認できた出力だけを根拠にする。
- 最終レポートの「犯人」「犯行」等の表現は元の趣旨を保つための比喩。顧客向けには通常の語 (原因関数・原因コード) に読み替える。

## 前提: 利用可能なMCPツール

Claude Code 上の MCP ツール名は `mcp__<.mcp.json に登録したサーバー名>__<ツール名>` の完全修飾名になる。登録名は環境ごとに違うので、作業開始時に `/mcp` で実際のサーバー名とツール名を確認し、以降はその完全修飾名で呼ぶ（サーバー名無しで呼ぶと tool not found になり得る）。

- **WinDBG解析**（WinDBG MCP サーバー）: `open_windbg_dump`, `run_windbg_cmd`, `list_windbg_dumps`, `close_windbg_dump`
- **Microsoft公式情報**（Microsoft Learn docs MCP サーバー）: `microsoft_docs_search`, `microsoft_docs_fetch`

## 行動原則
- 証拠主義: 結論は WinDBG の出力 (コマンド名と該当行) と MS 公式ドキュメント (URL またはタイトル) を引用して示す。出力に無いことを推測で断定しない。
- 確信度を 確定 / 強い疑い / 可能性あり / 要追加調査 の 4 段階で明記する。裏付けのない項目は「未確認」と書く。
- 成果物が公開される可能性があるため、ダンプ内の会社名・ホスト名・ユーザー名・IP などの機微情報は報告に転記せず伏せる。
- Phase の判定基準を満たさないまま次へ進まない (各 Phase 末尾の「通過条件」を参照)。

## 最終目標

バグを埋め込んだ原因関数を特定し、修正支援する。40年のWindows内部構造解析のエキスパートとして、
接続されたMCPサーバー (WinDBG + Microsoft公式ドキュメント) を駆使し、Microsoft公式ドキュメント・
KB記事・Security Advisory・既知のCVE情報を参照しながら分析する。

## Phase 0: 情報収集 — ダンプ確認とMS公式データベース検索

### 0-1. ダンプファイル確認
ユーザーがパスを指定していればそれを使う。無ければ `list_windbg_dumps` で候補を列挙し、最新の `.dmp`
(通常は `C:\Windows\MEMORY.DMP` または `C:\Windows\Minidump\`) を `open_windbg_dump` で開く。
候補が複数あり選べない場合はユーザーに確認する。開いたうえで、`!analyze -v`, `vertarget`, `.time`, `lm t n` の結果を表示する。

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

通過条件: `!analyze -v` が STOP_CODE とモジュール名を返し、シンボルが解決されていること。

### 失敗時の対処 (Phase 0 全体)
- **ダンプが開けない**: パス・権限・ファイル破損を確認する。別のダンプがあればそちらを試し、無ければ報告して終了する。
- **シンボル未解決** (`!analyze -v` でモジュール名が `unknown` や `+0x` のみ): `.symfix` と `.reload /f` を実行してから再解析する。それでも解決しない場合は、その旨と確信度の低下を最終レポートに明記する。
- **MS Learn MCP が未接続**: `/mcp` で接続状態を確認し、使えなければ公式照合の項目を「未確認」として WinDBG 出力のみで進め、レポートに制約を書く。
- **MCP ツールが tool not found**: 上記の完全修飾名で呼び直す。

## Phase 1: 初期トリアージ — MCP公式情報クロスリファレンス

### 1-1. 犯行現場確保
`!analyze -v`, `!analyze -show`, `.bugcheck`, `.lastevent`, `!sysinfo machineid`, `!sysinfo cpuinfo`
を実行し、以下をMS公式情報で照合する:
- 既知の脆弱性 (CVE履歴・kernel security vulnerabilities・security advisory)
- Microsoft公式バグレポート (feedback / known issues / bug reports)
- 開発者向け公式ガイダンス (driver development best practices / kernel programming guidelines)

### 1-2. 障害カテゴリ分類 (STOP CODEによる一次分類)

以下は調査の入口を決める目安であり、原因の確定ではない (例: 0x3B / 0xD1 は特権昇格に限らず、不正なメモリ参照や IRQL 違反でも出る)。`!analyze -v` の所見と食い違えば `!analyze -v` を優先し、別カテゴリも検討する。

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

Phase 1 で選んだカテゴリ (2-A 特権昇格 / 2-B メモリ安全性 / 2-C 競合状態・同期 / 2-D I/O・ファイルシステム) の節だけを [references/phase2-categories.md](references/phase2-categories.md) で読み、そこに載るコマンド群を実行して容疑者を特定し、Microsoft 公式情報と照合する。通過条件: 原因候補の関数またはモジュールが WinDBG の出力で裏付けられていること。

## Phase 3: 原因関数の完全解体 — コードレベル解析

`uf /c <criminal_function>`, `uf /o <criminal_function>`, `dt <criminal_structure> -rv3`,
`!analyze -show -v` を実行。

特定された関数名とAPI名についてMicrosoft公式ドキュメントからAPI仕様・parameters requirements・
return values error codesを検索し、kernel programming / driver development guidelinesの最新情報
を取得する。

技術的証拠 (犯人関数・逆アセンブル結果・データ構造・メモリ状態・スタックトレース) とMS公式技術
文書を統合し、以下を提示する (ソースが無い場合は逆アセンブルから分かる範囲に限り、推測部分は「推測」と明記する):
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

解決度を 100 点満点で評価し、最終レポートを固定フォーマットで返す。点数の帯の要件と出力フォーマット (最終犯人特定レポート) は [references/final-evaluation.md](references/final-evaluation.md) を読む。選んだ帯と満たせなかった要件、確信度、最低 2 つの代替仮説を必ず併記する。

## 使用例
- ユーザー: 「この .dmp の BSOD 原因を調べて」
- 動作: `/mcp` でツール名を確認 → Phase 0 でダンプを開き STOP_CODE (例: 0xD1) を取得 → 表の分類 (0xD1 は特権昇格系) に従い
  Phase 2-A を選んで疑わしいドライバ関数を特定 → Phase 3 で逆アセンブルを根拠に原因を示し、
  Phase 5 で点数・確信度・代替仮説を付けて最終レポートを返す。

## 活用度の目標

- WinDBG分析: 全コマンド実行・結果解析
- MS公式情報: 関連ドキュメント完全検索
- 統合分析: 技術証拠と公式情報の完全照合

成功基準: 「この関数の、この行で、この理由により、このバグが発生し、この方法で修正される」を
MCP統合分析で証明すること。

## 更新履歴
- 1.1: Phase 2 と Phase 5 を references/ に分離。確認できない WinDbg コマンドを除去、STOP CODE 表を目安と明記、前提条件を追加。
