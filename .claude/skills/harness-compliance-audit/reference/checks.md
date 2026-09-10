# checks.md — 機械検査 id と公式原則の対応、エージェント判定の観点

公式原則の SoT は `.claude/skills/_shared/anthropic-best-practices.yaml`（または `.json`）。下表の「原則」列は SoT 内で照合する箇所（category と要点）で、principle id は SoT のものを使う（id の採番はリポジトリごとに異なるため、ここでは固定しない）。

## 機械検査（scripts/harness_check.sh）

| id | 対象 | 検査 | 原則（SoT の category・要点） |
|---|---|---|---|
| BP01 | repo | 公式原則キャッシュの存在 | best-practices: 判定基準は日付付きの構造化データで持つ |
| BP02 | SoT | `fetched` が `max_age_days` 内か | 同上（refetch_when） |
| C01 | CLAUDE.md | 200 行未満（超過は WARN） | memory: target under 200 lines |
| C02 | CLAUDE.md | `@import` 先の実在（欠落は FAIL） | memory: imports |
| C03 | CLAUDE.md | 強調語（IMPORTANT / YOU MUST）が 3 箇所超なら WARN | best-practices: emphasize one line, not many |
| C04 | CLAUDE.md | 見出しで構造化されているか | memory: headers and bullets |
| R01 | rules | frontmatter の description | memory: rules の description |
| R02 | rules | `paths:` の有無（path-scope か常時か）を表示 | memory: path-specific rules |
| R03 | rules | 200 行超は WARN（1 ファイル 1 トピック） | memory: one topic per file |
| S01 | SKILL.md | frontmatter の存在（無しは FAIL） | skills: SKILL.md structure |
| S02 | SKILL.md | `name` = ディレクトリ名 | skills: name matches directory |
| S03 | SKILL.md | `name` は kebab-case | skills: naming |
| S04 | SKILL.md | `name` に claude / anthropic を含まない | skills: reserved words |
| S05 | SKILL.md | `description`+`when_to_use` ≤ 1,536 文字・description 必須 | skills: description limit |
| S06 | SKILL.md | description に「いつ使うか」がある（無ければ WARN） | skills: description says what and when |
| S07 | SKILL.md | 500 行未満（超過は FAIL） | skills: progressive disclosure |
| S08 | SKILL.md | 副作用語（commit/push/deploy 等）があるのに `disable-model-invocation` が無ければ WARN | skills: disable-model-invocation |
| S09 | SKILL.md | `$ARGUMENTS` を使うのに `argument-hint` が無ければ WARN | skills: argument-hint |
| S10 | SKILL.md | frontmatter の山括弧プレースホルダは WARN（XML 風タグを拒否する配布経路への配慮・公式原則ではない） | — |
| S11 | SKILL.md | 本文リンク先（references/ scripts/ assets/）の実在（欠落は FAIL） | skills: supporting files |
| K01/K02 | commands | description の有無・山括弧 | skills: commands も同じ frontmatter 規則 |
| A01 | agents | name / description の存在 | sub-agents: frontmatter |
| H01/H02 | settings.json | JSON 妥当性・hook script の実在 | hooks: deterministic, command must exist |

## エージェント判定の観点（種別ごとの最低限）

reviewer は SoT の該当 category の principle を全件照合したうえで、少なくとも次を確認する。

- **skills / commands**: description が「何をするか＋いつ使うか」を先頭に持つ／本文は宣言的で検証可能／詳細は補助ファイルへ分割／`metadata` に動作規範を置かない／副作用の有無と `disable-model-invocation`・`user-invocable`・`allowed-tools` の整合／他 skill・rules と矛盾しない。
- **CLAUDE.md**: 各行が「消したら Claude が間違えるか」を満たす／一般論・コードから分かることが無い／矛盾する指示が無い／強調は本当に必要な行だけ／複数手順や部分適用の内容は skill か path-scope rule へ。
- **rules**: 1 ファイル 1 トピック／`paths:` が本文の対象と一致／常時 load 分は簡潔。
- **agents**: 役割・渡す情報・返す形式が自己完結（会話履歴に依存しない）。
- **hooks**: 「毎回・例外なく」かつ「機械的に pass/fail」のものだけを hook にしている／advisory で足りるものを hook にしていない。

## 減点規則（review-result/v1 の score）

100 − blocker×20 − major×10 − minor×3（下限 0）。blocker が 0 件で `verdict: PASS`。severity の目安: blocker = 公式原則に反し動作や発見性を壊す（frontmatter 欠落・矛盾する指示・500 行超）、major = 原則違反だが動作はする（description に「いつ」が無い・強調過多）、minor = 改善提案、info = 参考。
