#!/usr/bin/env bash
# provenance-check.sh — provenance.json（由来台帳）の整合性検査
#
# 目的: .claude/skills/agent-harness-bootstrap/provenance.json は「公式由来 / 著者嗜好」の
#   分離台帳で、別プロジェクトへのセットアップ時にユーザーへ提示する選択肢の SoT である。
#   台帳が実体（skills ディレクトリ・rubric 項目・各 SKILL.md の metadata.provenance）と
#   食い違うと、存在しない要素を提示したり、由来ラベルの二重管理が stale 化したりする。
#   本 check はその drift を検出する。
#
# 検査項目:
#   C1 provenance.json が妥当な JSON で、schema が harness-provenance/v1
#   C2 各 element の provenance が provenance_levels に定義された level
#   C3 各 element の skills[] / commands[] / files[] が実在する（.claude/skills/<name>/SKILL.md / .claude/commands/<name>.md / 相対パス）
#   C4 depends_on / soft_depends_on の参照先 id が台帳内に存在する（自己参照なし）
#   C5 rubric_items が rubric.md の実在項目番号を指す
#   C6 .claude/skills/*/SKILL.md の frontmatter metadata.provenance が台帳の provenance と一致する
#      （台帳に載っていない skill に metadata.provenance が付いている場合も報告）
#   C7 台帳の id に重複がない
#   C8 同じ skill / command が複数 element に所有されていない（provenance が同じでも違反。参照は related_skills を使う）
#   C9 rubric.md の「要素 id」列（逆方向）: 各 id が台帳に存在し、その element の rubric_items に当該行番号が含まれる
#   C10 operational-knowhow.md / hooks-reference.md の "> provenance: <level> · id: <ids>" 行: level が定義済みで、各 id が台帳に存在し provenance が一致する
#       （対象ファイルは PROVENANCE_KNOWHOW にコロン区切りで指定可）
#   C11 --selection <path> 指定時: 対象の harness-selection.json が schema harness-selection/v1・全要素を網羅・selected が boolean・
#       decided_by が user/default/excluded/scale・selected:true の depends_on が全て selected:true・repo-specific / portable:false が非選択
#       skill-group は selected:true なら skills[] が空でなく要素の skills の部分集合・repo-specific / portable:false ⇔ decided_by:excluded
#       （soft_depends_on の欠落は WARN 表示のみ・違反に数えない）
#       official の要素は selected:true が必須（公式由来は外せない）
#   C12 --target <対象ルート> 指定時: 対象の生成物を台帳の target_contract と突合する（--selection 省略時は
#       <対象>/.claude/harness-selection.json）。選択要素の when_selected / 非選択要素の when_unselected を全て評価し、
#       skills[] / commands[] / files[] の存在・不在も自動で検査する。共通: <!-- id: --> マーカーの残存禁止、
#       対象に .setup-automate/ があれば .gitignore に登録されていること
#   実行場所: cwd に依存しない（既定パスは本スクリプトの位置から解決。環境変数・--selection・--target の相対パスは呼び出し時の cwd 基準）
#
# usage:
#   bash .claude/skills/agent-harness-bootstrap/scripts/provenance-check.sh            # check（違反あれば exit 1）
#   bash .claude/skills/agent-harness-bootstrap/scripts/provenance-check.sh --report   # 件数サマリーのみ（exit 0）
#   bash .claude/skills/agent-harness-bootstrap/scripts/provenance-check.sh --selection <対象>/.claude/harness-selection.json  # C11 も検査
#   bash .claude/skills/agent-harness-bootstrap/scripts/provenance-check.sh --target <対象ルート>   # C11 + C12（生成物の契約検査）

