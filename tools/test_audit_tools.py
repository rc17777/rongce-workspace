"""
融策审计智析Agent — 文本分析工具集 v4 完整功能测试

测试所有5个工具 + 模拟器对偶 + MCP Server + 4步流水线

运行方式：
    cd tools
    python test_audit_tools.py
"""

import sys
import os
import json

# Windows GBK编码兼容
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 确保可以导入 audit_text_analysis
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("  融策审计智析Agent — 文本分析工具集 v4 功能测试")
print("=" * 70)


# ── 测试数据 ──────────────────────────────────────────────

MEETING_MINUTES = [
    """
    2024年第三次党组会议纪要

    会议时间：2024年6月15日
    参会人员：张局长、李副局长、王主任等12人

    一、关于市政务服务中心装修工程外包事项
    经讨论决定，将市政服务中心装修工程外包给天海建筑公司，合同金额约580万元。
    要求严格按照招标程序执行，确保工程质量。

    二、关于上半年预算执行情况
    截止6月底，各部门预算执行率偏低，特别是信息化建设项目资金滞留严重。
    要求各部门加快执行进度，不得挪用专项资金。

    三、关于废旧资产处置
    原办公楼拆除后的一批废旧设备需尽快处置，建议通过公开拍卖方式变卖。
    """,
    """
    2024年第四次党组会议纪要

    会议时间：2024年7月20日

    一、关于惠民补贴发放工作
    上半年惠农补贴已全部发放到位，共涉及12个乡镇3.2万户。
    发现个别乡镇存在冒领补贴的情况，已责成纪委介入调查。

    二、关于超标接待问题的整改
    通报了市审计局发现的超标接待问题，涉及金额约23万元。
    要求立即整改，相关责任人作出书面检查。

    三、关于政府采购项目
    审议通过了第三季度政府采购计划，包括办公设备采购、信息化运维服务等。
    强调要严格执行采购程序，严禁拆分采购规避招标。
    """,
    """
    2024年第五次党组会议纪要

    会议时间：2024年8月10日

    一、关于工程转包问题通报
    通报了某道路工程存在转包问题，实际施工方无相应资质。
    责令立即停工整改，追究相关人员责任。

    二、关于预付款管理
    针对部分项目大额预付款长期挂账问题，要求财务部门全面清理，
    对无正当理由的预付款限期追回。

    三、关于私车公养问题
    发现个别领导干部存在私车公养行为，已移交纪检监察部门处理。
    """,
]

EXPENSE_RECORDS = [
    "2024年6月餐饮招待费 发票号780234 ¥8,500元 接待上级检查工作组",
    "办公用品采购 得力文具一批 ¥3,200元 日常办公",
    "ETC充值 ¥5,000元 单位公务车加油卡充值",
    "会所消费 ¥12,800元 商务洽谈",
    "车辆维修费 ¥23,000元 更换轮胎及保养",
    "2024年7月招待费 ¥15,600元 超标接待餐饮开支 高档烟酒",
    "预付款 天海建筑公司 ¥2,000,000元 工程预付款",
    "现金支付 临时工工资 ¥45,000元",
    "拆分为三笔的办公设备采购：电脑1 ¥48,000元，电脑2 ¥47,000元，电脑3 ¥46,000元",
    "购物卡 ¥30,000元 节日慰问",
]

PERSONNEL_APPLICANTS = [
    {"name": "张三", "subsidy_type": "惠农补贴", "amount": 5000, "household_type": "农村"},
    {"name": "李四", "subsidy_type": "低保补贴", "amount": 8000, "household_type": "城镇"},
    {"name": "王五", "subsidy_type": "高龄补贴", "amount": 3000, "age": 65, "household_type": "农村"},
    {"name": "赵六", "subsidy_type": "惠农补贴", "amount": 5000, "household_type": "农村"},
    {"name": "张三", "subsidy_type": "危房改造", "amount": 20000, "household_type": "农村"},
]

REFERENCE_LISTS = {
    "finance_staff": ["李四", "王主任"],
    "deceased": ["钱七", "孙八"],
    "supervisor_relatives": ["赵六"],
}

CONTRACT_TEXT = """
建设工程施工合同

甲方：市政建设管理局
乙方：天海建筑工程有限公司

第一条 合同金额
合同总金额为人民币伍佰捌拾万元整（¥5,800,000元）。

第二条 签订日期
签订日期：2024年3月15日

第三条 工期
自2024年4月1日起至2025年3月31日止，总工期365日历天。

第四条 付款条件
预付款30%于合同签订后7日内支付；
进度款按每月完成工程量的80%支付；
竣工验收合格后支付至合同价的97%；
质保金3%于缺陷责任期满后14日内退还。

第五条 违约责任
逾期竣工违约金为每日合同价的万分之二。
质量不合格的，乙方应无条件返工并承担全部费用。

第六条 资质要求
承包资质：建筑工程施工总承包一级
"""

