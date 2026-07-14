import sys
sys.stdout.reconfigure(encoding='utf-8')

filepath = r"C:\Users\scrccpa\Desktop\原文.doc"
print(f"Reading: {filepath}")

# .doc format - try using textract or olefile
try:
    # First try to extract text via antiword-like approach
    import olefile
    ole = olefile.OleFileIO(filepath)
    print("OLE streams:", ole.listdir())
    
    # Try to read WordDocument stream
    if ole.exists('WordDocument'):
        data = ole.openstream('WordDocument').read()
        # Try to extract readable text from binary
        # UTF-16LE text extraction from binary
        text = data.decode('utf-16-le', errors='replace')
        # Filter to printable characters
        import re
        text = re.sub(r'[^\u4e00-\u9fff\u3000-\u303f\uff00-\uffefa-zA-Z0-9\s\.\,\;\:\!\?\-\+\=\@\#\$\%\^\&\*\(\)\[\]\{\}\<\>\/\\\|~\`\'\"\n\r\t]', '', text)
        if len(text) > 100:
            print("--- Extracted from binary ---")
            print(text[:10000])
    
    # Also try 1Table or 0Table
    for stream in ['1Table', '0Table']:
        if ole.exists(stream):
            print(f"\n--- {stream} ---")
            data = ole.openstream(stream).read()
            text = data.decode('utf-16-le', errors='replace')
            text = re.sub(r'[^\u4e00-\u9fff\u3000-\u303f\uff00-\uffefa-zA-Z0-9\s\.\,\;\:\!\?\-\+\=\@\#\$\%\^\&\*\(\)\[\]\{\}\<\>\/\\\|~\`\'\"\n\r\t]', '', text)
            if len(text) > 50:
                print(text[:5000])
    
    ole.close()
except ImportError:
    print("olefile not available, trying raw read...")
    with open(filepath, 'rb') as f:
        data = f.read()
    # Try UTF-16LE text extraction
    text = data.decode('utf-16-le', errors='replace')
    import re
    text = re.sub(r'[^\u4e00-\u9fff\u3000-\u303f\uff00-\uffefa-zA-Z0-9\s\.\,\;\:\!\?\-\+\=\@\#\$\%\^\&\*\(\)\[\]\{\}\<\>\/\\\|~\`\'\"\n\r\t]', '', text)
    if len(text) > 100:
        print("--- Raw text ---")
        print(text[:5000])
