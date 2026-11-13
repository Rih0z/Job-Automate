---
name: slide-composition-planner
description: "スライドを作る前に、構成（聴衆・結論・各スライドの主張・根拠・図表・視線の起点・配色の役割）を決め、形式非依存の deck-spec.json として出力する。構成は出典付きのベストプラクティス JSON（slide-best-practices.json）で機械検査する。pptx 生成 skill（標準の pptx skill など）へ deck-spec.json を渡して作らせる前段。Use when the user asks 'スライドの構成を決めて', 'スライドを作る前に構成案を作って', '資料の構成を JSON で', 'deck-spec を作って', 'デザインも考えた構成にして'. 使わない場面: pptx の生成そのもの（生成 skill を使う）、完成した pptx のレビュー（slide-clarity-review）、HTML スライドの生成（slides-pro）。"
allowed-tools: Read Write Glob Grep Bash
argument-hint: "<元資料の絶対パス（任意）> [目的・聴衆・発表時間]"
metadata:
  provenance: domain-prompt
  version: "1.3.0"
---

# スライド構成決定（pptx 生成の前段）

pptx 生成 skill に任せる前に、「誰に・何を・どの順で・どう見せるか」を決めて `deck-spec.json` に固める。**この skill は pptx を作らない。** 作るのは生成 skill（標準の `pptx` skill、または組織の標準テンプレート用の作成 skill など）で、`deck-spec.json` のパスを依頼文に添えて渡す。

根拠データ: `.claude/skills/_shared/slide-best-practices.json`（各 practice に出典 URL・著者・機関・原文の抜粋が付く。取得ログは `_shared/slide-sources/fetch-log.json`）。完成後の点検は `slide-clarity-review` が同じデータで行う。

依存: Python 3（標準ライブラリのみ）。検査は `.claude/skills/_shared/scripts/validate_slide_data.py`（`slide_checks.py` を使う）。別のプロジェクトでは、この skill と `_shared/` の基準データ・スクリプトを同じ相対パスに置き、そのプロジェクトのルートから実行する。

## 入力

目的、聴衆、元資料のパス（あれば）、発表時間または枚数の目安、`palette_ref`（役割→色の JSON のパス。任意）。聴衆と目的が分からなければ、構成に入る前にユーザーへ聞く。

## 手順

1. **聴衆と結論を決める**: 聴衆が普段使う道具・環境（v3 の `narrative.audience_profile.uses`）、前提知識と持っている疑問（`knowledge`・`question`）を書く。持ち帰ってほしいことを 1〜3 個（`narrative.takeaways`）にし、その要約の 1 文を `key_message` にする（結論を先に）。
2. **流れを決める**: 聴衆の課題を主役にし、現状と望ましい姿を対比させる（`storyline`）。本編の最後（参考の区切りより前）は、望ましい姿と次の行動で終える（`role: closing`。呼びかけ専用のスライドを置くなら closing より前）。補足・付録は参考の区切りの後ろに置く。章ごとの話題は 1 つにし、同じ話題を 2 つの章で説明しない（v2 の `sections`・`role: appendix`。下の「設計図 v2 の項目」）。**本編の各スライドが、どの持ち帰りを支えるかを決める**（v3 の `supports`）。どれも支えないスライドや章は、付録にするか削る。
3. **スライドに割り当てる**: 1 枚 1 要点。`action_title` は話題名でなく主張の一文にする。要点（`points`）は少数に絞る。本文のスライドには、そのスライドで何を示すかと前提を 1 文で書き（v2 の `intent`）、改善の前後を示す例・聴衆が使う素材・専門的な語は、下の「設計図 v2 の項目」の形で書く。章の始めと、前のスライドの成果物を使うスライドには、前とのつながりを画面に載せる 1 文を書く（v3 の `bridge`・`builds_on`）。同じ型のスライドを 3 回以上使うなら、3 回目からはその回で新しく示す点を書く（v3 の `repeat_pattern`・`new_point`）。下の「設計図 v3 の項目」。
4. **見せ方を決める**: `evidence_type`（図表で示せるものは文章にしない）、`layout_hint`、`focal_element`（最初に視線が向く要素）、`emphasis_role`、`text_size_class`。次の運用上の注意を守る（出典のない運用規則。2026-11 の実測で、作った資料にこの問題が出たため）。
   - **強調は、その見出しの主張の中心に向ける**: `emphasis_role: focus` を付けるとき、`key_message` に「どの要素を強調するか」を名指しで書く。順番や全体を主張するスライドで、最初の項目だけを強調しない。強調した要素には、色以外の手がかり（太字・番号・短い語）も添える
   - **図の型を、内容に合わせて変える**: 同じ見せ方（カード・表など）を 3 枚以上続けない。順序は図（シェブロン・時系列）、比較は表、数値は大数字、と使い分ける。順序や流れを、表で済ませない
   - **1 つの図の中の文字は短く**: 18pt 以上で、折り返しが不自然にならない長さ（1 項目 15 字前後）に収める。収まらなければ、項目を減らすかスライドを分ける
   - **空白を作りすぎない**: 要素が少ないスライドは、図を大きくするか、他のスライドと統合する
   - **空の枠を残さない・重ねない**: 使わないプレースホルダーは作らない（消す）。表は折り返しを見込んだ高さにし、下の図形に重ならない位置に置く（完成後の機械検査が候補として挙げる）
