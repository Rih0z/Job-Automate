# Step 0: 由来別の取捨選択（selection flow）

SKILL.md 本体の生成手順 Step 0 から参照する supporting file。対象がこのリポジトリ以外の別ディレクトリ / 別リポジトリの時に実行する。**Step 0 は省略しない**（対話が取れない時は `default_selection` で記録を生成する = 非対話扱い）。唯一の例外はこのリポジトリ自身の CLAUDE.md 剪定（新しい生成物を作らない）。

目的: このリポジトリには **Anthropic 公式ベストプラクティス由来の要素**と**著者の運用嗜好**（issue フォルダ管理・handoff 規約・並走 recheck 等）が同居している。両者を混ぜたまま他環境へ写さないため、要素ごとの由来を `provenance.json` で分け、**何を取り込み何を取り込まないかをユーザーが決める**。

## 0-1. 台帳の読込

`provenance.json` を Read する。`elements[]` の各要素は `provenance` と、その level の `default_selection`（要素側に `default_selection_override` があればそちら）を持つ。付随物は `skills[]` / `commands[]` / `files[]`（skill が参照する共有ファイル等）に列挙されており、要素を採用する時はこれら全てをコピーする。

## 0-2. 由来別に提示する

要素を次の 4 群に分けて提示する。群ごとに 1 表（列: id / 要約 / 依存 / デフォルト）。要素の要約は台帳の `summary` をそのまま使い、言い換えない:

| 群 | 該当 | 提示の仕方 |
|---|---|---|
| A | `provenance: official` | 「必ず採用（外せない）」— Anthropic 公式由来は全て取り込む。`provenance-check.sh` C11 が `selected: false` を拒否する |
| B | `provenance: official-derived`、および `default_selection_override: recommend` を持つ要素（例: `numeric-target-single-sot`） | 「推奨（事前チェック済み）。外すものがあれば申告」 |
| C | 上記以外の `author-preference` / `third-party` / `domain-prompt` | 「**デフォルト非採用**。取り込むものだけ選択」 |
| D | `repo-specific` / `portable: false` | 「本リポジトリ固有のため移植不可」（提示のみ・選択肢に含めない） |

群 C は要素数が多いので `kind` ごと（principle / process / rules / hooks / skill / command / asset / claude-md-section / skill-group）に小分けして提示する。`domain-skills-group` は先に業務カテゴリ（business-planning / content-creation / ops-management / research-intelligence / design・mcp）で該当有無を聞き、該当カテゴリの skill だけを個別に提示する。

## 0-3. 選択を取る

- **対話が可能な時**: `AskUserQuestion` を使う。ツールの制約は **1 回の呼び出しで最大 4 問・各問の選択肢は 2〜4 個・header は 12 文字以内**なので、群 C は「4 択 × 最大 4 問 = 1 呼び出し」を単位に分割し、**先に問数と呼び出し回数の見込みを 1 行で宣言**してから始める（例: 「著者嗜好 30 要素 → 8 問・2 呼び出し」）。選択肢の label は要素 id、description は台帳の `summary` を使う。`multiSelect: true`。群 B は最後に「外す要素はあるか」を 1 問で聞く（群 A は聞かない）。
- **Step 0 の質問はメインセッションで行う**: `AskUserQuestion` は Agent ツールで起動した subagent 内では使えない。本スキルが subagent や `context: fork` で走っていて利用不可を検知した場合は、default で進めずに「Step 0 の選択が必要」と親セッションへ返す（ユーザーがいるのに非対話扱いにしない）。
- **対話が不可能な時**（メインセッションで `AskUserQuestion` が利用不可 / エラーを返す・headless 実行・ユーザー応答が得られない）: `default_selection` のみ採用する（A = 採用、B = 採用、C = 非採用、D = 除外）。**この場合は最終報告の冒頭に「著者嗜好要素はデフォルト非採用で生成した。`harness-selection.json` を編集して再実行できる」と明記する**。推測でユーザーの好みを補わない。
- **依存関係の検証**: 選んだ要素の `depends_on` に非選択の要素があれば、その組合せは成立しないことを示して**選び直させる**（例: `session-restore-hook` を選ぶには `handoff-management` と `issue-lifecycle` と `hooks-reference-set` が要る）。`soft_depends_on` は**警告のみ**で成立させ、台帳の `note` に従う縮退形で採用する。
- **「全部入れて」への対応**: ユーザーがそう言った場合も群 D は入れない。群 C を全採用する時は、要素数と生成される rules / hooks の量を 1 行で示した上で確定する（過剰生成に気付く機会を残す。スケール調整の原則と同じ）。

