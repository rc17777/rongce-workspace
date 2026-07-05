#!/usr/bin/env python3
"""
OpenClaw Spawn 安全包装器
=========================
强制所有 spawn 调用带超时，防止子代理空转。

用法:
  from spawn_guard import safe_spawn
  
  result = safe_spawn(
      task="分析PDF",
      model="deepseek-v4-flash",
      timeout=300,  # 5分钟
      cleanup="delete"
  )

如果调用方没传 timeout，自动使用默认值。
"""

import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 默认超时配置（秒）
DEFAULT_TIMEOUTS = {
    "ocr_batch": 600,        # OCR批量: 10分钟
    "data_processing": 300,  # 数据处理: 5分钟
    "analysis": 300,         # 分析任务: 5分钟
    "query": 180,            # 查询任务: 3分钟
    "default": 300,          # 默认: 5分钟
}

# 绝对上限（任何任务不能超过）
HARD_TIMEOUT_CAP = 1800  # 30分钟

def safe_spawn(**kwargs):
    """
    安全的 spawn 包装器
    
    强制规则:
    1. 必须有 runTimeoutSeconds
    2. 不能超过 HARD_TIMEOUT_CAP
    3. 一次性任务必须 cleanup="delete"
    4. 打印 spawn 日志到控制台
    
    返回: spawn 结果
    """
    
    # 1. 处理超时
    timeout = kwargs.get("runTimeoutSeconds")
    if timeout is None:
        # 根据 task 内容推断类型
        task = kwargs.get("task", "").lower()
        if any(k in task for k in ["ocr", "扫描", "识别"]):
            timeout = DEFAULT_TIMEOUTS["ocr_batch"]
        elif any(k in task for k in ["数据", "处理", "批量"]):
            timeout = DEFAULT_TIMEOUTS["data_processing"]
        elif any(k in task for k in ["分析", "审计", "报告"]):
            timeout = DEFAULT_TIMEOUTS["analysis"]
        elif any(k in task for k in ["查询", "搜索", "查"]):
            timeout = DEFAULT_TIMEOUTS["query"]
        else:
            timeout = DEFAULT_TIMEOUTS["default"]
        
        kwargs["runTimeoutSeconds"] = timeout
        print(f"[Spawn Guard] 自动设置超时: {timeout}秒 (任务: {task[:50]}...)")
    
    # 2. 硬上限检查
    if timeout > HARD_TIMEOUT_CAP:
        print(f"[Spawn Guard] ⚠️ 超时 {timeout}秒 超过硬上限 {HARD_TIMEOUT_CAP}秒，已截断")
        kwargs["runTimeoutSeconds"] = HARD_TIMEOUT_CAP
        timeout = HARD_TIMEOUT_CAP
    
    # 3. 一次性任务 cleanup
    mode = kwargs.get("mode", "run")
    cleanup = kwargs.get("cleanup")
    if mode == "run" and cleanup != "delete":
        kwargs["cleanup"] = "delete"
        print(f"[Spawn Guard] 已设置 cleanup='delete' (一次性任务)")
    
    # 4. 打印 spawn 信息
    model = kwargs.get("model", "default")
    task_preview = kwargs.get("task", "")[:60]
    print(f"[Spawn Guard] 启动子代理")
    print(f"  模型: {model}")
    print(f"  超时: {timeout}秒 ({timeout//60}分{timeout%60}秒)")
    print(f"  任务: {task_preview}...")
    
    # 5. 实际 spawn (这里只是包装，实际调用由 OpenClaw 处理)
    # 注意：这个函数本身不能真正执行 spawn，它只是验证参数
    # 真正的 spawn 还是要通过 sessions_spawn 工具执行
    
    return kwargs  # 返回处理后的参数，供调用方使用

def validate_spawn_params(kwargs: dict) -> tuple[bool, str]:
    """
    验证 spawn 参数是否安全
    
    返回: (是否安全, 错误信息)
    """
    errors = []
    
    if "runTimeoutSeconds" not in kwargs:
        errors.append("缺少 runTimeoutSeconds")
    elif kwargs["runTimeoutSeconds"] > HARD_TIMEOUT_CAP:
        errors.append(f"runTimeoutSeconds {kwargs['runTimeoutSeconds']} 超过硬上限 {HARD_TIMEOUT_CAP}")
    
    if kwargs.get("mode") == "run" and kwargs.get("cleanup") != "delete":
        errors.append("一次性任务应设置 cleanup='delete'")
    
    if not errors:
        return True, "OK"
    
    return False, "; ".join(errors)

if __name__ == "__main__":
    print("=== Spawn Guard 测试 ===")
    
    # 测试1: 缺少超时
    params = safe_spawn(task="分析PDF文件", model="deepseek-v4-flash")
    print(f"测试1 - 自动超时: {params.get('runTimeoutSeconds')}秒")
    
    # 测试2: 超长超时
    params = safe_spawn(task="长时间任务", runTimeoutSeconds=3600)
    print(f"测试2 - 截断超时: {params.get('runTimeoutSeconds')}秒")
    
    # 测试3: 正常参数
    params = safe_spawn(task="查询数据", runTimeoutSeconds=180, cleanup="delete")
    print(f"测试3 - 正常: {params.get('runTimeoutSeconds')}秒, cleanup={params.get('cleanup')}")
    
    # 测试验证
    ok, msg = validate_spawn_params({"task": "test"})
    print(f"测试4 - 验证(无超时): {ok}, {msg}")
    
    ok, msg = validate_spawn_params({"task": "test", "runTimeoutSeconds": 300, "mode": "run", "cleanup": "delete"})
    print(f"测试5 - 验证(正常): {ok}, {msg}")
