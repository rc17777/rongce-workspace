# -*- coding: utf-8 -*-
"""
审盾闭环层 - 集成测试 v1.0
============================
验证闭环层各组件：
  1. 推理链构建
  2. 质控管道提交
  3. 质控审核
  4. 看板显示
"""

import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts.review_closure.schema import (
    ReviewFinding, ReasoningTrail, ReasoningStep, ReasoningStepType,
    QCPipeline, QCStatus
)
from scripts.review_closure.reasoning_trail import (
    build_quick_review_trail, build_full_pipeline, save_pipeline,
    pipeline_to_markdown, RULE_REGISTRY
)
from scripts.review_closure.qc_pipeline import (
    submit_to_qc, list_queue, get_pipeline, review_finding,
    batch_review, get_qc_dashboard
)


def test_schema():
    """测试数据模型"""
    print("\n📝 测试数据模型...")
    
    trail = ReasoningTrail("F-20260721-001")
    trail.add_data_load("报告文本", "加载审计报告全文")
    trail.add_rule_match("R-001", "检测金额单位混用", "万元和元同时出现", "需要统一")
    trail.add_rag_query("专项资金审计要点", "查到了3条相关法规", "RAG知识库")
    trail.add_calculation("合计校验", "100+200+300=600", "合计600万元")
    trail.add_judgment("判断金额差异是否重大", "差异50万", "属于重大差异，需标注", 0.85)
    trail.add_fp_check("FP-G1", "检查金额差异是否<0.01%", "差异0.5%，不触发抑制")
    trail.set_confidence(0.88)
    
    d = trail.to_dict()
    assert d['step_count'] == 6, f"步骤数不对: {d['step_count']}"
    assert d['overall_confidence'] == 0.88
    assert len(d['data_sources']) == 2, f"data_sources={d['data_sources']}"  # 数据加载 + RAG查询
    assert len(d['rules_applied']) == 2, f"rules_applied={d['rules_applied']}"  # 规则匹配 + FP检查
    assert len(d['rag_references']) == 1
    assert len(d['fp_checks']) == 1
    
    print(f"  ✅ 推理链: {d['step_count']}步, 置信度 {d['overall_confidence']}")
    print(f"     数据源: {len(d['data_sources'])}个, 规则: {len(d['rules_applied'])}条")
    print(f"     RAG引用: {len(d['rag_references'])}条, FP检查: {len(d['fp_checks'])}条")
    
    # 测试Markdown输出
    # trail.to_markdown() 方法已经改为 to_markdown_format
    md = trail.to_markdown()
    assert '推理过程' in md or '推演过程' in md
    print(f"  ✅ Markdown可读输出: {len(md)}字符")


def test_finding():
    """测试带推理链的发现"""
    print("\n📝 测试复核发现...")
    
    finding = ReviewFinding(
        finding_id="F-20260721-001",
        dimension="金额单位",
        severity="P1",
        message="报告同时使用万元和元为单位，建议统一",
        category="快速复核",
        location="第3页第2段",
        suggestion="统一为万元单位",
    )
    
    # 附加推理链
    finding.trail.add_data_load("报告文本", "扫描全文金额单位")
    finding.trail.add_rule_match("R-001", "检测金额单位混用", "万元和元", "需要统一")
    finding.trail.set_confidence(0.85)
    
    d = finding.to_dict()
    assert d['finding_id'] == 'F-20260721-001'
    assert d['severity'] == 'P1'
    assert d['qc_status'] == '待审核'
    
    print(f"  ✅ 发现: {d['finding_id']} [{d['severity']}] {d['dimension']}")
    print(f"     状态: {d['qc_status']}, 推理链: {len(d['trail']['steps'])}步")


def test_pipeline():
    """测试质控管道"""
    print("\n📝 测试质控管道...")
    
    pipeline = QCPipeline(report_name="测试报告-专项资金审计")
    
    # 添加几条发现
    for i in range(3):
        f = ReviewFinding(
            finding_id=f"F-20260721-{i+1:03d}",
            dimension=["金额单位", "错别字", "日期格式"][i],
            severity=["P1", "P2", "P2"][i],
            message=f"测试发现{i+1}",
            category="快速复核",
        )
        f.trail.add_data_load("报告文本", f"测试数据加载{i+1}")
        f.trail.set_confidence(0.85 - i*0.1)
        pipeline.add_finding(f)
    
    summary = pipeline.get_summary()
    assert summary['total_findings'] == 3
    assert summary['severity_breakdown']['P1'] == 1
    assert summary['severity_breakdown']['P2'] == 2
    
    print(f"  ✅ 管道: {summary['total_findings']}条发现")
    print(f"     P1: {summary['severity_breakdown']['P1']}, P2: {summary['severity_breakdown']['P2']}")
    print(f"     状态: {summary['status']}")


