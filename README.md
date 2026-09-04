# Job-Automate プロンプト集

AIを活用した業務自動化・開発効率化のためのプロンプトライブラリ。

このリポジトリは 2 種類の知見を、由来を分けて持つ:

- **Anthropic 公式ベストプラクティス**（"Write an effective CLAUDE.md" / Skills / hooks）を全て取り入れている。原則は取得日と再取得条件付きの 1 つの構造化データ [anthropic-best-practices.json](.claude/skills/_shared/anthropic-best-practices.json) に保持し、各 skill が判定基準として参照する。該当時は公式ドキュメントの現行版で裏取りして更新する。
- **日々 AI と開発しながら気づいた改善点**（レビューの別エージェント分離、issue フォルダ管理、handoff 規約、並走 recheck、数値目標の単一 SoT 化 等）を還元している。失敗パターンから得た運用ノウハウは、公式由来と混ざらないよう「著者の運用嗜好」として台帳 [provenance.json](.claude/skills/agent-harness-bootstrap/provenance.json) に登録する。

別プロジェクトへは、公式由来をデフォルトで入れ、著者の運用嗜好はあなたが選んだものだけを入れる（下記クイックスタート）。どのプロジェクトでも同じ土台（公式準拠の生成 + 選択記録 + 別エージェントの突合レビュー）で CLAUDE.md を作るので、生成物は同じ基準で揃う。何がどこまで揃うかは「品質の保証範囲」を参照。

### 品質の保証範囲

| 揃うもの | 仕組み |
|---|---|
| 公式基準への準拠 | 生成時に公式ドキュメントを WebFetch し、別エージェントが 36 項目のルーブリックを全 Y になるまで判定する（`agent-harness-bootstrap` Step 7） |
| 構成（何が入り、何が入らないか） | 台帳の各要素が持つ契約（選択時に必ず現れる語句・ファイル・`@import`・`paths:` / 非選択時に現れてはならないもの）を `provenance-check.sh --target` が**決定的に**検査し、別エージェントの突合レビューで「選択済みの抜けゼロ・非選択の混入ゼロ」を must_pass 判定する。両方 PASS するまで `harness-setup-review` が完了を認めず、Stop hook が終了を block する |
| 既存 skills の公式準拠 | setup 前から対象にある skills を `skills-audit` が公式ベストプラクティス基準で監査し tier を報告する |
| 台帳と実体の整合 | `provenance-check.sh` の 11 検査 + 33 件の regression test |

保証しないもの: 構造・語句の契約は決定的だが、条文の中身の良し悪し（ルーブリックの Y/N）は LLM レビュアの判定で、完全な決定性はない。生成後のドリフトは、governance.md や hooks を選んだ場合と再同期時にしか検出されない。プロジェクトごとに選ぶ著者嗜好の集合は異なるので、揃うのは「公式準拠の土台 + 記録された差分」であり、全プロジェクトが同一の CLAUDE.md になるわけではない。

---

## クイックスタート: 別プロジェクトへ移植する (2026-09-01 制定・2026-09-04 改訂)

このリポジトリの `CLAUDE.md`・`.claude/skills/`・`.claude/commands/` の仕組み（レビュー基準・エージェント分離・harness設計）を、別のプロジェクトにも使いたい場合。**Anthropic 公式由来の要素はデフォルトで入り、著者の運用嗜好（issue フォルダ管理・handoff 規約・並走 recheck 等）はあなたが選んだものだけ入る**。

### 配置と gitignore（先に決める）

移植元（このリポジトリ）の clone は、対象プロジェクト直下の **`.setup-automate/`** に置き、**gitignore する**。生成物と選択記録は対象側にコミットする:

