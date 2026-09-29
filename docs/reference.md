# CAIE 题库设计与数据质量记录(9709 / 9231 / 9618)

> 本文是 CAIE 三科建库时的设计记录,保留了切分、OCR、标注中各类问题的来龙去脉。
> 其中的目录布局与命令写法是当时的状态,已经过时。当前的目录布局、运行方式与
> 数据位置以 [README](../README.md)、[流水线说明](pipeline.md)、
> [数据同步](data-sync.md) 为准。下文数量为 CAIE 三科,入学考见 [admissions/](admissions/题库说明.md)。

**2956 道真题**,2021–2025,378 份卷子。每题含 LaTeX 题干、mark scheme、
syllabus topic 标签、分值、是否带图,以及**无损原图**。

| 科目 | 题数 | 卷数 | 卷子 |
|---|---|---|---|
| **9709** Mathematics | 1233 | 140 | P1 Pure 1 / P3 Pure 3 / P4 Mechanics / P5 Prob & Stats 1 |
| **9231** Further Mathematics | 841 | 120 | P1 FP1 / P2 FP2 / P3 Further Mechanics / P4 Further Prob & Stats |
| **9618** Computer Science | 882 | 118 | P1 Theory / P2 Problem-solving & Programming / P3 Advanced Theory / P4 Practical |

```
qb/
  caie.db          三科合一的 SQLite(含 FTS5 全文索引)
  img9709/  img9231/  img9618/    三科的无损裁图
  assets/caie.html    给人用的刷题界面(双击就能开,见下一节)
  assets/data.js          刷题界面读的数据(由 export_web.py 从 caie.db 生成)
  assets/vendor/katex/    离线公式渲染,断网也能用
  qb.py            命令行查询
  attic/mcp_server.py  MCP server(默认收起,见 attic/README.md)
  fetch_any.py     通用下载器     split_qp.py / split_ms.py  切分
  crop.py          裁图           ocr.py / merge_ocr.py      题干 LaTeX 转写
  ocr_ms.py / parse_ms_ocr.py / merge_ms_ocr.py   mark scheme OCR
  fix_garbled.py   切条重读退化的裁图   audit_text.py  可读性审计
  flag_quality.py  逐题择优并写入质量标记(combine 之后必须跑)
  tag_any.py       topic 标注     topics_9231.py / topics_9618.py / tag.py  标签表
  build_db.py      建单科库       combine.py                 合并三科
  fix_names.py     修文件名引用
  export_weak.py / merge_retag.py   导出最弱的组交给模型重标,再写回
  syllabus.py      解析大纲 PDF -> syllabus.json(官方 learning outcomes)
  topic_model.py   用官方措辞给主题打分   eval_tags.py  新旧标签器对比验证
  retag.py         合成打标并写回        prereq.py     先修关系图 -> prereq.json
  attic/progress.py    做题记录 / 掌握度 / 弱点诊断(attempts 表,默认收起)
  ocr_books.py     一条命令把教材 PDF 全部 OCR(含插图)
  split_chapters.py  按 PDF 书签合并成章   chapters.py  章节入索引 + 查漏
  clean_encoding.py  PUA / 控制字符 / 错映射字形修复
  fix_newlines.py    字面 \n 还原成真换行     html_tables.py  HTML 表格转竖线表格
  mark_partial.py    标出被截断保留的题干     export_web.py   导出 assets/data.js
```

PDF 原件不在包里(约 620 MB)。用 `fetch_any.py` 可重新下载。

### 目录结构 —— 三个图片文件夹要放在 `qb/` **里面**

```
任意位置/
└── qb/
    ├── caie.db
    ├── qb.py  lib/  pipeline/  attic/  ...
    ├── img9709/    1233 张
    ├── img9231/    841 张
    └── img9618/    882 张
```

图片压缩包里是顶层文件夹,所以**要在 `qb/` 目录内解压**。

两点兼容,都不需要重新下载图片:

- 解到了 `qb/` 外面一层也能用 —— `paths.py` 会自动往上一层找。也可以用
  `CAIE_IMG_ROOT` 环境变量显式指定。