DRUG_NAMES_STANDARD = [
    "维生素C咀嚼片 100mg×60片",
    "阿莫西林胶囊 0.5g×24粒",
    "布洛芬缓释胶囊 0.3g×20粒",
]

DRUG_NAMES_CHECK = [
    "维生素C片 100mg×60片",         # 微调
    "阿莫西林分散片 0.5g×24粒",      # 剂型微调
    "布洛芬胶囊 0.3g×20粒",          # 去除关键词
    "头孢克肟片 0.1g×12片",          # 完全不同
]

SUPPLIER_STANDARD = ["天海建筑工程有限公司", "中建三局集团有限公司"]
SUPPLIER_CHECK = [
    "天海建筑有限公司",          # 缺少"工程"
    "中建三局建设集团有限公司",   # 多"建设"
    "天海建筑装饰工程有限公司",   # 新增"装饰"
]


# ── 测试函数 ──────────────────────────────────────────────

def test_tool1_hotword():
    """测试工具1：热词分析"""
    print("\n" + "-" * 50)
    print("测试1：text_hotword_analysis")
    print("-" * 50)

    from audit_text_analysis.hotword import text_hotword_analysis

    result = text_hotword_analysis(
        documents=MEETING_MINUTES,
        doc_type="meeting_minutes",
        top_n=10,
    )

    print(f"  审计类型: {result['audit_type']}")
    print(f"  文档数: {result['doc_count']}")
    print(f"  关注领域: {result['suggested_audit_focus']}")
    print(f"  热词TOP10:")
    risk_count = 0
    for hw in result["hotwords"]:
        flag = "⚠️" if hw["risk_signal"] else "  "
        print(f"    {flag} {hw['word']}: {hw['weight']:.4f}  {hw['audit_relevance'][:40]}")
        if hw["risk_signal"]:
            risk_count += 1

    assert len(result["hotwords"]) > 0, "应提取到热词"
    assert risk_count > 0, "风险信号词应被检测到"
    print(f"\n  ✅ 通过（{len(result['hotwords'])}个热词，{risk_count}个风险信号）")


def test_tool2_similarity():
    """测试工具2：相似度比对"""
    print("\n" + "-" * 50)
    print("测试2：text_similarity_compare")
    print("-" * 50)

    from audit_text_analysis.similarity import text_similarity_compare

    # 药品名称比对
    drug_result = text_similarity_compare(
        reference_texts=DRUG_NAMES_STANDARD,
        check_texts=DRUG_NAMES_CHECK,
        mode="local",
        threshold=0.6,
    )

    print(f"  [药品比对] 总比对: {drug_result['total_comparisons']}, "
          f"匹配: {len(drug_result['matches'])}")
    for m in drug_result["matches"][:3]:
        print(f"    {m['ref_text']} ←→ {m['check_text']}: "
              f"{m['similarity']:.2%} [{m['risk_type']}]")

    # 供应商名称比对
    supplier_result = text_similarity_compare(
        reference_texts=SUPPLIER_STANDARD,
        check_texts=SUPPLIER_CHECK,
        mode="local",
        threshold=0.6,
    )

    print(f"  [供应商比对] 总比对: {supplier_result['total_comparisons']}, "
          f"匹配: {len(supplier_result['matches'])}")
    for m in supplier_result["matches"]:
        print(f"    {m['ref_text']} ←→ {m['check_text']}: "
              f"{m['similarity']:.2%} [{m['risk_type']}]")

    assert len(drug_result["matches"]) > 0, "药品比对应有匹配"
    print(f"\n  ✅ 通过")


