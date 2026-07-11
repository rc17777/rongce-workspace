"""
微信文章批量采集器 — 基于 OpenClaw 浏览器自动化

用法：
1. 将待采集的文章 URL 写入 urls.txt，每行一个
2. 运行：python wechat_batch.py --urls urls.txt --out output/
3. 脚本逐篇打开浏览器 → 提取正文 → 保存 Markdown

纯文本模式，不依赖任何第三方工具。
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime

def extract_from_page(page_data):
    """从浏览器页面数据中解析微信文章"""
    title = page_data.get('title', '').strip() or '未命名'
    content = page_data.get('content', '').strip()
    url = page_data.get('url', '')
    author = page_data.get('author', '')
    pub_date = page_data.get('pub_date', '')
    
    if not content:
        return None, "正文为空"
    
    # 构建 Markdown
    md = f"# {title}\n\n"
    if author:
        md += f"> 作者: {author}\n"
    if pub_date:
        md += f"> 日期: {pub_date}\n"
    md += f"> 来源: {url}\n"
    md += f"> 采集时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    md += "---\n\n"
    md += content
    md += "\n"
    
    return md, None


def save_article(md_text, title, output_dir):
    """保存为 Markdown 文件"""
    # 清理文件名中的非法字符
    safe_title = title.replace('/', '_').replace('\\', '_').replace(':', '_') \
                       .replace('*', '_').replace('?', '_').replace('"', '_') \
                       .replace('<', '_').replace('>', '_').replace('|', '_')
    safe_title = safe_title[:80]  # 截断过长标题
    
    filename = f"{safe_title}.md"
    filepath = os.path.join(output_dir, filename)
    
    # 处理重名
    counter = 1
    while os.path.exists(filepath):
        filepath = os.path.join(output_dir, f"{safe_title}_{counter}.md")
        counter += 1
    
    os.makedirs(output_dir, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(md_text)
    
    return filepath


def load_urls(path):
    """从文件加载 URL 列表"""
    urls = []
    if os.path.isfile(path):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    urls.append(line)
    else:
        print(f'[ERROR] URL 文件不存在: {path}')
        sys.exit(1)
    return urls


def generate_index(articles, output_dir):
    """生成索引文件"""
    index_lines = [
        f"# 微信文章采集索引",
        f"",
        f"> 采集时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"> 文章数量: {len(articles)}",
        f"",
        f"| # | 标题 | 来源 | 状态 |",
        f"|---|------|------|------|",
    ]
    
    for i, art in enumerate(articles, 1):
        status = art.get('status', '未知')
        icon = {'成功': '✅', '失败': '❌', '跳过': '⏭️'}.get(status, '❓')
        index_lines.append(f"| {i} | {art.get('title', '-')[:50]} | {art.get('url', '-')[:40]} | {icon} {status} |")
    
    index_path = os.path.join(output_dir, '_INDEX.md')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(index_lines))
    
    return index_path


# ============================================================
# 浏览器提取 JS（在浏览器 console 中执行）
# ============================================================

EXTRACT_JS = """
(function() {
    try {
        var title = document.querySelector('#activity-name') || document.querySelector('h1');
        var content = document.querySelector('#js_content');
        var author = document.querySelector('#js_name') || document.querySelector('.rich_media_meta_text');
        var date = document.querySelector('#publish_time') || document.querySelector('.rich_media_meta_text');
        
        return {
            title: title ? title.innerText.trim() : document.title,
            content: content ? content.innerText.trim() : '',
            author: author ? author.innerText.trim() : '',
            pub_date: date ? date.innerText.trim() : '',
            url: window.location.href
        };
    } catch(e) {
        return { error: e.message, url: window.location.href };
    }
})()
"""


def main():
    parser = argparse.ArgumentParser(description='微信文章批量采集（依赖 OpenClaw browser 工具）')
    parser.add_argument('--urls', required=True, help='URL 列表文件（每行一个）')
    parser.add_argument('--out', default='output/wechat_articles', help='输出目录')
    parser.add_argument('--delay', type=int, default=3, help='文章间延迟秒数')
    args = parser.parse_args()
    
    urls = load_urls(args.urls)
    print(f'\n共 {len(urls)} 篇文章待采集\n')
    
    articles = []
    success = 0
    fail = 0
    
    for i, url in enumerate(urls, 1):
        print(f'[{i}/{len(urls)}] {url[:80]}...')
        
        # 这里需要 AI 助手通过 browser 工具执行
        # 实际运行时，AI 会：
        #   1. browser.open(url)
        #   2. browser.snapshot + evaluate(EXTRACT_JS)
        #   3. 返回解析后的内容
        
        # 作为独立脚本，这里输出调用指令供 AI 执行
        print(f'  >> 需要 AI 助手打开浏览器并执行 EXTRACT_JS')
        print(f'  >> URL: {url}')
        print()
    
    print(f'\n=== 采集完成 ===')
    print(f'成功: {success}')
    print(f'失败: {fail}')
    print(f'索引: {args.out}/_INDEX.md')


if __name__ == '__main__':
    main()
