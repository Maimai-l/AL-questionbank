# 数据库对接契约:schema、界面与 MCP

questions 表、`data.js` 与 practice.html、MCP server 三者相互咬合,单独修改
其中一项会导致另外两项静默出错。修改任何一项之前应先阅读本文。

## questions 表

CAIE 与入学考共用一张表。入学考行填不满的列留 NULL,不要为其新增数据表——
界面与 MCP 均按单表实现。

| 列 | 说明 |
|---|---|
| `id` | 主键。CAIE 形如 `9709-s23-12-q5`,入学考形如 `TSA-2019-S1-q6` 或 `TMUA-2021-P1-q7`。图片文件名与之逐字相同 |
| `syllabus` | 取值 `9709` `9231` `9618` `TMUA` `TSA` `BMAT` |
| `component` / `component_name` | 卷号与卷名 |
| `paper` `variant` `year` `month` `session` `series` | 出处信息 |
| `q` `parts` `marks` `marks_parts` | 题号、小问列表、总分、各小问分值。入学考的 marks 为 1,parts 为空 |
| `topic` `topic_name` `topic_all` `topic_confident` `topic_margin` `topic_source` `topic_note` | 主题标签。`topic_source` 取 `keyword`(打分得出)或 `model`(经复核) |
| `subtopic` `subtopic_name` | 子标签,用于 TMUA P2 的 Arg、Prf、Err |
| `question_text` / `question_latex` | 正文。latex 版优先,text 版为 pdftotext 兜底 |
| `ms_text` / `ms_latex` `mark_codes` `ms_total` `totals_agree` | 答案与评分信息 |
| `image` | 原题图的相对路径 |
| `qp_pdf` `ms_pdf` `qp_pages` | 溯源信息 |
| `has_diagram` | 题干本身是否含插图。注意其含义不是"是否有原题图"——现在每题都有原题图,若按图片是否存在计算,该列将恒为 1 而失去意义 |
| `q_quality` `ms_quality` | 取值 `ok` `partial` `missing` `degraded` |
| `answer` `qtype` `options` | 入学考专用:答案、题型(`mcq` 或 `short`)、选项字母的 JSON 数组 |

## 全文索引

```sql
CREATE VIRTUAL TABLE q_fts USING fts5(
  id UNINDEXED, question_text, ms_text, topic_name,
  tokenize='porter unicode61');
```

修改 questions 表后必须同步 FTS,否则搜索结果与库内容不一致。合库脚本的
做法是先删除该 syllabus 的 FTS 行再整体插回,较逐行更新更为可靠:

```sql
DELETE FROM q_fts WHERE id IN (SELECT id FROM questions WHERE syllabus IN (...));
INSERT INTO q_fts (id, question_text, ms_text, topic_name)
  SELECT id, question_text, ms_text, topic_name FROM questions WHERE syllabus IN (...);
```

收尾校验:`SELECT COUNT(*) FROM q_fts` 应等于 `SELECT COUNT(*) FROM questions`。

## data.js 与 practice.html

界面读取的是 `data.js` 而非数据库。`fetch()` 在 `file://` 协议下被禁用,
因此数据必须以 `window.QB = [...]` 的脚本形式注入:

```bash
cd qb && python3 pipeline/admissions_rebuild/export_web.py caie.db data.js
```

字段名经过缩写,因为整个库压缩为单个文件,每一字节都需解析:`s` 为
syllabus,`c` 为 component,`qt` 为正文,`ms` 为答案,`img` 为图片,`t` 与
`tn` 为主题码与主题名,`st` 与 `stn` 为子标签,`ans`、`qty`、`opt` 分别为
答案、题型与选项,`pt` 与 `mp` 为小问与分值。新增列时必须同时在 `FIELDS`
与映射中添加,遗漏其一界面即取不到数据。

界面以下行为与数据结构直接咬合,修改数据时应予保留:

- 存在 `img` 时才显示"原题图与文字版"切换,否则直接显示文字版;
- `qty` 为 `mcq` 且 `ans` 为单个字母时,渲染 `opt` 中的字母按钮,点击后自动
  判定对错、展开详解并记入进度;
- 正文中的 `![](相对路径)` 会被渲染为图片,图片根目录按
  `["", "../", "./images/", "../images/"]` 依次尝试;
- 进度存于 `localStorage`,键名为 `caie-progress-v1`。所有读写均包裹在
  try/catch 中,因为部分浏览器在 `file://` 下禁用存储,不应因此导致整页失效。

## 图片目录

| 目录 | 内容 | 命名规则 |
|---|---|---|
| `img9709/` `img9231/` `img9618/` | CAIE 逐题裁图 | 由 `crop.py` 决定 |
| `img_adm/` | 入学考逐题原页图与 `index.csv` | 文件名与题号 id 完全相同 |
| `img_tara/<考试>-<年份>/` | 入学考题干内引用的插图裁片 | 沿用 OCR 的原始命名 |

`img_adm/index.csv` 供使用者在本地建立索引,列依次为题号、图片名、考试、
卷、年份、场次、题序、主题码、主题名、子标签、答案、题型、选项、题干是否
含插图、是否有详解、原卷 PDF 路径。新增考试后需重新生成。

## MCP server

位于 `attic/mcp_server.py`,采用 stdio 传输,提供 10 个工具,涵盖搜索、取题、
主题列表、组卷、记录作答、弱项分析、下一课推荐、章节列表与取章节等。当前
未接入,移回项目根目录即可恢复。

`slim()` 负责将数据库行整理为供模型阅读的结构:优先提供 `ms_latex`,解析
JSON 列,并将 `image` 解析为绝对路径。新增 JSON 列时必须加入 `slim()` 的
解析列表——`options` 即是如此加入的——否则模型收到的将是字符串而非数组。

## 新增一门考试时需要改动的位置

1. `merge_*.py` 中的 `COMPONENT_NAMES` 条目与 id 命名规则;
2. `prereq.json` 中的 components 与 topic 边;
3. `export_web.py` 的 `FIELDS`,若引入了新列;
4. `mcp_server.py` 的 `slim()`,若引入了新的 JSON 列;
5. `qb/docs/使用说明.md` 中的数量表;
6. 图片目录与 `index.csv`。
