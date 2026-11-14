#!/usr/bin/env python3
"""Page Markdown from a textbook's own text layer — the no-OCR route.

The maths books were scans and went through PaddleOCR (pipeline/ocr/). A
publisher's PDF (Physics 9702, Hodder) has a real text layer instead, and
reading it directly is both free and more faithful than OCR: every glyph is
there, with its font, size and baseline. This turns that into the same
page_NNNN.md files ocr_books.py produces, so split_chapters.py and
chapters.py run unchanged afterwards.

    python3 -m pipeline.books.text_layer pages   <book.pdf> <page_md_dir> [--from N] [--to M]
    python3 -m pipeline.books.text_layer chapters <book.pdf> <chapters.json> [--level 2]

then

    python3 -m pipeline.books.split_chapters <book.pdf> <page_md_dir> data/books/9702 \
            --prefix 9702 --table <chapters.json>

What the text layer gives and what it does not:

* Superscripts and subscripts are recovered from size and baseline and written
  as LaTeX: "m s−2" -> "m $\\mathrm{s}^{-2}$", "10" + raised "15" -> "$10^{15}$".
* Headings are recognised by font (DIN 16/14/12 pt in this series) and become
  ##/###/####; bold body text becomes **bold**.
* Figure artwork is dropped: labels set in the figure fonts (Frutiger,
  ITC Garamond, Tekton) or in small type, and anything over a raster image.
  Captions ("Figure 1.6 ...") are kept, so the reader knows a figure stood
  there. The page viewer does not show textbook images anyway.
* Display equations built from stacked lines (fractions, roots) cannot be
  rebuilt into LaTeX reliably from positions alone; their parts are written
  in reading order on one line, never invented.

Running furniture — page numbers, the vertical running title in the outer
margin, the topic tab number, the running header — is removed by position
and font.
"""
import json, os, re, sys, unicodedata

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))          # 项目根目录
from lib import paths  # noqa: F401,E402  (kept for the project's path rule)
from pipeline.text.clean_encoding import fix_pua  # noqa: E402

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        sys.exit("需要 PyMuPDF:  pip install pymupdf")

# artwork labels in this series are set in these families, never body text
FIG_FONTS = re.compile(r"^(Frutiger|ITCGaramond|Garamond|TektonPro)", re.I)
BOLD = 16
SUPER = 1

# (font prefix, size) -> markdown heading level; None drops the line (it
# repeats the chapter title, which split_chapters writes at the top)
HEADINGS = [
    (re.compile(r"^DIN-(Light|Bold)$"), 26, 70, None),     # chapter opener
    (re.compile(r"^DIN-Regular$"), 15.5, 17, 2),           # 1.1 Physical quantities
    (re.compile(r"^DIN-(Medium|Bold)$"), 13.5, 14.5, 3),   # Significant figures / WORKED EXAMPLE 1A
    (re.compile(r"^DIN-(Medium|Bold|MediumItalic)$"), 11.5, 12.5, 4),  # Answer / Learning outcomes
]

CHNUM = re.compile(r"^\s*(?:chapter|topic|unit)\s+(\d{1,2})\b\s*(.*)$", re.I)


# ---------------------------------------------------------------- chapters

def chapter_table(pdf, level=None):
    """Numbered chapters from the bookmarks, each ending where the next entry
    at the same *or a shallower* level begins.

    The shallower bound matters at the back of the book: the last topic
    (Practical work, p430) is followed at level 2 only by the glossary's
    letter "A" at p466, but at level 1 by "List of formulae" at p452. Ending
    at the next same-level entry would fold the formula sheet and the answers
    into the last chapter.
    """
    d = fitz.open(pdf)
    toc = [(lv, t.strip(), p) for lv, t, p in d.get_toc() if p > 0]
    n = d.page_count
    d.close()
    levels = sorted({lv for lv, _t, _p in toc})
    if level is None:
        level = max(levels, key=lambda lv: sum(1 for l, t, _p in toc
                                               if l == lv and CHNUM.match(t)))
    out = []
    for i, (lv, title, page) in enumerate(toc):
        if lv != level:
            continue
        m = CHNUM.match(title)
        if not m:
            continue
        end = next((p - 1 for l, _t, p in toc[i + 1:] if l <= level and p > page), n)
        out.append({"chapter": int(m.group(1)), "title": m.group(2).strip() or title,
                    "page_from": page, "page_to": end})
    return out


# ---------------------------------------------------------------- page text

CTRL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