5. **色は役割だけで指定する**（下表）。色コードは書かない。`palette_ref` があれば `palette` 検査を通す。
6. **根拠を付ける**: 事実の主張には `content_source`（URL か資料の絶対パス。複数あるときは文字列の配列）。意見・提案のスライドだけ `null` でよい。外部の根拠は、完成したスライドの同じページに所在（URL・文献名・資料名）を載せる前提で書く。
7. **検査する**（下記コマンド）。落ちた箇所を直して通す。
8. **ユーザーの承認を得てから**、生成 skill へ渡す（生成 skill がアウトラインの承認を取る場合は、この承認をそこに統合し、承認は 1 回にする）。

## deck-spec.json

トップ: `audience`, `goal`, `key_message`, `storyline`, `slides[]`, `design`（任意: `palette_ref`, `accent_area_max_pct`, `functional_area_max_pct`）。任意: `spec_version`（1・2・3。無ければ 1。新しく作る設計図は 3）、`sections[]`（`id`・`theme`・v3 では任意の `kind`）、`narrative`（v3）、`exhibits[]`（`id`・`kind`・`full_text_at`）、`glossary[]`（`term`・`definition`・`first_slide`）。

**設計図 v2**（`spec_version: 2`）: 本文のスライド（`role: content`）で `intent` を必須にし、書いた任意項目の整合を検査する（項目と検査は下の「設計図 v2 の項目」）。`spec_version` 1 の設計図は、従来どおりの検査だけを行う。

| slides[] の項目 | 値 |
|---|---|
| `no` | 1 からの通し番号 |
| `role` | title / agenda / section / content / closing / appendix（`section` には任意で `kind`: main / reference） |
| `action_title` | 主張の一文（空不可。長すぎない） |
| `key_message`, `points[]` | そのスライドの要点と、それを支える項目 |
| `evidence_type` | chart / diagram / image / table / quote / list / opinion / proposal |
| `layout_hint` | title / section / content-1col / content-2col / chart / image / closing |
| `content_source` | URL・絶対パス・それらの配列・null（null は opinion / proposal のみ） |
| `intent`, `section`, `example`, `exhibit_ref` | 任意（v2 では content の `intent` が必須）。下の「設計図 v2 の項目」 |
| `focal_element` | title / figure / number / image / none（content では none 不可） |
| `emphasis_role` | focus / neutral / functional / null |
| `text_size_class` | title / body / note（pt は書かない） |

数値の上限（要点数・見出し長など）は `slide-best-practices.json` の `check.threshold` が正で、この表には書かない。

### 設計図 v2 の項目

`spec_version: 2` で使う。例や付録を含まない資料には、該当する項目を書かなくてよい。

