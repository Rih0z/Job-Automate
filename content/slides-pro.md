# 企画書mdファイルからの16:9比率プレゼンテーションスライド生成プロンプト（プロフェッショナル版 v4.1）

ベテランITコンサルタントの視点から最適化された、提供された企画書のmdファイルから16:9比率のプレゼンテーションスライドをHTMLとCSSで自動生成するシステム。実際のビジネスプレゼンテーションで求められる要素を網羅し、視認性と操作性を最大化します。

---

## ⚠️ 重要：v4.1での改善点（視認性・表示崩れ対策）

### 問題点と対策

| 問題 | 原因 | 対策 |
|------|------|------|
| 文字が読めない | 背景色と文字色のコントラスト不足 | すべての要素に明示的な色指定 |
| コンテンツがはみ出す | 1スライドに情報を詰め込みすぎ | 情報量ガイドラインを設定 |
| CSS変数が効かない | 環境によって変数が解決されない | 直接カラーコードを使用 |
| 印刷時に崩れる | 印刷用スタイルの不備 | 印刷用スタイルを徹底 |

### 絶対ルール
1. **CSS変数（var(--xxx)）は使用禁止** → 直接カラーコードを記述
2. **すべてのテキスト要素に明示的なcolorを指定**
3. **背景色と文字色のコントラスト比4.5:1以上を確保**
4. **1スライドの情報量を制限**（詳細は後述）
5. **スクロールバーを必ず有効化**（長い場合の保険）

---

## 📐 フォントサイズガイドライン（v4.1）

プレゼンテーションは遠くから見ることも多いため、適切なサイズを維持します。

| 要素 | 推奨サイズ | 最小サイズ | 備考 |
|------|-----------|-----------|------|
| スライドタイトル（h1） | 36px | 32px | 1行に収める |
| セクション見出し（h2） | 26px | 24px | 明確に区別 |
| 小見出し（h3） | 20px | 18px | カード内など |
| 本文（p, li） | 20px | 18px | 読みやすさ重視 |
| 補足・注釈 | 16px | 14px | 控えめに |

---

## 📊 1スライドあたりの情報量ガイドライン（v4.1 新規）

**はみ出し防止の鍵は「フォントを小さくする」ではなく「情報を減らす」**

### 基本ルール

| 要素 | 上限 |
|------|------|
| 箇条書き（トップレベル） | **5項目まで** |
| 箇条書き（ネスト含む合計） | **10項目まで** |
| テーブルの行数 | **6行まで** |
| カードの数 | **4枚まで** |
| 段落テキスト | **3段落・計150文字まで** |

### スライド分割の判断基準

以下のいずれかに該当したら **スライドを分割**：

```
✅ 箇条書きが6項目以上
✅ テーブルが7行以上
✅ カードが5枚以上
✅ テキストが200文字以上
✅ 2カラムの両方にカードが3枚以上ずつ
```

### 情報量別のレイアウト選択

| 情報量 | 推奨レイアウト |
|--------|---------------|
| 少ない（要点1-2個） | センター配置、大きめフォント |
| 標準（要点3-5個） | 1カラム or 2カラム |
| 多い（要点6個以上） | **スライドを分割** |

---

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

---

## 基本設定（プロフェッショナル仕様 v4.1）

