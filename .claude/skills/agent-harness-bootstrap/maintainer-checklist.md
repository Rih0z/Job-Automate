# 本スキルのメンテ checklist（プロンプト管理者向け）

本スキル（`SKILL.md` + supporting files）を更新する人向け。**生成される CLAUDE.md の評価には関係しない**（生成物の評価は `rubric.md` を使う）。

- [ ] Step 7 で WebFetch が要件化されているか
- [ ] Step 8 で `/clear` + handoff 保存が指示されているか
- [ ] handoff 規約（ファイル名 `[YYYY-MM-DD]-issue-[ID]-[識別単語].md`、次 handoff 作成まで保持、issue ファイルへの完全パス記載）が一貫しているか
- [ ] skills 更新時の公式 Skills ガイド WebFetch レビューが要件化されているか
- [ ] 「公式準拠の核」と「独自運用」のラベル分離が崩れていないか
- [ ] emphasis（IMPORTANT / YOU MUST）が本スキル全体で 5 件以下か（語気強め「必須・禁止・削除不可・絶対」も平叙文化されているか）
- [ ] 公式内容（文言・テーブル・数値・API 契約）を焼き込まず実行時 WebFetch 取得に統一されているか（verbatim・テーブル転記が残っていないか）
- [ ] handoff 受領が user 明示指示駆動で、SessionStart hook がポインタ + verdict のみ注入（本文を注入しない）になっているか
- [ ] reviewer 過剰報告抑制（correctness / 明示要件に関わる gap のみ採用）が含まれているか
- [ ] 行数による出力拒否ゲートが残っていないか（公式は数値閾値を持たない）
- [ ] hooks 化判断が `hooks-reference.md` にあり、参考 6 hook 構成と監査手順（dead/無駄 hooks 検出）+ **OS 別 shell 実装（Windows PowerShell / Mac・Linux bash）**が含まれているか
- [ ] スケール調整（小規模では rules / hooks / オプションを間引く）が生成手順の最初に位置づけられているか
- [ ] PC 再起動・session 復元（SessionStart hook は processing scan をポインタ + verdict のみ注入＝本文非注入 → User 通知 + 選択後 1 件のみ Read + 並列委任）が含まれているか
- [ ] Step 8 で採用セット（CLAUDE.md / コア rules / 採用オプション / settings.json hooks + hook scripts）の実生成手順と雛形が含まれているか
- [ ] [claude-code Issue #23478](https://github.com/anthropics/claude-code/issues/23478) の path-scope auto-load Read 時のみ発火 bug が URL 付きで明示されているか
- [ ] `governance.md` 生成指示が複数観点の項目群（増減可）で記述されているか
- [ ] 常時 load rules ファイル個別の 5KB soft cap が明示されているか
- [ ] `execution-routing.md` / `docs-management.md` のオプション扱い（採用判定基準と生成内容）が明示されているか
- [ ] 関連 docs 読込宣言が「最初と最後の両方」になっているか
- [ ] 条文宣言の lazy load 運用（全条一括宣言は不要）が明示されているか
- [ ] 並走 agent 痕跡 4 軸 recheck が独自運用 + hook 仕様 + テンプレートに含まれているか
- [ ] 成果物の生成主体明示が独自運用 + test-verify.md 生成指示に含まれているか
- [ ] close 前検証 4 段（再現→pass / negative test / regression smoke / 証拠アーカイブ）が含まれているか
- [ ] 別エージェントレビューが 2〜4 本並列 + TDD test-first + ループ上限で記述され、レビュアに渡すのが対象完全パス + レビュー用 skill のみになっているか
- [ ] stale handoff 誤受領防止が含まれているか
- [ ] 特定の社内プロダクト名・実在企業/製品名が本文に混入していないか（汎用・匿名の維持）
- [ ] Progressive Disclosure が維持されているか（SKILL.md 本体 500 行未満・出力テンプレート/ルーブリック/hooks/メンテ checklist は supporting files に分離）
- [ ] スキル名に `claude` / `anthropic` が含まれていないか（kebab-case）
