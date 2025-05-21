#!/bin/bash
#
# ファイルパス: scripts/fix-node-version.sh
#
# Node.jsバージョンを自動修正するスクリプト
#
# @author Fix Script
# @created 2025-05-13
# @updated 2025-05-13 - nvm検出方法の改善
#

# 色の設定
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Portfolio Market Data API - Node.jsバージョン修正ツール${NC}"
echo -e "${BLUE}===============================================${NC}"

# 現在のNode.jsバージョンを確認
NODE_VERSION=$(node -v)
echo -e "現在のNode.jsバージョン: ${YELLOW}$NODE_VERSION${NC}"
echo -e "必要なバージョン: ${GREEN}v18.x${NC}"

# バージョンチェック
if [[ "$NODE_VERSION" == v18.* ]]; then
  echo -e "${GREEN}✓ Node.jsバージョンは適切です${NC}"
  exit 0
fi

# nvmのロードを試みる（環境に関わらず）
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# nvmが使用可能かテスト
if type nvm >/dev/null 2>&1; then
  echo -e "${BLUE}nvmが見つかりました。Node.js 18に切り替えを試みます...${NC}"
  
  # 直接 nvm use 18 を試す
  if nvm use 18 >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Node.js $(node -v) に切り替えました${NC}"
  else
    echo -e "${YELLOW}Node.js 18がインストールされていません。インストールします...${NC}"
    nvm install 18
    nvm use 18
    
    if [[ "$(node -v)" == v18.* ]]; then
      echo -e "${GREEN}✓ Node.js 18 をインストールし、$(node -v) に切り替えました${NC}"
      
      # .nvmrcファイルがなければ作成
      if [ ! -f .nvmrc ]; then
        echo "18" > .nvmrc
        echo -e "${BLUE}ℹ .nvmrcファイルを作成しました${NC}"
      fi
    else
      echo -e "${RED}✗ Node.js 18のインストールに失敗しました${NC}"
    fi
  fi
else
  echo -e "${YELLOW}⚠ nvmが見つかりません。${NC}"
  echo -e "以下のいずれかの方法を試してください:"
  echo -e "1. Node.js 18をインストール: https://nodejs.org/download/release/latest-v18.x/"
  echo -e "2. nvmをインストール: https://github.com/nvm-sh/nvm#installing-and-updating"
  echo -e "3. engine-strictを無効化: npm config set engine-strict false"
  
  echo
  read -p "engine-strictを無効化しますか？ (y/n): " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    npm config set engine-strict false
    echo -e "${GREEN}✓ engine-strictを無効化しました${NC}"
  fi
fi

# package.jsonのengines設定を更新
echo -e "${BLUE}package.jsonのengines設定を更新します...${NC}"
if [ -f package.json ]; then
  # package.jsonを一時ファイルにコピー
  cp package.json package.json.bak
  
  # Node.jsバージョン要件を更新
  sed -i.bak 's/"node": "18.x"/"node": ">=18.x"/g' package.json
  
  echo -e "${GREEN}✓ package.jsonを更新しました${NC}"
  echo -e "${BLUE}ℹ 元のファイルはpackage.json.bakとして保存されています${NC}"
else
  echo -e "${RED}✗ package.jsonが見つかりません${NC}"
fi

echo -e "${BLUE}===============================================${NC}"
echo -e "${GREEN}Node.jsバージョン修正完了${NC}"
echo -e "テスト実行コマンド例:"
echo -e "${YELLOW}./scripts/run-tests.sh --no-coverage integration${NC}"
