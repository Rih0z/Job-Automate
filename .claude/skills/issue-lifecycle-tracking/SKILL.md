---
name: issue-lifecycle-tracking
description: "バグ・改善点を、リポジトリ内の Issue ファイルとディレクトリ移動(open→processing→closed)で起票・追跡・close する。Use when the user asks to '問題を起票して', 'バグを記録したい', 'issueをcloseして', 'Issueをディレクトリ移動で管理して', '課題管理の仕組みを作りたい', 'issue-lifecycle-tracking'. 使わない場面: GitHub Issues など外部トラッカーでの管理、定期バッチ等の高頻度な失敗記録(ログ集約を使う)、文書の文体レビュー(stop-ai-slop-jp)、skill の採点(review-skill)."
metadata:
  provenance: author-preference
  version: 1.3.1
---

# Issue ライフサイクル追跡（ファイルベース状態遷移）

> 由来: **著者の運用嗜好**（frontmatter `metadata.provenance: author-preference`）。Anthropic 公式ベストプラクティスに根拠はない。別プロジェクトへ移す時は、ユーザーが明示的に選んだ場合のみコピーする。デフォルトでは持ち込まない。

## 前提と代替（repo 固有の依存）

- 必要なもの: git 管理下のリポジトリと、ファイル移動に使う `git mv`。`issues/` ディレクトリは無ければ最初の起票時に `mkdir -p issues/open` で作る。
- 使うツール: Bash(`git mv` / `mkdir -p`)、ファイルの Read / Write。
- 本文テンプレートと応答形式: [references/issue-template.md](references/issue-template.md)

この repo 固有の依存と、無い環境での最小動作は次のとおり。

| repo 固有の依存 | 無い環境での扱い |
|---|---|
| `agent-harness-bootstrap` skill の `provenance.json`(由来の台帳) | 読まない。この SKILL.md と references/ だけで動く |
| `state/close-verify/`、`state/thresholds.md`(著者の運用例のパス) | `issues/records/close-verify/[Issue番号].md`、`issues/records/thresholds.md` など、リポジトリ内の任意の場所へ読み替える。ディレクトリは最初に使うときに `mkdir -p` で作る |
| 他の skill(`stop-ai-slop-jp` 等) | 参照しない。「文体の採点と事実の突合を別のレビューに分ける」という要点だけを適用する |

最小動作の手順(台帳も `state/` も無い環境): (1) `mkdir -p issues/open issues/processing issues/closed`(取り下げが出たときに `issues/withdrawn` も作る) (2) テンプレートに沿って `issues/open/` へ Issue ファイルを作る (3) 状態が変わるたびに `git mv` で移動し `status` を揃える (4) close 前に検証結果を `issues/records/close-verify/` に置く。

## 概要

外部の Issue トラッカー(GitHub Issues 等)を使わず、リポジトリ内のディレクトリ間でファイルを移動することで状態を表現する軽量な問題管理パターン。git 管理下に置くことで、リポジトリ内検索・`git blame`・commit/PR との紐付けが一元化され、外部トラッカーとの二重管理コストを避けられる。

## 状態遷移

`issues/open/` → `issues/processing/` → (`issues/pending/`・任意) → `issues/closed/`。取り下げ(誤起票・重複)だけは専用の終端 `issues/withdrawn/` へ移す。状態遷移はファイル移動(`git mv`)で表現し、移動そのものが履歴として残る。

- `open/`: 発見済み・未着手
- `processing/`: 着手中
- `pending/` (任意ステージ): 修正は実施済みだが効果検証がまだの一時置き場
- `closed/`: **効果を実測して PASS したもの限定**で移動する(未検証のまま closed へ移動しない — 「直した"つもり"」を「直った」と混同しないための最終ゲート)
- `withdrawn/`: 誤起票・重複で修正せずに終えるもの。効果の実測は不要で、検証記録は作らない。取り下げの理由(誤起票か、重複なら統合先の Issue 番号)を本文に1文で書く。closed には入れない

## 各遷移の条件

