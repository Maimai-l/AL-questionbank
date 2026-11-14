# attic — 暂时不用的东西

这两个文件没删,只是搬开了。哪天想用,搬回上一层目录就行(它们自己会找项目根)。

- `mcp_server.py` — stdio MCP server,10 个工具。对话框里的 AI 一般不会调 MCP,
  所以日常用不上;要用得在 MCP 客户端里注册绝对路径 `<项目根>/attic/mcp_server.py`(放在 attic/ 里直接运行也可以)。
- `progress.py` — 做题记录 / 掌握度 / 弱点诊断,配套 `caie.db` 里的 `attempts` 表。
  现在学习进度自己管,页面也不再记录任何东西,所以这一层没人调用了。
  已经写进库的 `attempts` 数据不会丢,搬回去照样能读。

`mcp_server.py` 依赖 `progress.py`,要用就两个一起搬回去。

## admissions/(2026-11-14 归档)

入学考(TMUA、TSA、BMAT)的全部专用代码与说明：`admissions_rebuild/`(原 `pipeline/admissions_rebuild/`)、
`export_adm_practice.py`、`export_admissions_banks.py`(原 `pipeline/export/`)、`adm_practice.html`(原 `assets/`)、
`docs/`(原 `docs/admissions/`)、`admissions-mcq.md`(原 skill 的 references)、`pipeline.md`(原 `docs/pipeline.md` 中的两节)。
数据(1888 题的数据库行、`img_adm/`、`img_tara/`、`papers/bank/`、刷题页)在仓库的 `archive-admissions` 分支，恢复方法见该分支的 README.md。
`lib/paths.py` 的 `ADM` 已指向这里的 `admissions_rebuild/`。
