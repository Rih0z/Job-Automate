/**
 * ファイルパス: scripts/generate-coverage-chart.js
 * 
 * Jest テストカバレッジデータからグラフィカルなチャートを生成するスクリプト
 * テスト結果レポートに埋め込むためのSVGチャートを作成する
 * 
 * @author Portfolio Manager Team
 * @created 2025-05-16
 */

const fs = require('fs');
const path = require('path');

// 色の設定
const COLORS = {
  statements: '#4285F4', // Google Blue
  branches: '#34A853',   // Google Green
  functions: '#FBBC05',  // Google Yellow
  lines: '#EA4335',      // Google Red
  background: '#F8F9FA', // Light gray
  text: '#202124',       // Dark gray
  grid: '#DADCE0',       // Light gray for grid
  threshold: {
    initial: '#FFCDD2',  // Light red
    mid: '#FFECB3',      // Light amber
    final: '#C8E6C9'     // Light green
  }
};

// カバレッジ目標値の設定
const COVERAGE_THRESHOLDS = {
  initial: {
    statements: 30,
    branches: 20,
    functions: 25,
    lines: 30
  },
  mid: {
    statements: 60,
    branches: 50,
    functions: 60,
    lines: 60
  },
  final: {
    statements: 80,
    branches: 70,
    functions: 80,
    lines: 80
  }
};

/**
 * 数値を小数点以下2桁に丸める
 * @param {number} num 丸める数値
 * @returns {number} 丸められた数値
 */
function roundToTwo(num) {
  return Math.round((num + Number.EPSILON) * 100) / 100;
}

/**
 * カバレッジJSONデータを読み込む
 * @returns {Object|null} カバレッジデータまたはnull
 */
function loadCoverageData() {
  try {
    // 詳細結果のJSONファイルパス
    const resultsPath = path.resolve('./test-results/detailed-results.json');
    
    // ファイルが存在しない場合
    if (!fs.existsSync(resultsPath)) {
      console.error('カバレッジデータファイルが見つかりません:', resultsPath);
      return null;
    }
    
    // JSONファイルを読み込み
    const data = JSON.parse(fs.readFileSync(resultsPath, 'utf8'));
    
    // 必要なカバレッジデータを抽出
    return {
      statements: {
        pct: data.coverageMap.total.statements.pct,
        covered: data.coverageMap.total.statements.covered,
        total: data.coverageMap.total.statements.total
      },
      branches: {
        pct: data.coverageMap.total.branches.pct,
        covered: data.coverageMap.total.branches.covered,
        total: data.coverageMap.total.branches.total
      },
      functions: {
        pct: data.coverageMap.total.functions.pct,
        covered: data.coverageMap.total.functions.covered,
        total: data.coverageMap.total.functions.total
      },
      lines: {
        pct: data.coverageMap.total.lines.pct,
        covered: data.coverageMap.total.lines.covered,
        total: data.coverageMap.total.lines.total
      }
    };
  } catch (error) {
    console.error('カバレッジデータの読み込みに失敗しました:', error);
    return null;
  }
}

/**
 * 目標レベルを現在の環境変数から取得
 * @returns {string} 目標レベル（'initial', 'mid', 'final'）
 */
function getCoverageTarget() {
  const target = process.env.COVERAGE_TARGET || 'initial';
  if (!['initial', 'mid', 'final'].includes(target)) {
    console.warn(`不明なカバレッジ目標: ${target}、初期段階を使用します`);
    return 'initial';
  }
  return target;
}

/**
 * 棒グラフSVGを生成
 * @param {Object} coverageData カバレッジデータ
 * @param {string} targetLevel 目標レベル
 * @returns {string} SVG文字列
 */
