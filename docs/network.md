# 流水线需要访问的站点

云端沙盒的网络访问受环境的网络策略限制。下表列出流水线用到的全部外部站点,
新增数据来源时同步更新本表。"沙盒状态"为 2026-09-28 的实测结果。

| 站点 | 用途 | 使用它的脚本 | 沙盒状态 |
|---|---|---|---|
| `dynamicpapers.com` | CAIE 9709/9618 试卷与评分细则 PDF | `pipeline/fetch/fetch_any.py`、`fetch.py` | 可访问 |
| `uat-wp.s3.eu-west-2.amazonaws.com` | TMUA/TSA/BMAT 试卷、答案键、官方详解 PDF | `pipeline/admissions_rebuild/manifest.py` | 可访问 |
| `paddleocr.aistudio-app.com` | PaddleOCR-VL 接口,全部 OCR 依赖它 | `pipeline/ocr/paddle.py`、`pipeline/ocr/ocr_books.py` | 可访问 |
| `pastpapers.papacambridge.com` | 9231 试卷与评分细则 PDF(dynamicpapers 没有 9231) | `fetch_any.py --url-template` | 可访问 |
| `bestexamhelp.com` | 9231 的旧来源,已由 papacambridge 取代 | — | 被拦截 |
| `esat-tmua.ac.uk` | TMUA 官方站点,查找新卷子链接时使用 | — | 可访问 |
| `www.uat-uk.org` | 入学考官方站点,查找新卷子链接时使用 | — | 被拦截 |
| `pypi.org` `files.pythonhosted.org` | 安装 PyMuPDF、requests | `pip` | 默认放行 |
| `github.com` | 推送 `main` 与 `data` 分支 | `git` | 可访问 |
| `cdn.jsdelivr.net` | KaTeX 的备用加载源,页面已内置离线副本 | `assets/*.html` | 可访问 |

白名单写法:

```
dynamicpapers.com
uat-wp.s3.eu-west-2.amazonaws.com
paddleocr.aistudio-app.com
pastpapers.papacambridge.com
www.uat-uk.org
esat-tmua.ac.uk
```

9231 的下载命令:

```bash
python3 pipeline/fetch/fetch_any.py 9231 raw/pdf --years 21 22 23 24 25 --papers 1 2 3 4 --series s w \
  --url-template "https://pastpapers.papacambridge.com/directories/CAIE/CAIE-pastpapers/upload/{name}"
```

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
