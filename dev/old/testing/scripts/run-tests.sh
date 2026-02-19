#!/bin/bash
# 
# ファイルパス: scripts/run-tests.sh
# 
# Portfolio Market Data APIテスト実行スクリプト
# Jest設定ファイルを利用し、各種テスト実行オプションを提供
#
# @author Koki Riho
# @updated 2025-05-15 - 新しいテスト種別の追加、詳細レポート生成オプションの強化
# @updated 2025-05-16 - カバレッジチャートの自動生成機能追加、テストカバレッジ目標の段階追跡
# @updated 2025-05-17 - カバレッジオプションが確実に有効になるように修正、強制カバレッジオプション追加
# @updated 2025-05-19 - Jest設定ファイルを明示的に指定する機能追加、依存関係の明確化
# @updated 2025-05-20 - カバレッジデータ生成の信頼性向上、デバッグオプション強化
# @updated 2025-05-21 - カバレッジ率と目標カバレッジ率の表示を強化、非同期ハンドル問題の検出を追加
#

# 便利なサンプルコマンド
# JEST_COVERAGE=true ./scripts/run-tests.sh integration  # カバレッジを強制的に有効化して統合テストを実行
# USE_API_MOCKS=true ./scripts/run-tests.sh e2e          # モックを使用してE2Eテストを実行

# 色の設定
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 関数定義
print_header() {
  echo -e "\n${BLUE}===========================================${NC}"
  echo -e "${BLUE}$1${NC}"
  echo -e "${BLUE}===========================================${NC}\n"
}

print_success() {
  echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
  echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
  echo -e "${RED}✗ $1${NC}"
}

print_info() {
  echo -e "${BLUE}ℹ $1${NC}"
}

show_help() {
  print_header "Portfolio Market Data API テスト実行ヘルプ"
  echo "使用方法: $0 [オプション] <テスト種別>"
  echo ""
  echo "オプション:"
  echo "  -h, --help                  このヘルプメッセージを表示"
  echo "  -c, --clean                 テスト実行前にテスト環境をクリーンアップ"
  echo "  -v, --visual                テスト結果をビジュアルレポートで表示"
  echo "  -a, --auto                  APIサーバーを自動起動（E2Eテスト用）"
  echo "  -m, --mock                  APIモックを使用（E2Eテスト用）"
  echo "  -w, --watch                 監視モードでテストを実行（コード変更時に自動再実行）"
  echo "  -n, --no-coverage           カバレッジ計測・チェックを無効化"
  echo "  -f, --force                 サーバー状態に関わらずテストを強制実行"
  echo "  -d, --debug                 デバッグモードを有効化（詳細ログを表示）"
  echo "  -i, --ignore-coverage-errors テスト自体は成功してもカバレッジエラーを無視"
  echo "  -s, --specific              特定のファイルまたはパターンに一致するテストのみ実行"
  echo "  -t, --target                カバレッジ目標段階を指定 [initial|mid|final]"
  echo "  --html-coverage             HTMLカバレッジレポートをブラウザで開く"
  echo "  --chart                     カバレッジをチャートで生成（ビジュアルレポートに追加）"
  echo "  --junit                     JUnit形式のレポートを生成（CI環境用）"
  echo "  --nvm                       nvmを使用してNode.js 18に切り替え"
  echo "  --force-coverage            カバレッジ計測を強制的に有効化（--no-coverageより優先）"
  echo "  --config                    カスタムJest設定ファイルのパスを指定"
  echo "  --verbose-coverage          カバレッジデータ処理の詳細ログを出力"
  echo "  --detect-open-handles       非同期ハンドルの検出を有効化"
  echo ""
  echo "テスト種別:"
  echo "  unit                単体テストのみ実行"
  echo "  unit:services       サービス層の単体テストのみ実行"
  echo "  unit:utils          ユーティリティの単体テストのみ実行"
  echo "  unit:function       API関数の単体テストのみ実行"
  echo "  integration         統合テストのみ実行"
  echo "  integration:auth    認証関連の統合テストのみ実行" 
  echo "  integration:market  マーケットデータ関連の統合テストのみ実行"
  echo "  integration:drive   Google Drive関連の統合テストのみ実行"
  echo "  e2e                 エンドツーエンドテストのみ実行"
  echo "  all                 すべてのテストを実行"
  echo "  quick               単体テストと統合テストのみ高速実行（モック使用）"
  echo "  specific            -s オプションで指定したファイルまたはパターンに一致するテストのみ実行"
  echo ""
  echo "カバレッジ目標段階 (-t/--target オプション):"
  echo "  initial             初期段階の目標 (20-30%) - 基本的なテスト実装時"
  echo "  mid                 中間段階の目標 (40-60%) - サービス層とAPIハンドラーのテスト時"
  echo "  final               最終段階の目標 (70-80%) - 完全なテストカバレッジ時"
  echo ""
  echo "使用例:"
  echo "  $0 unit             単体テストのみ実行（カバレッジあり）"
  echo "  $0 -c all           環境クリーンアップ後、すべてのテストを実行"
  echo "  $0 -a -v e2e        APIサーバー自動起動でE2Eテストを実行し、結果をビジュアル表示"
  echo "  $0 -m -w unit       モックを使用し、監視モードで単体テストを実行"
  echo "  $0 quick            単体テストと統合テストを高速実行（モック使用）"
  echo "  $0 -n integration   カバレッジチェック無効で統合テストを実行"
  echo "  $0 --force-coverage integration  カバレッジを強制的に有効化して統合テストを実行"
  echo "  $0 -f -m e2e        テストを強制実行モードで実行（モック使用）"
  echo "  $0 -d e2e           デバッグモードでE2Eテストを実行（詳細ログ表示）"
  echo "  $0 -i e2e           カバレッジエラーを無視してテスト成功を正確に表示"
  echo "  $0 -s \"services/*.test.js\" specific  サービス関連のテストファイルのみ実行"
  echo "  $0 unit:services    サービス層の単体テストのみ実行"
  echo "  $0 --chart all      すべてのテストを実行し、カバレッジチャートを生成"
  echo "  $0 -t mid all       中間段階のカバレッジ目標を設定してすべてのテストを実行"
  echo "  $0 --config custom-jest.config.js unit  カスタム設定ファイルで単体テストを実行"
  echo "  $0 --verbose-coverage all    カバレッジデータ処理の詳細ログを確認"
  echo "  $0 --detect-open-handles unit  非同期ハンドルの検出を有効化して単体テストを実行"
  echo ""
}

