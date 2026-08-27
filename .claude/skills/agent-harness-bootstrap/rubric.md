# 自己評価ルーブリック（35 項目）

生成手順 Step 5 で使う。各項目を Y/N 評価する。N が 1 つでも残れば書き直して再評価する。Litmus Test に合格しない行は削る。**採用しなかったオプション要素は「該当なし・不要と明示宣言済み」であれば Y**。Step 7 の別エージェントレビューでも本 35 項目全 Y を合格基準に含める（Step 5 と Step 7 で同一基準）。

| # | 項目 | Y/N |
|---|------|-----|
| 1 | 公式 Litmus Test に各行が合格（消したら Claude がミスする行のみ残っている）。行数による硬性ゲートはなし |  |
| 2 | プロジェクト固有の事実のみ（一般論ゼロ） |  |
| 3 | 全コマンド・全パスが実在（推測ゼロ・捏造ゼロ） |  |
| 4 | ルート構成 1 行サマリがある |  |
| 5 | デフォルトと異なるコード規約・テスト方針が `code-quality.md` / `test-verify.md` に記載されている |  |
| 6 | 環境依存の注意点・既知の落とし穴（Step 1 で収集した「環境変数・OS 依存・既知の落とし穴」）が rules 本文に記載されている（新規プロジェクトで該当事実がなければ省略可） |  |
| 7 | 別エージェントレビューサイクルが `review.md` に記載されている |  |
| 8 | handoff は user 明示指示で受領し本文は選択 1 件のみ Read（最新を自動 Read しない）運用が `issue-workflow.md` に明記されている |  |
| 9 | handoff 命名規約（`[YYYY-MM-DD]-issue-[ID]-[識別単語].md`、識別単語は 2〜4 語 kebab-case）が明記されている |  |
| 10 | handoff 保持規約（次 handoff 作成まで前 handoff を削除しない）が明記されている |  |
| 11 | issue ファイル連携（`issues/open|processing/[ID].md` 冒頭に進行中 handoff の完全パス記載）が明記されている |  |
| 12 | 各 issue ファイル冒頭ヘッダ（タイトル / 概要 1〜2 行 / 状態 / 最新 handoff 完全パス / 起票日）の標準形式が明記され、handoff 更新時の同期更新ルールがある |  |
| 13 | issues/ 3 段階フォルダ管理（open → processing → closed の git mv 遷移）と問題発見即起票（scope creep 禁止・現タスクで触らない）が独立セクションとして明記されている |  |
| 14 | PC 再起動・session 復元の自動化（SessionStart hook はポインタ + verdict のみ注入＝本文を注入しない、`issues/processing/*.md` 全 scan で User 通知 → 選択後 1 件のみ Read + 並列委任）が明記されている（並走なし小規模では「不要」宣言で可） |  |
| 15 | Step 8 で採用セット（CLAUDE.md + 採用 rules + settings.json hooks + hook scripts）の **実生成手順** が明記され、雛形が示されている |  |
| 16 | 詳細ルールは別ファイルに分離 or リンクのみ |  |
| 17 | 意思決定支援（decision tree / 前提条件表 / ルール参照テーブル）が 1 つ以上ある |  |
| 18 | 「新しい○○を追加する手順」のガバナンスがある |  |
| 19 | emphasis（IMPORTANT / YOU MUST）出現が 5 件以下に絞られている（公式 emphasis ガイダンスに沿う） |  |
| 20 | 進行中タスク・TODO・バージョン番号など陳腐化情報がない |  |
| 21 | 確実に毎回実行したい advisory ルールが hooks 化候補として識別され、settings.json の hooks に登録されている（または該当なしと宣言されている） |  |
| 22 | `meta.md` 末尾「既知の制約」に [claude-code Issue #23478](https://github.com/anthropics/claude-code/issues/23478) が URL 付きで明記され、`@import` 一次防御 + 手動 Read 二次防御の二重防壁の理由が説明されている |  |
| 23 | `governance.md` が肥大化防止の複数観点（サイズ閾値 / 新項目ルーティング / 公式準拠 / 定期レビュー / 自動検証 / 常時 load ファイル cap 等・増減可）を項目立てて記述している |  |
| 24 | `meta.md` / `@import` で常時 load される rules ファイル個別に **5KB soft cap** が宣言されている |  |
| 25 | 関連 docs 読込宣言が**最初と最後の両方**に「完全パス + 1 文要約 + タスク関連性 1 文」を出力する形になっている |  |
| 26 | 条文宣言が **lazy load 運用**（タスク該当条のみ宣言・全条一括宣言は不要）になっている |  |
| 27 | `docs/` 配下に概ね 5 section 以上ある場合は **`docs-management.md`**（docs 配置 mapping / 新 docs 配置 flow / 全 section README 必須化 + 同期更新義務 / 過時マーカー）が生成されている。該当しない小規模プロジェクトでは「不要」と明示宣言されている |  |
| 28 | 複数の実行主体・モデル格を使い分けるプロジェクトでは **`execution-routing.md`**（司令塔 3 責務 + 振り分け表 + 高コスト主体抑制 + escalation）が生成されている。該当しない場合は「不要」と明示宣言されている |  |
| 28b | 28 で `execution-routing.md` を生成した場合、生成 CLAUDE.md 本体の `@import` ブロックに **`@.claude/rules/execution-routing.md` の行が実在する**（テーブルに「常時 load」と書くだけで `@import` 行が抜けている＝名ばかり常時 load になっていないか、生成物を Read して確認する） |  |
| 29 | 並走 agent 痕跡 4 軸 recheck（git log / handoff・plan / worktree / git status の 2 境界実行 + 検出時 action a〜d）が `issue-workflow.md` に明記され、SessionStart hook に **verdict のみ注入**の形で組込まれている（並走なし小規模では「不要」宣言で可） |  |
| 30 | 成果物の生成主体明示（LLM 生成物 vs script/lib 生成物の厳格区別・メタデータ突合）が `test-verify.md` に明記されている |  |
| 31 | close 前検証 4 段（再現→pass / negative test / regression smoke / 証拠アーカイブ）が `test-verify.md` または issue lifecycle に明記されている |  |
| 32 | 別エージェントレビューが 2〜4 本並列 + converged findings 抽出・TDD test-first・ループ上限（計画 3 / 実装 1）で `review.md` に明記され、レビュアに渡すのは**対象完全パス + レビュー用 skill のみ**になっている |  |
| 33 | stale handoff（7 日以上前 / 完了済 / 次 session 不要）を提示時に注記し user が誤選択しないようにする設計が明記されている |  |
| 34 | 公式（best-practices / skills / hooks）の文言・テーブル・数値・API 契約を本プロンプトに焼き込まず、生成・レビュー開始時に WebFetch で取得し現行版で判定する設計（焼き込み版が残っていない） |  |
| 35 | reviewer への過剰報告抑制（reviewer は gap を過剰報告しがち → correctness と明示要件に関わる gap のみ採用）が明記されている |  |
