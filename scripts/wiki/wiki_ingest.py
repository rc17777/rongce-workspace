#!/usr/bin/env python3
"""
融策 Wiki 自动摄入工具 (mindloom-style)
=========================================
将文章/文档自动编译为 Obsidian Wiki 页面。

用法:
  wiki_ingest.py add --title "标题" --type 政策法规 --domain 政府审计 --source-url "URL" --source-title "来源" --tags "标签" < content.md
  wiki_ingest.py add --title "标题" --type 专业方法 --domain 政府审计 --source "数审派" --content-file raw/file.md  
  wiki_ingest.py index        # 重新生成 index.md（基于 frontmatter 扫描）
  wiki_ingest.py stats         # 统计信息

设计原则:
  1. 原始文件 → raw/ 目录（永远保留原文）
  2. 编译页面 → wiki/ 目录（结构化，带 YAML frontmatter）
  3. 自动更新 [[index]] 和 [[log]]
  4. 每个页面只聚焦一个概念/方法/主题
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
import re

# Windows GBK 编码修复
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 配置
VAULT_PATH = Path(r"C:\Users\scrccpa\Documents\Obsidian Vault")
RAW_PATH = VAULT_PATH / "raw"
WIKI_PATH = VAULT_PATH / "wiki"
TEMPLATES_PATH = VAULT_PATH / "templates"
INDEX_PATH = WIKI_PATH / "index.md"
LOG_PATH = WIKI_PATH / "log.md"

# 页面类型 → wiki 子目录映射
TYPE_DIR_MAP = {
    "政策法规": {"政府审计": "政府审计/政策法规", "工程咨询": "工程咨询/政策规范"},
    "专业方法": {"政府审计": "政府审计/审计方法", "工程咨询": "工程咨询/专业方法"},
    "项目经验": {"政府审计": "政府审计/项目经验", "工程咨询": "工程咨询/项目经验"},
    "概念术语": {"政府审计": "政府审计/概念术语", "工程咨询": "工程咨询"},
    "分析判断": {"政府审计": "政府审计/分析判断", "工程咨询": "工程咨询/分析判断"},
    "业务类型": {"政府审计": "政府审计/业务类型", "工程咨询": "工程咨询"},
}

# 页面类型 → 显示名
TYPE_DISPLAY = {
    "政策法规": "📜 政策法规",
    "专业方法": "🔧 专业方法",
    "项目经验": "📋 项目经验", 
    "概念术语": "📖 概念术语",
    "分析判断": "🔍 分析判断",
    "业务类型": "📦 业务类型",
}

# 页面类型 → 模板文件
TYPE_TEMPLATE = {
    "政策法规": "t-政策法规.md",
    "专业方法": "t-专业方法.md",
    "项目经验": "t-项目经验.md",
    "概念术语": "t-概念术语.md",
    "分析判断": "t-分析判断.md",
    "业务类型": "t-业务类型.md",
}


def sanitize_filename(name: str) -> str:
    """清理文件名，移除不合法字符"""
    illegal = r'[<>:"/\\|?*]'
    name = re.sub(illegal, '-', name)
    name = name.strip().strip('.')
    return name


def get_wiki_dir(page_type: str, domain: str) -> Path:
    """根据页面类型和域获取 wiki 子目录"""
    mapping = TYPE_DIR_MAP.get(page_type, {})
    subdir = mapping.get(domain)
    if not subdir:
        # 默认回退
        if domain == "工程咨询":
            subdir = "工程咨询"
        else:
            subdir = f"政府审计/{page_type}" if page_type in TYPE_DIR_MAP else "政府审计"
    
    target = WIKI_PATH / subdir
    target.mkdir(parents=True, exist_ok=True)
    return target


def generate_frontmatter(page_type: str, domain: str, title: str, 
                         source_url: str = "", source_title: str = "",
                         tags: list = None, extra: dict = None) -> str:
    """生成标准 YAML frontmatter"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    today = datetime.now().strftime("%Y-%m-%d")
    
    fm = {
        "type": page_type,
        "domain": domain,
        "tags": tags or [],
        "status": "draft",
        "created": now,
        "updated": now,
    }
    
    if source_url:
        fm["source_url"] = source_url
    if source_title:
        fm["source_title"] = source_title
        fm["source_date"] = today
    
    if extra:
        fm.update(extra)
    
    # 生成 YAML
    lines = ["---"]
    for key, value in fm.items():
        if isinstance(value, list):
            lines.append(f"{key}: [{', '.join(value)}]")
        elif isinstance(value, str):
            # 包含特殊字符的值需要引号
            if ':' in value or '#' in value or value.startswith('['):
                lines.append(f'{key}: "{value}"')
            else:
                lines.append(f"{key}: {value}")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    
    return "\n".join(lines)


