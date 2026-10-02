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
| `pdftotext` | `split_ms.py`、`rebuild_ms.py` 需要(`apt-get install poppler-utils`) |
| `pillow` | 生成题图(`crop.py`、`render_adm_imgs.py` 经 `lib/png16.py` 存成 16 级灰度)与 `fix_garbled.py` 切横条需要。`pip install pillow` |
| Python 3.11+ | `answer_lines.py` 的正则用了占有量词 |
| `cwebp` | 仅 `export_9709_p1.py` 需要(`apt-get install webp`) |
| `requests` | OCR 与入学考下载需要 |
| `PADDLE_TOKEN` | OCR 需要,见 [network.md](network.md) |

单次 OCR 不得超过 100 页,否则会超时,整个任务作废。`ocr_ms.py` 中的
`MAX_PAGES = 100` 即此限制。

## CAIE 长题线(9709 / 9231 / 9618)

按必须的执行顺序排列:

```
1  下载      pipeline/fetch/fetch_any.py        通用下载器(9231 用 --url-template 指向 papacambridge,见 network.md)
            pipeline/fetch/fetch_fraft.py      按 cie.fraft.cn 的文件清单补下库中没有的试卷及其评分细则
2  切分      pipeline/split/split_qp.py         试卷 → 一题一条记录
            pipeline/split/split_ms.py         评分细则 → 按题号切开(需 pdftotext)
3  裁图      pipeline/split/crop.py             按 bbox 渲染 PNG
            pipeline/fetch/fix_names.py        修正裁图文件名引用
4  转写      pipeline/ocr/ocr.py                题干 → LaTeX(PaddleOCR-VL)
            pipeline/ocr/merge_ocr.py          写回
            pipeline/ocr/ocr_ms.py             评分细则整份 OCR
            pipeline/ocr/parse_ms_ocr.py       解析返回的 HTML 表格
            pipeline/ocr/merge_ms_ocr.py       写回 ms_latex(自带第 8 步规整与质量评级)
5  修复      pipeline/ocr/fix_garbled.py        切 900px 横条重读退化的 OCR
            pipeline/ocr/salvage.py            截断保留可读前缀
            pipeline/ocr/apply_reocr.py        重出题图后的新 OCR 写回 question_latex,去掉答题线
6  关键词    pipeline/tags/tag.py、topics_9231.py、topics_9618.py、tag_any.py
            pipeline/tags/export_weak.py、merge_retag.py   低置信组交给模型重标
7  建库      pipeline/db/build_db.py            单科库(含 FTS5)
            pipeline/db/combine.py             合成 data/caie.db
            pipeline/db/add_papers.py          库建成后补收新卷:就地切分、裁图、挂评分细则、按考纲打主题并插入(add),
                                               OCR 之后给新题评质量(finish);不重建整表
8  文本规整  pipeline/text/clean_encoding.py → fix_newlines.py → html_tables.py
9  质量      pipeline/text/audit_text.py        可读性审计(只报告)
            pipeline/text/flag_quality.py      写 q_quality / ms_quality
            pipeline/text/mark_partial.py      标出被截断保留的题干
            pipeline/split/rebuild_text.py     切分规则改动后,就地重建题干、分值与 LaTeX 末尾(不重建整表)
            pipeline/split/rebuild_ms.py       评分细则解析改动后,就地重建 ms_text 与总分(读 raw/ms/,需 pdftotext)
            pipeline/text/fix_ms_prefix.py     把 parse_ms_ocr.py 错放到下一题开头的 ms_latex 移回原题
            pipeline/text/split_parts.py       题干与评分细则按小问切开,写 part_data(分值、主题、任务类型)
            pipeline/ocr/drop_partial_ms_ocr.py OCR 评分细则缺小问时改用文本层(111 题,多为 9618 卷 2 第 8 题)
            pipeline/text/check_latex.py       找出 KaTeX 无法渲染的公式(评分细则按单元格,需 node)
            pipeline/ocr/latex_fix_batches.py  子 agent 对照原页更正这些公式(plan / verify / apply),写入 ms_fixes.jsonl
            pipeline/ocr/apply_ms_fixes.py     重放按原页人工更正的评分细则与题干公式(ms_fixes.jsonl)
            pipeline/text/review_batches.py    子 agent 对照题图与细则原页审查题干和评分细则(抽样或全量,只报告)
            pipeline/split/ms_total_from_ocr.py 只有 OCR 细则的题(35 题)从 ms_latex 读小计,写 ms_total / totals_agree
10 大纲标签  pipeline/tags/syllabus.py          大纲 PDF → syllabus.json
            pipeline/tags/topic_model.py       用大纲原文给主题打分
            pipeline/tags/eval_tags.py         新旧标签器对比(只报告)
            pipeline/tags/retag.py             合成标签并写回
            pipeline/tags/tag_batches.py       tagger 子 agent 按小问复核(plan / apply / write),见 tagging-plan.md
            pipeline/tags/prereq.py            先修关系 → prereq.json
11 详解      pipeline/explain/explain_batches.py explainer 子 agent 按小问写详解(plan / apply / write),写 explanation
            pipeline/explain/term_tree.py      关键术语:统计决定收录、级别、上下级与易混,termwriter 子 agent 按细则原文改写定义与区别 → exports/<科目>_terms/(Obsidian 仓库)
12 出页面    pipeline/export/build_site.py      data.js、textbooks.js 与页面 → data/
```

