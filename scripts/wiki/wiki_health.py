#!/usr/bin/env python3
"""
融策 Wiki 健检工具
==================
按 CLAUDE.md 健检规范自动扫描 Wiki。

用法:
  wiki_health.py scan       # 完整扫描
  wiki_health.py orphans    # 仅孤立页面
  wiki_health.py outdated   # 仅过期内容
  wiki_health.py report     # 生成健检报告（Markdown）

检查项目:
  1. 孤立页面（无入链、无出链）
  2. 矛盾页面（同一事实表述不一致）
  3. 过时内容（政策法规更新未同步）
  4. Frontmatter 完整性
  5. 链接有效性
"""

import os
import sys
import re
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# Windows GBK 编码修复
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 配置
VAULT_PATH = Path(r"C:\Users\scrccpa\Documents\Obsidian Vault")
WIKI_PATH = VAULT_PATH / "wiki"
INDEX_PATH = WIKI_PATH / "index.md"
LOG_PATH = WIKI_PATH / "log.md"


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
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if value.startswith("[") and value.endswith("]"):
                value = [v.strip().strip('"').strip("'") 
                        for v in value[1:-1].split(",") if v.strip()]
            result[key] = value
    return result


def extract_wiki_links(content: str) -> list:
    """提取 [[wiki链接]]，返回链接目标名列表"""
    links = re.findall(r'\[\[([^\]|#]+)(?:[|#][^\]]+)?\]\]', content)
    return [l.strip() for l in links]


def extract_headings(content: str) -> list:
    """提取所有标题"""
    headings = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
    return [(level, title.strip()) for level, title in headings]


def get_all_pages() -> list:
    """扫描所有 wiki 页面"""
    pages = []
    for md_file in WIKI_PATH.rglob("*.md"):
        if md_file.name in ("index.md", "log.md"):
            continue
        try:
            content = md_file.read_text(encoding="utf-8")
        except:
            continue
        
        fm = extract_frontmatter(content)
        links = extract_wiki_links(content)
        headings = extract_headings(content)
        
        pages.append({
            "path": str(md_file),
            "relpath": str(md_file.relative_to(WIKI_PATH)),
            "title": md_file.stem,
            "type": fm.get("type", "未知"),
            "domain": fm.get("domain", "未知"),
            "tags": fm.get("tags", []),
            "status": fm.get("status", "draft"),
            "created": fm.get("created", ""),
            "updated": fm.get("updated", ""),
            "source_url": fm.get("source_url", ""),
            "source_title": fm.get("source_title", ""),
            "has_frontmatter": bool(fm),
            "outgoing_links": links,
            "headings": headings,
            "content_length": len(content),
            "content_preview": content[:500],
        })
    return pages


def check_orphans(pages: list) -> list:
    """检查孤立页面"""
    # 构建入链索引
    all_page_titles = {p["title"] for p in pages}
    inbound = defaultdict(set)
    
    for p in pages:
        for link in p["outgoing_links"]:
            if link in all_page_titles:
                inbound[link].add(p["title"])
    
    # 有出链的页面集
    has_outbound = {p["title"] for p in pages if p["outgoing_links"]}
    
    orphans = []
    for p in pages:
        out_count = len([l for l in p["outgoing_links"] if l in all_page_titles])
        in_count = len(inbound.get(p["title"], set()))
        
        issues = []
        if out_count == 0:
            issues.append("无出链")
        if in_count == 0:
            issues.append("无入链（无其他页面引用）")
        
        if issues:
            orphans.append({
                "title": p["title"],
                "path": p["relpath"],
                "type": p["type"],
                "issues": issues,
                "out_count": out_count,
                "in_count": in_count,
            })
    
    return orphans