def clean(t):
    t = CTRL.sub("", t.replace("\t", " "))
    t = re.sub("[\u2002\u2003\u202f\xa0]", " ", t)
    t = re.sub("[\u2009\u200a]+", "\u2009", t)    # thin space: kept until render
    t = t.replace("\u00ad", "")                      # soft hyphen
    t = fix_pua(t).replace("\u2206", "\u0394")       # Symbol-font slots; increment sign -> Delta
    # zero-width and private-use leftovers: invisible here, fatal inside $...$
    return "".join(ch for ch in t if ch == "\u2009"
                   or unicodedata.category(ch) not in ("Cf", "Co", "Cn"))


def math_escape(s):
    s = s.replace("\u2212", "-").replace("\u2013", "-").replace("\u2009", " ").strip()
    s = re.sub(r"([%#&{}])", r"\\\1", s)
    return s


def is_script(span, line_size):
    return (span["size"] < 0.86 * line_size and span["text"].strip()
            and span["text"].strip() not in "»★•▲–-")


def line_size(spans):
    """The size of the line's ordinary text: the largest size that carries a
    fair share of the characters, so one big symbol does not count."""
    w = {}
    for s in spans:
        if s["text"].strip():
            w[round(s["size"], 1)] = w.get(round(s["size"], 1), 0) + len(s["text"].strip())
    if not w:
        return 0
    tot = sum(w.values())
    big = [sz for sz, c in w.items() if c >= 0.2 * tot]
    return max(big) if big else max(w)


BASE_TAIL = re.compile(r"([A-Za-z0-9.,\u0391-\u03c9]*[A-Za-z0-9\u0391-\u03c9])$")


def render_spans(spans):
    """One line of spans -> text, with scripts as $base^{...}$ / $base_{...}$
    and a small numeral set over another ("1" raised, "2" lowered, same x)
    as $\\frac{1}{2}$."""
    size = line_size(spans)
    base_y = None
    for s in spans:
        if round(s["size"], 1) == size and s["text"].strip():
            base_y = s["origin"][1]
            break
    out = []        # [kind, text, italic, bold, x0, x1]
    for s in spans:
        t = clean(s["text"])
        if not t:
            continue
        x0, x1 = s["bbox"][0], s["bbox"][2]
        if s.get("latex"):
            out.append(["m", s["latex"], False, False, x0, x1])
            continue
        if "overbar" in s and not is_script(s, size):
            k = s["overbar"]
            if t[:k]:
                out.append(["t", t[:k], bool(s["flags"] & 2), bool(s["flags"] & BOLD), x0, x0])
            out.append(["m", r"\bar{" + t[k] + "}", False, False, x0, x1])
            if t[k + 1:]:
                out.append(["t", t[k + 1:], bool(s["flags"] & 2), bool(s["flags"] & BOLD), x1, x1])
            continue
        if size and is_script(s, size):
            up = bool(s["flags"] & SUPER) or (base_y is not None and s["origin"][1] < base_y - 0.8)
            kind = "^" if up else "_"
            if out and out[-1][0] == kind and x0 - out[-1][5] < 2:
                out[-1][1] += t
                out[-1][5] = x1
            else:
                out.append([kind, t, False, False, x0, x1])
        else:
            # words set apart by position rather than by a space character
            # (table cells do this) still need the space
            if (out and out[-1][0] == "t" and x0 - out[-1][5] > 0.2 * (size or 10)
                    and not out[-1][1][-1:].isspace() and not t[:1].isspace()):
                t = " " + t
            out.append(["t", t, bool(s["flags"] & 2), bool(s["flags"] & BOLD), x0, x1])

    # whitespace between two bold runs is bold too, so "1.1" + " " + "Physical"
    # becomes one **1.1 Physical** and not **1.1****Physical**
    for i, tok in enumerate(out):
        if tok[0] == "t" and not tok[1].strip() and i and out[i - 1][0] == "t":
            tok[3] = out[i - 1][3]
    toks = []
    for tok in out:
        if toks and tok[0] == "t" and toks[-1][0] == "t" and toks[-1][3] == tok[3]:
            toks[-1][1] += tok[1]
            toks[-1][2] = tok[2]
            toks[-1][5] = tok[5]
        else:
            toks.append(list(tok))
    out = toks

    text = ""
    i = 0
    while i < len(out):
        kind, t, ital, bold, x0, x1 = out[i]
        i += 1
        if kind == "m":
            if text and not text[-1].isspace() and text[-1] not in "($":
                text += " "
            text += f"${t}$ "
            continue
        if kind == "t":
            if bold and t.strip() and not re.fullmatch(r"[\s\W]*", t):
                lead = t[:len(t) - len(t.lstrip())]
                trail = t[len(t.rstrip()):]
                t = f"{lead}**{t.strip()}**{trail}"
            text += t.replace("$", r"\$")
            continue
        script = math_escape(t)
        if not script:
            continue
        nxt = out[i] if i < len(out) else None
        no_base = not text or text[-1].isspace() or text[-1] in "=(×/"
        if (no_base and nxt and nxt[0] in "^_" and nxt[0] != kind
                and nxt[4] < x1 and x0 < nxt[5]):
            other = math_escape(nxt[1])
            num, den = (script, other) if kind == "^" else (other, script)
            text += f"$\\frac{{{num}}}{{{den}}}$" + (" " if nxt[1][-1:].isspace() else "")
            i += 1
            continue
        prev_ital = i > 1 and out[i - 2][0] == "t" and out[i - 2][2]
        # a thin space between a symbol and its exponent is typesetting,
        # not a word break
        if text.endswith("\u2009") and not text[:-1].endswith((" ", "\u2009")):
            text = text.rstrip("\u2009")
        mb = re.search(r"\*\*([^*]*?)([A-Za-z0-9.]{1,6})\*\*$", text)
        m = BASE_TAIL.search(text) if text and not text[-1].isspace() else None
        if mb:
            # base inside a bold run: "**kg m**" + "2" -> "**kg** $\mathbf{m}^{2}$"
            pre, b = mb.group(1), mb.group(2)
            text = text[:mb.start()]
            if pre.strip():
                text += f"**{pre.strip()}**" + (" " if pre != pre.rstrip() else "")
            else:
                text += pre
            base = b if re.fullmatch(r"[0-9.,]+", b) else r"\mathbf{" + b + "}"
        elif m and len(m.group(1)) <= 12:
            b = m.group(1)
            text = text[:m.start()]
            if re.fullmatch(r"[0-9.,]+", b) or re.fullmatch(r"[\u0391-\u03c9]", b):
                base = b
            elif prev_ital and len(b) <= 3:
                base = b
            else:
                base = r"\mathrm{" + b + "}"
        elif text.endswith("$") and not text.endswith(r"\$"):
            # a second script on the same base: $x^{2}$ then a subscript
            text = text[:-1] + f"{kind}{{{script}}}$" + (" " if t[-1:].isspace() else "")
            continue
        else:
            base = "{}"
        text += f"${base}{kind}{{{script}}}$" + (" " if t[-1:].isspace() else "")
    text = re.sub(r"(?<!\\)\$\$", "", text)     # two inline maths side by side are one
    return re.sub(r"[ ]{2,}", " ", text.replace("\u2009", " "))


