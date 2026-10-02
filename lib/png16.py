"""Question images are stored as 16-level grey PNGs (4-bit palette).

The crops are greyscale renders of printed pages: 95% of the pixels are
white, the rest are anti-aliased text edges, shaded regions of diagrams and
watermarks. Sixteen evenly spaced grey levels (0, 17, ..., 255) keep all of
these visibly unchanged, shaded regions included (CAIE fills them at 204,
which is a level), and take about 64% of the space of an 8-bit PNG. Two-level
(black and white) loses the shading, so it is not used.
"""
from PIL import Image

STEP = 17                                   # 255 / 15
LEVELS = 16
_LUT = [round(v / STEP) for v in range(256)]
PALETTE = [c for i in range(LEVELS) for c in (i * STEP,) * 3]


def to_gray16(im):
    """A 4-bit palette image with the 16 grey levels, from any PIL image."""
    idx = im.convert("L").point(_LUT)
    out = Image.frombytes("P", idx.size, idx.tobytes())
    out.putpalette(PALETTE)
    return out


def save(im, path):
    to_gray16(im).save(path, "PNG", bits=4, optimize=True)


def save_pixmap(pix, path):
    """Save a PyMuPDF Pixmap (grey or RGB, no alpha) as a 16-level PNG."""
    mode = {1: "L", 3: "RGB"}[pix.n]
    save(Image.frombytes(mode, (pix.width, pix.height), pix.samples, "raw", mode, pix.stride), path)


def is_gray16(path):
    with Image.open(path) as im:
        if im.mode != "P":
            return False
        pal = im.getpalette()[:LEVELS * 3]
        return pal == PALETTE[:len(pal)] and max(im.getdata()) < LEVELS


def convert(path):
    """Rewrite one PNG in place as 16-level grey. Returns (bytes before, after)."""
    import os
    before = os.path.getsize(path)
    if not is_gray16(path):
        with Image.open(path) as im:
            im.load()
        save(im, path)
    return before, os.path.getsize(path)
