#!/usr/bin/env python3
"""Drop OCR mark schemes (ms_latex) that miss parts the text-layer scheme has.

    python3 pipeline/ocr/drop_partial_ms_ocr.py [--write]

Every reader prefers ms_latex over ms_text. For some schemes the OCR kept
only one part: 9618_s22_22_q08 has 8(a) 8(b) 8(c) in ms_text (1786 chars)
but only 8(c) in ms_latex (562 chars), the pseudocode answers of 8(a) and
8(b) lost. A row is dropped when a part label of ms_text ("8(a)", "3(b)(ii)")
does not occur in ms_latex and ms_latex is under 60% of ms_text's length;
ms_quality is then graded from ms_text. Run split_parts.py --write after, so
the per-part schemes come from the full text. Dry run by default.
"""
import argparse, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
from lib import db  # noqa: E402
from pipeline.text.audit_text import classify_ms  # noqa: E402

LABEL = re.compile(r"(?m)^\s*(\d{1,2}(?:\([a-z]\))?(?:\([ivx]+\))?)\s")
ANY = re.compile(r"(\d{1,2}(?:\([a-z]\))?(?:\([ivx]+\))?)")


def partial(ms_text, ms_latex):
    """Part labels of ms_text missing from ms_latex, [] when it is complete."""
    have = set(ANY.findall(ms_latex))
    miss = sorted(x for x in set(LABEL.findall(ms_text)) if "(" in x and x not in have)
    return miss if miss and len(ms_latex) < 0.6 * len(ms_text) else []


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    con = db.connect()
    rows = con.execute(
        "SELECT id, syllabus, ms_text, ms_latex FROM questions WHERE ms_text IS NOT NULL "
        "AND ms_latex IS NOT NULL AND syllabus IN ('9709', '9231', '9618')").fetchall()
    upd = []
    for qid, syl, mt, ml in rows:
        miss = partial(mt, ml)
        if miss:
            upd.append((classify_ms(mt, syl != "9618"), qid))
            print(f"{qid}: OCR 缺 {', '.join(miss[:6])}({len(ml)}/{len(mt)} 字)")
    print(f"去掉 {len(upd)} 题的 OCR 评分细则,改用文本层")
    if a.write:
        con.executemany("UPDATE questions SET ms_latex=NULL, ms_quality=? WHERE id=?", upd)
        con.commit()
        print("已写入")
    else:
        print("(dry run;加 --write 写入)")


if __name__ == "__main__":
    main()
