#!/usr/bin/env python3
"""Export just the bookmarks and page counts from a folder of PDFs.

    python3 dump_toc.py <pdf_dir> <out.json>

Chapter boundaries live in the PDF's embedded contents tree, so splitting
chapters normally needs the PDF itself. That is hundreds of megabytes to move
around for a few kilobytes of information. This writes only the part that
matters, so the splitting can happen anywhere.
"""
import json, os, sys

try:
    import fitz
except ImportError:
    sys.exit("需要 PyMuPDF:  pip install pymupdf")


def main(pdf_dir, out="toc.json"):
    pdfs = sorted(f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf"))
    if not pdfs:
        sys.exit(f"{pdf_dir} 里没有 PDF")
    data = {}
    for f in pdfs:
        d = fitz.open(os.path.join(pdf_dir, f))
        toc = [[lv, t, p] for lv, t, p in d.get_toc()]
        data[f] = {"pages": d.page_count, "toc": toc}
        d.close()
        print(f"{f[:58]:<60}{data[f]['pages']:>5} 页,书签 {len(toc):>4} 条")
    json.dump(data, open(out, "w"), ensure_ascii=False, indent=1)
    print(f"\n-> {out}  ({os.path.getsize(out)/1024:.0f} KB)")


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if not a:
        sys.exit(__doc__)
    main(a[0], a[1] if len(a) > 1 else "toc.json")
