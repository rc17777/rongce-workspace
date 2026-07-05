#!/usr/bin/env python3
"""
Wrapper: scripts/deepseek_cost_guard.py → scripts/guards/deepseek_cost_guard.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'guards'))
os.chdir(os.path.dirname(__file__))

from guards.deepseek_cost_guard import main as guards_main
sys.argv = [os.path.join(os.path.dirname(__file__), 'guards', 'deepseek_cost_guard.py')] + sys.argv[1:]
guards_main()
