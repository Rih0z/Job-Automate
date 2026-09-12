---
name: three-agent-tdd-workflow
description: "Guides a 3-role (Leader/Executor/Reviewer), TDD-first development workflow run across 3 separate AI sessions/terminals for objectivity: Leader plans a test-first iteration, Executor writes a failing test then minimal implementation, Reviewer scores the result out of 100 and either sends it back for revision or hands off to the Leader for the next iteration. Use when the user asks to 'three-agent開発システムで進めて', '3エージェント体制で開発して', 'リーダー/実行/レビューの3ターミナルで開発を回して', or is starting any new coding project ('このシステムはすべての開発の起点')."
metadata:
  provenance: author-preference
---

# 3エージェント開発システム (TDD強化版) — Skill 概要

## 概要

3つのAIエージェント（進行役・実行者・レビュアー）が、テスト駆動開発（TDD）を前提に協調するための運用方法。厳密なウォーターフォールフェーズ分割（要件定義→基本設計→詳細設計...）は使わず、短いイテレーションを繰り返す。イテレーション内は 設計 → テスト設計 → テスト実装(Red) → 実装 → レビュー の順に固定する（下記「イテレーション内の工程順序」）。**このシステムはすべての開発の起点**として使うことを想定している。

## ロール構成

| エージェント | 役割 | ターミナル | 主なアウトプット |
|-------------|------|-----------|------------------|
| リーダー（進行役） | ゴール設定、テスト方針とタスク分解、次サイクル指示 | ターミナル1 | `---LEADER OUTPUT START---` と `.tmp/leader_instructions/...` |
| 実行エージェント | テスト→実装→リファクタのTDDサイクル実行 | ターミナル2 | `---OUTPUT START---` と `.tmp/execution/...` |
| レビューエージェント | テストと実装の品質評価、改善指示（100点満点） | ターミナル3 | `---REVIEW OUTPUT START---` と `.tmp/review/...` |

**重要**: 3つは必ず別々のAIセッション（別ターミナル）で実行する。同じセッションで複数ロールを担うと客観性が失われる。

## コア原則

1. **テストファースト**: 失敗する自動テストを書くことから全作業を始める
2. **3セッション分離**: 独立したターミナル/モデルで動かし、客観性を担保する
3. **`.tmp`配下への保存**: すべての計画・成果物・レビューを `.tmp/` 以下に保存し、`---CREATED FILES---` で完全パスを列挙する
4. **イテレーション駆動**: イテレーションをまたぐ大フェーズ（要件定義→基本設計→詳細設計…）は固定しない。イテレーション内の順序は「イテレーション内の工程順序」節に従う: 設計 → テスト設計 → テスト実装(Red) → 実装 → レビュー
5. **透明性**: 重要な決定・仮定・リスクは必ず文書化し、次エージェントに引き継ぐ
6. **長期的計画の追跡**: ロードマップの完全パスを `---LONG TERM PLAN---` セクションで常に出力する

## イテレーション内の工程順序

イテレーションは短く回すが、**その中の順序は固定する**: 設計 → テスト設計 → テスト実装(Red) → 実装(Green→Refactor)。前の工程が終わるまで次を始めない。

| 工程 | 担当 | 成果物 | 次へ進む条件 |
|---|---|---|---|
| 設計 | リーダー | ゴール・スコープ・インターフェース | `---EXECUTION INSTRUCTION---` に含まれている |
| テスト設計 | リーダー（不足分は実行が補う） | 検証ケース一覧・テスト名（仕様の文として読める形）・期待値とその導出根拠・E2E/手動確認に回す範囲 | テストコードを書く前に確定している |
| テスト実装(Red) | 実行 | テストコード + 失敗ログ（コマンドと出力） | 実行して失敗を確認済み |
| 実装(Green→Refactor) | 実行 | 最小実装 + リファクタ | 全テストが緑 |

禁止事項:
- Redを確認する前に実装コードを書くこと。後付けテストはTDDとみなさない
- 自分の成果物を自分でレビューして通過扱いにすること（レビューは必ずターミナル3の別セッション）

単一セッションで回す場合は `review-gate` skill（`criteria/*.json`）を使う（設計とテスト設計は design ゲート1回でまとめて審査する）。三役運用では順序の確認はイテレーション末のレビュー（`reviewer.md` のカテゴリ 2・4）に依るため、工程ごとの事前ゲートは無い（強制はレビュアー判定に依る確率的なもの）。

## ループ条件

- **100点未満**: レビュー結果 + 前回成果物 + 実行プロンプトをターミナル2（実行）へ戻し改善
- **100点**: レビュー結果 + リーダープロンプトをターミナル1（リーダー）へ渡し次のイテレーションを計画
- 全ゴール達成後、リーダーの完了出力テンプレートで締める

## 使い方（各ターミナルでの実行手順）

1. **ターミナル1（リーダー）**: ユーザー要望 + `workflows/software-development/three-agent/leader.md` の全文を貼り付け、イテレーション計画と `---EXECUTION INSTRUCTION---` を取得する
2. **ターミナル2（実行）**: リーダー出力の `---EXECUTION INSTRUCTION---` + `workflows/software-development/three-agent/executor.md` の全文を貼り付け、テストファーストで成果物を作成する
3. **ターミナル3（レビュー）**: 実行の `---OUTPUT DOCUMENT---`〜`---OUTPUT METADATA---` + `workflows/software-development/three-agent/reviewer.md` の全文を貼り付け、100点満点でレビューする
4. 点数に応じてステップ2または1に戻る。全ゴール達成でリーダーの完了テンプレートを出力

各ロールの完全な出力テンプレート（`---LEADER OUTPUT START---` 等の区切り記法、`.tmp/` 保存構造、品質基準、旧ウォーターフォール版テンプレート）は、Progressive Disclosure として以下の原文ファイルに委ねる。イテレーション実行時は必ず該当ロールの原文を Read してから、そこに定義された出力テンプレートをそのまま使うこと（要約・省略しない）。

| ロール | 原文（完全版） |
|---|---|
| リーダー | `workflows/software-development/three-agent/leader.md`（555行） |
| 実行 | `workflows/software-development/three-agent/executor.md`（439行） |
| レビュー | `workflows/software-development/three-agent/reviewer.md`（597行） |
| システム全体・FAQ・`.tmp`保存構造の詳細 | `workflows/software-development/three-agent/README.md`（320行） |

## 細部実装への参照

three-agent システムで進めながら、コーディング規約・MCPツールが必要な場合は以下を使う:

| 用途 | 参照先 |
|---|---|
| コーディング規約 | `workflows/software-development/rules/coding-principles.md`（`/review-implementation` `/review-changes` の評価基準としても参照される） |
| Playwright MCP（E2Eテスト） | `playwright-mcp-e2e-testing` Skill |
| Serena MCP / Windows Build Server MCP | `mcp-server-setup` Skill |

## 出典

原文: `workflows/software-development/three-agent/README.md`, `leader.md`, `executor.md`, `reviewer.md`。参考ドキュメント: Anthropic, _Build better software with Claude Code_ (2024) — テストファースト・短いループ・複数エージェント分離の推奨に準拠。
