---
name: slide-clarity-review
description: "完成した .pptx の分かりやすさ（主張と構成・テキスト量・視覚設計・根拠と図表・可読性）を、出典付きのベストプラクティス JSON で採点し、修正案（fixes）を出して直させる。判定は別エージェントが行う（自己レビューしない）。本 skill や slide-composition-planner を通していない既存の pptx にも使える。Use when the user asks 'pptx の分かりやすさをレビューして', 'スライドを点検して修正して', '完成したスライドのデザインを評価して', 'スライドの読みやすさを直して'. 使わない場面: スライドの新規作成（生成 skill）、構成を作る前の検討（slide-composition-planner）、HTML スライドのレビュー（review-slides）。"
disable-model-invocation: true
allowed-tools: Read Write Glob Grep Bash Agent
argument-hint: "<レビュー対象 .pptx の絶対パス>"
metadata:
  provenance: domain-prompt
  version: "1.0.0"
---

# 完成スライドの分かりやすさレビュー（点検 → 修正 → 再点検）

対象: $ARGUMENTS（.pptx の絶対パス）

> **判定は別エージェント（`readonly-reviewer`）に任せる。** 現在のセッションで採点しない。作成の意図・会話履歴は渡さない。レビュアーはファイルを書き換えない。修正は作成側セッションが、そのスライドを作った生成 skill（`anthropic-pptx` など）で行う。

根拠データ: `.claude/skills/_shared/slide-best-practices.json`（出典 URL・著者・機関・原文の抜粋つき）。観点と配点: `criteria/clarity.json`（5 軸・各 20 点）。ランクの意味: `.claude/skills/_shared/review-rubrics.yaml` の `rank5_100`。行動原則（証拠主義・引用義務・非破壊）は同ファイルの `common_principles` を適用する。

依存: python-pptx（`pip install python-pptx`）。画像化（LibreOffice・pdftoppm）は任意。無ければ構造とテキストだけで点検し、結果の limitations に記録する。

## 手順（リポジトリのルートから実行）

1. **事実の抽出**: `python .claude/skills/slide-clarity-review/scripts/extract_deck.py <deck.pptx> -o <作業dir>/deck-facts.json`。スライド毎に次を得る。
   - 内容: 見出し・本文量・箇条書き数・段落テキスト・画像数。
   - 文字サイズ: 明示指定された最小値。
   - 配置: トップレベル図形の位置と大きさ（インチ）、左端の種類数。
   - 色: 明示された色の種類数、文字色と背景色が両方明示された組の最小コントラスト比。
   - 取れないもの: 継承されたフォントと色、テーマ色（解決しない）、グループ内の座標、描画結果。limitations に検査できた割合（`font checked` / `color checked` / `color theme-based`）が出る。**描画した画像は作らない**（見た目の最終確認は人が行う）。
2. **機械検査**: `python .claude/skills/slide-clarity-review/scripts/check_deck.py <作業dir>/deck-facts.json --practices .claude/skills/_shared/slide-best-practices.json -o <作業dir>/auto-results.json`（違反があれば終了コード 1）。
3. **別エージェントで観点判定**: `readonly-reviewer` を起動し、下記の入力だけを渡す。
   - `deck-facts.json`（`shapes` の位置・大きさ・塗りを、整列・余白・視線の起点の判定に使わせる）、`auto-results.json`（画像があれば追加）
   - `clarity.json` の軸（id・title・practice_ids）と、軸が参照する `method: llm` の practice の `id` / `title` / `rule` / `check.how`（severity は渡さない）
   - 返却形式: `{"axes":[{"id","score","citations":["slide 3: …"]}],"llm_results":[{"practice_id","passed"}],"fixes":[{"slide","practice_id","problem","fix"}]}`。各軸 0〜20 点、citations は成果物内の記述の引用を最低 1 つ。判定できない観点は passed を false にし、理由を fixes に書く。
