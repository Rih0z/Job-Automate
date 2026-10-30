# 出力 HTML の完全テンプレートと機械検証

この文書と SKILL.md だけで、他のリポジトリでもスライド HTML を生成・検証できる。色は直接カラーコードで書き、CSS 変数は使わない。

目次
- 出力ファイルの構造
- スライド種別ごとの HTML 断片
- 完全な HTML テンプレート
- 機械検証(実行コマンドと期待結果)
- 不合格時の扱い

## 出力ファイルの構造

単一 HTML ファイル。上から次の順で構成する。

| 部位 | 要素 | 内容 |
|---|---|---|
| ヘッド | `<style>` | 16:9 の `.slide`、`.slide-content`(`overflow-y: auto`)、`.progress`、`.nav`、`@media print` |
| 進捗バー | `.progress > .bar` | 現在位置を幅 % で更新 |
| スライド群 | `section.slide` を 1 枚ずつ | タイトル → 本文スライド(複数) → 最終サマリー |
| 操作部 | `.nav` | 前へ/次へボタン、スライド番号、PDF 出力ボタン(`window.print()`) |
| スクリプト | `PresentationManager` クラス | ← → キー、タッチのスワイプ、進捗バー更新、番号表示 |

## スライド種別ごとの HTML 断片

- タイトルスライド: `section.slide.title-slide` に h1(48px・文字色 `#ffffff`・背景は濃色)、サブタイトル、作成日
- 本文スライド: `section.slide` に h2(26px)と `.slide-content`。箇条書きは `ul` のトップレベル 5 項目以内(ネスト含め 10 項目以内)、表は 6 行以内、カードは 4 枚以内(`.card`)、段落は 3 段落計 150 文字以内
- 最終サマリー: `section.slide.summary-slide` に重要ポイント 3〜5 個。各項目は `.summary-point`(本文)と `.summary-page`(`p.X` の参照ページ)を持つ。Next Action があれば `.next-action` に書く(文字色 `#ffffff`、背景は濃色)

フォントサイズ: h1 36px(タイトルは 48px)、h2 26px、h3 20px、本文 20px、補足 16px。

## 完全な HTML テンプレート

下のテンプレートを丸ごと使い、本文スライドの `section` を企画書の内容に応じて増減する。タグは 1 要素ずつ書き、機械検証の件数集計が成り立つようにする(`<li` や `<tr` を同じ行に詰めて数を隠さない)。

