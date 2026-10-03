# 给 Claude 的项目说明

## 数据位置

- 代码在 `main` 分支。数据库、题图、教材与页面在 `data/`,它是 `data` 分支的
  git worktree。会话开始时运行 `python3 sync.py pull --no-auto` 取回数据(云端不需要写 `exports/`)。
- 修改 `data/` 后:先运行 `python3 pipeline/export/build_site.py`,再运行
  `python3 sync.py push -m "<说明>"`。`data` 分支始终只有一个提交,push 会改写它。
- 不要把 `data/`、`raw/`、`exports/` 下的任何文件提交到 `main`。
- 所有路径经 `lib/paths.py` 解析,新脚本不得写死路径。

## 与题库 skill 的差异

`exam-bank-pipeline` skill 中的部分路径已与本仓库不同,以本仓库为准:

| skill 中的写法 | 本仓库 |
|---|---|
| `qb/caie.db` | `data/caie.db` |
| `qb/img9709/` 等 | `data/img9709/` 等 |
| 根目录的 `export_*.py` | `pipeline/export/` |
| `pipeline/admissions_rebuild/export_web.py` | `pipeline/export/export_web.py`,通常经 `build_site.py` 调用 |
| `qb/practice.html + data.js` | 源文件在 `assets/`,生成物在 `data/` |

## 文档

- `docs/status.md`:数据现状与待办,接手时先读
- `docs/pipeline.md`:执行顺序、脚本索引、已知问题
- `docs/data-sync.md`:data 分支
- `docs/network.md`:需要访问的站点。新增外部来源时必须更新此表和 `docs/allowed-domains.txt`(白名单,一行一个域名)

## 测试

- 修改 `manager/` 或 `manage.py` 后运行 `python3 -m unittest discover tests`,全部通过后再提交。
  新增页面或流程时在 `tests/test_manager.py`(接口)与 `tests/test_pages.py`(浏览器)中补上对应的流程;
  `manage.py` 的窗口代码对应 `tests/test_window.py`。发布记录在 `docs/releases/`。

## 协作约定

- 用户在多伦多(`America/Toronto`)。用量按 5 小时窗口轮换，2026-10-02 起窗口在多伦多时间 17:30 重置，之后的窗口起点为
  22:30、3:30、8:30、13:30。大批量的子 agent 任务按窗口分配任务量，每个窗口开始时用定时任务启动一轮。
- 汇报一律用中文。
