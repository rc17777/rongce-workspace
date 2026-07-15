"""
case_collector.py — 政府/国企审计案例采集器

采集策略（务实版）：
  1. 手动输入（--manual）—— 最可靠，项目经理遇到好案例直接录入
  2. URL采集（--fetch-url）—— 通过web_fetch抓取公众号文章/政府网页
  3. 微信文章（--wechat）—— 直接用移动端UA抓微信公众号文章
  4. 本地导入（--import-md）—— 批量导入已有Markdown文件
  5. 迁移已有案例（--migrate）—— 从知识库现有目录迁移

用法：
  python scripts/case_collector.py --manual                               # 手动输入
  python scripts/case_collector.py --fetch-url <url>                      # 从URL采集
  python scripts/case_collector.py --wechat <wechat_article_url>          # 微信文章采集
  python scripts/case_collector.py --import-md <file.md>                  # 导入本地文件
  python scripts/case_collector.py --migrate                              # 迁移已有案例
  python scripts/case_collector.py --index                                # 重建索引
  python scripts/case_collector.py --stats                                # 统计
"""

import json, os, re, sys, time, hashlib, urllib.request, urllib.parse
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional, Tuple

sys.stdout.reconfigure(encoding='utf-8')

# ── 路径 ──
WORKSPACE = Path(__file__).resolve().parent.parent
CONFIG_PATH = WORKSPACE / "config" / "case_collector_config.json"
OUTPUT_BASE = WORKSPACE / "knowledge" / "cases"
RAW_DIR = OUTPUT_BASE / "_raw"
INDEX_FILE = OUTPUT_BASE / "案例库索引.md"


# ════════════════════════════════════════════════════════════
# 案例模板
# ════════════════════════════════════════════════════════════

CASE_TEMPLATE = """---
id: {case_id}
type: "{case_type}"
source: "{source}"
source_url: "{source_url}"
date: "{date}"
date_collected: "{collected}"
tags: [{tags}]
severity: "{severity}"
industry: "{industry}"
region: "{region}"
audit_type: "{audit_type}"
amount: "{amount}"
---

# {title}

## 案例概述

{summary}

## 审计发现

{findings}

## 审计方法

{methods}

## 问题定性

{qualification}

## 处理结果

{result}

## 适用法规

{legal_refs}

## 可借鉴经验

{lessons}

---

*来源: [{source}]({source_url}) | 采集于 {collected}*
"""


def default_case() -> dict:
    return {
        "case_id": "", "type": "", "source": "", "source_url": "",
        "title": "", "date": "", "collected": "",
        "tags": [], "severity": "", "industry": "", "region": "",
        "audit_type": "", "amount": "",
        "summary": "", "findings": "（暂无）", "methods": "（暂无）",
        "qualification": "（暂无）", "result": "（暂无）",
        "legal_refs": "（暂无）", "lessons": "（暂无）",
    }


def gen_case_id() -> str:
    return "CAS-{}-{}".format(date.today().strftime("%Y%m%d"),
                              hashlib.md5(str(time.time()).encode()).hexdigest()[:4].upper())


def slugify(text: str, max_len=80) -> str:
    text = re.sub(r'[^\w\s\u4e00-\u9fff-]', '', text.lower())
    return re.sub(r'[-\s]+', '-', text).strip('-')[:max_len]


# ════════════════════════════════════════════════════════════
# 保存 & 索引
# ════════════════════════════════════════════════════════════

def save_case(case: dict) -> Path:
    slug = slugify(case.get("title", "untitled"))
    case_dir = Path(OUTPUT_BASE) / ((case.get("date") or "unknown")[:4] or "unknown")
    case_dir.mkdir(parents=True, exist_ok=True)

    filepath = case_dir / "{}.md".format(slug)
    counter = 1
    while filepath.exists():
        filepath = case_dir / "{}-{}.md".format(slug, counter)
        counter += 1

    c = {**default_case(), **case}
    content = CASE_TEMPLATE.format(
        case_id=c["case_id"] or gen_case_id(),
        case_type=c["type"] or "审计案例",
        source=c["source"] or "未知",
        source_url=c["source_url"] or "",
        title=c["title"] or "（无标题）",
        date=c["date"] or "",
        collected=c["collected"] or datetime.now().strftime("%Y-%m-%d %H:%M"),
        tags=", ".join(c.get("tags", [])),
        severity=c["severity"] or "",
        industry=c["industry"] or "",
        region=c["region"] or "",
        audit_type=c["audit_type"] or "",
        amount=c["amount"] or "",
        summary=c["summary"] or "（暂无）",
        findings=c["findings"] or "（暂无）",
        methods=c["methods"] or "（暂无）",
        qualification=c["qualification"] or "（暂无）",
        result=c["result"] or "（暂无）",
        legal_refs=c["legal_refs"] or "（暂无）",
        lessons=c["lessons"] or "（暂无）",
    )
    filepath.write_text(content, encoding="utf-8")
    return filepath


