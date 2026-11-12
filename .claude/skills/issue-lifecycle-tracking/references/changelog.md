# issue-lifecycle-tracking の更新履歴

- 1.6.0 (2026-11-12): 公式ベストプラクティス（skills / authoring）に合わせて SKILL.md を整理した。script の呼び出しを `${CLAUDE_SKILL_DIR}` にし、「してはいけないこと」を状態遷移の直後へ移し、同じ規則の重複をまとめ、重複の取り下げの既定を `merge` に揃え、「Issue」の表記を「issue」に、md の相互リンクを本文の「関連:」欄に揃えた。数値目標と連続 FAIL の節を `references/related-practices.md` へ、更新履歴をこのファイルへ移した。棚卸しに再実行のループを、CLAUDE.md から移した discovery-log の見返しの手順を「作業中に別件に気づいた時」節に足した。script は、stage した台帳を読めない時・base の台帳を読めない時（JSON 不正・UTF-8 でない・ファイルを開けない）に `check-new`・`request` が exit 2 で止まるようにし、BOM 付きの台帳を読み書きできるようにし、想定外の例外を exit 2 にし、`..` を含む前提のパスを「前提のパスが不正」として出すようにした。既定値の根拠を `--help` に書いた
- 1.5.0 (2026-11-12): 棚卸しの `issue_tracker.py triage`（読み取り専用。優先度順・前提が崩れた候補・確認が古い・欄の欠け・重複の候補）と、任意の欄 `priority` / `reviewed` / `premise` / `resolution` / `superseded_by`、JSON の終端 `obsolete` を足した。withdrawn の理由に「前提が変わった」を足した。起票時に前提のファイルを `premise` か本文のパスで書く
- 1.4.0 (2026-11-11): 起票の前に関連 issue を確かめる `scripts/issue_tracker.py`（related / request / merge / check-new。設定 `.claude/issue-tracker.json`、試験 `scripts/test_issue_tracker.py`）と、「関連:」欄・「## 利用者の要望」節を足した。close・取り下げ・統合の最後に handoff の `release` を入れた。設定の書き方 `references/issue-tracker-config.md`、hook が無い時の手順、「してはいけないこと」の節を足した
- 1.3.1 (2026-10-30): closed 後の再現は新規起票に統一、取り下げ専用の終端 `withdrawn/` を追加（検証記録は不要）
- 1.3.0 (2026-10-30): repo 固有の依存を「前提と代替」の表に集約し最小動作の手順を追加、open から closed への直行不可を明記、エラー対処を表に拡充
- 1.2.0 (2026-10-30): description を用途・トリガー・使わない場面に絞った。repo 固有のパスの読み替え方、close と検証 FAIL と重複起票の例を追加
- 1.1.0 (日付は未記録): 前提節、応答形式、本文テンプレート（references/）を追加
- 初版 (2026-09-03): 実運用プロジェクトでの知見を一般化して追加
