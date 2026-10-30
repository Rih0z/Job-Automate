# Phase 2 障害カテゴリ別の追跡手順

SKILL.md から分離した詳細。Phase 1 の分類で選んだカテゴリの節だけ読む。

## Phase 2: 障害カテゴリ別 犯人追跡

各カテゴリで共通のパターン:
1. 該当するWinDBGコマンド群を実行して容疑者を特定する
2. Microsoft公式セキュリティ/技術情報と照合する (MCP経由)
3. 統合分析で、関数・STOP Code・Exception Address・IRQL等の技術分析とMS公式ドキュメントを
   突き合わせ、以下を確認する: 制約事項の確認・WDF仕様との整合性・CFG/CET対応状況・最新の
   Security Mitigationとの関係・類似CVE事例。犯人特定要求として、コード行レベルの問題箇所・
   セキュリティ境界の違反パターン・Attack surface・修正すべき具体的API呼び出しを求める。

### Phase 2-A: 特権昇格
`!process 0 7`, `!thread`, `!token` (トークンの特権情報もここで確認する), `!acl`, `!sd`, `kv`, `!irql` を実行。
Windows Security Model / access control / TOKEN_TYPE、Exploit Guard / Kernel CFG / セキュリティ
緩和策をMS公式ドキュメントで照合する。追加コマンド: `uf /c <疑わしい関数名>` (関数名は `!analyze -v` の `FAILURE_BUCKET_ID` / `STACK_TEXT` の最上位フレームから取る),
`!analyze -hang -v`, `!locks -v`, `dt <structure> -r3`。

### Phase 2-B: メモリ安全性
`!heap -p -a <address>`, `!heap -flt s <size>`, `!poolused 2`, `!poolfind <tag> -v`,
`!analyze -hang -v`, `!verifier 4` を実行。Windows memory management / heap corruption detection /
CFI / Intel CET Windows support、secure coding practicesをMS公式ドキュメントで照合する。
Heap Manager内部動作・LFH・Segment Heap・Pool corruption detection・CET/ARM Pointer Authentication
対応状況を確認し、メモリ破壊を引き起こす具体的コード行 (不正ポインタ演算・Double-free/UAF・
integer overflow/underflow) を特定する。

### Phase 2-C: 競合状態・同期
`!locks -v`, `!critical_section` (ユーザーモードのダンプのみ), `!stacks 2`, `!ready`, `!running`
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

