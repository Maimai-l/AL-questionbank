#!/usr/bin/env python3
"""Bring the mark-scheme columns of the CAIE rows in line with split_ms.py.

    python3 pipeline/split/rebuild_ms.py [raw/ms] [--write]

The companion of rebuild_text.py: re-parses every mark scheme in the folder
and updates the rows in place rather than rebuilding the table (combine.py
would drop the OCR, the tags and the quality flags). Per question:

  ms_text, parts, mark_codes, ms_pdf
                  from the parse, through clean_encoding.clean() as in step 8.
                  Fills the rows that had no mark scheme (9709 s25 came from
                  papacambridge after the bank was built) and moves text the
                  old parser had filed under the previous question (a label
                  flush left or alone on its line, "10(c)(i)", "2(a)").
  ms_total, totals_agree
                  the sum of the part totals printed in the Marks column. Where
                  that disagrees with the paper's tariff but the award codes in
                  the column ("B1", "M1 A1", "B2,1,0") add up to it, the code
                  count is taken: the part total was misread, typically a
                  number from the Guidance column (9231_w22_ms_41 q6 read 19
                  off a fraction; the scheme says 9, and so do its codes).
                  ms_totals_checked.json holds the totals read off the PDF by
                  hand where neither count finds them, and overrides both.
  ms_quality      re-graded as flag_quality.py does, for rows whose ms_text
                  changed.

ms_latex (the OCR of the scheme) is not touched. Dry run by default; q_fts is
rebuilt on --write.
"""
import argparse, collections, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
from lib import db, paths  # noqa: E402
from pipeline.split import split_ms  # noqa: E402
from pipeline.text.audit_text import classify_ms  # noqa: E402
from pipeline.text.clean_encoding import clean  # noqa: E402
from pipeline.text.flag_quality import RANK  # noqa: E402

CHECKED = os.path.join(paths.ROOT, "pipeline", "split", "ms_totals_checked.json")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("msdir", nargs="?", default=os.path.join(paths.RAW, "ms"))
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()

    checked = {k: v for k, v in json.load(open(CHECKED)).items() if not k.startswith("_")}
    parsed = {}
    for f in sorted(os.listdir(a.msdir)):
        if "_ms_" in f:
            for m in split_ms.parse(os.path.join(a.msdir, f)):
                qid = f"{m['subject']}_{m['series']}_{m['component']}{m['variant']}_q{m['q']:02d}"
                parsed[qid] = m

    con = db.connect()
    rows = con.execute(
        "SELECT id, syllabus, marks, parts, ms_text, mark_codes, ms_total, totals_agree, "
        "ms_pdf, ms_latex, ms_quality FROM questions "
        "WHERE syllabus IN ('9709','9231','9618')").fetchall()

    upd, n = [], collections.Counter()
    left = []
    for r in rows:
        m = parsed.get(r["id"])
        if m is None:
            n["无评分细则"] += 1
            if r["ms_text"] is None:
                left.append(f"{r['id']}: 找不到评分细则")
            continue
        text = clean(m["ms_text"])[0]
        total = m["ms_total"]
        if total != r["marks"] and m["award_total"] == r["marks"]:
            total = m["award_total"]
            n["按给分代码计"] += 1
        if r["id"] in checked:
            total = checked[r["id"]]["ms_total"]
            n["人工核定"] += 1
        agree = int(total == r["marks"]) if total is not None and r["marks"] is not None else None
        if agree == 0 or total is None:
            left.append(f"{r['id']}: 题面 {r['marks']},评分细则 {total}"
                        f"(小计 {m['ms_total']},代码 {m['award_total']})")
        quality = r["ms_quality"]
        if text != r["ms_text"]:
            n["填入 ms_text" if r["ms_text"] is None else "改动 ms_text"] += 1
            maths = r["syllabus"] in ("9709", "9231")
            gt = classify_ms(text, maths)
            gl = classify_ms(r["ms_latex"], maths) if r["ms_latex"] else "missing"
            quality = gl if r["ms_latex"] and RANK[gl] <= RANK[gt] else gt
        if total != r["ms_total"]:
            n["改动 ms_total"] += 1
        new = (json.dumps(m["parts"]), text, json.dumps(m["mark_codes"]), total, agree,
               m["source"], quality)
        old = (r["parts"], r["ms_text"], r["mark_codes"], r["ms_total"], r["totals_agree"],
               r["ms_pdf"], r["ms_quality"])
        if new != old:
            upd.append(new + (r["id"],))

    final = {r["id"]: r["totals_agree"] for r in rows}
    final.update({u[-1]: u[4] for u in upd})
    before = sum(1 for r in rows if r["totals_agree"] == 1)
    after = sum(1 for v in final.values() if v == 1)
    print(f"{len(rows)} 题;将改动 {len(upd)} 题:" + ",".join(f"{k} {v}" for k, v in n.items()))
    print(f"题面分值与评分细则相符:{before} -> {after}")
    print(f"仍不相符或缺评分细则 {len(left)} 题:")
    for x in left:
        print("  " + x)
    if not a.write:
        print("(dry run;加 --write 写入)")
        return
    con.executemany("UPDATE questions SET parts=?, ms_text=?, mark_codes=?, ms_total=?, "
                    "totals_agree=?, ms_pdf=?, ms_quality=? WHERE id=?", upd)
    con.execute("DELETE FROM q_fts")
    con.execute("INSERT INTO q_fts(id,question_text,ms_text,topic_name) SELECT id, "
                "COALESCE(question_latex,question_text), COALESCE(ms_latex,ms_text), "
                "topic_name FROM questions")
    con.commit()
    print("已写入")


if __name__ == "__main__":
    main()