def family(spans):
    """Typeface family carrying most of a line: a caption (DIN) followed by
    body text (Berkeley) in the same block is two paragraphs."""
    w = {}
    for sp in spans:
        if sp.get("latex"):
            continue
        f = sp["font"].split("-")[0]
        w[f] = w.get(f, 0) + len(sp["text"].strip())
    return max(w, key=w.get) if w and max(w.values()) > 3 else None


def heading_level(spans):
    sig = [s for s in spans if s["text"].strip() and s["text"].strip() not in "▲★»"]
    if not sig:
        return 0
    for rx, lo, hi, lvl in HEADINGS:
        if all(rx.match(s["font"]) and lo <= s["size"] <= hi for s in sig):
            return lvl if lvl is not None else -1
    return 0


def furniture(line, spans, page_rect):
    x0, y0, x1, y1 = line["bbox"]
    if abs(line["dir"][0]) < 0.9:                         # vertical running title
        return True
    if x0 > page_rect.width - 50 or x1 < 42:              # outer margins
        return True
    if y0 > page_rect.height - 35:                        # page number
        return True
    sig = [s for s in spans if s["text"].strip()]
    if not sig:
        return True
    if all(s["font"].startswith("DIN-Black") and s["size"] < 10.5 for s in sig) and y0 < 50:
        return True                                       # running header
    if all(s["font"] == "DIN-Bold" and s["size"] >= 19 and s["size"] < 21 for s in sig) and y0 < 60:
        return True                                       # "AS LEVEL" banner
    return False


def figure_text(spans, size, bbox, images):
    sig = [s for s in spans if s["text"].strip()]
    if all(FIG_FONTS.match(s["font"]) for s in sig):
        return True
    if size and size < 8.3 and not any(s["flags"] & SUPER for s in sig):
        return True
    cx, cy = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
    for r in images:
        if r[0] <= cx <= r[2] and r[1] <= cy <= r[3]:
            return True
    return False


LABEL = re.compile(r"^\(?(?:\d{1,2}(?:\s*\(?[a-h]\)?)?(?:\s*\(?(?:i{1,3}|iv|vi{0,3})\)?)?|[a-h]|i{1,3}|iv|vi{0,3}|[A-D])\)?\.?$")