function generateBarChart(coverageData, targetLevel) {
  // チャートの設定
  const width = 800;
  const height = 400;
  const padding = 60;
  const barWidth = 80;
  const barGap = 70;
  const startX = 120;
  
  // カバレッジデータ配列
  const data = [
    { name: 'ステートメント', value: coverageData.statements.pct, threshold: COVERAGE_THRESHOLDS[targetLevel].statements },
    { name: 'ブランチ', value: coverageData.branches.pct, threshold: COVERAGE_THRESHOLDS[targetLevel].branches },
    { name: '関数', value: coverageData.functions.pct, threshold: COVERAGE_THRESHOLDS[targetLevel].functions },
    { name: '行', value: coverageData.lines.pct, threshold: COVERAGE_THRESHOLDS[targetLevel].lines }
  ];
  
  // Y軸の最大値（最大100%または現在の最大値+10%のいずれか大きい方）
  const maxValue = Math.max(100, Math.ceil((Math.max(...data.map(d => d.value)) + 10) / 10) * 10);
  
  // スケーリング関数
  const scaleY = (value) => height - padding - (value / maxValue) * (height - padding * 2);
  
  // SVG開始
  let svg = `<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">\n`;
  
  // 背景
  svg += `  <rect width="${width}" height="${height}" fill="${COLORS.background}" />\n`;
  
  // タイトル
  svg += `  <text x="${width/2}" y="30" text-anchor="middle" font-family="Arial" font-size="20" font-weight="bold" fill="${COLORS.text}">テストカバレッジ - ${new Date().toLocaleDateString('ja-JP')}</text>\n`;
  svg += `  <text x="${width/2}" y="55" text-anchor="middle" font-family="Arial" font-size="16" fill="${COLORS.text}">目標段階: ${targetLevel === 'initial' ? '初期 (20-30%)' : targetLevel === 'mid' ? '中間 (40-60%)' : '最終 (70-80%)'}</text>\n`;
  
  // Y軸と目盛り
  svg += `  <line x1="${padding}" y1="${padding}" x2="${padding}" y2="${height-padding}" stroke="${COLORS.text}" stroke-width="2" />\n`;
  
  // Y軸のグリッドラインと目盛り
  for (let i = 0; i <= maxValue; i += 10) {
    const y = scaleY(i);
    svg += `  <line x1="${padding-5}" y1="${y}" x2="${width-padding}" y2="${y}" stroke="${COLORS.grid}" stroke-width="1" />\n`;
    svg += `  <text x="${padding-10}" y="${y+5}" text-anchor="end" font-family="Arial" font-size="12" fill="${COLORS.text}">${i}%</text>\n`;
  }
  
  // X軸
  svg += `  <line x1="${padding}" y1="${height-padding}" x2="${width-padding}" y2="${height-padding}" stroke="${COLORS.text}" stroke-width="2" />\n`;
  
  // 目標閾値ライン
  data.forEach((d, i) => {
    const x = startX + i * (barWidth + barGap);
    const y = scaleY(d.threshold);
    
    // 目標閾値の背景（拡張）
    svg += `  <rect x="${x - 15}" y="${y}" width="${barWidth + 30}" height="${height - padding - y}" fill="${COLORS.threshold[targetLevel]}" opacity="0.3" />\n`;
    
    // 目標閾値ライン
    svg += `  <line x1="${x - 15}" y1="${y}" x2="${x + barWidth + 15}" y2="${y}" stroke="${COLORS.text}" stroke-width="2" stroke-dasharray="4" />\n`;
    svg += `  <text x="${x + barWidth/2}" y="${y - 5}" text-anchor="middle" font-family="Arial" font-size="12" fill="${COLORS.text}">${d.threshold}%</text>\n`;
  });
  
  // 棒グラフ
  data.forEach((d, i) => {
    const x = startX + i * (barWidth + barGap);
    const barHeight = (height - padding * 2) * (d.value / maxValue);
    const y = height - padding - barHeight;
    const color = Object.values(COLORS)[i % 4]; // 色を循環使用
    
    // 棒グラフ
    svg += `  <rect x="${x}" y="${y}" width="${barWidth}" height="${barHeight}" fill="${color}" />\n`;
    
    // ラベル (X軸)
    svg += `  <text x="${x + barWidth/2}" y="${height-padding+20}" text-anchor="middle" font-family="Arial" font-size="14" fill="${COLORS.text}">${d.name}</text>\n`;
    
    // 値ラベル
    svg += `  <text x="${x + barWidth/2}" y="${y-5}" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="${COLORS.text}">${roundToTwo(d.value)}%</text>\n`;
    
    // 詳細データ
    svg += `  <text x="${x + barWidth/2}" y="${y-25}" text-anchor="middle" font-family="Arial" font-size="12" fill="${COLORS.text}">${coverageData[d.name.toLowerCase().replace('ステートメント', 'statements').replace('ブランチ', 'branches').replace('関数', 'functions').replace('行', 'lines')].covered}/${coverageData[d.name.toLowerCase().replace('ステートメント', 'statements').replace('ブランチ', 'branches').replace('関数', 'functions').replace('行', 'lines')].total}</text>\n`;
  });
  
  // 凡例
  svg += `  <text x="${width-padding}" y="${padding/2}" text-anchor="end" font-family="Arial" font-size="12" font-style="italic" fill="${COLORS.text}">自動生成: ${new Date().toLocaleTimeString('ja-JP')}</text>\n`;
  
  // SVG終了
  svg += '</svg>';
  
  return svg;
}