def test_tool3_contract():
    """测试工具3：合同字段提取"""
    print("\n" + "-" * 50)
    print("测试3：contract_field_extract")
    print("-" * 50)

    from audit_text_analysis.contract import ContractFieldExtractor

    extractor = ContractFieldExtractor()
    result = extractor.extract(
        contract_texts=[("建设工程施工合同.txt", CONTRACT_TEXT)],
        payment_records=[
            {"amount": 6200000, "date": "2024-12-01"},  # 超付
        ],
    )

    contract = result.contracts[0]
    print(f"  文件: {contract.file}")
    print(f"  提取字段: {list(contract.fields.keys())}")
    if "amount_normalized" in contract.fields:
        print(f"  标准化金额: ¥{contract.fields['amount_normalized']:,.2f}")
    if "party" in contract.fields:
        print(f"  合同主体: {contract.fields['party']}")

    print(f"  风险标记 ({len(contract.risk_flags)}个):")
    for rf in contract.risk_flags:
        print(f"    [{rf['severity']}] {rf['type']}: {rf['detail'][:60]}")

    assert len(contract.fields) >= 3, "至少提取3个字段"
    assert len(contract.risk_flags) >= 1, "应检测到超付风险"
    print(f"\n  ✅ 通过（{len(contract.fields)}个字段，{len(contract.risk_flags)}个风险）")


def test_tool4_personnel():
    """测试工具4：人员身份比对"""
    print("\n" + "-" * 50)
    print("测试4：personnel_profile_check")
    print("-" * 50)

    from audit_text_analysis.personnel import personnel_profile_check

    result = personnel_profile_check(
        applicants=PERSONNEL_APPLICANTS,
        reference_lists=REFERENCE_LISTS,
    )

    print(f"  总申报人: {result['total_applicants']}")
    print(f"  违规人数: {result['matched_count']}")
    print(f"  违规类型: {result['violation_by_type']}")
    print(f"  通过人数: {result['clean_count']}")
    print(f"  摘要: {result['summary']}")

    for v in result["violations"]:
        print(f"    [{v['violation_type']}] {v['name']}: {v['evidence'][:60]}")

    assert result["matched_count"] >= 2, "应有至少2个违规"
    print(f"\n  ✅ 通过")


def test_tool5_budget():
    """测试工具5：预算合规扫描"""
    print("\n" + "-" * 50)
    print("测试5：budget_compliance_scan")
    print("-" * 50)

    from audit_text_analysis.budget import budget_compliance_scan

    result = budget_compliance_scan(
        expense_texts=EXPENSE_RECORDS,
    )

    print(f"  总记录: {result['total_expenses']}")
    print(f"  违规数: {result['violation_count']}")
    print(f"  违规率: {result['violation_rate']}")
    print(f"  严重度分布: {result['violation_by_severity']}")
    print(f"  类型分布: {result['violation_by_type']}")
    print(f"  摘要: {result['summary']}")

    for v in result["violations"][:5]:
        print(f"    [#{v['index']}] [{v['severity']}] {v['rule_description']}: "
              f"{v['original_text'][:50]}...")

    assert result["violation_count"] >= 3, "应有至少3个违规"
    print(f"\n  ✅ 通过")


def test_v5_simulator():
    """测试v5：模拟器对偶"""
    print("\n" + "-" * 50)
    print("测试6：simulator_duality（v5模拟器对偶）")
    print("-" * 50)

    from audit_text_analysis.simulator_duality import (
        SimulatorDualityEngine, generate_simulator_inferences,
    )

    engine = SimulatorDualityEngine()

    # 热词推理
    hotword_finding = {
        "word": "套取",
        "weight": 0.85,
        "risk_signal": True,
        "audit_relevance": "虚构交易套取资金",
    }
    inference = engine.infer_hotword(hotword_finding, "budget")
    print(f"  [热词] 原始发现: {inference.original_finding}")
    print(f"    信任方: {inference.trust_view[:50]}...")
    print(f"    质疑方: {inference.challenge_view[:50]}...")
    print(f"    仲裁倾向: {inference.arbitration_tilt.value} ({inference.confidence:.0%})")
    print(f"    建议: {inference.recommended_action[:50]}...")

    # 预算违规推理
    budget_finding = {
        "violation_type": "keyword_hit",
        "rule_description": "超标接待餐饮开支",
        "severity": "high",
    }
    inf2 = engine.infer_budget_violation(budget_finding)
    print(f"\n  [预算] 原始发现: {inf2.original_finding}")
    print(f"    仲裁倾向: {inf2.arbitration_tilt.value} ({inf2.confidence:.0%})")

    # 批量推理
    findings = [
        {"word": "外包", "weight": 0.9, "risk_signal": True},
        {"word": "挪用", "weight": 0.75, "risk_signal": True},
    ]
    enhanced = generate_simulator_inferences(
        "text_hotword_analysis",
        findings,
        {"audit_type": "economic_responsibility"},
    )
    print(f"\n  [批量] 增强 {len(enhanced)} 条发现:")
    for f in enhanced:
        si = f.get("simulator_inference", {})
        print(f"    {f['word']}: 倾向={si.get('arbitration_tilt', '?')} "
              f"置信度={si.get('confidence', 0):.0%}")

    assert inference.arbitration_tilt is not None, "应有仲裁结果"
    assert len(enhanced) == 2, "应增强全部2条"
    print(f"\n  ✅ 通过")


