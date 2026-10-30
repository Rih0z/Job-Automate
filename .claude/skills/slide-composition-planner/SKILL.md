---
name: slide-composition-planner
description: "スライドを作る前に、構成（聴衆・結論・各スライドの主張・根拠・図表・視線の起点・配色の役割）を決め、形式非依存の deck-spec.json として出力する。構成は出典付きのベストプラクティス JSON（slide-best-practices.json）で機械検査する。pptx 生成 skill（anthropic-pptx など）へ deck-spec.json を渡して作らせる前段。Use when the user asks 'スライドの構成を決めて', 'スライドを作る前に構成案を作って', '資料の構成を JSON で', 'deck-spec を作って', 'デザインも考えた構成にして'. 使わない場面: pptx の生成そのもの（生成 skill を使う）、完成した pptx のレビュー（slide-clarity-review）、HTML スライドの生成（slides-pro）。"
allowed-tools: Read Write Glob Grep Bash
argument-hint: "<元資料の絶対パス（任意）> [目的・聴衆・発表時間]"
metadata:
  provenance: domain-prompt
  version: "1.0.0"
---

# スライド構成決定（pptx 生成の前段）

pptx 生成 skill に任せる前に、「誰に・何を・どの順で・どう見せるか」を決めて `deck-spec.json` に固める。**この skill は pptx を作らない。** 作るのは生成 skill（`anthropic-pptx` など）で、`deck-spec.json` のパスを依頼文に添えて渡す。

根拠データ: `.claude/skills/_shared/slide-best-practices.json`（各 practice に出典 URL・著者・機関・原文の抜粋が付く。取得ログは `_shared/slide-sources/fetch-log.json`）。完成後の点検は `slide-clarity-review` が同じデータで行う。

## 入力

目的、聴衆、元資料のパス（あれば）、発表時間または枚数の目安、`palette_ref`（役割→色の JSON のパス。任意）。聴衆と目的が分からなければ、構成に入る前にユーザーへ聞く。

## 手順

1. **結論を決める**: 聴衆に持ち帰ってほしい 1 文を `key_message` にする（結論を先に）。
2. **流れを決める**: 聴衆の課題を主役にし、現状と望ましい姿を対比させる（`storyline`）。最後は望ましい姿と次の行動で終える（`role: closing`）。
3. **スライドに割り当てる**: 1 枚 1 要点。`action_title` は話題名でなく主張の一文にする。要点（`points`）は少数に絞る。
4. **見せ方を決める**: `evidence_type`（図表で示せるものは文章にしない）、`layout_hint`、`focal_element`（最初に視線が向く要素）、`emphasis_role`、`text_size_class`。
5. **色は役割だけで指定する**（下表）。色コードは書かない。`palette_ref` があれば `palette` 検査を通す。
6. **根拠を付ける**: 事実の主張には `content_source`（URL か資料の絶対パス）。意見・提案のスライドだけ `null` でよい。
7. **検査する**（下記コマンド）。落ちた箇所を直して通す。
8. **ユーザーの承認を得てから**、生成 skill へ渡す。

## deck-spec.json

トップ: `audience`, `goal`, `key_message`, `storyline`, `slides[]`, `design`（任意: `palette_ref`, `accent_area_max_pct`, `functional_area_max_pct`）。

| slides[] の項目 | 値 |
|---|---|
| `no` | 1 からの通し番号 |
| `role` | title / agenda / section / content / closing |
| `action_title` | 主張の一文（空不可。長すぎない） |
| `key_message`, `points[]` | そのスライドの要点と、それを支える項目 |
| `evidence_type` | chart / diagram / image / table / quote / list / opinion / proposal |
| `layout_hint` | title / section / content-1col / content-2col / chart / image / closing |
| `content_source` | URL・絶対パス・null（null は opinion / proposal のみ） |
| `focal_element` | title / figure / number / image / none（content では none 不可） |
| `emphasis_role` | focus / neutral / functional / null |
| `text_size_class` | title / body / note（pt は書かない） |

