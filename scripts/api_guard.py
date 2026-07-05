#!/usr/bin/env python3
"""
OpenClaw API 调用包装器 (带限流 + 熔断)
=======================================
拦截所有 DeepSeek API 调用，自动应用费用守卫规则。

用法：替换原有的 API 调用处
  from api_guard import guarded_chat_completion
  
  response = guarded_chat_completion(
      model="deepseek-v4-flash",
      messages=[...],
      timeout=60
  )

如果触发熔断，会抛出 CircuitBreakerError，调用方需捕获处理。
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 导入费用守卫
sys.path.insert(0, str(Path(__file__).parent))
from deepseek_cost_guard import check_circuit_breaker, load_config, load_guard_state, save_guard_state, send_alert

TZ = timezone(timedelta(hours=8))

class CircuitBreakerError(Exception):
    """熔断异常"""
    pass

class DailyLimitError(Exception):
    """日限额异常"""
    pass

def _count_call(model: str):
    """记录一次API调用"""
    cfg = load_config()
    state = load_guard_state()
    today = datetime.now(TZ).strftime("%Y-%m-%d")
    
    if state.get("date") != today:
        state = {"date": today, "flash_calls": 0, "v4pro_calls": 0}
    
    model_key = "flash_calls" if "flash" in model.lower() else "v4pro_calls"
    state[model_key] = state.get(model_key, 0) + 1
    save_guard_state(state)
    
    # 检查是否超限
    max_calls = cfg["max_flash_requests_per_day"] if "flash" in model.lower() else cfg["max_v4pro_requests_per_day"]
    if state[model_key] > max_calls:
        raise DailyLimitError(f"{model} 日调用超限: {state[model_key]}/{max_calls}")

def guarded_chat_completion(model="deepseek-v4-flash", messages=None, **kwargs):
    """
    带保护的 chat completion 调用
    
    参数: 同 OpenAI API
    返回: 标准 response 对象
    异常: CircuitBreakerError | DailyLimitError
    """
    if messages is None:
        messages = []
    
    # 1. 检查熔断
    tripped, msg = check_circuit_breaker()
    if tripped:
        send_alert("CRITICAL", f"API调用被熔断", {"model": model, "action": "blocked"})
        raise CircuitBreakerError(msg)
    
    # 2. 计数
    _count_call(model)
    
    # 3. 实际调用 (这里假设使用 openai 库)
    try:
        import openai
        # 从环境变量读取 key
        client = openai.OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs
        )
        
        # 记录用量
        usage = response.usage
        if usage:
            prompt_tokens = usage.prompt_tokens
            completion_tokens = usage.completion_tokens
            # 简单估算费用 (仅console记录)
            print(f"[API Guard] {model}: +{prompt_tokens} prompt + {completion_tokens} completion tokens")
        
        return response
        
    except Exception as e:
        # 调用失败也要记录
        print(f"[API Guard] 调用失败: {e}")
        raise

# ── 批量处理安全包装 ──

def batch_process(items, processor, model="deepseek-v4-flash", batch_size=10, delay_sec=1):
    """
    安全的批量处理器
    
    参数:
        items: 待处理列表
        processor: 处理函数(item) -> result
        model: 使用的模型
        batch_size: 每批处理数量
        delay_sec: 批次间延迟(秒)
    
    返回: results列表
    """
    import time
    
    results = []
    total = len(items)
    
    print(f"[Batch Guard] 开始批量处理: {total} 项, 批次大小: {batch_size}, 模型: {model}")
    
    for i in range(0, total, batch_size):
        batch = items[i:i+batch_size]
        
        # 每批前检查熔断
        tripped, msg = check_circuit_breaker()
        if tripped:
            print(f"[Batch Guard] ⚠️ 批量处理被熔断！已完成 {len(results)}/{total}")
            send_alert("CRITICAL", f"批量处理熔断中断", {"completed": len(results), "total": total})
            break
        
        # 处理本批
        for item in batch:
            try:
                result = processor(item)
                results.append(result)
            except (CircuitBreakerError, DailyLimitError) as e:
                print(f"[Batch Guard] 达到限额，停止处理: {e}")
                return results
            except Exception as e:
                print(f"[Batch Guard] 单项处理失败: {e}")
                results.append(None)
        
        # 批次延迟
        if i + batch_size < total:
            time.sleep(delay_sec)
        
        # 进度
        progress = min(i + batch_size, total)
        if progress % 50 == 0 or progress == total:
            print(f"[Batch Guard] 进度: {progress}/{total} ({progress/total*100:.0f}%)")
    
    print(f"[Batch Guard] 批量处理完成: {len(results)}/{total}")
    return results

if __name__ == "__main__":
    print("=== API Guard 测试 ===")
    
    # 测试熔断检查
    tripped, msg = check_circuit_breaker()
    print(f"熔断状态: {tripped}, {msg}")
    
    # 测试计数
    _count_call("deepseek-v4-flash")
    state = load_guard_state()
    print(f"Flash 调用计数: {state.get('flash_calls', 0)}")
