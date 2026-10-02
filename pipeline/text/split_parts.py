#!/usr/bin/env python3
"""Split each CAIE question and its mark scheme into its parts.

    python3 pipeline/text/split_parts.py [--write]

Writes the column part_data, JSON:

  {"stem": text before the first part,
   "parts": [{"label": "b(ii)", "marks": 3, "topic": "1.6", "sub": ...,
              "intro": "(b) ... text of (b) before its (i)",
              "text": "(ii) ...", "ms": "8(b)(ii) ... rows of the scheme",
              "task": "prove"}],
   "text_split": true | false}

so that an export can give just the parts a chapter or a paper needs, with
their own marks, topic and mark scheme: the stem, the part's intro and its
text read as a question on their own.

Parts are the lowest-level labels of question_latex in order: (a), (b), and
(i), (ii) under a letter. marks come from marks_parts (the paper's tariffs,
in the same order), topics from topic_parts, the scheme rows from the lines
of ms_latex (or ms_text) that open with "8(b)(ii)". When the labels found do
not match the tariffs one for one (the OCR dropped an "(a)", about one
question in ten), text_split is false and each part keeps only its label,
marks, topic and scheme; an export shows the whole question then.
Single-part questions get one part holding the whole text. task is what the
part asks for, from its command words (TASKS_CS for 9618: sql, trace,
write_code ...; TASKS_MATHS for 9709 and 9231: prove, sketch, find ...); an
unsplit question's parts all take the task of its whole text. Dry run by default.
"""
import argparse, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
from lib import db  # noqa: E402

ROMAN = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"]
LABEL = re.compile(r"(?:(?<=^)|(?<=[\s>|]))\(\s*([a-h]|i{1,3}|iv|vi{0,3}|ix|x)\s*\)(?=\s|$)", re.M)

# The task of a part, from its command words; the first pattern that matches
# its text (intro + text, or the whole question) wins, so the more specific
# tasks come first. 9618 papers set code, SQL and traces; 9709 and 9231 set
# proofs, sketches and tests.
TASKS_CS = [
    ("sql", r"(?i:\b(?:Write|Complete|Amend)\b[^.]{0,80}\b(?:SQL|D[DM]L)\b)"),
    ("assembly", r"(?i:\b(?:Write|Complete|Amend)\b[^.]{0,80}\b(?:assembly|machine code)\b)"),
    ("trace", r"\btrace table\b|\bDry[- ]run\b|\bTrace\b"),
    ("logic", r"\bBoolean\b|\bsum[- ]of[- ]products\b|\bKarnaugh\b|\blogic (?:expression|circuit)\b"),
    ("complete_code", r"(?i:\bComplete the (?:\w+ ){0,2}(?:pseudocode|program|algorithm|code|procedure|"
                      r"function)\b(?! flowchart))"),
    ("write_code", r"(?i:\bWrite (?:the |an? |your )?(?:\w+ ){0,3}(?:pseudocode|program code|program|code|"
                   r"algorithm|procedure|function|module|method|constructor|class)\b)|\bAmend\b|\bEdit\b"),
    ("draw", r"\bDraw\b|(?i:\bComplete the (?:\w+ ){0,2}(?:diagram|truth table|flowchart|table|"
             r"state[- ]transition))"),
    ("test", r"\bTest\b|\btest data\b"),
    ("calculate", r"(?i:\b(?:Calculate|Convert|Evaluate|Work out|Show your working)\b)"),
    ("explain", r"(?i:\b(?:Explain|Describe|State|Identify|Give|Outline|Define|Compare|Justify|Tick|"
                r"Complete|Write|Circle|Draw a line|Suggest|Name)\b)"),
]
TASKS_MATHS = [
    ("prove", r"(?i:\b(?:Show|Prove|Verify)\b(?!\s+(?:all|your|clearly|full|each|every)\b))"),
    ("sketch", r"(?i:\b(?:Sketch|Draw|Shade|Plot)\b|\bOn (?:a|the same) (?:diagram|axes|Argand)\b|"
               r"\bComplete the (?:\w+ ){0,2}(?:diagram|graph|table)\b)"),
    ("hypothesis_test", r"(?i:\bTest,? at\b|\bCarry out a\b.*\btest\b|\bsignificance level\b)"),
    ("explain", r"(?i:\b(?:Explain|Describe|Comment|Suggest|Interpret|Give a reason|State|Justify|"
                r"comparison|Compare)\b)"),
    ("find", r"(?i:\b(?:Find|Calculate|Solve|Evaluate|Determine|Obtain|Express|Deduce|Write down|"
             r"Use|Using|Hence|Simplify|Expand|Differentiate|Integrate|Estimate|How many|What is)\b)"),
]


def task_of(text, syllabus):
    """Task of a part: the first pattern of its syllabus found in the text."""
    if not text:
        return None
    for name, pat in TASKS_CS if syllabus == "9618" else TASKS_MATHS:
        if re.search(pat, text):
            return name
    return "other"


