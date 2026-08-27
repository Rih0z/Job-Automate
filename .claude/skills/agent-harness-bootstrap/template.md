# 出力テンプレート（CLAUDE.md 本体・rules 分離・条文方式）

生成手順 Step 4 で使う。project 固有値を埋める。該当しないセクションは削除可（削除理由を明示する）。**ルール一覧の「含む条」は生成プロジェクト自身の条番号を埋める**（条文に通し番号を振り、ファイル間で重複させないという手法の適用であって、他プロジェクトの固有番号を転記するものではない）。

````markdown
# CLAUDE.md - [プロジェクト名]

> [一行サマリ]

## 起動時手順

1. 関連 docs 読込宣言: 該当 docs を最低 1 つ Read し「完全パス + 1 文要約 + タスク関連性 1 文」を**宣言の最初と最後の両方**に出力する（最初 = 根拠表明、最後 = 実際に踏まえた証跡）
2. 条文宣言（lazy load 運用）: タスク該当ルール（下表）のみ宣言してから着手する。**全条一括宣言は不要**
3. 作業 → 自検証 → 他者レビュー（別エージェント）を作業節目で実施する。CLAUDE.md / skills 更新時は公式準拠を WebFetch ベースでレビュー（skills → レビュー用 skill で 90 点合格／3 回 FAIL で `issues/open/[ID].md` 起票・中断）
4. session 開始時（新規 chat / `/clear` 直後）: handoff は **user 明示指示でのみ受領**（最新を自動 Read しない）。hook が提示するポインタ + 並走 4 軸 verdict を見て、user が再開対象を選んだら**その 1 件のみ本文 Read**（stale = 7 日以上前 / 完了済 / 次 session 不要 は選ばない）。受領後は役割のみ実施・scope creep を避ける
5. handoff 規約: ファイル名 `[YYYY-MM-DD]-issue-[ID]-[識別単語].md`、次 handoff 作成まで保持、`issues/open|processing/[ID].md` 冒頭に進行中 handoff の完全パス記載（詳細 `issue-workflow.md`）

## ルール一覧

`meta.md` は常時 load。下記は CLAUDE.md `@import` で常時 load（path-scope auto-load 不安定への補償）。他は YAML `paths:` で Read 時のみ load:

@.claude/rules/code-quality.md
@.claude/rules/test-verify.md

| タスク種別 | rules | 含む条 |
|-----------|-------|-------|
| コード/ファイル変更 | `code-quality.md` (常時) | [該当条] |
| テスト/Issue close | `test-verify.md` (常時) | [該当条] |
| Issue/.tmp 作業 | `issue-workflow.md` (path-scope) | [該当条] |
| commit 直前/作業節目 | `review.md` (path-scope) | [該当条] |
| CLAUDE.md/.claude 編集 | `governance.md` (path-scope) | [該当条] |

（採用時の追加は load 戦略で扱いが異なる。**`execution-routing.md` を採用した場合**: 上の `@import` ブロックに `@.claude/rules/execution-routing.md` の行を追加**し**、ルール一覧テーブルにも行を追加する（`@import` 忘れは「テーブル上は常時 load と書いてあるが実際は読み込まれない」既知の失敗パターンなので両方必須）。**`docs-management.md` を採用した場合**: テーブルに行を追加するのみ（`@import` 不要、`paths:` で path-scope）。）

## ルート構成

`[entry]` / `[dir1]/` / `[dir2]/` / 一時: `.tmp/` `.history/`（gitignore 推奨）。git 完全追跡の例外: [明記]

## サイズ運用

公式は数値閾値を持たない（"Keep it concise"）。本プロジェクトは概ね 100 行を剪定検討の目安とする。新項目は rules / docs / skills / .tmp に振り分け、CLAUDE.md 直接記入は避ける（詳細 `.claude/rules/governance.md`）。

セットアップ: [quick_start](docs/...) / 検証: [...](docs/...) / ロードマップ: [...](docs/...)

---
*[行数] 行 / [KB] KB*
*[Optional: チーム鼓舞 1 行 — 例: "Ultrathink. Don't hold back. Give it your all!"]*
````
