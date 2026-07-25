# -*- coding: utf-8 -*-
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

path = r'C:\Users\scrccpa\.openclaw\workspace\output\新制度体系'
files = os.listdir(path)
for f in sorted(files):
    print(f)
