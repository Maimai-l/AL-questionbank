"""CAIE 9702 Physics: paper names.

Component -> paper (the bank keeps 1, 2, 4 and 5; paper 3 is the practical):
  1 = Multiple Choice                        (40 marks, AS content)
  2 = AS Level Structured Questions          (60 marks, AS content)
  4 = A Level Structured Questions           (100 marks, A Level content, AS assumed)
  5 = Planning, Analysis and Evaluation      (30 marks)

Topics come from syllabus.json (pipeline/tags/syllabus.py, sections 1-25 with
their subsections) through topic_model.py, not from keyword tables, so TOPICS is
empty.
"""

COMPONENT_NAME = {
    "1": "Multiple Choice",
    "2": "AS Level Structured Questions",
    "3": "Advanced Practical Skills",
    "4": "A Level Structured Questions",
    "5": "Planning, Analysis and Evaluation",
}

TOPICS = {}
