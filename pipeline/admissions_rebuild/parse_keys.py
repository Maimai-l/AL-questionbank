#!/usr/bin/env python3
"""Parse every answer key in the bank into one answers.json.

    python3 parse_keys.py

Output: {"TMUA-2021-1": {"1": "F", ...}, "TSA-2019": {...}, "BMAT-2021": {...}}

The keys are tables in the OCR output. TMUA keys carry both papers in one file;
TSA/BMAT one section per file. Counts are asserted — a key with 17 answers for
a 20-question paper stops the run rather than passing quietly.
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))          # 项目根目录;在任意目录下运行都能找到 lib
from lib import paths  # noqa: E402

ROOT = paths.BANK_OCR
OUT = os.path.join(paths.ADM, "answers.json")
ROW = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
CELL = re.compile(r"<td[^>]*>\s*([^<]*?)\s*</td>")
# BMAT S1 answers are usually a letter but sometimes a number ("37") or a
# pair ("C and E"); anything short and non-empty is a legitimate key
# a key cell is anything short: a letter, "37", "£10500", "30 to 49", "A & C".
# Header words are the only thing to exclude.
ANS = re.compile(r"^(?!(?:KEY|Correct|Comments?|Question|Answer|Maximum)\b)"
                 r"[A-Za-z0-9£%&;:.,()\- ]{1,24}$")


def read_all(d):
    t = ""
    for f in sorted(os.listdir(d)):
        if re.match(r"page_\d+\.md$", f):
            t += open(os.path.join(d, f), encoding="utf-8").read() + "\n"
    return t


def pairs_from_tables(text, columns=1):
    """(qnum, answer) pairs, row by row.

    Row-based on purpose: TMUA 2016 lays two papers side by side (Q,K,Q,K per
    row) and the old BMAT keys carry Comments and Max-points columns, so a
    flat cell scan pairs the wrong neighbours. `columns` streams are returned
    concatenated: stream 0 first, then stream 1.
    """
    streams = [[] for _ in range(columns)]
    for row in ROW.findall(text):
        cells = [c.strip() for c in CELL.findall(row)]
        # walk cells left to right: every (int, answer-like) adjacency is a hit
        hits = []
        i = 0
        while i + 1 < len(cells):
            if re.fullmatch(r"\d{1,2}", cells[i]) and cells[i + 1] \
                    and ANS.fullmatch(cells[i + 1]):
                hits.append((int(cells[i]), cells[i + 1]))
                i += 2
            else:
                i += 1
        for k, h in enumerate(hits[:columns]):
            streams[k].append(h)
    out = []
    for s in streams:
        out += s
    return out


def pairs_from_lines(text):
    """Fallback for keys that OCR'd as plain lines '7  C'."""
    out = []
    for m in re.finditer(r"^\s*(\d{1,2})[\s.|]+([A-H])\s*$", text, re.M):
        out.append((int(m.group(1)), m.group(2)))
    return out


def split_runs(pairs):
    """A key file holding two papers restarts numbering at 1."""
    runs, cur = [], []
    for q, a in pairs:
        if cur and q <= cur[-1][0]:
            runs.append(cur)
            cur = []
        cur.append((q, a))
    if cur:
        runs.append(cur)
    return runs


def main():
    answers, problems = {}, []

    # ---- TMUA: one file per year, two papers inside -----------------------
    for d in sorted(os.listdir(f"{ROOT}/TMUA/answer_keys")):
        m = re.match(r"TMUA-(\w+)-answer-keys", d)
        if not m:
            continue
        year = m.group(1)
        text = read_all(f"{ROOT}/TMUA/answer_keys/{d}")
        # try the side-by-side layout first; fall back to stacked tables
        for cols in (2, 1):
            runs = [r for r in split_runs(pairs_from_tables(text, cols) or
                                          pairs_from_lines(text)) if len(r) >= 10]
            if len(runs) == 2:
                break
        if len(runs) != 2:
            problems.append(f"TMUA {year}: 应有 2 张答案表,读到 {len(runs)}")
            continue
        for paper, run in zip(("1", "2"), runs):
            if len(run) != 20 or [q for q, _a in run] != list(range(1, 21)):
                problems.append(f"TMUA {year} P{paper}: {len(run)} 条,应为 1..20")
            answers[f"TMUA-{year}-{paper}"] = {str(q): a for q, a in run}

    # ---- TSA / BMAT: one file per year ------------------------------------
    # the paper sizes drifted over two decades, so the invariant is
    # completeness (1..N with no gaps), plus a sanity band on N
    for exam, sub, band in (("TSA", "TARA/TSA_section1/answer_keys", (50, 50)),
                            ("BMAT", "TARA/BMAT_section1/answer_keys", (30, 40))):
        for d in sorted(os.listdir(f"{ROOT}/{sub}")):
            m = re.match(rf"{exam}-(\d{{4}})-S1-key", d)
            if not m:
                continue
            year = m.group(1)
            text = read_all(f"{ROOT}/{sub}/{d}")
            pairs = pairs_from_tables(text)
            lines = pairs_from_lines(text)
            best = max((pairs, lines), key=len)
            # keep first occurrence per question number
            seen, run = set(), []
            for q, a in best:
                if q not in seen:
                    seen.add(q)
                    run.append((q, a))
            run.sort()
            gaps = [q for q in range(1, (run[-1][0] if run else 0) + 1)
                    if q not in seen]
            if not run or run[0][0] != 1 or gaps \
               or not (band[0] <= len(run) <= band[1]):
                problems.append(f"{exam} {year}: 读到 {len(run)} 条,缺 {gaps[:8]},"
                                f" N={run[-1][0] if run else 0}, 允许 {band}")
            answers[f"{exam}-{year}"] = {str(q): a for q, a in run}

    json.dump(answers, open(OUT, "w"), indent=1)
    total = sum(len(v) for v in answers.values())
    print(f"{len(answers)} 份答案键,共 {total} 个答案 -> answers.json")
    if problems:
        print(f"\n⚠️  {len(problems)} 处对不上:")
        for p in problems:
            print("  ", p)
    else:
        print("全部数量核验通过")


if __name__ == "__main__":
    main()
