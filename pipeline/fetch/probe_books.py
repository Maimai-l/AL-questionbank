#!/usr/bin/env python3
"""Decide, per textbook, whether OCR is actually needed.

Running PaddleOCR over six textbooks is thousands of pages. Before paying for
that, check what is already in the PDF:

* the embedded bookmark tree — if it is there, the whole chapter/section
  structure is free and no OCR can improve on it;
* the text layer's health. The failure we already hit on mark schemes is that
  `pdftotext` silently drops '=' and fraction bars from mathematical
  typesetting, so a page can look full of text and still be useless. The tell
  is an equation-free maths page, plus Private Use Area codepoints where the
  Symbol font was.

Verdict per book, and per sampled page, so OCR can be aimed at the pages that
need it instead of the whole file.

    pip install pymupdf
    python3 probe_books.py "/path/to/textbooks" [--sample 40]
"""
import os, re, sys, statistics

try:
    import fitz
except ImportError:
    sys.exit("需要 PyMuPDF:  pip install pymupdf")

PUA = re.compile(r"[-]")
MATHY = re.compile(r"\b(theorem|integral|derivative|equation|prove|substitut|"
                   r"differentiat|coefficient|matrix|vector|probability)\b", re.I)
EQ = re.compile(r"[=≡≈<>≤≥]")


def probe_page(page):
    t = page.get_text()
    n = len(t.strip())
    return {
        "chars": n,
        "eq": len(EQ.findall(t)),
        "pua": len(PUA.findall(t)),
        "mathy": bool(MATHY.search(t)),
        "images": len(page.get_images()),
    }


def verdict(pages):
    """What to do with this book."""
    real = [p for p in pages if p["chars"] > 200]
    if len(real) < len(pages) * 0.5:
        return ("扫描件或文本层残缺", "整本 OCR")
    maths = [p for p in real if p["mathy"]]
    if maths:
        noeq = sum(1 for p in maths if p["eq"] == 0)
        if noeq > len(maths) * 0.4:
            return (f"数学页里 {noeq}/{len(maths)} 页一个等号都没有 —— "
                    f"等号被文本层吞了", "公式页 OCR,正文用文本层")
    if sum(p["pua"] for p in real):
        return ("有 Symbol 字体的 PUA 码位", "先跑 clean_encoding.fix_pua,再看")
    return ("文本层完整", "不用 OCR,直接抽文本")


def main(folder, sample=40):
    pdfs = sorted(f for f in os.listdir(folder) if f.lower().endswith(".pdf"))
    if not pdfs:
        sys.exit(f"{folder} 里没有 PDF")
    for f in pdfs:
        doc = fitz.open(os.path.join(folder, f))
        n = doc.page_count
        toc = doc.get_toc()
        # skip front matter; sample evenly across the body
        lo, hi = int(n * 0.08), int(n * 0.95)
        step = max(1, (hi - lo) // sample)
        idx = list(range(lo, hi, step))[:sample]
        pages = [probe_page(doc[i]) for i in idx]

        why, todo = verdict(pages)
        chars = statistics.median(p["chars"] for p in pages)
        maths = sum(1 for p in pages if p["mathy"])
        noeq = [i for i, p in zip(idx, pages) if p["mathy"] and p["eq"] == 0]

        print(f"\n{'='*70}\n{f[:66]}")
        print(f"  {n} 页 | 抽查 {len(idx)} 页 | 每页正文中位数 {chars:.0f} 字符 "
              f"| 图 {sum(p['images'] for p in pages)}")
        if toc:
            depth = max(lv for lv, _, _ in toc)
            top = [t for lv, t, _ in toc if lv == 1]
            print(f"  内嵌书签: {len(toc)} 条,{depth} 层 —— 章节树白送,不用 OCR")
            for t in top[:6]:
                print(f"      {t[:60]}")
            if len(top) > 6:
                print(f"      ... 共 {len(top)} 章")
        else:
            print("  内嵌书签: 无 —— 章节结构要从正文标题里认")
        print(f"  数学页 {maths}/{len(idx)}"
              + (f",其中 {len(noeq)} 页无等号(页码 {noeq[:8]})" if noeq else ""))
        print(f"  判定: {why}\n  → {todo}")
        doc.close()

    print(f"\n{'='*70}")
    print("下一步:凡是判定'不用 OCR'的,先按书签切章节抽正文;"
          "\n只把'公式页 OCR'的那些页号喂给 Paddle。")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    s = 40
    if "--sample" in sys.argv:
        s = int(sys.argv[sys.argv.index("--sample") + 1])
    main(args[0] if args else ".", s)