```
<対象プロジェクト>/
├── .setup-automate/                 # このリポジトリの clone。gitignore する。再同期は中で git pull
├── .claude/
│   ├── harness-selection.json       # コミットする（何を取り込み何を外したかの記録 = 移植チェックリスト）
│   ├── rules/  skills/  commands/   # 選択した要素だけが入る
│   └── settings.json                # hooks を選んだ時のみ
├── CLAUDE.md                        # 生成物（コミットする）
├── .tmp/                            # handoff 規約を選んだ時のみ生成。gitignore する
└── workflows/software-development/  # review コマンドを選んだ時のみ（評価基準ファイル。台帳 files[] 由来・コミットする）
```

```bash
cd <対象プロジェクト>
git clone <このリポジトリの URL> .setup-automate && printf '.setup-automate/\n' >> .gitignore
cd .setup-automate   # ← ここで Claude Code を起動する
```

この clone の `.claude/settings.json` には SessionStart / Stop の hook が登録されている。setup の進行中（選択 → 生成 → 検証）だけ動き、検証（`harness-setup-review`）を PASS する前に Claude が終了しようとすると block する。setup をしていない時は何もしない。

### 手順

1. 上記のとおり `.setup-automate/` に clone し、**その中で** Claude Code を起動する（対象ルートで起動するとこのリポジトリの CLAUDE.md が読み込まれず、下記の指示が効かない）。clone するだけでは何も自動実行されない（Claude Code は明示的な指示なしにファイルを実行しない設計のため、次の一言だけは必要）。
2. 「親ディレクトリ（`..`）をセットアップして」と伝える（表現は厳密でなくてよい。「ここの仕組みを `..` にも入れて」「`<対象の絶対パス>` をセットアップして」等でも同じ手順が走る — 詳細な発火条件は [CLAUDE.md](CLAUDE.md)「他プロジェクトのセットアップ依頼への対応」参照）。
3. 以降は Claude Code が `CLAUDE.md` の**完全列挙 + 由来別選択ルール**を実行する: 全要素を載せた選択記録（= 移植チェックリスト）の作成 → **由来別（Anthropic 公式由来 / 公式原則の具体化 / 著者の運用嗜好 / 第三者 / 業務プロンプト）に提示し、何を取り込むかをあなたが選ぶ**（著者嗜好はデフォルト非採用） → 選択を対象の `.claude/harness-selection.json` に記録 → `.claude/skills/agent-harness-bootstrap` で対象 CLAUDE.md を生成 → 選択した skills をコピー → `harness-setup-review` で「選択済みの抜けゼロ・非選択の混入ゼロ」を機械検査 + 別エージェント突合レビュー（両方 PASS するまで Stop hook が終了を block）→ 既存 skills があれば `skills-audit` で公式準拠を監査。由来の台帳は [provenance.json](.claude/skills/agent-harness-bootstrap/provenance.json)、選択手順は [selection-flow.md](.claude/skills/agent-harness-bootstrap/selection-flow.md)。
4. 完了後、対象側で `CLAUDE.md`・`.claude/`・（採用時）`workflows/software-development/` をコミットする。`.setup-automate/` と `.tmp/` はコミットしない。

### 検証と再同期

選択記録は対象ルートから機械検証できる（cwd はどこでもよい）:

```bash
bash .setup-automate/.claude/skills/agent-harness-bootstrap/scripts/provenance-check.sh \
  --selection "$PWD/.claude/harness-selection.json"
```

このリポジトリが更新されたら `.setup-automate/` 内で `git pull` し、同じ指示をもう一度伝える。前回 `selected: false` にした要素は再提案されず、台帳に増えた新要素だけが提示される。`.setup-automate/` は gitignore されているので、他のメンバーが再同期する時は同じ場所に再 clone する（`.claude/harness-selection.json` がコミットされていれば選択は引き継がれる）。

このリポジトリ自身をセットアップする場合（対象＝このリポジトリの中で作業したいだけの場合）は、上記は不要。clone して Claude Code で開けば `.claude/commands/` `.claude/skills/` は自動検出される（下記「Claude Code スラッシュコマンド／Skills」節）。

---

## このプロンプト集の設計思想

