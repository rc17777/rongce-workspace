# -*- coding: utf-8 -*-
"""
审盾闭环层 - 质控管道 v1.0
============================
复核意见生成后，自动流转到质控系统。

工作流：
  1. 报告提交 → 复核管道运行
  2. 每条发现带推理链 → 进入质控队列
  3. 质控人员 CLI 审核 → 确认/驳回/修改
  4. 已确认发现 → 归档到知识库
  5. 已驳回发现 → 标记误报，反向优化规则

数据位置：
  output/qc_pipelines/       ← 管道JSON
  output/qc_pipelines/queue/ ← 待审核队列
  output/qc_pipelines/archive/ ← 已归档
"""

import sys, json, time, hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from .schema import (
    ReviewFinding, QCPipeline, QCStatus, ReasoningStep, ReasoningStepType, TZ
)

# 默认路径
ROOT = Path(__file__).resolve().parent.parent.parent
QC_DIR = ROOT / 'output' / 'qc_pipelines'
QUEUE_DIR = QC_DIR / 'queue'
ARCHIVE_DIR = QC_DIR / 'archive'
REPORT_DIR = QC_DIR / 'reports'


def ensure_dirs():
    for d in [QC_DIR, QUEUE_DIR, ARCHIVE_DIR, REPORT_DIR]:
        d.mkdir(parents=True, exist_ok=True)


# ============================================================
# 队列管理
# ============================================================

def submit_to_qc(pipeline: QCPipeline) -> str:
    """提交管道到质控队列"""
    ensure_dirs()
    
    # 保存完整管道
    pipeline.status = QCStatus.PENDING
    data = pipeline.to_dict()
    
    filepath = QUEUE_DIR / f"{pipeline.pipeline_id}.json"
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 同时保存推理链Markdown到报告目录
    from .reasoning_trail import pipeline_to_markdown
    md_path = REPORT_DIR / f"{pipeline.pipeline_id}_推理链.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(pipeline_to_markdown(pipeline))
    
    return str(filepath)


def list_queue(status_filter: Optional[str] = None) -> List[Dict]:
    """列出质控队列"""
    ensure_dirs()
    items = []
    for fp in sorted(QUEUE_DIR.glob('*.json')):
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            continue
        if status_filter and data.get('status') != status_filter:
            continue
        items.append(data)
    return items


