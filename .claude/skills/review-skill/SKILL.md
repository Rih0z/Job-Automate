---
name: review-skill
description: |
  作成・変更した skill を、別エージェント（readonly-reviewer）に 5 軸・100 点で採点させ、
  合否の記録を .claude/review-history/skill-review/ に保存する。作成者本人はレビューしない。
  skill を作った・直したあとに使う。全 skill の一括仕分けは skills-audit、直近の変更の公式準拠監査は harness-compliance-audit。
  Trigger phrases: 'Skillをレビューして', 'skill品質チェック', 'review-skill',
  'ベストプラクティス準拠確認', '公式準拠レビュー'.
disable-model-invocation: true
allowed-tools: Read, Glob, Grep, Agent, Bash(python .claude/skills/review-skill/scripts/skill_review_gate.py:*), Bash(python .claude/skills/review-skill/scripts/append_skill_review_record.py:*)
argument-hint: "[skill 名...（省略時は gate が未レビューと判定した skill）]"
metadata:
  provenance: official-derived
---

# /review-skill — skill の別エージェントレビューと記録

採点の観点・配点・合格条件・レビュアーへの固定依頼文は `criteria/skill-quality.json` が正本。この SKILL.md に観点を重ねて書かない。
散文版は `workflows/software-development/review-skill.md` の生成区間（`render_review_skill_md.py` が JSON から作る。手で直さない）。
判定の根拠となる公式原則は `.claude/skills/_shared/anthropic-best-practices.json`。

作成者がこの session でレビューしない。必ず Agent ツールで別エージェントを起動する。

## 手順

skill 1 つにつき、次を順に行う。

1. 現在の内容 hash を取る: `python .claude/skills/review-skill/scripts/skill_review_gate.py --hash SKILL名`。この値を手順 4 まで保持する。
2. Agent ツールで `subagent_type: readonly-reviewer` を起動する（定義が無い環境では general-purpose で起動し、依頼文の冒頭に「ファイルを作成・変更・削除しない」と書く）。
   - prompt は `criteria/skill-quality.json` の `reviewer_requirements.fixed_prompt` に、対象 skill ディレクトリの絶対パスと criteria の絶対パスの 2 つだけを添える。
   - 作成意図・設計判断・会話履歴・自己評価は渡さない（`forbid_to_reviewer`）。skill の内容の埋め込みもしない。
3. レビュアーが返した JSON（`output_schema` の形）を `.tmp/` 配下のファイルに UTF-8 で保存する。Agent の結果から agent_id を転記する。取れなければ `unavailable`。
4. 記録を保存する:
   `python .claude/skills/review-skill/scripts/append_skill_review_record.py --skill SKILL名 --expected-hash HASH --result-file .tmp/result.json --agent-id ID --subagent-type readonly-reviewer --model MODEL`
   - 保存前に、結果の JSON に他プロジェクト由来の会社名・顧客名・個人名が混ざっていないか grep で確かめる（公開 repo）。
   - レビュー中に skill が編集されていたら hash が合わず拒否される。再度手順 1 から行う。
   - 保存時刻と content_hash は script が付ける。拒否されたら理由を読んで直す。同じ結果の再保存は「記録済み」で成功する。
5. verdict が FAIL なら、指摘を直して手順 1 からやり直す。skill を 1 バイトでも直すと hash が変わり、前の記録は失効する。回数で止めず PASS まで続ける。

結果はレビュアーの出力をそのまま報告する。要約や解釈を足さない。

## gate と hook

- `python .claude/skills/review-skill/scripts/skill_review_gate.py --all` で全 skill の状態を見る（PASS・FAIL・INVALID・BASELINE_DEBT・STALE・UNREVIEWED）。`--strict` は PASS と BASELINE_DEBT 以外があれば exit 1。
- Stop hook（`scripts/hook-skill-review-gate.sh`）は、未レビューの skill があると turn の終了を最大 3 回 block する。1 turn に 1 skill ずつ依頼する。上限に達すると未レビュー名を通知して通す。SessionStart では件数と整合検査の結果を表示する。
- gate の exit 0 は、全 skill が別エージェントのレビュー済みという意味ではない。負債台帳（`.claude/review-history/skill-review/baseline-unreviewed.json`）にある skill は、内容が登録時と同じ間だけ免除される。
- hook が想定外に block し続けるときは、`.claude/settings.json` の Stop と SessionStart にある本 hook の登録 2 行を外す。外したら整合検査（`check_skill_review_consistency.py`）の hook_registration が NG になるので、直したあとに戻す。
- 整合検査は `python .claude/skills/review-skill/scripts/check_skill_review_consistency.py`（criteria と生成 md のずれ、principle id、台帳、hook 登録、スキーマ）。

## 負債台帳の修正

台帳の `--verify-ledger` は、台帳を最後に追加した commit の内容を基準にし、基準に無いエントリや書き換えを改ざんとみなす。台帳にある skill を編集した場合は、免除が失効して UNREVIEWED になるので、そのままレビューすれば PASS になる（台帳の修正は不要）。
初回の誤りの訂正など、台帳そのものを直すときは利用者の承認を得て、旧台帳を削除する commit と新台帳を追加する commit に分ける。新台帳の追加 commit が新しい基準になる。

## 制約

- gate・記録・hook はこの repo 固有の構成に依存する。`~/.claude/skills/` へコピーしても動くのは reviewer 起動の手順だけで、gate は働かない。
- gate の対象は `.claude/skills/` 直下の skill のみ。CLAUDE.md・agents・hooks 設定のレビュー記録は対象外。
- レビュアーの独立性は固定依頼文で標準化するだけで、機械では強制できない。記録の偽造や gate 自体の書き換えは検出できない。

## Examples

- 「新しく作った skill をレビューして」: `--hash` で hash を取る、readonly-reviewer を起動する、返ってきた JSON を `--expected-hash` つきで保存する、`--all` で PASS を確かめる。
- Stop hook が未レビューの skill 名を挙げて block した: 挙げられた skill のうち 1 つを上の手順で処理して終了する。残りは次の block で依頼される。
