"""
合并 LLM Wiki → 知识库（去重+分类）
"""
import os, sys, re, shutil, json, hashlib
sys.stdout.reconfigure(encoding='utf-8')

WIKI = r'D:\openclaw-workspace\archive\llm-wiki-融策业务总库'
KB = r'D:\openclaw-workspace\knowledge'

# 关键词→目录映射
KW_MAP = [
    (['招投标', '招标', '投标', '串标', '围标', '中标', '政府采购', '采购', '评标', '供应商', '标书', 'bid', 'tender'], '05-招投标采购'),
    (['经济责任', '经责', '领导干部', '权力寻租', '离任', '任中', '领导人员', '审计问责'], '01-经责审计'),
    (['预算执行', '预算审计', '财政预算', '决算', '零基预算', '预算管理', '财政审计'], '03-预算执行'),
    (['专项资金', '民生', '社保', '医保', '医疗', '公立医院', '医改', '医药', '农业农村', '惠农', '扶贫', '乡村振兴', '残疾人', '特困', '社会救助', '教育审计', '高校审计', '学校'], '04-专项资金'),
    (['绩效评价', '绩效审计', '绩效管理', '预算绩效', '绩效评估', '绩效考核', '绩效目标', '提质增效'], '08-绩效评价'),
    (['国企', '国有', '企业审计', '央企', '国资', '公司治理', '上市公司', '金融审计', '银行', '供应链金融', '私募'], '06-国企审计'),
    (['工程', '竣工', '决算', '建设', '投资审计', '工程造价', '隐蔽工程', '城中村', '安置房', '征地', '土地', '水利', '污水处理', '垃圾'], '07-工程审计'),
    (['补贴', '补助', '保险', '以旧换新', '设备更新', '养老', '托育', '适老化', '两新', '两重'], '09-政府补贴'),
    (['能源', '资源环境', '环境审计', '大气', '碳中和', '碳达峰', '绿色', '固废', '生态', '环保', '节能', '排污', '水土'], '10-能源资源'),
    (['大数据', '数据分析', '数字化', '人工智能', 'AI', '区块链', '信息化', '信息系统', '模型', '知识图谱', 'Neo4j', 'SQL', 'Python', '算法', '数据治理', 'RAG', 'LLM'], '11-数据化审计'),
    (['审计方法', '审计技术', '审计思维', '审计证据', '审计取证', '审计报告', '审计整改', '审计质量', '审计流程', '审计准则', '研究型审计', '穿透式', '审计工具', '底稿', '穿行测试', '审计程序', '审计复核'], '12-审计方法论'),
    (['财务收支', '收支审计', '财政收支', '财务审计', '往来款', '资金清理'], '02-收支审计'),
]

def classify_by_content(title, content_preview):
    combined = title + ' ' + content_preview[:5000]
    for kws, d in KW_MAP:
        if any(kw in combined for kw in kws):
            return d
    return '90-综合参考'

def get_content_hash(filepath):
    """计算文件内容哈希（去重用）"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        # 取前2000字符做快速哈希
        return hashlib.md5(content[:2000].encode()).hexdigest()
    except:
        return None

def main():
    # === 1. 建立知识库已有文件的哈希索引 ===
    print("建立知识库哈希索引...")
    kb_hashes = set()
    kb_titles = set()
    for root, dirs, files in os.walk(KB):
        # 跳过非业务目录
        rel = os.path.relpath(root, KB)
        if any(s in rel for s in ['_cleaned', '.rag_index', 'archive']):
            continue
        for f in files:
            if f.endswith('.md'):
                kb_titles.add(f.lower())
                h = get_content_hash(os.path.join(root, f))
                if h:
                    kb_hashes.add(h)
    
    print(f"  知识库: {len(kb_titles)} 个标题, {len(kb_hashes)} 个哈希")
    
    # === 2. 扫描 Wiki 文章 ===
    print("\n扫描 Wiki...")
    wiki_files = []
    for root, dirs, files in os.walk(WIKI):
        for f in files:
            if f.endswith('.md'):
                fp = os.path.join(root, f)
                wiki_files.append(fp)
    
    print(f"  Wiki: {len(wiki_files)} 篇")
    
    # === 3. 去重+分类 ===
    print("\n去重+分类...")
    stats = {'new': 0, 'dup_title': 0, 'dup_content': 0, 'errors': 0}
    classified = {}
    
    for i, fp in enumerate(wiki_files):
        fname = os.path.basename(fp)
        title = fname.replace('.md', '')
        
        # 标题去重
        if fname.lower() in kb_titles:
            stats['dup_title'] += 1
            continue
        
        # 内容哈希去重
        h = get_content_hash(fp)
        if h and h in kb_hashes:
            stats['dup_content'] += 1
            continue
        
        # 读取内容预览
        try:
            with open(fp, 'r', encoding='utf-8', errors='ignore') as fh:
                content = fh.read(10000)
        except:
            stats['errors'] += 1
            continue
        
        # 分类
        target_dir = classify_by_content(title, content)
        
        if target_dir not in classified:
            classified[target_dir] = []
        classified[target_dir].append(fp)
        stats['new'] += 1
        
        if (i + 1) % 200 == 0:
            print(f"  进度: {i+1}/{len(wiki_files)} (新增{stats['new']}, 去重{stats['dup_title']+stats['dup_content']})")
    
    print(f"\n  新增: {stats['new']}篇")
    print(f"  标题重复: {stats['dup_title']}篇")
    print(f"  内容重复: {stats['dup_content']}篇")
    print(f"  错误: {stats['errors']}篇")
    
    # === 4. 写入知识库 ===
    print("\n写入知识库...")
    for target_dir, files in classified.items():
        target_path = os.path.join(KB, target_dir)
        os.makedirs(target_path, exist_ok=True)
        
        for fp in files:
            fname = os.path.basename(fp)
            dst = os.path.join(target_path, fname)
            
            # 处理重名
            if os.path.exists(dst):
                base, ext = os.path.splitext(fname)
                counter = 1
                while os.path.exists(dst):
                    dst = os.path.join(target_path, f'{base}_{counter}{ext}')
                    counter += 1
            
            shutil.copy2(fp, dst)
    
    # === 5. 报告 ===
    print("\n" + "=" * 60)
    print("  合并完成!")
    print("=" * 60)
    
    total_before = len(kb_titles)
    total_after = total_before + stats['new']
    
    print(f"\n知识库: {total_before} → {total_after}篇 (+{stats['new']})")
    print(f"去重: {stats['dup_title'] + stats['dup_content']}篇")
    
    # 各业务线新增
    print("\n各业务线新增:")
    for d in sorted(classified.keys()):
        cnt = len(classified[d])
        existing = sum(1 for r, dd, fs in os.walk(os.path.join(KB, d)) for f in fs if f.endswith('.md')) - cnt
        print(f"  {d}: {existing} → {existing + cnt} (+{cnt})")
    
    return stats

if __name__ == '__main__':
    main()