- open → processing: 着手者が決まり、再現手順か調査方針が Issue 本文にある。ファイルを `issues/processing/` へ `git mv` し、`status` を更新する。
- processing → pending: 修正のコミットがあり、効果の検証がまだのとき。修正内容とコミットハッシュを本文に追記する。pending を使わない運用では、検証が済むまで processing に置く。
- pending(または processing) → closed: 下の「close 時の検証記録」を満たすとき。
- 検証が FAIL した場合: closed へ移さず processing に戻し、失敗内容を本文に追記する。
- open → closed の直行は不可。closed は効果を実測して PASS した Issue だけが入る場所なので、必ず processing を経由し、検証記録を満たしてから移す。open のまま取り下げたい(誤起票・重複)ときは、closed ではなく `issues/withdrawn/` へ移す(`git mv`、`status: withdrawn`)。理由を本文に書けば足り、検証記録は要らない。
- 移動先ディレクトリが無い場合は作成する(`mkdir -p issues/<状態>`)。同名ファイルが移動先にある場合は上書きせず、ID の重複を疑って内容を比べ、別 Issue なら新しい ID を採番する。

## 起票の例

ユーザー「ログイン画面で 500 エラーが出る。記録しておいて」→ `issues/open/` に Issue ファイルを作る。ひな形は [references/issue-template.md](references/issue-template.md)。

他の場面の例:

- close: ユーザー「#0012 を close して」→ 本文に検証結果の記載(条件の1文と記録ファイルのパス)があるか確認する。あれば `git mv issues/processing/0012-*.md issues/closed/` し、`status: closed` に更新して報告表を返す。検証結果が無ければ移動せず、「効果の実測が未記載のため processing のまま」と理由を伝える。
- 検証 FAIL: ユーザー「修正したが再現した」→ pending(または close 前の processing)にある Issue は `issues/processing/` に置いたまま(pending なら `git mv` で戻し)、`status` を揃えて再現した条件を本文に追記する。すでに closed の Issue は書き換えず、新規起票して相互リンクする。
- 取り下げ: ユーザー「#0015 は重複だった」→ 本文に理由と統合先の番号を1文書き、`git mv issues/open/0015-*.md issues/withdrawn/` して `status: withdrawn` にする。検証記録は作らない。
- 起票の重複: 同じ症状の Issue が `issues/` 配下にすでにあれば、新規起票せずその Issue に追記するかを確認する(再発で過去分が closed なら、新規起票して相互リンクする)。

`id` は連番(既存の最大値 + 1)、`severity` は high / medium / low、`category` は bug / improvement / docs など運用側で決めた語、`status` はディレクトリ名(open / processing / pending / closed / withdrawn)と一致させる。続けて症状・再現手順・該当箇所を本文に書く。

## Issue ファイルの必須項目

- frontmatter: `id` / `title` / `severity` / `category` / `created` / `status`
- 本文: 症状・再現手順・該当箇所(ファイルパス:行番号)・仮説・修正候補・関連ファイル
- close 時に追記する項目: 修正内容・関連コミットハッシュ・検証結果(テスト実測など効果の証跡。「直したはず」の申告だけでは close しない)
- 同一バグが再発した場合は新規 Issue ファイルを作成し、frontmatter で過去 Issue と相互リンクする(古い Issue を書き換えて再利用しない — 再発の履歴自体が情報になる)

## 応答形式

起票・遷移・close のたびに、操作 / Issue / 配置 / 根拠 / 次の一手の 5 項目の表で報告する(表のひな形は references/issue-template.md)。本文の全文転記や件数・列挙は報告に入れない。

## close 時の検証記録は条件で書く

close 時に追記する検証結果は、確かめた条件を1文で書く(例: 「修正後、別エージェントの再実行で症状が再現しなかった」)。件数、ファイルの列挙、コマンドの出力は Issue 本文に書かず、記録ファイル(例: `state/close-verify/[Issue番号].md`。前提の読み替えを参照)に置いて本文からパスで参照する。

理由: 本文に件数や列挙を書くと、列挙そのものが漏れや数え違いを生み、レビューのたびに新しい食い違いが見つかる。条件と記録を分けると、本文は短いまま保て、突合は記録ファイルと実物の間だけで済む。

## 数値目標の単一 SoT 化

レビュー合格点・カバレッジ目標・スコア閾値等の**頻繁に変わる数値**は、本体のルール文書に埋め込まず専用ファイル(例: `state/thresholds.md`)へ分離し、本体からは参照リンクのみを置く。

