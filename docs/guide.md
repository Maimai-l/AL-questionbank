# 使用手册

本手册写给题库的使用者:怎样取得和更新代码与数据,怎样使用各个页面和命令,
个人数据存在哪里,以及怎样维护一个稳定分支。流水线(重新生成数据)的细节见
[pipeline.md](pipeline.md),数据现状与待办见 [status.md](status.md)。

## 1. 文件放在哪里

| 位置 | 内容 | 来源 | 是否要自己备份 |
|---|---|---|---|
| 仓库目录(`main` 分支) | 代码、页面源文件、文档、大纲 | `git pull` | 不用,GitHub 上有 |
| `data/` | 数据库 `caie.db`、题图、原卷 PDF、教材、可直接打开的页面 | `python3 sync.py pull` | 不用,GitHub 的 `data` 分支上有 |
| 仓库旁边的 `qb-work/` | 作答记录、手写白板、题组、批量生成的结果 | 使用时自动生成 | **要**,只在本机 |
| 仓库旁边的 `exports/` | 章节包等导出的 ZIP | `sync.py pull` 后自动生成,或手动导出 | 不用,可以重新生成 |

「仓库旁边」指仓库目录的上一级。例如仓库在 `~/alevel/AL-questionbank`,
个人数据就在 `~/alevel/qb-work`,导出在 `~/alevel/exports`。
需要放到别处时,设置环境变量 `QB_WORK`、`CAIE_EXPORTS`(见 `lib/paths.py`)。

`data/` 是 `data` 分支的 git worktree。这个分支只保留一个提交,每次更新都整体替换,
所以 `data/` 在本地只读:不要在里面改文件,改了会在下次取回时被拒绝或覆盖。

## 2. 第一次安装

```bash
git clone --single-branch --branch main https://github.com/Maimai-l/AL-questionbank.git
cd AL-questionbank
python3 sync.py pull
```

需要 Python 3.8 以上。查询、刷题页和数据管理页只用标准库;
`python3 manage.py window` 另需 `pip install pywebview`;
生成题目卷 PDF 等功能需要 `pip install pymupdf`。

## 3. 日常更新

| 命令 | 作用 |
|---|---|
| `python3 sync.py update` | 更新代码(当前分支,只快进)并取回最新数据。日常只用这一条 |
| `python3 sync.py pull` | 只取回最新数据 |
| `python3 sync.py status` | 查看 `data/` 当前的版本与有没有本地改动 |

可加的选项:

| 选项 | 用于 | 作用 |
|---|---|---|
| `--no-auto` | `update`、`pull` | 取回后不运行自动流程(不生成章节包) |
| `--force` | `update`、`pull` | 覆盖 `data/` 里的本地改动 |
| `--gc` | `pull` | 取回后清理旧版本占用的磁盘 |
| `--ref NAME` | `update`、`pull` | 取回标签 `data-NAME` 的那一版数据,而不是最新版(见第 7 节) |

取回数据后,若题库有变化,会自动运行 `python3 manage.py auto`,把章节包写到 `exports/`。
第一次运行或数据大改后会慢一些。自动流程出错不影响已取回的数据,之后运行
`python3 manage.py auto` 重试即可。

确认数据是否最新:

```bash
git -C data log -1 --format='%h %s' && python3 qb.py stats
```

第一行是 `data` 分支的提交号与说明,与 GitHub 上 `data` 分支一致即为最新。

## 4. 使用

### 静态页面(不需要启动服务)

| 文件 | 内容 |
|---|---|
| `data/practice.html` | 刷题页:按科目、试卷、主题筛题,看题干、评分细则与详解 |
| `data/textbook.html` | 教材页:81 章教材正文,与题目按主题关联 |
| `data/concepts/9618/index.html` | 9618 每章复习页:先背什么、图、评分细则英文原话、常考题型;点概念名看英文定义 |

直接用浏览器打开,可以离线使用。

### 练习工作台(`app/`)

```bash
python3 qb.py serve            # 默认端口 8900,自动打开浏览器
```

总览、练习(白板作答、按评分细则判分、看详解)与复盘三个视图。作答与手写记录存在 `qb-work/`。
说明见 [app/README.md](../app/README.md)。

### 数据管理页(`manager/`)

```bash
python3 manage.py                        # 启动并打开浏览器,局域网可访问(默认端口 8910)
python3 manage.py --port 8910 --no-open  # 指定端口,不自动打开浏览器
python3 manage.py window                 # 独立窗口(需要 pywebview);macOS 可双击 manage.command
python3 manage.py auto                   # 题库更新后运行自动流程;题库没变时不运行
python3 manage.py auto --force           # 不论题库是否更新都运行
```