- 9709 的裁图原先叫 `img/`,现已统一为 `img9709/`。**旧名仍然识别**,本地
  `mv img img9709` 改不改都能跑。

`python3 qb.py stats` 最后一行会报告它实际用的是哪个位置和哪个文件夹名。

---

## 给人用:`assets/caie.html`

双击打开就行,不用装任何东西,也不用开服务器。

- **刷题** —— 左边按科目 / 卷子 / topic / 分值 / 年份 / 关键词筛,右边一次一题。
  默认显示**原题图**(页面原样裁下来的,含图形和排版),一键切"文字版"。
  空格显示答案,`←` `→` 翻题,`1` `2` `3` 打"会了 / 一般 / 不会"。
- **组卷** —— 选科目和 paper,每个 topic 各抽一题、凑到该卷官方总分,
  带倒计时,可以"留出某一年"当模考,可以直接打印。
- **统计** —— 按 topic 的掌握率,从低到高排;哪块最弱一眼看到。

做题记录存在浏览器本地。换机器或清了缓存,用右上角**导出记录 / 导入记录**
搬一个 JSON 就行。

> 打开后如果题图显示不出来,把 `img9709/ img9231/ img9618/` 三个文件夹放到
> `assets/caie.html` 旁边(或它的上一层)即可 —— 页面两处都会找。

改了 `caie.db` 之后重新生成界面用的数据:

```bash
python3 pipeline/export/build_site.py
```

---

## 快速开始

```bash
python3 qb.py stats                                          # 库里有什么
python3 qb.py topics --syllabus 9231                         # 某科的 topic 清单
python3 qb.py find --syllabus 9709 --topic 1.7 --marks 6-8   # P1 微分,6–8 分
python3 qb.py find --syllabus 9618 --text "recursion" -n 5   # 全文搜索
python3 qb.py find --syllabus 9231 --component 3 --diagram yes
python3 qb.py show 9231_s23_31_q04 --full                    # 单题 + 完整 mark scheme
python3 qb.py paper --syllabus 9618 --component 3            # 组一套 P3 模拟卷
python3 qb.py paper --syllabus 9709 --component 4 --exclude-year 2025
```

任何命令加 `--json` 输出机器可读格式。

## 大纲驱动的标签(v3)

原来的标签是我照着大纲**猜**的关键词表。现在大纲本身进来了:
`syllabus.py` 从三份 syllabus PDF 里抽出 Cambridge 自己的措辞 ——
9709 38 个 topic / 161 条 learning outcome,9231 24 / 89,9618 44 / 255 ——
`topic_model.py` 用这些正文做 TF-IDF 打分。

**测出来的结果和我预期相反,所以没有整套替换。** 用 768 道模型逐题重标的题当验证集:

| 子集 | 题数 | 关键词表 | 大纲模型 | 两者相加 | 大纲前三 |
|---|---|---|---|---|---|
| 平局 `margin=0` | 48 | 41.7% | 62.5% | **75.0%** | 95.8% |
| `margin=1` | 84 | 52.4% | 47.6% | **63.1%** | 92.9% |
| `margin>=2` | 636 | **81.3%** | 64.6% | 80.3% | 95.4% |
| 全部 | 768 | 75.7% | 62.6% | 78.1% | **95.2%** |

大纲模型单独用比关键词表**差**,但在关键词表拿不定主意的地方好 11–33 个点,
而且它的**前三名有 95% 命中**。所以 `retag.py` 的策略是:关键词表有把握时
(margin ≥ 2)保持原判,拿不定时用相加分数,模型逐题读过的 768 道一律不动。

结果:**2956 道全部有标签(原先 31 道没有)**,变动 174 道,新增 `topic_all`
三选一短名单。

独立验证(没有用来调参):CAIE 每份卷子按大纲铺主题,所以**每卷覆盖的主题数**
是个外部信号。重标后 9709 P3 **全覆盖的卷子从 1 份涨到 6 份**,9231 P1 从 24 涨到 28,
9709 P5 从 29 涨到 31,没有一组变差。

