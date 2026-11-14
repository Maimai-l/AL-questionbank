---
name: "exam-paper-review"
description: "Use when marking the user's answers to a past exam paper, or when they ask for practice or analysis that follows from that marking."
---

# Past-paper marking and weak-area analysis

Each session is dedicated to one paper (for example, one particular paper of one syllabus), and that paper's data builds up over the session. This skill contains only the process, rules and technical lessons that do not depend on a particular paper. Paper-specific material, such as topic areas and the characteristics of its question types, is worked out during the session from that paper's syllabus; it is not stored in advance.

## Hard rules set by the user

These rules come from the user's explicit requests or corrections, and they override general judgement.

1. **Download the mark scheme before marking.** Never mark from memory. Download only with this skill's `scripts/get_paper.py`; do not write your own download code:

   ```bash
   S=$(dirname "$(find / -path '*exam-paper-review/scripts/get_paper.py' 2>/dev/null | head -1)")
   python3 $S/get_paper.py 9231_w21_qp_13 9231_w21_ms_13 9231_w21_gt --out /home/claude/papers
   # or in bulk for one component: 9231 --years 21 --series w --papers 1 --variants 3 --gt
   ```

   Filenames take the form `9231_w21_ms_13` (syllabus_series and year_type_paper and variant); `gt` is the grade thresholds. Series: m is March, s is May/June, w is October/November.
   The script tries four sources in order, and each output line names the source it used. `--source papacambridge fraft` uses only those two sites, in that order; `--refresh` downloads files again even if they already exist. Every file the script hands over goes through `strip_watermark.py` (requires PyMuPDF), and the output line says so when a watermark was removed:

   | Source | Notes |
   |---|---|
   | github | `papers/` on the data branch of the question bank repository, Maimai-l/AL-questionbank: the best of the three sites' copies, already checked. Has no grade thresholds |
   | fraft | cie.fraft.cn. Some 2025-26 papers have an unreadable text layer or are laid out on Letter paper; the script skips these |
   | papacambridge | pastpapers.papacambridge.com. 2026 files carry a diagonal watermark, a banner and a QR code. Some 2021 files were repackaged with FPDF and have the site's logo in the bottom-right corner of every page. The script removes all of these |
   | dynamicpapers | dynamicpapers.com. In some files every page header carries the site's URL; the script removes it |

   `missing` in the output means none of the four sources has the file. If none of the sources can be reached, the script lists the domains that must be allowed in the network settings (raw.githubusercontent.com, cie.fraft.cn, pastpapers.papacambridge.com, dynamicpapers.com); ask the user to add them.

   **Mark scheme text for each question:** `scripts/qbank.py` gets the question bank (caie.db, about 65 MB, cached after the first download) from the same repository and prints each question's text and mark scheme. The text has been checked question by question against the original paper, except for 9702, whose text is OCR'd but not yet checked:

   ```bash
   python3 $S/qbank.py paper 9231_w21_13            # whole paper: question text, marks, mark scheme
   python3 $S/qbank.py show 9231_w21_13_q05         # one question
   ```

   The PDF is authoritative for marking. Use the qbank text to check marking points quickly, and look at the PDF when a question has a diagram (the output header flags it) or when the text and the PDF disagree.
   Coverage: 9709, 9231, 9618 and 9702 (physics, papers 1, 2, 4 and 5) for 2021-2026. For papers outside this range, use only get_paper.py.

2. **Do not question the user's own sense of how hard a question was or how much effort it took.** If the user says a question took effort, record it as such; never counter with "but you got it right".
3. **Judge effort by the area of crossing-out, not by whether the answer is right.** When the user gets a hard question right, it is often because they looked something up or asked how to do it. Correctness and effort are two independent dimensions and are tallied separately.
4. **The crossing-out index applies only to scans of paper.** Work done on an iPad or another erasable device leaves no crossing-out, so draw no conclusions from it. If you are unsure, ask what the user wrote on.
5. **Papers the user has already marked or corrected are recorded but not marked.** The original answers cannot be told apart from the corrections, so any marking would be inaccurate.
6. **Questions and answers for practice material must be two separate PDFs.**
7. **Size the writing space to the number of steps each question actually needs**; never give every question the same fixed number of lines. Graph areas must be at least as large as in the official paper and, as in the official paper, left blank with no pre-drawn axes.
8. **When the user asks for a practice paper, make the paper.** Do not switch to guided teaching instead.
9. **When the user names a method to remember, record it in their own words**, and give it priority in later questions and explanations.
10. **Write the analysis into the record; do not produce an HTML report** unless the user explicitly asks for one.

