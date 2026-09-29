#!/usr/bin/env python3
"""Repair character-level encoding damage.

Two unrelated sources of damage:

* `pdftotext` emits Symbol-font glyphs as Private Use Area codepoints — '=' as
  U+F03D, '+' as U+F02B and so on. Subtracting 0xF000 recovers the character,
  which is why maths mark schemes looked symbol-free. It also emits NUL/SOH
  where a ligature or a math delimiter stood.
* The vision model occasionally hallucinates a character from an unrelated
  script — Hangul, Katakana, Tibetan, Oriya — into otherwise clean output.
  Nothing in a Cambridge maths or CS paper is written in those scripts, so any
  occurrence is damage.

Greek is deliberately *not* suspect: α, θ, π, λ are ordinary maths.
"""
import re, sqlite3, sys

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))          # 项目根目录
from lib import paths

# Symbol font: PUA F020-F0FF mirrors the font's own 0x20-0xFF slots
PUA = re.compile(r"[-]")
CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")

# scripts that cannot legitimately appear in a CAIE English-language paper
SUSPECT = re.compile(
    "[ऀ-෿"      # Devanagari .. Malayalam
    "฀-࿿"       # Thai, Lao, Tibetan
    "ᄀ-ᇿ"       # Hangul Jamo
    "　-ヿ"       # CJK punctuation, Kana
    "㄰-㆏"       # Hangul compatibility
    "一-鿿"       # CJK ideographs
    "ꀀ-꓏"       # Yi
    "가-힯"       # Hangul syllables
    "豈-﫿"       # CJK compatibility
    "︰-﹏"       # CJK compatibility forms
    "�"              # replacement character
    "▀-▟"       # block elements — OCR noise, never real content
    "Ѐ-ӿ"       # Cyrillic
    "֐-ۿ"       # Hebrew, Arabic
    "]")

# Symbol-font slots that do not map straight back to ASCII
SYMBOL_EXTRA = {
    0xF0B4: "×", 0xF0B8: "÷", 0xF0B1: "±", 0xF0A3: "≤",
    0xF0B3: "≥", 0xF0B9: "≠", 0xF0BB: "≈", 0xF0D6: "√",
    0xF0D0: "⊗", 0xF0F2: "∫", 0xF0E5: "∑", 0xF0D7: "⋅",
    0xF0AE: "→", 0xF0DE: "⇒", 0xF0DB: "⇔", 0xF0A5: "∞",
    0xF061: "α", 0xF062: "β", 0xF067: "γ", 0xF064: "δ",
    0xF071: "θ", 0xF06C: "λ", 0xF06D: "μ", 0xF070: "π",
    0xF073: "σ", 0xF074: "τ", 0xF066: "φ", 0xF077: "ω",
    0xF044: "Δ", 0xF053: "Σ", 0xF057: "Ω",
}


# pdftotext occasionally resolves an embedded maths font through the wrong
# encoding table and lands in an Indic or Thai block: '=' comes out as
# Malayalam vowel sign AU, the superscript 2 as Oriya SHA. The glyphs are
# stable per font, so a lookup recovers them.
GLYPH = {
    "ൌ": "=", "൅": "+", "ଶ": "²", "ฬ": "|",
    "ോ": "-", "ଷ": "³", "ฯ": "|",
}
GLYPH_RE = re.compile("[" + "".join(GLYPH) + "]")


def fix_glyphs(text):
    return GLYPH_RE.sub(lambda m: GLYPH[m.group(0)], text)


def fix_pua(text):
    def sub(m):
        o = ord(m.group(0))
        if o in SYMBOL_EXTRA:
            return SYMBOL_EXTRA[o]
        low = o - 0xF000
        # the printable ASCII slots map straight through
        if 0x20 <= low <= 0x7e:
            return chr(low)
        return " "
    return PUA.sub(sub, text)


def clean(text):
    if not text:
        return text, 0
    before = text
    text = fix_pua(text)
    text = fix_glyphs(text)
    text = CTRL.sub(" ", text)
    text = re.sub(r"[ \t]{3,}", "  ", text)
    return text, int(text != before)


def main(dbpath):
    con = sqlite3.connect(dbpath)
    con.row_factory = sqlite3.Row
    fields = ("question_text", "ms_text", "question_latex", "ms_latex")
    counts = {f: 0 for f in fields}
    suspect = []
    for r in con.execute(f"SELECT id,{','.join(fields)} FROM questions").fetchall():
        upd = {}
        for f in fields:
            new, ch = clean(r[f])
            if ch:
                upd[f] = new
                counts[f] += 1
            if new and SUSPECT.search(new):
                suspect.append((r["id"], f))
        if upd:
            sets = ", ".join(f"{k}=?" for k in upd)
            con.execute(f"UPDATE questions SET {sets} WHERE id=?",
                        list(upd.values()) + [r["id"]])
    con.commit()
    print("修复的字段(PUA 还原 + 控制字符清除):")
    for f, n in counts.items():
        print(f"  {f}: {n}")
    print(f"\n仍含可疑文字(需要按退化处理)的字段: {len(suspect)}")
    seen = {}
    for qid, f in suspect:
        seen.setdefault(f, []).append(qid)
    for f, ids in seen.items():
        print(f"  {f}: {len(ids)}  例: {', '.join(ids[:4])}")
    con.close()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else paths.DB)
