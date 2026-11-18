#!/usr/bin/env python3
"""OCR a page range of one textbook, at most 100 pages per job, into page_NNNN.md.

    python3 pipeline/books/ocr_book_pages.py ocr <book.pdf> <book> --from 12 --to 227 \
            [--chunk 100] [--workers 3] [--strip REGEX ...] [--keep-header REGEX ...]
    python3 pipeline/books/ocr_book_pages.py pages <book> [--strip REGEX ...] [--keep-header REGEX ...]

Read the PDF with `python3 -I` when it was downloaded (the script puts the project
root on sys.path itself).

`ocr_books.py` sends a whole PDF as one job. That is over the 100-page limit
(docs/pipeline.md) for most books, and it writes every figure to imgs/<name>
where <name> is only the box on the page ("img_in_image_box_75_120_320_313.jpg"),
so two pages with a figure in the same place overwrite each other. This uses the
same API calls (`ocr_books.submit`, `wait_for`, `download_raw`, `parse_pages`,
`download_images`) and differs in three ways:

  * the range is cut into parts of at most --chunk pages, each its own job;
  * pages are numbered by the PDF page they came from (page_0084.md is PDF page 84),
    which is what `split_chapters.py` expects;
  * figures are saved as imgs/p0084_<name>, and the markdown is rewritten to match.

Everything lands under raw/book_ocr/<book>/ (lib/paths.py):

    parts/<book>_p0012-0111/_raw.jsonl   the API's untouched answer, one per part
    parts/<book>_p0012-0111/_job.json    job id, page range, minutes
    pages/page_0012.md                   one file per PDF page
    pages/imgs/p0012_....jpg             figures
    _book.json                           the PDF, the parts, --strip and --keep-header

`pages` rebuilds pages/ from the saved _raw.jsonl files without calling the API
(figures already on disk are not fetched again). --strip removes every match of
a regular expression from the page text, for a site watermark printed on every
page. Running headers, footers and page numbers are not in the markdown: the
model labels them `header`/`footer` and leaves them out. Some books print a
section's title in the same top band as the running header, and it is dropped
with it; --keep-header REGEX puts header blocks that match back at the top of
the page as "## …". Both kinds of pattern are kept in _book.json, so a later
`pages` run reuses them.
"""
import argparse, json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))          # 项目根目录
from lib import paths
from pipeline.ocr import ocr_books

MAX_PAGES = 100          # a single job beyond this risks timing out (docs/pipeline.md)
IMG_REF = re.compile(r"(?<![\w/])imgs/([^\s\"')]+)")


def book_dir(book):
    return os.path.join(paths.RAW, "book_ocr", book)


