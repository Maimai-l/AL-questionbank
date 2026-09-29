#!/usr/bin/env python3
"""Download the TMUA and TARA question banks from UAT-UK's own site.

    python3 manifest.py <out_dir>

Everything here comes from one origin — uat-wp.s3.eu-west-2.amazonaws.com, the
file store behind esat-tmua.ac.uk (UAT-UK, who run both tests). No mirrors, no
tutoring-site re-uploads, so the answer keys are the official ones.

Two banks, and why each is shaped the way it is:

TMUA   The test moved to Pearson (computer-based) in 2024 with, in UAT-UK's own
       words, "content specification and question style unchanged" — so the
       2016-2023 paper-based archive plus the early specimen IS the bank.
       Every paper has official worked answers, not just keys.

TARA   First sat in October 2025; no past papers exist. UAT-UK's preparation
       page states its Critical Thinking and Problem Solving components "share
       a common history with BMAT Section 1 and the TSA", and hosts those
       archives as TARA preparation — TSA Section 1 2008-2023 and BMAT
       Section 1 2003-2023, keys included.

Re-runnable: files already on disk with plausible size are skipped.
"""
import os, sys, time

try:
    import requests
except ImportError:
    sys.exit("需要 requests:  pip install requests")

S3 = "https://uat-wp.s3.eu-west-2.amazonaws.com/wp-content/uploads"

TMUA = {
    # year: (p1, p1_worked, p2, p2_worked, keys) — upload-timestamp path parts
    "2016": ("2024/05/07125112", "2024/05/07125113", "2024/05/07125102",
             "2024/05/07125106", "2024/05/07125113"),
    "2017": ("2024/05/07125230", "2024/05/07125231", "2024/05/07125224",
             "2024/05/07125228", "2024/05/07125232"),
    "2018": ("2024/05/07125407", "2024/05/07125413", "2024/05/07125404",
             "2024/05/07125406", "2024/05/07125413"),
    "2019": ("2024/05/07140825", "2024/05/07140826", "2024/05/07140823",
             "2024/05/07140824", "2024/05/07140827"),
    "2020": ("2024/05/07140953", "2024/05/07140955", "2024/05/07140951",
             "2024/05/07140952", "2024/05/07140956"),
    "2021": ("2024/05/07141119", "2024/05/07141121", "2024/05/07141117",
             "2024/05/07141118", "2024/05/07141122"),
    "2022": ("2024/05/07141241", "2024/06/04105226", "2024/05/07141239",
             "2024/06/04105227", "2024/05/07141242"),
    "2023": ("2024/04/30144109", "2024/06/04105227", "2024/04/30144111",
             "2024/06/04105226", "2024/04/30144123"),
}
TMUA_SPECIMEN = ("2024/05/07141417", "2024/05/07141418", "2024/05/07141413",
                 "2024/05/07141415", "2024/05/07141414")

TSA = {   # year: (question paper, answer key)
    "2008": ("2026/06/01172310", "2026/06/01172307"),
    "2009": ("2026/06/01172315", "2026/06/01172311"),
    "2010": ("2026/06/01172318", "2026/06/01172317"),
    "2011": ("2026/06/01172322", "2026/06/01172320"),
    "2012": ("2026/06/01172326", "2026/06/01172323"),
    "2013": ("2026/06/01172331", "2026/06/01172328"),
    "2014": ("2026/06/01172341", "2026/06/01172333"),
    "2015": ("2026/06/01154311", "2026/06/01154305"),
    "2016": ("2026/06/01154322", "2026/06/01154313"),
    "2017": ("2026/06/01154327", "2026/06/01154324"),
    "2018": ("2026/06/01154334", "2026/06/01154329"),
    "2019": ("2026/06/01154343", "2026/06/01154336"),
    "2020": ("2026/06/01154218", "2026/06/01154203"),
    "2021": ("2026/06/01154225", "2026/06/01154220"),
    "2022": ("2026/06/01154234", "2026/06/01154228"),
    "2023": ("2026/06/01154243", "2026/06/01154237"),
}
TSA_EXTRA = [("TSA/explained/TSA-2020-Section-1-Explained-Answers.pdf",
              "2026/06/01154212", "TSA-2020-Section-1-Explained-Answers.pdf")]

