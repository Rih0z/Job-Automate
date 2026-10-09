# Job-Automate — Claude Code リファレンス

このリポジトリは **(1) 自身のAI活用業務自動化のためのプロンプトライブラリ** であると同時に、**(2) 他のリポジトリに clone してセットアップ・レビューを行うための harness 提供リポジトリ** である。**(2) が本リポジトリの中核目的**: `agent-harness-bootstrap` / `harness-setup-review` 等の skills を通じて、対象プロジェクトを Anthropic 公式ベストプラクティス準拠の最適な状態にする（詳細は下記「他プロジェクトのセットアップ依頼への対応」節）。
Claude Code でプロンプトを開発・改善するときのガイドです。

プロンプトは成果物の種類ではなく**業務ワークフロー単位**で `workflows/<name>/` に束ねる（ハーネスの考え方は [workflows/README.md](workflows/README.md)）。Claude Code が自動検出する実行可能な Skills はリポジトリ直下 `.claude/skills/` に置く。

**別プロジェクトのセットアップに使いたい場合 (2026-09-01)**: このリポジトリを対象プロジェクト直下の `.setup-automate/`（gitignore 対象）に clone し、その中で Claude Code を起動して「親ディレクトリ（`..`）をセットアップして」「ここのやり方を `<対象>` にも入れて」等、**目的が伝われば表現は問わない**旨をこの CLAUDE.md 自体が常時 context にロードされることで保証する（clone しただけで自動実行はされない — Claude Code は明示的な指示なしにファイルを実行しない設計のため、開始の一言だけは必要）。詳細手順は下記「他プロジェクトのセットアップ依頼への対応」節、配置・gitignore・再同期は [README.md](README.md) 冒頭「クイックスタート: 別プロジェクトへ移植する」に掲載。

---

## アップロードポリシー（公開リポジトリ）

このリポジトリは公開 GitHub リポジトリである。**汎用的に再利用できるプロンプト・スキルのみ**をアップロードし、**特定の企業名・製品名・顧客名・社内プロジェクト名など、特定の企業やプロジェクトに紐づく情報を含むものはアップロードしない**。

- 他プロジェクト由来の設計パターンを本リポジトリに取り込む場合、そのプロジェクト固有の名称・識別子・条文番号・実装詳細を引用せず、一般化した設計原則として書き直す
- 既存ファイルを更新する際も、意図せず固有名詞が混入していないか確認する（コミット前に企業名・製品名で grep する等）
- 該当する社内知見・非公開プロジェクトの情報が必要な場合は、このリポジトリでなく非公開のリポジトリ/ドキュメントで管理する

---

## 応答ルール

作業完了を報告する際は、編集・作成した全ファイルの完全パスを応答に明記する。

バグ修正時: エラーメッセージが修正箇所を明確に示している単純な修正はそのまま直接修正する。依存関係や他ファイルとの整合確認が必要な修正は、着手前に対象が依存する workflow・skill・設定ファイルを洗い出し、その旨を明示する。複数ファイルにまたがる変更や設計判断を伴う複雑な修正は、実装に入る前に Plan Mode で依存関係の洗い出しと計画・レビューを行ってから着手する。洗い出した依存関係は、関連する `workflows/<name>/README.md` に一言残し、後から参照できるようにする。

