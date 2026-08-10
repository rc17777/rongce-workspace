"""
知识库重组脚本：按12业务线重新分类
策略：复制→验证→删除源
"""
import os, sys, re, shutil, json
from collections import defaultdict
sys.stdout.reconfigure(encoding='utf-8')

SRC = r'D:\openclaw-workspace\knowledge'
DST_BASE = SRC  # 原地重组

# === 13个目标目录 ===
BUSINESS_DIRS = {
    '01-经责审计': ['经济责任审计', '经责审计', '经济责任', '领导干部', '权力寻租', '离任审计', '任中审计', '经责'],
    '02-收支审计': ['财务收支', '收支审计', '财政收支', '财务审计'],
    '03-预算执行': ['预算执行', '预算审计', '财政预算', '决算审计', '预算管理', '零基预算'],
    '04-专项资金': ['专项资金', '专项审计调查', '民生审计', '社会保障', '医保', '医疗收费', '药品', '公立医院',
                   '医改', '医药卫生', '农业农村', '惠农', '扶贫', '乡村振兴', '残疾人', '特困', '社会救助',
                   '殡葬', '教育审计', '高校内部审计', '学校食堂', '营养餐', '保障性'],
    '05-招投标采购': ['招投标', '招标', '投标', '串标', '围标', '中标', '政府采购', '采购审计', '采购文件',
                     '供应商', '评标', '药械采购', '采购环节'],
    '06-国企审计': ['国有企业', '国企', '央企', '国资', '企业审计', '公司治理', '上市公司', '供应链金融',
                   '金融审计', '银行审计', '私募基金', '小额贷款'],
    '07-工程审计': ['工程审计', '投资审计', '竣工决算', '竣工财务决算', '工程造价', '工程建设', '隐蔽工程',
                   '城中村改造', '安置房', '征地拆迁', '土地整治', '水利工程', '固废', '污水处理', '垃圾处理',
                   '无人机', '微动探测', '抛石挤淤'],
    '08-绩效评价': ['绩效评价', '绩效审计', '绩效管理', '预算绩效', '政策绩效', '财政支出绩效', '绩效考核',
                   '绩效评估', '提质增效'],
    '09-政府补贴': ['补贴', '补助资金', '以旧换新', '设备更新', '消费品', '农业保险', '保费补贴',
                   '养老补贴', '托育补贴', '适老化', '两新', '两重'],
    '10-能源资源': ['能源审计', '资源环境', '环境审计', '大气污染', '碳中和', '碳达峰', '绿色转型',
                   '固体废物', '生态环境', '环保', '节能', '水土保持', '河道治理', '地力培肥',
                   '排污', '联防联控', '污染防治'],
    '11-数据化审计': ['大数据', '数据分析', '数字化', '人工智能', 'AI审计', '信息系统审计', '区块链',
                     '数据治理', 'Neo4j', 'SQL', 'GIS', '模型', '信息化', 'Python', '算法'],
    '12-审计方法论': ['审计方法', '审计技术', '审计思维', '审计取证', '审计证据', '审计流程', '审计报告',
                     '审计整改', '审计质量', '研究型审计', '穿透式审计', '审计工具', '审计程序',
                     '审计准则', '审计标准', '审计复核', '科学规范'],
    '90-综合参考': [],  # 兜底
}

# === 关键词→目录映射 ===
def classify_by_title(title, existing_bl=None):
    """根据标题关键词分类"""
    title_lower = title.lower()
    
    # 如果已有YAML business_line, 优先用
    if existing_bl:
        # Map existing business_line to our dirs
        bl_map = {
            '经责': '01-经责审计', '收支': '02-收支审计', '预算': '03-预算执行',
            '专项': '04-专项资金', '招投标': '05-招投标采购', '国企': '06-国企审计',
            '工程': '07-工程审计', '绩效': '08-绩效评价', '补贴': '09-政府补贴',
            '能源': '10-能源资源', '金融': '06-国企审计', '成本': '07-工程审计',
            '往来款': '02-收支审计', '综合': '90-综合参考',
        }
        for k, v in bl_map.items():
            if k in str(existing_bl):
                return v
    
    # 标题关键词匹配
    for dir_name, keywords in BUSINESS_DIRS.items():
        if dir_name == '90-综合参考':
            continue
        for kw in keywords:
            if kw in title_lower:
                return dir_name
    
    return '90-综合参考'

