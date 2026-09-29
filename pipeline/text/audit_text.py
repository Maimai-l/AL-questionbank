#!/usr/bin/env python3
"""Measure how readable each text field actually is.

Two very different pipelines feed the bank:
  question_latex  — PaddleOCR-VL read the crop, so maths survives as LaTeX
  ms_text         — pdftotext -layout on the mark scheme, which keeps the table
                    columns but silently drops '=', '-', superscripts and
                    fraction bars from mathematical typesetting

The tell for the second failure is orphaned single characters: real prose has
few, a stripped equation is almost nothing but. Count them, and count how often
a maths mark scheme contains no '=' at all — which cannot happen in a genuine
one.
"""
import re, sqlite3, sys, collections

CJK = re.compile(r"[㐀-鿿豈-﫿]")
BAD = re.compile("[\ufffd]")
# single letters that legitimately stand alone in maths/English prose
OK_SINGLES = set("aAIioxynrtkmspqPQRSTABCDEFGHOXYZuvwzcdefghjlb0123456789")

# OCR degeneration takes several shapes: a Chinese character hallucinated into
# an identifier, a run of newlines, a run of zeros. A truth table legitimately
# repeats "0 | 1 |", so a bare repetition test would flag real content —
# require the repeated unit to be blank, or the run to dominate the text.
# Whole scripts that cannot appear in an English-language CAIE paper. Greek is
# excluded on purpose — α, θ, π are ordinary maths.
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))          # 项目根目录
from lib import paths
from pipeline.text.clean_encoding import SUSPECT
BLANK_RUN = re.compile(r"(?:\s*\\n\s*){10,}|\n{10,}")
DIGIT_RUN = re.compile(r"\d{25,}")


def degenerate(text):
    if not text:
        return False
    if CJK.search(text) or SUSPECT.search(text):
        return True
    if BLANK_RUN.search(text) or DIGIT_RUN.search(text):
        return True
    m = re.search(r"(.{4,40}?)\1{14,}", text)
    if m and len(m.group(0)) > 0.4 * len(text):
        return True
    return False



# LaTeX is legitimately full of one-character tokens ($ + = -), so they must be
# removed before counting orphans — otherwise a perfectly typeset mark scheme
# scores worse than the stripped mush it replaced.
MATH_PUNCT = set("$+-=<>()[]{}|,.;:/*^_&!?'\"\u2212\u00d7\u00f7\u2264\u2265\u2260")
LATEX_CMD = re.compile(r"\\[a-zA-Z]+")


# A truth table or trace table is legitimately nothing but single characters —
# "| 0 | 1 | 0 |". Counting those rows as orphans marks the cleanest tables in
# the bank as damaged, so they are removed before the ratio is taken.
def _is_data_row(line):
    if line.count("|") < 2:
        return False
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    cells = [c for c in cells if c]
    if not cells:
        return True
    # a mark-scheme row is "answer | M1 | guidance" — long cells, keep it.
    # a truth-table row is "0 | 1 | 0 | 1" — every cell a character or two.
    return sum(len(c) for c in cells) / len(cells) <= 3


def strip_data_rows(text):
    return "\n".join(" " if _is_data_row(l) else l for l in text.split("\n"))


def orphan_ratio(text):
    t = strip_data_rows(text)
    t = LATEX_CMD.sub(" ", t)
    toks = [x for x in t.split() if x not in MATH_PUNCT]
    toks = [x for x in toks if not all(ch in MATH_PUNCT for ch in x)]
    if len(toks) < 20:
        return 0.0
    single = sum(1 for x in toks if len(x) == 1)
    return single / len(toks)


def classify_ms(text, is_maths):
    """Return a verdict string for one mark scheme."""
    if not text or len(text.strip()) < 40:
        return "missing"
    if degenerate(text):
        return "severe"
    r = orphan_ratio(text)
    if is_maths:
        eq = text.count("=") + text.count("≡")
        if r > 0.45 or (eq == 0 and r > 0.30):
            return "severe"
        if r > 0.30 or eq < 2:
            return "degraded"
        return "ok"
    if r > 0.45:
        return "severe"
    if r > 0.30:
        return "degraded"
    return "ok"


def classify_q(text):
    if not text or len(text.strip()) < 30:
        return "missing"
    if degenerate(text) or BAD.search(text):
        return "garbled"
    if orphan_ratio(text) > 0.40:
        return "degraded"
    return "ok"


def main(db):
    c = sqlite3.connect(db)
    c.row_factory = sqlite3.Row
    cols = {r[1] for r in c.execute("PRAGMA table_info(questions)")}
    msf = "ms_latex" if "ms_latex" in cols else "ms_text"
    rows = c.execute(f"SELECT id, syllabus, question_latex, question_text, "
                     f"COALESCE({msf}, ms_text) AS ms FROM questions").fetchall()

    qv = collections.defaultdict(collections.Counter)
    mv = collections.defaultdict(collections.Counter)
    examples = collections.defaultdict(list)
    for r in rows:
        s = r["syllabus"]
        maths = s in ("9709", "9231")
        vq = classify_q(r["question_latex"])
        qv[s][vq] += 1
        if vq != "ok" and len(examples[f"q:{s}:{vq}"]) < 3:
            examples[f"q:{s}:{vq}"].append(r["id"])
        vm = classify_ms(r["ms"], maths)
        mv[s][vm] += 1
        if vm not in ("ok", "missing") and len(examples[f"ms:{s}:{vm}"]) < 3:
            examples[f"ms:{s}:{vm}"].append(r["id"])

    def show(title, d):
        print(f"\n{title}")
        print(f"  {'科目':<8}{'ok':>7}{'degraded':>11}{'severe/garbled':>17}{'missing':>10}   可读率")
        for s in sorted(d):
            t = d[s]
            n = sum(t.values())
            bad = t["severe"] + t["garbled"]
            print(f"  {s:<8}{t['ok']:>7}{t['degraded']:>11}{bad:>17}{t['missing']:>10}"
                  f"   {t['ok']/n*100:>5.1f}%")

    show("题干 question_latex", qv)
    show("Mark scheme (ms_latex 优先, 回退 ms_text)", mv)

    print("\n样本:")
    for k, v in sorted(examples.items()):
        print(f"  {k}: {', '.join(v)}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else paths.DB)
