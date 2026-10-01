# data 分支与同步

## 为什么分成两个分支

数据库、题图与页面数据都由流水线生成,每次重新生成都会整体变化。若由 `main`
跟踪,每次变化都会在历史中留下一份完整副本:`caie.db` 约 34 MB,`data.js` 约
9 MB,重新裁一次图约 180 MB。旧仓库的历史因此达到 1.07 GB,而当前文件只有约
60 MB。

现在的做法是:

- `main` 只保存代码与文档,历史正常累积。
- `data` 是孤立分支,与 `main` 没有共同祖先,且始终只有一个提交。每次更新都改写
  这个提交并强制推送,旧版本不再被任何引用指向,由 GitHub 定期回收。

## data/ 的内容

| 路径 | 内容 | 由谁生成 |
|---|---|---|
| `caie.db` | 主库:questions、chapters、attempts、q_fts | `pipeline/db/combine.py`、`pipeline/admissions_rebuild/merge_admissions.py` 等 |
| `img9709/` `img9231/` `img9618/` | CAIE 逐题裁图 | `pipeline/split/crop.py` |
| `img9709_ans/` `img9231_ans/` `img9618_ans/` | 带答题区的裁图,刷题页白板以此为底图;只收题图漏掉了点线答题行的题,文件名与题图相同 | `pipeline/split/recrop.py --rows` |
| `img_adm/` | 入学考逐题原页图 | `pipeline/admissions_rebuild/render_adm_imgs.py` |
| `img_tara/` | 入学考题干中引用的插图 | `pipeline/admissions_rebuild/merge_admissions.py` |
| `books/<书>/` | 教材章节 Markdown 与插图 | `pipeline/books/split_chapters.py` |
| `data.js` `textbooks.js` | 页面读取的数据 | `pipeline/export/build_site.py` |
| `practice.html` `textbook.html` `vendor/` | 从 `assets/` 复制的页面 | `pipeline/export/build_site.py` |

`questions.image` 与 `chapters.path` 中存放的都是相对 `data/` 的路径。

旧版本中 `assets/books/*/imgs/` 下另有 2366 张 `layout_det_res_*.jpg`,共 959 MB。
它们是 PaddleOCR 输出的版面检测调试图,没有任何 Markdown 引用,因此未放入 `data` 分支。

## 命令

```bash
python3 sync.py pull            # 取回最新版本到 data/;首次运行时创建 worktree
python3 sync.py pull --gc       # 同上,并清理旧版本占用的本地磁盘
python3 sync.py status          # 当前版本与本地改动
python3 sync.py push -m "说明"  # 提交 data/ 的改动并覆盖远程 data 分支
```

`push` 使用 `--force-with-lease`,并在推送前检查远程版本是否仍是上次 `pull` 的
版本。若远程已被别处更新,`push` 会中止,避免覆盖对方的结果。

## 修改数据后的标准步骤(云端)

```bash
python3 sync.py pull
# …运行流水线,写入 data/caie.db 或题图…
python3 pipeline/export/build_site.py       # 修改数据库后必须执行,否则页面读到旧数据
python3 sync.py push -m "重裁 9709 题图"
```

## 旧历史

2026-09-29 起,`main` 从一个新的根提交开始,不再包含旧历史。旧历史(含全部图片与旧版
数据库,约 1.07 GB)与标签 `images-snapshot` 已从远程删除。其中仍需要的内容已全部
进入 `data` 分支:数据库、题图、教材章节与插图。未迁移的只有 2366 张
`layout_det_res_*.jpg` 版面检测调试图(959 MB,无任何引用)和已被取代的旧题图。
