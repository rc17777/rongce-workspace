"""分析招标文件关键条款"""
import fitz, sys, re
sys.stdout.reconfigure(encoding='utf-8')

path = r"C:\Users\scrccpa\Desktop\招投标审计\5号6号学生宿舍建设项目监理\监理招标文件定稿.pdf"
doc = fitz.open(path)

full_text = []
for pg in range(len(doc)):
    t = doc[pg].get_text()
    if t.strip():
        full_text.append(t.strip())

text = '\n'.join(full_text)
doc.close()

# Extract key sections
sections = {}

# 1. Project scope
m = re.search(r'(1\.1\.\d+.*?1\.2)', text, re.DOTALL)
if m: sections['项目概况'] = m.group(1)[:1500]

# 2. Qualification requirements
m = re.search(r'(1\.4\.\d+.*?投标人资质条件.*?)(?=1\.5)', text, re.DOTALL)
if m: sections['资质要求'] = m.group(1)[:2000]

# 3. Bid evaluation method  
m = re.search(r'(第三章 评标办法.*?)(?=第四章)', text, re.DOTALL)
if m: sections['评标办法'] = m.group(1)[:5000]

# 4. Scoring details
m = re.search(r'(2\.2\.\d+.*?评分标准.*?)(?=2\.3|3\.)', text, re.DOTALL)
if m: sections['评分标准'] = m.group(1)[:3000]

# 5. Financial requirements
m = re.search(r'(财务状况.*?)(?=业绩|信誉|项目)', text, re.DOTALL)
if m: sections['财务要求'] = m.group(1)[:1000]

# 6. Performance requirements  
m = re.search(r'(类似项目业绩.*?)(?=财务状况|信誉|项目|3\.)', text, re.DOTALL)
if m: sections['业绩要求'] = m.group(1)[:1500]

# 7. Personnel requirements 
m = re.search(r'(总监理工程师.*?)(?=其他主要人员|3\.)', text, re.DOTALL)
if m: sections['人员要求'] = m.group(1)[:1500]

# Print
for title, content in sections.items():
    print(f"\n{'='*70}")
    print(f"【{title}】")
    print('='*70)
    print(content[:2000])
    if len(content) > 2000:
        print(f"\n... (truncated, total {len(content)} chars)")
