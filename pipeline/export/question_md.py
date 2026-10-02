"""Markdown for one CAIE question in an export: whole, or only some of its parts.

Shared by the chapter, code-question and curated-paper exports. It reads the
columns part_data (pipeline/text/split_parts.py), q_quality and ms_quality.

- A question whose text cannot stand in for its crop (q_quality missing,
  garbled or partial, 62 questions in 2026-09) gets a note sending the reader
  to the image instead of the broken text.
- parts_md() gives the stem, then for each chosen part its letter's intro
  (once), its own text, marks and task, and its own rows of the mark scheme.
  When the question's text could not be cut at its labels (text_split false)
  the whole text is given with the chosen labels named.
"""
import json

IMAGE_ONLY = ("missing", "garbled", "partial")
NO_TEXT = "_题干文本不可用(识别质量:{q}),请以原题图为准。_"
NO_MS = "_暂无可用评分细则文本。_"


def keys(row):
    return row.keys() if hasattr(row, "keys") else row


def text_usable(row):
    return "q_quality" not in keys(row) or row["q_quality"] not in IMAGE_ONLY


def question_text(row):
    """The question's text, or a note pointing to the image."""
    t = row["question_latex"] or row["question_text"]
    if not t or not text_usable(row):
        return NO_TEXT.format(q=row["q_quality"] if "q_quality" in keys(row) else "missing")
    return t.strip()


def scheme_text(row):
    return (row["ms_latex"] or row["ms_text"] or NO_MS).strip()


def parts_of(row):
    d = row["part_data"] if "part_data" in keys(row) else None
    return json.loads(d) if d else None


def parts_md(row, labels):
    """(question markdown, scheme markdown) for the parts named in labels."""
    d = parts_of(row)
    want = [p for p in (d or {}).get("parts", []) if p["label"] in labels]
    if not d or not want or not text_usable(row):
        return question_text(row), scheme_text(row)
    names = ", ".join(f"({p['label']})" for p in want)
    if not d["text_split"]:
        q = (f"_本题只取小问 {names};题干未能按小问切开,下面是整题。_\n\n"
             + question_text(row))
    else:
        out, seen = [], set()
        if d["stem"]:
            out.append(d["stem"])
        for p in want:
            letter = p["label"].split("(")[0]
            if p["intro"] and letter not in seen:
                out.append(p["intro"])
            seen.add(letter)
            out.append(p["text"])
        q = f"_本题只取小问 {names}。_\n\n" + "\n\n".join(out)
    ms = [p["ms"] for p in want if p["ms"]]
    if len(ms) < len(want):
        ms = [scheme_text(row)]           # a part's rows were not found: the whole scheme
    return q, "\n\n".join(ms)


def labels_on_topic(row, topic):
    """Labels of the parts tagged with topic, [] when none or no part data."""
    d = parts_of(row)
    return [p["label"] for p in (d or {}).get("parts", []) if p.get("topic") == topic]