数値の上限（要点数・見出し長など）は `slide-best-practices.json` の `check.threshold` が正で、この表には書かない。

### 最小の例（2 枚抜粋。実際は全枚数を書く）

```json
{
  "audience": "経営会議の出席者", "goal": "来期の投資案を承認してもらう",
  "key_message": "投資すれば 2 年で回収できる", "storyline": "課題 → 解決策 → 根拠 → 次の行動",
  "design": { "palette_ref": null },
  "slides": [
    { "no": 2, "role": "content", "action_title": "現行の手作業が月 80 時間を消費している",
      "key_message": "自動化の余地が大きい", "evidence_type": "chart",
      "points": ["月次集計に 50 時間", "確認作業に 30 時間"], "layout_hint": "chart",
      "content_source": "https://example.com/audit-report", "focal_element": "number",
      "emphasis_role": "focus", "text_size_class": "body" },
    { "no": 8, "role": "closing", "action_title": "来月、試験導入に着手する",
      "key_message": "承認をいただきたい", "evidence_type": "proposal", "points": ["承認の依頼", "試験導入の日程"],
      "layout_hint": "closing", "content_source": null, "focal_element": "title",
      "emphasis_role": "neutral", "text_size_class": "title" }
  ]
}
```

### 色の役割

`focus`（視線を集める強調。面積は小さく）/ `surface-1`（ページの淡い地）/ `surface-2`（カードの地）/ `border` / `text-primary` / `text-secondary`（出典・注記のみ）/ `emphasis-mid`（中間の強調）/ `functional`（意味を担う色。最小限）。役割→色の対応は生成側が持つ。`criteria/palette.example.json` は役割の構造を示す汎用サンプル。

## コマンド（リポジトリのルートから）

```
python .claude/skills/_shared/scripts/validate_slide_data.py deck-spec <deck-spec.json> --practices .claude/skills/_shared/slide-best-practices.json
python .claude/skills/_shared/scripts/validate_slide_data.py palette <palette.json>
```

終了コード 0 で合格。1 は違反（`slide N: <practice id> violated (...)` の形で出る）、2 は読込エラー。

## 機械検査できない観点（作る側のセルフチェック）

`slide-best-practices.json` の `check.method` が `llm` の practice を読み、構成が満たしているかを自分で確かめる（主張の一文になっているか、結論が先か、1 枚 1 要点か、視線の起点が要点と一致するか、色を絞れているか、対比があるか）。ここは自己確認であり、判定は完成後に別エージェントが行う（`slide-clarity-review`）。

## 生成 skill への渡し方

依頼文に `deck-spec.json` の絶対パスを添え、「各スライドの `action_title` を見出しに、`layout_hint` を自分のレイアウトに、`emphasis_role` を自分の配色体系の役割に対応づけて作る」と伝える。語彙が合わない項目は生成側が最も近いものを選ぶ。**ブランドの準拠検査は生成側のゲートで行う**（この skill は関与しない）。生成後は `slide-clarity-review` に渡す。

## エラー時

- 元資料が読めない・空: 構成に入らず、パスの再指定を依頼する。
- 検査が 2 周直しても通らない: 通らない項目と理由をユーザーに示し、基準側を変えるか構成を変えるかを聞く（`slide-best-practices.json` を黙って緩めない）。
- `palette_ref` が無い: 役割名だけで出力し、色の決定は生成側に任せる（その旨を報告する）。
- 検査コマンドが実行できない（python が無い、スクリプトや `slide-best-practices.json` が無い、終了コード 2）: 検査を飛ばして先へ進まない。何が実行できなかったかを報告し、`deck-spec.json` は「未検査」と明記してユーザーに渡す。

## 使用例

「来期の投資案を経営会議で通したい。資料は `C:\docs\plan.md`。8 枚くらい」 → 聴衆と目的を確認し、結論を 1 文にする → 8 枚へ割り当てて `deck-spec.json` を書く → `deck-spec` 検査を通す → 構成をユーザーに見せて承認を得る → 生成 skill に `deck-spec.json` の絶対パスを添えて依頼する。
