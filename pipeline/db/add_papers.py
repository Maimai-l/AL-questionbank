#!/usr/bin/env python3
"""Add the question papers the bank does not have yet, without rebuilding it.

    python3 pipeline/db/add_papers.py add    [--write]
    python3 pipeline/db/add_papers.py finish [--write]

combine.py rebuilds the questions table from the per-subject databases and
would drop everything done to it since (OCR, fixes, model tags, quality
flags), so papers downloaded later (fetch_fraft.py) are added in place.

add     every question paper in raw/pdf whose paper id (9709_s26_21) has no
        row: split (split_qp.split_paper), crop to data/img<subject>/
        (crop.render), attach the mark scheme parsed from raw/ms
        (split_ms.parse), tag with the syllabus model restricted to the
        component's topics (topic_source 'syllabus'; 9709 P2 and P6 have no
        keyword table, and every new row goes to the tagger agents after),
        and insert the rows as build_db.py builds them, with their q_fts rows.
        Writes raw/new_papers/questions.json (image names included) for
        ocr.py and raw/new_papers/new_ids.txt for tag_batches.py --ids-file.
finish  after the OCR (ocr.py -> apply_reocr.py; ocr_ms.py -> parse_ms_ocr.py
        -> merge_ms_ocr.py): grades q_quality and ms_quality of the new rows
        as flag_quality.py does, without touching the rest of the table.

Dry run by default. Then run the rest of the chain on the whole table as usual
(rebuild_text.py, rebuild_ms.py, split_parts.py, build_site.py).
"""
import argparse, json, os, sqlite3, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
from lib import db, paths  # noqa: E402
from pipeline.db import build_db  # noqa: E402
from pipeline.split import crop, split_ms, split_qp  # noqa: E402
from pipeline.tags import topic_model  # noqa: E402

SUBJECTS = ("9709", "9231", "9618")
OUT = os.path.join(paths.RAW, "new_papers")


def paper_id(f):
    """9709_s26_qp_21.pdf -> 9709_s26_21"""
    return f.replace("_qp_", "_").replace("_ms_", "_")[:-4]


def new_papers(con):
    have = {r[0] for r in con.execute("SELECT DISTINCT substr(id, 1, 11) FROM questions")}
    return [f for f in sorted(os.listdir(os.path.join(paths.RAW, "pdf")))
            if "_qp_" in f and f[:4] in SUBJECTS and paper_id(f) not in have]


def tag(models, q, ms_text):
    """Topic from the syllabus model, within the component's own topics."""
    m = models[q["subject"]]
    scored = m.score(q["text"], q["component"], ms_text or "")
    if q["subject"] == "9618":                 # 9618 tags at section level
        best = {}
        for s, c, _h in scored:
            k = c.split(".")[0]
            if s > best.get(k, (-1, None))[0]:
                best[k] = (s, c)
        ranked = sorted(best, key=lambda k: -best[k][0])
        names = {t["component"]: t["component_name"] for t in m.topics.values()}
        name = names.get(ranked[0]) if ranked else None
        sub = best[ranked[0]][1] if ranked else None
    else:
        ranked = [c for _s, c, _h in scored]
        name = m.topics[ranked[0]]["name"] if ranked else None
        sub = ranked[0] if ranked else None
    q.update(topic=ranked[0] if ranked else None, topic_name=name,
             topics_all=ranked[:3], topic_confident=0, topic_margin=None,
             topic_source="syllabus", subtopic=sub)


