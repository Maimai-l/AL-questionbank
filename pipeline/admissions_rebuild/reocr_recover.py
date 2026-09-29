#!/usr/bin/env python3
"""Finish the crashed re-OCR run: reuse already-submitted jobs, submit the
rest, collect everything.

    python3 reocr_recover.py /tmp/problem_pages.json /tmp/reocr3.log [more logs]

The crash was an empty page set (a paper flagged with no pages) — skipped
here. Submitted jobs are recovered from the log's `已提交 job <id>` lines.
"""
import json, os, re, sys, tempfile

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))          # qb/ —— 直接跑脚本时也 import 得到包
from pipeline.ocr import ocr_books as ob
import fitz
import requests

from reocr_pages import pdf_for


def main(pagespath, *logpaths):
    submitted = {}
    for logpath in logpaths:
        for line in open(logpath, encoding="utf-8"):
            m = re.search(r"\]\s+(\S+\.pdf)\s+已提交\s+job\s+(\d+)", line)
            if m:
                submitted[m.group(1)] = m.group(2)  # last job per file wins
    print(f"日志里找到 {len(submitted)} 个已提交任务")

    live = []
    for label, pages in json.load(open(pagespath)).items():
        pages = sorted(set(pages))
        if not pages:
            print(f"  - {label} 无页码,跳过")
            continue
        exam, year = label.split("-", 1)
        pdf, out = pdf_for({"exam": exam, "year": year})
        name = os.path.basename(pdf)
        jid = submitted.get(name)
        if not jid:
            doc = fitz.open(pdf)
            tmp = fitz.open()
            for p in pages:
                pix = doc[p - 1].get_pixmap(dpi=200)
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

    print(f"待收取 {len(live)} 个任务")
    ok = 0
    for jid, name, out, pages in live:
        url = ob.wait_for(jid, name, quiet=True)
        if not url:
            print(f"  ✗ {name} 识别未完成"); continue
        raw = None
        for attempt in range(4):
            try:
                raw = requests.get(url, timeout=300).text
                break
            except requests.exceptions.RequestException as e:
                print(f"  … {name} 结果下载失败({type(e).__name__}),重试")
                import time
                time.sleep(10 * (attempt + 1))
        if raw is None:
            print(f"  ✗ {name} 结果下载放弃"); continue
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
        print(f"  ✓ {name} p{pages} 已替换", flush=True)
    print(f"完成 {ok}/{len(live)}")


if __name__ == "__main__":
    main(sys.argv[1], *sys.argv[2:])