/**
 * 折れ線グラフSVGを生成（履歴データを含む）
 * @param {Object} currentData 現在のカバレッジデータ
 * @param {Array} historyData 履歴カバレッジデータ
 * @param {string} targetLevel 目標レベル
 * @returns {string} SVG文字列
 */
function generateLineChart(currentData, historyData, targetLevel) {
  // 履歴データと現在のデータを結合
  const allData = [...historyData, {
    date: new Date().toISOString().split('T')[0],
    statements: currentData.statements.pct,
    branches: currentData.branches.pct,
    functions: currentData.functions.pct,
    lines: currentData.lines.pct,
  }];
  
  // チャートの設定
  const width = 800;
  const height = 400;
  const padding = 60;
  
  // マージンの追加
  const margin = {
    top: 40,
    right: 30,
    bottom: 60,
    left: 60
  };
  
  // 有効な描画領域
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  
  // データポイントの数
  const numPoints = allData.length;
  
  // X軸のスケーリング
  const xScale = (i) => margin.left + (i / (numPoints - 1)) * innerWidth;
  
  // Y軸の最大値
  const maxValue = Math.max(100, Math.ceil((Math.max(
    ...allData.map(d => d.statements),
    ...allData.map(d => d.branches),
    ...allData.map(d => d.functions),
    ...allData.map(d => d.lines),
    COVERAGE_THRESHOLDS[targetLevel].statements,
    COVERAGE_THRESHOLDS[targetLevel].branches,
    COVERAGE_THRESHOLDS[targetLevel].functions,
    COVERAGE_THRESHOLDS[targetLevel].lines
  ) + 10) / 10) * 10);
  
  // Y軸のスケーリング
  const yScale = (value) => margin.top + innerHeight - (value / maxValue) * innerHeight;
  
  // SVG開始
  let svg = `<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">\n`;
  
  // 背景
  svg += `  <rect width="${width}" height="${height}" fill="${COLORS.background}" />\n`;
  
  // タイトル
  svg += `  <text x="${width/2}" y="30" text-anchor="middle" font-family="Arial" font-size="20" font-weight="bold" fill="${COLORS.text}">テストカバレッジ履歴</text>\n`;
  
  // Y軸と目盛り
  svg += `  <line x1="${margin.left}" y1="${margin.top}" x2="${margin.left}" y2="${height-margin.bottom}" stroke="${COLORS.text}" stroke-width="2" />\n`;
  
  // Y軸のグリッドラインと目盛り
  for (let i = 0; i <= maxValue; i += 10) {
    const y = yScale(i);
    svg += `  <line x1="${margin.left-5}" y1="${y}" x2="${width-margin.right}" y2="${y}" stroke="${COLORS.grid}" stroke-width="1" />\n`;
    svg += `  <text x="${margin.left-10}" y="${y+5}" text-anchor="end" font-family="Arial" font-size="12" fill="${COLORS.text}">${i}%</text>\n`;
  }
  
  // X軸
  svg += `  <line x1="${margin.left}" y1="${height-margin.bottom}" x2="${width-margin.right}" y2="${height-margin.bottom}" stroke="${COLORS.text}" stroke-width="2" />\n`;
  
  // X軸ラベル
  allData.forEach((d, i) => {
    const x = xScale(i);
    svg += `  <text x="${x}" y="${height-margin.bottom+20}" text-anchor="middle" font-family="Arial" font-size="12" fill="${COLORS.text}" transform="rotate(-45 ${x} ${height-margin.bottom+20})">${d.date}</text>\n`;
  });
  
  // 目標ライン
  const thresholds = [
    { name: 'Statements', value: COVERAGE_THRESHOLDS[targetLevel].statements, color: COLORS.statements },
    { name: 'Branches', value: COVERAGE_THRESHOLDS[targetLevel].branches, color: COLORS.branches },
    { name: 'Functions', value: COVERAGE_THRESHOLDS[targetLevel].functions, color: COLORS.functions },
    { name: 'Lines', value: COVERAGE_THRESHOLDS[targetLevel].lines, color: COLORS.lines }
  ];
  
  thresholds.forEach((threshold) => {
    const y = yScale(threshold.value);
    svg += `  <line x1="${margin.left}" y1="${y}" x2="${width-margin.right}" y2="${y}" stroke="${threshold.color}" stroke-width="1" stroke-dasharray="4" />\n`;
    svg += `  <text x="${width-margin.right+5}" y="${y+4}" text-anchor="start" font-family="Arial" font-size="10" fill="${threshold.color}">${threshold.name}: ${threshold.value}%</text>\n`;
  });
  
  // 折れ線グラフのデータ系列
  const series = [
    { name: 'Statements', key: 'statements', color: COLORS.statements },
    { name: 'Branches', key: 'branches', color: COLORS.branches },
    { name: 'Functions', key: 'functions', color: COLORS.functions },
    { name: 'Lines', key: 'lines', color: COLORS.lines }
  ];
  
  // 折れ線グラフの描画
  series.forEach((serie) => {
    // 折れ線
    let path = `  <path d="M`;
    allData.forEach((d, i) => {
      const x = xScale(i);
      const y = yScale(d[serie.key]);
      path += `${x},${y} `;
    });
    path += `" fill="none" stroke="${serie.color}" stroke-width="2" />\n`;
    svg += path;
    
    // データポイント
    allData.forEach((d, i) => {
      const x = xScale(i);
      const y = yScale(d[serie.key]);
      svg += `  <circle cx="${x}" cy="${y}" r="4" fill="${serie.color}" />\n`;
      
      // 最新のデータポイントには値を表示
      if (i === allData.length - 1) {
        svg += `  <text x="${x+10}" y="${y}" text-anchor="start" font-family="Arial" font-size="12" font-weight="bold" fill="${serie.color}">${roundToTwo(d[serie.key])}%</text>\n`;
      }
    });
  });
  
  // 凡例
  const legendY = 20;
  const legendSpacing = 120;
  series.forEach((serie, i) => {
    const x = width - margin.right - (series.length - i - 1) * legendSpacing;
    svg += `  <line x1="${x-15}" y1="${legendY}" x2="${x-5}" y2="${legendY}" stroke="${serie.color}" stroke-width="2" />\n`;
    svg += `  <circle cx="${x-10}" cy="${legendY}" r="3" fill="${serie.color}" />\n`;
    svg += `  <text x="${x}" y="${legendY+4}" font-family="Arial" font-size="12" fill="${COLORS.text}">${serie.name}</text>\n`;
  });
  
  // SVG終了
  svg += '</svg>';
  
  return svg;
}