def starts_item(spans):
    """A question number, part letter, option letter or bullet opens a new
    paragraph. The book sets these bold, or follows them with a tab — plain
    "6 × 10" at the start of a wrapped line is neither."""
    sig = [s for s in spans if s["text"].strip()]
    if not sig:
        return False
    first = sig[0]["text"]
    if first.strip()[:1] in "★•»▲":
        return True
    if re.match(r"^\s*\S{1,5}\t", first):
        return True
    return bool(sig[0]["flags"] & BOLD and LABEL.match(first.strip()))


FUNC = {"sin", "cos", "tan", "log", "ln", "exp", "lg"}


def spans_latex(spans):
    """The spans of a numerator or denominator as LaTeX (no $ delimiters)."""
    spans = sorted(spans, key=lambda s: s["bbox"][0])
    big = line_size(spans) or max(s["size"] for s in spans)
    base_y = next((s["origin"][1] for s in spans if s["size"] >= 0.86 * big
                   and s["text"].strip()), None)
    out = ""
    for s in spans:
        t = clean(s["text"]).strip()
        if not t:
            continue
        if s.get("latex"):
            out += s["latex"]
            continue
        if s["size"] < 0.86 * big:
            up = bool(s["flags"] & SUPER) or (base_y is not None and s["origin"][1] < base_y - 0.8)
            out += ("^" if up else "_") + "{" + math_escape(t) + "}"
            continue
        words = re.findall(r"[A-Za-z]{3,}", t)
        italic_symbols = bool(s["flags"] & 2) and len(t) <= 4 and " " not in t
        if any(w.lower() not in FUNC for w in words) and not italic_symbols:
            # keep the spaces round a phrase: "speed in" + X, not "speed inX"
            tt = clean(s["text"]).replace("\u2009", " ")
            tt = (" " if tt[:1].isspace() and out else "") + t + (" " if tt[-1:].isspace() else "")
            out += r"\text{" + re.sub(r"([%#&{}])", r"\\\1", tt) + "}"
            continue
        t = math_escape(t).replace("×", r"\times ").replace("·", r"\cdot ")
        out += " " + t if out and out[-1].isalnum() and t[:1].isalnum() else t
    # two exponents in a row are one exponent; KaTeX rejects x^{a}^{b}
    out = re.sub(r"(\^\{[^{}]*)\}\^\{", r"\1", out)
    out = re.sub(r"(_\{[^{}]*)\}_\{", r"\1", out)
    return re.sub(r"[\^_]\{\s*\}", "", out)


