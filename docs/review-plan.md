# 剑桥考试题干与评分细则全量审校

9618、9709、9231 三门考试的全部题目，逐题对照原卷重写题干与评分细则。方法见 `pipeline/text/fix_batches.py`：

- 每批 10 题，由一个子 agent 完成；
- 批次按卷别生成，目录为 `raw/text_fix/<考试>-p<卷别>/`，例如 `raw/text_fix/9231-p2/`；
- 结果写到该目录下的 `out/batch_NN.json`；
- 通过 verify 后写回数据库，并记入 `pipeline/text/text_fixes.jsonl`。

`raw/text_fix/9618/`、`9709/`、`9231/` 是按考试生成的旧批次，不再使用。

## 处理顺序

按下表从上到下处理，一个卷别做完再做下一个。

| 序号 | 考试 | 卷别 | 批次目录 | 批数 |
|---|---|---|---|---|
| 1 | 9618 | 卷 2 Fundamental Problem-solving and Programming Skills | `raw/text_fix/9618-p2/` | 25 |
| 2 | 9618 | 卷 3 Advanced Theory | `raw/text_fix/9618-p3/` | 36 |
| 3 | 9618 | 卷 4 Practical | `raw/text_fix/9618-p4/` | 10 |
| 4 | 9618 | 卷 1 Theory Fundamentals | `raw/text_fix/9618-p1/` | 27 |
| 5 | 9231 | 卷 2 Further Pure Mathematics 2 | `raw/text_fix/9231-p2/` | 29 |
| 6 | 9231 | 卷 3 Further Mechanics | `raw/text_fix/9231-p3/` | 25 |
| 7 | 9231 | 卷 4 Further Probability & Statistics | `raw/text_fix/9231-p4/` | 22 |
| 8 | 9709 | 卷 3 Pure Mathematics 3 | `raw/text_fix/9709-p3/` | 45 |
| 9 | 9709 | 卷 4 Mechanics | `raw/text_fix/9709-p4/` | 30 |
| 10 | 9709 | 卷 5 Probability & Statistics 1 | `raw/text_fix/9709-p5/` | 28 |
| 11 | 9709 | 卷 6 Probability & Statistics 2 | `raw/text_fix/9709-p6/` | 29 |
| 12 | 9709 | 卷 1 Pure Mathematics 1 | `raw/text_fix/9709-p1/` | 46 |
| 13 | 9231 | 卷 1 Further Pure Mathematics 1 | `raw/text_fix/9231-p1/` | 26 |
| 14 | 9709 | 卷 2 Pure Mathematics 2 | `raw/text_fix/9709-p2/` | 31 |
| | | | 合计 | 409 |

排序依据：

- 9618 最先；
- 9231 卷 2（Further Pure Mathematics 2）、卷 3（Further Mechanics）、卷 4（Further Probability & Statistics）紧随 9618；
- 9709 卷 3 至卷 6 其次；
- 9709 卷 1 与 9231 卷 1 不再需要，放在最后；
- 9709 卷 2 没有考生，放在最末。

## 按用量窗口分配

用量按 5 小时窗口轮换，从多伦多时间 2026-10-02 14:00 起重置。每个窗口处理 50 批。下表是预计的进度：

| 窗口（多伦多时间） | 批次 |
|---|---|
| 10-02 14:00 | 9618 卷 2 第 1–25 批，9618 卷 3 第 1–25 批 |
| 10-02 19:00 | 9618 卷 3 第 26–36 批，9618 卷 4 第 1–10 批，9618 卷 1 第 1–27 批，9231 卷 2 第 1–2 批 |
| 10-03 00:00 | 9231 卷 2 第 3–29 批，9231 卷 3 第 1–23 批 |
| 10-03 05:00 | 9231 卷 3 第 24–25 批，9231 卷 4 第 1–22 批，9709 卷 3 第 1–26 批 |
| 10-03 10:00 | 9709 卷 3 第 27–45 批，9709 卷 4 第 1–30 批，9709 卷 5 第 1 批 |
| 10-03 15:00 | 9709 卷 5 第 2–28 批，9709 卷 6 第 1–23 批 |
| 10-03 20:00 | 9709 卷 6 第 24–29 批，9709 卷 1 第 1–44 批 |
| 10-04 01:00 | 9709 卷 1 第 45–46 批，9231 卷 1 第 1–26 批，9709 卷 2 第 1–22 批 |
| 10-04 06:00 | 9709 卷 2 第 23–31 批，然后做完整汇报 |

