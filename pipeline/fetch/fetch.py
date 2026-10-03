#!/usr/bin/env python3
"""Download CAIE 9709 question papers + mark schemes."""
import os, sys
from concurrent.futures import ThreadPoolExecutor
import urllib.request

BASE = "https://dynamicpapers.com/wp-content/uploads/2015/09/"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))          # qb/
from lib import paths

OUT = os.path.join(paths.ROOT, "pdf")
UA = {"User-Agent": "Mozilla/5.0"}

YEARS = [21, 22, 23, 24, 25]
# component -> variant digits.  March (m) series in India uses variant 2 only.
COMPONENTS = {"1": ["1", "2", "3"], "3": ["1", "2", "3"],
              "4": ["1", "2", "3"], "5": ["1", "2", "3"]}


def targets():
    out = []
    for y in YEARS:
        for s in ("m", "s", "w"):
            for comp, variants in COMPONENTS.items():
                vs = ["2"] if s == "m" else variants
                for v in vs:
                    for kind in ("qp", "ms"):
                        out.append(f"9709_{s}{y}_{kind}_{comp}{v}.pdf")
    return out


def grab(name):
    dest = os.path.join(OUT, name)
    if os.path.exists(dest) and os.path.getsize(dest) > 20000:
        return ("cached", name)
    req = urllib.request.Request(BASE + name, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        if not data.startswith(b"%PDF"):
            return ("notpdf", name)
        with open(dest, "wb") as f:
            f.write(data)
        return ("ok", name)
    except Exception as e:
        return (f"err:{type(e).__name__}", name)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    names = targets()
    print(f"{len(names)} files to fetch", flush=True)
    res = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        for i, (status, name) in enumerate(ex.map(grab, names), 1):
            res.setdefault(status.split(":")[0], []).append(name)
            if i % 40 == 0:
                print(f"  {i}/{len(names)}", flush=True)
    for k, v in sorted(res.items()):
        print(f"{k}: {len(v)}")
        if k not in ("ok", "cached"):
            print("   " + " ".join(v[:12]))