## 0-4. 決定を対象に記録する

対象プロジェクトの `.claude/harness-selection.json` に書く（Claude Code はこのファイルを解釈しない・人間と本スキルが読む台帳。**移植チェックリストの実体はこのファイルであり、別のチェックリストは作らない**）:

```json
{
  "schema": "harness-selection/v1",
  "source": "Job-Automate .claude/skills/agent-harness-bootstrap/provenance.json (updated 2026-09-04)",
  "decided_at": "2026-09-04",
  "decided_by": "user",
  "selections": {
    "official-claude-md-core": { "selected": true, "decided_by": "default" },
    "issue-lifecycle": { "selected": true, "decided_by": "user" },
    "handoff-management": { "selected": false, "decided_by": "user", "note": "単独開発のため不要" },
    "hooks-reference-set": { "selected": false, "decided_by": "scale", "note": "毎回実行したい規律が現時点で無い" },
    "domain-skills-group": { "selected": true, "decided_by": "user", "skills": ["review-blog", "slides-pro"] },
    "claude-md-review-skill-index": { "selected": false, "decided_by": "excluded" }
  }
}
```

- `source` の日付は台帳の `updated` を転記する（どの版の台帳で決めたかを残す）。
- トップレベル `decided_by` は `user`（対話で決めた）か `default`（非対話・default_selection のみ）。
- `selections` には**台帳の全要素**を載せる（選ばなかった要素も `selected: false` で残す。後で「あの観点は取り込めているか」と聞かれた時に、検討済みで外したのか未検討なのかを区別するため）。
- 要素側 `decided_by` は `user` / `default` / `excluded`（群 D）/ `scale`（Step 0 後のスケール調整で落とした）のいずれか。
- `skill-group` を `selected: true` にする時は `skills[]` に採用した skill 名を**必ず**列挙する（空・省略は不可。省略を全採用とみなさない — 「デフォルト非採用」の逆転を防ぐ）。
- 書いたら機械検証する: `bash <本スキル dir>/scripts/provenance-check.sh --selection <対象の絶対パス>/.claude/harness-selection.json`（全要素の網羅・値域・`depends_on` 充足・repo-specific ⇔ excluded・skill-group の `skills[]` を検査。`soft_depends_on` の欠落は WARN として表示）。既定パスはスクリプトの位置から解決するので cwd はどこでもよい。推奨配置（移植元 clone が対象の `.setup-automate/` にある）なら対象ルートで `bash .setup-automate/.claude/skills/agent-harness-bootstrap/scripts/provenance-check.sh --selection "$PWD/.claude/harness-selection.json"`。
- **対象側のコミット / gitignore**: `harness-selection.json`・生成 CLAUDE.md・`.claude/rules|skills|commands|settings.json`・採用した `files[]`（`workflows/software-development/` 等）は対象にコミットする。移植元 clone の `.setup-automate/` と、handoff 規約採用時の `.tmp/` は `.gitignore` に追加する（未追加なら Step 8 で追記し、最終報告に明記する）。

## 0-5. 以降の手順との接続