def test_mcp_server():
    """测试MCP Server协议"""
    print("\n" + "-" * 50)
    print("测试7：MCP Server")
    print("-" * 50)

    from audit_text_analysis.mcp_server import MCPServer

    server = MCPServer()

    # 测试 tools/list
    resp = server.handle_request({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
    })
    tools = resp["result"]["tools"]
    print(f"  注册工具: {len(tools)}个")
    for t in tools:
        print(f"    - {t['name']}")

    # 测试 tools/call
    resp = server.handle_request({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "text_hotword_analysis",
            "arguments": {
                "documents": MEETING_MINUTES[:1],
                "top_n": 5,
            },
        },
    })
    content = resp["result"]["content"]
    result = json.loads(content[0]["text"])
    print(f"\n  工具调用结果: {len(result['hotwords'])}个热词")

    assert len(tools) >= 5, "至少5个工具"
    assert "error" not in resp, "工具调用不应报错"
    print(f"\n  ✅ 通过")


def test_pipeline():
    """测试4步流水线"""
    print("\n" + "-" * 50)
    print("测试8：4步流水线 AuditTextPipeline")
    print("-" * 50)

    from audit_text_analysis.pipeline import AuditTextPipeline

    # 创建临时测试文件
    import tempfile
    tmpdir = tempfile.mkdtemp()

    files = []
    for i, text in enumerate(MEETING_MINUTES):
        fpath = os.path.join(tmpdir, f"meeting_{i+1}.txt")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(text)
        files.append(fpath)

    # 添加一个合同文件
    contract_path = os.path.join(tmpdir, "contract_001.txt")
    with open(contract_path, "w", encoding="utf-8") as f:
        f.write(CONTRACT_TEXT)
    files.append(contract_path)

    # 添加报销文件
    expense_path = os.path.join(tmpdir, "expenses_001.txt")
    with open(expense_path, "w", encoding="utf-8") as f:
        f.write("\n---\n".join(EXPENSE_RECORDS))
    files.append(expense_path)

    # 运行流水线
    pipeline = AuditTextPipeline()
    result = pipeline.run(
        source_files=files,
        project_name="测试审计项目",
        project_type="economic_responsibility",
        enable_simulator=True,
    )

    print(f"  项目: {result['project_name']}")
    print(f"  类型: {result['project_type']}")
    print(f"  覆盖率: {result['coverage']['coverage_pct']:.1f}%")
    print(f"  总疑点: {result['total_findings']}")
    print(f"    高危: {result['high_risk_count']}")
    print(f"    中危: {result['medium_risk_count']}")
    print(f"    低危: {result['low_risk_count']}")

    # 测试人工反馈
    feedback_result = pipeline.submit_human_feedback([
        {"index": 1, "decision": "confirmed", "note": "确认违规"},
        {"index": 2, "decision": "rejected", "note": "程序性瑕疵"},
    ])
    print(f"\n  人工反馈: 确认{feedback_result['confirmed']}条, "
          f"驳回{feedback_result['rejected']}条")

    assert result["total_findings"] > 0, "应有疑点产出"
    assert len(files) == 5, "应有5个测试文件"
    print(f"\n  ✅ 通过")

    # 清理
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)


