# 智析智能体 v2.0 — 主应用
# 整合全部功能模块 + Web界面

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import json
import os
from datetime import datetime

# 导入所有模块
from modules.data_collection.collector import (
    CollectorManager, CollectTask, DatabaseAdapter, APIConnector, FileImporter, AccountingParser
)
from modules.data_validation.validator import ValidationEngine, DataCleaner
from modules.data_migration.standardizer import DataMigrator, AuditStandardizer, StandardLibrary
from modules.unstructured.doc_extractor import OCREngine, DocExtractor, DocToDB
from modules.audit_models.workbench import ModelWorkbench, ANALYSIS_METHODS, AUDIT_SQL_MODELS
from modules.bigdata.analytics import GraphAnalyzer, TextMiner, VisualizationHelper
from modules.knowledge.engine import CoTEngine, PromptLibrary, DataQualityChecker, MethodologyEngine
from modules.knowledge.rag_bridge import get_rag_bridge
from modules.knowledge.report_review_engine import get_review_engine
from modules.audit_models.bid_collusion_extended import get_bid_detector

# 初始化RAG、报告复核和串标检测引擎
rag_bridge = get_rag_bridge()
review_engine = get_review_engine()
bid_detector = get_bid_detector()

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), "web", "templates"))
CORS(app)

# 初始化所有引擎
collector_mgr = CollectorManager()
validator = ValidationEngine()
cleaner = DataCleaner()
standardizer = AuditStandardizer()
std_library = StandardLibrary()
ocr = OCREngine()
model_wb = ModelWorkbench()
graph_analyzer = GraphAnalyzer()
text_miner = TextMiner()
cot_engine = CoTEngine()
prompt_lib = PromptLibrary()
dq_checker = DataQualityChecker()
methodology = MethodologyEngine()

# ============================================================
# 首页
# ============================================================
@app.route("/")
def index():
    return render_template("index.html")

# ============================================================
# API: 系统状态
# ============================================================
@app.route("/api/status")
def status():
    return jsonify({
        "name": "智析智能体 v2.0",
        "version": "2.0.0",
        "modules": {
            "data_collection": {"status": "active", "databases": DatabaseAdapter.list_supported()},
            "data_validation": {"status": "active", "rules": len(validator.rules)},
            "data_migration": {"status": "active", "domains": AuditStandardizer.list_domains()},
            "unstructured": {"status": "active", "ocr_backend": ocr.backend},
            "audit_models": {"status": "active", "models": len(model_wb.models), "categories": model_wb.list_categories()},
            "bigdata": {"status": "active"},
            "knowledge": {
                "status": "active",
                "cot_chains": cot_engine.list_chains(),
                "prompts": len(prompt_lib.list_all()),
                "dq_checks": 12,
                "methodologies": len(methodology.list_all()),
            },
        },
        "uptime": datetime.now().isoformat(),
    })

# ============================================================
# API: 健康检查（供 watchdog + MCP 调用）
# ============================================================
@app.route("/api/health")
def health():
    """轻量健康检查：返回 200 即表示服务正常"""
    return jsonify({"status": "ok", "service": "zhixi-v2", "timestamp": datetime.now().isoformat()})

# ============================================================
# API: 数据采集
# ============================================================
@app.route("/api/collector/databases")
def list_databases():
    return jsonify({"supported": DatabaseAdapter.list_supported(), "domestic": DatabaseAdapter.list_domestic()})

