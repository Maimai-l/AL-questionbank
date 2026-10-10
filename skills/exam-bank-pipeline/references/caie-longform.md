# CAIE 长题:9709、9231 与 9618

本文档说明 CAIE 长题线各脚本的职责与已知的执行顺序约束。库中已有 2956 题,
覆盖 2021 至 2025 年共 378 份卷子。

脚本位于 `scripts/qb/pipeline/` 下,按阶段分为 `fetch`、`split`、`ocr`、
`text`、`tags`、`books`、`db` 七个包。两种调用方式均可:

```bash
python3 -m pipeline.<包>.<脚本>      # 需先切换到 qb/ 目录
python3 pipeline/<包>/<脚本>.py      # 在任意目录下均可运行
```

## 与选择题线的根本差异

CAIE 的一道题由多个小问、分值与独立的评分细则构成,而非一段选项。由此产生
四点差异:

- 题目与答案分处两个 PDF(qp 与 ms),需分别切分后按题号配对;
- 切分锚点是题号与分数标记(`[3]`、`[Total: 12]`),而非选项连排;
- 验收依据是分数:题面标注的总分应等于评分细则中该题的总分,由
  `totals_agree` 列记录,不符即说明小问未切全;
- 一道题可能带有 `parts`(如 `["3(a)","3(b)"]`)与 `marks_parts`(各小问
  分值)。

## 流水线

```
fetch_any.py --years ...      抓取 qp 与 ms 的 PDF,CAIE 自 2002 年起可得
   ↓
split_qp.py / split_ms.py     按题号切分,产出逐题片段
   ↓
ocr.py / ocr_ms.py            文本层不可用时补充 OCR,9709 的评分细则尤其需要
   ↓
crop.py                       逐题无损裁图,输出 img9709/ img9231/ img9618/
   ↓
combine.py                    建立 questions 表
   ↓
syllabus.py + topic_model.py  主题标注
   ↓
build_db.py                   入库
```

辅助脚本及其职责:`parse_ms_ocr.py` 解析 OCR 版评分细则;`merge_ocr.py` 与
`merge_ms_ocr.py` 将 OCR 版正文并回数据表;`flag_quality.py` 标记
`q_quality` 与 `ms_quality`;`audit_text.py` 抽查正文质量;`clean_encoding.py`、
`fix_garbled.py` 与 `fix_newlines.py` 修补编码与换行;`html_tables.py` 将
真值表与追踪表转为 pipe 表;`mark_partial.py` 标记截断的正文;`salvage.py`
从损坏片段中抢救内容;`eval_tags.py` 评估标注准确率;`lib/paths.py` 解析
图片根目录;`qb.py` 提供命令行查询。

## 两处执行顺序约束

第一,`combine.py` 会重建整张 questions 表。因此 `flag_quality.py`、
`mark_partial.py` 这类向表中写入标记的步骤,必须排在 combine 之后。顺序颠倒
时标记会被静默覆盖,且表面上数据表完全正常。

第二,`merge_ocr.py` 必须在 `combine.py` 之后运行,否则 OCR 版正文会被覆盖
回 pdftotext 版。库中 `question_latex` 与 `ms_latex` 是 OCR 版,应优先使用;
`question_text` 与 `ms_text` 是文本层版,数学公式会退化,仅作兜底。

## 主题标注:以大纲为语料,IDF 在 component 内计算

不使用手写关键词表,而是直接采用大纲自身的措辞。每个 sub-topic 构成一份
文档,内容为标题、learning outcomes 与 notes;n-gram 取至 3,使
"stationary point"、"sum to infinity" 一类短语得以整体保留;题目按命中的
不同词的权重打分,不计词频——评分细则中方法词会反复出现,重复并不代表更强
的证据。

IDF 必须在 component 内部计算,不能全局计算。以 `differentiate` 为例,它在
全库范围内是废词,但 P1 与 P3 出自不同卷子,全局降权会使 P1 微分主题唯一的
标识词失效。

9618 有一处特殊:它按大纲章节号(1 至 20)编排题目,而每份卷子从若干章节
取题,因此需要一张 component 到章节范围的映射。两门数学不需要,其
component 号与 topic 前缀本就一致。

已验证的准确率:经模型复核的三个最弱分组实测为 78%,其余分组尚无验证集。
把握不足的题目以 `topic_confident=0` 与 `topic_margin=0` 标出,查询时可用
`--exclude-ties` 排除。

## 教材章节索引

81 章教材索引存于 `chapters` 表,表中只存路径,正文位于 `books/` 下的
markdown 文件。该索引与题库共用同一套 topic 码,因此"某主题的题目与对应
课本章节"可以一并取出。

```
ocr_books.py                      教材 OCR
split_chapters.py                 按目录切章
contents_table.py / dump_toc.py   解析目录页
chapters.py index                 建立索引并计算 coverage,即该章覆盖了大纲哪些条目
```

更换教材需重跑上述四步。章节中的插图须另行拷入 `books/<书名>/imgs/`,否则
markdown 中会显示为缺失图片。

## 先修关系

`prereq.py` 产出 `prereq.json`,包含 `components`(卷与卷之间的先修关系)
与 `topic_prerequisites`(主题之间的先修边)。其用途是:当某个主题得分偏低
时,判断是该主题本身掌握不足,还是其先修主题薄弱导致的下游表现不佳。
`export_web.py` 会将这张图一并写入 `data.js`,统计页据此做归因。

新增考试时也需在此补充边,例如 TMUA 的 `TMUA:P1 ← 9709:P1`,以及
`TMUA:MM6 → TMUA:MM7`(先掌握微分才谈得上积分)。

## 已知缺口

以下三项均为数据源本身的限制,不应作为缺陷修复:

- 114 道 9709 题没有答案。2025 年 6 月场次的评分细则官方尚未发布,题目本身
  是完整的。
- 67 道题的正文标记为 `partial`。OCR 中途退化,前半段可读而后续小问缺失。
  界面会显示"文字版不完整,以原题图为准",`--clean` 选项会排除这些题。原题
  图是完整的,因此这些题仍然可以作答。
- 5 条大纲要求在教材中找不到对应位置。其中 4 条属于措辞差异,1 条是教材确实
  未涵盖。