def test_qc_flow():
    """测试质控工作流"""
    print("\n📝 测试质控工作流...")
    
    # 创建管道
    pipeline = QCPipeline(report_name="QC工作流测试")
    
    for i in range(3):
        f = ReviewFinding(
            finding_id=f"F-20260721-{i+10:03d}",
            dimension=f"测试维度{i+1}",
            severity=["P0", "P1", "P2"][i],
            message=f"QC测试发现{i+1}",
            category="快速复核",
        )
        f.trail.add_data_load("报告文本", f"QC测试数据{i+1}")
        pipeline.add_finding(f)
    
    # 提交到队列
    path = submit_to_qc(pipeline)
    print(f"  ✅ 提交到队列: {pipeline.pipeline_id}")
    print(f"     路径: {path}")
    
    # 查看队列
    queue = list_queue()
    assert len(queue) >= 1
    print(f"  ✅ 队列中有 {len(queue)} 个管道")
    
    # 审核P0
    success, msg = review_finding(
        pipeline.pipeline_id, "F-20260721-010",
        "accept", "测试审核员", "P0问题已确认"
    )
    assert success
    print(f"  ✅ 审核P0: {msg}")
    
    # 批量审核P1
    results = batch_review(pipeline.pipeline_id, "accept", "P1", "测试审核员")
    assert len(results) == 1
    print(f"  ✅ 批量审核P1: {len(results)}条")
    
    # 审核P2
    success, msg = review_finding(
        pipeline.pipeline_id, "F-20260721-012",
        "reject", "测试审核员", "误报，格式正确"
    )
    assert success
    print(f"  ✅ 审核P2: {msg}")
    
    # 检查看板
    dash = get_qc_dashboard()
    assert dash['total_in_queue'] >= 1
    print(f"  ✅ 看板: 队列 {dash['total_in_queue']}个, 归档 {dash['total_archived']}个")


def test_quick_review_integration():
    """测试快速复核集成"""
    print("\n📝 测试快速复核集成...")
    
    test_text = """
    关于XX项目2023年度专项资金审计报告
    
    本次审计发现以下问题：
    一、资金使用不规范问题
    1. 账务处理错误，涉及金额500万元。
    2. 截止2023年12月31日，尚有200万元未拨付到位。
    3. 合同签定不规范，涉及金额300万元。
    4. 部份资金使用不符合规定，涉及金额100万元。
    
    二、管理建议
    1. 加墙财务管理，避免类似问题再次发生。
    2. 建议做出一系列整改措施。
    
    三、附表
    其中：专项支出合计 1000万元。
    （）
    （）
    """
    
    from scripts.review_closure.cli import _run_quick_review
    
    step2 = _run_quick_review(test_text)
    assert step2['total'] > 0, "应该有发现问题"
    
    print(f"  ✅ 快速复核发现 {step2['total']} 个问题")
    for issue in step2['issues']:
        print(f"     [{issue['severity']}] {issue['dimension']}: {issue['message'][:40]}")


def test_full_pipeline_integration():
    """测试完整流水线集成"""
    print("\n📝 测试完整流水线集成...")
    
    test_text = "关于XX项目2023年度专项资金审计报告\n\n存在账务处理不规范问题。"
    
    step2 = {"issues": [{"dimension": "错别字", "severity": "P1", "message": "发现账务应为账务", "context": ""}], "total": 1}
    step3 = {
        "audit_type": "专项资金",
        "report_name": "测试报告",
        "report_length": len(test_text),
        "dimensions": [{"id": "①", "name": "逻辑一致性", "focus": "测试", "risk_level": "重要层"}],
        "fp_rules": ["FP-G1"],
    }
    step1 = {"topics": [{"name": "专项资金", "confidence": "高"}], "rag_knowledge": [], "services_status": {"rag": True}}
    
    pipeline = build_full_pipeline(
        report_name="测试完整流水线",
        step2_result=step2,
        step3_framework=step3,
        step1_result=step1,
        report_text=test_text,
    )
    
    assert len(pipeline.findings) > 0
    print(f"  ✅ 完整流水线: {len(pipeline.findings)}条发现")
    for f in pipeline.findings:
        print(f"     [{f.severity}] {f.dimension}: {f.message[:50]}")
        print(f"       推理链: {f.trail.step_count}步, 置信度: {f.trail.overall_confidence}")
    
    # 保存管道
    path = save_pipeline(pipeline)
    print(f"  ✅ 已保存: {path}")


def test_all():
    """运行全部测试"""
    print("=" * 50)
    print("  审盾闭环层 - 集成测试")
    print("=" * 50)
    
    tests = [
        test_schema,
        test_finding,
        test_pipeline,
        test_qc_flow,
        test_quick_review_integration,
        test_full_pipeline_integration,
    ]
    
    passed = 0
    failed = 0
    
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"\n❌ 测试失败: {t.__name__}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n{'=' * 50}")
    print(f"  ✅ {passed} 通过, ❌ {failed} 失败")
    if failed == 0:
        print(f"  🎉 全部通过!")
    print(f"{'=' * 50}")
    
    return failed


if __name__ == '__main__':
    sys.exit(test_all())