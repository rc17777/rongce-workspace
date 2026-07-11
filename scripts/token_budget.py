#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
token_budget.py - Token 预算估算器
用途：大任务执行前估算 token 消耗，防止超支

用法：
  python scripts/token_budget.py --task "分析10万字审计报告" --files "path/to/file.docx"
  python scripts/token_budget.py --dir "projects/某项目/raw_data/" --task "生成审计报告"
  python scripts/token_budget.py --confirm --threshold 50000  # 超阈值需确认
"""

import os
import sys

# Windows控制台UTF-8编码修复
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import argparse
import json
from pathlib import Path
from typing import List, Tuple, Optional

# --- 配置 ---
DEFAULT_THRESHOLD = 50000  # 超过此token数需要确认
PRICE_PER_1K = {
    "deepseek-chat": {"input": 0.0015, "output": 0.006},  # 元/千token
    "deepseek-reasoner": {"input": 0.004, "output": 0.016},
    "kimi-k2": {"input": 0.015, "output": 0.060},
}

# 任务类型 → 输出token估算乘数
TASK_MULTIPLIERS = {
    "分析": 0.3,      # 输出 ≈ 输入的30%
    "总结": 0.2,      # 输出 ≈ 输入的20%
    "提取": 0.1,      # 输出 ≈ 输入的10%
    "生成报告": 2.0,   # 输出 ≈ 输入的2倍
    "翻译": 1.2,      # 输出 ≈ 输入的1.2倍
    "问答": 0.5,      # 输出 ≈ 输入的50%
    "ocr": 0.8,       # OCR识别，输出≈输入80%
    "embedding": 0,   # 纯embedding，无输出
    "默认": 0.5,
}

# 思考链模型额外乘数
REASONING_MULTIPLIER = 3.5  # R1/DeepThink 思考过程 ≈ 输出的3.5倍


def estimate_tokens(text: str, is_code: bool = False) -> int:
    """估算文本的token数"""
    if not text:
        return 0
    
    # 检测中英文比例
    cn_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    total_chars = len(text)
    cn_ratio = cn_chars / total_chars if total_chars > 0 else 0
    
    if is_code:
        return int(total_chars * 0.5)
    elif cn_ratio > 0.5:
        # 中文为主
        return int(total_chars * 1.3)
    else:
        # 英文为主（按词估算）
        words = len(text.split())
        return int(words * 1.3)


def read_file(filepath: str) -> Tuple[str, int]:
    """读取文件并返回(内容, token数)"""
    path = Path(filepath)
    if not path.exists():
        return "", 0
    
    # 根据扩展名判断处理方式
    ext = path.suffix.lower()
    is_code = ext in {'.py', '.js', '.java', '.cpp', '.c', '.h', '.go', '.rs', '.ts'}
    
    try:
        if ext in {'.docx', '.doc'}:
            # Word文档：尝试用python-docx
            try:
                from docx import Document
                doc = Document(filepath)
                text = '\n'.join([p.text for p in doc.paragraphs])
                return text, estimate_tokens(text, is_code)
            except ImportError:
                # 退化为按文件大小估算
                size = path.stat().st_size
                return "", int(size * 0.3)  # docx压缩率估算
        
        elif ext == '.pdf':
            # PDF：按文件大小估算（不准确但快速）
            size = path.stat().st_size
            # 扫描件PDF通常1页≈100KB，纯文本PDF更小
            return "", int(size * 0.2)
        
        elif ext in {'.png', '.jpg', '.jpeg', '.gif', '.webp'}:
            # 图片：vision模型估算
            # 通常一张图 ≈ 1k~3k token（取决于分辨率）
            return "", 2000
        
        else:
            # 文本文件
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            return text, estimate_tokens(text, is_code)
            
    except Exception as e:
        print(f"⚠️  读取文件失败 {filepath}: {e}", file=sys.stderr)
        return "", 0


def scan_directory(dirpath: str) -> Tuple[int, List[dict]]:
    """扫描目录，返回(总token数, 文件明细)"""
    total = 0
    details = []
    
    for root, _, files in os.walk(dirpath):
        for fname in files:
            fpath = os.path.join(root, fname)
            _, tokens = read_file(fpath)
            if tokens > 0:
                total += tokens
                details.append({
                    "file": fpath,
                    "tokens": tokens,
                    "size_kb": round(os.path.getsize(fpath) / 1024, 1)
                })
    
    return total, details


def estimate_task_output(input_tokens: int, task_type: str = "默认", 
                         reasoning: bool = False) -> int:
    """估算任务输出token"""
    multiplier = TASK_MULTIPLIERS.get(task_type, TASK_MULTIPLIERS["默认"])
    output = int(input_tokens * multiplier)
    
    if reasoning:
        # 思考链模型：输出 + 思考过程
        thinking = int(output * REASONING_MULTIPLIER)
        output += thinking
    
    return output


def calculate_cost(input_tokens: int, output_tokens: int, 
                   model: str = "deepseek-chat") -> dict:
    """计算费用"""
    price = PRICE_PER_1K.get(model, PRICE_PER_1K["deepseek-chat"])
    input_cost = (input_tokens / 1000) * price["input"]
    output_cost = (output_tokens / 1000) * price["output"]
    total = input_cost + output_cost
    
    return {
        "input_cost": round(input_cost, 4),
        "output_cost": round(output_cost, 4),
        "total_cost": round(total, 4),
        "model": model
    }


def print_budget_report(input_tokens: int, output_tokens: int, 
                        total_tokens: int, cost: dict, 
                        details: List[dict] = None,
                        threshold: int = DEFAULT_THRESHOLD):
    """打印预算报告"""
    print("\n" + "="*60)
    print("📊 Token 预算报告")
    print("="*60)
    print(f"  输入 token:  {input_tokens:,}")
    print(f"  输出 token:  {output_tokens:,}")
    print(f"  总计 token:  {total_tokens:,}")
    print(f"  预估费用:    ¥{cost['total_cost']:.4f} ({cost['model']})")
    print("-"*60)
    
    if total_tokens > threshold:
        print(f"⚠️  警告：超过阈值 {threshold:,} token！")
        print(f"   建议：拆分为多个小任务，或确认后继续。")
    else:
        print(f"✅ 在阈值范围内 ({threshold:,} token)")
    
    if details and len(details) > 0:
        print(f"\n📁 文件明细 (前10个最大的):")
        sorted_details = sorted(details, key=lambda x: x['tokens'], reverse=True)[:10]
        for d in sorted_details:
            fname = os.path.basename(d['file'])
            print(f"   {fname:30s} {d['tokens']:>8,} token  ({d['size_kb']:>6.1f} KB)")
    
    print("="*60)


def main():
    parser = argparse.ArgumentParser(description='Token 预算估算器')
    parser.add_argument('--files', '-f', nargs='+', help='输入文件路径')
    parser.add_argument('--dir', '-d', help='输入目录路径')
    parser.add_argument('--task', '-t', default='默认', 
                       help=f'任务类型: {", ".join(TASK_MULTIPLIERS.keys())}')
    parser.add_argument('--reasoning', '-r', action='store_true',
                       help='使用思考链模型(DeepSeek-R1等)')
    parser.add_argument('--model', '-m', default='deepseek-chat',
                       help='模型名称')
    parser.add_argument('--threshold', type=int, default=DEFAULT_THRESHOLD,
                       help=f'确认阈值 (默认{DEFAULT_THRESHOLD})')
    parser.add_argument('--confirm', '-c', action='store_true',
                       help='超阈值时请求确认')
    parser.add_argument('--json', '-j', action='store_true',
                       help='JSON格式输出')
    
    args = parser.parse_args()
    
    # 估算输入token
    input_tokens = 0
    details = []
    
    if args.files:
        for f in args.files:
            _, tokens = read_file(f)
            input_tokens += tokens
            details.append({"file": f, "tokens": tokens, "size_kb": 0})
    
    if args.dir:
        dir_tokens, dir_details = scan_directory(args.dir)
        input_tokens += dir_tokens
        details.extend(dir_details)
    
    # 估算输出token
    output_tokens = estimate_task_output(input_tokens, args.task, args.reasoning)
    total_tokens = input_tokens + output_tokens
    
    # 计算费用
    cost = calculate_cost(input_tokens, output_tokens, args.model)
    
    # 输出
    if args.json:
        result = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "cost": cost,
            "threshold": args.threshold,
            "exceeded": total_tokens > args.threshold,
            "details": details
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_budget_report(input_tokens, output_tokens, total_tokens, 
                          cost, details, args.threshold)
    
    # 确认模式
    if args.confirm and total_tokens > args.threshold:
        print(f"\n💰 预估费用: ¥{cost['total_cost']:.4f}")
        response = input("是否继续执行? [y/N]: ")
        if response.lower() not in ('y', 'yes'):
            print("❌ 已取消")
            sys.exit(1)
        print("✅ 继续执行")
    
    return 0 if total_tokens <= args.threshold else 2


if __name__ == '__main__':
    sys.exit(main())
