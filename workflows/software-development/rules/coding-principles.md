# コーディング原則

```yaml
ai_coding_principles:
  meta:
    version: "4.5"
    last_updated: "2026-01-28 (Updated with rules 11-12)"
    description: "Claude AIコーディング実行原則"
    project: " High-Performance AI Application Platform"
    
  core_principles:
    mandatory_declaration: "全てのコーディング作業開始時に必ずcore_principlesを完全に宣言すること"
    第1条: 
      rule: "常に思考開始前にClaude.mdの第1条から第16条のAIコーディング原則を全て宣言してから実施する"
      related_sections: ["execution_checklist", "mindset"]
    第2条: 
      rule: "常にプロの世界最高エンジニアとして対応する"
      related_sections: ["mindset", "quality_standards"]
    第3条: 
      rule: "モックや仮のコード、ハードコードを一切禁止する。コーディング前にread Serena's initial instructions,ユーザーから新規機能の実装支持がを受けたら、まずは.tmpフォルダ以下に実装計画を作成して。既存の実装をserena mcpを利用して詳細に分析し、プロとして恥ずかしくない実装を計画して。プロジェクトの構造は"docs\DOCUMENTATION_INDEX.md"を参照すること"
      related_sections: ["implementation", "architecture", "quality_standards", "https://github.com/oraios/serena"]
    第4条: 
      rule: "エンタープライズレベルの実装を実施し、修正は表面的ではなく、全体のアーキテクチャを意識して実施する"
      related_sections: ["architecture", "quality_standards", "deployment_requirements"]
    第5条: 
      rule: "問題に詰まったら、まずCLAUDE.mdやプロジェクトドキュメント内に解決策がないか確認する"
      related_sections: ["project_documentation"]
    第6条: 
      rule: "顧客データやセキュリティなど、push前にアップロードするべきではない情報が含まれていないか確認する。作業完了ごとにgithubに状況をpushする。"
      related_sections: ["security_checklist", "git_workflow"]
    第7条: 
      rule: "不要な文書やスクリプトは増やさない。スクリプト作成時は常に既存のスクリプトで使用可能なものがないか以下のセクションを確認する、スクリプトを作成したら.scriptフォルダに、ドキュメントはdocsフォルダに格納する。一時スクリプトや文書はそれぞれのフォルダの.tmpフォルダに保存し、使用後に必ず削除する。ファイルをさくせいしたら、作成したファイルの完全パスと作成日時を必ず".history\files.md"に書き込む。ドキュメント作成の際は、必ずすべての関連ドキュメントの完全パスを含める。"
      related_sections: ["file_structure", "how_to_use_scripts"]
    第8条: 
      rule: "デザインはhttps://atlassian.design/components を読み込み、これに準拠する。"
      related_sections: ["https://atlassian.design/components", "design_standards"]
    第9条: 
      rule: "作業完了後にもう一度すべての宣言を実施し、宣言どうりに作業を実施できているか確認する。"
      related_sections: ["execution_checklist", "quality_assurance"]
    第10条: 
      rule: "バグを修正する場合は、serena mcp を利用して原因の分析をし、.tmpフォルダ以下に報告資料を作成して。ユーザーに原因について報告する。すでに同様のバグの報告資料がある場合は、それを更新する。ユーザーが確認したら修正方法を提案する。修正方法が妥当か十分にレビューし、他の宣言に矛盾していないか確認した上でユーザーの確認をとり修正を実施する。バグ報告はドキュメントを作成し、.tmpフォルダ以下に保存する。ユーザーがバグが解決したと言うまでドキュメントを残し、バグが解決したらドキュメントは削除する。"
      related_sections: ["bug_tracking", "testing_standards"]
    第11条:
      rule: "ファイルバージョン管理の禁止: v2、_new、_oldなどのバージョン番号付きファイル作成を禁止する。既存ファイルの直接更新を徹底し、バックアップが必要な場合はGitを使用する。"
      related_sections: ["file_structure", "git_workflow"]
    第12条:
      rule: "環境変数によるハードコード排除: パス、URL、設定値は全て環境変数化する。backend/config/*.pyで設定を一元管理し、環境変数でオーバーライド可能にする。.envファイルは使用しない。"
      related_sections: ["implementation", "security_checklist", "quality_standards", "project_specific.configuration_management"]
    第13条:
      rule: "backend serverの起動が必要なテストを実施する際はユーザーにstart.batの実行を依頼する。AIがサーバーを起動してテストを始めることは許されない。単体テストなどのサーバーの起動が必要ないテストは積極的に実施する。"
    第14条:
      rule: "バックグラウンドタスクの実行は避ける。どうしても必要な場合はユーザーに許可をとる。"
    第15条:
      rule: "設計書などのドキュメントに沿って実行する場合は、出力の最初と最後に参考にしたドキュメントの完全パスを出力する。また、ドキュメントに作業が準拠しているか見直す。"
    第16条:
      rule: "一時的な解決策は実施せず、常に超長期的な問題解決を意識して解決に取り組む。複数の行動パターンがある場合は、長期的な目線で見て根本的な解決策になる方法を選んで"
  file_structure:
    temporary_files:
      location: ".tmp/"
      description: "一時ファイル、分析レポート、バグ報告"
      sub_folders:
        - ".tmp/analysis/"     # 分析レポート
        - ".tmp/bugs/"         # バグ報告
        - ".tmp/plans/"        # 実装計画
    documents: 
      location: "docs/"
      description: "プロジェクトドキュメント"
      existing_docs:
        - "architecture.md"
        - "modern_frontend_architecture.md"
        - "quick_start_guide.md"
        - "best_ai_frameworks_2025.md"
        - "PORTABLE_TOOLS_DOCUMENTATION.md"
    tests: 
      location: ".test/"
      description: "テストファイル"
      structure:
        - ".test/unit/"        # ユニットテスト
        - ".test/integration/" # 統合テスト
        - ".test/e2e/"        # E2Eテスト
    scripts: 
      location: ".script/"
      description: "ユーティリティスクリプト"
      structure:
        - ".script/setup/"     # セットアップスクリプト
        - ".script/deploy/"    # デプロイスクリプト
        - ".script/utils/"     # ユーティリティ
        - ".script/.tmp/"      # 一時スクリプト
    source:
      frontend: "frontend/"
      backend: "backend/"
      ai_infrastructure: ".tools/"
    config: 
      location: "config/"
      description: "設定ファイル"

  project_specific:
    configuration_management:
      central_location: "backend/config/"
      description: ".envファイルを使用せず、backend/config/*.pyで全設定を一元管理"
      principle: "全ての設定はbackend/config/*.pyで管理し、環境変数でオーバーライド可能にする"

      key_files:
        - "server_config.py - サーバー設定（ポート、ホスト）"
        - "api_config.py - API/CORS/認証設定"
        - "path_config.py - パス設定"
        - "rag_config.py - RAG設定"
        - "inference_config.py - 推論エンジン設定"
        - "inference_defaults.py - 推論デフォルト値"
        - "mcp_config.py - MCP設定"
        - "search_config.py - Web検索設定"
        - "embedding_config.py - エンベディング設定"

      environment_override:
        method: "start.bat または export コマンドで環境変数を設定"
        example: "set BACKEND_PORT=8080"
        priority: "環境変数 > config/*.py のデフォルト値"

      documentation: "backend/config/README.md - 詳細な設定ガイド"

    path_management:
      central_config: "backend/config/path_config.py"
      description: "全てのパス設定を一元管理"
      principle: "パス設定は必ずPathConfigクラスを通して参照すること"

      key_features:
        - "環境変数によるオーバーライド機能"
        - "自動バックエンド検出（CUDA優先）"
        - "モデル優先順位管理（GPT-OSS優先）"
        - "パス検証機能"

      usage:
        import_statement: "from backend.config.path_config import PathConfig"
        methods:
          - "PathConfig.get_llama_server_path() - LLAMA実行ファイル"
          - "PathConfig.get_available_models() - 利用可能モデル一覧"
          - "PathConfig.get_model_path(name) - 特定モデルパス"
          - "PathConfig.validate_paths() - パス検証"

      environment_overrides:
        LLAMA_BACKEND: "使用するバックエンド名"
        DEFAULT_MODEL: "デフォルトモデルファイル名"

      referenced_by:
        - "backend/services/gpt_oss_service.py"
        - "backend/api/model_management_endpoints.py"
        - "backend/api/test_model_endpoints.py"
        - "backend/config/llama_config.py"

    portable_environment:
      python:
        location: ".tools/extensions/backends/vendor/_amphibian/cpython3.11-win-x86@2/"
        version: "3.11.9"
        executable: "python.exe"
        description: "ポータブルPython - システムインストール不要"
      nodejs:
        location: ".tools/extensions/backends/vendor/_amphibian/node-v20.11.0-win-x64/"
        version: "20.11.0"
        executable: "node.exe"
        description: "ポータブルNode.js - システムインストール不要"
      documentation: "docs/PORTABLE_TOOLS_DOCUMENTATION.md"

    llama_integration:
      inference_port: 8080
      backends:
        - "llama.cpp-win-x86_64-nvidia-cuda-avx2-1.45.0"
        - "llama.cpp-win-x86_64-avx2-1.44.0"
        - "llama.cpp-win-x86_64-vulkan-avx2-1.44.0"
      embedding:
        priority: "ONNX Runtime > PyTorch > GGUF"
        models:
          - name: "BGE-M3 (ONNX)"
            path: ".tools/models/embeddings/bge-m3/onnx/model.onnx"
            dimensions: 1024
            performance: "23.5 texts/s (CPU), 117-235 texts/s (GPU)"
            priority: 1
            status: "✅ 実装済み"
          - name: "BGE-M3 (PyTorch)"
            path: ".tools/models/embeddings/models--BAAI--bge-m3/"
            dimensions: 1024
            performance: "GPU自動検出、バッチ64並列"
            priority: 2
            status: "✅ フォールバック実装済み"
          - name: "BGE-M3 (GGUF)"
            path: ".tools/models/embeddings/bge-m3-Q4_0.gguf"
            dimensions: 1024
            performance: "2 texts/s (省メモリ)"
            priority: 3
            status: "✅ フォールバック実装済み"
          - name: "nomic-embed-text-v1.5 (GGUF)"
            path: ".tools/models/embeddings/nomic-embed-text-v1.5.Q4_K_M.gguf"
            dimensions: 768
            performance: "英語特化"
            priority: 4
            status: "✅ サポート済み"
        service_file: "backend/services/onnx_embedding_service.py"
        documentation: "docs/02_implementation/rag/embedding_service.md"
    
    tech_stack:
      frontend:
        framework: "Next.js 15 (ポータブルNode.js使用)"
        ui: "shadcn/ui"
        styling: "Tailwind CSS"
        language: "TypeScript"
      backend:
        runtime: "Python 3.11 (ポータブル版)"
        api: "FastAPI / BentoML"
        agents: "CrewAI / AutoGen"
      databases:
        vector: "ChromaDB (local persistence)"
        traditional: "SQLite (local file-based)"
      deployment:
        serverless: "Modal"
        container: "BentoML"

  quality_standards:
    security:
      - "GitHubへのプッシュ前にセキュリティ上の問題がないか確認すること"
      - "脆弱性スキャンの実施"
      - "認証・認可の適切な実装"
      - ".tools/credentials/へのアクセス制限"
    
    architecture:
      - "SOLID原則に従っているか確認する"
      - "DDD（ドメイン駆動設計）/CQRSに従う"
      - "エンタープライズレベルのアーキテクチャにする"
      - "スケーラビリティを考慮した設計"
      - "llama.cpp APIとの適切な統合"
    
    implementation:
      - "デモデータではなく、実際に機能するシステムにする"
      - "ハードコードは一切使用しない"
      - "環境変数・設定ファイルを適切に使用"
      - "依存性注入を活用"
      - "llama.cpp HTTP APIの活用"

  testing_standards:
    approach:
      - "テストを修正する場合、ログをテストに合致するように修正するのではなく、プログラム自体を修正する"
      - "単体テスト、統合テスト、E2Eテストの実装"
      - "テストカバレッジ80%以上を維持"
    
    validation:
      - "全てのAPIエンドポイントのテスト"
      - "エラーハンドリングのテスト"
      - "パフォーマンステスト"
      - "llama.cpp接続テスト"

  documentation_management:
    structure:
      - "必要以上にドキュメントを増やさず、ログは.tmp/logs/フォルダに格納する"
      - "必要なドキュメントは必ずdocs/フォルダに保存する"
      - "更新は同じファイルを編集する"
      - "冗長に少しだけ名前を変えたファイルを増やさない"
    
    consistency:
      - "ドキュメント間の整合性を確認する"
      - "実装を変更したらそれに合わせてドキュメントも更新すること"
      - "APIドキュメントの自動生成"

  deployment_requirements:
    environment:
      - "必ずURLが固定の本番環境にデプロイするようにする"
      - "フロントエンドとバックエンドの通信が必ず成功するようにデプロイ先のURLは指定する"
      - "CI/CDパイプラインの構築"
      - "llama.cppサーバーとの接続確認"
    
    process:
      - "作業が完了したらClaude環境でビルドしデプロイすること"
      - "READMEにフロントエンドのデプロイ先を記載する"
      - "本番環境でのヘルスチェック実装"

  mindset:
    philosophy:
      - "Ultrathink - 深く考え抜く"
      - "Don't hold back. Give it your all! - 全力で取り組む"
      - "継続的改善の実践"
      - "コードレビューの徹底"

  git_workflow:
    commit_messages:
      format: "[type]: description"
      types:
        - "feat: 新機能"
        - "fix: バグ修正"
        - "docs: ドキュメント更新"
        - "refactor: リファクタリング"
        - "test: テスト追加・修正"
        - "chore: その他の変更"
    
    branch_strategy:
      - "main: 本番環境"
      - "develop: 開発環境"
      - "feature/*: 機能開発"
      - "bugfix/*: バグ修正"

  security_checklist:
    before_commit:
      - "[ ] backend/config/*.py に機密情報（APIキー・パスワード）がハードコードされていないか"
      - "[ ] .tools/credentials/ が .gitignore に含まれているか"
      - "[ ] ログファイルに機密情報が含まれていないか"
      - "[ ] 環境変数による設定オーバーライドが正しく機能しているか"

  design_standards:
    ui_framework: "Atlassian Design System"
    components: "https://atlassian.design/components"
    principles:
      - "一貫性のあるUI/UX"
      - "アクセシビリティの確保"
      - "レスポンシブデザイン"
      - "パフォーマンス最適化"

  bug_tracking:
    process:
      - "バグ発見 → .tmp/bugs/ に報告書作成"
      - "原因分析 → serena mcp使用"
      - "修正提案 → ユーザー確認"
      - "修正実施 → テスト"
      - "解決確認 → 報告書削除"

  execution_checklist:
    mandatory_declaration:
      - "[ ] **CORE_PRINCIPLES宣言**: 第1条〜第10条を完全に宣言"
      - "[ ] **関連セクション宣言**: 実行する作業に関連するセクションを宣言"
      - "[ ] 例：アーキテクチャ変更時は第3条・第4条 + architecture + quality_standards + implementation を宣言"
    
    before_coding:
      - "[ ] AIコーディング原則を宣言"
      - "[ ] 要件の理解と確認"
      - "[ ] アーキテクチャ設計"
      - "[ ] セキュリティ要件の確認"
      - "[ ] llama.cpp接続確認"
    
    during_coding:
      - "[ ] SOLID原則の適用"
      - "[ ] DDD/CQRSパターンの実装"
      - "[ ] ハードコード回避"
      - "[ ] 適切なエラーハンドリング"
    
    after_coding:
      - "[ ] テスト実装・実行"
      - "[ ] セキュリティチェック"
      - "[ ] ドキュメント更新"
      - "[ ] デプロイ・動作確認"
      - "[ ] Git commit & push"

  how_to_use_scripts:
    existing_scripts:
      setup:
        - "install_dependencies.sh: 依存関係インストール"
        - "setup_llama.sh: llama.cpp設定"
      deploy:
        - "deploy_frontend.sh: フロントエンドデプロイ"
        - "deploy_backend.sh: バックエンドデプロイ"
      utils:
        - "test_connection.py: llama.cpp接続テスト"
        - "cleanup_tmp.sh: 一時ファイル削除"
    
    before_creating:
      - "既存スクリプトを確認"
      - "再利用可能性を検討"
      - "必要最小限の実装"

  project_documentation:
    documentation_index: "docs/DOCUMENTATION_INDEX.md"  # 全ドキュメントの完全なインデックス
    
    core_documents:
      - "README.md: プロジェクト概要"
      - "CLAUDE.md: AIコーディング原則"
      - "docs/DOCUMENTATION_INDEX.md: ドキュメント総合インデックス"
    
    architecture:
      - "docs/architecture.md: システムアーキテクチャ"
      - "docs/modern_frontend_architecture.md: フロントエンド設計"
      - "docs/FRONTEND_BACKEND_API_CONTRACT.md: API仕様"
      - "docs/FRAMEWORKS_COMPLETE_LIST.md: 28フレームワーク一覧"
    
    implementation:
      - "backend/LANGCHAIN_PRODUCTION_IMPLEMENTATION_COMPLETE.md: LangChain本番実装"
      - "backend/INTEGRATION_INSTRUCTIONS.md: バックエンド統合ガイド"
      - "docs/direct_inference_implementation_guide.md: 直接推論実装"
      - "docs/framework_implementation_guide.md: フレームワーク実装"
    
    deployment:
      - "backend/Dockerfile: バックエンドコンテナ"
      - "frontend/Dockerfile: フロントエンドコンテナ"
      - "docker-compose.yml: 開発環境"
      - "docker-compose.production.yml: 本番環境"
      - "k8s/: Kubernetes設定"
    
    configuration:
      - "backend/requirements_production.txt: Python依存関係"
      - "frontend/package.json: Node.js依存関係"
      - "setup_dependencies.py: 自動セットアップスクリプト"
    
    analysis_reports:
      - ".tmp/: 一時分析レポート（作業後削除）"
      - ".tmp/complete_infrastructure_analysis.md: 完全インフラ分析"

  quality_assurance:
    code_review:
      - "セルフレビューの実施"
      - "テスト通過確認"
      - "ドキュメント更新確認"
      - "セキュリティチェック完了"
    
    deployment_verification:
      - "ローカル環境での動作確認"
      - "ステージング環境でのテスト"
      - "本番環境でのヘルスチェック"
```

