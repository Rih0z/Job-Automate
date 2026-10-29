# T28（regression）test_existing_checks_unchanged の実行手順

自動の unittest にしない。既存の検査を、実装の前後で実行して結果を比べる手順書（計画書 §4 の T28）。unittest の discover 対象外（ファイル名が test で始まらない）。

## 手順
1. 実装前の基準ログ: `.tmp/close-verify/skill-review-gate/t28-before.log`（取得済み。下の 5 つの実行結果・実行日時・HEAD を含む）。
2. 実装後（hook 登録の前と後）に同じ 5 つを実行して `.tmp/close-verify/skill-review-gate/t28-after.log` に保存する。`python .claude/skills/review-skill/scripts/tests/compare_t28.py --capture .tmp/close-verify/skill-review-gate/t28-after.log` で同じ形式（コマンド・exit・FAIL 件数・WARN 件数・実行日時・HEAD）のログが取れる。
3. 比較: `python .claude/skills/review-skill/scripts/tests/compare_t28.py .tmp/close-verify/skill-review-gate/t28-before.log .tmp/close-verify/skill-review-gate/t28-after.log`（増えていれば非ゼロ）。
4. 完了条件（必須）: **t28-after.log が close 時に存在し**、5 つとも FAIL 件数・WARN 件数が基準ログと同じか少ない（compare_t28.py が 0 で終わる）。
   - 基準ログの時点で `provenance-check.sh` は FAIL 1 件（C6: select-slop-viewpoints が台帳に未登録）。これは実装前からあるので基準。増えないことを確かめる。
5. `list_review_records.py` は、新設の `.claude/review-history/skill-review/`（負債台帳 `baseline-unreviewed.json` を含む）が存在する状態で、例外を出さず終了すること（出力が NO_PRIOR_RECORDS か一覧）。

## 実行コマンド（repo ルートで。実際に動いた形）
1. `python .claude/skills/_shared/scripts/check_compliance_status.py`（出力末尾の SUMMARY 行に violations=N）
2. `bash .claude/skills/harness-compliance-audit/scripts/harness_check.sh .claude/skills/review-skill/SKILL.md CLAUDE.md`（明示パスを渡す。範囲記法は使わない。末尾の SUMMARY 行に FAIL=N WARN=N）
3. `bash .claude/skills/agent-harness-bootstrap/scripts/provenance-check.sh`（FAIL 行の件数）
4. `bash .claude/skills/agent-harness-bootstrap/scripts/hook-stop-setup-gate.test.sh`（末尾の PASS=n FAIL=m。python の起動が遅い環境では 10 分以上かかるので background で実行する）
5. `python .claude/skills/_shared/scripts/list_review_records.py --target review-skill`（`--target` が必須。NO_PRIOR_RECORDS か一覧で exit 0）

## 注意
- 実行はメイン作業ツリーで行い、結果の記録以外に repo を変更しない。
- 他の session が python を大量に起動していると 1 回の python 起動が数十秒かかる。時間はぶれるので、件数だけを比べる。
