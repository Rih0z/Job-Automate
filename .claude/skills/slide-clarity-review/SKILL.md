---
name: slide-clarity-review
description: "完成した .pptx の分かりやすさ（主張と構成・テキスト量・視覚設計・根拠と図表・可読性）を、出典付きのベストプラクティス JSON で採点し、修正案（fixes）を出して直させる。判定は別エージェントが行う（自己レビューしない）。本 skill や slide-composition-planner を通していない既存の pptx にも使える。Use when the user asks 'pptx の分かりやすさをレビューして', 'スライドを点検して修正して', '完成したスライドのデザインを評価して', 'スライドの読みやすさを直して'. 使わない場面: スライドの新規作成（生成 skill）、構成を作る前の検討（slide-composition-planner）、HTML スライドのレビュー（review-slides）、スライドの文面の日本語の点検（slide-japanese-review）。"
disable-model-invocation: true
allowed-tools: Read Write Glob Grep Bash Agent
argument-hint: "<レビュー対象 .pptx の絶対パス>"
metadata:
  provenance: domain-prompt
  version: "1.3.0"
---

# 完成スライドの分かりやすさレビュー（点検 → 修正 → 再点検）

対象: $ARGUMENTS（.pptx の絶対パス）

> **判定は別エージェント（`readonly-reviewer`）に任せる。** 現在のセッションで採点しない。作成の意図・会話履歴は渡さない。レビュアーはファイルを書き換えない。修正は作成側セッションが、そのスライドを作った生成 skill（標準の `pptx` skill、または組織の標準テンプレート用の作成 skill など）で行う。

根拠データ: `.claude/skills/_shared/slide-best-practices.json`（出典 URL・著者・機関・原文の抜粋つき）。観点と配点: `criteria/clarity.json`（5 軸・各 20 点）。ランクの意味: `.claude/skills/_shared/review-rubrics.yaml` の `rank5_100`。行動原則（証拠主義・引用義務・非破壊）は同ファイルの `common_principles` を適用する。

移植するときの前提: この skill は同じリポジトリの `.claude/skills/_shared/`（`slide-best-practices.json`・`slide-sources/`・`review-rubrics.yaml`・`review-record.schema.json`・`scripts/` の `slide_checks.py`・`append_review_record.py`）を使い、コマンドはリポジトリのルートから実行する前提で書いている。別のプロジェクトへ入れる時は、これらを同じ相対パスに置く（一覧は `docs/slide-creation-kit.md` の「手でコピーする」。その文書が無い環境では、この段落の一覧に従う）。点検員の定義 `readonly-reviewer` が無ければ `general-purpose` に「ファイルを作成・変更・削除しない」と明記して使う。試験は `python .claude/skills/_shared/scripts/test_slide_skills.py`。

依存: 抽出（`extract_deck.py`）は標準ライブラリのみ。試験の fixture 作成には python-pptx（`pip install python-pptx`）。画像化（LibreOffice で PDF にし、poppler の pdftoppm で画像にする。PowerPoint がある環境では、PowerPoint で書き出した PDF・画像を代わりに渡してもよい）は、視覚設計と可読性の採点に必要。画像が無い場合は構造とテキストだけで点検し、結果の limitations に記録する。その場合、視覚設計と可読性の軸には満点を付けず、上限を 14 点とする（暫定値。2026-11 の実測で、画像なしの採点が、折り返しの不自然さ・空白・同じ見た目の連続・強調と主張の食い違いを見落としたため）。

## 手順（リポジトリのルートから実行）

1. **事実の抽出**: `python .claude/skills/slide-clarity-review/scripts/extract_deck.py <deck.pptx> -o <作業dir>/deck-facts.json`。スライド毎に次を得る。
   - 内容: 見出し・本文量・箇条書き数・段落テキスト・画像数。
   - 文字サイズ: 明示指定された最小値。
   - 配置: トップレベル図形の位置と大きさ（インチ）、左端の種類数。
   - 色: 明示された色の種類数、文字色と背景色が両方明示された組の最小コントラスト比。
   - ノート: 本文（`notes_text`）と文字数（`notes_chars`）、画面の文字数（`screen_chars`。見出しと表のセルを含む）、レイアウト名（`layout_name`）。
   - 取れないもの: 継承されたフォントと色、テーマ色（解決しない）、グループ内の座標、描画結果。limitations に検査できた割合（`font checked` / `color checked` / `color theme-based`）が出る。このスクリプト自体は画像を作らない。画像は手順 1b で作る。