顺带,9618 现在有了**子主题**:`subtopic` / `subtopic_name`,882 道全部落到
15.2 Boolean Algebra 这一级,不再只是"第 15 节"。

```bash
python3 qb.py find --syllabus 9618 --subtopic 15.2
```

### 先修关系

`prereq.py` 产出 `prereq.json`,每条边都标了来源,因为可信度不一样:

- `syllabus` —— 大纲明文。9231 的 prior-knowledge 表(P3 需要 9709 P1/P3/P4)、
  "Knowledge of Paper 1 is assumed" 这类句子、9618 目录树里的 AS / A Level 分层。
- `name-match` —— 同名主题在后修卷里重现(1.7 → 3.4 → 9231 2.3 Differentiation),
  方向由上面的卷间关系定出来,是推导不是断言。
- `co-occurrence` —— 题库里常同时出现的主题对。这是**相关不是先修**,标签写明了。

**没有一条边是我拍脑袋写的。**

## 学习者状态(v3)

`caie.db` 多了一张 `attempts` 表,**只增不改**:三月做错、六月做对,和一直做对
是两回事,而这个差别是整个系统里唯一能看出"学会了"的证据。

```bash
python3 attic/progress.py init
python3 attic/progress.py import caie-做题记录.json   # 刷题界面导出的那个
python3 attic/progress.py weak --syllabus 9709
```

```
主题                                掌握    题数   作答  诊断
9709 3.4 Differentiation           0.35    13    13  先补先修:9709:1.7
9709 1.7 Differentiation           0.42    13    13  问题就在这个主题本身
```

掌握度按**同一题的新记录压过旧记录**算(衰减 0.6),所以补回来的主题会往上爬,
不会被历史钉死。诊断那一列就是先修图的用处:掌握率低不代表问题在这个主题。

## 给 AI 调用(MCP)

8 个工具:`search_questions` / `get_question` / `list_topics` / `build_paper`
(找题、组卷),加上 v3 的 `topic_detail` / `record_attempt` / `weak_topics` /
`next_lesson`(讲课、记录、诊断)。

`next_lesson` 是把前面所有东西串起来的那个:挑出**先修已经过关**的最弱主题
——先修没过关就改教先修——返回该主题的大纲原文 learning outcomes,加一梯
由易到难的真题,其中一道是之前做错过的。

```json
{
  "mcpServers": {
    "caie-question-bank": {
      "command": "python3",
      "args": ["/绝对路径/question_bank/attic/mcp_server.py"]
    }
  }
}
```

四个工具:`search_questions`、`get_question`、`list_topics`、`build_paper`。
零依赖,标准库直接说 JSON-RPC。**按 topic 搜之前先调 `list_topics`**——
三科的 topic 编号体系不一样。

> 给我 5 道 9231 的复数题(2.5),8 分以上,2025 年的排除

> 用 9618 P2 的真题组一份 75 分的模拟卷,附 mark scheme

## 直接查 SQLite

```sql
SELECT id, marks, topic_name, question_latex
FROM questions
WHERE syllabus='9231' AND component='3' AND topic='3.3' AND marks >= 8
ORDER BY year DESC;
```