```html
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>プレゼンテーションタイトル</title>
  <style>
    /* ============================================
       v4.1: 視認性・表示崩れ対策版
       - CSS変数を使用せず直接カラーコード指定
       - すべての要素に明示的な色指定
       - コントラスト比を確保
       - フォントサイズを適正化（本文20px）
       ============================================ */
    
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
      font-family: "游ゴシック", "Yu Gothic", "Noto Sans JP", "Hiragino Kaku Gothic ProN", "メイリオ", sans-serif;
    }

    body {
      background-color: #1a1a1a;
      color: #333333;
      line-height: 1.6;
      overflow: hidden;
      height: 100vh;
      display: flex;
      justify-content: center;
      align-items: center;
    }

    /* メインコンテナ */
    .presentation-container {
      width: 100%;
      height: 100%;
      max-width: 1920px;
      max-height: 1080px;
      position: relative;
      background-color: #000000;
      box-shadow: 0 0 50px rgba(0, 0, 0, 0.8);
    }

    /* ============================================
       スライド基本スタイル
       重要: background-colorとcolorを必ず明示
       ============================================ */
    .slide {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background-color: #ffffff;
      color: #333333;
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

    /* スライドコンテンツ - スクロールバー有効（保険） */
    .slide-content {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      padding: 50px 70px 60px;
      overflow-y: auto;
      overflow-x: hidden;
      display: flex;
      flex-direction: column;
      background-color: #ffffff;
      color: #333333;
    }

    /* スクロールバーのカスタムスタイル（WebKit系） */
    .slide-content::-webkit-scrollbar {
      width: 8px;
    }

    .slide-content::-webkit-scrollbar-track {
      background: #f1f1f1;
      border-radius: 4px;
    }

    .slide-content::-webkit-scrollbar-thumb {
      background: #cccccc;
      border-radius: 4px;
    }

    .slide-content::-webkit-scrollbar-thumb:hover {
      background: #0066cc;
    }

    /* Firefox用スクロールバー */
    .slide-content {
      scrollbar-width: thin;
      scrollbar-color: #cccccc #f1f1f1;
    }

    /* ナビゲーション */
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

    .nav-prev { left: 0; }
    .nav-next { right: 0; }

    /* プログレスバー */
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
      color: #999999;
      z-index: 101;
    }

    /* ============================================
       タイポグラフィ（v4.1: 適正サイズ）
       重要: 必ずcolorを明示的に指定
       ============================================ */
    h1 {
      color: #003366;
      font-size: 36px;
      font-weight: 700;
      margin-bottom: 25px;
      padding-bottom: 12px;
      border-bottom: 3px solid #0066cc;
      line-height: 1.3;
    }

    h2 {
      color: #0066cc;
      font-size: 26px;
      font-weight: 600;
      margin: 15px 0 12px;
    }

    h3 {
      color: #333333;
      font-size: 20px;
      font-weight: 600;
      margin: 12px 0 8px;
    }

    h4 {
      color: #444444;
      font-size: 18px;
      font-weight: 600;
      margin: 10px 0 6px;
    }

    p {
      color: #333333;
      font-size: 20px;
      margin-bottom: 12px;
      line-height: 1.7;
    }

    ul, ol {
      margin: 8px 0 15px 30px;
    }

    li {
      color: #333333;
      font-size: 20px;
      margin-bottom: 8px;
      line-height: 1.5;
    }

    strong {
      color: #0066cc;
      font-weight: 600;
    }

    /* ============================================
       タイトルスライド（v4.1: 視認性確保）
       重要: 濃い背景 + 白文字を徹底
       ============================================ */
    .title-slide {
      background: linear-gradient(135deg, #003366 0%, #0066cc 100%);
    }

    .title-slide .slide-content {
      justify-content: center;
      align-items: center;
      text-align: center;
      background: transparent;
    }

    /* タイトルスライド内のすべてのテキストを白に */
    .title-slide h1 {
      color: #ffffff;
      font-size: 48px;
      margin-bottom: 20px;
      border: none;
      padding: 0;
      text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }

    .title-slide .subtitle {
      color: #e0e0e0;
      font-size: 24px;
      margin-bottom: 30px;
    }

    .title-slide .author {
      color: #cccccc;
      font-size: 20px;
    }

    .title-slide .date {
      color: #aaaaaa;
      font-size: 16px;
      margin-top: 15px;
    }

    .title-slide p {
      color: #e0e0e0;
    }

    .title-slide .logos {
      display: flex;
      gap: 25px;
      align-items: center;
      margin-bottom: 30px;
    }

    .title-slide .logo {
      padding: 10px 24px;
      border-radius: 6px;
      font-weight: 700;
      font-size: 18px;
      color: #ffffff;
    }

    .title-slide .times {
      color: #888888;
      font-size: 24px;
    }

    /* ============================================
       セクション区切りスライド
       ============================================ */
    .section-divider {
      background: linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%);
    }

    .section-divider .slide-content {
      justify-content: center;
      padding-left: 80px;
      background: transparent;
    }

    .section-divider h1 {
      font-size: 40px;
      color: #003366;
      border: none;
      border-left: 6px solid #0066cc;
      padding-left: 25px;
      line-height: 1.4;
    }

    /* ============================================
       レイアウト
       ============================================ */
    .two-column {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 40px;
      flex: 1;
    }

    .three-column {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 30px;
      flex: 1;
    }

    .column {
      display: flex;
      flex-direction: column;
    }

    /* ============================================
       カード（v4.1: 色を明示、サイズ適正化）
       ============================================ */
    .card {
      background-color: #f8f8f8;
      border-radius: 8px;
      padding: 18px 20px;
      margin-bottom: 15px;
      border-left: 4px solid #0066cc;
    }

    .card h3 {
      color: #0066cc;
      margin-top: 0;
      margin-bottom: 10px;
      font-size: 20px;
    }

    .card h4 {
      color: #003366;
      margin-top: 0;
      margin-bottom: 8px;
      font-size: 18px;
    }

    .card p {
      color: #333333;
      font-size: 18px;
      margin-bottom: 8px;
    }

    .card ul {
      margin: 8px 0 8px 25px;
    }

    .card li {
      color: #333333;
      font-size: 18px;
      margin-bottom: 5px;
    }

    /* カードのバリエーション */
    .card.accent {
      border-left-color: #ff6600;
    }

    .card.accent h3 {
      color: #e65100;
    }

    .card.success {
      border-left-color: #00a651;
    }

    .card.success h3 {
      color: #00a651;
    }

    /* ============================================
       キーポイント強調ボックス
       ============================================ */
    .key-point {
      background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
      border-left: 5px solid #0066cc;
      padding: 18px 22px;
      margin: 15px 0;
      border-radius: 0 8px 8px 0;
    }

    .key-point h3 {
      color: #003366;
      margin-top: 0;
      margin-bottom: 10px;
      font-size: 22px;
    }

    .key-point p {
      color: #333333;
      font-size: 20px;
      margin-bottom: 8px;
    }

    .key-point ul {
      margin: 8px 0 8px 25px;
    }

    .key-point li {
      color: #333333;
      font-size: 18px;
    }

    /* ============================================
       ハイライトボックス
       ============================================ */
    .highlight {
      background-color: #fffbeb;
      border: 1px solid #f5a623;
      border-radius: 8px;
      padding: 15px 20px;
      margin: 15px 0;
    }

    .highlight h4 {
      color: #b45309;
      margin: 0 0 8px 0;
      font-size: 20px;
    }

    .highlight p {
      color: #333333;
      font-size: 18px;
      margin: 0;
    }

    .highlight ul {
      margin: 8px 0 0 25px;
    }

    .highlight li {
      color: #333333;
      font-size: 18px;
    }

    /* ============================================
       CTA ボックス（v4.1: 内部テキストすべて白）
       ============================================ */
    .cta-box {
      background: linear-gradient(135deg, #0066cc 0%, #003366 100%);
      padding: 25px;
      border-radius: 12px;
      text-align: center;
      margin: 20px 0;
    }

    .cta-box h2 {
      color: #ffffff;
      margin: 0 0 12px 0;
      font-size: 28px;
    }

    .cta-box p {
      color: #ffffff;
      font-size: 20px;
      margin: 0;
    }

    .cta-box strong {
      color: #ffffff;
    }

    /* ============================================
       テーブル
       ============================================ */
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 15px 0;
      font-size: 18px;
      background-color: #ffffff;
      border-radius: 8px;
      overflow: hidden;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    th {
      background-color: #003366;
      color: #ffffff;
      font-weight: 600;
      padding: 12px 15px;
      text-align: left;
    }

    td {
      color: #333333;
      padding: 10px 15px;
      border-bottom: 1px solid #e0e0e0;
    }

    tr:last-child td {
      border-bottom: none;
    }

    tr:nth-child(even) {
      background-color: #f8f8f8;
    }

    /* ============================================
       ロードマップ
       ============================================ */
    .roadmap {
      display: flex;
      flex-direction: column;
      gap: 15px;
      margin: 20px 0;
      position: relative;
      padding-left: 35px;
    }

    .timeline-line {
      position: absolute;
      left: 14px;
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
      left: -26px;
      width: 14px;
      height: 14px;
      background-color: #0066cc;
      border: 3px solid #ffffff;
      border-radius: 50%;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }

    .roadmap-content {
      background-color: #f8f8f8;
      border-left: 4px solid #0066cc;
      padding: 15px 20px;
      border-radius: 0 8px 8px 0;
      flex: 1;
    }

    .roadmap-content h3 {
      color: #003366;
      margin: 0 0 6px 0;
      font-size: 20px;
    }

    .roadmap-content p {
      color: #666666;
      margin: 0;
      font-size: 18px;
    }

    /* ============================================
       参加者リスト
       ============================================ */
    .participant-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 40px;
    }

    .participant-section h2 {
      margin-bottom: 15px;
    }

    .badge {
      display: inline-block;
      padding: 6px 14px;
      border-radius: 4px;
      font-size: 14px;
      font-weight: 600;
      color: #ffffff;
    }

    .badge.primary {
      background-color: #0066cc;
    }

    .badge.accent {
      background-color: #ff6600;
    }

    .badge.success {
      background-color: #00a651;
    }

    .participant-list {
      list-style: none;
      margin: 0;
    }

    .participant-list li {
      padding: 10px 15px;
      background-color: #f8f8f8;
      margin-bottom: 8px;
      border-radius: 6px;
      border-left: 4px solid #dddddd;
    }

    .participant-list.primary li {
      border-left-color: #0066cc;
    }

    .participant-list.accent li {
      border-left-color: #ff6600;
    }

    .participant-list .name {
      color: #222222;
      font-weight: 600;
      display: block;
      font-size: 18px;
    }

    .participant-list .role {
      color: #666666;
      font-size: 14px;
    }

    /* ============================================
       サマリー（まとめスライド）v4.1強化版
       ============================================ */
    .summary-slide {
      background-color: #f8f9fa;
    }

    .summary-slide .slide-content {
      background-color: #f8f9fa;
    }

    .summary-item {
      display: flex;
      gap: 18px;
      background-color: #ffffff;
      padding: 18px 20px;
      margin-bottom: 15px;
      border-radius: 8px;
      align-items: center;
      box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    .summary-number {
      width: 40px;
      height: 40px;
      background-color: #0066cc;
      color: #ffffff;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 20px;
      flex-shrink: 0;
    }

    .summary-text {
      flex: 1;
    }

    .summary-text h3 {
      color: #003366;
      margin: 0 0 5px 0;
      font-size: 20px;
    }

    .summary-text p {
      color: #555555;
      margin: 0;
      font-size: 16px;
    }

    /* ページ番号参照 */
    .summary-page {
      color: #0066cc;
      font-size: 16px;
      font-weight: 600;
      white-space: nowrap;
      padding: 6px 12px;
      background-color: #e3f2fd;
      border-radius: 20px;
    }

    /* Next Action */
    .next-action {
      background: linear-gradient(135deg, #0066cc 0%, #003366 100%);
      padding: 20px 25px;
      border-radius: 10px;
      margin-top: 20px;
    }

    .next-action h3 {
      color: #ffffff;
      margin: 0 0 8px 0;
      font-size: 20px;
    }

    .next-action p {
      color: #ffffff;
      margin: 0;
      font-size: 18px;
    }

    .next-action ul {
      margin: 10px 0 0 25px;
    }

    .next-action li {
      color: #ffffff;
      font-size: 18px;
    }

    /* ============================================
       用語解説
       ============================================ */
    .glossary-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
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
      font-size: 16px;
    }

    .glossary-item p {
      color: #333333;
      margin: 0;
      font-size: 16px;
    }

    /* ============================================
       アニメーション
       ============================================ */
    @keyframes fadeInUp {
      from {
        opacity: 0;
        transform: translateY(15px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .slide.active .animate-item {
      animation: fadeInUp 0.5s ease-out forwards;
    }

    .animate-item:nth-child(1) { animation-delay: 0.1s; }
    .animate-item:nth-child(2) { animation-delay: 0.15s; }
    .animate-item:nth-child(3) { animation-delay: 0.2s; }
    .animate-item:nth-child(4) { animation-delay: 0.25s; }
    .animate-item:nth-child(5) { animation-delay: 0.3s; }
    .animate-item:nth-child(6) { animation-delay: 0.35s; }

    /* ============================================
       PDF出力ボタン
       ============================================ */
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
    }

    .pdf-export-btn svg {
      width: 24px;
      height: 24px;
      fill: #ffffff;
    }

    .pdf-export-btn::after {
      content: 'PDF出力';
      position: absolute;
      bottom: 100%;
      left: 50%;
      transform: translateX(-50%);
      background-color: rgba(0, 0, 0, 0.8);
      color: #ffffff;
      padding: 5px 10px;
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

    /* ============================================
       ヘルプオーバーレイ
       ============================================ */
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
      background-color: #ffffff;
      padding: 30px;
      border-radius: 12px;
      max-width: 420px;
    }

    .help-content h2 {
      color: #003366;
      margin-top: 0;
      margin-bottom: 20px;
      font-size: 22px;
    }

    .shortcut-list {
      list-style: none;
      margin: 0;
    }

    .shortcut-list li {
      color: #333333;
      display: flex;
      justify-content: space-between;
      margin-bottom: 10px;
      padding: 8px 12px;
      background-color: #f5f5f5;
      border-radius: 6px;
      font-size: 14px;
    }

    .shortcut-key {
      font-family: monospace;
      background-color: #e0e0e0;
      color: #333333;
      padding: 3px 8px;
      border-radius: 4px;
      font-weight: bold;
    }

    /* ============================================
       レスポンシブ対応
       ============================================ */
    @media (max-width: 1024px) {
      .slide-content {
        padding: 35px 45px 50px;
      }
      
      h1 { font-size: 30px; }
      h2 { font-size: 22px; }
      h3 { font-size: 18px; }
      p, li { font-size: 18px; }
      
      .two-column, .participant-grid, .glossary-grid {
        grid-template-columns: 1fr;
      }
      
      .nav-area {
        width: 20%;
      }
    }

    /* ============================================
       印刷・PDF出力用スタイル（v4.1改善版）
       ============================================ */
    @media print {
      * {
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
        color-adjust: exact !important;
      }

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
        background-color: #ffffff !important;
        overflow: visible;
      }

      .presentation-container {
        width: 287mm;
        height: auto;
        max-width: none;
        max-height: none;
        margin: 0;
        padding: 0;
        background-color: #ffffff !important;
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
        height: 161mm;
        page-break-after: always;
        page-break-inside: avoid;
        break-after: page;
        break-inside: avoid;
        margin: 0 auto 5mm auto;
        padding: 0;
        position: relative !important;
        background-color: #ffffff !important;
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
        padding: 10mm 12mm 12mm;
        overflow: hidden !important;
        height: 100% !important;
        box-sizing: border-box;
      }

      /* 印刷用フォントサイズ調整 */
      h1 { font-size: 28px !important; }
      h2 { font-size: 22px !important; }
      h3 { font-size: 18px !important; }
      p, li { font-size: 16px !important; }

      /* タイトルスライドの背景と文字色を保持 */
      .title-slide {
        background: linear-gradient(135deg, #003366 0%, #0066cc 100%) !important;
      }

      .title-slide .slide-content {
        background: transparent !important;
      }

      .title-slide h1 { font-size: 36px !important; }
      .title-slide .subtitle { font-size: 20px !important; }

      .title-slide h1,
      .title-slide .subtitle,
      .title-slide .author,
      .title-slide .date,
      .title-slide p {
        color: #ffffff !important;
      }

      /* セクション区切りの背景保持 */
      .section-divider {
        background: linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%) !important;
      }

      .section-divider .slide-content {
        background: transparent !important;
      }

      .section-divider h1 {
        font-size: 32px !important;
      }

      /* CTAボックス */
      .cta-box {
        background: linear-gradient(135deg, #0066cc 0%, #003366 100%) !important;
      }

      .cta-box h2,
      .cta-box p,
      .cta-box strong {
        color: #ffffff !important;
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
  </style>
</head>
<body>
  <div class="presentation-container">
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
          <li><span>次のスライド</span><span><span class="shortcut-key">→</span> / <span class="shortcut-key">Space</span></span></li>
          <li><span>前のスライド</span><span><span class="shortcut-key">←</span> / <span class="shortcut-key">Backspace</span></span></li>
          <li><span>最初のスライド</span><span><span class="shortcut-key">Home</span></span></li>
          <li><span>最後のスライド</span><span><span class="shortcut-key">End</span></span></li>
          <li><span>フルスクリーン</span><span><span class="shortcut-key">F</span></span></li>
          <li><span>ヘルプ</span><span><span class="shortcut-key">?</span></span></li>
        </ul>
      </div>
    </div>
  </div>

  <script>
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
        document.addEventListener('keydown', (e) => this.handleKeyPress(e));
        
        let touchStartX = 0;
        document.addEventListener('touchstart', (e) => {
          touchStartX = e.touches[0].clientX;
        });
        
        document.addEventListener('touchend', (e) => {
          const diff = touchStartX - e.changedTouches[0].clientX;
          if (Math.abs(diff) > 50) {
            this.navigateSlide(diff > 0 ? 1 : -1);
          }
        });
        
        document.getElementById('helpOverlay').addEventListener('click', (e) => {
          if (e.target.id === 'helpOverlay') this.toggleHelp();
        });
      }

      handleKeyPress(e) {
        switch(e.key) {
          case 'ArrowRight': case ' ': e.preventDefault(); this.navigateSlide(1); break;
          case 'ArrowLeft': case 'Backspace': e.preventDefault(); this.navigateSlide(-1); break;
          case 'Home': e.preventDefault(); this.showSlide(0); break;
          case 'End': e.preventDefault(); this.showSlide(this.totalSlides - 1); break;
          case 'f': case 'F': e.preventDefault(); this.toggleFullscreen(); break;
          case '?': e.preventDefault(); this.toggleHelp(); break;
          case 'Escape': 
            if (document.getElementById('helpOverlay').style.display === 'flex') this.toggleHelp();
            break;
        }
      }

      navigateSlide(direction) {
        const newSlide = this.currentSlide + direction;
        if (newSlide >= 0 && newSlide < this.totalSlides) this.showSlide(newSlide);
      }

      showSlide(index) {
        if (this.slides[this.currentSlide]) {
          this.slides[this.currentSlide].classList.remove('active');
          this.slides[this.currentSlide].classList.add('prev');
        }
        
        setTimeout(() => {
          this.slides.forEach(slide => slide.classList.remove('active', 'prev'));
          this.slides[index].classList.add('active');
          this.currentSlide = index;
          this.updateSlideNumber();
          this.updateProgressBar();
          
          const content = this.slides[index].querySelector('.slide-content');
          if (content) content.scrollTop = 0;
        }, 10);
      }

      updateSlideNumber() {
        document.getElementById('slideNumber').textContent = `${this.currentSlide + 1} / ${this.totalSlides}`;
      }

      updateProgressBar() {
        document.getElementById('progressBar').style.width = `${((this.currentSlide + 1) / this.totalSlides) * 100}%`;
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
        const overlay = document.getElementById('helpOverlay');
        overlay.style.display = overlay.style.display === 'flex' ? 'none' : 'flex';
      }

      exportToPDF() {
        if (confirm('📄 PDF出力の設定確認\n\n印刷ダイアログで以下を設定してください：\n\n✅ 用紙の向き：「横」（Landscape）\n✅ 用紙サイズ：A4\n✅ 余白：なし または 最小\n✅ 背景のグラフィック：オン\n\n続行しますか？')) {
          window.print();
        }
      }
    }

    let presentationManager;
    function navigateSlide(direction) { if (presentationManager) presentationManager.navigateSlide(direction); }
    function exportToPDF() { if (presentationManager) presentationManager.exportToPDF(); }
    document.addEventListener('DOMContentLoaded', () => { presentationManager = new PresentationManager(); });
  </script>
</body>
</html>
```

