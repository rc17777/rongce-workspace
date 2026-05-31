"""
审计文本挖掘 - 多关键词批量定位工具
在目录中所有 .docx 文件中搜索多个关键词，提取上下文并导出Excel。

用法：
  python keyword_search.py <文档目录路径> --keywords "关键词1|关键词2|关键词3" [--context 50] [--output 结果.xlsx]
  python keyword_search.py <文档目录路径> --keyword-file keywords.txt [--context 50] [--output 结果.xlsx]

依赖：pip install python-docx pandas openpyxl
"""

import os
import sys
import glob
import re
import argparse

import pandas as pd


def extract_paragraphs(filepath):
    """提取 .docx 文件中所有段落，返回 [(段落号, 文本), ...]"""
    try:
        from docx import Document
    except ImportError:
        print("❌ 缺少 python-docx 库，请执行：pip install python-docx")
        sys.exit(1)

    try:
        doc = Document(filepath)
        paragraphs = []
        for i, para in enumerate(doc.paragraphs, 1):
            text = para.text.strip()
            if text:
                paragraphs.append((i, text))
        return paragraphs
    except Exception as e:
        print(f"  ⚠️  无法读取 {os.path.basename(filepath)}: {e}")
        return []


def extract_context(text, match_start, match_end, context_chars=50):
    """提取匹配位置前后各 context_chars 个字符的上下文"""
    start = max(0, match_start - context_chars)
    end = min(len(text), match_end + context_chars)

    prefix = ""
    suffix = ""

    if start > 0:
        prefix = "..." + text[start:match_start]
    else:
        prefix = text[start:match_start]

    if end < len(text):
        suffix = text[match_end:end] + "..."
    else:
        suffix = text[match_end:end]

    return prefix, text[match_start:match_end], suffix


def search_keywords(directory, keywords, context_chars=50):
    """批量搜索关键词"""
    docx_files = glob.glob(os.path.join(directory, "*.docx"))
    if not docx_files:
        print("📭 目录中没有找到 .docx 文件")
        return []

    # 编译正则：匹配任意一个关键词
    pattern = re.compile("|".join(re.escape(kw) for kw in keywords))

    results = []
    total_hits = 0

    print(f"🔍 在 {len(docx_files)} 个文件中搜索 {len(keywords)} 个关键词...")
    print(f"   关键词：{' | '.join(keywords)}")
    print()

    for filepath in docx_files:
        filename = os.path.basename(filepath)
        paragraphs = extract_paragraphs(filepath)
        if not paragraphs:
            continue

        file_hits = 0
        for para_num, text in paragraphs:
            for match in pattern.finditer(text):
                prefix, keyword, suffix = extract_context(
                    text, match.start(), match.end(), context_chars
                )
                results.append({
                    "文件名": filename,
                    "段落号": para_num,
                    "关键词": keyword,
                    "上下文": f"{prefix}【{keyword}】{suffix}",
                    "所在段落全文": text,  # 方便核查时看完整段落
                })
                file_hits += 1
                total_hits += 1

        if file_hits > 0:
            print(f"  📄 {filename}: {file_hits} 处匹配")

    return results, total_hits


def main():
    parser = argparse.ArgumentParser(description="审计文档多关键词批量定位工具")
    parser.add_argument("directory", help="文档目录路径")
    parser.add_argument("--keywords", default=None, help="关键词列表，用 | 分隔，如 '借款|奖励|土地'")
    parser.add_argument("--keyword-file", default=None, help="从文件读取关键词（每行一个）")
    parser.add_argument("--context", type=int, default=50, help="上下文字符数（默认50）")
    parser.add_argument("--output", default="关键词定位结果.xlsx", help="输出Excel路径")
    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"❌ 目录不存在：{args.directory}")
        sys.exit(1)

    # 解析关键词
    keywords = []
    if args.keywords:
        keywords = [kw.strip() for kw in args.keywords.split("|") if kw.strip()]
    elif args.keyword_file:
        if os.path.exists(args.keyword_file):
            with open(args.keyword_file, "r", encoding="utf-8") as f:
                keywords = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        else:
            print(f"❌ 关键词文件不存在：{args.keyword_file}")
            sys.exit(1)
    else:
        print("❌ 请指定关键词：--keywords '词1|词2|词3' 或 --keyword-file keywords.txt")
        sys.exit(1)

    if not keywords:
        print("❌ 未指定有效的关键词")
        sys.exit(1)

    # 搜索
    results, total_hits = search_keywords(args.directory, keywords, args.context)

    if not results:
        print("\n📭 未找到任何匹配")
        return

    # 导出 Excel
    df = pd.DataFrame(results)
    # 按文件名、段落号排序
    df = df.sort_values(["文件名", "段落号"])
    df.to_excel(args.output, index=False)

    # 统计
    print(f"\n📊 搜索结果：")
    print(f"   总匹配数：{total_hits}")
    print(f"   涉及文件：{df['文件名'].nunique()} 个")
    print(f"\n   各关键词命中次数：")
    for kw in keywords:
        count = df[df["关键词"] == kw].shape[0]
        print(f"     {kw}: {count} 次")
    print(f"\n💾 结果已保存：{args.output}")


if __name__ == "__main__":
    main()
