# 流水线需要访问的站点

云端沙盒的网络访问受环境的网络策略限制。下表列出流水线用到的全部外部站点,
新增数据来源时同步更新本表。"沙盒状态"为 2026-09-28 的实测结果。

| 站点 | 用途 | 使用它的脚本 | 沙盒状态 |
|---|---|---|---|
| `dynamicpapers.com` | CAIE 9709/9618 试卷与评分细则 PDF | `pipeline/fetch/fetch_any.py`、`fetch.py` | 可访问 |
| `uat-wp.s3.eu-west-2.amazonaws.com` | TMUA/TSA/BMAT 试卷、答案键、官方详解 PDF | `pipeline/admissions_rebuild/manifest.py` | 可访问 |
| `paddleocr.aistudio-app.com` | PaddleOCR-VL 接口,全部 OCR 依赖它 | `pipeline/ocr/paddle.py`、`pipeline/ocr/ocr_books.py` | 可访问 |
| `cie.fraft.cn` | CAIE 试卷与评分细则(Frank 的 CIE 工坊)。接口已改到 `obj/Common/` 下:`Subject/combo` 学科列表,`Fetch/renum` 按学科、年份、季度检索(POST `subject=9709&year=2024&season=Jun`),`Fetch/redir/<文件名>` 下载,直接返回 PDF、不跳转,缺卷返回 404。参考代码 github.com/iewnfod/get_paper_rs 用的是旧接口 `obj/Fetch/...`,已失效 | `fetch_any.py --url-template` | 可访问(2026-09-29) |
| `*.bj.bcebos.com`(如 `paddleocr-store-3.bj.bcebos.com`) | PaddleOCR 结果与插图的下载地址:任务提交到 aistudio,结果 JSON 与图片由这里下发 | `pipeline/ocr/*.py`、`ocr_bank.py` | 可访问(2026-09-29 加入白名单后) |
| `pastpapers.papacambridge.com` | 9231 试卷与评分细则 PDF(dynamicpapers 没有 9231);9709 2025 年 6 月的评分细则(dynamicpapers 返回 404);cie.fraft.cn 上文本层不可读的 2025–2026 年文件。2026 年的文件带水印,下载后运行 `strip_watermark.py` | `fetch_any.py --url-template`、`fetch_fraft.py` | 可访问 |
| `bestexamhelp.com` | 9231 的旧来源,已由 papacambridge 取代 | — | 被拦截 |
| `esat-tmua.ac.uk` | TMUA 官方站点,查找新卷子链接时使用 | — | 可访问 |
| `www.uat-uk.org` | 入学考官方站点,查找新卷子链接时使用 | — | 被拦截 |
| `www.cambridgeinternational.org` | CAIE 大纲 PDF(9709/9231/9618 syllabus) | `pipeline/tags/syllabus.py` 的输入,手动下载 | 可访问(2026-09-29 加入白名单后) |
| `pypi.org` `files.pythonhosted.org` | 安装 PyMuPDF、requests | `pip` | 默认放行 |
| `archive.ubuntu.com` `security.ubuntu.com` | 安装 poppler-utils(`pdftotext`) | `apt-get` | 默认放行 |
| `github.com` | 推送 `main` 与 `data` 分支 | `git` | 可访问 |
| `cdn.jsdelivr.net` | KaTeX 的备用加载源,页面已内置离线副本 | `assets/*.html` | 可访问 |
| `raw.githubusercontent.com` | 复习页嵌入的字体(google/fonts 仓库的 Noto Sans SC、JetBrains Mono 与 OFL 许可),首次 build 时下载到 `raw/fonts/`;claude.ai 的 skill 从本仓库 data 分支取 `caie.db` 与 `papers/` | `pipeline/explain/concept_pages.py`、`skills/shared/get_paper.py`、`qbank.py` | 可访问(2026-10-10) |

白名单在 [allowed-domains.txt](allowed-domains.txt):一行一个域名(不是 URL),`*` 为通配,
可整份复制到环境设置的允许域名中。上表增删站点时同步修改该文件。`bestexamhelp.com` 虽已由
papacambridge 取代,仍是技能文档记载的来源,核对缺卷时要用,故保留。

9231 的下载命令:

```bash
python3 pipeline/fetch/fetch_any.py 9231 raw/pdf --years 21 22 23 24 25 --papers 1 2 3 4 --series s w \
  --url-template "https://pastpapers.papacambridge.com/directories/CAIE/CAIE-pastpapers/upload/{name}"
```

从 cie.fraft.cn 下载(与 dynamicpapers 同样的文件名,缺卷返回 404):

```bash
python3 pipeline/fetch/fetch_any.py 9709 raw/ms --years 24 --papers 3 --series s \
  --url-template "https://cie.fraft.cn/obj/Common/Fetch/redir/{name}"
```

9709 2025 年 6 月的评分细则(dynamicpapers 上没有):

```bash
python3 pipeline/fetch/fetch_any.py 9709 raw/ms --years 25 --papers 1 3 4 5 --series s \
  --url-template "https://pastpapers.papacambridge.com/directories/CAIE/CAIE-pastpapers/upload/{name}"
```

`rebuild_ms.py` 读 `raw/ms/` 中全部评分细则,其余卷子的评分细则用默认来源下载到同一目录。

## 环境变量

| 变量 | 用途 |
|---|---|
| `PADDLE_TOKEN` | PaddleOCR 接口的 token。不设时脚本使用代码中写死的默认值 |
| `CAIE_ROOT` `CAIE_DATA` `CAIE_DB` `CAIE_IMG_ROOT` `CAIE_RAW` | 覆盖 `lib/paths.py` 中的默认路径 |

## Python 依赖

查询与页面只用标准库。流水线另需:

```bash
pip install pymupdf requests
```

`pipeline/split/split_ms.py` 还需要 `pdftotext`(poppler-utils)。
