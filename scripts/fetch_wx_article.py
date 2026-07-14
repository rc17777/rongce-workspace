"""微信公众号文章抓取 + 入库"""
import urllib.request, re, html as html_mod, json, sys, hashlib
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE = Path(r"C:\Users\scrccpa\.openclaw\workspace")

def fetch_wx_article(url, save_to_kb=True):
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    resp = urllib.request.urlopen(req, timeout=15)
    raw = resp.read().decode('utf-8')

    title_m = re.search(r'<title>(.+?)</title>', raw)
    title = title_m.group(1).strip() if title_m else '无标题'
    
    # 微信富文本内容
    content_m = re.search(r'id="js_content"[^>]*>(.+?)</div>\s*<script', raw, re.DOTALL)
    if not content_m:
        content_m = re.search(r'id="js_content"[^>]*>(.+?)</div>\s*</div>', raw, re.DOTALL)
    
    text = ""
    if content_m:
        text = content_m.group(1)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = html_mod.unescape(text).strip()
    
    # 提取公众号名称
    author_m = re.search(r'var nickname\s*=\s*["\']([^"\']+)', raw)
    author = author_m.group(1) if author_m else ''
    
    # 提取描述
    desc_m = re.search(r'var msg_desc\s*=\s*["\']([^"\']+)', raw)
    desc = desc_m.group(1) if desc_m else ''
    
    print(f"标题: {title}")
    print(f"公众号: {author}")
    print(f"摘要: {desc[:100]}")
    print(f"正文长度: {len(text)} 字")
    
    if save_to_kb and text:
        today = datetime.now().strftime("%Y%m%d")
        article_id = hashlib.md5(url.encode()).hexdigest()[:12]
        
        # 保存到知识库
        out_dir = WORKSPACE / "knowledge" / "intel_raw" / "wechat"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{today}_{article_id}.md"
        
        content = f"""---
source: wechat
source_name: {author}
source_url: {url}
title: {title}
fetched_at: {datetime.now().isoformat()}
content_length: {len(text)}
---

# {title}

> 来源: [{author}]({url})
> 采集时间: {today}

## 摘要

{desc}

## 正文

{text[:10000]}
"""
        out_path.write_text(content, encoding='utf-8')
        print(f"\n✅ 已保存: {out_path}")
        return out_path
    
    return text

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else input("输入微信文章URL: ")
    fetch_wx_article(url.strip())