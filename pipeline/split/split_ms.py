#!/usr/bin/env python3
"""Parse CAIE 9709 mark schemes into per-question records.

Mark scheme pages are landscape/rotated, so PyMuPDF block coordinates are
unusable; `pdftotext -layout` renders the Question|Answer|Marks|Guidance table
faithfully, so we parse its text stream instead.
"""
import json, os, re, subprocess, sys, collections

# a row label sits in the left-hand column: a little indentation, then 3(a)(ii)
# and at least two spaces. In 9709_s25_ms_13 one space goes before " 10(a)" and
# none before "10(c)(i)"; 9709_w22_ms_11 prints question 4 as ".4"; "5(b(iii)"
# in 9618_s22_ms_13 lacks a bracket; 9618_s23_ms_11 goes up to (vi).
LABEL_RE = re.compile(r"^ {0,11}\.?(\d{1,2})(\([a-z]\)?)?(\((?:i{1,3}|iv|vi{0,3}|ix|x)\))?"
                      r"(?=\s\s|\s*$)")
# 9231_s23_ms_23 heads the column "Partial" / "Marks" on the lines above and
# below "Question  Answer  Guidance"
TABLE_HDR_RE = re.compile(r"^\s*Question\s+Answer\s+(?:Marks|Guidance)")
COL_HDR_RE = re.compile(r"^\s*(?:Partial|Marks)\s*$")
FURNITURE_RE = re.compile(
    r"©\s*UCLES|PUBLISHED|dynamicpapers|^\s*9709/|Cambridge International|"
    r"Page \d+ of \d+|^\s*BLANK PAGE", re.I)
CODE_RE = re.compile(
    r"(?<![A-Za-z])(\*?D?[MAB]\d|FT|CAO|CWO|AEF|OE|SOI|ISW|AWRT|WWW|AG|SC)(?![A-Za-z])")
# The part total in the Marks column. The Guidance column may carry on along
# the same line: prose ("5 Note: SC B1 B1 B1 ...", 9709_s25_ms_11 3(a)) or,
# after a gap, a piece of a formula ("5      dy", 9709_s24_ms_11 11(a)). A number
# followed closely by anything else is guidance wrapped into the column
# ("67 (or better).", 9709_s25_ms_42) and not a total.
TOTAL_RE = re.compile(r"( *)(\d{1,2})(?=\s|$)")
AFTER_TOTAL_RE = re.compile(r"\s*$| {3}| {1,2}(?:[A-Z][a-z]|[A-Z]{2}|[MAB]\d)")
# Award codes at the head of the Marks column: "B1", "M1 A1", "*DM1", "B2,1,0"
# (worth 2), "B1FT". "(M1)" in brackets belongs to an alternative method.
AWARDS_RE = re.compile(r"(?:\*?D?[MAB](\d)(?:,\d)*(?:FT)?(?: {1,2}|$))+")
AWARD_RE = re.compile(r"[MAB](\d)")
ALT_RE = re.compile(r"\bAlternative\b", re.I)


def marks_total(line, mcol, gcol):
    """The part total this line prints in the Marks column, as (total, alone).

    Answer text may run up to it (the label line of a CS scheme, "Im" beside
    9709_s23_ms_33 3, a table of iterates in 5(b)), but an award code in front
    of it ("M1   8", 9709_s21_ms_51 1) makes it guidance. alone: nothing else
    follows on the line.
    """
    for m in TOTAL_RE.finditer(line):
        col = m.start(2)
        if col > min(mcol + 13, gcol - 2):
            return None
        if col < mcol - 2 or line[col - 1:col].strip():
            continue
        if AWARD_RE.search(line[max(mcol - 6, 0):col]):
            return None
        rest = line[m.end():]
        if not AFTER_TOTAL_RE.match(rest):
            return None
        return int(m.group(2)), not rest.strip()
    return None


