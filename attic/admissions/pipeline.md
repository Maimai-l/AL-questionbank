# 入学考流水线(归档前 docs/pipeline.md 中的两节)

文中路径 `pipeline/admissions_rebuild/` 现为 `attic/admissions/admissions_rebuild/`。

## 入学考选择题线(TMUA / TSA / BMAT)

脚本位于 `pipeline/admissions_rebuild/`,路径经 `lib/paths.py` 解析,可在任意目录下运行:
原卷在 `raw/bank/`(`paths.BANK`),逐页 OCR 在 `raw/bank_ocr/`(`paths.BANK_OCR`),
跟踪的中间结果(`questions_adm.json`、`answers.json`、`ms_tmua.json`、`retag_*.json`)
在脚本旁(`paths.ADM`),题图在 `data/img_adm/`(`paths.IMG_ADM`)。

```bash
A=pipeline/admissions_rebuild
python3 $A/manifest.py                      # 0. 下载 PDF 与考纲,支持续跑
python3 $A/ocr_bank.py                      # 1. 按页 OCR(第三个参数为并发数,默认 4)
python3 $A/parse_keys.py                    # 2. 答案键 → answers.json
python3 $A/page_batches.py plan --out raw/page_batches/runN   # 2b. 切不好的页交给转录员
python3 $A/page_batches.py apply --out raw/page_batches/runN  #     收回,写入 page_fixes.json
python3 $A/split_admissions.py              # 3. 切题 → questions_adm.json,逐卷校验
python3 $A/attach_ms.py                     # 4. 挂接 TMUA 官方详解
python3 $A/tag_admissions.py                # 5. 主题标注与 PS/CT 配比校验
python3 $A/render_adm_imgs.py               # 6. 逐题原页图
python3 $A/audit_adm_imgs.py                #    裁图审计,全部通过后再推送
python3 $A/merge_admissions.py              # 7. 合并进 data/caie.db(重建入学考行,再写回模型标签)
python3 pipeline/export/build_site.py       # 8. 出页面
```

`page_fixes.json`(跟踪)是对照页面图像修正过的逐页识别文本,`split_admissions.py`
与 `attach_ms.py` 读页时优先使用(`page_fixes.py`)。`page_batches.py plan` 先切到临时
文件,与跟踪的 `questions_adm.json` 逐题比较(缺题、答案字母不在选项中、文本短一半以上、
与原题用词重合不足一半即错位),把相关页面渲染成图片,连同识别文本和"重点核对"提示分批
交给转录员子 agent;`apply` 只收下保留了全部 `<img>`、长度未缩短三分之一以上的页面。
`option_texts.py` 从题干按规则取出每个选项的文字,写 `option_texts`(图形选项为 null),
`merge_admissions.py` 插入时同样调用。

`review_batches.py` 负责把需要读图判断的题目分批、生成给 agent 的提示词,并在回收时
用不变量校验结果。改判结果写入 `retag_tmua.json` 与 `retag_tara.json`,不要直接改
`questions_adm.json`,后者在重跑时会被覆盖。

`spot_check.py` 是入学考抽查:每份试卷按固定种子抽题(默认 5 题,`--exam` 限定考试,`--run` 另存一组),子 agent 对照题图核对题干、
选项与答案字母,结果写在 `raw/adm_check/out/`;`report` 按试卷与考试统计有错的题与错误类型,
用来决定哪些试卷要整份重新转录。


## 入学考题图(img_adm)

`render_adm_imgs.py` 读 `raw/bank/` 下的原卷(`manifest.py raw/bank` 下载),写入
`data/img_adm/`。与 CAIE 裁图的做法相同:

- 页面固定元素:页码、各年份写法不同的页脚、页眉横线、页顶标志、BLANK PAGE
- 题号在全卷范围内按 1、2、3… 依次认领,选项旁的数值不会被当成题号。文本层损坏
  的三种情况都能还原:UCLES 老卷的 29 位偏移、TMUA 2016/2017 的 CambriaMath
  数字(U+0372 起)、字形缺失的空白题号
- 共享材料跨页时,续页顶部的材料段同样拼到每道相关题前面
- 下一题题号在下一页顶端时,那一页不属于本题

`audit_adm_imgs.py` 检查:题号序列是否完整且有序、裁图内是否有别题的题号、固定元素
是否残留(逐像素)、题目页上的内容是否被遗漏、有没有按整页输出的题。当前 55 份试卷、
1888 题全部通过。

