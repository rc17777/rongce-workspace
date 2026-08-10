import os, sys
sys.stdout.reconfigure(encoding='utf-8')
from PyPDF2 import PdfReader

src_dir = r'C:\Users\scrccpa\Desktop\算法\文献'
out_dir = r'C:\Users\scrccpa\.openclaw\workspace\temp\paper_texts'
os.makedirs(out_dir, exist_ok=True)

# Key papers most likely to contain concrete audit algorithm cases
key_papers = [
    '孤立点分析在审计疑点发现中的应用探讨——基于K-Means聚类算法的Python实现_陈旭.pdf',
    '基于Python的随机森林算法在电网企业人力资源审计中的应用研究_贺雅喆.pdf',
    '基于机器学习—线性回归算法的收入与用户预测模型在审计项目中的应用_杨思祺.pdf',
    'AI机器学习算法在通信运营企业建设项目审计中的应用探索-孙一炜.pdf',
    '关联规则挖掘算法在审计工作中的应用研究-李培培.pdf',
    '关联规则并行算法在社保审计中的应用研究_马康.pdf',
    '数据挖掘算法在行政审计中的应用-陶振海.pdf',
    '频率相似度算法在审计规则库中的应用_谢岳山.pdf',
]

for fname in key_papers:
    fpath = os.path.join(src_dir, fname)
    if not os.path.exists(fpath):
        print(f'NOT FOUND: {fname}')
        continue
    print(f'Extracting: {fname} ({os.path.getsize(fpath)} bytes)...')
    try:
        reader = PdfReader(fpath)
        text = []
        for i, page in enumerate(reader.pages):
            t = page.extract_text()
            if t:
                text.append(t)
        full = '\n\n'.join(text)
        out_name = fname.replace('.pdf', '.txt')
        out_path = os.path.join(out_dir, out_name)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(full)
        print(f'  -> {len(full)} chars, {len(reader.pages)} pages')
    except Exception as e:
        print(f'  ERROR: {e}')

print('\nDone.')
