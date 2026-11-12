# Issue 本文テンプレートと応答形式

SKILL.md「Issue ファイルの必須項目」の具体形。起票・close のたびにこのひな形を埋める。

## 本文テンプレート（`issues/open/<id>-<slug>.md`）

```
---
id: 0012
title: ログイン画面で 500 エラー
severity: high        # high / medium / low
category: bug         # bug / improvement / docs など運用側で決めた語
created: 2026-01-15
status: open          # ディレクトリ名と一致させる
priority: P2          # 任意。P1 次に着手 / P2 関係する所を触る時 / P3 判断待ち・保留
reviewed: 2026-01-15  # 任意。棚卸し（triage）で前提を確かめた日
related: []           # 再発時は過去 Issue の id を入れる（commit 前の check-new が見るのは本文の「関連:」欄で、ここではない）
---

関連: <related の結果を書く>
<!-- issue_tracker.py related --text "<題名>" で確かめてから、「関連: <関連 issue のパス>（別にした理由）」か「関連: なし（related 確認済み）」に書き換える。書き換えないと commit 前の check-new が止める -->

## 症状
## 再現手順
1.
## 該当箇所
- path/to/file:行番号
## 仮説
## 修正候補
## 関連ファイル

## 利用者の要望
<!-- issue_tracker.py request が「- <日時> <原文>」を足す。手で書く時も同じ形 -->

## close 時に追記
- 修正内容:
- 関連コミット:
- 検証結果(確かめた条件を1文): 記録ファイルのパス
```

## 応答形式（起票・遷移・close の報告）

| 項目 | 内容 |
|---|---|
| 操作 | 起票 / 遷移(移行元 → 移行先) / close |
| Issue | id と title |
| 配置 | 移動後のファイルパス |
| 根拠 | 遷移条件を満たした事実(再現手順の有無、コミットハッシュ、検証記録のパス) |
| 次の一手 | 次に必要な遷移、または「なし」 |

報告に含めないもの: Issue 本文の全文転記、件数や列挙(記録ファイルへ置く)。
