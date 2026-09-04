# 自己評価ルーブリック（36 項目）

生成手順 Step 5 で使う。各項目を Y/N 評価する。N が 1 つでも残れば書き直して再評価する。「削除したら Claude が間違えるか」の基準に合格しない行は削る。**採用しなかった要素は、対象の `harness-selection.json` に `selected: false`（`decided_by: "scale"` または `"user"`）で記録済みであれば Y**（口頭・報告文だけの「不要宣言」では Y にしない。記録に載らない除外を作らないため）。Step 7 の別エージェントレビューでも本 36 項目全 Y を合格基準に含める（Step 5 と Step 7 で同一基準）。

**要素 id 列と opt-out**: 各項目は `provenance.json` の要素 id に紐づく。Step 0（`selection-flow.md`）で対象の `harness-selection.json` に記録された選択だけを根拠に判定する:

- id 列の**全要素**が `selected: false` の項目 → 「opt-out 宣言済み」として **Y 扱い**（生成物にその要素が存在しないことが正しい状態）
- id 列に**選択済みの要素が 1 つでもある**項目 → 選択された id の観点で Y/N を判定する（例: 項目 18 で `governance-multi-aspect` が非選択でも `official-claude-md-core` は選択済みなので、「新しい○○を追加する手順」が CLAUDE.md 本体に残っているかを判定する）
- `selected: false` の要素が生成物に現れていれば、対応する項目は N（混入）
- `harness-selection.json` が無い生成では opt-out を認めず、全項目を検査する

id 列と台帳の整合（双方向）は `scripts/provenance-check.sh` で機械検査する。

