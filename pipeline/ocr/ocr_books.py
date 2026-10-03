#!/usr/bin/env python3
"""OCR every PDF in a folder. One command, one job per book, images included.

    python3 ocr_books.py <pdf_dir> <out_dir>

Options, none of them required:
    --workers N   books in flight at once (default 2)
    --only TEXT   just the books whose filename contains TEXT
    --redo        ignore what is already on disk and do it again
    --quiet       one line per event instead of the running poll

Output per book:

    <out_dir>/<book>/page_0001.md    one file per page, numbered from 1
    <out_dir>/<book>/imgs/...        every figure, at the path the markdown uses
    <out_dir>/<book>/_raw.jsonl      the API's untouched answer
    <out_dir>/<book>/_job.json       job id, counts, timings

`_raw.jsonl` is kept on purpose. The expensive part is the recognition; if the
way pages are written out ever turns out to be wrong again, it can be redone
from that file for free. Re-running this script re-uses it automatically.

The one bug that matters, written down so it does not come back: the API packs
several pages into a single JSONL line. Iterating lines and writing one file per
line silently keeps only the last page of each group — the first Pure Maths 2&3
run came out as 89 files for a 353-page book, every one of them looking
perfectly normal. Pages come from `layoutParsingResults`, not from lines.
"""
import json, os, re, sys, threading, time
from concurrent.futures import ThreadPoolExecutor

try:
    import requests
except ImportError:
    sys.exit("需要 requests:  pip install requests")

try:
    import fitz          # only for checking the page count; not required
except ImportError:
    fitz = None

JOB = os.environ.get("PADDLE_JOB_URL",
                     "https://paddleocr.aistudio-app.com/api/v2/ocr/jobs")
TOKEN = os.environ.get("PADDLE_TOKEN", "f976c86061d646ba2294e0a5a951893ac2e9d383")
HEAD = {"Authorization": f"bearer {TOKEN}"}
MODEL = os.environ.get("PADDLE_MODEL", "PaddleOCR-VL-1.6")
OPT = {"useDocOrientationClassify": False,
       "useDocUnwarping": False,
       "useChartRecognition": False}

SUBMIT_TRIES = 40           # the queue rejects while busy; it clears
POLL_EVERY = 10             # seconds
POLL_BUDGET = 4 * 3600      # a 646-page scan is allowed to take hours
IMG_WORKERS = 12

_print_lock = threading.Lock()
_t0 = time.time()


def log(book, msg):
    with _print_lock:
        el = time.time() - _t0
        tag = f"[{int(el//60):>3}:{int(el % 60):02d}]"
        print(f"{tag} {book[:34]:<36}{msg}", flush=True)


def slug(name):
    return re.sub(r"[^A-Za-z0-9]+", "_",
                  os.path.splitext(name)[0]).strip("_").lower()[:60]


def pdf_pages(path):
    if not fitz:
        return None
    try:
        d = fitz.open(path)
        n = d.page_count
        d.close()
        return n
    except Exception:
        return None


# --------------------------------------------------------------- API calls

def submit(path, book):
    size = os.path.getsize(path) / 1048576
    for attempt in range(1, SUBMIT_TRIES + 1):
        try:
            log(book, f"上传 {size:.0f} MB (第 {attempt} 次尝试)")
            with open(path, "rb") as f:
                r = requests.post(JOB, headers=HEAD,
                                  data={"model": MODEL,
                                        "optionalPayload": json.dumps(OPT)},
                                  files={"file": f}, timeout=600)
            if r.status_code == 200:
                jid = r.json()["data"]["jobId"]
                log(book, f"已提交  job {jid}")
                return jid
            body = r.text[:160].replace("\n", " ")
            wait = min(15 * attempt, 120)
            log(book, f"提交被拒 HTTP {r.status_code}: {body}")
            log(book, f"  {wait}s 后重试")
            time.sleep(wait)
        except Exception as e:
            wait = min(10 * attempt, 90)
            log(book, f"提交出错 {type(e).__name__}: {e}  {wait}s 后重试")
            time.sleep(wait)
    log(book, f"提交失败:{SUBMIT_TRIES} 次都没成功")
    return None


def wait_for(jid, book, quiet=False):
    """Poll until the job finishes. Returns the result URL."""
    start = time.time()
    last_note = 0
    while time.time() - start < POLL_BUDGET:
        try:
            r = requests.get(f"{JOB}/{jid}", headers=HEAD, timeout=120)
            d = r.json()["data"]
        except Exception as e:
            log(book, f"查询状态出错 {type(e).__name__}: {e}  {POLL_EVERY}s 后重试")
            time.sleep(POLL_EVERY)
            continue

        state = d.get("state")
        if state == "done":
            pr = d.get("extractProgress") or {}
            log(book, f"识别完成  服务端报 {pr.get('extractedPages', '?')} 页  "
                      f"耗时 {(time.time()-start)/60:.1f} 分")
            return d["resultUrl"]["jsonUrl"]
        if state == "failed":
            log(book, f"任务失败:{str(d.get('errorMsg'))[:200]}")
            return None
        if not quiet and time.time() - last_note >= 30:
            last_note = time.time()
            pr = d.get("extractProgress") or {}
            done, tot = pr.get("extractedPages"), pr.get("totalPages")
            bar = f" {done}/{tot} 页" if tot else ""
            log(book, f"{state}{bar}  已等 {(time.time()-start)/60:.0f} 分")
        time.sleep(POLL_EVERY)
    log(book, f"超过 {POLL_BUDGET/3600:.0f} 小时仍未完成,放弃(job {jid} 仍在服务端)")
    return None


