#!/usr/bin/env python3
"""Rescue what is readable from a degenerated OCR result.

Degeneration is nearly always a *tail* failure: the model reads the question
correctly, then falls into a loop. Cutting at the first sign of the loop keeps
the good prefix instead of throwing the whole record away. If too little
survives, the field is cleared so callers fall back to the PDF text layer.
"""
import re, sqlite3, sys

sys.path.insert(0, __file__.rsplit("/", 1)[0] if "/" in __file__ else ".")
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))          # 项目根目录
from lib import paths
from pipeline.text.audit_text import CJK, BLANK_RUN, DIGIT_RUN, degenerate
from pipeline.text.clean_encoding import SUSPECT

MIN_KEEP = 60


def cut_point(text):
    """Index of the earliest degeneration marker, or None."""
    idx = []
    for rx in (CJK, SUSPECT, BLANK_RUN, DIGIT_RUN):
        m = rx.search(text)
        if m:
            idx.append(m.start())
    m = re.search(r"(.{4,40}?)\1{14,}", text)
    if m and len(m.group(0)) > 0.4 * len(text):
        idx.append(m.start())
    return min(idx) if idx else None


def salvage(text):
    """Return the readable prefix, or None if nothing usable survives."""
    if not text or not degenerate(text):
        return text
    i = cut_point(text)
    if i is None:
        return None
    head = text[:i].rstrip()
    # don't end mid-formula
    if head.count("$") % 2:
        head = head[:head.rfind("$")].rstrip()
    if len(head) < MIN_KEEP or degenerate(head):
        return None
    return head


def main(dbpath):
    con = sqlite3.connect(dbpath)
    con.row_factory = sqlite3.Row
    stats = {"q_trimmed": 0, "q_cleared": 0, "ms_trimmed": 0, "ms_cleared": 0}
    for r in con.execute("SELECT id, question_latex, ms_latex, ms_text "
                         "FROM questions").fetchall():
        if r["question_latex"] and degenerate(r["question_latex"]):
            new = salvage(r["question_latex"])
            con.execute("UPDATE questions SET question_latex=? WHERE id=?",
                        (new, r["id"]))
            stats["q_trimmed" if new else "q_cleared"] += 1
        if r["ms_latex"] and degenerate(r["ms_latex"]):
            new = salvage(r["ms_latex"])
            # the text layer is a better fallback than a truncated mark scheme
            if not new or (r["ms_text"] and len(r["ms_text"]) > len(new)):
                new = None
            con.execute("UPDATE questions SET ms_latex=? WHERE id=?",
                        (new, r["id"]))
            stats["ms_trimmed" if new else "ms_cleared"] += 1
    con.commit()
    print(f"题干:截断保留 {stats['q_trimmed']},清空回退 {stats['q_cleared']}")
    print(f"答案:截断保留 {stats['ms_trimmed']},清空回退 {stats['ms_cleared']}")
    con.close()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else paths.DB)
