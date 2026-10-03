#!/usr/bin/env python3
"""Re-apply the 'partial' quality grade.

`salvage.py` truncates a degenerated OCR result at the first sign of the loop
and keeps the readable prefix. That prefix reads perfectly well, so every
downstream grader calls it 'ok' — which is dishonest: the later parts of the
question are simply missing, and nothing warns the reader. This walks the raw
OCR caches, finds the records whose stored text is a strict prefix of what the
model originally produced, and marks them 'partial'.
"""
import json, os, sqlite3, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))          # 项目根目录
from lib import paths

CACHES = ["ocr_cache.jsonl", "ocr9231.jsonl", "ocr9618.jsonl",
          "/tmp/regen.jsonl", "/tmp/regen2.jsonl"]


def raw_map():
    best = {}
    for path in CACHES:
        if not os.path.exists(path):
            continue
        for line in open(path):
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            qid, tx = d.get("id"), d.get("latex")
            if qid and tx and len(tx) > len(best.get(qid, "")):
                best[qid] = tx
    return best


def norm(s):
    return " ".join((s or "").split())


def main(dbpath=None):
    raw = raw_map()
    con = sqlite3.connect(dbpath)
    hits = []
    for qid, cur, grade in con.execute(
            "SELECT id, question_latex, q_quality FROM questions"):
        if not cur or grade != "ok":
            continue
        full = raw.get(qid)
        if not full:
            continue
        a, b = norm(cur), norm(full)
        # a truncation, not a different reading: strict prefix, meaningfully shorter
        if len(a) < len(b) - 20 and b.startswith(a[:max(40, len(a) - 5)]):
            hits.append(qid)
    con.executemany("UPDATE questions SET q_quality='partial' WHERE id=?",
                    [(q,) for q in hits])
    con.commit()
    print(f"标为 partial(截断保留,后半段缺失): {len(hits)}")
    for r in con.execute("SELECT q_quality, COUNT(*) FROM questions GROUP BY 1 ORDER BY 1"):
        print(f"  {r[0]:<9}{r[1]}")
    print("例:", ", ".join(hits[:8]))
    con.close()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else paths.DB)
