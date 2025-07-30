README.mdを読み込んで。このアプリを作成するにあたり最適な形になるよう宣言を追加し、CLAUDE.mdとして保存して。 ファイル構造はこのファイルに追記して。
# Claude.md - AIコーディング原則

```yaml
ai_coding_principles:
  meta:
    version: "1.0"
    last_updated: "2025-07-29"
    description: "Claude AIコーディング実行原則"
    
  core_principles:
    mandatory_declaration: "全てのコーディング作業開始時に必ずcore_principlesを完全に宣言すること"
    第1条: 
      rule: "常に思考開始前にClaude.mdの第1条から第10条のAIコーディング原則を全て宣言してから実施する"
      related_sections: ["execution_checklist", "mindset"]
    第2条: 
      rule: "常にプロの世界最高エンジニアとして対応する"
      related_sections: ["mindset", "quality_standards"]
    第3条: 
      rule: "モックや仮のコード、ハードコードを一切禁止する。コーディング前にread Serena's initial instructions"
      related_sections: ["implementation", "architecture", "quality_standards",https://github.com/oraios/serena]
    第4条: 
      rule: "エンタープライズレベルの実装を実施し、修正は表面的ではなく、全体のアーキテクチャを意識して実施する"
      related_sections: ["architecture", "quality_standards", "deployment_requirements"]
    第5条: 
      rule: "問題に詰まったら、まずCLAUDE.mdやプロジェクトドキュメント内に解決策がないか確認する"
    第6条: 
      rule: "push前にアップロードするべきではない情報が含まれていないか確認する。"
    第７条: 
      rule: "不要な文書やスクリプトは増やさない。スクリプト作成時は常に既存のスクリプトで使用可能なものがないか以下のセクションを確認する、スクリプトを作成したらscriptsフォルダに、ドキュメントはドキュメントフォルダに格納する。一時スクリプトや文書はそれぞれのフォルダのtmpフォルダに保存し、使用後に必ず削除する。"
      related_sections: ["how_to_use_scripts"]
    第8条: 
      rule: "デザインはhttps://atlassian.design/components を読み込み、これに準拠する。"
      related_sections: https://atlassian.design/components
    第9条: 
      rule: "作業完了後にもう一度すべての宣言を実施し、宣言どうりに作業を実施できているか確認する。"
    第10条: 
      rule: "バグを修正する場合は、まず原因の分析をしユーザーに原因について報告する。ユーザーが確認したら修正方法を提案する。修正方法が妥当か十分にレビューし、他の宣言に矛盾していないか確認した上でユーザーの確認をとり修正を実施する。"

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
    environment:
      - "必ずURLが固定の本番環境にデプロイするようにする"
      - "フロントエンドとバックエンドの通信が必ず成功するようにデプロイ先のURLは指定する"
      - "CI/CDパイプラインの構築"
    
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

  file_structure:
    logs: ".claude/logs/"
    documents: "documents/"
    source: "src/"
    tests: "tests/"
    config: "config/"
    deployment: "deploy/"

  execution_checklist:
    mandatory_declaration:
      - "[ ] **CORE_PRINCIPLES宣言**: 第1条〜第4条を完全に宣言"
      - "[ ] **関連セクション宣言**: 実行する作業に関連するセクションを宣言"
      - "[ ] 例：アーキテクチャ変更時は第3条・第4条 + architecture + quality_standards + implementation を宣言"
    
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

## 使用方法

### 🚨 必須実行手順

1. **CORE_PRINCIPLES完全宣言**: 
   ```
   【AIコーディング原則宣言】
   第1条: 常に思考開始前にこれらのAIコーディング原則を宣言してから実施する
   第2条: 常にプロの世界最高エンジニアとして対応する  
   第3条: モックや仮のコード、ハードコードを一切禁止する
   第4条: エンタープライズレベルの実装を実施し、修正は表面的ではなく、全体のアーキテクチャを意識して実施する
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
   ```

4. **チェックリスト活用**: mandatory_declaration → execution_checklistの順で確認
5. **品質保証**: quality_standardsに基づいて実装品質を担保
6. **継続的改善**: mindsetに基づいて常に最高品質を追求

## ⚠️ 重要な注意事項

### 🔴 絶対遵守ルール
- **CORE_PRINCIPLES必須宣言**: 作業開始時に第1条〜第4条を**必ず完全に宣言**
- **関連セクション必須宣言**: 実行する作業に関連するセクションを**必ず事前に宣言**
- **宣言なしでの作業開始は厳禁**: 宣言を省略・簡略化してはいけません

### 📋 宣言パターン例
```yaml
# アーキテクチャ変更時の必須宣言
core_principles: [第3条, 第4条]
related_sections: [architecture, implementation, quality_standards]

# セキュリティ実装時の必須宣言  
core_principles: [第1条, 第2条, 第4条]
related_sections: [quality_standards.security, architecture, deployment_requirements]

# テスト実装時の必須宣言
core_principles: [第2条, 第3条]
related_sections: [testing_standards, implementation, quality_standards]
```

### 🚫 禁止事項
- この原則は**必須遵守事項**です
- 宣言の省略・簡略化は**一切認められません**
- 例外的な対応が必要な場合は、事前に原則からの逸脱理由を明記してください
- 原則の更新時は、version番号とlast_updatedを必ず更新してください

### ✅ 品質保証
- 宣言なしの作業は**品質保証対象外**となります
- 関連セクション未宣言の作業は**不完全な実装**とみなされます
