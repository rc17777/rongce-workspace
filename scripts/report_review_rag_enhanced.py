#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报告复核 + RAG知识库增强  v1.0
================================
当用户说"复核报告"时自动触发：
  1. 提取报告中的关键审计主题
  2. 对每个主题检索 RAG 知识库（法规/案例/审计要点）
  3. 可选调用智析 API 做格式检查
  4. 生成增强版复核参考意见

用法：
  python report_review_rag_enhanced.py --file <报告路径> [--deep] [--output <输出路径>]
  python report_review_rag_enhanced.py --text "报告内容..." [--deep]

被 AI 调用时：
  from report_review_rag_enhanced import enhanced_review, enhanced_review_text
"""
import sys, io, os, json, re, argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

sys.stdout.reconfigure(encoding='utf-8')

# ============================================================
# 配置
# ============================================================
RAG_PORTS = [5001, 5000]  # 5001优先（5000常被Neo4j占用）
RAG_SERVER = None  # 运行时探测
ZHIXI_SERVER = "http://127.0.0.1:5002"
ROOT = Path(__file__).parent.parent

# 审计关键主题提取规则
TOPIC_PATTERNS = [
    # (正则, 主题名, RAG查询模板)
    (r'(经济责任|离任|任中|自然资源资产)', '经责审计', '经济责任审计 审计要点 常见问题'),
    (r'(专项资金|专款|补助资金|补贴资金)', '专项资金', '专项资金审计 常见问题 管理办法'),
    (r'(预算执行|预算编制|决算|部门预算)', '预算执行', '预算执行审计 关注重点'),
    (r'(政府采购|招标|投标|中标|采购方式)', '采购审计', '政府采购审计 围标串标 常见违规'),
    (r'(工程|竣工|结算|造价|工程量)', '工程审计', '工程竣工决算审计 造价审核要点'),
    (r'(绩效|绩效评价|绩效目标|指标体系)', '绩效评价', '绩效评价 指标体系设计 常见问题'),
    (r'(资产|资产清查|国有资产|固定资产)', '资产清查', '国有资产清查 审计要点'),
    (r'(财政监督|财会监督|监督检查)', '财政监督', '财政监督检查 重点领域 常见违规'),
    (r'(往来款|应收|应付|暂存|暂付)', '往来款清理', '往来款清理 审计方法'),
    (r'(补贴|农机补贴|耕地地力|惠农|产业扶持)', '补贴审计', '补贴资金审计 常见问题'),
    (r'(专项债|政府债务|隐性债务|债券)', '专项债', '专项债审计 管理办法'),
    (r'(内控|内部控制|风险管理)', '内部控制', '内部控制审计 常见缺陷'),
    (r'(社保|养老|医保|就业|民政)', '社保审计', '社保资金审计 常见问题'),
    (r'(教育|学校|营养餐|义务教育)', '教育审计', '教育经费审计 营养餐审计'),
    (r'(三公经费|公务接待|公车|因公出国)', '三公经费', '三公经费审计 过紧日子'),
]

REVIEW_DIMENSIONS = [
    ("政策合规", "检查报告引用的政策法规是否准确、现行有效，结论是否符合最新政策要求"),
    ("数据一致性", "检查报告中的金额、数量、日期是否与附表、取证单一致"),
    ("逻辑完整性", "检查问题→证据→结论的逻辑链条是否完整，有无跳跃"),
    ("表述规范性", "检查专业术语、金额大写、日期格式是否符合公文规范"),
    ("风险覆盖", "检查是否遗漏该类型审计的常见高风险领域"),
]


def detect_rag_server() -> str:
    """自动探测可用的 RAG 服务端口"""
    import urllib.request
    for port in RAG_PORTS:
        url = f"http://127.0.0.1:{port}"
        try:
            # 尝试 POST 到 /api/ask 看是否响应 JSON
            data = json.dumps({"query": "测试", "top_k": 1}).encode("utf-8")
            req = urllib.request.Request(
                f"{url}/api/ask", data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            resp = urllib.request.urlopen(req, timeout=5)
            json.loads(resp.read().decode("utf-8"))
            return url
        except:
            continue
    return None


def check_service(url: str, label: str) -> bool:
    """检查服务是否可达"""
    import urllib.request
    try:
        urllib.request.urlopen(url, timeout=3)
        return True
    except:
        return False


def extract_topics(text: str) -> List[Tuple[str, float, str]]:
    """从报告文本中提取审计主题
    
    Returns: [(主题名, 置信度, RAG查询词), ...]
    """
    topics = []
    seen = set()
    for pattern, topic_name, rag_query in TOPIC_PATTERNS:
        matches = re.findall(pattern, text)
        if matches:
            # 置信度：基于匹配次数和位置
            count = len(matches)
            # 出现在前20%位置的匹配加权
            early_match = bool(re.search(pattern, text[:int(len(text)*0.2)]))
            confidence = min(0.95, count * 0.2 + (0.3 if early_match else 0) + 0.3)
            
            if topic_name not in seen:
                topics.append((topic_name, round(confidence, 2), rag_query))
                seen.add(topic_name)
    
    # 按置信度降序
    topics.sort(key=lambda x: -x[1])
    return topics


def query_rag(query_text: str, top_k: int = 5) -> Dict:
    """调用 RAG 知识库检索"""
    import urllib.request
    global RAG_SERVER
    if not RAG_SERVER:
        RAG_SERVER = detect_rag_server()
    if not RAG_SERVER:
        return {"error": "RAG服务不可用", "answer": "", "sources": []}
    try:
        data = json.dumps({"query": query_text, "top_k": top_k}).encode("utf-8")
        req = urllib.request.Request(
            f"{RAG_SERVER}/api/ask",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e), "answer": "", "sources": []}


def query_zhixi_review(text: str, mode: str = "quick") -> Dict:
    """调用智析报告复核 API"""
    import urllib.request
    try:
        url = f"{ZHIXI_SERVER}/api/review/{mode}"
        data = json.dumps({"text": text[:50000]}).encode("utf-8")  # 限长
        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        resp = urllib.request.urlopen(req, timeout=60)
        return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e), "issues": []}


def read_report(file_path: str) -> str:
    """读取报告文件（支持 .txt .md .docx）"""
    fp = Path(file_path)
    if not fp.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    ext = fp.suffix.lower()
    if ext in ('.txt', '.md', '.json'):
        with open(fp, 'r', encoding='utf-8') as f:
            return f.read()
    elif ext == '.docx':
        try:
            from docx import Document
            doc = Document(fp)
            return '\n'.join([p.text for p in doc.paragraphs if p.text.strip()])
        except ImportError:
            raise RuntimeError("需要安装 python-docx: pip install python-docx")
    else:
        # 尝试当文本读
        try:
            with open(fp, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            raise RuntimeError(f"不支持的文件格式: {ext}")


def enhanced_review(report_path: str, deep: bool = False, 
                    use_zhixi: bool = True, use_rag: bool = True) -> Dict:
    """
    增强复核入口（文件路径版）
    
    Returns:
        {
            'report_path': str,
            'report_text': str (前2000字),
            'topics': [...],
            'rag_knowledge': [...],
            'zhixi_issues': [...],
            'review_advice': str,
            'services_status': {...},
        }
    """
    # 读取报告
    report_text = read_report(report_path)
    report_name = Path(report_path).stem
    
    # 检查服务
    rag_url = detect_rag_server() if use_rag else None
    services = {
        'rag': rag_url is not None,
        'rag_url': rag_url or '',
        'zhixi': check_service(f"{ZHIXI_SERVER}/", "智析"),
    }
    
    global RAG_SERVER
    if rag_url:
        RAG_SERVER = rag_url
    
    # Step 1: 提取审计主题
    topics = extract_topics(report_text)
    
    # Step 2: 对每个主题检索RAG
    rag_results = []
    if use_rag and services['rag']:
        for topic_name, confidence, rag_query in topics[:5]:  # 最多查5个主题
            resp = query_rag(rag_query, top_k=3)
            rag_results.append({
                'topic': topic_name,
                'confidence': confidence,
                'query': rag_query,
                'answer': resp.get('answer', '')[:500],
                'sources': [s.get('file', '') for s in resp.get('sources', [])[:3]],
            })
    elif use_rag and not services['rag']:
        rag_results.append({'error': 'RAG服务不可用 (127.0.0.1:5000)'})
    
    # Step 3: 智析复核
    zhixi_result = {}
    if use_zhixi and services['zhixi']:
        mode = "comprehensive" if deep else "quick"
        zhixi_result = query_zhixi_review(report_text, mode=mode)
    elif use_zhixi and not services['zhixi']:
        zhixi_result = {'error': '智析服务不可用 (127.0.0.1:5002)'}
    
    # Step 4: 生成复核建议
    advice = build_review_advice(report_name, topics, rag_results, zhixi_result, deep)
    
    return {
        'report_path': str(report_path),
        'report_name': report_name,
        'report_text_preview': report_text[:2000],
        'total_chars': len(report_text),
        'topics': [{'name': t[0], 'confidence': t[1]} for t in topics],
        'rag_knowledge': rag_results,
        'zhixi_issues': zhixi_result.get('issues', []),
        'review_advice': advice,
        'services_status': services,
        'timestamp': datetime.now().isoformat(),
    }


def enhanced_review_text(text: str, label: str = "在线报告", 
                         deep: bool = False, use_zhixi: bool = True, 
                         use_rag: bool = True) -> Dict:
    """
    增强复核入口（文本版，用于聊天中直接贴内容）
    """
    rag_url = detect_rag_server() if use_rag else None
    services = {
        'rag': rag_url is not None,
        'rag_url': rag_url or '',
        'zhixi': check_service(f"{ZHIXI_SERVER}/", "智析"),
    }
    
    global RAG_SERVER
    if rag_url:
        RAG_SERVER = rag_url
    
    topics = extract_topics(text)
    
    rag_results = []
    if use_rag and services['rag']:
        for topic_name, confidence, rag_query in topics[:5]:
            resp = query_rag(rag_query, top_k=3)
            rag_results.append({
                'topic': topic_name,
                'confidence': confidence,
                'query': rag_query,
                'answer': resp.get('answer', '')[:500],
                'sources': [s.get('file', '') for s in resp.get('sources', [])[:3]],
            })
    elif use_rag and not services['rag']:
        rag_results.append({'error': 'RAG服务不可用'})
    
    zhixi_result = {}
    if use_zhixi and services['zhixi']:
        mode = "comprehensive" if deep else "quick"
        zhixi_result = query_zhixi_review(text, mode=mode)
    elif use_zhixi and not services['zhixi']:
        zhixi_result = {'error': '智析服务不可用'}
    
    advice = build_review_advice(label, topics, rag_results, zhixi_result, deep)
    
    return {
        'report_name': label,
        'total_chars': len(text),
        'topics': [{'name': t[0], 'confidence': t[1]} for t in topics],
        'rag_knowledge': rag_results,
        'zhixi_issues': zhixi_result.get('issues', []),
        'review_advice': advice,
        'services_status': services,
        'timestamp': datetime.now().isoformat(),
    }


def build_review_advice(report_name: str, topics: List, 
                        rag_results: List[Dict], 
                        zhixi_result: Dict,
                        deep: bool) -> str:
    """生成最终复核建议"""
    lines = [
        f"## 📋 报告复核意见（RAG增强版）",
        f"",
        f"**报告**: {report_name}",
        f"**复核时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**复核深度**: {'深度复核(15维)' if deep else '快速复核'}",
        f"",
    ]
    
    # 识别的审计主题
    if topics:
        lines.append("### 🔍 识别到的审计主题")
        for i, (topic_name, confidence, _) in enumerate(topics[:8], 1):
            bar = '█' * int(confidence * 10) + '░' * (10 - int(confidence * 10))
            lines.append(f"  {i}. {topic_name} [{bar}] {confidence:.0%}")
        lines.append("")
    
    # RAG 知识检索结果
    rag_ok = [r for r in rag_results if 'error' not in r and r.get('answer')]
    if rag_ok:
        lines.append("### 📚 RAG知识库参考")
        for r in rag_ok:
            lines.append(f"#### {r['topic']}")
            lines.append(f"  {r['answer'][:300]}")
            if r.get('sources'):
                lines.append(f"  📄 来源: {', '.join(r['sources'][:3])}")
            lines.append("")
    elif rag_results and 'rag' in str(rag_results[0].get('error', '')):
        lines.append(f"### ⚠️ RAG服务不可用，跳过知识检索")
        lines.append("")
    
    # 智析复核结果
    issues = zhixi_result.get('issues', [])
    if isinstance(issues, list) and issues:
        lines.append(f"### 🔬 智析复核发现 ({len(issues)}个问题)")
        for i, issue in enumerate(issues, 1):
            msg = issue.get('message', str(issue))
            severity = issue.get('severity', '')
            icon = {'P0': '🔴', 'P1': '🟡', 'P2': '🟢'}.get(severity, '•')
            lines.append(f"  {icon} {i}. {msg}")
        lines.append("")
    elif 'error' in zhixi_result:
        lines.append(f"### ⚠️ 智析复核跳过（{zhixi_result.get('error', '服务不可用')})")
        lines.append("")
    
    # 复核维度逐一说明
    lines.append("### 🎯 复核维度覆盖")
    for dim, desc in REVIEW_DIMENSIONS:
        checked = "✅" if any(
            any(kw in str(r.get('answer', '')).lower() for kw in dim[:2]) 
            for r in rag_ok
        ) else "⚠️ 建议关注"
        lines.append(f"  {checked} **{dim}**: {desc}")
    lines.append("")
    
    # 建议操作
    lines.append("### 💡 建议操作")
    if deep:
        lines.append("  1. 逐项核实智析标记的P0/P1问题")
        lines.append("  2. 对照RAG知识库中的法规/案例，确认结论合规性")
        lines.append("  3. 金额数据与取证单、附表交叉比对")
        lines.append("  4. 关键结论处标注数据来源和计算方法")
    else:
        lines.append("  1. 核实智析标记的格式/一致性等低级错误")
        lines.append("  2. RAG知识库提示的审计要点，对照检查报告是否覆盖")
        lines.append("  3. 如需深度复核，使用 `--deep` 参数重新运行")
    
    lines.append("")
    lines.append("---")
    lines.append("*由 RAG增强复核引擎自动生成*")
    
    return '\n'.join(lines)


def format_for_ai(result: Dict) -> str:
    """将复核结果格式化为AI可直接使用的Markdown"""
    return result['review_advice']


# ============================================================
# CLI
# ============================================================
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='报告复核 RAG增强版')
    parser.add_argument('--file', '-f', help='报告文件路径')
    parser.add_argument('--text', '-t', help='直接输入报告文本')
    parser.add_argument('--deep', action='store_true', help='深度复核模式')
    parser.add_argument('--output', '-o', help='输出JSON文件路径')
    parser.add_argument('--json', action='store_true', help='JSON格式输出')
    parser.add_argument('--no-rag', action='store_true', help='跳过RAG检索')
    parser.add_argument('--no-zhixi', action='store_true', help='跳过智析复核')
    
    args = parser.parse_args()
    
    if not args.file and not args.text:
        parser.print_help()
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("  报告复核 RAG增强版 v1.0")
    print("=" * 60 + "\n")
    
    if args.file:
        print(f"📄 文件: {args.file}")
        result = enhanced_review(
            args.file, 
            deep=args.deep,
            use_zhixi=not args.no_zhixi,
            use_rag=not args.no_rag,
        )
    else:
        print(f"📝 文本输入 ({len(args.text)} 字符)")
        result = enhanced_review_text(
            args.text,
            deep=args.deep,
            use_zhixi=not args.no_zhixi,
            use_rag=not args.no_rag,
        )
    
    # 输出
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result['review_advice'])
        print(f"\n服务状态: RAG={'✅' if result['services_status'].get('rag') else '❌'} | "
              f"智析={'✅' if result['services_status'].get('zhixi') else '❌'}")
    
    # 保存JSON
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n📁 已保存: {args.output}")
    
    print()