def add(a):
    con = db.connect()
    files = new_papers(con)
    print(f"库中没有的试卷 {len(files)} 份")
    models = topic_model.load()
    pdfdir, msdir = os.path.join(paths.RAW, "pdf"), os.path.join(paths.RAW, "ms")
    by_subject, ms_by_subject, short = {}, {}, []
    for f in files:
        qs = split_qp.split_paper(os.path.join(pdfdir, f))
        if len(qs) < 4:
            short.append(f"{f}: {len(qs)} 题")
        ms_file = f.replace("_qp_", "_ms_")
        ms = split_ms.parse(os.path.join(msdir, ms_file)) \
            if os.path.exists(os.path.join(msdir, ms_file)) else []
        mk = {m["q"]: m for m in ms}
        for q in qs:
            tag(models, q, (mk.get(q["q"]) or {}).get("ms_text"))
        by_subject.setdefault(f[:4], []).extend(qs)
        ms_by_subject.setdefault(f[:4], []).extend(ms)
    n = sum(len(v) for v in by_subject.values())
    print(f"切出 {n} 题:" + ",".join(f"{s} {len(v)}" for s, v in sorted(by_subject.items())))
    print(f"评分细则:" + ",".join(f"{s} {len(v)} 题" for s, v in sorted(ms_by_subject.items())))
    for s in short:
        print("  题数过少:", s)
    if not a.write:
        print("(dry run;加 --write 裁图并写入)")
        return

    os.makedirs(OUT, exist_ok=True)
    allq, ids = [], []
    for subject, qs in sorted(by_subject.items()):
        imgdir = os.path.join(paths.DATA, f"img{subject}")
        os.makedirs(imgdir, exist_ok=True)
        for q in qs:
            try:
                q["image"] = crop.render(q, pdfdir, imgdir)
            except Exception:
                q["image"] = None
        with tempfile.TemporaryDirectory() as tmp:
            qj, mj = os.path.join(tmp, "q.json"), os.path.join(tmp, "m.json")
            json.dump(qs, open(qj, "w"))
            json.dump(ms_by_subject.get(subject, []), open(mj, "w"))
            tdb = os.path.join(tmp, "new.db")
            build_db.main(subject, qj, mj, tdb)
            con.execute("ATTACH DATABASE ? AS new", (tdb,))
            cols = [r[1] for r in con.execute("PRAGMA new.table_info(questions)")]
            con.execute(f"INSERT INTO questions ({','.join(cols)}) "
                        f"SELECT {','.join(cols)} FROM new.questions")
            con.execute("INSERT INTO q_fts (id, question_text, ms_text, topic_name) "
                        "SELECT id, question_text, ms_text, topic_name FROM new.q_fts")
            ids += [r[0] for r in con.execute("SELECT id FROM new.questions")]
            con.commit()
            con.execute("DETACH DATABASE new")
        for q in qs:
            qid = f"{subject}_{q['series']}_{q['component']}{q['variant']}_q{q['q']:02d}"
            con.execute("UPDATE questions SET subtopic=? WHERE id=?", (q.get("subtopic"), qid))
        allq += qs
    con.commit()
    json.dump(allq, open(os.path.join(OUT, "questions.json"), "w"), ensure_ascii=False, indent=1)
    open(os.path.join(OUT, "new_ids.txt"), "w").write("\n".join(ids) + "\n")
    print(f"已写入 {len(ids)} 题;题图 {sum(1 for q in allq if q.get('image'))} 张 -> {OUT}")


def finish(a):
    from pipeline.text.audit_text import classify_ms, classify_q
    from pipeline.text.flag_quality import RANK
    ids = open(os.path.join(OUT, "new_ids.txt")).read().split()
    con = db.connect()
    upd, dropped = [], 0
    for qid in ids:
        syl, ql, qt, ml, mt = con.execute(
            "SELECT syllabus, question_latex, question_text, ms_latex, ms_text "
            "FROM questions WHERE id=?", (qid,)).fetchone()
        maths = syl in ("9709", "9231")
        gl = classify_ms(ml, maths) if ml else "missing"
        gt = classify_ms(mt, maths) if mt else "missing"
        if ml and RANK[gl] > RANK[gt]:
            upd.append(("UPDATE questions SET ms_latex=NULL WHERE id=?", (qid,)))
            ml, dropped = None, dropped + 1
        upd.append(("UPDATE questions SET q_quality=?, ms_quality=? WHERE id=?",
                     (classify_q(ql), gl if ml else gt, qid)))
    grades = [u[1][0] for u in upd if u[0].startswith("UPDATE questions SET q_quality")]
    import collections
    print(f"{len(ids)} 道新题;题干 {dict(collections.Counter(grades))};"
          f"去掉不如文本层的 OCR 评分细则 {dropped}")
    if a.write:
        for sql, args in upd:
            con.execute(sql, args)
        con.commit()
        print("已写入")
    else:
        print("(dry run;加 --write 写入)")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["add", "finish"])
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    {"add": add, "finish": finish}[a.mode](a)


if __name__ == "__main__":
    main()
