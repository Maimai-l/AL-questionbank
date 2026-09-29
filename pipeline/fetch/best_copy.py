#!/usr/bin/env python3
"""Keep, for each new question paper, the copy that split_qp.py can split.

    python3 pipeline/fetch/best_copy.py [--write]

The three sites serve different files under the same name: fraft has some
2025-26 papers with unreadable fonts or retypeset on Letter paper,
papacambridge re-assembles some with FPDF (one text block per question, a
watermark image), dynamicpapers passes some through Ghostscript or PDFsharp.
split_qp.py reads the text layer and the margins, so a copy that looks right
can still split into nothing. For every question paper in raw/pdf that the
bank does not have, each copy is split and scored: the question total against
the component's printed total (9709 P1 75, P2 50 ...), then the number of
questions. The best copy replaces raw/pdf/<name> when it is better than the
one there. Mark schemes are not touched (split_ms.py reads them via
pdftotext, which copes). Dry run by default.
"""
import argparse, os, shutil, sys, tempfile, urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
from lib import db, paths  # noqa: E402
from pipeline.split import split_qp  # noqa: E402

SOURCES = {
    "fraft": "https://cie.fraft.cn/obj/Common/Fetch/redir/{name}",
    "papacambridge": "https://pastpapers.papacambridge.com/directories/CAIE/CAIE-pastpapers/upload/{name}",
    "dynamicpapers": "https://dynamicpapers.com/wp-content/uploads/2015/09/{name}",
}
TOTAL = {"9709": {"1": 75, "2": 50, "3": 75, "4": 50, "5": 50, "6": 50},
         "9231": {"1": 75, "2": 75, "3": 50, "4": 50},
         "9618": {"1": 75, "2": 75, "3": 75, "4": 75}}


def fetch(url):
    for k in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"},
                                         data=b"" if "fraft" in url else None)
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
            return data if data.startswith(b"%PDF") else None
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
        except Exception:
            pass
    return None


def score(path, name):
    """(total matches, -|total - printed|, questions) of the split."""
    try:
        qs = split_qp.split_paper(path)
    except Exception:
        return (0, -999, 0), 0, 0
    total = sum(q["marks"] or 0 for q in qs)
    want = TOTAL.get(name[:4], {}).get(name.split("_")[-1][0], 0)
    return (int(total == want), -abs(total - want), len(qs)), len(qs), total


def choose(name, write):
    """(name, source, matches the printed total, report line), or None when
    the copy on disk already splits to the printed total."""
    here = os.path.join(paths.RAW, "pdf", name)
    best = (score(here, name), "现有")
    if best[0][0][0] == 1:
        return None
    with tempfile.TemporaryDirectory() as tmp:
        for src, tpl in SOURCES.items():
            data = fetch(tpl.format(name=name))
            if not data:
                continue
            d = os.path.join(tmp, src)
            os.makedirs(d, exist_ok=True)
            p = os.path.join(d, name)              # split_qp reads the ids from the name
            open(p, "wb").write(data)
            s = score(p, name)
            if s[0] > best[0][0]:
                best = (s, src)
                if write:
                    shutil.copy(p, here + ".best")
        (key, n, total), src = best
        if write and src != "现有":
            os.replace(here + ".best", here)
    line = f"{name}: 用 {src},{n} 题 {total} 分" + ("" if key[0] else "(与满分不符)")
    return name, src, bool(key[0]), line


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--only", help="只处理这些文件名(逗号分隔)")
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 4)
    a = ap.parse_args()
    have = {r[0] for r in db.connect().execute(
        "SELECT DISTINCT substr(id, 1, 11) FROM questions")}
    pdfdir = os.path.join(paths.RAW, "pdf")
    names = [f for f in sorted(os.listdir(pdfdir))
             if "_qp_" in f and f[:4] in TOTAL and f.replace("_qp_", "_")[:-4] not in have]
    if a.only:
        names = [n for n in names if n in a.only.split(",")]
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        results = list(ex.map(choose, names, [a.write] * len(names)))
    changed = sum(1 for r in results if r and r[1] != "现有")
    bad = [r[0] for r in results if r and not r[2]]
    for r in results:
        if r:
            print(r[3])
    print(f"新卷 {len(names)} 份;换用其他来源 {changed} 份;仍与满分不符 {len(bad)} 份")
    if not a.write:
        print("(dry run;加 --write 替换)")


if __name__ == "__main__":
    main()
