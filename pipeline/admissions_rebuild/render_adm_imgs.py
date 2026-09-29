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

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
import pymupdf as fitz  # noqa: E402

from lib import paths  # noqa: E402
from pipeline.split import furniture  # noqa: E402

OUT = paths.IMG_ADM
BANK = paths.BANK                                # manifest.py 的下载目录
QUESTIONS = os.path.join(paths.ADM, "questions_adm.json")
DPI = 130
PAD = 6          # 裁切下沿留白(pt)
PAD_TOP = 12     # 题号之上留白:同一行的上标、根号会比题号高出几 pt
MATCH_X = 0.15   # 题号必须落在左边距这个比例内
ZOOM = DPI / 72.0

# 页面固定元素。UCLES、UAT-UK 三十年的卷子页脚写法有十几种,老卷还要先 unshift
FOOTER = re.compile(r"UCLES|Turn\s*over|^TSA(Oxford.*)?$|^BMAT\b.*Section|^Page\s*\d+\s*/\s*\d+$"
                    r"|^\s*(BLANK PAGE|This page is intentionally left blank)", re.I)

MATERIAL = re.compile(
    r"Questions?\s+(\d{1,2})\s*(?:-|–|—|to)\s*(\d{1,2})\s+refer", re.I)


def pdf_path(q):
    if q["exam"] == "TMUA":
        return os.path.join(BANK, f"TMUA/papers/TMUA-{q['year']}-paper-{q['paper']}.pdf")
    sub = "TSA_section1" if q["exam"] == "TSA" else "BMAT_section1"
    return os.path.join(BANK, f"TARA/{sub}/papers/{q['exam']}-{q['year']}-S1.pdf")


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


def cambria(t):
    """TMUA 2016、2017 用 CambriaMath 排版,数字 0–9 落在 U+0372–U+037B("ͳ" 是 1)。"""
    t = "".join(chr(ord(c) - 0x342) if 0x372 <= ord(c) <= 0x37B else c for c in t)
    return "".join(c if ord(c) >= 0x20 else " " for c in t).strip()   # "\x03" 是这套编码的空格


def readable(t):
    """文本层原样可读就原样返回,否则按 29 位偏移还原。"""
    if any(0 < ord(c) < 0x20 for c in t):
        return unshift(t)
    return t


_FCACHE = {}


def page_furniture(page):
    """[(kind, rect)] —— 页码、页脚、页眉横线、页顶标志,逐页缓存。"""
    key = (page.parent.name, page.number)
    if key in _FCACHE:
        return _FCACHE[key]
    W, H = page.rect.width, page.rect.height
    items = []
    for txt, r, _h in furniture.lines(page):
        t = readable(txt).strip()
        edge = r.y1 < 70 or r.y0 > H - 70
        # 偏移常常只落在一行的一部分("©" 偏移、"UCLES 2012" 正常),原文和还原后各比一次
        if edge and (FOOTER.search(t) or FOOTER.search(txt)):
            items.append(("footer", r))
        elif edge and re.fullmatch(r"\d{1,2}", t) and abs((r.x0 + r.x1) / 2 - W / 2) < 40:
            items.append(("pageno", r))
        elif re.fullmatch(r"\s*BLANK PAGE\s*", t):
            items.append(("blank", r))
    for d in page.get_drawings():
        r = furniture.fat(d["rect"])
        if r.y1 < 45 and r.width > 300:
            items.append(("rule", r))          # 页眉横线
    for img in page.get_image_info():
        r = fitz.Rect(img["bbox"])
        if r.y1 < 62:
            items.append(("logo", r))
    _FCACHE[key] = items
    return items


def band(page, items=None):
    """(上界, 下界):页眉元素之下、页脚元素之上。"""
    items = page_furniture(page) if items is None else items
    H = page.rect.height
    # 留 2pt:字形紧框之外还有抗锯齿的浅灰边,贴着切会在图边留一道灰痕
    top = max([r.y1 for _k, r in items if r.y1 < 75] + [0.0]) + 2
    bottom = min([r.y0 for _k, r in items if r.y0 > H - 75] + [H]) - 2
    return top, bottom


def whiteout(pix, clip, items):
    """裁切范围内残留的固定元素涂白。pixmap 的原点是裁切区在整页上的像素位置。"""
    for _k, r in items:
        r = fitz.Rect(r) & clip
        if r.is_empty:
            continue
        box = fitz.IRect(pix.x + int((r.x0 - clip.x0) * ZOOM) - 3, pix.y + int((r.y0 - clip.y0) * ZOOM) - 3,
                         pix.x + int((r.x1 - clip.x0) * ZOOM) + 4, pix.y + int((r.y1 - clip.y0) * ZOOM) + 4)
        box &= pix.irect
        if not box.is_empty:
            pix.set_rect(box, (255,) * pix.n)
    return pix


_DCACHE = {}