1b. **画像化（できる限り行う）**: `python .claude/skills/slide-clarity-review/scripts/render_deck.py <deck.pptx> -o <作業dir>/images`（LibreOffice で PDF にし、poppler でスライドごとの PNG にする。描画ソフトは環境変数 `SOFFICE` / `PDFTOPPM`、PATH、または作業フォルダの上にある持ち運び版（`00_vendor`）から探す。初回は設定の作成に数分かかることがある）。描画ソフトが無ければ終了コード 2 で理由を出す。そのときは PowerPoint で書き出した画像を使うか、「描画未確認」と報告する。
2. **機械検査**: `python .claude/skills/slide-clarity-review/scripts/check_deck.py <作業dir>/deck-facts.json --practices .claude/skills/_shared/slide-best-practices.json -o <作業dir>/auto-results.json`（違反があれば終了コード 1）。
   - `candidates`（候補）も出る: 空のプレースホルダー（`empty_placeholder`）、図形の部分的な重なり（`partial_overlap`）、複数の章の見出しに出る語（`repeated_topic_terms`）、所在に対応しない出典番号（`orphan_citations`）、表の推定の高さのはみ出し（`table_overflow`）、目次と本文の見出しの章番号の食い違い（`agenda_chapter_mismatch`。`only_in_agenda`／`only_in_body`。「第N章」「第N・M章」「第N〜M章」「Chapter N」、全角数字と漢数字の一〜十九を数える。50 を超える範囲は数えない。番号の無い章は拾えない）、ノートが長く画面が短いスライド（`notes_only_context`。ノート 200 字以上かつ画面の 2 倍以上。暫定値）。**候補は点数に入れず、終了コードにも影響しない**。点検員が画像で確かめるための手がかりで、0 件でも問題が無いとは限らない（2026-11 の実測では、重なりの候補は枠が重なるだけのものが大半、出典番号の候補は参考文献のページの見出しが取れない資料で取りこぼした）
3. **別エージェントで観点判定**: `readonly-reviewer` を起動し、下記の入力だけを渡す。
   - `deck-facts.json`（`shapes` の位置・大きさ・塗りを、整列・余白・視線の起点の判定に使わせる。`text_blocks` は、表のセルを含む文面を位置順に並べたもの）、`auto-results.json`、**手順 1b の画像（全スライド。1 枚ずつ開かせる）**
   - `clarity.json` の軸（id・title・practice_ids）と、軸が参照する `method: llm` の practice の `id` / `title` / `rule` / `check.how` と、適用条件 `applies_when.deck.condition`（ある場合）（severity は渡さない）
   - 返却形式: `{"axes":[{"id","score","citations":["[practice-id] slide 3: …"]}],"llm_results":[{"practice_id","passed"} | {"practice_id","applicable":false,"reason"}],"fixes":[{"slide","practice_id","problem","fix"}],"story_findings":[{"slide","kind","problem","fix"}]}`。`story_findings` は必須（無ければ空配列）。下の「話の流れの点検」。各軸 0〜20 点、citations は成果物内の記述の引用を最低 1 つ。引用の先頭に、理由にした観点の id を `[practice-id] ` の形で付けてよい（任意）。
   - **対象外と、判定できないの区別**: 適用条件（`applies_when.deck`）を持つ観点で、資料がその条件に当たらないときだけ `applicable: false` と理由を返す（減点も加点もしない）。適用条件の無い観点は対象外にできない。資料が条件に当たるのに判断材料が足りない観点は、対象外にせず passed を false にし、理由を fixes に書く。
   - 点検員への指示に「対象外にした観点を理由に、軸の点を下げない」と「構造の id（`bridge`・`supports-takeaway` など、practice でない id）を軸の引用の接頭辞に使わない」を含める。
   - **画像を渡せない時**: 点検員への指示に「視覚設計（`ax-design`）と可読性（`ax-legibility`）は 14 点以下で返す」を含め、limitations に「描画未確認」と書かせる（上の「依存」の上限。`finalize_review.py` は導出点と点検員の点の低い方を取るので、上限はこの指示で掛ける）。返ってきた 2 軸が 14 点を超えていたら、出し直しを依頼する。
