# Job-Automate — Claude Code リファレンス

このリポジトリはAI活用業務自動化のためのプロンプトライブラリです。
Claude Code でプロンプトを開発・改善するときのガイドです。

---

## レビュースキル一覧

### プロジェクトスキル（このリポジトリをクローンすれば誰でも使える）

> `.claude/commands/` に置かれており、このリポジトリを Claude Code で開けば誰でも使える。
> git で共有されるため、チーム全員が同じスキルを使える。

| コマンド | 用途 | 評価軸 |
|---------|------|--------|
| `/review-implementation` | **実装コードの総合レビュー** | テスト品質・処理の正確性・マネタイズ整合性・ペルソナ適合・UX（5軸・100点満点） |
| `/review-changes` | **変更差分のテスト・実装レビュー（エージェント分離）** | 実装正確性・テストカバレッジ・テスト品質/戦略・追跡可能性（4軸・100点満点） |

### グローバルスキル（どのプロジェクトでも使える・任意セットアップ）

> `~/.claude/commands/` にコピーすると、他のプロジェクトでも使える。
> `.claude/commands/` と同じ内容。個人環境に展開したい場合に使う。

```bash
# このリポジトリのスキルを個人のグローバルスキルにコピーする
mkdir -p ~/.claude/commands
cp .claude/commands/*.md ~/.claude/commands/
```

**使い方:**
```
（開発中のプロジェクトで）
/review-implementation          ← プロジェクト全体の総合レビュー
/review-changes                 ← 直近の変更差分をテスト・実装観点でレビュー
/review-changes path/to/file    ← 特定ファイルの変更をレビュー
```
→ `/review-implementation`: プロジェクトのコード・テスト・デザイン定義・ペルソナ情報を自動で収集して評価する。
→ `/review-changes`: **別エージェントを自動起動**し、テスト基盤を自動検出して変更に対する実装正確性・テスト網羅性を評価する。実装コンテキストを遮断して客観性を確保する。

**詳細な評価基準:**
- `docs/review-implementation.md` — `/review-implementation` の詳細基準
- `docs/review-changes.md` — `/review-changes` の詳細基準

**エージェント分離アーキテクチャ:** `agents.md` を参照

---

### 手動で使うレビュープロンプト（貼り付けて使う）

> コードではなく、ドキュメント・アイデア・提案書のレビューに使う。

| プロンプトファイル | 用途 | 評価軸 |
|----------------|------|--------|
| `docs/review-implementation.md` | 実装レビューの詳細基準（`/review-implementation` の参照元） | テスト・正確性・マネタイズ・ペルソナ・UX |
| `docs/review-changes.md` | 変更レビューの詳細基準（`/review-changes` の参照元） | 実装正確性・テストカバレッジ・テスト品質/戦略・追跡可能性 |
| `docs/review-business-idea.md` | ビジネスアイデアのレビュー | 独自性・競合克服戦略・市場性・実現可能性・ペルソナ明確性・エンゲージメント/リテンション設計・展開計画（6軸・100点満点） |
| `docs/review-proposal.md` | 提案書・企画書のレビュー | 構成・市場分析/競合克服戦略・ペルソナ適合性・根拠・エンゲージメント/リテンション設計・説得力（6軸・100点満点） |
| `dev/three-agent/reviewer.md` | TDDコードレビュー（three-agentシステム専用） | TDD証跡・カバレッジ・実装整合性・ドキュメント |

**手動での使い方:**
```
（Claude Code または Claude.ai で）
docs/review-implementation.md の内容 + 対象コードを貼り付けて「レビューしてください」と依頼
```

---

## レビュースキルの選び方

```
何をレビューしたいか？
│
├─ 実装コード（プロジェクト全体）
│   └─ /review-implementation（グローバルスキル）
│        └─ 詳細基準は docs/review-implementation.md
│
├─ 最新の変更差分（テスト・実装の正確性）
│   └─ /review-changes（グローバルスキル）
│        └─ 詳細基準は docs/review-changes.md
│
├─ ビジネスアイデア文書
│   └─ docs/review-business-idea.md を貼り付けて依頼
│
├─ 提案書・企画書
│   └─ docs/review-proposal.md を貼り付けて依頼
│
└─ Three-Agentシステムの各イテレーション
    └─ dev/three-agent/reviewer.md（ターミナル3専用）
```

---

## `/review-implementation` を使う前に準備しておくと精度が上がるもの

| 準備 | ファイル例 | なければ |
|------|-----------|---------|
| ペルソナ定義 | `dev/design/persona.md` | 推定ユーザーを仮定して評価（スコアに注記あり） |
| 収益モデル | README に記載 | マネタイズ観点をN/Aとして除外し80点満点に換算 |
| テスト戦略 | `jest.config.*` 等 | テストファイルを探して判断 |
| デザインガイドライン | `dev/design/design-guidelines.md` | 一般的なUXベストプラクティスで評価 |

---

## 新しいスキルを追加するルール

### プロジェクトスキルとして追加（推奨 — git 共有される）

1. `.claude/commands/[コマンド名].md` を作成する
2. コマンドを自己完結にする（他プロジェクトのパスをハードコードしない）
3. このファイル（`CLAUDE.md`）のプロジェクトスキルテーブルに追記する
4. 詳細な評価基準は `docs/review-[対象].md` に分離して記述する
5. エージェント分離が必要な場合は `agents.md` のエージェント一覧にも追記する
6. 他プロジェクトでも使いたい場合は `~/.claude/commands/` にもコピーする

### 手動プロンプトとして追加

1. `docs/review-[対象].md` にプロンプトを作成する
2. 対応する作成プロンプト（`docs/[対象].md`）とペアで管理する
3. このファイル（`CLAUDE.md`）と `README.md` のテーブルに追記する

---

## プロジェクト構成

```
Job-Automate/
├── CLAUDE.md              ← このファイル（レビュースキルのマニュアル）
├── agents.md              ← エージェント分離アーキテクチャ（レビューの客観性確保）
├── README.md              ← ユーザー向けプロンプト一覧
├── docs/                  ← 新規事業・提案書・レビュー基準ドキュメント
│   ├── review-implementation.md  ← /review-implementation の詳細基準
│   ├── review-changes.md         ← /review-changes の詳細基準
│   ├── review-business-idea.md
│   └── review-proposal.md
├── business/              ← ビジネスリサーチ系プロンプト
├── content/               ← プレゼン資料・スライド系プロンプト
├── dev/                   ← 開発プロンプト集
│   ├── design/            ← デザインシステム・ペルソナ分析
│   ├── rules/             ← コーディング規約
│   ├── mcp/               ← MCPツール設定
│   └── three-agent/       ← 3エージェント開発システム
├── .claude/commands/       ← プロジェクトスキル（git共有・クローンすれば誰でも使える）
│   ├── review-implementation.md  ← /review-implementation コマンド本体
│   └── review-changes.md         ← /review-changes コマンド本体
└── ops/                   ← サーバー運用・HR系プロンプト
```
