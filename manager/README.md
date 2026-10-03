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
| `settings.py` | 设置页:练习卷的版面默认档、页脚与配色 |
| `export.py`、`templates.py`、`templates/` | 输出(PDF、ZIP、图片 ZIP)与导出模板(F7、F8) |
| `board.py`、`whiteboard/` | 练习卷白板与批注版导出(F5) |
| `requirements.txt` | 依赖:`pip install -r manager/requirements.txt`;可选依赖写在文件末尾 |
| `flow.py`、`flows/` | 批量生成的运行器与内置示例(F9) |
| `vendor/inksync/`、`web/board/` | 来自 white-board 的同步组件与书写界面,见 `vendor/README.md` |
| `web/app.js` | 页面(React,不经构建,`h = React.createElement`) |
| `web/style.css` | 页面布局;类名以 `dm-` 开头的是为了避开设计系统已用的类名 |
| `web/ds/` | 设计系统 ENDFIELD React 的副本:React 18、`bundle.js`、`bundle.css`、`tokens.css`、字体 |

设计系统的来源是仓库 `Maimai-l/endfield-backup`(`design-system-react/project/components/` 与
`design-system/project/assets/Textures/`)。复制 `bundle.css` 后,把其中的 `url(/_blob/<id>)` 换成 `textures/` 下的同名图片。
`web/ds/fixes.css` 补上 Sidebar 线条图标的描边设置;设计系统修好后删除。

分期:`docs/data-manager.md` 第 10 节的五个阶段均已实现。

测试:`python3 -m unittest discover tests`(读取 `data/`,只写临时目录;约 2 分钟)。

| 文件 | 内容 |
|---|---|
| `tests/test_manager.py` | 各页面向服务器发出的请求，按使用顺序:查询页(各考试、题目详情、加入题组)、搜索页(各条件、各种写法)、题组(新建、改名、排序、移出、导出与导入 JSON、删除、练习卷、阅读文档、各模板与格式的输出)、白板(超过 115 页的题组建板、末页写入、导出带笔迹)、模板与流程(新建、修改、运行、删除，内置的不可改)、设置(保存、范围检查、各档预览);练习卷各档页数与「紧凑」不留答题线 |
| `tests/test_pages.py` | 在浏览器(Playwright)中按顺序操作每个页面的主要流程，出现脚本错误、失败的请求或错误提示即不通过。需要 `pip install playwright && playwright install chromium`,未安装时跳过;`QB_CHROMIUM` 可指定 Chromium |
| `tests/test_window.py` | macOS 窗口代码(`manage.py window`):窗口设置、标题栏拖动、双击行为;AppKit 与 pywebview 以替身代替 |
| `tests/support.py` | 临时目录(`QB_WORK`、`CAIE_EXPORTS`)与取题 |
