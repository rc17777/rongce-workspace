#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
法规政策自动入库 v1.0
====================
自动分类法规/政策文件，存入 RAG 知识库 + Obsidian，触发索引重建。

用法：
  # 处理单个文件
  python scripts/ingest_laws.py --file "新法规.docx"
  
  # 批量处理 _incoming/ 目录下所有待入库文件
  python scripts/ingest_laws.py --batch
  
  # 不重建索引（积累多条后再手动重建）
  python scripts/ingest_laws.py --file "xxx.md" --no-rebuild

流程：
  1. 读取文件内容（.md / .txt / .docx）
  2. 自动分类：法律/行政法规/部门规章/政策文件/司法解释
  3. 提取标题、机关、日期
  4. 生成标准化文件名
  5. 保存到 knowledge/laws/ + obsidian-vault/
  6. 重建 RAG 索引
"""
import sys, io, os, re, shutil, time
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(r'D:\openclaw-workspace')
INCOMING_DIR = ROOT / 'knowledge' / 'laws' / '_incoming'
LAWS_DIR = ROOT / 'knowledge' / 'laws'
OBSIDIAN_DIR = ROOT / 'obsidian-vault' / 'laws'
TZ = timezone(timedelta(hours=8))

# ============================================================
# 分类规则
# ============================================================
CATEGORY_RULES = {
    '法律': {
        'keywords': ['中华人民共和国', '全国人民代表大会', '主席令', '法'],
        'patterns': [r'第[一二三四五六七八九十\d]+号'],
        'target_dir': 'laws',
    },
    '行政法规': {
        'keywords': ['国务院令', '国务院第', '条例'],
        'patterns': [r'国务院令第\d+号'],
        'target_dir': 'laws',
    },
    '部门规章': {
        'keywords': ['审计署令', '财政部令', '财会', '财预', '审计署第'],
        'patterns': [r'(审计署|财政部)令第\d+号'],
        'target_dir': 'laws',
    },
    '政策文件': {
        'keywords': ['意见', '通知', '办法', '方案', '规定', '关于印发'],
        'patterns': [r'(国发|国办发|财办)\[\d{4}\]\d+号'],
        'target_dir': 'laws',
    },
}

def classify_document(text: str, filename: str) -> dict:
    """自动分类文档"""
    head = text[:2000].replace('\n', ' ').replace('#', '')
    fname = filename.lower()
    
    scores = {}
    for cat, rules in CATEGORY_RULES.items():
        score = 0
        for kw in rules['keywords']:
            if kw in head or kw in fname:
                score += 2
        for pat in rules['patterns']:
            if re.search(pat, head):
                score += 3
        scores[cat] = score
    
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        best = '政策文件'  # 默认归类
    
    # 提取元信息
    title = filename.replace('.md', '').replace('.txt', '').replace('.docx', '')
    m = re.search(r'《([^》]+)》', head)
    if m:
        title = m.group(1)
    
    # 提取文号
    doc_id = ''
    m = re.search(r'((?:国务院|审计署|财政部|国发|国办发|财会|财预)[\s\S]{0,30}?第?\d+[号令])', head)
    if m:
        doc_id = m.group(1).strip()
    
    # 提取日期
    doc_date = datetime.now(TZ).strftime('%Y-%m-%d')
    m = re.search(r'(20\d{2})[年\-.](\d{1,2})[月\-.](\d{1,2})', head)
    if m:
        doc_date = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    
    return {
        'category': best,
        'title': title,
        'doc_id': doc_id,
        'date': doc_date,
        'target_dir': CATEGORY_RULES[best]['target_dir'],
    }


def standardize_filename(meta: dict, original: str) -> str:
    """生成标准化文件名"""
    ext = Path(original).suffix or '.md'
    title = meta['title'][:80].strip()
    title = re.sub(r'[\\/:*?"<>|]', '', title)
    
    parts = [title]
    if meta['doc_id']:
        parts.append(meta['doc_id'].replace(' ', ''))
    if meta['date']:
        parts.append(meta['date'])
    
    return '-'.join(parts) + ext


def read_file(filepath: Path) -> str:
    """读取文件内容"""
    ext = filepath.suffix.lower()
    if ext in ('.txt', '.md'):
        return filepath.read_text(encoding='utf-8')
    elif ext == '.docx':
        try:
            from docx import Document
            doc = Document(str(filepath))
            return '\n'.join([p.text for p in doc.paragraphs if p.text.strip()])
        except ImportError:
            raise RuntimeError("需要 python-docx: pip install python-docx")
    else:
        raise RuntimeError(f"不支持格式: {ext}")


def generate_obsidian_md(text: str, meta: dict, source_file: str) -> str:
    """生成 Obsidian 格式 Markdown（含 YAML frontmatter + 标签）"""
    
    tags = [f'法规/{meta["category"]}']
    
    # 子标签
    if '审计' in meta['title']:
        tags.append('审计法规')
    if '政府' in meta['title']:
        tags.append('政府管理')
    if '采购' in meta['title'] or '招标' in meta['title'] or '投标' in meta['title']:
        tags.append('采购招标')
    if '预算' in meta['title']:
        tags.append('预算管理')
    if '会计' in meta['title'] or '财务' in meta['title']:
        tags.append('会计财务')
    if '工程' in meta['title'] or '投资' in meta['title'] or '建设' in meta['title']:
        tags.append('工程投资')
    if '经济责任' in meta['title'] or '领导干部' in meta['title']:
        tags.append('经济责任')
    if '绩效' in meta['title']:
        tags.append('绩效评价')
    if '内控' in meta['title'] or '内部控制' in meta['title']:
        tags.append('内控合规')
    
    tag_str = '\n  - '.join(tags)
    
    frontmatter = f'''---
title: "{meta['title']}"
category: {meta['category']}
publish_date: {meta['date']}
doc_id: "{meta['doc_id']}"
source_file: "{source_file}"
ingest_date: {datetime.now(TZ).strftime('%Y-%m-%d')}
tags:
  - {tag_str}
---

'''
    
    return frontmatter + text


def rebuild_rag():
    """重建 RAG 索引"""
    rebuild_script = ROOT.parent / 'scripts' / 'rag_rebuild.py'
    # Try both workspace paths
    for path in [
        Path(r'C:\Users\scrccpa\.openclaw\workspace\scripts\rag_rebuild.py'),
        ROOT.parent / 'scripts' / 'rag_rebuild.py',
    ]:
        if path.exists():
            import subprocess
            result = subprocess.run([sys.executable, str(path)], capture_output=True, text=True, timeout=600)
            return result.returncode == 0
    return False


def ingest_file(filepath: str, rebuild: bool = True) -> dict:
    """入库单个文件"""
    fp = Path(filepath)
    if not fp.exists():
        return {'error': f'文件不存在: {filepath}', 'status': 'failed'}
    
    print(f"\n{'='*60}")
    print(f"  📥 法规自动入库: {fp.name}")
    print(f"{'='*60}")
    
    # 1. 读取
    print(f"  [1/5] 读取文件...")
    text = read_file(fp)
    print(f"        {len(text)} 字符")
    
    # 2. 分类
    print(f"  [2/5] 自动分类...")
    meta = classify_document(text, fp.name)
    print(f"        类别: {meta['category']}")
    print(f"        标题: {meta['title'][:60]}")
    if meta['doc_id']:
        print(f"        文号: {meta['doc_id']}")
    
    # 3. 生成文件名
    new_name = standardize_filename(meta, fp.name)
    print(f"  [3/5] 保存文件...")
    
    # 保存到 knowledge/laws/
    LAWS_DIR.mkdir(parents=True, exist_ok=True)
    dest_laws = LAWS_DIR / new_name
    if fp.suffix.lower() == '.docx':
        # .docx → .md
        dest_laws = LAWS_DIR / (Path(new_name).stem + '.md')
        dest_laws.write_text(text, encoding='utf-8')
    else:
        if fp.resolve() != dest_laws.resolve():
            shutil.copy2(fp, dest_laws)
    print(f"        knowledge/laws/{dest_laws.name}")
    
    # 保存到 Obsidian
    OBSIDIAN_DIR.mkdir(parents=True, exist_ok=True)
    obsidian_content = generate_obsidian_md(text, meta, dest_laws.name)
    dest_obsidian = OBSIDIAN_DIR / (Path(new_name).stem + '.md')
    dest_obsidian.write_text(obsidian_content, encoding='utf-8')
    print(f"        obsidian-vault/laws/{dest_obsidian.name}")
    
    # 4. 移除原文件（如果在 _incoming/ 下）
    if '_incoming' in str(fp):
        print(f"  [4/5] 清理临时文件...")
        fp.unlink(missing_ok=True)
        print(f"        已删除: {fp.name}")
    else:
        print(f"  [4/5] 保留原文件")
    
    # 5. 重建索引
    if rebuild:
        print(f"  [5/5] 重建 RAG 索引...")
        ok = rebuild_rag()
        if ok:
            print(f"        ✅ 索引已更新")
        else:
            print(f"        ⚠️ 索引重建失败，请手动运行: python scripts/rag_rebuild.py")
    else:
        print(f"  [5/5] 跳过索引重建（--no-rebuild）")
    
    print(f"\n  ✅ 入库完成: {meta['title'][:50]}")
    
    return {
        'status': 'success',
        'original': str(fp),
        'title': meta['title'],
        'category': meta['category'],
        'doc_id': meta['doc_id'],
        'dest_laws': str(dest_laws),
        'dest_obsidian': str(dest_obsidian),
    }


def ingest_batch(rebuild: bool = True) -> list:
    """批量处理 _incoming/ 目录"""
    INCOMING_DIR.mkdir(parents=True, exist_ok=True)
    
    files = list(INCOMING_DIR.glob('*'))
    supported = [f for f in files if f.suffix.lower() in ('.md', '.txt', '.docx')]
    
    if not supported:
        print("📭 _incoming/ 目录为空，没有待入库文件")
        return []
    
    print(f"\n📦 发现 {len(supported)} 个待入库文件")
    results = []
    
    for i, f in enumerate(supported, 1):
        print(f"\n[{i}/{len(supported)}]")
        result = ingest_file(str(f), rebuild=False)  # 最后一次性重建
        results.append(result)
    
    # 全部入库后一次性重建
    if rebuild and any(r['status'] == 'success' for r in results):
        print(f"\n{'='*60}")
        print(f"  🔄 一次性重建 RAG 索引...")
        ok = rebuild_rag()
        print(f"  {'✅ 完成' if ok else '⚠️ 失败，请手动重建'}")
        print(f"{'='*60}")
    
    return results


# ============================================================
# CLI
# ============================================================
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='法规政策自动入库')
    parser.add_argument('--file', '-f', help='单个文件路径')
    parser.add_argument('--batch', '-b', action='store_true', help='批量处理 _incoming/ 目录')
    parser.add_argument('--no-rebuild', action='store_true', help='不重建 RAG 索引')
    
    args = parser.parse_args()
    
    if args.batch:
        ingest_batch(rebuild=not args.no_rebuild)
    elif args.file:
        ingest_file(args.file, rebuild=not args.no_rebuild)
    else:
        parser.print_help()
