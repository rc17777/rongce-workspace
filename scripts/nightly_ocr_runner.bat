@echo off
cd /d "C:\Users\scrccpa\.openclaw\workspace"
C:\Users\scrccpa\miniconda3\envs\paddleocr\python.exe -X utf8 scripts\nightly_ocr.py >> logs\nightly_ocr_stdout.log 2>&1
