#!/usr/bin/env python3
"""
案例归档器 v1.0
将确认的案例存档到本地knowledge/和Obsidian
"""

import json, sys, shutil, hashlib
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

CONFIG = Path(__file__).parent.parent / "config" / "case_sources.json"

def load_config():
    with open(CONFIG, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_markdown(case):
    """生成Markdown格式案例"""
    md = f"""---
title: "{case['title']}"
source: "{case['source']}"
type: "{case['type']}"
scene: "{case['scene']}"
url: "{case['url']}"
collected_at: "{case['collected_at']}"
archived_at: "{datetime.now().isoformat()}"
---

# {case['title']}

**来源**: {case['source']}  
**类型**: {case['type']}  
**场景**: {case['scene']}  
**采集时间**: {case['collected_at']}  
**原文链接**: {case['url']}

---

## 案例摘要

（待补充：需要手动抓取全文或AI提取摘要）

---

## 审计逻辑提炼

（待补充：需要运行 case_extractor.py 自动提取）

---

## 可复用方法

- 场景: {case['scene']}
- 审计方法: （待提取）
- 发现类型: （待提取）
- 问题表述: （待提取）

---

*本案例已纳入融策标准作业体系 v2.0*
"""
    return md

def archive_case(case, config):
    """归档单个案例"""
    scene = case['scene']
    
    # 生成文件名（标题去特殊字符 + 哈希防重）
    safe_title = "".join(c for c in case['title'] if c.isalnum() or c in " -_")[:50]
    file_hash = hashlib.md5(case['url'].encode('utf-8')).hexdigest()[:8]
    filename = f"{safe_title}_{file_hash}.md"
    
    # 存到本地 knowledge/cases/
    knowledge_dir = Path(config['storage']['archive_dir']) / scene
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    knowledge_file = knowledge_dir / filename
    
    # 存到 Obsidian
    obsidian_dir = Path(config['storage']['obsidian_dir']) / scene
    obsidian_dir.mkdir(parents=True, exist_ok=True)
    obsidian_file = obsidian_dir / filename
    
    # 生成并写入Markdown
    md_content = generate_markdown(case)
    
    knowledge_file.write_text(md_content, encoding='utf-8')
    obsidian_file.write_text(md_content, encoding='utf-8')
    
    return {
        "filename": filename,
        "knowledge_path": str(knowledge_file),
        "obsidian_path": str(obsidian_file)
    }

def update_catalog(archived_cases, config):
    """更新审计资料清单"""
    catalog_file = Path(config['storage']['catalog_file'])
    
    if catalog_file.exists():
        with open(catalog_file, 'r', encoding='utf-8') as f:
            catalog = json.load(f)
    else:
        catalog = []
    
    # 追加新案例
    for case in archived_cases:
        catalog.append({
            "path": case['obsidian_path'],
            "filename": case['filename'],
            "scene": case['scene'],
            "title": case['title'],
            "source": case['source'],
            "has_keywords": False,
            "has_findings": False
        })
    
    # 保存
    with open(catalog_file, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已更新审计资料清单: {catalog_file}")

def main():
    if len(sys.argv) < 2:
        print("用法: python case_archiver.py <classified_file.json>")
        print("示例: python case_archiver.py logs/case_collection/pending/pending_20260703_083000_classified.json")
        sys.exit(1)
    
    classified_file = Path(sys.argv[1])
    if not classified_file.exists():
        print(f"❌ 文件不存在: {classified_file}")
        sys.exit(1)
    
    print("=" * 60)
    print("案例归档器 v1.0")
    print("=" * 60)
    
    config = load_config()
    
    with open(classified_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not data.get('confirmed'):
        print("⚠️  案例尚未确认，请先运行确认步骤")
        sys.exit(1)
    
    confirmed_items = data.get('confirmed_items', [])
    if not confirmed_items:
        print("ℹ️  没有需要归档的案例")
        sys.exit(0)
    
    print(f"\n📦 开始归档 {len(confirmed_items)} 条案例...\n")
    
    archived = []
    for i, case in enumerate(confirmed_items, 1):
        print(f"{i}. [{case['scene']}] {case['title'][:50]}")
        result = archive_case(case, config)
        result['title'] = case['title']
        result['scene'] = case['scene']
        result['source'] = case['source']
        archived.append(result)
        print(f"   ✅ 已存档")
    
    # 更新审计资料清单
    print(f"\n📝 更新审计资料清单...")
    update_catalog(archived, config)
    
    print(f"\n{'='*60}")
    print(f"✅ 归档完成：{len(archived)} 条案例")
    print(f"{'='*60}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 归档失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
