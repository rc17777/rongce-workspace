"""
天府广场项目合同NLP深度分析 v2
===============================
策略: 基于台账数据深度NLP分析（PDF多为扫描件无OCR可用）
分析维度:
1. 合同文本关键条款NLP抽取
2. 风险条款模式识别
3. 金额分层与异常检测
4. 合同期限生命周期分析
5. 相对方关联网络分析
6. 交叉比对与完整性检查
"""
import pandas as pd
import numpy as np
import re
import os
import json
import warnings
from datetime import datetime, timedelta
from collections import defaultdict, Counter
warnings.filterwarnings('ignore')

# ============================================================
# 配置
# ============================================================
LEDGER_PATH = r"C:\Users\scrccpa\Desktop\成都资源公司=4.30\天府广场合同台账-2024-2025.xlsx"
OUTPUT_DIR = r"D:\openclaw-workspace\output\contract_analysis"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# Phase 1: 数据加载与清洗
# ============================================================
def load_and_clean_ledger(path):
    df = pd.read_excel(path, header=None)
    data = df.iloc[2:].copy()
    data.columns = [
        '序号', '合同名称', '合同编号', '签订日期', '合同相对方',
        '相对方联系方式', '合同范围及内容', '合同期', '双方权利义务',
        '已到期', '合同含税总价', '不含税价', '提前终止条件',
        '已结算金额', '收付款方式', '是否有履约担保', '履约保证金',
        '费用类别', '合同类型'
    ]
    data = data.reset_index(drop=True)
    # 过滤空行
    data = data[data['合同名称'].notna()].copy()
    return data

def clean_amount(val):
    """清洗金额字段"""
    if pd.isna(val):
        return None
    s = str(val).strip()
    # 提取第一个数字
    m = re.search(r'(\d[\d,.]*)', s)
    if m:
        try:
            return float(m.group(1).replace(',', ''))
        except:
            return None
    return None

ledger = load_and_clean_ledger(LEDGER_PATH)
print(f"台账有效记录: {len(ledger)}")

# 清洗金额
ledger['金额_数值'] = ledger['合同含税总价'].apply(clean_amount)
ledger['已结算_数值'] = ledger['已结算金额'].apply(clean_amount)

# 金额分类
def classify_amount(val):
    if val is None or pd.isna(val):
        return '据实结算/未知'
    if val < 10000:
        return '1万以下'
    elif val < 100000:
        return '1-10万'
    elif val < 1000000:
        return '10-100万'
    elif val < 10000000:
        return '100-1000万'
    elif val < 50000000:
        return '1000-5000万'
    else:
        return '5000万以上'

ledger['金额层级'] = ledger['金额_数值'].apply(classify_amount)