```html
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>スライドの題名</title>
<style>
  * { box-sizing: border-box; }
  body { margin: 0; background: #222222; font-family: "Hiragino Sans", "Yu Gothic", Meiryo, sans-serif; }
  .deck { width: 100vw; height: 100vh; display: flex; align-items: center; justify-content: center; }
  .slide { display: none; position: relative; width: min(100vw, 177.78vh); height: min(56.25vw, 100vh); padding: 40px 56px; background: #ffffff; color: #222222; overflow: hidden; }
  .slide.active { display: block; }
  .slide h1 { font-size: 36px; color: #1a3a6b; margin: 0 0 16px; }
  .slide h2 { font-size: 26px; color: #1a3a6b; margin: 0 0 16px; border-bottom: 3px solid #1a3a6b; padding-bottom: 8px; }
  .slide h3 { font-size: 20px; color: #1a3a6b; margin: 12px 0 8px; }
  .slide p { font-size: 20px; color: #222222; line-height: 1.6; margin: 8px 0; }
  .slide li { font-size: 20px; color: #222222; line-height: 1.6; }
  .slide .note { font-size: 16px; color: #444444; }
  .slide-content { overflow-y: auto; max-height: calc(100% - 80px); color: #222222; font-size: 20px; }
  .slide-content::-webkit-scrollbar { width: 10px; }
  .slide-content::-webkit-scrollbar-thumb { background: #888888; border-radius: 5px; }
  table { border-collapse: collapse; width: 100%; }
  th { background: #1a3a6b; color: #ffffff; font-size: 18px; padding: 8px; text-align: left; }
  td { background: #f2f5fa; color: #222222; font-size: 18px; padding: 8px; border-bottom: 1px solid #cccccc; }
  .cards { display: flex; flex-wrap: wrap; gap: 16px; }
  .card { flex: 1 1 40%; background: #f2f5fa; color: #222222; border-left: 6px solid #1a3a6b; padding: 12px 16px; }
  .card h3 { margin-top: 0; color: #1a3a6b; }
  .card p { color: #222222; font-size: 18px; }
  .title-slide { background: #1a3a6b; color: #ffffff; display: none; }
  .title-slide.active { display: flex; flex-direction: column; justify-content: center; }
  .title-slide h1 { font-size: 48px; color: #ffffff; }
  .title-slide p { color: #ffffff; }
  .cta { background: #1a3a6b; padding: 16px 24px; margin-top: 16px; }
  .cta p { color: #ffffff; }
  .summary-slide .summary-point { color: #222222; font-size: 20px; margin: 10px 0; }
  .summary-slide .summary-page { color: #1a3a6b; font-size: 16px; font-weight: bold; margin-left: 8px; }
  .summary-slide .next-action { background: #1a3a6b; padding: 12px 20px; margin-top: 16px; }
  .summary-slide .next-action p { color: #ffffff; }
  .progress { position: fixed; top: 0; left: 0; height: 4px; width: 100%; background: #cccccc; z-index: 10; }
  .progress .bar { height: 4px; width: 0; background: #1a3a6b; }
  .nav { position: fixed; bottom: 8px; right: 12px; z-index: 10; background: #1a3a6b; padding: 6px 10px; }
  .nav span { color: #ffffff; font-size: 16px; margin: 0 8px; }
  .nav button { font-size: 16px; color: #1a3a6b; background: #ffffff; border: 0; padding: 4px 10px; cursor: pointer; }
  @media print {
    body { background: #ffffff; }
    .deck { display: block; height: auto; }
    .slide { display: block; width: 100%; height: 100vh; page-break-after: always; }
    .title-slide { display: flex; }
    .nav, .progress { display: none; }
    .slide-content { overflow: visible; max-height: none; }
  }
</style>
</head>
<body>
<div class="progress"><div class="bar"></div></div>
<div class="deck">
<section class="slide title-slide active">
  <h1>題名</h1>
  <p>サブタイトル</p>
  <p class="note" style="color:#ffffff">2026年1月1日</p>
</section>
<section class="slide">
  <h2>見出し</h2>
  <div class="slide-content">
    <ul>
      <li>項目 1</li>
      <li>項目 2</li>
    </ul>
  </div>
</section>
<section class="slide">
  <h2>表とカードの例</h2>
  <div class="slide-content">
    <table>
      <tr>
        <th>項目</th>
        <th>内容</th>
      </tr>
      <tr>
        <td>A</td>
        <td>説明</td>
      </tr>
    </table>
    <div class="cards">
      <div class="card">
        <h3>カード見出し</h3>
        <p>カード本文</p>
      </div>
    </div>
    <div class="cta">
      <p>呼びかけの一文</p>
    </div>
  </div>
</section>
<section class="slide summary-slide">
  <h2>まとめ</h2>
  <div class="slide-content">
    <p class="summary-point">要点 1<span class="summary-page">p.2</span></p>
    <p class="summary-point">要点 2<span class="summary-page">p.3</span></p>
    <p class="summary-point">要点 3<span class="summary-page">p.3</span></p>
    <div class="next-action">
      <p>Next Action: 次にやること</p>
    </div>
  </div>
</section>
</div>
<div class="nav">
  <button onclick="pm.go(-1)">前へ</button>
  <span id="num"></span>
  <button onclick="pm.go(1)">次へ</button>
  <button onclick="window.print()">PDF出力</button>
</div>
<script>
class PresentationManager {
  constructor() {
    this.slides = Array.from(document.querySelectorAll('.slide'));
    this.index = 0;
    this.show();
    document.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowRight') this.go(1);
      if (e.key === 'ArrowLeft') this.go(-1);
    });
    let startX = 0;
    document.addEventListener('touchstart', (e) => { startX = e.touches[0].clientX; });
    document.addEventListener('touchend', (e) => {
      const dx = e.changedTouches[0].clientX - startX;
      if (Math.abs(dx) > 50) this.go(dx < 0 ? 1 : -1);
    });
  }
  go(n) {
    this.index = Math.min(this.slides.length - 1, Math.max(0, this.index + n));
    this.show();
  }
  show() {
    this.slides.forEach((el, k) => el.classList.toggle('active', k === this.index));
    document.querySelector('.bar').style.width = ((this.index + 1) / this.slides.length * 100) + '%';
    document.getElementById('num').textContent = (this.index + 1) + ' / ' + this.slides.length;
  }
}
const pm = new PresentationManager();
</script>
</body>
</html>
```

