#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ABBYY FineReader PDF 15 批量OCR处理脚本
配合 Obsidian 审计案例库使用
"""

import os
import sys
import subprocess
import json
import shutil
from datetime import datetime
from pathlib import Path

# 设置编码
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ============================================================
# 配置区（根据实际情况修改）
# ============================================================

# ABBYY 安装路径（默认路径，如果安装时改了请修改）
ABBYY_PATH = r"C:\Program Files\ABBYY\FineReader PDF 15\FineCmd.exe"
ABBYY_PATH_ALT = r"C:\Program Files (x86)\ABBYY\FineReader PDF 15\FineCmd.exe"

# 源文件目录
SOURCE_DIRS = [
    r"C:\Users\scrccpa\Desktop\审计观察",
    r"C:\Users\scrccpa\Desktop\经济责任审计"
]

# 输出目录
OUTPUT_DIR = r"C:\Users\scrccpa\Documents\Obsidian Vault\审计案例库-OCR-ABBYY"

# ABBYY处理参数
ABBYY_CONFIG = {
    "lang": "ChinesePRC,English",  # 识别语言：简体中文+英文
    "format": "PDF",               # 输出格式：可搜索PDF
    "quality": "High",             # 识别质量：高
    "keepFormat": True,            # 保留格式
    "keepPictures": True,          # 保留图片
    "keepPageNumbers": True,       # 保留页码
}

# ============================================================
# 工具函数
# ============================================================

def find_abbyy():
    """查找ABBYY安装路径"""
    for path in [ABBYY_PATH, ABBYY_PATH_ALT]:
        if os.path.exists(path):
            print(f"[OK] 找到ABBYY: {path}")
            return path
    
    # 尝试搜索
    print("[WARN] 默认路径未找到ABBYY，尝试搜索...")
    for root in [r"C:\Program Files", r"C:\Program Files (x86)"]:
        for dirpath, dirnames, filenames in os.walk(root):
            if "FineCmd.exe" in filenames:
                path = os.path.join(dirpath, "FineCmd.exe")
                print(f"[OK] 搜索到ABBYY: {path}")
                return path
    
    print("[ERROR] 未找到ABBYY FineCmd.exe！")
    print("[INFO] 请确认ABBYY FineReader PDF 15已正确安装")
    print("[INFO] 或手动修改脚本中的 ABBYY_PATH 变量")
    return None

def get_all_pdfs():
    """获取所有PDF文件"""
    pdfs = []
    for source_dir in SOURCE_DIRS:
        if not os.path.exists(source_dir):
            print(f"[WARN] 目录不存在: {source_dir}")
            continue
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if file.lower().endswith('.pdf'):
                    pdfs.append({
                        'path': os.path.join(root, file),
                        'name': file,
                        'folder': os.path.basename(root)
                    })
    return pdfs

def classify_by_filename(filename):
    """基于文件名分类"""
    if any(k in filename for k in ['经济责任', '领导干部', '主要领导', '党政领导', '离任', '任中', '任期']):
        return '经济责任审计'
    if any(k in filename for k in ['预算执行', '预算编制', '决算', '财政收支', '部门预算']):
        return '预算执行审计'
    if any(k in filename for k in ['工程', '建设项目', '招投标', '竣工', '造价', '施工', '基建']):
        return '工程审计'
    if any(k in filename for k in ['国有企业', '国资', '国企改革', '国有资本', '国有资产', '市属企业', '央企']):
        return '国企审计'
    if any(k in filename for k in ['金融', '银行', '保险', '证券', '投融资', '债务', '专项债', '债券', '信贷']):
        return '金融审计'
    if any(k in filename for k in ['资源', '环境', '生态', '污染', '绿色', '能源', '碳中和', 'ESG', '生态文明']):
        return '资源环境审计'
    if any(k in filename for k in ['信息', '数据', '数字化', '智慧审计', '网络安全', '信息系统', '大数据', '人工智能', 'AI', '大模型', '数智']):
        return '信息系统审计'
    if any(k in filename for k in ['绩效', '效益', '效率', '效果', '投入产出']):
        return '绩效审计'
    if any(k in filename for k in ['政策落实', '跟踪审计', '政策措施', '决策部署', '两新', '两重']):
        return '政策落实审计'
    if any(k in filename for k in ['社保', '民生', '养老', '医疗', '医保', '就业', '住房', '救助', '福利', '工伤']):
        return '社保民生审计'
    if any(k in filename for k in ['农业', '农村', '乡村', '粮食', '耕地', '涉农', '农民']):
        return '农业农村审计'
    if any(k in filename for k in ['教育', '学校', '高校', '科研', '科技', '文化', '卫生', '医院', '医疗']):
        return '教科文卫审计'
    if any(k in filename for k in ['内部审计', '内审', '内部控制', '风险管理', '内控', '公司治理']):
        return '内部审计'
    if any(k in filename for k in ['专项', '资金', '补助', '转移支付']):
        return '专项资金审计'
    return '其他审计'

def process_with_abbyy(abbyy_path, input_path, output_path):
    """使用ABBYY处理单个PDF"""
    
    # ABBYY FineCmd 命令行参数
    # 参考: https://help.abbyy.com/finereader-pdf/15/cli/
    cmd = [
        abbyy_path,
        "/input", input_path,
        "/output", output_path,
        "/lang", ABBYY_CONFIG["lang"],
        "/format", ABBYY_CONFIG["format"],
        "/quit",  # 处理完成后退出
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5分钟超时
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            return True, None
        else:
            return False, result.stderr or "未知错误"
    except subprocess.TimeoutExpired:
        return False, "处理超时（超过5分钟）"
    except Exception as e:
        return False, str(e)

def extract_text_from_pdf(pdf_path):
    """从可搜索PDF中提取文本"""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text() + "\n\n"
        doc.close()
        return text
    except ImportError:
        print("[WARN] PyMuPDF未安装，尝试安装...")
        os.system("pip install PyMuPDF -q")
        return extract_text_from_pdf(pdf_path)  # 重试
    except Exception as e:
        return f"[ERROR] 提取文本失败: {e}"

def create_obsidian_note(pdf_info, text, scene, output_dir):
    """创建Obsidian Markdown笔记"""
    
    safe_name = os.path.splitext(pdf_info['name'])[0]
    safe_name = "".join(c for c in safe_name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_name = safe_name.replace(' ', '_') + ".md"
    
    # 提取关键信息
    text_preview = text[:1000].replace('\n', ' ') if text else ""
    
    md_content = f"""---
