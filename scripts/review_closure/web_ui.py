# -*- coding: utf-8 -*-
"""
审盾闭环层 - Web质控界面 v1.0
================================
Flask Web UI for QC Pipeline Management

用法:
  python scripts/review_closure/web_ui.py
  
  浏览器打开: http://localhost:5001
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

# 配置UTF-8输出
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

# 确保工作区根目录在 sys.path 中
_WORKSPACE_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, _WORKSPACE_ROOT)

from scripts.review_closure.qc_pipeline import (
    list_queue, get_pipeline, review_finding, batch_review,
    get_qc_dashboard, QUEUE_DIR, ARCHIVE_DIR
)
from scripts.review_closure.reasoning_trail import pipeline_to_markdown

app = Flask(__name__)
app.secret_key = 'shendun-qc-2026'

TZ = timezone(timedelta(hours=8))


# ============================================================
# 路由
# ============================================================

@app.route('/')
def dashboard():
    """质控看板"""
    dash = get_qc_dashboard()
    return render_template('dashboard.html', dash=dash)


@app.route('/queue')
def queue_list():
    """待审核队列"""
    items = list_queue()
    return render_template('queue.html', items=items)


@app.route('/pipeline/<pipeline_id>')
def pipeline_detail(pipeline_id):
    """管道详情"""
    pipeline = get_pipeline(pipeline_id)
    if not pipeline:
        flash(f'管道不存在: {pipeline_id}', 'error')
        return redirect(url_for('dashboard'))
    
    # 按严重程度排序
    severity_order = {'P0': 0, 'P1': 1, 'P2': 2}
    sorted_findings = sorted(
        pipeline.findings,
        key=lambda f: (severity_order.get(f.severity, 9), f.finding_id)
    )
    
    return render_template(
        'pipeline.html',
        pipeline=pipeline,
        findings=sorted_findings
    )


@app.route('/pipeline/<pipeline_id>/trail/<finding_id>')
def finding_trail(pipeline_id, finding_id):
    """查看推理链"""
    pipeline = get_pipeline(pipeline_id)
    if not pipeline:
        flash(f'管道不存在: {pipeline_id}', 'error')
        return redirect(url_for('dashboard'))
    
    # 找到对应的发现
    target = None
    for f in pipeline.findings:
        if f.finding_id == finding_id:
            target = f
            break
    
    if not target:
        flash(f'发现不存在: {finding_id}', 'error')
        return redirect(url_for('pipeline_detail', pipeline_id=pipeline_id))
    
    return render_template(
        'trail.html',
        pipeline=pipeline,
        finding=target,
        trail=target.trail
    )


@app.route('/review', methods=['POST'])
def review_action():
    """审核操作"""
    pipeline_id = request.form.get('pipeline_id')
    finding_id = request.form.get('finding_id')
    action = request.form.get('action')  # accept, reject, modify
    reviewer = request.form.get('reviewer', '质控人员')
    comment = request.form.get('comment', '')
    
    if not all([pipeline_id, finding_id, action]):
        flash('缺少必要参数', 'error')
        return redirect(url_for('dashboard'))
    
    success, msg = review_finding(
        pipeline_id=pipeline_id,
        finding_id=finding_id,
        action=action,
        reviewer=reviewer,
        comment=comment
    )
    
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'error')
    
    return redirect(url_for('pipeline_detail', pipeline_id=pipeline_id))


@app.route('/batch', methods=['POST'])
def batch_action():
    """批量审核"""
    pipeline_id = request.form.get('pipeline_id')
    action = request.form.get('action')
    severity = request.form.get('severity')  # P0, P1, P2, or empty for all
    reviewer = request.form.get('reviewer', '质控人员')
    comment = request.form.get('comment', '')
    
    if not all([pipeline_id, action]):
        flash('缺少必要参数', 'error')
        return redirect(url_for('dashboard'))
    
    results = batch_review(
        pipeline_id=pipeline_id,
        action=action,
        severity_filter=severity if severity else None,
        reviewer=reviewer,
        comment=comment
    )
    
    if results:
        flash(f'批量审核完成: {len(results)} 条', 'success')
    else:
        flash('没有符合条件的待审核发现', 'warning')
    
    return redirect(url_for('pipeline_detail', pipeline_id=pipeline_id))


@app.route('/export/<pipeline_id>')
def export_pipeline(pipeline_id):
    """导出管道报告"""
    pipeline = get_pipeline(pipeline_id)
    if not pipeline:
        flash(f'管道不存在: {pipeline_id}', 'error')
        return redirect(url_for('dashboard'))
    
    fmt = request.args.get('format', 'md')
    
    if fmt == 'json':
        return jsonify(pipeline.to_dict())
    else:
        md = pipeline_to_markdown(pipeline)
        return md, 200, {
            'Content-Type': 'text/markdown; charset=utf-8',
            'Content-Disposition': f'attachment; filename={pipeline_id}_report.md'
        }


# ============================================================
# API (供其他脚本调用)
# ============================================================

@app.route('/api/pipelines')
def api_pipelines():
    """API: 获取所有管道"""
    items = list_queue()
    return jsonify(items)


@app.route('/api/pipeline/<pipeline_id>')
def api_pipeline(pipeline_id):
    """API: 获取管道详情"""
    pipeline = get_pipeline(pipeline_id)
    if not pipeline:
        return jsonify({'error': f'管道不存在: {pipeline_id}'}), 404
    return jsonify(pipeline.to_dict())


@app.route('/api/dashboard')
def api_dashboard():
    """API: 获取质控看板"""
    dash = get_qc_dashboard()
    return jsonify(dash)


# ============================================================
# 启动
# ============================================================

if __name__ == '__main__':
    print("=" * 60)
    print("  审盾闭环层 - Web质控界面")
    print("=" * 60)
    print(f"  队列目录: {QUEUE_DIR}")
    print(f"  归档目录: {ARCHIVE_DIR}")
    print()
    print("  🌐 浏览器打开: http://localhost:5001")
    print("  📊 API文档: http://localhost:5001/api/dashboard")
    print("=" * 60)
    print()
    
    app.run(host='0.0.0.0', port=5001, debug=True)