| 字段 | 说明 |
|---|---|
| `id` | `9231_s23_31_q04` = 科目 / 2023年6月 / 卷31 / 第4题 |
| `syllabus` | `9709` / `9231` / `9618` |
| `component` / `component_name` | 卷号与卷名 |
| `paper` / `variant` / `year` / `month` / `session` / `series` | 出处 |
| `q` / `parts` / `marks` / `marks_parts` | 题号、小问、总分、各小问分值 |
| `topic` / `topic_name` / `topic_all` | 大纲编号;`topic_all` 是排序后的候选 |
| `topic_margin` | 关键词打分的最高分减次高分。**`0` 表示平局,标签不可靠**;模型核过的为 `NULL` |
| `topic_source` | `model` = 模型逐题读过并判定;`keyword` = 关键词打分 |
| `topic_note` | 模型给的一句话理由(仅 `topic_source='model'` 时有) |
| `question_latex` | **LaTeX 题干**,`[DIAGRAM]` 标记图的位置 |
| `question_text` | 原始文本层,有损,只用于 FTS 分词,不要拿来阅读 |
| `has_diagram` | 该题是否含图 |
| `ms_latex` | **OCR 重读的 mark scheme**,保留 LaTeX 与四栏结构 —— 数学科看这个 |
| `ms_text` | PDF 文本层的 mark scheme;数学科严重丢符号,只用于 FTS 和取评分代码 |
| `mark_codes` / `ms_total` | 评分代码、总分 |
| `q_quality` / `ms_quality` | `ok` / `degraded` / `severe` / `garbled` / `missing` |
| `totals_agree` | 题目分值是否等于 mark scheme 总分(提取自检) |
| `image` | 无损裁图路径(`img9709/` `img9231/` `img9618/`)—— **公式和图形以此为准** |
| `qp_pdf` / `ms_pdf` / `qp_pages` | 回溯到原始 PDF |

---

## 数据质量(实测)

### 分值总和 —— 最硬的一条

每份卷子的分值加起来必须等于官方总分。漏题、重题或读错分值都会立刻暴露。

| 科目 | 精确对上的卷数 | 官方总分 |
|---|---|---|
| 9709 | **140 / 140** | P1/P3 75,P4/P5 50 |
| 9231 | **118 / 120** | P1/P2 75,P3/P4 50 |
| 9618 | **116 / 118** | 四卷均 75 |

### 每卷题数 vs 大纲规定

| | 实测 | 大纲 |
|---|---|---|
| 9709 P1 / P3 / P4 / P5 | 10.9 / 10.7 / 7.0 / 6.7 | 10–12 / 9–11 / 6–8 / 6–8 |
| 9231 P1 / P2 / P3 / P4 | 7.0 / 8.0 / 6.9 / 6.1 | 6–8 / 7–9 / 5–7 / 5–7 |
| 9618 P4(Practical) | 3.0 | 3 道大编程题 |

### 题目 ↔ mark scheme 交叉验证

两边独立提取的总分是否一致:**9618 97.5% / 9709 89.5% / 9231 88.0%**(整体 91.6%)。
不一致的全部是 mark scheme 侧总分**漏抓**(分栏位置逐页漂移),正文本身没问题。
`totals_agree` 字段记录了每道题的结果,可以据此过滤。

### 文本可读性 —— 实测,不是估计

判定标准:剥掉 LaTeX 记号后统计"孤立单字符"的比例,并检查数学答案里是否
连一个等号都没有(真答案不可能)。

| | 题干 `question_latex` | Mark scheme |
|---|---|---|
| 9709 | **99.9%** | **84.2%**(另有 114 道无答案) |
| 9231 | **99.5%** | **97.0%** |
| 9618 | **99.9%** | **97.4%** |

`q_quality` 有四档,`ms_quality` 三档,查询时可以直接过滤:

| 值 | 含义 |
|---|---|
| `ok` | 干净完整 |
| `partial` | **读得通,但后半截缺了** —— OCR 中途退化,截断保留了前面能读的部分。**原图是完整的**。67 道 |
| `degraded` | 排版有损,内容还能读 |
| `garbled` / `severe` | 不可读 |
| `missing` | 没有这个字段 |

`partial` 是单独一档而不是并进 `ok`,因为它读起来通顺、缺了一截却不会有任何
提示 —— 用的人根本察觉不到。`qb.py --clean` 和 MCP 的 `clean_text_only`
都只放 `ok` 过。

**这里踩过一个大坑,写下来备忘。** 最初只用 Paddle 补了题干,答案沿用
`pdftotext` 抽的,结果数学答案的可读率只有 **9709 20.5% / 9231 9.2%**——
数学排版的等号、减号、指数、分数线被整片丢掉:

```
真实答案:  y = -2/(x-3)² + 7
pdftotext: y        x  331 or                c
```

