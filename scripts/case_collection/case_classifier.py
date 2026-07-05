#!/usr/bin/env python3
"""
案例分类器 v1.0
对待确认案例进行AI分类，映射到12业务线
"""

import json, sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BUSINESS_LINES = {
    "经济责任审计": ["经责", "经济责任", "离任", "任中", "领导干部", "自然资源"],
    "收支审计": ["收支", "财政收支", "预算收支", "收入", "支出"],
    "预算执行审计": ["预算执行", "预算管理", "预算编制"],
    "专项资金审计": ["专项", "专项资金", "社保", "营养餐", "扶贫", "民生"],
    "往来款清理": ["往来款", "往来", "清理", "资金清理"],
    "招投标审计": ["招投标", "招标", "投标", "串标", "围标", "采购"],
    "国企审计": ["国企", "国有企业", "央企", "国资"],
    "成本效益审计": ["成本", "效益", "成本效益"],
    "能源审计": ["能源", "碳中和", "碳排放", "节能"],
    "工程竣工决算财务审计": ["工程", "竣工", "决算", "建设项目", "基建"],
    "预算绩效管理": ["绩效", "绩效评价", "绩效管理", "绩效目标"],
    "政府补贴审计": ["补贴", "财政补助", "政府补贴"]
}

def classify_case(title, keywords=None):
    """根据标题和关键词自动分类"""
    scores = {}
    text = title + " " + (keywords or "")
    
    for line, kws in BUSINESS_LINES.items():
        score = sum(text.count(kw) for kw in kws)
        if score > 0:
            scores[line] = score
    
    if not scores:
        return "其他"
    
    # 返回得分最高的业务线
    return max(scores.items(), key=lambda x: x[1])[0]

def batch_classify(pending_file):
    """批量分类待确认案例"""
    print(f"📂 读取待确认清单: {pending_file}")
    
    with open(pending_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    items = data['items']
    print(f"📋 共 {len(items)} 条待分类案例\n")
    
    classified = {}
    for item in items:
        scene = classify_case(item['title'])
        item['scene'] = scene
        
        if scene not in classified:
            classified[scene] = []
        classified[scene].append(item)
    
    # 打印分类结果
    print("【分类结果】")
    for scene, cases in sorted(classified.items()):
        print(f"\n{scene} ({len(cases)} 条)")
        for i, case in enumerate(cases[:3], 1):
            print(f"  {i}. {case['title'][:60]}")
        if len(cases) > 3:
            print(f"  ... 还有 {len(cases) - 3} 条")
    
    # 保存分类结果
    output_file = pending_file.parent / (pending_file.stem + "_classified.json")
    data['classified'] = classified
    data['classification_done'] = True
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 分类完成，已保存: {output_file}")
    return output_file

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python case_classifier.py <pending_file.json>")
        sys.exit(1)
    
    pending_file = Path(sys.argv[1])
    if not pending_file.exists():
        print(f"❌ 文件不存在: {pending_file}")
        sys.exit(1)
    
    batch_classify(pending_file)