---

## v4.1 コンテンツガイドライン

### フォントサイズ（v4.1 適正化）

| 要素 | 画面表示 | 印刷時 |
|------|----------|--------|
| タイトル（h1） | 36px | 28px |
| タイトルスライドh1 | 48px | 36px |
| 見出し（h2） | 26px | 22px |
| 小見出し（h3） | 20px | 18px |
| 本文（p, li） | 20px | 16px |
| 補足・注釈 | 16px | 14px |

### 色の組み合わせルール

```
【白背景 (#ffffff) の場合】
- 見出し: #003366（濃紺）または #0066cc（青）
- 本文: #333333（濃いグレー）
- 強調: #0066cc（青）

【濃い背景 (#003366等) の場合】
- すべてのテキスト: #ffffff（白）
- 副題: #e0e0e0（薄いグレー）
- 補足: #aaaaaa（グレー）

【グレー背景 (#f5f5f5等) の場合】
- 見出し: #003366（濃紺）
- 本文: #333333（濃いグレー）
```

### 禁止事項

1. ❌ CSS変数 `var(--xxx)` の使用
2. ❌ `color: white` の曖昧な記述（`#ffffff` を使用）
3. ❌ 背景色と同系色の文字色
4. ❌ 1スライドに6項目以上の箇条書き
5. ❌ スクロールバーの無効化
6. ❌ 最終スライドを「ご清聴ありがとうございました」だけで終わらせる

