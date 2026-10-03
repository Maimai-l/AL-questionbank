#!/usr/bin/env python3
"""Extract the official subject content from a CAIE syllabus PDF.

Why bother, when the bank already has topic labels: those labels come from
keyword lists I wrote by eye. The syllabus is the authority — every topic's
learning outcomes in Cambridge's own wording, which is also the wording the
question writers reach for. Read once, it replaces guesswork with evidence.

The layout is the same across 9709 / 9231 / 9618:

    62pt  "1"            component number      \\  same visual line
    85pt  "Pure Mathematics 1"   component name /
    62pt  "1.5<TAB> Trigonometry"              topic heading
    62pt  "Candidates should be able to:"
    62pt  "•"  79pt "sketch and use graphs ..."   left column: outcomes
   309pt  "Including e.g. y = 3 sin x ..."        right column: notes

so the split is a single x threshold. Maths in the left column comes out of
the text layer scrambled ("tan y x 4 1 r = + c m") — that is fine and expected.
The prose carries the terminology, and the prose is intact.
"""
import json, re, sys

import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))          # 项目根目录
from lib import paths as project_paths

try:
    import fitz
except ImportError:
    sys.exit("需要 PyMuPDF:  pip install pymupdf")

COL_X = 300.0          # left of this = learning outcome, right = notes
ROW_TOL = 6.0          # fragments this close vertically are one visual row
HEAD_Y, FOOT_Y = 40.0, 800.0
# Two shapes for the same heading. 9709/9231 put code and title on one line
# ("1.5<TAB> Trigonometry"); 9618 and a few 9231 pages split them into two
# text lines at the same y ("2.1" / "Networks including the internet").
TOPIC_RE = re.compile(r"^(\d{1,2}\.\d{1,2})[\t ]*(.*)$")
# component heading comes both ways too: alone on its line, or with the name
COMP_RE = re.compile(r"^(\d{1,2})[\t ]*$")
COMP1_RE = re.compile(r"^(\d{1,2})[\t ]+(\S.*)$")
SKIP = re.compile(r"Back to contents page|cambridgeinternational\.org|"
                  r"syllabus for \d{4}")
# Cambridge sets Greek through a Monotype font whose bytes come out as Latin.
# Only the mappings confirmed from unambiguous context are listed: 'i' is theta
# (cos i / sin i = tan i), 'r' is pi, '|' is chi (the chi-squared tests), 'm' is
# mu (distribution Po m), 'a' is alpha. The rest are left alone rather than
# guessed at — they occur a handful of times, all inside worked examples.
GREEK_FONT = "MMGreek"
GREEK = {"i": "\u03b8", "r": "\u03c0", "|": "\u03c7", "m": "\u03bc", "a": "\u03b1"}
STOP = re.compile(r"Candidates should be able to|Notes and (examples|guidance)")
# The subject-content section ends with advice to teachers — equipment lists,
# recommended books, "Computing is a practical subject". It carries no topic
# heading, so without this it accretes onto whatever topic came last: 9618's
# section 20 was carrying seven "learning outcomes" about the BCS book list.
END_SECTION = re.compile(r"^(Teacher guidance|Additional information|"
                         r"Support for .*teachers|Resources)\b", re.I)
# the syllabus states prerequisites in prose; this is the only place the
# ordering between components is written down
PREREQ = re.compile(r"(knowledge of .{0,120}?is assumed|"
                    r"assumed for this component|prior knowledge)", re.I)


def page_lines(page):
    out = []
    for b in page.get_text("dict")["blocks"]:
        if b.get("type"):
            continue
        for l in b["lines"]:
            t = "".join(
                "".join(GREEK.get(c, c) for c in s["text"])
                if GREEK_FONT in s["font"] else s["text"]
                for s in l["spans"]).strip()
            x0, y0 = l["bbox"][0], l["bbox"][1]
            if not t or y0 < HEAD_Y or y0 > FOOT_Y or SKIP.search(t):
                continue
            out.append((round(y0, 1), round(x0, 1), t))
    if not out:
        return out

    # Cluster into visual rows before ordering. The bullet glyph sits a point
    # or two below the text it introduces, so a plain sort by y puts it *after*
    # its own first line and every outcome gets attributed to the previous
    # bullet. Rows first, then left-to-right inside the row.
    out.sort()
    rows, cur = [], [out[0]]
    for f in out[1:]:
        if f[0] - cur[-1][0] <= ROW_TOL:
            cur.append(f)
        else:
            rows.append(cur); cur = [f]
    rows.append(cur)

    flat = []
    for r in rows:
        y = min(f[0] for f in r)
        for _, x, t in sorted(r, key=lambda f: f[1]):
            flat.append((y, x, t))
    return flat


def is_content_page(page):
    return "Subject content" in page.get_text()[:200]


