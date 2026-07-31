/**
 * ファイルパス: __tests__/setup.js
 * 
 * Jest テスト実行前後の共通処理設定
 * テスト実行の前後で実行されるグローバルな処理を定義
 * 
 * 注: このファイルはjest.config.jsのsetupFilesAfterEnvで指定されており、
 * 各テストファイルが実行される前に一度だけロードされます
 * 
 * @file __tests__/setup.js
 * @author プロジェクトチーム
 * @created 2023-07-20
 * @updated 2023-07-25 - エラーハンドリング強化、nockの条件付きロード追加
 */

// テスト用のタイムアウト設定
jest.setTimeout(30000); // 30秒

// React Testing Libraryの設定
import '@testing-library/jest-dom';

// エラーハンドリングを改善
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
  // テスト環境では強制終了しない
});

// モックサーバー関連のセットアップ
let mockServer;
try {
  const { setupServer } = require('msw/node');
  const { handlers } = require('./mocks/handlers');
  mockServer = setupServer(...handlers);
} catch (e) {
  console.log('MSW モックサーバーが設定できませんでした。エラー:', e.message);
}

// nockがインストールされている場合のみロード
try {
  const nock = require('nock');
  // nockの自動クリーンアップを設定
  nock.disableNetConnect();
  nock.enableNetConnect('localhost'); // ローカル接続は許可
  
  console.log('nock モックライブラリが有効化されました');
} catch (e) {
  // nockがインストールされていない場合はスキップ
  console.log('nock モックライブラリがインストールされていません');
}

// テスト前の共通処理
beforeAll(async () => {
  console.log('Starting test suite with environment:', process.env.NODE_ENV);
  console.log('Test configuration:');
  console.log('- RUN_E2E_TESTS:', process.env.RUN_E2E_TESTS);
  console.log('- MOCK_API:', process.env.MOCK_API);
  console.log('- SKIP_SLOW_TESTS:', process.env.SKIP_SLOW_TESTS);
  console.log('- COVERAGE_TARGET:', process.env.COVERAGE_TARGET || 'standard');
  
  // MSWモックサーバーを起動
  if (mockServer) {
    mockServer.listen({ onUnhandledRequest: 'warn' });
    console.log('MSW モックサーバーが起動しました');
  }
  
  // テスト実行モードによる設定変更
  if (process.env.MOCK_API === 'true') {
    console.log('API モックモードが有効です - 外部API呼び出しはモック化されます');
  }
  
  if (process.env.DEBUG === 'true') {
    console.log('デバッグモードが有効です - 詳細ログが表示されます');
    // デバッグモードではコンソール出力を復元
    console.log = global.originalConsole.log;
    console.info = global.originalConsole.info;
  }
});

// テスト後の共通処理
afterAll(async () => {
  console.log('Test suite completed');
  
  // MSWサーバーのクリーンアップ
  if (mockServer) {
    mockServer.close();
    console.log('MSW モックサーバーを停止しました');
  }
  
  // Jestのタイマーを確実にクリーンアップ
  jest.useRealTimers();
  
  // nockのクリーンアップ（存在する場合のみ）
  try {
    const nock = require('nock');
    nock.cleanAll();
    nock.enableNetConnect();
    console.log('nock モックがクリーンアップされました');
  } catch (e) {
    // nockがない場合は何もしない
  }
});

// 各テスト後のクリーンアップ
afterEach(() => {
  // タイマーのクリーンアップ
  jest.clearAllTimers();
  
  // MSWハンドラーのリセット
  if (mockServer) {
    mockServer.resetHandlers();
  }
  
  // モックのリセット
  jest.resetAllMocks();
  
  // localStorage と sessionStorage のクリア
  localStorage.clear();
  sessionStorage.clear();
});
