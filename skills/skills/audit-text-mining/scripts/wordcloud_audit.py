"""
审计文本挖掘 - 词云分析工具
对目录中所有 .docx 文件进行中文分词、词频统计、词云可视化。

用法：python wordcloud_audit.py <文档目录路径> [--top 200] [--output wordcloud.png] [--stopwords stopwords.txt]
依赖：pip install python-docx jieba wordcloud pandas openpyxl
"""

import os
import sys
import glob
import argparse
import re
from collections import Counter

import pandas as pd
import jieba

# ============================================================
# 默认停用词（审计文档中常见的无分析价值词汇）
# ============================================================
DEFAULT_STOPWORDS = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
    "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着",
    "没有", "看", "好", "自己", "这", "他", "她", "它", "们", "那", "些",
    "所", "为", "所以", "因为", "但是", "然而", "而且", "虽然", "如果",
    "可以", "这个", "那个", "什么", "怎么", "如何", "为什么", "哪", "吗",
    "啊", "吧", "呢", "哦", "嗯", "哈", "呀", "嘛",
    # 审计文档特有停用词
    "年月日", "年月", "关于", "根据", "按照", "依据", "会议", "研究", "同意",
    "决定", "要求", "通知", "报告", "汇报", "情况", "工作", "进行", "开展",
    "相关", "有关", "涉及", "包括", "主要", "基本", "进一步", "认真",
    "切实", "加强", "加大", "推进", "促进", "确保", "落实", "贯彻",
    "认真贯彻", "贯彻落实", "精神", "指出", "强调", "提出", "认为",
    "各位", "同志", "领导", "负责", "单位", "部门", "一下", "一个",
    "月份", "季度", "年度", "本期", "上期", "同比", "环比",
    "其中", "共计", "合计", "累计", "以上", "以下",
    # 可追加更多
}


def load_stopwords(filepath=None):
    """加载停用词"""
    stopwords = set(DEFAULT_STOPWORDS)
    if filepath and os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                word = line.strip()
                if word and not word.startswith("#"):
                    stopwords.add(word)
    return stopwords


def extract_text_from_docx(filepath):
    """提取 .docx 文件中所有段落文本"""
    try:
        from docx import Document
    except ImportError:
        print("❌ 缺少 python-docx 库，请执行：pip install python-docx")
        sys.exit(1)

    try:
        doc = Document(filepath)
        paragraphs = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                paragraphs.append(text)
        return "\n".join(paragraphs)
    except Exception as e:
        print(f"  ⚠️  无法读取 {os.path.basename(filepath)}: {e}")
        return ""


def generate_wordcloud(text, output_path, font_path=None, top_n=200):
    """生成词云图"""
    try:
        from wordcloud import WordCloud
        import matplotlib.pyplot as plt
    except ImportError:
        print("❌ 缺少 wordcloud 或 matplotlib 库")
        print("   请执行：pip install wordcloud matplotlib")
        return None

    # 尝试设置中文字体
    if font_path is None:
        # Windows 常见中文字体路径
        candidates = [
            "C:\\Windows\\Fonts\\msyh.ttc",       # 微软雅黑
            "C:\\Windows\\Fonts\\simhei.ttf",      # 黑体
            "C:\\Windows\\Fonts\\simsun.ttc",      # 宋体
            "C:\\Windows\\Fonts\\STSONG.TTF",      # 华文宋体
        ]
        for fp in candidates:
            if os.path.exists(fp):
                font_path = fp
                break

    if font_path is None:
        print("⚠️  未找到中文字体，词云可能无法正常显示中文")
        print("   请手动指定 --font 参数指向中文字体路径")
        font_path = "C:\\Windows\\Fonts\\msyh.ttc"  # 尝试默认

    try:
        wc = WordCloud(
            font_path=font_path,
            width=1200,
            height=800,
            background_color="white",
            max_words=top_n,
            max_font_size=200,
            random_state=42,
            collocations=False,
        )
        wc.generate(text)
        wc.to_file(output_path)
        return wc
    except Exception as e:
        print(f"❌ 词云生成失败：{e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="审计文档词云分析工具")
    parser.add_argument("directory", help="文档目录路径")
    parser.add_argument("--top", type=int, default=200, help="显示高频词数量（默认200）")
    parser.add_argument("--output", default="wordcloud.png", help="词云图输出路径")
    parser.add_argument("--stopwords", default=None, help="自定义停用词文件路径")
    parser.add_argument("--font", default=None, help="中文字体路径")
    parser.add_argument("--excel", default="词频统计.xlsx", help="词频统计Excel输出路径")
    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"❌ 目录不存在：{args.directory}")
        sys.exit(1)

    # 加载停用词
    stopwords = load_stopwords(args.stopwords)
    print(f"📋 已加载 {len(stopwords)} 个停用词")

    # 提取所有文档文本
    docx_files = glob.glob(os.path.join(args.directory, "*.docx"))
    if not docx_files:
        print("📭 目录中没有找到 .docx 文件")
        print("   提示：如有 .doc 文件，请先运行 doc_to_docx.py 转换格式")
        sys.exit(1)

    print(f"📄 找到 {len(docx_files)} 个 .docx 文件，正在提取文本...")
    all_text = []
    file_count = 0
    for filepath in docx_files:
        text = extract_text_from_docx(filepath)
        if text:
            all_text.append(text)
            file_count += 1

    if not all_text:
        print("❌ 未能从任何文档中提取到文本")
        sys.exit(1)

    combined_text = "\n".join(all_text)
    print(f"✅ 成功提取 {file_count}/{len(docx_files)} 个文件，共 {len(combined_text)} 字符")

    # Jieba 分词
    print("🔪 正在进行中文分词...")
    words = jieba.cut(combined_text)
    # 过滤：长度>1、非纯数字、非停用词
    filtered_words = []
    for w in words:
        w = w.strip()
        if len(w) <= 1:
            continue
        if re.match(r'^[\d\.]+$', w):  # 纯数字/小数
            continue
        if w in stopwords:
            continue
        filtered_words.append(w)

    # 词频统计
    word_counts = Counter(filtered_words)
    top_words = word_counts.most_common(args.top)

    print(f"\n📊 Top 20 高频词：")
    print("-" * 40)
    for i, (word, count) in enumerate(top_words[:20], 1):
        bar = "█" * min(count // max(1, top_words[0][1] // 20), 40)
        print(f"  {i:2d}. {word:<10s} {count:>6d}  {bar}")

    # 导出词频 Excel
    df = pd.DataFrame(top_words, columns=["关键词", "词频"])
    df.index = df.index + 1
    df.index.name = "排名"
    df.to_excel(args.excel)
    print(f"\n💾 词频统计已保存：{args.excel}")

    # 生成词云
    print("☁️  正在生成词云图...")
    # 构造词云文本（按频率重复）
    wc_text = " ".join(filtered_words)
    wc = generate_wordcloud(wc_text, args.output, font_path=args.font, top_n=args.top)
    if wc:
        print(f"💾 词云图已保存：{args.output}")

    # 输出审计重点建议
    print(f"\n🎯 审计重点关键词建议：")
    print(f"   可将以下高频词用于 keyword_search.py 批量定位：")
    keyword_candidates = [w for w, _ in top_words[:15]]
    print(f"   {'|'.join(keyword_candidates)}")


if __name__ == "__main__":
    main()
