# テストファイル作成ガイドライン

## 1. 概要

本ドキュメントでは、テストファイルを作成する際の基準と手順を定義します。テストファイルとソースコードの一貫性を保ち、参照エラーを防止するためのガイドラインです。プロジェクトでは次の3種類のテストを実装しています：

- **単体テスト**: 個々のコンポーネントや関数の機能をテスト
- **統合テスト**: 複数のコンポーネントの連携をテスト
- **E2Eテスト**: エンドユーザーの視点からシステム全体の動作をテスト

## 2. ディレクトリ構造と命名規則

### 2.1 ディレクトリ構造

```
__tests__/
├── e2e/                    # エンドツーエンドテスト
│   ├── Auth_test.js
│   ├── Dashboard_test.js
│   └── ...
├── integration/            # 統合テスト
│   ├── auth/
│   │   ├── login.test.js
│   │   └── ...
│   ├── api/
│   │   └── ...
│   └── forms/
│       └── ...
├── unit/                   # 単体テスト
│   ├── components/
│   │   ├── Button.test.js
│   │   └── ...
│   ├── utils/
│   │   ├── formatters.test.js
│   │   └── ...
│   └── store/
│       ├── userStore.test.js
│       └── ...
├── setup.js                # Jest設定ファイル
└── mocks/                  # テスト用モック定義
    ├── handlers.js
    ├── data.js
    └── ...
```

### 2.2 命名規則

1. **単体テスト・統合テスト**
   - テストファイル名: `{ソースファイル名}.test.js`
   - 例: `src/components/Button.js` → `__tests__/unit/components/Button.test.js`

2. **E2Eテスト**
   - テストファイル名: `{機能名}_test.js`
   - 例: `__tests__/e2e/Auth_test.js`

3. **ディレクトリ構造の反映**
   - ソースコードのディレクトリ構造をテストディレクトリにも反映させる
   - 例: `src/utils/formatters.js` → `__tests__/unit/utils/formatters.test.js`

## 3. テストファイルの基本構造

```javascript
/**
 * ファイルパス: __tests__/unit/components/Button.test.js
 * 
 * Buttonコンポーネントの単体テスト
 * 基本的なボタン機能、スタイルのバリエーション、イベントハンドリングなどをテスト
 * 
 * @author 開発者名
 * @created 2023-07-20
 * @updated 2023-07-25 - disabled状態のテストケース追加
 */

// テスト対象モジュールのインポート
import Button from '@/components/Button';

// テスト用ライブラリ
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

describe('Buttonコンポーネント', () => {
  // テスト用データ
  const defaultProps = {
    label: 'テストボタン',
    onClick: jest.fn(),
  };
  
  // 各テスト前の準備
  beforeEach(() => {
    // モックのリセット
    jest.clearAllMocks();
  });
  
  // 各テスト後のクリーンアップ
  afterEach(() => {
    // 必要に応じてクリーンアップ処理
  });
  
  it('ラベルが正しくレンダリングされる', () => {
    // テスト実行
    render(<Button {...defaultProps} />);
    
    // 検証
    expect(screen.getByText('テストボタン')).toBeInTheDocument();
  });
  
  it('クリックイベントが発火する', async () => {
    // テスト実行
    render(<Button {...defaultProps} />);
    
    // ボタンをクリック
    await userEvent.click(screen.getByText('テストボタン'));
    
    // 検証
    expect(defaultProps.onClick).toHaveBeenCalledTimes(1);
  });
  
  it('disabled属性が適用される', () => {
    // テスト実行
    render(<Button {...defaultProps} disabled />);
    
    // 検証
    expect(screen.getByText('テストボタン')).toBeDisabled();
  });
  
  it('異なるバリエーションが正しく適用される', () => {
    // テスト実行
    const { rerender } = render(<Button {...defaultProps} variant="primary" />);
    
    // primary variantの検証
    const button = screen.getByText('テストボタン');
    expect(button).toHaveClass('btn-primary');
    
    // secondary variantの検証に再レンダリング
    rerender(<Button {...defaultProps} variant="secondary" />);
    expect(button).toHaveClass('btn-secondary');
  });
});
```

## 4. テスト種別ごとの実装パターン

### 4.1 単体テスト

単体テストは小さく独立したコンポーネントや関数をテストします。外部依存はすべてモック化します。

```javascript
// __tests__/unit/utils/formatters.test.js の例
import { formatCurrency, formatDate, formatNumber } from '@/utils/formatters';

describe('フォーマッターユーティリティ', () => {
  describe('formatCurrency', () => {
    it('日本円のフォーマット', () => {
      const result = formatCurrency(1000, 'JPY');
      expect(result).toBe('¥1,000');
    });
    
    it('米ドルのフォーマット', () => {
      const result = formatCurrency(1000, 'USD');
      expect(result).toBe('$1,000.00');
    });
  });
  
  describe('formatDate', () => {
    it('ISO形式の日付を日本形式に変換', () => {
      const result = formatDate('2023-07-20T10:00:00Z');
      expect(result).toBe('2023年7月20日');
    });
  });
});
```

