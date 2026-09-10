#!/usr/bin/env bash
# harness_check.sh — ハーネスファイルの変更分を Anthropic 公式ベストプラクティスに照らして機械検査する。
# 使い方:
#   bash harness_check.sh                 # 未 commit 変更 + 直近 1 commit
#   bash harness_check.sh HEAD~3          # その ref 以降の変更
#   bash harness_check.sh path/a path/b   # 指定ファイルのみ
# 出力: CHECK <id> <PASS|WARN|FAIL> <file> <detail>  （1 行 1 検査）
# 終了コード: FAIL が 1 件以上なら 1、それ以外 0。
# check id と公式原則の対応は reference/checks.md。数値の閾値は公式 docs 由来のもののみ（skills 500 行・description 1536 文字・CLAUDE.md 200 行）。
set -u
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT" || exit 2
FAILS=0; WARNS=0
emit() { # id status file detail
  printf 'CHECK\t%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4"
  [ "$2" = FAIL ] && FAILS=$((FAILS+1)); [ "$2" = WARN ] && WARNS=$((WARNS+1)); return 0
}
is_harness() { case "$1" in CLAUDE.md|.claude/*) return 0;; *) return 1;; esac; }

# ---- 対象ファイルの決定 ----
FILES=()
if [ $# -eq 0 ]; then
  while IFS= read -r f; do [ -n "$f" ] && FILES+=("$f"); done < <( { git diff --name-only HEAD~1 2>/dev/null; git diff --name-only 2>/dev/null; git diff --name-only --cached 2>/dev/null; git ls-files --others --exclude-standard 2>/dev/null; } | sort -u )
elif [ $# -eq 1 ] && git rev-parse --verify "$1^{commit}" >/dev/null 2>&1; then
  while IFS= read -r f; do [ -n "$f" ] && FILES+=("$f"); done < <( { git diff --name-only "$1" 2>/dev/null; git ls-files --others --exclude-standard 2>/dev/null; } | sort -u )
else
  for a in "$@"; do FILES+=("${a#./}"); done
fi
TARGETS=()
for f in "${FILES[@]}"; do is_harness "$f" && [ -f "$f" ] && TARGETS+=("$f"); done
if [ ${#TARGETS[@]} -eq 0 ]; then echo "対象のハーネスファイル変更なし（CLAUDE.md / .claude/**）"; exit 0; fi

# ---- SoT（公式原則キャッシュ）の鮮度 ----
SOT=""
for c in .claude/skills/_shared/anthropic-best-practices.yaml .claude/skills/_shared/anthropic-best-practices.json; do [ -f "$c" ] && SOT="$c" && break; done
if [ -z "$SOT" ]; then
  emit BP01 FAIL "(repo)" "公式原則の構造化キャッシュ（.claude/skills/_shared/anthropic-best-practices.yaml|json）が無い"
else
  fetched=$(grep -oE '"?fetched"?:? *"?[0-9]{4}-[0-9]{2}-[0-9]{2}' "$SOT" | head -1 | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}')
  maxage=$(grep -oE '"?max_age_days"?:? *[0-9]+' "$SOT" | head -1 | grep -oE '[0-9]+$')
  if [ -n "$fetched" ] && [ -n "$maxage" ] && date -d "$fetched" +%s >/dev/null 2>&1; then
    age=$(( ( $(date +%s) - $(date -d "$fetched" +%s) ) / 86400 ))
    if [ "$age" -gt "$maxage" ]; then emit BP02 WARN "$SOT" "fetched=$fetched は max_age_days=$maxage を超過（${age} 日）。refetch_when 手順を先に実行"; else emit BP02 PASS "$SOT" "fetched=$fetched（${age} 日）"; fi
  else
    emit BP02 WARN "$SOT" "fetched / max_age_days を読めない（手動で鮮度を確認）"
  fi
fi

frontmatter() { awk 'NR==1{ if($0!="---") exit; next } /^---$/{ exit } { print }' "$1"; }
fm_get() { frontmatter "$1" | grep -E "^$2:" | head -1 | sed -E "s/^$2:[[:space:]]*//; s/^\"(.*)\"$/\\1/"; }
count_lines() { wc -l < "$1" | tr -d ' '; }
charlen() { printf '%s' "$1" | wc -m | tr -d ' '; }

