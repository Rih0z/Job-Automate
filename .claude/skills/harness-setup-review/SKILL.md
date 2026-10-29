---
name: harness-setup-review
description: "別プロジェクトへの harness セットアップ（agent-harness-bootstrap Step 0〜8）の完了後に、ユーザーが選択した全観点が対象の CLAUDE.md / rules / skills に反映されているか（抜けゼロ）と、非選択の著者嗜好が混入していないか（混入ゼロ）を検査する。機械検査（provenance-check.sh --target）と別エージェントの突合レビュー（criteria/porting-reconciliation.json）の両方が PASS するまで setup を完了扱いにしない（Stop hook が検証前の終了を block する）。対象に既存の skills があれば skills-audit で Anthropic 公式ベストプラクティス準拠も監査する。Use when the user asks to 'セットアップ結果をレビューして', 'harness-setup-review', '移植の抜けと混入を確認して', or immediately after agent-harness-bootstrap finishes generating for a target other than this repository."
allowed-tools: Read Bash Agent Glob Grep
argument-hint: "[対象プロジェクトの絶対パス]（省略時は進行中 setup の state から取得）"
metadata:
  provenance: official-derived
  version: "1.1.0"
  changelog: "1.1.0 使用例・エラー対処・出力形式を追加し、山括弧表記を除去"
---

# harness-setup-review — setup 後の抜け・混入レビュー

移植元（このリポジトリの clone）で実行する。前提として、clone 内の `.claude/skills/agent-harness-bootstrap/scripts/` 配下のスクリプトと bash・python が実在することを意図的に前提とする（対象プロジェクトへはスクリプトを持ち込まない設計）。対象プロジェクトへはコピーしない。公式ベストプラクティスの参照は `.claude/skills/_shared/anthropic-best-practices.json`（日付付きの構造化データ）を使い、判定前に `refetch_when` に該当していれば各 `source_url` の現行版で裏取りする。

## 入力

- 対象ルート `$ARGUMENTS`。省略時は `bash .claude/skills/agent-harness-bootstrap/scripts/harness-setup-state.sh show` の `target`。
- 対象の `.claude/harness-selection.json`（Step 0 の選択記録）。無ければ検査できないので中断し、Step 0 から実施するよう報告する。

## 手順（順序固定・省略不可）

1. **機械検査（決定的）**: 対象ルートで次を実行し、出力をそのまま記録する。

   ```bash
   bash [本 clone のパス]/.claude/skills/agent-harness-bootstrap/scripts/provenance-check.sh --target [対象の絶対パス]
   ```

   C11（選択記録: 全要素網羅・official は必ず selected・依存充足・skill-group の skills[]）と C12（生成物: 選択要素の契約語句・ファイル・`@import`・`paths:` の存在、非選択要素の語句・ファイル・ディレクトリ・skill の不在、id コメントマーカー残存禁止、`.setup-automate/` の gitignore）を評価する。FAIL 行があればそれが修正対象。
2. **突合レビュー（別エージェント）**: `Agent`（`readonly-reviewer`（`.claude/agents/readonly-reviewer.md`。定義が無い環境・未読込のセッションでは `general-purpose` で起動し、prompt 冒頭に「ファイルを作成・変更・削除しない」と明記する））を起動し、次の 4 点の完全パス**のみ**を渡す（会話履歴・実装意図・本 skill の本文は渡さない）:
   - 移植元 `.claude/skills/agent-harness-bootstrap/provenance.json`
   - 対象 `.claude/harness-selection.json`
   - 対象ルート
   - 観点定義 `.claude/skills/agent-harness-bootstrap/criteria/porting-reconciliation.json`

   レビュアには `review-gate` と同じ形式で「観点定義に従い対象を批判的にレビューし、JSON（score / verdict / must_pass_failures / findings / missing_perspectives）のみ返す」よう指示する。手順 1 の結果は渡さない（独立判断を保つ）。