| 項目 | 書くこと | 検査 |
|---|---|---|
| `sections[]`（`id`・`theme`）と各スライドの `section` | 章ごとの話題を 1 つ。2 回目以降は「第 N 章の手順で行う」のように参照だけにする | 話題の重複・存在しない章の参照 |
| `intent`（`role: content`） | そのスライドで何を示すかと前提を 1 文。章の始め・例・数値のスライドは副題か導入文として載せる | 空なら違反（v2 で必須） |
| `example`（`id`・`pattern`・`steps`・`effect`・`cause`・`conditions`） | 改善の前後（before-after）か良い例と悪い例（good-bad）。`steps` は before／result／after／effect の配列。`effect` は何が良くなったか、`cause` は結びつける原因・対策を 1 つ、結果を示すスライドの `conditions` は対象の数・手順・環境 | 前が後より先・効果あり・原因が 1 つ・結果には条件・before-after には result |
| `exhibits[]`（`id`・`kind`・`full_text_at`）と `exhibit_ref` | 聴衆が使う素材（依頼文・コマンド・設定・コード・テンプレート・計算式）の全文の置き場所（スライド番号・notes・配布物の名前）。説明のスライドには効く部分の抜粋だけを置き、何に効くかを書く | 参照先の有無・置き場所の空 |
| `role: appendix` と `role: section`・`kind: reference` | 補足・付録と、その前の参考の区切り | 付録の後ろに本文・まとめが無い・区切りはまとめの後で付録の前・付録の無い区切りは違反 |
| `glossary[]`（`term`・`definition`・`first_slide`） | 聴衆の前提知識から見て専門的な語と、その説明と初出のスライド | 初出より前のスライドで使っていないか |

`intent`・`cause`・`conditions`・`exhibits` は、設計図の検査だけを行う運用上の注意で、完成後の点検の点数には入れない（2026-11 の検証で、完成した資料での判定が点検員によって割れたため）。同じ話題は 1 か所・前後の順序・付録の順序は、完成後も `slide-clarity-review` が点検する。

v2 の例（抜粋。前後の対と付録）:

```json
{
  "spec_version": 2,
  "sections": [{"id": "s1", "theme": "申請画面の見直し"}],
  "exhibits": [{"id": "x1", "kind": "設定", "full_text_at": 9}],
  "glossary": [{"term": "差し戻し", "definition": "申請を申請者に返して直させること", "first_slide": 2}],
  "slides": [
    {"no": 3, "role": "content", "section": "s1", "intent": "見直し前の画面で何が起きたかを示す",
     "example": {"id": "e1", "pattern": "before-after", "steps": ["before", "result"], "conditions": "4 部署・1 か月", "cause": "必須の欄の配置"}},
    {"no": 4, "role": "content", "section": "s1", "intent": "見直し後に何が良くなったかを示す", "exhibit_ref": "x1",
     "example": {"id": "e1", "steps": ["after", "effect"], "effect": "差し戻しが半分になった", "cause": "必須の欄の配置"}},
    {"no": 7, "role": "closing"}, {"no": 8, "role": "section", "kind": "reference"}, {"no": 9, "role": "appendix"}
  ]
}
```

（例では各スライドの共通の項目 `action_title` 等を省いている。実際は全項目を書く）

### 設計図 v3 の項目（話の組み立て）

`spec_version: 3` = v2 の全検査 ＋ 下表。発表全体の筋（誰に・何を持ち帰らせ・各スライドがそのどれを支え・前とどうつながるか）を設計図に書かせ、スライドだけで話が通るようにする。出典の無い運用上の規則で（2026-11 に、AI が作った資料を人が手直しした差分から導いた）、`slide-best-practices.json` には入れず、点数にも入れない。検査は書き手が設計図を正直に書くことが前提で、脇道そのものを見つけるのではない。完成後のずれは `slide-clarity-review` の話の流れの指摘（`story_findings`）が拾う。

章の扱い: v3 では `sections[]`（`id`・`theme`・任意の `kind`: main / reference。無ければ main）が 1 個以上必須。content・closing・appendix・section のスライドは `section` 必須。区切りスライドの `kind`（無ければ main）は、その章の `kind` と一致させる。「章の最初のスライド」は、直前の content と `section` が異なる content（資料で最初の content は除く）。