def rebuild_fractions(data):
    """Stacked fractions and overbars, from the rules drawn between the glyphs.

    A displayed fraction in this book is three things in the PDF: numerator
    glyphs above a thin horizontal rule, denominator glyphs below it, and the
    rule itself as a vector stroke. Read as text it comes out as
    "v = u + v 2". Here each short rule with text directly above *and* below
    becomes one \\frac{..}{..} span, placed where the rule sits so it lands in
    its own line ("v = \\frac{u + v}{2}"). A very short rule over a single
    letter is an average-value bar: \\bar{v}. Rules that match neither
    (graph axes, table borders, underlines) are left alone.
    """
    bars = []
    for dr in data.get("_drawings", []):
        r = dr["rect"]
        if (r.height < 1.6 and 2.5 < r.width < 230
                and all(it[0] in ("l", "re") for it in dr["items"])):
            bars.append(r)
    # rules repeated at the same width a little further down are table rows
    # or grid lines, not fraction bars
    rep = set()
    for i, a in enumerate(bars):
        for j, b in enumerate(bars):
            if i != j and abs(a.x0 - b.x0) < 1.5 and abs(a.x1 - b.x1) < 1.5 \
                    and 3 < abs(a.y0 - b.y0) < 60 and a.width > 12:
                rep.add(i)
    tb = data.get("_tables", [])
    bars = [r for i, r in enumerate(bars) if i not in rep and not any(
        t[0] - 1 <= r.x0 and r.x1 <= t[2] + 1 and t[1] - 1 <= r.y0 <= t[3] + 1 for t in tb)]
    if not bars:
        return
    spans = []
    for b in data["blocks"]:
        if b["type"]:
            continue
        for ln in b["lines"]:
            for sp in ln["spans"]:
                if (sp["text"].strip() and not FIG_FONTS.match(sp["font"])
                        and sp["size"] >= 6 and not sp.get("_used")):
                    spans.append(sp)
    new_lines = []
    for r in sorted(bars, key=lambda r: r.width):
        y = (r.y0 + r.y1) / 2

        def inside(sp):
            x0, _y0, x1, _y1 = sp["bbox"]
            cx = (x0 + x1) / 2
            return (r.x0 - 2.5 <= cx <= r.x1 + 2.5 and x0 >= r.x0 - 4
                    and x1 <= r.x1 + 5 and not sp.get("_used"))
        num = [sp for sp in spans if inside(sp) and sp["bbox"][3] <= y + 3.5
               and sp["bbox"][3] >= y - 5 and (sp["bbox"][1] + sp["bbox"][3]) / 2 < y]
        den = [sp for sp in spans if inside(sp) and sp["bbox"][1] >= y - 3.5
               and sp["bbox"][1] <= y + 5 and (sp["bbox"][1] + sp["bbox"][3]) / 2 > y]
        if num and den:
            # scripts hang below/above the glyphs that touch the rule: ε₀ in
            # a denominator, r² in a numerator
            for grp, sign in ((num, -1), (den, 1)):
                top = min(sp["bbox"][1] for sp in grp)
                bot = max(sp["bbox"][3] for sp in grp)
                big = max(sp["size"] for sp in grp)
                for sp in spans:
                    if (sp in num or sp in den or not inside(sp)
                            or sp["size"] >= 0.86 * big):
                        continue
                    cy = (sp["bbox"][1] + sp["bbox"][3]) / 2
                    if top - 3 <= cy <= bot + 3 and (cy - y) * sign > 0:
                        grp.append(sp)
            latex = r"\frac{" + spans_latex(num) + "}{" + spans_latex(den) + "}"
            for sp in num + den:
                sp["_used"] = True
                sp["text"] = ""
            size = max(sp["size"] for sp in num + den)
            new_lines.append({"bbox": (r.x0, y - size / 2, r.x1, y + size / 2), "dir": (1, 0),
                              "spans": [{"text": "□", "latex": latex, "font": "math",
                                         "size": max(size, 9.5), "flags": 0,
                                         "origin": (r.x0, y + size * 0.3),
                                         "bbox": (r.x0, y - size / 2, r.x1, y + size / 2)}]})
            continue
        if r.width < 7:
            below = [sp for sp in spans if not sp.get("_used")
                     and sp["bbox"][1] - 1.5 <= y <= (sp["bbox"][1] + sp["bbox"][3]) / 2
                     and sp["bbox"][0] <= r.x0 + 2 and sp["bbox"][2] >= r.x1 - 2]
            for sp in below:
                t = sp["text"]
                # which character sits under the rule
                cw = (sp["bbox"][2] - sp["bbox"][0]) / max(len(t), 1)
                k = int(((r.x0 + r.x1) / 2 - sp["bbox"][0]) / cw) if cw else 0
                if 0 <= k < len(t) and t[k].isalpha():
                    sp["overbar"] = k
                break
    if new_lines:
        data["blocks"].append({"type": 0, "bbox": (0, 0, 0, 0), "lines": new_lines})


def find_tables(page):
    """Ruled tables, as (bbox, cell rows). find_tables() sees the rules; the
    cells' text is rendered by render_spans so that "4 × 10²⁶" keeps its
    exponent. Grids inside figures (graph paper, pixel diagrams) are tables to
    find_tables too; a table counts only if most of its text is body type."""
    try:
        found = page.find_tables().tables
    except Exception:
        return []
    out = []
    for t in found:
        rows = []
        for row in t.rows:
            rows.append([c for c in row.cells])
        if t.row_count < 2 or t.col_count < 2:
            continue
        out.append((tuple(t.bbox), rows))
    return out