def download_raw(url, dst, book):
    log(book, "下载识别结果 ...")
    r = requests.get(url, timeout=600)
    r.raise_for_status()
    with open(dst, "w", encoding="utf-8") as f:
        f.write(r.text)
    log(book, f"结果已存 {os.path.basename(dst)}  {len(r.text)/1048576:.1f} MB")
    return r.text


# ------------------------------------------------------------ page writing

def parse_pages(raw_text, book):
    """Every page in the response, in order.

    One JSONL line can hold several pages. This is the step that has to be
    right; everything else is recoverable.
    """
    pages, lines, per_line = [], 0, []
    for ln in raw_text.strip().split("\n"):
        if not ln.strip():
            continue
        lines += 1
        try:
            results = json.loads(ln)["result"]["layoutParsingResults"]
        except Exception as e:
            log(book, f"⚠️  第 {lines} 行解析失败,跳过:{e}")
            per_line.append(0)
            continue
        per_line.append(len(results))
        for res in results:
            md = res.get("markdown") or {}
            pages.append({"text": md.get("text") or "",
                          "images": md.get("images") or {},
                          "extra": res.get("outputImages") or {}})
    shapes = sorted(set(per_line))
    log(book, f"JSONL {lines} 行 -> {len(pages)} 页"
              + (f"  (每行 {shapes[0]}-{shapes[-1]} 页)" if len(shapes) > 1
                 else f"  (每行 {shapes[0]} 页)" if shapes else ""))
    return pages


def write_pages(pages, out, book):
    for i, pg in enumerate(pages, 1):
        with open(os.path.join(out, f"page_{i:04d}.md"), "w", encoding="utf-8") as f:
            f.write(pg["text"])
    log(book, f"写出 {len(pages)} 个 page_NNNN.md")


def download_images(pages, out, book, redo=False):
    todo, already = [], 0
    for i, pg in enumerate(pages, 1):
        for rel, url in pg["images"].items():
            todo.append((url, os.path.join(out, rel)))
        for name, url in pg["extra"].items():
            todo.append((url, os.path.join(out, "imgs", f"{name}_{i:04d}.jpg")))
    if not redo:
        # a re-run should not re-fetch hundreds of files it already has
        keep = [t for t in todo if not (os.path.exists(t[1])
                                        and os.path.getsize(t[1]) > 0)]
        already = len(todo) - len(keep)
        todo = keep
    if already:
        log(book, f"插图已有 {already} 张,跳过")
    if not todo:
        log(book, "插图齐了" if already else "这本没有插图")
        return already, already
    log(book, f"下载插图 {len(todo)} 张 ({IMG_WORKERS} 路并发) ...")

    done = [0]
    def get(item):
        url, dst = item
        for a in range(3):
            try:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                r = requests.get(url, timeout=120)
                r.raise_for_status()
                with open(dst, "wb") as f:
                    f.write(r.content)
                with _print_lock:
                    done[0] += 1
                    if done[0] % 100 == 0:
                        el = time.time() - _t0
                        print(f"[{int(el//60):>3}:{int(el%60):02d}] "
                              f"{book[:34]:<36}  插图 {done[0]}/{len(todo)}", flush=True)
                return True
            except Exception:
                time.sleep(2 * (a + 1))
        return False

    with ThreadPoolExecutor(max_workers=IMG_WORKERS) as ex:
        got = sum(1 for r in ex.map(get, todo) if r)
    if got < len(todo):
        log(book, f"⚠️  插图 {len(todo)-got} 张下载失败(重跑本命令会补)")
    log(book, f"插图 {got + already}/{len(todo) + already} 张")
    return got + already, len(todo) + already


# ------------------------------------------------------------------- book

def existing_pages(out):
    if not os.path.isdir(out):
        return 0
    return len([f for f in os.listdir(out) if re.match(r"page_\d+\.md$", f)])


