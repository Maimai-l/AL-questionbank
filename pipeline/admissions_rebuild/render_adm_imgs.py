#!/usr/bin/env python3
"""Render one image per admissions question — TMUA / TSA / BMAT.

    python3 render_adm_imgs.py            # 全部
    python3 render_adm_imgs.py TSA        # 只做一家

给人看的备份图,不是给模型看的:文件名就是题号 ID(`TSA-2019-S1-q20.png`),
放在同一个 img_adm/ 里,本地建索引时一一对应。

裁切怎么定:原卷的题号在 PDF 文本层里是左边距上的粗体数字(TSA/BMAT 是
Arial-Bold x≈51,TMUA 是 CM 粗体)。找到本题题号的 y 作上界、下一题题号的
y 作下界,就能把一页两题的卷面切成两张。找不到题号(OCR 字体损坏、
题目从上一页续下来)就退回整页 —— 宁可多给,不能切丢。

共享材料("Questions 8 - 11 refer to the following information")的题,
材料页整页拼在题目前面,否则单看题目没有上下文。
"""
import json, os, re, sys

import fitz

OUT = "img_adm"
DPI = 130
PAD = 6          # 裁切上下留白(pt)
MATCH_X = 0.15   # 题号必须落在左边距这个比例内

MATERIAL = re.compile(
    r"Questions?\s+(\d{1,2})\s*(?:-|–|—|to)\s*(\d{1,2})\s+refer", re.I)


def pdf_path(q):
    if q["exam"] == "TMUA":
        return f"bank/TMUA/papers/TMUA-{q['year']}-paper-{q['paper']}.pdf"
    sub = "TSA_section1" if q["exam"] == "TSA" else "BMAT_section1"
    return f"bank/TARA/{sub}/papers/{q['exam']}-{q['year']}-S1.pdf"


def qid(q):
    if q["exam"] == "TMUA":
        return f"TMUA-{q['year']}-P{q['paper']}-q{q['q']}"
    return f"{q['exam']}-{q['year']}-S1-q{q['q']}"


def unshift(t):
    """UCLES 老卷的嵌入字体把编码整体挪了 29 位(':KHQ' 其实是 'When')。

    人打开 PDF 看是正常的,机器读文本层才见乱码 —— TSA 2012/2013/2014
    的题号就藏在这里,不还原就一张都定位不到。
    """
    return "".join(chr(ord(c) + 29) if 0 < ord(c) < 0x7f else c for c in t)


_HCACHE = {}


def headers(page):
    """{题号: y} —— 左边距上的粗体数字,就是印刷体题号。逐页缓存。"""
    key = (page.parent.name, page.number)
    if key in _HCACHE:
        return _HCACHE[key]
    out = {}
    W = page.rect.width
    for b in page.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            for s in l["spans"]:
                t = s["text"].strip()
                if not re.fullmatch(r"\d{1,2}", t):
                    t = unshift(t).strip()
                    if not re.fullmatch(r"\d{1,2}", t):
                        continue
                if s["bbox"][0] > W * MATCH_X:
                    continue
                bold = "bold" in s["font"].lower() or re.search(r"BX|bd", s["font"])
                if not bold:
                    continue
                n = int(t)
                if n not in out or s["bbox"][1] < out[n]:
                    out[n] = s["bbox"][1]
    _HCACHE[key] = out
    return out


def material_pages(doc):
    """{题号: [材料页 0-based]} —— 共享材料块覆盖到的每一题。"""
    out = {}
    for i, page in enumerate(doc):
        raw = page.get_text()
        m = MATERIAL.search(raw) or MATERIAL.search(unshift(raw))
        if not m:
            continue
        a, b = int(m.group(1)), int(m.group(2))
        if not (0 < a <= b <= 60):
            continue
        for n in range(a, b + 1):
            out.setdefault(n, []).append(i)
    return out


