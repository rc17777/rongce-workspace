"""Test pygwalker - minimal approach with to_html."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
import numpy as np

np.random.seed(42)
n = 50  # Smaller dataset

data = {
    '项目名称': [f'项目-{i:03d}' for i in range(n)],
    '业务类别': np.random.choice(['预算编制', '工程结算', '绩效评价', '经责审计', '资产清查', '专项债'], n),
    '预算金额_万元': np.random.uniform(10, 500, n).round(1),
    '偏差率_%': np.abs(np.random.normal(5, 15, n)).round(1),
    '项目年份': np.random.choice([2023, 2024, 2025], n),
    '客户区域': np.random.choice(['成都', '绵阳', '德阳', '宜宾', '南充', '泸州'], n),
}
data['结算金额_万元'] = data['预算金额_万元'] * (1 + data['偏差率_%'] / 100)
df = pd.DataFrame(data)
print(f"Dataset: {len(df)} rows")

html_path = r'D:\openclaw-workspace\test_tools\output\audit_pygwalker.html'

# Try the to_html approach first
try:
    import pygwalker as pyg
    print(f"pygwalker version: {pyg.__version__}")
    
    # Try to_html
    html = pyg.to_html(df)
    print(f"to_html returned {type(html).__name__}, length: {len(html) if isinstance(html, str) else 'N/A'}")
    if isinstance(html, str):
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"Saved: {html_path}")
except Exception as e:
    print(f"to_html failed: {e}")
    
    # Fallback: try walk
    try:
        print("Trying walk()...")
        html = pyg.walk(df, spec={})
        if isinstance(html, str):
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"Saved via walk(): {html_path}")
        else:
            print(f"walk returned: {type(html).__name__}")
    except Exception as e2:
        print(f"walk failed: {e2}")