# 変数の初期化
CLEAN=0
VISUAL=0
AUTO=0
MOCK=0
WATCH=0
NO_COVERAGE=0
USE_NVM=0
FORCE_TESTS=0
DEBUG_MODE=0
IGNORE_COVERAGE_ERRORS=0
HTML_COVERAGE=0
GENERATE_CHART=0
JUNIT_REPORT=0
FORCE_COVERAGE=0
SPECIFIC_PATTERN=""
TEST_TYPE=""
COVERAGE_TARGET="initial"
JEST_CONFIG_PATH="jest.config.js"
VERBOSE_COVERAGE=0
DETECT_OPEN_HANDLES=0

# オプション解析
while [[ $# -gt 0 ]]; do
  case $1 in
    -h|--help)
      show_help
      exit 0
      ;;
    -c|--clean)
      CLEAN=1
      shift
      ;;
    -v|--visual)
      VISUAL=1
      shift
      ;;
    -a|--auto)
      AUTO=1
      shift
      ;;
    -m|--mock)
      MOCK=1
      shift
      ;;
    -w|--watch)
      WATCH=1
      shift
      ;;
    -n|--no-coverage)
      NO_COVERAGE=1
      shift
      ;;
    -f|--force)
      FORCE_TESTS=1
      shift
      ;;
    -d|--debug)
      DEBUG_MODE=1
      shift
      ;;
    -i|--ignore-coverage-errors)
      IGNORE_COVERAGE_ERRORS=1
      shift
      ;;
    -s|--specific)
      SPECIFIC_PATTERN="$2"
      shift 2
      ;;
    -t|--target)
      COVERAGE_TARGET="$2"
      shift 2
      ;;
    --html-coverage)
      HTML_COVERAGE=1
      shift
      ;;
    --chart)
      GENERATE_CHART=1
      shift
      ;;
    --junit)
      JUNIT_REPORT=1
      shift
      ;;
    --nvm)
      USE_NVM=1
      shift
      ;;
    --force-coverage)
      FORCE_COVERAGE=1
      shift
      ;;
    --config)
      JEST_CONFIG_PATH="$2"
      shift 2
      ;;
    --verbose-coverage)
      VERBOSE_COVERAGE=1
      shift
      ;;
    --detect-open-handles)
      DETECT_OPEN_HANDLES=1
      shift
      ;;
    unit|unit:services|unit:utils|unit:function|integration|integration:auth|integration:market|integration:drive|e2e|all|quick|specific)
      TEST_TYPE=$1
      shift
      ;;
    *)
      print_error "不明なオプション: $1"
      show_help
      exit 1
      ;;
  esac
done

# カバレッジ目標段階の検証
if [[ ! "$COVERAGE_TARGET" =~ ^(initial|mid|final)$ ]]; then
  print_error "不明なカバレッジ目標段階: $COVERAGE_TARGET"
  print_info "有効な値: initial, mid, final"
  exit 1
fi

