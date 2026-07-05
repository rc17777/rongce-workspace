import importlib
for m in ['pytesseract', 'pdf2image', 'PIL', 'fitz', 'pymupdf', 'paddleocr', 'easyocr']:
    try:
        importlib.import_module(m)
        print(f"OK: {m}")
    except:
        print(f"MISS: {m}")
