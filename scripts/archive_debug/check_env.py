import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import importlib

pkgs = [
    ('paddleocr', 'paddleocr'),
    ('paddle', 'paddle'),
    ('requests', 'requests'),
    ('PIL', 'Pillow'),
    ('pdf2image', 'pdf2image'),
    ('fitz', 'PyMuPDF'),
    ('openpyxl', 'openpyxl'),
    ('cv2', 'opencv-python'),
    ('numpy', 'numpy'),
]
for mod, pkg in pkgs:
    try:
        m = importlib.import_module(mod)
        ver = getattr(m, '__version__', '?')
        print(f"{pkg}: OK (v{ver})")
    except:
        print(f"{pkg}: MISSING")

# Check conda envs
import subprocess
result = subprocess.run(['conda', 'env', 'list'], capture_output=True, text=True)
print('\n--- conda envs ---')
print(result.stdout[:1000])
