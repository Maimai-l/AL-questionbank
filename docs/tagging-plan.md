# 标签重做:现状、实测与下一步

## 之前的做法

1. 手写关键词表(`pipeline/tags/tag.py`、`topics_9231.py`、`topics_9618.py`,经 `tag_any.py`)
   按题干加评分细则计分,只在该卷考纲允许的主题中比较;第一与第二的分差记为 `topic_margin`。
2. 大纲 TF-IDF(`topic_model.py`):以官方学习要求原文为向量。单独用 62.6%,前三覆盖 95%。
3. `retag.py`:分差 ≥ 2 用关键词,≤ 1 用两者相加。最弱 4 组(9709 P4、9231 P3、
   9618 P2/P4)共 768 题由模型逐题读过,`topic_source='model'`。
4. 入学考:TMUA 用考纲 TF-IDF,TSA/BMAT 按题干句式分 PS/CT(`tag_admissions.py`)。

已知准确率:最弱组 78%;按科目抽 40 题,9231 92.5%、9709 85%、9618 75%。其余未测。

## 2026-09-29 实测(9709 P1,规则标签、从未被模型读过的题)

每批 12 题,文字输入(题干 LaTeX 截 1500 字 + 评分细则截 800 字 + 该卷主题表)。

| 子 agent | 模型 | 批数 | subagent_tokens | 每题 |
|---|---|---:|---:|---:|
| general-purpose | 默认 | 1 | 54,863 | 4,572 |
| general-purpose | Haiku | 1 | 52,828 | 4,402 |
| general-purpose | Sonnet | 1 | 54,403 | 4,534 |
| general-purpose | Sonnet | 3(依次读) | 73,415 | 2,039 |

- 固定开销约 4.5 万 token(系统提示 + 全部工具定义,含几十个 GitHub MCP 工具),
  每多一批约 9,500。
- 36 题中 32 题与规则标签一致;不一致的 4 题里 2 题规则明显错(面积题标成弧度制、
  三角图像题标成微分),2 题是两个小问各考一个主题。
- 同一道多主题题(9709_w21_13_q03),单批两次给 1.1,三批那次给 1.7:主标签在多主题题上
  不稳定,应改为按小问标注。

## 下一步(新会话)

1. `.claude/agents/tagger.md` 定义了只带 Read 工具、默认 Sonnet 的子 agent,新会话才会加载。
   先用它重跑同样 12 题,量出固定开销降了多少。
2. 写 `pipeline/tags/tag_batches.py plan|apply`:
   - plan:从 `data/caie.db` 取题,按卷分批(每批 12 题),写批次文件与主题表;
     文字质量不是 ok 或含图的题附上 `data/img*/` 路径,让子 agent 读图。
   - 输出格式改为按小问:`{"id", "parts": [{"part": "a", "topic": "1.7"}], "topic": 主标签}`,
     主标签取分值最多的小问。
   - apply:校验 id 集合、主题码属于该卷考纲、TSA 每卷 25 PS + 25 CT,
     通过后写入 `pipeline/tags/retag_model.json`,再由脚本写库。
3. 一个子 agent 依次处理 8–10 批,摊薄固定开销;主进程统一落盘。
4. 先做约 200 题的测量(每个 component 抽约 10 题),按各组与规则标签的不一致率决定重标范围。
