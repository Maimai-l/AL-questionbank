#!/usr/bin/env python3
"""Upgrade question text to LaTeX with PaddleOCR-VL.

pdftotext flattens superscripts and fractions; the PNG crop is loss-free but
only a vision model can read it. This runs each crop through PaddleOCR-VL and
stores proper LaTeX, making the text field usable for search and for reasoning
without vision.

Results stream to a JSONL cache, so the run is resumable and a crash costs
nothing.

    python3 pipeline/ocr/ocr.py <questions.json> <imgdir> <cache.jsonl> [workers] [--pack N]

--pack N puts N crops into one PDF (one crop per page) and submits that as one
job, splitting the result back by page. The service queues jobs, so 2 482 single
crops for 9702 went at about 3 a minute while one job takes 25 seconds; packed,
the job count drops N-fold.

--figures DIR keeps the figures. Without it (the CAIE runs) every figure the
layout model cuts out becomes "[DIAGRAM]". With it, each figure the markdown
places (markdown.images in the response, as pipeline/ocr/ocr_books.py saves
them for the textbooks) is downloaded to DIR/<question id>_<n>.jpg, n counting
the figures in reading order, and its <img src> is rewritten to that file's path
relative to data/ (imgWPH/fig/WPH_hb1_ch03_q11_01.jpg), as the textbook markdown
links its figures; has_diagram is then whether any figure was kept, and the cache
line lists them under "figures". DIR must be under data/.
"""
import json, os, re, sys, threading, time
from concurrent.futures import ThreadPoolExecutor
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from lib import paths  # noqa: E402

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


def clean(md, figures=False):
    md = TRAIL_RE.sub("", md)
    md = re.sub(r'<div style="text-align: center;">\s*(\[\d+\])\s*</div>', r" \1", md)
    if not figures:
        md = re.sub(r'<div style="text-align: center;">\s*<img[^>]*>\s*</div>',
                    "\n[DIAGRAM]\n", md)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()


def run_job(path, full=False):
    """Markdown of each page of one submitted file; with full, {text, images} per page
    (images: the markdown's figure paths -> their download URLs)."""
    with open(path, "rb") as f:
        r = requests.post(JOB, headers=HEADERS,
                          data={"model": MODEL, "optionalPayload": json.dumps(OPT)},
                          files={"file": f}, timeout=300)
    if r.status_code != 200:
        raise RuntimeError(f"submit {r.status_code} {r.text[:120]}")
    jid = r.json()["data"]["jobId"]
    for _ in range(400):
        d = requests.get(f"{JOB}/{jid}", headers=HEADERS, timeout=90).json()["data"]
        if d["state"] == "done":
            pages = []
            for ln in requests.get(d["resultUrl"]["jsonUrl"], timeout=120).text.strip().split("\n"):
                for res in json.loads(ln)["result"]["layoutParsingResults"]:
                    md = res["markdown"]
                    pages.append({"text": md["text"], "images": md.get("images") or {}} if full
                                 else md["text"])
            return pages
        if d["state"] == "failed":
            raise RuntimeError("job failed: " + str(d.get("errorMsg"))[:120])
        time.sleep(3)
    raise TimeoutError("poll timeout")


FIG_SRC = re.compile(r'(<img\s[^>]*?src=")([^"]+)(")', re.I)


def save_figures(text, images, qid, figdir):
    """Download the figures the markdown places, in order, to figdir/<qid>_<n>.jpg and
    point their <img src> there (relative to data/). Returns (text, [paths])."""
    saved = []

    def one(m):
        url = images.get(m.group(2))
        if not url:
            return m.group(0)
        dst = os.path.join(figdir, f"{qid}_{len(saved) + 1:02d}.jpg")
        for a in range(3):
            try:
                r = requests.get(url, timeout=120)
                r.raise_for_status()
                os.makedirs(figdir, exist_ok=True)
                with open(dst, "wb") as f:
                    f.write(r.content)
                break
            except Exception:
                if a == 2:
                    raise
                time.sleep(2 * (a + 1))
        rel = paths.relative_to_data(dst).replace(os.sep, "/")
        saved.append(rel)
        return m.group(1) + rel + m.group(3)
    return FIG_SRC.sub(one, text), saved