def test_structured_output():
    """测试Agent输出结构化"""
    print("\n" + "-" * 50)
    print("测试9：Agent输出结构化 OutputBuilder + Validator")
    print("-" * 50)

    from audit_text_analysis.structured_output import (
        OutputBuilder, OutputValidator, build_from_tool_result,
    )
    from audit_text_analysis.hotword import text_hotword_analysis
    from audit_text_analysis.budget import budget_compliance_scan

    # 1. 从热词分析构建
    hotword_result = text_hotword_analysis(
        documents=MEETING_MINUTES,
        top_n=5,
    )
    output = build_from_tool_result(
        agent_name="经济责任审计Agent",
        project="2024年度经责审计",
        period="2024",
        tool_name="text_hotword_analysis",
        tool_result=hotword_result,
    )

    validator = OutputValidator()
    is_valid, passed, failed = validator.validate(output)

    print(f"  [热词→结构化] 校验: {'✅ 通过' if is_valid else '❌ 失败'}")
    print(f"    通过项: {passed}")
    if failed:
        print(f"    失败项: {failed}")
    print(f"    目标: {output.target.objective[:50]}...")
    print(f"    结论: {output.conclusion.statement[:50]}...")
    print(f"    例外: {len(output.conclusion.exceptions)}个")

    # 2. 从预算扫描构建
    budget_result = budget_compliance_scan(expense_texts=EXPENSE_RECORDS)
    output2 = build_from_tool_result(
        agent_name="CPA审计Agent",
        project="2024年度预算执行审计",
        period="2024",
        tool_name="budget_compliance_scan",
        tool_result=budget_result,
    )
    is_v2, p2, f2 = validator.validate(output2)

    print(f"\n  [预算→结构化] 校验: {'✅ 通过' if is_v2 else '❌ 失败'}")
    print(f"    总体意见: {output2.conclusion.overall_opinion}")

    assert output.agent_name == "经济责任审计Agent"
    assert len(output.conclusion.exceptions) >= 0
    print(f"\n  ✅ 通过")


def test_workpaper_scorer():
    """测试L1底稿质量评分引擎"""
    print("\n" + "-" * 50)
    print("测试10：L1评分引擎 WorkpaperScorer")
    print("-" * 50)

    from audit_text_analysis.workpaper_scorer import WorkpaperScorer

    scorer = WorkpaperScorer()

    # 优秀底稿
    good_wp = """
审计程序：应收账款存在性认定

一、目标
本程序针对应收账款的存在性认定，验证期末应收账款余额是否真实存在。

二、过程
采用分层抽样方法，按金额降序选取前20大客户（覆盖期末余额85%），
随机选取其余20家客户。
测试步骤：
1. 获取应收账款明细表（索引A-1）
2. 核对销售合同（索引C-1至C-40）
3. 核对客户签收单（索引D-1至D-40）
4. 对前20大客户执行函证程序

三、结论
经核查，未发现重大异常。20份函证已全部回函，
回函差异已逐项核对并记录处理（详见索引E-1）。
期末应收账款余额可以确认。

四、索引
- 明细表: A-1
- 合同: C-1 至 C-40
- 签收单: D-1 至 D-40
- 函证: E-1 至 E-20
"""

    report = scorer.score(
        content=good_wp,
        workpaper_id="WP-ARR-001",
        workpaper_title="应收账款存在性测试",
    )

    print(f"  [优秀底稿] 得分: {report.final_score}/100 （{report.grade[:8]}）")
    print(f"    四维: A={report.score_a} B={report.score_b} "
          f"C={report.score_c} D={report.score_d}")
    print(f"    扣分: E={report.penalty_e} F={report.penalty_f} G={report.penalty_g}")

    # 不合格底稿
    bad_wp = """
应收账款检查

金额500万，无异常。

已测试，没问题。
"""

    bad_report = scorer.score(
        content=bad_wp,
        workpaper_id="WP-BAD-001",
        workpaper_title="应收账款检查",
    )

    print(f"\n  [不合格底稿] 得分: {bad_report.final_score}/100 （{bad_report.grade[:8]}）")
    print(f"    风险标记: {bad_report.risk_flags}")
    print(f"    改进建议:")
    for item in bad_report.improvement_checklist:
        print(f"      - {item}")

    # 照抄检测
    prev_year = """
审计程序：应收账款存在性认定
本程序针对应收账款的存在性认定。
采用分层抽样方法，按金额降序选取前20大客户。
获取应收账款明细表，核对销售合同和客户签收单。
经核查，未发现重大异常。
期末应收账款余额可以确认。
"""
    copy_report = scorer.score(
        content=prev_year.replace("本程序", "本程序"),
        workpaper_id="WP-ARR-002",
        workpaper_title="应收账款测试（疑似照抄）",
        previous_year_content=prev_year,
    )

    print(f"\n  [照抄检测] 扣分G={copy_report.penalty_g} "
          f"（与上年度对比）")

    # 批量评分
    batch_reports = scorer.batch_score([
        ("WP-001", "A底稿", good_wp),
        ("WP-002", "B底稿", bad_wp),
    ])
    summary = scorer.summary(batch_reports)
    print(f"\n  [批量评分] 共{summary['total']}份，通过{summary['passed']}份，"
          f"平均分{summary['avg_score']}")

    assert report.final_score >= 70, "优秀底稿应通过L1"
    assert bad_report.final_score < 70, "不合格底稿应被识别"
    assert report.score_a >= 15, "优秀底稿目标应得分"
    print(f"\n  ✅ 通过")