## 使用方法

### 🚨 必須実行手順

1. **CORE_PRINCIPLES完全宣言**: 
   ```
   【AIコーディング原則宣言】
   第1条: 常に思考開始前にこれらのAIコーディング原則を宣言してから実施する
   第2条: 常にプロの世界最高エンジニアとして対応する  
   第3条: モックや仮のコード、ハードコードを一切禁止する
   第4条: エンタープライズレベルの実装を実施し、修正は表面的ではなく、全体のアーキテクチャを意識して実施する
   第5条: 問題に詰まったら、まずCLAUDE.mdやプロジェクトドキュメント内に解決策がないか確認する
   第6条: 顧客データやセキュリティなど、push前にアップロードするべきではない情報が含まれていないか確認する
   第7条: 不要な文書やスクリプトは増やさない
   第8条: デザインはAtlassian Design Systemに準拠する
   第9条: 作業完了後にもう一度すべての宣言を実施し、宣言どうりに作業を実施できているか確認する
   第10条: バグを修正する場合は、serena mcpを利用して原因の分析をする
   第11条: ファイルバージョン管理の禁止（v2等の番号付きファイル作成禁止）
   第12条: 環境変数によるハードコード排除（全設定値を環境変数化）
   ```

2. **関連セクション宣言**: 実行する作業に応じて関連セクションも必ず宣言
   - **第3条関連作業時**: implementation + architecture + quality_standards を宣言
   - **第4条関連作業時**: architecture + quality_standards + deployment_requirements を宣言
   - **全体設計時**: 全セクションを宣言