def parse_yaml_frontmatter(filepath):
    """提取YAML frontmatter中的business_line"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read(5000)
        if content.startswith('---'):
            end = content.find('---', 3)
            if end > 0:
                fm = content[3:end]
                for line in fm.split('\n'):
                    if line.startswith('business_line:'):
                        return line.split(':', 1)[1].strip().strip('"').strip("'")
    except:
        pass
    return None

def get_source_label(filepath):
    """识别来源路径"""
    rel = os.path.relpath(filepath, SRC)
    if '杂志资料/中国审计' in rel:
        return '中国审计'
    if '杂志资料/审计案例' in rel:
        return '审计案例'
    if '杂志资料/按类型' in rel:
        return '按类型'
    if '杂志资料/财政监督' in rel:
        return '财政监督'
    if 'audit-articles' in rel:
        return 'audit-articles'
    if '审计案例库-OCR' in rel:
        return '审计案例库-OCR'
    if '审计方法' in rel or '审计技术' in rel or '审计理论' in rel or '审计方法论' in rel:
        return '方法论'
    if '数据化审计' in rel:
        return '数据化审计'
    if 'cases' in rel:
        return 'cases'
    if 'audit-models' in rel:
        return 'audit-models'
    if 'procurement' in rel:
        return '招投标'
    if '隐性债务' in rel:
        return '隐性债务'
    if 'articles' in rel:
        return 'articles'
    return '其他'

def main(dry_run=True):
    if dry_run:
        print("=" * 60)
        print("  预览模式")
        print("=" * 60)
    
    # 收集所有md文件
    all_files = []
    for root, dirs, files in os.walk(SRC):
        # 跳过已重组目录和内部目录
        rel_root = os.path.relpath(root, SRC)
        if any(rel_root.startswith(d) for d in BUSINESS_DIRS.keys()):
            continue
        if any(skip in rel_root for skip in ['_cleaned', '_bak', '.rag_index', 'node_modules', 'literature', 'policies', 'laws']):
            continue
        # 跳过索引/系统文件
        if 'INDEX.md' in rel_root or 'PARA-INDEX' in rel_root:
            continue
        
        for f in files:
            if f.endswith('.md'):
                # 跳过临时review文件
                if f.startswith('review_') or f.startswith('tmp_'):
                    continue
                all_files.append(os.path.join(root, f))
    
    print(f"\n扫描到 {len(all_files)} 个.md文件")
    
    # 分类统计
    classification = defaultdict(list)
    source_stats = defaultdict(lambda: defaultdict(int))
    
    for fp in all_files:
        # 获取元数据
        title = os.path.splitext(os.path.basename(fp))[0]
        bl = parse_yaml_frontmatter(fp)
        src = get_source_label(fp)
        
        # 分类
        target_dir = classify_by_title(title, bl)
        
        # 特殊处理：明确来源的直接归类
        if src == '数据化审计':
            target_dir = '11-数据化审计'
        elif src == '方法论':
            target_dir = '12-审计方法论'
        elif src == '招投标' or src == 'procurement-audit':
            target_dir = '05-招投标采购'
        elif src == '隐性债务':
            target_dir = '03-预算执行'
        
        # 能源相关关键词优先进10-能源资源（避免被04-专项资金抢走）
        title_lower = title.lower()
        energy_kw = ['大气污染', '碳中和', '碳达峰', '绿色转型', '固体废物', '生态环境',
                     '排污', '联防联控', '污染防治', '水土保持', '河道治理', '地力培肥',
                     '能源审计', '环境审计', '资源环境', '节能环保', '汾渭平原']
        if any(kw in title_lower for kw in energy_kw):
            target_dir = '10-能源资源'
        
        classification[target_dir].append({
            'path': fp,
            'title': title,
            'source': src,
            'business_line': bl
        })
        source_stats[src][target_dir] += 1
    
    # 输出报告
    total = sum(len(v) for v in classification.values())
    print(f"\n分类结果 ({total}篇):")
    print("-" * 60)
    for dir_name in sorted(classification.keys()):
        files = classification[dir_name]
        sz = sum(os.path.getsize(f['path']) for f in files) / 1024 / 1024
        print(f"\n  {dir_name}  ({len(files)}篇, {sz:.0f}MB)")
        # 显示来源分布
        src_dist = defaultdict(int)
        for f in files:
            src_dist[f['source']] += 1
        for s, c in sorted(src_dist.items()):
            print(f"    ← {s}: {c}篇")
        # 显示5个样例
        for f in files[:5]:
            print(f"      · {f['title'][:70]}")
    
    # 来源→目标交叉表
    print(f"\n\n来源→目标交叉表:")
    print("-" * 60)
    srcs = sorted(source_stats.keys())
    targets = sorted(set(d for sd in source_stats.values() for d in sd.keys()))
    # 表头
    header = f"{'来源':<20}"
    for t in targets:
        short = t[:2] if t[0].isdigit() else t[:4]
        header += f" {short:>4}"
    print(header)
    for s in srcs:
        row = f"{s:<20}"
        for t in targets:
            row += f" {source_stats[s].get(t, 0):>4}"
        print(row)
    
    if dry_run:
        print(f"\n\n要执行重组请运行: python scripts/_reorg_kb.py --execute")
    else:
        # 执行重组
        print(f"\n\n开始重组...")
        ops = {'moved': 0, 'errors': 0}
        
        for dir_name, files in classification.items():
            target_path = os.path.join(SRC, dir_name)
            os.makedirs(target_path, exist_ok=True)
            
            for f_info in files:
                src_path = f_info['path']
                fname = os.path.basename(src_path)
                dst_path = os.path.join(target_path, fname)
                
                # 处理重名
                if os.path.exists(dst_path):
                    base, ext = os.path.splitext(fname)
                    counter = 1
                    while os.path.exists(dst_path):
                        dst_path = os.path.join(target_path, f"{base}_{counter}{ext}")
                        counter += 1
                
                try:
                    shutil.move(src_path, dst_path)
                    ops['moved'] += 1
                except Exception as e:
                    ops['errors'] += 1
                    if ops['errors'] <= 5:
                        print(f"  错误: {fname[:50]}: {e}")
        
        print(f"\n重组完成: 移动{ops['moved']}篇, 错误{ops['errors']}")
        
        # 清理空目录
        from pathlib import Path
        for root, dirs, files in os.walk(SRC, topdown=False):
            rel_root = os.path.relpath(root, SRC)
            if any(rel_root.startswith(d) for d in BUSINESS_DIRS.keys()):
                continue
            if not os.listdir(root) and root != SRC:
                try:
                    os.rmdir(root)
                except:
                    pass

if __name__ == '__main__':
    execute = '--execute' in sys.argv
    main(dry_run=not execute)
