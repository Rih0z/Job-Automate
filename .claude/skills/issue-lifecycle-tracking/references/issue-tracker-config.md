# `.claude/issue-tracker.json` の書き方

`scripts/issue_tracker.py` の設定。相対パスは `.claude/` の親（repo のルート）が基準。`--config` を省くと、実行した場所から上へ `.claude/issue-tracker.json` を探す。

## md の issue（この skill の `issues/open → processing → closed` 運用）の例

```json
{
  "sources": [
    {"type": "md_dirs", "root": "issues",
     "active": ["open", "processing", "pending"], "closed": ["closed"],
     "merged_dir": "withdrawn", "merged_state": "withdrawn",
     "status_line": {"regex": "^status:\\s*\\S+", "template": "status: {state}"},
     "exclude": ["README.md", "_TEMPLATE*.md", "_evidence/**"],
     "index_files": ["issues/README.md"]}
  ],
  "related_field": "関連:"
}
```

| 項目 | 意味 |
|---|---|
| `root` | issue のディレクトリ |
| `active` / `closed` | 状態ディレクトリの名前。issue はその直下の `.md`。`related` は既定で `active` だけを見る（`--include-closed` で `closed` と `merged_dir` も） |
| `merged_dir` | `merge` で統合元を移す先。無い source では `merge` を拒否する（exit 2）。統合済みを closed に置く運用なら `"closed"` |
| `merged_state` | 統合元の状態欄に書く値（例: `withdrawn`、`closed（統合）`）。無ければ `merged_dir` の名前 |
| `status_line` | 本文の状態欄の正規表現と、書き換える形（`{state}` に状態が入る）。無ければ状態欄を書き換えない |
| `exclude` | issue とみなさない file。`*` は file 名、`<名前>/**` はそのディレクトリの下 |
| `index_files` | 移動の後に更新が要る索引。一覧に出すだけで書き換えない |
| `related_field` | 新規の issue に求める欄の名前（既定 `関連:`） |
| `created`（任意） | 起票日の frontmatter の行名（既定 `created`）。`triage` が「確認が古い」を測る時、`reviewed` が無ければこれを使う |

## JSON の issue（配列の各要素を issue とみなす）の例

```json
{"sources": [{"type": "json_findings", "path": "docs/findings.json", "array": "findings",
              "id": "id", "title": "finding", "status": "status", "closed_values": ["done"]}]}
```

任意の `created` は起票日のキー名（既定 `created`。例えば `"created": "date"`）。終端に `obsolete` を使うなら `closed_values` に入れる。

`triage` は JSON の要素の `priority`・`reviewed`・`premise`（`[{"path", "contains"?}]`、path はリポジトリ相対か `~/` 始まり）・`related` を読む。md の issue は `premise` を読まず、本文に backtick で書いたパスを見る。

`check-new` は、base（既定 HEAD）と index の id の差で増えた要素に `related`（確かめた関連 id の配列。無ければ `[]`）があるかを見る。`merge` は JSON の要素には使えない（統合先の note に統合元の id と理由を書く）。

## 終了コード

0 正常 / 1 `check-new` で欠けがある / 2 引数・設定・対象が不正（何も変えない。例外は `merge` の「統合済みだが統合元が残った」で、統合先と移動先は書き終えている。統合元を手で消し、git で追跡していれば手で stage する）

## `triage` の出力例

```
## 優先度順
P1  Low  2026-11-11  CR-50  release の closed 判定が 2 段しか認めない
-  -  2026-10-02  CR-9  （priority・severity が無い時は -）

## 前提が崩れた候補
CR-40  .claude/skills/_shared/compliance-status.json#CR-40  前提の文言が無い: ~/CLAUDE.md

## 確認が古い
（なし）

## 欄の欠け
CR-9  .claude/skills/_shared/compliance-status.json#CR-9  priority, 関連

## 重複の候補
0.83  CR-9  CR-10
```

各節は 0 件なら「（なし）」。`--json` は同じ内容を `order` / `premise_broken` / `stale` / `missing` / `duplicates` のキーで出す。