def table_markdown(bbox, rows, spans):
    """Markdown table from cell boxes and the page's spans.

    find_tables merges rows that have no rule between them into one tall
    cell; such a row is split again by baseline, a sub-row being any baseline
    that opens text in two or more columns (a wrapped cell's second line opens
    text in only one, and stays with the line above)."""
    body = [s for s in spans if not FIG_FONTS.match(s["font"])]
    if not body:
        return None

    def inside(sp, box):
        cx = (sp["bbox"][0] + sp["bbox"][2]) / 2
        cy = (sp["bbox"][1] + sp["bbox"][3]) / 2
        return box[0] - 1 <= cx <= box[2] + 1 and box[1] - 1 <= cy <= box[3] + 1

    ncol = max(len(r) for r in rows)
    out_rows = []
    for row in rows:
        cells = [c for c in row]
        cell_spans = [[sp for sp in spans if c and inside(sp, c)] for c in cells]
        ys = sorted({round((sp["origin"][1]) / 2.5) for cs in cell_spans for sp in cs
                     if sp["text"].strip() and sp["size"] >= 8})
        # cluster baselines
        lines_y = []
        for y in ys:
            if lines_y and y - lines_y[-1][-1] <= 1:
                lines_y[-1].append(y)
            else:
                lines_y.append([y])
        groups = []
        for grp in lines_y:
            cols = sum(1 for cs in cell_spans
                       if any(round(sp["origin"][1] / 2.5) in grp and sp["text"].strip() for sp in cs))
            if groups and cols < 2:
                groups[-1] += grp
            else:
                groups.append(list(grp))
        if len(groups) <= 1:
            groups = [None]

        def home(sp, groups=groups):
            """The sub-row a span belongs to: its own baseline, or for a
            raised exponent the nearest baseline at or just below it."""
            y = round(sp["origin"][1] / 2.5)
            for g in groups:
                if g is not None and y in g:
                    return g
            best, dist = None, 9
            for g in groups:
                if g is None:
                    continue
                d = min(abs(x - y) for x in g)
                below = max(g) >= y
                if d <= 3 and (below, -d) > ((best is not None and max(best) >= y), -dist):
                    best, dist = g, d
            return best
        for grp in groups:
            r = []
            for cs in cell_spans:
                sub = [sp for sp in cs if grp is None or home(sp) is grp]
                # one line per baseline, in reading order
                sub.sort(key=lambda sp: (round(sp["origin"][1] / 4), sp["bbox"][0]))
                txt = []
                cur, cur_y = [], None
                for sp in sub:
                    yy = sp["origin"][1]
                    if cur and sp["size"] >= 8 and cur_y is not None and abs(yy - cur_y) > 4:
                        txt.append(render_spans(sorted(cur, key=lambda q: q["bbox"][0])))
                        cur = []
                    if sp["size"] >= 8:
                        cur_y = yy
                    cur.append(sp)
                if cur:
                    txt.append(render_spans(sorted(cur, key=lambda q: q["bbox"][0])))
                cell = " ".join(x.strip() for x in txt if x.strip())
                r.append(cell.replace("|", "\\|"))
            r += [""] * (ncol - len(r))
            if any(r):
                out_rows.append(r)
    if len(out_rows) < 2:
        return None
    keep = [j for j in range(ncol) if any(r[j] for r in out_rows)]
    out_rows = [[r[j] for j in keep] for r in out_rows]
    if len(keep) < 2 or sum(1 for r in out_rows for c in r if c) < 4:
        return None
    md = ["| " + " | ".join(out_rows[0]) + " |",
          "|" + "---|" * len(keep)]
    md += ["| " + " | ".join(r) + " |" for r in out_rows[1:]]
    return "\n".join(md)


def same_baseline(a, b):
    if a.get("table") or b.get("table"):
        return False
    ya, yb = (a["bbox"][1] + a["bbox"][3]) / 2, (b["bbox"][1] + b["bbox"][3]) / 2
    return abs(ya - yb) < 3.5 and -6 < b["bbox"][0] - a["bbox"][2] < 14


def join_split_lines(kept):
    """MuPDF sometimes ends a block in mid-line — "kinetic energy = ½ mass ×
    (speed)²" arrives as two blocks, cut at the fraction. A block whose first
    line continues another block's last line on the same baseline is glued
    back on."""
    kept = [(list(bb), list(lines)) for bb, lines in kept]
    changed = True
    while changed:
        changed = False
        for i, (bba, la) in enumerate(kept):
            for j, (bbb, lb) in enumerate(kept):
                if i == j or not la or not lb:
                    continue
                if same_baseline(la[-1], lb[0]):
                    last, first = la[-1], lb[0]
                    last["spans"] = last["spans"] + first["spans"]
                    last["bbox"] = [min(last["bbox"][0], first["bbox"][0]),
                                    min(last["bbox"][1], first["bbox"][1]),
                                    max(last["bbox"][2], first["bbox"][2]),
                                    max(last["bbox"][3], first["bbox"][3])]
                    la.extend(lb[1:])
                    kept[i] = ([min(bba[0], bbb[0]), min(bba[1], bbb[1]),
                                max(bba[2], bbb[2]), max(bba[3], bbb[3])], la)
                    kept[j] = (bbb, [])
                    changed = True
        kept = [k for k in kept if k[1]]
    return kept


def reading_order(blocks, depth=0):
    """Recursive XY-cut. The content stream is not reading order: on the
    summary pages the two-column summary at the top of the page comes after
    the questions below it. Cut the page into horizontal bands wherever no
    block straddles the gap, split a band into columns the same way, repeat."""
    if len(blocks) <= 1 or depth > 12:
        return sorted(blocks, key=lambda b: (b[0][1], b[0][0]))
    for axis in (1, 0):                       # rows first, then columns
        lo, hi = axis, axis + 2
        items = sorted(blocks, key=lambda b: b[0][lo])
        groups, cur, edge = [], [], None
        for b in items:
            if cur and b[0][lo] > edge + 1.5:
                groups.append(cur)
                cur, edge = [], None
            cur.append(b)
            edge = b[0][hi] if edge is None else max(edge, b[0][hi])
        groups.append(cur)
        if len(groups) > 1:
            return [x for g in groups for x in reading_order(g, depth + 1)]
    return sorted(blocks, key=lambda b: (b[0][1], b[0][0]))