4. **検査とゲート判定**: reviewer の JSON を保存し、`python .claude/skills/slide-clarity-review/scripts/finalize_review.py --deck <deck.pptx> --auto <作業dir>/auto-results.json --review <作業dir>/reviewer.json --practices .claude/skills/_shared/slide-best-practices.json --clarity .claude/skills/slide-clarity-review/criteria/clarity.json --facts <作業dir>/deck-facts.json --write`。
   - 終了コード 3: reviewer の出力が不正（軸の欠落・点数範囲外・citations 空・llm 観点の判定漏れ・対象外にできない観点の対象外・理由の無い対象外・機械の条件 `auto_trigger` と矛盾する対象外・対象外にした観点や存在しない id を接頭辞にした引用・`story_findings` の欠落と形の不正）。標準エラーの理由を添えて再出力を依頼する。`auto_trigger` を持つ観点を対象外にするには `--facts` が要る。
   - 0=PASS / 1=FAIL。`--write` で `.claude/review-history/slide-clarity-review/` に record が保存される。点検したのが別のリポジトリの資料なら、`--history-root <作業dir>/history` を付けて、この skill を置いたリポジトリに record を書かない。record には点検した .pptx の `target.sha256` と、対象外の一覧 `not_applicable` が入る。
   - **対象外の事後確認**: record の `not_applicable` と、軸ごとの citations・`reviewer_axis_scores` を並べて読み、対象外にした観点の内容を理由に軸を下げていないかを確かめて報告に書く（接頭辞の無い引用は機械で照合できないため）。下げていたら、その軸の出し直しを依頼する。
   - **点数の決め方（既定は `--score-mode min`）**: 軸の点数 = min(軸が参照する 28 項目の合否から導いた点数（残りの 5 項目は設計図の段階の検査）, 点検員が付けた点数)。対象外の観点は減点しない（対象外と合格は同じ点）。導出は、must の失敗で −6、llm 判定の should の失敗で −3、機械検査の should の失敗で −2（違反が 3 枚以上なら −4）を、20 点から引く（暫定値）。点検員は、引用を付けて点数を下げられるが、導出点より上げられない。出力の `axis_basis` に、軸ごとの減点の内訳が出る。`--score-mode derived` は導出のみ、`reviewer` は点検員の点数のみ（旧方式）。
   - **点数のぶれ**: 同じ版を別の点検員が採点すると、llm 判定の合否が割れて、点数が 10 点以上動くことがある（2026-11 の実測: 同じ版で 45 点と 60 点）。合計が合格線（80 点）の ±10 点以内のときは、別の点検員にもう 1 回独立に判定させ、低い方を採る。
5. **修正**: FAIL なら、`fixes` と `auto-results.json` の違反を、生成 skill で該当スライドに適用する。適用後は手順 1 からやり直す。**修正→再点検は最大 2 回**（合計 3 回まで）。2 回直しても FAIL なら止めて、残った違反をユーザーに報告する。資料作成の流れの中では、分かりやすさ・組織固有の検査・日本語の 3 種類の点検をまとめて 1 巡と数える（流れの文書 `docs/slide-creation-kit.md` が正）。ユーザーの指摘で直した場合も、点検をやり直す。
   - **修正の担当も、画像を自分で見ながら直す**（描画は手順 1b）。機械検査の数値（箇条書きの数、文字サイズ、左端）を満たすことを目的にしない。次の抜け道は使わない: シェブロンや時系列などの図を表に置き換える、文字を表のセルに移して文字量の判定を避ける、フォントを下げて収める。次の抜け道も使わない: 重なりを消すために文字を画像にする、出典番号を消して候補の検出を避ける（所在を書くのが直し方）、空の枠を消すために意味の無い文字を入れる、条件に当たる資料で対象外を使う、表を分けずにフォントを下げる。直し方は、項目を減らす・文言を短くする・図を大きくする・スライドを分ける・所在を書く・枠を消す。前回より点が上がった版では、点検員に、上の抜け道が使われていないかを画像で確かめさせる。機械検査は表のセルの文字を数えないので、表に移した文字は、点検員が `text_blocks` で量を見る。
   - 直した後は、手順 1 からやり直し、新しい版名で保存する（閲覧中のファイルのロックを避けるため）。
6. **続く点検**: 日本語の文面を含む場合は、PASS の後に `slide-japanese-review` で文面を点検する。組織固有の配色・フォント等の規定がある場合は、その検査も別のエージェントで行う（この skill では扱わない）。
7. **確定前の確認**: 確定する版に対して `python .claude/skills/slide-clarity-review/scripts/finalize_review.py --verify-latest <deck.pptx> [--history-root <dir>]` を実行する。同じハッシュの PASS の record があれば終了コード 0。無ければ 1 で、その版は未点検として扱う（直した後に点検し直していない、など）。この使い方は採点の引数と一緒に使えない（終了コード 2）。

