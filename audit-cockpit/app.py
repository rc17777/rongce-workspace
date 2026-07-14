#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
融策审计驾驶舱 — Flask Web 应用
项目级图形化审计工作界面：可点 · 可查 · 可问 · 可追溯
"""
import sys, os, json, hashlib, time, requests
sys.stdout.reconfigure(encoding='utf-8')

from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime

# 导入数据管理模块
from modules.data_manager import data_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = 'rongce-audit-cockpit-2026'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB 上传限制

# 注册蓝图
app.register_blueprint(data_bp, url_prefix='/data')

# ========== 模拟项目数据 ==========
MOCK_PROJECT = {
    "name": "天府广场独立商业项目",
    "code": "RC-2026-A001",
    "client": "成都轨道资源经营管理有限公司",
    "period": "2024.7 - 2025.12",
    "status": "进行中",
    "progress": 72,
    "team": {"cpa": 2, "assistant": 4, "ai_agent": 7},
    "kpi": {
        "total_assets": "12,856.32万",
        "total_revenue": "4,231.68万",
        "total_cost": "3,562.14万",
        "net_profit": "669.54万",
    },
    "anomalies": [
        {"level": "high", "desc": "停车费收入月波动>30%", "account": "其他业务收入-停车费", "period": "2024.10-2025.02"},
        {"level": "high", "desc": "商户租金拖欠6户共83.5万", "account": "应收账款-租金", "period": "2025.03"},
        {"level": "mid", "desc": "351次手动放行无记录", "account": "停车场收费系统", "period": "全期"},
        {"level": "mid", "desc": "物业用房违规占用", "account": "固定资产", "period": "2025.06"},
        {"level": "low", "desc": "67人三人行变1带多", "account": "管理费用-差旅", "period": "多次"},
    ],
    "balance_sheet": [
        {"code": "1001", "name": "货币资金", "begin": 2156.80, "end": 1834.25, "change": -322.55, "change_pct": -14.96, "flag": None},
        {"code": "1122", "name": "应收账款", "begin": 892.35, "end": 1345.62, "change": 453.27, "change_pct": 50.80, "flag": "high"},
        {"code": "1221", "name": "其他应收款", "begin": 456.20, "end": 523.15, "change": 66.95, "change_pct": 14.68, "flag": "mid"},
        {"code": "1405", "name": "存货", "begin": 312.50, "end": 298.30, "change": -14.20, "change_pct": -4.54, "flag": None},
        {"code": "1601", "name": "固定资产", "begin": 5823.40, "end": 5912.67, "change": 89.27, "change_pct": 1.53, "flag": None},
        {"code": "1701", "name": "无形资产", "begin": 1245.60, "end": 1189.33, "change": -56.27, "change_pct": -4.52, "flag": None},
        {"code": "2001", "name": "短期借款", "begin": 2000.00, "end": 1500.00, "change": -500.00, "change_pct": -25.00, "flag": None},
        {"code": "2202", "name": "应付账款", "begin": 1256.80, "end": 1658.42, "change": 401.62, "change_pct": 31.96, "flag": "high"},
        {"code": "4001", "name": "实收资本", "begin": 5000.00, "end": 5000.00, "change": 0, "change_pct": 0, "flag": None},
    ],
    "evidence_chain": [
        {
            "finding": "应收账款增长50.8%异常",
            "source": "余额表-2025.12",
            "trace": [
                {"step": "1. 余额表显示应收账款期末1,345.62万", "doc": "余额表-2025.12", "page": "附表2 P3"},
                {"step": "2. 明细账显示6户商户租金拖欠83.5万", "doc": "应收明细账-商户", "page": "附件1 Sheet2"},
                {"step": "3. 租赁合同显示该6户租期到期未续", "doc": "租赁合同台账", "page": "合同编号ZC-2024-031~036"},
                {"step": "4. 催缴记录缺失——未按合同约定30天内发函", "doc": "催缴记录", "page": "无"},
            ],
            "conclusion": "应收账款异常增长主要由租金拖欠导致，催缴程序存在合规缺失"
        },
    ],
    "workpapers": [
        {"name": "底稿A-货币资金", "status": "done", "reviewer": "CPA-张", "issues": 0},
        {"name": "底稿B-应收账款", "status": "review", "reviewer": "待复核", "issues": 3},
        {"name": "底稿C-收入确认", "status": "doing", "reviewer": "AI-数据侦察Agent", "issues": 2},
        {"name": "底稿D-成本费用", "status": "doing", "reviewer": "AI-合同猎犬Agent", "issues": 1},
        {"name": "底稿E-固定资产", "status": "todo", "reviewer": "-", "issues": 0},
        {"name": "底稿F-关联交易", "status": "todo", "reviewer": "-", "issues": 0},
    ],
    "ai_timeline": [
        {"time": "06-25 14:30", "agent": "数据侦察Agent", "action": "完成余额表数据采集，标记3个异常科目"},
        {"time": "06-25 15:45", "agent": "合同猎犬Agent", "action": "扫描142份租赁合同，发现6份到期未续"},
        {"time": "06-25 16:20", "agent": "投标猎手Agent", "action": "检测停车场外包招标，3家公司元数据一致"},
        {"time": "06-25 17:00", "agent": "法规审查Agent", "action": "对比成国资发〔2025〕15号，标记4处合规风险"},
        {"time": "06-25 17:35", "agent": "底稿工匠Agent", "action": "完成底稿B-应收账款初稿"},
        {"time": "06-25 18:10", "agent": "报告写手Agent", "action": "生成应收账款异常段落"},
        {"time": "06-25 18:55", "agent": "复核哨兵Agent", "action": "复核底稿B，发现3处勾稽不一致"},
    ],
    "risk_radar": {
        "labels": ["收入确认", "应收账款", "成本费用", "固定资产", "关联交易", "合同管理", "资金管理", "税务合规"],
        "scores": [78, 92, 45, 38, 25, 85, 40, 30],
    }
}


# ========== 路由 ==========
@app.route('/')
def index():
    return render_template('dashboard.html', project=MOCK_PROJECT)

@app.route('/financial')
def financial():
    return render_template('financial.html', project=MOCK_PROJECT)

@app.route('/evidence')
def evidence():
    return render_template('evidence.html', project=MOCK_PROJECT)

@app.route('/workpapers')
def workpapers():
    return render_template('workpapers.html', project=MOCK_PROJECT)

@app.route('/ai-assistant')
def ai_assistant():
    return render_template('ai_assistant.html', project=MOCK_PROJECT)

# ========== API ==========
@app.route('/api/project')
def api_project():
    return jsonify(MOCK_PROJECT)

@app.route('/api/balance_sheet')
def api_balance():
    return jsonify(MOCK_PROJECT['balance_sheet'])

@app.route('/api/anomalies')
def api_anomalies():
    return jsonify(MOCK_PROJECT['anomalies'])

@app.route('/api/timeline')
def api_timeline():
    return jsonify(MOCK_PROJECT['ai_timeline'])

@app.route('/api/evidence/<finding_id>')
def api_evidence_detail(finding_id):
    for f in MOCK_PROJECT['evidence_chain']:
        if hashlib.md5(f['finding'].encode()).hexdigest()[:8] == finding_id:
            return jsonify(f)
    return jsonify({"error": "not found"}), 404

@app.route('/api/ask', methods=['POST'])
def api_ask():
    """AI问答——接入RAG知识库 + DeepSeek"""
    data = request.json
    question = data.get('question', '')
    context = data.get('context', '')
    
    # 1. 查询RAG知识库
    from modules.rag_bridge import get_knowledge_context, rag_status
    kb_context = get_knowledge_context(question) if rag_status() else None
    
    # 2. 尝试调用DeepSeek API（如果可用）
    deepseek_answer = call_deepseek(question, context, kb_context)
    
    if deepseek_answer:
        sources = ["RAG审计知识库 (1,235份法规案例)"]
        if kb_context:
            sources.append("知识库匹配chunks已注入上下文")
        return jsonify({
            "answer": deepseek_answer,
            "sources": sources,
            "rag_available": True,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    # 3. 回退：使用RAG知识库生成回答
    if kb_context:
        answer = f"📚 基于审计知识库检索结果：\n\n{kb_context[:1500]}\n\n💡 以上为知识库中匹配度最高的内容，如需深度分析请确保DeepSeek API可用。"
        return jsonify({
            "answer": answer,
            "sources": ["RAG审计知识库"],
            "rag_available": True,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    # 4. 完全离线：模板回复
    return jsonify({
        "answer": f"⚠️ RAG知识库和AI服务均未连接。\n\n关于「{question}」——请先启动RAG服务(localhost:5000)，或配置DeepSeek API Key。\n\n当前为离线模式，只能使用预置的模板数据。",
        "sources": [],
        "rag_available": False,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


@app.route('/api/rag/status')
def api_rag_status():
    """检查RAG和AI服务状态"""
    from modules.rag_bridge import rag_status
    return jsonify({
        "rag": rag_status(),
        "rag_url": "http://localhost:5000",
        "deepseek": bool(os.environ.get('DEEPSEEK_API_KEY')),
    })


def call_deepseek(question, context, kb_context):
    """调用DeepSeek API"""
    import requests
    api_key = os.environ.get('DEEPSEEK_API_KEY', 'sk-dbc61b4ba6a64222a2621d646f15234c')
    if not api_key:
        return None
    
    system_prompt = "你是融策会计师事务所的AI审计助手。回答必须专业、准确、有据可查。"
    if kb_context:
        system_prompt += f"\n\n请参考以下审计知识库内容回答：\n{kb_context[:2000]}"
    if context:
        system_prompt += f"\n\n当前审计上下文：{context}"
    
    try:
        resp = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                "temperature": 0.3,
                "max_tokens": 1500,
            },
            timeout=30
        )
        if resp.status_code == 200:
            return resp.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"DeepSeek API error: {e}")
    return None

if __name__ == '__main__':
    print("\n🛩️  融策审计驾驶舱启动: http://localhost:5001")
    print("   按 Ctrl+C 停止\n")
    app.run(host='0.0.0.0', port=5001, debug=False)