def awards(line, mcol):
    """Marks awarded by the codes that open the Marks column of this line."""
    lo = max(mcol - 3, 0)
    start = len(line) - len(line[lo:].lstrip()) if line[lo:].strip() else None
    if start is None or start > mcol + 14 or line[lo - 1:lo].strip():
        return 0
    m = AWARDS_RE.match(line, start)
    return sum(int(d) for d in AWARD_RE.findall(m.group(0))) if m else 0


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
    rows, cur, prev = [], None, ""
    for line in lines[start:]:
        if TABLE_HDR_RE.match(line):
            if "Marks" in line:
                mcol = line.index("Marks")
            elif "Partial" in prev:
                mcol = prev.index("Partial")
            gcol = line.index("Guidance") if "Guidance" in line else mcol + 25
            continue
        prev = line
        if COL_HDR_RE.match(line):
            continue
        if FURNITURE_RE.search(line):
            continue
        m = LABEL_RE.match(line)
        # flush left only with a part: "10(c)(i)" in 9709_s25_ms_13
        if m and not line[0].isspace() and not m.group(2):
            m = None
        if m:
            if cur:
                rows.append(cur)
            q = int(m.group(1))
            part = m.group(2) or ""
            if part and not part.endswith(")"):
                part += ")"                       # "5(b(iii)" -> 5(b)(iii)
            part += m.group(3) or ""
            cur = {"q": q, "part": part, "lines": [line],
                   "totals": [], "loose": [], "awards": 0,
                   "alt": bool(ALT_RE.search(line))}
            cur["awards"] += awards(line, mcol)
        elif cur is not None:
            cur["lines"].append(line)
            cur["alt"] = cur["alt"] or bool(ALT_RE.search(line))
            if not cur["alt"]:
                cur["awards"] += awards(line, mcol)
        if cur is not None:
            # Marks column is narrow and right-aligned; Guidance prose also
            # produces numbers, so bound the window tightly. (A wider window
            # was tried and measured *worse* — it lets in Guidance-column
            # numbers faster than it recovers real totals.)
            # A number alone on its line outranks one with guidance after it:
            # in 9709_w24_ms_43 6(a) the total "1" is followed by "5   v", a
            # piece of a formula in the Guidance column.
            t = marks_total(line, mcol, gcol)
            if t:
                cur["totals" if t[1] else "loose"].append(t[0])
    if cur:
        rows.append(cur)

    # merge parts belonging to the same question number
    byq = collections.OrderedDict()
    for r in rows:
        body = "\n".join(r["lines"]).rstrip()
        entry = byq.setdefault(r["q"], {"q": r["q"], "parts": [], "text": [],
                                        "totals": {}, "awards": 0})
        entry["awards"] += r["awards"]
        label = f"{r['q']}{r['part']}"
        if r["part"] and label not in entry["parts"]:
            entry["parts"].append(label)
        entry["text"].append(body)
        # exactly one total per part, printed at the end of that part's rows.
        # A label comes back for a page break and for each alternative method
        # ("10(b) Alternative Method for Question 10(b)"), each with its own
        # total, so the last one stands for the part rather than their sum.
        tot = r["totals"] or r["loose"]
        if tot:
            entry["totals"][label] = tot[-1]

    stem = os.path.basename(path).replace(".pdf", "")
    subject, series, _, comp = stem.split("_")
    out = []
    for q, e in byq.items():
        body = "\n".join(e["text"])
        codes = CODE_RE.findall(body)
        totals = list(e["totals"].values())
        out.append({
            "subject": subject, "paper": f"{subject}/{comp}", "series": series,
            "component": comp[0], "variant": comp[1], "q": q,
            "parts": e["parts"],
            "ms_text": re.sub(r"\n{3,}", "\n\n", body).strip(),
            "mark_codes": codes,
            "ms_total": sum(totals) if totals else None,
            "award_total": e["awards"] or None,
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
