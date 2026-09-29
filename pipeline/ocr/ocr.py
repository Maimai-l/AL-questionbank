#!/usr/bin/env python3
"""Upgrade question text to LaTeX with PaddleOCR-VL.

pdftotext flattens superscripts and fractions; the PNG crop is loss-free but
only a vision model can read it. This runs each crop through PaddleOCR-VL and
stores proper LaTeX, making the text field usable for search and for reasoning
without vision.

Results stream to a JSONL cache, so the run is resumable and a crash costs
nothing.
"""
import json, os, re, sys, threading, time
from concurrent.futures import ThreadPoolExecutor
import requests

JOB = "https://paddleocr.aistudio-app.com/api/v2/ocr/jobs"
TOKEN = os.environ.get("PADDLE_TOKEN", "f976c86061d646ba2294e0a5a951893ac2e9d383")
MODEL = "PaddleOCR-VL-1.6"
HEADERS = {"Authorization": f"bearer {TOKEN}"}
OPT = {"useDocOrientationClassify": False, "useDocUnwarping": False,
       "useChartRecognition": False}

# a crop that runs to the foot of the last page picks up the answer booklet
TRAIL_RE = re.compile(
    r"(?:^|\n)\s*(?:\d{1,2}\s*\n)?\s*(?:BLANK PAGE|Additional Page|"
    r"If you use the following lined page).*", re.S | re.I)
IMG_RE = re.compile(r"<img\s", re.I)

lock = threading.Lock()


def clean(md):
    md = TRAIL_RE.sub("", md)
    md = re.sub(r'<div style="text-align: center;">\s*(\[\d+\])\s*</div>', r" \1", md)
    md = re.sub(r'<div style="text-align: center;">\s*<img[^>]*>\s*</div>',
                "\n[DIAGRAM]\n", md)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()


def ocr_one(path, tries=3):
    for attempt in range(tries):
        try:
            with open(path, "rb") as f:
                r = requests.post(JOB, headers=HEADERS,
                                  data={"model": MODEL, "optionalPayload": json.dumps(OPT)},
                                  files={"file": f}, timeout=180)
            if r.status_code != 200:
                raise RuntimeError(f"submit {r.status_code} {r.text[:120]}")
            jid = r.json()["data"]["jobId"]
            for _ in range(90):
                d = requests.get(f"{JOB}/{jid}", headers=HEADERS, timeout=90).json()["data"]
                st = d["state"]
                if st == "done":
                    parts = []
                    for ln in requests.get(d["resultUrl"]["jsonUrl"], timeout=90) \
                                       .text.strip().split("\n"):
                        for res in json.loads(ln)["result"]["layoutParsingResults"]:
                            parts.append(res["markdown"]["text"])
                    raw = "\n".join(parts)
                    return {"latex": clean(raw), "has_diagram": bool(IMG_RE.search(raw))}
                if st == "failed":
                    raise RuntimeError("job failed: " + str(d.get("errorMsg"))[:120])
                time.sleep(3)
            raise TimeoutError("poll timeout")
        except Exception as e:
            if attempt == tries - 1:
                return {"error": f"{type(e).__name__}: {e}"}
            time.sleep(4 * (attempt + 1))


def main(qjson, imgdir, cache, workers):
    Q = json.load(open(qjson))
    done = {}
    if os.path.exists(cache):
        for ln in open(cache):
            try:
                d = json.loads(ln)
                if "latex" in d:
                    done[d["id"]] = d
            except Exception:
                pass
    todo = [q for q in Q if q.get("image") and q["image"][:-4] not in done]
    print(f"{len(done)} cached, {len(todo)} to do, {workers} workers", flush=True)

    fh = open(cache, "a")
    t0, n = time.time(), [0]

    def work(q):
        qid = q["image"][:-4]
        res = ocr_one(os.path.join(imgdir, q["image"]))
        res["id"] = qid
        with lock:
            fh.write(json.dumps(res, ensure_ascii=False) + "\n"); fh.flush()
            n[0] += 1
            if n[0] % 25 == 0:
                el = time.time() - t0
                rate = n[0] / el
                print(f"  {n[0]}/{len(todo)}  {rate*60:.0f}/min  "
                      f"eta {(len(todo)-n[0])/rate/60:.0f} min", flush=True)
        return res

    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(work, todo))
    fh.close()
    errs = sum(1 for ln in open(cache) if '"error"' in ln)
    print(f"finished in {(time.time()-t0)/60:.1f} min, errors={errs}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3],
         int(sys.argv[4]) if len(sys.argv) > 4 else 6)
