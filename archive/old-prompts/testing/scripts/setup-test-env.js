/**
 * テスト環境セットアップスクリプト
 * DynamoDB Localの起動、テーブル作成、環境変数設定を自動化
 * 
 * @file scripts/setup-test-env.js
 * @updated 2025-05-15 - エラーハンドリング強化、設定の最適化
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// 色の設定
const colors = {
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  reset: '\x1b[0m'
};

// ログ関数
const log = {
  info: message => console.log(`${colors.blue}[INFO]${colors.reset} ${message}`),
  success: message => console.log(`${colors.green}[SUCCESS]${colors.reset} ${message}`),
  warning: message => console.log(`${colors.yellow}[WARNING]${colors.reset} ${message}`),
  error: message => console.log(`${colors.red}[ERROR]${colors.reset} ${message}`),
  step: message => console.log(`${colors.cyan}[STEP]${colors.reset} ${message}`)
};

// AWS SDK の読み込み（オフライン環境に対応）
let DynamoDBClient;
let CreateTableCommand;
let ListTablesCommand;
let dynamodbAvailable = false;
try {
  ({ DynamoDBClient, CreateTableCommand, ListTablesCommand } = require('@aws-sdk/client-dynamodb'));
  dynamodbAvailable = true;
} catch (err) {
  log.warning('@aws-sdk/client-dynamodb が見つかりません。DynamoDB 関連の処理をスキップします');
}

/**
 * DynamoDB Local が起動しているかチェック
 * @returns {boolean} 起動している場合はtrue
 */
function isDynamoDBRunning() {
  try {
    // ポートが開いているか確認
    if (process.platform === 'win32') {
      // Windows環境
      return execSync('netstat -ano | findstr "8000"', { stdio: 'pipe' }).toString().includes('LISTENING');
    } else {
      // Unix系環境
      return execSync('lsof -i :8000 | grep LISTEN', { stdio: 'pipe' }).toString().trim() !== '';
    }
  } catch (error) {
    return false;
  }
}

/**
 * DynamoDB Local の起動
 * @returns {Promise<boolean>} 起動成功時はtrue
 */
async function startDynamoDBLocal() {
  log.step('DynamoDB Local の確認・起動...');

  if (process.env.SKIP_DYNAMODB_CHECKS === 'true') {
    log.warning('SKIP_DYNAMODB_CHECKS=true のため DynamoDB Local の起動をスキップします');
    return false;
  }
  
  // 既に起動しているか確認
  if (isDynamoDBRunning()) {
    log.success('DynamoDB Local はすでに起動しています');
    return true;
  }
  
  // DynamoDBのjarファイルが存在するか確認
  const jarPath = './dynamodb-local/DynamoDBLocal.jar';
  if (!fs.existsSync(jarPath)) {
    log.warning(`DynamoDB Local の jar ファイルが見つかりません: ${jarPath}`);
    log.info('DynamoDB Local をダウンロードしますか？ (y/n)');
    
    // ユーザーの入力を待つ（同期的に）
    const readline = require('readline').createInterface({
      input: process.stdin,
      output: process.stdout
    });
    
    const answer = await new Promise(resolve => {
      readline.question('> ', resolve);
    });
    readline.close();
    
    if (answer.toLowerCase() === 'y') {
      log.info('DynamoDB Local をダウンロードしています...');
      
      try {
        // dynamodb-local ディレクトリを作成
        if (!fs.existsSync('./dynamodb-local')) {
          fs.mkdirSync('./dynamodb-local', { recursive: true });
        }
        
        // ダウンロードコマンドを実行
        execSync('curl -L https://d1ni2b6xgvw0s0.cloudfront.net/v2.2.0/dynamodb_local_latest.zip -o ./dynamodb-local/dynamodb_local_latest.zip', { stdio: 'inherit' });
        
        // 解凍
        if (process.platform === 'win32') {
          // Windows環境
          execSync('powershell -command "Expand-Archive -Path ./dynamodb-local/dynamodb_local_latest.zip -DestinationPath ./dynamodb-local -Force"', { stdio: 'inherit' });
        } else {
          // Unix系環境
          execSync('unzip -o ./dynamodb-local/dynamodb_local_latest.zip -d ./dynamodb-local', { stdio: 'inherit' });
        }
        
        log.success('DynamoDB Local のダウンロードが完了しました');
      } catch (error) {
        log.error(`DynamoDB Local のダウンロードに失敗しました: ${error.message}`);
        log.warning('テストはモックモードで実行する必要があります');
        return false;
      }
    } else {
      log.warning('DynamoDB Local のダウンロードをスキップします');
      log.warning('テストはモックモードで実行する必要があります');
      return false;
    }
  }
  
  // DynamoDB Local を起動
  log.info('DynamoDB Local を起動します...');
  
  try {
    // Java バージョンを確認
    try {
      const javaVersion = execSync('java -version 2>&1', { stdio: 'pipe' }).toString();
      log.info(`Java バージョン: ${javaVersion.split('\n')[0]}`);
    } catch (error) {
      log.error('Java が見つかりません。DynamoDB Local の実行には Java が必要です。');
      return false;
    }
    
    // バックグラウンドで DynamoDB Local を起動
    const child = require('child_process').spawn('java', [
      '-Djava.library.path=./dynamodb-local/DynamoDBLocal_lib',
      '-jar',
      './dynamodb-local/DynamoDBLocal.jar',
      '-inMemory',
      '-port',
      '8000',
      '-sharedDb'
    ], {
      detached: true,
      stdio: process.platform === 'win32' ? 'ignore' : ['ignore', 'pipe', 'pipe']
    });
    
    // エラーハンドリング
    if (child.stderr) {
      child.stderr.on('data', (data) => {
        log.error(`DynamoDB stderr: ${data}`);
      });
    }
    
    if (child.stdout) {
      child.stdout.on('data', (data) => {
        if (data.toString().includes('CorsParams')) {
          log.success('DynamoDB Local が正常に起動しました');
        }
      });
    }
    
    // 親プロセスから切り離す
    child.unref();
    
    // 起動を待機
    log.info('DynamoDB Local の起動を待機しています...');
    let attempts = 0;
    const maxAttempts = 5;
    
    while (attempts < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, 1000));
      attempts++;
      
      if (isDynamoDBRunning()) {
        log.success(`DynamoDB Local の起動が完了しました (${attempts}秒)`);
        return true;
      }
      
      log.info(`起動待機中... (${attempts}/${maxAttempts})`);
    }
    
    log.error('DynamoDB Local の起動タイムアウト');
    return false;
  } catch (error) {
    log.error(`DynamoDB Local の起動に失敗しました: ${error.message}`);
    log.warning('テストはモックモードで実行されます');
    return false;
  }
}