### 4.2 統合テスト

統合テストは複数のコンポーネントの連携をテストします。一部の依存をモック化する場合もあります。

```javascript
// __tests__/integration/auth/login.test.js の例
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LoginPage from '@/pages/Login';
import { useAuth } from '@/hooks/useAuth';

// モックの設定
jest.mock('@/hooks/useAuth');

describe('ログインフロー', () => {
  // モックの実装
  const mockLogin = jest.fn();
  
  beforeEach(() => {
    useAuth.mockReturnValue({
      login: mockLogin,
      isAuthenticated: false,
      user: null,
      error: null,
    });
  });
  
  it('有効な認証情報でログインできる', async () => {
    // テスト実行
    render(<LoginPage />);
    
    // フォームに入力
    await userEvent.type(screen.getByLabelText('メールアドレス'), 'test@example.com');
    await userEvent.type(screen.getByLabelText('パスワード'), 'password123');
    
    // フォーム送信
    await userEvent.click(screen.getByRole('button', { name: 'ログイン' }));
    
    // 検証
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
      });
    });
  });
  
  it('入力検証が機能する', async () => {
    // テスト実行
    render(<LoginPage />);
    
    // 空のフォーム送信
    await userEvent.click(screen.getByRole('button', { name: 'ログイン' }));
    
    // 検証
    expect(await screen.findByText('メールアドレスは必須です')).toBeInTheDocument();
    expect(mockLogin).not.toHaveBeenCalled();
  });
});
```

### 4.3 E2Eテスト

E2Eテストはユーザーの視点からシステム全体の動作をテストします。実際のAPIエンドポイントを呼び出すか、精度の高いモックを使用します。

```javascript
// __tests__/e2e/Auth_test.js の例
import { setupServer } from 'msw/node';
import { rest } from 'msw';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from '@/App';

// MSWサーバーの設定
const server = setupServer(
  rest.post('/api/auth/login', (req, res, ctx) => {
    const { email, password } = req.body;
    
    if (email === 'test@example.com' && password === 'password123') {
      return res(
        ctx.json({
          token: 'fake-token-123',
          user: {
            id: '1',
            name: 'Test User',
            email: 'test@example.com',
          },
        })
      );
    }
    
    return res(
      ctx.status(401),
      ctx.json({
        message: '認証情報が無効です',
      })
    );
  }),
  
  // その他のAPIエンドポイントモック...
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('認証フロー', () => {
  it('ログインからダッシュボード表示までの一連のフロー', async () => {
    // アプリのレンダリング
    render(<App />);
    
    // ログインリンクをクリック
    await userEvent.click(screen.getByText('ログイン'));
    
    // ログインページが表示されることを確認
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'ログイン' })).toBeInTheDocument();
    });
    
    // フォームに入力
    await userEvent.type(screen.getByLabelText('メールアドレス'), 'test@example.com');
    await userEvent.type(screen.getByLabelText('パスワード'), 'password123');
    
    // フォーム送信
    await userEvent.click(screen.getByRole('button', { name: 'ログイン' }));
    
    // ダッシュボードがレンダリングされることを確認
    await waitFor(() => {
      expect(screen.getByText('ダッシュボード')).toBeInTheDocument();
      expect(screen.getByText('Test User')).toBeInTheDocument();
    });
  });
});
```

## 5. モックの設定パターン

### 5.1 基本的なモック

```javascript
// 関数のモック
const mockFunction = jest.fn();
mockFunction.mockReturnValue('モック値');
mockFunction.mockImplementation(() => 'モック値');

// モジュールのモック
jest.mock('@/services/apiService');

// スパイの使用
jest.spyOn(console, 'log').mockImplementation();

// 特定のインスタンスメソッドのモック
Element.prototype.scrollTo = jest.fn();
```

### 5.2 React Hooks のモック

```javascript
// カスタムフックのモック
jest.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    user: { id: '1', name: 'Test User' },
    isAuthenticated: true,
    login: jest.fn(),
    logout: jest.fn(),
  }),
}));

// Contextのモック
jest.mock('@/contexts/ThemeContext', () => ({
  useTheme: () => ({
    theme: 'light',
    toggleTheme: jest.fn(),
  }),
}));
```

### 5.3 APIのモック

