#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
workflow_with_budget.py - 带Token预算检查的工作流包装器
用法：在任意任务脚本前加一层预算检查，防止超支

集成方式：
  from workflow_with_budget import check_budget
  
  # 任务前检查
  budget_ok, estimate = check_budget(
      files=["report.docx"],
      task="生成报告",
      reasoning=True,
      threshold=100000,
      auto_confirm=True  # 超阈值时自动提示确认
  )
  if not budget_ok:
      sys.exit(1)
  
  # 执行实际任务...
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import List, Tuple, Optional, Dict

# Windows控制台UTF-8编码修复
if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# 预算脚本路径
BUDGET_SCRIPT = Path(__file__).parent / "token_budget.py"

# 各任务类型默认阈值（token数）
DEFAULT_THRESHOLDS = {
    "ocr": 100000,
    "embedding": 500000,
    "生成报告": 100000,
    "分析": 50000,
    "翻译": 50000,
    "问答": 30000,
    "总结": 30000,
    "提取": 20000,
    "默认": 50000,
}

# 各任务类型默认模型
DEFAULT_MODELS = {
    "ocr": "deepseek-chat",
    "embedding": "deepseek-chat",
    "生成报告": "deepseek-reasoner",
    "分析": "deepseek-reasoner",
    "默认": "deepseek-chat",
}


def check_budget(
    files: Optional[List[str]] = None,
    directory: Optional[str] = None,
    task: str = "默认",
    reasoning: bool = False,
    model: Optional[str] = None,
    threshold: Optional[int] = None,
    auto_confirm: bool = True,
    quiet: bool = False
) -> Tuple[bool, Dict]:
    """
    检查任务token预算，超阈值时可交互确认
    
    返回: (是否继续执行, 估算详情dict)
    """
    # 确定阈值和模型
    if threshold is None:
        threshold = DEFAULT_THRESHOLDS.get(task, DEFAULT_THRESHOLDS["默认"])
    if model is None:
        model = DEFAULT_MODELS.get(task, DEFAULT_MODELS["默认"])
    
    # 构建命令
    cmd = [sys.executable, str(BUDGET_SCRIPT), "--task", task, "--model", model, "--threshold", str(threshold)]
    
    if files:
        cmd.extend(["--files"] + files)
    if directory:
        cmd.extend(["--dir", directory])
    if reasoning:
        cmd.append("--reasoning")
    if auto_confirm:
        cmd.append("--confirm")
    
    # 总是用JSON输出方便解析
    cmd.append("--json")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=60
        )
        
        # 尝试解析JSON输出
        try:
            estimate = json.loads(result.stdout)
        except json.JSONDecodeError:
            # 解析失败，从stdout提取关键信息
            estimate = {
                "total_tokens": 0,
                "exceeded": False,
                "raw_output": result.stdout
            }
        
        # 判断是否超阈值
        exceeded = estimate.get("exceeded", False)
        total = estimate.get("total_tokens", 0)
        
        if not quiet:
            cost = estimate.get("cost", {})
            print(f"\n💰 Token预算 [{task}]")
            print(f"   输入: {estimate.get('input_tokens', 0):,} | "
                  f"输出: {estimate.get('output_tokens', 0):,} | "
                  f"总计: {total:,}")
            print(f"   预估费用: ¥{cost.get('total_cost', 0):.4f} ({model})")
            
            if exceeded:
                print(f"   ⚠️  超过阈值 {threshold:,} token")
            else:
                print(f"   ✅ 在预算范围内")
        
        # 返回码0=通过，2=超阈值但确认继续，1=取消
        if result.returncode == 0:
            return True, estimate
        elif result.returncode == 2:
            # 超阈值但用户确认
            return True, estimate
        else:
            # 用户取消或出错
            if not quiet:
                print("   ❌ 任务已取消")
            return False, estimate
            
    except subprocess.TimeoutExpired:
        if not quiet:
            print("⚠️ 预算检查超时，继续执行任务")
        return True, {"timeout": True}
    except Exception as e:
        if not quiet:
            print(f"⚠️ 预算检查出错: {e}，继续执行任务")
        return True, {"error": str(e)}


