#!/usr/bin/env python3
"""
Wrapper: scripts/token_tracker.py → scripts/guards/token_tracker.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'guards'))
os.chdir(os.path.dirname(__file__))

from guards.token_tracker import main as guards_main
sys.argv = [os.path.join(os.path.dirname(__file__), 'guards', 'token_tracker.py')] + sys.argv[1:]
guards_main()
