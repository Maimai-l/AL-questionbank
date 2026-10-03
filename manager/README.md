# manager/

题库数据管理页(需求见 `docs/data-manager.md`,设计稿见该文件第 8 节):`python3 manage.py`(默认端口 8910;`python3 manage.py window` 在 pywebview 窗口中打开,
监听局域网,iPad 只通过白板外壳访问 `/ipad`)。对 `data/caie.db` 只读;题组等存放在 `paths.WORK`。

| 文件 | 内容 |
|---|---|
| `server.py` | aiohttp 服务:页面、题图、原卷、`/api/*` |
| `search.py` | 搜索页:自建全文索引(`paths.WORK/search.db`)、查询解析、命中片段 |
| `bank.py` | 题库的只读视图:查询表格的行、条件栏的计数、单题详情(评分细则逐行拆分) |
| `sets.py` | 题组:`paths.SETS` 下每组一个 JSON;与模型交换用 `alevel-question-set/v1` |
| `paper.py` | 练习卷 PDF(F4),缓存在 `paths.WORK/papers/` |
| `docs.py` | 评分细则与详解的阅读文档(F6) |
| `settings.py` | 设置页:练习卷页脚与配色 |
| `export.py`、`templates.py`、`templates/` | 输出(PDF、ZIP、图片 ZIP)与导出模板(F7、F8) |
| `board.py`、`whiteboard/` | 练习卷白板与批注版导出(F5) |
| `flow.py`、`flows/` | 批量生成的运行器与内置示例(F9) |
| `vendor/inksync/`、`web/board/` | 来自 white-board 的同步组件与书写界面,见 `vendor/README.md` |
| `web/app.js` | 页面(React,不经构建,`h = React.createElement`) |
| `web/style.css` | 页面布局;类名以 `dm-` 开头的是为了避开设计系统已用的类名 |
| `web/ds/` | 设计系统 ENDFIELD React 的副本:React 18、`bundle.js`、`bundle.css`、`tokens.css`、字体 |

设计系统的来源是仓库 `Maimai-l/endfield-backup`(`design-system-react/project/components/` 与
`design-system/project/assets/Textures/`)。复制 `bundle.css` 后,把其中的 `url(/_blob/<id>)` 换成 `textures/` 下的同名图片。
`web/ds/fixes.css` 补上 Sidebar 线条图标的描边设置;设计系统修好后删除。

分期:`docs/data-manager.md` 第 10 节的五个阶段均已实现。