执行顺序上的约束:

- `combine.py` 会重建 questions 表,因此 `flag_quality.py` 必须在它之后运行,否则
  质量标记会被静默抹掉。
- `mark_partial.py` 必须在 `flag_quality.py` 之后,后者会覆盖 `q_quality`。
- 第 8 步的三个脚本顺序为字形 → 换行 → 表格,顺序颠倒会互相破坏。
- `retag.py` 需要 `syllabus.json` 已存在。
- `tag_batches.py write` 把 `pipeline/tags/retag_model.json` 写进库,须在 `retag.py`
  之后运行;`combine.py` 重建题目后也要重跑一次,否则模型标签会被覆盖。
  `merge_admissions.py` 在重建入学考行后自行调用它。`retag.py` 不改
  `topic_source='model'` 的题。
- `rebuild_text.py` 在 `rebuild_ms.py` 之前:后者按题面分值判定 `totals_agree`。
- `split_parts.py` 读 `marks_parts` 与 `topic_parts`,须在第 10 步标签写回之后运行;
  标签或题干改动后重跑一次,导出才会用到新的小问数据。
- 评分细则每行为 `答案  |  评分代码  |  说明`,列之间是两侧各两个空格的竖线(`lib/scheme.py`);
  公式中的竖线不带这样的空格。单元格内换行存为 `<br>`,由 `fix_newlines.py` 写入,页面与导出负责显示。
- `apply_ms_fixes.py` 之后重跑 `split_parts.py`,小问数据才会用到更正后的文本。
- `drop_partial_ms_ocr.py` 在 OCR 评分细则合并(`merge_ms_ocr.py`)之后、`split_parts.py`
  之前运行,否则小问拿到的是被截断的细则。
