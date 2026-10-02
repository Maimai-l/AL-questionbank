#!/usr/bin/env python3
"""Re-apply hand corrections of OCR mark schemes (pipeline/ocr/ms_fixes.jsonl).

    python3 pipeline/ocr/apply_ms_fixes.py [--write]

Each line is {"id", "column", "find", "replace", "why"}: the text `find` in
that column (ms_latex, ms_text or question_latex) is replaced, checked against
the page image. latex_fix_batches.py appends the formula corrections. Lines whose
`find` no longer occurs (already applied, or the scheme was re-OCR'd) are
reported and skipped. Run after merge_ms_ocr.py, before split_parts.py.
"""
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
from lib import db  # noqa: E402

FIXES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ms_fixes.jsonl")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    con = db.connect()
    done = 0
    for line in open(FIXES):
        f = json.loads(line)
        assert f["column"] in ("ms_latex", "ms_text", "question_latex")
        text = con.execute(f"SELECT {f['column']} FROM questions WHERE id=?",
                           (f["id"],)).fetchone()[0] or ""
        if f["find"] in f["replace"] and f["replace"] in text:
            continue                         # already applied (the replacement contains the text it replaces)
        if f["find"] not in text:
            print(f"{f['id']}: 未找到原文,跳过(已改过或已重新识别)")
            continue
        print(f"{f['id']}: {f['why']}")
        if a.write:
            con.execute(f"UPDATE questions SET {f['column']}=? WHERE id=?",
                        (text.replace(f["find"], f["replace"]), f["id"]))
        done += 1
    if a.write:
        con.commit()
    print(f"{done} 处" + ("已写入" if a.write else "待写入(dry run;加 --write)"))


if __name__ == "__main__":
    main()