## 機械検証(実行コマンドと期待結果)

生成した HTML のパスを `F` に入れて、次を実行する(bash 系シェル。Windows では Git Bash か WSL)。目視確認だけで合格にしない。

```bash
F="生成した HTML のパス"
grep -c 'var(--' "$F"                                   # 期待: 0 (CSS 変数なし。未定義参照の検出を兼ねる)
grep -ciE 'color:[[:space:]]*white' "$F"                # 期待: 0 (white 表記なし。#ffffff を使う)
grep -c 'class="slide summary-slide' "$F"               # 期待: 1 (最終サマリーが 1 枚)
grep -c 'class="summary-page"' "$F"                     # 期待: 3 以上 5 以下 (参照ページ付きの要点)
grep -ciE 'thank you|ご清聴' "$F"                        # 期待: 0 (Thank You で終わらせない)
grep -c 'overflow-y:[[:space:]]*auto' "$F"              # 期待: 1 以上 (スクロール有効)
grep -c 'class PresentationManager' "$F"                # 期待: 1
grep -c 'window.print' "$F"                             # 期待: 1 以上 (PDF 出力ボタン)
grep -c 'ArrowRight' "$F"                               # 期待: 1 以上 (キー操作)
awk 'BEGIN{RS="</section>"} { if (gsub(/<li/,"&") > 10) print "li 超過: スライド " NR }' "$F"   # 期待: 出力なし (li は 1 枚 10 個以内)
awk 'BEGIN{RS="</section>"} { if (gsub(/<tr/,"&") > 7) print "tr 超過: スライド " NR }' "$F"   # 期待: 出力なし (見出し行 + 6 行以内)
awk 'BEGIN{RS="</section>"} { if (gsub(/class="card"/,"&") > 4) print "card 超過: スライド " NR }' "$F"   # 期待: 出力なし
```

- 期待結果と異なるコマンドが 1 つでもあれば不合格。トップレベル 5 項目以内・段落 150 文字以内・コントラスト 4.5:1 以上は件数集計できないため、SKILL.md の品質チェックリストで目視確認する(上のコマンドは目視の代わりではなく、目視の前に落とすための足切り)。
- grep や awk が使えない環境では、同じ検索語で編集エディタの検索を使い、結果を完了報告に書く。

## 不合格時の扱い

SKILL.md の品質チェックまたは上の機械検証で 1 項目でも外れたら、HTML を修正して再確認する。直し方は次のとおり。

- 箇条書き・表・カードが上限超過: スライドを分割する(フォント縮小で収めない)
- 文字色と背景色のコントラストが 4.5:1 未満、`var(--xxx)` や `color: white` の使用: 直接カラーコード(`#ffffff` 等)へ置換する
- 最終スライドが「Thank You」のみ、参照ページ番号が無い: `.summary-slide` 形式で作り直す
- すべて満たすまで完了報告をしない