def load_meta(book):
    p = os.path.join(book_dir(book), "_book.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


def save_meta(book, meta):
    os.makedirs(book_dir(book), exist_ok=True)
    with open(os.path.join(book_dir(book), "_book.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)


def part_name(book, a, z):
    return f"{book}_p{a:04d}-{z:04d}"


def cut(pdf, a, z, dst):
    """PDF pages a..z (1-based, inclusive) as their own file."""
    import fitz
    src = fitz.open(pdf)
    out = fitz.open()
    out.insert_pdf(src, from_page=a - 1, to_page=z - 1)
    out.save(dst, garbage=3, deflate=True)
    out.close()
    src.close()


def run_part(pdf, book, a, z):
    """One job: cut, submit, wait, keep the raw answer. Returns a status dict."""
    name = part_name(book, a, z)
    out = os.path.join(book_dir(book), "parts", name)
    raw = os.path.join(out, "_raw.jsonl")
    if os.path.exists(raw) and os.path.getsize(raw) > 0:
        ocr_books.log(name, "已有 _raw.jsonl,跳过")
        return {"part": name, "skipped": True}
    os.makedirs(out, exist_ok=True)
    tmp = os.path.join(out, name + ".pdf")
    t0 = time.time()
    try:
        cut(pdf, a, z, tmp)
        jid = ocr_books.submit(tmp, name)
        if not jid:
            return {"part": name, "error": "提交失败"}
        url = ocr_books.wait_for(jid, name, quiet=True)
        if not url:
            return {"part": name, "error": "识别未完成", "job": jid}
        text = ocr_books.download_raw(url, raw, name)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    n = len(ocr_books.parse_pages(text, name))
    mins = round((time.time() - t0) / 60, 1)
    json.dump({"jobId": jid, "pdf": os.path.basename(pdf), "from": a, "to": z,
               "pages": n, "minutes": mins},
              open(os.path.join(out, "_job.json"), "w"), ensure_ascii=False, indent=1)
    if n != z - a + 1:
        return {"part": name, "error": f"返回 {n} 页,应为 {z - a + 1} 页"}
    return {"part": name, "pages": n, "minutes": mins}


def clean(text, strip):
    for pat in strip:
        text = re.sub(pat, "", text)
    # a watermark that was a line of its own leaves an empty line behind
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


def read_raw(path):
    """[{text, images, headers}] per page, in order, from one _raw.jsonl.

    Like `ocr_books.parse_pages` (one line can hold several pages), plus the
    text of the blocks the model labelled `header`, which the markdown leaves out.
    """
    pages = []
    for ln in open(path, encoding="utf-8"):
        if not ln.strip():
            continue
        for res in json.loads(ln)["result"]["layoutParsingResults"]:
            md = res.get("markdown") or {}
            blocks = (res.get("prunedResult") or {}).get("parsing_res_list") or []
            pages.append({"text": md.get("text") or "", "images": md.get("images") or {},
                          "headers": [" ".join(b.get("block_content", "").split())
                                      for b in blocks if b.get("block_label") == "header"]})
    return pages


def build_pages(book, strip=None, keep=None):
    """pages/page_NNNN.md and pages/imgs/ from every part's _raw.jsonl."""
    meta = load_meta(book)
    strip = strip if strip is not None else meta.get("strip", [])
    keep = keep if keep is not None else meta.get("keep_header", [])
    out = os.path.join(book_dir(book), "pages")
    os.makedirs(out, exist_ok=True)
    pages, last = [], None
    for part in sorted(meta.get("parts", []), key=lambda p: p["from"]):
        raw = os.path.join(book_dir(book), "parts", part_name(book, part["from"], part["to"]),
                           "_raw.jsonl")
        if not os.path.exists(raw):
            print(f"缺 {raw},先跑 ocr")
            continue
        got = read_raw(raw)
        if len(got) != part["to"] - part["from"] + 1:
            sys.exit(f"{raw}: {len(got)} 页,应为 {part['to'] - part['from'] + 1} 页")
        for i, pg in enumerate(got):
            no = part["from"] + i
            pre = f"p{no:04d}_"
            images = {}
            for rel, url in pg["images"].items():
                d, base = os.path.split(rel)
                images[os.path.join(d, pre + base)] = url
            text = IMG_REF.sub(lambda m: "imgs/" + pre + m.group(1), pg["text"])
            heads = [h for h in pg["headers"] if any(re.search(k, h) for k in keep)]
            # a two-page section repeats its band ("EXAM PRACTICE") on the second page
            if heads and heads != last:
                text = "".join(f"## {h}\n\n" for h in heads) + text
            last = heads or last
            with open(os.path.join(out, f"page_{no:04d}.md"), "w", encoding="utf-8") as f:
                f.write(clean(text, strip))
            # outputImages are the layout-detection debug pictures; nothing refers to them
            pages.append({"text": "", "images": images, "extra": {}})
    ok, total = ocr_books.download_images(pages, out, book)
    print(f"{book}: {len(pages)} 页 -> {out},插图 {ok}/{total}")
    return len(pages)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["ocr", "pages"])
    ap.add_argument("args", nargs="+", help="ocr: <pdf> <book>;  pages: <book>")
    ap.add_argument("--from", dest="a", type=int, default=1)
    ap.add_argument("--to", dest="z", type=int)
    ap.add_argument("--chunk", type=int, default=MAX_PAGES)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--strip", action="append", help="regular expression removed from every page")
    ap.add_argument("--keep-header", action="append",
                    help="a header block matching this regular expression is kept, as a ## heading")
    o = ap.parse_args()

    if o.cmd == "pages":
        meta = load_meta(o.args[0])
        for k, v in (("strip", o.strip), ("keep_header", o.keep_header)):
            if v is not None:
                meta[k] = v
        save_meta(o.args[0], meta)
        build_pages(o.args[0])
        return
    if len(o.args) != 2:
        sys.exit("用法: ocr_book_pages.py ocr <book.pdf> <book> --from A --to B")
    pdf, book = os.path.abspath(o.args[0]), o.args[1]
    import fitz
    n = fitz.open(pdf).page_count
    z = min(o.z or n, n)
    chunk = min(o.chunk, MAX_PAGES)
    ranges = [(s, min(s + chunk - 1, z)) for s in range(o.a, z + 1, chunk)]
    meta = load_meta(book)
    meta.update({"pdf": os.path.basename(pdf), "pdf_pages": n,
                 "parts": [{"from": s, "to": e} for s, e in ranges]})
    for k, v in (("strip", o.strip), ("keep_header", o.keep_header)):
        if v is not None:
            meta[k] = v
    save_meta(book, meta)
    print(f"{book}: PDF {n} 页,OCR p{o.a}-{z},{len(ranges)} 个任务,{o.workers} 个并发")
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=o.workers) as ex:
        res = list(ex.map(lambda r: run_part(pdf, book, *r), ranges))
    for r in res:
        print("  ", r)
    print(f"OCR 用时 {(time.time() - t0) / 60:.1f} 分钟")
    if any(r.get("error") for r in res):
        sys.exit("有任务失败;再跑同样的命令只补失败的部分")
    build_pages(book)


if __name__ == "__main__":
    main()
