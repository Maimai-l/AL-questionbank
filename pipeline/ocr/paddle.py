#!/usr/bin/env python3
"""PaddleOCR-VL client for textbooks.

`ocr_ms.py` already talks to this API, but it throws away everything except the
markdown text. That is right for mark schemes and wrong for textbooks: a
mechanics chapter without its force diagrams, or a graphs chapter without its
graphs, is not a chapter. So this keeps the images, and returns one record per
page rather than one string.

Orientation classification is off here. Mark scheme pages are landscape and
need straightening; textbook pages are upright, and asking the model to decide
costs time and occasionally rotates a page that was already fine.
"""
import json, os, time

try:
    import requests
except ImportError:                                   # imported by --dry paths
    requests = None

JOB = "https://paddleocr.aistudio-app.com/api/v2/ocr/jobs"
TOKEN = os.environ.get("PADDLE_TOKEN", "f976c86061d646ba2294e0a5a951893ac2e9d383")
HEAD = {"Authorization": f"bearer {TOKEN}"}
MODEL = "PaddleOCR-VL-1.6"
OPT = {"useDocOrientationClassify": False, "useDocUnwarping": False,
       "useChartRecognition": False}
MAX_PAGES = 100          # a single job beyond this risks timing out


def submit(path, tries=40):
    for a in range(tries):
        try:
            with open(path, "rb") as f:
                r = requests.post(JOB, headers=HEAD,
                                  data={"model": MODEL,
                                        "optionalPayload": json.dumps(OPT)},
                                  files={"file": f}, timeout=300)
            if r.status_code == 200:
                return r.json()["data"]["jobId"]
            # 10010 = submission queue full server-side; back off and retry
            time.sleep(min(12 * (a + 1), 120))
        except Exception:
            time.sleep(min(8 * (a + 1), 90))
    return None


def collect(jid, budget=5400, poll=8):
    """[{text, images:{relpath: url}, extra:{name: url}}] — one entry per page.

    The budget is generous because a 100-page job legitimately takes far longer
    than the 20-page mark schemes this API was first used for; a job killed by
    an impatient client has still consumed the quota.
    """
    t0 = time.time()
    while time.time() - t0 < budget:
        try:
            d = requests.get(f"{JOB}/{jid}", headers=HEAD, timeout=90).json()["data"]
        except Exception:
            time.sleep(poll)
            continue
        st = d.get("state")
        if st == "done":
            pages = []
            body = requests.get(d["resultUrl"]["jsonUrl"], timeout=300).text
            for ln in body.strip().split("\n"):
                if not ln.strip():
                    continue
                # one line can carry several pages — the bug that cost 75% of
                # the first Pure 2&3 run was collapsing them onto one filename
                for res in json.loads(ln)["result"]["layoutParsingResults"]:
                    md = res.get("markdown", {}) or {}
                    pages.append({"text": md.get("text", "") or "",
                                  "images": md.get("images") or {},
                                  "extra": res.get("outputImages") or {}})
            return pages
        if st == "failed":
            raise RuntimeError(str(d.get("errorMsg"))[:200])
        time.sleep(poll)
    raise TimeoutError(f"job {jid} exceeded {budget}s")


def fetch_images(page, out_dir, page_no):
    """Save a page's figures next to its markdown. Returns how many landed."""
    n = 0
    for rel, url in (page.get("images") or {}).items():
        dst = os.path.join(out_dir, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        try:
            open(dst, "wb").write(requests.get(url, timeout=60).content)
            n += 1
        except Exception:
            pass
    for name, url in (page.get("extra") or {}).items():
        d = os.path.join(out_dir, "imgs")
        os.makedirs(d, exist_ok=True)
        try:
            open(os.path.join(d, f"{name}_{page_no:04d}.jpg"), "wb").write(
                requests.get(url, timeout=60).content)
            n += 1
        except Exception:
            pass
    return n
