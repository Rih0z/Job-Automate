# 統合プロンプト：API仕様書 & 簡潔README.md更新

現在のコードベースから最新のAPI仕様を抽出し、1分で読めるREADME.mdに更新してください。既存の資料を更新し、新しいドキュメントを作らないでください。全てのドキュメントについて、README.mdから参照してください。詳細はREADME.mdから他のドキュメントへ案内する形にしてください。

## STEP 1: 既存ドキュメント構造の確認と適応

### 1.1 既存ファイルの特定
```bash
# README.mdとAPI関連ドキュメントを探索
serena find-files --pattern="README*|readme*|API*|api*|openapi*|swagger*"
serena analyze-existing-api-docs --extract-structure
serena detect-api-versioning-strategy
```

### 1.2 適切な配置先の決定
```bash
# 既存の構造に合わせた配置戦略
serena determine-api-doc-location --follow-conventions
# 候補: /docs/api/, /api-docs/, /spec/, /swagger/ など
```

## STEP 2: API仕様書の生成・更新

### 2.1 API エンドポイントの自動検出
```bash
serena scan-api-endpoints --recursive --all-frameworks
serena analyze-route-definitions --extract-metadata
serena identify-auth-mechanisms --detailed
serena extract-data-models --with-validation-rules
```

### 2.2 OpenAPI仕様の生成
```bash
serena generate-openapi-schema --version=3.0 --comprehensive
serena validate-api-consistency --check-implementations
serena generate-api-examples --realistic-data
serena create-postman-collection --include-auth
```

### 2.3 API変更の検出と文書化
```bash
# 既存API仕様との比較（存在する場合）
serena compare-api-versions --detect-breaking-changes
serena generate-api-changelog --semantic-versioning
```

## STEP 3: 1分で読めるREADME.md作成

### 3.1 プロジェクト基本情報の抽出
```bash
serena extract-project-metadata --essential-only
serena identify-primary-use-case --one-liner
serena detect-quick-start-requirements --minimal
```

### 3.2 簡潔なREADME.md構成
**目標読了時間: 60秒以内**

```markdown
# プロジェクト名

> [30文字以内の簡潔な説明]

[![Build](badge)](#) [![Coverage](badge)](#) [![Version](badge)](#)

## 🚀 クイックスタート

```bash
# 3ステップで起動
npm install
cp .env.example .env
npm start
```

アプリは http://localhost:3000 で起動します。

## 📋 主な機能

- **機能1**: 簡潔な説明
- **機能2**: 簡潔な説明  
- **機能3**: 簡潔な説明

## 📚 ドキュメント

| 内容 | リンク |
|------|--------|
| 🏗️ アーキテクチャ | [docs/architecture/](./docs/architecture/) |
| 🔌 API仕様 | [docs/api/](./docs/api/) |
| 🚀 デプロイ | [docs/deployment.md](./docs/deployment.md) |
| 🔧 開発ガイド | [docs/development.md](./docs/development.md) |

## 🤝 貢献

[CONTRIBUTING.md](./CONTRIBUTING.md) をご覧ください。

---
**ライセンス**: [LICENSE](./LICENSE) | **更新**: [CHANGELOG.md](./CHANGELOG.md)
```

## 出力ファイル構成（.tmp内作業→確定配置）

### A. .tmp内でのREADME.md更新（既存ファイル保持）
**既存README.mdの.tmp内簡潔化戦略**：
```bash
# .tmp内での既存README.md処理
if [ -f ".tmp/readme-work/README.md" ]; then
    # 既存重要情報の抽出・保持
    serena extract-readme-sections ".tmp/readme-work/README.md" --preserve-badges --preserve-license --output=".tmp/readme-work/preserved.md"
    
    # 詳細情報の移行先決定・作成
    serena create-detailed-docs ".tmp/readme-work/detailed/" --from-existing-readme
    
    # 60秒読了版の作成
    serena create-concise-readme ".tmp/readme-work/" --input="README.md" --output="README-final.md" --preserve-preserved-content
fi
```

### B. .tmp内でのAPI仕様書セット（既存ファイル更新優先）

#### 1. .tmp内での既存API仕様ファイル更新
```bash
# 既存ファイル名パターンに応じた.tmp内更新戦略
if [ -f ".tmp/api-work/original/api.md" ]; then
    serena update-api-doc ".tmp/api-work/original/api.md" --enhance-openapi-integration --output=".tmp/api-work/api-updated.md"
elif [ -f ".tmp/api-work/original/API.md" ]; then  
    serena update-api-doc ".tmp/api-work/original/API.md" --preserve-structure --output=".tmp/api-work/API-updated.md"
elif [ -f ".tmp/api-work/original/swagger.yaml" ]; then
    serena migrate-to-openapi3 ".tmp/api-work/original/swagger.yaml" --preserve-examples --output=".tmp/api-work/openapi.yaml"
    serena create-api-readme ".tmp/api-work/" --from-openapi --output="api-docs.md"
else
    # 新規作成
    serena create-complete-api-spec ".tmp/api-work/" --from-analysis
fi
```