def layout(doc, q):
    """[(页, 上界, 下界)] —— 本题在卷面上真正占的那一块。

    题号未必在 q["pages"][0]:切分时段落头部常带着上一题的残行,把上一页
    也算了进来。所以要在本题所有页里找题号,找到哪页就从哪页开始裁。
    """
    pages = [p - 1 for p in range(q["pages"][0], q["pages"][-1] + 1)]
    # 题号也可能落在更靠前的页:切分记录的是段落文字的来源页,
    # 题目本身可能从上一页就开始了。往前多看两页。
    search = list(range(max(0, pages[0] - 2), pages[-1] + 1))
    start, y0 = pages[0], None
    for i in search:                     # 找本题题号
        h = headers(doc[i])
        if q["q"] in h:
            start, y0 = i, max(0, h[q["q"]] - PAD)
            break
    y1, endp = None, pages[-1]
    for i in [p for p in range(start, pages[-1] + 1)]:   # 找下一题题号
        h = headers(doc[i])
        later = [y for n, y in h.items()
                 if n > q["q"] and (i != start or y0 is None or y > y0)]
        if later:
            y1, endp = min(later) - PAD, i
            break
    # 裁得只剩页眉,说明上界找错了 —— 宁可整页给出
    span = sum((y1 if i == endp and y1 is not None else doc[i].rect.y1)
               - (y0 if i == start and y0 is not None else doc[i].rect.y0)
               for i in range(start, endp + 1))
    if span < 120:
        start, y0, endp, y1 = pages[0], None, pages[-1], None

    out = []
    for i in range(start, endp + 1):
        out.append((i, y0 if i == start else None, y1 if i == endp else None))
    return out


def trim(pix):
    """切掉整片留白的尾巴 —— 一页只印了三行的题不该配一张整页白纸。"""
    w, h, n = pix.width, pix.height, pix.n
    buf = pix.samples
    row = w * n
    last = 0
    for y in range(h - 1, -1, -1):
        s = buf[y * row:(y + 1) * row]
        if min(s) < 245:                  # 该行有墨
            last = y
            break
    keep = min(h, last + 24)
    if keep >= h - 4:
        return pix
    out = fitz.Pixmap(pix.colorspace, fitz.IRect(0, 0, w, keep), pix.alpha)
    out.clear_with(255)
    out.copy(pix, fitz.IRect(0, 0, w, keep))
    return out


def render(q, doc, mat, own=None):
    own = own if own is not None else layout(doc, q)
    mine = {i for i, _t, _b in own}
    parts = [(i, None, None) for i in mat.get(q["q"], []) if i not in mine]
    parts += own

    pix = []
    for i, top, bot in parts:
        page = doc[i]
        r = page.rect
        clip = fitz.Rect(r.x0, top if top is not None else r.y0,
                         r.x1, bot if bot is not None else r.y1)
        if clip.height < 40:               # 裁过头了,退回整页
            clip = r
        p = page.get_pixmap(dpi=DPI, colorspace=fitz.csGRAY, clip=clip)
        p.set_origin(0, 0)   # 带页面坐标的 pixmap 拼起来会错位
        pix.append(p)

    pix = [trim(p) for p in pix]
    if len(pix) == 1:
        return pix[0]
    W = max(p.width for p in pix)
    H = sum(p.height for p in pix)
    out = fitz.Pixmap(fitz.csGRAY, fitz.IRect(0, 0, W, H), False)
    out.clear_with(255)
    y = 0
    for p in pix:
        p.set_origin(0, y)          # copy 的矩形按源坐标算,先把落点定好
        out.copy(p, p.irect)
        y += p.height
    return out


def main(only=None):
    os.makedirs(OUT, exist_ok=True)
    qs = json.load(open("questions_adm.json"))
    if only:
        qs = [q for q in qs if q["exam"] == only]
    docs, mats, n, whole = {}, {}, 0, 0
    for q in qs:
        p = pdf_path(q)
        if p not in docs:
            docs[p] = fitz.open(p)
            mats[p] = material_pages(docs[p])
        doc = docs[p]
        lay = layout(doc, q)
        if all(t is None and b is None for _i, t, b in lay):
            whole += 1
        render(q, doc, mats[p], lay).save(os.path.join(OUT, qid(q) + ".png"))
        n += 1
    print(f"{n} 张 -> {OUT}/   其中 {whole} 张未能定位题号、按整页给出")
    sizes = sorted(os.path.getsize(os.path.join(OUT, f))
                   for f in os.listdir(OUT) if f.endswith(".png"))
    print(f"目录共 {len(sizes)} 张,最小 {sizes[0]//1024}KB 中位 "
          f"{sizes[len(sizes)//2]//1024}KB 最大 {sizes[-1]//1024}KB 合计 "
          f"{sum(sizes)//2**20}MB")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
