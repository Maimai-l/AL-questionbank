# manager/

题库数据管理页(需求见 `docs/data-manager.md`,设计稿见该文件第 8 节):`python3 qb.py manage`(默认端口 8910,
监听局域网,iPad 用 Mac 的地址访问)。对 `data/caie.db` 只读;题组等存放在 `paths.WORK`。

| 文件 | 内容 |
|---|---|
| `server.py` | aiohttp 服务:页面、题图、原卷、`/api/*` |
| `bank.py` | 题库的只读视图:查询表格的行、条件栏的计数、单题详情(评分细则逐行拆分) |
| `sets.py` | 题组:`paths.SETS` 下每组一个 JSON;与模型交换用 `alevel-question-set/v1` |
| `web/app.js` | 页面(React,不经构建,`h = React.createElement`) |
| `web/style.css` | 页面布局;类名以 `dm-` 开头的是为了避开设计系统已用的类名 |
| `web/ds/` | 设计系统 ENDFIELD React 的副本:React 18、`bundle.js`、`bundle.css`、`tokens.css`、字体 |

`web/ds/fixes.css` 记录对设计系统的两处覆盖:纹理图暂不显示(图片在设计系统的资源库中,未复制);
Sidebar 的线条图标补上描边设置。设计系统更新后,重新复制 `bundle.js` 与 `bundle.css`,并检查这两处是否还需要。

分期:第一阶段(查询、单题详情、题组)已实现;题目卷、评分细则与详解、导出、模板、白板、批量生成按
`docs/data-manager.md` 第 10 节依次实现。
