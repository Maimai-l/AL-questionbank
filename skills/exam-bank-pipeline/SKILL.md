---
name: "exam-bank-pipeline"
description: "Use when building, repairing or querying the AL-questionbank question bank."
---

# Question bank pipeline

The question bank's code, documentation and data are all in the public repository **Maimai-l/AL-questionbank**. This skill explains only how to get the repository, how to start working in it, and a few rules that the repository's docs do not collect in one place. For process details, the docs in the repository are authoritative:

| Repository doc | Contents |
|---|---|
| `CLAUDE.md` | Rules for working in the repository: where the data lives, syncing, tests, how to report |
| `docs/status.md` | Current state of the data and open tasks; read this first when taking over |
| `docs/pipeline.md` | The order in which every script runs, and the constraints between them |
| `docs/guide.md` | User guide: installation, syncing, commands, the stable branch |
| `docs/network.md` | Sites that must be reachable, and the allowlist (`docs/allowed-domains.txt`) |
| `docs/data-sync.md` | How the data branch is synced |

## 1. Getting the code and data

```bash
git clone --single-branch --branch main https://github.com/Maimai-l/AL-questionbank.git
cd AL-questionbank
python3 sync.py pull --no-auto       # fetch data/ (a worktree of the data branch, about 1.1 GB)
python3 qb.py stats                  # confirm the data is in place
```

If you only need question text, you do not need the whole repository. Use this skill's `scripts/qbank.py`, which downloads only caie.db (about 65 MB):

```bash
S=$(dirname "$(find / -path '*exam-bank-pipeline/scripts/qbank.py' 2>/dev/null | head -1)")
python3 $S/qbank.py paper 9618_s24_11          # whole paper: question text, marks, mark scheme
python3 $S/qbank.py find --syllabus 9709 --topic 1.7 --text "tangent"
python3 $S/qbank.py chapter --syllabus 9702 --topic 17   # textbook chapters for a syllabus topic
python3 $S/qbank.py chapter 9702 17                      # one chapter as markdown; --save DIR also writes its figures
```

`chapter` downloads only the chapters asked for. The books are 9709_p1, 9709_p23, 9709_p4, 9709_p5, 9231, 9618 and 9702; the 9702 chapters are text only, without figures. Add `--refresh` to download the bank again after it has been updated.

Single files can be downloaded directly from `https://raw.githubusercontent.com/Maimai-l/AL-questionbank/data/<path>`, for example `caie.db`, `papers/9618_s24_qp_11.pdf` or `img9618/…` on the `data` branch.

On a restricted network, allow `github.com` and `*.githubusercontent.com` in the environment's network settings. Fetching new papers also requires the three past-paper sites (see section 3).

## 2. Current state of the bank (2026-11)

```
data/caie.db        6531 questions: 9709 (2070) 9231 (1009) 9618 (970) 9702 (2482), years 2021-2026
data/papers/        question paper and mark scheme PDFs: 1387; all watermarks removed
data/img9709 ...    per-question images (img9702 is physics)
data/books/         107 textbook chapters as markdown (the 26 physics chapters are in books/9702/)
data/practice.html  practice page; textbook.html is the textbook page; concepts/9618/ holds a revision page for each 9618 chapter
```

