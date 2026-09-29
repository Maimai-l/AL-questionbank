# 流水线说明

所有脚本都可以用两种方式运行:

```bash
python3 -m pipeline.tags.retag        # 需先 cd 到项目根目录
python3 pipeline/tags/retag.py        # 在任意目录下均可
```

路径统一由 `lib/paths.py` 解析:数据库默认是 `data/caie.db`,题图与教材位于
`data/`,流水线输入(PDF、OCR 原始结果)约定放在 `raw/`。

## 运行前的要求

| 项目 | 说明 |
|---|---|
| Python 3.8+ | 查询与页面只用标准库 |
| `pymupdf` | 解析 PDF 的脚本需要。`pip install pymupdf` |
| `pdftotext` | 仅 `split_ms.py` 需要(poppler-utils) |
| `requests` | OCR 与入学考下载需要 |
| `PADDLE_TOKEN` | OCR 需要,见 [network.md](network.md) |

单次 OCR 不得超过 100 页,否则会超时,整个任务作废。`ocr_ms.py` 中的
`MAX_PAGES = 100` 即此限制。

## CAIE 长题线(9709 / 9231 / 9618)

按必须的执行顺序排列:

```
1  下载      pipeline/fetch/fetch_any.py        通用下载器(9231 用 --url-template 指向 papacambridge,见 network.md)
2  切分      pipeline/split/split_qp.py         试卷 → 一题一条记录
            pipeline/split/split_ms.py         评分细则 → 按题号切开(需 pdftotext)
3  裁图      pipeline/split/crop.py             按 bbox 渲染 PNG
            pipeline/fetch/fix_names.py        修正裁图文件名引用
4  转写      pipeline/ocr/ocr.py                题干 → LaTeX(PaddleOCR-VL)
            pipeline/ocr/merge_ocr.py          写回
            pipeline/ocr/ocr_ms.py             评分细则整份 OCR
            pipeline/ocr/parse_ms_ocr.py       解析返回的 HTML 表格
            pipeline/ocr/merge_ms_ocr.py       写回 ms_latex
5  修复      pipeline/ocr/fix_garbled.py        切 900px 横条重读退化的 OCR
            pipeline/ocr/salvage.py            截断保留可读前缀
6  关键词    pipeline/tags/tag.py、topics_9231.py、topics_9618.py、tag_any.py
            pipeline/tags/export_weak.py、merge_retag.py   低置信组交给模型重标
7  建库      pipeline/db/build_db.py            单科库(含 FTS5)
            pipeline/db/combine.py             合成 data/caie.db
8  文本规整  pipeline/text/clean_encoding.py → fix_newlines.py → html_tables.py
9  质量      pipeline/text/audit_text.py        可读性审计(只报告)
            pipeline/text/flag_quality.py      写 q_quality / ms_quality
            pipeline/text/mark_partial.py      标出被截断保留的题干
            pipeline/split/rebuild_text.py     切分规则改动后,就地重建题干、分值与 LaTeX 末尾(不重建整表)
10 大纲标签  pipeline/tags/syllabus.py          大纲 PDF → syllabus.json
            pipeline/tags/topic_model.py       用大纲原文给主题打分
            pipeline/tags/eval_tags.py         新旧标签器对比(只报告)
            pipeline/tags/retag.py             合成标签并写回
            pipeline/tags/tag_batches.py       tagger 子 agent 按小问复核(plan / apply / write),见 tagging-plan.md
            pipeline/tags/prereq.py            先修关系 → prereq.json
11 出页面    pipeline/export/build_site.py      data.js、textbooks.js 与页面 → data/
```

执行顺序上的约束:

- `combine.py` 会重建 questions 表,因此 `flag_quality.py` 必须在它之后运行,否则
  质量标记会被静默抹掉。
- `mark_partial.py` 必须在 `flag_quality.py` 之后,后者会覆盖 `q_quality`。
- 第 8 步的三个脚本顺序为字形 → 换行 → 表格,顺序颠倒会互相破坏。
- `retag.py` 需要 `syllabus.json` 已存在。
- `tag_batches.py write` 把 `pipeline/tags/retag_model.json` 写进库,须在 `retag.py`
  之后运行;`combine.py` 或 `merge_admissions.py` 重建题目后也要重跑一次,否则模型
  标签会被覆盖。`retag.py` 不改 `topic_source='model'` 的题。
