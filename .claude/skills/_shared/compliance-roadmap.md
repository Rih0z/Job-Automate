# Job-Automate — Anthropic 公式ベストプラクティス準拠ロードマップ

> Job-Automate 自身（このリポジトリ）の公式ベストプラクティス逸脱・改善バックログを追跡する living document。`.claude/skills/_shared/anthropic-best-practices.json`（34 原則）を判定基準の SoT とする。ported プロジェクトはこのファイルの中身を持ち込まず、自分自身の監査を実行して自分の roadmap を作る（`provenance.json` の `shared-compliance-roadmap` 要素は `portable: false`）。

## 再監査手順

2 段階に分ける（毎回フル判定にすると one-subagent-per-file の fan-out コストが常に発生するため）。

- **軽量スイープ（機械検査のみ・頻繁に実行可）**: `.claude/` / `CLAUDE.md` に触れるセッション開始時、または最低月次で実行。
  ```bash
  bash .claude/skills/harness-compliance-audit/scripts/harness_check.sh $(find .claude CLAUDE.md -type f)
  ```
  純粋にパス・内容ベースの決定的チェックなので、このリポジトリの規模（約60ファイル）なら全件実行しても軽い。実行日と FAIL/WARN 件数をこの表の「最終確認」列に記録する。
- **フル判定スイープ（別エージェント判定つき・低頻度）**: 四半期に一度、または軽量スイープで新規 FAIL が出た時。`skills-audit`（リポジトリ全体）または `harness-compliance-audit`（特定ファイル指定）を実行し、新規の finding をこの表に追記する。

## Findings