- Step 1〜8 は **selected な要素だけ**を対象にする。非選択の author-preference 要素は rules 条文・hooks・template のブロック・skills コピー・付随 `files` のいずれにも現れてはならない（「念のため」の持ち込み禁止）。
- Step 8-2 の rules 表には「要素 id」列がある。各条文は対応 id が selected の時だけ生成し、id 列の要素が全て非選択のファイルは作らない。
- 選択した要素の `target_contract`（台帳に定義された契約語句・ファイル・`@import`・`paths:`）を生成物に必ず含める。語句は言い換えずそのまま使う（`provenance-check.sh --target` が正規表現で検査するため）。
- `template.md` の各ブロックには対応する要素 id が `<!-- id: ... -->` で付いている。非選択 id のブロック（複数 id の行はその断片）は削除する。
- `rubric.md` の各項目には要素 id 列がある。**id 列の全要素が非選択の項目**は「opt-out 宣言済み」として Y 扱い。1 つでも選択されていれば、選択された id の観点で Y/N を判定する。Step 7 のレビュアにも `harness-selection.json` の完全パスを渡し、同じ基準で判定させる。
- skills / commands のコピー: 各要素の `skills[]` / `commands[]` を対象の `.claude/skills/` / `.claude/commands/` へコピーする（`skill-group` は選択記録の `skills[]` に列挙したものだけ）。`files[]` は**同じ相対パス**へコピーする（参照元の SKILL.md / command がそのパスで Read するため。対象に `workflows/software-development/` 等が生まれるが、台帳登録済みの付随物であり突合レビューの「混入」判定からは除外される）。台帳の summary / note で「対象固有に調整する」とある要素（例: `skill-review-gate` の criteria JSON）は対象固有に調整する。`third-party` は無改変で LICENSE と作者表記を保つ。
- Step 8 の最終報告に「選択記録の完全パス」「群 C で採用した要素の一覧」「群 A・B で外した要素と理由」「`decided_by: scale` で落とした要素」を含める。

## 0-6. 再セットアップ・同期時

再同期には移植元 clone が要る（`provenance.json` と `provenance-check.sh` はそこにしか無い）。推奨配置なら対象の `.setup-automate/` で `git pull` する。gitignore されているため無いメンバーは同じ場所に再 clone する。対象に `harness-selection.json` が既にある場合は先に Read し、`selected: false, decided_by: "user"` の要素を**再提案しない**（ユーザーが「再検討したい」と明示した時のみ再提示）。台帳側に新要素が増えていれば `--selection` 検証が「entry が無い」と報告するので、その新要素だけを提示して追記する。`decided_by: "scale"` で落とした要素は前提（規律の有無・規模）が変わりうるので再同期時に再提示してよい。

## 突合レビュー（移植完了後）— `harness-setup-review` skill が担う

手順の本体は `.claude/skills/harness-setup-review/SKILL.md`。要点:

1. **機械検査**: `bash <本 clone>/.claude/skills/agent-harness-bootstrap/scripts/provenance-check.sh --target <対象の絶対パス>`（C11 + C12。決定的）
2. **別エージェントの突合レビュー**: 渡すのは **対象パス 3 点と観点定義のパスの計 4 点のみ**（このリポジトリの `provenance.json` / 対象の `harness-selection.json` / 対象ルート / `criteria/porting-reconciliation.json`）。会話履歴・実装意図・本スキルの他の部分は渡さない。レビュアは `review-gate` と同じ手順で criteria を検証し JSON で結果を返す（must_pass 全合格かつ min_score 以上で PASS）
3. **既存 skills の監査**: 対象に setup 前から `.claude/skills/` があれば `skills-audit` で公式準拠を監査し、tier を報告に添える
4. 1 と 2 の両方 PASS で `harness-setup-state.sh verify --machine PASS --review PASS` → `done`。FAIL なら findings を修正して 1 から再実行。3 回 FAIL で中断してユーザーに報告する（対象で `issue-lifecycle` が選択済みなら起票、非選択なら報告のみ）

強制: この clone の Stop hook（`scripts/hook-stop-setup-gate.sh`）が `done` 前の終了を block する。
