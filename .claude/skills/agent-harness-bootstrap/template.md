# 出力テンプレート（CLAUDE.md 本体・rules 分離・条文方式）

生成手順 Step 4 で使う。project 固有値を埋める。該当しないセクションは削除可（削除理由を明示する）。**ルール一覧の「含む条」は生成プロジェクト自身の条番号を埋める**（条文に通し番号を振り、ファイル間で重複させないという手法の適用であって、他プロジェクトの固有番号を転記するものではない）。

**`<!-- id: ... -->` マーカー**: 各ブロックに `provenance.json` の要素 id を付けている。Step 0 で `selected: false` になった要素のブロックは**削除**し、残すブロックからもマーカー自体は削除する（生成 CLAUDE.md にマーカーを残さない）。マーカーが複数 id を持つ行は、非選択 id に対応する断片だけを削る。断片と id の対応:

| 行 | 断片 | 要素 id | 非選択時の扱い |
|---|---|---|---|
| 起動時手順 3 | 「作業 → 自検証 → 他者レビュー（別エージェント）」 | separate-agent-review-cycle | 「作業 → 自検証」のみ残す |
| 起動時手順 3 | 「CLAUDE.md / skills 更新時は公式準拠を WebFetch ベースでレビュー」 | official-adversarial-review | （official・常に残る） |
| 起動時手順 3 | 「90 点合格／3 回 FAIL で…中断」 | review-cycle-parameters | 削除し「不合格なら修正して再レビュー」のみ残す |
| 起動時手順 3 | 「`issues/open/[ID].md` 起票」 | issue-lifecycle | 「ユーザーに報告して中断」に置換 |
| 起動時手順 4 | 「handoff は user 明示指示でのみ受領…stale…受領後は役割のみ実施」 | handoff-management | 行ごと削除（session-restore-hook / 4 軸 recheck も handoff に依存） |
| 起動時手順 4 | 「hook が提示するポインタ」 | session-restore-hook | 「`.tmp/handoffs/` を自分で ls して」に置換 |
| 起動時手順 4 | 「並走 4 軸 verdict」 | concurrent-agent-4-axis-recheck | 語句を削除 |
| 起動時手順 5 | 「`issues/open\|processing/[ID].md` 冒頭に…」「`issue-[ID]-`」 | issue-lifecycle | 命名を `[YYYY-MM-DD]-[識別単語].md` に、issue 連携の句を削除 |
| ルール一覧 | `governance.md` 行 | governance-multi-aspect | 行を削除し、代わりに official 由来の「新しい○○を追加する手順」（rubric 18）を CLAUDE.md 本体に 2〜3 行の節として残す |
| サイズ運用 | 「概ね 100 行を剪定検討の目安」 | size-guideline-100-lines | 「公式は数値閾値を持たない。新項目は rules / docs / skills に振り分ける」のみ残す |

````markdown
# CLAUDE.md - [プロジェクト名]

> [一行サマリ]

## 起動時手順

<!-- id: docs-read-declaration -->
1. 関連 docs 読込宣言: 該当 docs を最低 1 つ Read し「完全パス + 1 文要約 + タスク関連性 1 文」を**宣言の最初と最後の両方**に出力する（最初 = 根拠表明、最後 = 実際に踏まえた証跡）
<!-- id: lazy-rule-declaration -->
2. 条文宣言（lazy load 運用）: タスク該当ルール（下表）のみ宣言してから着手する。**全条一括宣言は不要**
<!-- id: separate-agent-review-cycle / official-adversarial-review / review-cycle-parameters / issue-lifecycle -->
3. 作業 → 自検証 → 他者レビュー（別エージェント）を作業節目で実施する。CLAUDE.md / skills 更新時は公式準拠を WebFetch ベースでレビュー（skills → レビュー用 skill で 90 点合格／3 回 FAIL で `issues/open/[ID].md` 起票・中断）
<!-- id: handoff-management / session-restore-hook / concurrent-agent-4-axis-recheck -->
4. session 開始時（新規 chat / `/clear` 直後）: handoff は **user 明示指示でのみ受領**（最新を自動 Read しない）。hook が提示するポインタ + 並走 4 軸 verdict を見て、user が再開対象を選んだら**その 1 件のみ本文 Read**（stale = 7 日以上前 / 完了済 / 次 session 不要 は選ばない）。受領後は役割のみ実施・scope creep を避ける
<!-- id: handoff-management / issue-lifecycle -->
5. handoff 規約: ファイル名 `[YYYY-MM-DD]-issue-[ID]-[識別単語].md`、次 handoff 作成まで保持、`issues/open|processing/[ID].md` 冒頭に進行中 handoff の完全パス記載（詳細 `issue-workflow.md`）

<!-- id: rules-split-progressive-disclosure -->
## ルール一覧

`meta.md` は常時 load。下記は CLAUDE.md `@import` で常時 load（path-scope auto-load 不安定への補償）。他は YAML `paths:` で Read 時のみ load:

@.claude/rules/code-quality.md
@.claude/rules/test-verify.md

| タスク種別 | rules | 含む条 |
|-----------|-------|-------|
| コード/ファイル変更 | `code-quality.md` (常時) | [該当条] |
| テスト/Issue close | `test-verify.md` (常時) | [該当条] |
<!-- id: issue-lifecycle / handoff-management -->
| Issue/.tmp 作業 | `issue-workflow.md` (path-scope) | [該当条] |
<!-- id: separate-agent-review-cycle -->
| commit 直前/作業節目 | `review.md` (path-scope) | [該当条] |
<!-- id: governance-multi-aspect -->
| CLAUDE.md/.claude 編集 | `governance.md` (path-scope) | [該当条] |

<!-- id: execution-routing / docs-management -->
（採用時の追加は load 戦略で扱いが異なる。**`execution-routing.md` を採用した場合**: 上の `@import` ブロックに `@.claude/rules/execution-routing.md` の行を追加**し**、ルール一覧テーブルにも行を追加する（`@import` 忘れは「テーブル上は常時 load と書いてあるが実際は読み込まれない」既知の失敗パターンなので両方必須）。**`docs-management.md` を採用した場合**: テーブルに行を追加するのみ（`@import` 不要、`paths:` で path-scope）。）

<!-- id: official-claude-md-core -->
## ルート構成

`[entry]` / `[dir1]/` / `[dir2]/` / 一時: `.tmp/` `.history/`（gitignore 推奨）/ 移植元 clone: `.setup-automate/`（gitignore・再同期用）。git 完全追跡の例外: [明記]

<!-- id: size-guideline-100-lines / governance-multi-aspect -->
## サイズ運用

公式は数値閾値を持たない（"Keep it concise"）。本プロジェクトは概ね 100 行を剪定検討の目安とする。新項目は rules / docs / skills / .tmp に振り分け、CLAUDE.md 直接記入は避ける（詳細 `.claude/rules/governance.md`）。

セットアップ: [quick_start](docs/...) / 検証: [...](docs/...) / ロードマップ: [...](docs/...)

---
*[行数] 行 / [KB] KB*
*[Optional: チーム鼓舞 1 行 — 例: "Ultrathink. Don't hold back. Give it your all!"]*
````
