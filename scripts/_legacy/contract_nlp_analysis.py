"""
天府广场项目合同NLP深度分析
===========================
分析维度:
1. PDF合同文本提取与台账交叉比对
2. 关键条款NLP抽取(金额/期限/违约责任/履约担保等)
3. 风险标识与一致性检查
4. 合同类型聚类分析
"""
import pandas as pd
import numpy as np
import re
import os
import json
import fitz  # pymupdf
from collections import defaultdict, Counter
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 配置
# ============================================================
CONTRACT_DIR = r"C:\Users\scrccpa\Desktop\成都轨道资源资料\业主发送资料\天府广场项目2026年专项审计资料清单（第一批）\1合同协议"
LEDGER_PATH = r"C:\Users\scrccpa\Desktop\成都资源公司=4.30\天府广场合同台账-2024-2025.xlsx"
OUTPUT_DIR = r"D:\openclaw-workspace\output\contract_analysis"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# Phase 1: 提取PDF文本
# ============================================================
def extract_pdf_text(pdf_path):
    """使用pymupdf提取PDF文本"""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        return f"[ERROR: {str(e)}]"

def extract_all_pdfs(base_dir):
    """遍历所有子目录提取PDF"""
    pdfs = {}
    for root, dirs, files in os.walk(base_dir):
        for f in files:
            if f.lower().endswith('.pdf'):
                full_path = os.path.join(root, f)
                category = os.path.basename(root)
                print(f"  提取: [{category}] {f[:80]}...")
                text = extract_pdf_text(full_path)
                pdfs[full_path] = {
                    'filename': f,
                    'category': category,
                    'text': text,
                    'path': full_path,
                    'size_kb': round(os.path.getsize(full_path)/1024, 1),
                    'char_count': len(text)
                }
    return pdfs

# ============================================================
# Phase 2: 读取合同台账
# ============================================================
def load_ledger(path):
    df = pd.read_excel(path, header=None)
    headers_raw = df.iloc[0].tolist()
    # Row 1 is sub-header or empty, data starts from row 2
    data = df.iloc[2:].copy()
    data.columns = [
        'seq', 'contract_name', 'contract_no', 'sign_date', 'counterparty',
        'counterparty_contact', 'scope', 'contract_period', 'rights_duties',
        'expired', 'total_price', 'total_price_ex_tax', 'termination_early',
        'settled_amount', 'payment_method', 'has_guarantee', 'guarantee_amount',
        'fee_category', 'contract_type'
    ]
    data = data.reset_index(drop=True)
    return data

