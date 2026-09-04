---
name: harness-setup-review
description: "別プロジェクトへの harness セットアップ（agent-harness-bootstrap Step 0〜8）の完了後に、ユーザーが選択した全観点が対象の CLAUDE.md / rules / skills に反映されているか（抜けゼロ）と、非選択の著者嗜好が混入していないか（混入ゼロ）を検査する。機械検査（provenance-check.sh --target）と別エージェントの突合レビュー（criteria/porting-reconciliation.json）の両方が PASS するまで setup を完了扱いにしない（Stop hook が検証前の終了を block する）。対象に既存の skills があれば skills-audit で Anthropic 公式ベストプラクティス準拠も監査する。Use when the user asks to 'セットアップ結果をレビューして', 'harness-setup-review', '移植の抜けと混入を確認して', or immediately after agent-harness-bootstrap finishes generating for a target other than this repository."
allowed-tools: Read Bash Agent Glob Grep
argument-hint: "<対象プロジェクトの絶対パス>（省略時は進行中 setup の state から取得）"
metadata:
  provenance: official-derived
---

# harness-setup-review — setup 後の抜け・混入レビュー

移植元（このリポジトリの clone）で実行する。対象プロジェクトへはコピーしない。公式ベストプラクティスの参照は `.claude/skills/_shared/anthropic-best-practices.json`（日付付きの構造化データ）を使い、判定前に `refetch_when` に該当していれば各 `source_url` の現行版で裏取りする。

## 入力

- 対象ルート `$ARGUMENTS`。省略時は `bash .claude/skills/agent-harness-bootstrap/scripts/harness-setup-state.sh show` の `target`。
- 対象の `.claude/harness-selection.json`（Step 0 の選択記録）。無ければ検査できないので中断し、Step 0 から実施するよう報告する。

## 手順（順序固定・省略不可）

1. **機械検査（決定的）**: 対象ルートで次を実行し、出力をそのまま記録する。

   ```bash
   bash <本 clone>/.claude/skills/agent-harness-bootstrap/scripts/provenance-check.sh --target <対象の絶対パス>
   ```

   C11（選択記録: 全要素網羅・official は必ず selected・依存充足・skill-group の skills[]）と C12（生成物: 選択要素の契約語句・ファイル・`@import`・`paths:` の存在、非選択要素の語句・ファイル・ディレクトリ・skill の不在、`<!-- id: -->` マーカー残存禁止、`.setup-automate/` の gitignore）を評価する。FAIL 行があればそれが修正対象。
2. **突合レビュー（別エージェント）**: `Agent`（`general-purpose`）を起動し、次の 4 点の完全パス**のみ**を渡す（会話履歴・実装意図・本 skill の本文は渡さない）:
   - 移植元 `.claude/skills/agent-harness-bootstrap/provenance.json`
   - 対象 `.claude/harness-selection.json`
   - 対象ルート
   - 観点定義 `.claude/skills/agent-harness-bootstrap/criteria/porting-reconciliation.json`

   レビュアには `review-gate` と同じ形式で「観点定義に従い対象を批判的にレビューし、JSON（score / verdict / must_pass_failures / findings / missing_perspectives）のみ返す」よう指示する。手順 1 の結果は渡さない（独立判断を保つ）。
3. **既存 skills の監査（対象に `.claude/skills/` が setup 前から存在した場合のみ）**: `skills-audit` を対象の skills に対して実行し、GOOD / MIGRATE / IMPROVE / SPLIT の tier を記録する。setup でコピーした skill は監査対象から外す（選択記録の `skills[]` と台帳の `skills[]` で判別）。監査結果は setup の合否には含めず、最終報告に「既存 skills の公式準拠状況」として添える。
4. **判定と state 更新**:

   ```bash
   bash <本 clone>/.claude/skills/agent-harness-bootstrap/scripts/harness-setup-state.sh verify --machine <PASS|FAIL> --review <PASS|FAIL>
   ```

   - 両方 PASS → `phase=verified`。続けて `harness-setup-state.sh done` を実行し、完了報告へ進む。
   - いずれか FAIL → findings（file:line）を修正し、手順 1 から再実行する。`verify` は FAIL のたびに `fail_count` を進め、**3 回 FAIL で中断してユーザーに報告する**（対象で `issue-lifecycle` が選択済みなら `issues/open/` に起票、非選択なら報告のみ）。
5. **完了報告**: 機械検査の出力（PASS 行または FAIL 行）、突合レビューの score / verdict / findings、手順 3 の tier 一覧、`harness-selection.json` の完全パス、修正した箇所の完全パスを含める。

## 禁止事項

- 手順 1 と手順 2 のどちらかを省略して `verify` を PASS にすること。
- 自分でレビューして通過扱いにすること（手順 2 は必ず別エージェント）。
- 非選択の著者嗜好要素を「あった方がよい」と判断して対象に足すこと（選択記録に無い追加は Step 0 に戻してユーザーに聞く）。
- `harness-setup-state.sh done` を `phase=verified` 以外で実行すること（スクリプトが拒否する）。

## 強制の仕組み

移植元 clone の `.claude/settings.json` に登録された Stop hook（`hook-stop-setup-gate.sh`）が、state の `phase` が `selecting` / `generated` の間は Claude の終了を block し、本 skill の実行を促す。SessionStart hook（`hook-session-start-setup.sh`）は進行中 setup のポインタを通知する。中断する場合は `harness-setup-state.sh clear` で state を消し、ユーザーに未検証である旨を報告する。