/**
 * カバレッジ履歴データを読み込む
 * @returns {Array} 履歴データ配列
 */
function loadCoverageHistory() {
  const historyFile = path.resolve('./test-results/coverage-history.json');
  
  if (!fs.existsSync(historyFile)) {
    // 履歴ファイルがない場合は空配列を返す
    return [];
  }
  
  try {
    const data = JSON.parse(fs.readFileSync(historyFile, 'utf8'));
    return Array.isArray(data) ? data : [];
  } catch (error) {
    console.error('カバレッジ履歴データの読み込みに失敗しました:', error);
    return [];
  }
}

/**
 * カバレッジ履歴データを保存する
 * @param {Object} currentData 現在のカバレッジデータ
 */
function saveCoverageHistory(currentData) {
  const historyFile = path.resolve('./test-results/coverage-history.json');
  const history = loadCoverageHistory();
  
  // 現在の日付
  const today = new Date().toISOString().split('T')[0];
  
  // 同じ日付のデータがあれば上書き、なければ追加
  const existingIndex = history.findIndex(item => item.date === today);
  
  const newDataPoint = {
    date: today,
    statements: currentData.statements.pct,
    branches: currentData.branches.pct,
    functions: currentData.functions.pct,
    lines: currentData.lines.pct
  };
  
  if (existingIndex >= 0) {
    history[existingIndex] = newDataPoint;
  } else {
    history.push(newDataPoint);
  }
  
  // 履歴を最大30日分に制限
  const limitedHistory = history.slice(-30);
  
  try {
    fs.writeFileSync(historyFile, JSON.stringify(limitedHistory, null, 2));
    console.log('カバレッジ履歴データを保存しました');
  } catch (error) {
    console.error('カバレッジ履歴データの保存に失敗しました:', error);
  }
}

