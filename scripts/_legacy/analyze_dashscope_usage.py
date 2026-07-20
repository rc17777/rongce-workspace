#!/usr/bin/env python3
"""
DashScope (阿里云百炼) 用量分析器
================================
分析 OpenClaw 工作区中可能触发 Qwen-VL 图片模型调用的场景。

注意：DashScope 的详细账单需要从阿里云控制台导出，本脚本仅分析本地工作区中
可能触发图片模型调用的操作记录。
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime, timezone, timedelta

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TZ = timezone(timedelta(hours=8))
ROOT = Path("D:/openclaw-workspace")

# ── 分析 memory 文件中的图片相关操作 ──

def analyze_image_operations():
    """分析 memory 文件中可能触发图片模型调用的操作"""
    
    memory_dir = ROOT / "memory"
    if not memory_dir.exists():
        print("memory 目录不存在")
        return
    
    image_keywords = [
        "图片", "image", "OCR", "ocr", "扫描", "截图", "照片",
        "qwen-vl", "dashscope", "vl-max", "视觉", "vision"
    ]
    
    results = []
    
    for md_file in sorted(memory_dir.glob("2026-06-*.md")):
        content = md_file.read_text(encoding="utf-8", errors="replace")
        date = md_file.stem
        
        # 统计图片相关关键词出现次数
        mentions = 0
        contexts = []
        
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if any(kw in line for kw in image_keywords):
                mentions += 1
                # 提取上下文
                start = max(0, i-1)
                end = min(len(lines), i+2)
                ctx = ' | '.join(lines[start:end])
                if len(ctx) > 200:
                    ctx = ctx[:200] + "..."
                contexts.append(ctx)
        
        if mentions > 0:
            results.append({
                "date": date,
                "mentions": mentions,
                "contexts": contexts[:5]  # 最多5条上下文
            })
    
    return results

# ── 输出报告 ──

def main():
    print("=" * 70)
    print("DashScope (Qwen-VL) 用量来源分析")
    print("=" * 70)
    print()
    print("⚠️  DashScope 的详细账单需从阿里云控制台导出")
    print("     https://bailian.console.aliyun.com/#/home")
    print()
    
    # 分析本地记录
    results = analyze_image_operations()
    
    if not results:
        print("未在 memory 文件中找到图片相关操作记录")
        return
    
    print("📅 按日期统计可能触发 Qwen-VL 调用的操作:")
    print("-" * 70)
    
    total_mentions = 0
    for r in results:
        print(f"\n{r['date']}: {r['mentions']} 次图片相关提及")
        total_mentions += r['mentions']
        for ctx in r['contexts']:
            print(f"  • {ctx}")
    
    print()
    print("-" * 70)
    print(f"总计: {total_mentions} 次图片相关操作记录")
    print()
    
    # 高消耗日提醒
    high_days = [r for r in results if r['mentions'] >= 5]
    if high_days:
        print("🔥 高消耗风险日（图片操作密集）:")
        for r in high_days:
            print(f"  • {r['date']}: {r['mentions']} 次")
        print()
    
    # 建议
    print("=" * 70)
    print("💡 控制 DashScope 费用的建议:")
    print("=" * 70)
    print("""
1. 【确认配置】检查 OpenClaw 是否配置了 imageModel 走 dashscope:
   查看配置: openclaw gateway config.get | findstr dashscope
   
2. 【按需使用】图片分析只在必要时调用:
   - 审计报告中的图片 → 可先用本地 OCR (PaddleOCR/Tesseract)
   - 截图/照片 → 如果不是必须 AI 分析，尽量不用
   
3. 【批量替代】大量图片处理时:
   - 用本地 PaddleOCR 替代 Qwen-VL (已配置)
   - 或用 python-pptx / Pillow 本地处理
   
4. 【监控余额】定期查看 DashScope 控制台:
   https://bailian.console.aliyun.com/#/home
   
5. 【限额设置】在阿里云控制台设置用量告警:
   - 余额低于 ¥X 时短信/邮件通知
   - 设置单 API Key 的调用上限
""")

if __name__ == "__main__":
    main()
