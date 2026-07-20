# -*- coding: utf-8 -*-
"""Call gpt-5.6-sol to analyze the latest brochure v3 and produce a professional critique."""
import json, os, sys, urllib.request, urllib.error
sys.stdout.reconfigure(encoding='utf-8')

workspace = r'C:\Users\scrccpa\.openclaw\workspace'

# Read theme CSS v3
with open(workspace + r'\huashu-demo\shared\brochure-theme.css', 'r', encoding='utf-8') as f:
    theme_css = f.read()

# Read all slides
slides = {}
slides_dir = workspace + r'\huashu-demo\slides'
for fname in sorted(os.listdir(slides_dir)):
    if fname.endswith('.html'):
        with open(os.path.join(slides_dir, fname), 'r', encoding='utf-8') as f:
            slides[fname] = f.read()

# Build prompt
lines = ['你是一个品牌视觉设计专家，专门为会计师事务所/工程咨询公司做宣传册评审。']
lines.append('')
lines.append('## 背景')
lines.append('这是四川融策会计师事务所/工程咨询公司的政府审计宣传册 v3 版本。')
lines.append('')
lines.append('已完成的改进：')
lines.append('- 创建了共享CSS主题系统（统一色板、字体、间距）')
lines.append('- 封面：深海渐变+几何装饰线+品牌符号（三层同心圆+十字线）')
lines.append('- 金色使用已减量50%，仅保留关键标题和分隔线')
lines.append('- 内容边距放大至80px')
lines.append('- 深蓝背景页加了左上角金色光晕')
lines.append('- 导航栏高度从72px降至56px')
lines.append('- 删除了所有页的footer（保留联系方式页）')
lines.append('- 新增2页过渡页（全屏深蓝+金句分隔业务和数字化板块）')
lines.append('- 字体层级差异化（80px/44px/24px/18px/13px四级）')
lines.append('- 纸纹改用极淡径向渐变')
lines.append('- 卡片阴影锐化，更接近印刷品')
lines.append('')
lines.append('现在请评审 v3 版本：')
lines.append('1. 以上改进是否有效？哪些方向对了，哪些还不够？')
lines.append('2. 当前版本在视觉上"不够高级"的根本原因是什么？')
lines.append('3. 给出下一页步迭代建议（P0必须做 / P1建议做 / P2锦上添花）')
lines.append('4. 给出对标方向（具体到哪家事务所的什么风格特征）')
lines.append('')
lines.append('## 共享CSS（前3000字符）')
lines.append('```')
lines.append(theme_css[:3000])
lines.append('```')
lines.append('')

for fname, content in slides.items():
    title = ''
    for line in content.split('\n'):
        if '<title>' in line:
            start = line.index('<title>') + 7
            end = line.index('</title>')
            title = line[start:end]
            break
    body_start = content.index('<body>') if '<body>' in content else 0
    body_end = content.index('</body>') if '</body>' in content else len(content)
    body = content[body_start:body_end] if body_start < body_end else ''
    body = body[:1000]
    lines.append('')
    lines.append('### ' + fname + ' - ' + title)
    lines.append('```html')
    lines.append(body)
    lines.append('```')

lines.append('')
lines.append('## 输出格式')
lines.append('')
lines.append('### 1. 总体评价（v3相比v2的进步/不足，评分1-10）')
lines.append('### 2. 核心问题（每个标注P0/P1/P2，详细说明原因和解决方案）')
lines.append('### 3. 逐页评审要点（每个页面2-3个观察点）')
lines.append('### 4. 对标方向')
lines.append('### 5. 行动建议清单（按优先级排序）')
lines.append('')
lines.append('注意：不要重复"缺照片"问题。聚焦设计语言、排版、视觉层次、间距、色彩、字体、装饰、布局节奏。')

prompt = '\n'.join(lines)

# Call gpt-5.6-sol
url = 'https://cbwyy.top/v1/chat/completions'
headers = {
    'Authorization': 'Bearer sk-eulyTfe7nRmr5ruwQH85kIfHkc8PPd88EoYGX0yadzlrkEpv',
    'Content-Type': 'application/json'
}
payload = json.dumps({
    'model': 'gpt-5.6-sol',
    'messages': [{'role': 'user', 'content': prompt}],
    'max_tokens': 8192,
    'temperature': 0.7
})

print('Calling gpt-5.6-sol for brochure v3 review...', flush=True)
req = urllib.request.Request(url, data=payload.encode('utf-8'), headers=headers, method='POST')
try:
    with urllib.request.urlopen(req, timeout=300) as resp:
        print('Status: ' + str(resp.status), flush=True)
        data = json.loads(resp.read().decode('utf-8'))
        if 'choices' in data and len(data['choices']) > 0:
            result = data['choices'][0]['message']['content']
            print('\n' + '='*60, flush=True)
            print(result, flush=True)
            print('\n' + '='*60, flush=True)
            usage = data.get('usage', {})
            print('\nUsage: ' + json.dumps(usage, ensure_ascii=False), flush=True)
        else:
            print('Error: ' + json.dumps(data, ensure_ascii=False, indent=2), flush=True)
except urllib.error.HTTPError as e:
    print('HTTP Error: ' + str(e.code), flush=True)
    body = e.read().decode('utf-8')
    print(body[:500], flush=True)