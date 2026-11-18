# 数据现状与待办(2026-11-14)

## Edexcel IAL 物理教材(2026-11-18 加入)

Pearson Edexcel International A Level Physics(WPH)Student Book 1(`edx_ial_phy1`,14 章)与 Book 2(`edx_ial_phy2`,
15 章)已 OCR 成带插图、公式为 LaTeX 的 Markdown,进了教材页与 chapters 表(syllabus 为 WPH,主题等考纲字段为空)。
题库里没有 Edexcel 的考纲和试卷。做法与已知的识别问题见 `docs/pipeline.md` 的「Edexcel 物理教材(2026-11)」;
教材页 KaTeX 有 8 处公式无法渲染，未改。

## 9702 物理(2026-11-14 加入)

卷 1、2、4、5,2021–2026 年 168 份试卷、2482 题(卷 1 选择题 1680 题、卷 2 281 题、卷 4 437 题、卷 5 84 题),
题图、原卷 PDF、评分细则、主题(按节)与按小问拆分的数据都已入库;物理教材 26 章已入教材页。做法见
`docs/pipeline.md` 的「新增 9702 物理」。OCR 已做:2423 题题干与 759 题评分细则为 LaTeX(含下面审校写入的)。下面几项还没做完:

- **对照原卷审校只做了 100 题(2026-11-14)。** 用 `fix_batches.py`,Haiku 子 agent,每批 20 题(批次大小实验见
  `docs/pipeline.md`):批次实验的 40 题与 `raw/text_fix/9702-r1/` 的 3 批 60 题，都是卷 2/4/5 中题干只有文本层
  (partial)的题。9702 的审校结果写入 `question_latex`、`ms_latex`,文本层留在 `question_text`、`ms_text`。
  还剩：卷 2/4/5 的 27 道 partial 题(约 2 批)与其余 675 题(约 34 批);卷 1 的 22 道 partial 选择题。
  子 agent 报告的「原卷印错」要逐条核对原页：第 1 批报告的 3 处只有 9702_m26_52_q02 的 261²(应为 261^n)属实，
  另两处是 OCR 读坏。
- **22 题公式 KaTeX 无法渲染**(`check_latex.py`),用 `latex_fix_batches.py` 对照原页更正(约 3 批)。
- 2021 年卷 4 有 14 道旧考纲题(通信、电子学),主题置空。
- **主题准确率约 86%。** 人工抽查 100 题 86 题节号正确，错的多是两节交界的题(驻波与波、功与动量、电路与电流)。
  需要更准时用 `tag_batches.py` 交给 tagger 子 agent 复核。
- `9702_s26_ms_21` 三个站点都没有，该卷 5 题没有评分细则。`9702_s26_52_q01`、`9702_s26_54_q01` 的评分细则仍是
  未分行的文本层，审校时一并重写。其余卷 2/4/5 题的评分码合计都与题面分值一致(`check_scheme_rows`)。
- 卷 2、4 的任务类型(`part_data` 的 task)沿用数学的分类(find / explain / prove / sketch / other)。

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

### 1. 入学考已归档

TMUA、TSA、BMAT 于 2026-11-14 从题库移出(用户决定不再使用),原来的第 1–4 项(BMAT 共用材料、TMUA 整体核对、
应用抽查改正、再次抽查)不再处理，原文见 `attic/admissions/docs/` 与 `archive-admissions` 分支。

### 2. 需要人看一眼的更正

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
