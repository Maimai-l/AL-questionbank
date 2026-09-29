#!/usr/bin/env python3
"""Recover crops whose OCR degenerated into a repetition loop.

A vision model sometimes falls into emitting one token forever (here: Chinese
financial numerals such as 貳柒). Simply asking again does *not* help — the
failure is deterministic for a given image. Failing crops are markedly taller
than average, so the fix is to slice the crop into overlapping horizontal
bands, read each separately, and stitch the results: a shorter input never
enters the loop.
"""
import json, os, re, sys, threading, time
from concurrent.futures import ThreadPoolExecutor

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))          # 项目根目录
from pipeline.ocr import ocr as ocr_mod
from lib import paths

CJK = re.compile(r"[㐀-鿿豈-﫿]")
BAND = 900          # px; comfortably below where degeneration starts
OVERLAP = 90        # px of shared context so a split line is not lost
lock = threading.Lock()


def degenerate(text):
    if not text or len(text.strip()) < 30:
        return True
    if CJK.search(text):
        return True
    if re.search(r"(.{6,40}?)\1{7,}", text):
        return True
    return False


def bands(path, workdir):
    from PIL import Image
    im = Image.open(path)
    w, h = im.size
    if h <= BAND:
        return [path]
    out, y, i = [], 0, 0
    while y < h:
        y1 = min(y + BAND, h)
        p = os.path.join(workdir, f"{os.path.basename(path)[:-4]}__b{i}.png")
        im.crop((0, y, w, y1)).save(p)
        out.append(p)
        if y1 >= h:
            break
        y, i = y1 - OVERLAP, i + 1
    return out


def main(dbpath, cache, workers=6):
    import sqlite3
    workdir = "/tmp/bands"
    os.makedirs(workdir, exist_ok=True)
    con = sqlite3.connect(dbpath)
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute(
        "SELECT id, image, question_latex FROM questions WHERE image IS NOT NULL")]
    bad = [r for r in rows if degenerate(r["question_latex"])]
    print(f"{len(bad)} crops to re-read in bands", flush=True)

    fh = open(cache, "a")
    ok, stuck = [0], []

    def work(r):
        path = paths.resolve(r["image"])
        if not path:
            return
        try:
            parts = bands(path, workdir)
        except Exception:
            return
        chunks = []
        for p in parts:
            res = ocr_mod.ocr_one(p, tries=2)
            t = res.get("latex", "")
            if t and not degenerate(t):
                chunks.append(t)
        text = "\n".join(chunks).strip()
        with lock:
            if text and not degenerate(text) and len(text) > 40:
                fh.write(json.dumps({"id": os.path.basename(path)[:-4],
                                     "latex": text,
                                     "has_diagram": "[DIAGRAM]" in text},
                                    ensure_ascii=False) + "\n")
                fh.flush()
                ok[0] += 1
            else:
                stuck.append(r["id"])
            done = ok[0] + len(stuck)
            if done % 20 == 0:
                print(f"  {done}/{len(bad)}  recovered {ok[0]}", flush=True)

    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(work, bad))
    fh.close()
    print(f"recovered {ok[0]}/{len(bad)}; still degenerate {len(stuck)}")
    if stuck:
        print("  " + ", ".join(stuck[:12]))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2],
         int(sys.argv[3]) if len(sys.argv) > 3 else 6)