第一个窗口结束后，按实际消耗调整每窗口的批数，并改写上表。

## 定时任务

每个窗口开始后 2 分钟各有一个一次性定时任务（另备两轮，供进度落后时使用），名称为「全量审校：第 N 轮」，提示均为「按 docs/review-plan.md 执行全量审校的下一轮」。各轮互不依赖：某一轮因额度用尽没有运行，后面的轮次仍按时启动，从未完成的批次接着做。

全部批次写回后，删除剩余的「全量审校」定时任务。

## 额度提醒

周额度用尽后，这个账号下的会话与定时任务都无法运行，因此提醒只能在用尽之前，或在额度恢复后的第一轮发出。提醒用 PushNotification 发送，内容写明需要使用 reset，以及审校停在哪个卷别的第几批。以下情况发送提醒：

- 子 agent 返回用量上限或额度相关的错误；
- 系统消息提示接近或达到用量上限；
- 窗口开始时发现上一窗口派出的批次没有全部完成，说明上一窗口中途停止。

## 每个窗口的步骤

1. 在 `/home/user/AL-questionbank` 下检查环境。若 `raw/text_fix/9618-p2/` 不存在（容器已重建），先依次运行：
   - `git pull origin claude/great-fermi-4j6vt3`
   - `python3 sync.py pull`
   - 按「处理顺序」表对每个卷别运行 `python3 pipeline/text/fix_batches.py plan --syllabus <考试> --component <卷别> --out <考试>-p<卷别> --size 10 --skip-done`
2. 检查上一窗口是否中途停止（见「额度提醒」），需要时发送提醒。
3. 写回上一个窗口留下的结果，依次运行：
   - `python3 pipeline/text/fix_batches.py apply --write`
   - `python3 pipeline/text/split_parts.py --write`
   - `python3 pipeline/text/check_latex.py`，结果须为 0 题
   - `python3 pipeline/export/build_site.py`
   - `python3 sync.py push -m "题干与评分细则审校：截至 <考试> 卷 <卷别> 第 N 批"`

   然后把 `pipeline/text/text_fixes.jsonl` 提交并推送到 `claude/great-fermi-4j6vt3`。
4. 分波派发。按「处理顺序」找出还没有 `out/batch_NN.json` 的批次，每波取 10 个，每批用 Agent 工具派一个子 agent（general-purpose，model sonnet，后台运行），提示语：

   > 工作目录是 /home/user/AL-questionbank。用 Read 打开 raw/text_fix/<考试>-p<卷别>/batch_NN.md，严格按其中的要求逐题完成：对照题图、PDF 文本层与评分细则原页重写题干和评分细则，把结果写到文件指定的 JSON 路径，并运行其中给出的 verify 命令直到全部通过。不要修改数据库或其他文件。最后只回复题数、改了题干的题数、改了评分细则的题数，以及 verify 中你判断为原卷本身如此、无法消除的报告。

   一波全部结束后执行第 3 步写回，再派下一波。以下任一情况出现就停止派发：
   - 本窗口已派满 50 批；
   - 全部批次已派完；
   - 窗口剩余时间不足一波。
5. 每波结束后，用一两句中文告诉用户：
   - 本波写入多少题；
   - 本窗口已完成多少批；
   - 当前卷别与剩余批数。
6. 全部批次写回后：
   - 删除剩余的「全量审校」定时任务；
   - 用中文向用户做完整汇报，包括每门考试改动的题数、仍有问题的题，以及入学考试的抽查计划。
