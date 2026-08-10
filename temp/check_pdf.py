import os, sys
sys.stdout.reconfigure(encoding='utf-8')

# Check if PyPDF2 is available
try:
    from PyPDF2 import PdfReader
    print("PyPDF2 available")
except:
    print("PyPDF2 NOT available - installing...")

try:
    import pdfplumber
    print("pdfplumber available")
except:
    print("pdfplumber NOT available")