- `build_site.py` 必须最后运行,否则页面读到的是旧数据。

## 入学考选择题线(TMUA / TSA / BMAT)

脚本位于 `pipeline/admissions_rebuild/`,路径经 `lib/paths.py` 解析,可在任意目录下运行:
原卷在 `raw/bank/`(`paths.BANK`),逐页 OCR 在 `raw/bank_ocr/`(`paths.BANK_OCR`),
跟踪的中间结果(`questions_adm.json`、`answers.json`、`ms_tmua.json`、`retag_*.json`)
在脚本旁(`paths.ADM`),题图在 `data/img_adm/`(`paths.IMG_ADM`)。

```bash
A=pipeline/admissions_rebuild
python3 $A/manifest.py                      # 0. 下载 PDF 与考纲,支持续跑
python3 $A/ocr_bank.py                      # 1. 按页 OCR(第三个参数为并发数,默认 4)
python3 $A/parse_keys.py                    # 2. 答案键 → answers.json
python3 $A/split_admissions.py              # 3. 切题 → questions_adm.json,逐卷校验
python3 $A/attach_ms.py                     # 4. 挂接 TMUA 官方详解
python3 $A/tag_admissions.py                # 5. 主题标注与 PS/CT 配比校验
python3 $A/render_adm_imgs.py               # 6. 逐题原页图
python3 $A/audit_adm_imgs.py                #    裁图审计,全部通过后再推送
python3 $A/merge_admissions.py              # 7. 合并进 data/caie.db(会重建入学考行)
python3 pipeline/tags/tag_batches.py write  #    重写模型标签,否则被第 7 步覆盖
python3 pipeline/export/build_site.py       # 8. 出页面
```

`review_batches.py` 负责把需要读图判断的题目分批、生成给 agent 的提示词,并在回收时
用不变量校验结果。改判结果写入 `retag_tmua.json` 与 `retag_tara.json`,不要直接改
`questions_adm.json`,后者在重跑时会被覆盖。

## 教材线

```bash
python3 -m pipeline.ocr.ocr_books "<教材 PDF 目录>" "<页面输出目录>"
python3 -m pipeline.books.split_chapters "<x.pdf>" "<页面输出目录>/<书>" data/books/9709_p23 --prefix 9709_p23
python3 -m pipeline.books.chapters index data/caie.db data/books/9709_p23 --syllabus 9709 --components 2,3
python3 -m pipeline.books.chapters coverage
```

`--components` 不能省略:"Integration" 在 P1 是 1.8,在 P2 是 2.5,在 P3 是 3.5,
仅凭章节正文无法区分。

`ocr_books.py` 会输出 `_raw.jsonl`(接口原始返回),应当保留:重新落盘时可以免费
从它重建。接口的一行 JSONL 包含多页,必须从 `layoutParsingResults` 中逐页取出,
按行写文件会只留下每组的最后一页。

## 导出分发包(pipeline/export/)

| 脚本 | 产出(写入 `exports/`,不跟踪) |
|---|---|
| `build_site.py` | `data/` 下的 data.js、textbooks.js 与页面 |
| `export_web.py` | `data/data.js`,可单独运行 |
| `export_textbooks.py` | `data/textbooks.js`,可单独运行 |
| `export_all_chapters.py` | 每章一个 ZIP,含章节正文、同主题真题、题图与评分细则 |
| `export_admissions_banks.py` | TMUA 包与 TARA(TSA 加 BMAT)包 |
| `export_9709_p1.py` | 9709 P1 文本包与图片包 |
| `export_curated_hard_papers.py` | 六套人工精选难卷 |
| `export_cs_code_questions.py` | 9618 中要求实际编写代码的题目 |
| `index_export_zips.py` | 为每个导出 ZIP 嵌入统一索引,先 dry run 再 `--write` |

## 题图裁切

`pipeline/split/` 中三个文件分工如下:

| 文件 | 职责 |
|---|---|
| `furniture.py` | 找出每页的固定元素:页码、页脚、水印、条形码、页边竖排文字与灰条、四角标记、BLANK PAGE、"is printed on the next page" |
| `split_qp.py` | 按题号切分,每页的上下边界取自 `furniture.band`,不再使用固定的 50/790 |
| `crop.py` | 裁切区域 = 题目范围 ∩ 固定元素之间的区域;跨边界的内容整体纳入;区域内残留的固定元素涂白 |
| `audit_crops.py` | 不看图的审计,见下 |