- `explain_batches.py plan` 读 `part_data`,须在 `split_parts.py` 之后;小问标签变化后,
  已写入的详解在 `apply` 时会因标签不符被拒收,需要重做。9618 卷 1–3 已完成
  (2026-09,874 题,Sonnet);卷 4 未做。
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
python3 $A/page_batches.py plan --out raw/page_batches/runN   # 2b. 切不好的页交给转录员
python3 $A/page_batches.py apply --out raw/page_batches/runN  #     收回,写入 page_fixes.json
python3 $A/split_admissions.py              # 3. 切题 → questions_adm.json,逐卷校验
python3 $A/attach_ms.py                     # 4. 挂接 TMUA 官方详解
python3 $A/tag_admissions.py                # 5. 主题标注与 PS/CT 配比校验
python3 $A/render_adm_imgs.py               # 6. 逐题原页图
python3 $A/audit_adm_imgs.py                #    裁图审计,全部通过后再推送
python3 $A/merge_admissions.py              # 7. 合并进 data/caie.db(重建入学考行,再写回模型标签)
python3 pipeline/export/build_site.py       # 8. 出页面
```

`page_fixes.json`(跟踪)是对照页面图像修正过的逐页识别文本,`split_admissions.py`
与 `attach_ms.py` 读页时优先使用(`page_fixes.py`)。`page_batches.py plan` 先切到临时
文件,与跟踪的 `questions_adm.json` 逐题比较(缺题、答案字母不在选项中、文本短一半以上、
与原题用词重合不足一半即错位),把相关页面渲染成图片,连同识别文本和"重点核对"提示分批
交给转录员子 agent;`apply` 只收下保留了全部 `<img>`、长度未缩短三分之一以上的页面。
`option_texts.py` 从题干按规则取出每个选项的文字,写 `option_texts`(图形选项为 null),
`merge_admissions.py` 插入时同样调用。

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
| `export_all_chapters.py` | 每章一个 ZIP,含章节正文、同主题真题、题图与评分细则;只有部分小问属于本章的题,只给这些小问及其评分细则(`part_data`)。`--syllabus`、`--chapter` 限定范围,`--no-images` 不含任何图片,文件名以 `_no_images` 结尾 |
| `export_admissions_banks.py` | TMUA 包与 TARA(TSA 加 BMAT)包 |
| `export_9709_p1.py` | 9709 P1 文本包与图片包 |
| `export_curated_hard_papers.py` | 六套人工精选难卷 |
| `export_cs_code_questions.py` | 9618 中要求实际编写代码的题目(整题规则加小问任务类型),列出代码小问 |
| `index_export_zips.py` | 为每个导出 ZIP 嵌入统一索引,先 dry run 再 `--write`;每题带 `q_quality`、`ms_quality`、`text_usable`、`has_diagram`、各小问的分值/主题/任务类型、入学考选项文字 |

`question_md.py` 是各导出共用的题目 Markdown:题干识别质量为 missing、garbled 或
partial 的题,不输出不可用的文本,而是提示以原题图为准。

## 题图裁切

`pipeline/split/` 中三个文件分工如下:

| 文件 | 职责 |
|---|---|
| `furniture.py` | 找出每页的固定元素:页码、页脚、水印、条形码、页边竖排文字与灰条、四角标记、BLANK PAGE、"is printed on the next page" |
| `split_qp.py` | 按题号切分,每页的上下边界取自 `furniture.band`,不再使用固定的 50/790。点线答题行不进题干文本,也不进题图;每段范围另记 `y1_rows`(含答题行的下沿),只有答题行的续页(下一题开始之前)记为 `rows_only`,供带答题区的裁图使用 |
| `crop.py` | 裁切区域 = 题目范围 ∩ 固定元素之间的区域;跨边界的内容整体纳入;区域内残留的固定元素涂白。`rows=True` 生成带答题区的裁图(`render_rows`,与题图相同时不保存) |
| `audit_crops.py` | 不看图的审计,见下 |
| `to_png16.py` | 把 `data/` 里的题图改存为 16 级灰度(4 位调色板 PNG),已是该格式的跳过 |
| `recrop.py` | 按现行规则重新生成库中已有 CAIE 题目的题图,只改图不改库;`--rows` 生成 `img*_ans/` 下带答题区的裁图;`--out` 先输出到别处比对 |

`audit_crops.py raw/pdf` 对每道题检查以下各项:

- 裁切区域是否与任何固定元素重叠(涂白的另计,并逐像素确认已涂白)
- cut:真实内容是否被裁切边界切断
- uncovered:题目页上的真实内容是否不属于任何一题
- slack:最后一段裁图底部是否有超过 30pt 的无内容空白
- overlap:同一页上两题的裁切区域是否共有含内容的部分(一题的裁图里出现下一题的开头)
- rows-out(`--crop rows`):题目页上的点线答题行是否没有进入任何带答题区的裁切区域
- `--crop old` 按原裁切规则计算,用于对比

改动裁切规则后,先运行审计,全部通过后再重新生成题图:

```bash
python3 pipeline/split/audit_crops.py raw/pdf
python3 pipeline/split/audit_crops.py raw/pdf --crop rows
python3 pipeline/split/recrop.py && python3 pipeline/split/recrop.py --rows
```

题图一律存成 16 级灰度(`lib/png16.py`):灰度取 0、17、…、255,文字边缘、图中阴影
(CAIE 填 204,恰为其中一级)与水印看不出变化,体积约为 8 位灰度 PNG 的 63%。黑白两级
会丢掉阴影区域,不用。`img_tara/` 是彩色 JPEG 插图,不在此列。

刷题页的白板以带答题区的裁图为底图(没有时用题图),每个小问下方保留原卷的答题区,
底图以下的画布仍可继续书写。题图本身保持紧凑,供阅读、导出与 OCR 使用。

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

1. **入学考脚本已改为经 `lib/paths.py` 解析路径并逐个验证(2026-09-29)。** 在其他目录下运行:
   `manifest.py` 下载到 `raw/bank`;`ocr_bank.py` 重新 OCR 123 份 PDF 到 `raw/bank_ocr`;
   `parse_keys.py` 重出的 `answers.json` 与跟踪版本逐字节相同;`render_adm_imgs.py` 重出的
   1888 张图与现有图逐像素相同;`tag_admissions.py` 重跑后 `questions_adm.json` 无变化;
   `merge_admissions.py` 在库副本上重跑,1888 题各列与现库完全一致(它现在自行写回模型标签,
   题干里的插图已在 `data/img_tara/` 时不再要求 `raw/bank_ocr` 存在)。
   `split_admissions.py`、`attach_ms.py`、`reocr_pages.py` 能跑通;单靠重新识别,新一轮切题
   只到 22/55 份卷零问题(1844 题,应为 1888),`attach_ms.py` 得 358/360:跟踪版本里有 58 题
   带人工补写(选项画在图里,当时对照页面图像逐项转录),识别本身做不到。
   **已从页面重建(2026-09-29)。** `page_batches.py` 把切不好的页面连同图像交给转录员子 agent
   (三轮,103 + 66 + 61 页),修正后的页面存在 `page_fixes.json`;同时改了三条切分规则
   (TMUA 按印出的题号再切一次并读题干里的 "(A, B, C, D or E)";已写出字母的图形选项不再
   把图上方的居中字母算作第二组选项;"3 …"、"4 …" 这样的陈述编号不当作丢了十位的题号)。
   结果:55/55 份卷零问题,1888 题与跟踪版本(已应用 `text_fixes.json`)逐题同号同答案,
   无缺题、无错位;`attach_ms.py` 360/360。抽查长度变化大的 27 题,新版均不差于旧版
   (补回首句、去掉串入的相邻题、`BMAT-2014-S1-q5` 选项补全到 H)。已用新结果覆盖
   `questions_adm.json` 并重新入库:232 道题干改变,主题标签无变化;不再被引用的 279 张
   `img_tara` 旧插图已删除。选项文字按规则写入 `option_texts`:1855 道选择题中 1725 道
   齐全,10 道部分为图形选项,120 道全部为图形选项。
   题干的人工修正写在 `text_fixes.json`(42 条:BMAT 串题与错位、漏掉的首句、识别错字),
   由 `merge_admissions.py` 在入库时应用;重跑切题不会冲掉。题号丢了首位数字
   ("2" 代表第 12 题)也在入库时改正。
2. **题图与题干已按新切分重建(2026-09-29)。** 重建时又修了三处切分问题:9231 2021 年 6 月
   卷 3、卷 4 的页脚在距页底 81pt 处,原先未被识别,留在题图和题干里(32 题);条形码判别把
   "……"、"●●●" 和 Symbol 字体字符当成乱码,丢掉了 9618 伪代码填空行(40 行);题目首行带
   分式或列向量时,该行高出题号,原先被划给上一题(约 90 对题)。共重出 220 张题图,
   `rebuild_text.py` 改写 428 题:题干 263、LaTeX 末尾的附加页与版权文字 207、分值 5
   (`9618_s24_13_q07` 19→22,`9709_s22_33_q02/q03`、`9709_s23_33_q05/q06`)。
   这 220 张图随后重新 OCR(`apply_reocr.py`):整张读 192 题;退化的再按 900px、500px 横条
   重读,又得 21 题;共 213 题换成新图的 OCR,其中 11 题原先是截断保留的 `partial`,现在完整。
   其余 7 题新结果都退化或丢内容,已对照题图人工校对(`pipeline/ocr/latex_checked.jsonl`,
   经 `apply_reocr.py` 写入);其中 `9709_s23_13_q09` 旧文本只剩 (c),`9709_s25_33_q03`
   的积分上限原为 3π/4,应为 π/4。
   OCR 把答题横线读成成百上千个编号下划线,`apply_reocr.py --strip-bank` 顺带从全库 34 题的
   `question_latex` 中去掉了这些内容(`9709_w23_13_q02` 一题就有 11 000 字)。
3. **评分细则与分值已重建(2026-09-29)。** 评分细则 PDF 全部下载到 `raw/ms/`(9709 2025 年
   6 月的 12 份来自 papacambridge,此前库中这 106 题没有评分细则)。`split_ms.py` 修了:
   标签只缩进一格或顶格("10(a)"、"10(c)(i)")、标签独占一行、标签印成 ".4"、缺括号
   ("5(b(iii)")、罗马数字到 (vi) 以上;小计后跟 Guidance 文字;另一种解法各带小计时误加;
   含 "mark scheme" 字样的行被当页眉丢掉;表头为 "Partial / Marks" 两行(9231_s23_ms_23,
   此前整卷无评分细则)。小计与题面分值不符而评分代码之和相符时取后者(18 题);仍读不出的
   8 题人工对照 PDF 核定,记在 `pipeline/split/ms_totals_checked.json`。题面一侧修了 3 题分值:
   分值后同一行跟着上标或分式下半("[6] 1"、"[1] c"),以及数组表头 "[9] [10]" 被当成分值。
   `totals_agree` 从 2568/2956 升到 2955/2956,378 份卷子的分值合计全部等于官方总分。唯一
   不符的 `9709_s24_33_q11` 是评分细则本身缺第 11 题:dynamicpapers、papacambridge、
   bestexamhelp、cie.fraft.cn 四个来源的 PDF 都是 19 页、只到第 10 题,共 66 分。`fix_ms_prefix.py` 另把 16 题 `ms_latex` 开头错放的内容移回原题或删去
   (评分通则、上一题的秩检验等)。9709 2025 年 6 月的 12 份评分细则已 OCR 并写入 `ms_latex`
   (106 题:98 ok、8 degraded);`parse_ms_ocr.py` 为此改为只接受比当前题号大 0 到 2 的
   标签,茎叶图的茎 "9" 原先会被当成第 9 题。
4. **14 个 `img_tara` 插图已补齐(2026-09-29)。** 均为 TSA/BMAT 各卷最后一题的图形选项,
   重新 OCR 的 `raw/bank_ocr` 中有同名文件,`merge_admissions.py` 已复制到 `data/img_tara/`,
   题干引用的 958 张插图现在全部存在。
5. **`export_project.py` 已补写(2026-09-29)。** 技能与仓库中都没有这个脚本,按文档描述重写:
   `exports/questions.csv` 一题一行,带题干与评分细则文本;`exports/image-only-questions.csv`
   列出题干文本缺失、乱码或截断、只能看原题图的题(62 题)。
6. **`export_textbooks.py` 已还原书名(2026-09-29)。** 教材下拉框原先显示目录名 `9709_p1`,
   现在显示 `Paper 1 · Pure Mathematics 1`,目录名保存在 `book_id` 字段。
7. **`export_admissions_banks.py` 已可运行(2026-09-29)。** TMUA 官方详解的 166 张插图改从
   `raw/bank_ocr/TMUA/worked_answers/`(`paths.BANK_OCR`)取,重新 OCR 后全部在;两个压缩包
   (TMUA 360 题 587 图,TARA 1528 题 2425 图)写到 `exports/`。
8. **`export_9709_p1.py` 需要 `cwebp`。** 云端先运行 `apt-get install -y webp`;已验证可导出
   380 题与 380 张无损 WebP 图。
9. **补收新卷(2026-09-29)。** `fetch_fraft.py` 从 cie.fraft.cn 补下库中没有的 148 份试卷及其
   评分细则:2021–2025 年 9709 卷 2、卷 6,2025 年新卷别(9709 `_x5`、9231 `_x4`),以及 2026 年
   3 月、6 月各科。fraft 有 79 份文件的字体没有 Unicode 映射(文本层是乱码),2 份被重排到
   Letter 纸上,均改用 papacambridge;`best_copy.py` 再对每份试卷比较三个站点的版本,取切出
   总分等于满分的一份(换了 8 份;`--ms` 对评分细则做同样的事,换了 29 份,2026 年 9709 的
   papacambridge 评分细则 `split_ms.py` 读不出)。`add_papers.py` 就地切分、裁图、插入 1093 题,
   其后 OCR(题干、评分细则)、tagger 子 agent 逐题标注(107 批),全部为模型标签。
   `split_qp.py` 同时修了一处:续页顶端第一行的文字框略高于页码下沿时整行被丢,
   `9709_m21_qp_22` q6(b)、`9709_s21_qp_21` q7(c) 连同分值一起丢失;修正后全库 237 题的题干
   找回了文字。`9709_s26_ms_13` 三个站点的评分细则都解析不出,该卷只有 OCR 的 `ms_latex`。
   9709 的关键词标注表(`tag.py`)没有卷 2、卷 6,`tag_batches.py` 对这两卷直接用考纲的主题。

## 去除 PapaCambridge 水印(2026-10-02)

`pipeline/fetch/strip_watermark.py` 就地处理 `raw/pdf`、`raw/ms`、`data/papers` 中带水印的文件。
2026 年 3 月、6 月的 58 份试卷来自 papacambridge,每页叠有斜向水印、底部横幅和页面中央的浅色字样;
其中 52 份把原卷整页包在 `/R` 里,只保留这一层即得原卷;另 6 份(`9618_s26_qp_12`、`_41`、`_42`、`_43`,
`9709_s26_qp_12`、`_32`)是 papacambridge 重新排版的压缩版,没有斜向水印,只有叠在最后的浅色字样和横幅,
内容流用空格分隔运算符;脚本在叠加层开始的整页裁剪处截断。这 6 份最初被误判为无水印,旧题图带有浅色字样,
其中 `9709_s26_12_q02` 还多截了下一题的首行,已重裁。
fraft 上同名文件没有水印,但已被重新排到 Letter 纸上(字号缩小到 0.94 倍),字体也没有 Unicode 映射,
不能用来切题;两份评分细则(`9709_m26_ms_42`、`9709_s26_ms_13`)只供阅读,改用 fraft 版。
处理前的原文件在 `raw/papacambridge_orig/`。之后对这 58 份试卷重跑 `recrop.py` 与 `recrop.py --rows`。

