# 给 Claude 的项目说明

## 数据位置

- 代码在 `main` 分支。数据库、题图、教材与页面在 `data/`,它是 `data` 分支的
  git worktree。会话开始时运行 `python3 sync.py pull` 取回数据。
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

- `docs/pipeline.md`:执行顺序、脚本索引、已知问题
- `docs/data-sync.md`:data 分支
- `docs/network.md`:需要访问的站点。新增外部来源时必须更新此表