`audit_crops.py raw/pdf` 对每道题检查六项:

- 裁切区域是否与任何固定元素重叠(涂白的另计,并逐像素确认已涂白)
- cut:真实内容是否被裁切边界切断
- uncovered:题目页上的真实内容是否不属于任何一题
- slack:最后一段裁图底部是否有超过 30pt 的无内容空白
- overlap:同一页上两题的裁切区域是否共有含内容的部分(一题的裁图里出现下一题的开头)
- `--crop old` 按原裁切规则计算,用于对比

改动裁切规则后,先运行审计,全部通过后再重新生成题图:

```bash
python3 pipeline/split/audit_crops.py raw/pdf
```

## 入学考题图(img_adm)

`render_adm_imgs.py` 读 `raw/bank/` 下的原卷(`manifest.py raw/bank` 下载),写入
`data/img_adm/`。与 CAIE 裁图的做法相同:

- 页面固定元素:页码、各年份写法不同的页脚、页眉横线、页顶标志、BLANK PAGE
- 题号在全卷范围内按 1、2、3… 依次认领,选项旁的数值不会被当成题号。文本层损坏
  的三种情况都能还原:UCLES 老卷的 29 位偏移、TMUA 2016/2017 的 CambriaMath
  数字(U+0372 起)、字形缺失的空白题号
- 共享材料跨页时,续页顶部的材料段同样拼到每道相关题前面
- 下一题题号在下一页顶端时,那一页不属于本题

`audit_adm_imgs.py` 检查:题号序列是否完整且有序、裁图内是否有别题的题号、固定元素
是否残留(逐像素)、题目页上的内容是否被遗漏、有没有按整页输出的题。当前 55 份试卷、
1888 题全部通过。

## 已知问题

1. **入学考脚本已改为经 `lib/paths.py` 解析路径(2026-09-29)。** 在其他目录下运行验证过:
   `manifest.py` 下载到 `raw/bank`;`render_adm_imgs.py` 重出的 1888 张图与现有图逐像素相同,
   `audit_adm_imgs.py` 全部通过;`tag_admissions.py` 重跑后 `questions_adm.json` 无变化;
   `merge_admissions.py` 在库副本上重跑,除 291 道带插图的题(插图取自 `raw/bank_ocr`)外
   与现库一致。`ocr_bank.py`、`parse_keys.py`、`split_admissions.py`、`attach_ms.py`、
   `reocr_*.py` 依赖 `raw/bank_ocr`,云端没有这份 OCR 结果,只做了编译检查。
2. **题图与题干已按新切分重建(2026-09-29)。** 重建时又修了三处切分问题:9231 2021 年 6 月
   卷 3、卷 4 的页脚在距页底 81pt 处,原先未被识别,留在题图和题干里(32 题);条形码判别把
   "……"、"●●●" 和 Symbol 字体字符当成乱码,丢掉了 9618 伪代码填空行(40 行);题目首行带
   分式或列向量时,该行高出题号,原先被划给上一题(约 90 对题)。共重出 220 张题图,
   `rebuild_text.py` 改写 428 题:题干 263、LaTeX 末尾的附加页与版权文字 207、分值 5
   (`9618_s24_13_q07` 19→22,`9709_s22_33_q02/q03`、`9709_s23_33_q05/q06`)。
   `question_latex` 仍是旧题图的 OCR,只截掉了末尾;若要与新题图完全一致,需重新 OCR。
3. **14 个 `img_tara` 插图缺失。** 题干中引用了 958 个 `img_tara/` 文件,其中 14 个在
   旧仓库中就不存在。
4. **`export_project.py` 缺失。** 旧文档描述的"将题库导出为 CSV"脚本不在仓库中。
5. **`export_textbooks.py` 是简化版。** 旧文档说它会把目录名 `9709_p1` 还原为
   `Paper 1 · Pure Mathematics 1`,仓库中的版本没有这一步。
6. **`export_admissions_banks.py` 需要原始数据。** TMUA 包引用了 166 张官方详解插图,
   位于 `raw/admissions_ocr_source/TMUA/worked_answers/`,该目录目前不在云端。
7. **`export_9709_p1.py` 需要 `cwebp`。** 云端运行前需先安装 webp 工具。
