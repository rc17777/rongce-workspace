#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""杂志文章分类 v2 - 先关键词匹配，category只做兜底"""
import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')

vault = r'C:\Users\scrccpa\Documents\Obsidian Vault'
base = os.path.join(vault, '杂志资料')

# === 关键词→场景映射（分数越高优先级越高） ===
SCENE_RULES = [
    (20, '经济责任审计', ['经济责任', '经责审计', '离任审计', '任期经济责任', '领导干部审计']),
    (20, '金融审计', ['空壳骗贷', '骗贷记', '金融审计', '商业银行审计', '银行信贷',
                     '财务舞弊', '舞弊行为', 'ST ', '上市造假', '内幕交易', '操纵市场',
                     '洗钱', '反洗钱', '金融风险', '融资平台', '地方政府债务']),
    (20, '社保民生审计', ['社保审计', '民生审计', '医保审计', '社会保障审计',
                        '工伤保险', '养老保险', '消费券', '课后服务', '双减']),
    (20, '农业农村审计', ['农业农村审计', '乡村振兴', '三农审计', '土地整治',
                        '农业科技示范', '骗取补贴', '农村', '土地综合整治']),
    (20, '资源环境审计', ['资源环境审计', '环境审计', '自然资源审计', '生态审计',
                        '长江', '黄河', '水环境', '碳审计', '碳中和', '耕地保护',
                        '林审计', '水域', '能源审计']),
    (15, '经济责任审计', ['领导干部', '经济责任', '经责', '离任', '任中']),
    (15, '国企审计', ['国有企业', '国企审计', '企业审计', '央企审计', '集团审计']),
    (15, '工程审计', ['工程审计', '招投标', '工程造价', '财政评审', '工程结算',
                     '竣工结算', '竣工决算', '基建审计', '建设项目审计',
                     '投资审计', '征拆', '拆迁']),
    (15, '金融审计', ['商业银行', '银行', '信贷', '贷款', '证券', '保险审计',
                     '金融机构', '金融']),
    (15, '信息系统审计', ['大数据审计', '智慧审计', '数字化审计', '数据审计',
                         'IT审计', '网络安全审计', '信息化审计', '人工智能',
                         '科技强审']),
    (15, '绩效审计', ['绩效评价', '绩效管理', '绩效审计', '预算绩效']),
    (15, '政策落实审计', ['政策落实', '跟踪审计', '政策措施', '督察审计', '专项督查']),
    (15, '教科文卫审计', ['教育审计', '高校审计', '科研审计', '医疗审计', '卫生审计',
                         '学校', '高校', '大学', '医院', '科研经费']),
    (15, '内部审计', ['内部审计', '内审', '内控', '内部控制', '公司治理']),
    (10, '内部审计', ['集团审计', '内控建设', '内控管理']),
    (10, '预算执行审计', ['预算执行', '部门预算', '预决算', '财政预算',
                        '中央预算', '财政收支审计']),
    (10, '社保民生审计', ['社保', '民生', '养老', '就业', '扶贫', '补助',
                         '补贴', '保险', '医保', '医疗', '救助']),
    (10, '工程审计', ['工程', '招标', '投标', '施工', '建设', '基建', '竣工',
                     '造价', '评审']),
    (10, '资源环境审计', ['环境', '生态', '水', '碳', '能源', '土地', '自然资源',
                         '环保', '林地', '耕地', '水域']),
    (10, '信息系统审计', ['大数据', '人工智能', 'AI', '数字化', '数据', '信息系统',
                         '智慧', '信息化', '科技', '网络安全']),
    (10, '绩效审计', ['绩效', '效益']),
]

CAT_FALLBACK = {
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

def get_meta(fp):
    with open(fp, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read(1000)
    title = ''
    category = ''
    tags = []
    m = re.search(r'title:\s*["\']?([^"\'\n]+)', content)
    if m: title = m.group(1).strip()
    m = re.search(r'category:\s*["\']?([^"\'\n]+)', content)
    if m: category = m.group(1).strip()
    m = re.findall(r'tags:\s*\[([^\]]+)\]', content)
    if m: tags = [t.strip().strip('"').strip("'") for t in m[0].split(',')]
    return title, category, tags

def classify(filename, title, category, tags):
    """优先关键词匹配，category仅做最后兜底"""
    search = f"{filename} {title} {' '.join(tags)}"
    
    best_score = 0
    best_scene = None
    best_source = ''
    
    for score, scene, keywords in SCENE_RULES:
        for kw in keywords:
            if kw in search:
                # 用分数比较而非简单stop-on-first
                if score > best_score:
                    best_score = score
                    best_scene = scene
                    best_source = f'kw:{kw}'
                break
    
    if best_scene:
        return best_scene, best_source
    
    # 第二优先级: category映射
    if category in CAT_FALLBACK:
        return CAT_FALLBACK[category], f'cat:{category}'
    
    # 第三优先级: 文件名本身含场景词
    for cat_name, cat_scene in CAT_FALLBACK.items():
        cat_key = cat_name[3:]  # 去掉"01-"前缀
        if cat_key in filename:
            return cat_scene, f'fname:{cat_key}'
    
    return '其他审计', 'default'

# === 执行 ===
stats = {}
total = 0
for root, dirs, files in os.walk(base):
    if '按类型' in root:
        continue
    for fname in files:
        if not fname.endswith('.md'):
            continue
        fp = os.path.join(root, fname)
        title, category, tags = get_meta(fp)
        scene, source = classify(fname, title, category, tags)
        
        # 更新YAML
        with open(fp, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        if content.startswith('---'):
            end_idx = content.find('---', 3)
            if end_idx > 0:
                head = content[3:end_idx]
                body = content[end_idx+3:]
                if re.search(r'^scene:', head, re.MULTILINE):
                    new_head = re.sub(r'^scene:.*$', f'scene: "{scene}"', head, flags=re.MULTILINE)
                else:
                    new_head = re.sub(r'^(tags:)', f'scene: "{scene}"\n\\1', head, flags=re.MULTILINE)
                    if 'tags:' not in head:
                        new_head = head.rstrip() + f'\nscene: "{scene}"\n'
                content = '---' + new_head + '---\n' + body.lstrip()
        else:
            content = f'---\nscene: "{scene}"\n---\n\n{content}'
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(content)
        
        stats[scene] = stats.get(scene, 0) + 1
        total += 1

print(f'分类完成，共处理 {total} 篇\n')
for s, c in sorted(stats.items(), key=lambda x: -x[1]):
    print(f'  {s}: {c}篇')