def rebuild_index():
    """重建案例库索引"""
    cases = []
    for f in sorted(OUTPUT_BASE.rglob("*.md")):
        if f.name in ("案例库索引.md",) or f.parent.name in ("_raw", "digests"):
            continue
        content = f.read_text(encoding="utf-8")
        info = {"file": str(f.relative_to(WORKSPACE)), "title": f.stem,
                "type": "", "source": "", "date": "", "tags": [],
                "severity": "", "industry": "", "region": "", "amount": ""}
        yaml_m = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if yaml_m:
            for line in yaml_m.group(1).splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    k, v = k.strip().lower(), v.strip().strip('"').strip("'")
                    if k in info:
                        info[k] = [t.strip() for t in v.split(",") if t.strip()] if k == "tags" else v
        body = re.sub(r'^---.*?---\s*', '', content, flags=re.DOTALL)
        m = re.match(r'^#\s+(.+)$', body, re.MULTILINE)
        if m:
            info["title"] = m.group(1).strip()
        cases.append(info)

    cases.sort(key=lambda c: c.get("date", ""), reverse=True)

    # 统计
    by_type, by_source, by_severity, all_tags = {}, {}, {}, []
    for c in cases:
        ct = c.get("type", "其他") or "其他"
        by_type[ct] = by_type.get(ct, 0) + 1
        src = c.get("source", "未知") or "未知"
        by_source[src] = by_source.get(src, 0) + 1
        sev = c.get("severity", "未标注") or "未标注"
        by_severity[sev] = by_severity.get(sev, 0) + 1
        all_tags.extend(c.get("tags", []) or [])
    tag_counts = dict(sorted({t: all_tags.count(t) for t in set(all_tags)}.items(), key=lambda x: -x[1])[:20])

    lines = [
        "# 🏛️ 审计案例库索引",
        "",
        "> 自动生成于 {}".format(datetime.now().strftime("%Y-%m-%d %H:%M")),
        "---",
        "",
        "## 📊 统计概览",
        "",
        "| 指标 | 数值 |",
        "|------|------|",
        "| 总案例数 | {} 篇 |".format(len(cases)),
        "| 最早 | {} |".format(cases[-1].get("date", "?") if cases else "N/A"),
        "| 最新 | {} |".format(cases[0].get("date", "?") if cases else "N/A"),
        "",
        "### 按类型",
    ]
    for ct, count in sorted(by_type.items(), key=lambda x: -x[1]):
        lines.append("| {} | {} |".format(ct, count))
    lines.extend(["", "### 按来源", ""])
    for src, count in sorted(by_source.items(), key=lambda x: -x[1]):
        lines.append("| {} | {} |".format(src, count))
    lines.extend(["", "### 热门标签", ""])
    for tag, count in tag_counts.items():
        lines.append("| {} | {} |".format(tag, count))
    lines.extend(["", "---", "", "## 📋 案例列表", ""])

    for c in cases:
        tags_str = " | ".join((c.get("tags") or [])[:5])
        if len((c.get("tags") or [])) > 5:
            tags_str += " ..."
        lines.extend([
            "### {}".format(c.get("title", "（无标题）")),
            "",
            "- **类型**：{} | **来源**：{} | **日期**：{}".format(
                c.get("type", "?"), c.get("source", "?"), c.get("date", "?")),
            "- **标签**：{}".format(tags_str or "（无）"),
            "- **文件**：[{}]({})".format(c["file"], c["file"]),
            "",
        ])

    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text("\n".join(lines), encoding="utf-8")
    print("✅ 索引已重建: {} ({} 篇)".format(INDEX_FILE, len(cases)))
    return cases