## 1. When a set of answers arrives

### 1.1 The four rounds

Issue all calls that do not depend on each other in the same block; Read and Bash calls can be mixed.

| Round | Contents |
|---|---|
| 1 | One bash call: unzip, download the mark scheme and grade thresholds with `get_paper.py`, crop the margins, split each page into halves, and print the per-question mark scheme with `qbank.py paper` (use `pdftotext` for papers outside its range) and the A threshold |
| 2 | One block containing a Read of every half page in parallel, plus renders of the mark scheme pages that contain diagrams |
| 3 | One script: update the record and recompute the checks |
| 4 | SendUserFile |

Never read pages one after another, and never split the Reads across several blocks.

### 1.2 Reading the input

- When unzipping, filenames may contain Chinese characters and spaces, and macOS `._` files may be mixed in:
  ```bash
  i=1; find raw -iname '*.jpg' ! -name '._*' -print0 | sort -z | while IFS= read -r -d '' f; do cp "$f" "p/$(printf '%02d' $i).jpg"; i=$((i+1)); done
  ```
- Identify the syllabus code, paper number and series. If the pages do not show them, ask the user; do not guess.
- Record any subjective notes the user includes (time taken, how they felt, which question was hardest). These notes are input, not claims to be checked.

### 1.3 Cropping and half pages (part of round 1)

```bash
python3 -I - <<'PY'
from PIL import Image, ImageOps
import glob, os
os.makedirs('h', exist_ok=True)
for f in sorted(glob.glob('raw/*.jpg')):
    n = os.path.basename(f)[:2]
    im = Image.open(f).convert('L'); w, h = im.size
    c = ImageOps.autocontrast(im.crop((int(w*.06), int(h*.05), int(w*.95), int(h*.96))), cutoff=1)
    W, H = c.size
    c.crop((0, 0, W, int(H*.55))).save('h/%sa.jpg' % n, quality=85)
    c.crop((0, int(H*.45), W, H)).save('h/%sb.jpg' % n, quality=85)
PY
```

- Crop off the vertical text in the margins, the barcode at the top and the footer. Adjust the crop ratios to the exam board's layout, and check one page after cropping.
- The top and bottom halves each take 55% of the page, overlapping by 10%, so that no line of working is cut in two.
- An A4 scan is within the image size limit. Splitting into halves adds no pixels; it only makes each region fill more of the image, which means fewer re-zooms to read unclear writing. Do not replace it with upscaling or supersampling.
- Skip the cover and any question pages with no handwriting (instruction pages, formula lists). Detecting them automatically by ink coverage is unreliable; list them by page number.
- Do not combine several pages into one image. Combining saves tokens but not rounds, and each page loses resolution in the combined layout.

If a detail is still unclear, crop small regions from the original image, doing all of them in the same block.

**Check crossed-out work first.** A line crossing out writing sits on top of existing ink and has the lowest contrast, and crossed-out work and kept work mean opposite things for marking. If the writing is ambiguous, report that it cannot be made out instead of giving a definite reading.

### 1.4 Marking

- Judge each M, A and B mark against the mark scheme, paying attention to annotations such as FT, AG, OE, CAO, SOI, ISW and WWW.
- Look specifically for work that runs past the edge of the scan, work on additional pages, and crossed-out work.
- List separately every place where you marked leniently, and give the score under strict marking as well.

### 1.5 What to write in the reply

Write in this order, without piling up subheadings:

