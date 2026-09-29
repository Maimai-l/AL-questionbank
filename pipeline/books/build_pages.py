#!/usr/bin/env python3
"""Produce one complete page_NNNN.md folder per textbook.

This is the step that was missing. `book_plan.py` decides which pages the text
layer cannot handle, and OCR fixes those — but the *other* pages still need to
exist, or the chapter merge finds a folder with a quarter of the book in it and
reports everything as missing. So both halves are written here:

    text layer good   ->  extracted locally, free, instant
    text layer broken ->  OCR'd, 100 pages at a time

The result is a folder numbered by the book's own pages, which is what
`split_chapters.py` and `map_ocr_pages.py` both expect. Resumable: a page that
already has a file is left alone, so an interrupted run costs nothing.

    python3 build_pages.py book_plan.json <textbooks_dir> <out_dir> \\
            [--only "Pure Mathematics 2"] [--force-ocr "Pure Mathematics 2"] \\
            [--workers 3] [--dry]

--force-ocr NAME re-reads that book whole; --force-ocr all does every book.

Both readings are kept, because deciding which is better is a question with an
answer and guessing at it has already cost us once:

    <out>/<book>/text/page_0001.md   the PDF's own text layer, always written
    <out>/<book>/ocr/page_0001.md    what the model read, where OCR ran
    <out>/<book>/page_0001.md        the one downstream uses

Writing the text layer is free, so it is written for every page of every book
even when OCR is also going to run. `compare_layers.py` then measures the two
against each other instead of us assuming.
"""
import json, os, re, sys, tempfile, threading, time
from concurrent.futures import ThreadPoolExecutor

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))          # 项目根目录
from pipeline.text.clean_encoding import fix_pua
from pipeline.ocr import paddle

try:
    import fitz
except ImportError:
    sys.exit("需要 PyMuPDF:  pip install pymupdf")

SLUG = re.compile(r"[^A-Za-z0-9]+")
lock = threading.Lock()


def slug(name):
    return SLUG.sub("_", os.path.splitext(name)[0]).strip("_").lower()[:60]


def page_path(d, n):
    return os.path.join(d, f"page_{n:04d}.md")


def write_text_layer(doc, out):
    """Every page's text layer, into text/. Free, so no reason to be selective."""
    d = os.path.join(out, "text")
    os.makedirs(d, exist_ok=True)
    n = 0
    for p in range(1, doc.page_count + 1):
        if os.path.exists(page_path(d, p)):
            continue
        t = fix_pua(doc[p - 1].get_text())
        with open(page_path(d, p), "w", encoding="utf-8") as f:
            f.write("<!-- source: text-layer -->\n\n" + t.strip() + "\n")
        n += 1
    return n


def choose(out, total):
    """Point page_NNNN.md at the OCR reading where there is one, else the text.

    A separate step so the choice can be revisited — re-running it after
    compare_layers.py says something different costs nothing.
    """
    import shutil
    picked = {"ocr": 0, "text": 0, "none": 0}
    for p in range(1, total + 1):
        o, t = page_path(os.path.join(out, "ocr"), p), \
               page_path(os.path.join(out, "text"), p)
        src = o if os.path.exists(o) else (t if os.path.exists(t) else None)
        if src is None:
            picked["none"] += 1; continue
        picked["ocr" if src is o else "text"] += 1
        shutil.copyfile(src, page_path(out, p))
    return picked


def extract_list(src, pages):
    """Lift an arbitrary set of pages into one temporary PDF, in order.

    A job does not have to be a contiguous range. Without this, Computer
    Science's 33 scattered formula pages became 18 separate submissions whose
    queue wait dwarfed the recognition; with it they are one job.
    """
    doc = fitz.open(src)
    out = fitz.open()
    for p in pages:
        out.insert_pdf(doc, from_page=p - 1, to_page=p - 1)
    fd, path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    out.save(path)
    out.close(); doc.close()
    return path


def ocr_pages(pdf_path, pages, out_root):
    out = os.path.join(out_root, "ocr")
    os.makedirs(out, exist_ok=True)
    label = f"p{pages[0]}-{pages[-1]}" + (f" ({len(pages)} 页)" if
                                          pages[-1] - pages[0] + 1 != len(pages) else "")
    tmp = None
    try:
        tmp = extract_list(pdf_path, pages)
        jid = paddle.submit(tmp)
        if not jid:
            return {"label": label, "error": "提交失败(重试 40 次后放弃)"}
        got = paddle.collect(jid)
    except Exception as e:
        return {"label": label, "error": f"{type(e).__name__}: {e}"}
    finally:
        if tmp and os.path.exists(tmp):
            os.unlink(tmp)

    if len(got) != len(pages):
        # Silently mis-numbering pages is how the first run lost three quarters
        # of a book while looking fine. Refuse instead of guessing.
        return {"label": label,
                "error": f"返回 {len(got)} 页,应为 {len(pages)} 页 —— 页码对不上,已跳过"}
    imgs = 0
    for pg, no in zip(got, pages):
        with open(page_path(out, no), "w", encoding="utf-8") as f:
            f.write("<!-- source: ocr -->\n\n" + (pg["text"] or "") + "\n")
        imgs += paddle.fetch_images(pg, out, no)
    return {"label": label, "pages": len(pages), "images": imgs}