def quick_estimate(text_or_file: str, task: str = "默认") -> int:
    """快速估算单个文本或文件的token数，返回整数"""
    if os.path.exists(text_or_file):
        # 文件
        cmd = [sys.executable, str(BUDGET_SCRIPT), "--files", text_or_file, "--task", task, "--json"]
    else:
        # 纯文本（写入临时文件）
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(text_or_file)
            tmp = f.name
        cmd = [sys.executable, str(BUDGET_SCRIPT), "--files", tmp, "--task", task, "--json"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=30)
        data = json.loads(result.stdout)
        if os.path.exists(tmp):
            os.unlink(tmp)
        return data.get("input_tokens", 0)
    except:
        # 出错时按字数回退估算
        text = text_or_file if not os.path.exists(text_or_file) else ""
        cn_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        return int(len(text) * 1.3) if cn_chars / max(len(text), 1) > 0.5 else int(len(text.split()) * 1.3)


def batch_check(items: List[dict]) -> List[Tuple[bool, Dict]]:
    """
    批量检查多个任务的预算
    items: [{"files": [...], "task": "...", "threshold": 50000}, ...]
    返回: [(是否继续, 估算详情), ...]
    """
    results = []
    for item in items:
        ok, est = check_budget(
            files=item.get("files"),
            directory=item.get("directory"),
            task=item.get("task", "默认"),
            reasoning=item.get("reasoning", False),
            model=item.get("model"),
            threshold=item.get("threshold"),
            auto_confirm=item.get("auto_confirm", True),
            quiet=item.get("quiet", False)
        )
        results.append((ok, est))
    return results


# --- 预置常用工作流 ---

def before_ocr(files: List[str], auto_confirm: bool = True) -> bool:
    """OCR任务前预算检查"""
    ok, _ = check_budget(
        files=files,
        task="ocr",
        threshold=DEFAULT_THRESHOLDS["ocr"],
        auto_confirm=auto_confirm
    )
    return ok


def before_embedding(directory: str, auto_confirm: bool = True) -> bool:
    """RAG embedding前预算检查"""
    ok, _ = check_budget(
        directory=directory,
        task="embedding",
        threshold=DEFAULT_THRESHOLDS["embedding"],
        auto_confirm=auto_confirm
    )
    return ok


def before_report(files: List[str], reasoning: bool = True, auto_confirm: bool = True) -> bool:
    """生成报告前预算检查"""
    ok, _ = check_budget(
        files=files,
        task="生成报告",
        reasoning=reasoning,
        threshold=DEFAULT_THRESHOLDS["生成报告"],
        auto_confirm=auto_confirm
    )
    return ok


def before_analysis(files: List[str], reasoning: bool = True, auto_confirm: bool = True) -> bool:
    """数据分析前预算检查"""
    ok, _ = check_budget(
        files=files,
        task="分析",
        reasoning=reasoning,
        threshold=DEFAULT_THRESHOLDS["分析"],
        auto_confirm=auto_confirm
    )
    return ok


if __name__ == '__main__':
    # 演示
    print("=" * 50)
    print("工作流预算检查演示")
    print("=" * 50)
    
    # 示例1: OCR检查
    print("\n📄 示例1: OCR任务")
    ok, est = check_budget(
        files=["README.md"],
        task="ocr",
        auto_confirm=False,
        quiet=False
    )
    print(f"结果: {'通过' if ok else '未通过'}")
    
    # 示例2: 报告生成
    print("\n📊 示例2: 报告生成")
    ok, est = check_budget(
        files=["SOUL.md", "USER.md"],
        task="生成报告",
        reasoning=True,
        auto_confirm=False,
        quiet=False
    )
    print(f"结果: {'通过' if ok else '未通过'}")
