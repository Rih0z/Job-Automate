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

## JSON の issue（配列の各要素を issue とみなす）の例

```json
{"sources": [{"type": "json_findings", "path": "docs/findings.json", "array": "findings",
              "id": "id", "title": "finding", "status": "status", "closed_values": ["done"]}]}
```

`check-new` は、base（既定 HEAD）と index の id の差で増えた要素に `related`（確かめた関連 id の配列。無ければ `[]`）があるかを見る。`merge` は JSON の要素には使えない（統合先の note に統合元の id と理由を書く）。

## 終了コード

0 正常 / 1 `check-new` で欠けがある / 2 引数・設定・対象が不正（何も変えない）