def generate_page_body(page_type: str, title: str, domain: str, 
                       content: str, frontmatter: str, 
                       linked_pages: list = None) -> str:
    """生成完整 wiki 页面"""
    type_icon = TYPE_DISPLAY.get(page_type, "📄")
    type_link = f"[[{'专业方法' if page_type == '专业方法' else page_type}]]"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    body_parts = [
        frontmatter,
        "",
        f"# {title}",
        "",
        f"> {type_icon} {type_link} | {domain} | 最近更新: {now}",
        "",
    ]
    
    # 尝试从内容中提取摘要作为"一句话定位"
    # 寻找第一个有意义段落
    content_lines = content.strip().split("\n")
    summary = ""
    for line in content_lines:
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith(">"):
            if len(line) > 10:
                summary = line[:200]
                break
    
    if summary:
        body_parts.extend([
            "## 概述",
            "",
            summary,
            "",
        ])
    
    # 添加主要内容
    body_parts.append(content.strip())
    body_parts.append("")
    
    # 添加关联页面部分
    if linked_pages:
        body_parts.extend([
            "## 关联页面",
        ])
        for page in linked_pages:
            body_parts.append(f"- [[{page}]]")
        body_parts.append("")
    
    return "\n".join(body_parts)


def save_raw(title: str, content: str, source_url: str = "", 
             category: str = "行业情报") -> Path:
    """保存原始文件到 raw/ 目录"""
    # 确定 raw 子目录
    raw_categories = {
        "政策法规": "政策法规",
        "专业方法": "方法论", 
        "项目经验": "项目资料",
    }
    cat_dir = raw_categories.get(category, "行业情报")
    target_dir = RAW_PATH / cat_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    
    safe_title = sanitize_filename(title)
    timestamp = datetime.now().strftime("%Y%m%d")
    filename = f"{timestamp}-{safe_title}.md"
    
    filepath = target_dir / filename
    
    # 添加元数据头
    header = f"""# {title}

> 原始来源: {source_url}
> 摄入日期: {datetime.now().strftime('%Y-%m-%d %H:%M')}
> 分类: {category}

---

"""
    filepath.write_text(header + content, encoding="utf-8")
    return filepath


def update_index(page_type: str, domain: str, title: str, wiki_path: Path):
    """更新 index.md，添加新页面引用"""
    if not INDEX_PATH.exists():
        # 创建新的 index
        index_content = """# 融策 Wiki · 首页索引

> 自动维护 · 最后更新: {{UPDATE_TIME}}

## 政府审计

### 📜 政策法规

### 🔧 审计方法

### 📋 项目经验

### 📖 概念术语

### 🔍 分析判断

### 📦 业务类型

---

## 工程咨询

### 📜 政策规范

### 🔧 专业方法

### 📋 项目经验

### 🔍 分析判断

---

> 由 wiki_ingest.py 自动维护
"""
        INDEX_PATH.write_text(index_content, encoding="utf-8")
    
    # 读取现有 index
    content = INDEX_PATH.read_text(encoding="utf-8")
    
    # 计算 wiki 内相对路径
    try:
        rel_path = wiki_path.relative_to(WIKI_PATH)
        wiki_link = str(rel_path.with_suffix('')).replace('\\', '/')
    except ValueError:
        wiki_link = title
    
    # 找到对应区块并添加
    type_section = TYPE_DISPLAY.get(page_type, page_type)
    
    # 检查是否已存在
    if f"[[{wiki_link}" in content or f"[[{title}" in content:
        return  # 已存在
    
    # 简单追加策略：找到对应区块，在下一个 ## 之前插入
    lines = content.split("\n")
    new_lines = []
    section_found = False
    inserted = False
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        
        # 找到类型区块标题
        if not inserted and type_section in line and line.strip().startswith("###"):
            section_found = True
            continue
        
        if section_found and not inserted:
            # 在区块标题后插入，在下一个 ### 或 --- 之前
            # 看看后面几行
            look_ahead = "\n".join(lines[i+1:i+10])
            # 查找已有的列表项定位
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith("###") and lines[j].strip() != "---":
                j += 1
            
            # 在区块末尾插入
            insert_pos = j
            new_lines.insert(insert_pos, f"- [[{wiki_link}|{title}]]")
            inserted = True
            section_found = False
    
    if not inserted:
        # 追加到文件末尾
        new_lines.append(f"- [[{wiki_link}|{title}]]")
    
    # 更新时间戳
    result = "\n".join(new_lines)
    result = result.replace("{{UPDATE_TIME}}", datetime.now().strftime("%Y-%m-%d %H:%M"))
    
    INDEX_PATH.write_text(result, encoding="utf-8")