def do_book(pdf_dir, name, out_dir, redo=False, quiet=False):
    src = os.path.join(pdf_dir, name)
    out = os.path.join(out_dir, slug(name))
    os.makedirs(out, exist_ok=True)
    raw_path = os.path.join(out, "_raw.jsonl")
    job_path = os.path.join(out, "_job.json")
    expect = pdf_pages(src)
    book = name

    log(book, f"开始  PDF {expect if expect else '?'} 页  "
              f"{os.path.getsize(src)/1048576:.0f} MB  -> {out}")

    have = existing_pages(out)
    if not redo and expect and have >= expect:
        log(book, f"已经完整({have}/{expect} 页),跳过")
        return {"book": name, "pages": have, "expected": expect, "skipped": True}

    t0 = time.time()
    raw = None
    if not redo and os.path.exists(raw_path):
        raw = open(raw_path, encoding="utf-8").read()
        log(book, "发现已保存的识别结果,直接用它重建(不重跑 OCR)")

    if raw is None:
        jid = submit(src, book)
        if not jid:
            return {"book": name, "expected": expect, "error": "提交失败"}
        json.dump({"jobId": jid, "pdf": name, "submitted": time.time()},
                  open(job_path, "w"), ensure_ascii=False, indent=1)
        url = wait_for(jid, book, quiet)
        if not url:
            return {"book": name, "expected": expect, "error": "识别未完成"}
        try:
            raw = download_raw(url, raw_path, book)
        except Exception as e:
            return {"book": name, "expected": expect,
                    "error": f"下载结果失败 {type(e).__name__}: {e}"}

    pages = parse_pages(raw, book)
    if not pages:
        return {"book": name, "expected": expect, "error": "结果里一页都没有"}
    write_pages(pages, out, book)
    ok, total = download_images(pages, out, book, redo)

    mins = (time.time() - t0) / 60
    json.dump({"pdf": name, "pages": len(pages), "expected": expect,
               "images_ok": ok, "images_total": total,
               "minutes": round(mins, 1)},
              open(job_path, "w"), ensure_ascii=False, indent=1)

    if expect and len(pages) != expect:
        log(book, f"⚠️  PDF {expect} 页,识别出 {len(pages)} 页 —— 对不上")
    else:
        log(book, f"完成  {len(pages)} 页,插图 {ok} 张,{mins:.1f} 分钟")
    return {"book": name, "pages": len(pages), "expected": expect,
            "images": ok, "images_total": total, "minutes": round(mins, 1)}


def main(pdf_dir, out_dir, workers=2, only=None, redo=False, quiet=False):
    if not os.path.isdir(pdf_dir):
        sys.exit(f"找不到目录 {pdf_dir}")
    pdfs = sorted(f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf"))
    if only:
        pdfs = [f for f in pdfs if only.lower() in f.lower()]
    if not pdfs:
        sys.exit(f"{pdf_dir} 里没有匹配的 PDF")
    os.makedirs(out_dir, exist_ok=True)

    print(f"{len(pdfs)} 本书,{workers} 本同时跑,输出到 {out_dir}")
    if not fitz:
        print("提示:没装 pymupdf,无法核对页数是否齐全(pip install pymupdf)")
    total = 0
    for f in pdfs:
        n = pdf_pages(os.path.join(pdf_dir, f))
        total += n or 0
        print(f"  {f[:60]:<62}{n if n else '?':>5} 页")
    print(f"  {'合计':<62}{total:>5} 页\n")

    res = list(ThreadPoolExecutor(max_workers=workers).map(
        lambda f: do_book(pdf_dir, f, out_dir, redo, quiet), pdfs))

    print("\n" + "=" * 78)
    print(f"{'书':<48}{'识别页':>7}{'PDF页':>7}{'插图':>7}{'分钟':>7}")
    bad = []
    for r in res:
        if r.get("error"):
            print(f"{r['book'][:46]:<48}  ✗ {r['error'][:44]}")
            bad.append(r["book"]); continue
        exp = r.get("expected")
        okc = r.get("skipped") or (exp is None) or r["pages"] == exp
        print(f"{r['book'][:46]:<48}{r['pages']:>7}{exp if exp else '?':>7}"
              f"{r.get('images', 0):>7}{r.get('minutes', 0):>7}"
              + ("" if okc else "   ⚠️ 页数对不上"))
        if not okc:
            bad.append(r["book"])
    print(f"\n总耗时 {(time.time()-_t0)/60:.1f} 分钟")
    if bad:
        print(f"\n有问题的 {len(bad)} 本:再跑一遍同样的命令。已完整的会跳过,")
        print("识别结果已存在 _raw.jsonl 的会直接重建,不会重复消耗 OCR。")
    else:
        print("\n全部完成。")
    print(f"\n每本的页在 {out_dir}/<书名>/page_NNNN.md,插图在同目录 imgs/ 下。")


if __name__ == "__main__":
    argv = sys.argv[1:]
    pos = [a for a in argv if not a.startswith("--")]
    if len(pos) < 2:
        sys.exit(__doc__)
    def opt(k, d=None):
        return argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else d
    main(pos[0], pos[1],
         int(opt("--workers", 2)), opt("--only"),
         "--redo" in argv, "--quiet" in argv)
