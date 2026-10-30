# slide-sources — スライドのベストプラクティスの取得ログ

`../slide-best-practices.json` の各 practice が引く出典を、いつ・どの手段で取得し、原文のどの部分を抜粋したかの記録。

## ファイル

| ファイル | 内容 |
|---|---|
| `fetch-log.json` | 出典ごとの取得記録。`source_id` / `url` / `fetched_on` / `method`（`raw-http` のみ）/ `sha256`（取得した本文のバイト列のハッシュ）/ `excerpts[]`（本文から逐語コピーした抜粋） |
| `<source_id>.html`（コミットしない） | 取得した本文の保存先。リポジトリ直下 `.tmp/slide-sources/` に置く。再照合の時だけ必要 |

## 出典の扱い

- `verification: fetched` の出典は、`curl` で取得した**生の HTTP 本文**から抜粋する。要約を返す取得手段（WebFetch など）の出力は証拠にしない（逐語を保証しないため）。
- 本文が取れない出典（403・本文が JS 描画）や、書籍・論文の本文は `fetched` にしない。`secondary` とし、`severity: must` の根拠には使わない。
- `year` が `n.d.` の出典は、ページから発行年を確認できなかったもの。推測で埋めない。
- 取得日（`checked_on`）から `max_age_days` を過ぎた出典は、検査が `stale source` の警告を出す。再取得して抜粋を確認し直す。

## 検査と再照合

```
python .claude/skills/_shared/scripts/validate_slide_data.py practices .claude/skills/_shared/slide-best-practices.json \
  --fetch-log .claude/skills/_shared/slide-sources/fetch-log.json --sources-dir .tmp/slide-sources
```

`--sources-dir` を付けると、保存本文の sha256 の再計算と、各抜粋が本文（タグ除去・実体参照の展開・空白の畳み込み後）に含まれることの確認まで行う。保存本文が無い環境では `--fetch-log` までの構造検査になる。

## 更新の手順

1. `curl -sL -A "Mozilla/5.0 (compatible; research-fetch)" -o .tmp/slide-sources/<source_id>.html <url>` で取得する。
2. 本文から抜粋を逐語コピーし、`slide-best-practices.json` の `evidence[].quote` と `fetch-log.json` の `excerpts[]` に同じ文字列を入れる。`sha256` と `fetched_on` を更新する。
3. 上の検査コマンドを通す。
4. 出典の主張を実際より強く書いていないか（`rule` / `rationale` / `adaptation`）、別エージェントに抜粋と本文を突き合わせさせる。