/**
 * テスト用ディレクトリの作成
 */
function createTestDirectories() {
  log.step('テストディレクトリを作成しています...');
  
  const directories = [
    './test-results',
    './test-results/junit',
    './coverage',
    './.jest-cache'
  ];
  
  directories.forEach(dir => {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
      log.success(`ディレクトリを作成しました: ${dir}`);
    } else {
      log.info(`ディレクトリは既に存在します: ${dir}`);
    }
  });
}

/**
 * DynamoDBクライアントの作成
 * @returns {DynamoDBClient} DynamoDBクライアント
 */
function createDynamoDBClient() {
  if (!dynamodbAvailable) {
    log.warning('DynamoDB クライアントを作成できません。AWS SDK がインストールされていません');
    return null;
  }

  return new DynamoDBClient({
    region: 'us-east-1',
    endpoint: process.env.DYNAMODB_ENDPOINT || 'http://localhost:8000',
    credentials: {
      accessKeyId: 'test',
      secretAccessKey: 'test'
    }
  });
}

/**
 * テスト用テーブルの作成
 * @returns {Promise<boolean>} 成功時はtrue
 */
async function createTestTables() {
  log.step('テスト用テーブルを作成しています...');

  try {
    if (!dynamodbAvailable) {
      log.warning('AWS SDK が利用できないため、テーブル作成をスキップします');
      return true;
    }

    const client = createDynamoDBClient();
    
    // 既存のテーブルを取得
    let existingTables = [];
    try {
      const { TableNames } = await client.send(new ListTablesCommand({}));
      existingTables = TableNames || [];
      log.info(`既存のテーブル: ${existingTables.join(', ') || '(なし)'}`);
    } catch (error) {
      log.warning(`テーブル一覧の取得に失敗しました: ${error.message}`);
    }
    
    // 作成するテーブルの定義
    const tables = [
      {
        name: process.env.SESSION_TABLE || 'test-sessions',
        keySchema: [{ AttributeName: 'sessionId', KeyType: 'HASH' }],
        attributeDefinitions: [{ AttributeName: 'sessionId', AttributeType: 'S' }]
      },
      {
        name: `${process.env.DYNAMODB_TABLE_PREFIX || 'test-'}cache`,
        keySchema: [{ AttributeName: 'key', KeyType: 'HASH' }],
        attributeDefinitions: [{ AttributeName: 'key', AttributeType: 'S' }]
      },
      {
        name: `${process.env.DYNAMODB_TABLE_PREFIX || 'test-'}scraping-blacklist`,
        keySchema: [{ AttributeName: 'symbol', KeyType: 'HASH' }],
        attributeDefinitions: [{ AttributeName: 'symbol', AttributeType: 'S' }]
      }
    ];
    
    // 各テーブルを作成
    let successCount = 0;
    for (const table of tables) {
      if (!existingTables.includes(table.name)) {
        try {
          log.info(`テーブルを作成しています: ${table.name}`);
          
          await client.send(new CreateTableCommand({
            TableName: table.name,
            KeySchema: table.keySchema,
            AttributeDefinitions: table.attributeDefinitions,
            BillingMode: 'PAY_PER_REQUEST'
          }));
          
          log.success(`テーブルを作成しました: ${table.name}`);
          successCount++;
        } catch (error) {
          if (error.name === 'ResourceInUseException') {
            log.info(`テーブルは既に存在します: ${table.name}`);
            successCount++;
          } else {
            log.error(`テーブル作成エラー - ${table.name}: ${error.message}`);
          }
        }
      } else {
        log.info(`テーブルは既に存在します: ${table.name}`);
        successCount++;
      }
    }
    
    return successCount === tables.length;
  } catch (error) {
    log.error(`テーブル作成処理に失敗しました: ${error.message}`);
    return false;
  }
}

