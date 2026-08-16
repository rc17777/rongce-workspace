"""急救实训室项目 投标文件关键数据提取"""
import os, re, json

base = r"D:\openclaw-workspace\output\急救实训室_extracted"
bidders = [
    "投标_四川省好医助医疗器械有限公司.txt",
    "投标_成都易可天地科技有限公司.txt",
    "投标_江西正好医疗器械有限公司.txt",
]

results = {}

for f in bidders:
    name = f.replace("投标_", "").replace(".txt", "")
    text = open(os.path.join(base, f), 'r', encoding='utf-8').read()
    
    data = {"file": f, "name": name, "chars": len(text)}
    
    # 1. 投标函 - 投标有效期
    m = re.search(r'投标有效期[:\s]*(\d+)\s*天', text)
    if not m:
        m = re.search(r'投标有效期.*?(\d+)\s*天', text)
    if not m:
        m = re.search(r'投标.*?有效.*?(\d+)\s*[天日]', text)
    data["投标有效期"] = m.group(1) if m else "未找到"
    
    # 2. 报价 - 总价
    # Look for 总报价 pattern
    total_patterns = [
        r'投标总价[：:]\s*[¥￥]?\s*([\d,]+\.?\d*)',
        r'总价[：:]\s*[¥￥]?\s*([\d,]+\.?\d*)',
        r'投标报价[：:]\s*[¥￥]?\s*([\d,]+\.?\d*)',
        r'报价[：:]\s*[¥￥]?\s*([\d,]+\.?\d*)',
        r'大写.*?小写[：:]\s*[¥￥]?\s*([\d,]+\.?\d*)',
        r'小写[：:]\s*[¥￥]?\s*([\d,]+\.?\d*)',
    ]
    total_price = None
    for pat in total_patterns:
        m = re.search(pat, text)
        if m:
            total_price = m.group(1).replace(',', '')
            break
    data["总报价"] = total_price if total_price else "未找到"
    
    # 3. 中小微企业声明
    has_sme = bool(re.search(r'(小型企业|微型企业|中小微企业)', text))
    data["中小企业"] = has_sme
    
    # 4. 质保期
    m = re.search(r'质保期[：:]\s*(\d+)\s*年', text)
    if not m:
        m = re.search(r'质保.*?(\d+)\s*年', text)
    data["质保期(年)"] = m.group(1) if m else "未找到"
    
    # 5. 注册地
    m = re.search(r'(?:地址|注册地|住所)[：:]\s*(.{5,50})', text)
    data["地址"] = m.group(1).strip() if m else "未找到"
    
    # 6. 法定代表人
    m = re.search(r'(?:法定代表人|负责人)[：:]\s*(.{2,10})', text)
    data["法定代表人"] = m.group(1).strip() if m else "未找到"
    
    # 7. 授权代表
    m = re.search(r'(?:授权代表|委托代理人|被授权人)[：:]\s*(.{2,10})', text)
    data["授权代表"] = m.group(1).strip() if m else "未找到"
    
    # 8. 交货期
    m = re.search(r'交货.*?(\d+)\s*[天日]', text)
    data["交货期"] = m.group(1) if m else "未找到"
    
    # 9. Extract itemized prices
    # Look for price sections
    price_section_start = text.find('报价表')
    if price_section_start >= 0:
        data["报价表位置"] = price_section_start
    
    # 10. 技术要求应答 - check for deviations
    tech_start = text.find('技术')
    data["技术应答长度"] = len(text[tech_start:tech_start+5000]) if tech_start >= 0 else 0
    
    results[name] = data

# Print results
for name, d in results.items():
    print(f"\n{'='*60}")
    print(f"【{name}】")
    for k, v in d.items():
        if k not in ['技术应答长度', '报价表位置']:
            print(f"  {k}: {v}")

# Save JSON
with open(os.path.join(base, '投标关键数据.json'), 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\nSaved to {base}/投标关键数据.json")
