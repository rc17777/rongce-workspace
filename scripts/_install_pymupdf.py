"""Install PyMuPDF and extract pages"""
import subprocess
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Install where the current Python can find it
result = subprocess.run(
    [sys.executable, '-m', 'pip', 'install', '--target', 
     r'C:\Users\scrccpa\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages',
     'PyMuPDF'],
    capture_output=True, text=True, timeout=120
)
print(result.stdout[-500:])
print(result.stderr[-500:])
print(f'Exit code: {result.returncode}')