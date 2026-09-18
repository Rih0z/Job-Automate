# セットアップガイド: 別プロジェクトへ移植する

[← README.md](../README.md)

このリポジトリの `CLAUDE.md`・`.claude/skills/` の仕組み（レビュー基準・エージェント分離・harness設計）を、別のプロジェクトにも使いたい場合の手順。**Anthropic 公式由来の要素はデフォルトで入り、著者の運用嗜好（issue フォルダ管理・handoff 規約・並走 recheck 等）はあなたが選んだものだけ入る**。

## 品質の保証範囲

公式ベストプラクティスは取得日・再取得条件付きの構造化データ [anthropic-best-practices.json](../.claude/skills/_shared/anthropic-best-practices.json)（34原則）として保持されており、これが検証の一次ソースである。WebFetch は「毎回」ではなく、このデータが古くなった時・食い違いの疑いが出た時・公式更新を確認した時・新しい対象プロジェクトへ初めて適用する時にだけ、公式ドキュメントの現行版で裏取りして更新する（条件は同ファイルの `refetch_when` に定義）。

| 揃うもの | 仕組み |
|---|---|
| 公式基準への準拠 | 構造化データを判定基準に、別エージェントが `rubric.md` の36項目ルーブリックを全 Y になるまで判定する（`agent-harness-bootstrap` Step 7） |
| 構成（何が入り、何が入らないか） | 台帳の各要素が持つ契約（選択時に必ず現れる語句・ファイル・`@import`・`paths:` / 非選択時に現れてはならないもの）を `provenance-check.sh --target` が**決定的に**検査し、別エージェントの突合レビューで「選択済みの抜けゼロ・非選択の混入ゼロ」を must_pass 判定する。両方 PASS するまで `harness-setup-review` が完了を認めず、Stop hook が終了を block する |
| 既存 skills の公式準拠 | setup 前から対象にある skills を `skills-audit` が構造化データ基準で監査し tier を報告する |
| 台帳と実体の整合 | `provenance-check.sh` の 11 検査 + regression test |

保証しないもの: 構造・語句の契約は決定的だが、条文の中身の良し悪し（ルーブリックの Y/N）は LLM レビュアの判定で、完全な決定性はない。生成後のドリフトは、governance.md や hooks を選んだ場合と再同期時にしか検出されない。プロジェクトごとに選ぶ著者嗜好の集合は異なるので、揃うのは「公式準拠の土台 + 記録された差分」であり、全プロジェクトが同一の CLAUDE.md になるわけではない。

## 配置と gitignore（先に決める）

移植元（このリポジトリ）の clone は、対象プロジェクト直下の **`.setup-automate/`** に置き、**gitignore する**。生成物と選択記録は対象側にコミットする:

```
<対象プロジェクト>/
├── .setup-automate/                 # このリポジトリの clone。gitignore する。再同期は中で git pull
├── .claude/
│   ├── harness-selection.json       # コミットする（何を取り込み何を外したかの記録 = 移植チェックリスト）
│   ├── rules/  skills/              # 選択した要素だけが入る
│   └── settings.json                # hooks を選んだ時のみ
├── CLAUDE.md                        # 生成物（コミットする）
├── .tmp/                            # handoff 規約を選んだ時のみ生成。gitignore する
└── workflows/software-development/  # review コマンドを選んだ時のみ（評価基準ファイル。台帳 files[] 由来・コミットする）
```

```bash
cd <対象プロジェクト>
git clone <このリポジトリの URL> .setup-automate && printf '.setup-automate/\n' >> .gitignore
cd .setup-automate   # ← ここで Claude Code を起動する
```

この clone の `.claude/settings.json` には SessionStart / Stop の hook が登録されている。setup の進行中（選択 → 生成 → 検証）だけ動き、検証（`harness-setup-review`）を PASS する前に Claude が終了しようとすると block する。setup をしていない時は何もしない。

## 手順

1. 上記のとおり `.setup-automate/` に clone し、**その中で** Claude Code を起動する（対象ルートで起動するとこのリポジトリの CLAUDE.md が読み込まれず、下記の指示が効かない）。clone するだけでは何も自動実行されない（Claude Code は明示的な指示なしにファイルを実行しない設計のため、次の一言だけは必要）。
2. 「親ディレクトリ（`..`）をセットアップして」と伝える（表現は厳密でなくてよい。「ここの仕組みを `..` にも入れて」「`<対象の絶対パス>` をセットアップして」等でも同じ手順が走る — 詳細な発火条件は [CLAUDE.md](../CLAUDE.md)「他プロジェクトのセットアップ依頼への対応」参照）。
3. 以降は Claude Code が `CLAUDE.md` の**完全列挙 + 由来別選択ルール**を実行する: 全要素を載せた選択記録（= 移植チェックリスト）の作成 → **由来別（Anthropic 公式由来 / 公式原則の具体化 / 著者の運用嗜好 / 第三者 / 業務プロンプト）に提示し、何を取り込むかをあなたが選ぶ**（著者嗜好はデフォルト非採用） → 選択を対象の `.claude/harness-selection.json` に記録 → `.claude/skills/agent-harness-bootstrap` で対象 CLAUDE.md を生成 → 選択した skills をコピー → `harness-setup-review` で「選択済みの抜けゼロ・非選択の混入ゼロ」を機械検査 + 別エージェント突合レビュー（両方 PASS するまで Stop hook が終了を block）→ 既存 skills があれば `skills-audit` で公式準拠を監査。由来の台帳は [provenance.json](../.claude/skills/agent-harness-bootstrap/provenance.json)、選択手順は [selection-flow.md](../.claude/skills/agent-harness-bootstrap/selection-flow.md)。
4. 完了後、対象側で `CLAUDE.md`・`.claude/`・（採用時）`workflows/software-development/` をコミットする。`.setup-automate/` と `.tmp/` はコミットしない。

## 検証と再同期

選択記録は対象ルートから機械検証できる（cwd はどこでもよい）:

```bash
bash .setup-automate/.claude/skills/agent-harness-bootstrap/scripts/provenance-check.sh \
  --selection "$PWD/.claude/harness-selection.json"
```

このリポジトリが更新されたら `.setup-automate/` 内で `git pull` し、同じ指示をもう一度伝える。前回 `selected: false` にした要素は再提案されず、台帳に増えた新要素だけが提示される。`.setup-automate/` は gitignore されているので、他のメンバーが再同期する時は同じ場所に再 clone する（`.claude/harness-selection.json` がコミットされていれば選択は引き継がれる）。

このリポジトリ自身をセットアップする場合（対象＝このリポジトリの中で作業したいだけの場合）は、上記は不要。clone して Claude Code で開けば `.claude/skills/` は自動検出される（[docs/skills-index.md](skills-index.md) 参照）。
