# 独自運用ノウハウの索引

SKILL.md から分離した索引。各項目の詳細本文は `operational-knowhow.md`、hooks 化判断は `hooks-reference.md`。

## 目次

- 導入注記
- 項目一覧（規模調整・サイズ・標準セット・routing・宣言・governance・handoff・並走 recheck・issue・hooks 化・品質基準・マルチエージェント・レビューサイクル・収束型自律前進・生成主体明示）

---

> 公式には記述がない本スキルの設計判断。プロジェクトに合わせて緩めてよい。詳細本文は `operational-knowhow.md` を参照（各項目名で検索可）。各項目の由来は `provenance.json` に登録済みで、`official-derived`（公式原則の具体化・推奨）と `author-preference`（著者の運用嗜好・**デフォルト非採用**）に分かれる。author-preference の項目は、別プロジェクトへの適用時に Step 0 でユーザーが選んだ場合のみ生成する:

- **規模に応じたスケール調整** — 標準セットは上限像。該当する条文・確実に毎回実行したい規律・採用判定を通ったオプションファイルだけ生成する
- **サイズの目安** — 公式目標（memory docs の Size 記述）に加え、著者の目安として CLAUDE.md 本体 100 行 / 10KB で剪定検討、常時 load rules は個別 5KB soft cap（数値は参考値、"rules getting lost in the noise" 兆候も合わせて見る）
- **標準セット構成** — `CLAUDE.md` 本体 + `.claude/rules/*.md`（公式原則由来のコア + Step 0 の選択に依存する author-preference 由来のファイル）+ hooks。load 戦略（`paths:` 無し = 起動時に常時 load、`paths:` 付き = 一致ファイルの Read 時に load する公式仕様。`@import` による二重指定はしない）
- **実行主体・モデル格の振り分け規約**（`execution-routing.md`）— 司令塔の 3 責務・振り分け表・高コスト主体抑制・escalation protocol
- **関連 docs 読込宣言** — タスク開始時に関連 docs を読み、宣言の最初と最後の両方に証跡を出力
- **条文宣言の lazy load 運用** — 該当条のみ宣言、全条一括宣言はしない
- **governance.md の項目群** — サイズ閾値・新項目ルーティング・公式準拠・定期レビュー・自動検証・常時 load cap・新条文追加手順（5 段チェックリスト）・advisory→hook 昇格判断（zero-exception 語気の条文は hook 化候補か判定）
- **handoff 受領** — user 明示指示でのみ受領、本文は自動 Read しない。stale 誤受領防止・archive ローテーション
- **並走 agent 痕跡 4 軸 recheck** — session 開始時 / plan 起票前に commit・handoff/plan・worktree・uncommitted Edit の 4 軸を確認
- **issue ライフサイクル管理**（open → processing → closed）— close 前検証 4 段、問題発見即起票ルール、1 issue = 1 目的
- **PC 再起動・session 復元の自動化** — SessionStart hook でポインタのみ通知、本文 Read は user 選択後
- **handoff 管理** — 命名規約・保持・issue 連携
- **規約の hooks 化判断** — advisory → deterministic 昇格の判断基準（詳細は `hooks-reference.md`）
- **自作 skill / MCP ツールの品質基準の継承**（該当時のみ）— 対象プロジェクトが独自 skill / MCP ツールを新規作成する場合、`skill-authoring-guide`（few-shot 設計・決定的強制・個人カスタマイズ）/ `mcp-server-setup`（構造化エラー応答設計）の観点をレビュー基準に含める
- **マルチエージェント/subagent 設計原則**（該当時のみ）— クラッシュ耐性 state manifest・コーディネーター中継のメタデータ保持・ツールスコープの限定（`agent-design.md`）。レビュー時の実装コンテキスト遮断・並列アンカリングは別エージェントレビューサイクル（`review.md`）側に属し重複させない
- **別エージェントレビューサイクル** — 対象完全パス + レビュー用 skill のみ渡す、並列本数・TDD test-first・ループ上限・自己レビュー不可・過剰報告の抑制
- **収束型自律前進**（オプション）— 独立レビュー 2 本以上収束後は user 確認を待たず進行可。6 類の例外は必須確認
- **成果物の生成主体明示** — LLM 生成物 vs script/lib 生成物を厳格に区別
