#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""其他审计 133篇 → 按内容细分到各场景"""
import sys, os, re, json, shutil
sys.stdout.reconfigure(encoding='utf-8')

VAULT = r'C:\Users\scrccpa\Documents\Obsidian Vault'
OCR_DIR = os.path.join(VAULT, '审计案例库-OCR')
MAG_DIR = os.path.join(VAULT, '杂志资料')

# 读取详细分类数据（含preview）
results_path = r'D:\openclaw-workspace\scripts\classification_results.json'
detailed_map = {}
if os.path.exists(results_path):
    with open(results_path, 'r', encoding='utf-8') as f:
        for item in json.load(f):
            fname = os.path.basename(item['filepath']).replace('.md', '')
            detailed_map[fname] = item

# 重新分类规则
RECLASSIFY_RULES = [
    # (优先级分, 目标场景, 关键词列表)
    # --- 预算相关 → 绩效审计（用户明确指令）---
    (30, '绩效审计', ['预算', '预算绩效', '零基预算']),
    
    # --- 财政/财会监督 → 预算执行审计 ---
    (25, '预算执行审计', ['财政监督', '财会监督', '财政科学管理', '财政资源统筹',
                        '财政政策', '转移支付', '财政管理', '财政紧平衡',
                        '财政行政处罚', '地方债', '隐性债务', '政府债务',
                        '非税收人', '财政货币', '财税政策', '财政赋能',
                        '人大预算', '预算监督', '预算审查', '财政学']),
    # 专项债 → 预算执行审计
    (25, '预算执行审计', ['专项债', '特别国债', '超长期', '政府投资']),

    # --- PPP/工程相关 → 工程审计 ---
    (25, '工程审计', ['PPP', '特许经营', '工程项目', '招投标', '招标',
                     '陪标', '政府采购', '投资审计']),

    # --- AI/科技/数据/数字化 → 信息系统审计 ---
    (25, '信息系统审计', ['人工智能', '数据要素', '数字化', '数智化', 'AI',
                        '信息化', '大数据', '区块链', '智慧', '科技',
                        '数据资产', '数智技术', '网络安全']),

    # --- 教育/教学/文化/医院 → 教科文卫审计 ---
    (25, '教科文卫审计', ['教育', '高校', '大学', '教学', '科研', '医疗',
                        '医院', '文化', '体育', '思政', '学生']),

    # --- 能源/环境/生态/碳 → 资源环境审计 ---
    (25, '资源环境审计', ['氢能', '生态文明', '降碳', '绿色', '循环经济',
                        '低碳', '新能源', '碳', '环保', '环境', '生态']),

    # --- 社保/民生/就业/扶贫 → 社保民生审计 ---
    (25, '社保民生审计', ['社保', '民生', '养老', '医保', '就业', '扶贫',
                        '保险', '补助', '救济', '消费券']),

    # --- 国企/国有资产 → 国企审计 ---
    (20, '国企审计', ['国有资产', '国有企业', '央企', '国有', '国资']),

    # --- 农业农村 → 农业农村审计 ---
    (20, '农业农村审计', ['乡村', '农村', '农业', '三农', '村', '振兴']),

    # --- 经济责任 → 经济责任审计 ---
    (20, '经济责任审计', ['经济责任', '经责', '领导干部', '离任']),

    # --- 政策/跟踪 → 政策落实审计 ---
    (20, '政策落实审计', ['政策落实', '跟踪审计', '两新', '两重', '督察',
                        '内需', '政绩观', '中国式现代化']),
]

stats = {'预算执行审计': 0, '绩效审计': 0, '工程审计': 0, '信息系统审计': 0,
         '教科文卫审计': 0, '资源环境审计': 0, '社保民生审计': 0, '国企审计': 0,
         '农业农村审计': 0, '经济责任审计': 0, '政策落实审计': 0, '内部审计': 0,
         '金融审计': 0, '其他审计': 0}

moved_files = []

def classify(title, filename, ocr_data=None):
    """判断文章应该归到哪个场景"""
    search = f"{filename} {title}"
    
    # 如果OCR数据中有preview，也加入搜索
    if ocr_data and 'preview' in ocr_data:
        search += ' ' + ocr_data['preview'][:500]
    
    best_score = 0
    best_scene = '其他审计'
    best_source = ''
    
    for score, scene, keywords in RECLASSIFY_RULES:
        for kw in keywords:
            if kw in search:
                if score > best_score:
                    best_score = score
                    best_scene = scene
                    best_source = kw
                break
    
    return best_scene, best_source

def read_title(fp):
    """从YAML中读取title"""
    with open(fp, 'r', encoding='utf-8', errors='replace') as f:
        c = f.read(1000)
    m = re.search(r'title:\s*["\']?([^"\'\n]+)', c)
    return m.group(1).strip() if m else ''

def update_yaml(fp, new_scene):
    """更新YAML中的scene字段"""
    with open(fp, 'r', encoding='utf-8', errors='replace') as f:
        c = f.read()
    c = re.sub(r'^scene:.*$', f'scene: "{new_scene}"', c, flags=re.MULTILINE)
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(c)

# === 处理所有其他审计文件 ===
for root, dirs, files in os.walk(VAULT):
    rel = os.path.relpath(root, VAULT)
    # 只处理 OCR 和 杂志资料中的 其他审计 目录
    is_ocr = rel.startswith('审计案例库-OCR')
    is_mag = rel.startswith('杂志资料')
    if not (is_ocr or is_mag):
        continue
    # 跳过已分类目录
    scene_dir = os.path.basename(root)
    if scene_dir != '其他审计':
        continue
    # 跳过按类型目录
    if '按类型' in rel:
        continue
    
    for f in files:
        if not f.endswith('.md') or f.startswith('00-') or f == '00-索引.md':
            continue
        
        fp = os.path.join(root, f)
        fname = f.replace('.md', '')
        title = read_title(fp)
        
        # 获取OCR详细数据
        ocr_data = detailed_map.get(fname)
        
        new_scene, source = classify(title, fname, ocr_data)
        
        if new_scene != '其他审计':
            stats[new_scene] = stats.get(new_scene, 0) + 1
            # 移动文件到新目录
            if is_ocr:
                new_dir = os.path.join(OCR_DIR, new_scene)
            else:
                new_dir = os.path.join(MAG_DIR, new_scene)
            os.makedirs(new_dir, exist_ok=True)
            new_fp = os.path.join(new_dir, f)
            
            # 更新YAML
            update_yaml(fp, new_scene)
            shutil.move(fp, new_fp)
            moved_files.append((f, new_scene, source))
        else:
            stats['其他审计'] = stats.get('其他审计', 0) + 1

# === 清理空目录 ===
for root, dirs, files in os.walk(VAULT, topdown=False):
    rel = os.path.relpath(root, VAULT)
    if rel.startswith(('审计案例库-OCR', '杂志资料')):
        if not os.listdir(root) and root != os.path.join(VAULT, '审计案例库-OCR') and root != os.path.join(VAULT, '杂志资料'):
            os.rmdir(root)

print('=' * 60)
print('其他审计 重新分类结果')
print('=' * 60)
print(f'\n移出到其他场景: {len(moved_files)}篇')
print(f'保留在其他审计: {stats["其他审计"]}篇\n')

print('各场景接收文章数:')
for s in sorted(stats.keys(), key=lambda x: -stats[x]):
    if stats[s] > 0 and s != '其他审计':
        print(f'  → {s}: {stats[s]}篇')

print(f'\n移动的文件清单:')
for f, scene, reason in sorted(moved_files):
    print(f'  [{scene}] ({reason}) {f[:70]}')
