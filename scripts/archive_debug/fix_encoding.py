import re
files = [
    'rongce-ocr-agent/ocr_engine.py',
    'rongce-ocr-agent/understanding_engine.py', 
    'rongce-ocr-agent/cross_validator.py',
    'rongce-ocr-agent/agent_api.py',
    'rongce-ocr-agent/self_test.py',
]
old_line = "sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')"
new_block = """try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
except (ValueError, AttributeError):
    pass"""

for f in files:
    with open(f, 'r', encoding='utf-8') as fh:
        content = fh.read()
    if old_line in content:
        content = content.replace(old_line, new_block)
        with open(f, 'w', encoding='utf-8') as fh:
            fh.write(content)
        print(f'Fixed: {f}')
    else:
        print(f'Skipped (already fixed): {f}')