### C. .tmp内での開発者向け詳細ガイド（既存ファイル活用）
```bash
# 既存開発関連ファイルの.tmp内処理
if [ -f "DEVELOPMENT.md" ]; then
    cp "DEVELOPMENT.md" ".tmp/readme-work/DEVELOPMENT-original.md"
    serena enhance-development-guide ".tmp/readme-work/DEVELOPMENT-original.md" --output=".tmp/readme-work/DEVELOPMENT-enhanced.md"
elif [ -f "SETUP.md" ]; then
    cp "SETUP.md" ".tmp/readme-work/SETUP-original.md"
    serena convert-setup-to-development ".tmp/readme-work/SETUP-original.md" --output=".tmp/readme-work/DEVELOPMENT.md"
else
    # README.mdから移行した詳細情報で新規作成
    serena create-development-guide ".tmp/readme-work/detailed/" --output=".tmp/readme-work/DEVELOPMENT.md"
fi
```

## STEP 4: .tmp内成果物の確認・承認

### 4.1 .tmp内品質チェック
```bash
# .tmp内で生成されたファイルの品質確認
serena validate-readme-reading-time ".tmp/readme-work/README-final.md" --target=60-seconds
serena test-quick-start ".tmp/readme-work/" --fresh-environment
serena validate-api-doc-accuracy ".tmp/api-work/" --compare-implementation

# 既存ファイルとの差分確認
serena show-changes --original=".tmp/readme-work/README.md" --updated=".tmp/readme-work/README-final.md"
serena show-api-changes --original=".tmp/api-work/original/" --updated=".tmp/api-work/"
```

### 4.2 中間承認プロセス
```bash
echo "=== README.md簡潔化結果確認 ==="
echo "📖 読了時間: $(serena measure-reading-time '.tmp/readme-work/README-final.md')"
echo "📋 移行された詳細情報: $(ls .tmp/readme-work/detailed/)"
echo ""
echo "=== API仕様書更新結果確認 ==="
echo "🔌 OpenAPI仕様: $(ls .tmp/api-work/*.yaml)"
echo "📚 更新されたAPI文書: $(ls .tmp/api-work/*api*.md)"
echo ""
echo "承認して本配置を実行しますか？ [y/N]"
read approval

if [[ $approval == "y" || $approval == "Y" ]]; then
    echo "✅ 承認されました。本配置を実行します。"
    serena proceed-to-deployment
else
    echo "⏸️ .tmp内で作業を継続します。"
fi
```

## STEP 5: .tmp→本番配置・クリーンアップ

### 5.1 既存ファイル名保持での配置実行
```bash
# README.mdとAPI関連ファイルの配置
serena deploy-readme --source=".tmp/readme-work/README-final.md" --destination="README.md" --backup-original
serena deploy-api-docs --source=".tmp/api-work/" --destination="." --preserve-existing-paths

# 新規作成された詳細ドキュメントの配置
if [ ! -f "DEVELOPMENT.md" ]; then
    cp ".tmp/readme-work/DEVELOPMENT.md" "DEVELOPMENT.md"
    echo "✅ DEVELOPMENT.md created from README.md details"
fi

# API仕様書の適切な配置
serena deploy-api-specs ".tmp/api-work/" --existing-file-names-priority
```

### 5.2 配置ログ・クリーンアップ
```bash
# 配置結果の記録
serena log-readme-api-deployment --changes-summary --reading-time-achieved
echo "📋 README.md: $(serena measure-reading-time 'README.md') 読了"
echo "🔌 API仕様: $(serena count-api-endpoints) エンドポイント文書化"
echo "📚 新規作成: $(serena list-newly-created-files)"

# .tmpクリーンアップ（作業履歴保持）
serena archive-api-readme-work --source=".tmp/" --destination=".tmp/archive/api-readme-$(date +%Y%m%d-%H%M)"
serena cleanup-tmp-workspace --keep-successful-archive

echo "✅ API仕様書・README.md更新完了"
echo "📁 作業履歴: .tmp/archive/api-readme-$(date +%Y%m%d-%H%M)/"
```

## 実行時の動的判断

### 既存README.mdの処理
```bash
# 既存README.mdが存在する場合
if [ -f "README.md" ]; then
    # 重要な情報を抽出して保持
    serena extract-important-sections --preserve-custom
    # 既存の詳細情報を適切なドキュメントに移行
    serena migrate-detailed-content --to-docs-folder
fi
```

### API仕様の段階的更新
```bash
# 既存API仕様書がある場合
serena merge-api-specifications --preserve-custom-examples
serena update-version-info --semantic-increment
```

## 品質保証と検証

### 1. README.md読了時間の測定
```bash
serena measure-reading-time --target=60-seconds
serena validate-quick-start --actual-test
```

### 2. API仕様の精度確認
```bash
serena validate-openapi-spec --lint
serena test-api-examples --live-endpoints
serena check-auth-flow --end-to-end
```

### 3. ドキュメント間のリンク整合性
```bash
serena validate-internal-links --comprehensive
serena check-navigation-flow --user-journey
```

## 自動化設定

### リアルタイム更新
```bash
# コード変更時のAPI仕様自動更新
serena setup-api-doc-automation --on-commit
serena configure-spec-validation --ci-integration
```

### メトリクス追跡
```bash
# README.mdの効果測定
serena track-doc-engagement --reading-patterns
serena measure-developer-onboarding --time-to-first-success
```

このプロンプトにより、既存プロジェクト構造を尊重しつつ、1分で読めるREADME.mdと包括的な仕様書を生成できます。
Ultrathink. Don't hold back. give it your all！
