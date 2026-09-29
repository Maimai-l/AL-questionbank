#!/usr/bin/env python3
"""Split the OCR'd TMUA / TSA / BMAT papers into individual questions.

    python3 split_admissions.py            # all three
    python3 split_admissions.py TMUA       # one family

Three formats, three anchors:

TMUA   one question per page. The cover and BLANK pages are recognisable, and
       what remains, in order, is Q1..Q20 — asserted, not assumed. OCR often
       drops the printed question number; the position supplies it.

TSA    numbers are unreliable (the leading digit of two-digit numbers is
       frequently lost) but every question ends in a complete A..E option run,
       so option runs are the anchor and numbers only corroborate.

BMAT   same engine as TSA, with two extra wrinkles: option letters go up to H
       in some years, and the early papers mix in short-answer questions with
       no options at all — those are recovered from numbered heads between
       option runs.

Validation per paper, against answers.json:
  * question count must equal the key's count exactly;
  * for every lettered answer, that letter must exist among the question's
    options.
Failures are listed per paper; nothing is silently dropped.
"""
import json, os, re, sys

ROOT = "bank_ocr"
KEYS = json.load(open("answers.json"))

BLANK = re.compile(r"^#*\s*BLANK PAGE\s*$", re.M)
COVER = re.compile(r"INSTRUCTIONS TO CANDIDATES|Time:\s*\d+|"
                   r"Thinking Skills Assessment|BioMedical Admissions Test|"
                   r"BMAT|UNIVERSITY ADMISSION", re.I)
