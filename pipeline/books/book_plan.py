#!/usr/bin/env python3
"""Decide, page by page, which textbook pages actually need OCR — and dump
just enough structure to write the chunker against.

`probe_books.py` answered "does this book need OCR" from a 40-page sample.
This answers "which pages", which is the difference between 2366 pages of OCR
and about a thousand. It also emits the skeleton — contents tree, heading
candidates with their font sizes, worked-example markers — because a chunker
written against a guess at the layout will be wrong, and these six books are
laid out three different ways.

The output JSON is deliberately small: structure and page numbers, plus two
short text samples per book. It is not a copy of the books.

    pip install pymupdf
    python3 book_plan.py "/path/to/textbooks" [--out book_plan.json]

Then, for each job the plan lists:

    python3 ocr_book.py <pdf> <from> <to>      # 100 pages at a time, never more
"""
import json, os, re, statistics, sys
from collections import Counter

try:
    import fitz
except ImportError:
    sys.exit("需要 PyMuPDF:  pip install pymupdf")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))          # 项目根目录
try:
    from pipeline.text.clean_encoding import fix_pua
except ImportError:                     # runnable standalone next to the books
    PUA = re.compile(r"[-]")
    def fix_pua(t):
        return PUA.sub(lambda m: chr(ord(m.group(0)) - 0xF000)
                       if 0x20 <= ord(m.group(0)) - 0xF000 <= 0x7e else " ", t)

MAX_JOB_PAGES = 100        # hard limit: bigger jobs time out and are lost
MIN_CHARS = 200            # below this there is no usable text layer

EQ = re.compile(r"[=≡≈≤≥<>]")
MATHY = re.compile(r"\b(theorem|integral|integrat|derivative|differentiat|"
                   r"equation|prove|substitut|coefficient|matrix|matrices|"
                   r"vector|probability|expansion|gradient|logarithm|"
                   r"trigonometr|binomial|hyperbolic|eigen)\b", re.I)
# a worked example is atomic — the chunker must never cut one in half, so find
# out now how each book labels them
EXAMPLE = re.compile(r"^\s*(WORKED\s+EXAMPLE|Example|EXAMPLE|Exercise|EXERCISE|"
                     r"Solution|SOLUTION|Key point|KEY POINT|Activity|"
                     r"Question)\b[\s\d.:]*", re.M)
WORD = re.compile(r"[A-Za-z][A-Za-z\-']+")


def page_stats(page):
    raw = page.get_text()
    t = fix_pua(raw)
    words = WORD.findall(t)
    singles = sum(1 for w in words if len(w) == 1)
    return {
        "chars": len(t.strip()),
        "eq": len(EQ.findall(t)),
        "mathy": bool(MATHY.search(t)),
        "orphan": round(singles / len(words), 3) if len(words) >= 20 else 0.0,
        "images": len(page.get_images()),
        "examples": len(EXAMPLE.findall(t)),
    }


def needs_ocr(s):
    """Why this page needs re-reading, or None."""
    if s["chars"] < MIN_CHARS:
        return "无文本层"
    if s["mathy"] and s["eq"] == 0:
        # the failure already seen on maths mark schemes: prose survives,
        # every '=' and fraction bar is dropped
        return "数学页但一个等号都没有"
    if s["orphan"] > 0.45:
        return "公式被打散成单字符"
    return None


def batches(pages, limit=MAX_JOB_PAGES):
    """Pages to submit per job — the pages themselves, not ranges spanning them.

    An earlier version merged nearby runs into ranges so that scattered formula
    pages would not each become a one-page job. That traded one problem for
    two: it re-read 94 pages that did not need it, and it still left Computer
    Science with 18 jobs averaging 2.8 pages, where the queue wait dwarfs the
    recognition. A job does not have to be a contiguous range — the pages can
    be lifted into one temporary PDF in order and mapped back afterwards — so
    the right unit is simply the next 100 pages that need doing.
    """
    return [pages[i:i + limit] for i in range(0, len(pages), limit)]


def as_ranges(pages):
    """Compact display form: [1,2,3,7,9,10] -> "1-3, 7, 9-10"."""
    if not pages:
        return ""
    out, a, prev = [], pages[0], pages[0]
    for p in pages[1:] + [None]:
        if p != prev + 1:
            out.append(f"{a}-{prev}" if prev > a else f"{a}")
            a = p
        prev = p if p is not None else prev
    return ", ".join(out)


