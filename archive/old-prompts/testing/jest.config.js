/**
 * ファイルパス: jest.config.js
 * 
 * Jest テスト設定ファイル
 * テスト全体の設定・構成を管理する中心ファイル
 * 
 * 依存関係:
 * - setupFiles: './jest.setup.js' - 基本環境変数とモックの設定
 * - setupFilesAfterEnv: './__tests__/setup.js' - テスト実行前後の共通処理
 * - reporters: 'custom-reporter.js' - カスタムレポート生成
 * 
 * @file jest.config.js
 * @author プロジェクトチーム
 * @created 2023-07-20
 * @updated 2023-07-25 - 設定の最適化と依存関係の明確化
 * @updated 2023-08-02 - カバレッジレポータ設定の追加
 */

module.exports = {
  // テスト環境
  testEnvironment: 'jsdom',
  
  // カバレッジの設定
  collectCoverage: true,
  coverageDirectory: 'coverage',
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.{js,jsx,ts,tsx}',
    '!src/**/*.test.{js,jsx,ts,tsx}',
    '!**/node_modules/**'
  ],
  
  // カバレッジレポーターの設定 - 複数の形式を同時に出力
  coverageReporters: [
    'json',         // 詳細なJSONフォーマット
    'lcov',         // HTML形式（ブラウザで表示）
    'text',         // コンソール出力用
    'text-summary', // コンソール出力サマリー
    'json-summary'  // 簡易JSON形式
  ],
  
  // カバレッジのしきい値
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 80,
      lines: 80,
      statements: 80
    },
    'src/utils/*.{js,jsx,ts,tsx}': {
      branches: 80,
      functions: 90,
      lines: 90
    },
    'src/components/*.{js,jsx,ts,tsx}': {
      branches: 75,
      functions: 85,
      lines: 85
    }
  },
  
  // テストファイルのパターン
  testMatch: [
    '**/__tests__/**/*.{js,jsx,ts,tsx}',
    '**/?(*.)+(spec|test).{js,jsx,ts,tsx}'
  ],
  
  // 開始前に実行するファイル - 環境変数やモックの基本設定
  setupFiles: ['./jest.setup.js'],
  
  // テスト実行前後のグローバル設定
  setupFilesAfterEnv: ['./__tests__/setup.js'],
  
  // テストタイムアウト設定
  testTimeout: 10000,
  
  // モジュール名のマッピング
  moduleNameMapper: {
    // スタイルとアセットのモック
    '\\.(css|less|scss|sass)$': '<rootDir>/__mocks__/styleMock.js',
    '\\.(gif|ttf|eot|svg|png|jpg|jpeg)$': '<rootDir>/__mocks__/fileMock.js',
    // パスエイリアス
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@components/(.*)$': '<rootDir>/src/components/$1',
    '^@utils/(.*)$': '<rootDir>/src/utils/$1',
    '^@api/(.*)$': '<rootDir>/src/api/$1',
    // axios等のモック化
    '^axios$': '<rootDir>/__mocks__/axios.js'
  },

  // トランスフォーマー設定
  transform: {
    '^.+\\.(js|jsx|ts|tsx)$': ['babel-jest', { configFile: './babel.config.js' }]
  },

  // 変換対象外のパターン
  transformIgnorePatterns: [
    '/node_modules/(?!(@testing-library|some-module-that-needs-to-be-transformed)/)'
  ],
  
  // 並列実行設定
  maxWorkers: '50%',
  
  // テストの詳細レポート
  verbose: true,
  
  // レポート形式
  reporters: [
    'default',
    ['jest-junit', {
      outputDirectory: './test-results',
      outputName: 'junit.xml'
    }],
    ['jest-html-reporter', {
      pageTitle: 'テスト結果',
      outputPath: './test-results/test-report.html',
      includeFailureMsg: true
    }],
    ['<rootDir>/custom-reporter.js', {}]
  ],
  
  // 特定のテストフォルダーの優先度設定
  projects: [
    {
      displayName: 'unit',
      testMatch: ['**/__tests__/unit/**/*.{js,jsx,ts,tsx}'],
      testPathIgnorePatterns: ['/node_modules/']
    },
    {
      displayName: 'integration',
      testMatch: ['**/__tests__/integration/**/*.{js,jsx,ts,tsx}'],
      testPathIgnorePatterns: ['/node_modules/']
    },
    {
      displayName: 'e2e',
      testMatch: ['**/__tests__/e2e/**/*.{js,jsx,ts,tsx}'],
      testPathIgnorePatterns: ['/node_modules/']
    }
  ],
  
  // キャッシュ設定
  cacheDirectory: './.jest-cache',
  
  // エラー表示設定
  errorOnDeprecated: true,
  
  // テスト終了後に強制終了（CI環境用）
  forceExit: true,
  
  // カスタムリゾルバー
  resolver: null
};
