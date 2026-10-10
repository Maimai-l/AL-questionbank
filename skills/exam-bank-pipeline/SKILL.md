---
name: "exam-bank-pipeline"
description: CAIE(9709/9231/9618)与入学考(TMUA/TSA/BMAT)题库的建库流水线与数据,代码与数据在 GitHub 仓库 Maimai-l/AL-questionbank(main 分支是代码,data 分支是 caie.db、题图、原卷 PDF 与页面)。涵盖抓卷(三个站点与去水印)、OCR、题目切分、对照原卷审校、主题标注、详解、复习页与导出。凡涉及这套题库的操作——新增卷子、修复切坏的题、答案或标签对不上、重跑 OCR、改动 schema 或页面、按题取题干与评分细则——均应加载本 skill。
---

# 题库流水线

题库的代码、文档与数据都在公开仓库 **Maimai-l/AL-questionbank**。本 skill 只说明怎样拿到它、
怎样开始工作,以及仓库文档里没有集中写出的几条规则。流程细节以仓库内的文档为准:

| 仓库文档 | 内容 |
|---|---|
| `CLAUDE.md` | 在仓库里工作的规则:数据位置、同步、测试、汇报方式 |
| `docs/status.md` | 数据现状与待办,接手时先读 |
| `docs/pipeline.md` | 全部脚本的执行顺序与相互约束 |
| `docs/guide.md` | 使用手册:安装、同步、命令、稳定分支 |
| `docs/network.md` | 需要访问的站点与白名单(`docs/allowed-domains.txt`) |
| `docs/data-sync.md` | data 分支的同步方式 |

## 一、拿到代码与数据

```bash
git clone --single-branch --branch main https://github.com/Maimai-l/AL-questionbank.git
cd AL-questionbank
python3 sync.py pull --no-auto       # 取回 data/(data 分支的 worktree,约 1.2 GB)
python3 qb.py stats                  # 确认数据就位
```

只需要题目文本时不必取整个仓库,用本 skill 的 `scripts/qbank.py`(只下载 caie.db,约 75 MB):

```bash
S=$(dirname "$(find / -path '*exam-bank-pipeline/scripts/qbank.py' 2>/dev/null | head -1)")
python3 $S/qbank.py paper 9618_s24_11          # 整卷:题干、分值、评分细则
python3 $S/qbank.py find --syllabus 9709 --topic 1.7 --text "tangent"
```

单个文件可以直接取:`https://raw.githubusercontent.com/Maimai-l/AL-questionbank/data/<路径>`,
例如 `data` 分支的 `caie.db`、`papers/9618_s24_qp_11.pdf`、`img9618/…`。

网络受限时,需要在环境的网络设置里允许 `github.com`、`*.githubusercontent.com`;
抓新卷还要允许三个试卷站点(见第三节)。

## 二、题库现状(2026-10)

```
data/caie.db        5937 题:9709(2070) 9231(1009) 9618(970)  2021–2026 年
                              TMUA(360) TSA(800) BMAT(728)
data/papers/        原卷与评分细则 PDF:CAIE 1052 份,入学考 55 份在 bank/ 下,均已去水印
data/img9709 …      逐题题图;data/img_adm、img_tara 入学考题图
data/books/         81 章教材正文(markdown)
data/practice.html  刷题页;textbook.html 教材页;concepts/9618/ 9618 每章复习页
```

- 题干与评分细则以 `question_latex`、`ms_latex` 为准(经 OCR 并逐题对照原卷审校),
  `question_text`、`ms_text` 是 PDF 文本层,只作兜底。
- 原卷的印刷错误已按正确写法更正,依据写在 `pipeline/text/text_fixes.jsonl` 各行的 `why`。
- 9618 有逐小问详解(`explanation` 列,970 题中 968 题);9709、9231 不做详解(用户决定)。
- 仍待处理的事项(BMAT 共用材料、TMUA 整体核对等)见 `docs/status.md`。

## 三、试卷来源与去水印

三个站点同名文件内容不同,要挑能被切分脚本读懂的那一份:

| 站点 | 情况 |
|---|---|
| `cie.fraft.cn` | 接口 `obj/Common/Fetch/renum`(按科目、年份、季度列清单,POST)与 `Fetch/redir/<文件名>`(POST 下载)。部分 2025–26 年卷子字体无 Unicode 映射(文本层是乱码),个别排在 Letter 纸上 |
| `pastpapers.papacambridge.com` | `directories/CAIE/CAIE-pastpapers/upload/<文件名>`。有 9231 与最新一季;带水印,部分评分细则被重新拼版 |
| `dynamicpapers.com` | `wp-content/uploads/2015/09/<文件名>`。缺文件时返回 WordPress 的 500 页面而不是 404 |

