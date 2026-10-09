---
name: select-slop-viewpoints
description: |
  作る資料の種類（ブログ・体験記、イベント参加報告資料、調査・分析レポート、技術文書など）に応じて、
  stop-ai-slop-jp の観点（コアルール 14 項目・採点 5 軸・blocker）のうち、どれをどう使うかを選び、
  JSON で返す。観点の目録と、種類ごとの選択は構造化データ（criteria/*.json）にあり、
  レビューを行う別エージェントにこの JSON を渡して、種類に合った観点だけで採点させる。
  日本語の資料を書く前と確定前のレビューで、その資料にどの観点を当てるかを決める時に使う。
  Trigger phrases: '資料の種類に合わせて stop slop の観点を選んで', '報告資料の AI 臭レビューの観点',
  'ブログと報告資料で観点を切り替えて', 'stop-ai-slop の観点を JSON で', 'select slop viewpoints'.
allowed-tools: Read Glob Grep Bash
argument-hint: "資料の種類の id（blog / event-report / analysis-report / tech-doc ほか）"
metadata:
  provenance: domain-prompt
---

# 資料の種類に応じた stop-ai-slop-jp の観点の選択

`stop-ai-slop-jp` はブログ・体験記を前提にした規則と採点基準を持つ。報告資料や技術文書にそのまま当てると、構造や口調が種類の約束事と食い違う規則（例: 報告資料の「3 項目並列を疑う」、技術文書の「語尾を崩す」）が、誤った指摘を生む。この skill は、**種類ごとに使う観点を構造化データで決め、選んだ結果を JSON で返す**。規則の本文は `stop-ai-slop-jp` が正本で、この skill は選択だけを持つ。

対象: $ARGUMENTS

## 使う場面

- 日本語の資料を書く前と、確定前のレビューで、「この資料にどの観点を当てるか」を決めたい時。
- レビューを別エージェントに依頼する時（採点者に、種類に合った観点の JSON だけを渡したい時）。

## 手順

1. **資料の種類を決める。** 依頼者の宣言を優先する。決められなければ依頼者に聞く（推測で決めない）。種類の一覧は `python scripts/select_viewpoints.py --list`（この skill のフォルダ基準。リポジトリ直下からは `.claude/skills/select-slop-viewpoints/scripts/select_viewpoints.py`）。
2. **観点を選ぶ。** `python scripts/select_viewpoints.py --doc-type <id> --output <path>`。出力 JSON は次を持つ。
   - `rules`: 14 規則それぞれの扱い（`apply` 適用 / `skip` 指摘しない / `modify` 条件付きで変えて適用 / `conditional` 条件の範囲だけ適用）、条件（`condition`）、`skip` の受け持ち先（`covered_by`）。
   - `axes`: 使う 5 軸の質問文・1/5/10 点の anchor・配点。種類ごとの調整（`override`）があれば、根拠・緩めない点・減点が残る反例を含む。
   - `blockers`: 点に関わらず最優先で是正する項目。
   - `pass_rule`: 合格点（`stop-ai-slop-jp/criteria/scoring.json` と同値）。
3. **採点者に渡す。** レビューを行う別エージェント（作成者とは別）に、資料と手順 2 の JSON だけを渡す。実装の経緯や会話履歴は渡さない。採点者は JSON の `instructions_for_scorers` に従い、`skip` の規則は指摘せず、`modify`・`conditional` は条件の範囲だけで適用する。
4. **点と合否。** 出力 JSON の `procedure`（独立 3 回の中央値で合否を決める `verdict_rule`、文体だけを採点する `scoring_scope`、反論の扱い）に従う。blocker は点に関わらず是正する。

## 資料の種類（汎用）

| id | 資料 | 規則の扱いの要点 |
|---|---|---|
| `blog` | ブログ・体験記 | 全規則と 5 軸を `stop-ai-slop-jp` の定義どおりに使う |
| `event-report` | イベント参加報告資料 | 帰属と限定（`attribution`）を主軸にする。反証可能な主張は所感・示唆の節だけ。口語の評価語と雑談調の伝聞は使わず、出所と確度を書く。3 項目並列は `skip` |
| `analysis-report` | 調査・分析レポート | 確度を示すヘッジと、確度を添えた代替仮説の併記を slop として指摘しない |
| `tech-doc` | 技術文書 | 口語の評価語・毒・語尾のムラは `skip`。整形は `stop-ai-slop-jp/references/tech-writing.md` に従う |

扱いは**提案値**。使って食い違えば、根拠を付けて `criteria/doc-types.json` を直す（下記）。

## 種類を足す・扱いを直す

1. `criteria/doc-types.json` に種類を足すか、規則ごとの扱いを直す（リポジトリ固有の種類は `criteria/doc-types.local.json`。汎用の id と衝突させない）。
2. 全 14 規則に扱いを付ける。`skip` には `covered_by`（別の規則・軸・検査、または外す理由）、`modify` と `conditional` には `condition` を必ず書く。
3. 軸の問い・anchor・閾値を調整する時は、`axis_overrides` に `ground`（どの指示とどの基準がどう食い違うか）、`keeps`（緩めない点）、`counter_examples`（調整後も減点が残る例を 2 件以上）を書く。基本の軸を別の軸に置き換える時は、`axis_replacements` に同じ 3 項目を書く。
4. `python scripts/select_viewpoints.py --validate` と `python scripts/tests/run_tests.py` を通す。

## 緩めない保証

- 合格点は `scoring.json` の `pass_rule.min_total` と同値で、種類ごとに変えない。
- `agency`・`concreteness` は読み替えない規定（`stop-ai-slop-jp` の G3）がある repo では、その軸を調整する種類を `scoring.json` の G3 の `exceptions` に根拠付きで残す。残っていなければ検査が落とす。
- 種類が `inherit_profile` を持つ時は、その profile の `guards`・`finding_labels`・`scope`・`rebuttal_rule` が出力 JSON の `inherited_profile` に入り、採点者に渡す JSON だけで足りる。
- blocker は全ての種類で残る。帰属誤り・属性の過小断定は `stop-ai-slop-jp` の定義で、指示文のメモ書き化（`instruction_echo`。依頼文の言い回しや作業用の語の漏れ）はこの skill が追加した blocker。意味の一意性（`single_meaning`。文の読み方が 2 通りに割れて、読み手が別の事実に取る誤り）は `stop-ai-slop-jp` の `blocker_checks` と同じ定義。
- `skip` にできるのは最大 5 規則。false agency・偏愛語・横文字メタファー・記号のアーティファクト（R01・R11・R12・R14）は、`skip` にも `modify`・`conditional` にもできない（`apply` のみ）。基本の 5 軸を別の軸に置き換える時は、根拠（`axis_replacements`）が要る。
- 種類の調整は根拠と反例が無ければ検査が落とす。基準を緩めるだけで合格させない（`scoring.json` に `conflict_policy` があればそれに従い、無ければ `procedure.scoring_scope` の 3 項目目に従う）。

## 他の skill との関係

- `stop-ai-slop-jp`: 規則の本文・採点軸・リファレンスの正本（第三者 OSS の vendoring。この skill からは編集しない）。
- ブログ記事の総合レビュー用の skill（例: `review-blog`。リポジトリにある場合）: 品質・有用性・コンプライアンス等を見る別の目的で、文体の観点の選択はしない。重複しない。

## 試験

`python scripts/tests/run_tests.py`（標準ライブラリのみ）。目録の見出し語が `stop-ai-slop-jp/SKILL.md` に含まれること、全ての種類の検査と出力（14 規則・5 軸・配点の合計・合格点・blocker）、根拠の無い調整や受け持ち先の無い `skip` を検査が落とすこと、公開版に固有名詞が無いことを確かめる。
