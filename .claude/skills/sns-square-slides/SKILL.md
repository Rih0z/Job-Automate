---
name: sns-square-slides
description: "SNS（X など）の投稿に添える正方形のスライド 4 枚の構成（各枚の役割・暗い地と明るい地の並び・文字量・注記の書き方）と投稿文との分担を決め、設定 JSON から 1080x1080 の JPEG を 4 枚作る（python-pptx → LibreOffice で PDF → poppler で JPEG）。Use when the user asks 'SNS 用のスライドを作って', 'X に載せる画像 4 枚を作って', '告知用の正方形スライド', '投稿用のカード画像を作って', 'ツイートに付けるスライド構成', 'make four square images for an X post', 'SNS carousel slides'. 使わない場面: 16:9 の発表資料（slide-composition-planner と作成 skill）、HTML スライド（slides-pro）、SNS への投稿そのもの（この skill は投稿しない）、サムネイル 1 枚の画像生成（thumbnail-generation）。"
allowed-tools: Read Write Glob Grep Bash Agent
argument-hint: "<元にする記事・資料の絶対パス> [出力先ディレクトリの絶対パス]"
metadata:
  provenance: domain-prompt
  version: "1.0.0"
---

# SNS 投稿用の正方形スライド 4 枚

記事や調査を SNS で知らせるときに、投稿に添える正方形の画像 4 枚を作る。構成を決めて `cards.json` に書き、`scripts/make_square_cards.py` で検査してから画像にする。**投稿はしない。** 投稿は利用者か、そのプロジェクトの投稿の手順で行う。

数値（枚数・役割と地の並び・文字数の上限と目安・明暗差・投稿文の数え方・文字サイズ・既定の配色とフォント）と画像の点検表は `criteria/card-rules.json` が正本。この文書に数値を重ねて書かない。

## 前提条件

| 前提 | 用途 | 無いとき |
|---|---|---|
| Python 3 | 検査（`--check` は標準ライブラリだけで動く） | 実行できなかったと報告して止まる |
| python-pptx（`pip install python-pptx`） | .pptx の生成 | `--preflight` が exit 3。生成しない |
| LibreOffice（`soffice`）と poppler（`pdftoppm`） | PDF 経由で JPEG にする | 同上。探し方は同じリポジトリの `slide-clarity-review/scripts/render_deck.py` の `find_soffice` / `find_pdftoppm`を使う（soffice は環境変数 `SOFFICE` → PATH → 持ち運び版 `00_vendor/` → Windows の既定の場所、pdftoppm は環境変数 `PDFTOPPM` → PATH → 持ち運び版 `00_vendor/`）。render_deck.py が無いと exit 3 |
| `fc-list`（任意） | `--preflight` でフォントの有無を確かめる | フォントは「未確認」と出す（macOS は標準で持たない。既定の Hiragino Sans は macOS に標準で入っている） |
| 読み取り専用の点検用エージェント `readonly-reviewer` | 画像の点検 | `general-purpose` に「ファイルを作成・変更・削除しない」と明記して使う |

コマンドは、この skill を置いたリポジトリのルートから実行する。別のプロジェクトでは `slide-clarity-review` と一緒に同じ相対パスへ置く。日本語のフォントは、macOS では Hiragino Sans、それ以外では Noto Sans CJK JP を既定にする（`cards.json` の `font` で変える）。

## 4 枚の構成

| 枚 | role | 地 | 書くこと |
|---|---|---|---|
| 1 | `hook` | 暗い | 流し見で手が止まる結論か数字を 1 つ。title に結論、body に対象と時点 |
| 2 | `evidence` | 明るい | 結論を支えるデータか比較を 1 つ |
| 3 | `evidence` | 明るい | 2 枚目と別の角度のデータ（条件・反対側の数字・限界）を 1 つ |
| 4 | `close` | 暗い | 読み手が持ち帰る結論か次の行動。リンクの案内だけで終えない |

暗い地で 1 枚目と 4 枚目を挟み、データを読ませる 2・3 枚目を明るい地にする（運用上の経験則で、出典は無い）。role の並びは検査で固定し、地の色は role から決まる（設定には書かない）。

書き方:

