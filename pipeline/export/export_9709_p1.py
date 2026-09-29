#!/usr/bin/env python3
"""Export 9709 Pure Mathematics 1 as separate text and image ZIPs.

Question images are converted to lossless WebP to reduce their transfer size.
Extract both ZIPs into the same destination folder: questions.md then resolves
images/img9709/*.webp without needing this project.
"""
from __future__ import annotations

import csv
import json
import shutil
import sqlite3
import subprocess
import tempfile
import zipfile
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from lib import paths  # noqa: E402

DATA = Path(paths.DATA)
ASSETS = DATA  # images and books/ live in data/
DB = Path(paths.DB)
OUT = Path(paths.EXPORTS)
PACKAGE = "9709_p1_question_bank"

VIEWER_HTML = """<!doctype html>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>9709 P1 · question viewer</title>
<style>body{margin:0;background:#f6f7f9;color:#1a1d21;font:15px/1.6 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}header{position:sticky;top:0;padding:12px 18px;background:#fff;border-bottom:1px solid #ddd}main{max-width:1000px;margin:20px auto;padding:0 16px}.card{background:#fff;border:1px solid #ddd;border-radius:10px;padding:16px;margin:14px 0}.meta{color:#667085;font-size:13px}.qimg{width:100%;background:#fff;border:1px solid #ddd;border-radius:6px;margin-top:12px}.empty{padding:18px;background:#fff;border-radius:10px}code{background:#eee;padding:2px 4px;border-radius:3px}</style>
<header><strong>9709 Pure Mathematics 1 · 图片题组</strong><span id="count"></span></header><main id="app"></main>
<script src="index.js"></script><script>
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const requested=decodeURIComponent(location.hash.slice(1)).split(',').map(x=>x.trim()).filter(Boolean);
const all=window.QUESTION_INDEX||[], chosen=requested.length?requested.map(id=>all.find(q=>q.id===id)).filter(Boolean):[];
document.querySelector('#count').textContent=chosen.length?` · ${chosen.length} questions`:'';
document.querySelector('#app').innerHTML=chosen.length?chosen.map(q=>`<article class="card"><strong>${esc(q.paper)} · ${esc(q.session)} · Q${q.question}</strong><div class="meta">${esc(q.topic)} · ${esc(q.marks)} marks · <code>${esc(q.id)}</code></div>${q.image?`<img class="qimg" src="images/${encodeURI(q.image)}" alt="${esc(q.id)}">`:''}</article>`).join(''):`<div class="empty">在地址栏追加题号即可展示题组，例如：<br><code>viewer.html#9709_s25_12_q03,9709_w24_11_q05</code><br><br>图片 ZIP 也须解压到同一目录。</div>`;
</script>"""