理由: 数値だけが変わるたびに本体ドキュメントの diff が肥大化し、「基準値の更新」と「ルールの構造変更」が同じ diff に混ざって履歴が追いにくくなる。この条項は対象プロジェクトが実コードのカバレッジ%を持たない場合でも、「合格率」「品質スコア」等の類似の閾値へ読み替えて適用する(N/A 判定はしない)。

## N 回連続 FAIL の Issue 起票エスカレーション

レビューゲートを同一対象に対して固定回数(既定は 3 回。プロジェクトで別の値を決めていればその値を使い、決めていなければ 3 回とする)連続で FAIL した場合、無限に「修正→再レビュー」を繰り返さず、当該タスクを中断して `issues/open/` に Issue を起票する。起票内容には各回でどの評価軸が低かったか・試行内容・残課題・推奨次手を記録する。これにより「基準が厳しすぎる/観点がずれている」可能性を人間が判断する機会を確保する。

文体レビューの修正ループが、事実主張の多い文書で収束しないことがある。この場合は文書の修正を続けず、文体の採点と事実の突合を別のレビューに分ける(`stop-ai-slop-jp` skill の「採点範囲」節)。

## エラー時・戻し方

| 状況 | 対処 |
|---|---|
| Issue ファイルを誤って移動した | `git mv` で元のディレクトリへ戻し、`status` も戻す(履歴は git に残る) |
| `issues/` が存在しない | 最初の起票時に `mkdir -p issues/open` で作る |
| open から closed へ直接移そうとした | 移さない。修正したなら processing へ移し、検証記録を満たしてから closed へ移す。誤起票・重複なら `issues/withdrawn/` へ移す |
| 誤起票・重複で終わらせたい | `issues/withdrawn/` へ `git mv` し、理由を本文に書く。検証記録は要らない |
| 検証結果が本文に無いのに close を頼まれた | closed へ移さず processing のまま、「効果の実測が未記載」と理由を伝える |
| closed 後に再現した | closed のファイルは書き換えず、`git mv` でも戻さず、新規 Issue を起票して相互リンクする(再発の履歴を残す)。検証 FAIL を close 前に見つけた場合だけ、その Issue を processing に置く |
| `git mv` が「not under version control」で失敗した | 対象ファイルが未追跡。`git add` してから `git mv` するか、通常の `mv` で移して後で `git add` する |
| 移動先に同名ファイルがある | 上書きしない。ID の重複を疑って内容を比べ、別 Issue なら新しい ID を採番する |
| `status` とディレクトリ名が食い違っている | ディレクトリ(実際の置き場)を正とし、`status` を直す。どちらが正か判断できなければ変更せず利用者に確認する |

## 発見時の強制フロー (推奨)

別作業中に問題を発見した場合、些細な内容でもその場で Issue ファイル化する。起票だけで終わらせず、同種 Issue の棚卸し・統合 → 恒久対応が必要なら計画書化 → 作業再開のための引継ぎ作成、までを一連の流れとして実行する(起票して満足し放置する失敗パターンの防止)。

## 適用しない方がよいケース

- 高頻度・低リスクな自動実行タスク(定期バッチ等)の失敗記録: ファイルベース Issue 化だと運用が追いつかないため、ログ集約 + アラートの方が適する
- 単一開発者・短命プロジェクトで状態遷移の恩恵が薄い場合: `open/`/`closed/` の2状態のみで十分なことが多い

---

## 更新履歴

- 初版 (2026-09-03): 実運用プロジェクトでの知見を一般化して追加
- 1.1.0 (日付は未記録): 前提節、応答形式、本文テンプレート(references/)を追加
- 1.2.0 (2026-10-30): description を用途・トリガー・使わない場面に絞った。repo 固有のパスの読み替え方、close と検証 FAIL と重複起票の例を追加
- 1.3.0 (2026-10-30): repo 固有の依存を「前提と代替」の表に集約し最小動作の手順を追加、open から closed への直行不可を明記、エラー対処を表に拡充
- 1.3.1 (2026-10-30): closed 後の再現は新規起票に統一、取り下げ専用の終端 `withdrawn/` を追加(検証記録は不要)
