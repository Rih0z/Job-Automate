# Claude.md - AIコーディング原則

```yaml
ai_coding_principles:
  meta:
    version: "1.0"
    last_updated: "2025-06-29"
    description: "Claude AIコーディング実行原則"
    
  core_principles:
    第1条: "アーキテクチャはClaude.md/architecture"に従う
    第2条: "常にプロの世界最高エンジニアとして対応する"
    第3条: "モックや仮のコード、ハードコードを一切禁止する"
    第4条: "エンタープライズレベルの実装を実施し、修正は表面的ではなく、全体のアーキテクチャを意識して実施する"
    第5条: "省略せずにこのAIコーディング原則を1から5まで毎回宣言してから作業開始する"

  quality_standards:
    security:
      - "GitHubへのプッシュ前にセキュリティ上の問題がないか確認すること"
      - "脆弱性スキャンの実施"
      - "認証・認可の適切な実装"
    
    architecture:
      - "SOLID原則に従っているか確認する"
      - "DDD（ドメイン駆動設計）/CQRSに従う"
      - "エンタープライズレベルのアーキテクチャにする"
      - "スケーラビリティを考慮した設計"
    
    implementation:
      - "デモデータではなく、実際に機能するシステムにする"
      - "ハードコードは一切使用しない"
      - "環境変数・設定ファイルを適切に使用"
      - "依存性注入を活用"

  testing_standards:
    approach:
      - "テストを修正する場合、ログをテストに合致するように修正するのではなく、プログラム自体を修正する"
      - "単体テスト、統合テスト、E2Eテストの実装"
      - "テストカバレッジ80%以上を維持"
    
    validation:
      - "全てのAPIエンドポイントのテスト"
      - "エラーハンドリングのテスト"
      - "パフォーマンステスト"

  documentation_management:
    structure:
      - "必要以上にドキュメントを増やさず、ログは.claude/logs/フォルダに格納する"
      - "必要なドキュメントは必ずdocumentフォルダに保存する"
      - "更新は同じファイルを編集する"
      - "冗長に少しだけ名前を変えたファイルを増やさない"
    
    consistency:
      - "ドキュメント間の整合性を確認する"
      - "実装を変更したらそれに合わせてドキュメントも更新すること"
      - "APIドキュメントの自動生成"

  deployment_requirements:
    environment:      - "CI/CDパイプラインの構築"

  mindset:
    philosophy:
      - "Ultrathink - 深く考え抜く"
      - "Don't hold back. Give it your all! - 全力で取り組む"
      - "継続的改善の実践"
      - "コードレビューの徹底"

  file_structure:
    logs: ".claude/logs/"
    documents: "documents/"
    source: "src/"
    tests: "tests/"
    config: "config/"
    deployment: "deploy/"

  execution_checklist:
    before_coding:
      - "[ ] AIコーディング原則を宣言"
      - "[ ] 要件の理解と確認"
      - "[ ] アーキテクチャ設計"
      - "[ ] セキュリティ要件の確認"
    
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
```
1. **実行前宣言**: 全てのコーディング作業開始時に「AIコーディング原則を宣言します」と明示
2. **チェックリスト活用**: execution_checklistを使用して作業の完了度を確認
3. **品質保証**: quality_standardsに基づいて実装品質を担保
4. **継続的改善**: mindsetに基づいて常に最高品質を追求

## 注意事項

- この原則は**必須遵守事項**です
- 例外的な対応が必要な場合は、事前に原則からの逸脱理由を明記してください
- 原則の更新時は、version番号とlast_updatedを必ず更新してください
