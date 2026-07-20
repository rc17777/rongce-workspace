#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
审计案例文件处理脚本 v3 - 扫描件版本
基于文件名进行智能分类，生成Obsidian结构
"""

import os
import sys
import re
from datetime import datetime

# 设置编码
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

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

def classify_by_filename(filename):
    """基于文件名进行智能分类"""
    
    # 经济责任审计（最高优先级）
    if any(k in filename for k in ['经济责任', '领导干部', '主要领导', '党政领导', '离任', '任中', '任期']):
        return '经济责任审计'
    
    # 预算执行审计
    if any(k in filename for k in ['预算执行', '预算编制', '决算', '财政收支', '部门预算', '预算管理']):
        return '预算执行审计'
    
    # 工程审计
    if any(k in filename for k in ['工程', '建设项目', '招投标', '竣工', '造价', '施工', '基建', '工程结算', '概算']):
        return '工程审计'
    
    # 国企审计
    if any(k in filename for k in ['国有企业', '国资', '国企改革', '国有资本', '国有资产', '市属企业', '央企', '国企领导', '境外投资']):
        return '国企审计'
    
    # 金融审计
    if any(k in filename for k in ['金融', '银行', '保险', '证券', '投融资', '债务', '专项债', '债券', '信贷', '不良资产', '金融风险', '影子银行', '普惠金融', '绿色金融']):
        return '金融审计'
    
    # 资源环境审计
    if any(k in filename for k in ['资源', '环境', '生态', '污染', '绿色', '能源', '碳中和', 'ESG', '生态文明', '海洋生态', '矿产资源', '地热']):
        return '资源环境审计'
    
    # 信息系统审计
    if any(k in filename for k in ['信息', '数据', '数字化', '智慧审计', '网络安全', '信息系统', '大数据', '人工智能', 'AI', '大模型', '数智']):
        return '信息系统审计'
    
    # 绩效审计
    if any(k in filename for k in ['绩效', '效益', '效率', '效果', '投入产出', '绩效目标', '绩效指标', '绩效监控', '绩效评价']):
        return '绩效审计'
    
    # 政策落实审计
    if any(k in filename for k in ['政策落实', '跟踪审计', '政策措施', '决策部署', '重大政策', '政策效果', '两新', '两重']):
        return '政策落实审计'
    
    # 社保民生审计
    if any(k in filename for k in ['社保', '民生', '养老', '医疗', '医保', '就业', '住房', '救助', '福利', '工伤', '共同富裕', '看病贵', '托育']):
        return '社保民生审计'
    
    # 农业农村审计
    if any(k in filename for k in ['农业', '农村', '乡村', '粮食', '耕地', '涉农', '农民', '农产品', '农业补贴', '脱贫攻坚']):
        return '农业农村审计'
    
    # 教科文卫审计
    if any(k in filename for k in ['教育', '学校', '高校', '科研', '科技', '文化', '卫生', '医院', '医疗', '基础科学', '研发', '科技创新']):
        return '教科文卫审计'
    
    # 内部审计
    if any(k in filename for k in ['内部审计', '内审', '内部控制', '风险管理', '内控', '公司治理', '风险防控', '合规管理']):
        return '内部审计'
    
    # 专项资金审计
    if any(k in filename for k in ['专项', '资金', '补助', '转移支付', '项目资金']):
        return '专项资金审计'
    
    return '其他审计'

def create_markdown_stub(pdf_info, scene):
    """创建Obsidian Markdown文件（扫描件占位符版本）"""
    
    # 生成文件名
    safe_name = re.sub(r'[\\/*?:"<>|]', "_", pdf_info['name'])
    safe_name = safe_name.replace('.pdf', '.md')
    
    # 构建Markdown内容
    md_content = f"""---
created: {datetime.now().strftime('%Y-%m-%d %H:%M')}
tags:
  - 审计案例
  - {scene}
  - 扫描件
source: {pdf_info['path']}
folder: {pdf_info['folder']}
---

# {pdf_info['name'].replace('.pdf', '')}

## 基本信息

- **来源**: {pdf_info['path']}
- **场景分类**: {scene}
- **原始文件夹**: {pdf_info['folder']}
- **处理时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- **文件类型**: 扫描件（图片型PDF）

## 状态

> ⚠️ **注意**: 此文件为扫描件，文本内容需要OCR识别后才能提取。
> 
> 建议操作：
> 1. 使用Adobe Acrobat Pro进行OCR识别
> 2. 或使用ABBYY FineReader等OCR工具
> 3. 识别后将文本内容补充到本文件中

## 预期审计场景

基于文件名分析，此案例可能涉及：**{scene}**

## 待补充内容

- [ ] OCR文本内容
- [ ] 关键审计发现
- [ ] 审计建议
- [ ] 法规依据
- [ ] 关联案例

## 备注

- 适合用于大模型训练的数据场景: {scene}
- 建议标注标签: #{scene} #审计案例 #扫描件

## 原始文件链接

