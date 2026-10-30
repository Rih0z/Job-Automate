# 公式準拠の核: 取得対象と構造化データ

SKILL.md「公式準拠の核」から分離した取得対象表。生成・レビュー開始時に参照する。

## 目次

- 取得対象と確認項目（URL 表）
- 構造化データ（参照の SoT）

---

### 取得対象と確認項目（名称のみ列挙・本文/テーブル/数値は取得して読む）

| URL | 取得時に現行版を確認する項目 |
|---|---|
| `https://code.claude.com/docs/en/best-practices`（"Write an effective CLAUDE.md" / "Configure permissions" / "Avoid common failure patterns" / "Add an adversarial review step"） | 行の要否判定基準の文言（**固定の名称ではなく都度の言い回しを確認する**。2026-09-02 確認時点では「削除したら Claude がミスするか」という問い掛け形式）/ Include・Exclude テーブルの現行内容 / emphasis ガイダンス / hooks（advisory との対比）/ permissions の事前承認と sandbox / 検証ゲートの強さ（prompt → `/goal` → Stop hook）/ Writer-Reviewer・adversarial review の注意（reviewer は gap を過剰報告しがち → correctness と明示要件に関わる gap のみ採用） |
| `https://code.claude.com/docs/en/memory` | CLAUDE.md のサイズ目標（"Size" の記述）/ 配置場所と上位ディレクトリの連結読み込み・`claudeMdExcludes` / `@path` import の解決規則 / `.claude/rules/` の frontmatter（読まれるのは `paths` のみ）と load タイミング / AGENTS.md の扱い（`@AGENTS.md`）/ `CLAUDE.local.md` / compaction 後に再注入されるもの / `/context` と `InstructionsLoaded` による読み込み確認 |
| `https://code.claude.com/docs/en/skills` | SKILL.md 必須・frontmatter（`name` 任意 / `description` 推奨 / `description`+`when_to_use` の文字数上限）/ 本文の recurring token cost と簡潔性 / progressive disclosure（supporting files で参照分離）/ SKILL.md 行数の目安 / commands と skills の統合 / `disable-model-invocation` 等 |
| `https://code.claude.com/docs/en/hooks`・`https://code.claude.com/docs/en/hooks-guide` | hook イベント別の出力契約（どの stdout が context 注入されるか / `exit 2` の意味 / `additionalContext` / `systemMessage` / exit 0 の stderr の行き先 / Stop の連続 block 上限など、hook 生成直前に現行仕様を確認）/ exec form と shell form / `timeout` 既定値 / Security best practices と workspace trust |
| `https://code.claude.com/docs/en/sub-agents` | `.claude/agents/*.md` の frontmatter（`tools` / `disallowedTools` / `model` 等・name の制約）/ ツール制限による制約の強制 |
| `https://code.claude.com/docs/en/permissions`・`https://code.claude.com/docs/en/settings` | ルール評価順（deny → ask → allow）/ 機密ファイルの `Read` deny / `$schema` / `settings.local.json` の gitignore |

取得後、冒頭に「取得日時 + 確認した現行原則の要点」を出力してから生成・レビューに進む。

**構造化データ（参照の SoT）**: 公式原則の要約は `.claude/skills/_shared/anthropic-best-practices.json` に 1 つの構造化データとして保持する（各原則に `id` / `source`（`sources` の URL を指す）/ `statement` / `quote` / `check` / `used_by`、ファイル全体に取得日 `fetched` と再取得条件 `refetch_when`）。本スキル・`harness-setup-review`・`skills-audit`・`harness-compliance-audit`・`skill-authoring-guide`・`review-skill` はこのファイルを判定基準として参照する。生成・レビュー開始時は `fetched` を確認し、`refetch_when` に該当すれば上記 URL を WebFetch して現行版と突合し、差分があれば同ファイルを更新して `fetched` を進める。WebFetch に失敗した場合、`fetched` が `max_age_days` 以内なら構造化データで判定を続け、報告に「公式現行版との突合未実施」と明記する。超過していれば取得できるまで中断する（日付と再取得条件を持たない転記だけが焼き込み禁止の対象）。