BMAT = {  # year: (question paper, answer key)
    "2003": ("2025/08/06104328", "2025/08/06104327"),
    "2004": ("2025/08/06104330", "2025/08/06104329"),
    "2005": ("2025/08/06104332", "2025/08/06104331"),
    "2006": ("2025/08/06104335", "2025/08/06104333"),
    "2007": ("2025/08/06104337", "2025/08/06104336"),
    "2008": ("2025/08/06104340", "2025/08/06104338"),
    "2009": ("2025/08/06104342", "2025/08/06104341"),
    "2010": ("2025/08/06104346", "2025/08/06104343"),
    "2011": ("2025/08/06104349", "2025/08/06104347"),
    "2012": ("2025/08/06104352", "2025/08/06104350"),
    "2013": ("2025/08/06104355", "2025/08/06104353"),
    "2014": ("2025/08/06104358", "2025/08/06104356"),
    "2015": ("2025/08/06104400", "2025/08/06104359"),
    "2016": ("2025/08/06104405", "2025/08/06104402"),
    "2017": ("2025/08/06104407", "2025/08/06104406"),
    "2018": ("2025/08/06104301", "2025/08/06104259"),
    "2019": ("2025/08/06104306", "2025/08/06104303"),
    "2020": ("2025/08/06104312", "2025/08/06104308"),
    "2021": ("2025/08/06104316", "2025/08/06104313"),
    "2022": ("2025/08/06104321", "2025/08/06104317"),
    "2023": ("2025/08/06104326", "2025/08/06104323"),
}

TARA_DOCS = [
    ("TARA/docs/TARA_Question_Guide_June2025.pdf",
     "2025/06/24172250", "TARA_Question_Guide_June2025.pdf"),
    ("TARA/docs/TARA_Content_Specification_April2025.pdf",
     "2025/04/30103001", "TARA_Content_Specification_April2025.pdf"),
]


def jobs():
    out = []
    for y, (p1, w1, p2, w2, k) in TMUA.items():
        out += [
            (f"TMUA/papers/TMUA-{y}-paper-1.pdf", p1, f"TMUA-{y}-paper-1.pdf"),
            (f"TMUA/worked_answers/TMUA-{y}-paper-1-worked-answers.pdf", w1,
             f"TMUA-{y}-paper-1-worked-answers.pdf"),
            (f"TMUA/papers/TMUA-{y}-paper-2.pdf", p2, f"TMUA-{y}-paper-2.pdf"),
            (f"TMUA/worked_answers/TMUA-{y}-paper-2-worked-answers.pdf", w2,
             f"TMUA-{y}-paper-2-worked-answers.pdf"),
            (f"TMUA/answer_keys/TMUA-{y}-answer-keys.pdf", k,
             f"TMUA-{y}-answer-keys.pdf"),
        ]
    p1, w1, p2, w2, k = TMUA_SPECIMEN
    out += [
        ("TMUA/papers/TMUA-specimen-paper-1.pdf", p1, "TMUA-early-specimen-paper-1.pdf"),
        ("TMUA/worked_answers/TMUA-specimen-paper-1-worked-answers.pdf", w1,
         "TMUA-early-specimen-paper-1-worked-answers.pdf"),
        ("TMUA/papers/TMUA-specimen-paper-2.pdf", p2, "TMUA-early-specimen-paper-2.pdf"),
        ("TMUA/worked_answers/TMUA-specimen-paper-2-worked-answers.pdf", w2,
         "TMUA-early-specimen-paper-2-worked-answers.pdf"),
        ("TMUA/answer_keys/TMUA-specimen-answer-keys.pdf", k,
         "TMUA-early-specimen-paper-answer-keys.pdf"),
    ]
    for y, (q, k) in TSA.items():
        out += [
            (f"TARA/TSA_section1/papers/TSA-{y}-S1.pdf", q,
             f"TSA-{y}-Section-1-Question-Paper.pdf"),
            (f"TARA/TSA_section1/answer_keys/TSA-{y}-S1-key.pdf", k,
             f"TSA-{y}-Section-1-Answer-Key.pdf"),
        ]
    for y, (q, k) in BMAT.items():
        out += [
            (f"TARA/BMAT_section1/papers/BMAT-{y}-S1.pdf", q,
             f"BMAT-{y}-Section-1-Question-Paper.pdf"),
            (f"TARA/BMAT_section1/answer_keys/BMAT-{y}-S1-key.pdf", k,
             f"BMAT-{y}-Section-1-Answer-Key.pdf"),
        ]
    out += TSA_EXTRA + TARA_DOCS
    return out


def main(root):
    todo = jobs()
    print(f"{len(todo)} 个文件")
    ok = fail = skip = 0
    for rel, stamp, fname in todo:
        dst = os.path.join(root, rel)
        if os.path.exists(dst) and os.path.getsize(dst) > 10240:
            skip += 1
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        url = f"{S3}/{stamp}/{fname}"
        for a in range(3):
            try:
                r = requests.get(url, timeout=120)
                if r.status_code == 200 and r.content[:4] == b"%PDF":
                    open(dst, "wb").write(r.content)
                    ok += 1
                    print(f"  OK  {rel}  {len(r.content)//1024} KB", flush=True)
                    break
                print(f"  !!  {rel}  HTTP {r.status_code} "
                      f"{'非PDF' if r.status_code == 200 else ''}", flush=True)
            except Exception as e:
                print(f"  !!  {rel}  {type(e).__name__}", flush=True)
            time.sleep(3 * (a + 1))
        else:
            fail += 1
    print(f"\n下载 {ok},跳过 {skip},失败 {fail}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "bank")
