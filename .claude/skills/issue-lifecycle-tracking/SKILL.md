---
name: issue-lifecycle-tracking
description: "バグ・改善点を、リポジトリ内の issue ファイル（issues/状態名/*.md）とディレクトリ移動(open→processing→closed)で起票・追跡・close し、起票前の関連確認と棚卸しを issue_tracker.py で行う（JSON の finding 台帳も対象）。Use when the user asks to '問題を起票して', 'バグを記録したい', 'issueをcloseして', 'Issueをディレクトリ移動で管理して', '課題管理の仕組みを作りたい', 'issueを棚卸しして優先度を付け直して', '課題台帳(JSON)を棚卸しして', '重複したissueを統合して', 'issue-lifecycle-tracking'. 使わない場面: GitHub Issues など外部トラッカーでの管理、定期バッチ等の高頻度な失敗記録(ログ集約を使う)、文書の文体レビュー(stop-ai-slop-jp)、skill の採点(review-skill)."
metadata:
  provenance: author-preference
  version: 1.6.0
---

# issue ライフサイクル追跡（ファイルベース状態遷移）

> 由来: 著者の運用嗜好（`metadata.provenance: author-preference`）。別プロジェクトには、ユーザーが選んだ時だけ持ち込む。

## 前提と代替

- 必要なもの: git 管理下のリポジトリと `git mv`。`issues/` が無ければ最初の起票時に `mkdir -p issues/open` で作る。
- script: `scripts/issue_tracker.py`（Python 3 の標準ライブラリだけ。試験は `scripts/test_issue_tracker.py`）。以下の `IT` は `python "${CLAUDE_SKILL_DIR}/scripts/issue_tracker.py"` の略（skill として読み込まずに Read で開き、変数が展開されない時は `python .claude/skills/issue-lifecycle-tracking/scripts/issue_tracker.py`。`python` が無く `python3` だけの環境では `python3` に読み替える）。repo のルート（`.claude/` の親）で実行する。`request`・`merge` に渡すパスは実行した場所が基準。既定値の根拠は `IT <サブコマンド> --help`。
- 設定 `.claude/issue-tracker.json` の書き方・終了コード・出力例: [references/issue-tracker-config.md](references/issue-tracker-config.md)。本文のひな形と報告の表: [references/issue-template.md](references/issue-template.md)

| repo 固有の依存 | 無い環境での扱い |
|---|---|
| `.claude/issue-tracker.json` | 無いと script は exit 2。references の md 用の例を写して作る。python が無ければ script を使わず、`issues/` の題名を grep して同じ判断をする |
| commit 前の hook（`.claude/hooks/pre-git-ledger-gate.sh`） | 無ければ commit は止まらない。commit の前に `IT check-new` を手で実行し、exit 1 なら「関連:」欄を書く |
| 検証記録の置き場（著者の運用例は `state/close-verify/`） | `issues/records/close-verify/<id>.md` など repo 内の任意の場所。最初に使う時に `mkdir -p` |
| handoff の片付け（agent-harness-bootstrap の `handoff_lifecycle.py`） | handoff を使わない repo では読み飛ばす |

## 状態遷移

`issues/open/` → `issues/processing/` →（`issues/pending/`・任意）→ `issues/closed/`。直さずに終えるものだけは終端 `issues/withdrawn/` へ移す。状態は `git mv` で表し、移動そのものが履歴になる。

- `open/`: 発見済み・未着手
- `processing/`: 着手中
- `pending/`（任意）: 修正済みで効果の検証待ち
- `closed/`: 効果を実測して PASS したものだけ（「直したつもり」と「直った」を分ける最終ゲート）
- `withdrawn/`: 誤起票・重複・前提が変わって不要になったもの。検証記録は作らず、理由を本文に 1 文書く（誤起票 / 重複なら統合先の id / 「前提が変わった: <何が>」）。消さないのは、なぜ不要になったかが残らないと同じ問題を再起票しやすいため

## してはいけないこと

- 効果を実測していない issue を `closed/` へ移す（open から closed への直行を含む）
- closed の issue を書き換える・戻す（再発は新規起票して相互リンクする）
- 移動先の同名ファイルを上書きする
- `related` を確かめずに新規起票する（「関連:」欄を空のまま・ひな形のままにする）
- issue を物理削除する（終えるのは closed か withdrawn）

## 各遷移の条件

