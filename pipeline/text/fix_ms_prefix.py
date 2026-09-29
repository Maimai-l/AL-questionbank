#!/usr/bin/env python3
"""Move text that parse_ms_ocr.py filed at the head of the wrong mark scheme.

    python3 pipeline/text/fix_ms_prefix.py [--write]

parse_ms_ocr.py starts a new question at any table row whose first cell is a
number. A stem-and-leaf row ("3 | 2 0 3 0 6 7"), a rank ("4 | 6 -5 1 ..."), a
row of test data ("5 | Bee") or a numbered note of the general marking
instructions ("3 Allow alternative conventions ...") therefore opens the
scheme of question 3, 4 or 5, and whatever follows up to that question's own
"3(a)" lands in front of it (9231_s23_43_q04 began with the rank test of q3).

For a question with parts whose own "N(a)" row comes more than 40 characters
into ms_latex, the text before it is taken off. The PDF text layer (ms_text,
split correctly by split_ms.py) of the same paper says whose it is — the
question holding most of its lines: if that question's ms_latex lacks some of
them, the text is appended there; if no question has it, it
was the general instructions and is dropped. A question whose ms_latex is empty
is left empty rather than given a fragment. Dry run by default.
"""
import argparse, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
from lib import db  # noqa: E402

WS = re.compile(r"\s+")


def probes(text):
    """Each line of prose in the text, without whitespace or markup."""
    out = []
    for l in text.split("\n"):
        l = re.sub(r"\$[^$]*\$|\|", " ", l)
        if len(re.findall(r"[A-Za-z]", l)) >= 10:
            out.append(WS.sub("", l)[:20])
    return out


def owner_of(head, paper, rows, self_id):
    """The question of the paper whose ms_text holds most lines of head."""
    keys = probes(head)
    best, hits = None, 0
    for j, s in rows.items():
        if j.startswith(paper + "_") and j != self_id:
            t = WS.sub("", s["ms_text"] or "")
            n = sum(k in t for k in keys)
            if n > hits:
                best, hits = j, n
    return best, keys


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    con = db.connect()
    rows = {r["id"]: dict(r) for r in con.execute(
        "SELECT id, q, ms_latex, ms_text FROM questions "
        "WHERE syllabus IN ('9709','9231','9618')")}

    upd = {}
    for i, r in rows.items():
        lat = r["ms_latex"]
        if not lat:
            continue
        m = re.search(r"(?m)^\s*%d\s*\(a\)" % r["q"], lat)
        if not m or m.start() <= 40:
            continue
        head = lat[:m.start()].rstrip()
        owner, keys = owner_of(head, i.rsplit("_", 1)[0], rows, i)
        key = keys[0] if keys else ""
        upd[i] = lat[m.start():]
        if owner is None:
            what = "丢弃(评分通则)"
        elif not rows[owner]["ms_latex"]:
            what = f"丢弃({owner} 没有 ms_latex)"
        elif all(k in WS.sub("", rows[owner]["ms_latex"]) for k in keys):
            what = f"丢弃({owner} 已有)"
        else:
            upd[owner] = upd.get(owner, rows[owner]["ms_latex"]).rstrip() + "\n" + head
            what = f"移到 {owner} 末尾"
        print(f"{i}: 去掉开头 {len(head)} 字 -> {what}  [{key}]")

    print(f"共改动 {len(upd)} 题")
    if not a.write:
        print("(dry run;加 --write 写入)")
        return
    con.executemany("UPDATE questions SET ms_latex=? WHERE id=?",
                    [(v, k) for k, v in upd.items()])
    con.execute("DELETE FROM q_fts")
    con.execute("INSERT INTO q_fts(id,question_text,ms_text,topic_name) SELECT id, "
                "COALESCE(question_latex,question_text), COALESCE(ms_latex,ms_text), "
                "topic_name FROM questions")
    con.commit()
    print("已写入")


if __name__ == "__main__":
    main()