| # | 項目 | 要素 id | Y/N |
|---|------|--------|-----|
| 1 | 各行が「削除したら Claude が間違えるか」の基準に合格（消したら Claude がミスする行のみ残っている）。行数による硬性ゲートはなし | official-claude-md-core / no-line-count-gate |  |
| 2 | プロジェクト固有の事実のみ（一般論ゼロ） | official-claude-md-core |  |
| 3 | 全コマンド・全パスが実在（推測ゼロ・捏造ゼロ） | official-claude-md-core |  |
| 4 | ルート構成 1 行サマリがある | official-claude-md-core |  |
| 5 | デフォルトと異なるコード規約・テスト方針が `code-quality.md` / `test-verify.md` に記載されている | rules-split-progressive-disclosure / generic-discipline-menu |  |
| 6 | 環境依存の注意点・既知の落とし穴（Step 1 で収集した「環境変数・OS 依存・既知の落とし穴」）が rules 本文に記載されている（新規プロジェクトで該当事実がなければ省略可） | rules-split-progressive-disclosure |  |
| 7 | 別エージェントレビューサイクルが `review.md` に記載されている | separate-agent-review-cycle / official-adversarial-review |  |
| 8 | handoff は user 明示指示で受領し本文は選択 1 件のみ Read（最新を自動 Read しない）運用が `issue-workflow.md` に明記されている | handoff-management |  |
| 9 | handoff 命名規約（`[YYYY-MM-DD]-issue-[ID]-[識別単語].md`、識別単語は 2〜4 語 kebab-case）が明記されている | handoff-management |  |
| 10 | handoff 保持規約（次 handoff 作成まで前 handoff を削除しない）が明記されている | handoff-management |  |
| 11 | issue ファイル連携（`issues/open\|processing/[ID].md` 冒頭に進行中 handoff の完全パス記載）が明記されている | issue-lifecycle |  |
| 12 | 各 issue ファイル冒頭ヘッダ（タイトル / 概要 1〜2 行 / 状態 / 最新 handoff 完全パス / 起票日）の標準形式が明記され、handoff 更新時の同期更新ルールがある | issue-lifecycle |  |
| 13 | issues/ 3 段階（または pending 検証バッファを挟む 4 段階・採用判定は該当条件に基づく）のフォルダ管理（git mv 遷移）と問題発見即起票（scope creep 禁止・現タスクで触らない）が独立セクションとして明記されている | issue-lifecycle |  |
| 14 | PC 再起動・session 復元の自動化（SessionStart hook はポインタ + verdict のみ注入＝本文を注入しない、`issues/processing/*.md` 全 scan で User 通知 → 選択後 1 件のみ Read + 並列委任）が明記されている（並走なし小規模では `selected: false, decided_by: "scale"` の記録で opt-out 可） | session-restore-hook |  |
| 15 | Step 8 で採用セット（CLAUDE.md + 採用 rules + settings.json hooks + hook scripts）の **実生成手順** が明記され、雛形が示されている | rules-split-progressive-disclosure |  |
| 16 | 詳細ルールは別ファイルに分離 or リンクのみ | official-claude-md-core / official-skills-core |  |
| 17 | 意思決定支援（decision tree / 前提条件表 / ルール参照テーブル）が 1 つ以上ある | official-claude-md-core |  |
| 18 | 「新しい○○を追加する手順」のガバナンスがある | official-claude-md-core / governance-multi-aspect / claude-md-add-before-check |  |
| 19 | emphasis（IMPORTANT / YOU MUST）出現が 5 件以下に絞られている（公式 emphasis ガイダンスに沿う） | emphasis-cap-5 |  |
| 20 | 進行中タスク・TODO・バージョン番号など陳腐化情報がない | official-claude-md-core |  |
| 21 | 確実に毎回実行したい advisory ルールが hooks 化候補として識別され、settings.json の hooks に登録されている（または該当なしと宣言されている） | hooks-promotion-judgement |  |
| 22 | `meta.md` 末尾「既知の制約」に [claude-code Issue #23478](https://github.com/anthropics/claude-code/issues/23478) が URL 付きで明記され、`@import` 一次防御 + 手動 Read 二次防御の二重防壁の理由が説明されている | rules-split-progressive-disclosure |  |
| 23 | `governance.md` が肥大化防止の複数観点（サイズ閾値 / 新項目ルーティング / 公式準拠 / 定期レビュー / 自動検証 / 常時 load ファイル cap 等・増減可）を項目立てて記述している | governance-multi-aspect |  |
| 24 | `meta.md` / `@import` で常時 load される rules ファイル個別に **5KB soft cap** が宣言されている | always-load-5kb-cap |  |
| 25 | 関連 docs 読込宣言が**最初と最後の両方**に「完全パス + 1 文要約 + タスク関連性 1 文」を出力する形になっている | docs-read-declaration |  |
| 26 | 条文宣言が **lazy load 運用**（タスク該当条のみ宣言・全条一括宣言は不要）になっている | lazy-rule-declaration |  |
| 27 | `docs/` 配下に概ね 5 section 以上ある場合は **`docs-management.md`**（docs 配置 mapping / 新 docs 配置 flow / 全 section README 必須化 + 同期更新義務 / 過時マーカー）が生成されている。該当しない小規模プロジェクトでは `selected: false, decided_by: "scale"` で記録されている | docs-management |  |
| 28 | 複数の実行主体・モデル格を使い分けるプロジェクトでは **`execution-routing.md`**（司令塔 3 責務 + 振り分け表 + 高コスト主体抑制 + escalation）が生成されている。該当しない場合は `selected: false, decided_by: "scale"` で記録されている | execution-routing |  |
| 28b | 28 で `execution-routing.md` を生成した場合、生成 CLAUDE.md 本体の `@import` ブロックに **`@.claude/rules/execution-routing.md` の行が実在する**（テーブルに「常時 load」と書くだけで `@import` 行が抜けている＝名ばかり常時 load になっていないか、生成物を Read して確認する） | execution-routing |  |
| 29 | 並走 agent 痕跡 4 軸 recheck（git log / handoff・plan / worktree / git status の 2 境界実行 + 検出時 action a〜d）が `issue-workflow.md` に明記され、SessionStart hook に **verdict のみ注入**の形で組込まれている（並走なし小規模では `selected: false, decided_by: "scale"` の記録で opt-out 可） | concurrent-agent-4-axis-recheck |  |
| 30 | 成果物の生成主体明示（LLM 生成物 vs script/lib 生成物の厳格区別・メタデータ突合）が `test-verify.md` に明記されている | artifact-generator-attribution |  |
| 31 | close 前検証 4 段（再現→pass / negative test / regression smoke / 証拠アーカイブ）が `test-verify.md` または issue lifecycle に明記されている | close-verification-4-steps |  |
| 32 | 別エージェントレビューが 2〜4 本並列 + converged findings 抽出・TDD test-first・ループ上限（計画 3 / 実装 1）で `review.md` に明記され、レビュアに渡すのは**対象完全パス + レビュー用 skill のみ**になっている | review-cycle-parameters / separate-agent-review-cycle |  |
| 33 | stale handoff（7 日以上前 / 完了済 / 次 session 不要）を提示時に注記し user が誤選択しないようにする設計が明記されている | handoff-management |  |
| 34 | 公式（best-practices / skills / hooks）の文言・テーブル・数値・API 契約を本プロンプトに焼き込まず、`_shared/anthropic-best-practices.json`（取得日 `fetched` + `refetch_when` 付き）を参照し、該当時は WebFetch で現行版と突合する設計（日付・再取得条件の無い転記が残っていない） | shared-anthropic-best-practices |  |
| 35 | reviewer への過剰報告抑制（reviewer は gap を過剰報告しがち → correctness と明示要件に関わる gap のみ採用）が明記されている | official-adversarial-review |  |
| 36 | `test-verify.md` に数値目標の単一 SoT 化条文（閾値は強制する設定ファイルのみを SoT とし prose に重複記載しない。カバレッジ%が無い場合は合格率等に読み替え）があり、生成 CLAUDE.md / rules の prose に閾値の重複記載が無い | numeric-target-single-sot |  |