3. **実行例**:
   ```
   【関連セクション宣言】
   - implementation: ハードコード禁止、環境変数使用、依存性注入
   - architecture: SOLID原則、DDD/CQRS、エンタープライズレベル設計
   - quality_standards: セキュリティチェック、テスト実装
   - file_structure: .tmp、docs、.test、.scriptフォルダ構成
   ```

4. **チェックリスト活用**: mandatory_declaration → execution_checklistの順で確認
5. **品質保証**: quality_standardsに基づいて実装品質を担保
6. **継続的改善**: mindsetに基づいて常に最高品質を追求

## ⚠️ 重要な注意事項

### 🔴 絶対遵守ルール
- **CORE_PRINCIPLES必須宣言**: 作業開始時に第1条〜第10条を**必ず完全に宣言**
- **関連セクション必須宣言**: 実行する作業に関連するセクションを**必ず事前に宣言**
- **宣言なしでの作業開始は厳禁**: 宣言を省略・簡略化してはいけません

### 📋 宣言パターン例
```yaml
# アーキテクチャ変更時の必須宣言
core_principles: [第3条, 第4条]
related_sections: [architecture, implementation, quality_standards]

# セキュリティ実装時の必須宣言  
core_principles: [第1条, 第2条, 第4条, 第6条]
related_sections: [quality_standards.security, architecture, deployment_requirements, security_checklist]

# テスト実装時の必須宣言
core_principles: [第2条, 第3条]
related_sections: [testing_standards, implementation, quality_standards, file_structure.tests]

# バグ修正時の必須宣言
core_principles: [第10条]
related_sections: [bug_tracking, testing_standards, file_structure.temporary_files]
```

