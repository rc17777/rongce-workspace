#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

desktop = r'C:\Users\scrccpa\Desktop'
for item in os.listdir(desktop):
    print(repr(item))