for f in "${TARGETS[@]}"; do
  case "$f" in
    CLAUDE.md|*/CLAUDE.md)
      n=$(count_lines "$f")
      if [ "$n" -gt 200 ]; then emit C01 WARN "$f" "$n 行（公式目標 200 行未満）"; else emit C01 PASS "$f" "$n 行"; fi
      while IFS= read -r imp; do
        p="${imp#@}"; [ -f "$p" ] && emit C02 PASS "$f" "@import $p 実在" || emit C02 FAIL "$f" "@import 先 $p が無い"
      done < <(grep -oE '^@[^ ]+' "$f" | sort -u)
      em=$(grep -cE 'IMPORTANT|YOU MUST|MUST NOT' "$f")
      if [ "$em" -gt 3 ]; then emit C03 WARN "$f" "強調語 $em 箇所（多用すると何も目立たない）"; else emit C03 PASS "$f" "強調語 $em 箇所"; fi
      grep -qE '^# ' "$f" && emit C04 PASS "$f" "見出しあり" || emit C04 WARN "$f" "Markdown 見出しが無い（構造化推奨）"
      ;;
    .claude/rules/*.md)
      if [ "$(head -1 "$f")" = "---" ]; then
        d=$(fm_get "$f" description); [ -n "$d" ] && emit R01 PASS "$f" "description あり" || emit R01 WARN "$f" "frontmatter に description が無い"
        if frontmatter "$f" | grep -qE '^paths:'; then emit R02 PASS "$f" "paths あり（path-scope）"; else emit R02 PASS "$f" "paths なし（常時 load）"; fi
      else
        emit R01 PASS "$f" "frontmatter なし（常時 load・description 省略）"
      fi
      n=$(count_lines "$f"); [ "$n" -gt 200 ] && emit R03 WARN "$f" "$n 行（1 ファイル 1 トピックか確認）" || emit R03 PASS "$f" "$n 行"
      ;;
    .claude/skills/*/SKILL.md)
      dir=$(basename "$(dirname "$f")")
      if [ "$(head -1 "$f")" != "---" ]; then emit S01 FAIL "$f" "YAML frontmatter が無い"; continue; fi
      name=$(fm_get "$f" name)
      [ "$name" = "$dir" ] && emit S02 PASS "$f" "name=$name" || emit S02 FAIL "$f" "name '$name' がディレクトリ名 '$dir' と不一致"
      echo "$name" | grep -qE '^[a-z0-9]+(-[a-z0-9]+)*$' && emit S03 PASS "$f" "kebab-case" || emit S03 FAIL "$f" "name が kebab-case でない"
      echo "$name" | grep -qiE 'claude|anthropic' && emit S04 FAIL "$f" "name に claude/anthropic を含む（予約語）" || emit S04 PASS "$f" "予約語なし"
      d=$(fm_get "$f" description); w=$(frontmatter "$f" | awk '/^when_to_use:/{flag=1;next} flag&&/^[a-z_-]+:/{flag=0} flag{print}' | tr -d '\n')
      if [ -z "$d" ]; then emit S05 FAIL "$f" "description が無い"; else
        len=$(charlen "$d$w"); [ "$len" -le 1536 ] && emit S05 PASS "$f" "description+when_to_use ${len} 文字" || emit S05 FAIL "$f" "description+when_to_use ${len} 文字（上限 1536）"
        echo "$d" | grep -qiE 'use when|とき|時に|場合|依頼|when ' && emit S06 PASS "$f" "いつ使うかの記述あり" || emit S06 WARN "$f" "description に『いつ使うか』が読み取れない"
      fi
      n=$(count_lines "$f"); [ "$n" -lt 500 ] && emit S07 PASS "$f" "$n 行" || emit S07 FAIL "$f" "$n 行（500 行未満に分割）"
      body=$(awk 'NR==1&&$0=="---"{s=1;next} s==1&&/^---$/{s=2;next} s==2{print}' "$f")
      if echo "$body" | grep -qiE 'git (commit|push)|deploy|rm -rf|Remove-Item|\.mcp\.json を(編集|登録)|上書き保存'; then
        frontmatter "$f" | grep -qE '^disable-model-invocation: *true' && emit S08 PASS "$f" "副作用あり・disable-model-invocation: true" || emit S08 WARN "$f" "副作用（commit/push/deploy 等）を含むが disable-model-invocation が無い（意図的なら根拠を記す）"
      else emit S08 PASS "$f" "副作用語なし"; fi
      if echo "$body" | grep -qE '\$ARGUMENTS|\$[0-9]'; then
        frontmatter "$f" | grep -qE '^argument-hint:' && emit S09 PASS "$f" "引数あり・argument-hint あり" || emit S09 WARN "$f" "\$ARGUMENTS を使うが argument-hint が無い"
      else emit S09 PASS "$f" "引数なし"; fi
      frontmatter "$f" | grep -qE '<[^>]+>' && emit S10 WARN "$f" "frontmatter に山括弧プレースホルダ（XML 風タグを拒否する配布経路がある）" || emit S10 PASS "$f" "山括弧なし"
      for ref in $(echo "$body" | grep -oE '\]\((references?|scripts|assets)/[^)]+\)' | sed -E 's/^\]\(//; s/\)$//' | sort -u); do
        [ -e "$(dirname "$f")/$ref" ] && emit S11 PASS "$f" "$ref 実在" || emit S11 FAIL "$f" "リンク先 $ref が無い"
      done
      ;;
    .claude/commands/*.md)
      if [ "$(head -1 "$f")" = "---" ]; then
        d=$(fm_get "$f" description); [ -n "$d" ] && emit K01 PASS "$f" "description あり" || emit K01 WARN "$f" "description が無い"
        frontmatter "$f" | grep -qE '<[^>]+>' && emit K02 WARN "$f" "frontmatter に山括弧プレースホルダ" || emit K02 PASS "$f" "山括弧なし"
      else emit K01 WARN "$f" "frontmatter なし（description で発動条件を書くと自動発見される）"; fi
      ;;
    .claude/agents/*.md)
      [ "$(head -1 "$f")" = "---" ] || { emit A01 FAIL "$f" "frontmatter が無い"; continue; }
      [ -n "$(fm_get "$f" name)" ] && [ -n "$(fm_get "$f" description)" ] && emit A01 PASS "$f" "name/description あり" || emit A01 FAIL "$f" "name または description が無い"
      ;;
    .claude/settings.json|.claude/settings.local.json)
      if command -v python >/dev/null 2>&1; then python -c "import json,sys; json.load(open(sys.argv[1], encoding='utf-8'))" "$f" >/dev/null 2>&1 && emit H01 PASS "$f" "JSON として妥当" || emit H01 FAIL "$f" "JSON parse エラー"; else emit H01 WARN "$f" "python 不在で JSON 検証をスキップ"; fi
      while IFS= read -r cmd; do
        p=$(echo "$cmd" | grep -oE '(\$CLAUDE_PROJECT_DIR"?/|\./)?\.claude/[^" ]+' | head -1 | sed -E 's#^\$CLAUDE_PROJECT_DIR"?/##; s#^\./##')
        [ -z "$p" ] && continue
        [ -f "$p" ] && emit H02 PASS "$f" "hook script $p 実在" || emit H02 FAIL "$f" "hook script $p が無い"
      done < <(grep -oE '"command": *"[^"]+"' "$f")
      ;;
    *) emit X00 PASS "$f" "検査対象外の種別（エージェント判定のみ）";;
  esac
done
echo "SUMMARY FAIL=$FAILS WARN=$WARNS targets=${#TARGETS[@]}"
[ "$FAILS" -gt 0 ] && exit 1 || exit 0
