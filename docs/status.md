# 数据现状与待办(2026-10-03)

## 已完成

剑桥三门考试(9618、9709、9231)的题干与评分细则已全部对照原卷核对:

| 工作 | 范围 | 结果 |
|---|---|---|
| 全量审校 | 409 批,4041 题 | 题干改 3688 题,评分细则改 3880 题 |
| 图示复核(重点) | 492 题:全部评分细则草图与带近似读数的题干图 | 211 题有更正 |
| 图示复核(其余) | 476 题:其余题干图示 | 41 题有更正 |
| 原卷错误更正 | 92 题:上一轮按原页保留的印刷错误 | 73 处改为正确写法 |

规则以正确为准:原卷印错的地方改为正确写法,依据写在 `pipeline/text/text_fixes.jsonl` 各行的 `why`
里(见 `pipeline/text/fix_batches.py` 的「原卷本身的错误」一节)。更正全部记在 `text_fixes.jsonl`,
写回数据库后已同步到 data 分支。

## 待办

按优先级排列。用户安排(2026-10-03):BMAT 不刷题,暂不处理(第 1、3 项中的 BMAT 部分);TMUA 留到以后。

### 0. 9618 详解

970 题中 968 题有详解(2026-10-03):卷 1–3 的 874 题已对照审校后的评分细则复核(`--recheck`),
卷 4 新写 94 题,小问标签与 `part_data` 全部一致。

- 缺 2 题:9618_w25_41_q03、9618_w25_42_q01(卷 4 批次 046 没有交回)。补做:
  `explain_batches.py plan --out DIR --syllabus 9618 --components 4 --skip-done`,交给 explainer,再 `apply`、`write --write`。
- 卷 4 原卷评分细则有几处示例代码本身有错,详解按正确写法写并在 pitfalls 中说明,评分细则文本未改:
  s23_42_q01 c 冒泡循环上界、s22_43_q03 c 回绕条件、s22_41_q03 b NumberItems 应为 BYREF、
  s21_43_q01 d(i) addNode 顺序、s21_42/43_q03 b "4 elements"、s24_43_q01 冒泡与二分查找、
  s24_42_q03 c(i) 插入排序、w21_41 q03 缩进、w22_41 q01/q02 循环范围;
  w21_41_q02、w21_42_q02 的 (e) 细则分值合计 9,题面为 8。
- 9709、9231 不做详解(用户决定)。`raw/explain_9709`、`raw/explain_9231` 各有 1 批试做,未写入。

### 1. BMAT 共用材料缺失(系统性问题)

原卷中几道题共用的背景材料(「Questions 8 to 11 refer to the following information」之后的文章与数据表)
只存在组内第一题的题干里,同组其他题缺这段材料,单看一题无法作答。抽查的 105 道 BMAT 题中有 15 道属于此类。

做法:在 `merge_admissions.py`(或单独的脚本)中按「Questions X to Y refer to」找到每组的说明段与材料,
复制到同组各题题干的开头,重新入库。只改代码,不需要子 agent。TSA 若有同类分组,一并处理。

### 2. TMUA 错误率高,需要整体核对

每份 TMUA 卷抽 2 题,36 题中 8 题有错(约 22%);TSA 抽 32 题只有 1 题有错。TMUA 的错误有:
- 漏掉题干开头的句子:TMUA-2023-P1-q12、TMUA-2023-P2-q3;
- 漏掉方程标号 (*):TMUA-2023-P2-q6;
- 选项中的 ≤ 写成 <:TMUA-2020-P2-q1;
- 选项没有拆进 option_texts:TMUA-2019-P2-q18(缺 H)、TMUA-2020-P1-q8(B–F 为空);
- 题干句子重复:TMUA-2020-P2-q18;字符错误:TMUA-2018-P1-q11。

TMUA 共 360 题,数学内容直接影响作答,建议按剑桥三科的做法逐题对照原卷重写(约 36 批)。
已改:TMUA-2016-P1-q1 选项 A 的 `\angle` 识别错误(记在 `text_fixes.json`,数据库已改)。

### 3. 应用抽查中改好的题

`pipeline/admissions_rebuild/spot_check_results.json` 是入学考抽查的结果(178 题,34 题有错,`run` 字段区分两次抽样)。
有错的题已经写出改正后的完整题干(`text`)与选项(`options`)。做完第 1 项后,把其中仍然需要的改正
写进 `pipeline/admissions_rebuild/text_fixes.json`(格式见该文件的 `_说明`),再运行 `merge_admissions.py`。

除共用材料外,其余错误是:
- 图中数值没有写进题干(diagram):BMAT-2006-S1-q21、2011-S1-q8、2014-S1-q34、2019-S1-q20、2020-S1-q26、2020-S1-q28;
- 混入其他题的内容或页眉(extra):BMAT-2011-S1-q7、q34,2012-S1-q7,2014-S1-q5;
- 选项开头的单词 A 被当成选项字母:BMAT-2020-S1-q9;
- 字词错误:BMAT-2013-S1-q12。

### 4. 再次抽查的方法

```
python3 pipeline/admissions_rebuild/spot_check.py plan --exam TMUA --per-paper 2 --run NAME --seed 7
python3 pipeline/admissions_rebuild/spot_check.py report --run NAME
```

每批交给一个 general-purpose 子 agent。换一个 `--seed` 才会抽到不同的题。

### 5. 需要人看一眼的更正

- 9618_w24_23_q04:评分细则备选代码原本有逻辑错误,子 agent 改了代码结构(内层循环前先置 FALSE、删去 ELSE)。
- 9709_w22_31_q05:评分细则中未定义的 `v` 改成了 `u²/w`,属于记号更正。
- 9709_s26_52_q04:评分细则保留了原页的 `(M1`、`B1)` 括号写法,与其他题去掉括号的做法不一致。

## 继续工作的步骤

```
python3 sync.py pull                                   # 取回 data/
python3 pipeline/text/fix_batches.py plan ...          # 生成批次,交给子 agent
python3 pipeline/text/fix_batches.py verify <结果>      # 子 agent 自查
python3 pipeline/text/fix_batches.py apply --write     # 写回,记入 text_fixes.jsonl
python3 pipeline/text/split_parts.py --write
python3 pipeline/text/check_latex.py
python3 pipeline/export/build_site.py
python3 sync.py push -m "<说明>"
```

然后提交 `pipeline/text/text_fixes.jsonl`。

## 不在仓库里的内容

云端沙盒中还有 `raw/`(约 1.7 GB)与 `exports/`(约 460 MB),按约定不进仓库,容器回收后会消失:

| 内容 | 位置 | 丢失后的影响 |
|---|---|---|
| 原卷与评分细则 PDF | `raw/pdf`、`raw/ms`、`raw/bank` | 无:已复制到 data 分支的 `papers/` |
| 入学考逐页 OCR | `raw/bank_ocr`(574 MB) | 只有从头重新切分入学考时才需要,可用 `ocr_bank.py` 重新识别(要调用 OCR 接口) |
| 审校批次与子 agent 结果 | `raw/text_fix`、`raw/latex_fix` 等 | 无:通过检查的更正都记在 `text_fixes.jsonl`、`ms_fixes.jsonl` |
| 9618 详解批次 | `raw/explain_9618` | 无:结果已写入数据库(data 分支);重做时重新生成批次 |
| 入学考抽查批次 | `raw/adm_check` | 无:结果存在 `spot_check_results.json` |
| 导出 ZIP | `exports/` | 无:由 `pipeline/export/` 的脚本重新生成 |
