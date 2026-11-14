#!/usr/bin/env python3
"""OCR the whole TMUA/TARA bank, reusing the textbook pipeline.

    python3 ocr_bank.py <bank_dir> <out_dir> [workers]

Same engine as qb/ocr_books.py — one job per PDF, whole file submitted, pages
taken from layoutParsingResults, figures downloaded to the paths the markdown
references. The only difference is the walk: the bank is nested by exam, and
the output mirrors that nesting so TMUA/papers/x.pdf becomes
<out>/TMUA/papers/x/page_NNNN.md.

Resumable per PDF: an output folder whose page count matches is skipped.
"""
import os, sys, threading, time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))          # qb/ —— 直接跑脚本时也 import 得到包
from lib import paths
from pipeline.ocr import ocr_books as ob

lock = threading.Lock()


def all_pdfs(root):
    out = []
    for r, _d, fs in os.walk(root):
        for f in sorted(fs):
            if f.endswith(".pdf"):
                out.append(os.path.relpath(os.path.join(r, f), root))
    return out


def do_one(root, rel, out_root):
    src = os.path.join(root, rel)
    out = os.path.join(out_root, rel[:-4])          # strip .pdf
    os.makedirs(out, exist_ok=True)
    name = os.path.basename(rel)
    expect = ob.pdf_pages(src)
    have = ob.existing_pages(out)
    if expect and have >= expect:
        return {"rel": rel, "pages": have, "expected": expect, "skipped": True}

    raw_path = os.path.join(out, "_raw.jsonl")
    raw = open(raw_path, encoding="utf-8").read() if os.path.exists(raw_path) else None
    if raw is None:
        jid = ob.submit(src, name)
        if not jid:
            return {"rel": rel, "expected": expect, "error": "提交失败"}
        url = ob.wait_for(jid, name, quiet=True)
        if not url:
            return {"rel": rel, "expected": expect, "error": "识别未完成"}
        try:
            raw = ob.download_raw(url, raw_path, name)
        except Exception as e:
            return {"rel": rel, "expected": expect,
                    "error": f"{type(e).__name__}: {e}"}
    pages = ob.parse_pages(raw, name)
    if not pages:
        return {"rel": rel, "expected": expect, "error": "结果为空"}
    ob.write_pages(pages, out, name)
    ok, total = ob.download_images(pages, out, name)
    return {"rel": rel, "pages": len(pages), "expected": expect,
            "images": ok, "images_total": total}


def main(root, out_root, workers=4):
    pdfs = all_pdfs(root)
    print(f"{len(pdfs)} 个 PDF,{workers} 并发", flush=True)
    t0 = time.time()
    res = list(ThreadPoolExecutor(max_workers=workers).map(
        lambda r: do_one(root, r, out_root), pdfs))
    print(f"\n用时 {(time.time()-t0)/60:.1f} 分钟")
    bad = []
    for r in res:
        if r.get("error"):
            bad.append(r); print(f"  ✗ {r['rel']}  {r['error'][:60]}")
        elif r.get("expected") and r["pages"] != r["expected"] and not r.get("skipped"):
            bad.append(r); print(f"  ⚠️ {r['rel']}  {r['pages']}/{r['expected']} 页")
    ok = len(res) - len(bad)
    imgs = sum(r.get("images", 0) for r in res)
    print(f"完好 {ok}/{len(res)},插图 {imgs} 张"
          + ("" if not bad else " —— 重跑同一命令补失败的"))


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0] if a else paths.BANK, a[1] if len(a) > 1 else paths.BANK_OCR,
         int(a[2]) if len(a) > 2 else 4)