def update_log(action: str, page_type: str, title: str, description: str = ""):
    """更新 log.md"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    if not LOG_PATH.exists():
        LOG_PATH.write_text(
            "# 融策 Wiki · 操作日志\n\n"
            "> 自动记录所有 Wiki 变更\n\n"
            "| 时间 | 操作 | 类型 | 页面 | 说明 |\n"
            "|------|------|------|------|------|\n",
            encoding="utf-8"
        )
    
    log_entry = f"| {now} | {action} | {page_type} | [[{title}]] | {description} |\n"
    
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(log_entry)


def scan_wiki_pages() -> list:
    """扫描所有 wiki 页面，提取 frontmatter"""
    pages = []
    
    for md_file in WIKI_PATH.rglob("*.md"):
        if md_file.name in ("index.md", "log.md"):
            continue
        
        content = md_file.read_text(encoding="utf-8")
        fm = extract_frontmatter(content)
        
        pages.append({
            "path": str(md_file.relative_to(WIKI_PATH)),
            "title": md_file.stem,
            "type": fm.get("type", "未知"),
            "domain": fm.get("domain", "未知"),
            "tags": fm.get("tags", []),
            "status": fm.get("status", "draft"),
            "updated": fm.get("updated", ""),
            "has_frontmatter": bool(fm),
            "outgoing_links": extract_wiki_links(content),
        })
    
    return pages


def extract_frontmatter(content: str) -> dict:
    """提取 YAML frontmatter"""
    if not content.startswith("---"):
        return {}
    
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    
    fm_text = parts[1].strip()
    result = {}
    
    for line in fm_text.split("\n"):
        line = line.strip()
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            
            # 解析列表
            if value.startswith("[") and value.endswith("]"):
                value = [v.strip().strip('"').strip("'") 
                        for v in value[1:-1].split(",") if v.strip()]
            
            result[key] = value
    
    return result


def extract_wiki_links(content: str) -> list:
    """提取 [[wiki链接]]"""
    return re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', content)


def cmd_add(args):
    """添加新页面"""
    title = args.title
    page_type = args.type
    domain = args.domain
    source_url = args.source_url or ""
    source_title = args.source_title or ""
    tags = args.tags.split(",") if args.tags else []
    
    # 读取内容
    if args.content_file:
        content = Path(args.content_file).read_text(encoding="utf-8")
    else:
        content = sys.stdin.read()
    
    if not content.strip():
        print("错误：没有提供内容", file=sys.stderr)
        sys.exit(1)
    
    # 保存原始文件
    raw_path = save_raw(title, content, source_url, page_type)
    print(f"✅ 原始文件: {raw_path}")
    
    # 生成 wiki 页面
    fm = generate_frontmatter(page_type, domain, title, source_url, source_title, tags)
    
    # 检测内容中是否已有 wiki 链接
    existing_links = extract_wiki_links(content)
    
    wiki_dir = get_wiki_dir(page_type, domain)
    safe_title = sanitize_filename(title)
    wiki_path = wiki_dir / f"{safe_title}.md"
    
    page_content = generate_page_body(page_type, title, domain, content, fm, existing_links)
    wiki_path.write_text(page_content, encoding="utf-8")
    print(f"✅ Wiki 页面: {wiki_path}")
    
    # 更新索引和日志
    update_index(page_type, domain, title, wiki_path)
    print(f"✅ 索引已更新: {INDEX_PATH}")
    
    update_log("摄入", page_type, title, f"来源: {source_title or source_url}")
    print(f"✅ 日志已更新: {LOG_PATH}")
    
    # 总结
    print(f"\n📦 摄入完成: [[{title}]] → {wiki_path.relative_to(WIKI_PATH)}")
    print(f"   类型: {page_type} | 域: {domain}")
    if source_url:
        print(f"   来源: {source_url}")


def cmd_index(args):
    """重新生成 index.md（基于扫描所有页面）"""
    pages = scan_wiki_pages()
    
    # 按类型和域分组
    groups = {}
    for p in pages:
        key = (p["domain"], p["type"])
        if key not in groups:
            groups[key] = []
        groups[key].append(p)
    
    # 生成 index
    lines = [
        "# 融策 Wiki · 首页索引",
        "",
        f"> 自动维护 · 最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"> 页面总数: {len(pages)}",
        "",
    ]
    
    # 政府审计部分
    lines.append("## 政府审计")
    lines.append("")
    
    audit_types = ["政策法规", "专业方法", "项目经验", "概念术语", "分析判断", "业务类型"]
    for pt in audit_types:
        lines.append(f"### {TYPE_DISPLAY.get(pt, pt)}（{sum(1 for p in pages if p['type']==pt and p['domain']=='政府审计')}页）")
        for p in sorted(pages, key=lambda x: x["title"]):
            if p["type"] == pt and p["domain"] == "政府审计":
                lines.append(f"- [[{p['path'].replace(chr(92),'/').removesuffix('.md')}|{p['title']}]]")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    lines.append("## 工程咨询")
    lines.append("")
    
    eng_types = ["政策法规", "专业方法", "项目经验", "分析判断"]
    for pt in eng_types:
        count = sum(1 for p in pages if p['type']==pt and p['domain']=='工程咨询')
        if count > 0 or pt in ["政策法规", "专业方法"]:
            lines.append(f"### {TYPE_DISPLAY.get(pt, pt)}（{count}页）")
            for p in sorted(pages, key=lambda x: x["title"]):
                if p["type"] == pt and p["domain"] == "工程咨询":
                    lines.append(f"- [[{p['path'].replace(chr(92),'/').removesuffix('.md')}|{p['title']}]]")
            lines.append("")
    
    lines.append("---")
    lines.append("")
    lines.append("> 由 wiki_ingest.py 自动维护")
    
    INDEX_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ index.md 已重新生成（{len(pages)} 个页面）")


def cmd_stats(args):
    """显示统计信息"""
    pages = scan_wiki_pages()
    
    type_counts = {}
    domain_counts = {}
    no_fm = 0
    
    for p in pages:
        t = p["type"]
        type_counts[t] = type_counts.get(t, 0) + 1
        d = p["domain"]
        domain_counts[d] = domain_counts.get(d, 0) + 1
        if not p["has_frontmatter"]:
            no_fm += 1
    
    print(f"📊 融策 Wiki 统计")
    print(f"   总页面数: {len(pages)}")
    print(f"   缺 Frontmatter: {no_fm}")
    print()
    print("按域分布:")
    for d, c in sorted(domain_counts.items()):
        print(f"   {d}: {c}")
    print()
    print("按类型分布:")
    for t, c in sorted(type_counts.items()):
        print(f"   {t}: {c}")
    
    # 最近更新
    sorted_pages = sorted([p for p in pages if p["updated"]], 
                         key=lambda x: x["updated"], reverse=True)
    if sorted_pages:
        print()
        print("最近更新（Top 10）:")
        for p in sorted_pages[:10]:
            print(f"   {p['updated']} | {p['type']} | {p['title']}")


def main():
    parser = argparse.ArgumentParser(description="融策 Wiki 自动摄入工具")
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # add 命令
    add_parser = subparsers.add_parser("add", help="添加新页面")
    add_parser.add_argument("--title", required=True, help="页面标题")
    add_parser.add_argument("--type", required=True, 
                           choices=list(TYPE_DIR_MAP.keys()), help="页面类型")
    add_parser.add_argument("--domain", required=True, 
                           choices=["政府审计", "工程咨询"], help="业务域")
    add_parser.add_argument("--source-url", default="", help="来源URL")
    add_parser.add_argument("--source-title", default="", help="来源标题")
    add_parser.add_argument("--tags", default="", help="标签（逗号分隔）")
    add_parser.add_argument("--content-file", default="", help="内容文件路径（默认从stdin读取）")
    
    # index 命令
    subparsers.add_parser("index", help="重新生成 index.md")
    
    # stats 命令
    subparsers.add_parser("stats", help="显示统计信息")
    
    args = parser.parse_args()
    
    if args.command == "add":
        cmd_add(args)
    elif args.command == "index":
        cmd_index(args)
    elif args.command == "stats":
        cmd_stats(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
