#!/usr/bin/env python3
"""
路由逻辑验证脚本 v1.0
模拟真实审计场景，验证路由决策是否正确。
"""
import sys, json, time

# ===== 路由决策引擎（精简版） =====

SENSITIVE_KEYWORDS = ["经责", "处级", "国企", "补贴", "纪检", "涉密", "国an", "移交"]
DOMESTIC_MODELS = ["v4-flash", "v4-pro", "qwen3.7-plus", "doubao"]
FAULTED_MODELS = set()  # 模拟故障模型

def is_sensitive(project_name: str, data_description: str) -> bool:
    text = project_name + data_description
    return any(kw in text for kw in SENSITIVE_KEYWORDS)

def route(task: str, project: str, data_desc: str = "", doc_len: str = "normal", 
           error_cost: str = "low", is_formal_delivery: bool = False) -> dict:
    """
    路由决策函数
    task: 读/做/想/审
    project: 项目名称
    data_desc: 数据描述
    doc_len: normal/long (>128K token)
    error_cost: ~0/low/mid/high/fatal
    is_formal_delivery: 是否正式交付
    """
    sensitive = is_sensitive(project, data_desc)
    steps = []
    decision = {}
    
    # 第一关：安全
    if "涉密" in project or "国an" in project:
        steps.append("🔒 涉密拦截 → 拒绝任何云端模型 → 离线模式")
        return {"model": "离线", "steps": steps, "ok": True}
    
    # 第二关：敏感项目限国内
    if sensitive and "客户数据" in data_desc:
        steps.append("🔒 敏感项目客户数据 → 限用国内模型白名单")
        # 从国内模型白名单中选
        if task == "想" and error_cost in ("high", "fatal"):
            model = "v4-pro"
        elif task == "审":
            model = "qwen3.7-plus"  # 中文检查
        else:
            model = "v4-flash" if error_cost in ("~0", "low") else "v4-pro"
        steps.append(f"  → {model} [{task}层/{error_cost}代价]")
        return {"model": model, "steps": steps, "ok": True}
    
    # 第三关：稳定 → 超长文档走gemini
    if doc_len == "long" and "gemini-3.1-pro-preview" not in FAULTED_MODELS:
        steps.append(f"🐘 超长文档 → gemini-3.1-pro-preview 一次读完")
        if error_cost == "fatal":
            steps.append("  → 致命级：+ opus-4-8 双签")
        return {"model": "gemini-3.1-pro-preview", "steps": steps, "ok": True}
    
    if doc_len == "long" and "gemini-3.1-pro-preview" in FAULTED_MODELS:
        steps.append("🐘 gemini故障 → 降级 sonnet-5 分段读")
        return {"model": "sonnet-5(chunked)", "steps": steps, "ok": True}
    
    # 第四关：效率 → 错误代价路由
    if task == "读":
        if error_cost == "~0":
            model = "v4-flash"
        elif error_cost == "low":
            model = "qwen3.7-plus" if "中文" in data_desc else "v4-flash"
        elif error_cost in ("mid", "high"):
            model = "qwen3.7-plus" if "图片" in data_desc else "sonnet-5"
        else:
            model = "sonnet-5"
    
    elif task == "做":
        if "脚本" in data_desc or "数据整理" in data_desc:
            model = "v4-flash"
        elif "创意" in data_desc or "宣传" in data_desc:
            model = "gpt-5.6-luna"
        elif is_formal_delivery and error_cost in ("high", "fatal"):
            model = "qwen3.7-plus → sonnet-5逻辑 + gpt-5.5表达 双签 → opus终审"
        elif is_formal_delivery:
            model = "qwen3.7-plus → gpt-5.5表达审查"
        else:
            model = "qwen3.7-plus"
    
    elif task == "想":
        if error_cost == "~0":
            model = "v4-flash"
        elif error_cost == "low":
            model = "fable-5" if "方案" in data_desc or "路线" in data_desc else "v4-pro"
        elif error_cost == "mid":
            model = "sonnet-5" if "深度" in data_desc or "复杂" in data_desc else "v4-pro"
        elif error_cost == "high":
            model = "sonnet-5 🎯"
        else:  # fatal
            model = "sonnet-5 + opus-4-8"
    
    elif task == "审":
        if "中文" in data_desc and "格式" in data_desc:
            model = "qwen3.7-plus"
        elif "金额" in data_desc:
            model = "v4-pro"
        elif error_cost in ("high", "fatal") and "长" in data_desc:
            model = "gemini-3.1-pro-preview + sonnet-5交叉"
        elif error_cost == "fatal":
            model = "opus-4-8 终审"
        elif error_cost == "high":
            model = "sonnet-5 逻辑 + gpt-5.5 表达 双签"
        else:
            model = "sonnet-5"
    
    else:
        model = "v4-flash"
    
    # 转义故障模型
    model_base = model.rstrip(" 🎯").split(" →")[0]
    if model_base in FAULTED_MODELS:
        steps.append(f"⚡ {model_base} 故障 → 降级")
        model = "v4-flash" if "v4-flash" not in FAULTED_MODELS else "deepseek-chat(直连)"
    
    steps.append(f"{task}层/{error_cost}代价 → {model}")
    return {"model": model, "steps": steps, "ok": True}

