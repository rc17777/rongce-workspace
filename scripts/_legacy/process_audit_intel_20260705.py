#!/usr/bin/env python3
"""
处理2026-07-05审计情报采集内容
任务：
1. 从媒体视点提取2024年审计整改关键数据
2. 从审计要闻提取地方审计工作经验关键词
3. 标记无效采集文件
"""

import json, sys, re
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).parent.parent
POLICY_DIR = BASE_DIR / "knowledge" / "policies"
OUTPUT_DIR = BASE_DIR / "knowledge" / "intel_summaries"
LOG_DIR = BASE_DIR / "logs" / "audit_intel"

def extract_media_data():
    """从媒体视点提取2024年审计整改关键数据"""
    file_path = POLICY_DIR / "20260705_审计署-媒体视点.md"
    
    if not file_path.exists():
        print(f"❌ 文件不存在: {file_path}")
        return None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取关键数据
    data = {
        "标题": "2024年度审计整改关键数据",
        "来源": "审计署媒体视点",
        "采集时间": "2026-07-05",
        "关键数据": []
    }
    
    # 整改金额
    match = re.search(r'整改.*?金额.*?([\d.]+)\s*(万亿|亿)', content)
    if match:
        amount = match.group(1)
        unit = match.group(2)
        data["关键数据"].append({
            "指标": "整改问题金额",
            "数值": f"{amount}{unit}元",
            "原文": match.group(0)
        })
    
    # 制度完善
    match = re.search(r'制定.*?完善.*?制度.*?(\d+)\s*[多余]?项', content)
    if match:
        count = match.group(1)
        data["关键数据"].append({
            "指标": "制定完善制度",
            "数值": f"{count}项",
            "原文": match.group(0)
        })
    
    # 重点内容
    keywords = ["审计整改", "基本办学条件", "两新", "骗补", "家电销售企业", "民生领域", "教育", "养老"]
    data["涉及领域"] = [kw for kw in keywords if kw in content]
    
    # 提取具体条目
    items = []
    for line in content.split('\n'):
        if '审计署发布2024年度审计整改报告' in line:
            items.append(line.strip(' .'))
    
    data["重点报道"] = items[:5] if items else []
    
    return data

def extract_local_experience():
    """从审计要闻提取地方审计工作经验关键词"""
    file_path = POLICY_DIR / "20260705_审计署-审计要闻.md"
    
    if not file_path.exists():
        print(f"❌ 文件不存在: {file_path}")
        return None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取地方经验
    regions = {
        "陕西西安": [],
        "海南": [],
        "山东青岛": [],
        "黑龙江": []
    }
    
    for region in regions.keys():
        match = re.search(rf'{region}[：:](.*?)(?=\n|\[)', content)
        if match:
            desc = match.group(1).strip()
            regions[region] = {
                "描述": desc,
                "关键词": []
            }
            
            # 提取关键词
            if "高质量发展" in desc:
                regions[region]["关键词"].append("高质量发展")
            if "现代化" in desc or "现代化建设" in desc:
                regions[region]["关键词"].append("现代化建设")
            if "审计保障" in desc:
                regions[region]["关键词"].append("审计保障")
            if "监督职责" in desc:
                regions[region]["关键词"].append("监督职责")
            if "主动服务" in desc:
                regions[region]["关键词"].append("主动服务大局")
            if "两重" in desc or "两新" in desc:
                regions[region]["关键词"].append("两重两新")
    
    return {
        "标题": "地方审计工作经验提取",
        "来源": "审计署审计要闻",
        "采集时间": "2026-07-05",
        "地方经验": regions
    }