# Jest configuration のデバッグ情報を追加
debug_jest_config() {
  print_info "Jest設定のデバッグ情報を表示します..."
  
  # Jest のバージョンを確認
  JEST_VERSION=$(npx jest --version 2>/dev/null || echo "Jest not found")
  echo "Jest バージョン: $JEST_VERSION"
  
  # 使用するJest設定ファイルの確認
  echo "使用する設定ファイル: $JEST_CONFIG_PATH"
  if [ -f "$JEST_CONFIG_PATH" ]; then
    echo "$JEST_CONFIG_PATH が見つかりました"
    echo "設定内容:"
    cat "$JEST_CONFIG_PATH" | grep -E "coverage|collectCoverage|setupFiles|reporters" || echo "主要設定が見つかりません"
  else
    print_error "$JEST_CONFIG_PATH が見つかりません"
    
    # 代替設定ファイルを探す
    if [ -f "jest.config.js" ]; then
      echo "jest.config.js が見つかりました（代替として使用します）"
      JEST_CONFIG_PATH="jest.config.js"
    elif [ -f "jest.config.json" ]; then
      echo "jest.config.json が見つかりました（代替として使用します）"
      JEST_CONFIG_PATH="jest.config.json"
    else
      # package.jsonのJest設定を確認
      if [ -f "package.json" ]; then
        echo "package.json の Jest 設定を確認:"
        cat package.json | grep -A 20 '"jest":' || echo "package.jsonにJest設定が見つかりません"
      fi
    fi
  fi
  
  # 関連ファイルの存在確認
  echo "関連ファイルのチェック:"
  
  if [ -f "jest.setup.js" ]; then
    echo "- jest.setup.js: 存在します"
  else
    echo "- jest.setup.js: 見つかりません"
  fi
  
  if [ -f "__tests__/setup.js" ]; then
    echo "- __tests__/setup.js: 存在します"
  else
    echo "- __tests__/setup.js: 見つかりません"
  fi
  
  if [ -f "custom-reporter.js" ]; then
    echo "- custom-reporter.js: 存在します"
  else
    echo "- custom-reporter.js: 見つかりません" 
  fi
  
  # .env.localファイルの確認
  if [ -f ".env.local" ]; then
    echo ".env.local ファイルをチェックしています（カバレッジ設定の上書きがないか）:"
    cat .env.local | grep -E "JEST|COVERAGE|collectCoverage|jest" || echo "カバレッジ関連の設定は見つかりません"
  fi
  
  # 関連するnodeモジュールをチェック
  echo "インストールされている関連パッケージ:"
  npm list | grep -E "jest|istanbul|coverage" || echo "カバレッジ関連パッケージが見つかりません"
}

# デバッグモードの場合は、Jest設定も表示
if [ $DEBUG_MODE -eq 1 ]; then
  debug_jest_config
fi

# nvmが指定されている場合、Node.js 18に切り替え
if [ $USE_NVM -eq 1 ]; then
  print_info "nvmを使用してNode.js 18に切り替えます..."
  
  # nvmをロード
  export NVM_DIR="$HOME/.nvm"
  [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
  
  # 現在のNode.jsバージョンを確認
  CURRENT_NODE_VERSION=$(node -v)
  
  if [[ "$CURRENT_NODE_VERSION" == v18.* ]]; then
    print_success "既にNode.js $CURRENT_NODE_VERSION を使用しています"
  else
    # Node.js 18に切り替え
    nvm use 18 || {
      print_warning "Node.js 18に切り替えられませんでした。インストールを試みます..."
      nvm install 18 && nvm use 18 || {
        print_error "Node.js 18のインストールに失敗しました。"
        print_info "nvm install 18 を手動で実行するか、npm config set engine-strict false を実行してください。"
        exit 1
      }
    }
    print_success "Node.js $(node -v) に切り替えました"
  fi
fi

# 環境変数が既に設定されているかチェック
check_env_vars() {
  # 環境変数から直接実行された場合
  if [ -n "$JEST_COVERAGE" ] || [ -n "$USE_API_MOCKS" ] || [ -n "$COLLECT_COVERAGE" ]; then
    print_info "コマンドラインから環境変数が設定されています："
    
    if [ -n "$JEST_COVERAGE" ]; then
      echo "- JEST_COVERAGE=$JEST_COVERAGE"
      # 既に設定されている場合は明示的に環境変数に追加
      ENV_VARS="$ENV_VARS JEST_COVERAGE=$JEST_COVERAGE"
    fi
    
    if [ -n "$USE_API_MOCKS" ]; then
      echo "- USE_API_MOCKS=$USE_API_MOCKS"
      ENV_VARS="$ENV_VARS USE_API_MOCKS=$USE_API_MOCKS"
      MOCK=1
    fi
    
    if [ -n "$COLLECT_COVERAGE" ]; then
      echo "- COLLECT_COVERAGE=$COLLECT_COVERAGE"
      ENV_VARS="$ENV_VARS COLLECT_COVERAGE=$COLLECT_COVERAGE"
      if [ "$COLLECT_COVERAGE" = "true" ]; then
        FORCE_COVERAGE=1
      fi
    fi
  fi
}

# 環境変数をチェック
check_env_vars

# テスト種別が指定されていない場合はエラー
if [ -z "$TEST_TYPE" ]; then
  print_error "テスト種別を指定してください"
  show_help
  exit 1
fi

# テスト種別が「specific」で、パターンが指定されていない場合はエラー
if [ "$TEST_TYPE" = "specific" ] && [ -z "$SPECIFIC_PATTERN" ]; then
  print_error "specific テスト種別を使用する場合は -s オプションでパターンを指定してください"
  show_help
  exit 1
fi

# クリーンアップが指定された場合は実行
if [ $CLEAN -eq 1 ]; then
  print_info "テスト環境をクリーンアップしています..."
  npm run test:clean
  print_success "クリーンアップ完了"
fi

# テスト環境のセットアップ
print_info "テスト環境をセットアップしています..."
npm run test:setup
print_success "セットアップ完了"

# カバレッジ目標に応じた環境変数を設定
case $COVERAGE_TARGET in
  initial)
    print_info "カバレッジ目標: 初期段階 (20-30%)"
    ENV_VARS="$ENV_VARS COVERAGE_TARGET=initial"
    ;;
  mid)
    print_info "カバレッジ目標: 中間段階 (40-60%)"
    ENV_VARS="$ENV_VARS COVERAGE_TARGET=mid"
    ;;
  final)
    print_info "カバレッジ目標: 最終段階 (70-80%)"
    ENV_VARS="$ENV_VARS COVERAGE_TARGET=final"
    ;;