[[{pdf_info['name']}]]
"""
    
    return safe_name, md_content

def generate_summary(scene_stats, pdf_files):
    """生成场景分析总结"""
    summary = """---
created: {date}
tags:
  - 审计案例库
  - 分析总结
---

# 审计案例场景分析总结

> 基于 {total} 个案例的文件名分析
> 生成时间: {date}
> **注意**: 所有文件均为扫描件（图片型PDF），需要OCR处理后才能提取完整文本内容

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

## 三、OCR处理建议

### 3.1 推荐工具

1. **Adobe Acrobat Pro**（推荐）
   - 打开PDF → 工具 → 扫描和OCR → 识别文本
   - 支持批量处理
   - 识别准确率较高

2. **ABBYY FineReader**
   - 专业OCR软件
   - 支持中文识别
   - 保留原始格式

3. **在线OCR工具**
   - 百度OCR
   - 腾讯OCR
   - 讯飞OCR

### 3.2 处理流程

```
1. 选择OCR工具
2. 批量导入PDF文件
3. 设置识别语言：中文简体
4. 执行OCR识别
5. 导出为可搜索PDF或文本文件
6. 将文本内容补充到对应的Markdown文件中
```

## 四、大模型训练建议

### 4.1 数据标注要点

1. **场景标签**: 为每个案例标注主要审计场景（可多标签）
2. **问题类型**: 标注发现问题的具体类型
3. **法规依据**: 提取涉及的法律法规和制度依据
4. **审计方法**: 标注使用的审计技术和方法

### 4.2 训练数据组织

```
审计案例库/
├── 经济责任审计/
│   ├── 案例1.md (OCR后补充完整内容)
│   ├── 案例2.md
│   └── ...
├── 预算执行审计/
│   └── ...
├── 工程审计/
│   └── ...
└── 00-索引.md
```

### 4.3 提示词模板

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

## 五、持续优化建议

1. **OCR处理**: 优先处理高频场景的案例文件
2. **质量审核**: 对OCR结果进行人工校对
3. **标签完善**: 补充更细致的标签体系
4. **关联建立**: 建立案例之间的关联关系
5. **定期更新**: 每月补充新的审计案例

---

*本总结由AI自动生成，建议结合实际业务经验进行完善。*
*所有案例文件均为扫描件，需OCR处理后才能用于大模型训练。*
"""
    
    return summary

def main():
    print("=" * 60)
    print("审计案例文件处理工具 v3 - 扫描件版本")
    print("=" * 60)
    
    # 获取PDF文件
    print("\n[1/3] 扫描PDF文件...")
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
    
    print("\n[2/3] 基于文件名分类处理...")
    for i, pdf_info in enumerate(pdf_files, 1):
        print(f"  [{i}/{len(pdf_files)}] {pdf_info['name'][:50]}...", end=" ")
        
        try:
            # 基于文件名分类
            scene = classify_by_filename(pdf_info['name'])
            
            # 创建场景子目录
            scene_dir = os.path.join(OUTPUT_DIR, scene)
            os.makedirs(scene_dir, exist_ok=True)
            
            # 生成Markdown
            safe_name, md_content = create_markdown_stub(pdf_info, scene)
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
    
    # 生成分类索引
    print("\n[3/3] 生成分类索引和总结...")
    
    # 索引
    index_content = """---
created: {date}
tags:
  - 审计案例库
  - 索引
---

# 审计案例库索引

> 自动生成于 {date}
> **注意**: 所有文件均为扫描件，需要OCR处理

## 分类统计

| 审计场景 | 案例数量 |
|:---------|:---------|
""".format(date=datetime.now().strftime('%Y-%m-%d %H:%M'))
    
    for scene, count in sorted(scene_stats.items(), key=lambda x: x[1], reverse=True):
        index_content += f"| [[{scene}]] | {count} |\n"
    
    index_content += f"""
## 总计

- **已处理**: {processed}
- **总计**: {len(pdf_files)}
- **文件类型**: 扫描件（图片型PDF）

## 快速导航

"""
    
    for scene in sorted(scene_stats.keys()):
        index_content += f"- [[{scene}]]\n"
    
    # 写入索引
    index_path = os.path.join(OUTPUT_DIR, "00-索引.md")
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    # 生成场景分析总结
    summary_content = generate_summary(scene_stats, pdf_files)
    summary_path = os.path.join(OUTPUT_DIR, "00-场景分析总结.md")
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary_content)
    
    print("\n" + "=" * 60)
    print("处理完成！")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"成功: {processed}")
    print("\n场景分布:")
    for scene, count in sorted(scene_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {scene}: {count}")
    print("=" * 60)
    print("\n⚠️  重要提示:")
    print("所有PDF文件均为扫描件（图片型PDF），无法直接提取文本。")
    print("请使用Adobe Acrobat Pro或ABBYY FineReader等工具进行OCR识别。")
    print("识别后将文本内容补充到对应的Markdown文件中。")

if __name__ == "__main__":
    main()