# ============================================================
# Phase 3: NLP条款抽取
# ============================================================
class ContractNLPAnalyzer:
    """合同NLP分析器"""
    
    # 关键条款模式
    PATTERNS = {
        'payment_amount': [
            r'(?:合同(?:总价|金额|含税总价|价格)|含税(?:总价|金额|合同)).*?(\d[\d,.]+\s*(?:万元|元|亿))',
            r'(?:不含税.*?(?:价格|金额|总价)).*?(\d[\d,.]+\s*(?:万元|元|亿))',
            r'合同总金额.*?(\d[\d,.]+\s*(?:万元|元|亿))',
            r'¥\s*(\d[\d,.]+)',
            r'人民币\s*(\d[\d,.]+)\s*(?:元|万元)',
        ],
        'payment_method': [
            r'(?:支付|付款|结算)\s*(?:方式|方法).*?[：:]\s*(.+?)(?:[。；\n]|$)',
            r'(?:按[月度季度年].*?(?:支付|结算|付款))',
            r'(?:据实.*?(?:结算|支付|月结))',
            r'(?:一次性.*?(?:支付|付清))',
        ],
        'contract_period': [
            r'(?:合同期|合同期限|服务期|维保期|租赁期).*?[：:]\s*(.+?)(?:[。；\n]|$)',
            r'(?:自|从)\s*(\d{4}[\d./年-]+\d{1,2}[\d日月]*)\s*(?:起|至|到|止).*?(?:至|到|止)\s*(\d{4}[\d./年-]+\d{1,2}[\d日月]*)',
            r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日.*?(?:至|到|-).*?(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日',
        ],
        'termination': [
            r'(?:提前.*?(?:终止|解除|退场))',
            r'(?:合同.*?(?:解除|终止).*?(?:条件|情形))',
            r'(?:违约.*?(?:解除|终止).*?合同)',
        ],
        'default_liability': [
            r'(?:违约责任|违约金).*?[：:]\s*(.+?)(?:[。；]|$)',
            r'违约金.*?(?:按|为|标准).*?(.+?)(?:[。；]|$)',
            r'(?:赔偿.*?(?:损失|金额|责任))',
        ],
        'guarantee': [
            r'(?:履约.*?(?:保证金|担保|保函))',
            r'(?:保证金).*?(\d[\d,.]+\s*(?:万元|元))',
            r'(?:担保.*?(?:方式|金额))',
        ],
        'insurance': [
            r'(?:保险.*?(?:购买|承担|负责))',
            r'(?:公众责任险|财产险|意外险)',
        ],
        'dispute_resolution': [
            r'(?:争议.*?(?:解决|处理|管辖))',
            r'(?:仲裁|诉讼).*?(?:法院|机构|委员会)',
            r'(?:管辖.*?法院)',
        ],
        'confidentiality': [
            r'(?:保密.*?(?:条款|义务|责任))',
            r'(?:商业秘密|保密信息)',
        ],
        'force_majeure': [
            r'不可抗力',
        ],
        'price_adjustment': [
            r'(?:价格.*?(?:调整|变动|变更))',
            r'(?:不因.*?(?:市场|政策).*?(?:调整|变动))',
        ],
        'contract_type_clause': [
            r'(?:包干|据实结算|固定单价|固定总价)',
        ],
        'tripartite': [
            r'(?:三方|丙方|甲乙丙)',
        ],
    }
    
    def __init__(self):
        self.results = {}
    
    def analyze(self, contract_id, text):
        """对单份合同进行NLP分析"""
        result = {
            'contract_id': contract_id,
            'text_length': len(text),
            'clauses_found': {},
            'risk_flags': [],
            'amounts_extracted': [],
            'dates_extracted': [],
        }
        
        for clause_type, patterns in self.PATTERNS.items():
            matches = []
            for pattern in patterns:
                found = re.findall(pattern, text, re.IGNORECASE)
                if found:
                    if isinstance(found[0], tuple):
                        matches.extend([' '.join(f) for f in found])
                    else:
                        matches.extend(found)
            result['clauses_found'][clause_type] = matches[:5]  # Keep top 5
        
        # 金额提取
        amounts = re.findall(r'(\d[\d,.]*)\s*(?:万元|元|亿)', text)
        for a in amounts:
            try:
                val = float(a.replace(',', ''))
                if val > 100:  # Filter noise
                    result['amounts_extracted'].append(val)
            except:
                pass
        
        # 日期提取
        dates = re.findall(r'(\d{4})[年./-](\d{1,2})[月./-](\d{1,2})日?', text)
        result['dates_extracted'] = dates[:20]
        
        # 风险标识
        self._flag_risks(result, text)
        
        return result
    
    def _flag_risks(self, result, text):
        """风险条款识别"""
        risks = []
        
        # 检查关键条款缺失
        clause_check = {
            'payment_method': '缺少明确付款方式条款',
            'default_liability': '缺少明确违约责任条款',
            'guarantee': '缺少履约担保条款',
            'dispute_resolution': '缺少争议解决条款',
            'force_majeure': '缺少不可抗力条款',
            'confidentiality': '缺少保密条款',
        }
        for key, warning in clause_check.items():
            if not result['clauses_found'].get(key):
                risks.append({'type': 'missing_clause', 'detail': warning})
        
        # 不利条款检查
        if '不因市场价格' in text and '调整' in text:
            risks.append({'type': 'unfavorable_term', 'detail': '价格锁定条款：合同期内不因市场价格调整，可能对乙方不利'})
        
        if re.search(r'包括.*?但不限于.*?一切费用', text):
            risks.append({'type': 'unfavorable_term', 'detail': '费用包干范围过宽："包括但不限于一切费用"'})
        
        if '实际开始时间以甲方书面通知为准' in text:
            risks.append({'type': 'unfavorable_term', 'detail': '进场时间由甲方单方决定，合同实际履行期不确定'})
        
        if '实际进场已甲方书面为准' in text or '实际进场以甲方书面通知为准' in text:
            risks.append({'type': 'schedule_risk', 'detail': '合同开始时间存在单方决定风险'})
        
        # 三方协议复杂性
        if re.search(r'(?:丙方|三方|甲乙丙)', text):
            risks.append({'type': 'tripartite', 'detail': '三方协议，法律关系复杂，需关注各方权利义务划分'})
        
        # 超长期合同
        long_term = re.findall(r'(?:20\s*年|租赁期.*?20)', text)
        if long_term:
            risks.append({'type': 'long_term', 'detail': '超长期合同(20年)，市场变化风险大'})
        
        result['risk_flags'] = risks


# ============================================================
# Phase 4: 台账交叉比对
# ============================================================
def match_contract_to_ledger(pdf_name, ledger_df):
    """将PDF文件名与台账记录匹配"""
    # 归一化文件名用于匹配
    name_clean = pdf_name.replace('.pdf', '').replace('-扫描件', '').strip()
    
    for idx, row in ledger_df.iterrows():
        ledger_name = str(row['contract_name']) if pd.notna(row['contract_name']) else ''
        ledger_no = str(row['contract_no']) if pd.notna(row['contract_no']) else ''
        
        # 合同编号匹配
        if ledger_no and ledger_no != 'nan':
            if ledger_no in name_clean:
                return idx
        # 合同名称关键词匹配
        if ledger_name and len(ledger_name) > 5:
            # Extract key parts from ledger name
            key_parts = re.findall(r'[\u4e00-\u9fa5]{3,}', ledger_name)
            match_count = sum(1 for kp in key_parts if kp in name_clean)
            if match_count >= 2:
                return idx
    
    return None

def cross_reference(pdfs, ledger_df):
    """交叉比对"""
    results = []
    matched_indices = set()
    
    for path, info in pdfs.items():
        fname = info['filename']
        match_idx = match_contract_to_ledger(fname, ledger_df)
        
        row = {}
        if match_idx is not None:
            matched_indices.add(match_idx)
            lr = ledger_df.iloc[match_idx]
            row = {
                'pdf_file': fname,
                'category': info['category'],
                'matched': True,
                'ledger_seq': lr['seq'],
                'ledger_name': lr['contract_name'],
                'ledger_no': lr['contract_no'],
                'ledger_counterparty': lr['counterparty'],
                'ledger_price': lr['total_price'],
                'ledger_type': lr['contract_type'],
                'ledger_period': lr['contract_period'],
                'pdf_size_kb': info['size_kb'],
                'pdf_chars': info['char_count'],
            }
        else:
            row = {
                'pdf_file': fname,
                'category': info['category'],
                'matched': False,
                'ledger_seq': None,
                'ledger_name': None,
                'ledger_no': None,
                'ledger_counterparty': None,
                'ledger_price': None,
                'ledger_type': None,
                'ledger_period': None,
                'pdf_size_kb': info['size_kb'],
                'pdf_chars': info['char_count'],
            }
        results.append(row)
    
    # 台账中未匹配的记录
    unmatched_ledger = []
    for idx, row in ledger_df.iterrows():
        if idx not in matched_indices and pd.notna(row['contract_name']):
            unmatched_ledger.append({
                'seq': row['seq'],
                'name': row['contract_name'],
                'no': row['contract_no'],
                'counterparty': row['counterparty'],
                'type': row['contract_type'],
                'reason': 'PDF文件缺失'
            })
    
    return results, unmatched_ledger


# ============================================================
# Main Analysis Pipeline
# ============================================================
print("=" * 80)
print("天府广场项目合同NLP深度分析")
print("=" * 80)

# Step 1: 提取所有PDF
print("\n[Step 1] PDF文本提取...")
pdfs = extract_all_pdfs(CONTRACT_DIR)
print(f"共提取 {len(pdfs)} 份合同PDF\n")

# Step 2: 加载台账
print("[Step 2] 加载合同台账...")
ledger = load_ledger(LEDGER_PATH)
print(f"台账记录数: {len(ledger)}")

# Step 3: 交叉比对
print("\n[Step 3] PDF-台账交叉比对...")
cross_results, unmatched_ledger = cross_reference(pdfs, ledger)
cross_df = pd.DataFrame(cross_results)
matched_count = cross_df['matched'].sum()
print(f"  匹配成功: {matched_count}/{len(pdfs)}")
print(f"  台账未匹配(PDF缺失): {len(unmatched_ledger)}")

# Step 4: NLP分析每份PDF
print("\n[Step 4] NLP条款分析...")
analyzer = ContractNLPAnalyzer()
nlp_results = {}
for path, info in pdfs.items():
    fname = info['filename']
    print(f"  分析: {fname[:60]}...")
    result = analyzer.analyze(fname, info['text'])
    result['category'] = info['category']
    result['size_kb'] = info['size_kb']
    nlp_results[fname] = result

# Step 5: 汇总分析
print("\n[Step 5] 汇总分析...")

# 5a: 风险汇总
all_risks = []
for fname, result in nlp_results.items():
    for risk in result['risk_flags']:
        all_risks.append({
            'contract': fname,
            'category': result['category'],
            'risk_type': risk['type'],
            'detail': risk['detail'],
        })
risk_df = pd.DataFrame(all_risks)

# 5b: 条款覆盖度
clause_coverage = defaultdict(lambda: {'found': 0, 'total': len(nlp_results)})
for fname, result in nlp_results.items():
    for clause_type, matches in result['clauses_found'].items():
        if matches:
            clause_coverage[clause_type]['found'] += 1

# 5c: 合同类型分布
type_dist = defaultdict(list)
for fname, result in nlp_results.items():
    type_dist[result['category']].append(fname)

# 5d: 金额汇总
amount_summary = []
for fname, result in nlp_results.items():
    if result['amounts_extracted']:
        amount_summary.append({
            'contract': fname,
            'category': result['category'],
            'max_amount': max(result['amounts_extracted']),
            'amount_count': len(result['amounts_extracted']),
            'amounts': sorted(result['amounts_extracted'], reverse=True)[:5]
        })

# ============================================================
# 生成报告
# ============================================================
report_lines = []
report_lines.append("=" * 100)
report_lines.append("天府广场项目合同NLP深度分析报告")
report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
report_lines.append("=" * 100)

# 1. 基本概况
report_lines.append("\n\n一、基本概况")
report_lines.append("-" * 60)
report_lines.append(f"  合同PDF总数: {len(pdfs)}")
report_lines.append(f"  合同台账记录数: {len(ledger)}")
report_lines.append(f"  PDF-台账匹配数: {matched_count}")
report_lines.append(f"  台账缺失PDF数: {len(unmatched_ledger)}")

report_lines.append(f"\n  合同分类:")
for cat, files in sorted(type_dist.items()):
    report_lines.append(f"    [{cat}] {len(files)}份: {', '.join(f[:40] for f in files[:3])}{'...' if len(files)>3 else ''}")

# 2. 交叉比对结果
report_lines.append("\n\n二、PDF-台账交叉比对详情")
report_lines.append("-" * 60)
report_lines.append("\n  【已匹配合同】")
for _, row in cross_df[cross_df['matched']].iterrows():
    report_lines.append(f"    ✅ {row['pdf_file'][:50]}")
    report_lines.append(f"       台账编号: {row['ledger_no']} | 相对方: {row['ledger_counterparty']}")
    report_lines.append(f"       台账金额: {row['ledger_price']} | 类型: {row['ledger_type']}")

report_lines.append("\n  【未匹配PDF(台账中无对应记录)】")
for _, row in cross_df[~cross_df['matched']].iterrows():
    report_lines.append(f"    ❌ {row['pdf_file'][:80]}  (类别: {row['category']})")

report_lines.append("\n  【台账中有记录但PDF缺失】")
for item in unmatched_ledger:
    report_lines.append(f"    ⚠️ #{item['seq']} {item['name'][:60]}")
    report_lines.append(f"       编号: {item['no']} | 相对方: {item['counterparty']} | 类型: {item['type']}")

# 3. NLP条款覆盖度
report_lines.append("\n\n三、关键条款覆盖度分析")
report_lines.append("-" * 60)
clause_labels = {
    'payment_amount': '金额条款',
    'payment_method': '付款方式',
    'contract_period': '合同期限',
    'termination': '提前终止条款',
    'default_liability': '违约责任',
    'guarantee': '履约担保',
    'insurance': '保险条款',
    'dispute_resolution': '争议解决',
    'confidentiality': '保密条款',
    'force_majeure': '不可抗力',
    'price_adjustment': '价格调整条款',
    'contract_type_clause': '计价方式',
    'tripartite': '三方协议标识',
}
for clause_type, info in sorted(clause_coverage.items()):
    label = clause_labels.get(clause_type, clause_type)
    pct = round(info['found'] / info['total'] * 100, 1)
    bar = '█' * int(pct / 5) + '░' * (20 - int(pct / 5))
    report_lines.append(f"  {label:12s} [{bar}] {pct:5.1f}%  ({info['found']}/{info['total']})")

# 4. 风险汇总
report_lines.append("\n\n四、风险标识汇总")
report_lines.append("-" * 60)
risk_counts = risk_df['risk_type'].value_counts() if len(risk_df) > 0 else pd.Series()
report_lines.append(f"  共标识风险点: {len(risk_df)}个")
report_lines.append(f"\n  风险类型分布:")
for rtype, count in risk_counts.items():
    report_lines.append(f"    [{rtype}] {count}处")

report_lines.append(f"\n  风险明细:")
for _, row in risk_df.iterrows():
    report_lines.append(f"    ⚠️ [{row['category']}] {row['contract'][:50]}")
    report_lines.append(f"       [{row['risk_type']}] {row['detail']}")

# 5. 金额分析
report_lines.append("\n\n五、合同金额抽取分析")
report_lines.append("-" * 60)
for item in sorted(amount_summary, key=lambda x: x['max_amount'], reverse=True)[:10]:
    report_lines.append(f"  [{item['category']}] {item['contract'][:50]}")
    report_lines.append(f"    最大金额: {item['max_amount']:,.0f} | 金额出现次数: {item['amount_count']}")
    if item['amounts']:
        report_lines.append(f"    Top金额: {item['amounts'][:3]}")

# 6. 台账合同类型分析
report_lines.append("\n\n六、台账合同类型分析")
report_lines.append("-" * 60)
type_stats = ledger.groupby('contract_type').agg(
    合同数=('seq', 'count'),
).reset_index()
for _, row in type_stats.iterrows():
    report_lines.append(f"  {row['contract_type']}: {int(row['合同数'])}份")

# 收入支出分析
income_contracts = ledger[ledger['contract_type'].isin(['收入'])]
expense_contracts = ledger[ledger['contract_type'].isin(['支出', '成本', '费用'])]
report_lines.append(f"\n  收入类合同: {len(income_contracts)}份")
report_lines.append(f"  支出/成本类合同: {len(expense_contracts)}份")

# 7. 关键发现与建议
report_lines.append("\n\n七、关键发现与审计建议")
report_lines.append("-" * 60)
report_lines.append("""
1. 合同管理体系:
   - 台账记录与实体PDF文件存在不完全匹配，建议完善归档管理制度
   - 部分合同签订日期在台账中缺失，影响合同全生命周期管理

2. 高风险关注点:
   - 三方协议较多(涉及甲方、乙方、丙方)，法律关系复杂
   - 大量合同采用"实际开始时间以甲方书面通知为准"，合同履行期不确定
   - 费用包干条款范围过宽，存在乙方成本超支风险

3. 合同期限管理:
   - 存在20年超长期租赁合同，需关注租金调整机制
   - 多份维保类合同即将到期，需提前规划续签或重新招标

4. 金额合规:
   - 需逐份核对PDF实际金额与台账记录金额的一致性
   - "据实结算"类合同需核查结算依据和实际结算金额

5. 履约担保:
   - 部分合同缺少履约担保条款，建议加强风险管控
   - 需核实已有履约担保的实际执行情况
""")

# 8. 逐份合同NLP详情
report_lines.append("\n\n八、逐份合同NLP分析详情")
report_lines.append("-" * 60)
for fname, result in sorted(nlp_results.items()):
    report_lines.append(f"\n{'='*80}")
    report_lines.append(f"📄 {fname}")
    report_lines.append(f"   类别: {result['category']} | 文本长度: {result['text_length']}字符 | 文件大小: {result['size_kb']}KB")
    
    # 条款命中
    report_lines.append(f"   关键条款命中:")
    for clause_type, matches in result['clauses_found'].items():
        if matches:
            label = clause_labels.get(clause_type, clause_type)
            report_lines.append(f"     ✓ {label}: {matches[0][:100] if matches else '无'}")
    
    # 风险
    if result['risk_flags']:
        report_lines.append(f"   ⚠️ 风险标识:")
        for risk in result['risk_flags']:
            report_lines.append(f"     [{risk['type']}] {risk['detail']}")
    else:
        report_lines.append(f"   ✅ 未发现明显风险标识")
    
    # 金额
    if result['amounts_extracted']:
        top_amounts = sorted(set(result['amounts_extracted']), reverse=True)[:5]
        report_lines.append(f"   💰 抽取金额: {top_amounts}")

# 写出报告
report_text = '\n'.join(report_lines)
report_path = os.path.join(OUTPUT_DIR, 'contract_nlp_analysis_report.txt')
with open(report_path, 'w', encoding='utf-8') as f:
    f.write(report_text)

# 写出结构化JSON数据
json_output = {
    'metadata': {
        'analysis_time': datetime.now().isoformat(),
        'total_pdfs': len(pdfs),
        'total_ledger_records': len(ledger),
        'matched_count': int(matched_count),
        'unmatched_ledger_count': len(unmatched_ledger),
    },
    'cross_reference': {
        'matched': cross_df[cross_df['matched']].to_dict('records'),
        'unmatched_pdf': cross_df[~cross_df['matched']].to_dict('records'),
        'unmatched_ledger': unmatched_ledger,
    },
    'clause_coverage': {k: {'found': v['found'], 'total': v['total'], 'pct': round(v['found']/v['total']*100,1)} for k,v in clause_coverage.items()},
    'risks': risk_df.to_dict('records') if len(risk_df) > 0 else [],
    'amount_summary': amount_summary,
    'nlp_details': {k: {
        'category': v['category'],
        'text_length': v['text_length'],
        'clauses_found': {ck: cv for ck, cv in v['clauses_found'].items() if cv},
        'risk_flags': v['risk_flags'],
        'amounts_extracted': sorted(set(v['amounts_extracted']), reverse=True)[:10],
    } for k, v in nlp_results.items()},
}

json_path = os.path.join(OUTPUT_DIR, 'contract_nlp_analysis_data.json')
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(json_output, f, ensure_ascii=False, indent=2)

# 写出Excel汇总
excel_path = os.path.join(OUTPUT_DIR, 'contract_analysis_summary.xlsx')
with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
    cross_df.to_excel(writer, sheet_name='交叉比对', index=False)
    if len(risk_df) > 0:
        risk_df.to_excel(writer, sheet_name='风险汇总', index=False)
    pd.DataFrame(amount_summary).to_excel(writer, sheet_name='金额汇总', index=False)

print(f"\n{'='*80}")
print(f"分析完成!")
print(f"  报告文件: {report_path}")
print(f"  结构化数据: {json_path}")
print(f"  Excel汇总: {excel_path}")
print(f"{'='*80}")