| 項目 | 書くこと | 検査（括弧は構造の id） |
|---|---|---|
| `narrative.audience_profile.uses`（必須）・`knowledge`・`question`（任意） | 聴衆が普段使う道具・環境 / 前提知識 / 持っている疑問 | `uses` が空（audience-profile） |
| `narrative.takeaways[]`（`id`・`text`）・`thread`（任意） | 持ち帰り 1〜3 個（`key_message` はその要約）/ 全体を通す題材 | 個数・id 重複（takeaways） |
| `supports`（content で必須） | 支える takeaway の id の配列。導入・前提は `["premise"]`、呼びかけ専用のスライドは `["cta"]`（どちらも単独で） | 空・未知の id・どの content にも支えられない takeaway・premise が持ち帰りのスライドより後・混在（supports-takeaway）。closing の `supports` は任意で、書くなら takeaway の id。付録は検査しない |
| `cta` の位置 | — | closing より後の呼びかけ（cta-before-closing） |
| `builds_on`・`bridge`（content だけで検査） | 前のどのスライドの成果物を使うか（番号）/ 前とのつながりを画面に載せる 1 文 | 前を指さない builds_on。章の最初のスライドと builds_on を持つスライドで bridge が空（bridge） |
| `repeat_pattern`・`new_point`（content だけで数える） | 同じ型のスライドの型名（`example.pattern` とは別物）/ その回で新しく示す点 | 同じ型の 3 枚目以降で new_point が空（pattern-repeat） |
| 目次の `agenda_sections` | その目次に載せる章の id | 目次があるときだけ。空・未知や参考の章・本編の章の漏れ（agenda-sections）。目次の文言（`points`）は照合しない |

`intent` と `bridge` の分担: `intent` はこのスライドで示すことと前提、`bridge` は前の章・前の成果物とのつながり。画面では 1 文にまとめてよい（例:「第 1 章で作った依頼文を使い、レビューを別の会話で行う」）。設計図には両方書く。

運用上の注意（出典なし。手直しの差分から）:
- 例の結果が章の主張と逆向きになるもの（但し書き・例外）は本編に置かず、ノートか付録に移し、本編には 1 行の注にとどめる
- 依頼文などの「やること」を先に見せ、「なぜ効くか」はその後に置く
- 例に出す道具の名前は `uses` から選ぶ（聴衆が普段使わない道具で例を示さない）
- 前提・条件・つながりは画面に書く。ノートは補足だけにし、ノートを読まないと主張が成り立たない形にしない
- スライドや章を削ったら、目次（`agenda_sections`）と冒頭の概要スライドも直す

v3 の例（抜粋）:

```json
{
  "spec_version": 3,
  "narrative": {"audience_profile": {"uses": "表計算ソフトと社内のチャット", "knowledge": "AI チャットは使ったことがある", "question": "どう頼めば確かな答えが返るか"},
                "takeaways": [{"id": "t1", "text": "依頼を決まった項目にする"}, {"id": "t2", "text": "別の会話でレビューする"}],
                "thread": "出張先の店選び"},
  "sections": [{"id": "s1", "theme": "依頼の形"}, {"id": "s2", "theme": "レビューの分け方"}, {"id": "r1", "theme": "参考", "kind": "reference"}],
  "slides": [
    {"no": 2, "role": "agenda", "agenda_sections": ["s1", "s2"]},
    {"no": 3, "role": "content", "section": "s1", "supports": ["premise"], "intent": "題材と条件を示す"},
    {"no": 4, "role": "content", "section": "s1", "supports": ["t1"], "intent": "依頼文を項目にした結果を示す", "repeat_pattern": "why-it-works"},
    {"no": 5, "role": "content", "section": "s2", "supports": ["t2"], "builds_on": 4, "intent": "レビューの頼み方を示す",
     "bridge": "第 1 章で作った依頼文を使い、レビューを別の会話で行う"},
    {"no": 6, "role": "content", "section": "s2", "supports": ["cta"], "intent": "相談の窓口を示す"},
    {"no": 7, "role": "closing", "section": "s2", "supports": ["t1", "t2"]},
    {"no": 8, "role": "section", "section": "r1", "kind": "reference"}, {"no": 9, "role": "appendix", "section": "r1"}
  ]
}
```

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

### 色と見せ方の原則（構成の段階で決めておく）

根拠の出典と抜粋は `slide-best-practices.json` の各 practice にある。数値の基準もそちらが正。

- **土台はグレーの階調、色は要点にだけ使う**（`neutral-base`、`color-restraint`）。重要でない情報はグレーに落とし、`emphasis_role: focus` は要点のスライドにだけ付ける。
- **意味を色だけで伝えない**（`color-not-sole`）。比較・良否・凡例には、形・文字・位置などの手がかりを添える。赤と緑のように見分けにくい組み合わせは避ける。
- **背景は彩度を抑え、とても明るいか暗い色**にする（`calm-background`）。
- **視線の起点を 1 つに絞る**（`focal-point`）。`focal_element` に、最初に見てほしい要素を決める。
- **文字は小さくしすぎず、明暗差を確保する**（`min-font`、`contrast-measured`）。`text_size_class` で区分だけ決め、pt は生成側に任せる。
- 色の対応表（`palette_ref`）がある場合は、`palette` 検査で文字と地の明暗差を確かめてから渡す。

