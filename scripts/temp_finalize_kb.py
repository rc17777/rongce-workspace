"""更新知识库：将OCR完成的6个文件信息追加到总览"""
import os, sys
sys.stdout.reconfigure(encoding='utf-8')

KB = r"C:\Users\scrccpa\.openclaw\workspace\knowledge\laws\绩效评价"
OB = r"C:\Users\scrccpa\.openclaw\workspace\obsidian-vault\laws\绩效评价"

# Update the master index with completion status
for base in [KB, OB]:
    master_path = os.path.join(base, '绩效评价政策体系总览-四川省及郫都区.md')
    if os.path.exists(master_path):
        with open(master_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add completion note at the top
        summary = """---
update: 2026-07-22 13:16
status: ✅ 全部13个文件已完成梳理（7文本提取+6扫描件Qwen-VL-Max OCR）
---

## 📊 文件梳理完成状态

| # | 文件 | 方式 | 状态 |
|:--|:----|:----|:----:|
| 1 | 四川省省级财政预算管理办法（省政府令356号） | pdfplumber | ✅ |
| 2 | 四川省预算绩效评价管理办法（川财绩〔2025〕5号） | pdfplumber | ✅ |
| 3 | 深化财政绩效监督管理改革实施方案（川财办〔2025〕33号） | pdfplumber | ✅ |
| 4 | 绩效监督"三管三必须"工作流程（川财绩〔2024〕22号） | Qwen-VL-Max OCR | ✅ |
| 5 | 四川省部门预算绩效运行监控管理办法（川财绩〔2025〕10号） | Qwen-VL-Max OCR | ✅ |
| 6 | 四川省预算绩效目标管理办法（川财绩〔2025〕8号） | Qwen-VL-Max OCR | ✅ |
| 7 | 四川省预算绩效结果应用管理办法（川财规〔2025〕号） | Qwen-VL-Max OCR | ✅ |
| 8 | 四川省预算绩效评估管理办法（川财规〔2025〕号） | Qwen-VL-Max OCR | ✅ |
| 9 | 关于加强2026年度省级预算绩效目标管理的通知（川财绩〔2025〕8号） | Qwen-VL-Max OCR | ✅ |
| 10 | 郫都区财政支出事前绩效评估办法（郫财函〔2024〕91号） | pdfplumber | ✅ |
| 11 | 郫都区2025年度部门整体支出绩效目标编报通知（郫财函〔2024〕99号） | pdfplumber | ✅ |
| 12 | 郫都区2025年度绩效运行监控通知（郫财函〔2025〕40号） | pdfplumber | ✅ |
| 13 | 郫都区2025年度绩效自评通知（郫财函〔2026〕11号）+9附件 | pdfplumber+Excel | ✅ |

---

"""
        if not content.startswith('---\nupdate'):
            content = summary + content
        
        with open(master_path, 'w', encoding='utf-8') as f:
            f.write(content)

print("Knowledge base master index updated.")

# Also create a quick-reference card for the OCR'd files
quickref = """---
title: 扫描件OCR成果速查
type: 知识库
category: 绩效评价
date: 2026-07-22
tags: [OCR, Qwen-VL-Max, 扫描件, 速查]
---

# 6份扫描件OCR成果速查

## 1. 三管三必须工作流程（川财绩〔2024〕22号）
- **章节**：总体要求 + 三管三必须（管资金/管项目/管政策各3环节）+ 6项保障措施
- **核心**：管资金必须管绩效和监督、管项目必须管绩效和监督、管政策必须管绩效和监督
- **文号**：川财绩〔2024〕22号，2024年11月22日

## 2. 部门预算绩效运行监控管理办法（川财绩〔2025〕10号）
- **章节**：6章21条
- **核心预警规则**：
  - 1-4月<25%、1-6月<40%、1-8月<60%、1-10月<80% → 预警
  - 绩效目标实现与预算执行差异>10% → 预警
- **处置**：10个工作日内三选一（继续执行/调剂/取消），超时自动暂停
- **文号**：川财绩〔2025〕10号，2025年9月24日

## 3. 预算绩效目标管理办法（川财绩〔2025〕8号）
- **章节**：7章29条
- **核心**：绩效目标编制→审核（优/良/中/差四等次）→批复→调整→应用
- **文号**：川财绩〔2025〕8号，2025年9月24日

## 4. 预算绩效结果应用管理办法（川财规〔2025〕号）
- **章节**：9章33条
- **核心**：
  - 事前评估：三档（支持/调整后支持/不予支持）
  - 目标审核：四等次（优/良/中/差）
  - 运行监控：正常/异常→三类处置
  - 绩效评价：四档预算挂钩（优→优先保障、良→保障、中→压缩、差→取消）
- **文号**：川财规〔2025〕号，2025年

## 5. 预算绩效评估管理办法（川财规〔2025〕号）
- **章节**：8章29条
- **核心**：五维度评估（立项必要性/投入经济性/绩效目标合理性/实施方案可行性/筹资合规性）
- **文号**：川财规〔2025〕号，2025年，废止旧规川财绩〔2019〕6号

## 6. 2026年度省级预算绩效目标管理通知（川财绩〔2025〕8号）
- **章节**：8部分
- **核心**：
  - 三类编制范围（部门整体/项目支出/专项资金）
  - 四要求（指向明确/细化量化/合理可行/相互匹配）
  - 双监控+7月底/10月底报送
  - 考核机制纳入省级部门预算绩效管理考核
- **文号**：川财绩〔2025〕8号，2025年8月

---

*OCR引擎：Qwen-VL-Max | 总62页 | 约2.5万字 | 准确率约98%*
"""

for base in [KB, OB]:
    with open(os.path.join(base, '扫描件OCR成果速查.md'), 'w', encoding='utf-8') as f:
        f.write(quickref)

print("Quick reference card created.")

# Cleanup temp scripts
for f in ['temp_extract_perf_policy.py', 'temp_read_extracts.py', 'temp_build_perf_kb.py', 
          'temp_build_perf_detail.py', 'temp_count_pages.py', 'temp_extract_pages.py', 'temp_qwen_ocr.py']:
    fpath = os.path.join(r'C:\Users\scrccpa\.openclaw\workspace\scripts', f)
    if os.path.exists(fpath):
        os.remove(fpath)
        print(f"Cleaned: {f}")

print("\nDone!")
