#!/usr/bin/env python3
"""Rewrite the question images in data/ as 16-level grey PNGs (lib/png16.py).

    python3 pipeline/split/to_png16.py [DIR ...] [--jobs 4]

Without DIR: the CAIE crops (img9709/ img9231/ img9618/), their answer-space
copies (img*_ans/) and the admissions crops (img_adm/). Images already in
the 16-level format are left alone, so the run can be repeated. img_tara/
holds colour JPEG illustrations and is not touched.
"""
import argparse, glob, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
from lib import paths, png16  # noqa: E402

DIRS = ["img9709", "img9231", "img9618", "img9709_ans", "img9231_ans", "img9618_ans", "img_adm"]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dirs", nargs="*")
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    dirs = a.dirs or [os.path.join(paths.DATA, d) for d in DIRS]
    files = [f for d in dirs for f in sorted(glob.glob(os.path.join(d, "*.png")))]
    from multiprocessing import Pool
    with Pool(a.jobs) as pool:
        sizes = pool.map(png16.convert, files, chunksize=32)
    before, after = sum(b for b, _ in sizes), sum(x for _, x in sizes)
    print(f"{len(files)} 张:{before / 1e6:.1f} MB -> {after / 1e6:.1f} MB"
          f"({after / max(before, 1) * 100:.1f}%)")


if __name__ == "__main__":
    main()