esac

# 環境変数の設定
if [ $AUTO -eq 1 ]; then
  ENV_VARS="$ENV_VARS RUN_E2E_TESTS=true"
  print_info "APIサーバー自動起動モードが有効です"
fi

if [ $MOCK -eq 1 ]; then
  ENV_VARS="$ENV_VARS USE_API_MOCKS=true"
  print_info "APIモック使用モードが有効です"
fi

if [ $FORCE_TESTS -eq 1 ]; then
  ENV_VARS="$ENV_VARS FORCE_TESTS=true"
  print_info "テスト強制実行モードが有効です"
fi

if [ $DEBUG_MODE -eq 1 ]; then
  ENV_VARS="$ENV_VARS DEBUG=true"
  print_info "デバッグログが有効です"
fi

if [ $IGNORE_COVERAGE_ERRORS -eq 1 ]; then
  ENV_VARS="$ENV_VARS IGNORE_COVERAGE_ERRORS=true"
  print_info "カバレッジエラーを無視するモードが有効です"
fi

if [ $JUNIT_REPORT -eq 1 ]; then
  ENV_VARS="$ENV_VARS JEST_JUNIT_OUTPUT_DIR=./test-results/junit"
  print_info "JUnit形式のレポートを生成します"
fi

if [ $GENERATE_CHART -eq 1 ]; then
  ENV_VARS="$ENV_VARS GENERATE_COVERAGE_CHART=true"
  print_info "カバレッジチャートを生成します"
  VISUAL=1  # チャート生成時は自動的にビジュアルレポートを表示
  FORCE_COVERAGE=1  # チャート生成時は常にカバレッジを有効化
fi

if [ $VERBOSE_COVERAGE -eq 1 ]; then
  ENV_VARS="$ENV_VARS VERBOSE_COVERAGE=true"
  print_info "カバレッジデータ処理の詳細ログを出力します"
fi

# テストコマンドの構築
TEST_CMD=""
JEST_ARGS=""

# Jest設定ファイルを指定
JEST_ARGS="--config=$JEST_CONFIG_PATH"

# 非同期ハンドルの検出
if [ $DETECT_OPEN_HANDLES -eq 1 ]; then
  JEST_ARGS="$JEST_ARGS --detectOpenHandles"
  print_info "非同期ハンドルの検出が有効です"
fi

# テスト種別に基づいてJestの引数を設定
case $TEST_TYPE in
  unit)
    print_header "単体テストを実行中..."
    JEST_ARGS="$JEST_ARGS --selectProjects unit"
    ;;
  unit:services)
    print_header "サービス層の単体テストを実行中..."
    JEST_ARGS="$JEST_ARGS --selectProjects unit --testPathPattern=services"
    ;;
  unit:utils)
    print_header "ユーティリティの単体テストを実行中..."
    JEST_ARGS="$JEST_ARGS --selectProjects unit --testPathPattern=utils"
    ;;
  unit:function)
    print_header "API関数の単体テストを実行中..."
    JEST_ARGS="$JEST_ARGS --selectProjects unit --testPathPattern=function"
    ;;
  integration)
    print_header "統合テストを実行中..."
    JEST_ARGS="$JEST_ARGS --selectProjects integration"
    ;;
  integration:auth)
    print_header "認証関連の統合テストを実行中..."
    JEST_ARGS="$JEST_ARGS --selectProjects integration --testPathPattern=auth"
    ;;
  integration:market)
    print_header "マーケットデータ関連の統合テストを実行中..."
    JEST_ARGS="$JEST_ARGS --selectProjects integration --testPathPattern=marketData"
    ;;
  integration:drive)
    print_header "Google Drive関連の統合テストを実行中..."
    JEST_ARGS="$JEST_ARGS --selectProjects integration --testPathPattern=drive"
    ;;
  e2e)
    print_header "エンドツーエンドテストを実行中..."
    JEST_ARGS="$JEST_ARGS --selectProjects e2e"
    ;;
  all)
    print_header "すべてのテストを実行中..."
    JEST_ARGS="$JEST_ARGS --selectProjects unit integration e2e"
    ;;
  quick)
    print_header "クイックテスト（単体+統合）を実行中..."
    JEST_ARGS="$JEST_ARGS --selectProjects unit integration"
    ENV_VARS="$ENV_VARS USE_API_MOCKS=true"
    ;;
  specific)
    print_header "特定のパターンに一致するテストを実行中..."
    print_info "パターン: $SPECIFIC_PATTERN"
    JEST_ARGS="$JEST_ARGS --testPathPattern=$SPECIFIC_PATTERN"
    ;;
  *)
    print_error "不明なテスト種別: $TEST_TYPE"
    show_help
    exit 1
    ;;
esac

