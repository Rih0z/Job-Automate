# Job-Automate — Claude Code リファレンス

このリポジトリはAI活用業務自動化のためのプロンプトライブラリです。
Claude Code でプロンプトを開発・改善するときのガイドです。

プロンプトは成果物の種類ではなく**業務ワークフロー単位**で `workflows/<name>/` に束ねる（ハーネスの考え方は [workflows/README.md](workflows/README.md)）。Claude Code が自動検出する実行可能な Skills/Commands はリポジトリ直下 `.claude/` に置く。

**別プロジェクトのセットアップに使いたい場合 (2026-09-01)**: このリポジトリを clone した状態で Claude Code を起動し、「このリポジトリを使って `<対象ディレクトリ>` をセットアップして」「ここのやり方を `<対象>` にも入れて」等、**目的が伝われば表現は問わない**旨をこの CLAUDE.md 自体が常時 context にロードされることで保証する（clone しただけで自動実行はされない — Claude Code は明示的な指示なしにファイルを実行しない設計のため、開始の一言だけは必要）。詳細手順は下記「他プロジェクトのセットアップ依頼への対応」節、要点は [README.md](README.md) 冒頭「クイックスタート: 別プロジェクトへ移植する」にも掲載。

---

## アップロードポリシー（公開リポジトリ）

このリポジトリは公開 GitHub リポジトリである。**汎用的に再利用できるプロンプト・スキルのみ**をアップロードし、**特定の企業名・製品名・顧客名・社内プロジェクト名など、特定の企業やプロジェクトに紐づく情報を含むものはアップロードしない**。

- 他プロジェクト由来の設計パターンを本リポジトリに取り込む場合、そのプロジェクト固有の名称・識別子・条文番号・実装詳細を引用せず、一般化した設計原則として書き直す
- 既存ファイルを更新する際も、意図せず固有名詞が混入していないか確認する（コミット前に企業名・製品名で grep する等）
- 該当する社内知見・非公開プロジェクトの情報が必要な場合は、このリポジトリでなく非公開のリポジトリ/ドキュメントで管理する

---

## 応答ルール

作業完了を報告する際は、編集・作成した全ファイルの完全パスを応答に明記する。

バグ修正時: エラーメッセージが修正箇所を明確に示している単純な修正はそのまま直接修正する。依存関係や他ファイルとの整合確認が必要な修正は、着手前にその旨を明示し、計画とレビューが必要であることを示す。

`/compact` 実行時は必ず以下を残す: 編集・作成した全ファイルの完全パス、対象の workflow/skill 名、実行したテスト・検証コマンドと結果。

---

## レビュースキル一覧

### プロジェクトスキル（このリポジトリをクローンすれば誰でも使える）

> `.claude/commands/` に置かれており、このリポジトリを Claude Code で開けば誰でも使える。
> git で共有されるため、チーム全員が同じスキルを使える。

| コマンド | 用途 | 評価軸 |
|---------|------|--------|
| `/review-implementation` | **実装コードの総合レビュー** | テスト品質・処理の正確性・マネタイズ整合性・ペルソナ適合・UX（5軸・100点満点） |
| `/review-changes` | **変更差分のテスト・実装レビュー（エージェント分離）** | 実装正確性・テストカバレッジ・テスト品質/戦略・追跡可能性（4軸・100点満点） |
| `/review-skill` | **Skills品質レビュー** | 構造・トリガー設計・命令品質・出力設計・実用性（5軸・100点満点） |

### 自動発動するSkills（`.claude/skills/`）

このリポジトリの `workflows/` 配下のプロンプトは全て `.claude/skills/<name>/SKILL.md` として skill 化されている。このリポジトリを Claude Code で開けば、該当する話題を話した時に自動発動するか、`/<name>` で直接呼び出せる（一覧は `.claude/skills/` を `ls` するか `/skills` コマンドで確認。個別の説明・トリガー文言は各 SKILL.md の frontmatter `description` に集約されており、本表では重複記載しない）。

