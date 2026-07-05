#!/usr/bin/env python3
"""
审计情报采集器 v1.0
采集来源：审计署、财政部、各省审计厅等政府网站
输出：knowledge/policies/ 下的 .md 文件
"""

import json, os, sys, re, datetime, hashlib, subprocess, tempfile
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config" / "audit_intel_config.json"
POLICY_DIR = Path(__file__).parent.parent / "knowledge" / "policies"
INTEL_LOG  = Path(__file__).parent.parent / "logs" / "audit_intel"
SUMMARY_DIR = Path(__file__).parent.parent / "knowledge" / "intel_summaries"
HISTORY_FILE = INTEL_LOG / "collection_history.json"

def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_history():
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"collected": {}, "last_run": None}

def save_history(history):
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def fetch_url(url, timeout=20):
    """Try to fetch a URL using available methods"""
    # Method 1: Try urllib with NO proxy (China gov sites often blocked by proxy)
    try:
        import urllib.request
        proxy_support = urllib.request.ProxyHandler({})
        opener = urllib.request.build_opener(proxy_support)
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        })
        with opener.open(req, timeout=timeout) as resp:
            content = resp.read().decode('utf-8', errors='replace')
            if len(content) > 200:
                return content
    except Exception as e:
        pass
    
    # Method 2: Try urllib with system proxy
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read().decode('utf-8', errors='replace')
            if len(content) > 200:
                return content
    except Exception as e:
        pass
    
    # Method 3: Try PowerShell bypassing proxy (direct)
    try:
        ps_cmd = f"""
        $wc = New-Object System.Net.WebClient
        $wc.Proxy = [System.Net.GlobalProxySelection]::GetEmptyWebProxy()
        try {{
            $s = $wc.DownloadString('{url}')
            Write-Output $s
        }} catch {{
            # Fallback: try with system proxy
            $wc.Proxy = [System.Net.WebRequest]::GetSystemWebProxy()
            $s = $wc.DownloadString('{url}')
            Write-Output $s
        }}
        """
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=timeout+5
        )
        if result.returncode == 0 and len(result.stdout) > 200:
            return result.stdout
    except:
        pass
    
    return None

def extract_text_from_html(html):
    """Basic HTML to text extraction"""
    # Remove script/style
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL|re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL|re.IGNORECASE)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '\n', text)
    # Decode entities
    text = text.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&amp;', '&').replace('&quot;', '"')
    # Collapse whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

def save_policy(source_name, content, source_url):
    """Save collected content as a markdown policy file"""
    POLICY_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    
    # Generate filename from source name
    safe_name = re.sub(r'[\\/:*?"<>|]', '_', source_name)
    filename = f"{date_str}_{safe_name}.md"
    filepath = POLICY_DIR / filename
    
    # Extract title and key content
    title = source_name
    lines = content.split('\n')
    for line in lines[:50]:
        line = line.strip()
        if 10 < len(line) < 120 and ('审计' in line or '财政部' in line or '通知' in line or '办法' in line):
            title = line
            break
    
    md_content = f"""---
title: "{title}"
source: "{source_name}"
url: "{source_url}"
collected: "{timestamp}"
status: "raw"
---

# {title}

> **采集来源**: {source_name}  
> **采集时间**: {timestamp}  
> **原始URL**: {source_url}

---

{content}

---

*本文由审计情报采集器自动采集，需人工审核后归档。*
"""
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"  ✅ 已保存: {filename} ({len(content)} chars)")
    return filename

def fetch_source(source):
    """Fetch a single source and save"""
    name = source.get("name", "unknown")
    url = source.get("url", "")
    stype = source.get("type", "static")
    schedule = source.get("schedule", "weekly")
    
    print(f"\n📡 {name}")
    print(f"   URL: {url}")
    print(f"   Type: {stype} | Schedule: {schedule}")
    
    content = fetch_url(url)
    if content:
        text = extract_text_from_html(content)
        # Only save if substantial content
        if len(text) > 500:
            filename = save_policy(name, text, url)
            return {"name": name, "url": url, "status": "success", "file": filename, "len": len(text)}
        else:
            print(f"  ⚠️ 内容太少 ({len(text)} chars)，跳过")
            return {"name": name, "url": url, "status": "too_short", "len": len(text)}
    else:
        print(f"  ❌ 无法访问")
        return {"name": name, "url": url, "status": "unreachable"}


def generate_daily_report(results):
    """Generate a daily intel summary report"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    success = [r for r in results if r.get("status") == "success"]
    failed = [r for r in results if r.get("status") != "success"]
    
    report = f"""---
title: "审计情报日报 {date_str}"
generated: "{timestamp}"
total_sources: {len(results)}
success: {len(success)}
failed: {len(failed)}
---

# 审计情报日报 {date_str}

## 采集概况

- 计划采集: {len(results)} 个来源
- 成功: {len(success)} 个
- 失败: {len(failed)} 个

## 成功采集

"""
    for r in success:
        report += f"- ✅ **{r['name']}** → `{r['file']}` ({r['len']} chars)\n"
    
    report += "\n## 失败来源\n"
    for r in failed:
        report += f"- ❌ **{r['name']}** — {r.get('status', 'unknown')}\n"
    
    report += "\n---\n*本报告由审计情报采集器自动生成*\n"
    
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    report_file = SUMMARY_DIR / f"intel_report_{date_str}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📊 日报已生成: {report_file}")
    return report

def main():
    print("=" * 60)
    print("  审计情报采集器 v1.0")
    print(f"  运行时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Ensure directories exist
    for d in [POLICY_DIR, INTEL_LOG, SUMMARY_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    
    # Load config and history
    config = load_config()
    history = load_history()
    
    print(f"\n📋 配置加载: {len(config.get('sources', {}))} 个来源分类")
    
    all_results = []
    
    # Iterate through all source groups
    for group_name, sources in config.get("sources", {}).items():
        print(f"\n{'─' * 40}")
        print(f"📁 来源分组: {group_name} ({len(sources)} 个)")
        print(f"{'─' * 40}")
        
        for source in sources:
            result = fetch_source(source)
            all_results.append(result)
    
    # Generate report
    report = generate_daily_report(all_results)
    
    # Check if anything new was collected
    new_count = sum(1 for r in all_results if r.get("status") == "success")
    
    print(f"\n{'=' * 60}")
    print(f"  采集完成: {new_count}/{len(all_results)} 成功")
    print(f"{'=' * 60}")
    
    return new_count > 0

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result else 1)