修法是把 **365 份 mark scheme**(三科全做,约 6000 页)整份送进 PaddleOCR-VL
(页面横向旋转,要开 `useDocOrientationClassify`),它返回带 LaTeX 的 HTML
表格,Question/Answer/Marks/Guidance 四栏结构完整保留,再按题号拆开存进
`ms_latex`。

**9618 是个例外**:它的文本层本来就是干净散文,OCR 反而会把表格压平。所以
`flag_quality.py` 会**逐题比较两个版本,哪个好用哪个**,并丢弃 43 份评分更差
的 OCR 结果——不是无脑覆盖。

题干那边另有 **104 道 OCR 退化**——模型陷入重复循环,一直吐"貳柒"这类字符。
整图重跑无效(同一张图必然复现),但**把图切成 900px 的横条分别识别再拼接**
恢复了 64 道:短输入进不了循环。

`q_quality` / `ms_quality` 字段记录了每道题的等级,可以直接过滤:

```bash
python3 qb.py find --syllabus 9709 --clean          # 排除仍然读不顺的
python3 qb.py find --syllabus 9231 --readable-ms    # 只要 OCR 过的答案
```

**题干干净且答案可读的共 2766 道。**

`q_quality` 的四档见上一节。`partial` 单独成一档,是因为它读起来通顺、
却缺了一截,用的人不会察觉 —— 并进 `ok` 属于不诚实。

#### 表格和换行 —— 最后一轮才发现的两个问题

界面写完、把答案摊在屏幕上看,才看见两件在命令行里一直没露头的事:

1. **mark scheme 里的换行是字面的两个字符 `\` + `n`**,不是真换行。整份答案
   挤成一行,读起来是 `...(Max 5)\nOne mark per...`;按行切分的检索也会把
   整份当成一个块。1911 份答案受影响。
   还原时要绕开真 LaTeX:`\neq` `\nu` `\nabla` 得留着。判据是后面跟不跟字母
   —— 只有 `\ne` 要特判,后面是 `.` 的一律是换行 + "e.g."(在这个库里
   四比一),后面是空格的才是 ≠。
2. **OCR 把每个表格都还成了 HTML `<table>`**,601 道题的题干里塞着几万个
   `<td style='text-align: center; word-wrap: break-word;'>`。内容是对的,
   但人读不了,喂给模型也是纯浪费 token —— 一张 20 行的 trace table,
   光样式属性就几百个 token。

   现在统一转成竖线表格,`rowspan` / `colspan` 会展开对齐:

   ```
   | A | B | C | Working space | S |
   |---|---|---|---|---|
   | 0 | 0 | 0 |  |  |
   ```

   只动已知的排版标签。9618 的 BNF 题里 `<symbol>` `<letter>` 是**题目内容**
   不是标记,剥掉就毁了。

顺带修好了一个自伤的判据:可读性是按"孤立单字符占比"算的,而真值表本来就
只有单字符,于是 30 道最干净的 9618 表格题被判成 degraded。现在按行判断,
每格平均 ≤3 字符的行算数据行,不计入。

#### OCR 退化的形态不止一种

最初只查了中文字符,漏掉了另外三种,其中 5 条**混在 mark scheme 里被判成 ok**:

- 长串换行 `\n\n\n\n…`
- 长串数字 `0.0000000000…`
- **中文塞进代码标识符**:`File门外FoundException`、`Line.split借贷")`

同时要小心**误伤**:9618 的真值表本来就长这样 `0 | 1 | 0 | 1 | …`,单纯的
"重复片段"检测会把合法内容判成乱码。所以判定要求重复单元是空白,或者重复
段落占全文 40% 以上。

修完全库**零残留退化**。

#### 裁图边界也修了一轮

每卷**最后一题**的裁图原先会一路延到文档末尾,把"Additional page"、整页答题
横线、版权声明、条形码全裁进去。一道 6 分的积分题,图有 1646px 高,真正的
题目只占最上面一行。

三个原因叠加,都修了:

- 尾部样板要**按位置截断**(检测到标记就从那一行往下全不要),只删匹配到的
  文字行不够 —— 版权段的续行("shown."、"publisher will be pleased…")
  单独看根本认不出来。