def check_frontmatter(pages: list) -> list:
    """检查 Frontmatter 完整性"""
    required_fields = {
        "政策法规": ["type", "domain", "tags", "status", "source_title"],
        "专业方法": ["type", "domain", "tags", "status", "method_category"],
        "项目经验": ["type", "domain", "tags", "status", "project_name"],
        "概念术语": ["type", "domain", "tags", "status"],
        "分析判断": ["type", "domain", "tags", "status", "confidence"],
        "业务类型": ["type", "domain", "tags", "status", "service_name"],
    }
    
    issues = []
    for p in pages:
        if not p["has_frontmatter"]:
            issues.append({
                "title": p["title"],
                "path": p["relpath"],
                "type": p["type"],
                "issue": "完全缺失 YAML Frontmatter",
                "severity": "🔴",
            })
            continue
        
        fm = extract_frontmatter(Path(p["path"]).read_text(encoding="utf-8"))
        required = required_fields.get(p["type"], ["type", "domain", "status"])
        missing = [f for f in required if f not in fm or not fm[f]]
        
        if missing:
            issues.append({
                "title": p["title"],
                "path": p["relpath"],
                "type": p["type"],
                "issue": f"缺少必填字段: {', '.join(missing)}",
                "severity": "🟡",
            })
    
    return issues


def check_outdated(pages: list, days_threshold: int = 180) -> list:
    """检查可能过期的内容"""
    now = datetime.now()
    outdated = []
    
    policy_pages = [p for p in pages if p["type"] == "政策法规"]
    
    for p in policy_pages:
        updated = p.get("updated", "")
        if updated:
            try:
                update_date = datetime.strptime(updated[:10], "%Y-%m-%d")
                age = (now - update_date).days
                if age > days_threshold:
                    outdated.append({
                        "title": p["title"],
                        "path": p["relpath"],
                        "type": p["type"],
                        "last_updated": updated,
                        "age_days": age,
                        "issue": f"最后一次更新 {age} 天前，法规可能已有变动",
                        "severity": "🟡",
                    })
            except ValueError:
                pass
    
    return outdated


def check_broken_links(pages: list) -> list:
    """检查链接有效性"""
    all_page_titles = {p["title"] for p in pages}
    
    # 添加已知的外部引用（raw/ 目录下的文件引用）
    external_refs = set()
    
    broken = []
    for p in pages:
        for link in p["outgoing_links"]:
            # 跳过外部链接（含 / 或 URL 特征）
            if "/" in link or link.startswith("http"):
                continue
            # 跳过融策工作区链接
            if "融策工作区" in link:
                continue
            # 检查内部链接
            if link not in all_page_titles and link not in external_refs:
                broken.append({
                    "source": p["title"],
                    "source_path": p["relpath"],
                    "broken_link": link,
                    "issue": f"[{p['title']}] 引用了不存在的页面 [[{link}]]",
                    "severity": "🟡",
                })
    
    return broken


def check_duplication(pages: list) -> list:
    """检查可能的重复/矛盾页面（基于标题相似度）"""
    from difflib import SequenceMatcher
    
    dups = []
    titles = [(p["title"], p) for p in pages]
    
    for i in range(len(titles)):
        for j in range(i+1, len(titles)):
            ratio = SequenceMatcher(None, titles[i][0], titles[j][0]).ratio()
            if ratio > 0.7:  # 标题相似度超过70%
                dups.append({
                    "page1": titles[i][1]["title"],
                    "path1": titles[i][1]["relpath"],
                    "page2": titles[j][1]["title"],
                    "path2": titles[j][1]["relpath"],
                    "similarity": f"{ratio:.0%}",
                    "issue": f"标题高度相似（{ratio:.0%}），可能存在内容重复或矛盾",
                    "severity": "🟡",
                })
    
    return dups