def _candidates(doc):
    """左边距上所有可能是题号的文字,按阅读顺序:(页, y, x, 数字或 None, 粗体)。

    数字取原文或 unshift 后的形式。None 表示一个位于左边距、字形不在文本层
    里的粗体空白(TSA 2013 Q9 的 "9" 就是这样),只在题号序列恰好缺它时启用。
    """
    out = []
    for page in doc:
        if page.number == 0:
            continue            # 封面:考生须知的 "1." "2." 不是题号
        W = page.rect.width
        furn = [r for _k, r in page_furniture(page)]
        for b in page.get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                for sp in l["spans"]:
                    x0, y0 = sp["bbox"][0], sp["bbox"][1]
                    if x0 > W * MATCH_X or any(fitz.Rect(sp["bbox"]) in f for f in furn):
                        continue
                    bold = bool("bold" in sp["font"].lower() or re.search(r"BX|bd", sp["font"]))
                    raw = sp["text"].strip().rstrip(".")
                    n = None
                    for t in (raw, unshift(sp["text"]).strip().rstrip(".")):
                        if re.fullmatch(r"\d{1,2}", t):
                            n = int(t)
                            break
                    # "7.   Find the…":编号与题干同在一个片段,带句点和空格
                    m = re.match(r"(\d{1,2})\.\s", sp["text"].lstrip()) if n is None else None
                    if m:
                        n = int(m.group(1))
                    # CambriaMath 的题号常和题干第一个符号挤在同一片段里:"2 f(x)…"
                    m = re.match(r"(\d{1,2})(?:\s|$)", cambria(sp["text"])) if n is None else None
                    if m and any(0x372 <= ord(c) <= 0x37B for c in sp["text"][:3]):
                        n = int(m.group(1))
                    if n is None and not (bold and not unshift(sp["text"]).strip()):
                        continue
                    out.append((page.number, y0, x0, n, bold))
    return sorted(out)


def doc_headers(doc):
    """{题号: (页, y)} —— 按 1, 2, 3… 在全卷左边距上依次认领。

    选项旁的数值、表格里的数字不会按顺序出现,自然被跳过;逐页找则会把它们
    当成题号。粗体优先:同一个编号先认粗体。"""
    key = doc.name
    if key in _DCACHE:
        return _DCACHE[key]
    cands = _candidates(doc)
    known = [c for c in cands if c[3] is not None]
    xs = sorted(c[2] for c in known if c[4])
    col = xs[len(xs) // 2] if xs else None        # 题号所在的那一列
    out, expect = {}, 1
    for k, (pg, y, x, n, bold) in enumerate(cands):
        if n is None and (col is None or abs(x - col) > 6):
            continue            # 空白只在题号列上才算;真数字靠顺序约束,不看列
        if n == expect:
            out[n] = (pg, y)
            expect += 1
        elif n is None:
            # 空白粗体只填序列里恰好缺的那一个:后面紧接着出现的是 expect+1
            nxt = next((c for c in cands[k + 1:] if c[3] is not None and abs(c[2] - col) <= 6), None)
            if nxt and nxt[3] == expect + 1:
                out[expect] = (pg, y)
                expect += 1
        elif n == expect + 1:
            out[n] = (pg, y)
            expect = n + 1
    _DCACHE[key] = out
    return out


def headers(page):
    """{题号: y} —— 本页上的题号,取自全卷序列。"""
    return {n: y for n, (pg, y) in doc_headers(page.parent).items() if pg == page.number}


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
    H = doc_headers(doc)
    start, y0 = pages[0], None
    if q["q"] in H:
        start, y = H[q["q"]]
        y0 = max(0, y - PAD_TOP)
    last = max(pages[-1], start)           # 题号可能落在记录页之后
    y1, endp = None, last
    # 下一题题号:只在本题范围内找。更远处的题号之前可能隔着别组的共享材料页
    later = sorted(v for n, v in H.items() if n > q["q"] and start <= v[0] <= last
                   and (v[0] != start or y0 is None or v[1] > y0))
    if later:
        endp, y1 = later[0][0], later[0][1] - PAD
    if y0 is None:
        # 题号定位不到:只好给出整页,审计会把它列在 whole-page 里
        start, endp, y1 = pages[0], pages[-1], None

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


def clips(doc, parts):
    """[(页, 裁切矩形)]:题目范围限制在页眉页脚之间;空白页不出图。"""
    out = []
    for i, top, bot in parts:
        page = doc[i]
        items = page_furniture(page)
        if any(k == "blank" for k, _r in items):
            continue
        r = page.rect
        b0, b1 = band(page, items)
        clip = fitz.Rect(r.x0, max(top if top is not None else b0, b0),
                         r.x1, min(bot if bot is not None else b1, b1))
        if clip.height < 8:
            continue        # 下一题题号就在这页顶端:这页不属于本题。退回整页会把下一题整个带进来
        out.append((i, clip))
    return out


def parts_of(q, doc, mat, own=None):
    """材料页 + 材料续页 + 本题自己的范围。

    共享材料常常跨页:末页只标出了 "Questions 24 to 27 refer to…" 所在的那页,
    续到下一页顶部、排在第一个题号之上的那段同样是材料,四道题都要带上。"""
    own = own if own is not None else layout(doc, q)
    mine = {i for i, _t, _b in own}
    mpages = mat.get(q["q"], [])
    parts = [(i, None, None) for i in mpages if i not in mine]
    if mpages:
        nxt = max(mpages) + 1
        if nxt < doc.page_count and nxt not in mpages:
            h = headers(doc[nxt])
            if h:
                cut = min(h.values()) - PAD
                own_top = next((t for i, t, _b in own if i == nxt), "absent")
                # 本题从续页顶部起就整页在裁,续段已经包含在内
                if own_top is not None and cut - band(doc[nxt])[0] > 20:
                    parts.append((nxt, None, cut))
    return parts + own


def render(q, doc, mat, own=None):
    parts = parts_of(q, doc, mat, own)

    pix = []
    for i, clip in clips(doc, parts):
        page = doc[i]
        p = page.get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), colorspace=fitz.csGRAY, clip=clip)
        whiteout(p, clip, page_furniture(page))
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
    qs = json.load(open(QUESTIONS))
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