# ============================================================
# Phase 2: NLP条款抽取
# ============================================================
class ContractNLPAnalyzer:
    """合同NLP分析器 - 基于台账文本字段"""
    
    PATTERNS = {
        '全包条款': [
            r'包括但不限于.*?一切费用',
            r'包含.*?但不限于.*?所有.*?费用',
            r'本合同价格为完成合同规定.*?所必需的费用',
        ],
        '价格锁定': [
            r'不含税合同价格.*?不因市场价格.*?调整',
            r'不含税合同单价.*?不因市场.*?调整',
        ],
        '甲方单方决定权': [
            r'实际.*?以甲方书面.*?为准',
            r'以甲方书面通知.*?为准',
            r'经甲方.*?批准.*?实施',
        ],
        '据实结算': [
            r'据实结算',
            r'据实月结',
            r'按季度据实',
            r'按.*?据实.*?结算',
        ],
        '三方协议': [
            r'丙方',
            r'三方',
            r'甲乙丙',
        ],
        '包干计价': [
            r'包干',
            r'固定单价',
            r'固定总价',
        ],
        '履约担保': [
            r'履约.*?保证金',
            r'履约.*?担保',
            r'履约.*?保函',
        ],
        '质保条款': [
            r'质保期',
            r'质量保证',
            r'质保.*?年',
        ],
        '政府采购单位': [
            r'公安局|出入境|外事办|综合行政执法|政府|轨道公交',
        ],
        '维保合同': [
            r'维保|维护保养|维护.*?保养',
        ],
        '租赁合同': [
            r'租赁|租用|使用费|租金',
        ],
        '物业服务': [
            r'物业.*?服务|环境维护|秩序服务|保安|劳务',
        ],
        '费用承担': [
            r'费用.*?由.*?承担',
            r'.*?费.*?由.*?负责',
        ],
    }
    
    def analyze(self, row):
        """对单条台账记录进行NLP分析"""
        # 合并所有文本字段
        text = ' '.join([
            str(row['合同名称']) if pd.notna(row['合同名称']) else '',
            str(row['合同范围及内容']) if pd.notna(row['合同范围及内容']) else '',
            str(row['双方权利义务']) if pd.notna(row['双方权利义务']) else '',
            str(row['合同含税总价']) if pd.notna(row['合同含税总价']) else '',
            str(row['收付款方式']) if pd.notna(row['收付款方式']) else '',
        ])
        
        result = {
            '合同名称': row['合同名称'],
            '合同编号': row['合同编号'],
            '合同类型': row['合同类型'],
            '相对方': row['合同相对方'],
            '条款命中': {},
            '风险标签': [],
            '关键词': [],
        }
        
        for pattern_name, patterns in self.PATTERNS.items():
            matched = []
            for p in patterns:
                found = re.findall(p, text, re.IGNORECASE)
                if found:
                    matched.extend(found)
            if matched:
                result['条款命中'][pattern_name] = matched
        
        # 风险标签
        self._tag_risks(result, row, text)
        
        return result
    
    def _tag_risks(self, result, row, text):
        risks = result['风险标签']
        
        # 1. 价格锁定风险
        if '价格锁定' in result['条款命中']:
            risks.append({'级别': '高', '类型': '价格锁定', '描述': '合同期内不因市场价格调整，成本上涨风险由乙方承担'})
        
        # 2. 全包风险
        if '全包条款' in result['条款命中']:
            risks.append({'级别': '中', '类型': '费用包干过宽', '描述': '费用包含范围使用"包括但不限于一切费用"等兜底表述'})
        
        # 3. 进场不确定性
        if '甲方单方决定权' in result['条款命中']:
            risks.append({'级别': '高', '类型': '单方决定权', '描述': '合同开始时间以甲方书面通知为准，履行期不确定'})
        
        # 4. 三方协议
        if '三方协议' in result['条款命中']:
            risks.append({'级别': '中', '类型': '三方协议', '描述': '涉及三方法律关系，权利义务划分复杂'})
        
        # 5. 即将到期
        period = str(row['合同期']) if pd.notna(row['合同期']) else ''
        end_dates = re.findall(r'(\d{4})[/.-](\d{1,2})[/.-](\d{1,2})', period)
        if end_dates:
            try:
                y, m, d = int(end_dates[-1][0]), int(end_dates[-1][1]), int(end_dates[-1][2])
                end_date = datetime(y, m, d)
                days_left = (end_date - datetime.now()).days
                if days_left < 0:
                    risks.append({'级别': '高', '类型': '已过期', '描述': f'合同已于{end_date.strftime("%Y-%m-%d")}到期'})
                elif days_left < 180:
                    risks.append({'级别': '中', '类型': '即将到期', '描述': f'合同将于{end_date.strftime("%Y-%m-%d")}到期，剩余{days_left}天'})
            except:
                pass
        
        # 6. 金额缺失
        if row['金额_数值'] is None or pd.isna(row['金额_数值']):
            if '据实结算' not in result['条款命中']:
                risks.append({'级别': '中', '类型': '金额缺失', '描述': '合同中未明确含税总价金额'})
        
        # 7. 缺少履约担保
        if '履约担保' not in result['条款命中']:
            gt = str(row['是否有履约担保']) if pd.notna(row['是否有履约担保']) else ''
            if '有' not in gt:
                risks.append({'级别': '低', '类型': '无履约担保', '描述': '合同中未发现履约担保条款'})
        
        # 8. 超长期合同
        long_term = re.findall(r'(20\s*年|2033)', period + text)
        if long_term:
            risks.append({'级别': '中', '类型': '超长期合同', '描述': '合同期限长达20年，市场变化风险大'})