### 📁 ファイル配置ルール
- **一時ファイル**: `.tmp/` 以下に配置（作業完了後削除）
- **ドキュメント**: `docs/` 以下に配置（永続的）
- **テスト**: `.test/` 以下に配置
- **スクリプト**: `.script/` 以下に配置
- **ソースコード**: `frontend/`、`backend/` に配置

### 🚫 禁止事項
- この原則は**必須遵守事項**です
- 宣言の省略・簡略化は**一切認められません**
- 例外的な対応が必要な場合は、事前に原則からの逸脱理由を明記してください
- 原則の更新時は、version番号とlast_updatedを必ず更新してください

### ✅ 品質保証
- 宣言なしの作業は**品質保証対象外**となります
- 関連セクション未宣言の作業は**不完全な実装**とみなされます

## プロジェクト固有情報

### llama.cpp設定
- **APIエンドポイント**: http://127.0.0.1:8080
- **利用可能バックエンド**: CUDA、Vulkan、AVX2
- **エンベディングモデル**: Nomic Embed Text v1.5

### 技術スタック
- **フロントエンド**: Next.js 15 + shadcn/ui + TypeScript
- **バックエンド**: Python 3.11 + FastAPI/BentoML
- **エージェント**: CrewAI / AutoGen
- **ベクトルDB**: Chroma (開発) / Pinecone (本番)