created: {datetime.now().strftime('%Y-%m-%d %H:%M')}
tags:
  - 审计案例
  - {scene}
  - ABBYY_OCR
source: {pdf_info['path']}
folder: {pdf_info['folder']}
ocr_engine: ABBYY_FineReader_15
---

# {pdf_info['name'].replace('.pdf', '')}

## 基本信息

- **来源**: {pdf_info['path']}
- **场景分类**: {scene}
- **原始文件夹**: {pdf_info['folder']}
- **OCR时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- **OCR引擎**: ABBYY FineReader PDF 15
- **文本长度**: {len(text)} 字符

## 案例摘要

{text_preview}...

## OCR完整文本

<details>
<summary>点击展开完整文本内容（{len(text)}字符）</summary>

```
{text}
```

</details>

## 质量说明

> ✅ **OCR质量提示**
>
> 本文本由ABBYY FineReader PDF 15 Corporate识别生成，质量等级：**高**
> 
> 建议重点核对：
> - [ ] 金额数字（如有）
> - [ ] 日期时间
> - [ ] 人名职务
> - [ ] 单位名称

## 关联案例

- 

## 备注

- 适合用于大模型训练的数据场景: {scene}
- 建议标注标签: #{scene} #审计案例 #ABBYY_OCR

"""
    
    scene_dir = os.path.join(output_dir, scene)
    os.makedirs(scene_dir, exist_ok=True)
    
    md_path = os.path.join(scene_dir, safe_name)
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    return md_path

def main():
    print("=" * 60)
    print("ABBYY FineReader PDF 15 批量OCR处理工具")
    print("=" * 60)
    
    # 1. 查找ABBYY
    print("\n[1/5] 查找ABBYY FineReader...")
    abbyy_path = find_abbyy()
    if not abbyy_path:
        return
    
    # 2. 获取PDF文件
    print("\n[2/5] 扫描PDF文件...")
    pdfs = get_all_pdfs()
    print(f"找到 {len(pdfs)} 个PDF文件")
    
    if not pdfs:
        print("未找到PDF文件！")
        return
    
    # 3. 创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    temp_dir = os.path.join(OUTPUT_DIR, "_temp_pdf")
    os.makedirs(temp_dir, exist_ok=True)
    
    # 4. 处理文件
    print("\n[3/5] 开始ABBYY OCR处理...")
    print(f"提示: 共{len(pdfs)}个文件，ABBYY处理速度约1-3分钟/个")
    print(f"预计总时间: {len(pdfs)}~{len(pdfs)*3} 分钟\n")
    
    processed = 0
    failed = 0
    failed_files = []
    scene_stats = {}
    
    start_time = datetime.now()
    
    for i, pdf_info in enumerate(pdfs, 1):
        print(f"[{i}/{len(pdfs)}] {pdf_info['name'][:50]}...", end=" ")
        
        try:
            # 确定输出路径
            temp_pdf = os.path.join(temp_dir, f"ocr_{i}.pdf")
            
            # ABBYY OCR处理
            success, error = process_with_abbyy(abbyy_path, pdf_info['path'], temp_pdf)
            
            if not success:
                print(f"[FAIL] ABBYY错误: {error}")
                failed += 1
                failed_files.append(f"{pdf_info['name']}: {error}")
                continue
            
            # 提取文本
            text = extract_text_from_pdf(temp_pdf)
            
            if not text or text.startswith("[ERROR]"):
                print(f"[FAIL] 文本提取失败")
                failed += 1
                failed_files.append(f"{pdf_info['name']}: 文本提取失败")
                continue
            
            # 分类
            scene = classify_by_filename(pdf_info['name'])
            
            # 创建Obsidian笔记
            md_path = create_obsidian_note(pdf_info, text, scene, OUTPUT_DIR)
            
            # 统计
            scene_stats[scene] = scene_stats.get(scene, 0) + 1
            processed += 1
            print(f"[OK] {scene} ({len(text)}字)")
            
        except Exception as e:
            print(f"[FAIL] 异常: {e}")
            failed += 1
            failed_files.append(f"{pdf_info['name']}: {e}")
    
    # 清理临时文件
    try:
        shutil.rmtree(temp_dir)
    except:
        pass
    
    # 5. 生成索引
    print("\n[4/5] 生成索引文件...")
    
    elapsed = (datetime.now() - start_time).total_seconds()
    
    index_content = f"""---
