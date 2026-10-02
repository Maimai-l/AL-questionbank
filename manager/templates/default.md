---
name: 默认
per_question: [image_with_space, mark_scheme]
documents: []
answers: written_pdf
layout: folder_per_question
filename: "{index:02}_{paper_code}_Q{q}"
answer_filename: answers
manifest: true
summary: false
prompt_file: README.md
---
# {title}

{count} 题，满分 {total_marks} 分，来自 {papers}。

## 题目

{question_table}
