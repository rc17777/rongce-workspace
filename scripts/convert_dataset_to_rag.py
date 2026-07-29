# -*- coding: utf-8 -*-
"""将审计行业高质量数据集JSON条目转换为Markdown文件 → RAG可索引"""
import sys, os, json
from pathlib import Path
from datetime import date
sys.stdout.reconfigure(encoding='utf-8')

TODAY = date.today().isoformat()
WORKSPACE = Path(r'C:\Users\scrccpa\.openclaw\workspace')
DATASET_DIR = WORKSPACE / 'knowledge' / 'datasets'
MD_OUTPUT = WORKSPACE / 'knowledge' / 'datasets' / '_rag_indexed'

def case_to_md(case):
    """案例→Markdown（含丰富元数据和正文）"""
    bl = case.get('business_line', case.get('audit_type', ''))
    severity = case.get('severity', '')
    title = case.get('title', '')
    summary = case.get('summary', '')
    violation = case.get('violation_category', '')
    subcat = case.get('violation_subcategory', '')
    source = case['provenance'].get('source_file', '')
    source_type = case['provenance'].get('source_type', '')
    is_real = case['provenance'].get('is_real', False)
    keywords = ', '.join(case.get('keywords', []))
    methods = ', '.join(case.get('detection_method', []))
    regs = ', '.join(case.get('regulation', []))
    amount = case.get('amount_range', '')
    
    # 五层穿透
    p = case.get('penetration_chain', {})
    penetration = ''
    if p:
        penetration = '\n'.join(f'- **{k}**：{v}' for k, v in p.items())
    
    md = f"""---
title: "{title}"
business_line: "{bl}"
audit_type: "{bl}"
violation_category: "{violation}"
violation_subcategory: "{subcat}"
severity: "{severity}"
amount_range: "{amount}"
source_type: "{source_type}"
is_real: {str(is_real).lower()}
keywords: [{keywords}]
detection_methods: [{methods}]
regulations: [{regs}]
source_file: "{source}"
dataset_id: "{case.get('id', '')}"
date_collected: "{TODAY}"
---

# {title}

## 摘要
{summary}

## 审计信息
- **业务线**：{bl}
- **违规类别**：{violation}
- **子类型**：{subcat}
- **严重程度**：{severity}
- **涉案金额区间**：{amount}
- **来源**：{source}
- **来源类型**：{source_type}
- **真实性**：{'真实案例' if is_real else '方法论推演'}

## 五层穿透分析
{penetration if penetration else '（待补充）'}

## 关键词
{keywords}

## 关联检测方法
{methods if methods else '（待关联）'}

## 关联法规
{regs if regs else '（待关联）'}
"""
    return md

def method_to_md(m):
    """检测方法→Markdown"""
    return f"""---
title: "{m.get('name', '')}"
type: "detection_method"
layer: "{m.get('layer', '')}"
confidence_level: "{m.get('confidence_level', '')}"
alias: "{m.get('alias', '')}"
business_line: "{m.get('business_line', '通用')}"
keywords: [{', '.join(m.get('keywords', []))}]
dataset_id: "{m.get('id', '')}"
---

# {m.get('name', '')}

## 方法描述
{m.get('method_description', '')}

## 检测逻辑
{m.get('detection_logic', '（待补充）')}

## 输入数据
- 必须：{', '.join(m.get('input_data', {}).get('primary', []))}
- 可选：{', '.join(m.get('input_data', {}).get('optional', []))}

## 技术参数
```python
{m.get('technical_params', {}).get('code_snippet', '# 待补充')}
```

## 误报风险
{chr(10).join('- ' + r for r in m.get('false_positive_risks', [])) if m.get('false_positive_risks') else '（待补充）'}

## 组合规则
{chr(10).join('- ' + r for r in m.get('combination_rules', [])) if m.get('combination_rules') else '（待补充）'}
"""

