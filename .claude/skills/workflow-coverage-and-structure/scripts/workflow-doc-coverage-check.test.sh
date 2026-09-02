#!/usr/bin/env bash
# workflow-doc-coverage-check.test.sh — regression test（隔離 fixture repo 方式）
#
# カバー範囲:
#   T1 全ファイルが README に記載済み → PASS
#   T2 README 未記載の新規ファイル → FAIL exit 1
#   T3 README に追記すれば PASS に戻る
#   T4 examples/ 配下は個別ファイルへのリンク不要（ディレクトリ言及のみで可）
#   T5 --report は常に exit 0 で件数を表示する
#   T6 README.md 自体が存在しない category → FAIL
#   T7 category はあるが workflows/README.md の一覧表に未記載 → FAIL
# 実行: bash .claude/skills/workflow-coverage-and-structure/scripts/workflow-doc-coverage-check.test.sh

set -uo pipefail
CHECK="$(cd "$(dirname "$0")" && pwd)/workflow-doc-coverage-check.sh"
PASS=0; FAIL=0
t() { # $1=name $2=expect $3=actual
  if [[ "$2" == "$3" ]]; then PASS=$((PASS+1)); echo "ok - $1"
  else FAIL=$((FAIL+1)); echo "NOT OK - $1 (expect=$2 got=$3)"; fi
}

FIX=$(mktemp -d) || { echo "FATAL: mktemp failed"; exit 1; }
trap 'rm -rf "$FIX"' EXIT
cd "$FIX" || { echo "FATAL: cd fixture failed"; exit 1; }
git init -q .
git config user.email test@test && git config user.name test
mkdir -p workflows/demo-category
cat > workflows/README.md <<'EOF'
# workflows/

| ワークフロー | 目的 |
|---|---|
| [demo-category/](demo-category/README.md) | サンプルカテゴリ |
EOF
cat > workflows/demo-category/README.md <<'EOF'
# workflows/demo-category/

| プロンプト | レビュー | 用途 |
|---|---|---|
| [thing.md](thing.md) | [review-thing.md](review-thing.md) | サンプル |
EOF
echo 'thing prompt' > workflows/demo-category/thing.md
echo 'review prompt' > workflows/demo-category/review-thing.md
git add -A && git commit -qm init

# T1 全ファイルが記載済み → PASS
rc=0; bash "$CHECK" >/dev/null 2>&1 || rc=$?
t "T1 全ファイル記載済み PASS" 0 "$rc"

# T2 README 未記載の新規ファイル → FAIL
echo 'undocumented' > workflows/demo-category/new-thing.md
rc=0; out=$(bash "$CHECK" 2>&1) || rc=$?
t "T2 未記載ファイル FAIL exit" 1 "$rc"
echo "$out" | grep -q "new-thing.md"; t "T2 未記載ファイル表示" 0 "$?"

# T3 README に追記すれば PASS に戻る
cat >> workflows/demo-category/README.md <<'EOF'
| [new-thing.md](new-thing.md) | - | 追加分 |
EOF
rc=0; bash "$CHECK" >/dev/null 2>&1 || rc=$?
t "T3 README 追記後 PASS" 0 "$rc"
rm -f workflows/demo-category/new-thing.md

# T4 examples/ 配下は個別ファイルリンク不要
mkdir -p workflows/demo-category/examples
echo 'worked example' > workflows/demo-category/examples/case1.md
rc=0; bash "$CHECK" >/dev/null 2>&1 || rc=$?
t "T4 examples/ 配下は個別リンク不要 PASS" 0 "$rc"

# T5 --report は exit 0
rc=0; out=$(bash "$CHECK" --report 2>&1) || rc=$?
t "T5 --report exit 0" 0 "$rc"
echo "$out" | grep -q "workflow prompt files"; t "T5 --report 件数表示" 0 "$?"

# T6 README.md 自体が存在しない category → FAIL
mkdir -p workflows/no-readme-category
echo 'orphan' > workflows/no-readme-category/orphan.md
rc=0; out=$(bash "$CHECK" 2>&1) || rc=$?
t "T6 README 不在 category FAIL exit" 1 "$rc"
echo "$out" | grep -q "README.md 自体が存在しない"; t "T6 README 不在表示" 0 "$?"
rm -rf workflows/no-readme-category

# T7 category 自体に README はあるが workflows/README.md の一覧表に未記載 → FAIL
mkdir -p workflows/unlisted-category
cat > workflows/unlisted-category/README.md <<'EOF'
# workflows/unlisted-category/
| プロンプト | レビュー | 用途 |
|---|---|---|
EOF
rc=0; out=$(bash "$CHECK" 2>&1) || rc=$?
t "T7 workflows/README.md 未記載 category FAIL exit" 1 "$rc"
echo "$out" | grep -q "workflows/README.md に未記載の category: unlisted-category"; t "T7 未記載 category 表示" 0 "$?"
rm -rf workflows/unlisted-category

# T8 category ディレクトリ名にスペースを含んでいても正しく処理される
# (regression 防壁 — unquoted `for cat in $CATEGORIES` の word-splitting バグの再発防止・2026-09-02 修正)
mkdir -p "workflows/cat with space"
cat > "workflows/cat with space/README.md" <<'EOF'
# workflows/cat with space/
| プロンプト | レビュー | 用途 |
|---|---|---|
| [thing2.md](thing2.md) | - | サンプル |
EOF
echo 'thing2 prompt' > "workflows/cat with space/thing2.md"
cat >> workflows/README.md <<'EOF'
| [cat with space/](cat with space/README.md) | スペースを含む category 名のテスト |
EOF
rc=0; out=$(bash "$CHECK" 2>&1) || rc=$?
t "T8 スペースを含む category 名でも正しく PASS" 0 "$rc"
rm -rf "workflows/cat with space"

echo ""
echo "=== $PASS passed, $FAIL failed ==="
[[ $FAIL -eq 0 ]] && exit 0 || exit 1
