# 剑桥考试题干与评分细则全量审校

9618、9709、9231 三门考试的全部题目，逐题对照原卷重写题干与评分细则。方法见 `pipeline/text/fix_batches.py`：

- 每批 10 题，由一个子 agent 完成；
- 结果写到 `raw/text_fix/<考试>/out/batch_NN.json`；
- 通过 verify 后写回数据库，并记入 `pipeline/text/text_fixes.jsonl`。

## 任务量

| 考试 | 题数 | 批数 | 批次目录 |
|---|---|---|---|
| 9618 | 962 | 97 | `raw/text_fix/9618/` |
| 9709 | 2070 | 207 | `raw/text_fix/9709/` |
| 9231 | 1009 | 101 | `raw/text_fix/9231/` |
| 合计 | 4041 | 405 | |

9618 已在试跑中更正 8 题，不在上表内。批数以 `plan` 实际生成的文件为准。

## 按用量窗口分配

用量按 5 小时窗口轮换，从多伦多时间 2026-10-02 14:00 起重置。每个窗口处理 50 批。

按 9618、9709、9231 的顺序处理，前一门做完再做下一门。下表是预计的进度：

| 窗口（多伦多时间） | 批次 |
|---|---|
| 10-02 14:00 | 9618 第 1–50 批 |
| 10-02 19:00 | 9618 第 51–97 批，9709 第 1–3 批 |
| 10-03 00:00 | 9709 第 4–53 批 |
| 10-03 05:00 | 9709 第 54–103 批 |
| 10-03 10:00 | 9709 第 104–153 批 |
| 10-03 15:00 | 9709 第 154–203 批 |
| 10-03 20:00 | 9709 第 204–207 批，9231 第 1–46 批 |
| 10-04 01:00 | 9231 第 47–96 批 |
| 10-04 06:00 | 9231 第 97–101 批，完整汇报 |

第一个窗口结束后，按实际消耗调整每窗口的批数，并改写上表。

## 每个窗口的步骤

由定时任务在窗口开始时启动。

1. 预约下一轮：用 `send_later` 在 5 小时后发送同一条提示「按 docs/review-plan.md 执行全量审校的下一轮」。
2. 在 `/home/user/AL-questionbank` 下检查环境。若 `raw/text_fix/9618/` 不存在（容器已重建），先依次运行：
   - `git pull origin claude/great-fermi-4j6vt3`
   - `python3 sync.py pull`
   - 对三门考试分别运行 `python3 pipeline/text/fix_batches.py plan --syllabus <考试> --out <考试> --size 10 --skip-done`
3. 写回上一个窗口留下的结果，依次运行：
   - `python3 pipeline/text/fix_batches.py apply --write`
   - `python3 pipeline/text/split_parts.py --write`
   - `python3 pipeline/text/check_latex.py`，结果须为 0 题
   - `python3 pipeline/export/build_site.py`
   - `python3 sync.py push -m "题干与评分细则审校：截至 <考试> 第 N 批"`

   然后把 `pipeline/text/text_fixes.jsonl` 提交并推送到 `claude/great-fermi-4j6vt3`。
4. 分波派发。按上面的顺序找出还没有 `out/batch_NN.json` 的批次，每波取 10 个，每批用 Agent 工具派一个子 agent（general-purpose，model sonnet，后台运行），提示语：

   > 工作目录是 /home/user/AL-questionbank。用 Read 打开 raw/text_fix/<考试>/batch_NN.md，严格按其中的要求逐题完成：对照题图、PDF 文本层与评分细则原页重写题干和评分细则，把结果写到文件指定的 JSON 路径，并运行其中给出的 verify 命令直到全部通过。不要修改数据库或其他文件。最后只回复题数、改了题干的题数、改了评分细则的题数，以及 verify 中你判断为原卷本身如此、无法消除的报告。

   一波全部结束后执行第 3 步写回，再派下一波。以下任一情况出现就停止派发：
   - 本窗口已派满 50 批；
   - 全部批次已派完；
   - 窗口剩余时间不足一波。
5. 每波结束后，用一两句中文告诉用户：
   - 本波写入多少题；
   - 本窗口已完成多少批；
   - 三门考试各剩多少批。
6. 全部批次写回后：
   - 不再预约下一轮；
   - 用中文向用户做完整汇报，包括每门考试改动的题数、仍有问题的题，以及入学考试的抽查计划。
