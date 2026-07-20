import sys
sys.stdout.reconfigure(encoding='utf-8')
try:
    import pypdf
    lib='pypdf'
except ImportError:
    try:
        import PyPDF2 as pypdf
        lib='PyPDF2'
    except ImportError:
        lib=None
print('lib:', lib)
if lib:
    for path in [r'C:\Users\scrccpa\Desktop\新建文件夹\全过程控制合同.pdf',
                 r'C:\Users\scrccpa\Desktop\新建文件夹\全过程控制的招标资料(1).pdf']:
        try:
            r = pypdf.PdfReader(path)
            n = len(r.pages)
            txt = ''
            for i in range(min(5,n)):
                txt += (r.pages[i].extract_text() or '')[:400]
            print(f'--- {path.split(chr(92))[-1]}: {n} pages, text_sample_len={len(txt)}')
            print(txt[:800])
        except Exception as e:
            print(path, 'ERR', e)