def batches(pages, limit=paddle.MAX_PAGES):
    ps = sorted(pages)
    return [ps[i:i + limit] for i in range(0, len(ps), limit)]


def main(plan_path, folder, out_root, only=None, force=None, workers=3, dry=False):
    plan = json.load(open(plan_path))
    books = [b for b in plan["books"]
             if not only or only.lower() in b["file"].lower()]
    if not books:
        sys.exit(f"没有书名含 {only!r}")

    jobs, summary = [], []
    for b in books:
        pdf = os.path.join(folder, b["file"])
        if not os.path.exists(pdf):
            print(f"⚠️  找不到 {pdf},跳过"); continue
        out = os.path.join(out_root, slug(b["file"]))
        os.makedirs(out, exist_ok=True)
        doc = fitz.open(pdf)
        total = doc.page_count

        forced = bool(force and (force.lower() == "all"
                                 or force.lower() in b["file"].lower()))
        # the page list is authoritative; ocr_jobs is only a display grouping
        listed = b.get("ocr_page_list")
        if listed is None:      # plan produced by an older book_plan.py
            listed = [p for a, z in b["ocr_jobs"] for p in range(a, z + 1)]
        want_ocr = set(range(1, total + 1)) if forced else set(listed)
        text_pages = [p for p in range(1, total + 1) if p not in want_ocr]

        wrote = 0 if dry else write_text_layer(doc, out)
        doc.close()
        ocr_dir = os.path.join(out, "ocr")
        todo = [p for p in sorted(want_ocr)
                if not os.path.exists(page_path(ocr_dir, p))]
        bs = batches(todo)
        for grp in bs:
            jobs.append((pdf, grp, out, b["file"]))
        summary.append((b["file"], total, len(text_pages), wrote,
                        len(want_ocr), len(todo), len(bs), forced, out))

    print(f"{'书':<42}{'总页':>5}{'文本层已存':>11}{'要OCR':>7}{'(还欠)':>8}{'任务':>5}")
    for f, total, tp, wrote, op, todo, nr, forced, out in summary:
        print(f"{f[:40]:<42}{total:>5}{wrote:>11}{op:>7}{todo:>8}{nr:>5}"
              + ("  [强制全本]" if forced else ""))
        print(f"{'':<42}-> {out}")
    tot_ocr = sum(s[5] for s in summary)
    print(f"\n本次要 OCR {tot_ocr} 页,分 {len(jobs)} 个任务,{workers} 个并发")
    if dry:
        print("(--dry,没有真的提交)")
        return
    if not jobs:
        print("没有待办的 OCR。整理 page_NNNN.md ...")
        for f, total, tp, wrote, op, todo, nr, forced, out in summary:
            pk = choose(out, total)
            print(f"  {out}  OCR {pk['ocr']} 页 / 文本层 {pk['text']} 页"
                  + (f" / 缺 {pk['none']} 页" if pk["none"] else ""))
        return
    if requests_missing():
        sys.exit("需要 requests:  pip install requests")

    t0, n = time.time(), [0]

    def work(j):
        pdf, grp, out, name = j
        r = ocr_pages(pdf, grp, out)
        with lock:
            n[0] += 1
            el = (time.time() - t0) / 60
            tag = ("ERR " + r["error"][:70]) if r.get("error") else \
                  f"{r['pages']} 页,图 {r['images']} 张"
            print(f"  [{n[0]}/{len(jobs)}] {name[:26]} {r['label']}  {tag}  "
                  f"({el:.0f} 分,预计还要 {el/n[0]*(len(jobs)-n[0]):.0f} 分)", flush=True)
        return r

    with ThreadPoolExecutor(max_workers=workers) as ex:
        res = list(ex.map(work, jobs))
    errs = [r for r in res if r.get("error")]
    print(f"\n用时 {(time.time()-t0)/60:.1f} 分钟,失败 {len(errs)} 个任务"
          + (" —— 再跑一次同样的命令只补失败的部分" if errs else ""))

    for f, total, tp, wrote, op, todo, nr, forced, out in summary:
        pk = choose(out, total)
        have = pk["ocr"] + pk["text"]
        mark = "✅" if have >= total else "⚠️ "
        print(f"  {mark} {out}  {have}/{total} 页 "
              f"(OCR {pk['ocr']} / 文本层 {pk['text']}"
              + (f" / 缺 {pk['none']}" if pk["none"] else "") + ")")
    print("\n两份读法都留着了,接下来:\n"
          "  python3 compare_layers.py <out_dir>     # 逐页比对,看文本层到底够不够")


def requests_missing():
    try:
        import requests  # noqa: F401
        return False
    except ImportError:
        return True


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if len(a) < 3:
        sys.exit(__doc__)
    g = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
    main(a[0], a[1], a[2], g("--only"), g("--force-ocr"),
         int(g("--workers") or 3), "--dry" in sys.argv)
