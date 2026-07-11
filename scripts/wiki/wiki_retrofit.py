#!/usr/bin/env python3
"""
融策 Wiki Frontmatter 批量补全工具
====================================
给所有现有 wiki 页面添加标准化 YAML frontmatter。
基于目录结构自动推断类型和域。
"""

import sys
from pathlib import Path
from datetime import datetime
import re

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

VAULT_PATH = Path(r"C:\Users\scrccpa\Documents\Obsidian Vault")
WIKI_PATH = VAULT_PATH / "wiki"

# 目录路径 → (类型, 域) 映射
DIR_MAPPING = {
    "政府审计\\审计方法": ("专业方法", "政府审计", "审计方法"),
    "政府审计\\政策法规": ("政策法规", "政府审计", ""),
    "政府审计\\概念术语": ("概念术语", "政府审计", ""),
    "政府审计\\分析判断": ("分析判断", "政府审计", ""),
    "政府审计\\业务类型": ("业务类型", "政府审计", ""),
    "政府审计\\项目经验": ("项目经验", "政府审计", ""),
    "工程咨询\\专业方法": ("专业方法", "工程咨询", "专业方法"),
    "工程咨询\\政策规范": ("政策法规", "工程咨询", ""),
    "工程咨询\\分析判断": ("分析判断", "工程咨询", ""),
    "工程咨询\\项目经验": ("项目经验", "工程咨询", ""),
}

# 跨域页面（wiki 根目录下直接放的 .md）
CROSS_DOMAIN_PAGES = {
    "招投标-合规雷区": ("分析判断", "跨域", "招投标"),
    "政府投资项目-全生命周期": ("分析判断", "跨域", "政府投资"),
    "财政资金管理-红线汇编": ("政策法规", "跨域", "财政资金"),
}


def extract_metadata_from_content(content: str) -> dict:
    """从现有页面内容提取元数据"""
    meta = {}
    
    # 提取标题
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if title_match:
        meta["h1_title"] = title_match.group(1).strip()
    
    # 提取来源和类型信息
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("> 来源:"):
            source = line.replace("> 来源:", "").strip()
            # 提取来源标题
            src_match = re.search(r'「([^」]+)」', source)
            if src_match:
                meta["source_title"] = src_match.group(1)
            url_match = re.search(r'\((https?://[^)]+)\)', source)
            if url_match:
                meta["source_url"] = url_match.group(1)
        elif line.startswith("> 类型:"):
            meta["old_type"] = line.replace("> 类型:", "").strip()
        elif line.startswith("> 最近更新:"):
            meta["old_update"] = line.replace("> 最近更新:", "").strip()
    
    # 提取标签（从二级标题推断）
    h2s = re.findall(r'^##\s+(.+)$', content, re.MULTILINE)
    if h2s:
        meta["sections"] = h2s[:5]  # 前5个二级标题
    
    return meta


def infer_tags(page_type: str, domain: str, meta: dict) -> list:
    """推断标签"""
    tags = []
    
    if page_type == "专业方法":
        sections = meta.get("sections", [])
        if any("分析" in s for s in sections):
            tags.append("数据分析")
        if any("查" in s or "核查" in s for s in sections):
            tags.append("核查")
        if any("统计" in s for s in sections):
            tags.append("统计")
        if any("抽样" in s for s in sections):
            tags.append("抽样")
        if any("网络" in s or "关联" in s for s in sections):
            tags.append("网络分析")
    
    elif page_type == "概念术语":
        if "资产" in meta.get("h1_title", ""):
            tags.append("资产")
        if "债务" in meta.get("h1_title", ""):
            tags.append("债务")
        if "采购" in meta.get("h1_title", ""):
            tags.append("采购")
        if "绩效" in meta.get("h1_title", ""):
            tags.append("绩效")
        if "资金" in meta.get("h1_title", ""):
            tags.append("资金")
    
    elif page_type == "分析判断":
        tags.append("分析")
        if "数字" in meta.get("h1_title", ""):
            tags.append("数字化转型")
    
    elif page_type == "政策法规":
        tags.append("法规")
    
    elif page_type == "项目经验":
        tags.append("项目复盘")
    
    if not tags:
        tags.append(domain)
    
    return tags


