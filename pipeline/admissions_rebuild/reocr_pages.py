#!/usr/bin/env python3
"""Re-OCR the specific pages whose option blocks the first pass dropped.

    python3 reocr_pages.py [pages.json]      # REOCR_DPI=260 换清晰度

Reads questions_adm.json, finds every question whose answer letter is not
among its options (or whose text is implausibly short), renders those exact
PDF pages at high resolution, and sends them back through the same OCR — one
mini-PDF per paper, pages mapped back by position. The originals are kept as
page_NNNN.md.bak.

Rendering at 220 dpi matters: the first pass read the embedded PDF directly,
and on these pages the option grid fell below whatever the layout model needed.
A crisp bitmap of the same page is a different, easier problem.
"""
import json, os, re, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))          # qb/ —— 直接跑脚本时也 import 得到包
from lib import paths
from pipeline.ocr import ocr_books as ob
import fitz

ROOT = paths.BANK_OCR
BANK = paths.BANK


def pdf_for(q):
    if q["exam"] == "TMUA":
        return (f"{BANK}/TMUA/papers/TMUA-{q['year']}-paper-{q['paper']}.pdf",
                f"{ROOT}/TMUA/papers/TMUA-{q['year']}-paper-{q['paper']}")
    sub = "TSA_section1" if q["exam"] == "TSA" else "BMAT_section1"
    return (f"{BANK}/TARA/{sub}/papers/{q['exam']}-{q['year']}-S1.pdf",
            f"{ROOT}/TARA/{sub}/papers/{q['exam']}-{q['year']}-S1")


def needs_fix(q):
    a = q.get("answer") or ""
    if len(q.get("text", "")) < 40:
        return True
    if re.fullmatch(r"[A-H]", a):
        return not (a in q.get("options", [])
                    or re.search(rf"^{a}[\s.):]", q["text"], re.M))
    return False


def main():
    # 渲染清晰度:同一张图再读往往得到同样的错误,换个清晰度再读
    dpi = int(os.environ.get("REOCR_DPI", "200"))
    jobs = {}
    if len(sys.argv) > 1:
        # explicit page list: {"TSA-2010": [9, 16], "TMUA-2016-P1": [5], ...}
        for label, pages in json.load(open(sys.argv[1])).items():
            exam, year = label.split("-", 1)
            q = {"exam": exam, "year": year}
            if exam == "TMUA":
                q["year"], paper = year.rsplit("-P", 1)
                q["paper"] = int(paper)
            pdf, out = pdf_for(q)
            jobs.setdefault((pdf, out), set()).update(pages)
    else:
        qs = json.load(open(os.path.join(paths.ADM, "questions_adm.json")))
        for q in qs:
            if not needs_fix(q):
                continue
            pdf, out = pdf_for(q)
            jobs.setdefault((pdf, out), set()).update(q["pages"])
    total = sum(len(v) for v in jobs.values())
    print(f"{len(jobs)} 份卷,共 {total} 页需要重读")

    # phase 1: build every mini-PDF and submit them all — the jobs then run
    # concurrently on the server instead of one at a time
    live = []
    for (pdf, out), pages in sorted(jobs.items()):
        pages = sorted(pages)
        name = os.path.basename(pdf)
        doc = fitz.open(pdf)
        tmp = fitz.open()
        for p in pages:
            pix = doc[p - 1].get_pixmap(dpi=dpi)
            # an uncompressed pixmap embeds as a ~9 MB image per page and the
            # upload stalls; JPEG at 85 is a hundredth of that
            jpg = pix.tobytes("jpeg", jpg_quality=85)
            page = tmp.new_page(width=pix.width, height=pix.height)
            page.insert_image(page.rect, stream=jpg)
        fd, path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        tmp.save(path)
        tmp.close(); doc.close()

        jid = ob.submit(path, name)
        os.unlink(path)
        if not jid:
            print(f"  ✗ {name} 提交失败"); continue
        live.append((jid, name, out, pages))
    print(f"已提交 {len(live)} 个任务,开始收取")

    # phase 2: collect in submission order
    import requests
    ok = 0
    for jid, name, out, pages in live:
        url = ob.wait_for(jid, name, quiet=True)
        if not url:
            print(f"  ✗ {name} 识别未完成"); continue
        raw = requests.get(url, timeout=300).text
        got = ob.parse_pages(raw, name)
        if len(got) != len(pages):
            print(f"  ✗ {name} 返回 {len(got)} 页,应为 {len(pages)},跳过")
            continue
        for pg, no in zip(got, pages):
            dst = os.path.join(out, f"page_{no:04d}.md")
            if os.path.exists(dst) and not os.path.exists(dst + ".bak"):
                os.rename(dst, dst + ".bak")
            open(dst, "w", encoding="utf-8").write(pg["text"] or "")
        ob.download_images(got, out, name)
        ok += 1
        print(f"  ✓ {name} p{pages} 已替换")
    print(f"完成 {ok}/{len(live)}")


if __name__ == "__main__":
    main()
