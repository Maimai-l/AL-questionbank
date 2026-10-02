#!/usr/bin/env python3
"""Render each TMUA question's page(s) to one PNG — the loss-free 原题图.

    python3 render_tmua_imgs.py

TMUA layouts vary (mostly one question per page; 2016 and the specimen pack
two), so the page render is the honest presentation: exactly what the
candidate saw. Every TMUA question sits on exactly one page (asserted).

Output: img_adm/TMUA-<year>-P<paper>-q<n>.png at 150 dpi.
"""
import json, os

import fitz

OUT = "img_adm"
DPI = 150


def main():
    os.makedirs(OUT, exist_ok=True)
    qs = [q for q in json.load(open("questions_adm.json")) if q["exam"] == "TMUA"]
    docs = {}
    n = 0
    for q in qs:
        key = (q["year"], q["paper"])
        if key not in docs:
            docs[key] = fitz.open(
                f"bank/TMUA/papers/TMUA-{q['year']}-paper-{q['paper']}.pdf")
        doc = docs[key]
        assert len(q["pages"]) == 1, (q["year"], q["paper"], q["q"])
        pix = doc[q["pages"][0] - 1].get_pixmap(dpi=DPI)
        name = f"TMUA-{q['year']}-P{q['paper']}-q{q['q']}.png"
        pix.save(os.path.join(OUT, name))
        n += 1
    print(f"{n} 张 -> {OUT}/")
    # sizes sanity
    sizes = sorted(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT))
    print(f"最小 {sizes[0]//1024}KB 最大 {sizes[-1]//1024}KB 共 "
          f"{sum(sizes)//2**20}MB")


if __name__ == "__main__":
    main()