- **卷子中间的整页 BLANK PAGE 不是尾部**,要跳过而不是终止;混为一谈会把
  跨页的题目截断(实测让 9618 有一卷少了 6 分)。封面那句 "Any blank pages
  are indicated" 也会误匹配,所以 `BLANK_RE` 必须区分大小写。
- 镜像水印在文本层留下**含控制字符**的碎片(`,\x01\x01 ,`),会把裁图撑出
  一条细边。

修完那道题的裁图从 1646px 降到 84px。共 1144 张裁图重新生成。

MCP 对应参数:`clean_text_only`、`readable_mark_scheme`。

### Topic 标注 —— 最弱的一环

人工抽样核对(每科 40 题,看原图判定):

| 科目 | 准确率(跨 topic 且合理算对) | 严格精确 | 最差的卷 |
|---|---|---|---|
| **9231** | **92.5%** | 92.5% | P3 Further Mechanics 80% |
| **9709** | **85%** | 75% | P4 Mechanics 70% |
| **9618** | **75%**(修正前) | 67.5% | P4 Practical 60% |

#### 三个最弱的组已由模型逐题重标

关键词法在词汇无法区分 topic 的地方失效。这三组共 **540 道题**已经由模型
逐题读题干和 mark scheme 重新判定(必要时开原图),`topic_source='model'`:

| 组 | 题数 | 改动 |
|---|---|---|
| **9618 P2 Problem-solving & Programming** | 228 | **98(43%)** |
| 9709 P4 Mechanics | 245 | 49(20%) |
| 9231 P3 Further Mechanics | 208 | 21(10%) |
| 9618 P4 Practical | 87 | 10(11%) |

合计 **768 道**(占全库 26%)带 `topic_source='model'`。

典型错误:功率题(P=Fv)被标成牛顿定律;纯微积分运动学被"acceleration"
一词拉去 4.4;抛体题因为"collide"被标成动量;9618 里实现栈/队列/链表的题
因为 mark scheme 用类写的而被标成 OOP;9618 P2 里**结构图和状态转换图**
本属 section 12(程序设计表示法)却被塞进 11,**追踪表和流程图**本属 9
却因为"写伪代码"被当成编程题。

9618 P2 修正后的分布(与关键词版对比):

| section | 关键词 | 模型 |
|---|---|---|
| 9 Algorithm Design | 37 | **50** |
| 10 Data Types and Structures | 106 | 65 |
| 11 Programming | 67 | 81 |
| 12 Software Development | 18 | **32** |

**一个独立的结构验证**:9231 P3 每份卷子的出题结构就是六个 topic 各一题
(外加一道圆周运动)。重标后 **30/30 份卷子覆盖全部 6 个 topic**;重标前有
几份卷子根本没有抛体题、却有两三道动量题。

```bash
python3 qb.py find --syllabus 9709 --component 4 --verified    # 只要模型核过的
```
MCP 的 `search_questions` 有对应的 `verified_topic_only` 参数。

核对后修掉的系统性错误:

- 9618 **section 15 整节漏了 Boolean Algebra / 逻辑电路**(大纲 15.2),导致
  26 道卡诺图题无法标注。修正后 P3 的 null 从 35 降到 2。
- 9618 排序有 **tie-break bug**:`sorted(reverse=True)` 在同分时按字符串比,
  `'20'` 永远压过 `'19'`。修正后 P4 的 19:20 分布从 18:69 变成 48:39。
- 9618 section 11 是垃圾桶:P2 里占 63%(mark scheme 的散文里到处是
  function/parameter/loop)。降权后降到 29%,section 9 从 5% 升到 16%。
- 9231 卡方检验被误标成 t 检验:4.3 从 29 升到 39。
- 9709 静力学被误标成牛顿定律(4.1↔4.4)、几何/二项分布被吞进"概率"(5.3↔5.4)。

**上述修正是在抽样核对之后做的,没有重新抽样复测**,所以表里的数字偏保守
——尤其 9618,它的三个系统性错误都已修掉。

