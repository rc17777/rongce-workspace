# PDF merger - combines individual page PDFs into one brochure
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

output_dir = r'C:\Users\scrccpa\.openclaw\workspace\huashu-demo\output'

# Use pypdf (pure Python, no deps) or PyPDF2
try:
    from pypdf import PdfWriter, PdfReader
    print('Using pypdf')
except ImportError:
    try:
        from PyPDF2 import PdfWriter, PdfReader
        print('Using PyPDF2')
    except ImportError:
        print('Installing pypdf...')
        import subprocess
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pypdf', '-q'])
        from pypdf import PdfWriter, PdfReader

writer = PdfWriter()
pages = sorted([f for f in os.listdir(output_dir) if f.startswith('page-') and f.endswith('.pdf')])

for page_file in pages:
    path = os.path.join(output_dir, page_file)
    reader = PdfReader(path)
    writer.add_page(reader.pages[0])
    print(f'  + {page_file}')

output_path = os.path.join(output_dir, '融策-政府审计宣传册.pdf')
with open(output_path, 'wb') as f:
    writer.write(f)

print(f'\n✅ Merged {len(pages)} pages → {output_path}')
print(f'   Size: {os.path.getsize(output_path) / 1024 / 1024:.1f} MB')