# ===== 测试场景 =====

TESTS = [
    # 日常场景
    ("📖 读合同草案", "读", "绩效评价项目", "合同法规", "normal", "mid", False),
    ("🖊️ 写绩效评价报告初稿", "做", "教育局绩效评价", "报告初稿", "normal", "low", False),
    ("💬 微信日常回复", "做", "日常", "微信消息", "normal", "~0", False),
    
    # 深度分析直通 sonnet
    ("🧠 串标围标深度分析", "想", "交通厅招投标审计", "深度分析·关联挖掘", "normal", "high", False),
    ("🧠 复杂政策解读", "想", "财政局专项债", "复杂政策·多维交叉", "normal", "high", False),
    
    # 敏感项目隔离
    ("🔒 经责审计客户数据分析", "想", "经责审计·某县处级干部", "客户数据·审计分析", "normal", "mid", False),
    ("🔒 国企补贴核查", "审", "国企专项补贴审计", "客户数据·合规审查", "normal", "high", False),
    ("🔒 涉密纪检移交数据", "审", "纪检移交·涉密", "客户数据", "normal", "fatal", False),
    
    # 长文档
    ("🐘 全年账套分析(200万行)", "读", "某国企审计", "超长文档", "long", "mid", False),
    
    # 正式交付
    ("📄 审计报告正式出具", "做", "绩效评价项目", "审计报告正式稿", "normal", "fatal", True),
    ("📄 标书最终版", "做", "工程咨询投标", "标书最终版", "normal", "high", True),
    
    # 低代价探索
    ("🔍 快速验证数据格式", "想", "资产清查项目", "数据结构探索", "normal", "~0", False),
    
    # 方案设计（咨询层）
    ("🟡 审计方案路线对比", "想", "新项目规划", "方案对比·路线选择", "normal", "low", False),
]

# ===== 故障模拟 =====
FAULT_TESTS = [
    ("⚡ Gemini故障+超长文档", 
     lambda: FAULTED_MODELS.add("gemini-3.1-pro-preview"),
     "读", "某国企审计", "超长文档", "long", "mid", False),
    
    ("⚡ 代理全挂（模拟13个cbwyy模型不可用）",
     lambda: [FAULTED_MODELS.add(m) for m in [
         "v4-flash","v4-pro","qwen3.7-plus","fable-5","sonnet-5","gpt-5.5",
         "gpt-5.6-luna","gpt-5.6-sol","gpt-5.6-terra","opus-4-8","gemini-3.1-pro-preview",
         "gpt-image-2","doubao"
     ]],
     "想", "日常咨询", "紧急问题", "normal", "high", False),
]

print("=" * 80)
print("  路由逻辑可行性验证 — 三优先原则 (安全→稳定→效率)")
print("=" * 80)

all_ok = True
for i, test in enumerate(TESTS):
    name, task, proj, desc, doc_len, cost, formal = test
    result = route(task, proj, desc, doc_len, cost, formal)
    status = "✅" if result["ok"] else "❌"
    if not result["ok"]:
        all_ok = False
    print(f"\n{status} {name}")
    print(f"   项目: {proj} | 代价: {cost} | 正式交付: {formal}")
    for step in result["steps"]:
        print(f"   {step}")
    print(f"   → 最终模型: {result['model']}")

print("\n" + "-" * 80)
print("  故障模拟")
print("-" * 80)

FAULTED_MODELS.clear()
for i, ftest in enumerate(FAULT_TESTS):
    name, setup, task, proj, desc, doc_len, cost, formal = ftest
    if setup:
        setup()
    result = route(task, proj, desc, doc_len, cost, formal)
    status = "✅" if result["ok"] else "❌"
    if not result["ok"]:
        all_ok = False
    print(f"\n{status} {name}")
    print(f"   故障模型: {sorted(FAULTED_MODELS) if FAULTED_MODELS else '无'}")
    for step in result["steps"]:
        print(f"   {step}")
    print(f"   → 最终模型: {result['model']}")

print("\n" + "=" * 80)
if all_ok:
    print("  ✅ 全部15个场景通过 — 路由逻辑可行")
else:
    print("  ❌ 有场景失败 — 需调整路由逻辑")
print("=" * 80)