- open → processing: 着手者が決まり、再現手順か調査方針が本文にある。`git mv` し、`status` を揃える。
- processing → pending: 修正のコミットがあり、検証がまだ。修正内容とコミットハッシュを本文に足す。pending を使わない運用では processing に置いたまま。
- pending（または processing）→ closed: 下の「報告と close 時の検証記録」の検証結果を満たす時だけ。open から closed へは移さない。
- 検証が FAIL: closed へ移さず processing に置き（pending なら `git mv` で戻す）、失敗した条件を本文に足す。closed 後の再発は、closed のファイルを触らずに新規起票して相互リンクする。
- 取り下げ: 重複なら `IT merge <src> --into <dst>`（統合元を `withdrawn/` へ移し、統合先に経緯を写す）。統合先の無い誤起票・前提の消えたものは `git mv` で `withdrawn/` へ移し、`status: withdrawn` と理由を書く。
- 移動先のディレクトリが無ければ `mkdir -p issues/<状態>`。移動先に同名ファイルがあれば上書きせず、内容を比べ、別 issue なら新しい id を採番する。
- 未追跡のファイルは `git add` してから `git mv` する。

## 起票の前に関連 issue を確かめる <!-- KH-0005 -->

1. `IT related --text "<題名や要約>"` を実行する。出力は `score  state  path  title` で、近いものほど上（判断材料で、合否は出さない。再発の確認は `--include-closed`）。
2. 近いものがあれば新規にしない。利用者の要望なら `IT request <issue のパス> --text "<原文>"` で「## 利用者の要望」節に原文を足す。重複なら上の「取り下げ」の `IT merge`（拒否される条件と exit 2 は references/issue-tracker-config.md）。
3. 新規にする時は、本文に「関連: <候補のパス>（別にした理由を 1 文）」か「関連: なし（related 確認済み）」を書く。JSON の issue（finding）なら `related: [<確かめた id>...]`（無ければ `[]`）。前提が特定のファイルの記述に依存するなら、JSON は `premise: [{"path": <リポジトリ相対か ~/ 始まり>, "contains": <その記述>}]`、md は本文に backtick でそのパスを書く（棚卸しで、前提が崩れた時に候補に出る）。
4. `IT check-new` は index で新しく足された issue だけを見て、欄が無ければ exit 1、stage した台帳を読めなければ exit 2 になる。hook を登録した repo では commit が止まる。

作業中に利用者が新しい要望・好み・やり方の指定を述べたら、関係する issue を `related` で探して `request` で原文を残す。1 回きりの指示で関係する issue も無ければ記録しない（issue を乱立させない）。 <!-- KH-0006 -->

## 棚卸し（優先度の付け直しと、前提が変わった issue の終わらせ方） <!-- KH-0008 -->

イテレーション完了時・引継ぎ資料を作る時・起票で active が増えた時に行う。`IT triage` は読み取り専用で候補を出すだけで、終えるかどうかは判定しない（前提が変わったかは解釈が要るため）。節は 優先度順 / 前提が崩れた候補 / 確認が古い / 欄の欠け / 重複の候補。

1. `IT triage` を実行する。
2. 前提が崩れた候補は実物を確かめ、(i) 今も成り立つ → `reviewed` を今日に（premise が古い書き方なら直す）、(ii) 前提が消えて不要 → JSON は `status: obsolete` と `resolution`、md は `withdrawn/` へ移して理由を書く、(iii) 別 issue に吸収 → JSON は `obsolete` + `resolution` + `superseded_by`、md は `IT merge`。
3. 重複の候補は、同じ問題なら (iii)。別の問題なら両方の関連（md は「関連:」欄、JSON は `related`）に互いを書く。
4. `priority` を付け直し、確かめたものの `reviewed` を今日にする。件数や数値を本文に書いた issue は数え直して note に足す。
5. 他のデータから参照されている JSON の issue（finding）を obsolete にする時は、参照している側も見直す（例: このリポジトリの `compliance-status.json` の `principles[].cr`）。
6. もう一度 `IT triage` を実行し、前提が崩れた候補と欄の欠けが、直したか利用者に聞くと決めたものだけになるまで 2〜5 を繰り返す。解釈が割れるもの（読み方次第のもの、方針の転換になるもの）は終端にせず利用者に聞く。

使い分け: 直して終えたら closed（JSON は `done`）、直さずに前提が消えた・吸収されたら withdrawn（JSON は `obsolete`）、最初から誤りなら withdrawn（JSON は `false-positive`）。

## 作業中に別件に気づいた時

本題と別の問題に気づいたら、その場で直さず、何を見つけたかを応答で一言報告して記録する。記録だけで終わらせず、下の見返しで issue か決まりにする。

- repo が discovery-log（`.tmp/discovery-log.md`、1 行 1 つの JSON。書式はリポジトリの CLAUDE.md）を使うなら 1 行足す。使わない repo では、この skill で直接起票する。
- 見返し（drain。時機はリポジトリの CLAUDE.md）では、`status: queued` の行を次のどれかにする。行は消さずに残し、status で終わりを示す（handoff の前の gate が見るのは queued が残っていないことだけ）:
  - 対応済み → `"done"`（`resolution` に何をしたか）
  - 直す必要がある → 上の「起票の前に関連 issue を確かめる」で起票し、`"issued"` と発行した id（欄の名前は repo の CLAUDE.md が決める。例: `"cr"`）
  - 今後も守る決まり → `.claude/knowhow.json` に KH として入れ、反映先に書いてアンカー（`<!-- KH-<番号> -->` の形）を置いてから `reflected` にし（台帳の書き方は agent-harness-bootstrap の operational-knowhow.md）、`"knowhow"` と `"kh"`