/**
 * SVGチャートをHTMLレポートに埋め込む
 * @param {string} barChartSvg 棒グラフSVG
 * @param {string} lineChartSvg 折れ線グラフSVG
 */
function embedChartsInReport(barChartSvg, lineChartSvg) {
  const reportFile = path.resolve('./test-results/visual-report.html');
  
  if (!fs.existsSync(reportFile)) {
    console.error('ビジュアルレポートファイルが見つかりません:', reportFile);
    return;
  }
  
  try {
    // レポートHTMLを読み込む
    let html = fs.readFileSync(reportFile, 'utf8');
    
    // チャートセクションが既に存在するか確認
    const chartSectionExists = html.includes('<div class="coverage-charts">');
    
    if (chartSectionExists) {
      // 既存のチャートセクションを置き換え
      html = html.replace(
        /<div class="coverage-charts">[\s\S]*?<\/div><!-- end coverage-charts -->/,
        `<div class="coverage-charts">
          <h2>コードカバレッジチャート</h2>
          <div class="chart-container">
            ${barChartSvg}
          </div>
          <div class="chart-container">
            ${lineChartSvg}
          </div>
        </div><!-- end coverage-charts -->`
      );
    } else {
      // チャートセクションを追加
      const insertPosition = html.indexOf('</body>');
      if (insertPosition !== -1) {
        html = html.slice(0, insertPosition) + 
        `<div class="coverage-charts">
          <h2>コードカバレッジチャート</h2>
          <div class="chart-container">
            ${barChartSvg}
          </div>
          <div class="chart-container">
            ${lineChartSvg}
          </div>
        </div><!-- end coverage-charts -->
        ` + 
        html.slice(insertPosition);
      }
    }
    
    // スタイルシートを追加/更新
    if (!html.includes('.coverage-charts')) {
      const stylePosition = html.indexOf('</style>');
      if (stylePosition !== -1) {
        html = html.slice(0, stylePosition) + 
        `
        /* カバレッジチャートのスタイル */
        .coverage-charts {
          margin-top: 30px;
          border-top: 1px solid #eee;
          padding-top: 20px;
        }
        .coverage-charts h2 {
          text-align: center;
          margin-bottom: 20px;
        }
        .chart-container {
          display: flex;
          justify-content: center;
          margin-bottom: 30px;
        }
        ` + 
        html.slice(stylePosition);
      }
    }
    
    // レポートを保存
    fs.writeFileSync(reportFile, html);
    console.log('ビジュアルレポートにチャートを埋め込みました:', reportFile);
  } catch (error) {
    console.error('レポートへのチャート埋め込みに失敗しました:', error);
  }
}

/**
 * メイン処理
 */
function main() {
  console.log('カバレッジチャート生成を開始します...');
  
  // カバレッジデータを読み込む
  const coverageData = loadCoverageData();
  if (!coverageData) {
    console.error('カバレッジデータが取得できないため、処理を終了します');
    process.exit(1);
  }
  
  // カバレッジ目標を取得
  const targetLevel = getCoverageTarget();
  console.log(`カバレッジ目標段階: ${targetLevel}`);
  
  // 棒グラフを生成
  const barChartSvg = generateBarChart(coverageData, targetLevel);
  
  // 履歴データを読み込む
  const historyData = loadCoverageHistory();
  
  // 現在のデータを履歴に保存
  saveCoverageHistory(coverageData);
  
  // 折れ線グラフを生成
  const lineChartSvg = generateLineChart(coverageData, historyData, targetLevel);
  
  // SVGファイルとして保存（オプション）
  const outputDir = path.resolve('./test-results');
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }
  
  fs.writeFileSync(path.join(outputDir, 'coverage-bar-chart.svg'), barChartSvg);
  fs.writeFileSync(path.join(outputDir, 'coverage-line-chart.svg'), lineChartSvg);
  
  console.log('SVGチャートファイルを生成しました');
  
  // レポートに埋め込む
  embedChartsInReport(barChartSvg, lineChartSvg);
  
  console.log('カバレッジチャート生成が完了しました');
}

// スクリプトを実行
main();
