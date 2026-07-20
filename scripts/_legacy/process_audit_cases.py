#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
审计案例文件处理脚本
1. 扫描指定目录的PDF文件
2. 提取PDF文本内容
3. 按审计场景分类
4. 生成Obsidian Markdown文件
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime

# 配置路径
SOURCE_DIRS = [
    r"C:\Users\scrccpa\Desktop\审计观察",
    r"C:\Users\scrccpa\Desktop\经济责任审计"
]
OBSIDIAN_VAULT = r"C:\Users\scrccpa\Documents\Obsidian Vault"
OUTPUT_DIR = os.path.join(OBSIDIAN_VAULT, "审计案例库")

def get_pdf_files():
    """获取所有PDF文件"""
    pdf_files = []
    for source_dir in SOURCE_DIRS:
        if os.path.exists(source_dir):
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        pdf_files.append({
                            'path': os.path.join(root, file),
                            'name': file,
                            'folder': os.path.basename(root)
                        })
    return pdf_files

def extract_text_from_pdf(pdf_path):
    """提取PDF文本内容"""
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
    except Exception as e:
        print(f"PyPDF2失败，尝试pdfplumber: {e}")
        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except Exception as e2:
            print(f"pdfplumber也失败: {e2}")
            return ""

def analyze_content(text, filename):
    """分析内容，确定审计场景分类"""
    # 定义关键词映射
    scene_keywords = {
        "经济责任审计": ["经济责任", "领导干部", "任期", "离任", "任中", "履职", "廉政", "权力运行"],
        "预算执行审计": ["预算执行", "预算编制", "决算", "财政收支", "预算管理", "国库集中支付"],
        "专项资金审计": ["专项资金", "社保", "养老", "医疗", "教育", "扶贫", "补贴", "惠农"],
        "工程审计": ["工程", "建设项目", "招投标", "竣工决算", "造价", "施工", "监理"],
        "国企审计": ["国有企业", "国资", "国企改革", "国有资本", "国有资产", "市属企业"],
        "内部审计": ["内部审计", "内审", "单位内部", "内部控制", "风险管理"],
        "绩效审计": ["绩效", "绩效评价", "效益", "效率", "效果", "成本效益"],
        "信息系统审计": ["信息系统", "数据安全", "网络安全", "信息化", "数字化", "智慧"],
        "资源环境审计": ["自然资源", "生态环境", "节能减排", "碳中和", "ESG", "环保"],
        "金融审计": ["金融", "银行", "保险", "证券", "投融资", "债务", "专项债"],
        "政策落实审计": ["政策落实", "跟踪审计", "稳增长", "促改革", "调结构", "惠民生"],
        "农业农村审计": ["农业", "农村", "乡村振兴", "粮食", "耕地", "涉农"],
        "教科文卫审计": ["教育", "科技", "文化", "卫生", "医院", "学校", "科研"],
        "社保民生审计": ["社会保障", "民生", "就业", "住房", "救助", "福利"]
    }
    
    text_lower = text.lower()
    scores = {}
    
    for scene, keywords in scene_keywords.items():
        score = 0
        for keyword in keywords:
            count = text_lower.count(keyword.lower())
            score += count
        scores[scene] = score
    
    # 获取最高分的场景
    if scores:
        max_score = max(scores.values())
        if max_score > 0:
            best_scenes = [s for s, v in scores.items() if v == max_score]
            return best_scenes[0]
    
    return "其他审计"