def generate_report(pages: list) -> str:
    """生成健检报告"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    orphans = check_orphans(pages)
    fm_issues = check_frontmatter(pages)
    outdated = check_outdated(pages)
    broken = check_broken_links(pages)
    dups = check_duplication(pages)
    
    total_issues = len(orphans) + len(fm_issues) + len(outdated) + len(broken) + len(dups)
    
    lines = [
        f"# 融策 Wiki 健检报告",
        f"",
        f"> 🩺 自动生成 · {now}",
        f"> 页面总数: {len(pages)} · 问题总数: {total_issues}",
        f"",
        f"## 📊 总览",
        f"",
        f"| 检查项 | 问题数 | 状态 |",
        f"|--------|--------|------|",
        f"| Frontmatter 完整性 | {len(fm_issues)} | {'🔴 需处理' if fm_issues else '✅ 正常'} |",
        f"| 孤立页面 | {len(orphans)} | {'🔴 需处理' if orphans else '✅ 正常'} |",
        f"| 断链 | {len(broken)} | {'🟡 需关注' if broken else '✅ 正常'} |",
        f"| 过期内容 | {len(outdated)} | {'🟡 需关注' if outdated else '✅ 正常'} |",
        f"| 重复/相似页面 | {len(dups)} | {'🟡 需关注' if dups else '✅ 正常'} |",
        f"",
    ]
    
    # Frontmatter 问题
    if fm_issues:
        lines.append("## 🔴 Frontmatter 问题")
        lines.append("")
        for iss in fm_issues:
            lines.append(f"- **{iss['title']}** ({iss['type']}): {iss['issue']}")
        lines.append("")
    
    # 孤立页面
    if orphans:
        lines.append("## 🔴 孤立页面")
        lines.append("")
        for o in orphans:
            lines.append(f"- **{o['title']}** ({o['type']}, {o['path']}): {', '.join(o['issues'])}")
        lines.append("")
    
    # 断链
    if broken:
        lines.append("## 🟡 断链")
        lines.append("")
        for b in broken:
            lines.append(f"- {b['issue']}")
        lines.append("")
    
    # 过期内容
    if outdated:
        lines.append("## 🟡 可能过期")
        lines.append("")
        for o in outdated:
            lines.append(f"- **{o['title']}**: 最后更新 {o['age_days']} 天前")
        lines.append("")
    
    # 重复页面
    if dups:
        lines.append("## 🟡 重复/相似页面")
        lines.append("")
        for d in dups:
            lines.append(f"- **{d['page1']}** ↔ **{d['page2']}** 标题相似度 {d['similarity']}")
        lines.append("")
    
    if total_issues == 0:
        lines.append("## ✅ 全部正常")
        lines.append("")
        lines.append("未发现问题。知识库保持得很好！")
        lines.append("")
    
    lines.append("---")
    lines.append(f"*报告生成时间: {now}*")
    
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("用法: wiki_health.py [scan|orphans|outdated|report]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    pages = get_all_pages()
    
    if cmd == "scan":
        print(f"🔍 扫描 {len(pages)} 个页面...")
        print()
        
        orphans = check_orphans(pages)
        fm_issues = check_frontmatter(pages)
        outdated = check_outdated(pages)
        broken = check_broken_links(pages)
        dups = check_duplication(pages)
        
        print(f"📋 Frontmatter 缺失/不完整: {len(fm_issues)}")
        for iss in fm_issues:
            print(f"   {iss['severity']} {iss['title']}: {iss['issue']}")
        
        print(f"🔗 孤立页面: {len(orphans)}")
        for o in orphans:
            print(f"   🔴 {o['title']}: {', '.join(o['issues'])}")
        
        print(f"💔 断链: {len(broken)}")
        for b in broken:
            print(f"   {b['severity']} {b['issue']}")
        
        print(f"⏰ 可能过期: {len(outdated)}")
        for o in outdated:
            print(f"   {o['severity']} {o['title']}: {o['age_days']}天未更新")
        
        print(f"🔄 重复/相似: {len(dups)}")
        for d in dups:
            print(f"   {d['severity']} {d['page1']} ↔ {d['page2']}")
    
    elif cmd == "orphans":
        orphans = check_orphans(pages)
        for o in orphans:
            print(f"🔴 {o['title']} ({o['path']}): {', '.join(o['issues'])}")
        if not orphans:
            print("✅ 无孤立页面")
    
    elif cmd == "outdated":
        outdated = check_outdated(pages)
        for o in outdated:
            print(f"{o['severity']} {o['title']}: {o['age_days']}天未更新")
        if not outdated:
            print("✅ 无过期内容")
    
    elif cmd == "report":
        report = generate_report(pages)
        report_path = WIKI_PATH.parent / "健康检查报告.md"
        report_path.write_text(report, encoding="utf-8")
        print(report)
        print(f"\n📄 报告已保存: {report_path}")
    
    else:
        print(f"未知命令: {cmd}")
        print("用法: wiki_health.py [scan|orphans|outdated|report]")


if __name__ == "__main__":
    main()