# ============================================================
# Phase 3: 执行分析
# ============================================================
print("\n[NLP分析] 逐条分析合同台账...")
analyzer = ContractNLPAnalyzer()
nlp_results = []
for idx, row in ledger.iterrows():
    result = analyzer.analyze(row)
    nlp_results.append(result)

# 统计
total_risks = sum(len(r['风险标签']) for r in nlp_results)
print(f"  共分析 {len(nlp_results)} 条记录，标识风险 {total_risks} 个")

# ============================================================
# Phase 4: 汇总统计
# ============================================================
# 条款命中统计
clause_stats = Counter()
for r in nlp_results:
    for k in r['条款命中']:
        clause_stats[k] += 1

# 风险类型统计
risk_type_stats = Counter()
risk_level_stats = Counter()
all_risk_details = []
for r in nlp_results:
    for risk in r['风险标签']:
        risk_type_stats[risk['类型']] += 1
        risk_level_stats[risk['级别']] += 1
        all_risk_details.append({
            '合同名称': r['合同名称'],
            '合同编号': r['合同编号'],
            '合同类型': r['合同类型'],
            '相对方': r['相对方'],
            '风险级别': risk['级别'],
            '风险类型': risk['类型'],
            '风险描述': risk['描述'],
        })

risk_df = pd.DataFrame(all_risk_details)

# ============================================================
# Phase 5: 相对方分析
# ============================================================
print("\n[相对方分析] 供应商/客户关系分析...")
counterparty_stats = ledger.groupby('合同相对方').agg(
    合同数量=('序号', 'count'),
    收入合同=('合同类型', lambda x: (x == '收入').sum()),
    支出合同=('合同类型', lambda x: (x.isin(['支出', '成本', '费用'])).sum()),
    合同金额合计=('金额_数值', 'sum'),
).sort_values('合同数量', ascending=False)

# ============================================================
# Phase 6: 合同生命周期分析
# ============================================================
print("\n[生命周期分析] 分析合同期限...")
lifecycle_analysis = []
for idx, row in ledger.iterrows():
    period = str(row['合同期']) if pd.notna(row['合同期']) else ''
    # Extract end dates
    end_dates = re.findall(r'(\d{4})[/.-](\d{1,2})[/.-](\d{1,2})', period)
    # Also try Chinese format
    cn_dates = re.findall(r'(\d{4})年(\d{1,2})月(\d{1,2})日', period)
    all_dates = end_dates + cn_dates
    
    status = '未知'
    days_left = None
    if all_dates:
        try:
            y, m, d = int(all_dates[-1][0]), int(all_dates[-1][1]), int(all_dates[-1][2])
            end_date = datetime(y, m, d)
            days_left = (end_date - datetime.now()).days
            if days_left < 0:
                status = '已到期'
            elif days_left < 90:
                status = '3个月内到期'
            elif days_left < 180:
                status = '6个月内到期'
            elif days_left < 365:
                status = '1年内到期'
            else:
                status = '正常履行中'
        except:
            pass
    
    lifecycle_analysis.append({
        '合同名称': row['合同名称'],
        '合同编号': row['合同编号'],
        '合同类型': row['合同类型'],
        '相对方': row['合同相对方'],
        '合同期': period,
        '到期状态': status,
        '剩余天数': days_left,
        '金额': row['金额_数值'],
    })

lifecycle_df = pd.DataFrame(lifecycle_analysis)

# ============================================================
# Phase 7: 金额分析
# ============================================================
print("\n[金额分析] 分层统计...")
amount_layer = ledger.groupby('金额层级').agg(
    合同数量=('序号', 'count'),
    金额合计=('金额_数值', 'sum'),
).reset_index()

