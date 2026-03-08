# Job-Automate — Claude Code リファレンス

このリポジトリはAI活用業務自動化のためのプロンプトライブラリです。
Claude Code でプロンプトを開発・改善するときのガイドです。

---

## レビュースキル一覧

### グローバルスキル（どのプロジェクトでも使える）

> `~/.claude/commands/` に置かれており、Claude Code を開いたどのプロジェクトでも `/コマンド名` で呼び出せる。

| コマンド | 用途 | 評価軸 |
|---------|------|--------|
| `/review-implementation` | **実装コードの総合レビュー** | テスト品質・処理の正確性・マネタイズ整合性・ペルソナ適合・UX（5軸・100点満点） |

**使い方:**
```
（開発中のプロジェクトで）
/review-implementation
```
→ プロジェクトのコード・テスト・デザイン定義・ペルソナ情報を自動で収集して評価する。
→ ペルソナ未定義・収益モデル未定義の場合も自動で補正して評価する。

**詳細な評価基準:** `docs/review-implementation.md` を参照

---

### 手動で使うレビュープロンプト（貼り付けて使う）

> コードではなく、ドキュメント・アイデア・提案書のレビューに使う。

| プロンプトファイル | 用途 | 評価軸 |
|----------------|------|--------|
| `docs/review-implementation.md` | 実装レビューの詳細基準（`/review-implementation` の参照元） | テスト・正確性・マネタイズ・ペルソナ・UX |
| `docs/review-business-idea.md` | ビジネスアイデアのレビュー | 独自性・市場性・実現可能性・ペルソナ明確性・展開計画 |
| `docs/review-proposal.md` | 提案書・企画書のレビュー | 構成・市場分析・ペルソナ適合性・根拠・説得力 |
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
├─ 実装コード（テスト・ロジック・UI）
│   └─ /review-implementation（グローバルスキル）
│        └─ 詳細基準は docs/review-implementation.md
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

### グローバルスキルとして追加

1. `~/.claude/commands/[コマンド名].md` を作成する
2. コマンドを自己完結にする（他プロジェクトのパスをハードコードしない）
3. このファイル（`CLAUDE.md`）のグローバルスキルテーブルに追記する
4. 詳細な評価基準は `docs/review-[対象].md` に分離して記述する

### 手動プロンプトとして追加

1. `docs/review-[対象].md` にプロンプトを作成する
2. 対応する作成プロンプト（`docs/[対象].md`）とペアで管理する
3. このファイル（`CLAUDE.md`）と `README.md` のテーブルに追記する

---

## プロジェクト構成

```
Job-Automate/
├── CLAUDE.md              ← このファイル（レビュースキルのマニュアル）
├── README.md              ← ユーザー向けプロンプト一覧
├── docs/                  ← 新規事業・提案書・レビュー基準ドキュメント
│   ├── review-implementation.md  ← /review-implementation の詳細基準
│   ├── review-business-idea.md
│   └── review-proposal.md
├── business/              ← ビジネスリサーチ系プロンプト
├── content/               ← プレゼン資料・スライド系プロンプト
├── dev/                   ← 開発プロンプト集
│   ├── design/            ← デザインシステム・ペルソナ分析
│   ├── rules/             ← コーディング規約
│   ├── mcp/               ← MCPツール設定
│   └── three-agent/       ← 3エージェント開発システム
└── ops/                   ← サーバー運用・HR系プロンプト

~/.claude/commands/        ← グローバルスキル（どのプロジェクトでも使える）
└── review-implementation.md  ← /review-implementation コマンド本体
```
