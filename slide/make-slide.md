# 企画書mdファイルからの16:9比率プレゼンテーションスライド生成プロンプト（プロフェッショナル版）

ベテランITコンサルタントの視点から最適化された、提供された企画書のmdファイルから16:9比率のプレゼンテーションスライドをHTMLとCSSで自動生成するシステム。実際のビジネスプレゼンテーションで求められる要素を網羅し、視認性と操作性を最大化します。

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

    /* スライドコンテンツ */
    .slide-content {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      padding: 60px 80px 80px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
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
      font-size: 42px;
      font-weight: 700;
      margin-bottom: 30px;
      letter-spacing: -0.5px;
      line-height: 1.2;
    }

    h2 {
      color: #0066cc;
      font-size: 32px;
      font-weight: 600;
      margin: 20px 0 15px;
      letter-spacing: -0.3px;
    }

    h3 {
      color: #333;
      font-size: 24px;
      font-weight: 500;
      margin: 15px 0 10px;
    }

    p {
      font-size: 18px;
      margin-bottom: 15px;
      line-height: 1.8;
    }

    /* リストスタイル改良 */
    ul, ol {
      margin: 0 0 20px 30px;
    }

    li {
      font-size: 18px;
      margin-bottom: 12px;
      line-height: 1.6;
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
      font-size: 56px;
      margin-bottom: 30px;
      text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    }

    .title-slide .subtitle {
      font-size: 28px;
      margin-bottom: 40px;
      opacity: 0.9;
    }

    .title-slide .author {
      font-size: 22px;
      opacity: 0.8;
    }

    .title-slide .date {
      font-size: 18px;
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
      font-size: 48px;
      color: #003366;
    }

    /* 2カラムレイアウト */
    .two-column {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 40px;
      height: 100%;
    }

    .column {
      display: flex;
      flex-direction: column;
    }

    /* 3カラムレイアウト */
    .three-column {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 30px;
      height: 100%;
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
      margin: 20px 0;
      background-color: white;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      border-radius: 8px;
      overflow: hidden;
    }

    th {
      background-color: #003366;
      color: white;
      font-weight: 600;
      padding: 12px 16px;
      text-align: left;
      font-size: 16px;
    }

    td {
      padding: 10px 16px;
      border-bottom: 1px solid #e0e0e0;
      font-size: 15px;
    }

    tr:last-child td {
      border-bottom: none;
    }

    tr:nth-child(even) {
      background-color: #f8f9fa;
    }

    /* コンパクトテーブル */
    .compact-table {
      font-size: 14px;
    }

    .compact-table th, .compact-table td {
      padding: 6px 10px;
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
      gap: 12px;
      margin-bottom: 16px;
    }

    .icon-list li::before {
      content: "▶";
      color: #0066cc;
      font-weight: bold;
      flex-shrink: 0;
      margin-top: 2px;
    }

    /* カード型レイアウト */
    .card-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 20px;
      margin: 20px 0;
    }

    .card {
      background-color: #f8f9fa;
      border-radius: 8px;
      padding: 20px;
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
      margin-bottom: 12px;
      font-size: 20px;
    }

    /* キーポイント強調ボックス */
    .key-point {
      background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
      border-left: 4px solid #0066cc;
      padding: 20px 25px;
      margin: 20px 0;
      border-radius: 0 8px 8px 0;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    .key-point h3 {
      margin-top: 0;
      color: #003366;
    }

    /* まとめスライド */
    .summary-slide {
      background-color: #f8f9fa;
    }

    .summary-points {
      display: flex;
      flex-direction: column;
      gap: 20px;
      margin-top: 30px;
    }

    .summary-item {
      display: flex;
      align-items: center;
      gap: 20px;
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }

    .summary-number {
      width: 48px;
      height: 48px;
      background-color: #0066cc;
      color: white;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      font-weight: bold;
      flex-shrink: 0;
    }

    /* コールトゥアクション */
    .cta-box {
      background: linear-gradient(135deg, #0066cc 0%, #003366 100%);
      color: white;
      padding: 30px;
      border-radius: 12px;
      text-align: center;
      margin: 30px 0;
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }

    .cta-box h2 {
      color: white;
      margin-bottom: 15px;
    }

    .cta-box p {
      font-size: 20px;
      opacity: 0.9;
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
      padding: 40px;
      border-radius: 12px;
      max-width: 500px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    }

    .help-content h2 {
      margin-top: 0;
      margin-bottom: 20px;
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

    /* プリント対応 */
    @media print {
      body {
        background-color: white;
      }
      
      .slide {
        page-break-after: always;
        position: relative;
        display: block !important;
        opacity: 1 !important;
        transform: none !important;
        margin-bottom: 20px;
      }
      
      .nav-area, .slide-progress, .help-overlay {
        display: none !important;
      }
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
        } else {
          document.exitFullscreen();
        }
      }

      toggleHelp() {
        const helpOverlay = document.getElementById('helpOverlay');
        helpOverlay.style.display = 
          helpOverlay.style.display === 'flex' ? 'none' : 'flex';
      }
    }

    // グローバル関数（HTML内のonclickから呼び出し用）
    let presentationManager;
    
    function navigateSlide(direction) {
      if (presentationManager) {
        presentationManager.navigateSlide(direction);
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

### 6. インタラクティブ要素

#### トランジション効果
- スライド切り替え: スムーズなスライドイン
- 要素アニメーション: 段階的なフェードイン
- 強調効果: ホバー時のハイライト

#### プレゼンテーション機能
- フルスクリーンモード（F キー）
- プレゼンターノート（別ウィンドウ）
- タイマー機能（オプション）
- ポインター/ペンツール（将来実装）

### 7. 実装のベストプラクティス

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

### 8. 出力オプション

#### エクスポート形式
1. **HTML単体ファイル**: すべてのリソースを含む
2. **PDF**: 印刷用に最適化
3. **PowerPoint互換**: PPTXへの変換（別ツール経由）
4. **画像シーケンス**: 各スライドをPNG/JPEGで出力

### 9. 品質チェックリスト

プレゼンテーション生成後、以下の項目を自動チェック：

- [ ] 各スライドが16:9比率で表示されているか
- [ ] スクロールバーが表示されていないか
- [ ] フォントサイズが適切か（最小12px）
- [ ] 画像が適切に配置されているか
- [ ] アニメーションが正常に動作するか
- [ ] ナビゲーションが直感的か
- [ ] カラーコントラストが十分か
- [ ] 情報の階層が明確か

### 10. カスタマイズオプション

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

このプロフェッショナル版の実装により、企画書から自動生成されるプレゼンテーションは、実際のビジネスシーンで即座に使用できる品質となります。