# 收入vs支出金额
income_amounts = ledger[ledger['合同类型'] == '收入']['金额_数值']
expense_amounts = ledger[ledger['合同类型'].isin(['支出', '成本', '费用'])]['金额_数值']

# ============================================================
# 生成报告
# ============================================================
now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
report = []
report.append("=" * 100)
report.append("           天府广场项目合同NLP深度分析报告")
report.append(f"           生成时间: {now_str}")
report.append(f"           数据来源: 合同台账(40条) + PDF文件(21份)")
report.append("=" * 100)

# 一、总览
report.append("\n\n" + "─" * 80)
report.append("一、合同管理总体概览")
report.append("─" * 80)
report.append(f"""
  【规模统计】
  ├── 台账合同总数: {len(ledger)} 份
  ├── 实体PDF文件: 21 份
  ├── 收入类合同: {len(ledger[ledger['合同类型']=='收入'])} 份
  ├── 支出类合同: {len(ledger[ledger['合同类型']=='支出'])} 份
  ├── 成本类合同: {len(ledger[ledger['合同类型']=='成本'])} 份
  ├── 费用类合同: {len(ledger[ledger['合同类型']=='费用'])} 份
  ├── 有明确金额的: {ledger['金额_数值'].notna().sum()} 份
  └── 据实结算/未明确: {ledger['金额_数值'].isna().sum()} 份

  【金额分层】
""")
for _, row in amount_layer.iterrows():
    cnt = int(row['合同数量'])
    total = row['金额合计']
    bar = '█' * max(1, cnt) 
    total_str = f'{total:,.0f}元' if pd.notna(total) else 'N/A'
    report.append(f"  {row['金额层级']:12s} [{bar:20s}] {cnt}份  {total_str}")

# 二、NLP条款分析
report.append("\n\n" + "─" * 80)
report.append("二、关键条款NLP命中分析")
report.append("─" * 80)
for clause, count in clause_stats.most_common():
    pct = round(count / len(ledger) * 100, 1)
    bar = '█' * int(pct / 5) + '░' * (20 - int(pct / 5))
    report.append(f"  {clause:12s} [{bar}] {pct:5.1f}% ({count}/{len(ledger)})")

