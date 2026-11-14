# 入学考(TMUA / TSA / BMAT)归档

2026-11-14 从题库(Maimai-l/AL-questionbank 的 data 分支,版本 1f146be)中移出。

| 内容 | 说明 |
|---|---|
| `admissions.db` | `questions` 表中 syllabus 为 TMUA、TSA、BMAT 的 1888 行，列与当时的 `questions` 表相同(44 列);`schema_note` 存当时的建表语句 |
| `img_adm/` | 逐题题图(`questions.image` 指向这里) |
| `img_tara/` | TSA/BMAT 题干里引用的图(`question_latex` 中的 `img_tara/...`) |
| `papers/bank/` | 原卷与答案 PDF(TMUA、TARA) |
| `adm_practice.html`、`adm_practice.js` | TMUA/TARA 刷题页及其数据，两个文件放在一起、旁边放 `img_adm/`、`img_tara/` 即可单独打开 |

恢复到题库:

```bash
cp -r img_adm img_tara <仓库>/data/ && cp -r papers/bank <仓库>/data/papers/
sqlite3 <仓库>/data/caie.db "ATTACH 'admissions.db' AS a; INSERT INTO questions SELECT * FROM a.questions;"
# 列数不同时按列名插入;之后重建全文索引(pipeline/ocr/apply_reocr.py 末尾的 q_fts 重建语句)
```

处理这些数据的脚本在仓库 `attic/admissions/` 下(原 `pipeline/admissions_rebuild/` 等)。
