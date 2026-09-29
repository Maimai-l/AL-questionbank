#!/usr/bin/env python3
"""Download CAIE past papers for any subject code.

  fetch_any.py 9618 pdf9618 --years 21 22 23 24 25 --papers 1 2 3 4 \
               --variants 1 2 3 --series s w [--workers 6]

The mirror rate-limits bursts with 503, so requests back off and retry rather
than recording a false miss.
"""
import argparse, os, random, threading, time
import urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor

BASE = "https://dynamicpapers.com/wp-content/uploads/2015/09/{name}"
UA = {"User-Agent": "Mozilla/5.0"}
lock = threading.Lock()


def grab(args):
    name, url, outdir, tries = args
    dest = os.path.join(outdir, name)
    if os.path.exists(dest) and os.path.getsize(dest) > 20000:
        return ("cached", name)
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=90) as r:
                data = r.read()
            if not data.startswith(b"%PDF"):
                return ("notpdf", name)
            with open(dest, "wb") as f:
                f.write(data)
            return ("ok", name)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return ("404", name)
            # dynamicpapers 对"文件不存在"返回的是 500 加一张 WordPress 错误页,
            # 而不是干净的 404。若不区分,每个尚未上线的卷子都会被当成服务端
            # 抖动重试四次,既拖慢整轮抓取,又在报告里显示为失败而非缺卷。
            if e.code == 500:
                try:
                    body = e.read(4096)
                except Exception:
                    body = b""
                if b"WordPress" in body or b"<!DOCTYPE html" in body:
                    return ("missing", name)
            if e.code in (503, 429, 502, 500) and attempt < tries - 1:
                time.sleep((2 ** attempt) * 3 + random.random() * 2)
                continue
            return (f"http{e.code}", name)
        except Exception as e:
            if attempt < tries - 1:
                time.sleep((2 ** attempt) * 2)
                continue
            return (f"err:{type(e).__name__}", name)
    return ("giveup", name)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("subject")
    p.add_argument("outdir")
    p.add_argument("--years", nargs="+", required=True)
    p.add_argument("--papers", nargs="+", required=True)
    p.add_argument("--variants", nargs="+", default=["1", "2", "3"])
    p.add_argument("--series", nargs="+", default=["m", "s", "w"])
    p.add_argument("--march-variant", default="2",
                   help="March series usually has only one variant")
    p.add_argument("--workers", type=int, default=6)
    p.add_argument("--url-template", default=BASE,
                   help="placeholders: {name} {subject} {year4} {year2} {series} {kind} {comp}")
    p.add_argument("--tries", type=int, default=4)
    a = p.parse_args()

    os.makedirs(a.outdir, exist_ok=True)
    names = []
    for y in a.years:
        for s in a.series:
            for comp in a.papers:
                vs = [a.march_variant] if s == "m" else a.variants
                for v in vs:
                    for kind in ("qp", "ms"):
                        nm = f"{a.subject}_{s}{y}_{kind}_{comp}{v}.pdf"
                        names.append((nm, a.url_template.format(
                            name=nm, subject=a.subject, year4=f"20{y}", year2=y,
                            series=s, kind=kind, comp=f"{comp}{v}")))

    print(f"{len(names)} candidate files, {a.workers} workers", flush=True)
    res, n = {}, [0]
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for status, name in ex.map(grab, [(nm, u, a.outdir, a.tries) for nm, u in names]):
            res.setdefault(status.split(":")[0], []).append(name)
            n[0] += 1
            if n[0] % 60 == 0:
                print(f"  {n[0]}/{len(names)}", flush=True)
    for k, v in sorted(res.items()):
        print(f"{k}: {len(v)}")
        if k not in ("ok", "cached", "404", "missing"):
            print("   " + " ".join(v[:8]))


if __name__ == "__main__":
    main()
