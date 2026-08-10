# -*- coding: utf-8 -*-
"""Fix Chinese quotes in part1 - replace ASCII \" used as em-dash markers"""
from pathlib import Path
p = Path(r'C:\Users\scrccpa\.openclaw\workspace\scripts\rongce_v5_part1.py')
text = p.read_text('utf-8')
# The problematic lines use ASCII " as Chinese emphasis markers inside Python "-delimited strings
# Replace with Unicode escape sequences
text = text.replace('从"有没有"到"对不对"再到"值不值"', "从\u201c有没有\u201d到\u201c对不对\u201d再到\u201c值不值\u201d")
text = text.replace('您关心的不只是"花了多少钱"，更是"效果怎么样"', "您关心的不只是\u201c花了多少钱\u201d，更是\u201c效果怎么样\u201d")
text = text.replace('"花了没有"走向"花得值不值"', "\u201c花了没有\u201d走向\u201c花得值不值\u201d")
p.write_text(text, 'utf-8')
print('Done')
# Verify no more ASCII " inside Chinese strings
import py_compile
py_compile.compile(str(p), doraise=True)
print('Syntax OK')