def paragraphs(lines):
    """Join wrapped lines; a bullet or a vertical gap starts a new one."""
    paras, cur, prev_y, hard = [], [], None, True
    def close():
        if cur:
            paras.append((hard, " ".join(cur)))
    for y, x, t in lines:
        if t in ("•", "‧", "·"):
            close(); cur, hard = [], True      # a bullet is a real boundary
            prev_y = y
            continue
        if prev_y is not None and y - prev_y > 18 and cur:
            close(); cur, hard = [], False     # a gap only might be
        cur.append(t)
        prev_y = y
    close()
    paras = [(h, re.sub(r"\s{2,}", " ", p).strip())
             for h, p in paras if len(p.strip()) > 3]

    # A stray formula opens a vertical gap mid-sentence, splitting one outcome
    # in two. Undo that — but only where the split came from a gap. A bullet
    # boundary is authoritative, and most outcomes do begin lower-case
    # ("use the derivative of ..."), so merging on case alone eats the list.
    # A gap-split fragment continues the previous outcome, but only on evidence.
    # 9709 and 9231 bullet their outcomes, so anything unbulleted is a
    # continuation; 9618 does not bullet at all, and merging on "the previous
    # line has no full stop" alone collapsed its 255 outcomes into 68.
    DANGLING = ("in", "of", "the", "a", "an", "and", "or", "with", "for", "to",
                "from", "on", "at", "by", "as", "into", "using", "including",
                "between", "such", "which", "that", "their", "its")
    merged = []
    for h, p_ in paras:
        prev = merged[-1].rstrip() if merged else ""
        if merged and not h and not prev.endswith((".", ":", ";")) and (
                p_[:1].islower()
                or p_[:1] in "-–—"
                or prev.split()[-1].lower() in DANGLING):
            merged[-1] += " " + p_
        else:
            merged.append(p_)
    return merged


def parse(path):
    doc = fitz.open(path)
    code = re.search(r"\b(9709|9231|9618)\b", doc[0].get_text()).group(1)

    topics, comp_no, comp_name, cur = {}, None, None, None
    prereqs, prior_block = [], []
    for pno in range(doc.page_count):
        page = doc[pno]
        if not is_content_page(page):
            continue
        raw = page.get_text()
        if "Prior knowledge" in raw:
            # the 9231 prior-knowledge table is a table, so no single line
            # matches a prose pattern — keep the page whole and mine it later
            prior_block.append(raw)
        lines = page_lines(page)
        i = 0
        while i < len(lines):
            y, x, t = lines[i]
            if x < 70:
                m = COMP_RE.match(t)
                if m and i + 1 < len(lines) and abs(lines[i + 1][0] - y) < 4:
                    comp_no, comp_name = m.group(1), lines[i + 1][2]
                    # a new paper starts: its preamble ("Knowledge of the
                    # following probability notation is assumed") belongs to no
                    # topic, and without this it is glued onto the last topic of
                    # the previous paper
                    cur = None
                    i += 2
                    continue
                m = COMP1_RE.match(t)
                if m and not STOP.search(t):
                    comp_no, comp_name = m.group(1), m.group(2).strip()
                    cur = None
                    i += 1
                    continue
                m = TOPIC_RE.match(t)
                if m and not STOP.search(t):
                    cur, name = m.group(1), m.group(2).strip()
                    skip = 1
                    if not name and i + 1 < len(lines) and abs(lines[i + 1][0] - y) < 4:
                        name, skip = lines[i + 1][2], 2
                    topics.setdefault(cur, {
                        "code": cur, "name": name,
                        "component": comp_no, "component_name": comp_name,
                        "outcomes": [], "notes": []})
                    i += skip
                    continue
            if END_SECTION.match(t) and x < 70:
                cur = None
                i += 1
                continue
            if PREREQ.search(t):
                prereqs.append({"component": comp_no, "text": t})
            if cur and not STOP.search(t):
                topics[cur].setdefault("_L" if x < COL_X else "_R", []).append((y, x, t))
            i += 1

    for tp in topics.values():
        tp["outcomes"] = paragraphs(tp.pop("_L", []))
        tp["notes"] = paragraphs(tp.pop("_R", []))
    # 9618 splits its sections into an AS half and an A Level half, and says so
    # only in the contents tree; the A Level papers assume the AS ones.
    levels = {}
    for lv, title, _pg in doc.get_toc():
        m = re.match(r"(AS|A Level) content", title.strip())
        if m:
            levels.setdefault(m.group(1), title)
    return code, topics, prereqs, "\n".join(prior_block), sorted(levels)


def main(pdfs, out=None):
    out = out or project_paths.SYLLABUS
    all_ = {}
    for p in pdfs:
        code, topics, prereqs, prior, levels = parse(p)
        all_[code] = {"source": p.rsplit("/", 1)[-1], "topics": topics,
                      "prerequisites": prereqs, "prior_knowledge": prior,
                      "levels": levels}
        n_out = sum(len(t["outcomes"]) for t in topics.values())
        print(f"{code}: {len(topics)} 个 topic,{n_out} 条 learning outcome,"
              f"{len(prereqs)} 条先修说明")
        for c in sorted(topics, key=lambda k: [int(x) for x in k.split(".")]):
            t = topics[c]
            print(f"   {c:<5} {t['name'][:44]:<46} "
                  f"outcomes {len(t['outcomes']):>2}  notes {len(t['notes']):>2}")
    json.dump(all_, open(out, "w"), ensure_ascii=False, indent=1)
    print(f"\n-> {out}")


if __name__ == "__main__":
    main(sys.argv[1:] or sys.exit("用法: syllabus.py a.pdf b.pdf c.pdf"))