---
*Ultrathink. Don't hold back. Give it your all!*

---

# 汎用的なコード規則 (Universal Coding Standards)

## 1. ファイルヘッダー規則

すべてのソースファイルの冒頭に以下の情報を含めること:

```
/**
 * プロジェクト: [プロジェクト名]
 * ファイルパス: [プロジェクトルートからの相対パス]
 *
 * 作成者: [名前]
 * 作成日: [YYYY-MM-DD]
 *
 * 更新履歴:
 * - [YYYY-MM-DD] [名前] [更新内容の簡潔な説明]
 * - [YYYY-MM-DD] [名前] [更新内容の簡潔な説明]
 *
 * 説明:
 * [このファイルの目的と機能の簡潔な説明]
 */
```

## 2. 命名規則

- **クラス/型名**: PascalCase (例: `UserProfile`, `DataProcessor`)
- **変数/関数/メソッド名**: camelCase (例: `getUserData()`, `isValid`)
- **定数**: UPPER_SNAKE_CASE (例: `MAX_RETRY_COUNT`, `API_BASE_URL`)
- **ファイル名**: 内容を表す意味のある名前。コンポーネントはPascalCase、それ以外はkebab-caseまたはsnake_case
- **命名は説明的に**: 短い略語より具体的な名前を使用 (`getData()`より`fetchUserProfiles()`)
- **ブール変数**: `is`, `has`, `can`などの接頭辞を使用 (例: `isActive`, `hasPermission`)