#### 平局:142 道题(4.8%)的标签是被迫二选一

打分相同时必须挑一个。我抽了 32 道平局逐一看图核对,结论:

- **全局"低编号优先"就是抛硬币**(11 比 11),原先按字符串比更是荒谬(`'20'` 压 `'19'`)。
- **正确方向按科目相反**:9709 该选后者(前面的编号往往是"载体"——三角、对数、代数,
  后面的才是考点——微积分、微分方程),9618 该选前者(算法设计题的 mark scheme
  里满是编程词汇,把 9 拉向 10/11)。9231 样本太少,不下结论。
- **21% 的平局,正确答案根本不在前两名**——平局是"打分失效"的信号,不是
  "两个都有道理"。

现在的做法:按科目定方向,加几条有实测依据的配对规则(9709 1.7/1.8→1.8、
5.3/5.4→5.4;9231 2.1/2.4→2.4、4.2/4.3→4.2;9618 16/19→16、9/10→9、9/11→9),
并且**把 `topic_margin` 存进库**。

```bash
python3 qb.py find --syllabus 9709 --topic 1.8 --exclude-ties
```
MCP 的 `search_questions` 有对应的 `exclude_tied_topics` 参数(模型核过的题
`topic_margin` 为 NULL,不会被这个过滤误伤)。排除平局后仍有 **2806 道**可用。

`topic_confident` 在 9709 上**校准是反的**(在最差的 Mechanics 上最自信),
在 9618 上有效(true 87% / false 40%)。别单独依赖它。

剩下 2157 道仍是关键词标签:9709 P1/P3/P5、9231 P1/P2/P4、9618 P1 和 P3。
抽样准确率见上表(85–92.5%),这几组的词汇区分度都比已重标的四组好。

---

## 已知限制

1. `question_latex` 没有逐题人工核对。偶有 OCR 幻觉(见过把变量 `j` 认成
   CJK 字符)。**要 100% 确定时读 `image`**,那是页面原样裁下来的。
2. Topic 标签的主体仍是关键词打分。上表实测:模型重标过的三个最弱组里,
   关键词 + 大纲相加是 78.1%。其余组没有验证集,准确率未知。
   `retag.py` 里 margin ≤ 1 这个阈值是看着验证集定的 —— 机制(拿不准时听第二意见)
   是讲道理的,具体这个数是拟合出来的。
3. 只覆盖 2021–2025。改 `fetch_any.py` 的 `--years` 可扩(CAIE 从 2002 年就有)。
4. **114 道 9709 题没有 mark scheme** —— 2025 年 6 月的
   mark scheme 镜像尚未上传。题目本身完整。
5. 题源:9709 和 9618 来自 Dynamic Papers,9231 来自 bestexamhelp
   (Dynamic Papers 没有托管 9231)。**GCE Guide 域名已被抢注,不要用。**
6. 版权归 UCLES / Cambridge International。自用可以,别公开分发。
7. 67 道题的 `question_latex` 是 `partial`(见上),文字版缺后半截,`image` 完整。
8. 5 道 9618 的 mark scheme 仍是 `severe` —— 整份几乎只有真值表,没有散文可读。

## 重跑 / 扩展