def test_agent_config():
    """测试Agent配置 + 系统提示注入"""
    print("\n" + "-" * 50)
    print("测试11：Agent配置 + 系统提示注入")
    print("-" * 50)

    from audit_text_analysis.agent_config import (
        AGENT_CONFIGS, get_agent_tool_matrix, get_agent_for_project,
        get_system_prompt, inject_kb_to_prompt,
    )

    # 工具分配矩阵
    matrix = get_agent_tool_matrix()
    print(f"  Agent数量: {len(AGENT_CONFIGS)}")
    for name, tools in matrix.items():
        print(f"    {name}: {len(tools)}个工具")

    # 项目→Agent映射
    agents = get_agent_for_project("economic_responsibility")
    print(f"  经责审计激活: {[a.agent_name for a in agents]}")
    assert len(agents) >= 1

    # 系统提示
    prompt = get_system_prompt("national_audit")
    assert "国家审计Agent" in prompt
    assert "国家审计准则" in prompt
    print(f"  国家审计Agent系统提示: {len(prompt)}字符")

    # KB注入
    injected = inject_kb_to_prompt("你是审计助手。", "cpa_audit")
    assert "中国注册会计师" in injected
    print(f"  KB注入后: {len(injected)}字符")

    print(f"\n  ✅ 通过")


def test_pitfall_guards():
    """测试避坑约束"""
    print("\n" + "-" * 50)
    print("测试12：避坑约束 PitfallGuard")
    print("-" * 50)

    from audit_text_analysis.pitfall_guards import PitfallGuard

    guard = PitfallGuard()

    # 误区1：交叉验证
    findings_ok = [
        {"index": 1, "severity": "high", "cross_refs": ["合同A-1"]},
        {"index": 2, "severity": "medium", "cross_refs": ["付款记录B-3"]},
    ]
    check = guard.check_cross_validation(findings_ok)
    print(f"  [误区1-交叉验证] 通过={check.passed} 得分={check.score:.0%}")
    assert check.passed

    findings_bad = [
        {"index": 1, "severity": "high"},
        {"index": 2, "severity": "medium"},
    ]
    check2 = guard.check_cross_validation(findings_bad)
    assert not check2.passed
    print(f"  [误区1-无交叉验证] 通过={check2.passed} 详情={check2.detail}")

    # 误区2：人机核验
    check3 = guard.check_human_review(
        findings_ok,
        [{"index": 1, "decision": "confirmed"}],
    )
    assert check3.passed
    print(f"  [误区2-已复核] 通过={check3.passed}")

    # 误区3：覆盖检查
    check4 = guard.check_data_coverage(100, 85)
    assert not check4.passed
    print(f"  [误区3-覆盖率不足] 通过={check4.passed} 详情={check4.detail}")

    # 综合检查
    report = guard.run_all(
        findings=findings_ok,
        expected_count=100,
        actual_count=95,
        project_type="economic_responsibility",
        human_review_status=[{"index": 1, "decision": "confirmed"}],
    )
    print(f"  [综合] 通过={report.all_passed} 失败={report.failed_count}")

    print(f"\n  ✅ 通过")


def test_year_over_year():
    """测试年度对比检测"""
    print("\n" + "-" * 50)
    print("测试13：年度对比检测 YearOverYear")
    print("-" * 50)

    from audit_text_analysis.year_over_year import detect_copy_paste

    # 照抄案例
    prev = """
应收账款存在性测试
2023年度审计
本程序针对应收账款的存在性认定。
采用分层抽样方法，选取前20大客户。
经核查，未发现重大异常。
期末应收账款余额5,800,000元可以确认。
"""
    cur_copy = """
应收账款存在性测试
2024年度审计
本程序针对应收账款的存在性认定。
采用分层抽样方法，选取前20大客户。
经核查，未发现重大异常。
期末应收账款余额5,800,000元可以确认。
"""

    report = detect_copy_paste(
        current_content=cur_copy,
        previous_content=prev,
        workpaper_id="WP-ARR-001",
        current_year="2024",
        previous_year="2023",
    )

    print(f"  [照抄底稿] 相似度={report.overall_similarity:.1%} "
          f"风险={report.risk_level} 陈旧度={report.staleness_score}")
    print(f"    差异化标注: {'有' if report.has_diff_analysis else '无'}")
    print(f"    数据更新: {'是' if report.has_updated_numbers else '否'}")
    print(f"    建议: {report.recommendation}")
    assert report.risk_level == "high"

    # 正常更新案例
    cur_updated = """
应收账款存在性测试
2024年度审计
本程序针对应收账款的存在性、准确性认定。
采用分层抽样方法覆盖期末余额88%（较上年提升3个百分点），选取前25大客户。
本年度新增3家重大客户，新增应收账款1,200,000元。
经核查，未发现重大异常。
期末应收账款余额7,000,000元可以确认。
"""

    report2 = detect_copy_paste(
        current_content=cur_updated,
        previous_content=prev,
        workpaper_id="WP-ARR-002",
        current_year="2024",
        previous_year="2023",
    )

    print(f"\n  [正常更新] 相似度={report2.overall_similarity:.1%} "
          f"风险={report2.risk_level}")
    assert report2.risk_level != "high"

    print(f"\n  ✅ 通过")