def extract_key_findings(text):
    """提取关键审计发现"""
    findings = []
    
    # 常见发现模式
    patterns = [
        r"([一二三四五六七八九十]+、.*?问题.*?[。；]\s*)",
        r"(发现.*?问题[：:]\s*.*?[。；])",
        r"(主要问题[：:]\s*.*?[。；])",
        r"(存在.*?问题[：:]\s*.*?[。；])"
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches[:5]:  # 限制数量
            clean = match.strip().replace('\n', ' ')
            if len(clean) > 20 and len(clean) < 500:
                findings.append(clean)
    
    return findings[:10]  # 最多返回10个

def extract_recommendations(text):
    """提取审计建议"""
    recommendations = []
    
    patterns = [
        r"(建议[：:]\s*.*?[。；])",
        r"(审计建议[：:]\s*.*?[。；])",
        r"(提出以下建议[：:]\s*.*?[。；])"
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches[:5]:
            clean = match.strip().replace('\n', ' ')
            if len(clean) > 20 and len(clean) < 500:
                recommendations.append(clean)
    
    return recommendations[:10]

def create_markdown(pdf_info, text, scene):
    """创建Obsidian Markdown文件"""
    # 提取关键信息
    findings = extract_key_findings(text)
    recommendations = extract_recommendations(text)
    
    # 生成文件名
    safe_name = re.sub(r'[\\/*?:"<>|]', "_", pdf_info['name'])
    safe_name = safe_name.replace('.pdf', '.md')
    
    # 构建Markdown内容
    md_content = f"""---
created: {datetime.now().strftime('%Y-%m-%d %H:%M')}
tags:
  - 审计案例
  - {scene}
source: {pdf_info['path']}
folder: {pdf_info['folder']}
---

# {pdf_info['name'].replace('.pdf', '')}

## 基本信息

- **来源**: {pdf_info['path']}
- **场景分类**: {scene}
- **原始文件夹**: {pdf_info['folder']}
- **处理时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 案例摘要

{text[:500].replace(chr(10), ' ') if text else '（无法提取文本内容）'}...

## 审计发现

"""
    
    if findings:
        for i, finding in enumerate(findings, 1):
            md_content += f"{i}. {finding}\n"
    else:
        md_content += "（未能自动提取关键发现，请手动补充）\n"
    
    md_content += "\n## 审计建议\n\n"
    
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            md_content += f"{i}. {rec}\n"
    else:
        md_content += "（未能自动提取建议，请手动补充）\n"
    
    md_content += f"""
## 完整内容

<details>
<summary>点击展开完整文本内容</summary>

```
{text}
```

</details>

## 关联案例

- 

## 备注

- 
"""
    
    return safe_name, md_content

def main():
    # 设置编码
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    print("=" * 60)
    print("审计案例文件处理工具")
    print("=" * 60)
    
    # 检查依赖
    try:
        import PyPDF2
    except ImportError:
        print("警告: PyPDF2未安装，尝试安装...")
        os.system("pip install PyPDF2 pdfplumber -q")
    
    # 获取PDF文件
    print("\n[1/4] 扫描PDF文件...")
    pdf_files = get_pdf_files()
    print(f"找到 {len(pdf_files)} 个PDF文件")
    
    if not pdf_files:
        print("未找到PDF文件，请检查路径！")
        return
    
    # 创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 分类统计
    scene_stats = {}
    processed = 0
    failed = 0
    
    print("\n[2/4] 处理PDF文件...")
    for i, pdf_info in enumerate(pdf_files, 1):
        print(f"  [{i}/{len(pdf_files)}] {pdf_info['name'][:50]}...", end=" ")
        
        try:
            # 提取文本
            text = extract_text_from_pdf(pdf_info['path'])
            
            if not text:
                print("[无文本内容]")
                failed += 1
                continue
            
            # 分析场景
            scene = analyze_content(text, pdf_info['name'])
            
            # 创建场景子目录
            scene_dir = os.path.join(OUTPUT_DIR, scene)
            os.makedirs(scene_dir, exist_ok=True)
            
            # 生成Markdown
            safe_name, md_content = create_markdown(pdf_info, text, scene)
            md_path = os.path.join(scene_dir, safe_name)
            
            # 写入文件
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            # 统计
            scene_stats[scene] = scene_stats.get(scene, 0) + 1
            processed += 1
            print(f"[OK -> {scene}]")
            
        except Exception as e:
            print(f"[错误: {e}]")
            failed += 1
    
    # 生成分类索引
    print("\n[3/4] 生成分类索引...")
    index_content = """---
created: {date}
tags:
  - 审计案例库
  - 索引
---

# 审计案例库索引

> 自动生成于 {date}

## 分类统计

| 审计场景 | 案例数量 |
|:---------|:---------|
""".format(date=datetime.now().strftime('%Y-%m-%d %H:%M'))
    
    for scene, count in sorted(scene_stats.items(), key=lambda x: x[1], reverse=True):
        index_content += f"| [[{scene}]] | {count} |\n"
    
    index_content += f"""
## 总计

- **成功处理**: {processed}
- **失败**: {failed}
- **总计**: {len(pdf_files)}

## 快速导航

"""
    
    for scene in sorted(scene_stats.keys()):
        index_content += f"- [[{scene}]]\n"
    
    # 写入索引
    index_path = os.path.join(OUTPUT_DIR, "00-索引.md")
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    # 生成场景分析总结
    print("\n[4/4] 生成场景分析总结...")
    summary_content = generate_summary(scene_stats, pdf_files)
    summary_path = os.path.join(OUTPUT_DIR, "00-场景分析总结.md")
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary_content)
    
    print("\n" + "=" * 60)
    print("处理完成！")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"成功: {processed}, 失败: {failed}")
    print("=" * 60)