## 3. コードフォーマット

- **インデント**: スペース4つまたは2つで統一（言語により異なる場合あり）
- **行の長さ**: 最大80-120文字（プロジェクトで統一）
- **ブロック**: 開始ブレースは同じ行、終了ブレースは新しい行に配置
- **空白行**: 論理的なコードブロック間に挿入して可読性を向上
- **関数の長さ**: 一つの関数は最大30-50行程度に制限
- **ファイルの長さ**: 一つのファイルは500-1000行程度に制限

## 4. コメント規則

- **コードを説明するコメント**: なぜその実装をしたのか、複雑なロジックの説明に使用
- **TODO形式**: `// TODO(名前): 実装すべき内容 (チケット番号)`
- **FIXME形式**: `// FIXME(名前): 修正すべき問題 (チケット番号)`
- **API/関数ドキュメント**: すべての公開API/関数の前に入力、出力、例外を文書化
- **冗長なコメントを避ける**: コード自体が説明的で明確な場合は不要

## 5. エラー処理

- **例外のキャッチ**: 具体的な例外タイプを指定してキャッチ（`catch(Exception)`は避ける）
- **エラーメッセージ**: 具体的で行動可能なメッセージを提供
- **リカバリーメカニズム**: エラー発生時のフォールバック策を実装
- **エラーログ**: エラー発生箇所、スタックトレース、関連パラメータを記録
- **ユーザー向けエラー**: 技術的詳細を省き、対処方法を提示