/**
 * テスト環境変数の設定
 */
function setupEnvironmentVariables() {
  log.step('テスト環境変数を設定しています...');
  
  // .env.test ファイルのパス
  const envFile = path.join(process.cwd(), '.env.test');
  
  // デフォルトの環境変数設定
  const defaultEnv = `# テスト環境用の環境変数
NODE_ENV=test
DYNAMODB_ENDPOINT=http://localhost:8000
SESSION_TABLE=test-sessions
DYNAMODB_TABLE_PREFIX=test-
API_TEST_URL=http://localhost:3000/dev
SKIP_DYNAMODB_CHECKS=true
USE_API_MOCKS=true
CACHE_TIME_US_STOCK=60
CACHE_TIME_JP_STOCK=60
CACHE_TIME_MUTUAL_FUND=60
CACHE_TIME_EXCHANGE_RATE=60
CORS_ALLOW_ORIGIN=*
TEST_MODE=true
`;
  
  // .env.test ファイルが存在するか確認
  if (fs.existsSync(envFile)) {
    log.info('.env.test ファイルが見つかりました');
    
    // ファイルの内容を読み込む
    const content = fs.readFileSync(envFile, 'utf8');
    
    // 必要な環境変数が含まれているか確認
    const requiredVars = [
      'NODE_ENV',
      'DYNAMODB_ENDPOINT',
      'SESSION_TABLE',
      'DYNAMODB_TABLE_PREFIX'
    ];
    
    const missingVars = requiredVars.filter(varName => !content.includes(`${varName}=`));
    
    if (missingVars.length > 0) {
      log.warning(`.env.test ファイルに不足している環境変数があります: ${missingVars.join(', ')}`);
      log.info('ファイルを更新しますか？ (y/n)');
      
      // ユーザーの入力を待つ（同期的に）
      const answer = require('readline-sync').question('> ');
      
      if (answer.toLowerCase() === 'y') {
        // 既存の内容に追加
        const updatedContent = content + '\n' + missingVars.map(varName => {
          const defaultValue = defaultEnv.match(new RegExp(`${varName}=(.*)`))[1];
          return `${varName}=${defaultValue}`;
        }).join('\n') + '\n';
        
        fs.writeFileSync(envFile, updatedContent);
        log.success('.env.test ファイルを更新しました');
      }
    }
  } else {
    // .env.test ファイルがなければ作成
    log.warning('.env.test ファイルが見つかりません。デフォルト設定で作成します。');
    fs.writeFileSync(envFile, defaultEnv);
    log.success('.env.test ファイルを作成しました');
  }
  
  // 現在のプロセスの環境変数を設定
  process.env.NODE_ENV = 'test';
  process.env.DYNAMODB_ENDPOINT = 'http://localhost:8000';
  process.env.SESSION_TABLE = 'test-sessions';
  process.env.DYNAMODB_TABLE_PREFIX = 'test-';
  process.env.SKIP_DYNAMODB_CHECKS = 'true';
  process.env.USE_API_MOCKS = 'true';
  
  log.success('環境変数の設定が完了しました');
}