---

## 📋 最終スライド（まとめ）のガイドライン（v4.1 新規）

**最終スライドは「Thank You」ではなく、発表内容のサマリーとする**

### 必須要素

1. **重要ポイント3〜5個**（箇条書き）
2. **各ポイントの参照ページ番号**（詳細を見返せるように）
3. **Next Action / 次のステップ**（あれば）

### 推奨フォーマット

```html
<!-- 最終スライド: まとめ -->
<div class="slide summary-slide">
  <div class="slide-content">
    <h1>まとめ</h1>
    
    <div class="summary-item">
      <div class="summary-number">1</div>
      <div class="summary-text">
        <h3>重要ポイント1のタイトル</h3>
        <p>簡潔な説明文（1〜2行）</p>
      </div>
      <div class="summary-page">→ p.5</div>
    </div>
    
    <div class="summary-item">
      <div class="summary-number">2</div>
      <div class="summary-text">
        <h3>重要ポイント2のタイトル</h3>
        <p>簡潔な説明文（1〜2行）</p>
      </div>
      <div class="summary-page">→ p.8</div>
    </div>
    
    <div class="summary-item">
      <div class="summary-number">3</div>
      <div class="summary-text">
        <h3>重要ポイント3のタイトル</h3>
        <p>簡潔な説明文（1〜2行）</p>
      </div>
      <div class="summary-page">→ p.12</div>
    </div>
    
    <!-- Next Actionがあれば -->
    <div class="next-action">
      <h3>Next Action</h3>
      <p>次のステップの内容</p>
    </div>
  </div>
</div>
```

