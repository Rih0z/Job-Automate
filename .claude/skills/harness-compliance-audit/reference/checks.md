# checks.md — 機械検査 id と公式原則の対応、エージェント判定の観点

公式原則の SoT は `.claude/skills/_shared/anthropic-best-practices.yaml`（または `.json`）。

## 機械検査（scripts/harness_check.sh）

check id ごとの対象・検査内容・対応する principle id は **`reference/checks.json`（SoT）** に構造化データとして持つ。check を追加・変更する時は先に `checks.json` を更新する（`scripts/test_new_checks.sh` の B15 が `harness_check.sh` の emit id との一致を検査する）。本ファイルには表を重複して書かない。

## エージェント判定の観点（種別ごとの最低限）

reviewer は SoT の該当 category の principle を全件照合したうえで、少なくとも次を確認する。

- **skills / commands**: description が「何をするか＋いつ使うか」を先頭に持つ／本文は宣言的で検証可能／詳細は補助ファイルへ分割／`metadata` に動作規範を置かない／副作用の有無と `disable-model-invocation`・`user-invocable`・`allowed-tools` の整合／他 skill・rules と矛盾しない。
- **CLAUDE.md**: 各行が「消したら Claude が間違えるか」を満たす／一般論・コードから分かることが無い／矛盾する指示が無い／強調は本当に必要な行だけ／複数手順や部分適用の内容は skill か path-scope rule へ。
- **rules**: 1 ファイル 1 トピック／`paths:` が本文の対象と一致／常時 load 分は簡潔／frontmatter は `paths` のみ／常時 load の rules を `@import` で二重指定していない。
- **agents**: 役割・渡す情報・返す形式が自己完結（会話履歴に依存しない）／書き込みを禁じたい役割は `tools` / `disallowedTools` で制限されている（依頼文だけに頼らない）。
- **hooks**: 「毎回・例外なく」かつ「機械的に pass/fail」のものだけを hook にしている／advisory で足りるものを hook にしていない／スクリプトを絶対パスで呼び変数を引用している／ユーザーへの通知は `systemMessage`（exit 0 の stderr は誰にも見えない）／Stop hook は `stop_hook_active` を読み、自前のカウンタを turn ごとにリセットする。

## 減点規則（review-result/v1 の score）

100 − blocker×20 − major×10 − minor×3（下限 0）。blocker が 0 件で `verdict: PASS`。severity の目安: blocker = 公式原則に反し動作や発見性を壊す（frontmatter 欠落・矛盾する指示・500 行超）、major = 原則違反だが動作はする（description に「いつ」が無い・強調過多）、minor = 改善提案、info = 参考。