created: {datetime.now().strftime('%Y-%m-%d %H:%M')}
tags:
  - 审计案例库
  - 索引
  - ABBYY_OCR
---

# 审计案例库OCR索引（ABBYY版）

> 处理完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}
> OCR引擎: ABBYY FineReader PDF 15 Corporate
> 处理时长: {elapsed/60:.1f} 分钟

## 分类统计

| 审计场景 | 案例数量 |
|:---------|:---------|
"""
    
    for scene, count in sorted(scene_stats.items(), key=lambda x: x[1], reverse=True):
        index_content += f"| [[{scene}]] | {count} |\n"
    
    index_content += f"""
## 处理统计

- **成功处理**: {processed}
- **失败**: {failed}
- **总计**: {len(pdfs)}
- **处理时间**: {elapsed/60:.1f} 分钟
- **平均速度**: {elapsed/len(pdfs)/60:.1f} 分钟/文件

## 失败文件

"""
    if failed_files:
        for f in failed_files:
            index_content += f"- ❌ {f}\n"
    else:
        index_content += "无\n"
    
    index_content += "\n## 快速导航\n\n"
    for scene in sorted(scene_stats.keys()):
        index_content += f"- [[{scene}]]\n"
    
    with open(os.path.join(OUTPUT_DIR, "00-索引.md"), 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    # 6. 生成质量报告
    print("[5/5] 生成质量报告...")
    
    report = f"""# ABBYY OCR处理质量报告

## 处理概况

- **OCR引擎**: ABBYY FineReader PDF 15 Corporate
- **处理时间**: {elapsed/60:.1f} 分钟
- **平均速度**: {elapsed/len(pdfs)/60:.1f} 分钟/文件
- **识别语言**: 简体中文 + 英文

## 质量等级评估

相比PaddleOCR，ABBYY的质量预期：

| 检查项 | 预期准确率 | 校对建议 |
|:-------|:----------|:---------|
| 印刷体文字 | 99%+ | 基本无需校对 |
| 数字金额 | 99%+ | 抽查核对即可 |
| 表格结构 | 95%+ | 复杂表格需检查 |
| 页眉页脚 | 90%+ | 可忽略 |
| 印章覆盖文字 | 70% | 可能漏识别 |

## 后续建议

1. **人工抽查**: 随机抽查10-20个文件的关键数据
2. **表格修复**: 对复杂表格可手动重建结构
3. **补充标签**: 添加案例难度、审计方法等标签
4. **关联建立**: 在Obsidian中建立案例间链接

---

*本报告由自动化脚本生成*
"""
    
    with open(os.path.join(OUTPUT_DIR, "00-质量报告.md"), 'w', encoding='utf-8') as f:
        f.write(report)
    
    # 输出总结
    print("\n" + "=" * 60)
    print("ABBYY OCR处理完成！")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"成功: {processed}, 失败: {failed}")
    print(f"总用时: {elapsed/60:.1f} 分钟")
    print("\n场景分布:")
    for scene, count in sorted(scene_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {scene}: {count}")
    print("=" * 60)
    print("\n✅ 请查看质量报告了解后续校对建议。")

if __name__ == "__main__":
    main()