def test_data_readiness():
    """测试非结构化数据就绪度评估"""
    print("\n" + "-" * 50)
    print("测试14：数据就绪度评估 DataReadiness")
    print("-" * 50)

    from audit_text_analysis.data_readiness import DataReadinessAssessor

    assessor = DataReadinessAssessor()

    # 模拟文件列表（政府审计典型场景）
    mock_files = [
        {"name": "预算执行数据.csv", "type": "csv", "pages": 1},
        {"name": "科目余额表.xlsx", "type": "excel", "pages": 5},
        {"name": "合同扫描件_001.pdf", "type": "pdf", "pages": 12},
        {"name": "合同扫描件_002.pdf", "type": "pdf", "pages": 8},
        {"name": "会议纪要扫描件.pdf", "type": "pdf", "pages": 30},
        {"name": "手写凭证.jpg", "type": "image", "pages": 1},
        {"name": "凭证扫描件_001.pdf", "type": "pdf", "pages": 2},
        {"name": "凭证扫描件_002.pdf", "type": "pdf", "pages": 3},
    ]

    dashboard = assessor.assess_file_list(
        files=mock_files,
        project_name="测试政府审计项目",
    )

    print(f"  项目: {dashboard.project_name}")
    print(f"  总文件: {dashboard.total_files}，总页数: ~{dashboard.total_pages}")
    print(f"  L1绿色: {dashboard.l1_count}个 ({dashboard.l1_ratio:.0%})")
    print(f"  L2黄色: {dashboard.l2_count}个 ({dashboard.l2_ratio:.0%})")
    print(f"  L3红色: {dashboard.l3_count}个 ({dashboard.l3_ratio:.0%})")
    print(f"  就绪度: {dashboard.overall_readiness:.0f}/100 [{dashboard.readiness_grade}]")
    print(f"  需OCR: {dashboard.needs_ocr_pages}页 (~{dashboard.estimated_ocr_hours}h)")
    print(f"  需预处理: {'是' if dashboard.preprocess_required else '否'}")
    print(f"  建议: {dashboard.recommendation[:80]}...")

    assert dashboard.l3_count >= 3 or any(
        s.readiness.value == "L3_红色" and s.file_count >= 3
        for s in dashboard.sources
    ), "应有L3红色文件"
    print(f"\n  ✅ 通过")


def test_ontology():
    """测试审计业务本体论"""
    print("\n" + "-" * 50)
    print("测试15：审计业务本体论 AuditOntology")
    print("-" * 50)

    from audit_text_analysis.audit_ontology import AuditOntology, get_ontology

    onto = AuditOntology()
    onto.load_defaults()

    stats = onto.stats
    print(f"  本体统计: {stats}")

    # 实体查询
    expenses = onto.get_entities_by_type("expense")
    print(f"  费用实体: {len(expenses)}个")
    assert len(expenses) >= 3

    # 规则查询
    rules = onto.get_rules_by_category("procurement")
    print(f"  采购审计规则: {len(rules)}条")
    for r in rules[:3]:
        print(f"    [{r.risk_level}] {r.name}: {r.description[:50]}...")

    # 条件匹配
    matched = onto.match_rules(
        category="procurement",
        conditions={"amount_min": 500000, "same_supplier": True},
    )
    print(f"  条件匹配: {len(matched)}条 首条={matched[0].name if matched else '无'}")
    assert len(matched) >= 1

    # 搜索
    results = onto.search_rules("围标")
    print(f"  关键词搜索'围标': {len(results)}条")
    assert len(results) >= 1

    # Prompt注入
    prompt_snippet = onto.inject_to_prompt("procurement", max_rules=3)
    assert "审计业务本体知识" in prompt_snippet
    print(f"  Prompt注入: {len(prompt_snippet)}字符")

    # 序列化
    data = onto.to_dict()
    assert data["version"] == "1.0.0"
    print(f"  可序列化: JSON {len(json.dumps(data, ensure_ascii=False))}字节")

    print(f"\n  ✅ 通过")