### まとめスライド用CSS

```css
/* まとめスライド */
.summary-slide {
  background-color: #f8f9fa;
}

.summary-slide .slide-content {
  background-color: #f8f9fa;
}

.summary-item {
  display: flex;
  gap: 18px;
  background-color: #ffffff;
  padding: 18px 20px;
  margin-bottom: 15px;
  border-radius: 8px;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.summary-number {
  width: 40px;
  height: 40px;
  background-color: #0066cc;
  color: #ffffff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 20px;
  flex-shrink: 0;
}

.summary-text {
  flex: 1;
}

.summary-text h3 {
  color: #003366;
  margin: 0 0 5px 0;
  font-size: 20px;
}

.summary-text p {
  color: #555555;
  margin: 0;
  font-size: 16px;
}

/* ページ番号参照 */
.summary-page {
  color: #0066cc;
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap;
  padding: 6px 12px;
  background-color: #e3f2fd;
  border-radius: 20px;
}

/* Next Action */
.next-action {
  background: linear-gradient(135deg, #0066cc 0%, #003366 100%);
  padding: 20px 25px;
  border-radius: 10px;
  margin-top: 20px;
}

.next-action h3 {
  color: #ffffff;
  margin: 0 0 8px 0;
  font-size: 20px;
}

.next-action p {
  color: #ffffff;
  margin: 0;
  font-size: 18px;
}

.next-action ul {
  margin: 10px 0 0 25px;
}

.next-action li {
  color: #ffffff;
  font-size: 18px;
}
```