```javascript
// axios のモック
jest.mock('axios');
import axios from 'axios';

// レスポンスの設定
axios.get.mockResolvedValue({
  data: {
    id: '1',
    name: 'Test Item',
  },
});

// エラーレスポンスの設定
axios.post.mockRejectedValue({
  response: {
    status: 400,
    data: {
      message: 'バリデーションエラー',
      errors: {
        name: '名前は必須です',
      },
    },
  },
});
```

### 5.4 MSW によるモック

```javascript
// MSW ハンドラーの設定
import { rest } from 'msw';

export const handlers = [
  rest.get('/api/users', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json([
        { id: '1', name: 'User 1' },
        { id: '2', name: 'User 2' },
      ])
    );
  }),
  
  rest.post('/api/users', (req, res, ctx) => {
    const { name } = req.body;
    
    if (!name) {
      return res(
        ctx.status(400),
        ctx.json({
          message: 'バリデーションエラー',
          errors: {
            name: '名前は必須です',
          },
        })
      );
    }
    
    return res(
      ctx.status(201),
      ctx.json({
        id: '3',
        name,
      })
    );
  }),
];
```

## 6. 非同期テストのパターン

### 6.1 async/await パターン

```javascript
it('非同期データを取得する', async () => {
  // 非同期関数の実行
  const result = await fetchData();
  
  // 結果の検証
  expect(result).toEqual({
    id: '1',
    name: 'Test Item',
  });
});
```

### 6.2 React Testing Library の waitFor

```javascript
it('非同期UIの更新をテストする', async () => {
  // コンポーネントのレンダリング
  render(<AsyncComponent />);
  
  // ロード中の表示を確認
  expect(screen.getByText('読み込み中...')).toBeInTheDocument();
  
  // データ読み込み完了を待機
  await waitFor(() => {
    expect(screen.queryByText('読み込み中...')).not.toBeInTheDocument();
  });
  
  // 読み込まれたコンテンツを確認
  expect(screen.getByText('Data: Test Item')).toBeInTheDocument();
});
```

### 6.3 タイマーのモック

```javascript
it('タイマー処理をテストする', () => {
  // タイマーをモック
  jest.useFakeTimers();
  
  // コンポーネントのレンダリング
  render(<TimerComponent />);
  
  // 初期状態を確認
  expect(screen.getByText('0')).toBeInTheDocument();
  
  // タイマーを進める
  jest.advanceTimersByTime(1000);
  
  // 更新された状態を確認
  expect(screen.getByText('1')).toBeInTheDocument();
  
  // タイマーをリセット
  jest.useRealTimers();
});
```

## 7. 環境変数の取り扱い

### 7.1 環境変数の設定とリセット

```javascript
describe('環境変数を使用するテスト', () => {
  // 元の環境変数を保存
  const originalEnv = process.env;
  
  beforeEach(() => {
    // 環境変数をリセット
    process.env = { ...originalEnv };
    
    // テスト用の環境変数を設定
    process.env.API_BASE_URL = 'http://test-api.example.com';
    process.env.AUTH_ENABLED = 'true';
  });
  
  afterAll(() => {
    // テスト後に環境変数を元に戻す
    process.env = originalEnv;
  });
  
  it('環境変数を使用する関数のテスト', () => {
    const config = getConfig();
    expect(config.apiBaseUrl).toBe('http://test-api.example.com');
    expect(config.authEnabled).toBe(true);
  });
});
```

### 7.2 NODE_ENV の設定

```javascript
it('開発環境での動作テスト', () => {
  process.env.NODE_ENV = 'development';
  
  const config = getEnvironmentConfig();
  expect(config.isDevelopment).toBe(true);
  expect(config.isProduction).toBe(false);
});

it('本番環境での動作テスト', () => {
  process.env.NODE_ENV = 'production';
  
  const config = getEnvironmentConfig();
  expect(config.isDevelopment).toBe(false);
  expect(config.isProduction).toBe(true);
});
```

## 8. テスト間干渉の回避

```javascript
// グローバル状態を持つモジュールの場合
beforeEach(() => {
  // テスト前に状態をリセット
  require('@/store').resetState();
});

// ローカルストレージのモックをクリア
beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
});

// ドキュメントの状態をクリア
afterEach(() => {
  document.body.innerHTML = '';
});
```

## 9. スナップショットテスト

```javascript
it('UIコンポーネントが期待通りにレンダリングされる', () => {
  const { container } = render(<MyComponent title="テストタイトル" />);
  expect(container).toMatchSnapshot();
});

it('特定の要素のスナップショットをテストする', () => {
  render(<ComplexComponent />);
  const headerElement = screen.getByTestId('header');
  expect(headerElement).toMatchSnapshot();
});
```

## 10. 前提条件確認

テストファイル作成前に、以下の確認を必ず行ってください：