# カバレッジオプションの追加
if [ $FORCE_COVERAGE -eq 1 ]; then
  print_info "カバレッジ計測を強制的に有効化しています"
  # 明示的にカバレッジを有効化
  if [ $HTML_COVERAGE -eq 1 ]; then
    print_info "HTMLカバレッジレポートを生成します"
    JEST_ARGS="$JEST_ARGS --coverage --coverageReporters=lcov --coverageReporters=json-summary --coverageReporters=json"
  else
    JEST_ARGS="$JEST_ARGS --coverage --coverageReporters=json-summary --coverageReporters=json"
  fi
  # カバレッジ関連の環境変数を設定
  ENV_VARS="$ENV_VARS COLLECT_COVERAGE=true FORCE_COLLECT_COVERAGE=true"
  NO_COVERAGE=0
elif [ $NO_COVERAGE -eq 1 ]; then
  print_info "カバレッジチェックが無効化されています"
  JEST_ARGS="$JEST_ARGS --no-coverage"
else
  print_info "カバレッジ計測を有効化しています"
  # デフォルトでもカバレッジを有効化
  if [ $HTML_COVERAGE -eq 1 ]; then
    print_info "HTMLカバレッジレポートを生成します"
    JEST_ARGS="$JEST_ARGS --coverage --coverageReporters=lcov --coverageReporters=json-summary --coverageReporters=json"
  else
    JEST_ARGS="$JEST_ARGS --coverage --coverageReporters=json-summary --coverageReporters=json"
  fi
  # カバレッジ関連の環境変数を設定
  ENV_VARS="$ENV_VARS COLLECT_COVERAGE=true FORCE_COLLECT_COVERAGE=true"
fi

# JUnitレポート設定
if [ $JUNIT_REPORT -eq 1 ]; then
  JEST_ARGS="$JEST_ARGS --reporters=default --reporters=jest-junit"
fi

# カスタムレポーター設定
JEST_ARGS="$JEST_ARGS --reporters=default --reporters=./custom-reporter.js"

# 監視モードの設定
if [ $WATCH -eq 1 ]; then
  print_info "監視モードが有効です"
  JEST_ARGS="$JEST_ARGS --watch"
else
  # CI環境用の設定
  JEST_ARGS="$JEST_ARGS --forceExit"
fi

# テスト実行コマンドの準備
JEST_CMD="jest $JEST_ARGS"

# デバッグモードの場合、実行予定のコマンドを表示
if [ $DEBUG_MODE -eq 1 ] || [ $VERBOSE_COVERAGE -eq 1 ]; then
  print_info "実行するJestコマンド:"
  echo "npx $JEST_CMD"
  if [ -n "$ENV_VARS" ]; then
    print_info "環境変数:"
    echo "$ENV_VARS"
  fi
  echo ""
fi

# テストの実行
if [ -n "$ENV_VARS" ]; then
  # JESTのカバレッジ設定を強制的に有効化（.env.localの設定より優先）
  eval "npx cross-env JEST_COVERAGE=true COLLECT_COVERAGE=true FORCE_COLLECT_COVERAGE=true ENABLE_COVERAGE=true $ENV_VARS $JEST_CMD"
else
  # JESTのカバレッジ設定を強制的に有効化
  eval "npx cross-env JEST_COVERAGE=true COLLECT_COVERAGE=true FORCE_COLLECT_COVERAGE=true ENABLE_COVERAGE=true $JEST_CMD"
fi

# テスト結果
TEST_RESULT=$?