### 作成プロンプトは短く、AIに自由を与える

作成（実行）プロンプトを細かく指示しすぎると、**AIの可能性を狭めて結果を悪化させるリスクがある**。AIは日々進化しており、昨日まで必要だった細かな指示が、今日のモデルでは足かせになることがある。

作成プロンプトでは、**ゴール・制約・品質基準を簡潔に示し、具体的な手順はAIに委ねる**。文字数を削って余白を残すことで、AIがあらゆるアプローチを探索できる状態を作る。これが最良の成果物を引き出す設計原則である。

### レビュープロンプトこそが本質

**本当に価値があるのはレビュープロンプトである。**

レビュープロンプトには以下が凝縮される：

- **利用者の実力と経験** — 何が良い成果物で何がダメかを見分ける目
- **チームのノウハウ** — 過去のプロジェクトで蓄積した判断基準
- **失敗経験** — 「これをやるとこうなる」という痛みから得た知見
- **業界・ドメインの知見** — AI単体では持ち得ない現場の文脈

AIがどれだけ進化しても、**「何を良しとするか」の基準を決めるのは人間**である。作成プロンプトはAIの進化に合わせて陳腐化するが、レビュープロンプトは人間の知見が詰まっているからこそ価値が持続する。

### レビュープロンプトはチームで練り上げる

レビュープロンプトは個人で完結させず、**チームで共有し、議論し、継続的に改善する**べきものである。

```
新しい失敗が起きた → レビュー基準に追加
業界の基準が変わった → 評価軸を更新
メンバーの知見が増えた → チェック項目を洗練
```

このリポジトリのレビュープロンプト群（`review-*.md`）は、そのための共有資産として設計されている。

### ワークフローハーネスとは

成果物の種類（プレゼン／文書／コード等）ではなく、**業務ワークフロー単位**でプロンプトを束ねる考え方。1つの `workflows/<name>/` フォルダが1つの完結したハーネスであり、目的・作成プロンプト・レビュープロンプト・使用順序・関連する Claude Code Skills/Commands を1つの `README.md` に定義する。新しい業務が生まれたら、既存の分類に無理に押し込めず新しいワークフローフォルダを追加する。詳細・一覧・追加手順は [workflows/README.md](workflows/README.md) を参照。

### ハーネスを組むループ — 作成プロンプトも人間は書かない

このリポジトリ自身のharness（`CLAUDE.md`・`workflows/*/README.md`・Skills）を組み立てる時も、上記の設計思想をそのまま適用する。

