#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""杂志资料文章按文件名+标题关键词分类 - 写入YAML head"""
import sys, os, re, shutil
sys.stdout.reconfigure(encoding='utf-8')

vault = r'C:\Users\scrccpa\Documents\Obsidian Vault'
base = os.path.join(vault, '杂志资料')

# === 关键词 → 场景映射 ===
# 按优先级排列（更多关键词=更精确匹配优先）
SCENE_RULES = [
    # 经济责任审计
    (10, '经济责任审计', ['经责', '经济责任', '领导干部', '离任审计', '任期经济']),
    # 预算执行审计
    (10, '预算执行审计', ['预算执行', '部门预算', '财政预算', '预决算']),
    # 工程审计
    (9, '工程审计', ['工程审计', '招标投标', '招投标', '工程造价', '财政评审', '工程结算',
                    '竣工结算', '竣工决算', '基建审计', '建设项目审计', '投资审计',
                    '工程项目', '工程建设']),
    # 国企审计
    (9, '国企审计', ['国有企业', '央企', '国企审计', '企业审计', '集团公司', '集团审计']),
    # 金融审计
    (10, '金融审计', ['金融审计', '商业银行', '银行审计', '信贷审计', '贷款审计',
                    '证券', '保险审计', '金融风险', '金融机构']),
    # 资源环境审计
    (10, '资源环境审计', ['资源环境', '环境审计', '自然资源', '生态审计', '碳中和',
                        '水环境', '土地审计', '环保审计', '能源审计', '碳排放']),
    # 信息系统审计
    (8, '信息系统审计', ['信息系统', '大数据', '人工智能', '数字化审计', '智慧审计',
                       '网络安全', '数据审计', '信息化', '科技审计', 'IT审计']),
    # 绩效审计
    (9, '绩效审计', ['绩效评价', '绩效管理', '绩效审计', '绩效', '效益审计']),
    # 政策落实审计
    (9, '政策落实审计', ['政策落实', '跟踪审计', '贯彻落实', '政策措施', '专项督查']),
    # 社保民生审计
    (10, '社保民生审计', ['社保审计', '民生审计', '医保审计', '社会保障', '养老保险',
                        '就业审计', '扶贫审计', '补助审计', '补贴审计', '救济']),
    # 农业农村审计
    (10, '农业农村审计', ['农业农村', '乡村振兴', '三农审计', '农业审计', '农村审计',
                        '土地整治', '扶贫资金']),
    # 教科文卫审计
    (9, '教科文卫审计', ['教育审计', '高校审计', '学校审计', '医疗审计', '卫生审计',
                        '科研审计', '科技审计', '文化审计', '体育审计']),
    # 内部审计
    (9, '内部审计', ['内部审计', '内审', '内控', '内部控制', '公司治理']),
]

# category→scene粗略映射（用于中国审计等已有category的文章）
CAT_MAP = {
    '01-财政审计': '预算执行审计',
    '02-农业农村审计': '农业农村审计',
    '03-民生审计': '社保民生审计',
    '04-投资审计': '工程审计',
    '05-经济责任审计': '经济责任审计',
    '06-资源环境审计': '资源环境审计',
    '07-企业审计': '国企审计',
    '08-金融审计': '金融审计',
    '09-大数据与内部审计': '信息系统审计',
    '10-绩效评价': '绩效审计',
}

def get_title_from_file(fp):
    """读取文件的title和category/tags"""
    with open(fp, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read(1000)
    title = ''
    category = ''
    tags = []
    
    m = re.search(r'title:\s*["\']?([^"\'\n]+)', content)
    if m:
        title = m.group(1).strip()
    
    m = re.search(r'category:\s*["\']?([^"\'\n]+)', content)
    if m:
        category = m.group(1).strip()
    
    m = re.findall(r'tags:\s*\[([^\]]+)\]', content)
    if m:
        tags = [t.strip().strip('"').strip("'") for t in m[0].split(',')]
    
    return title, category, tags

def classify_article(filename, title, category, tags):
    """
    基于文件名+标题+category确定场景
    返回 (scene, confidence_source)
    """
    # 组合搜索文本
    search_text = f"{filename} {title} {' '.join(tags)}"
    
    # 1. 优先用category映射（如果有category且能映射）
    if category and category in CAT_MAP:
        return CAT_MAP[category], f'category:{category}'
    
    # 2. 如果没有category，用关键词匹配
    best_score = 0
    best_scene = '其他审计'
    best_source = '默认'
    
    for score, scene, keywords in SCENE_RULES:
        for kw in keywords:
            if kw in search_text:
                if score > best_score:
                    best_score = score
                    best_scene = scene
                    best_source = f'keyword:{kw}'
                break  # 一个场景匹配一个关键词就够了
    
    if best_score == 0:
        # 3. 最后兜底 - 看tags
        for t in tags:
            if t in ['财政监督', '中国审计']:
                continue
            best_scene = '其他审计'
            best_source = f'tag:{t}'
    
    return best_scene, best_source

def update_yaml(fp, scene, source):
    """为文件添加或更新scene字段到YAML head"""
    with open(fp, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    # 检查是否有YAML head
    if not content.startswith('---'):
        # 没有YAML head，添加
        yaml_head = f'---\nscene: "{scene}"\n---\n\n'
        new_content = yaml_head + content
    else:
        # 已有YAML head，在第二个---之前插入scene
        end_idx = content.find('---', 3)
        if end_idx > 0:
            head = content[3:end_idx]
            body = content[end_idx+3:]
            
            # 检查是否已有scene字段
            if re.search(r'^scene:', head, re.MULTILINE):
                # 替换已有scene
                new_head = re.sub(r'^scene:.*$', f'scene: "{scene}"', head, flags=re.MULTILINE)
            else:
                # 在tags之前插入（如果有tags），否则在末尾插入
                if re.search(r'^tags:', head, re.MULTILINE):
                    new_head = re.sub(r'^(tags:)', f'scene: "{scene}"\n\\1', head, flags=re.MULTILINE)
                else:
                    new_head = head.rstrip() + f'\nscene: "{scene}"\n'
            
            new_content = '---' + new_head + '---\n' + body.lstrip()
    
    with open(fp, 'w', encoding='utf-8') as f:
        f.write(new_content)

# === 主逻辑 ===
stats = {}
total = 0
for root, dirs, files in os.walk(base):
    if '按类型' in root:
        continue
    mds = [f for f in files if f.endswith('.md')]
    for fname in mds:
        fp = os.path.join(root, fname)
        title, category, tags = get_title_from_file(fp)
        scene, source = classify_article(fname, title, category, tags)
        update_yaml(fp, scene, source)
        
        stats[scene] = stats.get(scene, 0) + 1
        total += 1

print(f'分类完成，共处理 {total} 篇杂志文章\n')
print('场景分布:')
for scene, count in sorted(stats.items(), key=lambda x: -x[1]):
    print(f'  {scene}: {count}篇')
