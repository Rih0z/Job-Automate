# 企画書mdファイルからの16:9比率プレゼンテーションスライド生成プロンプト（改良版）

以下の指示に従って、提供された企画書のmdファイルから16:9比率のプレゼンテーションスライドをHTMLとCSSで自動生成します。スクロールバーが表示されないよう最適化され、各スライドが1画面におさまるデザインを実現します。

## 基本設定

```html
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>プレゼンテーションタイトル</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
      font-family: "Yu Gothic", "メイリオ", sans-serif;
    }

    body {
      background-color: #f5f5f5;
      color: #333;
      line-height: 1.5;
      padding: 20px;
    }

    .slide-container {
      width: 100%;
      max-width: 1024px; /* 16:9比率のベース幅 */
      margin: 0 auto;
    }

    .slide {
      background-color: white;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
      margin-bottom: 30px;
      display: none;
      position: relative;
      width: 100%;
      aspect-ratio: 16 / 9; /* 16:9アスペクト比を直接指定 */
    }

    .slide-content {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      padding: 30px;
      overflow: hidden; /* スクロールしないように設定 */
      display: flex;
      flex-direction: column;
    }

    .slide.active {
      display: block;
    }

    h1 {
      color: #0066cc;
      font-size: 28px;
      margin-bottom: 15px;
      border-bottom: 2px solid #0066cc;
      padding-bottom: 8px;
    }

    h2 {
      color: #333;
      font-size: 22px;
      margin: 12px 0 8px;
    }

    h3 {
      font-size: 18px;
      margin: 8px 0 6px;
    }

    ul {
      margin-left: 20px;
      margin-bottom: 12px;
    }

    li {
      margin-bottom: 6px;
      font-size: 16px;
    }

    .highlight {
      font-weight: bold;
      color: #0066cc;
    }

    .section {
      margin-bottom: 15px;
    }

    .footer {
      font-size: 14px;
      text-align: right;
      color: #777;
      margin-top: auto;
      padding-top: 10px;
    }

    /* ナビゲーションコントロール用スタイル */
    .nav-controls {
      display: flex;
      justify-content: center;
      margin: 15px 0;
      gap: 20px;
    }

    .nav-btn {
      padding: 10px 20px;
      background-color: #0066cc;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 16px;
      transition: background-color 0.3s;
    }

    .nav-btn:hover {
      background-color: #0052a3;
    }

    .nav-btn:disabled {
      background-color: #cccccc;
      cursor: not-allowed;
    }

    .slide-indicator {
      display: flex;
      align-items: center;
      font-size: 16px;
      padding: 0 10px;
    }

    /* テーブル用スタイル */
    .table-wrapper {
      overflow-x: auto;
    }
    
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 12px 0;
      font-size: 14px;
    }

    table, th, td {
      border: 1px solid #ddd;
    }

    th, td {
      padding: 6px;
      text-align: left;
    }

    th {
      background-color: #f0f8ff;
    }

    tr:nth-child(even) {
      background-color: #f9f9f9;
    }

    /* 情報量が多いスライド用のスタイル */
    .compact-table th, .compact-table td {
      padding: 3px;
      font-size: 11px;
    }

    .smaller-text li {
      font-size: 14px;
      margin-bottom: 3px;
    }

    .very-small-text li {
      font-size: 12px;
      margin-bottom: 2px;
    }

    .appendix-title {
      font-size: 24px;
    }
    
    .appendix-section {
      margin-bottom: 10px;
    }
    
    .appendix-section h2 {
      font-size: 20px;
      margin: 10px 0 6px;
    }

    /* ロードマップ図用のスタイル */
    .roadmap-container {
      margin: 10px 0;
      position: relative;
      flex-grow: 1;
      display: flex;
      flex-direction: column;
    }

    .roadmap {
      display: flex;
      flex-direction: column;
      width: 100%;
      position: relative;
      flex-grow: 1;
    }

    .roadmap-line {
      position: absolute;
      left: 18px;
      top: 0;
      bottom: 0;
      width: 4px;
      background-color: #0066cc;
      z-index: 1;
    }

    .roadmap-quarter {
      display: flex;
      margin-bottom: 8px;
      position: relative;
      flex: 1;
    }

    .roadmap-marker {
      width: 32px;
      height: 32px;
      background-color: #0066cc;
      border-radius: 50%;
      display: flex;
      justify-content: center;
      align-items: center;
      color: white;
      font-weight: bold;
      margin-right: 12px;
      z-index: 2;
      flex-shrink: 0;
      font-size: 14px;
    }

    .roadmap-content {
      flex: 1;
      background-color: #f0f8ff;
      border-left: 5px solid;
      padding: 6px;
      border-radius: 0 8px 8px 0;
      box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
      display: flex;
      flex-direction: column;
      justify-content: center;
    }

    .roadmap-content h3 {
      margin-top: 0;
      margin-bottom: 3px;
      color: #333;
      font-size: 15px;
    }

    .roadmap-content ul {
      margin-bottom: 0;
      margin-top: 2px;
    }

    .roadmap-content li {
      font-size: 12px;
      margin-bottom: 2px;
    }

    /* 各四半期のカラー設定 */
    .q1 { border-left-color: #4285f4; }
    .q2 { border-left-color: #34a853; }
    .q3 { border-left-color: #fbbc05; }
    .q4 { border-left-color: #ea4335; }

    .q1 .roadmap-marker { background-color: #4285f4; }
    .q2 .roadmap-marker { background-color: #34a853; }
    .q3 .roadmap-marker { background-color: #fbbc05; }
    .q4 .roadmap-marker { background-color: #ea4335; }

    /* 円グラフ用スタイル - サイズ調整 */
    .chart-container {
      display: flex;
      justify-content: center;
      align-items: center;
      height: 240px;
      margin: 10px 0;
    }

    .pie-chart {
      width: 200px;
      height: 200px;
      position: relative;
      border-radius: 50%;
      background: conic-gradient(
        #4285f4 0% 20%, 
        #34a853 20% 65%, 
        #fbbc05 65% 90%, 
        #ea4335 90% 100%
      );
    }

    .pie-chart::before {
      content: "";
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 80px;
      height: 80px;
      background-color: white;
      border-radius: 50%;
    }

    .chart-labels {
      display: flex;
      flex-direction: column;
      margin-left: 20px;
    }

    .chart-label {
      display: flex;
      align-items: center;
      margin-bottom: 8px;
      font-size: 13px;
    }

    .color-box {
      width: 16px;
      height: 16px;
      margin-right: 8px;
      flex-shrink: 0;
    }

    .color-1 { background-color: #4285f4; }
    .color-2 { background-color: #34a853; }
    .color-3 { background-color: #fbbc05; }
    .color-4 { background-color: #ea4335; }

    /* 中央揃え */
    .center-content {
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      height: 100%;
      text-align: center;
    }

    .title-text {
      font-size: 40px;
      font-weight: bold;
      color: #0066cc;
      margin-bottom: 20px;
    }

    .subtitle-text {
      font-size: 24px;
      color: #555;
    }

    .date-text {
      font-size: 18px;
      color: #777;
      margin-top: 20px;
    }

    /* 目標一覧表 - コンパクト化 */
    .goals-table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
      font-size: 13px;
    }

    .goals-table th, .goals-table td {
      padding: 6px;
      text-align: left;
      border-bottom: 1px solid #ddd;
    }

    .goals-table th {
      background-color: #f0f8ff;
      font-weight: bold;
    }

    .weight-cell {
      text-align: center;
      font-weight: bold;
    }

    /* 2カラム用レイアウト */
    .two-column {
      display: flex;
      gap: 15px;
      margin-top: 10px;
    }

    .column {
      flex: 1;
    }

    /* 懸念事項用のコンパクトスタイル */
    .concern-section {
      margin-bottom: 10px;
    }

    .concern-section h3 {
      font-size: 15px;
      margin: 5px 0 3px;
    }

    .concern-section ul {
      margin-bottom: 5px;
    }
    
    /* 全体計画表用のさらにコンパクトなスタイル */
    .very-compact-table th, .very-compact-table td {
      padding: 2px;
      font-size: 10px;
    }
  </style>
</head>
<body>
  <div class="slide-container">
    <!-- スライドコンテンツはここに動的に生成されます -->
    
    <!-- ナビゲーションコントロール -->
    <div class="nav-controls">
      <button id="prev-btn" class="nav-btn">前へ</button>
      <div class="slide-indicator">
        <span id="current-slide">1</span> / <span id="total-slides">X</span>
      </div>
      <button id="next-btn" class="nav-btn">次へ</button>
    </div>
  </div>

  <script>
    document.addEventListener('DOMContentLoaded', function() {
      const slides = document.querySelectorAll('.slide');
      const prevBtn = document.getElementById('prev-btn');
      const nextBtn = document.getElementById('next-btn');
      const currentSlideEl = document.getElementById('current-slide');
      const totalSlidesEl = document.getElementById('total-slides');
      
      let currentSlide = 0; // 最初のスライドを表示
      const totalSlides = slides.length;
      
      // 初期表示
      totalSlidesEl.textContent = totalSlides;
      showSlide(currentSlide);
      
      // 前へボタン
      prevBtn.addEventListener('click', function() {
        if (currentSlide > 0) {
          showSlide(currentSlide - 1);
        }
      });
      
      // 次へボタン
      nextBtn.addEventListener('click', function() {
        if (currentSlide < totalSlides - 1) {
          showSlide(currentSlide + 1);
        }
      });
      
      // キーボードイベント
      document.addEventListener('keydown', function(e) {
        if (e.key === 'ArrowLeft') {
          if (currentSlide > 0) {
            showSlide(currentSlide - 1);
          }
        } else if (e.key === 'ArrowRight') {
          if (currentSlide < totalSlides - 1) {
            showSlide(currentSlide + 1);
          }
        }
      });
      
      // スライド表示関数
      function showSlide(index) {
        slides.forEach((slide, i) => {
          if (i === index) {
            slide.classList.add('active');
          } else {
            slide.classList.remove('active');
          }
        });
        
        currentSlide = index;
        currentSlideEl.textContent = index + 1;
        
        // ボタン状態の更新
        prevBtn.disabled = currentSlide === 0;
        nextBtn.disabled = currentSlide === totalSlides - 1;
      }
    });
  </script>
</body>
</html>
```