3. **既存 skills の監査（対象に `.claude/skills/` が setup 前から存在した場合のみ）**: `skills-audit` を対象の skills に対して実行し、GOOD / MIGRATE / IMPROVE / SPLIT の tier を記録する。setup でコピーした skill は監査対象から外す（選択記録の `skills[]` と台帳の `skills[]` で判別）。監査結果は setup の合否には含めず、最終報告に「既存 skills の公式準拠状況」として添える。
4. **判定と state 更新**:

   ```bash
   bash [本 clone のパス]/.claude/skills/agent-harness-bootstrap/scripts/harness-setup-state.sh verify --machine [PASS または FAIL] --review [PASS または FAIL]
   ```

   - 両方 PASS → `phase=verified`。続けて `harness-setup-state.sh done` を実行し、完了報告へ進む。
   - いずれか FAIL → findings（file:line）を修正し、手順 1 から再実行する。`verify` は FAIL のたびに `fail_count` を進め、**3 回 FAIL で中断してユーザーに報告する**（対象で `issue-lifecycle` が選択済みなら `issues/open/` に起票、非選択なら報告のみ）。
5. **読み込みの確認（ユーザーに依頼）**: 対象ルートで Claude Code を新しく起動して `/context` を実行し、Memory files に生成した `CLAUDE.md` と常時 load の rules（frontmatter に `paths:` の無いもの）が載っていることを確かめてもらう（対話操作のため本 skill からは実行できない。依頼した事実と、結果を受け取った場合はその内容を完了報告に含める）。対象に `AGENTS.md` がある場合は、CLAUDE.md の `@AGENTS.md` で取り込まれていることも併せて確認してもらう。
6. **完了報告**: 機械検査の出力（PASS 行または FAIL 行）、突合レビューの score / verdict / findings、手順 3 の tier 一覧、手順 5 の確認依頼、`harness-selection.json` の完全パス、修正した箇所の完全パスを含める。

## 出力の型

突合レビューの返却 JSON（レビュアに指定する形式）:

```json
{"score": 0, "verdict": "PASS または FAIL", "must_pass_failures": ["観点 id と理由"], "findings": [{"file": "対象内の相対パス", "line": 1, "criterion": "観点 id", "issue": "内容", "fix": "直し方"}], "missing_perspectives": ["観点定義に無いが見るべき点"]}
```

完了報告の型（この順・この見出しで書く。余分な考察は足さない）:

1. 機械検査: PASS 行または FAIL 行の原文
2. 突合レビュー: score / verdict / findings の要約
3. 既存 skills の公式準拠状況: tier 一覧（対象外なら「対象外」）
4. 読み込み確認の依頼内容と、受け取った結果
5. `harness-selection.json` と修正箇所の完全パス

## 使用例とエッジケース

- 使用例: ユーザー「セットアップ結果をレビューして」→ 対象を state から取得し、機械検査と別エージェントの突合レビューを実行 → 両方 PASS なら `verify` と `done` を実行して完了報告を返す。
- 突合レビューだけ FAIL: findings の file:line を直し、手順 1 から再実行する（`fail_count` が進む）。
- `harness-selection.json` が無い: 検査せず中断し、Step 0 からの実施を報告する。
- スクリプトが無い・python が無い: 機械検査を PASS 扱いにしない。該当スクリプトの不在またはインストール不足を報告して中断し、`verify` は実行しない。

## 禁止事項

- 手順 1 と手順 2 のどちらかを省略して `verify` を PASS にすること。
- 自分でレビューして通過扱いにすること（手順 2 は必ず別エージェント）。
- 非選択の著者嗜好要素を「あった方がよい」と判断して対象に足すこと（選択記録に無い追加は Step 0 に戻してユーザーに聞く）。
- `harness-setup-state.sh done` を `phase=verified` 以外で実行すること（スクリプトが拒否する）。

## 強制の仕組み

移植元 clone の `.claude/settings.json` に登録された Stop hook（`hook-stop-setup-gate.sh`）が、state の `phase` が `selecting` / `generated` の間は Claude の終了を block し、本 skill の実行を促す。block は 1 turn あたり 3 回までで、上限に達すると終了を許し、検証未完了である旨を `systemMessage` でユーザーに表示する（カウンタは次の turn で 0 に戻るので、ゲートは再び働く）。python が見つからない環境ではゲートを評価できない旨を表示して終了を許す。SessionStart hook（`hook-session-start-setup.sh`）は進行中 setup のポインタを通知する。中断する場合は `harness-setup-state.sh clear` で state を消し、ユーザーに未検証である旨を報告する。