def generate_frontmatter(page_type: str, domain: str, title: str, 
                         meta: dict, tags: list) -> str:
    """生成 YAML frontmatter"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    source_date = meta.get("old_update", datetime.now().strftime("%Y-%m-%d"))
    
    fm_lines = ["---"]
    fm_lines.append(f"type: {page_type}")
    fm_lines.append(f"domain: {domain}")
    fm_lines.append(f"tags: [{', '.join(tags)}]")
    fm_lines.append("status: published")
    fm_lines.append(f"created: {source_date}")
    fm_lines.append(f"updated: {now}")
    
    if meta.get("source_title"):
        fm_lines.append(f'source_title: "{meta["source_title"]}"')
    if meta.get("source_url"):
        fm_lines.append(f'source_url: {meta["source_url"]}')
    
    # 类型特有字段
    if page_type == "专业方法":
        method_cat = "数据分析" if "数据分析" in tags else "现场核查" if "核查" in tags else "文档审查"
        fm_lines.append(f"method_category: {method_cat}")
    elif page_type == "分析判断":
        fm_lines.append("confidence: medium")
    elif page_type == "概念术语":
        fm_lines.append("aliases: []")
    
    fm_lines.append("---")
    
    return "\n".join(fm_lines)


def add_frontmatter_to_page(filepath: Path, page_type: str, domain: str, 
                            meta: dict, dry_run: bool = False) -> bool:
    """给单个页面添加 frontmatter"""
    content = filepath.read_text(encoding="utf-8")
    
    # 如果已有 frontmatter，跳过
    if content.startswith("---"):
        return False
    
    title = meta.get("h1_title", filepath.stem)
    tags = infer_tags(page_type, domain, meta)
    fm = generate_frontmatter(page_type, domain, title, meta, tags)
    
    new_content = fm + "\n\n" + content
    
    if dry_run:
        print(f"  📝 {filepath.stem} → type={page_type}, domain={domain}, tags={tags}")
        return True
    
    filepath.write_text(new_content, encoding="utf-8")
    print(f"  ✅ {filepath.stem}: {page_type} / {domain} / {tags}")
    return True


def main():
    dry_run = "--dry-run" in sys.argv
    force = "--force" in sys.argv
    
    if dry_run:
        print("🔍 预览模式（--dry-run），不会修改文件\n")
    
    count = 0
    skipped = 0
    
    for md_file in WIKI_PATH.rglob("*.md"):
        if md_file.name in ("index.md", "log.md"):
            continue
        
        content = md_file.read_text(encoding="utf-8")
        
        # 如果已有 frontmatter 且不强制
        if content.startswith("---") and not force:
            skipped += 1
            continue
        
        meta = extract_metadata_from_content(content)
        rel = str(md_file.relative_to(WIKI_PATH))
        
        # 确定类型和域
        page_type = None
        domain = None
        
        # 先检查跨域页面
        if md_file.stem in CROSS_DOMAIN_PAGES:
            page_type, domain, _ = CROSS_DOMAIN_PAGES[md_file.stem]
        else:
            # 根据目录路径匹配
            parent_rel = str(md_file.parent.relative_to(WIKI_PATH))
            for dir_pattern, (pt, dom, _) in DIR_MAPPING.items():
                if parent_rel == dir_pattern or parent_rel.startswith(dir_pattern + "\\"):
                    page_type, domain = pt, dom
                    break
        
        if not page_type:
            print(f"  ⚠️ 无法分类: {md_file.stem} ({rel})")
            skipped += 1
            continue
        
        if add_frontmatter_to_page(md_file, page_type, domain, meta, dry_run):
            count += 1
    
    print(f"\n📊 总计: {count} 页已处理, {skipped} 页跳过")
    
    if not dry_run:
        print("\n💡 提示: 运行 wiki_ingest.py index 重新生成索引")


if __name__ == "__main__":
    main()