```bash
pip install pymupdf requests

# 下载(9231 的源不同)
python3 -m pipeline.fetch.fetch_any 9709 pdf --years 21 22 23 24 25 --papers 1 3 4 5
python3 -m pipeline.fetch.fetch_any 9618 pdf9618 --years 21 22 23 24 25 --papers 1 2 3 4 --series s w
python3 -m pipeline.fetch.fetch_any 9231 pdf9231 --years 21 22 23 24 25 --papers 1 2 3 4 --series s w \
  --url-template "https://bestexamhelp.com/exam/cambridge-international-a-level/mathematics-further-9231/{year4}/{name}"

# 每科一遍
python3 -m pipeline.split.split_qp pdf9231 q9231.json
python3 -m pipeline.split.split_ms pdf9231 ms9231.json
python3 -m pipeline.split.crop q9231.json pdf9231 img9231
python3 -m pipeline.tags.tag_any 9231 q9231.json ms9231.json
python3 -m pipeline.db.build_db 9231 q9231.json ms9231.json 9231.db img9231

# LaTeX 转写(约 60 张/分钟,32 并发;结果流式写入,中断可续跑)
export PADDLE_TOKEN=你的token
python3 -m pipeline.ocr.ocr q9231.json img9231 ocr9231.jsonl 32
python3 -m pipeline.ocr.merge_ocr ocr9231.jsonl 9231.db

# 模型重标最弱的三组(可选)
python3 -m pipeline.tags.export_weak caie.db retag        # 导出成批次
#   ... 让模型逐批读题,结果写成 retag/out_*.json ...
python3 -m pipeline.tags.merge_retag retag                # 写回 JSON,再重建库

# Mark scheme OCR(数学科必须做,否则答案不可读)
python3 -m pipeline.ocr.ocr_ms pdf,pdf9231 ms_ocr.jsonl 24
python3 -m pipeline.ocr.parse_ms_ocr ms_ocr.jsonl ms_ocr_parsed.json
python3 -m pipeline.ocr.merge_ms_ocr ms_ocr_parsed.json caie.db

# 修复 OCR 退化的题干,再审计一遍
python3 -m pipeline.ocr.fix_garbled caie.db /tmp/regen.jsonl 10
python3 -m pipeline.ocr.merge_ocr /tmp/regen.jsonl caie.db
python3 -m pipeline.text.audit_text caie.db

# 合并 —— combine 会重建表,质量标记必须在它之后写
python3 -m pipeline.db.combine caie.db 9709.db 9231.db 9618.db

# 文本规整:字形 → 换行 → 表格,顺序不能换
python3 -m pipeline.text.clean_encoding caie.db     # PUA / 控制字符 / 错映射的印地文·泰文字形
python3 -m pipeline.text.fix_newlines  caie.db      # 字面的 \n 还原成真换行(避开 \neq \nu)
python3 -m pipeline.text.html_tables   caie.db      # OCR 的 HTML 表格 → 竖线表格
python3 -m pipeline.text.flag_quality  caie.db
python3 -m pipeline.text.mark_partial  caie.db      # 必须在 flag_quality 之后:它会覆盖 q_quality
python3 pipeline/export/build_site.py

# 大纲 -> 标签 -> 先修图 -> 界面数据(顺序不能换)
python3 -m pipeline.tags.syllabus 697427-*.pdf 697357-*.pdf 697372-*.pdf   # -> syllabus.json
python3 -m pipeline.tags.eval_tags caie.db          # 先量,再改
python3 -m pipeline.tags.retag     caie.db --dry-run
python3 -m pipeline.tags.retag     caie.db
python3 -m pipeline.tags.prereq    syllabus.json caie.db                   # -> prereq.json
python3 attic/progress.py  init caie.db
python3 pipeline/export/build_site.py
```

要加新科目:写一个 `topics_<code>.py`(照抄 `topics_9618.py` 的结构:
`TOPICS` / `COMPONENT_TOPICS` / `COMPONENT_NAME` / `PAPER_TOTAL`),
其余流程不用动 —— CAIE 所有科目的卷子是同一套排版模板。

### 切分的几个坑(改代码前先读)

- **必须按 line 级切分**,不能按 block:行内公式会生成独立 block,其 y 坐标
  略高于所在行,block 级切分会把下一题的公式划进上一题。
- **分值必须按"行尾 + 右对齐到 x1≥530"双条件匹配**。只看行尾会把伪代码的
  数组下标 `Table[3]` 和追踪表的列头 `[10]` 算成分值。
- **CS 卷子比数学卷用满页面**:分值可以低到 y=785,`FOOTER_Y` 不能设 780。
- **Mark scheme 页面是横向旋转的**,PyMuPDF 坐标不可用,要用
  `pdftotext -layout` 解析表格文本流;总分所在的 Marks 列位置逐页漂移,
  必须按每页表头重新定位。