def page_markdown(page):
    rect = page.rect
    data = page.get_text("dict")
    data["_drawings"] = page.get_drawings()
    tables = find_tables(page)
    data["_tables"] = [t[0] for t in tables]
    rebuild_fractions(data)
    # a fraction's own line goes into the line it sits on, ordered by x
    extra = [b for b in data["blocks"] if b["type"] == 0 and b["bbox"] == (0, 0, 0, 0)]
    for eb in extra:
        rest = []
        for fl in eb["lines"]:
            fy = (fl["bbox"][1] + fl["bbox"][3]) / 2
            host = None
            for b in data["blocks"]:
                if b is eb or b["type"]:
                    continue
                for ln in b["lines"]:
                    ly = (ln["bbox"][1] + ln["bbox"][3]) / 2
                    if (abs(ly - fy) < 4 and ln["bbox"][0] - 16 < fl["bbox"][2]
                            and fl["bbox"][0] < ln["bbox"][2] + 16
                            and any(sp["text"].strip() for sp in ln["spans"])):
                        host = ln
                        break
                if host:
                    break
            if host:
                host["spans"] = sorted(host["spans"] + fl["spans"], key=lambda sp: sp["bbox"][0])
                host["bbox"] = (min(host["bbox"][0], fl["bbox"][0]), min(host["bbox"][1], fl["bbox"][1]),
                                max(host["bbox"][2], fl["bbox"][2]), max(host["bbox"][3], fl["bbox"][3]))
            else:
                rest.append(fl)
        eb["lines"] = rest
        eb["bbox"] = (min((l["bbox"][0] for l in rest), default=0),
                      min((l["bbox"][1] for l in rest), default=0),
                      max((l["bbox"][2] for l in rest), default=0),
                      max((l["bbox"][3] for l in rest), default=0))
    images = [b["bbox"] for b in data["blocks"] if b["type"] == 1
              and (b["bbox"][2] - b["bbox"][0]) * (b["bbox"][3] - b["bbox"][1]) > 4000
              and b["bbox"][3] - b["bbox"][1] < rect.height * 0.9]

    kept = []           # (bbox, lines) per block, furniture and artwork removed
    for b in data["blocks"]:
        if b["type"] != 0:
            continue
        lines = []
        for ln in b["lines"]:
            spans = [s for s in ln["spans"]
                     if not (s["font"].startswith("DIN-Medium") and s["size"] >= 19
                             and s["text"].strip().isdigit())]      # topic tab number
            if not spans or furniture(ln, spans, rect):
                continue
            lines.append({"bbox": list(ln["bbox"]), "spans": spans})
        # merge lines that MuPDF split off a raised/lowered script
        merged = []
        for ln in lines:
            sz = line_size(ln["spans"])
            if merged and sz and sz < 8.3:
                prev = merged[-1]
                psz = line_size(prev["spans"])
                pb, lb = prev["bbox"], ln["bbox"]
                if psz >= 9 and lb[1] < pb[3] and lb[3] > pb[1] and lb[0] >= pb[0] - 2:
                    prev["spans"] = sorted(prev["spans"] + ln["spans"],
                                           key=lambda s: s["bbox"][0])
                    prev["bbox"] = [min(pb[0], lb[0]), min(pb[1], lb[1]),
                                    max(pb[2], lb[2]), max(pb[3], lb[3])]
                    continue
            merged.append(ln)
        merged = [ln for ln in merged
                  if not figure_text(ln["spans"], line_size(ln["spans"]), ln["bbox"], images)]
        if merged:
            bb = [min(l["bbox"][0] for l in merged), min(l["bbox"][1] for l in merged),
                  max(l["bbox"][2] for l in merged), max(l["bbox"][3] for l in merged)]
            kept.append((bb, merged))

    # tables: their text leaves the running blocks and comes back as one
    # markdown table at the table's place in the reading order
    all_spans = [sp for b in data["blocks"] if b["type"] == 0
                 for ln in b["lines"] for sp in ln["spans"] if sp["text"].strip()]
    for tbbox, rows in tables:
        tspans = [sp for sp in all_spans
                  if tbbox[0] - 1 <= (sp["bbox"][0] + sp["bbox"][2]) / 2 <= tbbox[2] + 1
                  and tbbox[1] - 1 <= (sp["bbox"][1] + sp["bbox"][3]) / 2 <= tbbox[3] + 1]
        md_t = table_markdown(tbbox, rows, tspans)
        if not md_t:
            continue

        def in_t(ln):
            cx = (ln["bbox"][0] + ln["bbox"][2]) / 2
            cy = (ln["bbox"][1] + ln["bbox"][3]) / 2
            return tbbox[0] - 1 <= cx <= tbbox[2] + 1 and tbbox[1] - 1 <= cy <= tbbox[3] + 1
        nk = []
        for bb, lines in kept:
            lines = [ln for ln in lines if not in_t(ln)]
            if lines:
                nk.append(([min(l["bbox"][0] for l in lines), min(l["bbox"][1] for l in lines),
                            max(l["bbox"][2] for l in lines), max(l["bbox"][3] for l in lines)],
                           lines))
        kept = nk + [(list(tbbox), [{"bbox": list(tbbox), "table": md_t, "spans": []}])]

    kept = join_split_lines(kept)
    paras = []          # [kind, text]  kind: "h2".."h4", "p", "table"
    for _bb, merged in reading_order(kept):
        cur = None
        prev_fam = None
        for ln in merged:
            if ln.get("table"):
                paras.append(["table", ln["table"]])
                cur = None
                continue
            spans = ln["spans"]
            lvl = heading_level(spans)
            if lvl == -1:
                cur = None
                continue
            raw = "".join(clean(s["text"]) for s in spans).strip()
            text = render_spans(spans).strip()
            if not text:
                continue
            if lvl:
                plain_text = re.sub(r"\*\*", "", text)
                if cur and cur[0] == f"h{lvl}" and paras and paras[-1] is cur:
                    cur[1] += " " + plain_text
                else:
                    cur = [f"h{lvl}", plain_text]
                    paras.append(cur)
                continue
            item = starts_item(spans)
            if re.fullmatch(r"\[\d{1,2}\]", raw) and cur is not None and cur[0] == "p":
                cur[1] += " " + text                          # mark allocation
                continue
            if raw.startswith("▲"):
                text = re.sub(r"^▲\s*", "", text)
            if raw.startswith("★") or raw.startswith("»"):
                text = "- " + re.sub(r"^[★»]\s*", "", text)
            fam = family(spans)
            switched = prev_fam is not None and fam != prev_fam
            prev_fam = fam
            if cur is None or cur[0].startswith("h") or item or switched:
                cur = ["p", text]
                paras.append(cur)
            elif cur[1].endswith("-") and not cur[1].endswith(" -"):
                cur[1] += text
            else:
                cur[1] += " " + text
        cur = None
        if paras and paras[-1][0] == "p":
            paras[-1] = paras[-1] + ["end"]

    # a paragraph carried into the next block (same sentence) is one paragraph
    out = []
    for p in paras:
        kind, text = p[0], p[1]
        if (kind == "p" and out and out[-1][0] == "p"
                and (text[:1].islower() or text[:1] == "$")
                and not re.search(r"[.:?!]\**$", out[-1][1])):
            out[-1][1] += " " + text
            continue
        out.append([kind, text])

    md = []
    for kind, text in out:
        text = re.sub(r"[ ]{2,}", " ", text).strip()
        text = re.sub(r"\s+▲\s*", "\n\n", text)        # two captions run together
        if kind.startswith("h"):
            md.append("#" * int(kind[1]) + " " + text)
        else:
            md.append(text)
    return "\n\n".join(md) + "\n"