### 画像を渡すときに、reviewer に見させる点（手順 3 の追加）

画像（スライドごとの PNG）が作れる場合は、reviewer に全スライドの画像を 1 枚ずつ開かせ、次を判定させる。見た内容を citations に書かせる。
- **1 スライド 1 メッセージ**: 主張が 2 つ以上混ざっていないか。見出しの主張を、本文と図が支えているか
- **デザインと主張の一致**: 色の強調・大きさ・配置が、そのスライドで一番伝えたい点に向いているか。強調が別の点に付いていないか。図の型（シェブロン・時系列・カード・表・大数字）が内容に合っているか
- **似た見た目のスライドの連続**: 同じレイアウトが続き、メッセージの違いが見た目で区別できないか
- **文字の折り返しと空白**: 1〜2 文字だけ次の行に落ちる、語の途中で改行される、空白が大きく文字が小さい
- **候補の確認**: `candidates` の空の枠・重なり・表のはみ出しが、画像で本当に見えるか
- **運用上の注意（出典なし。点数に入れず、気づいた点を fixes に書く）**: 前のスライドからつながらないスライド（章の始め・例・数値）の冒頭に、目的と前提があるか。1 つの例に 2 つの対策が混ざっていないか。聴衆が使う素材（依頼文・設定・計算式など）の全文がどこか 1 か所にあり、説明のスライドで効く部分が対応付けられているか。例や結果が、書いた条件（対象の数・手順）と一致しているか（2026-11 の検証で、完成した資料でのこの 4 点の判定は点検員の間で割れたため、点数に入れない）

LibreOffice など、実機の PowerPoint と違う描画ソフトを使った場合は、折り返しの指摘に「描画ソフトの差の可能性」を添える。

### 話の流れの点検（手順 3 の追加。点数・ゲートに入れない）

スライドだけで話が完結しているか、発表全体の筋が通っているかを、点検員に全スライドを順に見させて判定させる（2026-11 に、AI が作った資料を人が手直しした差分から導いた。出典の無い運用上の観点で、点検員によって判定が割れうるため点数に入れない）。**先にノートを読まずに**画面だけで各スライドの主張が成り立つかを判定させ、その後で `notes_text` を読ませる。見る点と `kind`:

| kind | 見る点 |
|---|---|
| tangent | 資料の結論（持ち帰り）を支えない脇道のスライド・章 |
| redundant | 同じ内容、または同じ型の説明が繰り返され、新しい情報が少ない |
| counter-example | 例の結果が、その章の主張と逆向き（但し書き・例外が本編にある） |
| missing-bridge | 章の始め・前の成果物を使うスライドに、前とのつながりが画面に無い |
| notes-dependent | 画面に無くノートにだけある前提・条件のため、ノートを読まないと主張が成り立たない（候補 `notes_only_context` は手がかり） |
| order | 「やること」より「なぜ効くか」が先、まとめが最後でない、など順序の問題 |
| agenda | 目次・冒頭の概要と本文の章が食い違う（候補 `agenda_chapter_mismatch` は手がかり。番号の無い章は点検員が見る） |