- **1 枚 1 要点。** 2・3 枚目で同じことを言い換えない。足りない要点は投稿文か元の記事に回す
- **数値には時点か期間を付ける。** 「直近」「最近」だけで終えない
- **例や換算は対象を名指しする。** 「100 万円なら」と書くときは、何の商品・指標の数値で計算したかを同じカードに書く。別の対象の数値を当てはめない
- **注記は、どの計算に掛かるかを行単位で書く。** 1 枚に 2 つの計算を並べ、片方にしか当てはまらない前提（例: 為替や手数料を入れていない）があるなら、「2 行目の計算は〜を入れていない」のように対象を名指しする。注記は `note` に 1 つ書き、両方に掛かるならそう書く
- title は大きい文字（`font_pt.title`）で描くので 1 行に入る字数が少ない。1 字だけ次の行に落ちる長さは避け、言い換えて 1 行に収めるか、2 行にそろえる（画像で確かめる）
- 行数は改行で数え、上限は `limits` の `*_max_lines`。行の中の折り返しは数えないので、画像で確かめる
- 文字数は `limits` の目安（`*_recommended`）に収める。上限（`*_max`）を超えると検査で落ちる。収まらなければ、項目を減らすか投稿文へ回す。文字を小さくして詰めない

## 投稿文との分担

- 投稿文は `post.text` に書く。長さは `post_count` の数え方で検査する。既定の `x` は X の公開している規則（全角はおおむね 2、半角英数は 1、`https://` から始まる URL は 23、上限 280）で、出典は criteria の `source`。X 以外で文字数そのものが上限の媒体は `post.count` を `chars` にする。URL は `https://` から書く（無いと文字として数え、警告が出る）。投稿の手順の側に独自の検査があれば、その数え方も確かめる
- **スライドの要約を写さない。** スライドに無い一次の補足（元の資料に当たって分かった事実・条件）を 1 つ足し、その出どころを `post.supplement_source` に書く。検査は、空白と改行を除いて `copy_min_chars` 文字以上になるカードの title・note・body（全体と各行）が、投稿文に丸ごと入っていれば落とす（言い換えた写しは検査では見つからないので、点検で見る）
- 元の記事へのリンクは投稿文の側に置く（4 枚目は結論で終える）
- 投稿文は散文なので、日本語の点検は `stop-ai-slop-jp`（ある環境のみ）で行う

## 手順

1. 元の記事・資料を読み、1 枚目に置く結論か数字を 1 つ決める。数値は元の資料で確かめる（記事の要約から写さない）
2. 上の表に沿って 4 枚を割り当て、`cards.json` を書く（形式は `examples/cards.example.json`）。置き場所は出力先と同じフォルダにする（出力先の指定が無ければ、元にする記事・資料と同じフォルダの下に `sns-cards/` を作ってそこに置く）。ブランドの色やアカウント名は、`palette_ref`（配色 JSON のパス）・`palette`（役割ごとの上書き）・`label` で渡す。配色の形式は `slide-composition-planner` の palette と同じ `roles`（`focus`・`surface-1`・`surface-2`・`text-primary`・`text-secondary`）。`focus` は暗い地のラベルに使うので、明るい資料向けの濃い `focus` を持つ配色では明暗差の検査で落ちる。そのときは `palette` で `focus` だけ明るい色に上書きする
3. 検査する（`C1` 枚数・`C2` role の並び・`C3` 文字数と行数・`C4` 明暗差・`C5` 配色・`C6` 投稿文・`C7` キーと型）: `python3 .claude/skills/sns-square-slides/scripts/make_square_cards.py --config <cards.json> --check`。exit 0 になるまで直す。警告（目安を超えた）は、直せるなら直す
4. 道具を確かめる: `python3 .claude/skills/sns-square-slides/scripts/make_square_cards.py --preflight`
5. 画像にする: `python3 .claude/skills/sns-square-slides/scripts/make_square_cards.py --config <cards.json> --out-dir <出力先> --name <名前>`。`<名前>-1.jpg`〜`-4.jpg`（1080x1080）と `<名前>.pptx` ができる
6. 点検する（別エージェント）: `readonly-reviewer` に、JPEG 4 枚と `cards.json` の絶対パス、`criteria/card-rules.json` の絶対パスだけを渡して、その `review_checklist`（R1〜R8）で判定するように指示し、項目ごとの合否と根拠（何枚目のどの文字か）を返させる。作った意図は渡さない。スライドの日本語は、`<名前>.pptx` を `slide-japanese-review`（ある環境のみ）に渡す。投稿文は `stop-ai-slop-jp`（ある環境のみ）
7. 不合格の項目を `cards.json` で直し、3 から繰り返す。直したら点検もやり直す。直しと点検は最大 2 回（点検は合計 3 回まで）とし、それでも不合格なら止めて、残った項目と理由を利用者に報告する

