import re

files = [
    'rongce-ocr-agent/ocr_engine.py',
    'rongce-ocr-agent/understanding_engine.py', 
    'rongce-ocr-agent/cross_validator.py',
    'rongce-ocr-agent/agent_api.py',
    'rongce-ocr-agent/pipeline.py',
    'rongce-ocr-agent/self_test.py',
]

for f in files:
    with open(f, 'r', encoding='utf-8') as fh:
        content = fh.read()
    
    # Remove the try/except block
    content = re.sub(
        r"try:\s+sys\.stdout = io\.TextIOWrapper\(sys\.stdout\.buffer, encoding='utf-8'\)\s+except \(ValueError, AttributeError\):\s+pass\s*",
        "# stdout encoding handled by caller\n",
        content
    )
    content = re.sub(
        r"sys\.stdout = io\.TextIOWrapper\(sys\.stdout\.buffer, encoding='utf-8'\)\s*",
        "# stdout encoding handled by caller\n",
        content
    )
    
    # Also remove unused imports
    content = content.replace(
        "import sys, io, os\n",
        "import sys, os\n"
    )
    
    with open(f, 'w', encoding='utf-8') as fh:
        fh.write(content)
    print(f'Fixed: {f}')
