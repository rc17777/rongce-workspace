import os, sys, re, json
sys.stdout.reconfigure(encoding='utf-8')

KB = r'D:\openclaw-workspace\knowledge\杂志资料'

# 四场景 × 12业务线 匹配矩阵
SCENARIO_KW = {
    '投标方案编制': {
        'keywords': ['政策','法规','制度','标准','规范','办法','指南','管理','改革','体制','机制','模式','框架','路径','对策','建议','优化','提升','体系','创新','发展'],
        '权重2x': ['绩效评价','绩效管理','预算绩效','全过程','跟踪审计','内部控制','风险防控','专项资金','政府采购','合同管理'],
    },
    '项目实施疑点': {
        'keywords': ['案例','疑点','异常','造假','舞弊','虚报','套取','挪用','违规','问题','线索','发现','识别','检测','检查','漏洞','陷阱','风险点','常见问题','教训'],
        '权重2x': ['围标','串标','回扣','利益输送','小金库','假发票','虚列','空转','阴阳合同','高估冒算'],
    },
    '审计评价思路': {
        'keywords': ['方法','思路','框架','模型','指标','评价','分析','审计方法','审计思路','技术','工具','数据','信息化','数字化','大数据','SQL','Python','流程','步骤'],
        '权重2x': ['数据分析','指标体系','评价框架','审计模型','核查方法','分析思路','技术方法'],
    },
    '报告撰写': {
        'keywords': ['问题','定性','建议','整改','报告','底稿','文书','意见','结论','评价','定性','表述','措辞','模板','格式'],
        '权重2x': ['审计建议','整改措施','审计发现','审计评价','审计意见','审计报告'],
    },
}

BIZ_KW = {
    '经济责任审计': ['经责','经济责任','离任','任中','自然资源','领导干部','履职','三重一大','决策'],
    '收支审计': ['预算执行','财政收支','三公经费','非税收入','部门预算','决算','财政资金','转移支付'],
    '政府专项审计': ['专项资金','社保','医保','教育资金','民政','保障房','惠农','救济','营养餐'],
    '招投标审计': ['招标','投标','围标','串标','中标','采购','政府采购','招投标','评标','竞价'],
    '国企审计': ['国企','国有','国资','央企','国有资产','国有企业'],
    '工程审计': ['工程','竣工','造价','结算','施工','监理','变更','签证','基建','概算','招标控制价'],
    '预算绩效管理': ['绩效评价','绩效目标','事前评估','事中监控','结果应用','绩效指标','绩效管理'],
    '政府补贴审计': ['补贴','补助','奖补','贴息','农机','耕地','退耕'],
    '能源审计': ['能源','节能','碳排放','碳中和','碳达峰','能耗','新能源','绿色'],
    '往来款清理': ['往来款','挂账','应收账款','应付账款','坏账','债权债务','往来清理'],
    '成本效益': ['成本效益','投入产出','降本增效','成本控制','效益分析'],
}

# Scan all articles
articles = []
for r, _, fs in os.walk(KB):
    if '.git' in r: continue
    for f in fs:
        if not f.endswith('.md'): continue
        path = os.path.join(r, f)
        rel = os.path.relpath(path, KB)
        
        # Read first 500 chars for classification
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as fh:
                content = fh.read(1500)
        except:
            content = ''
        
        title = f.replace('.md', '')
        full_text = f'{title} {content[:1000]}'
        
        # Classify scenario
        scenarios = []
        for sc, rules in SCENARIO_KW.items():
            score = sum(1 for kw in rules['keywords'] if kw in full_text)
            score += sum(2 for kw in rules['权重2x'] if kw in full_text)
            if score >= 3:
                scenarios.append((sc, score))
        
        # Classify business line
        biz_lines = []
        for bl, kws in BIZ_KW.items():
            score = sum(1 for kw in kws if kw in title)
            if score > 0:
                biz_lines.append(bl)
        
        articles.append({
            'title': title[:100],
            'path': rel,
            'scenario': [s[0] for s in sorted(scenarios, key=lambda x:-x[1])[:2]],
            'biz': biz_lines,
        })

# Count
sc_counts = {'投标方案编制':0,'项目实施疑点':0,'审计评价思路':0,'报告撰写':0}
for a in articles:
    for s in a['scenario']:
        sc_counts[s] = sc_counts.get(s, 0) + 1

print(f'扫描: {len(articles)} 篇文章')
for s, c in sorted(sc_counts.items(), key=lambda x:-x[1]):
    print(f'  {s}: {c}篇')
print()

# Output JSON for later use
with open(r'D:\openclaw-workspace\temp\scene_match.json','w',encoding='utf-8') as f:
    json.dump(articles, f, ensure_ascii=False, indent=2)
print(f'Index saved: {len(articles)} entries')