set -uo pipefail
# 既定パスは本スクリプトの位置（移植元リポジトリの skill ディレクトリ）から解決し、cwd に依存しない。
# 環境変数で上書きする相対パスは「呼び出し時の cwd」基準で絶対化してから使う（--selection も同様）。
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="${PROVENANCE_ROOT:-$(cd "$SKILL_DIR/../../.." && pwd)}"
abs() { case "$1" in /*) printf '%s' "$1" ;; *) printf '%s/%s' "$PWD" "$1" ;; esac; }
abs_list() { local out="" item; IFS=: read -ra items <<<"$1"; for item in "${items[@]}"; do [[ -z "$item" ]] && continue; out="${out:+$out:}$(abs "$item")"; done; printf '%s' "$out"; }

MANIFEST="$(abs "${PROVENANCE_MANIFEST:-$SKILL_DIR/provenance.json}")"
RUBRIC="$(abs "${PROVENANCE_RUBRIC:-$SKILL_DIR/rubric.md}")"
KNOWHOW="$(abs_list "${PROVENANCE_KNOWHOW:-$SKILL_DIR/operational-knowhow.md:$SKILL_DIR/hooks-reference.md}")"
SKILLS_DIR="$(abs "${PROVENANCE_SKILLS_DIR:-$ROOT/.claude/skills}")"
COMMANDS_DIR="$(abs "${PROVENANCE_COMMANDS_DIR:-$ROOT/.claude/commands}")"

MODE="check"; SELECTION=""; TARGET=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --report) MODE="report"; shift ;;
    --selection) SELECTION="${2:-}"; [[ -n "$SELECTION" ]] || { echo "FAIL: --selection にはパスが必要" >&2; exit 1; }; SELECTION="$(abs "$SELECTION")"; shift 2 ;;
    --target) TARGET="${2:-}"; [[ -n "$TARGET" ]] || { echo "FAIL: --target にはパスが必要" >&2; exit 1; }; TARGET="$(abs "$TARGET")"; shift 2 ;;
    *) echo "FAIL: 不明な引数 $1" >&2; exit 1 ;;
  esac
done
if [[ -n "$TARGET" ]]; then
  [[ -d "$TARGET" ]] || { echo "FAIL: --target $TARGET がディレクトリでない" >&2; exit 1; }
  [[ -n "$SELECTION" ]] || SELECTION="$TARGET/.claude/harness-selection.json"
  [[ -f "$SELECTION" ]] || { echo "FAIL: 選択記録 $SELECTION が無い（Step 0 を経ていない生成物は検査できない）" >&2; exit 1; }
fi
[[ -z "$SELECTION" || -f "$SELECTION" ]] || { echo "FAIL: $SELECTION が存在しない" >&2; exit 1; }

# python3 という名前の実行ファイルが PATH にあっても動作するとは限らない（Windows の
# Microsoft Store stub 等、`command -v` は成功するが実行すると何もしない/エラーになるケースがある）。
# 実際に `-c "print(1)"` を実行させて動く候補を選ぶ。
resolve_python() {
  local cand
  for cand in python3 python py; do
    if command -v "$cand" >/dev/null 2>&1 && "$cand" -c "print(1)" >/dev/null 2>&1; then
      printf '%s' "$cand"; return 0
    fi
  done
  return 1
}
PYTHON="$(resolve_python)" || { echo "FAIL: 動作する python (python3 / python / py) が見つからない" >&2; exit 1; }
# Windows のコンソールコードページ (cp1252 等) だと日本語 print() で UnicodeEncodeError になるため強制 UTF-8
export PYTHONUTF8=1
[[ -f "$MANIFEST" ]] || { echo "FAIL: $MANIFEST が存在しない" >&2; exit 1; }
# files[] の相対パスは移植元リポジトリのルート基準で解決する
cd "$ROOT" || { echo "FAIL: ROOT $ROOT に cd できない" >&2; exit 1; }

# Python 側で C1〜C11 をまとめて判定し、違反行を stdout に出す（1 行 1 違反。WARN 行は違反に数えない）。
# 末尾に "SUMMARY elements=<n> skills=<n> violations=<n>" を出す。
OUT=$("$PYTHON" - "$MANIFEST" "$RUBRIC" "$SKILLS_DIR" "$COMMANDS_DIR" "$KNOWHOW" "$SELECTION" "$TARGET" <<'PY'
import json, os, re, sys
manifest, rubric, skills_dir, commands_dir, knowhow, selection, target = sys.argv[1:8]
v = []
warns = []
try:
    d = json.load(open(manifest, encoding="utf-8"))
except Exception as e:
    print(f"C1 JSON parse error: {e}")
    print("SUMMARY elements=0 skills=0 violations=1")
    sys.exit(0)
if d.get("schema") != "harness-provenance/v1":
    v.append(f"C1 schema が harness-provenance/v1 ではない: {d.get('schema')}")
levels = set(d.get("provenance_levels", {}).keys())
elements = d.get("elements", [])
ids = [e.get("id") for e in elements]
for i in ids:
    if ids.count(i) > 1:
        v.append(f"C7 id 重複: {i}")
idset = set(ids)

# rubric 項目番号と「要素 id」列の抽出（| 1 | 項目 | id / id | Y/N | 形式。28b のような枝番も許容）
rubric_ids = set()
rubric_row_ids = {}  # row number -> [element ids]（id 列が無い行は登録しない）
if os.path.isfile(rubric):
    for line in open(rubric, encoding="utf-8"):
        m = re.match(r"^\|\s*(\d+[a-z]?)\s*\|", line)
        if not m:
            continue
        rubric_ids.add(m.group(1))
        # コードスパン内のエスケープ済み \| はセル区切りではないので先に退避する
        cells = [c.strip() for c in line.replace("\\|", "\x00").strip().strip("|").split("|")]
        if len(cells) >= 4:
            rubric_row_ids[m.group(1)] = [i.strip() for i in cells[2].split("/") if i.strip()]
else:
    v.append(f"C5 rubric が存在しない: {rubric}")

prov_by_skill = {}  # skill name -> 台帳側 provenance（最初に登録した element のもの）
owner_by_skill = {}  # skill name -> element id
owner_by_command = {}  # command name -> element id
for e in elements:
    eid = e.get("id", "?")
    if e.get("provenance") not in levels:
        v.append(f"C2 {eid}: provenance '{e.get('provenance')}' は provenance_levels に未定義")
    for s in e.get("skills", []):
        if not os.path.isfile(os.path.join(skills_dir, s, "SKILL.md")):
            v.append(f"C3 {eid}: skill '{s}' が {skills_dir}/{s}/SKILL.md に存在しない")
        if s in owner_by_skill:
            v.append(f"C8 {eid}: skill '{s}' は {owner_by_skill[s]} が既に所有（所有は 1 element に絞り、参照は related_skills を使う）")
        prov_by_skill.setdefault(s, e.get("provenance"))
        owner_by_skill.setdefault(s, eid)
    for c in e.get("commands", []):
        if not os.path.isfile(os.path.join(commands_dir, c + ".md")):
            v.append(f"C3 {eid}: command '{c}' が {commands_dir}/{c}.md に存在しない")
        if c in owner_by_command:
            v.append(f"C8 {eid}: command '{c}' は {owner_by_command[c]} が既に所有")
        owner_by_command.setdefault(c, eid)
    for f in e.get("files", []):
        if not os.path.exists(f):
            v.append(f"C3 {eid}: file '{f}' が存在しない")
    for key in ("depends_on", "soft_depends_on"):
        for dep in e.get(key, []):
            if dep == eid:
                v.append(f"C4 {eid}: {key} が自己参照")
            elif dep not in idset:
                v.append(f"C4 {eid}: {key} の参照先 '{dep}' が台帳に存在しない")
    for r in e.get("rubric_items", []):
        if str(r) not in rubric_ids:
            v.append(f"C5 {eid}: rubric_items '{r}' が {rubric} に存在しない")

# C9: rubric の id 列 → 台帳（逆方向）。id が実在し、その element の rubric_items に行番号が載っていること
rubric_items_by_id = {e.get("id"): {str(r) for r in e.get("rubric_items", [])} for e in elements}
for row, row_ids in rubric_row_ids.items():
    for rid in row_ids:
        if rid not in idset:
            v.append(f"C9 rubric 行 {row}: 要素 id '{rid}' が台帳に存在しない")
        elif row not in rubric_items_by_id.get(rid, set()):
            v.append(f"C9 rubric 行 {row}: 要素 '{rid}' の rubric_items に {row} が含まれていない（片方向 drift）")

# C10: operational-knowhow.md / hooks-reference.md の "> provenance: <level> · id: <a> / <b>（...）" 行を台帳と突合
prov_by_id = {e.get("id"): e.get("provenance") for e in elements}
for knowhow in [k for k in knowhow.split(":") if k and os.path.isfile(k)]:
    for ln, line in enumerate(open(knowhow, encoding="utf-8"), 1):
        m = re.match(r"^>\s*provenance:\s*([a-z-]+)\s*·\s*id:\s*(.+)$", line.strip())
        if not m:
            continue
        level, rest = m.group(1), m.group(2)
        if level not in levels:
            v.append(f"C10 {knowhow}:{ln}: level '{level}' は provenance_levels に未定義")
        ids_part = re.split(r"[（(]", rest, maxsplit=1)[0]
        for kid in [i.strip() for i in ids_part.split("/") if i.strip()]:
            if kid not in idset:
                v.append(f"C10 {knowhow}:{ln}: id '{kid}' が台帳に存在しない")
            elif prov_by_id[kid] != level:
                v.append(f"C10 {knowhow}:{ln}: id '{kid}' は台帳では '{prov_by_id[kid]}'、本文は '{level}'")

# C11: --selection 指定時、対象の harness-selection.json を台帳と突合
if selection:
    by_id = {e.get("id"): e for e in elements}
    try:
        s = json.load(open(selection, encoding="utf-8"))
    except Exception as ex:
        s = None
        v.append(f"C11 selection JSON parse error: {ex}")
    if isinstance(s, dict):
        if s.get("schema") != "harness-selection/v1":
            v.append(f"C11 selection schema が harness-selection/v1 ではない: {s.get('schema')}")
        if s.get("decided_by") not in ("user", "default"):
            v.append(f"C11 selection トップレベル decided_by '{s.get('decided_by')}' は user / default のいずれかでない")
        sels = s.get("selections", {})
        if not isinstance(sels, dict):
            v.append("C11 selection の selections が object でない")
            sels = {}
        for i in ids:
            if i not in sels:
                v.append(f"C11 selection に要素 '{i}' の entry が無い（全要素を載せる）")
        valid_by = ("user", "default", "excluded", "scale")
        for i, ent in sels.items():
            if i not in idset:
                v.append(f"C11 selection の '{i}' は台帳に存在しない id")
                continue
            if not isinstance(ent, dict) or not isinstance(ent.get("selected"), bool):
                v.append(f"C11 selection '{i}': selected が boolean でない")
                continue
            if ent.get("decided_by") not in valid_by:
                v.append(f"C11 selection '{i}': decided_by '{ent.get('decided_by')}' は {list(valid_by)} のいずれかでない")
            e = by_id[i]
            is_group_d = e.get("provenance") == "repo-specific" or e.get("portable") is False
            if is_group_d and ent.get("decided_by") != "excluded":
                v.append(f"C11 selection '{i}': repo-specific / portable:false の要素は decided_by:excluded にする")
            if not is_group_d and ent.get("decided_by") == "excluded":
                v.append(f"C11 selection '{i}': decided_by:excluded は repo-specific / portable:false の要素にのみ使う")
            if e.get("provenance") == "official" and ent.get("selected") is not True:
                v.append(f"C11 selection '{i}': official（Anthropic 公式由来）の要素は外せない。selected:true にする")
            if not ent["selected"]:
                continue
            if is_group_d:
                v.append(f"C11 selection '{i}': repo-specific / portable:false は selected:true にできない")
            if e.get("kind") == "skill-group":
                chosen = ent.get("skills")
                if not isinstance(chosen, list) or not chosen:
                    v.append(f"C11 selection '{i}': skill-group は selected:true なら skills[] を空でなく列挙する（省略を全採用とみなさない）")
                else:
                    for sk in chosen:
                        if sk not in e.get("skills", []):
                            v.append(f"C11 selection '{i}': skills[] の '{sk}' は要素の skills に存在しない")
            def _sel(dep):
                d = sels.get(dep)
                return isinstance(d, dict) and d.get("selected") is True
            for dep in e.get("depends_on", []):
                if not _sel(dep):
                    v.append(f"C11 selection '{i}': depends_on '{dep}' が非選択（成立しない組合せ。選び直す）")
            for dep in e.get("soft_depends_on", []):
                if not _sel(dep):
                    warns.append(f"WARN selection '{i}': soft_depends_on '{dep}' が非選択 → 縮退形で採用: {e.get('note', '(note なし)')}")

# C12: --target 指定時、対象の生成物を target_contract と突合
if target and selection:
    try:
        sel_doc = json.load(open(selection, encoding="utf-8"))
        sels = sel_doc.get("selections", {}) if isinstance(sel_doc, dict) else {}
    except Exception:
        sels = {}
    by_id = {e.get("id"): e for e in elements}
    def tp(p):
        return os.path.join(target, p)
    def files_under(p):
        if os.path.isfile(p):
            return [p]
        out = []
        for root, _, fs in os.walk(p):
            for f in fs:
                if f.endswith((".md", ".json", ".sh", ".yaml", ".yml", ".ps1", ".txt")):
                    out.append(os.path.join(root, f))
        return out
    def grep_any(p, pattern):
        ap = tp(p)
        if not os.path.exists(ap):
            return None
        rx = re.compile(pattern)
        for f in files_under(ap):
            try:
                if rx.search(open(f, encoding="utf-8", errors="ignore").read()):
                    return True
            except OSError:
                continue
        return False
    claude_md = ""
    if os.path.isfile(tp("CLAUDE.md")):
        claude_md = open(tp("CLAUDE.md"), encoding="utf-8", errors="ignore").read()
    def run_check(c, eid, mode):
        ty = c.get("type"); p = c.get("path", ""); pat = c.get("pattern", "")
        ok, msg = True, ""
        if ty == "file_exists":
            ok = os.path.isfile(tp(p)); msg = f"{p} が無い"
        elif ty == "file_absent":
            ok = not os.path.exists(tp(p)); msg = f"{p} が存在する（非選択要素の混入）"
        elif ty == "dir_absent":
            ok = not os.path.isdir(tp(p)); msg = f"{p}/ が存在する（非選択要素の混入）"
        elif ty == "grep":
            r = grep_any(p, pat); ok = (r is True); msg = f"{p} に /{pat}/ が無い" + ("（path 自体が無い）" if r is None else "")
        elif ty == "grep_absent":
            r = grep_any(p, pat); ok = (r is not True); msg = f"{p} に /{pat}/ が現れている（非選択要素の混入）"
        elif ty == "import":
            ok = os.path.isfile(tp(p)) and re.search(r"^@" + re.escape(p) + r"\s*$", claude_md, re.M) is not None
            msg = f"CLAUDE.md に '@{p}' の行が無いか {p} が無い（名ばかり常時 load）"
        elif ty == "frontmatter_paths":
            ap = tp(p); ok = False
            if os.path.isfile(ap):
                txt = open(ap, encoding="utf-8", errors="ignore").read()
                m = re.match(r"^---\n(.*?)\n---", txt, re.S)
                ok = bool(m and re.search(r"^paths:", m.group(1), re.M))
            msg = f"{p} の frontmatter に paths: が無い（path-scope になっていない）"
        elif ty == "emphasis_max":
            ap = tp(p); n = 0
            if os.path.isfile(ap):
                n = len(re.findall(r"IMPORTANT|YOU MUST", open(ap, encoding="utf-8", errors="ignore").read()))
            ok = n <= int(c.get("max", 5)); msg = f"{p} の emphasis が {n} 件（上限 {c.get('max', 5)}）"
        elif ty == "gitignore":
            gi = tp(".gitignore"); ok = False
            if os.path.isfile(gi):
                ok = any(l.strip() == pat for l in open(gi, encoding="utf-8", errors="ignore"))
            msg = f".gitignore に '{pat}' の行が無い"
        else:
            ok = False; msg = f"未知の check type '{ty}'"
        if not ok:
            v.append(f"C12 {eid} [{mode}] {ty}: {msg}")
    def is_selected(i):
        d0 = sels.get(i)
        return isinstance(d0, dict) and d0.get("selected") is True
    required_files = set()
    for e in elements:
        if is_selected(e.get("id")):
            required_files.update(e.get("files", []))
    for e in elements:
        eid = e.get("id"); selected = is_selected(eid)
        contract = e.get("target_contract", {})
        for c in contract.get("when_selected" if selected else "when_unselected", []):
            run_check(c, eid, "selected" if selected else "unselected")
        # skills / commands / files の自動検査
        chosen = sels.get(eid, {}).get("skills") if isinstance(sels.get(eid), dict) else None
        for s in e.get("skills", []):
            want = selected and (e.get("kind") != "skill-group" or (isinstance(chosen, list) and s in chosen))
            exists = os.path.isfile(tp(f".claude/skills/{s}/SKILL.md"))
            if want and not exists:
                v.append(f"C12 {eid} [selected] skill: .claude/skills/{s}/SKILL.md が無い")
            if (not want) and exists:
                v.append(f"C12 {eid} [unselected] skill: .claude/skills/{s}/ が存在する（非選択 skill の混入）")
        for cmd in e.get("commands", []):
            exists = os.path.isfile(tp(f".claude/commands/{cmd}.md"))
            if selected and not exists:
                v.append(f"C12 {eid} [selected] command: .claude/commands/{cmd}.md が無い")
            if (not selected) and exists:
                v.append(f"C12 {eid} [unselected] command: .claude/commands/{cmd}.md が存在する（非選択 command の混入）")
        for f in e.get("files", []):
            exists = os.path.exists(tp(f))
            if selected and not exists:
                v.append(f"C12 {eid} [selected] file: {f} が無い")
            if (not selected) and exists and f not in required_files:
                v.append(f"C12 {eid} [unselected] file: {f} が存在する（非選択要素の付随ファイルの混入）")
    # 共通契約
    if re.search(r"<!-- id:", claude_md):
        v.append("C12 common: CLAUDE.md に <!-- id: --> マーカーが残っている")
    if grep_any(".claude/rules", r"<!-- id:") is True:
        v.append("C12 common: .claude/rules に <!-- id: --> マーカーが残っている")
    if os.path.isdir(tp(".setup-automate")):
        gi = tp(".gitignore")
        if not (os.path.isfile(gi) and any(l.strip() == ".setup-automate/" for l in open(gi, encoding="utf-8", errors="ignore"))):
            v.append("C12 common: .setup-automate/ があるのに .gitignore に '.setup-automate/' が無い")

# C6: 各 SKILL.md の metadata.provenance と台帳の突合
n_skills = 0
if os.path.isdir(skills_dir):
    for name in sorted(os.listdir(skills_dir)):
        p = os.path.join(skills_dir, name, "SKILL.md")
        if not os.path.isfile(p):
            continue
        n_skills += 1
        txt = open(p, encoding="utf-8").read()
        fm = txt.split("---", 2)
        if len(fm) < 3 or not txt.startswith("---"):
            continue
        # frontmatter 内の "metadata:" ブロック配下の provenance を取る（簡易 YAML 走査）
        declared = None
        in_meta = False
        for line in fm[1].splitlines():
            if re.match(r"^metadata:\s*$", line):
                in_meta = True
                continue
            if in_meta:
                if line.startswith("  "):
                    m = re.match(r"^\s+provenance:\s*(\S+)", line)
                    if m:
                        declared = m.group(1).strip('"').strip("'")
                else:
                    in_meta = False
        expected = prov_by_skill.get(name)
        if declared == "mixed" and name != "agent-harness-bootstrap":
            v.append(f"C6 {name}: metadata.provenance 'mixed' は agent-harness-bootstrap（台帳の保持者）にのみ許す")
        elif declared is None and expected is not None and name != "agent-harness-bootstrap":
            v.append(f"C6 {name}: 台帳では '{expected}' だが SKILL.md に metadata.provenance が無い")
        elif declared is not None and expected is None and declared != "mixed":
            v.append(f"C6 {name}: SKILL.md に metadata.provenance '{declared}' があるが台帳に未登録")
        elif declared is not None and expected is not None and declared != expected:
            v.append(f"C6 {name}: SKILL.md は '{declared}'、台帳は '{expected}' で不一致")

for line in warns:
    print(line)
for line in v:
    print(line)
print(f"SUMMARY elements={len(elements)} skills={n_skills} violations={len(v)}")
PY
)

SUMMARY=$(printf '%s\n' "$OUT" | tail -n 1)
VIOL=$(printf '%s\n' "$OUT" | sed '$d')
N_VIOL=$(printf '%s' "$SUMMARY" | sed -E 's/.*violations=([0-9]+).*/\1/')

if [[ "$MODE" == "report" ]]; then
  echo "=== provenance-check report ==="
  echo "$SUMMARY"
  [[ -n "$VIOL" ]] && printf '%s\n' "$VIOL"
  exit 0
fi

if [[ "$N_VIOL" != "0" ]]; then
  echo "FAIL: provenance.json と実体の不整合 ($N_VIOL 件)"
  printf '%s\n' "$VIOL"
  exit 1
fi
echo "PASS: provenance.json は実体と整合 ($SUMMARY)"
[[ -n "$VIOL" ]] && printf '%s\n' "$VIOL"   # WARN 行（soft_depends_on の欠落）があれば表示
exit 0
