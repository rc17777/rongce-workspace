#!/usr/bin/env python3
"""
中国审计第6期OCR索引重建与优化
- 读取现有JSON索引
- 生成Markdown索引目录
- 输出统计报告
"""

import json, sys
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).parent.parent
VAULT_DIR = Path("C:/Users/scrccpa/Documents/Obsidian Vault")
INDEX_JSON = VAULT_DIR / "中国审计第6期-OCR归档索引.json"
OUTPUT_DIR = BASE_DIR / "output"

def load_index():
    """加载现有索引"""
    with open(INDEX_JSON, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_index_md(data):
    """生成Markdown索引目录"""
    
    # 按场景分组
    by_scene = defaultdict(list)
    for item in data:
        scene = item.get("scene", "未分类")
        by_scene[scene].append(item)
    
    # 统计
    total = len(data)
    scene_counts = {scene: len(items) for scene, items in by_scene.items()}
    
    md = f"""# 中国审计第6期 OCR归档索引

**总计**: {total} 篇  
**OCR时间**: 2026-06-30  
**归档路径**: `C:\\Users\\scrccpa\\Documents\\Obsidian Vault\\审计案例库-OCR\\中国审计第6期\\`

---

## 场景分布统计

"""
    
    for scene in sorted(scene_counts.keys(), key=lambda x: scene_counts[x], reverse=True):
        count = scene_counts[scene]
        percentage = count / total * 100
        md += f"- **{scene}**: {count} 篇 ({percentage:.1f}%)\n"
    
    md += "\n---\n\n"
    
    # 按场景展开
    for scene in sorted(by_scene.keys()):
        items = by_scene[scene]
        md += f"## {scene} ({len(items)} 篇)\n\n"
        
        for i, item in enumerate(items, 1):
            title = item.get("title", "未知标题")
            text_len = item.get("text_length", 0)
            keywords = item.get("keywords", [])[:5]  # 只显示前5个关键词
            
            md += f"### {i}. {title}\n\n"
            md += f"- **文本长度**: {text_len} 字符\n"
            md += f"- **关键词**: {', '.join(keywords)}\n"
            
            # 场景置信度
            scores = item.get("scene_scores", {})
            top_scenes = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
            if top_scenes:
                md += f"- **场景匹配**: "
                md += " / ".join([f"{s}({sc})" for s, sc in top_scenes if sc > 0])
                md += "\n"
            
            # 人工复核备注
            note = item.get("manual_review_note")
            if note:
                md += f"- **人工复核**: {note}\n"
            
            # Obsidian链接
            archive_path = item.get("archive_path", "")
            if archive_path:
                # 转为相对路径用于Obsidian内部链接
                rel_path = archive_path.replace("C:\\Users\\scrccpa\\Documents\\Obsidian Vault\\", "")
                rel_path = rel_path.replace("\\", "/")
                md += f"- **文件**: `[[{title}]]`\n"
            
            md += "\n"
        
        md += "---\n\n"
    
    return md

def generate_statistics(data):
    """生成统计报告"""
    
    total = len(data)
    
    # 场景分布
    by_scene = defaultdict(int)
    for item in data:
        by_scene[item.get("scene", "未分类")] += 1
    
    # 文本长度统计
    lengths = [item.get("text_length", 0) for item in data]
    avg_length = sum(lengths) / len(lengths) if lengths else 0
    min_length = min(lengths) if lengths else 0
    max_length = max(lengths) if lengths else 0
    
    # 关键词统计
    all_keywords = []
    for item in data:
        all_keywords.extend(item.get("keywords", []))
    
    keyword_freq = defaultdict(int)
    for kw in all_keywords:
        keyword_freq[kw] += 1
    
    top_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:20]
    
    # 人工复核统计
    manual_reviewed = sum(1 for item in data if item.get("manual_review_note"))
    
    report = f"""# 中国审计第6期 统计报告

## 基本信息

- **总篇数**: {total}
- **OCR完成时间**: 2026-06-30
- **人工复核篇数**: {manual_reviewed}

## 场景分布

"""
    
    for scene, count in sorted(by_scene.items(), key=lambda x: x[1], reverse=True):
        percentage = count / total * 100
        bar = "█" * int(percentage / 5)
        report += f"- **{scene}**: {count} 篇 ({percentage:.1f}%) {bar}\n"
    
    report += f"""
## 文本长度统计

- **平均长度**: {avg_length:.0f} 字符
- **最短**: {min_length} 字符
- **最长**: {max_length} 字符

## 高频关键词 (Top 20)

"""
    
    for i, (kw, freq) in enumerate(top_keywords, 1):
        report += f"{i}. **{kw}**: {freq} 次\n"
    
    report += f"""
## 场景匹配质量

"""
    
    for item in data:
        title = item.get("title", "")
        scene = item.get("scene", "")
        scores = item.get("scene_scores", {})
        
        # 计算匹配度
        if scores:
            assigned_score = scores.get(scene, 0)
            max_score = max(scores.values())
            confidence = assigned_score / max_score if max_score > 0 else 0
            
            if confidence < 0.5:
                report += f"- ⚠️ **{title}** → {scene} (置信度: {confidence:.1%})\n"
    
    report += "\n---\n\n*统计时间: 2026-07-05*\n"
    
    return report

def main():
    print("=" * 60)
    print("  中国审计第6期 OCR索引重建与优化")
    print("=" * 60)
    
    # 1. 加载现有索引
    print("\n📂 加载现有索引...")
    data = load_index()
    print(f"  ✅ 已加载 {len(data)} 篇文章")
    
    # 2. 生成Markdown索引
    print("\n📄 生成Markdown索引...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    index_md = generate_index_md(data)
    index_file = OUTPUT_DIR / "中国审计第6期_OCR索引目录.md"
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(index_md)
    print(f"  ✅ 已保存: {index_file.name}")
    
    # 3. 生成统计报告
    print("\n📊 生成统计报告...")
    stats = generate_statistics(data)
    stats_file = OUTPUT_DIR / "中国审计第6期_统计报告.md"
    with open(stats_file, 'w', encoding='utf-8') as f:
        f.write(stats)
    print(f"  ✅ 已保存: {stats_file.name}")
    
    # 4. 检查索引完整性
    print("\n🔍 检查索引完整性...")
    issues = []
    
    for item in data:
        title = item.get("title")
        archive_path = item.get("archive_path")
        
        # 检查文件是否存在
        if archive_path and Path(archive_path).exists():
            pass  # OK
        elif archive_path:
            issues.append(f"⚠️ 文件不存在: {title} → {archive_path}")
        else:
            issues.append(f"⚠️ 缺少归档路径: {title}")
    
    if issues:
        print(f"  发现 {len(issues)} 个问题:")
        for issue in issues[:5]:  # 只显示前5个
            print(f"    {issue}")
        if len(issues) > 5:
            print(f"    ... 还有 {len(issues) - 5} 个问题")
    else:
        print("  ✅ 索引完整，所有文件路径有效")
    
    print("\n" + "=" * 60)
    print("  完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()
