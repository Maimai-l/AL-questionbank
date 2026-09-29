#!/usr/bin/env python3
"""Repoint image filenames at their real subject prefix.

crop.py originally hard-coded the 9709 subject code into every crop name, so
the 9231 and 9618 crops were written as 9709_*.png. The files on disk have
been renamed; this fixes the references in the question JSON and remaps any
OCR cache entries that were keyed under the old name.
"""
import json, os, sys


def fix_questions(qjson, subject, imgdir):
    Q = json.load(open(qjson))
    n = 0
    for q in Q:
        img = q.get("image")
        if img and not img.startswith(subject + "_"):
            q["image"] = subject + "_" + img.split("_", 1)[1]
            n += 1
    json.dump(Q, open(qjson, "w"), ensure_ascii=False, indent=1)
    missing = sum(1 for q in Q if q.get("image")
                  and not os.path.exists(os.path.join(imgdir, q["image"])))
    print(f"{qjson}: renamed {n} references, {missing} still missing on disk")


def fix_cache(cache, subject):
    if not os.path.exists(cache):
        return
    kept, dropped = [], 0
    for ln in open(cache):
        ln = ln.strip()
        if not ln:
            continue
        try:
            d = json.loads(ln)
        except Exception:
            continue
        if "latex" not in d:          # failed entries: drop so they are retried
            dropped += 1
            continue
        if not d["id"].startswith(subject + "_"):
            d["id"] = subject + "_" + d["id"].split("_", 1)[1]
        kept.append(json.dumps(d, ensure_ascii=False))
    open(cache, "w").write("\n".join(kept) + "\n")
    print(f"{cache}: kept {len(kept)} results, dropped {dropped} failures")


if __name__ == "__main__":
    subject, qjson, imgdir, cache = sys.argv[1:5]
    fix_questions(qjson, subject, imgdir)
    fix_cache(cache, subject)
