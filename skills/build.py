#!/usr/bin/env python3
"""Package the two claude.ai skills kept in this folder as .skill files to upload.

    python3 skills/build.py            exports/exam-bank-pipeline.skill, exports/exam-paper-review.skill

The scripts in skills/shared/ (get_paper.py, strip_watermark.py, qbank.py) go into each
skill's scripts/. Upload the .skill files under claude.ai → Settings → Capabilities → Skills,
replacing the skills of the same name.
"""
import os, re, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from lib import paths  # noqa: E402

SKILLS = ["exam-bank-pipeline", "exam-paper-review"]
SHARED = ["get_paper.py", "strip_watermark.py", "qbank.py"]


def check(folder):
    text = open(os.path.join(folder, "SKILL.md"), encoding="utf-8").read()
    m = re.match(r"---\nname: \"?([\w-]+)\"?\ndescription: (.+?)\n---\n", text, re.S)
    if not m or m.group(1) != os.path.basename(folder):
        sys.exit(f"{folder}/SKILL.md 的开头要有 name 与 description")
    if len(m.group(2)) > 1024:
        sys.exit(f"{folder}: description 超过 1024 字符")


def main():
    os.makedirs(paths.EXPORTS, exist_ok=True)
    for name in SKILLS:
        folder = os.path.join(HERE, name)
        check(folder)
        out = os.path.join(paths.EXPORTS, f"{name}.skill")
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for root, dirs, files in os.walk(folder):
                dirs[:] = [d for d in dirs if d != "__pycache__"]
                for f in files:
                    if f.endswith(".pyc") or f == ".DS_Store":
                        continue
                    full = os.path.join(root, f)
                    z.write(full, os.path.join(name, os.path.relpath(full, folder)))
            for f in SHARED:
                z.write(os.path.join(HERE, "shared", f), os.path.join(name, "scripts", f))
        print(f"{out}  {os.path.getsize(out) // 1024} KB")


if __name__ == "__main__":
    main()
