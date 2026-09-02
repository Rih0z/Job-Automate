#!/usr/bin/env bash
# workflow-doc-coverage-check.sh — workflows/ 配下ファイルのドキュメント網羅性検査
#
# 目的: このリポジトリはプロンプトの種類ではなく業務ワークフロー単位で構成され、各
#   workflows/<category>/README.md が「プロンプト | レビュー | 用途」形式の表で
#   作成プロンプトとレビュープロンプトの対応関係を人手で curate している（1:1 の
#   命名規則ではなく、1つの review-*.md が複数の作成プロンプトをまとめて担当する
#   ケースがあるため、ファイル名の類推では正確な対応関係を機械判定できない）。
#
#   このため本 check は「対応する review が存在するか」ではなく、より単純で
#   誤検知の少ない指標を使う: 「各 workflows/<category>/ 配下の .md ファイルが、
#   その category の README.md 内にリンクとして記載されているか」。
#   これは「新規ファイルを追加したが README への追記を忘れた」というドキュメント
#   drift を検出する（README 自体が create/review 対応関係の一次ソースであるため、
#   ここが正確であれば人間が対応関係を確認できる）。
#
# 除外: examples/ 配下（README ではディレクトリ単位でリンクされる worked-example 集・
#   個別ファイルへのリンクは要求しない設計）。
#
# usage:
#   bash .claude/skills/workflow-coverage-and-structure/scripts/workflow-doc-coverage-check.sh            # check
#   bash .claude/skills/workflow-coverage-and-structure/scripts/workflow-doc-coverage-check.sh --report    # 件数サマリーのみ (exit 0)

set -uo pipefail
cd "$(git rev-parse --show-toplevel)" || { echo "FAIL: not in a git repo" >&2; exit 1; }

undocumented_in_category() { # $1 = category dir (e.g. workflows/business-planning)
  local cat="$1" readme="$1/README.md"
  if [[ ! -f "$readme" ]]; then
    echo "$cat: README.md 自体が存在しない"
    return
  fi
  find "$cat" -name "*.md" ! -name "README.md" | grep -v "/examples/" | while IFS= read -r f; do
    rel="${f#"$cat"/}"
    grep -qF "($rel)" "$readme" || echo "$f"
  done
}

ALL_GAPS=""
# category 名にスペースを含む可能性を考慮し、word-splitting を避けるため IFS=$'\n' + read で反復する
# （unquoted `for cat in $CATEGORIES` は空白を含むディレクトリ名で誤分割するバグがあった・2026-09-02 修正）
while IFS= read -r cat; do
  [[ -z "$cat" ]] && continue
  gaps=$(undocumented_in_category "$cat")
  [[ -n "$gaps" ]] && ALL_GAPS="${ALL_GAPS}${gaps}"$'\n'
done < <(find workflows -mindepth 1 -maxdepth 1 -type d | sort)

# category（トップレベル workflows/<name>/ ディレクトリ）が workflows/README.md の一覧表に
# リンクされているかを確認（新規 category 追加時のドキュメント drift 検出）。
CATEGORY_GAPS=""
while IFS= read -r cat; do
  [[ -z "$cat" ]] && continue
  base=$(basename "$cat")
  grep -qF "($base/README.md)" workflows/README.md || CATEGORY_GAPS="${CATEGORY_GAPS}workflows/README.md に未記載の category: $base"$'\n'
done < <(find workflows -mindepth 1 -maxdepth 1 -type d | sort)
[[ -n "$CATEGORY_GAPS" ]] && ALL_GAPS="${ALL_GAPS}${CATEGORY_GAPS}"

if [[ "${1:-}" == "--report" ]]; then
  total_files=$(find workflows -name "*.md" ! -name "README.md" | grep -v "/examples/" | wc -l | tr -d ' ')
  total_review=$(find workflows -name "review-*.md" | wc -l | tr -d ' ')
  total_skills=$(find .claude/skills -mindepth 1 -maxdepth 1 -type d ! -name "_shared" | wc -l | tr -d ' ')
  gap_count=$(printf '%s' "$ALL_GAPS" | grep -c . || true)
  echo "workflow-doc-coverage-check --report"
  echo "  workflow prompt files (excl. README/examples): $total_files"
  echo "  review-*.md files:                             $total_review"
  echo "  .claude/skills/ 個別 skill 数:                   $total_skills"
  echo "  category README 未記載ファイル数:                $gap_count"
  exit 0
fi

if [[ -z "$ALL_GAPS" ]]; then
  echo "workflow-doc-coverage-check: PASS (全 workflow ファイルが category README に記載済み)"
  exit 0
fi

echo "workflow-doc-coverage-check: FAIL — category README に未記載のファイル:"
printf '%s' "$ALL_GAPS" | grep -v '^$' | sed 's/^/  /'
echo "対応: 該当 workflows/<category>/README.md の表に追記（プロンプト・対応レビュー・用途）"
exit 1