def generate_summary(scene_stats, pdf_files):
    """生成场景分析总结"""
    summary = """---
created: {date}
tags:
  - 审计案例库
  - 分析总结
---

# 审计案例场景分析总结

> 基于 {total} 个案例的自动分析

## 一、场景分布概览

""".format(date=datetime.now().strftime('%Y-%m-%d %H:%M'), total=len(pdf_files))
    
    # 场景分布
    for scene, count in sorted(scene_stats.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(pdf_files)) * 100
        summary += f"### {scene} ({count}个, {percentage:.1f}%)\n\n"
        summary += f"**特点**: \n\n"
        summary += f"**常见审计重点**: \n\n"
        summary += f"**典型问题类型**: \n\n"
        summary += "---\n\n"
    
    summary += """## 二、业务场景归纳

### 2.1 财政财务审计类

涵盖场景：预算执行审计、专项资金审计、绩效审计

**核心关注点**:
- 预算编制的科学性和完整性
- 预算执行的合规性和效率
- 专项资金的使用效益
- 财政资金的绩效管理

### 2.2 经济责任审计类

涵盖场景：经济责任审计、国企审计

**核心关注点**:
- 领导干部履职情况
- 重大经济决策程序
- 国有资产保值增值
- 廉政建设和权力运行

### 2.3 投资建设审计类

涵盖场景：工程审计

**核心关注点**:
- 项目立项和招投标合规性
- 工程质量和进度管理
- 投资控制和造价审核
- 竣工决算的真实性

### 2.4 信息系统审计类

涵盖场景：信息系统审计

**核心关注点**:
- 系统安全性和可靠性
- 数据完整性和准确性
- 内部控制有效性
- 数字化转型成效

### 2.5 资源环境审计类

涵盖场景：资源环境审计

**核心关注点**:
- 自然资源资产管理
- 生态环境保护
- 节能减排政策落实
- ESG相关信息披露

### 2.6 民生审计类

涵盖场景：社保民生审计、农业农村审计、教科文卫审计

**核心关注点**:
- 惠民政策落实情况
- 社会保障资金安全
- 教育、医疗等公共服务质量
- 乡村振兴战略实施

## 三、大模型训练建议

### 3.1 数据标注要点

1. **场景标签**: 为每个案例标注主要审计场景（可多标签）
2. **问题类型**: 标注发现问题的具体类型
3. **法规依据**: 提取涉及的法律法规和制度依据
4. **审计方法**: 标注使用的审计技术和方法

### 3.2 训练数据组织

```
审计案例库/
├── 经济责任审计/
│   ├── 案例1.md
│   ├── 案例2.md
│   └── ...
├── 预算执行审计/
│   └── ...
├── 工程审计/
│   └── ...
└── 00-索引.md
```

### 3.3 提示词模板

**案例学习模板**:
```
请学习以下审计案例，分析其主要特点和审计方法：

[案例内容]

要求：
1. 总结该案例的审计重点
2. 分析使用的审计方法
3. 提炼可复用的审计思路
4. 指出需要注意的风险点
```

**场景对比模板**:
```
请对比以下两个审计场景的差异：

场景A: [描述]
场景B: [描述]

要求：
1. 比较审计目标的不同
2. 分析审计方法的差异
3. 总结关注重点的区别
4. 提炼各自的审计要点
```

## 四、持续优化建议

1. **定期更新**: 每月补充新的审计案例
2. **质量审核**: 对自动提取的内容进行人工校对
3. **标签完善**: 补充更细致的标签体系
4. **关联建立**: 建立案例之间的关联关系
5. **反馈收集**: 收集使用过程中的问题和建议

---

*本总结由AI自动生成，建议结合实际业务经验进行完善。*
"""
    
    return summary

if __name__ == "__main__":
    main()
