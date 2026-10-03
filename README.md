# AL Question Bank

离线题库,共 5937 题:

| 科目 | 题数 | 卷子 | 年份 | 核对情况 |
|---|---:|---:|---|---|
| 9709 Mathematics | 2070 | 252 | 2021–2026 | 题干、评分细则与图示已逐题对照原卷 |
| 9231 Further Mathematics | 1009 | 144 | 2021–2026 | 同上 |
| 9618 Computer Science | 970 | 130 | 2021–2026 | 同上;卷 1–3 有分小问详解 |
| TMUA | 360 | 18 | 2016–2023 | 只做过结构检查与抽查,抽查错误率约 22% |
| TSA Section 1 | 800 | 16 | 2008–2023 | 只做过结构检查与抽查,抽查错误率约 3% |
| BMAT Section 1 | 728 | 21 | 2003–2023 | 只做过结构检查与抽查,共用材料缺失 |

另有 81 章教材正文(Markdown),以及官方大纲的解析结果。数据现状与待办见
[docs/status.md](docs/status.md)。

## 仓库的组织方式

仓库分为两个分支:

| 分支 | 内容 | 历史 |
|---|---|---|
| `main` | 代码、页面源文件、文档、大纲与先修关系 | 正常累积 |
| `data` | `caie.db`、题图、教材章节、可直接打开的刷题页 | 始终只有一个提交,每次更新覆盖上一版 |

`data` 分支检出在 `data/` 目录下(git worktree),`main` 不跟踪它。这样重新生成
数据库或题图时,仓库历史不会增长。详细说明见 [docs/data-sync.md](docs/data-sync.md)。

流水线在云端沙盒中运行,结果推送到 `data` 分支;本地只需取回。

## 本地使用

首次:

```bash
git clone --single-branch --branch main https://github.com/Maimai-l/AL-questionbank.git
cd AL-questionbank
python3 sync.py pull
```

之后每次需要最新数据时:

```bash
python3 sync.py pull
```

打开 `data/practice.html` 刷题,打开 `data/textbook.html` 看教材。两个页面均可离线使用。

`data/` 在本地是只读副本。`sync.py pull` 会覆盖其中的改动,有未提交改动时会先拒绝执行。
题库有更新时,`sync.py pull` 随后运行自动流程,把章节包写到 `exports/chapters/`。

## 数据管理页

```bash
python3 manage.py                                     # 查询、题组、导出、批量生成,局域网可访问
python3 manage.py window                              # 同上,在独立窗口中打开(需要 pip install pywebview)
python3 manage.py auto                                # 题库更新后运行自动流程(题库没变时不运行)
```

macOS 上可以在访达中双击 `manage.command` 打开窗口。

## 命令行

```bash
python3 qb.py stats                                   # 各科题数与数据位置
python3 qb.py find --syllabus 9709 --topic 1.7 --marks 6-8
python3 qb.py show 9231_s23_31_q04 --full
python3 qb.py paper --syllabus 9618 --component 3 --exclude-year 2025
python3 qb.py chapters                                # 教材章节与主题码的对应情况
```

任何 `qb.py` 命令加 `--json` 可输出机器可读格式。

## 目录

```text
qb.py                 查询、组卷、统计;qb.py serve 启动刷题服务(app/)
manage.py             数据管理页入口(manager/)
sync.py               取回与推送 data/
app/                  刷题服务:页面、作答记录、手写批改
manager/              数据管理页:查询、题组、导出、批量生成、白板
lib/                  paths.py(全部路径在此解析)、db.py(数据库连接)
pipeline/
  fetch/              下载试卷
  split/              CAIE 按题号切分题目与评分细则,逐题裁图
  ocr/                OCR 与结果合并、修补
  text/               正文清洗与质量标记
  tags/               大纲解析、主题标注、先修关系
  books/              教材分页、分章、章节入库
  db/                 单科建库与合库
  admissions_rebuild/ TMUA / TSA / BMAT 选择题的完整流程
  export/             生成页面数据与各类分发 ZIP
assets/               页面源文件 practice.html、textbook.html 与离线 KaTeX
attic/                暂不使用的 MCP server、做题记录模块与已被取代的脚本
docs/                 文档
.claude/agents/       流水线用的子 agent 定义(explainer、tagger、termwriter、transcriber)
syllabus.json         官方大纲解析结果
prereq.json           主题先修关系
data/                 data 分支的 worktree(不属于 main)
```

## 文档

- [docs/status.md](docs/status.md):数据现状与待办,接手时先读
- [docs/pipeline.md](docs/pipeline.md):流水线各阶段、执行顺序与脚本索引
- [docs/data-sync.md](docs/data-sync.md):`data` 分支的结构与同步方式
- [docs/network.md](docs/network.md):流水线需要访问的站点
- [docs/INTEGRATION.md](docs/INTEGRATION.md):数据库 schema 与对接契约
- [docs/reference.md](docs/reference.md):CAIE 三科的设计与数据质量记录
- [docs/admissions/题库说明.md](docs/admissions/题库说明.md):入学考题库的来源与结构

## 版权

试卷与评分细则版权归 UCLES / Cambridge International 与 UAT-UK,教材版权归原出版方。
仅供个人使用,不得公开分发。
