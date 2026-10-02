"""Rows of the CAIE mark schemes as stored in ms_latex and ms_text.

parse_ms_ocr.py writes each row as `answer  |  marks  |  guidance`: the cells are
joined by a bar with two spaces on each side. Maths uses bare bars too (|x|,
\\left|, P(A|B)), never padded like that, so only the padded bar separates cells.
A line without one continues the row above. A line break inside a cell is <br>.
"""
import re

SEP = re.compile(r"(?:^|\s{2})\|(?=\s{2}|\s*$)")


def cells(line):
    """The cells of one row, stripped; a line that is not a row is one cell."""
    return [c.strip() for c in SEP.split(line)]


def is_row(line):
    return bool(SEP.search(line))