### 良い例 vs 悪い例

**❌ 悪い例（避けるべき）**
```
Thank You
ご清聴ありがとうございました
```
→ 情報価値がない、聴衆が内容を忘れる

**✅ 良い例**
```
まとめ

1. Ansible v2.6への直接移行を推奨 → p.12
   EDA、自己修復、Lightspeed等のAI機能を活用

2. Satellite + Ansible統合で一元管理 → p.15
   サイロ化した顧客システムを統合

3. 非接続環境でのAI機能が課題 → p.13
   Air-gapped環境での動作検証が必要

4. 商流は日本経由 → p.17
   Red Hat Japan経由での契約が想定

Next Action: Deep Diveセッションの日程調整
```
→ 一目で重要ポイントがわかる、詳細ページに戻れる

---

## 品質チェックリスト（v4.1）

プレゼンテーション生成後、以下を必ず確認：

### 視認性チェック
- [ ] タイトルスライドの文字が白色で表示されているか
- [ ] 通常スライドの文字が濃い色で表示されているか
- [ ] すべてのカード内テキストが読めるか
- [ ] CTAボックス内のテキストが白色か
- [ ] 遠くからでも読めるフォントサイズか

### レイアウトチェック
- [ ] 1スライドの箇条書きが5項目以内か
- [ ] テーブルが6行以内か
- [ ] コンテンツがスライド内に収まっているか
- [ ] スクロールバーが機能するか（長いコンテンツ時）