## 終了コード

| コード | 意味 |
|---|---|
| 0 | 合格（`--check`）・道具が揃っている（`--preflight`）・4 枚できた（既定） |
| 1 | 検査の違反（`C1`〜`C7` の記号つきで 1 行ずつ出る） |
| 2 | 入力の誤り（引数の不足・不正〈`--config`・`--out-dir`・`--name`〉、待ち時間の環境変数の誤り、設定・`palette_ref`・criteria が無いか壊れているか形が違う） |
| 3 | 道具が無い（python-pptx・soffice・pdftoppm・render_deck.py の import、`--preflight` のフォントの NG） |
| 4 | 描画の失敗・時間切れ・JPEG の枚数か大きさが違う。出力先には何も足さず、前回の出力も消さない（この実行で作った出力先は、空のまま失敗したら消す）。例外は最後の 5 つのファイルの移動の途中で OS のエラーが起きた時だけで、そのときは移し終えたファイルの名前を出す（そのファイルは新しい版に置き換わっている） |
| 5 | 内部の誤り（想定外の例外。traceback を出す） |

## 報告の形

利用者には次の順で返す。

1. JPEG 4 枚と .pptx の絶対パス
2. `--check` の結果（違反 0 件・警告の件数と中身）
3. 点検表 R1〜R8 の合否（別エージェントの判定と、根拠の何枚目のどの文字か）と、`slide-japanese-review`・`stop-ai-slop-jp` を通したかどうか
4. 投稿文の案と、`supplement_source`
5. 残った警告と、直さなかった理由

## エラー時

- exit 1: 出た記号の項目を直す。`C6` で投稿文の写しが出たら、写した文を消して、スライドに無い補足に置き換える
- exit 3: `--preflight` の出力で欠けた道具を入れるか、`SOFFICE` / `PDFTOPPM` に場所を渡す。入れられない環境では画像にせず、`--check` の結果と `cards.json` を渡して止める
- exit 4: この skill は専用の LibreOffice のプロファイル（既定は `$XDG_CACHE_HOME` か `~/.cache` の下の `sns-square-cards/lo_profile`、環境変数 `SNS_CARDS_PROFILE`）を使い回すので、他の LibreOffice とは衝突しないが、この skill を同時に 2 つ動かすと後の方が失敗する。同時に動かさない。初回はプロファイルの作成に数分かかる（待ち時間は既定 600 秒、`SNS_CARDS_SOFFICE_TIMEOUT`）。時間切れなら一度だけやり直し、それでも失敗したら出力を添えて報告する
- exit 5: 出力の traceback を添えて報告する（設定の直しでは解けない）
- 環境変数 `SNS_CARDS_RENDER_DECK` は試験用の継ぎ目で、通常は設定しない
- 試験（`scripts/test_make_square_cards.py`）の実物の描画は、本番と同じ利用者のキャッシュのプロファイルを使う（初回の作成の数分を避けるため）。本番の実行と同時に試験を回さない
- 点検で文字のはみ出しが出た: 文字を減らす。フォントの置き換えで折り返しが変わることがあるので、点検の指摘には描画環境（OS とフォント）を添える

## 使用例

- 「この記事の告知用に X の画像 4 枚を作って」: 記事を読む → 1 枚目の結論を決める → `cards.json` を書く → `--check` → `--preflight` → 画像にする → 別エージェントに点検表で点検させる → JPEG と投稿文の案を渡す（投稿はしない）
- 「ブランドの色で」: 配色 JSON を `palette_ref` に渡す。暗い地のラベルの明暗差で落ちたら `palette` で `focus` を上書きする
- 失敗系: 3 枚しか要点が無い → 4 枚目を水増ししない。3 枚目に条件か限界を置き、4 枚目を結論にする。それでも埋まらないなら、画像付きの投稿にしない案を利用者に出す

## 更新履歴

- 1.0.0（2026-11-12）: 追加。試験は `python3 .claude/skills/sns-square-slides/scripts/test_make_square_cards.py`
