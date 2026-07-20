#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RAG Server wrapper - starts on port 5001 (5000 occupied by Neo4j)"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r'D:\openclaw-workspace')

with open(r'C:\Users\scrccpa\.openclaw\workspace\scripts\rag_server.py', 'r', encoding='utf-8') as f:
    code = f.read()
code = code.replace("port=5000", "port=5001")
exec(code, {'__name__': '__main__'})