def write_pages(pdf, out_dir, first=1, last=None):
    d = fitz.open(pdf)
    last = min(last or d.page_count, d.page_count)
    os.makedirs(out_dir, exist_ok=True)
    empty = []
    for pn in range(first, last + 1):
        md = page_markdown(d[pn - 1])
        if len(md.strip()) < 20:
            empty.append(pn)
        with open(os.path.join(out_dir, f"page_{pn:04d}.md"), "w", encoding="utf-8") as f:
            f.write(md)
    d.close()
    print(f"p{first}-{last}: {last - first + 1} 页 -> {out_dir}")
    if empty:
        print(f"  几乎没有文字的页 {len(empty)} 个:{empty[:30]}")


OPTS = ("--from", "--to", "--level")


def main(argv):
    a, opts, i = [], {}, 0
    while i < len(argv):
        if argv[i] in OPTS and i + 1 < len(argv):
            opts[argv[i]] = argv[i + 1]
            i += 2
            continue
        a.append(argv[i])
        i += 1
    if len(a) < 3:
        sys.exit(__doc__)
    if a[0] == "pages":
        write_pages(a[1], a[2], int(opts.get("--from", 1)),
                    int(opts["--to"]) if "--to" in opts else None)
    elif a[0] == "chapters":
        lv = opts.get("--level")
        tbl = chapter_table(a[1], int(lv) if lv else None)
        with open(a[2], "w", encoding="utf-8") as f:
            json.dump(tbl, f, ensure_ascii=False, indent=1)
        for e in tbl:
            print(f"  ch{e['chapter']:02d} p{e['page_from']:>4}-{e['page_to']:<4} {e['title']}")
        print(f"{len(tbl)} 章 -> {a[2]}")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