1. **Score and threshold:** the score, the A threshold for that series, and the margin above it, in one sentence.
2. **Question-by-question explanation:** cover only the parts where marks were lost. For each one, say what the student wrote, which step went wrong, what the correct method is, and which line of the mark scheme applies. Also point out wording that was not standard but did not lose marks.
3. **Weak-area analysis:** three dimensions, each written separately.
   - Topic areas: this paper's score in each topic area, compared with the running totals.
   - Nature of lost marks: the seven labels, defined in `references/记录格式.md`. Distinguish "did not know how" (the concept label) from "knew how but made an error in execution" (the other six labels).
   - Area of crossing-out: rated by hand from 0 to 3, because automatic detection is unreliable. Applies only to scans of paper.
4. **Conclusion:** which of the problems this paper revealed repeat mechanisms already recorded, and which are new.

Points to keep in mind in the analysis:

- When the sample is too small, state how reliable the statistical conclusions are.
- Combine the crossing-out index with the score rate to form four groups. Heavy crossing-out with a low score calls for more practice. Light crossing-out with a low score points to an error of approach or concept, which the student cannot find by checking their own work; it calls for concept work.
- When the user questions why their scores have dropped or whether the papers have got harder, answer with data: regress the score against the order in which questions were attempted, correlate scores with grade thresholds, and compare question features (for example, how often "in terms of" appears) with the score rate on each part.
- Concept errors usually account for less than half of all marks lost so far; the rest were marks the student could have got but did not. The ratio between these two is the main basis for revision priorities; restate it each time a paper is added.

### 1.6 Updating the record

As soon as marking is finished, update the record file and deliver it. The format and how to maintain it are in `references/记录格式.md`, a complete sample is in `references/记录样例.md`, and the maintenance method is in `references/记录方法.md`. The record is the only routine deliverable, and it is what context is rebuilt from after the session is compacted.

Combine all changes into a single script and run it once. Before each replacement, check with `assert old in s` that the original text is present. At the end, the script recomputes the totals, mechanisms and labels from the per-question tables and prints them, so this does not take a separate round. In the script, write replacement strings that contain full-width quotation marks or `−` using `\u` escapes.

## 2. On "careless mistakes"

- Break carelessness down into mechanisms that can be observed. At a minimum, distinguish **transcription errors** (the working is correct, but it goes wrong when copied to the answer line) from **target errors** (the calculation is correct, but the wrong thing is found, a condition is left unused, or the answer is incomplete).
- There is also a separate mechanism: **the question names two objects or two parts, and the answer covers only one.** Typical forms: an answer that only suits (ii) is written under (i), leaving nothing to write under (ii); or an explanation asked for "A and B" covers only A. The fix is to circle each part's qualifying words before starting to write, and then decide which answer goes where. The student usually does know the material involved, so these losses do not go under the concept label.
- Tie each fix to one specific lost mark. Recommend **numerical checks** first: substitute n=1 into a summation formula; substitute the same number into both sides of a partial-fraction identity; multiply an inverse matrix back and see whether the identity results; set a parameter in an expression to 0 or 1; for a sum with changed limits, take f(r)=1 to count the terms. The result of the check must agree with the values given in the question. If the check itself is miscalculated and the error goes unnoticed, record that as a mechanism of lost marks.
- Give only one fix at a time, and add the next only once the student does the first automatically. Record the marks lost to each mechanism on every paper, as evidence of whether a fix is working.

## 3. Output on request

| The user asks for | What to do |
|---|---|
| Topic practice or a targeted practice paper | Make the paper in Typst; see `references/练习材料.md`. Samples and scripts are in `assets/` |
| A list of gaps to fill | Mark each item "concept work" or "practice"; practice items name the specific paper and question number |
| Trends, correlations or other statistics | Answer in the reply, and write the conclusion into the relevant part of the record |
| A summary of key points | Group by syllabus chapter. Each item gives the sentence to remember, how to answer, and the source paper and question number. List items lost repeatedly and items already fixed separately |
| Advice on which papers to do | List candidate questions with `qbank.py find --syllabus … --topic …`, total the marks each paper offers on the weak subsections, and then recommend; do not judge by how new or old a paper is |

Every answer to a question you write yourself must be checked, one by one, with sympy or numerical computation before it is delivered.