| ID | Finding | 原則 | 優先度 | 状態 | 備考 |
|---|---|---|---|---|---|
| CR-01 | `.claude/commands/*.md`（3件、旧形式・frontmatter無し）が公式ガイダンス「commands は skills に統合済み」に反する | `skills.file-location-and-precedence` | High | **done**（2026-09-11） | `.claude/skills/{review-changes,review-implementation,review-skill}/SKILL.md` へ移行。`provenance.json` の `review-commands`/`command-review-implementation` を `kind:"command"→"skill"` に更新。移行後の別エージェントレビュー（review-skill 自身）で B(78)/A(86)/A(81) を確認、指摘（後述 CR-06〜08）は反映済み |
| CR-02 | 34/53 skills の `description` が 250 文字超（本リポジトリ独自の `skill-authoring-guide` 目安。公式の上限は description+when_to_use 合計 1,536 文字で、いずれも遠く及ばない） | `skills.description-key-use-case-first`（style 目安であり違反ではない） | Low | open / backlog | 他の理由でそのスキルを触る時に機会があれば整える。一括修正はしない |
| CR-03 | 3 skills（`skill-authoring-guide`/`three-agent-tdd-workflow`/`ui-design-guidelines`）が副作用語検出で `disable-model-invocation` 欠如を機械的に疑われたが、実地確認の結果いずれも「pre-publish checklist」等のチェックリスト名称・内部シミュレーション上の hand-off であり実際の副作用ではない | `skills.side-effect-workflows-manual` | Low | **done**（false positive 確認済み・編集不要） | 再監査時に再度浮上したら同じ結論を確認するだけでよい |
| CR-04 | `CLAUDE.md` の「レビュースキル一覧」節が全体の約46%（常時 load） | `claude-md.on-demand-goes-to-skills` | Medium | **done**（2026-09-11） | README.md へ集約しポインタ化。174行→99行（公式目標 <200 行に対し余裕あり） |
| CR-05 | `.claude/skills/agent-harness-bootstrap/provenance.json` が1,447行で skill ツリー中最大。移植レビュー等で全文がエージェントに渡る場面がある | （SKILL.md 500行ルールは非該当。structured lookup data） | Low / long-term | open / backlog | `provenance-check.test.sh`（52 tests）がこのファイルの厳密な構造に依存するため、再構成は「意味を変えずに分割する」計画と再テストが前提。今は着手しない |
| CR-06 | `workflows/software-development/review-changes.md`・`review-implementation.md` に `dev/`・`docs/` 配下への死んだパス参照が多数残存（2026-07-31 の `workflows/` 構造への再編で取り残された既存債務）。これらのファイルはレビューエージェントへのプロンプトに丸ごと埋め込まれるため、修正前は実際に誤ったパスをエージェントに渡していた | （公式原則の直接該当なし。品質・正確性の一般論） | High | **done**（2026-09-11、CR-01 移行時の別エージェントレビューで発見・即修正） | 全 `dev/design/*`・`dev/three-agent/*`・`dev/rules/*`・`docs/review-*.md` を `workflows/` 配下の実在パスへ修正済み。修正後の残存チェック済み（grep 0件） |
| CR-07 | `review-skill/SKILL.md` の収集項目「README.md のドキュメント反映状況」が README.md に存在しない節を指す実行不能な指示だった | `skills.progressive-disclosure` の実用性側面 | High | **done**（2026-09-11） | 「対象スキルが一覧テーブルに実際に記載されているか」という具体的な確認項目に書き換え |
| CR-08 | `review-changes/SKILL.md` に出力テンプレートが無く、他2件（review-implementation/review-skill）と非対称だった。3件とも `## Examples` 節が0件だった | `skills.progressive-disclosure`（構造の一貫性） | Medium | **done**（2026-09-11） | review-changes に採点表+出力フォーマットを追加。3件とも Examples 節・相互の対象範囲の違いを追記 |
| CR-09 | `harness_check.sh` の `fm_get()`（shell の単一行 grep ベース）が YAML block scalar（`description: \|`）を正しく読めず、`S05`/`S06` を誤判定する（実測: 文字数が実際は数百文字のところ「1 文字」と出る） | （ツール自体の限界。原則 `skills.frontmatter-fields` の検査手段の不備） | Low | **done**（2026-09-15） | `fm_get()` を YAML block scalar 対応（`\|` `\|-` `\|+` `>` `>-` `>+` の6種、次の桁0キーまで収集）の awk 実装に置換し、`when_to_use` 専用の別抽出awk（`next`で1行値を欠落させる潜在バグ持ち）も `fm_get()` 呼び出しに一本化。単体テスト `test_fm_get.sh`（23ケース）で Red→Green を確認。全56 SKILL.md への before/after diff: FAIL増加なし、WARN 47→46（`server-init` の S06 が WARN→PASS）、他は S05 の文字数表記が実測値に修正されるのみ（判定結果は不変） |
| CR-10 | `.claude/skills/specification/SKILL.md` が commit/push/deploy 系の語を含むが `disable-model-invocation` が無い（closing sweep で新規検出） | `skills.side-effect-workflows-manual` | Low | **done**（false positive 確認済み・編集不要、2026-09-15） | 実地確認: 該当語は `deploy` 1件のみで、生成対象の技術仕様書テンプレート内コード例のフィールド名（`deployment: "[アプリストア/Web/その他]"`）であり、Claude が実際にデプロイ操作を実行する指示ではない。CR-03 と同型の誤検知 |
| CR-11 | 11 skills の frontmatter に山括弧プレースホルダ（`<...>` 等）があり、XML 風タグを拒否する一部配布経路（claude.ai アップロード等）で問題になり得る | `skills.spec-fields-outside-claude-code` | Low | open / backlog | Claude Code 専用利用なら実害なし。claude.ai 等への配布を計画する時にまとめて対応 |
| CR-13 | CR-09 の修正（`fm_get()`）が `sed -E '1{s/^"(.*)"$/\1/}'` という GNU sed 前提の block 構文を使っており、BSD sed（macOS 標準）では `bad flag in substitute command: '}'` で無条件に失敗していた。この1点の失敗が `name`/`description` 抽出を丸ごと壊し、macOS で全リポジトリスイープを実行すると **56 skills 全件が S02/S03/S05 で FAIL**（FAIL=168）になる一方、`test_fm_get.sh`（23ケース）も同一環境で **22/23 FAIL** していた。CR-09 の「Red→Green 確認」「FAIL増加なし」は GNU sed/awk 環境（Linux）でのみ成立しており、macOS では未検証のまま "done" と記録されていた | （公式原則の直接該当なし。クロスプラットフォーム正確性の一般論。本リポジトリは Windows 標準化手順等も抱えるためクロスプラットフォーム動作が前提） | High | **done**（2026-09-16、macOS/BSD sed で再現・修正） | `1{s/.../}"` の block 構文を `1 s/.../` （アドレス直接指定、`{}` 無し）に変更するだけで GNU/BSD 両対応になることを確認。`test_fm_get.sh` 23/23 PASS、全リポジトリスイープ FAIL=168→0（WARN も 48 に復帰、内訳は CR-09 の記録どおり）で確認済み。**教訓**: shell スクリプトの CR close 時、`bash`/`sed`/`awk` の GNU 実装依存を疑い、可能なら BSD 環境（macOS）でも実行して確認する一文を再監査手順に追加検討 |
| CR-12 | 工程順序（設計 → テスト設計 → テスト実装(Red) → 実装）の強制がレビュアー判定のみで、機械的な検査がない。ゲートを飛ばしても検出されない | `hooks.deterministic-zero-exceptions` | Medium | open / backlog | 候補: `review-gate/SKILL.md` が定めるコミットメッセージ規約 `review-gate:<stage> PASS <score>` を commit 直前の hook で検査する（該当工程の行が無ければ block）。誤検出（docs のみの変更・規約導入前のコミット）の除外条件を先に決める必要がある。次のフル判定スイープ（四半期）で再検討。それまでは `review-gate/SKILL.md` の「強制の限界」の表記で運用する。**関連 (2026-09-14 追加)**: レビュー結果自体（観点別合否・出典URL・要約）の永続化は `review-record/v1`（`.claude/skills/_shared/review-record.schema.json` + `.claude/review-history/`）で対応済み（`research-deliverable-review`/`source-verification-scan`/`staged-investigation-workflow` に導入）。本CR-12が指す「工程順序の通過そのものの機械的検査」は別課題として残る。`review-gate` が同機構を採用する場合は同じスキーマ・スクリプトをそのまま流用できる |

## 直近の監査ログ

| 日時 | 種別 | 結果 |
|---|---|---|
| 2026-09-11 | 軽量スイープ（`harness_check.sh` 移行対象ファイルのみ） | FAIL=0 WARN=7（CR-09 起因の S06 ×3、BP02 ×1、既知の残存WARN） |
| 2026-09-11 | フル判定（`/review-skill` を CR-01 移行対象3件に実行） | B(78)/A(86)/A(81) → 指摘反映後 再検証は軽量スイープで完了（CR-06〜08 参照） |
| 2026-09-11 | 軽量スイープ（`harness_check.sh` 全リポジトリ・98 targets、本ロードマップ運用の初回ベースライン） | FAIL=0 WARN=49（S06 ×35 = CR-09、S10 ×11 = CR-11、S08 ×1 = CR-10、H01 ×1 python 未検出・BP02 ×1） |
| 2026-09-16 | 軽量スイープ（macOS/BSD sed 環境・102 targets、pull 直後の再監査） | **実行直後は FAIL=168**（56 skills 全件 S02/S03/S05、CR-13 の BSD sed 非互換が原因）→ CR-13 修正後 FAIL=0 WARN=48 に復帰。`test_fm_get.sh` も同時点で 22/23 FAIL → 修正後 23/23 PASS |
