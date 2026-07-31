"""Start OCR as fully detached process"""
import subprocess, os, sys

script = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\full_ocr_new.py'
log = r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr\ocr_log.txt'

# Kill any existing OCR processes first
subprocess.run(['powershell', '-Command', 
    "Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -match 'full_ocr'} | Stop-Process -Force"],
    capture_output=True)

# Start with DETACHED_PROCESS flag
proc = subprocess.Popen(
    ['python', '-X', 'utf8', script],
    stdout=open(log, 'w', encoding='utf-8'),
    stderr=subprocess.STDOUT,
    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
    cwd=r'C:\Users\scrccpa\.openclaw\workspace\temp_ocr'
)
print(f'OCR started, PID: {proc.pid}')