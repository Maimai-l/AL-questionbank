# 剑桥考试题干与评分细则全量审校

> 本计划已于 2026-10-02 全部完成。现状与待办见 `docs/status.md`。

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

## 运行方式

从 2026-10-02 11:20（多伦多时间）起连续运行，不按窗口限量，直到额度用尽或订阅结束（10-03 上午 8 点左右）。额度用尽后由用户使用 reset，随后从未完成的批次接着做，做到哪里算哪里。

- 始终保持 10 个子 agent 同时运行，完成一个就按「处理顺序」补派下一个；
- 每完成 10 批写回一次（见下文第 3 步）。

## 定时任务

用量窗口在多伦多时间 17:30、22:30、3:30 重置（2026-10-02 起）。保留三个一次性定时任务，作为中断后的续做入口：10-02 17:32、10-02 22:32、10-03 03:32，提示均为「按 docs/review-plan.md 执行全量审校的下一轮」。触发时若子 agent 仍在运行，不重复派发；若已全部停止，按下文步骤续做。

## 额度提醒

周额度用尽后，这个账号下的会话与定时任务都无法运行，因此提醒只能在用尽之前，或在额度恢复后的第一轮发出。提醒用 PushNotification 发送，内容写明需要使用 reset，以及审校停在哪个卷别的第几批。以下情况发送提醒：

- 子 agent 返回用量上限或额度相关的错误；
- 系统消息提示接近或达到用量上限；
- 续做时发现有已派出但没有结果文件的批次，说明运行中途停止。

## 续做与写回的步骤

1. 在 `/home/user/AL-questionbank` 下检查环境。若 `raw/text_fix/9618-p2/` 不存在（容器已重建），先依次运行：
   - `git pull origin claude/great-fermi-4j6vt3`
   - `python3 sync.py pull`
   - 按「处理顺序」表对每个卷别运行 `python3 pipeline/text/fix_batches.py plan --syllabus <考试> --component <卷别> --out <考试>-p<卷别> --size 10 --skip-done`
2. 检查运行是否中途停止（见「额度提醒」），需要时发送提醒。
3. 写回已有的结果，依次运行：
   - `python3 pipeline/text/fix_batches.py apply --write`
   - `python3 pipeline/text/split_parts.py --write`
   - `python3 pipeline/text/check_latex.py`，结果须为 0 题
   - `python3 pipeline/export/build_site.py`
   - `python3 sync.py push -m "题干与评分细则审校：截至 <考试> 卷 <卷别> 第 N 批"`

   然后把 `pipeline/text/text_fixes.jsonl` 提交并推送到 `claude/great-fermi-4j6vt3`。
4. 连续派发。按「处理顺序」找出还没有 `out/batch_NN.json` 的批次，保持 10 个同时运行，每批用 Agent 工具派一个子 agent（general-purpose，model sonnet，后台运行），提示语：

   > 工作目录是 /home/user/AL-questionbank。用 Read 打开 raw/text_fix/<考试>-p<卷别>/batch_NN.md，严格按其中的要求逐题完成：对照题图、PDF 文本层与评分细则原页重写题干和评分细则，把结果写到文件指定的 JSON 路径，并运行其中给出的 verify 命令直到全部通过。不要修改数据库或其他文件。最后只回复题数、改了题干的题数、改了评分细则的题数，以及 verify 中你判断为原卷本身如此、无法消除的报告。

   每完成 10 批执行一次第 3 步写回。全部批次派完后停止派发。
5. 每次写回后，用一两句中文告诉用户：
   - 本次写入多少题；
   - 累计完成多少批；
   - 当前卷别与剩余批数。
6. 全部批次写回后：
   - 删除剩余的「全量审校」定时任务；
   - 用中文向用户做完整汇报，包括每门考试改动的题数、仍有问题的题，以及入学考试的抽查计划。
