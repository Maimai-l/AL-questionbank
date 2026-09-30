#!/usr/bin/env python3
"""ms_total and totals_agree for the rows whose scheme exists only as OCR.

    python3 pipeline/split/ms_total_from_ocr.py [--write]

rebuild_ms.py reads the part totals off the text layer of the scheme PDF; 35
rows of the 2025-26 papers have no usable text layer (9709_s26_ms_13 cannot
be read at any of the three sites), only the OCR in ms_latex, so their
ms_total stayed empty and the paper-against-scheme check skipped them.

In the OCR each part opens with its label at the start of a line ("3(b)")
and ends with its total alone on a line ("  4", "(4)") or as "Available marks | 4"
after alternative methods; a 9618 scheme gives it in the Marks column of the
row ("... | 4 | guidance"). The total of a part is the first such line after
its label (alternative methods repeat the same total).
Where the sum disagrees with the paper, the award codes of the part (B1, M1,
A1, DM1, B2 ...) are counted as for rebuild_ms.py; ms_totals_checked.json
overrides both. Only rows with ms_text NULL are touched. Dry run by default.
"""
import argparse, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
from lib import db, paths  # noqa: E402

CHECKED = os.path.join(paths.ROOT, "pipeline", "split", "ms_totals_checked.json")
TOTAL = re.compile(r"^\s*(?:Available marks\s*\|\s*)?\(?(\d{1,2})\)?\s*$")
CELL = re.compile(r"\|\s*(\d{1,2})\s*(?:\||$)")       # 9618: the Marks column of a row
CODE = re.compile(r"\b\*?D?[BMA]([1-9])\b")


def part_totals(ms, qno, cells=False):
    """[(label, total or None, award-code count)] in the order of the scheme.

    Labels are the question's own number ("7", "7(b)", "7(b)(ii)") followed by
    two spaces or the line end, so a row of bits or "4 letters" is not one."""
    label = re.compile(rf"^\s*({qno}(?:\([a-z]\))?(?:\([ivx]+\))?)(?=\s{{2}}|$)")
    parts, cur = [], None
    for line in ms.splitlines():
        m = label.match(line)
        if m and (not parts or m.group(1) != parts[-1][0]) and not TOTAL.match(line):
            cur = [m.group(1), None, 0, False]
            parts.append(cur)
        if cur is None:
            continue
        t = TOTAL.match(line) or (cells and CELL.search(line))
        if t and cur[1] is None:
            cur[1] = int(t.group(1))
            cur[3] = True                      # codes after the total are an alternative
        elif not cur[3]:
            cur[2] += sum(int(c) for c in CODE.findall(line))
    return [(l, t, c) for l, t, c, _ in parts]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    checked = {k: v for k, v in json.load(open(CHECKED)).items() if not k.startswith("_")}
    con = db.connect()
    rows = con.execute("SELECT id, marks, ms_latex FROM questions WHERE ms_text IS NULL "
                       "AND ms_latex IS NOT NULL AND syllabus IN ('9709','9231','9618')"
                       ).fetchall()
    upd, bad = [], []
    for qid, marks, ms in rows:
        parts = part_totals(ms, int(qid.rsplit("_q", 1)[1]), qid.startswith("9618"))
        total = sum(t or 0 for _, t, _ in parts)
        how = "小计"
        if total != marks and sum(c for *_, c in parts) == marks:
            total, how = marks, "给分代码"
        if qid in checked:
            total, how = checked[qid]["ms_total"], "人工核定"
        agree = int(total == marks) if marks else None
        upd.append((total or None, agree, qid))
        line = (f"{qid}: 题面 {marks},细则 {total}({how};"
                + " + ".join(f"{l} {t}" for l, t, _ in parts) + ")")
        if not agree:
            bad.append(line)
    print(f"{len(rows)} 题只有 OCR 评分细则;与题面分值一致 {len(rows) - len(bad)},不一致 {len(bad)}")
    for line in bad:
        print("  " + line)
    if a.write:
        con.executemany("UPDATE questions SET ms_total=?, totals_agree=? WHERE id=?", upd)
        con.commit()
        print("已写入")
    else:
        print("(dry run;加 --write 写入)")


if __name__ == "__main__":
    main()
