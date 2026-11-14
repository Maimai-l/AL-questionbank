#!/usr/bin/env python3
"""Parse CAIE mark schemes (9709 / 9231 / 9618 / 9702) into per-question records.

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
# 9702 heads its table "Question  Answer  Mark" (singular, no Guidance column) and
# also awards C1 (a compensation mark, implied by a correct final answer). Used for
# 9702 only, so the other subjects' schemes parse exactly as before.
TABLE_HDR_9702 = re.compile(r"^\s*Question\s+Answer\s+Marks?")
CODE_9702 = re.compile(
    r"(?<![A-Za-z])(\*?D?[MABC]\d|FT|CAO|CWO|AEF|OE|SOI|ISW|AWRT|WWW|AG|SC|ECF|POT)(?![A-Za-z])")
AWARDS_9702 = re.compile(r"(?:\*?D?[MABC](\d)(?:,\d)*(?:FT)?(?: {1,2}|$))+")
AWARD_9702 = re.compile(r"[MABC](\d)")
# with a Guidance column the codes are one run, single-spaced ("C1 C1"); the guidance
# after them may itself open with a code ("C1 mark is for ...")
AWARDS_COL_9702 = re.compile(r"\*?D?[MABC]\d(?:,\d)*(?:FT)?(?: \*?D?[MABC]\d(?:,\d)*(?:FT)?)*(?=\s|$)")
AWARDS_TAIL_9702 = re.compile(r"\s{2}((?:\*?D?[MABC]\d(?:,\d)*(?:FT)?(?: {1,2}|$))+)\s*$")
FURNITURE_9702 = re.compile(r"^\s*9702/")


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


def awards(line, mcol, awards_re=None, award_re=None, exact=None):
    """Marks awarded by the codes that open the Marks column of this line. exact: the
    column the codes start at (9702 schemes with a Guidance column, whose prose also
    opens with codes: "C1 is for the working ...")."""
    awards_re, award_re = awards_re or AWARDS_RE, award_re or AWARD_RE
    if exact is not None:
        m = code_at(line, exact)
        return sum(int(d) for d in award_re.findall(m.group(0))) if m else 0
    lo = max(mcol - 3, 0)
    start = len(line) - len(line[lo:].lstrip()) if line[lo:].strip() else None
    if awards_re is AWARDS_9702:
        # a long 9702 answer line runs into the Marks column ("... at each node      B1")
        m = AWARDS_TAIL_9702.search(line)
        if m and m.start(1) >= mcol - 6 and (start is None or line[lo - 1:lo].strip()
                                              or not awards_re.match(line, start)):
            return sum(int(d) for d in award_re.findall(m.group(1)))
    if start is None or start > mcol + 14 or line[lo - 1:lo].strip():
        return 0
    m = awards_re.match(line, start)
    return sum(int(d) for d in award_re.findall(m.group(0))) if m else 0


def code_at(line, cols):
    """The run of award codes in the Marks column: starting within 3 characters of the
    codes' column (the layout text drifts a little from line to line), after a gap, and
    ending before the Guidance column, whose prose may open with a code."""
    col, gcol = cols
    for c in range(max(col - 3, 2), min(col + 4, gcol)):
        if c < len(line) and line[c].strip() and not line[c - 2:c].strip():
            return AWARDS_COL_9702.match(line[:gcol], c)
    return None


def code_column(lines, mcol):
    """Where a 9702 table with a Guidance column starts its award codes: the commonest
    start of a code on the lines that open a part."""
    cols, guide = collections.Counter(), collections.Counter()
    for l in lines:
        if LABEL_RE.match(l) and l[:1].isspace():
            m = re.search(r"(?<=\s\s)\*?D?[MABC]\d\s+(?=\S)", l[max(mcol - 4, 0):mcol + 16])
            if m:
                cols[max(mcol - 4, 0) + m.start()] += 1
                guide[max(mcol - 4, 0) + m.end()] += 1
    if not cols:
        return None
    col = cols.most_common(1)[0][0]
    return col, max(guide.most_common(1)[0][0], col + 3)


def row_9702(line, mcol, gcol, exact=None):
    """One line of a 9702 scheme as `answer  |  marks` (lib/scheme.py) when it ends in
    the Marks column: award codes ("C1", "B1 B1") or, on paper 5 and paper 1, a mark.
    With a Guidance column (exact: where the codes start) `answer  |  codes  |  guidance`."""
    if exact is not None:
        m = code_at(line, exact)
        if m:
            return "  |  ".join([line[:m.start()].strip(), m.group(0).strip(),
                                 line[m.end():].strip()]).rstrip(" |")
        return line.rstrip()
    m = AWARDS_TAIL_9702.search(line)
    if m and m.start(1) >= mcol - 6:
        return f"{line[:m.start()].strip()}  |  {m.group(1).strip()}"
    t = marks_total(line, mcol, gcol)
    if t and t[1]:
        n = re.search(r"(\d{1,2})\s*$", line)
        if n and n.start(1) >= mcol - 6:
            return f"{line[:n.start(1)].strip()}  |  {n.group(1)}"
    return line.rstrip()


def parse(path):
    txt = subprocess.run(["pdftotext", "-layout", path, "-"],
                         capture_output=True, text=True, timeout=120).stdout
    lines = txt.split("\n")
    phys = os.path.basename(path).startswith("9702")
    hdr_re = TABLE_HDR_9702 if phys else TABLE_HDR_RE
    code_re = CODE_9702 if phys else CODE_RE
    aw = (AWARDS_9702, AWARD_9702) if phys else (AWARDS_RE, AWARD_RE)

    # skip the generic marking-instructions preamble
    start = next((i for i, l in enumerate(lines) if hdr_re.match(l)), None)
    if start is None:
        return []

    # The per-part mark total is a lone number right-aligned in the Marks
    # column. Numbers further right belong to Guidance prose and must not be
    # counted, so track the column boundaries from each table header.
    mcol, gcol = 89, 114
    rows, cur, prev = [], None, ""
    exact = None
    for k, line in enumerate(lines[start:], start):
        if hdr_re.match(line):
            if phys:                    # 2026: a Guidance column beside the codes
                end = next((j for j in range(k + 1, len(lines)) if hdr_re.match(lines[j])), len(lines))
                m = line.find("Mark")
                exact = code_column(lines[k + 1:end], m) if "Guidance" in line else None
            if "Marks" in line:
                mcol = line.index("Marks")
            elif phys and "Mark" in line:
                mcol = line.index("Mark")
            elif "Partial" in prev:
                mcol = prev.index("Partial")
            gcol = line.index("Guidance") if "Guidance" in line else mcol + 25
            continue
        prev = line
        if COL_HDR_RE.match(line):
            continue
        if FURNITURE_RE.search(line) or (phys and FURNITURE_9702.search(line)):
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
            cur = {"q": q, "part": part, "lines": [line], "cols": (mcol, gcol, exact),
                   "totals": [], "loose": [], "awards": 0,
                   "alt": bool(ALT_RE.search(line))}
            cur["awards"] += awards(line, mcol, *aw, exact=exact)
        elif cur is not None:
            cur["lines"].append(line)
            cur["alt"] = cur["alt"] or bool(ALT_RE.search(line))
            if not cur["alt"]:
                cur["awards"] += awards(line, mcol, *aw, exact=exact)
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
        if phys:                        # the Marks column as a cell, as the OCR'd schemes have it
            body = "\n".join(row_9702(l, *r["cols"]) for l in r["lines"]).rstrip()
        else:
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
        if tot and phys and r["q"] and r["awards"] == 0:
            # 9702 paper 5 prints a mark beside each marking point instead of award
            # codes and a part total: the rows add up
            entry["totals"][label] = entry["totals"].get(label, 0) + sum(r["totals"] + r["loose"])
        elif tot:
            entry["totals"][label] = tot[-1]

    stem = os.path.basename(path).replace(".pdf", "")
    subject, series, _, comp = stem.split("_")
    out = []
    for q, e in byq.items():
        body = "\n".join(e["text"])
        codes = code_re.findall(body)
        totals = list(e["totals"].values())
        if phys and not totals and e["awards"]:
            totals = [e["awards"]]            # 9702 prints award codes, no part totals
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
        if phys and comp[0] == "1":         # multiple choice: "12   C   1"
            a = re.match(r"^\s*\d{1,2}\s+([A-D])\b", body)
            out[-1]["answer"] = a.group(1) if a else None
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
