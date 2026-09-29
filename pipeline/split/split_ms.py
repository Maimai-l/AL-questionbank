#!/usr/bin/env python3
"""Parse CAIE 9709 mark schemes into per-question records.

Mark scheme pages are landscape/rotated, so PyMuPDF block coordinates are
unusable; `pdftotext -layout` renders the Question|Answer|Marks|Guidance table
faithfully, so we parse its text stream instead.
"""
import json, os, re, subprocess, sys, collections

# a row label sits in the left-hand column: a little indentation, then 3(a)(ii)
LABEL_RE = re.compile(r"^ {2,11}(\d{1,2})(\([a-z]\))?(\((?:i{1,3}|iv|v)\))?(?=\s)")
TABLE_HDR_RE = re.compile(r"^\s*Question\s+Answer\s+Marks")
FURNITURE_RE = re.compile(
    r"©\s*UCLES|PUBLISHED|dynamicpapers|^\s*9709/|Cambridge International|"
    r"Page \d+ of \d+|Mark Scheme|^\s*BLANK PAGE", re.I)
CODE_RE = re.compile(
    r"(?<![A-Za-z])(\*?D?[MAB]\d|FT|CAO|CWO|AEF|OE|SOI|ISW|AWRT|WWW|AG|SC)(?![A-Za-z])")
LONE_NUM_RE = re.compile(r"^(\s+)(\d{1,2})\s*$")
# CS mark schemes print the part total at the end of the label line rather than
# on a line of its own; capture it only when it lands in the Marks column.
TRAIL_NUM_RE = re.compile(r"^.*?(\s)(\d{1,2})\s*$")


def parse(path):
    txt = subprocess.run(["pdftotext", "-layout", path, "-"],
                         capture_output=True, text=True, timeout=120).stdout
    lines = txt.split("\n")

    # skip the generic marking-instructions preamble
    start = next((i for i, l in enumerate(lines) if TABLE_HDR_RE.match(l)), None)
    if start is None:
        return []

    # The per-part mark total is a lone number right-aligned in the Marks
    # column. Numbers further right belong to Guidance prose and must not be
    # counted, so track the column boundaries from each table header.
    mcol, gcol = 89, 114
    rows, cur = [], None
    for line in lines[start:]:
        if TABLE_HDR_RE.match(line):
            mcol = line.index("Marks")
            gcol = line.index("Guidance") if "Guidance" in line else mcol + 25
            continue
        if FURNITURE_RE.search(line):
            continue
        m = LABEL_RE.match(line)
        if m:
            if cur:
                rows.append(cur)
            q = int(m.group(1))
            part = (m.group(2) or "") + (m.group(3) or "")
            cur = {"q": q, "part": part, "lines": [line],
                   "totals": [], "totals_wide": []}
            tn = TRAIL_NUM_RE.match(line)
            if tn:
                col = tn.start(2)
                if mcol - 2 <= col <= min(mcol + 13, gcol - 2):
                    cur["totals"].append(int(tn.group(2)))
        elif cur is not None:
            cur["lines"].append(line)
            n = LONE_NUM_RE.match(line)
            # Marks column is narrow and right-aligned; Guidance prose also
            # produces lone numbers, so bound the window tightly. The column
            # drifts a few characters page to page, so keep a wider capture as
            # a fallback for parts where the tight window finds nothing.
            # (A wider fallback window was tried and measured *worse* — it lets
            # in Guidance-column numbers faster than it recovers real totals.)
            if n and mcol - 2 <= len(n.group(1)) <= min(mcol + 13, gcol - 2):
                cur["totals"].append(int(n.group(2)))
    if cur:
        rows.append(cur)

    # merge parts belonging to the same question number
    byq = collections.OrderedDict()
    for r in rows:
        body = "\n".join(r["lines"]).rstrip()
        entry = byq.setdefault(r["q"], {"q": r["q"], "parts": [], "text": [],
                                        "totals": []})
        label = f"{r['q']}{r['part']}"
        if r["part"] and label not in entry["parts"]:
            entry["parts"].append(label)
        entry["text"].append(body)
        # exactly one total per part, printed at the end of that part's rows
        tot = r["totals"]
        if tot:
            entry["totals"].append(tot[-1])

    stem = os.path.basename(path).replace(".pdf", "")
    subject, series, _, comp = stem.split("_")
    out = []
    for q, e in byq.items():
        body = "\n".join(e["text"])
        codes = CODE_RE.findall(body)
        totals = e["totals"]
        out.append({
            "subject": subject, "paper": f"{subject}/{comp}", "series": series,
            "component": comp[0], "variant": comp[1], "q": q,
            "parts": e["parts"],
            "ms_text": re.sub(r"\n{3,}", "\n\n", body).strip(),
            "mark_codes": codes,
            "ms_total": sum(totals) if totals else None,
            "source": os.path.basename(path),
        })
    return out


if __name__ == "__main__":
    files = sorted(f for f in os.listdir(sys.argv[1]) if "_ms_" in f)
    allm, bad = [], []
    for f in files:
        try:
            rs = parse(os.path.join(sys.argv[1], f))
            if len(rs) < 4:
                bad.append((f, len(rs)))
            allm += rs
        except Exception as e:
            bad.append((f, f"{type(e).__name__}: {e}"))
    json.dump(allm, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
    print(f"ms files={len(files)}  records={len(allm)}  suspicious={len(bad)}")
    for f, why in bad[:15]:
        print("  ", f, why)
