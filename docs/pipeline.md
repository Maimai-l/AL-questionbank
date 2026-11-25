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

## CAIE 长题线(9709 / 9231 / 9618 / 9702)

按必须的执行顺序排列:

```
1  下载      pipeline/fetch/fetch_any.py        通用下载器(9231 用 --url-template 指向 papacambridge,见 network.md)
            pipeline/fetch/fetch_fraft.py      按 cie.fraft.cn 的文件清单补下库中没有的试卷及其评分细则
2  切分      pipeline/split/split_qp.py         试卷 → 一题一条记录
            pipeline/split/split_ms.py         评分细则 → 按题号切开(需 pdftotext)
3  裁图      pipeline/split/crop.py             按 bbox 渲染 PNG
            pipeline/fetch/fix_names.py        修正裁图文件名引用
4  转写      pipeline/ocr/ocr.py                题干 → LaTeX(PaddleOCR-VL);插图写成 [DIAGRAM],--figures DIR 时另存插图并在原位写 <img>
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
            pipeline/text/fix_batches.py       子 agent 对照原图重写题干与评分细则(图示写成文字),写入 text_fixes.jsonl 并重放;
                                               --focus diagrams 只复核图示描述,--focus errata 加 --notes 更正原卷本身的错误
            pipeline/split/ms_total_from_ocr.py 只有 OCR 细则的题(35 题)从 ms_latex 读小计,写 ms_total / totals_agree
10 大纲标签  pipeline/tags/syllabus.py          大纲 PDF → syllabus.json
            pipeline/tags/topic_model.py       用大纲原文给主题打分
            pipeline/tags/eval_tags.py         新旧标签器对比(只报告)
            pipeline/tags/retag.py             合成标签并写回
            pipeline/tags/tag_batches.py       tagger 子 agent 按小问复核(plan / apply / write),见 tagging-plan.md
            pipeline/tags/prereq.py            先修关系 → prereq.json
11 详解      pipeline/explain/explain_batches.py explainer 子 agent 按小问写详解(plan / apply / write),写 explanation
            pipeline/explain/term_tree.py      关键术语:统计决定收录、级别、上下级与易混,termwriter 子 agent 按细则原文改写定义与区别 → exports/<科目>_terms/(Obsidian 仓库)
            pipeline/explain/concepts.py       9618 每章概念清单:子 agent 按教材与术语统计每章挑 8–20 个,一句话英文定义(plan / check)→ raw/concepts_9618/out/
            pipeline/explain/concept_pages.py  9618 每章复习页:子 agent 以第 1 章为范本写页面(plan / check --render / build),外壳在 assets/concepts/ → data/concepts/9618/
            pipeline/explain/glossary.py       9618 卷 2 词汇:卷 2 题目与评分细则里答题必须知道含义、字面看不出意思的术语(清单 glossary_p2.json,人工挑选,原句逐条核对)→ data/concepts/9618/glossary.html
12 出页面    pipeline/export/build_site.py      data.js、textbooks.js 与页面 → data/

精选题(教材练习题,syllabus WPH,带 tags)另走 pipeline/books/book_questions.py,见「精选题:Hodder Edexcel A Level Physics 1」。
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
- `fix_batches.py apply --write` 在 `apply_ms_fixes.py` 之后、`split_parts.py` 之前运行。9618 的评分细则每个小问一块:
  首行以小问标签开头,块内逐行写评分点、表格与代码,最后一行末尾是 `  |  分值`(`manager/bank.scheme_rows` 按此解析)。
- `drop_partial_ms_ocr.py` 在 OCR 评分细则合并(`merge_ms_ocr.py`)之后、`split_parts.py`
  之前运行,否则小问拿到的是被截断的细则。
- `explain_batches.py plan` 读 `part_data`,须在 `split_parts.py` 之后;小问标签变化后,
  已写入的详解在 `apply` 时会因标签不符被拒收,需要重做。9618 卷 1–3 已完成
  (2026-09,874 题,Sonnet);卷 4 未做。
- `build_site.py` 必须最后运行,否则页面读到的是旧数据。

## 入学考(已归档)

TMUA、TSA、BMAT 于 2026-11-14 从题库移出(用户决定不再使用)。1888 题的数据库行、题图(`img_adm/`、`img_tara/`)、
原卷(`papers/bank/`)与刷题页在 `archive-admissions` 分支，恢复方法见该分支的 README.md;
流水线脚本在 `attic/admissions/`,原来这里的两节说明移到 `attic/admissions/pipeline.md`。
选择题的通用支持(`answer`、`qtype='mcq'`、`options` 列，做题页与刷题页的选项判分)保留，供 9702 卷 1 使用。

## 教材线

```bash
python3 -m pipeline.ocr.ocr_books "<教材 PDF 目录>" "<页面输出目录>"
python3 -m pipeline.books.split_chapters "<x.pdf>" "<页面输出目录>/<书>" data/books/9709_p23 --prefix 9709_p23
python3 -m pipeline.books.chapters index data/caie.db data/books/9709_p23 --syllabus 9709 --components 2,3
python3 -m pipeline.books.chapters coverage
```

`--components` 不能省略:"Integration" 在 P1 是 1.8,在 P2 是 2.5,在 P3 是 3.5,
仅凭章节正文无法区分。

超过 100 页的书用 `pipeline/books/ocr_book_pages.py`(分段提交、按 PDF 页码命名、插图加页码前缀),见
「Edexcel 物理教材(2026-11)」。

`ocr_books.py` 会输出 `_raw.jsonl`(接口原始返回),应当保留:重新落盘时可以免费
从它重建。接口的一行 JSONL 包含多页,必须从 `layoutParsingResults` 中逐页取出,
按行写文件会只留下每组的最后一页。

## 导出分发包(pipeline/export/)

| 脚本 | 产出(写入项目文件夹旁的 `exports/`,与 `qb-work/` 并列,不跟踪;`CAIE_EXPORTS` 可改位置) |
|---|---|
| `build_site.py` | `data/` 下的 data.js、textbooks.js 与页面 |
| `export_web.py` | `data/data.js`,可单独运行 |
| `export_textbooks.py` | `data/textbooks.js`,可单独运行 |
| `export_all_chapters.py` | 每章一个 ZIP,放在 `exports/chapters/<考试>/`(9231、9618、9709 三个文件夹),文件名为 `<教材>_<两位章号>_<标题>.zip`,例如 `9709/9709_p1_09_Integration.zip`;旧版按教材分散存放的同一章文件在写新文件后删除。含章节正文、同主题真题、题图与评分细则;只有部分小问属于本章的题,只给这些小问及其评分细则(`part_data`)。教材插图中的 JPEG 以质量 75 重新压缩(更小时才替换,文件名不变)。数据管理页批量生成的「章节包」节点用同一函数 `write_chapter()` 写同样的 ZIP。`--syllabus`、`--chapter` 限定范围,`--no-images` 不含任何图片,文件名以 `_no_images` 结尾 |
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

## 新增 9702 物理(2026-11-14)

只收卷 1(选择题，40 分)、卷 2(AS 结构题，60 分)、卷 4(A Level 结构题，100 分)、卷 5(实验设计与数据分析，30 分),
不收卷 3 实验操作卷(用户决定)。2021–2026 年 168 份试卷、2482 题;未用子 agent。

```bash
python3 pipeline/tags/syllabus.py <664565-2025-2027-syllabus.pdf>    # 只追加 9702,其他科目保留
python3 pipeline/fetch/fetch_fraft.py 9702 --papers 1 2 4 5 --years 2021-2026
python3 pipeline/fetch/strip_watermark.py raw/pdf raw/ms
python3 pipeline/db/add_papers.py add --write && python3 pipeline/db/add_papers.py finish --write
python3 pipeline/tags/physics_topics.py --write                       # 需要 chapters 表里的 9702 教材
python3 pipeline/text/split_parts.py --syllabus 9702 --write
cp raw/pdf/9702_*.pdf raw/ms/9702_*.pdf data/papers/
```

1. **考纲。** `syllabus.py` 新增 `parse_9702`:节标题("1 Physical quantities and units")与小节标题("1.1 Physical
   quantities")都是粗体，学习目标用细体编号，跨行时编号在两行之间，按距离归到最近的编号。76 个小节、300 条学习目标，
   第 1–11 节为 AS,12–25 节为 A Level。`topic_model.PAPER_SECTIONS` 加 9702:卷 1、2 用 1–11 节，卷 4 用 12–25 节。
2. **来源。** fraft 上的 9702 全部被重排到 Letter 纸上，脚本全部改用 papacambridge。其中 49 份是已知的水印格式;
   2026 年的 19 份评分细则和 5 份卷 1 是新格式：叠加层画浅色斜向 "PapaCambridge" 轮廓、页脚
   "9702/22 Mark Scheme June 2026"、隐形的 "Trace ID: PC-…" 与 "Re-uploading, mirroring … traceable",
   页面框写成 `0 0 595 842`(评分细则横向为 `0 0 841.92 595.32`),旧规则只认 `595.27 841.89`,没有截掉叠加层。
   `strip_watermark.py` 已放宽页面框的写法，并把这几种文字加入检查。处理后 335 份文件的全部对象中无站点名与追踪文字。
   `9702_s26_ms_21` 三个站点都没有。
3. **切分。** `split_qp.py` 不用改：卷 2、4、5 的题号、分值与总分全部正确;卷 1 每题记 1 分。
   `split_ms.py` 对 9702 另用一套规则(其他科目 526 份评分细则的解析结果逐字节不变):表头 "Mark" 为单数;
   评分代码含 C1(补偿分);没有小问小计，以评分代码合计为细则总分;卷 5 每个得分点旁写 1,按行相加;
   2026 年多了 Guidance 列，说明文字也会以 "C1 …" 开头，所以先按每张表求出评分代码所在的列，只认该列上的代码;
   答题行写成 `答案  |  代码  |  说明`(`lib/scheme.py` 的格式),页面与逐项打分可以直接用;卷 1 读出答案字母。
   结果:2477 题有评分细则,2475 题分值与题面一致(不一致的是 `9702_m26_22_q05`、`9702_s26_42_q10`)。
4. **入库。** `add_papers.py` 支持 9702:卷 1 写 `answer`、`qtype='mcq'`、`options`;`finish` 对新行用
   `clean_encoding.clean` 还原 Symbol 字体的私用区字符(λ、×、Δ);没有 OCR 时 9702 题干评为 partial
   (文本层的上下标与分式被压平，页面提示以原题图为准),卷 1 有答案的细则评为 ok。物理卷的答题区在每问之下、
   以 "答案 = …… [分值]" 结束，这一行属于题目，所以题图已含答题区,`img9702_ans` 只有卷 5 的 42 张。
5. **主题。** 只用考纲原文打分(`topic_model.py`)时，人工判定的 100 题中 70 题节号正确(例如 "density" 也出现在第 9 节)。
   `physics_topics.py` 用教材各章正文加考纲原文做 TF-IDF 余弦相似度，再加 `terms_9702.py` 的各节术语，节号正确 86 题
   (另取的 40 题新样本上 34 题，原方法 26 题)。卷 5 的候选不含第 1 节(实验设计题总在谈不确定度与测量)。
   小节取考纲模型在该节内的最高分。`retag.py` 跳过 9702。
6. **教材。** 物理教材(Crundell & Goodwin,第 3 版)由子 agent 处理:PDF 自带文字层，新脚本 `pipeline/books/text_layer.py`
   按字体、字号与基线读出，上下标转 LaTeX、叠排分式按分数线重建为 `\frac`;按书签切成 26 章,`chapters.py index
   --syllabus 9702 --components 2,4` 映射到第 1–25 节。已知不足：根号是画出来的，读不到;并排的两张表会合成一张。
   第 26 章 Practical work 在考纲里没有对应节，主题置空(重新 index 后要再置空一次)。
   `chapters.py` 对按节标注的科目(`topic_model.PAPER_SECTIONS` 里的 9618、9702)统一按节存主题;
   覆盖率只有 9702 按整节的学习目标计算,9618 仍按小节。

7. **OCR(同日补做)。** PaddleOCR-VL 的 token 已内置在 `pipeline/ocr/*.py`(环境变量 `PADDLE_TOKEN` 可覆盖)。
   - 题干：逐张提交时服务端排队，每分钟只有约 3 张;`ocr.py --pack 10` 把 10 张题图合成一个 PDF 提交，每分钟约 50 张，
     48 分钟读完 2482 张。合包时模型偶尔漏掉一段(常是开头的 (a) 或图后的问句与选项),所以
     `apply_reocr.py --check-text` 用文本层核对：小问标号序列必须一致，选择题必须有选项字母与问句;
     不通过的题用 `ocr.py`(不合包)单张重读，经 `--second` 再核对一次。两次读法相同而缺选项字母的选择题
     (选项画在图里)也采用。结果 2363 题写入 `question_latex`(q_quality ok),117 题仍用文本层(partial)。
   - 评分细则：卷 2、4、5 的 125 份整份 OCR(`ocr_ms.py`),`parse_ms_ocr.py` 对 9702 只认表头为 Question … Answer
     的表(前面通用评分说明的编号表会被当成第 7 题)。`merge_ms_ocr.py` 对 9702 只在评分代码合计等于题面分值时
     写入 `ms_latex`:797 题中 750 题写入，其余保留文本层版本。
   - `split_parts.py --syllabus 9702` 重跑后，题干按小问切开 99.9%,小问有评分细则片段 99.0%。
   - `check_latex.py`:23 题仍有 KaTeX 无法渲染的公式(细则 18 题、题干 5 题),多为 OCR 读错的
     `\frac{{1}/{2}…}` 一类，需要对照原页更正(`latex_fix_batches.py`)。

```bash
python3 pipeline/ocr/ocr.py raw/new_papers/questions.json data/img9702 raw/ocr/q_9702.jsonl 4 --pack 10
python3 pipeline/ocr/apply_reocr.py raw/ocr/q_9702.jsonl --check-text --failed failed.txt
#   failed.txt 中的题：ocr.py 不加 --pack,写入 raw/ocr/q_9702_single.jsonl
python3 pipeline/ocr/apply_reocr.py raw/ocr/q_9702.jsonl --check-text --second raw/ocr/q_9702_single.jsonl --write
python3 pipeline/ocr/ocr_ms.py raw/ms_ocr_9702 raw/ocr/ms_9702.jsonl 2        # 卷 2/4/5 细则的链接目录
python3 pipeline/ocr/parse_ms_ocr.py raw/ocr/ms_9702.jsonl raw/ocr/ms_9702_parsed.json
python3 pipeline/ocr/merge_ms_ocr.py raw/ocr/ms_9702_parsed.json data/caie.db
python3 pipeline/text/split_parts.py --syllabus 9702 --write
```

8. **旧考纲。** 2021 年的卷子按 2019–2021 考纲命题,A Level 部分还有通信(调幅、模拟与数字传输)和电子学(运算放大器)。
   卷 4 中这 14 题在现行考纲里没有对应节，主题置空,`topic_note` 注明。

教材线的文字层路线:

```bash
python3 -m pipeline.books.text_layer chapters <pdf> <chapters.json>
python3 -m pipeline.books.text_layer pages <pdf> <页面目录> --from 17 --to 451
python3 -m pipeline.books.split_chapters <pdf> <页面目录> data/books/9702 --prefix 9702 --table <chapters.json>
python3 -m pipeline.books.chapters index data/caie.db data/books/9702 --syllabus 9702 --components 2,4
```

## Edexcel 物理教材(2026-11)

Pearson Edexcel International A Level Physics(IAL,规格 WPH)Student Book 1、2(Miles Hudson),用户考 IAL。
题库里没有 Edexcel 的考纲和试卷，这次只加教材：教材页、chapters 表与 `qbank.py chapter` 可用，主题等考纲字段为空。

| 书 id | 来源 | PDF | 章 | OCR 页 |
|---|---|---|---|---|
| `edx_ial_phy1` | https://github.com/Maimai-l/blender-workspace/releases/download/temp-blobs/edexcel-international-a-level-physics-student-book-.pdf.zip 中的 `edexcel-international-a-level-physics-student-book-.pdf` | 225 页，扫描件 | 14 | PDF 13–215 |
| `edx_ial_phy2` | https://github.com/Maimai-l/blender-workspace/releases/download/temp-blobs/physics2.zip 中的 `268-edexcel-international-a-level-physics-student-book-2-in-pdf.pdf` | 237 页，扫描件 | 15 | PDF 12–227 |

两本都没有文字层，书签无用(Book 2 是逐页的 "combined-001",Book 1 是 xhtml 文件名),章节按目录页(Book 1 第 4–6 页、
Book 2 第 3–5 页)手工写成 `pipeline/books/tables/<书>.json`。章按书内 Topic 下的章划分(1A、1B…、5A、5B…),
章号从 1 连续编;Book 1 另有「Working as a physicist」(第 1 章，单位与估算)。两本的「Maths skills」各为一章,
「Preparing for your exams」连同其后的「Sample exam answers」为最后一章。不作为章节的有 Course structure、About this book、
Practical skills、Assessment overview 等前言页，以及 Command words、Glossary、Index。Topic 的扉页并入该 Topic 第一章。
书内页码 = PDF 页码 − 11(Book 1)、− 10(Book 2),用 OCR 结果中标为 `number` 的页码块逐页核对(Book 1 有 94 页、
Book 2 有 107 页印着页码),全部一致。

```bash
cp <Book 1>.pdf raw/textbooks/edx_ial_phy1.pdf          # paths.TEXTBOOKS;数据管理页的章节 PDF 也从这里切
cp <Book 2>.pdf raw/textbooks/edx_ial_phy2.pdf
H1='^(\d{1,2}[A-D] )?[1-9] [A-Z][^.]*$'; H2='^(\d{1,2}[A-D] )?(THINKING BIGGER|EXAM PRACTICE)$'
python3 -I pipeline/books/ocr_book_pages.py ocr raw/textbooks/edx_ial_phy1.pdf edx_ial_phy1 --from 13 --to 215 --chunk 68 --keep-header "$H1" --keep-header "$H2"
python3 -I pipeline/books/ocr_book_pages.py ocr raw/textbooks/edx_ial_phy2.pdf edx_ial_phy2 --from 12 --to 227 --chunk 72 --keep-header "$H1" --keep-header "$H2"
for b in edx_ial_phy1 edx_ial_phy2; do
  python3 -I pipeline/books/split_chapters.py raw/textbooks/$b.pdf raw/book_ocr/$b/pages data/books/$b --prefix $b --table pipeline/books/tables/$b.json
  python3 pipeline/books/chapters.py index data/caie.db data/books/$b --syllabus WPH --no-topics
done
python3 pipeline/export/build_site.py
```

(`python3 -I -m pipeline.…` 找不到模块:`-I` 不把当前目录放进 `sys.path`,所以用脚本路径。)

1. **OCR 脚本。** `ocr_books.py` 把整本 PDF 作为一个任务提交，超过 100 页的上限;插图又按页内方框命名
   (`img_in_image_box_75_120_320_313.jpg`),不同页同一位置的图会互相覆盖。新脚本 `pipeline/books/ocr_book_pages.py`
   沿用 `ocr_books.py` 的提交、轮询、下载与插图函数，把页码范围切成不超过 `--chunk` 页的子 PDF 各自提交，
   每份接口原始返回存为 `raw/book_ocr/<书>/parts/<书>_pNNNN-NNNN/_raw.jsonl`;页文件按 PDF 页码命名
   (`pages/page_0084.md`),插图改名为 `imgs/p0084_<原名>` 并同步改写 Markdown。`pages` 子命令只从 `_raw.jsonl`
   重建，不再调用接口。共 419 页、6 个任务:Book 2 216 页 9.5 分钟，Book 1 203 页 14.5 分钟，另各约 1 分钟下载插图
   (343 张、415 张)。耗时主要在上传:30–37 MB 的子 PDF 上传要 1–7 分钟，识别每 70 页只要 1.3–3 分钟。
   先试读了 Book 2 第 14–16 页，公式、上下标与矢量粗体都读成了 LaTeX,质量够用后再整本提交。
2. **页眉。** 页眉、页脚与页码被模型标为 `header`/`footer`/`number`,不进 Markdown,所以不用另去。但每节开头的色带
   ("5A 1 ENERGY IN COLLISIONS"、"2 CENTRIPETAL FORCE"、"6A THINKING BIGGER")有时也被标为 `header`,节标题随之丢失。
   `--keep-header` 把匹配的 `header` 块放回页首作 `## …`;两条规则只认「章号 + 一位节号 + 标题」与
   「章号 + THINKING BIGGER/EXAM PRACTICE」,不认带点的眉题("5A.1 ENERGY IN COLLISIONS")与带页码的眉题
   ("104 3B.1 …");相邻两页相同的只保留第一次。规则存在 `raw/book_ocr/<书>/_book.json`,重跑 `pages` 时沿用。
3. **水印。** 两本没有逐页水印;Book 2 封面的 "PDF COMPILED BY SAAD" 不在章节范围内。`--strip REGEX` 留给有逐页
   网址水印的书用(正文里 Thinking Bigger 引文的出处网址是原书内容，保留)。
4. **入库。** `chapters.py index` 新增 `--no-topics`:不加载考纲模型,topic、subtopic、覆盖率等字段置空，只记标题、
   页码与词数;`chapters.id` 为 `WPH_edx_ial_phy1_ch01` 这样。`export_textbooks.py` 把 `edx_ial_phy<N>` 显示为
   "Edexcel International A Level Physics (WPH) Book <N>",教材页的下拉框在书名已含 "(WPH)" 时不再加 "WPH · " 前缀
   (CAIE 各书不变)。`manager/flow.py` 的 `BOOKS` 加了这两本，数据管理页的「教材」节点可以选。
5. **抽查。** 每本 3 页对照原页(Book 1:1A.6 运动学公式、2B.2 应力应变、4B.3 分压电路;Book 2:6B.3 电容放电、
   9A.2 半衰期、11B.2 恒星分类表),正文、公式与表格都对得上;各章首页与末页(Exam practice)与目录一致。
   已知的识别问题：个别斜体粗体字母读错(1A.6 的 $v=s/t$ 读成大写 $V=S/t$,加速度 a 读成 α);粗体关键词偶尔被读成下标
   (`{}_{strain}`);"1A" 偶尔读成 "IA";侧栏(Exam hint)的标题与正文顺序会被正文隔开;Exam practice 中的
   "(Total for Question N = 1 mark)" 与 Thinking Bigger 引文出处有几处被标为页脚而丢失;教材页渲染 KaTeX 约 2750 处，
   8 处出错(Book 1 两处、Book 2 六处)。插图 758 张中 29 张没有被 Markdown 引用(被并进了更大的图框),随目录一并复制。
6. **章节包。** `export_all_chapters.py` 与 `manage.py auto` 会为 WPH 各章也写 ZIP(`exports/chapters/WPH/`),
   因为没有主题，包里只有章节正文和插图，没有真题。

7. **校对(2026-11-18)。** `pipeline/books/proof_batches.py` 取章节中有公式的页(304 页;`--all-pages` 取全部 419 页)渲染原页，
   每批 20 页交给 Haiku 子 agent,只交回逐处的 `old → new`;`verify` 要求 `old` 在页内唯一、不动插图、不新增 KaTeX 错误;
   `apply --write` 记入 `pipeline/books/book_fixes.jsonl` 并重放到章节文件(重新切章后再跑一次即可)。16 批分两个用量窗口跑完，
   实测每页约 3.2 万输入 token 当量(输入 1、写缓存 1.25、读缓存 0.1、输出 5),共约 900 万。改正 304 条，另手工 6 条
   (`\,^{\circ}` 缺底数 3 处、美元金额的 `$` 被当成公式定界符 2 处、多余的 `}` 1 处),教材页 KaTeX 报错从 8 处降为 0。
   主要改正：速度 v 读成 ν 或 V、加速度 a 读成 α、中微子 ν 读成 v、反粒子的横线、核对用的 ✓ 读成 ↙、Exam practice 缺的分值 [n]、
   重复的句子与多出的竖式。抽查 12 处，撤掉 1 处(第 225 页 agent 在看不清时把 "that" 猜成 "that that")。
   子 agent 会照 CLAUDE.md 的会话约定运行 `sync.py pull`,批次说明里已写明不要运行 `sync.py` 与 git。

## 精选题:Hodder Edexcel A Level Physics 1(2026-11)

Edexcel A Level Physics Student Book 1(Hodder,Mike Benn、Graham George,2015,英国本土 9PH0 Year 1)每章末的
「Exam practice questions」与「Stretch and challenge」作为精选题收进题库(syllabus `WPH`,用户考 Edexcel IAL;WPH 的考纲与
真题以后另加)。书中没有答案。来源:https://github.com/Maimai-l/blender-workspace/releases/download/temp-blobs/as1.Edexcel.A.Level.Physics.Student.pdf
(814 页 US Letter 电子书排版，有文字层，书签给出 19 章的起始页)。

```bash
cp <as1.pdf> raw/textbooks/hodder_edx_al1.pdf                      # paths.TEXTBOOKS
python3 -I pipeline/books/book_questions.py extract raw/textbooks/hodder_edx_al1.pdf --book hodder_edx_al1
python3 pipeline/books/book_questions.py add --write                 # 先备份 data/caie.db;同一本书的旧行整体替换
python3 -c "import json; d=json.load(open('raw/book_questions/hodder_edx_al1/questions.json'))['questions']; \
  json.dump([{'image': r['image'].split('/')[1]} for r in d], open('raw/book_questions/hodder_edx_al1/ocr_input.json', 'w'))"
python3 pipeline/ocr/ocr.py raw/book_questions/hodder_edx_al1/ocr_input.json data/imgWPH raw/ocr/q_WPH_hb1_fig.jsonl 4 --pack 10 \
  --figures data/imgWPH/fig                                          # 插图存 data/imgWPH/fig/<题号>_<序号>.jpg
python3 pipeline/books/book_questions.py marks raw/ocr/q_WPH_hb1_fig.jsonl --out raw/ocr/q_WPH_hb1_fig_marked.jsonl
python3 pipeline/ocr/apply_reocr.py raw/ocr/q_WPH_hb1_fig_marked.jsonl --syllabus WPH --check-text --write
python3 pipeline/books/book_questions.py fixes raw/ocr/q_WPH_hb1_fig_marked.jsonl pipeline/books/hodder_edx_al1_ocr_fixes.jsonl \
  --out raw/ocr/q_WPH_hb1_fig_fixed.jsonl                           # --check-text 拒收、对照题图后认可或改正的题
python3 pipeline/ocr/apply_reocr.py raw/ocr/q_WPH_hb1_fig_fixed.jsonl --syllabus WPH --write
python3 pipeline/text/split_parts.py --syllabus WPH --write
python3 pipeline/export/build_site.py
```

| 章 | Exam practice | Stretch and challenge | 章 | Exam practice | Stretch and challenge |
|---|---:|---|---|---:|---|
| 1 Quantities and units | 1–8 | 无 | 10 Resistance and resistivity | 1–11 | 12 |
| 3 Rectilinear motion | 1–15 | 16 | 11 Internal resistance … potential divider | 1–13 | 14、15、16 |
| 4 Momentum | 1–19 | 20 | 12 Fluids | 1–10 | 11 |
| 5 Forces | 1–14 | 15 | 13 Solid materials | 1–10 | 11 |
| 6 Work, energy and power | 1–14 | 15 | 14 Nature of waves | 1–11 | 12 |
| 7 Charge and current | 1–9 | 10 | 15 Transmission and reflection of waves | 1–16 | 17 |
| 8 Potential difference, e.m.f. and power | 1–15 | 16 | 16 Superposition of waves | 1–15 | 16 |
| 9 Current–potential difference relationships | 1–9 | 10 | 17 Particle nature of light | 1–13 | 14、15 |

共 202 + 18 = 220 题，各章题号连续、无跳号。第 2 章(Practical skills)、第 18 章(Maths in physics)、第 19 章
(Preparing for the exams,其中是带评语的样卷答案)没有这两节。Stretch and challenge 共 15 节 18 题(第 11 章 3 题、第 17 章 2 题)。

1. **题号与字段。** id 为 `WPH_hb1_ch<章>_q<题号>`。书中 Stretch and challenge 的题号本来就接在该章 Exam practice 之后
   (第 3 章是 1–15 与 16),所以直接用书上的题号，不另加 `_s`。`component` 为章号(`"3"`),`component_name` 为章名;
   试卷字段照 CAIE 的格式填，让现有代码不必区分：`paper` 为 `WPH/<章>`(科目/卷号 + 空变体，练习工作台的题墙按
   `paper|series` 找格子),`variant` 为空，`series` 为 `hb1`,`session` 为书名,`year` 为出版年 2015,`month` 为 0,
   `q` 为书上的题号,`qp_pdf` 为 `hodder_edx_al1.pdf`,`qp_pages` 为题图用到的页(从 0 起)。`topic` 为空,
   `topic_note` 为「按教材章节分组;WPH 考纲加入后再定主题」。`ms_text`、`ms_latex` 为空,`ms_quality='missing'`。
   `qb.py stats`、`qb.py find --tag`、刷题页、练习工作台、数据管理页(查询、题组、导出、练习卷、批量生成)、`build_site.py`
   都用这批数据跑过;`export_all_chapters.py` 按主题配题，精选题没有主题，不进章节包。
2. **切题。** 按书签分章，在章内找字号大于 16 的「Exam practice questions」「Stretch and challenge」标题;题目从左边距的
   粗体题号开始(必须按 1、2、3… 连续),到它最后一个「[Total n Marks]」为止。电子书把图表常排在 [Total] 之后，所以 [Total]
   与下一题之间的内容默认归前一题;写明题号的句子(「Use Figure 9.17 to answer Questions 4 and 5」「This information is
   for use in Questions 1 and 5」「Questions 2–4: …」)连同其后的材料归它点名的题;句子跨行时从句首算起。三处图在
   [Total] 之后、却属于前面几题，写在脚本的 `shared` 里(9.16 → 第 9 章 1–3 题，9.17 → 4–5 题，10.17 → 第 10 章 1–3 题)。
   题干引用章节正文里的图时，把那张图拼在题后(`extra`:10.6、10.1b、11.10、11.43)。
3. **题图。** 与 9702 相同:150 dpi、16 级灰度(`lib/png16.py`),横向固定裁 66–546 pt(正文栏 72–540),每页一段按
   内容上下界加 4 pt,跨页的上下拼接，不同来源(共用材料、本题、正文插图)之间留 12 pt 空白。存为 `data/imgWPH/<id>.png`,
   220 张、6.5 MB,宽 1001 px。整题题图照旧保留;题干里的插图另存(见下一条)。`has_diagram` 按 OCR 切出的插图判定:
   71 题有插图(入库时先按题内 50×120 pt 以上的位图粗判为 73 题,OCR 写回后以插图为准;差的 2 题是第 10 章第 7 题的数据表
   与第 13 章第 11 题的电子表格，都是表格图片，被读成了表格)。
4. **题干。** `question_text` 为文字层，一行一行，上标写成 `^`(`m s^−1`),粗体选项字母与正文之间补空格。
   `question_latex` 用 PaddleOCR,保留插图:`ocr.py` 新增 `--figures DIR`(不加时照旧，插图写成 `[DIAGRAM]`,CAIE 四科不变),
   像 `ocr_books.py` / `ocr_book_pages.py` 那样下载接口返回的 `markdown.images`(版面检测切出的插图),按阅读顺序存为
   `DIR/<题号>_<序号>.jpg`,并把 markdown 里原位置的 `<img src>` 改成相对 data/ 的路径(`<img src="imgWPH/fig/WPH_hb1_ch03_q11_01.jpg" …>`,
   与教材 markdown 的写法一致);缓存行的 `has_diagram` 为是否存下了插图,`figures` 列出这些文件。`apply_reocr.py` 的规整
   去掉外层 `<div>`,`<img>` 单独成行。102 张插图、71 题、2.4 MB。刷题页的文字版、数据管理页的「题干文字」显示这些图
   (相对 data/,数据管理页经 `/q/` 取);导出时数据管理页把题干里的插图放进 ZIP(每题文件夹的 `fig/`,平铺时 `<文件名>_fig/`)
   并改写链接，章节包(`export_all_chapters.py`,经 `question_md.figures/relink`)放进 `images/questions/`。
   第一次 OCR 没有保留插图(`raw/ocr/q_WPH_hb1.jsonl`,22 个任务 6.5 分钟，其中一个任务服务端 500,重跑 0.4 分钟;10 张单张重读
   1.7 分钟);保留插图重读一遍用了 3.8 分钟(22 个任务，无错误)。共提交 460 张题图。OCR 把右对齐的 [n] 与 [Total n Marks]
   当页面装饰丢掉(163 题少了分值),
   `book_questions.py marks` 按文字层把它们放回：分值放在 OCR 文本中「文字层里分值前一行」所在段落之后(按字母数字比对，
   去掉 LaTeX 命令),放回后 218 题的分值序列与文字层一致，余下 2 题是计数误判(`\sqrt[4]{…}` 与文字层丢了「[」)。
   `apply_reocr.py` 新增 `--syllabus`(只处理该科、只重建该科的全文索引行，不碰 CAIE)、`--keep-diagram`(不改 has_diagram;
   这本书最后没有用),并把书里的裸标号 `a)`、`ii)` 当作 `(a)`、`(ii)` 比对。`--check-text` 拒收 10 题(两次 OCR 都是这 10 题),
   逐题对照题图后记在 `pipeline/books/hodder_edx_al1_ocr_fixes.jsonl`(每行 `id`、`why`,改正的另有 `find`/`replace`;
   `book_questions.py fixes` 从 OCR 缓存取出这些题、套用改正，再不带 `--check-text` 写回;重新 OCR 后找不到 `find` 的会列出):
   6 题是选项写在 `$$\begin{aligned}…$$` 或 `\mathbf{}` 里、检查误报;第 6 章第 3 题书上选项印成 A、B、C、C(没有 D),照印;
   第 10 章第 7 题 OCR 读出了表格图片里的 (i)–(v),比文字层全;第 3 章第 14 题与第 12 章第 9 题把 iii) 读成 ii),已改;
   第 4 章第 2 题与第 8 章第 1 题评为 degraded(单位上标在公式外),改写成 `\mathrm{}`;另有 2 处 KaTeX 修正(`\,^{\circ}` 缺底数)。
   结果 220 题 `q_quality='ok'`,没有 `[DIAGRAM]`,`check_latex.py` 无报错。
5. **分值与小问。** `marks` 为各 [Total] 之和(第 1 章第 1 题 a–d 各一个 [Total 1 Mark],共 4 分);没有 [Total] 时为各 [n]
   之和。第 11 章第 16 题(Stretch and challenge)书上没有印分值,`marks` 为空。`parts` 为最低一级标号(与 `split_parts.py`
   一致,`7(a)`、`6(b)(ii)`;h) 之后的 i) 是小问 (i) 而不是罗马数字),`marks_parts` 为每个小问后面印的分值;书上几个小问
   合印一个分值时(如 `a) … b) … [Total 2 Marks]`、`(i)(ii) … [4]`),没印的记 `null`,印的那个记在最后一个小问上，非空值之和等于
   `marks`,45 题有 `null`。选择题:1 分、无小问、有 A–D 选项的 43 题，加上选项画在图里的 8 题(第 9 章 1–5、第 10 章 1–3),
   共 51 题 `qtype='mcq'`,`options` 为 `["A","B","C","D"]`,文字选项存在 `option_texts`(字母 → 文字),`answer` 为空。
   第 1 章第 1 题、第 3 章第 1 题、第 5 章第 1 与第 4 题、第 12 章第 1 题、第 13 章第 1 题由几道选择题组成((a)(b)…各 1 分),
   按结构题存(`qtype` 为空)。
6. **拆小问。** `split_parts.py` 对非 CAIE 科目先把行首的 `a)`、`ii)` 改写成 `(a)`、`(ii)` 再切(CAIE 不变),默认科目加了 WPH。
   220 题 576 个小问,219 题按小问切开;第 10 章第 7 题表格单元格里的 (i)–(v) 被当成小问标号，与分值对不上，只保留标号与分值。
7. **标签。** `questions.tags`:JSON 数组，默认 NULL,由 `lib/db.ensure_tags` 加列(`book_questions.py add` 调用;`build_db.py`
   的表结构也加了这一列),CAIE 各行仍为 NULL。读的一方用 `db.tags_column(con)`,没有这一列的旧库读作 NULL。这本书的题为
   `["精选", "Hodder Edexcel A Level Physics 1"]`。`data.js` 每题多一个 `tg`(只有带标签的题有);刷题页筛选栏有「标签」,
   选了全部没有评分细则的标签或科目时自动取消「只看有答案的」,没有评分细则的题写「本题没有评分细则(教材未附答案)」。
   练习工作台:`/api/filters` 带各科标签与题数,`/api/questions?tag=` 筛选，总览标题下有标签按钮;没有答案的选择题与
   没有评分细则的小问一律「填分」判分(`app/marking.py`)。数据管理页：查询页「标签」条件，批量生成的筛选字段「标签」
   (列表字段，「是」= 含有),题组、导出与练习卷可以放精选题;`qb.py find --tag 精选`。
8. **没有做的。** 题目之间的引用没有拼进题图:第 7 章第 5 题(引用第 1 题，共用数据已在图中)、第 8 章第 9 题(第 7 题)、
   第 11 题(第 10 题)、第 15 题(第 3 题的数据表)、第 9 章第 7 题(第 6 题)。题号前的彩色圆点(前言说练习题按难度分级)没有记录。

## 力学章节标签(CIE Mechanics 练习册，2026-11-23)

用户提供的「CIE Mechanics 练习册(学生版)」把 140 道 9709 卷 4 真题(2016–2020)与 5 道教材练习按 9 章编排(Velocity and
acceleration、Force and motion in one dimension、Forces in two dimensions、Friction、Connected particles、General motion in a
straight line、Momentum、Work and energy、The work-energy principle and power)。题库的卷 4 是 2021–2026 年，与练习册没有重合，
所以把这 9 章当作分类标准，给题库 292 道卷 4 题打标签(tags 列，如 `力学 5 Connected particles`,主章节在前，最多 3 个)。
考纲主题(4.1–4.5)不变。

```bash
cp <练习册>.pdf raw/textbooks/cie_mech_wb.pdf
python3 -I pipeline/books/ocr_book_pages.py ocr raw/textbooks/cie_mech_wb.pdf cie_mech_wb --from 3 --to 154 --chunk 80
python3 pipeline/tags/chapter_labels.py examples pipeline/tags/labels_mech.json cie_mech_wb   # 145 题，已知章节
python3 pipeline/tags/chapter_labels.py plan pipeline/tags/labels_mech.json --set test --out test1
python3 pipeline/tags/chapter_labels.py score pipeline/tags/labels_mech.json --out test1
python3 pipeline/tags/chapter_labels.py plan pipeline/tags/labels_mech.json --set bank --out bank1
python3 pipeline/tags/chapter_labels.py apply pipeline/tags/labels_mech.json --out bank1 --write
python3 pipeline/tags/chapter_labels.py apply pipeline/tags/labels_mech.json --saved --write   # 重建数据库后
```

1. **标签表** `pipeline/tags/labels_mech.json`:9 章各自的方法范围与目录页码。结果存在 `labels_mech_result.json`(提交)。
2. **切题。** 练习册的出处写在题末，章标题 OCR 不一定识别(第 5、8 章没识别出来);按「### N.」切题，题号回到 1 即换章，
   目录页码核对。第 2 章的 5 题出自教材 Chapter Review Exercise,只作示例。
3. **验证。** 2016–2017 年的题与教材练习作示例，2018–2020 年的 100 题让 Haiku 子 agent 分类，与练习册的章节比对：主章节对
   91 题，练习册章节在标签中 97 题。错得最多的是功与能的题判成摩擦(3 题),规则补上「能量方法归 8、功率与功能原理归 9」。
4. **题库。** 292 题 9 批(每批 35 题，题干上限 4000 字),共约 80 万 subagent token。与考纲主题交叉核对：4.1→3/4/5、
   4.2→1/6、4.3→7、4.4→2/4/5、4.5→8/9;不一致的 6 题逐题看过，改了 1 题(9709_m24_42_q03 用功率求摩擦系数，补上 9)。

## 练习册题入库与评分细则(2026-11-23)

```bash
python3 pipeline/books/workbook_questions.py --write             # 145 题：题图、OCR 题干与插图、标签
python3 skills/shared/get_paper.py <31 份 qp 与 ms> --out raw/mwb_papers
python3 pipeline/books/workbook_questions.py --schemes --write   # 按出处补评分细则与原卷分值
python3 pipeline/text/split_parts.py --syllabus 9709 --write
```

- 题图：练习册文字层里有题号行「1.」与出处行「(9709_s17_qp_41)」,从题号顶到出处底裁出，跨页拼接。
- 原卷题号：`split_qp.py` 切原卷，按共有词(Jaccard)找练习册题对应的题：最佳匹配相似度都在 0.68 以上，比第二名高 0.34 以上。
- 评分细则：2016–2020 年有三种版式(2016 年无表格;2017–18 年表头「Mark」单数、每小问以「Total: n」收尾;2019 年起与现行相同)。
  每题取三种读法(`split_ms.py`、`old_scheme`、`any_scheme`)中合计等于原卷分值的那一个，`split_ms.py` 本身没改。
- 小问：不写 parts、marks_parts,由 `split_parts.py` 按练习册题干自己的小问标签拆(写原卷的小问标签反而只拆开 58 题)。
- 刷题页：选标签时只要其中有题没有评分细则，就取消「只看有答案的」(「精选」里练习册题有评分细则,Hodder 题没有)。

## Kinematics 练习题(2026-11-25)

用户提供的三份 Edexcel IAL 物理 Kinematics 练习 PDF(`data/sources/WPH/kinematics/`,说明见该目录 README)作为精选题入库，
共 94 题，脚本 `pipeline/books/kinematics_questions.py`。三份都没有附评分细则，只有选择题有答案表。

```bash
python3 -I pipeline/books/kinematics_questions.py extract          # 题图 + raw/book_questions/kinematics/questions.json
python3 pipeline/ocr/ocr.py raw/book_questions/kinematics/ocr_input.json data/imgWPH raw/ocr/q_WPH_kin_fig.jsonl 4 \
  --pack 10 --figures data/imgWPH/fig
python3 pipeline/books/kinematics_questions.py marks               # 找回 OCR 丢掉的分值 -> raw/ocr/q_WPH_kin_fig_marked.jsonl
python3 pipeline/books/kinematics_questions.py add --write         # 先备份 data/caie.db;三份的旧行整体替换
python3 pipeline/text/split_parts.py --syllabus WPH --write
python3 pipeline/export/build_site.py
```

| series | 文件 | 题数 | 题号 | 分值 | 评分细则 |
|---|---|---:|---|---|---|
| kpmt | kinematics_pmt_questions.pdf(63 页扫描) | 31 | `WPH_kpmt_q01`–`q31`,Q1–Q31 齐全(Q11 在第 16 页，不缺) | 各 [n] 之和，共 256 分 | 无 |
| ktop | kinematics_pmt_qp.pdf(7 页) | 7 | `WPH_ktop_q01`–`q07` | Total,共 26 分 | 无 |
| kmcq | kinematics_mcq.pdf(6 页) | 56 | `WPH_kmcq_q01`–`q56` | 每题 1 分 | 答案表 |

1. **字段。** 一份一「卷」:`component` 与 `series` 都是 kpmt / ktop / kmcq,`paper` 为 `WPH/<series>`,
   `component_name` 与 `session` 为来源名(kmcq 的 session 带考季，如 `Kinematics 选择题 · Nov 2008`)。kmcq 的 `year`、`month`
   取题前的考季标题(May 02 → 2002 年 5 月，范围 2002–2010),kpmt、ktop 的 `year` 为提供年份 2026、`month` 0,`topic_note` 写明。
   `tags` 为 `["精选", "WPH Kinematics", <来源标签>]`,来源标签为「PMT Kinematics 真题汇编」「PMT IAL Questions by Topic: Kinematics」
   「Kinematics 选择题 2002–2010」。`topic` 为空。`qp_pdf` 为文件名(不在 data/papers,数据管理页不提供原卷)。
   约定「`paper` 等于 `<科目>/<series>`」即练习合集：`manager/bank.paper_code` 写作 `WPH/KMCQ`,练习工作台(`app/web/js/core.js`
   的 `isCollection`)写作 `WPH KMCQ`;刷题页的试卷下拉框对非数字的 component 只显示名称(不写「第 kpmt 章」)。
2. **切题。** kpmt:文字层只有「Qn.」与页码，题目是整页扫描图;从「Qn.」到下一个「Qn.」,按页取其间的图片上下界，跨页拼接，
   没有图片的第 59–63 页跳过。题目是剑桥 9702 卷 2 式结构题(题前印原卷题号，如「Q1.」下是「2 (a) (i)」),原卷没有认出
   (题库的 9702 只有 2021 年以后)。ktop:没有文字层(Print to PDF 把字转成了曲线),整份 7 页先 OCR 一次
   (`raw/book_ocr/kinematics/ktop_pages.jsonl`,32 秒),用版面框里的「Qn.」与「(Total for question = n mark)」定位;非末页的下界
   按渲染后的墨迹找(页脚 748 pt 以上)。kmcq:两栏，按文字层的题号「n.」(须按 1、2、3… 连续)、考季标题与「Answers」切，
   阅读顺序为左栏、右栏、下一页;题图按栏裁，题干 `question_text` 用文字层。题图 150 dpi、16 级灰度，共 94 张 3.4 MB。
3. **去重。** ktop 每题与 kpmt 各题按 OCR 文字的词集 Jaccard 比较，最高 0.18(阈值 0.5),没有重复;ktop 是 Edexcel IAL 题，
   kpmt 是剑桥式题，本来就不同。
4. **OCR。** 94 张题图 10 个任务 2.7 分钟，无错误;插图 142 张(2.7 MB,75 题 `has_diagram=1`)。写入时去掉题图顶上的「Qn.」/「## Q9」,
   `*(b)` 改作 `(b) *`(星号是 Edexcel 的书面表达题记号，不改则小问标号认不出),删掉 OCR 把答题虚线读成的
   `\begin{array}…\cdots…` 乱码，`\textsc{A}` 改 `\text{A}`(KaTeX 不支持)。94 题 `q_quality='ok'`,`check_latex.py` 无报错。
5. **分值(已知问题)。** OCR 把右对齐的 [n]、(n) 当页面装饰丢掉，这两份又没有文字层可补。ktop 从整页 OCR 的版面框取 (n)
   (7 处全在)。kpmt 的整页与右侧窄条 OCR 都只认出少数几个 [2](版面模型把孤立的小方括号当图片或不检测);最后用
   `bracket_boxes` 在题图右半部按笔画找方括号(13–34 px 高的竖笔，一侧上下有衬线、中间空),每个候选框放大三倍、一页一个、
   **关掉版面检测**(`useLayoutDetection: false`)读字，读成「[n]」的算分值:301 个候选读出 130 个分值(约 4 分钟，一次服务端 500
   重跑后成功;单个任务超过 100 页时 `ocr_job` 按 100 页分批)。每个分值归它上方最近的小问标号(标号高度取自题图再 OCR 一次的
   版面框),几个小问合印一个分值时前面的记 `null`(与 Hodder 题相同)。29 题拆出小问，30、31 题 OCR 文字的小问标号与版面框不一致，
   不拆(整题一个小问)。kpmt 的分值没有原卷可对，对照题图抽查第 1、2、7、22 题，分值与小问归属都对;漏认的方括号会让总分偏小。
   分值放回题干文字用 `book_questions.restore_marks`,有 10 处找不到锚点没放回(分值仍计入 marks)。
6. **选择题。** kmcq 56 题 `qtype='mcq'`,`options` 为 A–D,`answer` 取文末答案表(56 题全有，与答案表逐题核对一致);评分细则照
   9702 卷 1 的存法:`ms_text` 为 `<题号>  <答案>  |  1`,`mark_codes='[]'`,`ms_total=1`,`totals_agree=1`,`ms_quality='ok'`,
   `ms_pdf` 为 kinematics_mcq.pdf。部分选项画在图里(如第 2 题四张图),题干文字里只有图。练习工作台按答案判对错
   (`app/marking.py` 原来只给 9702 补选项字母，现在凡有 `options` 的都补);刷题页点字母即判。ktop 的 4 道选择题
   (Q1、2、5、6)没有答案，与 Hodder 的选择题一样 `answer` 为空、填分。
7. **小问。** `split_parts.py --syllabus WPH`:WPH 314 题 757 个小问，按小问切开 313 题。

## 子 agent 批次大小实验(2026-11-14)

问题：审校批次每批放几题最省钱、质量又不下降。做法：同一组 40 道 9702 题(卷 2、4、5,含 4 处已核实的错误)
用 `fix_batches.py plan --size N` 分别切成每批 5、10、20、40 题，每批交给一个 Haiku 子 agent(general-purpose),
按各 agent 记录里的用量计费。费用折算成输入 token 当量：输入 1,写缓存 1.25,读缓存 0.1,输出 5。

| 每批题数 | 批数 | 读缓存合计 | 每题费用(输入当量) | 4 处已知错误找出 |
|---:|---:|---:|---:|---:|
| 5 | 8 | 7.5M | 92k | 3 |
| 10 | 4 | 11.0M | 77k | 2 |
| **20** | 2 | 15.3M | **72k** | 3 |
| 40 | 1 | 24.3M | 89k | 4 |

- 每批有固定开销(系统提示、工具定义、批次说明),批越小，这部分分到每题越多。
- 每读一张题图，之后每一轮都要重读全部上文，读缓存随批次大小超线性增长。40 题一批时读缓存是 5 题一批的 3 倍多。
- 两者相加，每题费用在 20 题一批时最低，比 10 题一批省约 6%,比 40 题一批省约 20%。
- 质量上四种大小没有随批次变大而变差的迹象(40 题一批 4 处全找到),漏掉的都是需要细看图的错误：
  原卷本身漏印的 ×10⁻³(9702_w21_41_q08)、OCR 把 ⅓V₀ 读成 ½V₀(9702_s26_42_q06)。样本只有 4 处错误，不能据此比较质量，
  只能说明 20 题一批没有明显变差。
- 结论：`fix_batches.py plan` 的 `--size` 默认改为 20。其他批次脚本(`tag_batches.py`、`latex_fix_batches.py` 等)
  每题读图更少，固定开销占比更高，同样不宜低于 20 题一批。

同时补上 9702 评分细则的校验:`verify` 对 9702 按行格式检查(`check_scheme_rows`),评分码 B1/C1/A1/M1(卷 5 为每点分数)
合计应等于题目分值；列出多种解法(OR、Alternative)时可以超出。括号里的码 "(C1)" 属于另一种解法，卷 5 的 D1–D10
只取其中几点，两者都不计入合计。对现有 802 道卷 2/4/5 题运行，795 道通过；其余 7 道是没有评分细则的 9702_s26_21
(5 题)与评分细则尚未转成行格式的 9702_s26_52_q01、9702_s26_54_q01(OCR 版分别因乱码和表格内分值位置未写入)。

## 清除残留水印(2026-10-21)

1. **FPDF 重组卷的标志。** data 分支 `papers/` 中 11 份 2021 年 6 月的试卷(`9231_s21_qp_32`、`_33`、`_41`、`_42`、`_43`,
   `9709_s21_qp_21`、`_22`、`_23`、`_61`、`_62`、`_63`,共 160 页)是 papacambridge 用 FPDF 重新打包的版本
   (producer 为 "FPDF 1.7")。每页把原页面作为表单对象 `/TPLn` 缩小约 0.95 倍画出，右下角画一张
   PapaCambridge 标志图(`/I1`,999×156)并覆盖一个指向 papacambridge.com 的链接，另有一段粉色的空格文字。
   文本层里没有站点名称，此前按文字查找的检查漏掉了它们。`strip_watermark.py` 把页面内容换成只画 `/TPLn`
   (按原尺寸，即剑桥原版版面),删去标志图与链接。题图是另行裁切的，不含标志，不需要重裁。
2. **不再画出但仍留在文件里的水印对象。** 前两次去水印只删了画出水印的指令，被引用的对象仍在页面资源里，
   保存时没有被丢弃:344 份 dynamicpapers 文件里写着网址的表单对象(6009 处),58 份 2026 年 papacambridge
   文件里的 `/FormXob.pcm`(828 处)。脚本现在删去页面资源中未被画出的水印对象。
3. **文档属性。** 58 份 2026 年 papacambridge 文件的标题、作者、主题、关键词、创建程序、生成程序与 XMP
   元数据都写着 PapaCambridge,阅读器的标题栏会显示。脚本删去含站点名称的属性与 XMP 元数据。

处理后对 data 分支全部 1107 份 PDF 检查：解压后的全部对象中不再出现 papacambridge、dynamicpapers、fraft
等站点名称;文本层中的网址只有 `www.cambridgeinternational.org` 与题目里的示例网址;外部链接为零;
逐页渲染找彩色像素，命中的都是评分标注符号、程序输出与彩色图表;页面四周 14–18 pt 边缘区域的深色内容
都是剑桥原卷的页边竖排文字、条形码、DataMatrix 页码码与角标。除 11 份 FPDF 卷外，处理前后共 6901 页渲染逐像素相同。
题图(`img*/` 下 9877 张)按同样方法检查，彩色的只有 BMAT 2006–2007 的 9 张图表。
题库管理器组卷的缓存键加入了原卷 PDF 的修改时间，原卷更新后用整份原卷组成的卷子会重新生成。

## 去除 dynamicpapers 页眉网址(2026-10-18)

data 分支 `papers/` 中 344 份来自 dynamicpapers 的试卷与评分细则(9709 2021–2025 年 248 份、9618 2023–2025 年 96 份)
每页页眉带 `www.dynamicpapers.com`。它是 Acrobat 加的页眉:页面内容末尾一段
`/Artifact <</Contents (www.dynamicpapers.com)/Subtype /Header …>> BDC … EMC`,调用一个只画这串文字的表单对象。
`strip_watermark.py` 删去这一段(表单对象在保存时作为无用对象丢弃);处理前后正文渲染逐像素相同,只有页眉区域变化。
此前 skill 说明称 GitHub 源已去水印,实际只去过 papacambridge 的,现已一并处理。

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