def headings(doc, sample=60):
    """Font sizes in the book, and what the larger ones say.

    Chapter and section headings are set larger than body text, so the body
    size is the mode of the size histogram and anything meaningfully above it
    is a heading candidate. Reported rather than acted on — the threshold
    differs per book and is worth eyeballing once.
    """
    sizes = Counter()
    spans = []
    step = max(1, doc.page_count // sample)
    for pno in range(0, doc.page_count, step):
        for b in doc[pno].get_text("dict")["blocks"]:
            if b.get("type"):
                continue
            for l in b["lines"]:
                for s in l["spans"]:
                    txt = " ".join(s["text"].split())
                    if not txt:
                        continue
                    sz = round(s["size"], 1)
                    sizes[sz] += len(txt)
                    spans.append((sz, s["font"], txt, pno))
    if not sizes:
        return {"body_size": None, "candidates": []}
    body = sizes.most_common(1)[0][0]
    cand = [(sz, f, t, p) for sz, f, t, p in spans
            if sz >= body * 1.15 and 2 < len(t) < 70]
    per_size, out = Counter(), []
    for sz, f, t, p in sorted(cand, key=lambda x: -x[0]):
        if per_size[sz] >= 3:          # three examples of each size is plenty
            continue
        per_size[sz] += 1
        out.append({"size": sz, "font": f, "text": t, "page": p})
        if len(out) >= 24:
            break
    return {"body_size": body,
            "size_histogram": dict(sizes.most_common(8)),
            "candidates": out}


def analyse(path):
    doc = fitz.open(path)
    name = os.path.basename(path)
    stats = [page_stats(doc[i]) for i in range(doc.page_count)]
    todo = [i for i, s in enumerate(stats) if needs_ocr(s)]
    reasons = Counter(needs_ocr(s) for s in stats if needs_ocr(s))

    toc = [{"level": lv, "title": t, "page": pg} for lv, t, pg in doc.get_toc()]
    ex_pages = [i for i, s in enumerate(stats) if s["examples"]]
    sample_pages = [i for i, s in enumerate(stats) if s["chars"] > 800][:2]

    out = {
        "file": name,
        "pages": doc.page_count,
        "median_chars": statistics.median(s["chars"] for s in stats),
        "toc": toc,
        "toc_levels": max([t["level"] for t in toc], default=0),
        "headings": headings(doc),
        "example_marker_pages": len(ex_pages),
        "ocr_pages": len(todo),
        "ocr_reasons": dict(reasons),
        # 1-based page numbers, the way a human counts them
        "ocr_page_list": [i + 1 for i in todo],
        "ocr_jobs": [[b[0] + 1, b[-1] + 1] for b in batches(todo)],
        "samples": [{"page": p + 1, "text": fix_pua(doc[p].get_text())[:900]}
                    for p in sample_pages],
    }
    doc.close()
    return out


def main(folder, out="book_plan.json"):
    pdfs = sorted(f for f in os.listdir(folder) if f.lower().endswith(".pdf"))
    if not pdfs:
        sys.exit(f"{folder} 里没有 PDF")
    books, tot_pages, tot_ocr, tot_jobs = [], 0, 0, 0
    for f in pdfs:
        b = analyse(os.path.join(folder, f))
        books.append(b)
        tot_pages += b["pages"]; tot_ocr += b["ocr_pages"]
        tot_jobs += -(-b["ocr_pages"] // MAX_JOB_PAGES)
        print(f"\n{'='*70}\n{f[:66]}")
        print(f"  {b['pages']} 页,正文中位数 {b['median_chars']:.0f} 字符 | "
              f"目录 {len(b['toc'])} 条 {b['toc_levels']} 层 | "
              f"例题标记出现在 {b['example_marker_pages']} 页")
        if b["ocr_pages"]:
            why = ", ".join(f"{k} {v}页" for k, v in b["ocr_reasons"].items())
            print(f"  需要 OCR:{b['ocr_pages']} 页({b['ocr_pages']/b['pages']*100:.0f}%)"
                  f" —— {why}")
            nb = len(b["ocr_jobs"])
            print(f"  分成 {nb} 个任务(每个 ≤{MAX_JOB_PAGES} 页),页码:")
            print(f"      {as_ranges(b['ocr_page_list'])[:150]}"
                  + (" ..." if len(as_ranges(b['ocr_page_list'])) > 150 else ""))
        else:
            print("  不用 OCR,文本层直接可用")
        h = b["headings"]
        if h["candidates"]:
            print(f"  正文字号 {h['body_size']},更大的字号样本:")
            for c in h["candidates"][:5]:
                print(f"      {c['size']:>5}  {c['text'][:52]}")

    json.dump({"books": books}, open(out, "w"), ensure_ascii=False, indent=1)
    print(f"\n{'='*70}")
    print(f"合计 {tot_pages} 页,需要 OCR {tot_ocr} 页 "
          f"({tot_ocr/tot_pages*100:.0f}%),共 {tot_jobs} 个任务")
    print(f"结构和页码清单 -> {out}(几十 KB,不含书的正文,可以直接发回来)")


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    o = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "book_plan.json"
    main(a[0] if a else ".", o)