查询、题组、题目卷与评分细则 PDF、导出、批量生成、iPad 白板。说明见
[data-manager.md](data-manager.md)。

### 命令行(`qb.py`)

| 命令 | 作用 |
|---|---|
| `python3 qb.py stats` | 各科题数与数据位置 |
| `python3 qb.py topics --syllabus 9231` | 某科的主题码与题数 |
| `python3 qb.py find --syllabus 9709 --topic 1.7 --marks 6-8` | 按主题、分值等筛题 |
| `python3 qb.py find --text "recursion" --syllabus 9618` | 全文搜索 |
| `python3 qb.py show 9709_s23_12_q05 --full` | 显示一题的题干与评分细则 |
| `python3 qb.py paper --syllabus 9231 --component 3` | 组一套模拟卷 |
| `python3 qb.py chapters` | 教材章节与主题码的对应情况 |
| `python3 qb.py serve` | 启动练习工作台 |

任何命令加 `--json` 输出机器可读格式。

### 测试

```bash
python3 -m unittest discover tests
```

## 5. 数据更新的来源

题库数据(题干、评分细则、详解、题图)在云端沙盒里生成和修改,改完后推送到 GitHub 的
`data` 分支;代码与文档通过 Pull Request 合并到 `main`。本地只需要第 3 节的 `update` 或 `pull`。

云端修改数据的固定步骤(写在 [CLAUDE.md](../CLAUDE.md) 里):

```bash
python3 sync.py pull --no-auto                 # 开始前取回数据
# ……修改数据库……
python3 pipeline/export/build_site.py          # 重新生成页面数据
python3 sync.py push -m "<说明>"               # 推送到 data 分支(覆盖唯一的提交)
```

对题干与评分细则的每一处更正都记在 `pipeline/text/text_fixes.jsonl`(入学考在
`pipeline/admissions_rebuild/text_fixes.json`),随代码进入 `main`,可以重放。

## 6. 本地改了 `data/` 怎么办

`sync.py pull` 发现 `data/` 有未提交的改动时会拒绝执行,并提示两种选择:

- 不要这些改动:`python3 sync.py pull --force`;
- 要保留:把改动另存出来。本地一般不应修改 `data/`,数据的修改应在云端完成后推送。

`python3 sync.py push` 只在云端使用。它会检查 GitHub 上的 `data` 分支自上次取回后
没有被别处更新,否则拒绝推送,避免覆盖别人的结果。

## 7. 稳定分支

`data` 分支每次更新都整体替换,旧版本不会保留。要让稳定版的代码固定使用某一版数据,
需要给那一版数据打标签:

```bash
# 在已经取回了想要的那版数据的机器上(本地,不是云端):
python3 sync.py pin stable                     # 打标签 data-stable 并推送到 GitHub

# 建稳定分支(代码):
git checkout -b stable
git push -u origin stable

# 在只运行稳定版的机器上:
git checkout stable
python3 sync.py update --ref stable            # 代码取 stable 分支,数据取 data-stable 那一版
```

注意:

- 稳定版机器上不要运行不带 `--ref` 的 `update` 或 `pull`,那样会取回最新数据,
  而最新数据可能需要更新的代码才能正确显示。
- 想让稳定版换到新数据:在新数据上重新 `python3 sync.py pin stable`(会移动标签),
  确认 `stable` 分支的代码能正确显示后,稳定版机器再运行 `update --ref stable`。
- 也可以用日期作标签名(`pin 2026-10-03`),保留多个版本,需要时取回其中任何一个。
- 云端沙盒不能推送标签,`pin` 只能在本地运行。
- 稳定分支上修了 bug,同样要合并回 `main`,否则下次从 `main` 重建稳定分支时会丢失。

## 8. 常用排查

| 现象 | 处理 |
|---|---|
| `data/ 还没有取回` | 运行 `python3 sync.py pull` |
| `data/ 已存在且不是 worktree` | 把现有的 `data/` 目录移走,再 `pull` |
| `data/ 里有未提交的改动` | 见第 6 节 |
| `代码目录有未提交的改动,先提交或撤销再 update` | 先处理代码目录的改动(`git status` 查看) |
| 页面显示的是旧数据 | `python3 sync.py status` 看版本;刷题页 `data/practice.html` 需要强制刷新浏览器缓存 |
| `找不到标签 data-NAME` | 先在本地运行 `python3 sync.py pin NAME` |
| 磁盘占用越来越大 | `python3 sync.py pull --gc` |
