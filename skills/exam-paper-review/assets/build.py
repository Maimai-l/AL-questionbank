"""编译练习卷：题目册与答案册各一个 PDF。
用法：python3 build.py [源文件.typ] [字体目录]
"""
import sys, typst

src = sys.argv[1] if len(sys.argv) > 1 else "练习卷样例.typ"
fonts = [sys.argv[2]] if len(sys.argv) > 2 else []
stem = src.rsplit(".", 1)[0]

typst.compile(src, output=f"{stem}_题目.pdf", font_paths=fonts, sys_inputs={"mode": "paper"})
typst.compile(src, output=f"{stem}_答案.pdf", font_paths=fonts, sys_inputs={"mode": "ms"})
print(f"已生成 {stem}_题目.pdf 与 {stem}_答案.pdf")