# カバレッジ関連ファイルのチェック
if [ $NO_COVERAGE -ne 1 ] || [ $FORCE_COVERAGE -eq 1 ]; then
  # カバレッジ結果ファイルの存在チェック
  if [ ! -f "./test-results/detailed-results.json" ]; then
    print_warning "カバレッジ結果ファイルが見つかりません。Jest実行中にエラーが発生した可能性があります。"
    
    # カバレッジディレクトリを確認
    if [ -d "./coverage" ]; then
      print_info "coverage ディレクトリが存在します。内容を確認します："
      ls -la ./coverage
      
      # coverage-final.json が存在するか確認
      if [ -f "./coverage/coverage-final.json" ]; then
        print_success "coverage-final.json ファイルが見つかりました。"
        
        # デバッグモードでカバレッジファイルの詳細を表示
        if [ $DEBUG_MODE -eq 1 ] || [ $VERBOSE_COVERAGE -eq 1 ]; then
          print_info "カバレッジファイルの先頭部分:"
          head -n 20 ./coverage/coverage-final.json
        fi
      else
        print_warning "coverage-final.json ファイルが見つかりません。"
        
        # 代替ファイルを確認
        for file in ./coverage/*; do
          if [ -f "$file" ]; then
            print_info "検出されたファイル: $file"
          fi
        done
      fi
    else
      print_warning "coverage ディレクトリが見つかりません。"
      print_info "カバレッジを有効にして再実行してみてください: --force-coverage オプションを使用"
    fi
  else
    # coverageMapプロパティの存在チェック
    if ! grep -q "coverageMap" ./test-results/detailed-results.json; then
      print_warning "カバレッジデータが結果ファイルに含まれていません。"
      print_info "Jest設定でcollectCoverageオプションが有効になっていることを確認してください。"
      
      # カバレッジファイルを直接コピー（緊急対応）
      if [ -f "./coverage/coverage-final.json" ]; then
        print_info "coverage-final.json ファイルを ./test-results/coverage-data.json にコピーします。"
        cp ./coverage/coverage-final.json ./test-results/coverage-data.json
      fi
    else
      print_success "カバレッジデータが結果ファイルに含まれています。"
    fi
  fi
fi

# カバレッジエラーを無視するモードが有効な場合
if [ $IGNORE_COVERAGE_ERRORS -eq 1 ] && [ -f "./test-results/detailed-results.json" ]; then
  # JSON結果ファイルを読み込んでテスト自体の成功/失敗を確認
  FAILED_TESTS=$(grep -o '"numFailedTests":[0-9]*' ./test-results/detailed-results.json | cut -d':' -f2)
  
  if [ "$FAILED_TESTS" = "0" ]; then
    print_info "テスト自体は成功していますが、カバレッジ要件を満たしていない可能性があります"
    print_info "カバレッジエラーを無視するモードが有効なため、テスト成功として扱います"
    TEST_RESULT=0
  fi
fi

# カバレッジチャート生成
if [ $GENERATE_CHART -eq 1 ] && [ $NO_COVERAGE -ne 1 ] && [ -f "./test-results/detailed-results.json" ]; then
  print_info "カバレッジチャートを生成しています..."
  
  # チャート生成スクリプトを実行
  npx cross-env NODE_ENV=production node ./scripts/generate-coverage-chart.js
  
  if [ $? -eq 0 ]; then
    print_success "カバレッジチャートが生成されました"
  else
    print_warning "カバレッジチャートの生成に失敗しました"
    # エラーの詳細を確認
    if [ $DEBUG_MODE -eq 1 ]; then
      print_info "チャート生成スクリプトを手動で実行してエラーを確認します..."
      NODE_ENV=production node --trace-warnings ./scripts/generate-coverage-chart.js
    fi
  fi
fi

# HTMLカバレッジレポートを開く
if [ $HTML_COVERAGE -eq 1 ] && [ $TEST_RESULT -eq 0 ]; then
  print_info "HTMLカバレッジレポートを開いています..."
  if [ -f "./coverage/lcov-report/index.html" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
      # macOS
      open ./coverage/lcov-report/index.html
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
      # Linux
      if command -v xdg-open > /dev/null; then
        xdg-open ./coverage/lcov-report/index.html
      else
        print_warning "xdg-open コマンドが見つかりません。ブラウザで ./coverage/lcov-report/index.html を開いてください。"
      fi
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
      # Windows
      start ./coverage/lcov-report/index.html
    else
      print_warning "未知のOSタイプです。ブラウザで ./coverage/lcov-report/index.html を開いてください。"
    fi
  else
    print_warning "カバレッジレポートが見つかりません。"
  fi
fi

# 視覚的レポートが指定された場合
if [ $VISUAL -eq 1 ]; then
  print_info "テスト結果をビジュアルレポートで表示します..."
  if [ -f "./test-results/visual-report.html" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
      # macOS
      open ./test-results/visual-report.html
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
      # Linux
      if command -v xdg-open > /dev/null; then
        xdg-open ./test-results/visual-report.html
      else
        print_warning "xdg-open コマンドが見つかりません。ブラウザで ./test-results/visual-report.html を開いてください。"
      fi
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
      # Windows
      start ./test-results/visual-report.html
    else
      print_warning "未知のOSタイプです。ブラウザで ./test-results/visual-report.html を開いてください。"
    fi
  else
    print_warning "ビジュアルレポートが見つかりません。"
  fi
fi

# テスト成功・失敗のヘッダーを表示
if [ $TEST_RESULT -eq 0 ]; then
  print_header "テスト実行が成功しました! 🎉"
else
  print_header "テスト実行が失敗しました... 😢"
  
  # テスト自体は成功しているが、Jest終了コードが非ゼロの場合の特別なメッセージ
  if grep -q "Test Suites: .* passed, .* total" ./test-results/test-log.md 2>/dev/null && 
     ! grep -q "Test Suites: .* failed" ./test-results/test-log.md 2>/dev/null; then
    print_warning "すべてのテストは成功していますが、Jest終了コードに問題があります"
    print_info "非同期処理の完了を待機していない可能性があります（--detect-open-handles オプションを試してください）"
  fi
fi

# カバレッジ情報の表示（テスト結果に関わらず表示）
if [ -f "./test-results/detailed-results.json" ] && grep -q "coverageMap" ./test-results/detailed-results.json; then
  # 各カバレッジメトリクスを取得（より堅牢な方法）
  # json形式を考慮し、jqがあれば使用、なければgrepとawk
  if command -v jq > /dev/null; then
    if jq -e '.coverageMap.total.statements.pct' ./test-results/detailed-results.json > /dev/null 2>&1; then
      STATEMENTS_COVERAGE=$(jq '.coverageMap.total.statements.pct' ./test-results/detailed-results.json)
      BRANCHES_COVERAGE=$(jq '.coverageMap.total.branches.pct' ./test-results/detailed-results.json)
      FUNCTIONS_COVERAGE=$(jq '.coverageMap.total.functions.pct' ./test-results/detailed-results.json)
      LINES_COVERAGE=$(jq '.coverageMap.total.lines.pct' ./test-results/detailed-results.json)
    else
      # フォールバック - 数値を確実に取得
      print_warning "jqでのカバレッジデータ取得に失敗しました。代替方法を使用します。"
      STATEMENTS_COVERAGE=0
      BRANCHES_COVERAGE=0
      FUNCTIONS_COVERAGE=0
      LINES_COVERAGE=0
    fi
  else
    # 代替方法 - sedとgrepを使用
    STATEMENTS_COVERAGE=$(grep -o '"statements":{[^}]*"pct":[0-9.]*' ./test-results/detailed-results.json | sed 's/.*"pct":\([0-9.]*\).*/\1/g')
    BRANCHES_COVERAGE=$(grep -o '"branches":{[^}]*"pct":[0-9.]*' ./test-results/detailed-results.json | sed 's/.*"pct":\([0-9.]*\).*/\1/g')
    FUNCTIONS_COVERAGE=$(grep -o '"functions":{[^}]*"pct":[0-9.]*' ./test-results/detailed-results.json | sed 's/.*"pct":\([0-9.]*\).*/\1/g')
    LINES_COVERAGE=$(grep -o '"lines":{[^}]*"pct":[0-9.]*' ./test-results/detailed-results.json | sed 's/.*"pct":\([0-9.]*\).*/\1/g')
    
    # データが取得できなかった場合はデフォルト値を設定
    [ -z "$STATEMENTS_COVERAGE" ] && STATEMENTS_COVERAGE=0
    [ -z "$BRANCHES_COVERAGE" ] && BRANCHES_COVERAGE=0
    [ -z "$FUNCTIONS_COVERAGE" ] && FUNCTIONS_COVERAGE=0
    [ -z "$LINES_COVERAGE" ] && LINES_COVERAGE=0
  fi
  
  # カバレッジ目標段階とカバレッジ率の表示
  echo -e "${BLUE}カバレッジ目標段階: ${YELLOW}$COVERAGE_TARGET${NC}"
  
  # 目標に応じてカバレッジ率を色分け表示
  case $COVERAGE_TARGET in
    initial)
      # 20-30%目標
      THRESHOLD_STATEMENTS=30
      THRESHOLD_BRANCHES=20
      THRESHOLD_FUNCTIONS=25
      THRESHOLD_LINES=30
      ;;
    mid)
      # 40-60%目標
      THRESHOLD_STATEMENTS=60
      THRESHOLD_BRANCHES=50
      THRESHOLD_FUNCTIONS=60
      THRESHOLD_LINES=60
      ;;
    final)
      # 70-80%目標
      THRESHOLD_STATEMENTS=80
      THRESHOLD_BRANCHES=70
      THRESHOLD_FUNCTIONS=80
      THRESHOLD_LINES=80
      ;;
  esac
  
  # カバレッジ率の表示（目標達成状況に応じて色分け）
  # 数値比較のヘルパー関数
  compare_for_display() {
    local val1="$1"
    local val2="$2"
    if [ $(echo "$val1 >= $val2" | bc -l 2>/dev/null) -eq 1 ] 2>/dev/null; then
      return 0  # true - 目標達成
    else
      return 1  # false - 目標未達
    fi
  }
  
  if compare_for_display "$STATEMENTS_COVERAGE" "$THRESHOLD_STATEMENTS"; then
    echo -e "Statements: ${GREEN}${STATEMENTS_COVERAGE}%${NC} (目標: ${THRESHOLD_STATEMENTS}%)"
  else
    echo -e "Statements: ${RED}${STATEMENTS_COVERAGE}%${NC} (目標: ${THRESHOLD_STATEMENTS}%)"
  fi
  
  if compare_for_display "$BRANCHES_COVERAGE" "$THRESHOLD_BRANCHES"; then
    echo -e "Branches:   ${GREEN}${BRANCHES_COVERAGE}%${NC} (目標: ${THRESHOLD_BRANCHES}%)"
  else
    echo -e "Branches:   ${RED}${BRANCHES_COVERAGE}%${NC} (目標: ${THRESHOLD_BRANCHES}%)"
  fi
  
  if compare_for_display "$FUNCTIONS_COVERAGE" "$THRESHOLD_FUNCTIONS"; then
    echo -e "Functions:  ${GREEN}${FUNCTIONS_COVERAGE}%${NC} (目標: ${THRESHOLD_FUNCTIONS}%)"
  else
    echo -e "Functions:  ${RED}${FUNCTIONS_COVERAGE}%${NC} (目標: ${THRESHOLD_FUNCTIONS}%)"
  fi
  
  if compare_for_display "$LINES_COVERAGE" "$THRESHOLD_LINES"; then
    echo -e "Lines:      ${GREEN}${LINES_COVERAGE}%${NC} (目標: ${THRESHOLD_LINES}%)"
  else
    echo -e "Lines:      ${RED}${LINES_COVERAGE}%${NC} (目標: ${THRESHOLD_LINES}%)"
  fi
  
  # 現在のカバレッジ率と目標カバレッジ率のサマリー表示
  echo -e "\n${BLUE}現在のカバレッジ率サマリー:${NC}"
  echo -e "Statements: ${STATEMENTS_COVERAGE}% | Branches: ${BRANCHES_COVERAGE}% | Functions: ${FUNCTIONS_COVERAGE}% | Lines: ${LINES_COVERAGE}%"
  
  echo -e "${BLUE}目標カバレッジ率:${NC}"
  echo -e "Statements: ${THRESHOLD_STATEMENTS}% | Branches: ${THRESHOLD_BRANCHES}% | Functions: ${THRESHOLD_FUNCTIONS}% | Lines: ${THRESHOLD_LINES}%"
  
  # 次の目標段階の提案
  ALL_TARGETS_MET=1
  
  # 数値比較の安全な実行
  compare_values() {
    local val1="$1"
    local val2="$2"
    if [ $(echo "$val1 < $val2" | bc -l 2>/dev/null) -eq 1 ] 2>/dev/null; then
      return 0  # true
    else
      return 1  # false
    fi
  }
  
  # カバレッジが目標未達の場合
  if compare_values "$STATEMENTS_COVERAGE" "$THRESHOLD_STATEMENTS" || \
     compare_values "$BRANCHES_COVERAGE" "$THRESHOLD_BRANCHES" || \
     compare_values "$FUNCTIONS_COVERAGE" "$THRESHOLD_FUNCTIONS" || \
     compare_values "$LINES_COVERAGE" "$THRESHOLD_LINES"; then
    ALL_TARGETS_MET=0
  fi
  
  if [ $ALL_TARGETS_MET -eq 1 ]; then
    case $COVERAGE_TARGET in
      initial)
        print_success "初期段階の目標を達成しました！次は中間段階(-t mid)に挑戦しましょう"
        ;;
      mid)
        print_success "中間段階の目標を達成しました！次は最終段階(-t final)に挑戦しましょう"
        ;;
      final)
        print_success "最終段階の目標を達成しました！素晴らしい成果です 🎉"
        ;;
    esac
  else
    print_warning "現在の段階の目標をまだ達成していません。引き続きテスト実装を進めましょう"
    
    # 未達成の目標を表示
    echo -e "${YELLOW}未達成の目標:${NC}"
    if compare_values "$STATEMENTS_COVERAGE" "$THRESHOLD_STATEMENTS"; then
      echo -e "- Statements: ${RED}${STATEMENTS_COVERAGE}%${NC} → ${YELLOW}${THRESHOLD_STATEMENTS}%${NC}"
    fi
    if compare_values "$BRANCHES_COVERAGE" "$THRESHOLD_BRANCHES"; then
      echo -e "- Branches:   ${RED}${BRANCHES_COVERAGE}%${NC} → ${YELLOW}${THRESHOLD_BRANCHES}%${NC}"
    fi
    if compare_values "$FUNCTIONS_COVERAGE" "$THRESHOLD_FUNCTIONS"; then
      echo -e "- Functions:  ${RED}${FUNCTIONS_COVERAGE}%${NC} → ${YELLOW}${THRESHOLD_FUNCTIONS}%${NC}"
    fi
    if compare_values "$LINES_COVERAGE" "$THRESHOLD_LINES"; then
      echo -e "- Lines:      ${RED}${LINES_COVERAGE}%${NC} → ${YELLOW}${THRESHOLD_LINES}%${NC}"
    fi
  fi