# ════════════════════════════════════════════════════════════
# 手动输入
# ════════════════════════════════════════════════════════════

FIELDS = [
    ("title", "标题", ""),
    ("source", "来源", "审计署/国资委/财政部/地方审计局/微信公众号/其他"),
    ("source_url", "来源链接", ""),
    ("date", "日期", "YYYY-MM-DD"),
    ("type", "类型", "绩效审计/经责审计/财政审计/专项资金审计/工程审计/国企审计/其他"),
    ("audit_type", "审计类型", "任中/离任/专项/跟踪/决算/其他"),
    ("industry", "行业", "教育/医疗/交通/工程/金融/国企/农业/社保/其他"),
    ("region", "地区", "省/市/县"),
    ("amount", "涉及金额", "xxx万元"),
    ("severity", "严重程度", "严重/较重/一般"),
    ("tags", "标签", "逗号分隔"),
    ("summary", "案例概述", ""),
    ("findings", "审计发现", ""),
    ("methods", "审计方法", ""),
    ("qualification", "问题定性", ""),
    ("result", "处理结果", ""),
    ("legal_refs", "适用法规", ""),
    ("lessons", "可借鉴经验", ""),
]


def manual_input():
    print("\n📝 手动输入审计案例")
    print("=" * 60)
    print("逐项输入，直接回车跳过可选字段，输入 END 结束")
    print("=" * 60)

    case = default_case()
    case["case_id"] = gen_case_id()
    case["collected"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    for key, label, hint in FIELDS:
        prompt = "  {} [{}]: ".format(label, hint) if hint else "  {}: ".format(label)
        val = input(prompt).strip()
        if val.upper() == "END":
            break
        if not val and key in ("title",):
            print("  ⚠️ 标题必填，再试一次")
            val = input(prompt).strip()
        if key == "tags":
            case[key] = [t.strip() for t in val.split(",") if t.strip()]
        elif key in ("summary", "findings", "methods", "qualification", "result", "legal_refs", "lessons"):
            # 多行输入
            if val:
                lines = [val]
                while True:
                    line = input("    (继续输入，空行结束): ").strip()
                    if not line or line.upper() == "END":
                        break
                    lines.append(line)
                case[key] = "\n".join(lines)
        else:
            case[key] = val

    if not case["title"]:
        print("❌ 标题为空，取消保存")
        return

    fpath = save_case(case)
    print("\n✅ 案例已保存: {}".format(fpath))
    rebuild_index()
    return fpath


# ════════════════════════════════════════════════════════════
# URL采集（通过web_fetch或直接HTTP）
# ════════════════════════════════════════════════════════════

def fetch_from_url(url: str) -> Optional[dict]:
    """从URL采集案例内容"""
    print("  📡 正在采集: {}".format(url))
    case = default_case()
    case["case_id"] = gen_case_id()
    case["source_url"] = url
    case["collected"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-S9080) AppleWebKit/537.36 Chrome/120.0.6099.230 Mobile Safari/537.36 MicroMessenger/8.0.47',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=20)
        html = resp.read().decode('utf-8', errors='replace')

        # 提取标题
        for pat in [r'class="con-article-title"[^>]*>(.*?)</div>',
                    r'class="article-title"[^>]*>(.*?)</div>',
                    r'id="article-title"[^>]*>(.*?)</div>',
                    r'<title>(.*?)</title>',
                    r'var msg_title\s*=\s*["\'](.+?)["\']',
                    r'<h1[^>]*>(.*?)</h1>']:
            m = re.search(pat, html, re.DOTALL | re.IGNORECASE)
            if m:
                case["title"] = re.sub(r'<[^>]+>', '', m.group(1)).strip()
                if len(case["title"]) > 5:
                    break

        # 提取正文
        for pat in [r'class="con-article-txt-box"[^>]*>(.*?)</div>',
                    r'class="article-content"[^>]*>(.*?)</div>',
                    r'class="content"[^>]*>(.*?)</div>',
                    r'id="js_content"[^>]*>(.*?)(?:</div>|</section>)',
                    r'class="rich_media_content"[^>]*>(.*?)(?:</div>|</section>)',
                    r'id="article-content"[^>]*>(.*?)</div>',
                    r'class="TRS_Editor"[^>]*>(.*?)</div>']:
            m = re.search(pat, html, re.DOTALL | re.IGNORECASE)
            if m:
                text = re.sub(r'<[^>]+>', '', m.group(1))
                text = re.sub(r'&nbsp;', ' ', text)
                text = re.sub(r'\s+', '\n', text).strip()
                if len(text) > 100:
                    case["summary"] = text[:2000]
                    break

        # 如果正文没找到，取body文本
        if not case["summary"]:
            body = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL)
            if body:
                text = re.sub(r'<[^>]+>', '', body.group(1))
                text = re.sub(r'&nbsp;', ' ', text)
                text = re.sub(r'\s+', '\n', text).strip()
                if len(text) > 50:
                    case["summary"] = text[:2000]

        # 识别来源
        if 'audit.gov.cn' in url:
            case["source"] = "审计署"
            case["type"] = "审计署典型案例"
        elif 'sasac.gov.cn' in url:
            case["source"] = "国务院国资委"
            case["type"] = "国资委追责案例"
        elif 'mof.gov.cn' in url:
            case["source"] = "财政部"
            case["type"] = "财会监督案例"
        elif 'mp.weixin.qq.com' in url:
            case["source"] = "微信公众号"
            case["type"] = "审计实务案例"
        elif 'sjt.sc.gov.cn' in url or 'audit' in url:
            case["source"] = "审计机关"
            case["type"] = "审计案例"

        if not case["title"]:
            case["title"] = "来自 {}".format(url)

        print("  ✅ 标题: {}".format(case["title"][:60]))
        if case["summary"]:
            print("  📄 正文: {} 字".format(len(case["summary"])))
        else:
            print("  ⚠️ 未提取到正文（JS渲染页面）")
            print("  建议: 手动阅读后通过 --manual 录入")

        return case

    except Exception as e:
        print("  ❌ 采集失败: {}".format(e))
        return None