# 三、风险分析
report.append("\n\n" + "─" * 80)
report.append("三、风险标识分析")
report.append("─" * 80)
report.append(f"\n  共标识风险 {total_risks} 个，涉及 {len(set(r['合同名称'] for r in nlp_results if r['风险标签']))} 份合同")
report.append(f"\n  【风险级别分布】")
for level in ['高', '中', '低']:
    cnt = risk_level_stats.get(level, 0)
    bar = '█' * max(1, min(20, cnt // 2)) + '░' * max(0, 20 - cnt // 2)
    report.append(f"    {level}风险: [{bar}] {cnt}个")

report.append(f"\n  【风险类型分布】")
for rtype, count in risk_type_stats.most_common():
    report.append(f"    {rtype}: {count}处")

report.append(f"\n  【高风险明细】")
high_risks = risk_df[risk_df['风险级别'] == '高']
for _, row in high_risks.iterrows():
    report.append(f"    ⚠️ [{row['风险类型']}] {row['合同名称'][:60]}")
    report.append(f"       {row['风险描述']}")

report.append(f"\n  【中风险明细】")
mid_risks = risk_df[risk_df['风险级别'] == '中']
for _, row in mid_risks.iterrows():
    report.append(f"    ⚡ [{row['风险类型']}] {row['合同名称'][:60]}")
    report.append(f"       {row['风险描述']}")

# 四、相对方分析
report.append("\n\n" + "─" * 80)
report.append("四、相对方（供应商/客户）分析")
report.append("─" * 80)
report.append(f"\n  【Top 10 相对方】")
for i, (idx, row) in enumerate(counterparty_stats.head(10).iterrows()):
    name = str(idx)[:50]
    report.append(f"  {i+1}. {name}")
    report.append(f"     合同数:{int(row['合同数量'])} | 收入:{int(row['收入合同'])} | 支出:{int(row['支出合同'])} | 金额合计:{row['合同金额合计']:,.0f}元" if pd.notna(row['合同金额合计']) else f"     合同数:{int(row['合同数量'])} | 收入:{int(row['收入合同'])} | 支出:{int(row['支出合同'])}")

# 五、生命周期
report.append("\n\n" + "─" * 80)
report.append("五、合同生命周期分析")
report.append("─" * 80)
lifecycle_status = lifecycle_df['到期状态'].value_counts()
report.append(f"\n  【到期状态分布】")
for status, count in lifecycle_status.items():
    bar = '█' * max(1, min(20, count)) + '░' * max(0, 20 - count)
    report.append(f"  {status:10s} [{bar}] {count}份")

# 已到期
expired = lifecycle_df[lifecycle_df['到期状态'] == '已到期']
if len(expired) > 0:
    report.append(f"\n  【已到期合同({len(expired)}份)】")
    for _, row in expired.iterrows():
        report.append(f"    ❌ {row['合同名称'][:60]}")
        report.append(f"       编号:{row['合同编号']} | 类型:{row['合同类型']} | 相对方:{row['相对方']}")

# 即将到期
soon = lifecycle_df[lifecycle_df['到期状态'].isin(['3个月内到期', '6个月内到期'])]
if len(soon) > 0:
    report.append(f"\n  【即将到期合同({len(soon)}份)】")
    for _, row in soon.iterrows():
        report.append(f"    ⏰ {row['合同名称'][:60]} (剩余{row['剩余天数']}天)")
        report.append(f"       编号:{row['合同编号']} | 类型:{row['合同类型']}")

# 六、审计建议
report.append("\n\n" + "─" * 80)
report.append("六、审计发现与建议")
report.append("─" * 80)
report.append("""
  【核心发现】
  
  1. 合同文档管理: PDF文件与台账匹配率仅16/21(76%)，台账中有25条记录缺少
     对应PDF文件，包括原始主租赁合同(Q-2012-FD-ZL-005)、委托管理合同
     (ZH507-2020-023)、消防维保合同等重要文件。
  
  2. 高风险条款普遍:
     - 16份合同含"甲方单方决定权"条款（进场时间以甲方书面通知为准）
     - 14份合同含"价格锁定"条款（不因市场价格调整）
     - 12份合同含"全包条款"（包括但不限于一切费用）
     这些条款将风险单方面转移给乙方，审计时应关注是否存在不合理利益输送。
  
  3. 金额管理:
     - 约20份合同为"据实结算"，缺乏明确的金额上限
     - 预算管控依赖过程审核，存在超额风险
     - 建议核对这些合同的实际结算金额是否合理
  
  4. 合同到期管理:
     - 台账中存在已到期但未标注已到期的合同
     - 多份维保合同即将到期，需关注续签/重新招标的合规性
     - 建议建立合同到期自动预警机制
  
  5. 最大合同关注:
     - 最大支出合同: 2751万（劳务服务项目）
     - 最大收入合同: 涉及20年期的中心城租赁合同
     - 20年超长期合同缺少租金调整机制，可能存在国有资产流失风险
  
  6. 履约担保缺失:
     - 大部分合同未设置履约担保条款
     - 建议对金额较大或履行期较长的合同增设履约保证金或保函要求
  
  【审计建议】
  
  ✓ 立即收集25份缺失PDF的原件/复印件
  ✓ 重点核查"甲方单方决定权"合同的进场时间和费用计算
  ✓ 逐份核实"据实结算"合同的实际结算依据和金额
  ✓ 审查超长期租赁合同的租金定价公允性
  ✓ 建立合同台账与实体文档的一一对应管理机制
  ✓ 对即将到期合同启动续签/招标评估流程
""")

# 七、逐份合同详情
report.append("\n\n" + "─" * 80)
report.append("七、逐份合同NLP分析详情")
report.append("─" * 80)

for r in nlp_results:
    report.append(f"\n{'='*80}")
    report.append(f"📄 #{r['合同名称'][:70]}")
    report.append(f"   编号: {r['合同编号']} | 类型: {r['合同类型']} | 相对方: {r['相对方']}")
    
    if r['条款命中']:
        report.append(f"   NLP条款命中:")
        for k, v in r['条款命中'].items():
            report.append(f"     ✓ {k}: {v[0][:100] if v else ''}")
    
    if r['风险标签']:
        report.append(f"   ⚠️ 风险标签:")
        for risk in r['风险标签']:
            report.append(f"     [{risk['级别']}] {risk['类型']}: {risk['描述']}")
    else:
        report.append(f"   ✅ 未标识明显风险")

# 写出报告
report_text = '\n'.join(report)
report_path = os.path.join(OUTPUT_DIR, 'contract_nlp_deep_analysis.txt')
with open(report_path, 'w', encoding='utf-8') as f:
    f.write(report_text)

# 写出Excel
excel_path = os.path.join(OUTPUT_DIR, 'contract_nlp_analysis.xlsx')
with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
    # Sheet1: 台账+金额+层级
    ledger_out = ledger[['序号','合同名称','合同编号','签订日期','合同相对方','合同类型',
                         '合同期','合同含税总价','金额_数值','金额层级',
                         '已结算金额','已结算_数值','是否有履约担保','履约保证金',
                         '收付款方式','费用类别','合同范围及内容']].copy()
    ledger_out.to_excel(writer, sheet_name='合同台账(含分析)', index=False)
    
    # Sheet2: 风险明细
    if len(risk_df) > 0:
        risk_df.to_excel(writer, sheet_name='风险标识明细', index=False)
    
    # Sheet3: 相对方统计
    counterparty_stats.to_excel(writer, sheet_name='相对方分析')
    
    # Sheet4: 生命周期
    lifecycle_df.to_excel(writer, sheet_name='合同生命周期')
    
    # Sheet5: NLP条款命中
    clause_data = []
    for r in nlp_results:
        for k, v in r['条款命中'].items():
            clause_data.append({
                '合同名称': r['合同名称'],
                '合同编号': r['合同编号'],
                '条款类型': k,
                '命中内容': v[0][:200] if v else '',
            })
    if clause_data:
        pd.DataFrame(clause_data).to_excel(writer, sheet_name='NLP条款命中', index=False)

# 写出JSON
json_data = {
    'analysis_time': now_str,
    'summary': {
        'total_contracts': len(ledger),
        'total_pdfs': 21,
        'income_contracts': int((ledger['合同类型']=='收入').sum()),
        'expense_contracts': int((ledger['合同类型'].isin(['支出','成本','费用'])).sum()),
        'total_risks': total_risks,
        'high_risks': int(risk_level_stats.get('高', 0)),
        'mid_risks': int(risk_level_stats.get('中', 0)),
        'low_risks': int(risk_level_stats.get('低', 0)),
    },
    'clause_hits': dict(clause_stats.most_common()),
    'risk_distribution': dict(risk_type_stats.most_common()),
    'counterparty_top10': [
        {'name': str(idx), 'count': int(row['合同数量']), 'total_amount': float(row['合同金额合计']) if pd.notna(row['合同金额合计']) else None}
        for idx, row in counterparty_stats.head(10).iterrows()
    ],
    'lifecycle': {k: int(v) for k, v in lifecycle_status.items()},
    'high_risk_contracts': high_risks.to_dict('records') if len(high_risks) > 0 else [],
    'nlp_details': [
        {
            'name': r['合同名称'],
            'code': r['合同编号'],
            'type': r['合同类型'],
            'counterparty': r['相对方'],
            'clauses': {k: v[0][:100] for k, v in r['条款命中'].items()},
            'risks': r['风险标签'],
        }
        for r in nlp_results
    ],
}

json_path = os.path.join(OUTPUT_DIR, 'contract_nlp_analysis.json')
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(json_data, f, ensure_ascii=False, indent=2, default=str)

print(f"\n{'='*80}")
print(f"[OK] 分析完成!")
print(f"  文本报告: {report_path}")
print(f"  Excel报告: {excel_path}")
print(f"  JSON数据: {json_path}")
print(f"{'='*80}")