IMGTAG = re.compile(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>')
ROWRE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
CELLRE = re.compile(r"<td[^>]*>\s*(.*?)\s*</td>", re.S)
TABLERE = re.compile(r"<table\b.*?</table>", re.S)


def pages_of(d):
    out = []
    for f in sorted(os.listdir(d)):
        m = re.match(r"page_(\d+)\.md$", f)
        if m:
            out.append((int(m.group(1)),
                        open(os.path.join(d, f), encoding="utf-8").read()))
    return out


def tables_to_lines(text):
    """Option tables ("A | 1:1") become plain 'A 1:1' lines; data tables stay.

    The discriminator: a table whose rows are (letter, value) pairs is an
    option list, anything else is content the question needs verbatim.
    """
    def conv(m):
        rows = []
        letterish = 0
        for row in ROWRE.findall(m.group(0)):
            cells = [re.sub(r"<[^>]+>", " ", c).strip() for c in CELLRE.findall(row)]
            rows.append(cells)
            if cells and re.fullmatch(r"[A-H]", cells[0]):
                letterish += 1
        if rows and letterish >= max(2, len(rows) - 1):
            return "\n" + "\n".join(f"{r[0]} {' '.join(r[1:]).strip()}"
                                    for r in rows if r) + "\n"
        return m.group(0)
    return TABLERE.sub(conv, text)


# ---------------------------------------------------------------- TMUA

def page_segments(text):
    """Split one page into question segments by option runs.

    Returns (segments, leading_run): segments are (text, options); leading_run
    is true when the page *opens* with options — the tail of the previous
    page's question in a dense layout.
    """
    lines = [(0, l) for l in tables_to_lines(text).split("\n")]
    runs = find_option_runs(lines)
    if not runs:
        return [(text.strip(), mathblock_options(text))], False
    leading = bool(runs and all(not lines[i][1].strip()
                                for i in range(runs[0][0]))
                   is False and runs[0][0] == next(
                       (k for k, (_n, l) in enumerate(lines) if l.strip()), 0))
    segs, prev = [], 0
    for run in runs:
        end = run[-1] + 1
        seg = "\n".join(l for _n, l in lines[prev:end]).strip()
        segs.append((seg, [lines[i][1].strip()[0] for i in run]))
        prev = end
    tail = "\n".join(l for _n, l in lines[prev:]).strip()
    if len(tail) > 40:
        if re.match(r"^(?:\*\*|#+\s*)?\d{1,2}[.\s]", tail):
            # a numbered head: genuinely the next question
            segs.append((tail, mathblock_options(tail)))
        elif segs:
            # no head: a displaced piece of the question above (OCR often
            # emits the display equation after the option run)
            segs[-1] = (segs[-1][0] + "\n" + tail, segs[-1][1])
        else:
            segs.append((tail, mathblock_options(tail)))
    return segs, leading


def split_tmua(year, paper):
    d = f"{ROOT}/TMUA/papers/TMUA-{year}-paper-{paper}"
    key = KEYS.get(f"TMUA-{year}-{paper}", {})
    qs = []
    for no, text in pages_of(d):
        body = text.strip()
        if not body or BLANK.search(body[:80]):
            continue
        if no <= 2 and COVER.search(body):
            continue
        segs, leading = page_segments(text)
        for k, (seg, opts) in enumerate(segs):
            if k == 0 and leading and qs and not qs[-1]["options"]:
                # page opens with the previous question's options
                qs[-1]["text"] += "\n" + seg
                qs[-1]["options"] = opts
                qs[-1]["pages"].append(no)
                continue
            qs.append({"exam": "TMUA", "year": year, "paper": paper,
                       "q": None, "pages": [no], "text": seg,
                       "options": opts})
    for i, q in enumerate(qs, 1):
        q["q"] = i
        q["text"] = re.sub(rf"^\s*(?:\*\*)?{i}(?:\*\*)?[.\s]", "",
                           q["text"], count=1).strip()
        q["answer"] = key.get(str(i))
    return qs, len(key) or 20


# ------------------------------------------------------------ TSA / BMAT

OPT_LINE = re.compile(r"^(?:\*\*)?([A-H])(?:\*\*)?[\s.):]+(.*)$")
# options packed into one display-math block: $$ \textbf{A}\quad ... \textbf{B} ... $$
TEXTBF = re.compile(r"\\(?:textbf|mathbf|bf)\s*\{\s*([A-H])\s*\}")


def mathblock_options(text):
    """Letters of an option list living inside a $$ ... $$ aligned block."""
    best = []
    for m in re.finditer(r"\$\$.*?\$\$", text, re.S):
        letters = TEXTBF.findall(m.group(0))
        seq = []
        for L in letters:
            if not seq or ord(L) == ord(seq[-1]) + 1:
                seq.append(L)
        if seq[:1] == ["A"] and len(seq) >= 3 and len(seq) > len(best):
            best = seq
    return best


DIVLET = re.compile(r"^<div[^>]*>\s*\(?([A-H])[.)]?\s*</div>\s*$", re.M)
# an option line that names a figure rather than carrying its own text
PICOPT = re.compile(r"\(图形选项\)|见图|见上方图|图中")
# a bare centring div (a stray caption between figures)
DIVRE = re.compile(r"<div[^>]*>[^<]{0,40}</div>")


def repair_option_gaps(lines):
    """Re-letter an option whose letter the OCR dropped.

    Pattern: option lines lettered X and X+2 with exactly one prose line
    between them — that middle line is option X+1 ('Depression is caused by
    the pace of modern life.' sitting letterless between C and E). The letter
    is prepended in place so both run detection and the question text heal.
    """
    opt = []   # (position in lines, letter)
    for i, (_no, ln) in enumerate(lines):
        m = OPT_LINE.match(ln.strip())
        if m:
            opt.append((i, m.group(1)))
    for (i1, l1), (i2, l2) in zip(opt, opt[1:]):
        if ord(l2) - ord(l1) != 2 or i2 - i1 > 5:
            # not an interior single-letter gap (or too far apart to be
            # neighbours in one option list)
            continue
        between = [j for j in range(i1 + 1, i2)
                   if lines[j][1].strip()
                   and not lines[j][1].lstrip().startswith("<")]
        if len(between) == 1:
            j = between[0]
            missing = chr(ord(l1) + 1)
            lines[j] = (lines[j][0], f"{missing} {lines[j][1].strip()}")

    # terminal gap: the last option's letter dropped. After option L comes a
    # single letterless prose line, and right after it the next question's
    # numbered head (or nothing) — that line is option L+1.
    opt2 = []
    for i, (_no, ln) in enumerate(lines):
        m = OPT_LINE.match(ln.strip())
        if m:
            opt2.append((i, m.group(1)))
    for i1, l1 in opt2:
        if l1 >= "H":
            continue
        after = [j for j in range(i1 + 1, min(i1 + 6, len(lines)))
                 if lines[j][1].strip()]
        if not after:
            continue
        j = after[0]
        cand = lines[j][1].strip()
        if (OPT_LINE.match(cand) or cand.startswith("<")
                or cand.endswith("?") or HEAD_NUM.match(cand)
                or len(cand) < 20):
            continue
        rest = [x for x in after[1:] if x > j]
        nxt = lines[rest[0]][1].strip() if rest else ""
        if not rest or re.match(r"^(?:#+\s*|\*\*)?\d{1,2}[.\s]", nxt):
            lines[j] = (lines[j][0], f"{chr(ord(l1) + 1)} {cand}")

    # leading gap: options B,C,... present but A's letter dropped. The line
    # right before B is option A exactly when the line before *that* is the
    # stem's question sentence (ends with ?).
    for k, (i1, l1) in enumerate(opt):
        if l1 != "B" or (k and opt[k - 1][1] == "A" and i1 - opt[k - 1][0] <= 5):
            continue
        prose = [j for j in range(max(0, i1 - 4), i1)
                 if lines[j][1].strip() and not lines[j][1].lstrip().startswith("<")]
        if not prose:
            continue
        j = prose[-1]
        cand = lines[j][1].strip()
        before = [x for x in range(0, j) if lines[x][1].strip()]
        if (not cand.endswith("?") and not OPT_LINE.match(cand) and before
                and lines[before[-1]][1].strip().endswith("?")):
            lines[j] = (lines[j][0], f"A {cand}")
    return lines


def line_stream(pages, skip_covers=True):
    """(page_no, line) for content pages, tables normalised first.

    Pictorial options (a centred <div>A</div> above each answer figure) are
    unwrapped to plain letter lines tagged (图形选项), so they anchor runs the
    same way text options do.
    """
    out = []
    for no, text in pages:
        body = text.strip()
        if not body or BLANK.search(body[:80]):
            continue
        if skip_covers and no <= 2 and COVER.search(body):
            continue
        text = DIVLET.sub(r"\1 (图形选项)", tables_to_lines(text))
        for ln in text.split("\n"):
            out.append((no, ln))
    return repair_option_gaps(out)


def _next_letter(lines, idx):
    """Letter of the next contentful line, for one-line lookahead."""
    for j in range(idx + 1, min(idx + 4, len(lines))):
        s = lines[j][1].strip()
        if not s or s.startswith("<"):
            continue
        m = OPT_LINE.match(s)
        return m.group(1) if m else None
    return None


def find_option_runs(lines):
    """Maximal runs of consecutive option lines A,B,C,... per question.

    A run must start at A and ascend without repeats; length >= 3. Blank lines
    inside a run are tolerated (OCR puts them between options).
    """
    runs, cur, expect = [], [], None
    for idx, (no, ln) in enumerate(lines):
        s = ln.strip()
        if not s or s.startswith("<") or IMGTAG.search(s):
            # markers, figures and tables may sit between options without
            # breaking the run (pictorial options interleave images; some
            # option lists are lettered data tables)
            continue
        m = OPT_LINE.match(s)
        letter = m.group(1) if m else None
        if letter and (expect is None or letter == expect):
            if expect is None:
                if letter != "A":
                    continue
                cur = []
            cur.append(idx)
            expect = chr(ord(letter) + 1)
        elif letter and cur and expect and letter > expect \
                and "(图形选项)" in s:
            # OCR drops some letters of pictorial option grids; the printed
            # letters are always consecutive, so a gap here is tolerable
            cur.append(idx)
            expect = chr(ord(letter) + 1)
        elif cur and expect and len(s) <= 40 and not letter \
                and "(图形选项)" in lines[cur[-1]][1]:
            # a short caption under a pictorial option ("View from East")
            # sits between letters without ending the list
            continue
        elif cur and expect and not letter \
                and _next_letter(lines, idx) == expect:
            # a single displaced line (often the question sentence, which
            # the OCR emitted mid-list) with the expected letter right after
            continue
        elif letter and cur and letter == "A":
            if _run_ok(lines, cur):
                runs.append(cur)
            cur = [idx]
            expect = "B"
        else:
            if cur and _run_ok(lines, cur):
                runs.append(cur)
            cur, expect = [], None
    if cur and _run_ok(lines, cur):
        runs.append(cur)
    return runs


def _run_ok(lines, cur):
    """A text run needs 3+ letters; a pictorial one may have lost all but
    one letter to the OCR, so any 图形选项 letters are accepted (the answer
    key later extends the range)."""
    if len(cur) >= 3:
        return True
    return bool(cur) and all("(图形选项)" in lines[i][1] for i in cur)


def split_mcq(exam, year, subdir, letters="A-E"):
    d = f"{ROOT}/{subdir}"
    key = KEYS.get(f"{exam}-{year}", {})
    want = len(key)
    lines = line_stream(pages_of(d))
    runs = find_option_runs(lines)

    # question boundaries: text between the end of one option run and the end
    # of the next belongs to the next question
    qs = []
    prev_end = 0
    for run in runs:
        start, end = prev_end, run[-1] + 1
        # a long option wraps onto following lines; absorb them up to the
        # next blank line so they don't open the next question's text.
        # Never cross onto the next page and never absorb a question
        # sentence — both mean the next question has begun.
        while end < len(lines):
            s = lines[end][1].strip()
            if not s or HEAD_NUM.match(s) or OPT_LINE.match(s) \
                    or s.startswith("<"):
                break
            # Only a genuine continuation: the last option must be unfinished
            # (no sentence-final punctuation) and the next line must not start
            # a new sentence. Otherwise this is the following question's
            # passage, and swallowing it leaves that question unanswerable.
            last = lines[end - 1][1].strip()
            if re.search(r"[.?!:;]$", last) or re.match(r"^[A-Z0-9“\"']", s):
                break
            end += 1
        # pictorial options: the letters are a caption list and the figures
        # they name follow *after* the run, so they must be absorbed too —
        # otherwise every chart lands in the next question, which then shows
        # someone else's diagrams while this one shows none.
        if any(PICOPT.search(lines[i][1]) for i in run):
            while end < len(lines):
                s = lines[end][1].strip()
                if not s or IMGTAG.search(s) or DIVRE.fullmatch(s):
                    end += 1
                    continue
                break
        seg = lines[start:end]
        prev_end = end
        pages = sorted({no for no, _l in seg})
        body = "\n".join(l for _n, l in seg).strip()
        opts = [lines[i][1].strip()[0] for i in run]
        if any("(图形选项)" in lines[i][1] for i in run):
            # printed pictorial options are consecutive; fill the gaps
            opts = [chr(c) for c in range(ord("A"), ord(opts[-1]) + 1)]
        qs.append({"pages": pages, "text": body, "options": opts})

    # early BMAT (2003-09): short-answer questions have no option run and
    # hide between runs; recover them by numbered heads inside an over-long
    # segment. Later papers are pure MCQ — a shortfall there means a lost
    # option run, and splitting at statement numbers would only mangle it.
    if want and len(qs) < want and (exam == "TSA" or int(year) <= 2011):
        qs = recover_short_answers(qs, want)

    nums = align_numbers(qs, want)
    out = []
    for q, n in zip(qs, nums):
        ans = key.get(str(n))
        opts = q.get("options", [])
        if ans and re.fullmatch(r"[A-H]", ans):
            if opts and "(图形选项)" in q["text"] and ans > opts[-1]:
                # the key's letter must exist on the printed page; a pictorial
                # grid whose last letters the OCR dropped is extended to it
                opts = [chr(c) for c in range(ord("A"), ord(ans) + 1)]
            m = re.search(r"\(\s*A\s*[-–]\s*([B-H])\s*\)", q["text"])
            if not opts and m:
                # the stem declares its own range: "Which plane (A - H) ..."
                opts = [chr(c) for c in range(ord("A"), ord(m.group(1)) + 1)]
        out.append({"exam": exam, "year": year, "paper": "1", "q": n,
                    "pages": q["pages"], "text": q["text"],
                    "options": opts, "answer": ans})
    return out, want


HEAD_EVID = re.compile(r"^(?:#+\s*|\*\*)?(\d{1,2})(?:\*\*)?[.\s]")


def align_numbers(qs, want):
    """Assign true question numbers to segments in order.

    When OCR loses questions, position numbering shifts everything after the
    hole and every answer after it is wrong. The printed heads are partial
    evidence (two-digit numbers often lose the leading digit), so this aligns
    the segment sequence 1..m to 1..want by DP: exact head match scores best,
    a last-digit match (dropped leading digit) close behind, no head is
    neutral, a contradicting head costs.
    """
    m = len(qs)
    if not want or m >= want:
        return list(range(1, m + 1))
    evid = []
    for q in qs:
        h = HEAD_EVID.match(q["text"].strip())
        evid.append(int(h.group(1)) if h else None)

    def score(e, n):
        if e is None:
            return 0
        if e == n:
            return 3
        if e < 10 <= n and n % 10 == e % 10:
            return 2       # leading digit lost
        return -3

    NEG = float("-inf")
    dp = [[NEG] * (want + 1) for _ in range(m + 1)]
    back = [[0] * (want + 1) for _ in range(m + 1)]
    dp[0] = [0] * (want + 1)
    for i in range(1, m + 1):
        for n in range(1, want + 1):
            best, arg = NEG, 0
            for p in range(i - 1, n):
                if dp[i - 1][p] > best:
                    best, arg = dp[i - 1][p], p
            if best > NEG:
                dp[i][n] = best + score(evid[i - 1], n)
                back[i][n] = arg
    # best end
    endn = max(range(m, want + 1), key=lambda n: dp[m][n])
    nums = []
    n = endn
    for i in range(m, 0, -1):
        nums.append(n)
        n = back[i][n]
    return nums[::-1]


HEAD_NUM = re.compile(r"^(\d{1,2})\s+\S")


def recover_short_answers(qs, want):
    """Split segments that contain a numbered head after their question text.

    Only applied when the paper is short of questions, and only at heads whose
    number is consistent with the position being created.
    """
    changed = True
    while changed and len(qs) < want:
        changed = False
        for i, q in enumerate(qs):
            lines = q["text"].split("\n")
            # look for a numbered head strictly inside the segment
            for j in range(1, len(lines)):
                m = HEAD_NUM.match(lines[j].strip())
                if not m:
                    continue
                n = int(m.group(1))
                # the head should announce the (i+2)-th question at this point
                if n == i + 2 or (i + 2 >= 10 and n == (i + 2) % 10
                                  and n >= 4):
                    pass
                else:
                    continue
                if True:
                    first = {"pages": q["pages"], "options": [],
                             "text": "\n".join(lines[:j]).strip()}
                    second = {"pages": q["pages"],
                              "options": q.get("options", []),
                              "text": "\n".join(lines[j:]).strip()}
                    if len(first["text"]) > 30 and len(second["text"]) > 30:
                        qs[i:i + 1] = [first, second]
                        changed = True
                        break
            if changed:
                break
    return qs


# ---------------------------------------------------------------- checks

def validate(qs, want, label):
    errs = []
    if len(qs) != want:
        errs.append(f"切出 {len(qs)} 题,答案键有 {want} 题")
    for q in qs:
        a = q.get("answer")
        if not a:
            errs.append(f"q{q['q']} 没有答案")
            continue
        if re.fullmatch(r"[A-H]", a):
            # the key's letter must be offered by the question
            body = q["text"]
            if not (re.search(rf"^(?:\*\*)?{a}(?:\*\*)?[\s.):]", body, re.M)
                    or a in q.get("options", [])
                    or re.search(rf"\\(?:textbf|mathbf|bf)\s*{{\s*{a}\s*}}", body)):
                errs.append(f"q{q['q']} 答案 {a} 不在选项里")
        if len(q["text"]) < 40:
            errs.append(f"q{q['q']} 题干只有 {len(q['text'])} 字符")
        # a question whose options name figures must actually carry them,
        # or the reader is told to look at a picture that isn't there
        if PICOPT.search(q["text"]) and not IMGTAG.search(q["text"]) \
                and q["exam"] != "TMUA":
            errs.append(f"q{q['q']} 说'见图'但没有插图")
    return errs


def main(only=None):
    all_qs, report = [], []
    for year in ("2016", "2017", "2018", "2019", "2020", "2021", "2022",
                 "2023", "specimen"):
        if only and only != "TMUA":
            break
        for paper in ("1", "2"):
            qs, want = split_tmua(year, paper)
            errs = validate(qs, want, f"TMUA {year} P{paper}")
            report.append((f"TMUA {year} P{paper}", len(qs), want, errs))
            all_qs += qs
    for exam, base, rng in (("TSA", "TARA/TSA_section1/papers", range(2008, 2024)),
                            ("BMAT", "TARA/BMAT_section1/papers", range(2003, 2024))):
        if only and only != exam and only != "TARA":
            continue
        for y in rng:
            sub = f"{base}/{exam}-{y}-S1"
            if not os.path.isdir(f"{ROOT}/{sub}"):
                continue
            qs, want = split_mcq(exam, str(y), sub)
            errs = validate(qs, want, f"{exam} {y}")
            report.append((f"{exam} {y}", len(qs), want, errs))
            all_qs += qs

    json.dump(all_qs, open("questions_adm.json", "w"), ensure_ascii=False, indent=1)
    print(f"{'卷':<18}{'切出':>5}{'应有':>5}  问题")
    perfect = 0
    for label, n, want, errs in report:
        flag = "" if not errs else f"  {len(errs)} 处: " + "; ".join(errs[:3])
        if not errs:
            perfect += 1
        print(f"{label:<18}{n:>5}{want:>5}{flag}")
    print(f"\n{perfect}/{len(report)} 份卷零问题;共 {len(all_qs)} 题 -> questions_adm.json")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