4. **検査とゲート判定**: reviewer の JSON を保存し、`python .claude/skills/slide-clarity-review/scripts/finalize_review.py --deck <deck.pptx> --auto <作業dir>/auto-results.json --review <作業dir>/reviewer.json --practices .claude/skills/_shared/slide-best-practices.json --clarity .claude/skills/slide-clarity-review/criteria/clarity.json --write`。
   - 終了コード 3: reviewer の出力が不正（軸の欠落・点数範囲外・citations 空・llm 観点の判定漏れ）。標準エラーの理由を添えて再出力を依頼する。
   - 0=PASS / 1=FAIL。`--write` で `.claude/review-history/slide-clarity-review/` に record が保存される。
5. **修正**: FAIL なら、`fixes` と `auto-results.json` の違反を、生成 skill で該当スライドに適用する。適用後は手順 1 からやり直す。**修正→再点検は最大 2 回**（合計 3 回まで）。2 回直しても FAIL なら止めて、残った違反をユーザーに報告する。

### reviewer の返却例（3 軸抜粋）

```json
{
  "axes": [
    {"id": "ax-message", "score": 15, "citations": ["slide 3: 見出し「売上の推移」は話題名で主張になっていない"]},
    {"id": "ax-design", "score": 17, "citations": ["slide 5: 左端が揃っていない図が 2 つある"]},
    {"id": "ax-legibility", "score": 20, "citations": ["slide 2: 本文は明示指定で十分な大きさ"]}
  ],
  "llm_results": [{"practice_id": "assertion-title", "passed": false}],
  "fixes": [{"slide": 3, "practice_id": "assertion-title", "problem": "見出しが話題名",
             "fix": "「売上は 2 年で 2 割伸びた」のように結論の一文にする"}]
}
```

実際は 5 軸すべてと、軸が参照する llm 観点すべての判定が要る（足りないと手順 4 で終了コード 3）。

## 判定の定義

- ゲート: must の機械検査違反が 1 件でもある、または llm 観点の must が不合格、または総合点が 79 点以下なら FAIL。
- ランクはゲートと別: 95 点でも must 違反があれば「ランク S・FAIL」と両方を報告する。
- `verdict` の PASS / FAIL は修正ループのゲート結果であり、`review-rubrics.yaml` の点数ランクの scale とは別物（ランクは summary に書く）。
- severity は `slide-best-practices.json` の定義が正。reviewer の申告は使わない。
- 二次資料のみを根拠とする practice は should 止まり。出力では「secondary（未照合）」と区別して示す。

## 軸

`criteria/clarity.json` が正。①主張と構成 ②テキスト量と読みやすさ ③視覚設計（焦点・色・余白・整列と反復） ④根拠と図表 ⑤可読性（コントラスト・文字サイズ）。デザインは ③ と ⑤ で採点する。配色や書式のブランド準拠は生成側のゲートで検査する（この skill では扱わない）。

## 出力

ユーザーへの報告: ゲート結果とランク、軸別の得点、違反の一覧（スライド番号・practice id・出典 URL）、適用した修正、limitations。reviewer の結果を要約し直して緩めない。

## エラー時

| 状況 | 対処 |
|---|---|
| .pptx が開けない・存在しない | 実行せず、正しい絶対パスを求める |
| python-pptx が無い | インストールを案内して停止する（代替の推測採点はしない） |
| `readonly-reviewer` を起動できない | `general-purpose` で再試行し、prompt に「ファイルを作成・変更・削除しない」と明記する。それでも失敗したら未実施と報告し、現セッションで代替採点しない |
| 画像化できない | 構造とテキストだけで点検し、limitations に「描画未確認」と書く |
| スクリプトが実行できない（python が無い、`slide-best-practices.json` が無い、終了コード 2） | 点検を飛ばさない。実行できなかった内容を報告して停止する |

## 使用例

「`C:\decks\sales2025.pptx` の分かりやすさを点検して直して」 → 事実の抽出 → 機械検査（違反 3 件）→ `readonly-reviewer` が 5 軸を採点（ランク B・FAIL）→ `fixes` を生成 skill で 3 枚に適用 → 再抽出から再点検 → PASS → record を保存して報告。
