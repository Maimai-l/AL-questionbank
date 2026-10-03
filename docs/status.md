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

按优先级排列。

### 1. BMAT 共用材料缺失(系统性问题)

原卷中几道题共用的背景材料(「Questions 8 to 11 refer to the following information」之后的文章与数据表)
只存在组内第一题的题干里,同组其他题缺这段材料,单看一题无法作答。抽查的 105 道 BMAT 题中有 15 道属于此类。

做法:在 `merge_admissions.py`(或单独的脚本)中按「Questions X to Y refer to」找到每组的说明段与材料,
复制到同组各题题干的开头,重新入库。只改代码,不需要子 agent。TSA 若有同类分组,一并处理。

### 2. 应用抽查中改好的 25 题

`pipeline/admissions_rebuild/spot_check_results.json` 是入学考抽查的结果(110 题,25 题有错)。
有错的题已经写出改正后的完整题干(`text`)与选项(`options`)。做完第 1 项后,把其中仍然需要的改正
写进 `pipeline/admissions_rebuild/text_fixes.json`(格式见该文件的 `_说明`),再运行 `merge_admissions.py`。

除共用材料外,其余错误是:
- 图中数值没有写进题干(diagram):BMAT-2006-S1-q21、2011-S1-q8、2014-S1-q34、2019-S1-q20、2020-S1-q26、2020-S1-q28;
- 混入其他题的内容或页眉(extra):BMAT-2011-S1-q7、q34,2012-S1-q7,2014-S1-q5;
- 选项开头的单词 A 被当成选项字母:BMAT-2020-S1-q9;
- 字词错误:BMAT-2013-S1-q12。

### 3. 入学考抽查未做完

已抽 110 题(BMAT 105、TSA 5),TMUA 未抽。继续时:

```
python3 pipeline/admissions_rebuild/spot_check.py plan --per-paper 2   # 重新抽样会覆盖 raw/adm_check/
python3 pipeline/admissions_rebuild/spot_check.py report
```

每批交给一个 general-purpose 子 agent;按 `report` 的结果决定哪些试卷整份重新转录(`page_batches.py`)。

### 4. 需要人看一眼的更正

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
