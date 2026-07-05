"""精确提取评标办法核心条款"""
import fitz, sys, re
sys.stdout.reconfigure(encoding='utf-8')

path = r"C:\Users\scrccpa\Desktop\招投标审计\5号6号学生宿舍建设项目监理\监理招标文件定稿.pdf"
doc = fitz.open(path)

full_text = []
for pg in range(len(doc)):
    t = doc[pg].get_text()
    if t.strip():
        full_text.append(f'---PAGE {pg+1}---\n{t.strip()}')

text = '\n'.join(full_text)
doc.close()

# Search for evaluation-related keywords and print surrounding context
keywords = [
    '分值构成', '评分标准', '资信业绩', '监理大纲', '投标报价',
    '评标基准价', '偏差率', '综合评估法', '总分', '权重',
    '类似项目业绩', '项目负责人', '总监理工程师', '其他主要人员',
    '信用评价', '财务状况', '履约评价', '前附表',
    '评审因素', '施工监理', '房屋建筑', '否决投标',
    '形式评审', '资格评审', '响应性评审'
]

for kw in keywords:
    # Find all occurrences
    for m in re.finditer(re.escape(kw), text):
        start = max(0, m.start() - 200)
        end = min(len(text), m.end() + 800)
        ctx = text[start:end]
        # Find page number
        pg_match = re.search(r'---PAGE (\d+)---', ctx[::-1])
        print(f"\n{'='*60}")
        print(f"【{kw}】at offset {m.start()}:")
        print('='*60)
        print(ctx[:1200])
        
        # Only show first 2 occurrences per keyword to avoid flooding
        break  # just first occurrence per keyword

print(f"\n\nTotal PDF text: {len(text):,} chars")