| ドメイン | 例 |
|---|---|
| 汎用ガバナンス | `agent-harness-bootstrap`（CLAUDE.md/rules/hooks 一式生成）・`review-oss-contribution`・`skills-audit`・`skill-authoring-guide`・`stop-ai-slop-jp`（[iKora128/stop-ai-slop-jp](https://github.com/iKora128/stop-ai-slop-jp) 着想・MIT・vendoring）・`review-gate`（工程別レビューゲート・観点はcriteria JSONで定義し育てる）・`single-session-tdd`（単一セッションTDD+独立レビュー）・`repo-hygiene-patrol`（ファイル構造衛生パトロール、2026-08-31 追加）・`blind-eval-harness`（複数サンプル盲検一括評価、2026-09-01 追加）・`issue-lifecycle-tracking`（ファイルベース状態遷移によるIssue追跡・数値目標の単一SoT化・N回連続FAILのIssue起票エスカレーション、2026-09-03 追加） |
| business-planning | `business-idea` / `business-proposal` / `generic-proposal` / `it-proposal` / `specification` / `ai-automation` とそれぞれの `review-*`・`multi-tenant-template-injector`（複数クライアント向けテンプレートのテナント分離、2026-09-01 追加） |
| content-creation | `creative-text-art` / `slides-pro` / `review-blog` / `review-slides` |
| ops-management | `year-end-adjustment-csv` / `server-automation` / `server-init` / `server-windows-standard` / `review-ops` |
| research-intelligence | `craft-beer-news-research` / `it-tech-news-research` / `general-news-research` / `investment-portfolio-analysis` / `seo-keyword-article-planner` / `blog-seo-growth-planner` / `research-deliverable-review` / `source-verification-scan`（非公開情報・捏造導線スキャン、2026-09-01 追加） / `staged-investigation-workflow`（ゲート付き段階的調査、2026-09-01 追加） |
| software-development (design/mcp/その他) | `ui-design-guidelines` / `ibm-carbon-design-system` / `avoid-ai-generated-design-look` / `customer-persona-design` / `review-persona-analysis` / `playwright-mcp-e2e-testing` / `mcp-server-setup` / `model-cost-optimization-routing` / `three-agent-tdd-workflow`（3ターミナル分離型。単一セッション版は `single-session-tdd`） |

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
- `workflows/software-development/review-implementation.md` — `/review-implementation` の詳細基準
- `workflows/software-development/review-changes.md` — `/review-changes` の詳細基準

**エージェント分離アーキテクチャ:** `agents.md` を参照

---

### 手動で使うレビュープロンプト（Claude Code 外・貼り付けて使う場合のフォールバック）

> 以下は全て `.claude/skills/` 配下に対応する skill があるため、Claude Code 環境では上表の skill を使う方が推奨（自動発動 + エージェント分離が組込済み）。Claude.ai 等 Claude Code 以外の環境で使う場合のみ、元プロンプトを直接貼り付ける。

| プロンプトファイル | 用途 | 評価軸 |
|----------------|------|--------|
| `workflows/software-development/review-implementation.md` | 実装レビューの詳細基準（`/review-implementation` の参照元） | テスト・正確性・マネタイズ・ペルソナ・UX |
| `workflows/software-development/review-changes.md` | 変更レビューの詳細基準（`/review-changes` の参照元） | 実装正確性・テストカバレッジ・テスト品質/戦略・追跡可能性 |
| `workflows/software-development/review-skill.md` | Skills品質レビューの詳細基準（`/review-skill` の参照元） | 構造・トリガー設計・命令品質・出力設計・実用性 |
| `workflows/software-development/skills-building-guide.md` | Anthropic公式Skills作成マニュアル（`/review-skill` の評価根拠） | — |
| `workflows/business-planning/review-business-idea.md` | ビジネスアイデアのレビュー | 独自性・競合克服戦略・市場性・実現可能性・ペルソナ明確性・エンゲージメント/リテンション設計・展開計画（6軸・100点満点） |
| `workflows/business-planning/review-proposal.md` | 提案書・企画書のレビュー | 構成・市場分析/競合克服戦略・ペルソナ適合性・根拠・エンゲージメント/リテンション設計・説得力（6軸・100点満点） |
| `workflows/business-planning/review-specification.md` | 技術仕様書のレビュー | 要件網羅性・アーキテクチャ・API/データ設計・テスト戦略・実装/運用計画（5軸・100点満点） |
| `workflows/research-intelligence/review-research.md` | リサーチ・ニュース収集・SEO分析のレビュー | 正確性・網羅性・分析深度・構成・実用性（5軸・100点満点） |
| `workflows/business-planning/ideas/review-ai-automation.md` | AI自動化ビジネスモデルのレビュー | 実現可能性・収益性・自動化・競合モート・エンゲージメント・リスク（6軸・100点満点） |
| `workflows/software-development/design/review-persona.md` | ペルソナ分析のレビュー | 具体性・課題深掘り・デザイン整合性・セグメント分類・検証可能性（5軸・100点満点） |
| `workflows/ops-management/review-ops.md` | 運用スクリプト・サーバー設定のレビュー | セキュリティ・冪等性・エラーハンドリング・運用性・パフォーマンス（5軸・100点満点） |
| `workflows/content-creation/review-blog.md` | ブログ記事（note / Qiita / Zenn / Medium / 企業ブログ等）のレビュー | わかりやすさ・独自性・有益性・事実正確性・事実所感分離・冒頭サマリ・冗長性一貫性・読みやすさ文体・コンプライアンス・第三者配慮・技術評価妥当性（11軸・110点満点／100点換算で判定） |
| `workflows/software-development/three-agent/reviewer.md` | TDDコードレビュー（three-agentシステム専用） | TDD証跡・カバレッジ・実装整合性・ドキュメント |

**手動での使い方:**
```
（Claude Code または Claude.ai で）
workflows/software-development/review-implementation.md の内容 + 対象コードを貼り付けて「レビューしてください」と依頼
```

---

## `/review-implementation` を使う前に準備しておくと精度が上がるもの

| 準備 | ファイル例 | なければ |
|------|-----------|---------|
| ペルソナ定義 | `workflows/software-development/design/persona.md` | 推定ユーザーを仮定して評価（スコアに注記あり） |
| 収益モデル | README に記載 | マネタイズ観点をN/Aとして除外し80点満点に換算 |
| テスト戦略 | `jest.config.*` 等 | テストファイルを探して判断 |
| デザインガイドライン | `workflows/software-development/design/design-guidelines.md` | 一般的なUXベストプラクティスで評価 |

---

## 新しいワークフロー・スキルを追加するルール

**追加前チェック（共通）**: 既存の `workflows/` 一覧・`.claude/commands/` 一覧を検索し、目的が重複する既存プロンプト/スキルがないか確認する（重複なら新設せず既存を拡張する）。作成後は別エージェント（`/review-skill` 等）によるレビューを最低 1 回受け、指摘が収束してからマージする。

### 業務ワークフローとして追加（プロンプトの本体）

1. `workflows/<workflow-name>/` を作成する
2. 対応する作成プロンプト（`<対象>.md`）とレビュープロンプト（`review-<対象>.md`）をペアで管理する
3. `workflows/<workflow-name>/README.md` に目的・使用順序・関連skills/commandsを書く
4. `workflows/README.md` の一覧表と `README.md` のテーブルに追記する（この step の追記漏れは `.claude/skills/workflow-coverage-and-structure/SKILL.md` で機械検査できる、2026-09-02 追加）

### Claude Code プロジェクトスキルとして追加（推奨 — git 共有される）

1. `.claude/commands/[コマンド名].md` を作成する
2. コマンドを自己完結にする（他ワークフローのパスをハードコードしない）
3. このファイル（`CLAUDE.md`）のプロジェクトスキルテーブルに追記する
4. 詳細な評価基準は該当ワークフローの `review-[対象].md` に分離して記述する
5. エージェント分離が必要な場合は `agents.md` のエージェント一覧にも追記する
6. 他プロジェクトでも使いたい場合は `~/.claude/commands/` にもコピーする

---

## 他プロジェクトのセットアップ依頼への対応 — 完全列挙 + 由来別選択ルール (2026-09-01 制定・2026-09-04 改訂)

**発火条件 (2026-09-01 拡張)**: 「このリポジトリを使って `<対象>` をセットアップして」のような精密な言い回しに限定しない。ただし**必須条件は「このリポジトリ以外の別ディレクトリ/別リポジトリが対象と明確に読み取れること」**（対象パスの明示、「別プロジェクト」「他のリポジトリ」等の明示、のいずれか）。この条件を満たす依頼は表現を問わず本節を適用する: 「ここの仕組みを別プロジェクトにも入れて」「このリポジトリの CLAUDE.md/skills/rules を〈他リポジトリ〉に移植して」「clone した内容を〈対象パス〉で使えるようにして」等。**対象が明示されない「セットアップして」「使えるようにして」は本節を発火させない**（このリポジトリ自身の中で作業したいだけの依頼と区別できないため。この場合は通常の応答＝リポジトリ内での作業支援として扱う）。対象は明示されたが依頼が曖昧な場合のみ「対象ディレクトリはどこか」を確認する（適用するかどうか自体は聞き返さない）。

このリポジトリには **Anthropic 公式ベストプラクティス由来の要素**と**著者の運用嗜好**（issue フォルダ管理・handoff 規約・並走 4 軸 recheck・SessionStart hook 等）が同居している。別プロジェクトへ移す時に両者を混ぜたまま持ち込まないため、要素ごとの由来は `.claude/skills/agent-harness-bootstrap/provenance.json` を唯一の SoT として管理し（各 SKILL.md の frontmatter `metadata.provenance` は台帳の写し）、以下の手順で「何を取り込み、何を取り込まないか」を**ユーザーが決める**:

1. `provenance.json` の全要素（本 CLAUDE.md の各セクションも `claude-md-*` 要素として登録済み）を列挙した**移植チェックリスト**を最初に作る（列挙の完全性は維持する。黙って省略しない）。チェックリストの実体は手順 4 で書く `harness-selection.json`（全要素分の entry）そのものであり、別ファイルは作らない。
2. 各要素を由来ラベルで分けて提示する: `official`（公式由来・デフォルト採用）/ `official-derived`（公式原則の具体化・推奨、外せる）/ `author-preference` `third-party` `domain-prompt`（著者の嗜好等・**デフォルト非採用**、ユーザーが選んだものだけ採用）/ `repo-specific`（本リポジトリ固有・移植不可）。手順の本体は `.claude/skills/agent-harness-bootstrap/selection-flow.md`。
3. ユーザーに選択を取る（対話: `AskUserQuestion` / 非対話: `default_selection` のみ採用し、その旨を報告冒頭に明記。ユーザーの好みを推測で補わない）。`depends_on` を欠く選択は成立しないと示して選び直させ、`soft_depends_on` の欠落は警告のみで台帳の `note` に従う縮退形を採用する。
4. 決定を対象の `.claude/harness-selection.json` に全要素分（非選択も `selected: false` で）記録し、以降の生成（`agent-harness-bootstrap` Step 1〜8）・skills コピー・criteria JSON の対象固有調整は選択済み要素だけを対象にする。**非選択の著者嗜好要素を「念のため」持ち込まない**。
5. 移植完了後、**別エージェント**に突合レビューをさせる。渡すのは対象パス 3 点（移植元 `provenance.json`・対象 `harness-selection.json`・対象ルート）と観点定義 `.claude/skills/agent-harness-bootstrap/criteria/porting-reconciliation.json` のパスのみ。(a) 選択済み要素の抜けゼロ (b) 非選択要素の混入ゼロ (c) 選択記録の完全性（`provenance-check.sh --selection` で機械確認）を確認してから完了報告する。

「数値目標の単一 SoT 化」条文（`test-verify.md`）について: 2026-09-01 制定時は N/A 判定不可の必須項目としていたが、2026-09-04 に `author-preference`（default `recommend` = 事前チェック済みだがユーザーが外せる）へ再分類した。公式根拠のない著者の運用判断であり、「採用の決定はユーザーが行う」という本節の趣旨と矛盾するため。採用時は機械検査として `repo-hygiene-patrol` の「数値目標の整合性ドリフト」check を持つ `skill-repo-hygiene-patrol` の選択を勧める（未選択なら `test-verify.md` の条文のみ。台帳 id: `numeric-target-single-sot`、`soft_depends_on`）。

背景: セットアップ時に一部の観点だけ移植され、後から「あの観点は取り込めているか」という確認・追加依頼が繰り返される失敗パターンへの対策として**列挙の完全性**は維持する。一方で、公式由来と著者嗜好が区別されないまま全部持ち込まれ、移植先に不要な運用が混入する失敗パターンへの対策として、**採用の決定**はユーザーに委ねる。完全性は依頼者の記憶でなくチェックリスト・選択記録・突合レビューで担保する。

## 根拠明記の推奨 (2026-08-31)

research/proposal/report 系の成果物が外部情報・過去データに基づく事実主張をする場合、根拠となる資料の完全パス (ローカルファイル) または URL (外部情報源) を近接記載することを推奨する。適用対象は成果物テンプレート出力および `review-*` skill のレビュー結果 (既存の `citation_required` は変更しない)。事実主張でない意見・提案・戦略考察には適用しない。

本 repo は自動 CI 機械検証を持たないため、本項目は **advisory な推奨** であり必須ゲートではない (2026-08-31 時点。将来 review-* skill への組み込みが進めば昇格を検討)。

## プロジェクト構成

トップレベルは `CLAUDE.md` / `README.md` / `agents.md` / `.claude/`（commands・skills）/ `workflows/`（業務ワークフロー単位のハーネス）/ `archive/`（旧プロンプト）。ワークフローごとの内訳・各ファイルの所在は [workflows/README.md](workflows/README.md) と [README.md](README.md) を参照（このファイルでは重複記載しない）。

**「テストカバレッジは?」「プロジェクト構成は?」に相当する質問への回答 (2026-09-02 追加)**: `.claude/skills/workflow-coverage-and-structure/SKILL.md` で即答する（`bash .claude/skills/workflow-coverage-and-structure/scripts/workflow-doc-coverage-check.sh --report`）。上記「新しいワークフロー・スキルを追加するルール」step 4（README 追記）の機械検査として使う。
