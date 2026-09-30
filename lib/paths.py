"""One place that knows where everything lives.

Code lives on the `main` branch; everything the pipeline produces (database,
crops, textbook chapters, the page data) lives under `data/`, which is a git
worktree of the `data` branch. See docs/data-sync.md.

Environment overrides, for running against a copy without moving anything:

    CAIE_ROOT       project root (the folder holding qb.py)
    CAIE_DATA       data folder (default: <root>/data)
    CAIE_DB         database file (default: <data>/caie.db)
    CAIE_IMG_ROOT   folder holding img9709/ img9231/ img9618/ img_adm/ img_tara/
    QB_WORK         what practising produces: handwriting boards, attempts
                    (default: qb-work/ next to the project folder)
"""
import os

# lib/ sits directly under the project root
ROOT = os.environ.get("CAIE_ROOT") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))

DATA = os.environ.get("CAIE_DATA") or os.path.join(ROOT, "data")
DB = os.environ.get("CAIE_DB") or os.path.join(DATA, "caie.db")
BOOKS = os.path.join(DATA, "books")
ASSETS = os.path.join(ROOT, "assets")        # page sources: html + vendor/
EXPORTS = os.path.join(ROOT, "exports")      # distribution ZIPs, not tracked
RAW = os.environ.get("CAIE_RAW") or os.path.join(ROOT, "raw")  # pipeline inputs: PDFs, OCR
SYLLABUS = os.path.join(ROOT, "syllabus.json")

# Admissions pipeline (pipeline/admissions_rebuild/). Its tracked intermediates
# (questions_adm.json, answers.json, ms_tmua.json, retag_*.json) sit next to the
# scripts; the downloaded papers and their page OCR are inputs under raw/.
ADM = os.path.join(ROOT, "pipeline", "admissions_rebuild")
BANK = os.path.join(RAW, "bank")            # manifest.py: papers, keys, specs
BANK_OCR = os.path.join(RAW, "bank_ocr")    # ocr_bank.py: one markdown per page
IMG_ADM = os.path.join(DATA, "img_adm")     # render_adm_imgs.py: one PNG per question
PREREQ = os.path.join(ROOT, "prereq.json")

# The practice server's own records (app/): handwriting boards and attempts.
# Not under data/, which `sync.py pull` resets and cleans; not in the repo.
WORK = os.environ.get("QB_WORK") or os.path.join(os.path.dirname(ROOT), "qb-work")
INK = os.path.join(WORK, "ink")                 # inksync storage
ATTEMPTS = os.path.join(WORK, "attempts.db")    # app/store.py

# Where the question crops may be. data/ is the normal place; the others keep
# a copy unpacked in an older layout working.
_ROOTS = [
    os.environ.get("CAIE_IMG_ROOT"),   # explicit override wins
    DATA,                              # data/img9709/...
    ASSETS,                            # older layout: assets/img9709/...
    ROOT,
]

# The 9709 crops used to live in a folder called `img/`; it is now `img9709/`
# to match the other two. Accept either.
_ALIASES = [("img9709/", "img/"), ("img/", "img9709/")]


def _candidates(rel):
    yield rel
    for new, old in _ALIASES:
        if rel.startswith(new):
            yield old + rel[len(new):]


def resolve(rel):
    """Return an absolute path to the crop, or None if it cannot be found."""
    if not rel:
        return None
    if os.path.isabs(rel):
        return rel if os.path.exists(rel) else None
    for cand in _candidates(rel):
        for root in _ROOTS:
            if not root:
                continue
            p = os.path.join(root, cand)
            if os.path.exists(p):
                return p
    return None


def under_data(path):
    """Absolute path for something recorded relative to data/ (chapter files)."""
    return path if os.path.isabs(path) else os.path.join(DATA, path)


def relative_to_data(path):
    """Inverse of `under_data`, for values about to be stored in the database."""
    ap = os.path.abspath(path)
    base = os.path.abspath(DATA)
    return os.path.relpath(ap, base) if ap.startswith(base + os.sep) else ap


def image_root_report():
    """Which layout is in use — for `qb.py stats` and troubleshooting."""
    for root in _ROOTS:
        if not root:
            continue
        for folder in ("img9709", "img"):
            if os.path.isdir(os.path.join(root, folder)):
                return f"{root}  (9709 crops in {folder}/)"
    return None
