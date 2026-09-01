---
name: review-gate
description: "工程別レビューゲート。仕様・設計・テスト・実装・リリースの各工程が1つ進むごとに、成果物を別エージェントにJSON定義の観点でレビューさせ、PASSするまで次工程に進ませない品質ゲート。レビュアーが観点定義自体の抜け漏れも指摘し、criteria JSONを育てていく。Use when the user asks to '工程レビューして', 'レビューゲートを通して', '仕様/設計/テスト/実装をレビューして', or when a development stage (spec/design/test/implementation/release) has just been completed and needs independent review before proceeding."
---

# review-gate — 工程別レビューゲート

各工程の成果物は、**次の工程に進む前に必ず別エージェントのレビューを受ける**。自分の成果物を自分でレビューして通過扱いにすることを禁止する（self-review 禁止）。

## 工程と観点ファイルの対応

| 工程 | タイミング | 観点ファイル |
|---|---|---|
| 仕様 | 仕様書を書いた/変えた直後、テスト作成前 | [criteria/spec.json](criteria/spec.json) |
| 設計 | 設計・スキーマ・APIを書いた/変えた直後、実装前 | [criteria/design.json](criteria/design.json) |
| テスト | テストを書きRed確認直後、実装(Green)前 | [criteria/test.json](criteria/test.json) |
| 実装 | Green+リファクタ完了直後、コミット前 | [criteria/implementation.json](criteria/implementation.json) |
| リリース | デプロイ・本番反映の直前 | [criteria/release.json](criteria/release.json) |

## 手順

1. 該当工程の criteria JSON を読む。
2. `Agent` ツール(`general-purpose`、`run_in_background: false`)で独立レビュアーを起動する。レビュアーには対象ファイルと観点定義のパスだけを渡し、呼び出し元セッションの実装意図・設計判断は渡さない。プロンプト:

   ```
   あなたは独立レビュアー。次の観点定義に従い、対象を批判的にレビューせよ。
   観点定義: <criteria JSONのパス。読み込ませる>
   レビュー対象: <対象ファイルのパス一覧。文脈に必要な仕様書・設計書も含める>
   まず対象全体を一度通読し、criterion単位の採点に入る前に全体として破綻がないか
   (目的と実装の乖離・致命的な欠落等)を把握せよ(個別criterionから先に読むと、
   最初に見た項目に評価が引きずられるため、全体像の把握を先に行う)。
   その上で各criterionを checks に沿って検証し、weightに基づき100点満点で採点。
   甘い採点を禁止する。判断に迷ったら減点し findings に書く。
   プロジェクトに該当しない criterion は N/A とし、残りの weight で按分して100点換算する。
   さらに「この観点定義自体に抜けている観点はないか」を考え、あれば missing_perspectives に提案せよ。
   出力は次のJSONのみ(説明文なし):
   {
     "stage": "...",
     "score": 0-100,
     "verdict": "PASS" | "FAIL",
     "must_pass_failures": ["criterion_id", ...],
     "findings": [{"criterion_id": "...", "severity": "high|medium|low", "comment": "...", "location": "file:line"}],
     "missing_perspectives": [{"proposed_criterion": "...", "reason": "..."}]
   }
   ```

3. **判定**: must_pass の criterion がすべて合格、かつ score ≥ pass_rule.min_score で PASS。
   - FAIL → findings を修正して同じ工程を再レビュー。PASSするまで次工程に進まない。
   - PASS → 次工程へ。コミットメッセージ末尾に `review-gate:<stage> PASS <score>` を1行入れる。
4. **観点の自己更新**: レビュアーの `missing_perspectives` に妥当な提案があれば、または開発中に観点の抜け漏れに気づいたら、その場で criteria JSON に criterion を追加してコミットする(weightは既存とのバランスで調整し合計100を維持)。スキルは育てるもの。

   **観点の自己検証 (2026-08-31 追加)**: criteria JSON の checks を「厳格」と称する前に、意図的に劣化させたサンプル(基準を満たさないよう壊した対象)を実際にレビュアーへ通し、当該 criterion が FAIL することを確認する。FAIL しない check は基準が緩すぎるため、checks の記述を締め直してからコミットする。**孤立チェックの点検 (2026-09-01 追加)**: 上記に加え、criteria JSON 内の各 criterion が実際に score/verdict へ反映されているか（採点ロジックから参照されない孤立した check がないか）も定期的に確認する。checks を追加・変更した際、それが `weight` 計算や `must_pass` 判定のどちらにも紐付いていなければ、レビュアーがそのcriterionを検証しても結果が採点に反映されない不整合となる。

## 運用ノート

- **プロジェクトへの導入**: この skill をプロジェクトの `.claude/skills/` にコピーし、criteria JSON にそのプロジェクト固有の観点(ドメイン固有のセキュリティ要件・設計テーマ等)を追記して使う。汎用観点のまま使うより精度が大きく上がる。
- レビュー対象が小さい変更(typo・文言修正)でも工程をまたぐなら省略しない。ゲートを飛ばしてよい例外は docs 以外に影響しない誤字修正のみ。
- **PASS後のfindings対応**: PASSした上で残ったfindingsを修正する編集が「レビュアーの指摘をそのまま反映するだけで新しい意思決定を含まない」場合、即時の再レビューは不要。次にその工程を通るときのレビューで検証する(無限ループ防止)。新しい判断を足す修正はこの例外に当たらない。
- レビュアーには結論だけでなく location を出させ、修正を機械的に適用できるようにする。
- 同一工程で3回FAILしたら、観点かレビュー粒度に問題がある可能性を疑い、ユーザーに相談する。
- 単一セッションでの開発フロー全体は `single-session-tdd` skill、3ターミナル分離で回す場合は `three-agent-tdd-workflow` skill を参照。
