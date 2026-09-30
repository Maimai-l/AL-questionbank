#!/usr/bin/env python3
"""Take the ruled answer space out of the question text.

    python3 pipeline/text/answer_lines.py [--write]

The answer space printed under a question is not part of the question, and
neither the text layer nor the OCR should carry it; the crop keeps it. It comes
back in three forms:

  * dotted lines, on a line of their own or inside a line (a blank table cell
    "| Pixel | .................... |", "\\underline{\\text{……}} \\\\ \\hline");
  * ruled lines the OCR reads as arrays of numbered or empty underlines, often
    hundreds long ("\\underline{\\text{1}} ... \\underline{\\text{524}}",
    9709_s22_11_q04), sometimes cut off mid-token;
  * lines of underscores ("___");
  * an array of empty rows ("\\(\\begin{array}{l}\\hline} \\\\ \\\\ ...", hundreds of them), or
    lines of CJK characters or radicals the model reads the rules as
    ("仝二", "⻴⻴⻴…", 9709_w25_15_q09, 9231_s25_34_q02). A line in brackets
    is never taken for one: "A (图形选项)" is an admissions placeholder.

Only runs of four or more full stops, or two or more ellipses, count as dots:
"0, 2, 4, ... ." in 9231_s21_43_q04 is an ellipsis and stays. strip() is used
by rebuild_text.py, apply_reocr.py and merge_admissions.py; run as a script it
cleans question_text and question_latex across the table (dry run by default).
"""
import argparse, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
from lib import db  # noqa: E402

DOTS = re.compile(r"…(?:[ \t]*…)+|\.{4,}|·{4,}")

LINE_TOKEN = (r"\\underline\{\\text\{[\s\d]*\}\}|\\text\{[\s\d]*\}|\\underline\{?|"
              r"\\uwave\{?|\\hline|"
              r"\\begin\{array\}(?:\{l\})?|\\end\{array\}|\\left\[|\\right\]|"
              r"\\\\|\\ |\\\(|\\\)|\$|\{|\}|\d+\.?|\s")
ANSWER_LINES = re.compile(r"(?>%s){40,}+" % LINE_TOKEN)
# what is left of a run cut short: "\text{", "\(\begin{array}{l}\underline{\", "\"
# (a line that is only a number is a question number or a datum, and stays)
ONLY_LINE_TOKENS = re.compile(r"(?>%s|\\text\{|\\)*+" % LINE_TOKEN)
UNDERSCORES = re.compile(r"\s*_{3,}\s*")
# the ruled lines read as CJK characters or radicals ("仝二", "⻴⻴⻴…"); a line
# in brackets ("A (图形选项)", the admissions placeholders) is never one
CJK = re.compile(r"[\u2e80-\u2fdf\u3400-\u9fff\uf900-\ufaff]")


def is_cjk_noise(line):
    s = re.sub(r"\s", "", line)
    if not s or re.search(r"[()（）\[\]]", s):
        return False
    return len(CJK.findall(s)) >= 0.5 * len(s)


def is_answer_lines(run):
    """Underlines, or line numbers counting from 1 ("1 2 3 ... 1040", 9618 CS
    papers) - not a list of data, which a statistics question may well print,
    nor the days 1 to 28 along the axis of a plan (TSA-2008-S1-q25)."""
    if len(run.strip()) < 60:
        return False
    if "\\underline" in run or run.count("\\\\") >= 20:
        return True                     # underlines, or an array of empty rows
    nums = [int(x) for x in re.findall(r"\d+", run)]
    return len(nums) >= 60 and nums[:60] == list(range(1, 61))


def strip(t):
    if not t:
        return t
    t = DOTS.sub("", t)
    t = ANSWER_LINES.sub(lambda m: "\n\n" if is_answer_lines(m.group(0)) else m.group(0), t)
    keep = []
    for l in t.split("\n"):
        if "\\" in l and ONLY_LINE_TOKENS.fullmatch(l):
            continue
        if UNDERSCORES.fullmatch(l) or is_cjk_noise(l):
            continue
        keep.append(l)
    t = "\n".join(keep)
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    con = db.connect()
    upd, n = [], {}
    for r in con.execute("SELECT id, question_text, question_latex FROM questions"):
        t, l = strip(r["question_text"]), strip(r["question_latex"])
        if (t, l) != (r["question_text"], r["question_latex"]):
            n["question_text"] = n.get("question_text", 0) + (t != r["question_text"])
            n["question_latex"] = n.get("question_latex", 0) + (l != r["question_latex"])
            upd.append((t, l, r["id"]))
    print(f"改动 {len(upd)} 题:{n}")
    left = sum(1 for (x,) in con.execute("SELECT question_latex FROM questions")
               if x and DOTS.search(x))
    print(f"改动前 question_latex 含虚线的题:{left}")
    if not a.write:
        print("(dry run;加 --write 写入)")
        return
    con.executemany("UPDATE questions SET question_text=?, question_latex=? WHERE id=?", upd)
    con.execute("DELETE FROM q_fts")
    con.execute("INSERT INTO q_fts(id,question_text,ms_text,topic_name) SELECT id, "
                "COALESCE(question_latex,question_text), COALESCE(ms_latex,ms_text), "
                "topic_name FROM questions")
    con.commit()
    print("已写入")


if __name__ == "__main__":
    main()