作業中に本題と別件の問題・改善点（バグ・逸脱・想定外の挙動を含む）に気づいた場合、上記「AIが作業中に別の問題を見つけても、その場で勝手に修正させない」原則（[README.md「ハーネスを組むループ」](README.md#ハーネスを組むループ--作成プロンプトも人間は書かない)）どおり、その場で修正に着手せず、まず「何を見つけたか」の事実だけをその応答内で一言報告する。加えて `.tmp/discovery-log.md` へ気づいた記録を残す（詳細な書式・drain 手順は下記）。

**discovery-log の書式と扱い**（2026-09-15 改訂: 自由文 1 行から JSON 構造化へ）:

- **いつ書くか**: 気づいた**その瞬間**（口頭報告や自由文の1行では長い作業の中で読み手・書き手双方の記憶から埋もれるため、その場で必ず追記する）。
- **書式**: 自由文ではなく **JSON Lines（1オブジェクト1行）**。後から grep/jq 等で機械的に拾い漏れを検知できるようにするため。
  `{"ts": "<ISO8601日時>", "summary": "<気づいた内容を1文で>", "location": "<手がかりとなるファイル:行 または文脈>", "status": "queued"}`
- **位置づけ**: 正式なタスク化・修正の代わりではなく、人間が直すかどうか・いつ直すかを判断するまでの一時的な備忘バッファ。
- **見返し（drain）のタイミング**: イテレーション完了時、`/compact` 実行前、**引継ぎ資料 (`.tmp/handoffs/`) を作成する時点を含む**。
- **drain の判断**: `status` を `"done"`（対応済み）に更新するか、本リポジトリの Issue 相当物である `.claude/skills/_shared/compliance-status.json` の `findings` へ CR-xx として追加し `status` を `"issued"` にした上で発行した CR-id を併記するかを決めてから当該行を消す（残したまま「完了」と報告しない）。
- **引継ぎ資料作成時の gate**: 作成前に `status: "queued"` のまま残っているエントリが無いことを確認する（残っていれば先に `"done"`/`"issued"` のいずれかへ倒してから作成する）。

コード・スクリプトを書く・直す作業は **設計 → テスト設計 → テスト実装(Red) → 実装(Green→Refactor)** の順で行う（テスト設計 = 検証ケース・テスト名・期待値の導出・自動化しない範囲を決める工程。成果物は設計書の「テスト戦略」の節）。各工程は別エージェントのレビューで終え、PASS するまで次工程に着手しない（設計とテスト設計は 1 回のゲートでまとめて審査する。テストを書く前に実装コードを書かない・Red を確認していないテストは後付け扱い・自己レビューで通過扱いにしない）。手順とテスト設計の中身は [single-session-tdd](.claude/skills/single-session-tdd/SKILL.md) skill、工程別の観点は [review-gate](.claude/skills/review-gate/SKILL.md) skill の `criteria/*.json`、3ターミナル分離で回す場合は [three-agent-tdd-workflow](.claude/skills/three-agent-tdd-workflow/SKILL.md) skill。

`/compact` 実行時は必ず以下を残す: 編集・作成した全ファイルの完全パス、対象の workflow/skill 名、実行したテスト・検証コマンドと結果。

---

## レビュースキル一覧

Claude Code 環境で使えるレビュー系コマンド／Skills の全一覧（用途・評価軸）は [README.md](README.md)「Claude Code スラッシュコマンド／Skills」節に、エージェント分離の起動手順は [agents.md](agents.md) に集約されている（本ファイルでは重複記載しない）。個別の一覧は `.claude/skills/` を `ls` するか `/skills` コマンドで確認。Claude Code 以外（Claude.ai 等）で使う場合の元プロンプト直接貼り付けの対応表は README.md「レビュープロンプトの違い」表を参照。

既知の公式ベストプラクティス逸脱・改善バックログ（公式原則ごとの採用状況と CR-xx）は構造化データ [.claude/skills/_shared/compliance-status.json](.claude/skills/_shared/compliance-status.json)、再監査手順は [.claude/skills/_shared/compliance-roadmap.md](.claude/skills/_shared/compliance-roadmap.md) を参照。

調査系レビュー結果の構造化永続化（観点別合否・出典・要約をJSONで保存し後から見返す仕組み）は、対象 skill 自身（`research-deliverable-review` 等）と [.claude/skills/_shared/review-record.schema.json](.claude/skills/_shared/review-record.schema.json) を参照（2026-09-14 追加）。

---

## `/review-implementation` を使う前に準備しておくと精度が上がるもの

| 準備 | ファイル例 | なければ |
|------|-----------|---------|
| ペルソナ定義 | `workflows/software-development/design/persona.md` | 推定ユーザーを仮定して評価（スコアに注記あり） |
| 収益モデル | README に記載 | マネタイズ観点をN/Aとして除外し80点満点に換算 |
| テスト基盤（ランナー設定） | `jest.config.*` 等 | テストファイルを探して判断 |
| デザインガイドライン | `workflows/software-development/design/design-guidelines.md` | 一般的なUXベストプラクティスで評価 |

---

## 新しいワークフロー・スキルを追加するルール

**追加前チェック（共通）**: 既存の `workflows/` 一覧・`.claude/skills/` 一覧を検索し、目的が重複する既存プロンプト/スキルがないか確認する（重複なら新設せず既存を拡張する）。作成後は別エージェント（`/review-skill` 等）によるレビューを最低 1 回受け、指摘が収束してからマージする。

**採点基準と採点対象の矛盾**: レビュー・採点系の skill を新設・改修する時は、採点対象のディレクトリや生成物の条件（規約、生成 script の固定文、文書の構造）と採点基準が矛盾しないか確かめる。矛盾することがあり、その場合は矛盾しない設計に見直す。矛盾の型と見つけた時の手順は [stop-ai-slop-jp](.claude/skills/stop-ai-slop-jp/SKILL.md) の `criteria/scoring.json`（`conflict_policy`）にある。

### 業務ワークフローとして追加（プロンプトの本体）

1. `workflows/<workflow-name>/` を作成する
2. 対応する作成プロンプト（`<対象>.md`）とレビュープロンプト（`review-<対象>.md`）をペアで管理する
3. `workflows/<workflow-name>/README.md` に目的・使用順序・関連skills/commandsを書く
4. `workflows/README.md` の一覧表と `README.md` のテーブルに追記する（この step の追記漏れは `.claude/skills/workflow-coverage-and-structure/SKILL.md` で機械検査できる、2026-09-02 追加）

### Claude Code プロジェクトスキルとして追加（推奨 — git 共有される）

1. `.claude/skills/[skill-name]/SKILL.md` を作成する（YAML frontmatter 必須。`.claude/commands/*.md` の旧形式は使わない — commands は skills に統合済み）
2. スキルを自己完結にする（他ワークフローのパスをハードコードしない）
3. `README.md` のスキル一覧テーブルに追記する
4. 詳細な評価基準は該当ワークフローの `review-[対象].md` に分離して記述する
5. エージェント分離が必要な場合は `agents.md` のエージェント一覧にも追記する
6. 他プロジェクトでも使いたい場合は `~/.claude/skills/` にもコピーする

---

## 他プロジェクトのセットアップ依頼への対応 — 完全列挙 + 由来別選択ルール (2026-09-01 制定・2026-09-04 改訂)

**発火条件 (2026-09-01 拡張)**: 「このリポジトリを使って `<対象>` をセットアップして」のような精密な言い回しに限定しない。ただし**必須条件は「このリポジトリ以外の別ディレクトリ/別リポジトリが対象と明確に読み取れること」**（対象パスの明示、「別プロジェクト」「他のリポジトリ」等の明示、のいずれか）。この条件を満たす依頼は表現を問わず本節を適用する: 「親ディレクトリ（`..`）をセットアップして」（推奨配置: このリポジトリが対象の `.setup-automate/` に clone されている場合。対象 = `..` の絶対パス）「ここの仕組みを別プロジェクトにも入れて」「このリポジトリの CLAUDE.md/skills/rules を〈他リポジトリ〉に移植して」「clone した内容を〈対象パス〉で使えるようにして」等。**対象が明示されない「セットアップして」「使えるようにして」は本節を発火させない**（このリポジトリ自身の中で作業したいだけの依頼と区別できないため。この場合は通常の応答＝リポジトリ内での作業支援として扱う）。対象は明示されたが依頼が曖昧な場合のみ「対象ディレクトリはどこか」を確認する（適用するかどうか自体は聞き返さない）。

このリポジトリには **Anthropic 公式ベストプラクティス由来の要素**と**著者の運用嗜好**（issue フォルダ管理・handoff 規約・並走 4 軸 recheck・SessionStart hook 等）が同居している。別プロジェクトへ移す時に両者を混ぜたまま持ち込まないため、要素ごとの由来は `.claude/skills/agent-harness-bootstrap/provenance.json` を唯一の SoT として管理し（各 SKILL.md の frontmatter `metadata.provenance` は台帳の写し）、次の 3 点を守って「何を取り込み、何を取り込まないか」を**ユーザーが決める**:

- **列挙は完全に**: `provenance.json` の全要素（本 CLAUDE.md の各セクションも `claude-md-*` 要素）を載せた選択記録（対象の `.claude/harness-selection.json`、非選択も `selected: false` で記録）を移植チェックリストの実体とする。黙って省略しない。
- **採用はユーザーが決める**: `official` は必ず採用（外せない）/ `official-derived` は推奨（外せる）/ `author-preference` `third-party` `domain-prompt` はデフォルト非採用（選んだものだけ）/ `repo-specific` は移植不可。非対話なら `default_selection` のみ採用し、その旨を報告冒頭に明記する（好みを推測で補わない）。非選択の著者嗜好要素を「念のため」持ち込まない。
- **検証は省略不可**: 移植完了後に `harness-setup-review` skill（`provenance-check.sh --target` の契約検査と別エージェントの突合レビュー。対象に既存 skills があれば `skills-audit` も）を実行し、両方 PASS するまで完了報告しない。移植元 clone の Stop hook が検証前の終了を block する。

手順の本体（提示の仕方・`AskUserQuestion` の分割・`depends_on` / `soft_depends_on` の扱い・記録の書式・生成との接続）は `.claude/skills/agent-harness-bootstrap/selection-flow.md`、検証の本体は `.claude/skills/harness-setup-review/SKILL.md`。個々の要素の採否の経緯（例: `numeric-target-single-sot` を 2026-09-04 に author-preference へ再分類）は台帳の `history` / `note` にある。

背景: セットアップ時に一部の観点だけ移植され、後から「あの観点は取り込めているか」という確認・追加依頼が繰り返される失敗パターンへの対策として**列挙の完全性**は維持する。一方で、公式由来と著者嗜好が区別されないまま全部持ち込まれ、移植先に不要な運用が混入する失敗パターンへの対策として、**採用の決定**はユーザーに委ねる。完全性は依頼者の記憶でなくチェックリスト・選択記録・突合レビューで担保する。

## 根拠明記の推奨 (2026-08-31)

research/proposal/report 系の成果物が外部情報・過去データに基づく事実主張をする場合、根拠となる資料の完全パス (ローカルファイル) または URL (外部情報源) を近接記載することを推奨する。適用対象は成果物テンプレート出力および `review-*` skill のレビュー結果 (既存の `citation_required` は変更しない)。事実主張でない意見・提案・戦略考察には適用しない。

本 repo は自動 CI 機械検証を持たないため、本項目は **advisory な推奨** であり必須ゲートではない (2026-08-31 時点。将来 review-* skill への組み込みが進めば昇格を検討)。

## プロジェクト構成

トップレベルは `CLAUDE.md` / `README.md` / `agents.md` / `.claude/`（skills）/ `workflows/`（業務ワークフロー単位のハーネス）/ `archive/`（旧プロンプト）。ワークフローごとの内訳・各ファイルの所在は [workflows/README.md](workflows/README.md) と [README.md](README.md) を参照（このファイルでは重複記載しない）。

**「テストカバレッジは?」「プロジェクト構成は?」に相当する質問への回答 (2026-09-02 追加)**: `.claude/skills/workflow-coverage-and-structure/SKILL.md` で即答する（`bash .claude/skills/workflow-coverage-and-structure/scripts/workflow-doc-coverage-check.sh --report`）。上記「新しいワークフロー・スキルを追加するルール」step 4（README 追記）の機械検査として使う。
