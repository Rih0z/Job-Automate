# workflows/content-creation/ — プレゼン資料作成・レビュー

業務ワークフロー「コンテンツ制作」のハーネス。スライド生成とレビューのプロンプト集。

---

## スライド生成

| プロンプト | レビュー | 説明 |
|---|---|---|
| [slides-pro.md](slides-pro.md) | [review-slides.md](review-slides.md) | HTMLスライド自動生成 v4.1 |
| [thumbnail-generation.md](thumbnail-generation.md) | [review-thumbnail.md](review-thumbnail.md) | Gemini等の画像生成AI + Claudeの3ラウンド分業でサムネイル画像を生成(2026-09-04追加) |

### slides-pro.md が何をするか

mdファイル（企画書・資料）を渡すと、**ブラウザで動くHTMLスライドを1ファイルで生成**する。

**生成されるもの**
- 16:9比率の横向きスライド（← → キー・スペースで操作）
- 進捗バー・スライド番号・フルスクリーン（F キー）
- PDF出力ボタン（ブラウザ印刷経由、A4横）

**自動で適用されるルール（v4.1）**
- 1スライドの箇条書きは5項目まで → 超えたらスライドを自動分割
- CSS変数禁止・全要素に色を直接指定 → 文字が消えない
- 最終スライドはサマリー形式（ポイント番号＋参照ページ番号＋Next Action）

### review-slides.md が何をするか

生成済みのスライドHTMLを渡すと、視認性・情報量・構成・最終スライド品質をレビューする。

---

## サムネイル画像生成

### thumbnail-generation.md が何をするか

ブラウザ操作可能な画像生成AI(Gemini等)とClaude Codeの役割分担で、ブログ/動画のサムネイル画像を3ラウンド(土台生成→創造的仕上げ→CTRフック追加+レビュー修正)で生成する。ラウンドごとの新規チャットセッション・ブランド要素参照画像の毎回添付・サーキットブレーカー規則など、実測ベースの運用ノウハウを含む。

### review-thumbnail.md が何をするか

生成済みのサムネイル画像を、整合性(破綻・誤生成・架空要素)とCTR観点の2軸チェックリストでレビューし PASS/REVISE/REGENERATE を判定する。

---

## その他

| ファイル | 説明 |
|---|---|
| [creative.md](creative.md) | クリエイティブ制作 |
| [review-blog.md](review-blog.md) | ブログ記事の11軸レビュー（詳細は [ルートREADME](../../README.md#content-creation--プレゼン資料作成レビュー)） |
| [examples/](examples/) | 実際の活用事例 |

---

[← ワークフロー一覧に戻る](../README.md)
