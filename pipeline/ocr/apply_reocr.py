#!/usr/bin/env python3
"""Replace question_latex with a fresh OCR of the current crops.

    python3 pipeline/ocr/apply_reocr.py <cache.jsonl> [--write]

For crops re-rendered after the bank was built (pipeline/ocr/reocr_pending.txt
lists the 220 of the 2026-09 split fixes), run each PNG through
pipeline/ocr/ocr.py's ocr_one() into a JSONL cache ({"id", "latex",
"has_diagram"}), then this folds the cache in. Unlike merge_ocr.py, which
precedes step 8, it runs the step-8 chain on each result itself (glyphs ->
line breaks -> tables), then cuts the end matter as rebuild_text.py does, so
nothing else has to be re-run over the whole table.

A new result replaces the old one only if audit_text grades it 'ok'; q_quality
becomes 'ok' (a salvaged 'partial' prefix is superseded by the full question).
Anything else keeps the old text and is listed. Dry run by default; q_fts is
rebuilt on --write.
"""
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
from lib import db  # noqa: E402
from pipeline.split.rebuild_text import cut_end_matter  # noqa: E402
from pipeline.text.audit_text import classify_q  # noqa: E402
from pipeline.text.clean_encoding import clean  # noqa: E402
from pipeline.text.fix_newlines import unescape  # noqa: E402
from pipeline.text.html_tables import convert  # noqa: E402


def normalise(latex):
    t = clean(latex)[0]
    t = unescape(t)[0]
    t = convert(t)[0]
    return cut_end_matter(t)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cache")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()

    got = {}
    for ln in open(a.cache):
        d = json.loads(ln)
        if d.get("latex"):
            got[d["id"]] = d
    con = db.connect()
    upd, kept = [], []
    for qid, d in sorted(got.items()):
        r = con.execute("SELECT question_latex, q_quality FROM questions WHERE id=?",
                        (qid,)).fetchone()
        if r is None:
            kept.append(f"{qid}: 库中没有")
            continue
        new = normalise(d["latex"])
        grade = classify_q(new)
        if grade != "ok":
            kept.append(f"{qid}: 新结果评为 {grade},保留旧文本({r['q_quality']})")
            continue
        old = r["question_latex"] or ""
        upd.append((new, int(bool(d.get("has_diagram"))), "ok", qid,
                    len(old), len(new), r["q_quality"]))

    ratios = sorted(u[5] / max(u[4], 1) for u in upd)
    print(f"缓存 {len(got)} 题;替换 {len(upd)},保留旧文本 {len(kept)}")
    if ratios:
        print(f"新旧长度比:最小 {ratios[0]:.2f},中位 {ratios[len(ratios)//2]:.2f},"
              f"最大 {ratios[-1]:.2f}")
    print("partial -> ok:", sum(1 for u in upd if u[6] == "partial"))
    for u in upd:
        if not 0.6 <= u[5] / max(u[4], 1) <= 1.6:
            print(f"  长度变化大 {u[3]}: {u[4]} -> {u[5]}")
    for k in kept:
        print("  " + k)
    if not a.write:
        print("(dry run;加 --write 写入)")
        return
    con.executemany("UPDATE questions SET question_latex=?, has_diagram=?, q_quality=? "
                    "WHERE id=?", [u[:4] for u in upd])
    con.execute("DELETE FROM q_fts")
    con.execute("INSERT INTO q_fts(id,question_text,ms_text,topic_name) SELECT id, "
                "COALESCE(question_latex,question_text), COALESCE(ms_latex,ms_text), "
                "topic_name FROM questions")
    con.commit()
    print("已写入")


if __name__ == "__main__":
    main()
