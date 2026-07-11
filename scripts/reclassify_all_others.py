#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重新分类全部其他审计 - 按YAML scene字段扫描"""
import sys, os, re, json, shutil
sys.stdout.reconfigure(encoding='utf-8')

VAULT = r'C:\Users\scrccpa\Documents\Obsidian Vault'

# 预读OCR详细数据
results_path = r'D:\openclaw-workspace\scripts\classification_results.json'
detailed_map = {}
if os.path.exists(results_path):
    with open(results_path, 'r', encoding='utf-8') as f:
        for item in json.load(f):
            fname = os.path.basename(item['filepath']).replace('.md', '')
            detailed_map[fname] = item

# 分类规则 - 预算优先（用户指令）
RULES = [
    (30, '绩效审计', ['预算']),
    (25, '预算执行审计', ['财政监督', '财会监督', '财政科学管理', '财政资源',
                         '财政政策', '转移支付', '财政管理', '财政紧平衡',
                         '财政行政处罚', '地方债', '隐性债务', '政府债务',
                         '非税收', '财政货币', '财税政策', '财政赋能',
                         '人大预算', '预算监督', '预算审查', '财政学',
                         '专项债', '特别国债', '超长期国债', '政府投资',
                         '税收', '税制', '会计法', '会计准则']),
    (25, '工程审计', ['PPP', '特许经营', '招标', '投标', '陪标',
                     '政府采购', '投资审计', '工程项目', '工程造价']),
    (25, '信息系统审计', ['人工智能', '数据要素', '数字化', '数智化', 'AI',
                        '信息化', '大数据', '区块链', '智慧', '科技',
                        '数据资产', '数智技术', '网络安全', '虚拟电厂']),
    (25, '教科文卫审计', ['教育', '高校', '大学', '教学', '科研', '医院',
                        '文化', '体育', '思政', '学生', '科技']),
    (25, '资源环境审计', ['氢能', '生态文明', '降碳', '绿色', '循环经济',
                        '低碳', '新能源', '碳', '节能']),
    (25, '国企审计', ['国有资产', '国有企业', '央企', '国有', '国资']),
    (20, '社保民生审计', ['社保', '民生', '养老', '医保', '就业', '扶贫',
                        '保险', '救济', '消费券']),
    (20, '农业农村审计', ['乡村', '农村', '农业', '三农', '村(社区)', '振兴']),
    (20, '政策落实审计', ['两新', '两重', '内需', '政绩观', '中国式现代化']),
]

def read_title_and_preview(fp):
    """读取title和preview"""
    with open(fp, 'r', encoding='utf-8', errors='replace') as f:
        c = f.read(2000)
    title = ''
    scene = ''
    m = re.search(r'title:\s*["\']?([^"\'\n]+)', c)
    if m: title = m.group(1).strip()
    m = re.search(r'scene:\s*["\']?([^"\'\n]+)', c)
    if m: scene = m.group(1).strip()
    return title, scene

def classify(title, fname, ocr_data=None):
    search = f"{fname} {title}"
    if ocr_data and 'preview' in ocr_data:
        search += ' ' + ocr_data['preview'][:500]
    best_score = 0
    best_scene = '其他审计'
    for score, scene, keywords in RULES:
        for kw in keywords:
            if kw in search and score > best_score:
                best_score = score
                best_scene = scene
                break
    return best_scene

# 扫描所有scene=其他审计的文件
others = []
for root, dirs, files in os.walk(VAULT):
    rel = os.path.relpath(root, VAULT)
    if '.obsidian' in rel or '按类型' in rel or rel.startswith('_'):
        continue
    if not rel.startswith(('审计案例库-OCR', '杂志资料')):
        continue
    for f in files:
        if not f.endswith('.md') or f.startswith('00-') or f == '00-索引.md' or f == 'INDEX.md':
            continue
        fp = os.path.join(root, f)
        title, scene = read_title_and_preview(fp)
        if scene == '其他审计' or scene == '其他审计':
            fname = f.replace('.md', '')
            ocr_data = detailed_map.get(fname)
            others.append((fp, f, title, fname, ocr_data, rel))

print(f'扫描到 scene=其他审计 的文件: {len(others)}篇\n')

# 执行分类
stats = {}
moved = []
for fp, f, title, fname, ocr_data, rel in others:
    new_scene = classify(title, fname, ocr_data)
    stats[new_scene] = stats.get(new_scene, 0) + 1
    
    if new_scene == '其他审计':
        continue
    
    # 确定目标目录
    if rel.startswith('审计案例库-OCR'):
        new_dir = os.path.join(VAULT, '审计案例库-OCR', new_scene)
    else:
        new_dir = os.path.join(VAULT, '杂志资料', new_scene)
    os.makedirs(new_dir, exist_ok=True)
    new_fp = os.path.join(new_dir, f)
    
    # 更新YAML
    with open(fp, 'r', encoding='utf-8', errors='replace') as fh:
        content = fh.read()
    content = re.sub(r'^scene:.*$', f'scene: "{new_scene}"', content, flags=re.MULTILINE)
    with open(new_fp, 'w', encoding='utf-8') as fh:
        fh.write(content)
    
    if fp != new_fp:
        os.remove(fp)
    
    moved.append((f, new_scene))

# 清理空目录
for root, dirs, files in os.walk(VAULT, topdown=False):
    rel = os.path.relpath(root, VAULT)
    if '按类型' in rel or rel.startswith('_'):
        continue
    if rel.startswith(('审计案例库-OCR', '杂志资料')):
        if root != os.path.join(VAULT, '审计案例库-OCR') and root != os.path.join(VAULT, '杂志资料'):
            try:
                if not os.listdir(root):
                    os.rmdir(root)
            except:
                pass

print('分类结果:')
for s in sorted(stats.keys(), key=lambda x: -stats[x]):
    print(f'  {s}: {stats[s]}篇')

print(f'\n移动的文件 ({len(moved)}篇):')
for f, s in sorted(moved):
    print(f'  → {s}: {f[:70]}')
