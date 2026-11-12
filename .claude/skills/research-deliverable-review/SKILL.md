---
name: research-deliverable-review
description: >
  news/*・seo/* リサーチプロンプトで生成されたニュース収集・SEO分析の成果物を、情報の正確性・信頼性/
  網羅性・カバレッジ/分析の深度・洞察/構成・可読性/実用性・アクション接続の5軸100点満点で客観的に
  採点する。別エージェントを起動してレビューする(自己レビューしない)。
  Trigger phrases: 'リサーチ成果物 レビュー', 'ニュース収集結果を採点', 'SEO分析レポート レビュー',
  'research deliverable review', 'score this research output'.
  使わない場面: 一次情報との照合や非公開情報・伝聞の混入検査だけをしたいとき（source-verification-scan）、
  ブログ記事の公開前レビュー（review-blog）、news/*・seo/* 以外の文書の採点。
metadata:
  provenance: domain-prompt
  version: "1.1"
---

# リサーチ・情報収集 品質レビュー（エージェント分離実行）

> **このスキルは別エージェントを起動してレビューを行う。現在のセッションでは直接採点しない。**
> 生成コンテキスト（どの意図でリサーチしたか等の会話履歴）をレビューエージェントに渡さないことで客観性を確保する。

対象: `news/*.md` および `seo/*.md` 系のリサーチプロンプト（`workflows/research-intelligence/news/` と `workflows/research-intelligence/seo/`）で生成された、ニュース収集・SEO分析の成果物。

## 前提条件

- Agent ツールで別エージェントを起動できること。`.claude/agents/readonly-reviewer.md` は任意（無ければステップ2のフォールバック）。
- 評価観点の正本 `references/criteria.md` と、同じリポジトリの `.claude/skills/_shared/`（`review-rubrics.yaml`、`review-record.schema.json`、`scripts/list_review_records.py`、`scripts/append_review_record.py`）。他リポジトリへ移す場合は `_shared` も一緒に置く。`_shared` が無い環境では、判定段階を `references/criteria.md` の採点目安の合計（90 以上 S、80 以上 A、70 以上 B、60 以上 C、それ未満 D）で決め、過去記録の検索と永続化を省いて、その旨を最終報告に書く。
- Python 3。コマンド例の `python` は Python 3 を指し、`python` が無い環境では `python3` に置き換える。

## 使用例

- ユーザー「`news/it.md` で作った今日の IT ニュースまとめを採点して」→ ステップ1で本文と基本情報を集め、過去記録を検索 → ステップ2で readonly-reviewer に採点させる → Markdown の結果をそのまま表示し、JSON を `append_review_record.py` で保存して保存先を報告する。
- ユーザー「この SEO 分析をレビューして」（使用プロンプトと想定読者が不明）→ ステップ1の 2〜6 が埋まらないので、レビューを起動する前に依頼者へ確認する。
- ユーザー「この記事に非公開情報が混ざっていないかだけ見て」→ 本 skill ではなく source-verification-scan を案内する。


---

## 実行手順

### ステップ1: 情報収集（この実装セッションで行う）

レビュー対象の成果物および前提事実のみを収集する。評価コメント・採点は含めない。

```
収集対象:
1. レビュー対象の成果物本文（Markdown等、全文）
2. どのプロンプトで生成された成果物か（`workflows/research-intelligence/` 配下の news/craft-beer.md, news/investment.md, news/it.md,
   news/trends.md, seo/base.md, seo/trend-keywords.md のいずれか、または不明）
3. 対象とする地域・市場（例: シアトル/全米/日本）
4. 対象期間（例: 直近24-72時間、または特定期間分析）
5. 成果物の利用目的（投資判断・事業戦略・コンテンツ企画・市場参入検討など）
6. 想定読者（経営層・マーケター・エンジニア・投資家など）
```

上記 2-6 が成果物または依頼者から確認できない場合は、レビュー起動前に確認すること。

**過去レビュー記録の参照**: レビュー起動前に以下を実行し、同一対象の過去レビュー記録を検索する（`--skill` を省略することで、このskill以外の別のレビュー系skillが過去に同一対象をレビューした記録も横断的に拾う）。

```bash
python .claude/skills/_shared/scripts/list_review_records.py --target "<成果物タイトルまたはファイルパスの一部>"
```

`NO_PRIOR_RECORDS` 以外がヒットした場合、該当行（path/skill/reviewed_at/verdict/score/summary）をステップ2のレビューエージェントへのプロンプトに「過去レビュー記録」として渡す（該当ファイルを Read して verdict・主な指摘も要約に含める）。

### ステップ2: レビューエージェント起動

**Agent ツール**を使い、以下の設定で別エージェントを起動する:

```
Agent ツールの設定:
- subagent_type: "readonly-reviewer"（`.claude/agents/readonly-reviewer.md`。書き込み系ツールを持たない。定義が無い環境・新設直後で未読込のセッションでは "general-purpose" で起動し、prompt 冒頭に「ファイルを作成・変更・削除しない」と明記する）
- description: "Review research deliverable objectively"
- prompt: 以下のテンプレートに収集した情報を埋め込む
```

**プロンプトテンプレート（レビューエージェントに渡す内容）:**

```
あなたは依頼者・作成者とは別の客観的なリサーチ品質レビュアーです。
以下のリサーチ・ニュース収集・SEO分析成果物を、5項目・各20点・合計100点満点で評価してください。

## 基本情報
- 成果物タイトル: [ここに埋め込む]
- 使用プロンプト: [ここに埋め込む。例: news/it.md]
- 対象地域: [ここに埋め込む]
- 対象期間: [ここに埋め込む]
- 想定読者・利用目的: [ここに埋め込む]

## レビュー対象成果物（全文）
[ここに成果物本文を埋め込む]

## レビュー観点（5項目・各20点・合計100点）
[ここに `.claude/skills/research-deliverable-review/references/criteria.md` の絶対パスを埋め込む]を Read し、5 観点のチェック項目・採点目安と「評価調整」をそのまま適用すること。要約・省略・改変しない。

## 総合判定
`.claude/skills/_shared/review-rubrics.yaml` を Read し、`verdict_scales.rank5_100` の bands/meaning に従って S/A/B/C/D を判定すること（点数帯・各段階の対応方針は同ファイルが SoT）。

## 行動原則
`.claude/skills/_shared/review-rubrics.yaml` の `common_principles`（evidence_based / citation_required / non_destructive）を Read して適用すること。

## 出力フォーマット
以下の構造で出力すること:

# リサーチ・情報収集 レビュー結果

## 基本情報
（成果物タイトル / レビュー日 / 使用プロンプト / 対象地域 / 対象期間 / 想定読者・利用目的）

## 総合評価
総合点: XX点 / 100点、判定: X（S/A/B/C/D）

## 観点別採点
| # | 観点 | 配点 | 得点 | 主なコメント |
|---|---|---|---|---|
| 1 | 情報の正確性・信頼性 | 20 | | |
| 2 | 網羅性・カバレッジ | 20 | | |
| 3 | 分析の深度・洞察 | 20 | | |
| 4 | 構成・可読性 | 20 | | |
| 5 | 実用性・アクション接続 | 20 | | |

## 良かった点（Keep）
## 改善提案（Problem / Try）
## 具体的な強化が必要な箇所
| 観点 | 現状 | 不足している点 | 補強案 |
|---|---|---|---|

## 重要チェック項目
| 項目 | 記載 | コメント |
|---|---|---|
| ソースURL明記 | ✅/❌ | |
| 事実と推測の区別 | ✅/❌ | |
| 指定カテゴリ・地域の網羅 | ✅/❌ | |
| 出力フォーマット準拠 | ✅/❌ | |
| So What?（洞察）の記載 | ✅/❌ | |
| 次のアクション提示 | ✅/❌ | |
| 情報の鮮度（対象期間内） | ✅/❌ | |

## 次のアクション推奨
（S/A判定なら「そのまま活用」、B以下なら「改善提案を反映し再生成または手動補完」）

## 補足コメント
```

**上記Markdown出力に加え、レビューエージェントには次の review-record/v1 準拠 JSON も1ブロックとして出力させること**（`.claude/skills/_shared/review-record.schema.json` 参照。Markdownの内容をこのJSONへ機械的に写すだけでよい）:

```
{
  "schema": "review-record/v1",
  "skill": "research-deliverable-review",
  "reviewed_at": "<ISO8601>",
  "target": {"description": "<成果物タイトル>", "path_or_url": "<対象ファイルパスまたはnull>"},
  "verdict": "<S/A/B/C/D>",
  "score": <0-100>,
  "criteria": [
    {"id": "accuracy", "name": "情報の正確性・信頼性", "result": "<得点>", "summary": "<主なコメント>", "source_urls": ["<成果物内で引用されたURL等>"]},
    {"id": "coverage", "name": "網羅性・カバレッジ", "result": "<得点>", "summary": "...", "source_urls": []},
    {"id": "insight", "name": "分析の深度・洞察", "result": "<得点>", "summary": "...", "source_urls": []},
    {"id": "structure", "name": "構成・可読性", "result": "<得点>", "summary": "...", "source_urls": []},
    {"id": "actionability", "name": "実用性・アクション接続", "result": "<得点>", "summary": "...", "source_urls": []}
  ],
  "sources_cited": ["<成果物全体で引用されたURL・出典の一覧>"],
  "summary": "<総合評価の要約1〜数文>",
  "prior_records_referenced": ["<ステップ1で見つけた過去レコードのパス。無ければ空配列>"]
}
```

**該当データが無い場合の例**（対象ファイルパスが不明・過去記録が無い・ある観点に出典URLが無いケース。値を無理に埋めない）:

```
{
  "schema": "review-record/v1",
  "skill": "research-deliverable-review",
  "reviewed_at": "2026-09-14T10:00:00+09:00",
  "target": {"description": "news/it.md 生成分（2026-09-14実行）", "path_or_url": null},
  "verdict": "C",
  "score": 62,
  "criteria": [
    {"id": "accuracy", "name": "情報の正確性・信頼性", "result": "12", "summary": "引用元URLが一部欠落", "source_urls": []},
    {"id": "coverage", "name": "網羅性・カバレッジ", "result": "11", "summary": "指定カテゴリの一部が未収集", "source_urls": []},
    {"id": "insight", "name": "分析の深度・洞察", "result": "13", "summary": "", "source_urls": []},
    {"id": "structure", "name": "構成・可読性", "result": "14", "summary": "", "source_urls": []},
    {"id": "actionability", "name": "実用性・アクション接続", "result": "12", "summary": "", "source_urls": []}
  ],
  "sources_cited": [],
  "summary": "指定カテゴリの一部が未収集。引用元URLの欠落が目立つ。",
  "prior_records_referenced": []
}
```

### ステップ3: 結果の報告と永続化

1. レビューエージェントから返却されたMarkdown結果を、そのままユーザーに表示する。要約や解釈を加えない（レビューの客観性を維持するため）。
2. レビューエージェントが出力した review-record/v1 JSON を `.tmp/` 配下の一時ファイルに UTF-8 で保存し、以下を実行して永続化する:
   ```bash
   python .claude/skills/_shared/scripts/append_review_record.py <一時JSONファイルのパス>
   ```
3. **このスクリプトが成功（書き込み先パスを標準出力）するまで、レビューを完了として報告しない**。検証エラー（必須フィールド欠落等）で失敗した場合は、エラー内容に従ってJSONを修正し再実行する。書き込み先パスを最終報告に含める。

## エラー時の対処

- Agent の起動が失敗した: エラーを伝えて 1 回だけ再試行する。だめなら、このセッションで代わりに採点せず中断して報告する。
- 結果に review-record/v1 の JSON が無い、または JSON の点数や判定が Markdown の観点別採点と合わない: 同じエージェントに、Markdown の採点に合わせた JSON の再出力を 1 回だけ依頼する。直らなければ永続化せず、食い違いをそのまま報告する（呼び出し元が点数を書き換えない）。
- `list_review_records.py` が `NO_PRIOR_RECORDS` を返した: 過去記録なしとして進める。

---

## 注意事項

- **絶対にこのセッション内で直接採点しない**。必ず Agent ツールで別エージェントを起動すること
- S/A判定であればそのままビジネス判断・社内共有に活用してよい旨を伝える。B以下の場合は改善提案を反映して該当プロンプトで再生成、または手動補完するよう案内する
- **強制の限界**: ステップ3の永続化はプロンプト指示によるものであり、`review-gate` 同様に確率的な強制に留まる（決定的な保証ではない）。`append_review_record.py` 自体はスキーマ検証を機械的に行うため、実行さえされれば不正なレコードの書き込みは防げる。

## 更新履歴

- 1.1: 観点 1（情報の正確性と信頼性）に、系列と時点と出典の明記、要約や抽出ツールの出力だけに頼った数値、不在の主張の探索範囲、取得時刻、依頼文の前提の書き写しを加えた。観点 2（網羅性とカバレッジ）に時事の題材を選ぶ前の一次データの確認、観点 3（分析の深度と洞察）に集計の除外条件と窓、部分一致による件数の水増しを加えた。5 観点と評価調整を `references/criteria.md` に分け、重視観点の扱いを決めた。使わない場面、前提条件、使用例、エラー時の対処を足し、データ欠落時の JSON の例に 5 観点を残した。version と更新履歴を追加。