def leaves(t):
    """[(label, start, letter_start)] of the lowest-level parts, in order.
    A letter that is followed by (i) is not a leaf itself; a label out of
    sequence ("(c)" quoted inside a sentence) is ignored."""
    out, letter, letter_at, want_letter, want_roman = [], None, None, "a", 0
    for m in LABEL.finditer(t or ""):
        x = m.group(1)
        if x == want_letter:
            letter, letter_at = x, m.start()
            want_letter, want_roman = chr(ord(x) + 1), 0
            out.append([x, m.start(), m.start()])
        elif letter and want_roman < len(ROMAN) and x == ROMAN[want_roman]:
            if want_roman == 0 and out and out[-1][0] == letter:
                out.pop()                         # (b) is split into (i), (ii)
            out.append([f"{letter}({x})", m.start(), letter_at])
            want_roman += 1
    return out


def ms_rows(ms, q):
    """{label: rows of the scheme}; label "b(ii)" for a row opening "8(b)(ii)"."""
    heads = list(re.finditer(r"(?m)^\s*%d\s*\(([a-h])\)(?:\s*\(([ivx]+)\))?" % q, ms or ""))
    out = {}
    for k, h in enumerate(heads):
        end = heads[k + 1].start() if k + 1 < len(heads) else len(ms)
        lab = h.group(1) + (f"({h.group(2)})" if h.group(2) else "")
        out[lab] = (out.get(lab, "") + "\n" + ms[h.start():end].strip()).strip()
    return out


def split(row):
    t = row["question_latex"] or row["question_text"] or ""
    marks = json.loads(row["marks_parts"] or "[]")
    tp = {p["part"]: p for p in json.loads(row["topic_parts"] or "[]")}
    ms = ms_rows(row["ms_latex"] or row["ms_text"], row["q"])
    L = leaves(t)
    if len(marks) <= 1 and not L:
        p = tp.get("") or next(iter(tp.values()), {})
        return {"stem": "", "text_split": True, "parts": [{
            "label": "", "marks": marks[0] if marks else row["marks"],
            "topic": p.get("topic") or row["topic"], "sub": p.get("sub"),
            "intro": "", "text": t, "ms": row["ms_latex"] or row["ms_text"] or "",
            "task": task_of(t, row["syllabus"])}]}
    ok = len(L) == len(marks)
    labels = [l[0] for l in L] if ok else [p for p in tp] or [str(k + 1) for k in range(len(marks))]
    parts = []
    for k, lab in enumerate(labels):
        letter = lab.split("(")[0]
        p = tp.get(lab) or tp.get(letter) or {}
        part = {"label": lab, "marks": marks[k] if k < len(marks) else p.get("marks"),
                "topic": p.get("topic") or row["topic"], "sub": p.get("sub"),
                "intro": "", "text": None,
                "ms": ms.get(lab) or ms.get(letter) or ""}
        if ok:
            _, start, letter_at = L[k]
            end = L[k + 1][1] if k + 1 < len(L) else len(t)
            part["text"] = t[start:end].strip()
            if letter_at < start:                  # "(b) intro (i) ..." : keep the intro
                first = next(l[1] for l in L if l[2] == letter_at)
                part["intro"] = t[letter_at:first].strip()
        part["task"] = task_of(part["text"] or t, row["syllabus"])
        parts.append(part)
    return {"stem": t[:L[0][1]].strip() if ok and L else "", "text_split": ok, "parts": parts}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    con = db.connect()
    db.add_column(con, "questions", "part_data")
    rows = con.execute("SELECT id, syllabus, q, marks, marks_parts, topic, topic_parts, question_latex, "
                       "question_text, ms_latex, ms_text FROM questions "
                       "WHERE syllabus IN ('9709','9231','9618')").fetchall()
    upd, split_ok, ms_ok, nparts = [], 0, 0, 0
    for r in rows:
        d = split(r)
        split_ok += d["text_split"]
        nparts += len(d["parts"])
        ms_ok += sum(1 for p in d["parts"] if p["ms"])
        upd.append((json.dumps(d, ensure_ascii=False), r["id"]))
    import collections
    tasks = collections.defaultdict(collections.Counter)
    for r, (d, _) in zip(rows, upd):
        for p in json.loads(d)["parts"]:
            tasks[r["syllabus"]][p["task"]] += 1
    for syl, c in sorted(tasks.items()):
        print(syl, dict(c.most_common()))
    print(f"{len(rows)} 题,{nparts} 个小问;题干按小问切开 {split_ok} 题"
          f"({split_ok / len(rows):.1%}),有评分细则片段的小问 {ms_ok}({ms_ok / nparts:.1%})")
    if a.write:
        con.executemany("UPDATE questions SET part_data=? WHERE id=?", upd)
        con.commit()
        print("已写入 part_data")
    else:
        print("(dry run;加 --write 写入)")


if __name__ == "__main__":
    main()
