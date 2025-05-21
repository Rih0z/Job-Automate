/**
 * ファイルパス: jest.setup.js
 * 
 * Jest テスト開始前の基本環境設定
 * テスト実行に必要な環境変数のデフォルト値とモックの設定
 * 
 * 注: このファイルはjest.config.jsのsetupFilesで指定されており、
 * 各テストファイルが実行される前に一度だけロードされます
 * 
 * @file jest.setup.js
 * @author プロジェクトチーム
 * @created 2023-07-20
 * @updated 2023-07-25 - 環境変数設定の最適化、コメント追加
 */

// テスト環境を設定 - 各テストで共通の環境変数のデフォルト値を設定
process.env = {
  ...process.env,
  NODE_ENV: process.env.NODE_ENV || 'test',
  API_BASE_URL: process.env.API_BASE_URL || 'http://localhost:3000/api',
  MOCK_API: process.env.MOCK_API || 'true',
  AUTH_TOKEN_KEY: process.env.AUTH_TOKEN_KEY || 'test-auth-token',
  CACHE_STORAGE_KEY: process.env.CACHE_STORAGE_KEY || 'test-cache',
  
  // API設定
  API_TIMEOUT: process.env.API_TIMEOUT || '5000',
  API_RETRY_COUNT: process.env.API_RETRY_COUNT || '3',
  
  // 認証設定
  AUTH_ENABLED: process.env.AUTH_ENABLED || 'true',
  SESSION_DURATION: process.env.SESSION_DURATION || '3600',
  
  // テスト設定
  TEST_TIMEOUT: process.env.TEST_TIMEOUT || '10000',
  SKIP_ANIMATIONS: process.env.SKIP_ANIMATIONS || 'true',
  RUN_SLOW_TESTS: process.env.RUN_SLOW_TESTS || 'false',
};

// Matcherの拡張
expect.extend({
  toBeWithinRange(received, floor, ceiling) {
    const pass = received >= floor && received <= ceiling;
    if (pass) {
      return {
        message: () => `expected ${received} not to be within range ${floor} - ${ceiling}`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected ${received} to be within range ${floor} - ${ceiling}`,
        pass: false,
      };
    }
  },
  toBeValidDate(received) {
    const date = new Date(received);
    const pass = !isNaN(date.getTime());
    if (pass) {
      return {
        message: () => `expected ${received} not to be a valid date`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected ${received} to be a valid date`,
        pass: false,
      };
    }
  },
});

// グローバルモックの設定
global.fetch = jest.fn();
global.localStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  key: jest.fn(),
  length: 0
};
global.sessionStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  key: jest.fn(),
  length: 0
};

// ブラウザAPI モック
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

global.MutationObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  disconnect: jest.fn(),
  takeRecords: jest.fn(),
}));

window.matchMedia = jest.fn().mockImplementation(query => ({
  matches: false,
  media: query,
  onchange: null,
  addListener: jest.fn(),
  removeListener: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  dispatchEvent: jest.fn(),
}));

// コンソール出力をモック化（静かなテスト実行のため）
global.originalConsole = {
  log: console.log,
  error: console.error,
  warn: console.warn,
  info: console.info
};

// テスト中は警告・エラーのみ出力（CI環境では調整可能）
if (process.env.CI !== 'true' && process.env.DEBUG !== 'true') {
  console.log = jest.fn();
  console.info = jest.fn();
}

// 日付のモック
jest.spyOn(global.Date, 'now').mockImplementation(() => 1689842400000); // 2023-07-20T10:00:00.000Z

// テスト開始時のログ（デバッグに役立つ情報）
console.log('------------- テスト環境設定 -------------');
console.log('NODE_ENV:', process.env.NODE_ENV);
console.log('API_BASE_URL:', process.env.API_BASE_URL);
console.log('現在のテスト日時:', new Date(Date.now()).toISOString());
console.log('-----------------------------------------');