1. **ソースコードの存在確認**
   ```bash
   # ソースファイルの存在を確認
   ls -la src/components/Button.js
   
   # ファイルが存在しない場合は検索で確認
   find src -name "Button*.js"
   ```

2. **ファイル内容の確認**
   ```bash
   # ファイルの内容を確認して、正確なプロパティ名や関数名を把握
   cat src/components/Button.js
   ```

3. **エクスポートの確認**
   ```bash
   # どの関数/クラスがエクスポートされているかを確認
   grep -n "export " src/components/Button.js
   ```

4. **依存関係の確認**
   ```bash
   # ソースファイルの依存関係を確認
   grep -n "import " src/components/Button.js
   ```

## 11. テストファイル作成フロー

1. **適切なディレクトリを選択する**
   - 単体テスト: `__tests__/unit/{カテゴリ}/`
   - 統合テスト: `__tests__/integration/{カテゴリ}/`
   - E2Eテスト: `__tests__/e2e/`

2. **テストファイルを作成する**
   ```bash
   mkdir -p __tests__/unit/components
   touch __tests__/unit/components/Button.test.js
   ```

3. **インポートを設定する**
   ```javascript
   // テスト対象モジュールをインポート
   import Button from '@/components/Button';
   
   // テスト用ライブラリをインポート
   import { render, screen } from '@testing-library/react';
   import userEvent from '@testing-library/user-event';
   ```

4. **モックを設定する**
   ```javascript
   // 依存モジュールをモック化
   jest.mock('@/utils/analytics');
   
   // モック実装を設定
   import { trackEvent } from '@/utils/analytics';
   trackEvent.mockImplementation(() => null);
   ```

5. **テストケースを作成する**
   ```javascript
   describe('Buttonコンポーネント', () => {
     // テスト用データ
     const defaultProps = {
       label: 'テストボタン',
       onClick: jest.fn(),
     };
     
     // モックリセット
     beforeEach(() => {
       jest.clearAllMocks();
     });
     
     // テストケース
     it('ラベルが正しくレンダリングされる', () => {
       render(<Button {...defaultProps} />);
       expect(screen.getByText('テストボタン')).toBeInTheDocument();
     });
   });
   ```

6. **テストを実行する**
   ```bash
   # 特定のテストファイルを実行
   npm test -- __tests__/unit/components/Button.test.js
   
   # 特定のテストケースを実行
   npm test -- -t "ラベルが正しくレンダリングされる"
   ```

## 12. テスト実装ベストプラクティス

### 12.1 テスト記述のパターン

1. **Arrange-Act-Assert (AAA) パターン**
   ```javascript
   it('ボタンクリックでカウンターが増加する', () => {
     // Arrange - セットアップ
     render(<Counter initialValue={0} />);
     
     // Act - 操作
     fireEvent.click(screen.getByRole('button', { name: '増加' }));
     
     // Assert - 検証
     expect(screen.getByText('1')).toBeInTheDocument();
   });
   ```

2. **Given-When-Then パターン**
   ```javascript
   it('フォーム送信が成功する', () => {
     // Given - 前提条件
     render(<LoginForm />);
     fillFormWithValidData();
     
     // When - イベント発生
     submitForm();
     
     // Then - 結果検証
     expectSuccessMessage();
   });
   ```

### 12.2 効果的な命名規則

```javascript
// 単体テスト
it('空の配列の場合は0を返す', () => {...});
it('nullが渡された場合はエラーをスローする', () => {...});

// 統合テスト
it('ログイン成功後にダッシュボードに遷移する', () => {...});
it('無効な認証情報の場合はエラーメッセージを表示する', () => {...});

// E2Eテスト
it('ユーザーが新規登録からプロフィール編集までの一連の流れを完了できる', () => {...});
```

### 12.3 テスト実装の留意点

- **1テストにつき1つのアサーション**: テストは単一の機能や挙動に集中する
- **DRY原則の適切な適用**: テストコードは読みやすさを優先し、過度な抽象化を避ける
- **境界値テスト**: エッジケースや境界条件（空、null、最大値など）を考慮する
- **独立したテスト**: テスト間の依存関係を避け、順序に関わらず実行できるようにする
- **テスト用データの明示**: テストデータは十分に明示的で理解しやすくする

## 13. 参考リソース

- Jest ドキュメント: https://jestjs.io/docs/
- React Testing Library: https://testing-library.com/docs/react-testing-library/intro/
- MSW (Mock Service Worker): https://mswjs.io/docs/
- Testing Trophy: https://kentcdodds.com/blog/write-tests
- JavaScript テスティングのベストプラクティス: https://github.com/goldbergyoni/javascript-testing-best-practices