### 最終スライドチェック
- [ ] 「Thank You」だけで終わっていないか
- [ ] 重要ポイントが3〜5個まとめられているか
- [ ] 各ポイントに参照ページ番号があるか
- [ ] Next Action/次のステップが記載されているか（あれば）

### 機能チェック
- [ ] ← → キーでスライド移動できるか
- [ ] PDF出力ボタンが機能するか
- [ ] プログレスバーが更新されるか
- [ ] スライド番号が正しいか

---

## 更新履歴

### v4.1 (2026-01-22)
- **フォントサイズ適正化**: 本文を20px、見出しを適切なサイズに変更
- **情報量ガイドライン追加**: 1スライドあたりの上限を明確化
- **スライド分割基準**: はみ出し防止のための判断基準を追加
- **最終スライドガイドライン追加**: 「Thank You」ではなくサマリー形式に
- **ページ番号参照**: まとめスライドに詳細ページへの参照を追加
- **Next Actionセクション**: 次のステップを明示するスタイル追加
- **パディング調整**: スライドコンテンツの余白を拡大

### v4 (2026-01-21)
- CSS変数廃止、直接カラーコード指定
- 視認性強化、コントラスト確保

### v3 (2025-11-25)
- 印刷90度回転バグ完全修正

### v2 (2025-11-25)
- スクロールバー追加
- cta-box文字色修正

### v1 (初版)
- 基本的なスライド生成機能
