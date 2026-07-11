#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""找到正确的桌面路径编码"""
import os
import glob

user_profile = os.path.expanduser('~')
desktop = os.path.join(user_profile, 'Desktop')

print(f"Desktop path: {desktop}")
print(f"Desktop exists: {os.path.exists(desktop)}")

if os.path.exists(desktop):
    for item in os.listdir(desktop):
        item_path = os.path.join(desktop, item)
        if os.path.isdir(item_path):
            print(f"  DIR: {item}")
        else:
            print(f"  FILE: {item}")