- 起票で active な issue が増えたら、上の棚卸しも行う。

## 起票の例

ユーザー「ログイン画面で 500 エラーが出る。記録しておいて」→ `IT related` で近い issue が無いことを確かめ、ひな形（references/issue-template.md）で `issues/open/` に作り、「関連: なし（related 確認済み）」を書く。

- close: 「#0012 を close して」→ 本文に検証結果（条件の 1 文と記録ファイルのパス）があれば `git mv issues/processing/0012-*.md issues/closed/` し、`status: closed` にして報告の表を返す。無ければ移さず「効果の実測が未記載のため processing のまま」と伝える。
- 検証 FAIL: 「修正したが再現した」→ 上の「各遷移の条件」の検証 FAIL のとおり。
- 重複: 「#0015 は #0009 と同じだった」→ `IT merge issues/open/0015-*.md --into issues/open/0009-*.md`。
- close・取り下げ・統合の最後: handoff を使う repo（agent-harness-bootstrap の script がある repo）では repo のルートで `python .claude/skills/agent-harness-bootstrap/scripts/handoff_lifecycle.py release --issue <移動後のパス> --config .claude/handoff-lifecycle.json` を実行し、その issue の handoff を片付ける（残したものは理由が出る）。

## issue ファイルの必須項目

- frontmatter: `id`（連番。既存の最大値 + 1）/ `title` / `severity`（high / medium / low）/ `category`（bug / improvement / docs など運用側で決めた語）/ `created` / `status`（ディレクトリ名と一致）。任意で `priority`（P1 次に着手 / P2 関係する所を触る時 / P3 判断待ち。`severity` とは別）と `reviewed`（棚卸しで前提を確かめた日 YYYY-MM-DD。無ければ `created` で古さを測る）
- 本文: 「関連:」欄（issue どうしの相互リンクはすべてここに書く。再発の過去 issue もここ）・症状・再現手順・該当箇所（パス:行）・仮説・修正候補・関連ファイル
- close 時に足す: 修正内容・関連コミット・検証結果（「直したはず」の申告だけでは close しない）
- JSON の issue（finding）の任意の欄: `priority` / `reviewed` / `premise` / `related`、status `obsolete` の時の `resolution`（理由）と `superseded_by`（統合先 id）

## 報告と close 時の検証記録

起票・遷移・close のたびに、操作 / issue / 配置 / 根拠 / 次の一手の 5 項目の表で報告する（references/issue-template.md）。本文の全文転記や件数・列挙は報告に入れない。

close 時の検証結果は、確かめた条件を 1 文で書く（例: 「修正後、別エージェントの再実行で症状が再現しなかった」）。件数・ファイルの列挙・コマンドの出力は本文に書かず、記録ファイル（例: `issues/records/close-verify/<id>.md`）に置いてパスで参照する。本文に列挙を書くと、列挙そのものが漏れや数え違いを生み、レビューのたびに新しい食い違いが見つかるため。

## エラー時・戻し方

| 状況 | 対処 |
|---|---|
| issue ファイルを誤って移動した | `git mv` で元のディレクトリへ戻し、`status` も戻す（履歴は git に残る） |
| `git mv` が「not under version control」で失敗した | `git add` してから `git mv` する |
| `status` とディレクトリ名が食い違っている | ディレクトリ（実際の置き場）を正とし `status` を直す。どちらが正か判断できなければ変えずに利用者に聞く |
| `issue_tracker.py` が exit 2 で止まった | 設定・引数・台帳の JSON が不正。何も変えていないので、メッセージの指す箇所を直して再実行する。merge の「統合済みだが統合元が残った」だけは扱いが違う（references/issue-tracker-config.md の終了コード） |
| commit が「関連:」欄の欠けで止まった | `IT related` で関連 issue を確かめ、新規の issue に「関連:」欄（JSON なら `related`）を書いて stage し直す |
| triage の「前提が崩れた候補」に出た | すぐ終端にしない。実物を確かめて「棚卸し」の手順 2 の (i)〜(iii) のどれかにする。読み方次第なら利用者に聞く |
| triage の「確認が古い」に「日付が読めない」が出た | `reviewed` か起票日を `YYYY-MM-DD` に直す |

## 適用しない方がよいケース

- 高頻度・低リスクな自動実行（定期バッチ等）の失敗記録: ログ集約とアラートの方が適する
- 単一開発者・短命のプロジェクト: `open/` と `closed/` の 2 状態で足りることが多い

関連する運用（数値目標の置き場、レビューが続けて FAIL した時の起票）は [references/related-practices.md](references/related-practices.md)、更新履歴は [references/changelog.md](references/changelog.md)。