## 6. セキュリティガイドライン

- **入力バリデーション**: すべてのユーザー入力を検証
- **認証・認可**: 適切な認証メカニズムと最小権限の原則を適用
- **機密情報**: シークレットキー等はハードコードせず環境変数または安全なストレージを使用
- **SQL/NoSQL注入対策**: パラメータ化クエリを使用
- **クロスサイトスクリプティング(XSS)対策**: 出力エスケープを徹底
- **CSRF対策**: トークンベースの保護を実装

## 7. テスト規則

- **ユニットテスト**: すべての公開関数/メソッドに対して作成
- **テストカバレッジ**: コードカバレッジ80%以上を目標
- **テスト命名**: `test_[テスト対象の機能]_[テスト条件]_[期待される結果]`
- **テストの独立性**: 各テストは他のテストに依存しないこと
- **モック/スタブ**: 外部依存は適切にモック化
- **境界値テスト**: エッジケースを含む入力範囲を網羅

## 8. コード構造と組織

- **関心の分離**: 異なる機能は異なるモジュール/クラスに分離
- **単一責任の原則**: 各クラス/関数は単一の責任のみを持つ
- **依存性注入**: ハードコードされた依存関係を避け、外部から注入
- **インターフェース**: 実装より抽象インターフェースに依存
- **ファイル/フォルダ構造**: 論理的な階層構造を維持（機能/レイヤー別など）

## 9. コードレビュー基準

- **コミットサイズ**: 1プルリクエストあたり300-500行以下が推奨
- **レビューポイント**: セキュリティ、パフォーマンス、可読性、テスト、仕様適合性
- **自己レビュー**: プルリクエスト提出前に自己レビューを実施
- **指摘への対応**: すべてのレビューコメントに対応または議論

## 10. バージョン管理プラクティス

- **コミットメッセージ**: `[type]: [簡潔な説明] (関連チケット番号)`
  - typeの例: feat, fix, docs, style, refactor, test, chore
- **ブランチ戦略**: GitFlowまたはGitHub Flowなどの標準的な戦略を採用
- **リリースタグ**: セマンティックバージョニング(major.minor.patch)に従う

## 11. 依存関係管理

- **バージョン固定**: すべての依存関係のバージョンを明示的に固定
- **定期的な更新**: セキュリティ更新とパッチを定期的に適用
- **最小限の依存関係**: 必要最小限の外部ライブラリのみを使用

## 12. AI実装固有の規則

- **AI呼び出し分離**: AIモデル呼び出しは専用サービス層に分離
- **プロンプト管理**: プロンプトテンプレートは定数または設定ファイルで管理
- **応答検証**: AIからの応答は必ず検証し、予期せぬ出力に対処
- **フォールバック**: AI機能が失敗した場合の代替パスを実装
- **ユーザーフィードバック**: AI応答の品質向上のためのフィードバックメカニズムを実装

## 13. パフォーマンス最適化

- **早期最適化を避ける**: プロファイリングに基づいて最適化を実施
- **リソース管理**: 接続、ファイルハンドル等のリソースは適切に解放
- **遅延読み込み**: 必要になるまでリソースを読み込まない
- **キャッシング**: 頻繁にアクセスされるデータはキャッシュを検討

## 14. 国際化と地域化

- **ハードコードされた文字列を避ける**: 表示テキストは翻訳ファイルに分離
- **日付/時刻/数値のフォーマット**: 地域設定に依存しないよう注意
- **文化的配慮**: 文化固有の参照やメタファーを避ける

## 15. アクセシビリティ

- **セマンティックHTML**: 適切なHTML要素とARIA属性を使用（Webアプリ）
- **キーボードナビゲーション**: すべての機能がキーボードでアクセス可能
- **スクリーンリーダー対応**: 代替テキスト、適切なラベルを提供
- **コントラスト**: 十分な色コントラストを確保

## 16. ドキュメンテーション

- **コード内ドキュメント**: すべての公開API/クラスに説明を付与
- **README**: 各リポジトリには適切なREADMEを含め、設定・実行方法を説明
- **アーキテクチャ図**: 複雑なシステムには構成図を提供
- **更新の同期**: コード変更時にドキュメントも更新