@app.route("/api/collector/tasks", methods=["GET", "POST"])
def collector_tasks():
    if request.method == "POST":
        data = request.json
        task = CollectTask(
            id=data.get("id", f"TASK-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
            name=data["name"],
            source_type=data["source_type"],
            source_config=data["source_config"],
            target_table=data.get("target_table", ""),
            schedule=data.get("schedule", "once"),
        )
        collector_mgr.add_task(task)
        return jsonify({"status": "created", "task_id": task.id})
    return jsonify(collector_mgr.get_status())

@app.route("/api/collector/run/<task_id>", methods=["POST"])
def run_collector(task_id):
    result = collector_mgr.run_task(task_id)
    return jsonify(result)

@app.route("/api/collector/accounting/software")
def list_accounting_software():
    return jsonify({k: v["desc"] for k, v in AccountingParser.ACCOUNTING_SOFTWARE.items()})

# ============================================================
# API: 数据校验清洗
# ============================================================
@app.route("/api/validator/rules")
def validator_rules():
    return jsonify([{"id": r.id, "name": r.name, "type": r.rule_type, "severity": r.severity} for r in validator.rules])

@app.route("/api/validator/run", methods=["POST"])
def run_validation():
    """接收JSON数据，执行校验"""
    try:
        data = request.json
        import pandas as pd
        df = pd.DataFrame(data.get("data", []))
        key_cols = data.get("key_cols", [])
        required_cols = data.get("required_cols", [])
        reports = validator.run_all(df, key_cols=key_cols, required_cols=required_cols)
        summary = validator.summary()
        # Convert numpy types to Python native
        import numpy as np
        def conv(obj):
            if isinstance(obj, (np.integer,)): return int(obj)
            if isinstance(obj, (np.floating,)): return float(obj)
            if isinstance(obj, (np.bool_,)): return bool(obj)
            if isinstance(obj, (np.ndarray,)): return obj.tolist()
            return obj
        return jsonify({
            "summary": summary,
            "reports": [{"rule_id": r.rule_id, "rule_name": r.rule_name, "passed": conv(r.passed),
                          "fail_rows": conv(r.fail_rows), "fail_pct": conv(r.fail_pct), "details": r.details} for r in reports]
        })
    except Exception as e:
        return jsonify({"error": str(e), "summary": {"total": 0, "passed": 0, "failed": 0}}), 200

@app.route("/api/cleaner/outliers", methods=["POST"])
def detect_outliers():
    data = request.json
    import pandas as pd
    df = pd.DataFrame(data.get("data", []))
    col = data.get("col")
    method = data.get("method", "iqr")
    outliers = DataCleaner.detect_outliers(df, col, method)
    return jsonify({"total_outliers": len(outliers), "samples": outliers.head(20).to_dict("records")})

# ============================================================
# API: 数据标准化
# ============================================================
@app.route("/api/standardizer/domains")
def standardizer_domains():
    return jsonify({"domains": AuditStandardizer.list_domains()})

@app.route("/api/standardizer/schema/<domain>")
def standardizer_schema(domain):
    schema = AuditStandardizer.get_standard_schema(domain)
    return jsonify({k: {"name": v["name"], "type": v["type"], "required": v.get("required", False)} for k, v in schema.items()})

@app.route("/api/standardizer/library")
def standardizer_library():
    return jsonify(std_library.to_catalog())

# ============================================================
# API: 非结构化处理
# ============================================================
@app.route("/api/unstructured/extract", methods=["POST"])
def extract_document():
    """接收文本，自动识别文档类型并提取关键要素"""
    try:
        data = request.json
        text = data.get("text", "")
        doc_type = data.get("doc_type", "auto")
        result = DocExtractor.process_document(text, doc_type)
        return jsonify(result)
    except Exception as e:
        return jsonify({"doc_type": "error", "error": str(e)})

@app.route("/api/unstructured/ocr", methods=["POST"])
def ocr_document():
    """上传图片进行OCR"""
    if "file" not in request.files:
        return jsonify({"error": "请上传图片文件"}), 400
    file = request.files["file"]
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        file.save(tmp.name)
        text = ocr.recognize(tmp.name)
    return jsonify({"text": text, "length": len(text)})

# ============================================================
# API: 审计模型工作台
# ============================================================
@app.route("/api/models/categories")
def model_categories():
    return jsonify(model_wb.list_categories())

@app.route("/api/models")
def list_models():
    category = request.args.get("category")
    return jsonify(model_wb.list_models(category=category))

@app.route("/api/models/<model_id>")
def get_model(model_id):
    model = model_wb.get_model(model_id)
    if not model:
        return jsonify({"error": f"模型不存在: {model_id}"}), 404
    return jsonify({"id": model.id, "name": model.name, "category": model.category,
                    "sql": model.sql_template, "description": model.description, "params": model.params})

@app.route("/api/models/search")
def search_models():
    kw = request.args.get("q", "")
    return jsonify(model_wb.search(kw))

@app.route("/api/models/analysis-methods")
def analysis_methods():
    return jsonify(ANALYSIS_METHODS)

# ============================================================
# API: 大数据分析
# ============================================================
@app.route("/api/bigdata/graph/fund-flow", methods=["POST"])
def build_fund_flow():
    transactions = request.json.get("transactions", [])
    G = graph_analyzer.build_fund_flow_graph(transactions)
    key_nodes = graph_analyzer.find_key_nodes(G)
    loops = graph_analyzer.find_fund_loops(G)
    return jsonify({
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "key_nodes": key_nodes,
        "fund_loops": loops,
        "graph_data": graph_analyzer.export_for_vis(G),
    })

@app.route("/api/bigdata/graph/supplier", methods=["POST"])
def build_supplier_network():
    bid_data = request.json.get("bid_data", [])
    G = graph_analyzer.build_supplier_graph(bid_data)
    cartels = graph_analyzer.find_bid_cartels(G, min_clique_size=3)
    return jsonify({
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "bid_cartels": cartels,
        "graph_data": graph_analyzer.export_for_vis(G),
    })

@app.route("/api/bigdata/text/wordcloud", methods=["POST"])
def text_wordcloud():
    texts = request.json.get("texts", [])
    freq = text_miner.word_frequency(texts, top_n=50)
    return jsonify([{"word": w, "count": c} for w, c in freq])

@app.route("/api/bigdata/visualize", methods=["POST"])
def visualize():
    data = request.json
    chart_type = data.get("type", "bar")
    chart_data = data.get("data", {})
    title = data.get("title", "")
    
    if chart_type == "bar":
        config = VisualizationHelper.bar_chart(chart_data, title)
    elif chart_type == "pie":
        config = VisualizationHelper.pie_chart(chart_data, title)
    else:
        config = {"error": f"不支持: {chart_type}"}
    return jsonify(config)

# ============================================================
# API: 知识资产
# ============================================================
@app.route("/api/knowledge/cot-chains")
def cot_chains():
    return jsonify(cot_engine.list_chains())

@app.route("/api/knowledge/cot-chains/<name>")
def cot_chain_detail(name):
    chain = cot_engine.get_chain(name)
    if not chain:
        return jsonify({"error": f"思维链不存在: {name}"}), 404
    return jsonify(chain)

@app.route("/api/knowledge/prompts")
def prompts():
    return jsonify(prompt_lib.list_all())

@app.route("/api/knowledge/prompts/<name>")
def prompt_detail(name):
    p = prompt_lib.get(name)
    if not p:
        return jsonify({"error": f"提示词不存在: {name}"}), 404
    return jsonify(p)

@app.route("/api/knowledge/dq-check", methods=["POST"])
def dq_check():
    profile = request.json
    result = dq_checker.run_checks(profile)
    report = dq_checker.generate_report(result)
    return jsonify({"score": result["score"], "grade": result["grade"], "results": result["results"], "report": report})

@app.route("/api/knowledge/methodology")
def methodology_list():
    return jsonify(methodology.list_all())

@app.route("/api/knowledge/methodology/recommend/<audit_type>")
def methodology_recommend(audit_type):
    return jsonify(methodology.recommend_for_audit_type(audit_type))

# ============================================================
# API: RAG知识库查询（新增）
# ============================================================
@app.route("/api/rag/status")
def rag_status():
    """RAG知识库状态"""
    return jsonify(rag_bridge.get_status())

@app.route("/api/rag/search")
def rag_search():
    """RAG知识检索"""
    query = request.args.get("q", "")
    top_k = int(request.args.get("k", 5))
    if not query:
        return jsonify({"error": "缺少查询参数 q"}), 400
    results = rag_bridge.search(query, top_k=top_k)
    return jsonify({
        "query": query,
        "count": len(results),
        "results": results
    })

@app.route("/api/rag/query", methods=["POST"])
def rag_query():
    """RAG完整查询（检索+生成答案）"""
    data = request.json or {}
    query = data.get("query", "")
    top_k = data.get("top_k", 5)
    if not query:
        return jsonify({"error": "缺少query参数"}), 400
    result = rag_bridge.query(query, top_k=top_k)
    return jsonify(result)

# ============================================================
# API: AI报告复核（新增）
# ============================================================
@app.route("/api/review/dimensions")
def review_dimensions():
    """获取复核维度列表"""
    return jsonify({
        "dimensions": review_engine.dimensions,
        "count": len(review_engine.dimensions)
    })

@app.route("/api/review/quick", methods=["POST"])
def review_quick():
    """快速规则检查"""
    data = request.json or {}
    report_text = data.get("text", "")
    if not report_text:
        return jsonify({"error": "缺少text参数"}), 400
    issues = review_engine.rule_based_check(report_text)
    return jsonify({
        "issues_found": len(issues),
        "issues": issues
    })

@app.route("/api/review/comprehensive", methods=["POST"])
def review_comprehensive():
    """综合复核（规则+LLM）"""
    data = request.json or {}
    report_text = data.get("text", "")
    if not report_text:
        return jsonify({"error": "缺少text参数"}), 400
    result = review_engine.comprehensive_review(report_text)
    return jsonify(result)

@app.route("/api/review/fix-suggestions", methods=["POST"])
def review_fix_suggestions():
    """生成修改建议"""
    data = request.json or {}
    report_text = data.get("text", "")
    issues = data.get("issues", [])
    if not issues:
        return jsonify({"error": "缺少issues参数"}), 400
    suggestions = review_engine.generate_fix_suggestions(report_text, issues)
    return jsonify({
        "suggestions": suggestions
    })

# ============================================================
# API: 串标围标检测扩展（新增L8工商关联）
# ============================================================
@app.route("/api/bid/l8/analyze", methods=["POST"])
def bid_l8_analyze():
    """L8工商关联分析"""
    data = request.json or {}
    bidder_names = data.get("bidders", [])
    use_api = data.get("use_api", True)
    
    if not bidder_names or len(bidder_names) < 2:
        return jsonify({"error": "至少需要2家投标人"}), 400
    
    if use_api and bid_detector.tianyancha_key:
        result = bid_detector.l8_full_analysis(bidder_names)
    else:
        # 使用本地替代方案
        docs = data.get("bidder_docs", [])
        result = bid_detector.local_relation_check(docs if docs else 
            [{'name': n} for n in bidder_names])
    
    return jsonify(result)

@app.route("/api/bid/l8/company-info", methods=["POST"])
def bid_company_info():
    """查询企业工商信息"""
    data = request.json or {}
    company_name = data.get("company", "")
    if not company_name:
        return jsonify({"error": "缺少company参数"}), 400
    
    info = bid_detector.query_company_info(company_name)
    return jsonify({
        "company": company_name,
        "found": info is not None,
        "info": info or {}
    })

@app.route("/api/bid/l8/extract", methods=["POST"])
def bid_extract_companies():
    """从文本提取企业名称"""
    data = request.json or {}
    text = data.get("text", "")
    if not text:
        return jsonify({"error": "缺少text参数"}), 400
    
    companies = bid_detector.extract_company_names(text)
    return jsonify({
        "companies": companies,
        "count": len(companies)
    })


# ============================================================
# 五大新技能API（v2.1增强）
# ============================================================

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入五大新技能工具
from skills.penetrating_audit.tool import PenetratingAuditTool
from skills.special_bond_audit.tool import SpecialBondAuditTool
from skills.bim_engineering_audit.tool import BIMEngineeringAuditTool
from skills.audit_risk_portrait.tool import AuditRiskPortraitTool
from skills.dynamic_audit_alert.tool import DynamicAuditAlertTool

penetrating_tool = PenetratingAuditTool()

@app.route("/api/penetrating/fund", methods=["POST"])
def penetrating_fund():
    """资金穿透分析"""
    data = request.json or {}
    transactions = data.get("transactions", [])
    result = penetrating_tool.fund_penetration(transactions)
    result["report"] = penetrating_tool.generate_report(result)
    return jsonify(result)

@app.route("/api/penetrating/project", methods=["POST"])
def penetrating_project():
    """项目穿透分析"""
    data = request.json or {}
    projects = data.get("projects", [])
    result = penetrating_tool.project_penetration(projects)
    result["report"] = penetrating_tool.generate_report(result)
    return jsonify(result)

@app.route("/api/penetrating/supply-chain", methods=["POST"])
def penetrating_supply_chain():
    """供应链穿透分析"""
    data = request.json or {}
    suppliers = data.get("suppliers", [])
    contracts = data.get("contracts", [])
    result = penetrating_tool.supply_chain_penetration(suppliers, contracts)
    result["report"] = penetrating_tool.generate_report(result)
    return jsonify(result)

# 2. 专项债券审计
from skills.special_bond_audit.tool import SpecialBondAuditTool
bond_tool = SpecialBondAuditTool()

@app.route("/api/special-bond/checklist")
def special_bond_checklist():
    """专项债券四环节检查清单"""
    stages = request.args.get("stages", "").split(",") if request.args.get("stages") else None
    result = bond_tool.generate_checklist(stages)
    return jsonify(result)

@app.route("/api/special-bond/analyze", methods=["POST"])
def special_bond_analyze():
    """专项债券项目分析"""
    data = request.json or {}
    result = bond_tool.analyze_bond(data)
    result["report"] = bond_tool.generate_report(result)
    return jsonify(result)

# 3. BIM工程审计
from skills.bim_engineering_audit.tool import BIMEngineeringAuditTool
bim_tool = BIMEngineeringAuditTool()

@app.route("/api/bim/parse-ifc", methods=["POST"])
def bim_parse_ifc():
    """解析IFC工程量"""
    data = request.json or {}
    ifc_data = data.get("ifc_data", {})
    result = bim_tool.parse_ifc_quantities(ifc_data)
    return jsonify(result)

@app.route("/api/bim/compare", methods=["POST"])
def bim_compare():
    """BIM工程量与结算书比对"""
    data = request.json or {}
    bim_qty = data.get("bim_quantities", {})
    settlement = data.get("settlement_data", {})
    result = bim_tool.compare_with_settlement(bim_qty, settlement)
    result["report"] = bim_tool.generate_report(result)
    return jsonify(result)

@app.route("/api/bim/change-orders", methods=["POST"])
def bim_change_orders():
    """变更单分析"""
    data = request.json or {}
    changes = data.get("change_orders", [])
    result = bim_tool.analyze_change_orders(changes)
    return jsonify(result)

# 4. 风险画像
from skills.audit_risk_portrait.tool import AuditRiskPortraitTool
portrait_tool = AuditRiskPortraitTool()

@app.route("/api/risk-portrait/dimensions")
def risk_portrait_dimensions():
    """风险画像维度定义"""
    return jsonify(portrait_tool.DIMENSIONS)

@app.route("/api/risk-portrait/generate", methods=["POST"])
def risk_portrait_generate():
    """生成风险画像"""
    data = request.json or {}
    result = portrait_tool.generate_portrait(data)
    result["report"] = portrait_tool.generate_report(result)
    result["radar_chart"] = portrait_tool.generate_radar_chart_config(result)
    return jsonify(result)

# 5. 动态审计预警
from skills.dynamic_audit_alert.tool import DynamicAuditAlertTool
alert_tool = DynamicAuditAlertTool()

@app.route("/api/alert/rules")
def alert_rules():
    """预警规则列表"""
    return jsonify(alert_tool.ALERT_RULES)

@app.route("/api/alert/evaluate", methods=["POST"])
def alert_evaluate():
    """评估预警"""
    data = request.json or {}
    alerts = alert_tool.evaluate_rules(data)
    return jsonify({
        "alerts": alerts,
        "count": len(alerts),
        "report": alert_tool.generate_alert_report(alerts)
    })

@app.route("/api/alert/trend")
def alert_trend():
    """预警趋势分析"""
    days = request.args.get("days", 30, type=int)
    result = alert_tool.analyze_trend(days)
    return jsonify(result)


if __name__ == "__main__":
    print("=" * 60)
    print("  智析智能体 v2.0 — 审计数据分析平台")
    print("  http://127.0.0.1:5002")
    print("=" * 60)
    print(f"  数据采集模块: {len(DatabaseAdapter.list_supported())} 种数据库适配")
    print(f"  审计模型库:   {len(model_wb.models)} 个SQL模型")
    print(f"  思维链:       {len(cot_engine.list_chains())} 条审计思维链")
    print(f"  提示词库:     {len(prompt_lib.list_all())} 个专业提示词")
    print(f"  方法论框架:   {len(methodology.list_all())} 个")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5002, debug=False)
