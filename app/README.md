# app/

练习工作台:`python3 qb.py serve`(默认端口 8900)。服务端 `server.py`,作答记录
`store.py`(在 `paths.WORK`,不进 `data/`),可勾选的分码 `marking.py`。

## 页面(`web/`)

三个视图,顶栏切换考试(9709 9231 9618 · TMUA TSA BMAT)与视图,⌘K 或 `/` 按试卷代码跳题
(`s23 12 q5`、`m/j 23 p3`、主题编号或名字)。

| 视图 | 内容 | 文件 |
|---|---|---|
| 总览 | 一门考试的全部真题:一卷一行、一题一格,格宽与分值成正比,颜色是最近一次的得分;右栏是考纲主题的覆盖与得失 | `js/overview.js` |
| 练习 | 左栏当前一套(整卷、同主题或复盘列出的失分题),中间白板(题图为底,带答题区的版本优先),右栏按评分细则判分与详解;计时按考试时长与本卷总分折算每题预算 | `js/workspace.js` `js/marking.js` `js/explain.js` |
| 复盘 | 每道题最近一次判分没拿到的分,逐个分码列出;失分按分码种类(M / A / B …)与主题统计 | `js/review.js` |

共用的工具在 `js/core.js`,跳题在 `js/palette.js`,入口 `app.js`。书写工具栏与 iPad 笔具盘
取自 white-board(`tools.js`、`wb/`,见 `wb/README.md`)。字体 Newsreader 与 IBM Plex Mono
放在 `web/fonts/`(SIL OFL),离线可用。

设计的约定:纸白、墨黑,红色只用于分数(判分时给出的分、复盘里丢掉的分),蓝色是选中与焦点;
界面上的控件用图标,文字只用于题号、分值、细则与详解这些内容本身。

## 预览

`python3 app/preview.py OUT_DIR` 生成不需要服务端的静态副本:全部题目的索引、几套样卷的详情与
示例作答记录,作答存在浏览器本机。
