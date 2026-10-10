#!/usr/bin/env python3
"""Rebuild the offline site inside data/ after the database changes.

    python3 pipeline/export/build_site.py

Writes data/data.js, data/adm_practice.js and data/textbooks.js, then copies the page sources from
assets/ (practice.html, textbook.html, vendor/) next to them, so that data/
opens on its own: data/practice.html finds data.js and img9709/ beside it.
"""
import os, shutil, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
from lib import paths  # noqa: E402
from pipeline.export import export_adm_practice, export_textbooks, export_web  # noqa: E402

PAGES = ["practice.html", "textbook.html", "adm_practice.html"]


def main():
    export_web.main()
    export_adm_practice.main()
    export_textbooks.main()
    for name in PAGES:
        shutil.copy2(os.path.join(paths.ASSETS, name), os.path.join(paths.DATA, name))
    dst = os.path.join(paths.DATA, "vendor")
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(os.path.join(paths.ASSETS, "vendor"), dst)
    print(f"pages + vendor/ -> {paths.DATA}")


if __name__ == "__main__":
    main()