def mark_invalid_files():
    """标记无效采集文件并生成清单"""
    invalid_files = []
    
    # 检查审计法文件
    audit_law_file = POLICY_DIR / "20260705_中华人民共和国审计法.md"
    if audit_law_file.exists():
        with open(audit_law_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查内容质量
        text = re.sub(r'---.*?---', '', content, flags=re.DOTALL)
        text = re.sub(r'\*本文由.*?\*', '', text)
        clean_text = text.strip()
        
        if len(clean_text) < 1000 or '无障碍浏览' in clean_text or '网站地图' in clean_text:
            invalid_files.append({
                "文件": "20260705_中华人民共和国审计法.md",
                "原因": "抓取HTML导航菜单，未获取法条正文",
                "原始URL": "http://www.npc.gov.cn/npc/c30834/202110/8e9b467a53b64c5c92adb6b900513091.shtml",
                "建议方案": [
                    "使用PDF版本：全国人大常委会提供的纯文本PDF",
                    "或从立法数据库目录重新获取",
                    "或手动整理该法律全文（7章63条）"
                ],
                "优先级": "中",
                "状态": "待处理"
            })
    
    # 检查国家审计准则
    standard_file = POLICY_DIR / "20260705_国家审计准则.md"
    if not standard_file.exists():
        invalid_files.append({
            "文件": "20260705_国家审计准则.md",
            "原因": "未采集到或内容为空",
            "原始URL": "https://flk.npc.gov.cn/detail2.html?ZmY4MDg2MDc2MjM3MTE2YzAxNjI3YzIzMDIxNzA4Yzc",
            "建议方案": [
                "检查URL是否失效",
                "使用浏览器引擎重新抓取准则全文",
                "参考中国审计年鉴收录版本"
            ],
            "优先级": "中",
            "状态": "待处理"
        })
    else:
        with open(standard_file, 'r', encoding='utf-8') as f:
            content = f.read()
        if len(content) < 1000:
            invalid_files.append({
                "文件": "20260705_国家审计准则.md",
                "原因": f"抓取数据仅{len(content)}字符，严重不足",
                "原始URL": "https://flk.npc.gov.cn/detail2.html?ZmY4MDg2MDc2MjM3MTE2YzAxNjI3YzIzMDIxNzA4Yzc",
                "建议方案": [
                    "检查URL是否失效",
                    "使用浏览器引擎重新抓取准则全文",
                    "参考中国审计年鉴收录版本"
                ],
                "优先级": "中",
                "状态": "待处理"
            })
    
    return invalid_files

def save_structured_notes():
    """保存结构化笔记"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. 媒体视点数据
    print("\n📊 处理媒体视点数据...")
    media_data = extract_media_data()
    if media_data:
        media_file = OUTPUT_DIR / "20260705_2024年审计整改关键数据.json"
        with open(media_file, 'w', encoding='utf-8') as f:
            json.dump(media_data, f, ensure_ascii=False, indent=2)
        print(f"  ✅ 已保存: {media_file.name}")
        
        # 同时生成Markdown版本
        md_content = f"""# {media_data['标题']}

**来源**: {media_data['来源']}  
**采集时间**: {media_data['采集时间']}

## 关键数据

"""
        for item in media_data.get("关键数据", []):
            md_content += f"### {item['指标']}\n"
            md_content += f"- **数值**: {item['数值']}\n"
            md_content += f"- **原文**: {item['原文']}\n\n"
        
        md_content += f"## 涉及领域\n\n"
        for field in media_data.get("涉及领域", []):
            md_content += f"- {field}\n"
        
        md_content += f"\n## 重点报道\n\n"
        for i, item in enumerate(media_data.get("重点报道", []), 1):
            md_content += f"{i}. {item}\n"
        
        md_file = OUTPUT_DIR / "20260705_2024年审计整改关键数据.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f"  ✅ 已保存: {md_file.name}")
    
    # 2. 地方经验关键词
    print("\n🏛️ 处理地方审计工作经验...")
    local_data = extract_local_experience()
    if local_data:
        local_file = OUTPUT_DIR / "20260705_地方审计工作经验关键词.json"
        with open(local_file, 'w', encoding='utf-8') as f:
            json.dump(local_data, f, ensure_ascii=False, indent=2)
        print(f"  ✅ 已保存: {local_file.name}")
        
        # Markdown版本
        md_content = f"""# {local_data['标题']}

**来源**: {local_data['来源']}  
**采集时间**: {local_data['采集时间']}

"""
        for region, info in local_data.get("地方经验", {}).items():
            if info:
                md_content += f"## {region}\n\n"
                md_content += f"**工作描述**: {info.get('描述', '未提取')}\n\n"
                md_content += f"**关键词**: {', '.join(info.get('关键词', []))}\n\n"
        
        md_file = OUTPUT_DIR / "20260705_地方审计工作经验关键词.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f"  ✅ 已保存: {md_file.name}")
    
    # 3. 无效文件清单
    print("\n⚠️ 标记无效采集文件...")
    invalid_list = mark_invalid_files()
    if invalid_list:
        invalid_file = LOG_DIR / "采集无效文件清单.md"
        
        md_content = f"""# 审计情报采集-无效文件清单

## 2026-07-05

"""
        for i, item in enumerate(invalid_list, 1):
            md_content += f"### {i}. {item.get('文件', '未知文件')}\n"
            md_content += f"- **原因**: {item.get('原因', '未知')}\n"
            md_content += f"- **原始URL**: {item.get('原始URL', '')}\n"
            md_content += f"- **建议方案**:\n"
            for j, solution in enumerate(item.get('建议方案', []), 1):
                md_content += f"  {j}. {solution}\n"
            md_content += f"- **优先级**: {item.get('优先级', '待定')}\n"
            md_content += f"- **状态**: {item.get('状态', '待处理')}\n\n"
        
        md_content += "---\n\n*本清单用于追踪审计情报采集器无法自动处理的文件，需人工补充。*\n"
        
        with open(invalid_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f"  ✅ 已保存: {invalid_file.name}")
        
        # 同时保存JSON版本供程序读取
        json_file = LOG_DIR / "采集无效文件清单.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                "date": "2026-07-05",
                "total": len(invalid_list),
                "items": invalid_list
            }, f, ensure_ascii=False, indent=2)
        print(f"  ✅ 已保存: {json_file.name}")
    
    print("\n" + "=" * 60)
    print("  处理完成！")
    print("=" * 60)

if __name__ == "__main__":
    save_structured_notes()