def fetch_url_workflow(url: str):
    """URL采集工作流"""
    print("\n📡 从URL采集审计案例")
    print("=" * 60)
    case = fetch_from_url(url)
    if not case:
        return

    print("\n已提取基本信息，是否补充字段？(y/n): ", end="")
    if input().strip().lower() in ("y", "yes", ""):
        print("（直接回车跳过，输入字段值，空行结束）")
        for key, label, hint in FIELDS:
            if case.get(key):
                continue
            prompt = "  {} [{}]: ".format(label, hint) if hint else "  {}: ".format(label)
            val = input(prompt).strip()
            if val.upper() == "END":
                break
            if key == "tags":
                case[key] = [t.strip() for t in val.split(",") if t.strip()]
            else:
                case[key] = val

    fpath = save_case(case)
    print("\n✅ 案例已保存: {}".format(fpath))
    rebuild_index()


# ════════════════════════════════════════════════════════════
# 微信文章采集
# ════════════════════════════════════════════════════════════

def fetch_wechat(url: str):
    """采集微信公众号文章"""
    if 'mp.weixin.qq.com' not in url:
        print("⚠️ 不是微信公众号文章链接")
        return
    fetch_url_workflow(url)


# ════════════════════════════════════════════════════════════
# 导入本地Markdown
# ════════════════════════════════════════════════════════════