各要素は `{"slide": 1 以上の整数か null（資料全体）, "kind", "problem", "fix"}`。形が不正なら手順 4 で終了コード 3。record の `story_findings` と summary の末尾「話の流れの指摘 N 件」に出る。報告では点数と別に全件を出し、作る側は直すか、直さない理由を書く。組織固有の検査（他資料への依存を見るもの）がある場合、そちらとは別に、本 skill は口頭・ノート・前後のスライドへの依存を見る。

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
             "fix": "「売上は 2 年で 2 割伸びた」のように結論の一文にする"}],
  "story_findings": [{"slide": 9, "kind": "tangent", "problem": "製品比較の章が、結論のどの持ち帰りも支えない",
                      "fix": "付録に移すか削り、目次も直す"}]
}
```

対象外の例: `{"practice_id": "before-after-order", "applicable": false, "reason": "改善の前後や良い例と悪い例の対を含まない"}`。

実際は 5 軸すべてと、軸が参照する llm 観点すべての判定（合否か、対象外）と、`story_findings`（空配列可）が要る（足りないと手順 4 で終了コード 3）。

## 判定の定義

- ゲート: must の機械検査違反が 1 件でもある、または llm 観点の must が不合格、または総合点が 79 点以下なら FAIL。
- ランクはゲートと別: 95 点でも must 違反があれば「ランク S・FAIL」と両方を報告する。
- `verdict` の PASS / FAIL は修正ループのゲート結果であり、`review-rubrics.yaml` の点数ランクの scale とは別物（ランクは summary に書く）。
- severity は `slide-best-practices.json` の定義が正。reviewer の申告は使わない。
- 二次資料のみを根拠とする practice は should 止まり。出力では「secondary（未照合）」と区別して示す。

## 軸

`criteria/clarity.json` が正。①主張と構成 ②テキスト量と読みやすさ ③視覚設計（焦点・色・余白・整列と反復） ④根拠と図表 ⑤可読性（コントラスト・文字サイズ）。デザインは ③ と ⑤ で採点する。配色や書式のブランド準拠は生成側のゲートで検査する（この skill では扱わない）。

## 出力

ユーザーへの報告は次の型で返す。reviewer の結果を要約し直して緩めない。

```
## 分かりやすさの点検: <PASS / FAIL>（<合計> 点・ランク <S〜D>・<n> 回目の点検）
対象: <.pptx の絶対パス>（sha256 の先頭 12 桁）／ record: <保存した record のパス>
| 軸 | 得点 | 導出点 | 主な根拠（[practice-id] slide N: 引用） |
|---|---|---|---|
| ax-message 〜 ax-legibility の 5 行 |
違反: <スライド番号・practice id・出典 URL を 1 行ずつ。無ければ「なし」>
対象外にした観点: <practice id と理由。手順 4 の事後確認の結果>
候補: <種類と件数。画像で確かめた結果>
話の流れの指摘（story_findings。点数とは別）: <slide・kind・problem・fix を 1 行ずつ全件。作る側が直すか、直さない理由を添える。無ければ「なし」>
適用した修正: <スライド番号と内容。無ければ「なし」>
limitations: <描画未確認・描画ソフトの差・検査できた割合>
```

## エラー時

| 状況 | 対処 |
|---|---|
| .pptx が開けない・存在しない | 実行せず、正しい絶対パスを求める |
| `readonly-reviewer` を起動できない | `general-purpose` で再試行し、prompt に「ファイルを作成・変更・削除しない」と明記する。それでも失敗したら未実施と報告し、現セッションで代替採点しない |
| 画像化できない（`render_deck.py` が終了コード 2） | PowerPoint で書き出した画像があれば使う。無ければ構造とテキストだけで点検し、limitations に「描画未確認」と書き、視覚設計と可読性は 14 点を上限にする |
| スクリプトが実行できない（python が無い、`slide-best-practices.json` が無い、終了コード 2） | 点検を飛ばさない。実行できなかった内容を報告して停止する |

## 使用例

「`C:\decks\sales2025.pptx` の分かりやすさを点検して直して」 → 事実の抽出 → 画像化 → 機械検査（違反 3 件）→ `readonly-reviewer` が 5 軸を採点（ランク B・FAIL）→ `fixes` を生成 skill で 3 枚に適用 → 再抽出から再点検 → PASS → record を保存して報告。

## 更新履歴

- 1.3.0（2026-11-12）: 話の流れの点検（`story_findings`。必須・点数外）と、候補 `agenda_chapter_mismatch`・`notes_only_context`、抽出の `notes_text`・`notes_chars`・`screen_chars`・`layout_name` を追加
- 1.2.1（2026-11-12）: 画像を渡せない時の 2 軸の上限（14 点）を、手順 3 の点検員への指示で掛けることを明記した。ユーザーへの報告の型、移植するときの前提（`_shared/` の一覧・実行場所・試験の場所）を足した。`render_deck.py` の先頭に、`find_soffice` / `find_pdftoppm` を `sns-square-slides` が import する旨を 1 行足した
- 1.2.0（2026-11-06）: 適用条件のある観点（当たらない資料では対象外）と、対象外の返却・検査（`--facts`・引用の接頭辞）を追加。軸の参照を 24 項目から 28 項目に（同じ話題は 1 か所・前後の順序・所在の明示・本編と参考の順序）。機械検査の候補、record のハッシュ、`--history-root`、確定前の `--verify-latest` を追加
- 1.1.0: このリポジトリに追加
