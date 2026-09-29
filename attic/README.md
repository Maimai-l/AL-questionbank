# attic — 暂时不用的东西

这两个文件没删,只是搬开了。哪天想用,搬回上一层目录就行(它们自己会找项目根)。

- `mcp_server.py` — stdio MCP server,10 个工具。对话框里的 AI 一般不会调 MCP,
  所以日常用不上;要用得在 MCP 客户端里注册绝对路径 `<项目根>/attic/mcp_server.py`(放在 attic/ 里直接运行也可以)。
- `progress.py` — 做题记录 / 掌握度 / 弱点诊断,配套 `caie.db` 里的 `attempts` 表。
  现在学习进度自己管,页面也不再记录任何东西,所以这一层没人调用了。
  已经写进库的 `attempts` 数据不会丢,搬回去照样能读。

`mcp_server.py` 依赖 `progress.py`,要用就两个一起搬回去。
