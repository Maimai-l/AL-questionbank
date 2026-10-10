#!/usr/bin/env python3
"""Download CAIE question papers, mark schemes and grade thresholds, one file per name.

    python3 get_paper.py 9231_w21_ms_13 9231_w21_qp_13 9231_w21_gt --out papers
    python3 get_paper.py 9231 --years 21 22 --series w --papers 1 --variants 3 --out papers
        (the second form expands to the qp and ms of every paper, add --gt for the thresholds)

Where each file comes from, in order:
  1. github   the question bank's own copies (Maimai-l/AL-questionbank, branch data, papers/):
              the best of the three sites, checked and with watermarks removed.
              No grade thresholds there.
  2. fraft        cie.fraft.cn
  3. papacambridge pastpapers.papacambridge.com  (watermarked; the watermark is removed)
  4. dynamicpapers dynamicpapers.com

A copy is kept only if it is a PDF and, when PyMuPDF is installed, its text layer
has words in it and its pages are A4: fraft serves some 2025-26 papers with fonts
that have no Unicode map, and retypesets a few on Letter paper. Without PyMuPDF the
check is skipped and the watermark is left in (pip install pymupdf).

Each line of output: the file name, the site it came from (or "cached", "missing").
A site that cannot be reached is reported once; if every site fails, the sandbox's
network settings need the domains listed in DOMAINS below.
"""
import argparse, os, re, sys, time, urllib.error, urllib.parse, urllib.request

SITES = [
    ("github", "https://raw.githubusercontent.com/Maimai-l/AL-questionbank/data/papers/{name}"),
    ("fraft", "https://cie.fraft.cn/obj/Common/Fetch/redir/{name}"),
    ("papacambridge", "https://pastpapers.papacambridge.com/directories/CAIE/CAIE-pastpapers/upload/{name}"),
    ("dynamicpapers", "https://dynamicpapers.com/wp-content/uploads/2015/09/{name}"),
]
DOMAINS = ["raw.githubusercontent.com", "cie.fraft.cn", "pastpapers.papacambridge.com", "dynamicpapers.com"]
UA = {"User-Agent": "Mozilla/5.0"}
unreachable = set()


def request(site, url, tries=3):
    """The body, None when the file is not there, or "down" when the site cannot be reached."""
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA, data=b"" if site == "fraft" else None)
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (403, 404, 410):
                return None
            if e.code == 500:          # dynamicpapers answers a missing file with a WordPress 500 page
                return None
            time.sleep(2 * (k + 1))
        except Exception:
            time.sleep(2 * (k + 1))
    return "down"


def readable(data):
    try:
        import pymupdf
    except ImportError:
        return True
    try:
        doc = pymupdf.open(stream=data, filetype="pdf")
        text = "".join(p.get_text() for p in doc)
        w, h = doc[0].rect.width, doc[0].rect.height
    except Exception:
        return False
    a4 = abs(w - 595.3) < 3 or abs(h - 595.3) < 3
    return a4 and len(re.findall(r"[A-Za-z]{4,}", text)) > 50


def get(name, out):
    dest = os.path.join(out, name)
    if os.path.exists(dest) and os.path.getsize(dest) > 20000:
        return "cached"
    for site, tpl in SITES:
        if site in unreachable or (site == "github" and "_gt" in name):
            continue
        data = request(site, tpl.format(name=urllib.parse.quote(name)))
        if data == "down":
            unreachable.add(site)
            print(f"  连不上 {site},之后跳过", file=sys.stderr)
            continue
        if not data or not data.startswith(b"%PDF") or ("_gt" not in name and not readable(data)):
            continue
        with open(dest, "wb") as f:
            f.write(data)
        if site == "papacambridge":
            try:
                from strip_watermark import strip
                return f"{site}(去水印:{strip(dest)})"
            except ImportError:
                return f"{site}(带水印:没有 PyMuPDF 或 strip_watermark.py)"
        return site
    return "missing"


def names(a):
    if not a.items or not re.fullmatch(r"\d{4}", a.items[0]):
        return [n if n.endswith(".pdf") else n + ".pdf" for n in a.items]
    out = []
    for y in a.years:
        for s in a.series:
            for p in a.papers:
                for v in (a.variants if s != "m" else ["2"]):
                    for kind in ("qp", "ms"):
                        out.append(f"{a.items[0]}_{s}{y}_{kind}_{p}{v}.pdf")
            if a.gt:
                out.append(f"{a.items[0]}_{s}{y}_gt.pdf")
    return list(dict.fromkeys(out))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("items", nargs="+", help="file names (9231_w21_ms_13), or a syllabus code with --years ...")
    ap.add_argument("--out", default="papers")
    ap.add_argument("--years", nargs="+", default=[])
    ap.add_argument("--series", nargs="+", default=["m", "s", "w"], help="m = Feb/Mar, s = May/Jun, w = Oct/Nov")
    ap.add_argument("--papers", nargs="+", default=[])
    ap.add_argument("--variants", nargs="+", default=["1", "2", "3"])
    ap.add_argument("--gt", action="store_true", help="also the grade thresholds of each series")
    a = ap.parse_args()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    os.makedirs(a.out, exist_ok=True)
    got = 0
    for n in names(a):
        res = get(n, a.out)
        got += res != "missing"
        print(f"{n:28} {res}")
    print(f"{got} 个文件在 {a.out}/")
    if len(unreachable) == len(SITES):
        print("所有站点都连不上:网络设置里要允许 " + "、".join(DOMAINS), file=sys.stderr)


if __name__ == "__main__":
    main()