def regulation_to_md(r):
    """法规→Markdown"""
    return f"""---
title: "{r.get('law_name', '')}"
type: "regulation"
law_level: "{r.get('law_level', '')}"
article: "{r.get('article', '')}"
keywords: [{', '.join(r.get('keywords', []))}]
dataset_id: "{r.get('id', '')}"
---

# {r.get('law_name', '')}

## 基本信息
- **层级**：{r.get('law_level', '')}
- **条款**：{r.get('article', '')}
- **简称**：{r.get('law_short', '')}

## 条款内容
{r.get('content', '')}

## 核心要点
{r.get('key_point', '')}

## 适用场景
{chr(10).join('- ' + s for s in r.get('applicable_scenario', []))}

## 违反后果
{r.get('violation_consequence', '（待补充）')}

## 处罚幅度
{r.get('penalty_range', '（待补充）')}
"""

def pattern_to_md(p):
    """疑点模式→Markdown"""
    bl = p.get('business_line', '')
    chain = p.get('inference_chain', [])
    chain_md = ''
    if chain:
        for step in chain:
            chain_md += f"""
### Step {step.get('step', '')}：{step.get('observation', '')}
- **假设**：{step.get('hypothesis', '')}
- **排除**：{step.get('exclusion', '')}
- **结论**：{step.get('conclusion', '')}
"""
    
    return f"""---
title: "{p.get('name', '')}"
type: "finding_pattern"
confidence: "{p.get('confidence', '')}"
severity_when_confirmed: "{p.get('severity_when_confirmed', '')}"
business_line: "{bl}"
keywords: [{', '.join(p.get('keywords', []))}]
dataset_id: "{p.get('id', '')}"
---

# {p.get('name', '')}

## 信号描述
{p.get('signal_description', '')}

## 推断链
{chain_md if chain_md else '（待补充）'}

## 置信度
**{p.get('confidence', '')}** | 确认后严重程度：{p.get('severity_when_confirmed', '')}

## 误报场景
{chr(10).join('- ' + r for r in p.get('false_positive_scenarios', [])) if p.get('false_positive_scenarios') else '（待补充）'}
"""

def convert_all():
    MD_OUTPUT.mkdir(parents=True, exist_ok=True)
    total = 0
    converted = {}
    
    # 遍历所有数据集JSON文件
    for root, dirs, files in os.walk(DATASET_DIR):
        for f in files:
            if not f.endswith('.json') or 'catalog' in f or 'schema' in f:
                continue
            
            fp = os.path.join(root, f)
            with open(fp, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
            
            if not isinstance(data, list):
                continue
            
            source = os.path.basename(root) if 'entries' in root else os.path.relpath(root, DATASET_DIR).replace('\\', '-')
            count = 0
            
            for item in data:
                t = item.get('type', '')
                title = item.get('title', item.get('name', item.get('law_name', '')))
                if not title:
                    continue
                
                # 安全文件名
                safe_title = title[:40].replace('/', '-').replace('\\', '-').replace(':', '-').replace('"', '').replace('*', '').replace('?', '').replace('<', '').replace('>', '').replace('|', '-').strip()
                safe_id = item.get('id', '').replace('/', '-').replace(':', '-')
                out_name = f"{safe_id}_{safe_title}.md"
                
                if t == 'case':
                    md = case_to_md(item)
                elif t == 'detection_method':
                    md = method_to_md(item)
                elif t == 'regulation':
                    md = regulation_to_md(item)
                elif t == 'finding_pattern':
                    md = pattern_to_md(item)
                else:
                    continue
                
                out_path = MD_OUTPUT / out_name
                with open(out_path, 'w', encoding='utf-8') as fh:
                    fh.write(md)
                
                count += 1
                total += 1
            
            if count > 0:
                converted[source] = count
                print(f"  {source}: {count} entries → .md")
    
    print(f"\n{'='*50}")
    print(f"  转换完成: {total} 个 .md 文件")
    print(f"  输出目录: {MD_OUTPUT}")
    
    # 确认RAG可以索引
    sample = list(MD_OUTPUT.glob('*.md'))[0] if list(MD_OUTPUT.glob('*.md')) else None
    if sample:
        print(f"\n  样本文件: {sample.name}")
        print(f"  路径在 knowledge/ 下: {'knowledge' in str(sample)}")
        print(f"  扩展名: {sample.suffix}")
        print(f"  ✅ RAG可索引: {sample.suffix == '.md' and 'knowledge' in str(sample)}")
    
    return total

if __name__ == '__main__':
    convert_all()