def main() -> None:
    if not shutil.which("cwebp"):
        raise RuntimeError("cwebp is required for the compact lossless-WebP image export.")
    OUT.mkdir(parents=True, exist_ok=True)
    text_zip = OUT / "9709_p1_questions_text.zip"
    image_zip = OUT / "9709_p1_images_webp.zip"
    temp = Path(tempfile.mkdtemp(prefix="9709-p1-export-"))
    try:
        with sqlite3.connect(DB) as con:
            con.row_factory = sqlite3.Row
            rows = list(con.execute("""
                SELECT id, paper, session, year, month, q, marks, topic, topic_name,
                       question_latex, question_text, ms_latex, ms_text, image
                FROM questions
                WHERE syllabus = '9709' AND component = '1'
                ORDER BY year, month, paper, q, id
            """))
        if not rows:
            raise RuntimeError("No 9709 Paper 1 questions found.")

        lines = ["# CAIE 9709 Pure Mathematics 1", "",
                 f"{len(rows)} questions with mark schemes. Extract the companion image ZIP into this same folder to display images.", ""]
        manifest = []
        index = []
        images: dict[str, Path] = {}
        for row in rows:
            image_link = ""
            if row["image"]:
                source = ASSETS / row["image"]
                webp_rel = Path(row["image"]).with_suffix(".webp").as_posix()
                images[webp_rel] = source
                image_link = f"![Question image](images/{webp_rel})\n\n"
            question = row["question_latex"] or row["question_text"] or "_Question text unavailable._"
            scheme = row["ms_latex"] or row["ms_text"] or "_Mark scheme unavailable._"
            lines += ["---", "", f"## {row['paper']} · {row['session']} · Q{row['q']}", "",
                      f"- ID: `{row['id']}`", f"- Topic: {row['topic_name'] or 'Unclassified'}",
                      f"- Marks: {row['marks'] if row['marks'] is not None else '—'}", "",
                      "### Question", "", image_link + question.strip(), "", "### Mark scheme", "", scheme.strip(), ""]
            manifest.append({"id": row["id"], "paper": row["paper"], "session": row["session"],
                             "question": row["q"], "topic": row["topic_name"] or "",
                             "marks": row["marks"] or "", "image": webp_rel if row["image"] else ""})
            index.append({"id": row["id"], "syllabus": "9709", "component": "1",
                          "paper": row["paper"], "session": row["session"], "year": row["year"],
                          "question": row["q"], "marks": row["marks"], "topic": row["topic_name"] or "",
                          "image": webp_rel if row["image"] else "", "question_text": question,
                          "mark_scheme": scheme})

        question_md = temp / "questions.md"
        question_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        manifest_csv = temp / "manifest.csv"
        with manifest_csv.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(manifest[0]))
            writer.writeheader(); writer.writerows(manifest)
        readme = temp / "README.md"
        readme.write_text(
            "# 9709 Pure Mathematics 1\n\n"
            "1. Extract `9709_p1_questions_text.zip`.\n"
            "2. Extract `9709_p1_images_webp.zip` into the same destination.\n\n"
            "The resulting `questions.md` has only internal relative image links. Images are lossless WebP conversions of the question crops.\n",
            encoding="utf-8")
        index_json = temp / "index.json"
        index_json.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
        index_js = temp / "index.js"
        index_js.write_text("window.QUESTION_INDEX=" + json.dumps(index, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
        viewer = temp / "viewer.html"
        viewer.write_text(VIEWER_HTML, encoding="utf-8")

        with zipfile.ZipFile(text_zip, "w", allowZip64=True) as zf:
            zf.write(question_md, f"{PACKAGE}/questions.md", compress_type=zipfile.ZIP_DEFLATED)
            zf.write(manifest_csv, f"{PACKAGE}/manifest.csv", compress_type=zipfile.ZIP_DEFLATED)
            zf.write(readme, f"{PACKAGE}/README.md", compress_type=zipfile.ZIP_DEFLATED)
            zf.write(index_json, f"{PACKAGE}/index.json", compress_type=zipfile.ZIP_DEFLATED)
            zf.write(index_js, f"{PACKAGE}/index.js", compress_type=zipfile.ZIP_DEFLATED)
            zf.write(viewer, f"{PACKAGE}/viewer.html", compress_type=zipfile.ZIP_DEFLATED)

        converted = 0
        with zipfile.ZipFile(image_zip, "w", allowZip64=True) as zf:
            for rel, source in sorted(images.items()):
                if not source.is_file():
                    raise FileNotFoundError(source)
                webp = temp / Path(rel).name
                subprocess.run(["cwebp", "-quiet", "-lossless", "-m", "6", str(source), "-o", str(webp)], check=True)
                zf.write(webp, f"{PACKAGE}/images/{rel}", compress_type=zipfile.ZIP_STORED)
                converted += 1
        print(f"Questions: {len(rows)}; images: {converted}")
        print(f"Text: {text_zip} ({text_zip.stat().st_size / 1024:.1f} KiB)")
        print(f"Images: {image_zip} ({image_zip.stat().st_size / 1024 / 1024:.1f} MiB)")
    finally:
        shutil.rmtree(temp, ignore_errors=True)


if __name__ == "__main__":
    main()