def get_pipeline(pipeline_id: str) -> Optional[QCPipeline]:
    """获取管道（从队列和归档中查找）"""
    for d in [QUEUE_DIR, ARCHIVE_DIR]:
        fp = d / f"{pipeline_id}.json"
        if fp.exists():
            with open(fp, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return _dict_to_pipeline(data)
    return None


def _dict_to_pipeline(data: Dict) -> QCPipeline:
    """将字典转回QCPipeline对象"""
    pipeline = QCPipeline(
        report_name=data.get('report_name', ''),
        pipeline_id=data.get('pipeline_id', '')
    )
    pipeline.status = QCStatus(data.get('status', '待审核'))
    pipeline.created_at = data.get('created_at', '')
    pipeline.updated_at = data.get('updated_at', '')
    pipeline.completed_at = data.get('completed_at')
    pipeline.report_path = data.get('report_path')
    pipeline.raw_report_path = data.get('raw_report_path')
    pipeline.metadata = data.get('metadata', {})
    
    for f_data in data.get('findings', []):
        finding = ReviewFinding(
            finding_id=f_data.get('finding_id', ''),
            dimension=f_data.get('dimension', ''),
            severity=f_data.get('severity', 'P2'),
            message=f_data.get('message', ''),
            category=f_data.get('category', ''),
            location=f_data.get('location', ''),
            suggestion=f_data.get('suggestion', ''),
            amount=f_data.get('amount'),
        )
        finding.timestamp = f_data.get('timestamp', '')
        finding.qc_status = QCStatus(f_data.get('qc_status', '待审核'))
        finding.qc_comment = f_data.get('qc_comment')
        finding.qc_reviewer = f_data.get('qc_reviewer')
        finding.qc_reviewed_at = f_data.get('qc_reviewed_at')
        
        # 恢复推理链
        trail_data = f_data.get('trail', {})
        if trail_data:
            finding.trail.overall_confidence = trail_data.get('overall_confidence')
            finding.trail.data_sources = trail_data.get('data_sources', [])
            finding.trail.rules_applied = trail_data.get('rules_applied', [])
            finding.trail.rag_references = trail_data.get('rag_references', [])
            finding.trail.fp_checks = trail_data.get('fp_checks', [])
            for s_data in trail_data.get('steps', []):
                try:
                    step_type = ReasoningStepType(s_data.get('step_type', ''))
                except ValueError:
                    step_type = ReasoningStepType.DATA_LOAD
                step = ReasoningStep(
                    step_type=step_type,
                    description=s_data.get('description', ''),
                    input_data=s_data.get('input_data'),
                    output_data=s_data.get('output_data'),
                    rule_ref=s_data.get('rule_ref'),
                    source_ref=s_data.get('source_ref'),
                    confidence=s_data.get('confidence'),
                )
                step.timestamp = s_data.get('timestamp', step.timestamp)
                finding.trail.steps.append(step)
        
        pipeline.findings.append(finding)
    
    return pipeline


def _save_pipeline(pipeline: QCPipeline, directory: Path):
    """保存管道到指定目录"""
    data = pipeline.to_dict()
    filepath = directory / f"{pipeline.pipeline_id}.json"
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return str(filepath)


# ============================================================
# 质控审核操作
# ============================================================

def review_finding(pipeline_id: str, 
                   finding_id: str, 
                   action: str,
                   reviewer: str = "质控人员",
                   comment: str = "") -> Tuple[bool, str]:
    """
    审核一条发现
    
    Args:
        pipeline_id: 管道ID
        finding_id: 发现ID
        action: accept / reject / modify / skip
        reviewer: 审核人
        comment: 审核意见
    
    Returns:
        (成功, 消息)
    """
    pipeline = get_pipeline(pipeline_id)
    if not pipeline:
        return False, f"管道不存在: {pipeline_id}"
    
    # 找发现
    target = None
    for f in pipeline.findings:
        if f.finding_id == finding_id:
            target = f
            break
    
    if not target:
        return False, f"发现不存在: {finding_id}"
    
    # 执行操作
    action_map = {
        'accept': QCStatus.ACCEPTED,
        'reject': QCStatus.REJECTED,
        'modify': QCStatus.MODIFIED,
        'skip': QCStatus.IN_REVIEW,
    }
    
    if action not in action_map:
        return False, f"不支持的操作: {action}"
    
    target.qc_status = action_map[action]
    target.qc_reviewer = reviewer
    target.qc_reviewed_at = datetime.now(TZ).isoformat()
    if comment:
        target.qc_comment = comment
    
    pipeline.updated_at = datetime.now(TZ).isoformat()
    
    # 检查是否全部审核完毕
    all_done = all(f.qc_status not in [QCStatus.PENDING, QCStatus.IN_REVIEW] 
                   for f in pipeline.findings)
    
    if all_done:
        pipeline.status = QCStatus.ARCHIVED
        pipeline.completed_at = datetime.now(TZ).isoformat()
        # 从队列移入归档
        _save_pipeline(pipeline, ARCHIVE_DIR)
        _remove_from_queue(pipeline_id)
        return True, f"全部审核完成，已归档 | {target.finding_id} -> {target.qc_status.value}"
    else:
        # 更新队列中的状态
        _save_pipeline(pipeline, QUEUE_DIR)
        return True, f"审核完成 | {target.finding_id} -> {target.qc_status.value}"


def _remove_from_queue(pipeline_id: str):
    """从队列中移除"""
    fp = QUEUE_DIR / f"{pipeline_id}.json"
    if fp.exists():
        fp.unlink()


def batch_review(pipeline_id: str, 
                 action: str,
                 severity_filter: Optional[str] = None,
                 reviewer: str = "质控人员",
                 comment: str = "") -> List[str]:
    """批量审核"""
    pipeline = get_pipeline(pipeline_id)
    if not pipeline:
        return [f"管道不存在: {pipeline_id}"]
    
    results = []
    for f in pipeline.findings:
        if f.qc_status not in [QCStatus.PENDING, QCStatus.IN_REVIEW]:
            continue  # 已审核的跳过
        if severity_filter and f.severity != severity_filter:
            continue
        
        success, msg = review_finding(
            pipeline_id, f.finding_id, action, reviewer, comment
        )
        if success:
            results.append(msg)
    
    return results


# ============================================================
# 管道状态报告
# ============================================================

def get_qc_dashboard() -> Dict:
    """获取质控看板"""
    ensure_dirs()
    
    queue = list_queue()
    archived = []
    for fp in sorted(ARCHIVE_DIR.glob('*.json')):
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                data = json.load(f)
            archived.append(data)
        except:
            continue
    
    # 统计
    total_in_queue = len(queue)
    total_archived = len(archived)
    
    severity_sum = {"P0": 0, "P1": 0, "P2": 0}
    qc_status_sum = {}
    
    for item in queue + archived:
        for f in item.get('findings', []):
            s = f.get('severity', 'P2')
            severity_sum[s] = severity_sum.get(s, 0) + 1
            qs = f.get('qc_status', '待审核')
            qc_status_sum[qs] = qc_status_sum.get(qs, 0) + 1
    
    # 待审核列表
    pending_items = []
    for item in queue:
        pending_count = sum(
            1 for f in item.get('findings', [])
            if f.get('qc_status') in ['待审核', '审核中']
        )
        pending_items.append({
            'pipeline_id': item.get('pipeline_id'),
            'report_name': item.get('report_name'),
            'total_findings': len(item.get('findings', [])),
            'pending_count': pending_count,
            'created_at': item.get('created_at'),
        })
    
    return {
        'total_in_queue': total_in_queue,
        'total_archived': total_archived,
        'severity_breakdown': severity_sum,
        'qc_status_breakdown': qc_status_sum,
        'pending_items': pending_items,
    }


def get_qc_dashboard_markdown() -> str:
    """生成质控看板Markdown"""
    dash = get_qc_dashboard()
    
    lines = [
        f"# 📊 审盾质控看板",
        f"",
        f"**更新时间**: {datetime.now(TZ).strftime('%Y-%m-%d %H:%M')}",
        f"",
        f"## 概览",
        f"",
        f"| 指标 | 值 |",
        f"|:-----|:----|",
        f"| 队列中待审核 | {dash['total_in_queue']} 个管道 |",
        f"| 已归档 | {dash['total_archived']} 个管道 |",
        f"| 发现总数 | {sum(dash['severity_breakdown'].values())} |",
        f"| 🔴 P0 (致命) | {dash['severity_breakdown'].get('P0', 0)} |",
        f"| 🟡 P1 (重要) | {dash['severity_breakdown'].get('P1', 0)} |",
        f"| 🟢 P2 (基础) | {dash['severity_breakdown'].get('P2', 0)} |",
        f"",
        f"**质控状态分布**:",
        f"",
    ]
    
    for status, count in sorted(dash['qc_status_breakdown'].items()):
        icon = {'待审核': '⏳', '审核中': '👁️', '已确认': '✅', 
                '已驳回': '❌', '已修改': '✏️', '已归档': '📦'}.get(status, '•')
        lines.append(f"- {icon} {status}: {count}")
    
    lines.append("")
    
    if dash['pending_items']:
        lines.append("## 待审核队列")
        lines.append("")
        lines.append("| 管道ID | 报告名称 | 发现总数 | 待审核 | 创建时间 |")
        lines.append("|:-------|:---------|:---------|:-------|:---------|")
        for item in dash['pending_items']:
            lines.append(f"| {item['pipeline_id']} | {item['report_name'][:30]} | {item['total_findings']} | {item['pending_count']} | {item['created_at'][:16]} |")
        lines.append("")
        lines.append("> 使用 `python -m scripts.review_closure.cli list` 查看详情")
        lines.append("> 使用 `python -m scripts.review_closure.cli review <pipeline_id> <finding_id> accept` 审核")
    else:
        lines.append("✅ 队列为空，所有管道已审核完毕")
    
    return '\n'.join(lines)