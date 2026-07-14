#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型路由配置 (Model Routing Config) v1.0
========================================
将 TOOLS.md 中的路由规则转化为可执行的JSON配置，
供 engine.py / api_guard.py 读取和自动决策。

错误代价六级：
  ~0  → flash
  低  → qwen3.7-plus
  💡  → fable-5 (咨询层)
  中  → v4-pro
  高  → sonnet-5 + gpt-5.5
  致命 → opus-4-8 终审
"""
import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'model_routing.json')

DEFAULT_ROUTING = {
    "version": "1.0",
    "error_cost_levels": {
        "free": {
            "label": "~0 代价",
            "desc": "错了重来",
            "models": ["deepseek-v4-flash"],
            "fallback": ["deepseek-v4-pro"]
        },
        "low": {
            "label": "低代价",
            "desc": "改两行就行",
            "models": ["qwen3.7-plus"],
            "fallback": ["deepseek-v4-flash", "deepseek-v4-pro"]
        },
        "consult": {
            "label": "咨询层",
            "desc": "方向选错 — 独立顾问给建议，不做执行",
            "models": ["claude-fable-5"],
            "fallback": ["claude-sonnet-5"]
        },
        "medium": {
            "label": "中代价",
            "desc": "重跑一遍",
            "models": ["deepseek-v4-pro"],
            "fallback": ["claude-sonnet-5", "deepseek-v4-flash"]
        },
        "high": {
            "label": "高代价",
            "desc": "改半天",
            "models": ["claude-sonnet-5", "gpt-5.5"],
            "fallback": ["gpt-5.6-sol", "claude-opus-4-8"]
        },
        "fatal": {
            "label": "致命代价",
            "desc": "吊销执照",
            "models": ["claude-sonnet-5", "gpt-5.5", "claude-opus-4-8"],
            "fallback": ["gpt-5.6-terra"]
        }
    },
    "task_routes": {
        "read_general": {
            "label": "读·普通文档/代码/日志",
            "cost_level": "free",
            "upgrade_if": "涉及关键证据 → low",
            "upgrade_to": "low"
        },
        "read_image": {
            "label": "读·图片/扫描件",
            "cost_level": "low",
            "upgrade_if": "涉及关键证据 → high",
            "upgrade_to": "high"
        },
        "read_contract": {
            "label": "读·合同/法规/政策",
            "cost_level": "high",
            "upgrade_if": "重大条款纠纷 → fatal",
            "upgrade_to": "fatal"
        },
        "do_data": {
            "label": "做·数据整理/脚本",
            "cost_level": "free",
            "upgrade_if": "结果将用于正式报告 → medium",
            "upgrade_to": "medium"
        },
        "do_report_draft": {
            "label": "做·报告初稿/公文",
            "cost_level": "low",
            "upgrade_if": "正式交付客户 → high",
            "upgrade_to": "high"
        },
        "do_bid_final": {
            "label": "做·标书最终版",
            "cost_level": "low",
            "upgrade_if": "废标=丢项目 → high双签",
            "upgrade_to": "high",
            "dual_sign": True
        },
        "do_audit_report": {
            "label": "做·审计报告正式出具",
            "cost_level": "low",
            "upgrade_if": "签字责任 → fatal终审",
            "upgrade_to": "fatal"
        },
        "do_cover": {
            "label": "做·封面/配图",
            "cost_level": "free",
            "models_override": ["gpt-image-2"],
            "upgrade_if": "品牌形象要求 → high视觉建议",
            "upgrade_to": "high"
        },
        "think_explore": {
            "label": "想·探索性分析",
            "cost_level": "free",
            "upgrade_if": "方向不确定 → consult",
            "upgrade_to": "consult"
        },
        "think_audit": {
            "label": "想·审计分析/数据核查",
            "cost_level": "medium",
            "upgrade_if": "出定性结论 → high交叉验证",
            "upgrade_to": "high"
        },
        "think_bid_rigging": {
            "label": "想·串标围标分析",
            "cost_level": "medium",
            "upgrade_if": "出具正式结论 → high+终审",
            "upgrade_to": "fatal"
        },
        "think_compliance": {
            "label": "想·风险判断/合规研判",
            "cost_level": "high",
            "upgrade_if": "影响行政处罚 → fatal",
            "upgrade_to": "fatal"
        },
        "think_plan_compare": {
            "label": "想·方案对比/路线选择",
            "cost_level": "consult",
            "upgrade_if": "分歧大 → high判断",
            "upgrade_to": "high"
        },
        "think_architecture": {
            "label": "想·架构设计/工具选型",
            "cost_level": "consult",
            "upgrade_if": "分歧大 → high",
            "upgrade_to": "high"
        },
        "review_typo": {
            "label": "审·中文错别字/格式",
            "cost_level": "low",
            "models_override": ["qwen3.7-plus"]
        },
        "review_amount": {
            "label": "审·金额追踪/数据核验",
            "cost_level": "medium"
        },
        "review_detail": {
            "label": "审·细节/合规/逻辑",
            "cost_level": "high"
        },
        "review_expression": {
            "label": "审·表达/可读性",
            "cost_level": "high",
            "models_override": ["gpt-5.5", "gpt-5.6-luna"]
        },
        "review_final": {
            "label": "审·关键结论验收",
            "cost_level": "high",
            "upgrade_if": "审计报告级别 → fatal",
            "upgrade_to": "fatal"
        },
        "review_signoff": {
            "label": "审·重大定稿终审",
            "cost_level": "fatal"
        }
    },
    "default_chain": {
        "primary": "deepseek-v4-flash",
        "fallbacks": ["deepseek-v4-pro", "claude-sonnet-5"]
    },
    "heartbeat_override": {
        "model": "deepseek-v4-flash",
        "reason": "心跳任务必须用免费模型节省成本"
    },
    "cost_control": {
        "flash_plus_qwen_pct": 80,
        "pro_plus_fable_pct": 15,
        "sonnet_plus_gpt_pct": 5,
        "opus_per_project_max": 3
    }
}

def get_routing_config():
    """加载路由配置"""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return DEFAULT_ROUTING.copy()

def save_routing_config(config):
    """保存路由配置"""
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f"[OK] 路由配置已保存: {CONFIG_PATH}")

def resolve_model(task_type, error_cost_unknown=False):
    """
    根据任务类型和错误代价不确定性，返回推荐的模型。
    
    Args:
        task_type: str - 任务类型ID（对应task_routes的key）
        error_cost_unknown: bool - 错误代价不确定？是则向上一级
    
    Returns:
        dict: {"primary": str, "fallbacks": list, "dual_sign": bool, "level": str}
    """
    config = get_routing_config()
    routes = config.get("task_routes", {})
    
    if task_type not in routes:
        return {"primary": config["default_chain"]["primary"],
                "fallbacks": config["default_chain"]["fallbacks"],
                "dual_sign": False, "level": "free"}
    
    route = routes[task_type]
    cost_level = route.get("cost_level", "free")
    
    # 如果错误代价不确定，向上一级
    if error_cost_unknown:
        level_order = ["free", "low", "consult", "medium", "high", "fatal"]
        current_idx = level_order.index(cost_level)
        cost_level = level_order[min(current_idx + 1, len(level_order) - 1)]
    
    level_config = config["error_cost_levels"].get(cost_level, {})
    models = route.get("models_override", level_config.get("models", []))
    fallbacks = level_config.get("fallback", config["default_chain"]["fallbacks"])
    
    return {
        "primary": models[0] if models else config["default_chain"]["primary"],
        "fallbacks": fallbacks,
        "dual_sign": route.get("dual_sign", False),
        "level": cost_level,
    }

def show_routing_table():
    """展示路由表"""
    config = get_routing_config()
    print(f"\n{'='*70}")
    print(f"  模型路由配置 v{config['version']}")
    print(f"{'='*70}")
    print(f"\n{'任务类型':<28s} {'级别':<8s} {'模型':<28s} {'升级路径':<20s}")
    print(f"{'-'*28} {'-'*8} {'-'*28} {'-'*20}")
    for tid, route in config["task_routes"].items():
        cost = route.get("cost_level", "?")
        models = route.get("models_override", 
                          config["error_cost_levels"].get(cost, {}).get("models", ["?"]))
        upgrade = route.get("upgrade_if", "-")
        print(f"  {tid:<26s} {cost:<8s} {models[0]:<28s} {upgrade[:18]:<20s}")
    print(f"\n默认链路: {config['default_chain']['primary']} → {', '.join(config['default_chain']['fallbacks'][:2])}")
    print(f"{'='*70}\n")

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'save':
        save_routing_config(DEFAULT_ROUTING)
    elif len(sys.argv) > 1 and sys.argv[1] == 'resolve':
        task = sys.argv[2] if len(sys.argv) > 2 else 'read_general'
        unknown = '--unknown' in sys.argv
        result = resolve_model(task, unknown)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        show_routing_table()