/**
 * モックセットアップファイルの確認と生成
 */
function checkMockSetup() {
  log.step('モックセットアップファイルを確認しています...');
  
  const mockDirs = [
    './__mocks__',
    './__mocks__/aws-sdk',
    './__mocks__/axios'
  ];
  
  // ディレクトリがなければ作成
  mockDirs.forEach(dir => {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
      log.success(`ディレクトリを作成しました: ${dir}`);
    }
  });
  
  // Axiosモックファイルの確認
  const axiosMockFile = './__mocks__/axios.js';
  if (!fs.existsSync(axiosMockFile)) {
    const axiosMockContent = `/**
 * Axios モック
 * @file __mocks__/axios.js
 */

module.exports = {
  get: jest.fn().mockResolvedValue({
    status: 200,
    data: { success: true, data: {} }
  }),
  post: jest.fn().mockResolvedValue({
    status: 200,
    data: { success: true, data: {} }
  }),
  put: jest.fn().mockResolvedValue({
    status: 200,
    data: { success: true, data: {} }
  }),
  delete: jest.fn().mockResolvedValue({
    status: 200,
    data: { success: true, data: {} }
  }),
  create: jest.fn().mockReturnThis(),
  defaults: {
    headers: {
      common: {}
    }
  },
  interceptors: {
    request: { use: jest.fn(), eject: jest.fn() },
    response: { use: jest.fn(), eject: jest.fn() }
  }
};`;
    
    fs.writeFileSync(axiosMockFile, axiosMockContent);
    log.success(`モックファイルを作成しました: ${axiosMockFile}`);
  }
  
  log.success('モックファイルの確認が完了しました');
}

/**
 * テスト実行前の設定とクリーンアップ
 */
function prepareTestEnvironment() {
  log.step('テスト実行前の準備...');
  
  // 古いレポートファイルのクリーンアップ
  const reportPatterns = [
    './test-results/junit.xml',
    './test-results/test-report.html',
    './test-results/test-log.md'
  ];
  
  reportPatterns.forEach(pattern => {
    if (fs.existsSync(pattern)) {
      try {
        fs.unlinkSync(pattern);
        log.info(`古いレポートを削除しました: ${pattern}`);
      } catch (error) {
        log.warning(`レポートファイルの削除に失敗しました: ${pattern}`);
      }
    }
  });
  
  // テストモードフラグファイルの作成
  fs.writeFileSync('./test-results/.test-mode', new Date().toISOString());
  
  log.success('テスト実行前の準備が完了しました');
}

/**
 * メイン処理
 */
async function main() {
  log.info('テスト環境のセットアップを開始します...');
  console.log('=====================================');
  
  try {
    // テストディレクトリの作成
    createTestDirectories();
    
    // モックのセットアップ
    checkMockSetup();
    
    // 環境変数の設定
    setupEnvironmentVariables();
    
    // DynamoDB Local の起動
    const dynamoDBRunning = await startDynamoDBLocal();
    
    // テーブルの作成（DynamoDBが起動している場合のみ）
    let tablesCreated = false;
    if (dynamoDBRunning) {
      // DynamoDB起動確認後に少し待機
      await new Promise(resolve => setTimeout(resolve, 1000));
      tablesCreated = await createTestTables();
    }
    
    // 前処理
    prepareTestEnvironment();
    
    console.log('=====================================');
    
    if (dynamoDBRunning && tablesCreated) {
      log.success('テスト環境のセットアップが完了しました！');
      log.info('テストを実行するには:');
      log.info('  npm test');
      log.info('  または');
      log.info('  ./scripts/run-tests.sh [テスト種別]');
    } else if (dynamoDBRunning) {
      log.warning('DynamoDB は起動していますが、テーブル作成に問題がありました');
      log.info('必要に応じてモックモードでテストを実行してください:');
      log.info('  USE_API_MOCKS=true npm test');
    } else {
      log.warning('DynamoDBの起動に問題があります。モックモードでテストを実行してください:');
      log.info('  USE_API_MOCKS=true npm test');
    }
    
    return 0;
  } catch (error) {
    log.error(`テスト環境のセットアップに失敗しました: ${error.message}`);
    log.error(error.stack);
    return 1;
  }
}

// スクリプトを実行
main().then(exitCode => {
  if (exitCode !== 0) {
    process.exit(exitCode);
  }
}).catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
