"""Hand corrections to single OCR pages of the admissions bank.

The OCR cannot read what a page only draws: option letters under a figure, a
question number set in the margin, a sentence it drops. Those pages were once
corrected in raw/bank_ocr itself, which is a local cache, and the corrections
went with it. They now live in page_fixes.json beside this file, keyed by the
page's path under raw/bank_ocr ("TARA/TSA_section1/papers/TSA-2010-S1/
page_0009.md"), and every script that reads a page reads it through here.
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
from lib import paths  # noqa: E402

FILE = os.path.join(paths.ADM, "page_fixes.json")
_fixes = None


def fixes():
    global _fixes
    if _fixes is None:
        _fixes = {}
        if os.path.exists(FILE):
            _fixes = {k: v["text"] for k, v in json.load(open(FILE, encoding="utf-8")).items()
                      if not k.startswith("_")}
    return _fixes


def read_page(path):
    """The page's text: the correction if there is one, else the OCR."""
    key = os.path.relpath(path, paths.BANK_OCR).replace(os.sep, "/")
    if key in fixes():
        return fixes()[key]
    return open(path, encoding="utf-8").read()