- 在仓库里:`pipeline/fetch/fetch_fraft.py` 按 fraft 清单补下库中没有的卷,文本层不可读时改用
  papacambridge;`pipeline/fetch/best_copy.py` 对三个站点的版本逐一试切,留下题数与总分对得上的一份;
  `pipeline/fetch/strip_watermark.py` 去掉 papacambridge 水印(`--check` 只检查)。
- 不在仓库里时:本 skill 的 `scripts/get_paper.py` 依次试 GitHub(data 分支 `papers/`)、fraft、
  papacambridge、dynamicpapers,检查文本层与纸张,papacambridge 的文件自动去水印:

  ```bash
  python3 $S/get_paper.py 9231_w21_qp_13 9231_w21_ms_13 9231_w21_gt --out papers
  python3 $S/get_paper.py 9618 --years 25 26 --series s --papers 1 2 --gt --out papers
  ```

## 四、修改数据的固定步骤

`data/` 是 `data` 分支的 worktree,这个分支始终只有一个提交:

```bash
python3 sync.py pull --no-auto                 # 开始前
# ……修改……
python3 pipeline/export/build_site.py          # 重新生成页面数据,必须最后运行
python3 sync.py push -m "<说明>"               # 覆盖 data 分支唯一的提交
```

- 不要把 `data/`、`raw/`、`exports/` 下的文件提交到 `main`;所有路径经 `lib/paths.py` 解析。
- 对题干与评分细则的更正一律经 `pipeline/text/fix_batches.py` 写入 `text_fixes.jsonl`,随代码进
  `main`,可以重放;不要直接改数据库。
- 改了 `manager/` 或 `manage.py` 要跑 `python3 -m unittest discover tests`。

## 五、子 agent 批处理的约定

审校、标签复核、详解、复习页都按同一个模式:脚本 `plan` 生成批次文件,每批交给一个子 agent,
agent 只写自己的结果文件(或只返回 JSON),脚本 `verify`/`check` 校验,`apply` 由主进程统一写入。

- agent 不直接改数据库或共享文件:出错时可以按批回滚,也能从校验数值反推是哪一批出的问题。
- 每批 10 至 15 题。批次太大,agent 会在后几题开始推测而不是核对。
- 结果先过校验再写入;未通过的批次重做,不手工改数值绕过校验。
- 收回后自己抽查约 5%。agent 的错误有规律,抽样就能发现。

## 六、不变量

每改一处就重跑校验,数值会指出剩余问题的位置:

| 不变量 | 违反时的含义 |
|---|---|
| CAIE 题面总分等于评分细则总分(`totals_agree`) | 小问没切全 |
| 每卷切出题数等于答案键条数(入学考) | 丢题或多切,其后题号整体错位 |
| 选择题答案字母属于该题选项 | 选项被 OCR 吞掉,或切分越界到相邻题 |
| 题干写「见图」则必须有图 | 配图被切给了下一题 |
| TSA 每卷 25 题 PS 加 25 题 CT | 题型误判 |
| OCR 页数等于 PDF 页数 | JSONL 解析有误 |

题数不符比答案错误更危险:少切一题会让后面每一题的答案错位一位,而单看每一题都正常。

## 七、references/

`references/` 是建库初期整理的领域知识,其中的路径是旧目录(`qb/…`),以仓库现状为准:

| 文档 | 适用场景 |
|---|---|
| `admissions-mcq.md` | TMUA/TSA/BMAT 的切分规则与题型 |
| `caie-longform.md` | 9709/9231/9618 的切分与评分细则格式 |
| `ocr-damage.md` | 校验报告异常、页面内容明显不对时的损伤类型与处理 |
| `db-contract.md` | schema 与页面、导出之间的约定(新增列见仓库 `lib/db.py` 与 `docs/`) |

## scripts/

| 脚本 | 用途 |
|---|---|
| `get_paper.py` | 下载 qp、ms、等级线:GitHub → fraft → papacambridge(去水印)→ dynamicpapers |
| `strip_watermark.py` | 去 papacambridge 水印(需要 PyMuPDF),`--check` 只检查 |
| `qbank.py` | 不取仓库,只用 caie.db 按卷、按题、按主题取题干与评分细则 |
