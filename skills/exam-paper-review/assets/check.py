"""逐题测量作答空间：每个带 [n] 的题干下方，到同页下一个题干或版心底边的距离，单位毫米。
数值远小于设定值，说明题干与作答区被分页拆开，需要调整行数或让该题从新页开始。
用法：python3 check.py 题目册.pdf [版心底边距页底毫米数，默认 22]
"""
import subprocess, re, sys, html
pdf=sys.argv[1]; bottom=float(sys.argv[2]) if len(sys.argv)>2 else 22
xml=subprocess.run(['pdftotext','-bbox-layout',pdf,'-'],capture_output=True,text=True).stdout
pt2mm=25.4/72
for pi,page in enumerate(re.findall(r'<page (.*?)</page>',xml,re.S),1):
    H=float(re.search(r'height="([\d.]+)"',page).group(1))
    lines=[]
    for ln in re.findall(r'<line (.*?)</line>',page,re.S):
        y=float(re.search(r'yMax="([\d.]+)"',ln).group(1))
        words=' '.join(html.unescape(w) for w in re.findall(r'>([^<]*)</word>',ln))
        lines.append((y,words))
    lines.sort()
    prompts=[(y,w) for y,w in lines if re.search(r'\[\d+\]\s*$',w)]
    for i,(y,w) in enumerate(prompts):
        nxt=prompts[i+1][0]-12 if i+1<len(prompts) else H-bottom/pt2mm
        print(f'p{pi}  {(nxt-y)*pt2mm:6.1f} mm  {w[:60]}')