fi

# エラー処理（テスト失敗時のみ）
if [ $TEST_RESULT -ne 0 ]; then
  # デバッグモードの場合、詳細情報を表示
  if [ $DEBUG_MODE -eq 1 ]; then
    print_info "テスト失敗の詳細情報:"
    echo "テスト種別: $TEST_TYPE"
    echo "終了コード: $TEST_RESULT"
    
    if [ -f "./test-results/detailed-results.json" ]; then
      FAILED_TESTS=$(grep -o '"numFailedTests":[0-9]*' ./test-results/detailed-results.json | cut -d':' -f2)
      print_info "失敗したテスト数: $FAILED_TESTS"
      
      # 失敗したテストの詳細を表示（最大5件）
      if [ -f "./test-results/test-log.md" ]; then
        echo "失敗したテストの詳細:"
        grep -A 5 "## エラーサマリー" ./test-results/test-log.md | head -10
      fi
    fi
    
    echo "ログファイルは ./test-results/ ディレクトリにあります"
  fi
  
  # 改善提案を表示
  print_info "改善提案:"
  echo "- 詳細なエラー情報を確認: cat ./test-results/test-log.md"
  echo "- ビジュアルレポートを表示: ./scripts/run-tests.sh -v $TEST_TYPE"
  echo "- モックモードでテストを再実行: ./scripts/run-tests.sh -m $TEST_TYPE"
  echo "- カバレッジエラーを無視してテスト: ./scripts/run-tests.sh -i $TEST_TYPE"
  echo "- カバレッジの問題が原因の場合は強制的に有効化: ./scripts/run-tests.sh --force-coverage $TEST_TYPE"
  echo "- デバッグモードで詳細情報を表示: ./scripts/run-tests.sh -d $TEST_TYPE"
  echo "- カバレッジデータ処理の詳細を確認: ./scripts/run-tests.sh --verbose-coverage $TEST_TYPE"
  echo "- 非同期ハンドル問題を検出: ./scripts/run-tests.sh --detect-open-handles $TEST_TYPE"
fi

# テスト後のクリーンアップ提案
if [ $TEST_RESULT -eq 0 ] && [ $CLEAN -ne 1 ]; then
  print_info "次回のテスト実行前に環境をクリーンアップすることをお勧めします:"
  echo "  ./scripts/run-tests.sh -c ..."
fi

exit $TEST_RESULT