def result(page, qid=None, figdir=None):
    """The cache line for one crop's page: a str (no figures) or {text, images}."""
    if figdir is None:
        t = page if isinstance(page, str) else page["text"]
        return {"latex": clean(t), "has_diagram": bool(IMG_RE.search(t))}
    text, figs = save_figures(page["text"], page["images"], qid, figdir)
    return {"latex": clean(text, figures=True), "has_diagram": bool(figs), "figures": figs}


def ocr_pack(paths, tries=3, qids=None, figdir=None):
    """One job for several crops: a PDF with one crop per page. A result per crop."""
    import tempfile
    from PIL import Image
    for attempt in range(tries):
        try:
            with tempfile.TemporaryDirectory() as tmp:
                pdf = os.path.join(tmp, "pack.pdf")
                ims = [Image.open(p).convert("RGB") for p in paths]
                ims[0].save(pdf, "PDF", save_all=True, append_images=ims[1:], resolution=200)
                pages = run_job(pdf, full=figdir is not None)
            if len(pages) != len(paths):
                raise RuntimeError(f"{len(pages)} pages back for {len(paths)} crops")
            return [result(t, qid, figdir) for t, qid in zip(pages, qids or [None] * len(pages))]
        except Exception as e:
            if attempt == tries - 1:
                return [{"error": f"{type(e).__name__}: {e}"} for _ in paths]
            time.sleep(5 * (attempt + 1))


def ocr_one(path, tries=3, qid=None, figdir=None):
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
                    parts, images = [], {}
                    for ln in requests.get(d["resultUrl"]["jsonUrl"], timeout=90) \
                                       .text.strip().split("\n"):
                        for res in json.loads(ln)["result"]["layoutParsingResults"]:
                            parts.append(res["markdown"]["text"])
                            images.update(res["markdown"].get("images") or {})
                    raw = "\n".join(parts)
                    return result(raw if figdir is None else {"text": raw, "images": images},
                                  qid, figdir)
                if st == "failed":
                    raise RuntimeError("job failed: " + str(d.get("errorMsg"))[:120])
                time.sleep(3)
            raise TimeoutError("poll timeout")
        except Exception as e:
            if attempt == tries - 1:
                return {"error": f"{type(e).__name__}: {e}"}
            time.sleep(4 * (attempt + 1))


def main(qjson, imgdir, cache, workers, pack=1, figdir=None):
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

    def record(qid, res):
        res["id"] = qid
        with lock:
            fh.write(json.dumps(res, ensure_ascii=False) + "\n"); fh.flush()
            n[0] += 1
            if n[0] % 25 == 0:
                el = time.time() - t0
                rate = n[0] / el
                print(f"  {n[0]}/{len(todo)}  {rate*60:.0f}/min  "
                      f"eta {(len(todo)-n[0])/rate/60:.0f} min", flush=True)

    def work(q):
        record(q["image"][:-4], ocr_one(os.path.join(imgdir, q["image"]),
                                        qid=q["image"][:-4], figdir=figdir))

    def work_pack(group):
        for q, res in zip(group, ocr_pack([os.path.join(imgdir, q["image"]) for q in group],
                                          qids=[q["image"][:-4] for q in group], figdir=figdir)):
            record(q["image"][:-4], res)

    with ThreadPoolExecutor(max_workers=workers) as ex:
        if pack > 1:
            list(ex.map(work_pack, [todo[i:i + pack] for i in range(0, len(todo), pack)]))
        else:
            list(ex.map(work, todo))
    fh.close()
    errs = sum(1 for ln in open(cache) if '"error"' in ln)
    print(f"finished in {(time.time()-t0)/60:.1f} min, errors={errs}")


if __name__ == "__main__":
    args = sys.argv[1:]
    pack, figdir = 1, None
    if "--pack" in args:
        i = args.index("--pack")
        pack = int(args[i + 1])
        del args[i:i + 2]
    if "--figures" in args:
        i = args.index("--figures")
        figdir = os.path.abspath(args[i + 1])
        del args[i:i + 2]
        if not figdir.startswith(os.path.abspath(paths.DATA) + os.sep):
            sys.exit("--figures 的目录须在 data/ 下(题干里的路径相对 data/)")
    main(args[0], args[1], args[2], int(args[3]) if len(args) > 3 else 6, pack, figdir)
