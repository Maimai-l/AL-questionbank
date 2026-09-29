#!/usr/bin/env python3
"""Replace question_latex with a fresh OCR of the current crops.

    python3 pipeline/ocr/apply_reocr.py <cache.jsonl> [--strip-bank] [--write]

For crops re-rendered after the bank was built (220 after the 2026-09 split
fixes), run each PNG through pipeline/ocr/ocr.py's ocr_one() into a JSONL cache
({"id", "latex", "has_diagram"}), then this folds the cache in. A text checked
by hand against the crop goes in the same way (pipeline/ocr/latex_checked.jsonl).
Unlike merge_ocr.py, which precedes step 8, it runs the step-8 chain on each
result itself (glyphs ->
line breaks -> tables), then cuts the end matter as rebuild_text.py does, so
nothing else has to be re-run over the whole table.

The answer space (dotted and ruled lines, which the model transcribes as long
arrays of numbered underlines) is dropped by pipeline/text/answer_lines.py. A new result replaces the old one only if
audit_text grades it 'ok' and it is not much shorter than the old text; q_quality
becomes 'ok' (a salvaged 'partial' prefix is superseded by the full question).
Anything else keeps the old text and is listed. Dry run by default; q_fts is
rebuilt on --write. --strip-bank also drops the answer lines from every other
row's question_latex (29 rows in 2026-09; 9709_w23_13_q02 alone 11 000 chars).
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
from pipeline.text.answer_lines import strip as strip_answer_lines  # noqa: E402


def normalise(latex):
    t = clean(latex)[0]
    t = unescape(t)[0]
    t = convert(t)[0]
    return strip_answer_lines(cut_end_matter(t))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cache")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--strip-bank", action="store_true",
                    help="也清掉库中其余题 question_latex 里的答题线")
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
        if len(new) < 0.6 * len(strip_answer_lines(old)):
            kept.append(f"{qid}: 新结果 {len(new)} 字,旧文本去掉答题线后 "
                        f"{len(strip_answer_lines(old))} 字,保留旧文本")
            continue
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
    stripped = []
    if a.strip_bank:
        done = {u[3] for u in upd}
        for qid, t in con.execute("SELECT id, question_latex FROM questions "
                                  "WHERE question_latex IS NOT NULL").fetchall():
            if qid not in done and strip_answer_lines(t) != t.strip():
                stripped.append((strip_answer_lines(t), qid))
        print(f"其余题中去掉答题线:{len(stripped)} 题,"
              f"{sum(len(t) for t, _ in stripped)} 字留下")
    if not a.write:
        print("(dry run;加 --write 写入)")
        return
    con.executemany("UPDATE questions SET question_latex=?, has_diagram=?, q_quality=? "
                    "WHERE id=?", [u[:4] for u in upd])
    con.executemany("UPDATE questions SET question_latex=? WHERE id=?", stripped)
    con.execute("DELETE FROM q_fts")
    con.execute("INSERT INTO q_fts(id,question_text,ms_text,topic_name) SELECT id, "
                "COALESCE(question_latex,question_text), COALESCE(ms_latex,ms_text), "
                "topic_name FROM questions")
    con.commit()
    print("已写入")


if __name__ == "__main__":
    main()