## コマンド（リポジトリのルートから）

```
python .claude/skills/_shared/scripts/validate_slide_data.py deck-spec <deck-spec.json> --practices .claude/skills/_shared/slide-best-practices.json
python .claude/skills/_shared/scripts/validate_slide_data.py palette <palette.json>
```

終了コード 0 で合格。1 は違反（`slide N: <practice id> violated (...)` の形で出る。設計図 v2・v3 の構造の誤りは `slide 3: intent missing (purpose-and-premise)`・`slide 5: bridge missing (bridge)` のように、関係する観点の id を括弧で添えて出る）、2 は読込エラー。

## 機械検査できない観点（作る側のセルフチェック）

`slide-best-practices.json` の `check.method` が `llm` の practice を読み、構成が満たしているかを自分で確かめる（主張の一文になっているか、結論が先か、1 枚 1 要点か、視線の起点が要点と一致するか、色を絞れているか、対比があるか、同じ話題を 1 か所で説明しているか、例と条件が一致するか）。`applies_when.deck` を持つ practice は、資料がその条件に当たるときだけ確かめる。ここは自己確認であり、判定は完成後に別エージェントが行う（`slide-clarity-review`）。

## 生成 skill への渡し方

依頼文に `deck-spec.json` の絶対パスを添え、「各スライドの `action_title` を見出しに、`layout_hint` を自分のレイアウトに、`emphasis_role` を自分の配色体系の役割に対応づけて作る」と伝える。語彙が合わない項目は生成側が最も近いものを選ぶ。**ブランドの準拠検査は生成側のゲートで行う**（この skill は関与しない）。生成後は `slide-clarity-review` に渡し、日本語の文面は続けて `slide-japanese-review` で点検する（5 段階の流れの全体は `docs/slide-creation-kit.md`。その文書が無い環境では読み飛ばす）。

## エラー時

- 元資料が読めない・空: 構成に入らず、パスの再指定を依頼する。
- 検査が 2 周直しても通らない: 通らない項目と理由をユーザーに示し、基準側を変えるか構成を変えるかを聞く（`slide-best-practices.json` を黙って緩めない）。
- `palette_ref` が無い: 役割名だけで出力し、色の決定は生成側に任せる（その旨を報告する）。
- v2・v3 の構造の誤り（`slide 3: intent missing (purpose-and-premise)`・`slide 4: supports missing (supports-takeaway)` など）: 括弧の観点の id を手がかりに、その項目を書き足すか直す。例を含まない資料で `example` 等の誤りが出たら、項目自体を消す（書かなければ検査されない）。`supports-takeaway` で落ちたスライドは、支える持ち帰りを書けないなら付録に移すか削る（持ち帰りを増やして通さない）。
- 検査コマンドが実行できない（python が無い、スクリプトや `slide-best-practices.json` が無い、終了コード 2）: 検査を飛ばして先へ進まない。何が実行できなかったかを報告し、`deck-spec.json` は「未検査」と明記してユーザーに渡す。

## 使用例

「来期の投資案を経営会議で通したい。資料は `C:\docs\plan.md`。8 枚くらい」 → 聴衆と目的を確認し、結論を 1 文にする → 8 枚へ割り当てて `deck-spec.json` を書く → `deck-spec` 検査を通す → 構成をユーザーに見せて承認を得る → 生成 skill に `deck-spec.json` の絶対パスを添えて依頼する。

## 更新履歴

- 1.3.0（2026-11-12）: 設計図 v3（聴衆の道具・持ち帰り 1〜3 個・各スライドが支える持ち帰り・前とのつながり・同じ型の繰り返し・目次と章の一致・呼びかけの位置）と、その構造の検査を追加。AI が作った資料を人が手直しした差分（脇道の章・逆向きの例・同じ型の 3 回目の削除、前の章の成果物を次の章で使う流れ、まとめを最後に）から導いた
- 1.2.0（2026-11-06）: 設計図 v2（章立て・目的と前提・例の型・素材の置き場所・用語の一覧・付録の順序）と、その構造の検査を追加。本編の最後を「参考の区切りより前」とした。空の枠と表の高さの運用上の注意を追加
- 1.1.0: このリポジトリに追加
