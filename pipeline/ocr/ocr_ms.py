#!/usr/bin/env python3
"""Re-read maths mark schemes with PaddleOCR-VL.

`pdftotext -layout` keeps the Question|Answer|Marks|Guidance columns but drops
every '=', '-', superscript and fraction bar from mathematical typesetting, so
a 9709/9231 mark scheme comes out unreadable (audit: 9.2% usable for 9231).
The vision model returns the same table as HTML with proper LaTeX instead.

Whole PDFs are submitted, one job each — CAIE mark schemes run 18-26 pages, well
under the point where a single job risks timing out. Results stream to a JSONL
cache so the run is resumable.
"""
import json, os, sys, threading, time
from concurrent.futures import ThreadPoolExecutor
import requests

JOB = "https://paddleocr.aistudio-app.com/api/v2/ocr/jobs"
TOKEN = os.environ.get("PADDLE_TOKEN", "f976c86061d646ba2294e0a5a951893ac2e9d383")
HEADERS = {"Authorization": f"bearer {TOKEN}"}
MODEL = "PaddleOCR-VL-1.6"
# mark scheme pages are landscape; let the model straighten them
OPT = {"useDocOrientationClassify": True, "useDocUnwarping": False,
       "useChartRecognition": False}
MAX_PAGES = 100          # a single job beyond this risks timing out

lock = threading.Lock()


def submit(path, tries=40):
    for a in range(tries):
        try:
            with open(path, "rb") as f:
                r = requests.post(JOB, headers=HEADERS,
                                  data={"model": MODEL,
                                        "optionalPayload": json.dumps(OPT)},
                                  files={"file": f}, timeout=300)
            if r.status_code == 200:
                return r.json()["data"]["jobId"]
            # 10010 = server-side submission queue full; back off and retry
            time.sleep(min(12 * (a + 1), 120))
        except Exception:
            time.sleep(min(8 * (a + 1), 90))
    return None


def collect(jid, budget=2400):
    t0 = time.time()
    while time.time() - t0 < budget:
        try:
            d = requests.get(f"{JOB}/{jid}", headers=HEADERS, timeout=90).json()["data"]
        except Exception:
            time.sleep(8)
            continue
        st = d.get("state")
        if st == "done":
            pages = []
            for ln in requests.get(d["resultUrl"]["jsonUrl"],
                                   timeout=180).text.strip().split("\n"):
                for res in json.loads(ln)["result"]["layoutParsingResults"]:
                    pages.append(res["markdown"]["text"])
            return pages
        if st == "failed":
            raise RuntimeError(str(d.get("errorMsg"))[:150])
        time.sleep(8)
    raise TimeoutError("job budget exceeded")


def run(args):
    path, name = args
    try:
        import fitz
        n = fitz.open(path).page_count
        if n > MAX_PAGES:
            return {"file": name, "error": f"too many pages: {n}"}
    except Exception:
        pass
    jid = submit(path)
    if not jid:
        return {"file": name, "error": "submit failed after retries"}
    try:
        pages = collect(jid)
    except Exception as e:
        return {"file": name, "error": f"{type(e).__name__}: {e}"}
    return {"file": name, "pages": pages}


def main(pdfdirs, cache, workers):
    done = set()
    if os.path.exists(cache):
        for ln in open(cache):
            try:
                d = json.loads(ln)
                if d.get("pages"):
                    done.add(d["file"])
            except Exception:
                pass

    todo = []
    for d in pdfdirs:
        for f in sorted(os.listdir(d)):
            if "_ms_" in f and f not in done:
                todo.append((os.path.join(d, f), f))
    print(f"{len(done)} cached, {len(todo)} to do, {workers} workers", flush=True)

    fh = open(cache, "a")
    t0, n = time.time(), [0]

    def work(item):
        res = run(item)
        with lock:
            fh.write(json.dumps(res, ensure_ascii=False) + "\n")
            fh.flush()
            n[0] += 1
            if n[0] % 10 == 0:
                el = (time.time() - t0) / 60
                print(f"  {n[0]}/{len(todo)}  {el:.0f} min elapsed, "
                      f"eta {el/n[0]*(len(todo)-n[0]):.0f} min", flush=True)
        return res

    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(work, todo))
    fh.close()
    errs = sum(1 for ln in open(cache) if '"error"' in ln)
    print(f"finished in {(time.time()-t0)/60:.1f} min, error lines={errs}")


if __name__ == "__main__":
    dirs = sys.argv[1].split(",")
    main(dirs, sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 6)