- The authoritative question text and mark schemes are `question_latex` and `ms_latex` (OCR'd, then checked question by question against the original paper for 9709, 9231 and 9618). `question_text` and `ms_text` are the PDF text layer and serve only as a fallback.
- Printing errors in the original papers have been corrected. The reason for each correction is in the `why` field of its line in `pipeline/text/text_fixes.jsonl`.
- 9618 has a worked solution for each part (`explanation` column; 968 of 970 questions). 9709 and 9231 have no worked solutions (the user's decision).
- 9702 physics (added 2026-11) includes only papers 1, 2, 4 and 5; paper 3, the practical paper, is excluded. It has been OCR'd (question text for 2363 questions and mark schemes for 750 are LaTeX) but not yet checked against the original papers. The remaining question text and mark schemes come from the text layer (`q_quality` partial: subscripts, superscripts and fractions are flattened), and the question images are authoritative. Paper 1 consists of 40 multiple-choice questions, stored with `answer`, `qtype='mcq'` and `options`. The 14 paper 4 questions of 2021 on communication and electronics belong to the 2019-2021 syllabus and have no topic. Topics are assigned by syllabus section (1-25) by `pipeline/tags/physics_topics.py`, using the textbook text and the syllabus; a manual check of 100 questions found 86 correct.
- The admissions tests (TMUA, TSA, BMAT) were archived in 2026-11: their data is on the repository's `archive-admissions` branch and their scripts are in `attic/admissions/`.
- Outstanding work (checking 9702 against the original papers, fixing its formulas that KaTeX cannot render, and so on) is listed in `docs/status.md`.

## 3. Paper sources and watermark removal

A file with the same name can have different contents on each of the three sites. Keep the copy that the splitting scripts can parse:

| Site | Notes |
|---|---|
| `cie.fraft.cn` | Two endpoints: `obj/Common/Fetch/renum` lists files by syllabus, year and series (POST), and `Fetch/redir/<filename>` downloads a file (POST). Some 2025-26 papers use fonts with no Unicode mapping, so their text layer is garbled; a few are laid out on Letter paper |
| `pastpapers.papacambridge.com` | `directories/CAIE/CAIE-pastpapers/upload/<filename>`. Has 9231 and the most recent series. Files are watermarked, and some mark schemes have been rearranged into a different page layout. Some 2021 papers were repackaged with FPDF: every page has the site's logo in the bottom-right corner, and the text layer does not contain the site name |
| `dynamicpapers.com` | `wp-content/uploads/2015/09/<filename>`. A missing file returns a WordPress 500 page, not a 404. In some files (in the bank: 9709 2021-2025 and 9618 2023-2025) every page header carries the site's URL (an Acrobat header, `/Artifact ... BDC ... EMC`) |

- Inside the repository: `pipeline/fetch/fetch_fraft.py` downloads papers on the fraft list that the bank does not have yet, and falls back to papacambridge when the text layer is unreadable. `pipeline/fetch/best_copy.py` runs a trial split on each site's copy and keeps the one whose question count and total marks agree. `pipeline/fetch/strip_watermark.py` removes the papacambridge watermarks (diagonal watermark, banner, QR code, and the logo on FPDF-repackaged papers) and the dynamicpapers header URL. It also deletes watermark objects that are never drawn, links to these sites, and document properties that name them (`--check` only reports).
- Outside the repository: this skill's `scripts/get_paper.py` tries GitHub (`papers/` on the data branch), fraft, papacambridge and dynamicpapers in that order, and checks each file's text layer and paper size. Every file it hands over, whether newly downloaded or already cached, has its watermarks removed. `--source` uses only the sites named, in the order given; `--refresh` ignores files already downloaded and downloads them again:

  ```bash
  python3 $S/get_paper.py 9231_w21_qp_13 9231_w21_ms_13 9231_w21_gt --out papers
  python3 $S/get_paper.py 9618 --years 25 26 --series s --papers 1 2 --gt --out papers
  python3 $S/get_paper.py 9709_s24_qp_52 --source papacambridge fraft --refresh --out papers
  ```

## 4. Required steps when changing data

`data/` is a worktree of the `data` branch, and that branch always has exactly one commit:

```bash
python3 sync.py pull --no-auto                 # before you start
# ... make the changes ...
python3 pipeline/export/build_site.py          # regenerate the page data; this must run last
python3 sync.py push -m "<message>"            # replaces the single commit on the data branch
```

- Never commit files under `data/`, `raw/` or `exports/` to `main`. Resolve every path through `lib/paths.py`.
- Every correction to question text or mark schemes goes through `pipeline/text/fix_batches.py` into `text_fixes.jsonl`. That file is committed to `main` with the code, so the corrections can be replayed. Do not edit the database directly.
- After changing `manager/` or `manage.py`, run `python3 -m unittest discover tests`.

## 5. Conventions for subagent batches

Review, tag re-checks, worked solutions and revision pages all follow the same pattern. The script's `plan` command writes batch files. Each batch goes to one subagent, which writes only its own result file (or only returns JSON). The script's `verify` or `check` command validates the results, and the main process writes them all with `apply`.

- Agents never modify the database or shared files directly. A faulty batch can then be rolled back on its own, and the validation numbers show which batch caused a problem.
- Use 20 questions per batch. An experiment on 40 physics questions (2026-11, Haiku subagents, batches of 5, 10, 20 and 40) found 20 the cheapest per question: smaller batches repeat the fixed prompt cost more often, and larger ones reread a growing context after every image. Quality did not fall with batch size in that sample. The table is in `docs/pipeline.md`.
- Validate results before writing them. Redo any batch that fails; never edit numbers by hand to get past validation.
- After collecting results, spot-check about 5% yourself. Agent errors follow patterns, so a sample is enough to find them.

## 6. Invariants

Re-run validation after every change. The numbers show where the remaining problems are:

| Invariant | What a violation means |
|---|---|
| CAIE: total marks on the question paper equal total marks in the mark scheme (`totals_agree`) | Some parts were not split out |
| 9702 paper 1: each paper splits into 40 questions, each with an answer letter | A question was lost or split in two, so every later question number is shifted |
| An MCQ answer letter is one of that question's options | OCR dropped the options, or the split ran into the neighbouring question |
| A question that says "see the diagram" has a diagram | The diagram was assigned to the next question |
| OCR page count equals PDF page count | The JSONL was parsed incorrectly |

A wrong question count is more dangerous than a wrong answer: one missing question shifts every later answer by one, while each question looks fine on its own.

## 7. references/

`references/` contains domain knowledge gathered early in the project. Its paths use the old directory layout (`qb/...`); where they differ, the repository's current layout is correct:

| File | When to use it |
|---|---|
| `caie-longform.md` | Splitting and mark scheme format for 9709/9231/9618 |
| `ocr-damage.md` | Types of damage and how to fix them, when a validation report looks abnormal or a page's content is plainly wrong |
| `db-contract.md` | The contract between the schema, the pages and the exports (newer columns are documented in the repository's `lib/db.py` and `docs/`) |

## scripts/

| Script | Purpose |
|---|---|
| `get_paper.py` | Downloads question papers, mark schemes and grade thresholds, trying GitHub, fraft, papacambridge and dynamicpapers in turn (`--source` sets which sites and in what order); every file it hands over has its watermarks removed |
| `strip_watermark.py` | Removes papacambridge and dynamicpapers watermarks (requires PyMuPDF); `--check` only reports |
| `qbank.py` | Gets question text and mark schemes by paper, question or topic from caie.db alone, without the repository; `chapter` lists textbook chapters by topic and prints or saves one chapter |