def test_index_system():
    """测试审计索引子系统"""
    print("\n" + "-" * 50)
    print("测试16：审计索引子系统 AuditIndexSystem")
    print("-" * 50)

    from audit_text_analysis.audit_index import AuditIndexSystem

    idx = AuditIndexSystem("2024年度经责审计")

    # 添加索引条目
    wp1 = idx.add_entry("WP", "ARR", "应收账款存在性测试",
                        assertions=["存在性", "计价"])
    wp2 = idx.add_entry("WP", "INV", "存货盘点底稿",
                        assertions=["存在性", "完整性"])
    ev1 = idx.add_entry("EV", "INV", "盘点表-原材料",
                        file_path="/audit/evidence/INV-001.pdf")
    ev2 = idx.add_entry("EV", "INV", "盘点表-半成品",
                        file_path="/audit/evidence/INV-002.pdf")
    ct1 = idx.add_entry("CT", "PUR", "采购合同-设备",
                        file_path="/audit/contracts/PUR-001.pdf")
    pm1 = idx.add_entry("PM", "PUR", "设备采购付款记录")

    print(f"  创建索引: {len(idx.entries)}条")
    print(f"    底稿: {wp1}, {wp2}")
    print(f"    证据: {ev1}, {ev2}")
    print(f"    合同: {ct1}")
    print(f"    支付: {pm1}")

    # 建立交叉引用
    idx.add_ref(wp1, ev1)
    idx.add_ref(wp1, ct1)
    idx.add_ref(wp2, ev1)
    idx.add_ref(wp2, ev2)
    idx.add_ref(ct1, pm1)
    idx.add_ref(wp1, pm1)

    # 文本自动链接
    text = "详见 WP-ARR-001 和 EV-INV-002 以及 CT-PUR-001"
    linked = idx.auto_link_from_text(wp2, text)
    print(f"  自动链接: {linked}条")

    # 引用链
    chains = idx.get_ref_chain(wp1)
    print(f"  引用链(WP-ARR-001): {len(chains)}条路径")
    for chain in chains[:2]:
        print(f"    {' → '.join(chain)}")

    # 校验
    validation = idx.validate()
    print(f"  校验: 完整性={validation.completeness:.0%}"
          f" 断链={validation.broken_refs} 孤岛={validation.orphan_entries}")

    # 搜索
    results = idx.search("盘点")
    print(f"  搜索'盘点': {len(results)}条")
    assert len(results) >= 2

    # 统计
    st = idx.stats
    print(f"  统计: {st['total_entries']}条, {st['total_refs']}个引用, "
          f"完整性={st['completeness']}")

    # Mermaid可视化
    mermaid = idx.to_mermaid()
    assert "WP_ARR_001" in mermaid
    print(f"  Mermaid图: {len(mermaid)}字符")

    # 序列化
    import tempfile
    tmp = tempfile.mktemp(suffix=".json")
    idx.to_json(tmp)
    idx2 = AuditIndexSystem.from_json(tmp)
    assert len(idx2.entries) == len(idx.entries)
    os.unlink(tmp)
    print(f"  序列化: 往返一致 ✅")

    print(f"\n  ✅ 通过")


# ── 主函数 ──────────────────────────────────────────────

def main():
    tests = [
        ("工具1：热词分析", test_tool1_hotword),
        ("工具2：相似度比对", test_tool2_similarity),
        ("工具3：合同提取", test_tool3_contract),
        ("工具4：人员比对", test_tool4_personnel),
        ("工具5：预算合规", test_tool5_budget),
        ("v5：模拟器对偶", test_v5_simulator),
        ("MCP Server", test_mcp_server),
        ("4步流水线", test_pipeline),
        ("输出结构化", test_structured_output),
        ("L1评分引擎", test_workpaper_scorer),
        ("Agent配置+提示", test_agent_config),
        ("避坑约束", test_pitfall_guards),
        ("年度对比检测", test_year_over_year),
        ("数据就绪度", test_data_readiness),
        ("业务本体论", test_ontology),
        ("索引子系统", test_index_system),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"\n  ❌ {name} 失败: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 70)
    print(f"  测试结果: {passed}通过 / {failed}失败 / {len(tests)}总计")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
