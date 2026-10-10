# claude.ai 上的两个 skill

| 目录 | skill |
|---|---|
| `exam-bank-pipeline/` | 题库流水线:怎样取仓库与数据、试卷来源与去水印、修改数据的步骤、子 agent 约定、不变量 |
| `exam-paper-review/` | 真题卷判分与薄弱项分析 |
| `shared/` | 两个 skill 共用的脚本,打包时放进各自的 `scripts/` |

`shared/` 里的脚本不依赖仓库,在 claude.ai 的沙盒里单独运行:

| 脚本 | 用途 |
|---|---|
| `get_paper.py` | 下载 qp、ms、等级线:先取本仓库 data 分支的 `papers/`,再依次试 fraft、papacambridge(自动去水印)、dynamicpapers |
| `strip_watermark.py` | `pipeline/fetch/strip_watermark.py` 的独立副本 |
| `qbank.py` | 只下载 `caie.db`,按卷、按题、按主题取题干与评分细则 |

改完后打包,在 claude.ai 的 设置 → 功能 → Skills 里上传,替换同名的 skill:

```bash
python3 skills/build.py        # 生成 exports/exam-bank-pipeline.skill 与 exam-paper-review.skill
```

`strip_watermark.py` 与仓库里的那份要一起改。