- **作成プロンプトは人間が書き下ろさず、AIに書かせる**。ワークフローの作成プロンプトそのものも、まずAIに生成させてから人間が評価する。人間の時間は「何を良しとするか」を決めるレビュー基準の練り上げと、生成物の**監査・レビュー**に集中させる（作成プロンプトを人間が直接執筆する時間を最小化する）。
- **AIが作業中に別の問題（バグ・逸脱・想定外の挙動）を見つけても、その場で勝手に修正させない**。まず「何を見つけたか」の事実だけを報告させ、直すかどうか・いつ直すかは人間が判断してから着手させる。暴走の芽を勝手に握り潰させない・現在のタスクの範囲を広げさせない（scope creep防止）ための安全弁。
- この2点を含む「AIにharnessを作らせる時に人間が何を人間の役割として残すか」という考え方は、任意のプロジェクト向けにCLAUDE.md/harnessを生成するSkillである **`.claude/skills/agent-harness-bootstrap/SKILL.md`**（[本文へのリンク](.claude/skills/agent-harness-bootstrap/SKILL.md)）に体系化されている。同Skillが内蔵する主な原則:
  - **段階的開示（progressive disclosure）**: 頻繁には使わない知識をCLAUDE.md本体に書き込まず、`.claude/skills/` へ逃がして常時読み込みコストを下げる
  - **公式準拠の核と独自運用ノウハウのラベル分離**: Anthropic公式ドキュメントの内容は実行時にその都度取得し、Skill本体に転記・焼き込みしない（公式ドキュメントは更新されるため、転記は陳腐化する）
  - **由来台帳による取捨選択 (2026-09-04 追加)**: harness の全要素を `provenance.json` で `official` / `official-derived` / `author-preference` / `third-party` / `domain-prompt` / `repo-specific` に分類し、別プロジェクトへ適用する時は著者の運用嗜好（issue フォルダ管理・handoff 規約等）をデフォルト非採用にしてユーザーが選ぶ。公式由来と著者嗜好を混ぜたまま他環境へ写さないための仕組みで、台帳と実体の整合は `scripts/provenance-check.sh` で機械検査する
  - **自己レビュー不可**: 生成したCLAUDE.md・Skillsは生成した本人（同一セッション）が合格判定を下さず、別エージェントに検証させる
  - **規模に応じたスケール調整**: 「フル装備」を上限として、そのプロジェクトに実在しない規律・不要なオプション要素は生成しない（過剰生成の回避）
  - **行の要否判定 / Include・Exclude 判定**: 各セクション候補に Anthropic 公式の判定基準（「削除したらClaudeが間違えるか」を問い、コードを読めば分かることは書かない・推測で誤動作しうる手順だけ残す 等）を適用してから採用する（用語・文言は公式ドキュメントの改訂で変わりうるため、本skill自体は文言を焼き込まず実行時にWebFetchで確認する）
  - **Adversarial review step**: 生成した CLAUDE.md・skills・hooks を、生成した本人と会話履歴を共有しない別エージェントに公式基準で採点させ、全項目合格するまで再生成する（自己レビュー不可の具体形）
  - **数値目標の単一 SoT 化 (2026-09-01 追加)**: カバレッジ%・合格率等の数値目標は、それを実際に強制する設定ファイル（CI 閾値・validator 定数等）のみを SoT とし、CLAUDE.md や docs へ数値を重複記載しない。数値の宣言箇所と強制箇所が食い違ったまま放置される、という観察された失敗パターンへの対策。生成される `test-verify.md` の条文で、由来は著者の運用嗜好（default `recommend`: 事前チェック済みだがユーザーが外せる。2026-09-04 に必須から再分類）

---

## アップロードポリシー（公開リポジトリ）

このリポジトリは公開 GitHub リポジトリである。**汎用的に再利用できるプロンプト・スキルのみ**をアップロードし、**特定の企業名・製品名・顧客名・社内プロジェクト名など、特定の企業やプロジェクトに紐づく情報を含むものはアップロードしない**。詳細は [CLAUDE.md](CLAUDE.md) を参照。

---

## 対応AIサービス

