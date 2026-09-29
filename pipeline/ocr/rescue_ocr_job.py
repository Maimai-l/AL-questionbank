#!/usr/bin/env python3
"""Re-download a finished PaddleOCR job and write its pages out correctly.

A job whose result was mis-written is not a job that has to be re-run. The
model already read every page; what went wrong was on the way to disk — several
pages arriving in one JSONL line were written to the same filename, so only the
last of each group survived. The job id is still in `.ocr_checkpoint.json`, and
the server keeps the result for a while, so the fix is usually a download rather
than another few hundred pages of OCR.

    python3 rescue_ocr_job.py .ocr_checkpoint.json out_dir
    python3 rescue_ocr_job.py <jobId> out_dir

Writes page_0001.md ... numbered across *all* results in order, plus any images
the result carries. If the job has expired the script says so, and then
`ocr_book.py` is the way.
"""
import json, os, sys

try:
    import requests
except ImportError:
    sys.exit("需要 requests:  pip install requests")

JOB = "https://paddleocr.aistudio-app.com/api/v2/ocr/jobs"
TOKEN = os.environ.get("PADDLE_TOKEN", "f976c86061d646ba2294e0a5a951893ac2e9d383")
HEAD = {"Authorization": f"bearer {TOKEN}"}


def job_id_from(arg):
    if os.path.exists(arg):
        d = json.load(open(arg))
        jid = d.get("jobId")
        if not jid:
            sys.exit(f"{arg} 里没有 jobId")
        print(f"从 {arg} 读到 jobId: {jid}")
        return jid
    return arg


def fetch(jid):
    r = requests.get(f"{JOB}/{jid}", headers=HEAD, timeout=90)
    if r.status_code != 200:
        sys.exit(f"查询失败 HTTP {r.status_code}: {r.text[:200]}\n"
                 f"任务可能已经过期,只能重跑 ocr_book.py")
    d = r.json()["data"]
    st = d.get("state")
    print(f"任务状态: {st}")
    if st != "done":
        sys.exit(f"任务不是 done,救不回来({d.get('errorMsg') or ''})。重跑 ocr_book.py")
    prog = d.get("extractProgress") or {}
    if prog:
        print(f"服务端记录:共 {prog.get('totalPages','?')} 页,"
              f"已提取 {prog.get('extractedPages','?')} 页")
    return d["resultUrl"]["jsonUrl"]


def main(arg, out_dir):
    jid = job_id_from(arg)
    url = fetch(jid)
    print("下载结果 ...")
    lines = [l for l in requests.get(url, timeout=300).text.strip().split("\n") if l.strip()]
    print(f"JSONL {len(lines)} 行")

    os.makedirs(out_dir, exist_ok=True)
    img_dir = os.path.join(out_dir, "imgs")
    page = 0
    per_line = []
    imgs = 0
    for ln in lines:
        try:
            results = json.loads(ln)["result"]["layoutParsingResults"]
        except Exception as e:
            print(f"  跳过一行,解析失败: {e}")
            continue
        per_line.append(len(results))
        # the whole point: one file per result, not one per line
        for res in results:
            page += 1
            md = res.get("markdown", {}) or {}
            with open(os.path.join(out_dir, f"page_{page:04d}.md"), "w",
                      encoding="utf-8") as f:
                f.write(md.get("text", "") or "")
            for rel, iu in (md.get("images") or {}).items():
                dst = os.path.join(out_dir, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                try:
                    open(dst, "wb").write(requests.get(iu, timeout=60).content)
                    imgs += 1
                except Exception:
                    pass
            for name, iu in (res.get("outputImages") or {}).items():
                os.makedirs(img_dir, exist_ok=True)
                try:
                    open(os.path.join(img_dir, f"{name}_{page:04d}.jpg"), "wb").write(
                        requests.get(iu, timeout=60).content)
                    imgs += 1
                except Exception:
                    pass

    from collections import Counter
    c = Counter(per_line)
    print(f"\n每行包含的页数分布: {dict(c)}")
    if max(c) > 1:
        print(f"→ 确认:一行最多 {max(c)} 页。原来的脚本让它们共用同一个文件名,"
              f"所以只剩 {len(lines)} 个文件。")
    print(f"\n写出 {page} 页 -> {out_dir}" + (f",图片 {imgs} 张" if imgs else ""))
    print(f"\n接着跑:\n  python3 map_ocr_pages.py <book.pdf> {out_dir}"
          f"   # 确认现在是 1:1\n  python3 split_chapters.py <book.pdf> {out_dir} "
          f"books/9709_p23 --prefix 9709_p23")


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if len(a) < 2:
        sys.exit(__doc__)
    main(a[0], a[1])