def import_markdown(filepath: str):
    path = Path(filepath)
    if not path.exists():
        print("❌ 文件不存在: {}".format(filepath))
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    case = default_case()
    case["case_id"] = gen_case_id()
    case["source"] = "本地导入"
    case["source_url"] = str(path)
    case["date"] = date.today().isoformat()
    case["collected"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    yaml_m = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
    if yaml_m:
        for line in yaml_m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                k, v = k.strip().lower(), v.strip().strip('"').strip("'")
                if k == "title": case["title"] = v
                elif k == "source": case["source"] = v
                elif k == "type": case["type"] = v
                elif k == "date": case["date"] = v
                elif k == "tags": case["tags"] = [t.strip() for t in v.split(",") if t.strip()]
        text = text[yaml_m.end():]

    if not case["title"]:
        m = re.match(r'^#\s+(.+)$', text, re.MULTILINE)
        if m: case["title"] = m.group(1).strip()
    if not case["title"]:
        case["title"] = path.stem
    case["summary"] = text.strip()[:1000]

    fpath = save_case(case)
    print("✅ 已导入: {} → {}".format(path.name, fpath))
    rebuild_index()
    return fpath


# ════════════════════════════════════════════════════════════
# 迁移已有案例
# ════════════════════════════════════════════════════════════

def migrate_existing():
    source_dirs = [
        WORKSPACE / "knowledge" / "审计案例库-OCR",
        WORKSPACE / "knowledge" / "审计方法",
        WORKSPACE / "knowledge" / "审计方法论",
        WORKSPACE / "knowledge" / "审计技术",
    ]
    migrated = 0
    for src_dir in source_dirs:
        if not src_dir.exists():
            continue
        print("\n📂 扫描: {}/".format(src_dir.name))
        for f in sorted(src_dir.rglob("*.md")):
            import_markdown(str(f))
            migrated += 1
    print("\n📊 迁移完成: {} 篇".format(migrated))
    rebuild_index()


# ════════════════════════════════════════════════════════════
# 统计
# ════════════════════════════════════════════════════════════

def show_stats():
    if not OUTPUT_BASE.exists():
        print("📭 案例库为空")
        return
    total, by_type, by_source, all_tags = 0, {}, {}, []
    for f in OUTPUT_BASE.rglob("*.md"):
        if f.name == "案例库索引.md" or f.parent.name in ("_raw", "digests"):
            continue
        total += 1
        content = f.read_text(encoding="utf-8")
        yaml_m = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if yaml_m:
            for line in yaml_m.group(1).splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    k, v = k.strip().lower(), v.strip().strip('"').strip("'")
                    if k == "type": by_type[v] = by_type.get(v, 0) + 1
                    elif k == "source": by_source[v] = by_source.get(v, 0) + 1
                    elif k == "tags": all_tags.extend([t.strip() for t in v.split(",") if t.strip()])
    tag_counts = sorted({t: all_tags.count(t) for t in set(all_tags)}.items(), key=lambda x: -x[1])[:10]

    print("\n📊 审计案例库统计")
    print("=" * 40)
    print("  总案例数: {} 篇".format(total))
    print()
    print("  按类型:")
    for t, c in sorted(by_type.items(), key=lambda x: -x[1]):
        print("    {}: {} 篇".format(t, c))
    print()
    print("  按来源:")
    for s, c in sorted(by_source.items(), key=lambda x: -x[1]):
        print("    {}: {} 篇".format(s, c))
    print()
    print("  热门标签:")
    for t, c in tag_counts:
        print("    {}: {} 篇".format(t, c))


# ════════════════════════════════════════════════════════════
# 主入口
# ════════════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description="政府/国企审计案例采集器")
    parser.add_argument("--manual", action="store_true", help="手动输入案例")
    parser.add_argument("--fetch-url", type=str, help="从URL采集案例")
    parser.add_argument("--wechat", type=str, help="采集微信公众号文章")
    parser.add_argument("--import-md", type=str, help="导入本地Markdown文件")
    parser.add_argument("--migrate", action="store_true", help="迁移已有案例")
    parser.add_argument("--index", action="store_true", help="重建索引")
    parser.add_argument("--stats", action="store_true", help="统计")
    args = parser.parse_args()

    OUTPUT_BASE.mkdir(parents=True, exist_ok=True)

    if args.stats: return show_stats()
    if args.index: return rebuild_index()
    if args.manual: return manual_input()
    if args.migrate: return migrate_existing()
    if args.fetch_url: return fetch_url_workflow(args.fetch_url)
    if args.wechat: return fetch_wechat(args.wechat)
    if args.import_md: return import_markdown(args.import_md)

    parser.print_help()
    print()
    print("💡 推荐用法：")
    print("  # 手动录入（最可靠）")
    print("  python scripts/case_collector.py --manual")
    print()
    print("  # 从URL采集（试试公众号文章）")
    print('  python scripts/case_collector.py --fetch-url "https://mp.weixin.qq.com/s/..."')
    print()
    print("  # 整理索引")
    print("  python scripts/case_collector.py --index")
    print("  python scripts/case_collector.py --stats")


if __name__ == "__main__":
    main()