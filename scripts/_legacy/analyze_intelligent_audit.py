#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度分析23篇智能化审计文章
"""
import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

INPUT_DIR = r"E:\2026\审计方法\智能化\ocr_output"
OUTPUT_DIR = r"E:\2026\审计方法\智能化\analysis_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def read_all_articles():
    """读取所有文章"""
    articles = []
    md_files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.md') and f != 'ocr_report.json']
    
    for md_file in sorted(md_files):
        file_path = os.path.join(INPUT_DIR, md_file)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取标题
        title = md_file.replace('.md', '')
        lines = content.split('\n')
        if lines and lines[0].startswith('# '):
            title = lines[0][2:].strip()
        
        articles.append({
            'filename': md_file,
            'title': title,
            'content': content,
            'length': len(content)
        })
    
    return articles

def extract_metadata(content):
    """提取文章元数据"""
    meta = {
        'abstract': '',
        'keywords': [],
        'authors': '',
        'pages': content.count('## 第'),
        'has_tables': 'table' in content.lower() or '表' in content,
        'has_figures': '图' in content or 'figure' in content.lower(),
    }
    
    # 提取摘要
    abstract_match = re.search(r'【摘要[】](.*?)(?=【关键词|关键词)', content, re.DOTALL)
    if abstract_match:
        meta['abstract'] = abstract_match.group(1).strip()[:500]
    
    # 提取关键词
    kw_match = re.search(r'【关键词[】](.*?)(?=\n)', content)
    if kw_match:
        kw_text = kw_match.group(1)
        meta['keywords'] = [k.strip() for k in re.split(r'[\s,;，；]', kw_text) if k.strip()]
    
    return meta

def analyze_themes(content):
    """分析主题分类"""
    themes = []
    
    # 技术主题
    tech_patterns = {
        '大语言模型/LLM': ['大语言模型', 'LLM', '大模型', 'GPT', '生成式AI'],
        '机器学习': ['机器学习', '深度学习', '神经网络', '算法模型'],
        '大数据': ['大数据', '数据挖掘', '数据分析', '数据融合'],
        'RPA/自动化': ['RPA', '机器人流程', '自动化'],
        '自然语言处理': ['自然语言', 'NLP', '文本挖掘', '语义分析'],
        '计算机视觉': ['图像识别', 'OCR', '视觉', '视频分析'],
        '知识图谱': ['知识图谱', '图谱', '关系网络'],
    }
    
    # 应用领域
    app_patterns = {
        '医保审计': ['医保', '医疗', '医院'],
        '工程审计': ['工程', '结算', '造价', '建设项目'],
        '企业内审': ['内部审计', '内审', '企业'],
        '政府审计': ['政府', '财政', '专项债', '预算'],
        '招投标审计': ['招投标', '招标', '投标', '围标', '串标'],
        '金融审计': ['银行', '保险', '金融', '投资'],
        '经责审计': ['经济责任', '经责', '离任'],
        '绩效审计': ['绩效', '效益', '评价'],
    }
    
    # 方法论主题
    method_patterns = {
        '穿透式审计': ['穿透式', '穿透'],
        '持续审计': ['持续审计', '实时审计', '动态监控'],
        '风险导向': ['风险', '预警', '风险评估'],
        '数据驱动': ['数据驱动', '数据赋能'],
        '智能化转型': ['数字化转型', '智能化', '数智化'],
    }
    
    for category, patterns in [('技术', tech_patterns), ('应用', app_patterns), ('方法论', method_patterns)]:
        for theme_name, keywords in patterns.items():
            if any(kw in content for kw in keywords):
                themes.append(f"{category}:{theme_name}")
    
    return themes

def analyze_structure(content):
    """分析文章结构"""
    structure = {
        'has_introduction': bool(re.search(r'引言|绪论|一、引言|一、问题的提出', content)),
        'has_literature': bool(re.search(r'文献综述|研究现状|国内外研究', content)),
        'has_methodology': bool(re.search(r'研究方法|研究设计| methodology', content)),
        'has_case_study': bool(re.search(r'案例分析|实证研究|以.*为例|实践应用', content)),
        'has_conclusion': bool(re.search(r'结论|结语|总结与展望', content)),
        'has_references': bool(re.search(r'参考文献|References', content)),
        'section_count': len(re.findall(r'[一二三四五六七八九十]、', content)),
    }
    return structure

def generate_summary(articles):
    """生成综合分析摘要"""
    summary = {
        'total_articles': len(articles),
        'total_pages': sum(a['meta']['pages'] for a in articles),
        'avg_pages': round(sum(a['meta']['pages'] for a in articles) / len(articles), 1),
        'theme_distribution': {},
        'tech_mentions': {},
        'app_mentions': {},
        'method_mentions': {},
        'article_summaries': []
    }
    
    # 统计主题分布
    for article in articles:
        for theme in article['themes']:
            category, name = theme.split(':', 1)
            if category not in summary['theme_distribution']:
                summary['theme_distribution'][category] = {}
            if name not in summary['theme_distribution'][category]:
                summary['theme_distribution'][category][name] = 0
            summary['theme_distribution'][category][name] += 1
    
    # 文章摘要
    for article in articles:
        summary['article_summaries'].append({
            'title': article['title'],
            'pages': article['meta']['pages'],
            'keywords': article['meta']['keywords'][:5],
            'themes': article['themes'],
            'abstract_preview': article['meta']['abstract'][:200] if article['meta']['abstract'] else '未提取到摘要'
        })
    
    return summary

def main():
    print("=" * 60)
    print("深度分析 - 智能化审计文章")
    print("=" * 60)
    
    # 读取文章
    print("\n读取文章...")
    articles = read_all_articles()
    print(f"✓ 读取了 {len(articles)} 篇文章")
    
    # 分析每篇文章
    print("\n分析文章元数据和主题...")
    for i, article in enumerate(articles, 1):
        print(f"  [{i}/{len(articles)}] {article['title'][:40]}...")
        article['meta'] = extract_metadata(article['content'])
        article['themes'] = analyze_themes(article['content'])
        article['structure'] = analyze_structure(article['content'])
    
    # 生成综合分析
    print("\n生成综合分析...")
    summary = generate_summary(articles)
    
    # 保存详细分析结果
    analysis_path = os.path.join(OUTPUT_DIR, "detailed_analysis.json")
    with open(analysis_path, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': summary,
            'articles': [
                {
                    'title': a['title'],
                    'filename': a['filename'],
                    'meta': a['meta'],
                    'themes': a['themes'],
                    'structure': a['structure']
                }
                for a in articles
            ]
        }, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 详细分析已保存: {analysis_path}")
    
    # 生成Markdown报告
    report_path = os.path.join(OUTPUT_DIR, "analysis_report.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# 智能化审计文章深度分析报告\n\n")
        f.write(f"*分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        f.write("---\n\n")
        
        # 总体统计
        f.write("## 一、总体统计\n\n")
        f.write(f"- **文章总数**: {summary['total_articles']} 篇\n")
        f.write(f"- **总页数**: {summary['total_pages']} 页\n")
        f.write(f"- **平均每篇**: {summary['avg_pages']} 页\n\n")
        
        # 主题分布
        f.write("## 二、主题分布\n\n")
        for category, themes in summary['theme_distribution'].items():
            f.write(f"### {category}维度\n\n")
            for theme, count in sorted(themes.items(), key=lambda x: -x[1]):
                f.write(f"- {theme}: {count} 篇\n")
            f.write("\n")
        
        # 文章详情
        f.write("## 三、文章详情\n\n")
        for i, article_summary in enumerate(summary['article_summaries'], 1):
            f.write(f"### {i}. {article_summary['title']}\n\n")
            f.write(f"- **页数**: {article_summary['pages']}\n")
            f.write(f"- **关键词**: {', '.join(article_summary['keywords']) if article_summary['keywords'] else '未提取'}\n")
            f.write(f"- **主题标签**: {', '.join(article_summary['themes'])}\n")
            f.write(f"- **摘要预览**: {article_summary['abstract_preview']}\n\n")
    
    print(f"✓ 分析报告已保存: {report_path}")
    
    # 打印摘要
    print("\n" + "=" * 60)
    print("分析完成!")
    print("=" * 60)
    print(f"文章总数: {summary['total_articles']}")
    print(f"总页数: {summary['total_pages']}")
    print(f"平均每篇: {summary['avg_pages']} 页")
    print("\n主题分布:")
    for category, themes in summary['theme_distribution'].items():
        print(f"\n  {category}:")
        for theme, count in sorted(themes.items(), key=lambda x: -x[1]):
            print(f"    - {theme}: {count}篇")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