| カテゴリ | 推奨サービス |
|---|---|
| 全般（`workflows/content-creation` / `business-planning` / `ops-management`） | [Claude](https://claude.ai) / [ChatGPT](https://chatgpt.com) / [Gemini](https://gemini.google.com) |
| リサーチ・ニュース収集（`workflows/research-intelligence`） | [Perplexity](https://www.perplexity.ai) / [Grok](https://grok.com) / [Gemini](https://gemini.google.com) |
| 開発（`workflows/software-development`） | [Claude Code](https://docs.anthropic.com/ja/docs/claude-code/overview) / [Cursor](https://www.cursor.com) / [Cline](https://cline.bot) |

---

## Claude Code スラッシュコマンド／Skills

このリポジトリをクローンして Claude Code で開くだけで、リポジトリ直下の `.claude/` が自動検出されて使える。

### `.claude/commands/` — スラッシュコマンド

| コマンド | コマンド本体 | 何をするか |
|---------|-------------|-----------|
| `/review-implementation` | [.claude/commands/review-implementation.md](.claude/commands/review-implementation.md) | 実装を5軸（テスト・正確性・マネタイズ・ペルソナ・UX）で100点満点評価 |
| `/review-changes` | [.claude/commands/review-changes.md](.claude/commands/review-changes.md) | 直近の変更差分を4軸（実装正確性・テストカバレッジ・テスト品質/戦略・追跡可能性）で100点満点評価。**別エージェントで実行**し客観性を確保 |
| `/review-skill` | [.claude/commands/review-skill.md](.claude/commands/review-skill.md) | 作成済みSkillsをAnthropicベストプラクティスに基づき5軸（構造・トリガー・命令品質・出力設計・実用性）で100点満点評価 |

> `/review-changes` は実装セッションとは別のエージェントを自動起動してレビューする。詳細は [agents.md](agents.md) 参照。

### `.claude/skills/` — 自動発動するSkills

| Skill本体（フルパス） | 何をするか |
|---|---|
| [.claude/skills/agent-harness-bootstrap/SKILL.md](.claude/skills/agent-harness-bootstrap/SKILL.md) | 任意のプロジェクトに Anthropic ベストプラクティス準拠の `CLAUDE.md` + `.claude/rules/` + hooks 一式を生成・剪定する（= CLAUDE.md を作成するprompt本体） |
| [.claude/skills/review-oss-contribution/SKILL.md](.claude/skills/review-oss-contribution/SKILL.md) | OSS貢献候補を独自性・先行技術・実現可能性・戦略の4基準で審査しGO/HOLD/REJECTを判定する |
| [.claude/skills/skills-audit/SKILL.md](.claude/skills/skills-audit/SKILL.md) | リポジトリ内の全Skillsを一括監査しGOOD/MIGRATE/IMPROVE/SPLITを判定する |
| [.claude/skills/stop-ai-slop-jp/SKILL.md](.claude/skills/stop-ai-slop-jp/SKILL.md) | AIで書いた日本語を人間の文章に戻す（[iKora128/stop-ai-slop-jp](https://github.com/iKora128/stop-ai-slop-jp) 着想・MIT・Daichi Nagashima 作、vendoring） |

**他のプロジェクトでもコマンドを使いたい場合:**
```bash
mkdir -p ~/.claude/commands
cp .claude/commands/*.md ~/.claude/commands/
```

> 詳細は `CLAUDE.md` を参照。

---

## ルートファイル

| ファイル | 何をするか |
|---|---|
| [CLAUDE.md](CLAUDE.md) | Claude Code 向けリファレンスマニュアル（スキル一覧・追加ルール・プロジェクト構成） |
| [agents.md](agents.md) | エージェント分離アーキテクチャ（レビューの客観性確保・分離ルール・制約と限界） |

## ディレクトリ構成

```
Job-Automate/
├── .claude/
│   ├── commands/              Claude Code スラッシュコマンド（自動検出）
│   └── skills/                Claude Code Skills（自動検出）
├── workflows/                 業務ワークフロー単位のハーネス（詳細: workflows/README.md）
│   ├── content-creation/      プレゼン資料・ブログ等の作成レビュー
│   ├── business-planning/     アイデア→提案書→仕様書の事業企画
│   ├── research-intelligence/ ニュース収集・SEO分析
│   ├── software-development/  コーディング・3エージェント開発・デザイン・Skills品質
│   └── ops-management/        サーバー運用・HR
├── archive/                   現行ワークフロー非採用の旧プロンプト（履歴参照用）
├── agents.md                  エージェント分離アーキテクチャ
└── CLAUDE.md                  Claude Code 向けリファレンスマニュアル
```

---

## workflows/content-creation/ — プレゼン資料作成・レビュー

詳細は [workflows/content-creation/README.md](workflows/content-creation/README.md)。

| プロンプト | レビュー | 何をするか |
|---|---|---|
| [slides-pro.md](workflows/content-creation/slides-pro.md) | [review-slides.md](workflows/content-creation/review-slides.md) | mdファイルを渡す → ブラウザで動くHTMLスライドを生成（← →キー操作・PDF出力・16:9対応） |
| [review-blog.md](workflows/content-creation/review-blog.md) | — | 任意のサイト（note / Qiita / Zenn / Medium / Dev.to / 企業ブログ等）のブログ記事を11観点110点満点でレビュー。0-gate（プラットフォーム固有制約）/ 4-gate（外部主体財務・性能・評判断定）/ 9-gate（コンプライアンス・業界規制）で重大違反を即D判定 |
| [creative.md](workflows/content-creation/creative.md) | — | ゴンベ顔文字など装飾的なテキストアートを生成する |
| [examples/beer-project-blog.md](workflows/content-creation/examples/beer-project-blog.md) | — | ビールプロジェクトのブログ記事例 |

---

## workflows/business-planning/ — 新規事業・提案書作成

アイデアの発展から提案書完成・品質評価まで一貫して使える。詳細は [workflows/business-planning/README.md](workflows/business-planning/README.md)。

```
1. business-idea.md でアイデアを対話形式で発展
      ↓
2. review-business-idea.md でS/A/B判定（次に進めるか確認）
      ↓
3. 提案書プロンプトで文書化
      ↓
4. review-proposal.md で品質評価
      ↓
5. specification.md で技術仕様書化 → review-specification.md で評価
```

| プロンプト | レビュー | 何をするか |
|---|---|---|
| [business-idea.md](workflows/business-planning/business-idea.md) | [review-business-idea.md](workflows/business-planning/review-business-idea.md) | ひと言のアイデアを話す → 対話形式で市場・ペルソナ・収益モデル・**競合克服戦略・エンゲージメント設計**を整理し事業計画へ発展 |
| [business-proposal.md](workflows/business-planning/business-proposal.md) | [review-proposal.md](workflows/business-planning/review-proposal.md) | ビジネスコンセプト＋チーム情報を入力 → 事業提案書を生成（ペルソナ・TAM/SAM・競合分析・**習慣ループ・リテンション設計**含む） |
| [it-proposal.md](workflows/business-planning/it-proposal.md) | [review-proposal.md](workflows/business-planning/review-proposal.md) | IT課題・システム概要を入力 → 体験価値重視のIT企画書を生成（**エンゲージメント設計・モート分析**含む） |
| [generic-proposal.md](workflows/business-planning/generic-proposal.md) | [review-proposal.md](workflows/business-planning/review-proposal.md) | 商品・サービスの情報を入力 → 業界問わず使える汎用提案書を生成（**エンゲージメント・リテンション設計**含む） |
| [specification.md](workflows/business-planning/specification.md) | [review-specification.md](workflows/business-planning/review-specification.md) | 企画書のmdファイルを渡す → 開発者が実装できる技術仕様書を生成 |

### レビュープロンプトの違い（`review-*.md` 一覧）

| ファイル | 対象 | 評価軸（100点満点） |
|---|---|---|
| [review-business-idea.md](workflows/business-planning/review-business-idea.md) | アイデア文書 | **6軸**: 独自性・競合克服戦略(20)／市場性(15)／実現可能性(15)／ペルソナ(15)／**エンゲージメント・リテンション設計(20)**／展開計画(15) |
| [review-proposal.md](workflows/business-planning/review-proposal.md) | 提案書・企画書 | **6軸**: 構成(15)／市場分析・競合克服戦略(20)／ペルソナ適合性(15)／根拠(15)／**エンゲージメント・リテンション設計(20)**／説得力(15) |
| [review-implementation.md](workflows/software-development/review-implementation.md) | 実装コード | 5軸: テスト品質／処理の正確性／マネタイズ整合性／ペルソナ適合実装／UX品質 |
| [review-changes.md](workflows/software-development/review-changes.md) | 変更差分 | 4軸: 実装正確性／テストカバレッジ／テスト品質・戦略／追跡可能性 |
| [review-specification.md](workflows/business-planning/review-specification.md) | 技術仕様書 | 5軸: 要件網羅性／アーキテクチャ／API・データ設計／テスト戦略／実装・運用計画 |
| [review-skill.md](workflows/software-development/review-skill.md) | Skills品質 | 5軸: 構造・命名／トリガー設計／命令品質／出力設計／実用性・保守性 |
| [review-research.md](workflows/research-intelligence/review-research.md) | リサーチ・ニュース・SEO | 5軸: 正確性／網羅性／分析深度／構成／実用性 |
| [review-ai-automation.md](workflows/business-planning/ideas/review-ai-automation.md) | AI自動化ビジネスモデル | 6軸: 実現可能性／収益性／自動化／競合モート／エンゲージメント／リスク |
| [review-persona.md](workflows/software-development/design/review-persona.md) | ペルソナ分析 | 5軸: 具体性／課題深掘り／デザイン整合性／セグメント分類／検証可能性 |
| [review-ops.md](workflows/ops-management/review-ops.md) | 運用スクリプト・サーバー設定 | 5軸: セキュリティ／冪等性／エラーハンドリング／運用性／パフォーマンス |
| [review-blog.md](workflows/content-creation/review-blog.md) | ブログ記事（note / Qiita / Zenn / Medium / 企業ブログ等） | **11軸110点満点**: わかりやすさ／独自性／有益性／事実正確性／事実と所感分離／冒頭サマリ／冗長性・一貫性／読みやすさ・文体／コンプライアンス／第三者配慮／技術評価妥当性 + **3ゲート条項**（0-gate プラットフォーム制約 / 4-gate 外部主体断定 / 9-gate コンプラ違反）で即D判定 |

### workflows/business-planning/ideas/ — AI自動化ビジネスモデル

| ファイル | レビュー | 何をするか |
|---|---|---|
| [ideas/ai-automation.md](workflows/business-planning/ideas/ai-automation.md) | [ideas/review-ai-automation.md](workflows/business-planning/ideas/review-ai-automation.md) | 無料ツール（Gemini API・Cloudflare等）で収益化を目指すAI自動化ビジネスを複数案提案させる |

---

## workflows/research-intelligence/ — リサーチ・ニュース・SEO

詳細は [workflows/research-intelligence/README.md](workflows/research-intelligence/README.md)。レビューは共通で [review-research.md](workflows/research-intelligence/review-research.md) を使用。

| ファイル | 何をするか |
|---|---|
| [news/it.md](workflows/research-intelligence/news/it.md) | ITニュースを収集・要約する |
| [news/craft-beer.md](workflows/research-intelligence/news/craft-beer.md) | クラフトビール業界のニュースを収集・要約する |
| [news/trends.md](workflows/research-intelligence/news/trends.md) | 指定分野のトレンドをリサーチする |
| [news/investment.md](workflows/research-intelligence/news/investment.md) | 投資関連情報を収集・整理する |
| [seo/base.md](workflows/research-intelligence/seo/base.md) | サイト・コンテンツのSEO基盤を設計する |
| [seo/trend-keywords.md](workflows/research-intelligence/seo/trend-keywords.md) | 今トレンドのSEOキーワードを収集・分析する |

---

## workflows/software-development/ — 開発プロンプト集

> **コーディングを含むすべての開発は [three-agent/](workflows/software-development/three-agent/) から始めてください。** 詳細は [workflows/software-development/README.md](workflows/software-development/README.md)。

### dev/three-agent/ — 3エージェント開発システム

3つのAIセッションを使い分け、TDD（テスト駆動開発）で品質を担保しながら開発する。

| ファイル | 役割 | 何をするか |
|---|---|---|
| [README.md](workflows/software-development/three-agent/README.md) | — | システム全体の使い方・ロール説明 |
| [leader.md](workflows/software-development/three-agent/leader.md) | リーダー（ターミナル1） | ゴール設定・テスト方針・タスク分解・次イテレーション指示 |
| [executor.md](workflows/software-development/three-agent/executor.md) | 実行（ターミナル2） | テスト→実装→リファクタのTDDサイクルを回す |
| [reviewer.md](workflows/software-development/three-agent/reviewer.md) | レビュー（ターミナル3） | テストと実装の品質評価・改善指示 |

### design/ — デザインシステム（IBM Carbon準拠）

| ファイル | レビュー | 何をするか |
|---|---|---|
| [persona.md](workflows/software-development/design/persona.md) | [review-persona.md](workflows/software-development/design/review-persona.md) | 顧客の年齢・ニーズ・フラストレーションを分析 → カラー・フォント・UXパターンを決定する（最初に実施） |
| [design-system.md](workflows/software-development/design/design-system.md) | — | IBM Carbon準拠のデザイントークン・コンポーネント仕様を参照する |
| [design-guidelines.md](workflows/software-development/design/design-guidelines.md) | — | 絵文字禁止・ダークモード・レスポンシブ・品質チェックリストを参照する |
| [design-research.md](workflows/software-development/design/design-research.md) | — | 優れたUX原則・AIっぽくないデザイン手法のリファレンス |

### rules/・mcp/

| ファイル | 何をするか |
|---|---|
| [rules/coding-principles.md](workflows/software-development/rules/coding-principles.md) | AIコーディング時に守るべき規則（過剰実装禁止・セキュリティ・テスト方針など） |
| [mcp/playwright.md](workflows/software-development/mcp/playwright.md) | Playwright MCPのセットアップ手順とE2Eテスト実行方法 |
| [mcp/serena.md](workflows/software-development/mcp/serena.md) | Serena MCP（コードベース分析）のセットアップ手順 |
| [mcp/windows-setup.md](workflows/software-development/mcp/windows-setup.md) | Windows環境でのMCP設定手順 |

---

## workflows/ops-management/ — 運用・管理

詳細は [workflows/ops-management/README.md](workflows/ops-management/README.md)。レビューは [review-ops.md](workflows/ops-management/review-ops.md) を使用。

| ファイル | 何をするか |
|---|---|
| [server/automation.md](workflows/ops-management/server/automation.md) | サーバー作業を自動化するスクリプトを生成する |
| [server/init.md](workflows/ops-management/server/init.md) | 新規サーバーの初期設定手順を生成する |
| [server/windows-standard.md](workflows/ops-management/server/windows-standard.md) | Windows環境の標準化手順を生成する |
| [hr/year-end-adjustment.md](workflows/ops-management/hr/year-end-adjustment.md) | 年末調整用のCSVファイルを生成する |

---

## 新しいワークフロー・スキルを追加するルール

### 新しい業務ワークフローを追加する

1. `workflows/<workflow-name>/` を作成する
2. 作成プロンプトとペアになる `review-*.md` を作成する
3. `workflows/<workflow-name>/README.md` に目的・使用順序・関連skills/commandsを書く
4. `workflows/README.md` の一覧表と、本ファイルに追記する（追記漏れは `.claude/skills/workflow-coverage-and-structure/SKILL.md` で機械検査できる）

### Claude Code Skill/Command として追加（自動発動させたい場合）

1. `.claude/commands/[コマンド名].md`（対話的スラッシュコマンド）または `.claude/skills/[name]/SKILL.md`（条件発動）を作成する
2. 自己完結にする（他ワークフローのパスをハードコードしない）
3. 本ファイルの「Claude Code スラッシュコマンド／Skills」節に追記する
4. エージェント分離が必要な場合は `agents.md` にも追記する

---

## ライセンス

[MIT License](LICENSE)。ただし `.claude/skills/stop-ai-slop-jp/` は第三者OSSのvendoringであり、同ディレクトリ内は同梱の独自MITライセンス・著作権表記（[LICENSE](.claude/skills/stop-ai-slop-jp/LICENSE)）が適用される。

## 運営者

[Koki Riho（Rih0z）](https://github.com/Rih0z) — GitHub / Twitter: [@rihobeer2](https://x.com/rihobeer2)
