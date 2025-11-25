# 企画書mdファイルからの16:9比率プレゼンテーションスライド生成プロンプト（プロフェッショナル版 v2）

ベテランITコンサルタントの視点から最適化された、提供された企画書のmdファイルから16:9比率のプレゼンテーションスライドをHTMLとCSSで自動生成するシステム。実際のビジネスプレゼンテーションで求められる要素を網羅し、視認性と操作性を最大化します。

## 重要：スライド生成前の事前処理

**必ず以下の手順を実行してからスライドを生成してください：**

1. **現在の日付を取得**
   - web_searchツールを使用して「今日の日付」を検索
   - または「current date today」で検索
   - 取得した日付をプレゼンテーションの作成日として使用

2. **日付フォーマット**
   - 日本語表記：2024年12月19日
   - 英語表記：December 19, 2024
   - タイトルスライドや最終スライドに自動挿入

## 基本設定（プロフェッショナル仕様）

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
      font-family: "游ゴシック", "Yu Gothic", "Noto Sans JP", "Hiragino Kaku Gothic ProN", "メイリオ", sans-serif;
    }

    body {
      background-color: #1a1a1a;
      color: #333;
      line-height: 1.6;
      overflow: hidden;
      height: 100vh;
      display: flex;
      justify-content: center;
      align-items: center;
    }

    /* メインコンテナ - フルスクリーン対応 */
    .presentation-container {
      width: 100%;
      height: 100%;
      max-width: 1920px;
      max-height: 1080px;
      position: relative;
      background-color: #000;
      box-shadow: 0 0 50px rgba(0, 0, 0, 0.8);
    }

    /* スライドスタイル */
    .slide {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background-color: white;
      display: none;
      opacity: 0;
      transform: translateX(100%);
      transition: opacity 0.5s ease-in-out, transform 0.5s ease-in-out;
    }

    .slide.active {
      display: block;
      opacity: 1;
      transform: translateX(0);
    }

    .slide.prev {
      display: block;
      opacity: 0;
      transform: translateX(-100%);
    }

    /* スライドコンテンツ - スクロールバー対応 */
    .slide-content {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      padding: 50px 70px 70px;
      overflow-y: auto;
      overflow-x: hidden;
      display: flex;
      flex-direction: column;
    }

    /* スクロールバーのカスタムスタイル（WebKit系ブラウザ用） */
    .slide-content::-webkit-scrollbar {
      width: 10px;
    }

    .slide-content::-webkit-scrollbar-track {
      background: #f1f1f1;
      border-radius: 5px;
    }

    .slide-content::-webkit-scrollbar-thumb {
      background: #c1c1c1;
      border-radius: 5px;
      transition: background 0.3s;
    }

    .slide-content::-webkit-scrollbar-thumb:hover {
      background: #0066cc;
    }

    /* Firefox用スクロールバー */
    .slide-content {
      scrollbar-width: thin;
      scrollbar-color: #c1c1c1 #f1f1f1;
    }

    /* ナビゲーション - 透明な画面内ボタン */
    .nav-area {
      position: absolute;
      top: 0;
      width: 15%;
      height: 100%;
      z-index: 100;
      cursor: pointer;
      background: transparent;
      transition: background-color 0.3s;
    }

    .nav-area:hover {
      background-color: rgba(0, 0, 0, 0.05);
    }

    .nav-prev {
      left: 0;
    }

    .nav-next {
      right: 0;
    }

    /* スライド番号とプログレスバー */
    .slide-progress {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      height: 4px;
      background-color: #e0e0e0;
      z-index: 101;
    }

    .progress-bar {
      height: 100%;
      background-color: #0066cc;
      transition: width 0.5s ease-out;
    }

    .slide-number {
      position: absolute;
      bottom: 20px;
      right: 30px;
      font-size: 14px;
      color: #999;
      z-index: 101;
    }

    /* タイポグラフィ最適化 */
    h1 {
      color: #003366;
      font-size: 38px;
      font-weight: 700;
      margin-bottom: 25px;
      letter-spacing: -0.5px;
      line-height: 1.2;
    }

    h2 {
      color: #0066cc;
      font-size: 28px;
      font-weight: 600;
      margin: 15px 0 12px;
      letter-spacing: -0.3px;
    }

    h3 {
      color: #333;
      font-size: 22px;
      font-weight: 500;
      margin: 12px 0 8px;
    }

    h4 {
      color: #555;
      font-size: 18px;
      font-weight: 500;
      margin: 10px 0 6px;
    }

    p {
      font-size: 17px;
      margin-bottom: 12px;
      line-height: 1.7;
    }

    /* リストスタイル改良 */
    ul, ol {
      margin: 0 0 15px 25px;
    }

    li {
      font-size: 16px;
      margin-bottom: 8px;
      line-height: 1.5;
    }

    /* 強調表示 */
    .highlight {
      background: linear-gradient(transparent 60%, #ffeb3b 60%);
      font-weight: 600;
      padding: 0 4px;
    }

    strong {
      color: #0066cc;
      font-weight: 600;
    }

    /* タイトルスライド専用スタイル */
    .title-slide {
      background: linear-gradient(135deg, #003366 0%, #0066cc 100%);
      color: white;
    }

    .title-slide .slide-content {
      justify-content: center;
      align-items: center;
      text-align: center;
    }

    .title-slide h1 {
      color: white;
      font-size: 52px;
      margin-bottom: 25px;
      text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    }

    .title-slide .subtitle {
      font-size: 26px;
      margin-bottom: 35px;
      opacity: 0.9;
    }

    .title-slide .author {
      font-size: 20px;
      opacity: 0.8;
    }

    .title-slide .date {
      font-size: 16px;
      margin-top: 10px;
      opacity: 0.7;
    }

    /* セクション区切りスライド */
    .section-divider {
      background: linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%);
    }

    .section-divider .slide-content {
      justify-content: center;
      align-items: center;
      text-align: center;
    }

    .section-divider h1 {
      font-size: 44px;
      color: #003366;
      line-height: 1.4;
      padding: 0 40px;
    }

    /* 2カラムレイアウト */
    .two-column {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 35px;
      flex: 1;
    }

    .column {
      display: flex;
      flex-direction: column;
    }

    /* 3カラムレイアウト */
    .three-column {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 25px;
      flex: 1;
    }

    /* 画像とテキストのレイアウト */
    .image-text-layout {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 40px;
      align-items: center;
      height: 100%;
    }

    .image-container {
      display: flex;
      justify-content: center;
      align-items: center;
      background-color: #f5f5f5;
      border-radius: 8px;
      padding: 20px;
      height: 100%;
    }

    /* プロフェッショナルな表デザイン */
    table {
      width: 100%;
      border-collapse: separate;
      border-spacing: 0;
      margin: 15px 0;
      background-color: white;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      border-radius: 8px;
      overflow: hidden;
    }

    th {
      background-color: #003366;
      color: white;
      font-weight: 600;
      padding: 12px 14px;
      text-align: left;
      font-size: 15px;
    }

    td {
      padding: 10px 14px;
      border-bottom: 1px solid #e0e0e0;
      font-size: 14px;
    }

    tr:last-child td {
      border-bottom: none;
    }

    tr:nth-child(even) {
      background-color: #f8f9fa;
    }

    /* ロードマップ専用デザイン */
    .roadmap {
      display: flex;
      flex-direction: column;
      gap: 20px;
      margin: 20px 0;
      position: relative;
      padding-left: 40px;
    }

    .timeline-line {
      position: absolute;
      left: 20px;
      top: 20px;
      bottom: 20px;
      width: 3px;
      background: linear-gradient(180deg, #0066cc 0%, #003366 100%);
    }

    .roadmap-item {
      display: flex;
      align-items: flex-start;
      position: relative;
    }

    .roadmap-marker {
      position: absolute;
      left: -29px;
      width: 16px;
      height: 16px;
      background-color: #0066cc;
      border: 3px solid white;
      border-radius: 50%;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }

    .roadmap-content {
      background-color: #f8f9fa;
      border-left: 4px solid #0066cc;
      padding: 15px 20px;
      border-radius: 0 8px 8px 0;
      flex: 1;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }

    .roadmap-content h3 {
      margin: 0 0 8px 0;
      font-size: 20px;
      color: #003366;
    }

    /* 円グラフ */
    .chart-container {
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 40px;
      margin: 30px 0;
    }

    .pie-chart-wrapper {
      position: relative;
    }

    .pie-chart {
      width: 280px;
      height: 280px;
      border-radius: 50%;
      position: relative;
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }

    .chart-center {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 120px;
      height: 120px;
      background-color: white;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-direction: column;
      box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    .chart-legend {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .legend-item {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 16px;
    }

    .legend-color {
      width: 24px;
      height: 24px;
      border-radius: 4px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
    }

    /* アイコン付きリスト */
    .icon-list {
      list-style: none;
      margin-left: 0;
    }

    .icon-list li {
      display: flex;
      align-items: flex-start;
      gap: 10px;
      margin-bottom: 12px;
    }

    .icon-list li::before {
      content: "▶";
      color: #0066cc;
      font-weight: bold;
      flex-shrink: 0;
      margin-top: 2px;
      font-size: 12px;
    }

    /* カード型レイアウト */
    .card-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 18px;
      margin: 15px 0;
    }

    .card {
      background-color: #f8f9fa;
      border-radius: 8px;
      padding: 18px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      transition: transform 0.2s, box-shadow 0.2s;
    }

    .card:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    }

    .card h3 {
      color: #0066cc;
      margin-top: 0;
      margin-bottom: 10px;
      font-size: 18px;
    }

    .card h4 {
      color: #003366;
      margin-top: 0;
      margin-bottom: 8px;
      font-size: 16px;
    }

    .card p {
      font-size: 15px;
      margin-bottom: 8px;
    }

    .card ul {
      margin: 0 0 8px 20px;
    }

    .card li {
      font-size: 14px;
      margin-bottom: 4px;
    }

    /* キーポイント強調ボックス */
    .key-point {
      background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
      border-left: 4px solid #0066cc;
      padding: 18px 22px;
      margin: 15px 0;
      border-radius: 0 8px 8px 0;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    .key-point h3 {
      margin-top: 0;
      color: #003366;
      font-size: 20px;
    }

    .key-point p {
      font-size: 16px;
      margin-bottom: 8px;
    }

    /* まとめスライド */
    .summary-slide {
      background-color: #f8f9fa;
    }

    .summary-points {
      display: flex;
      flex-direction: column;
      gap: 15px;
      margin-top: 20px;
    }

    .summary-item {
      display: flex;
      align-items: center;
      gap: 18px;
      background-color: white;
      padding: 16px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }

    .summary-number {
      width: 44px;
      height: 44px;
      background-color: #0066cc;
      color: white;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 22px;
      font-weight: bold;
      flex-shrink: 0;
    }

    .summary-item h3 {
      margin: 0 0 4px 0;
      font-size: 18px;
    }

    .summary-item p {
      margin: 0;
      font-size: 15px;
    }

    /* コールトゥアクション */
    .cta-box {
      background: linear-gradient(135deg, #0066cc 0%, #003366 100%);
      color: white;
      padding: 25px;
      border-radius: 12px;
      text-align: center;
      margin: 20px 0;
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }

    .cta-box h2 {
      color: white;
      margin-bottom: 12px;
      font-size: 26px;
    }

    .cta-box p {
      font-size: 18px;
      opacity: 0.9;
      color: white;
    }

    /* cta-box内のstrong要素も白文字に */
    .cta-box strong {
      color: white;
    }

    /* 用語解説グリッド */
    .glossary-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 15px;
    }

    .glossary-item {
      background: linear-gradient(135deg, #fff9e6 0%, #fff3cc 100%);
      border-left: 4px solid #ff9800;
      padding: 15px 18px;
      border-radius: 0 8px 8px 0;
    }

    .glossary-item h4 {
      color: #e65100;
      margin: 0 0 6px 0;
      font-size: 17px;
    }

    .glossary-item p {
      margin: 0;
      font-size: 14px;
      line-height: 1.5;
    }

    /* アニメーション */
    @keyframes fadeInUp {
      from {
        opacity: 0;
        transform: translateY(20px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .slide.active .animate-item {
      animation: fadeInUp 0.6s ease-out forwards;
    }

    .animate-item:nth-child(1) { animation-delay: 0.1s; }
    .animate-item:nth-child(2) { animation-delay: 0.2s; }
    .animate-item:nth-child(3) { animation-delay: 0.3s; }
    .animate-item:nth-child(4) { animation-delay: 0.4s; }
    .animate-item:nth-child(5) { animation-delay: 0.5s; }
    .animate-item:nth-child(6) { animation-delay: 0.6s; }

    /* キーボードショートカットヘルプ */
    .help-overlay {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background-color: rgba(0, 0, 0, 0.8);
      display: none;
      justify-content: center;
      align-items: center;
      z-index: 1000;
    }

    .help-content {
      background-color: white;
      padding: 35px;
      border-radius: 12px;
      max-width: 450px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    }

    .help-content h2 {
      margin-top: 0;
      margin-bottom: 20px;
      color: #003366;
    }

    .shortcut-list {
      list-style: none;
      margin: 0;
    }

    .shortcut-list li {
      display: flex;
      justify-content: space-between;
      margin-bottom: 10px;
      padding: 8px;
      background-color: #f5f5f5;
      border-radius: 4px;
    }

    .shortcut-key {
      font-family: monospace;
      background-color: #e0e0e0;
      padding: 2px 6px;
      border-radius: 3px;
      font-weight: bold;
    }

    /* レスポンシブ対応 */
    @media (max-width: 1024px) {
      .slide-content {
        padding: 40px;
      }
      
      h1 { font-size: 32px; }
      h2 { font-size: 26px; }
      h3 { font-size: 20px; }
      p, li { font-size: 16px; }
      
      .two-column {
        grid-template-columns: 1fr;
      }
      
      .nav-area {
        width: 20%;
      }
    }

    /* =====================================
       印刷・PDF出力用スタイル（v3 - 回転問題完全修正版）
       - 90度回転バグを解消
       - 表示通りに横向きで印刷
       - A4サイズを明示的に指定
       ===================================== */
    @media print {
      * {
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
        color-adjust: exact !important;
      }

      /* A4横向きを明示的にmm単位で指定（重要！） */
      @page {
        size: 297mm 210mm;
        margin: 5mm;
      }

      html {
        width: 297mm;
        height: 210mm;
      }

      body {
        width: 297mm;
        height: auto;
        margin: 0;
        padding: 0;
        background-color: white !important;
        overflow: visible;
      }

      .presentation-container {
        width: 287mm;
        height: auto;
        max-width: none;
        max-height: none;
        margin: 0;
        padding: 0;
        background-color: white !important;
        box-shadow: none !important;
        display: block;
        position: static;
      }

      .slides-wrapper {
        display: block;
        width: 100%;
      }

      .slide {
        width: 287mm;
        height: 161.4mm; /* 16:9比率 = 287 * 9/16 */
        page-break-after: always;
        page-break-inside: avoid;
        break-after: page;
        break-inside: avoid;
        margin: 0 auto 5mm auto;
        padding: 0;
        position: relative !important;
        background-color: white !important;
        display: block !important;
        opacity: 1 !important;
        transform: none !important;
        box-sizing: border-box;
        overflow: hidden;
      }

      .slide:last-child {
        page-break-after: avoid;
        break-after: auto;
        margin-bottom: 0;
      }

      .slide-content {
        position: absolute !important;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        padding: 8mm 10mm 10mm;
        overflow: hidden !important;
        height: 100% !important;
        box-sizing: border-box;
      }

      /* タイトルスライドの背景保持 */
      .title-slide {
        background: linear-gradient(135deg, #003366 0%, #0066cc 100%) !important;
      }

      .title-slide .slide-content,
      .title-slide h1,
      .title-slide .subtitle,
      .title-slide .author,
      .title-slide .date,
      .title-slide p {
        color: white !important;
      }

      /* セクション区切りの背景保持 */
      .section-divider {
        background: linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%) !important;
      }

      /* 印刷用フォントサイズ調整 */
      h1 { font-size: 28px !important; margin-bottom: 15px !important; }
      h2 { font-size: 22px !important; margin-bottom: 10px !important; }
      h3 { font-size: 18px !important; margin-bottom: 8px !important; }
      h4 { font-size: 15px !important; }
      p { font-size: 13px !important; margin-bottom: 8px !important; }
      li { font-size: 13px !important; margin-bottom: 5px !important; }

      .title-slide h1 { font-size: 38px !important; }
      .title-slide .subtitle { font-size: 20px !important; }
      .section-divider h1 { font-size: 32px !important; }

      /* 表のスタイル保持 */
      table {
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
      }

      th {
        background-color: #003366 !important;
        color: white !important;
        padding: 8px 10px !important;
      }

      td {
        padding: 6px 10px !important;
      }

      /* カードの背景保持 */
      .card {
        background-color: #f8f9fa !important;
        padding: 10px !important;
        margin-bottom: 8px !important;
      }

      .key-point {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%) !important;
        padding: 10px 12px !important;
        margin: 10px 0 !important;
      }

      /* CTA ボックスの保持 */
      .cta-box {
        background: linear-gradient(135deg, #0066cc 0%, #003366 100%) !important;
        color: white !important;
        padding: 15px !important;
        margin: 12px 0 !important;
      }

      .cta-box h2,
      .cta-box p,
      .cta-box strong {
        color: white !important;
      }

      /* 用語解説 */
      .glossary-item {
        background: linear-gradient(135deg, #fff9e6 0%, #fff3cc 100%) !important;
        padding: 10px 12px !important;
      }

      /* グリッド調整 */
      .two-column {
        gap: 20px !important;
      }

      .card-grid {
        gap: 12px !important;
      }

      /* アニメーション要素の表示 */
      .animate-item {
        opacity: 1 !important;
        transform: none !important;
        animation: none !important;
      }

      /* ナビゲーション要素を非表示 */
      .nav-area, 
      .slide-progress, 
      .help-overlay, 
      .pdf-export-btn,
      .slide-number {
        display: none !important;
      }
    }

    /* PDF出力ボタン */
    .pdf-export-btn {
      position: fixed;
      bottom: 20px;
      left: 20px;
      width: 48px;
      height: 48px;
      background-color: #0066cc;
      border: none;
      border-radius: 50%;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.3s ease;
      z-index: 102;
      opacity: 0.8;
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
    }

    .pdf-export-btn:hover {
      background-color: #0052a3;
      opacity: 1;
      transform: scale(1.1);
      box-shadow: 0 6px 12px rgba(0, 0, 0, 0.4);
    }

    .pdf-export-btn svg {
      width: 24px;
      height: 24px;
      fill: white;
    }

    /* ツールチップ */
    .pdf-export-btn::after {
      content: 'PDF出力';
      position: absolute;
      bottom: 100%;
      left: 50%;
      transform: translateX(-50%);
      background-color: rgba(0, 0, 0, 0.8);
      color: white;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 12px;
      white-space: nowrap;
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.3s;
      margin-bottom: 8px;
    }

    .pdf-export-btn:hover::after {
      opacity: 1;
    }

    /* フルスクリーン時は控えめに */
    .fullscreen .pdf-export-btn {
      opacity: 0.2;
      width: 40px;
      height: 40px;
    }

    .fullscreen .pdf-export-btn:hover {
      opacity: 0.9;
      width: 48px;
      height: 48px;
    }

    .fullscreen .pdf-export-btn svg {
      width: 20px;
      height: 20px;
    }
  </style>
</head>
<body>
  <div class="presentation-container">
    <!-- スライドコンテンツ -->
    <div class="slides-wrapper">
      <!-- スライドはここに動的に生成される -->
    </div>
    
    <!-- ナビゲーション -->
    <div class="nav-area nav-prev" onclick="navigateSlide(-1)"></div>
    <div class="nav-area nav-next" onclick="navigateSlide(1)"></div>
    
    <!-- プログレスバー -->
    <div class="slide-progress">
      <div class="progress-bar" id="progressBar"></div>
    </div>
    
    <!-- スライド番号 -->
    <div class="slide-number" id="slideNumber">1 / X</div>
    
    <!-- PDF出力ボタン -->
    <button class="pdf-export-btn" onclick="exportToPDF()" title="PDFとして出力">
      <svg viewBox="0 0 24 24">
        <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20M10,17L8,11H10L11.2,15.2L12.5,11H14.3L15.6,15.2L16.8,11H18.5L16.5,17H14.7L13.4,12.6L12.1,17H10Z"/>
      </svg>
    </button>
    
    <!-- ヘルプオーバーレイ -->
    <div class="help-overlay" id="helpOverlay">
      <div class="help-content">
        <h2>キーボードショートカット</h2>
        <ul class="shortcut-list">
          <li>
            <span>次のスライド</span>
            <span><span class="shortcut-key">→</span> / <span class="shortcut-key">Space</span></span>
          </li>
          <li>
            <span>前のスライド</span>
            <span><span class="shortcut-key">←</span> / <span class="shortcut-key">Backspace</span></span>
          </li>
          <li>
            <span>最初のスライド</span>
            <span><span class="shortcut-key">Home</span></span>
          </li>
          <li>
            <span>最後のスライド</span>
            <span><span class="shortcut-key">End</span></span>
          </li>
          <li>
            <span>フルスクリーン</span>
            <span><span class="shortcut-key">F</span></span>
          </li>
          <li>
            <span>ヘルプを閉じる</span>
            <span><span class="shortcut-key">Esc</span> / <span class="shortcut-key">?</span></span>
          </li>
        </ul>
      </div>
    </div>
  </div>

  <script>
    // プレゼンテーション管理クラス
    class PresentationManager {
      constructor() {
        this.slides = [];
        this.currentSlide = 0;
        this.totalSlides = 0;
        this.init();
      }

      init() {
        this.slides = document.querySelectorAll('.slide');
        this.totalSlides = this.slides.length;
        
        if (this.totalSlides > 0) {
          this.showSlide(0);
          this.setupEventListeners();
          this.updateSlideNumber();
          this.updateProgressBar();
        }
      }

      setupEventListeners() {
        // キーボードイベント
        document.addEventListener('keydown', (e) => this.handleKeyPress(e));
        
        // タッチジェスチャー
        let touchStartX = 0;
        document.addEventListener('touchstart', (e) => {
          touchStartX = e.touches[0].clientX;
        });
        
        document.addEventListener('touchend', (e) => {
          const touchEndX = e.changedTouches[0].clientX;
          const diff = touchStartX - touchEndX;
          
          if (Math.abs(diff) > 50) {
            if (diff > 0) {
              this.navigateSlide(1);
            } else {
              this.navigateSlide(-1);
            }
          }
        });
        
        // ヘルプオーバーレイ
        document.getElementById('helpOverlay').addEventListener('click', (e) => {
          if (e.target.id === 'helpOverlay') {
            this.toggleHelp();
          }
        });
      }

      handleKeyPress(e) {
        switch(e.key) {
          case 'ArrowRight':
          case ' ':
            e.preventDefault();
            this.navigateSlide(1);
            break;
          case 'ArrowLeft':
          case 'Backspace':
            e.preventDefault();
            this.navigateSlide(-1);
            break;
          case 'Home':
            e.preventDefault();
            this.showSlide(0);
            break;
          case 'End':
            e.preventDefault();
            this.showSlide(this.totalSlides - 1);
            break;
          case 'f':
          case 'F':
            e.preventDefault();
            this.toggleFullscreen();
            break;
          case '?':
            e.preventDefault();
            this.toggleHelp();
            break;
          case 'Escape':
            e.preventDefault();
            if (document.getElementById('helpOverlay').style.display === 'flex') {
              this.toggleHelp();
            }
            break;
        }
      }

      navigateSlide(direction) {
        const newSlide = this.currentSlide + direction;
        if (newSlide >= 0 && newSlide < this.totalSlides) {
          this.showSlide(newSlide);
        }
      }

      showSlide(index) {
        // 現在のスライドを非表示
        if (this.slides[this.currentSlide]) {
          this.slides[this.currentSlide].classList.remove('active');
          this.slides[this.currentSlide].classList.add('prev');
        }
        
        // 新しいスライドを表示
        setTimeout(() => {
          this.slides.forEach(slide => {
            slide.classList.remove('active', 'prev');
          });
          
          this.slides[index].classList.add('active');
          this.currentSlide = index;
          this.updateSlideNumber();
          this.updateProgressBar();
          
          // スクロール位置をリセット
          const slideContent = this.slides[index].querySelector('.slide-content');
          if (slideContent) {
            slideContent.scrollTop = 0;
          }
          
          // アニメーション要素をリセット
          const animateItems = this.slides[index].querySelectorAll('.animate-item');
          animateItems.forEach(item => {
            item.style.opacity = '0';
            setTimeout(() => {
              item.style.opacity = '';
            }, 10);
          });
        }, 10);
      }

      updateSlideNumber() {
        document.getElementById('slideNumber').textContent = 
          `${this.currentSlide + 1} / ${this.totalSlides}`;
      }

      updateProgressBar() {
        const progress = ((this.currentSlide + 1) / this.totalSlides) * 100;
        document.getElementById('progressBar').style.width = `${progress}%`;
      }

      toggleFullscreen() {
        if (!document.fullscreenElement) {
          document.documentElement.requestFullscreen();
          document.body.classList.add('fullscreen');
        } else {
          document.exitFullscreen();
          document.body.classList.remove('fullscreen');
        }
      }

      toggleHelp() {
        const helpOverlay = document.getElementById('helpOverlay');
        helpOverlay.style.display = 
          helpOverlay.style.display === 'flex' ? 'none' : 'flex';
      }

      exportToPDF() {
        // 印刷前の設定案内を表示
        const confirmed = confirm(
          '📄 PDF出力の設定確認\n\n' +
          '印刷ダイアログで以下を設定してください：\n\n' +
          '✅ 用紙の向き：「横」（Landscape）\n' +
          '✅ 用紙サイズ：A4\n' +
          '✅ 余白：なし または 最小\n' +
          '✅ 背景のグラフィック：オン\n\n' +
          '【Chrome/Edgeの場合】\n' +
          '「詳細設定」→「用紙サイズ」と「レイアウト」を確認\n\n' +
          '続行しますか？'
        );
        
        if (confirmed) {
          window.print();
        }
      }
    }

    // グローバル関数（HTML内のonclickから呼び出し用）
    let presentationManager;
    
    function navigateSlide(direction) {
      if (presentationManager) {
        presentationManager.navigateSlide(direction);
      }
    }

    function exportToPDF() {
      if (presentationManager) {
        presentationManager.exportToPDF();
      }
    }

    // 初期化
    document.addEventListener('DOMContentLoaded', () => {
      presentationManager = new PresentationManager();
    });
  </script>
</body>
</html>
```

## 企画書のMarkdownからスライドを生成する方法（プロ仕様）

### 1. コンテンツ解析と構造化

企画書のmdファイルを解析する際は、以下の要素を識別し、適切なスライドタイプに変換します：

#### スライドタイプの自動判定
- **タイトルスライド**: 最初の`#`見出し、または`タイトル`を含む最初のセクション
- **エグゼクティブサマリー**: `要約`、`サマリー`、`概要`を含むセクション
- **アジェンダ/目次**: `目次`、`アジェンダ`、`agenda`を含むセクション
- **セクション区切り**: 新しい大きなトピックの開始時
- **コンテンツスライド**: 通常の内容
- **比較スライド**: `比較`、`vs`、`対`を含むセクション
- **ロードマップ**: `ロードマップ`、`スケジュール`、`工程`を含むセクション
- **まとめスライド**: `まとめ`、`結論`、`今後`を含むセクション

### 2. コンテンツ最適化ルール

#### 文章の圧縮と要約
```markdown
# 元の文章
弊社の新しいクラウドサービスは、従来のオンプレミス型のシステムと比較して、初期投資を大幅に削減できるだけでなく、運用コストも約40%削減することが可能です。また、システムの拡張性も高く、ビジネスの成長に合わせて柔軟にリソースを追加できます。

# スライド用に最適化
• 初期投資: 大幅削減（オンプレミス比）
• 運用コスト: 40%削減
• 拡張性: ビジネス成長に応じた柔軟なリソース追加
```

#### 情報の階層化
- **メインポイント**: 各スライド3-5個まで
- **サブポイント**: 各メインポイントに2-3個まで
- **詳細情報**: 必要に応じて付録スライドへ移動

### 3. ビジュアル要素の自動生成

#### データの可視化
- **数値データ** → 円グラフ、棒グラフ
- **時系列データ** → ロードマップ、タイムライン
- **比較データ** → 比較表、2カラムレイアウト
- **プロセス** → フローチャート、ステップ図

#### アイコンとビジュアルキュー
- 重要ポイントには自動的にアイコンを付与
- カラーコーディングで情報の種類を区別
- 視覚的な階層構造を明確化

### 4. スライド分割の自動化

#### 分割基準
1. **コンテンツ量**: 1スライドに収まらない場合は自動分割
2. **論理的まとまり**: トピックごとに適切に分割
3. **視認性**: フォントサイズが12px以下にならないよう調整

#### 分割パターン
```javascript
// コンテンツ量に基づく自動分割
function shouldSplitSlide(content) {
  const maxBulletPoints = 6;
  const maxTableRows = 8;
  const maxTextLength = 500;
  
  return (
    content.bulletPoints > maxBulletPoints ||
    content.tableRows > maxTableRows ||
    content.textLength > maxTextLength
  );
}
```

### 5. プロフェッショナルなデザインパターン

#### カラースキーム
```css
:root {
  --primary-color: #003366;      /* 濃紺 - 信頼性 */
  --secondary-color: #0066cc;    /* 青 - 技術的 */
  --accent-color: #ff6600;       /* オレンジ - 強調 */
  --success-color: #00a651;      /* 緑 - 成功/達成 */
  --warning-color: #ffc107;      /* 黄 - 注意 */
  --danger-color: #dc3545;       /* 赤 - リスク */
}
```

#### レイアウトパターン
1. **インパクト重視**: タイトル + 大きな数字/グラフ
2. **詳細説明**: 2カラム（テキスト + ビジュアル）
3. **比較分析**: 並列カラムまたは比較表
4. **ストーリー展開**: タイムライン形式

### 6. スクロールバー機能（v2で追加）

各スライドにスクロールバーを追加し、コンテンツが多い場合でも下まで閲覧可能にします。

#### 実装ポイント
```css
/* スクロールバー対応 */
.slide-content {
  overflow-y: auto;
  overflow-x: hidden;
}

/* カスタムスクロールバー（WebKit系） */
.slide-content::-webkit-scrollbar {
  width: 10px;
}

.slide-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 5px;
}

.slide-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 5px;
}

.slide-content::-webkit-scrollbar-thumb:hover {
  background: #0066cc;
}

/* Firefox用 */
.slide-content {
  scrollbar-width: thin;
  scrollbar-color: #c1c1c1 #f1f1f1;
}
```

### 7. インタラクティブ要素

#### トランジション効果
- スライド切り替え: スムーズなスライドイン
- 要素アニメーション: 段階的なフェードイン
- 強調効果: ホバー時のハイライト

#### プレゼンテーション機能
- フルスクリーンモード（F キー）
- プレゼンターノート（別ウィンドウ）
- タイマー機能（オプション）
- ポインター/ペンツール（将来実装）

### 8. 印刷・PDF出力機能（v2で修正）

#### 修正内容
- 90度回転バグを解消
- 表示通りにそのまま印刷
- 横向き（landscape）で出力

#### 実装ポイント
```css
@media print {
  @page {
    size: landscape;  /* A4 landscapeではなくlandscapeのみ */
    margin: 10mm;
  }

  html, body {
    height: auto;
    overflow: visible;
  }

  .slide {
    width: 100%;
    height: auto;
    min-height: 180mm;
    aspect-ratio: 16 / 9;
    page-break-after: always;
    break-after: page;
    position: relative !important;
    display: block !important;
    opacity: 1 !important;
    transform: none !important;
  }

  .slide-content {
    position: relative !important;
    overflow: visible !important;
    height: auto !important;
  }
}
```

### 9. 実装のベストプラクティス

#### パフォーマンス最適化
```javascript
// 画像の遅延読み込み
const lazyLoadImages = () => {
  const images = document.querySelectorAll('img[data-src]');
  const imageObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target;
        img.src = img.dataset.src;
        imageObserver.unobserve(img);
      }
    });
  });
  
  images.forEach(img => imageObserver.observe(img));
};
```

#### アクセシビリティ
- キーボードナビゲーション完全対応
- スクリーンリーダー対応
- 高コントラストモード
- フォントサイズ調整機能

### 10. 出力オプション

#### エクスポート形式
1. **HTML単体ファイル**: すべてのリソースを含む
2. **PDF**: 印刷用に最適化（表示通りに出力）
3. **PowerPoint互換**: PPTXへの変換（別ツール経由）
4. **画像シーケンス**: 各スライドをPNG/JPEGで出力

### 11. 品質チェックリスト

プレゼンテーション生成後、以下の項目を自動チェック：

- [ ] 各スライドが16:9比率で表示されているか
- [ ] スクロールバーが正常に機能するか
- [ ] フォントサイズが適切か（最小12px）
- [ ] 画像が適切に配置されているか
- [ ] アニメーションが正常に動作するか
- [ ] ナビゲーションが直感的か
- [ ] カラーコントラストが十分か
- [ ] 情報の階層が明確か
- [ ] 印刷時に90度回転しないか
- [ ] cta-box内の文字が白文字になっているか

### 12. カスタマイズオプション

#### テーマ設定
```javascript
const themes = {
  corporate: {
    primary: '#003366',
    secondary: '#0066cc',
    font: 'Noto Sans JP'
  },
  modern: {
    primary: '#2c3e50',
    secondary: '#3498db',
    font: 'Helvetica Neue'
  },
  creative: {
    primary: '#e74c3c',
    secondary: '#f39c12',
    font: 'Montserrat'
  }
};
```

---

## 更新履歴

### v3 (2025-11-25)
- **印刷90度回転バグ完全修正**: @pageサイズを`297mm 210mm`で明示的に指定
- **スライドサイズ固定**: 印刷時のスライドサイズを`287mm x 161.4mm`（16:9比率）に固定
- **印刷前設定案内**: PDF出力ボタン押下時に横向き設定などの確認ダイアログを表示
- **印刷用フォントサイズ最適化**: 印刷時のフォントサイズを調整して可読性向上

### v2 (2025-11-25)
- **スクロールバー追加**: 各スライドに縦方向のスクロールバーを追加。コンテンツが多くても下まで閲覧可能に
- **印刷バグ修正**: PDF出力時の90度回転バグを解消（部分的）
- **cta-box文字色修正**: cta-box内のstrong要素も白文字に統一

### v1 (初版)
- 基本的なスライド生成機能
- 16:9比率対応
- キーボードショートカット
- PDF出力機能

---

## 印刷時の注意事項

PDF出力ボタンをクリックすると、以下の設定を促すダイアログが表示されます：

1. **用紙の向き**: 「横」（Landscape）を選択
2. **用紙サイズ**: A4
3. **余白**: 「なし」または「最小」
4. **背景のグラフィック**: オン（チェックを入れる）

### ブラウザ別の設定方法

| ブラウザ | 設定場所 |
|----------|----------|
| Chrome | 「詳細設定」→「レイアウト」で「横」を選択 |
| Edge | 「その他の設定」→「レイアウト」で「横」を選択 |
| Firefox | 印刷プレビュー → 「ページ設定」 |
| Safari | 「ページ設定」→「向き」で横を選択 |

---

このプロフェッショナル版の実装により、企画書から自動生成されるプレゼンテーションは、実際のビジネスシーンで即座に使用できる品質となります。