## 企画書のMarkdownからスライドを生成する方法

1. 提供された企画書のmdファイルを解析し、次の要素を特定します：
   - タイトル（# で始まる行）
   - 見出し（##, ###, #### で始まる行）
   - 箇条書きリスト（- または * で始まる行）
   - 表（|---|---| 形式のMarkdown表）
   - コードブロック（```で囲まれた部分）

2. 各セクションを適切なスライドに変換します：
   - 各見出し（## レベル）ごとに新しいスライドを作成
   - 小見出し（### レベル）は同じスライド内のセクションとして扱う
   - 表は適切なHTMLテーブルに変換
   - 箇条書きリストはULリストに変換

## スライド生成のルール

1. **タイトルスライド**
   - 企画書の最初の見出し（# レベル）をスライドタイトルとして使用
   - サブタイトル、日付、発表者情報を追加（企画書内で指定されている場合）

2. **目次スライド**
   - 企画書内の ## レベルの見出しを収集して目次を作成
   - クリック可能なリンクを設定（オプション）

3. **コンテンツスライド**
   - 各 ## 見出しごとに新しいスライドを作成
   - 見出し直後のテキストをスライドの説明文として使用
   - 箇条書きリストをそのままスライドのポイントとして使用

4. **特殊なスライドタイプ**
   - "ロードマップ" という単語が見出しに含まれる場合、ロードマップ図用のテンプレートを適用
   - "比較" または "表" という単語が見出しに含まれる場合、表形式のテンプレートを適用
   - "まとめ" または "結論" という単語が含まれる場合、まとめ用のテンプレートを適用

## スクロールバーなしでコンテンツを表示するための工夫

1. **テキスト表現の最適化**
   - 長い文章は「キーワード - 簡潔な説明」形式で表現
   - 文字数を減らし、要点のみを記載
   - 情報量が多い場合は複数のスライドに分割

2. **レイアウトとサイズの調整**
   - overflow: hidden で強制的にスクロールバーを非表示に
   - aspect-ratio: 16 / 9 で正確な比率を維持
   - フォントサイズを全体的に小さめに設定
   - 情報量の多いスライドではさらにフォントサイズを小さく調整

3. **表示領域の最大活用**
   - 余白を最小限に抑える
   - 行間を適切に設定
   - リスト項目の間隔を調整
   - 2カラムレイアウトを活用して横幅を最大限に活用

## 改良点

1. **目標概要スライド**
   - 円グラフのサイズを縮小し、ラベルのフォントサイズを小さく調整
   - 目標一覧表のフォントサイズと行間を小さく調整

2. **懸念事項および対策スライド**
   - 2カラムレイアウトを活用し、複数の懸念事項を横に配置
   - 懸念と対策のセクションをコンパクトに表示
   - 必要に応じてさらに分割して複数スライドに分散

3. **全体実行計画スライド**
   - 超コンパクトな表スタイルを適用し、情報を圧縮
   - 必要に応じて表を縦方向に分割し、目標ごとに別スライドを作成

4. **ロードマップスライド**
   - ロードマップの各要素の間隔を縮小
   - フォントサイズを小さく調整
   - マーカーのサイズを縮小

5. **リストの表示**
   - 通常のリストよりもさらに小さいフォントサイズのクラスを追加
   - リストアイテムの間隔をさらに縮小

## 実装手順

1. 企画書のmdファイルを読み込む
2. Markdownの構造を解析してスライド構造を決定
3. 各セクションに適したテンプレートを適用
4. コンテンツ量に応じて適切なフォントサイズとレイアウトを選択
5. 情報量が多い箇所は複数スライドに分割
6. HTMLファイルとして出力

この改良されたプロンプトを使用することで、すべてのスライドが16:9比率の表示領域にスクロールなしで収まり、視認性と可読性を保った効果的なプレゼンテーションを生成できます。
