"""
P2: context_window_monitor — 上下文窗口预警 + 断点续传助手 (v8, 2d)

功能：
1. 跟踪当前会话的token消耗（预估）
2. 在达到80%窗口上限时触发预警
3. 自动生成Checkpoint摘要，可作为新会话的初始化上下文
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import os


# ── 模型上下文窗口定义 ──────────────────────────────────────

MODEL_CONTEXT_WINDOWS = {
    "deepseek-v4-pro": 128_000,
    "deepseek-v4-flash": 128_000,
    "qwen-max": 32_000,
    "kimi": 128_000,
    "glm-4": 128_000,
    "default": 64_000,
}

# 预警阈值
WARNING_THRESHOLD = 0.80   # 80% → 发出预警
CRITICAL_THRESHOLD = 0.95  # 95% → 强制建议刷新


@dataclass
class WindowStatus:
    """上下文窗口状态"""
    model: str
    max_tokens: int
    estimated_used: int
    usage_pct: float
    status: str  # ok | warning | critical
    recommendation: str


@dataclass
class CheckpointSummary:
    """断点续传摘要"""
    project_name: str
    project_type: str
    current_step: str
    completed_tools: List[str]
    findings_count: int
    high_risk_count: int
    pending_actions: List[str]
    key_context: str  # 精简的上下文描述
    timestamp: str = ""
    estimated_restart_tokens: int = 0


class ContextWindowMonitor:
    """上下文窗口监控器"""

    def __init__(self, model: str = "default"):
        self.model = model
        self.max_tokens = MODEL_CONTEXT_WINDOWS.get(model, MODEL_CONTEXT_WINDOWS["default"])
        self._estimated_tokens = 0
        self._base_tokens = 0  # 基础提示词消耗

    def set_base_tokens(self, base_system_prompt_length: int):
        """设置基础提示词token数（系统提示+工具定义等固定开销）"""
        # 粗略估算：1个中文字符≈1.5 tokens，1个英文字符≈0.3 tokens
        self._base_tokens = int(base_system_prompt_length * 0.3)
        self._estimated_tokens = self._base_tokens

    def add_message(self, text: str, role: str = "user"):
        """添加消息，估算token消耗"""
        # 字符→token粗略估算
        if any('\u4e00' <= c <= '\u9fff' for c in text):
            # 中文为主：每字符≈1.5 tokens
            new_tokens = int(len(text) * 1.5)
        else:
            # 英文为主：每字符≈0.3 tokens
            new_tokens = int(len(text) * 0.3)
        self._estimated_tokens += new_tokens

    def add_tool_result(self, output_text: str):
        """添加工具调用结果"""
        new_tokens = int(len(output_text) * 0.1)  # JSON结构，token效率高
        self._estimated_tokens += new_tokens

    def check(self) -> WindowStatus:
        """检查窗口状态"""
        pct = self.usage_pct

        if pct >= CRITICAL_THRESHOLD:
            status = "critical"
            recommendation = (
                f"🔴 上下文窗口已达{pct:.0%}（{self._estimated_tokens:,}/{self.max_tokens:,} tokens）。"
                f"强烈建议立即保存当前进度并开启新会话。"
            )
        elif pct >= WARNING_THRESHOLD:
            status = "warning"
            recommendation = (
                f"⚠️ 上下文窗口已达{pct:.0%}（{self._estimated_tokens:,}/{self.max_tokens:,} tokens）。"
                f"建议在当前分析批次完成后开启新会话。"
            )
        else:
            status = "ok"
            recommendation = (
                f"✅ 上下文窗口使用正常（{pct:.0%}），"
                f"剩余约{self.remaining_tokens:,} tokens可用。"
            )

        return WindowStatus(
            model=self.model,
            max_tokens=self.max_tokens,
            estimated_used=self._estimated_tokens,
            usage_pct=round(pct, 3),
            status=status,
            recommendation=recommendation,
        )

    @property
    def usage_pct(self) -> float:
        return self._estimated_tokens / self.max_tokens

    @property
    def remaining_tokens(self) -> int:
        return max(0, self.max_tokens - self._estimated_tokens)

    def generate_checkpoint(
        self,
        project_name: str,
        project_type: str,
        current_step: str,
        completed_tools: List[str],
        findings_count: int,
        high_risk_count: int,
        pending_actions: List[str],
        key_context: str,
    ) -> CheckpointSummary:
        """生成断点续传摘要"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        checkpoint = CheckpointSummary(
            project_name=project_name,
            project_type=project_type,
            current_step=current_step,
            completed_tools=completed_tools,
            findings_count=findings_count,
            high_risk_count=high_risk_count,
            pending_actions=pending_actions,
            key_context=key_context,
            timestamp=timestamp,
            estimated_restart_tokens=self._estimate_restart_tokens(),
        )

        return checkpoint

    def _estimate_restart_tokens(self) -> int:
        """估算重启后需要的token数"""
        # 基础提示词 + checkpoint摘要 + 精简上下文 ≈ 20-30%窗口
        return int(self.max_tokens * 0.20)

    def checkpoint_to_prompt(self, checkpoint: CheckpointSummary) -> str:
        """将Checkpoint转换为新会话的初始化Prompt"""
        return f"""## 断点续传上下文（从上次会话继承）

**项目**：{checkpoint.project_name}
**审计类型**：{checkpoint.project_type}
**上次进度**：已完成{checkpoint.current_step}步骤
**已执行工具**：{', '.join(checkpoint.completed_tools)}
**已发现疑点**：{checkpoint.findings_count}条（高危{checkpoint.high_risk_count}条）
**断点时间**：{checkpoint.timestamp}

**关键上下文**：
{checkpoint.key_context[:500]}

**待处理事项**：
{chr(10).join(f'- {a}' for a in checkpoint.pending_actions)}

**续传指令**：
请从上一次会话的断点继续，优先处理上述待处理事项。
"""


def check_context_window(
    model: str,
    estimated_tokens: int,
    base_tokens: int = 0,
) -> dict:
    """快速检查上下文窗口（MCP工具接口）"""
    monitor = ContextWindowMonitor(model=model)
    monitor._estimated_tokens = estimated_tokens + base_tokens
    status = monitor.check()
    return {
        "model": status.model,
        "max_tokens": status.max_tokens,
        "estimated_used": status.estimated_used,
        "usage_pct": f"{status.usage_pct:.0%}",
        "remaining": f"{monitor.remaining_tokens:,}",
        "status": status.status,
        "recommendation": status.recommendation,
    }


def generate_resume_checkpoint(
    project_name: str,
    project_type: str,
    current_step: str,
    completed_tools: List[str],
    findings_count: int,
    high_risk_count: int,
    key_context: str,
    pending_actions: Optional[List[str]] = None,
    model: str = "default",
) -> dict:
    """生成断点续传摘要（MCP工具接口）"""
    monitor = ContextWindowMonitor(model=model)
    checkpoint = monitor.generate_checkpoint(
        project_name=project_name,
        project_type=project_type,
        current_step=current_step,
        completed_tools=completed_tools,
        findings_count=findings_count,
        high_risk_count=high_risk_count,
        pending_actions=pending_actions or [],
        key_context=key_context,
    )
    return {
        "checkpoint": monitor.checkpoint_to_prompt(checkpoint),
        "restart_tokens_estimate": checkpoint.estimated_restart_tokens,
        "timestamp": checkpoint.timestamp,
        "save_instruction": "将上方'断点续传上下文'复制到新会话的初始消息中即可恢复工作。",
    }
