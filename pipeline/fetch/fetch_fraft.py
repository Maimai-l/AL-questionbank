#!/usr/bin/env python3
"""Download the papers cie.fraft.cn lists that the bank does not have yet.

    python3 pipeline/fetch/fetch_fraft.py 9709 9231 9618 --years 2021-2026 [--dry-run]

The site (Frank 的 CIE 工坊) lists every file of a subject, year and season:
POST obj/Common/Fetch/renum with subject, year, season (Mar/Jun/Nov). Each
question paper absent from the bank is fetched with its mark scheme through
obj/Common/Fetch/redir/<file>, the PDF itself (no redirect; 404 when missing).
Question papers go to raw/pdf/, mark schemes to raw/ms/, where split_qp.py
and split_ms.py / rebuild_ms.py read them. The site resets connections now and
then, so every request is retried with a growing pause.
"""
import argparse, json, os, sys, time
import urllib.parse, urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
from lib import db, paths  # noqa: E402

SITE = "https://cie.fraft.cn/obj/Common/Fetch/"
UA = {"User-Agent": "Mozilla/5.0"}


def request(url, data=None, tries=6):
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA,
                                         data=urllib.parse.urlencode(data).encode() if data else None)
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(3 * (k + 1))
        except Exception:
            time.sleep(3 * (k + 1))
    raise RuntimeError(f"多次失败:{url} {data or ''}")


def listing(subject, year, season):
    body = request(SITE + "renum", {"subject": subject, "year": year, "season": season})
    return [r["file"] for r in json.loads(body).get("rows", [])]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("subjects", nargs="+")
    ap.add_argument("--years", default="2021-2026")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    y0, y1 = (int(x) for x in a.years.split("-"))

    have = {r[0] for r in db.connect().execute(
        "SELECT DISTINCT substr(id, 1, 11) FROM questions")}
    qpdir, msdir = os.path.join(paths.RAW, "pdf"), os.path.join(paths.RAW, "ms")
    os.makedirs(qpdir, exist_ok=True); os.makedirs(msdir, exist_ok=True)

    todo = []
    for s in a.subjects:
        for y in range(y0, y1 + 1):
            for season in ("Mar", "Jun", "Nov"):
                files = set(listing(s, y, season))
                for f in sorted(files):
                    if "_qp_" in f and f.replace("_qp_", "_")[:-4] not in have:
                        todo.append(f)
                        ms = f.replace("_qp_", "_ms_")
                        if ms in files:
                            todo.append(ms)
    print(f"待下载 {len(todo)} 个文件(题目卷 {sum('_qp_' in f for f in todo)})")
    if a.dry_run:
        print(" ".join(todo))
        return
    got = missing = 0
    for f in todo:
        dest = os.path.join(qpdir if "_qp_" in f else msdir, f)
        if os.path.exists(dest) and os.path.getsize(dest) > 20000:
            got += 1
            continue
        data = request(SITE + "redir/" + f)
        if not data or not data.startswith(b"%PDF"):
            missing += 1
            print("  缺:", f)
            continue
        open(dest, "wb").write(data)
        got += 1
    print(f"已有或下载成功 {got},缺 {missing}")


if __name__ == "__main__":
    main()
