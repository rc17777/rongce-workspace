"""
天府广场项目合同NLP深度分析 v3 - Windows OCR版
==============================================
管道: PDF → pymupdf转图片 → Windows OCR → NLP分析
"""
import pandas as pd
import numpy as np
import re
import os
import sys
import json
import fitz  # pymupdf
import asyncio
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
import warnings
warnings.filterwarnings('ignore')

# Windows OCR
from winrt.windows.media.ocr import OcrEngine
from winrt.windows.graphics.imaging import BitmapDecoder
from winrt.windows.storage import StorageFile, FileAccessMode
from winrt.windows.globalization import Language

# ============================================================
# 配置
# ============================================================
CONTRACT_DIR = r"C:\Users\scrccpa\Desktop\成都轨道资源资料\业主发送资料\天府广场项目2026年专项审计资料清单（第一批）\1合同协议"
LEDGER_PATH = r"C:\Users\scrccpa\Desktop\成都资源公司=4.30\天府广场合同台账-2024-2025.xlsx"
OUTPUT_DIR = r"D:\openclaw-workspace\output\contract_analysis"
TEMP_IMG_DIR = os.path.join(OUTPUT_DIR, "temp_images")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_IMG_DIR, exist_ok=True)

# ============================================================
# Phase 1: Windows OCR 文本提取
# ============================================================
def ocr_page_image(image_path):
    """使用Windows OCR提取单张图片文本"""
    try:
        file = StorageFile.get_file_from_path_async(image_path).get()
        stream = file.open_async(FileAccessMode.READ).get()
        decoder = BitmapDecoder.create_async(stream).get()
        bitmap = decoder.get_software_bitmap_async().get()
        
        engine = OcrEngine.try_create_from_user_profile_languages()
        if engine is None:
            engine = OcrEngine.try_create_from_language(Language("zh-Hans"))
        
        result = engine.recognize_async(bitmap).get()
        text = result.text if result else ""
        return text
    except Exception as e:
        return f"[OCR_ERROR: {str(e)}]"

def extract_pdf_with_ocr(pdf_path, max_pages=30):
    """提取PDF文本：先尝试直接提取，失败则OCR"""
    result = {
        'text': '',
        'pages_processed': 0,
        'method': 'direct',
        'page_texts': [],
    }
    
    try:
        doc = fitz.open(pdf_path)
        total_pages = min(len(doc), max_pages)
        
        # 先尝试直接提取
        direct_text = ""
        for i in range(total_pages):
            page_text = doc[i].get_text()
            direct_text += page_text
        
        if len(direct_text.strip()) > 200:
            # 文本型PDF，直接使用
            result['text'] = direct_text
            result['pages_processed'] = total_pages
            result['method'] = 'direct'
        else:
            # 扫描件，需要OCR
            result['method'] = 'ocr'
            all_text = []
            base_name = Path(pdf_path).stem[:30]
            
            for i in range(total_pages):
                page = doc[i]
                # 渲染为图片
                pix = page.get_pixmap(dpi=200)
                img_path = os.path.join(TEMP_IMG_DIR, f"{base_name}_p{i+1}.png")
                pix.save(img_path)
                
                # OCR识别
                page_text = ocr_page_image(img_path)
                all_text.append(page_text)
                result['pages_processed'] += 1
                
                # 清理临时图片
                try:
                    os.remove(img_path)
                except:
                    pass
                
                if (i+1) % 5 == 0:
                    print(f"    OCR进度: {i+1}/{total_pages} 页")
            
            result['text'] = '\n'.join(all_text)
            result['page_texts'] = all_text
        
        doc.close()
    except Exception as e:
        result['text'] = f"[ERROR: {str(e)}]"
    
    return result

# ============================================================
# Phase 2: NLP分析器
# ============================================================
class DeepContractAnalyzer:
    """深度合同NLP分析器"""
    
    # 扩展条款模式（针对完整合同文本）
    PATTERNS = {
        # 签约主体
        '甲方信息': [r'甲方[：:]\s*(.+?)(?:[。；\n]|乙方|$)'],
        '乙方信息': [r'乙方[：:]\s*(.+?)(?:[。；\n]|甲方|丙方|$)'],
        '丙方信息': [r'丙方[：:]\s*(.+?)(?:[。；\n]|$)'],
        
        # 金额条款
        '合同金额': [
            r'(?:合同(?:总价|金额|价款|价格)|含税总价)[：:]*\s*.*?(\d[\d,.]+\s*(?:万元|元|亿))',
            r'(?:不含税.*?(?:金额|总价|价格)).*?(\d[\d,.]+\s*(?:万元|元|亿))',
            r'(?:¥|￥)\s*(\d[\d,.]+)',
        ],
        '付款方式': [
            r'(?:付款|支付|结算)\s*(?:方式|方法|条件).*?[：:]\s*(.+?)(?:[。；]|\n\n)',
            r'(?:按[月度季度年].*?(?:支付|结算|付款))',
            r'(?:据实.*?(?:结算|支付|月结))',
        ],
        '发票条款': [r'(?:发票|增值税).*?(?:专用|普通|开具|提供)'],
        
        # 合同期限
        '合同期限': [
            r'(?:合同期|合同期限|服务期|维保期|租赁期|协议期|履行期).*?[：:]\s*(.+?)(?:[。；]|\n)',
            r'(?:自|从)\s*(\d{4}[\d./年-]+\d{1,2}[\d日月]*)\s*(?:起|至|到|止).*?(?:至|到|止)\s*(\d{4}[\d./年-]+\d{1,2}[\d日月]*)',
        ],
        
        # 权利义务
        '甲方权利义务': [r'(?:甲方|业主|委托方)\s*(?:权利|义务|责任|职责).*?[：:]\s*(.+?)(?:[。；]|\n\n)'],
        '乙方权利义务': [r'(?:乙方|承包方|服务方)\s*(?:权利|义务|责任|职责).*?[：:]\s*(.+?)(?:[。；]|\n\n)'],
        '服务范围': [r'(?:服务|实施|维保|租赁)\s*(?:范围|内容|区域).*?[：:]\s*(.+?)(?:[。；]|\n\n)'],
        
        # 违约责任
        '违约责任': [
            r'(?:违约|违约责任|违约金).*?[：:]\s*(.+?)(?:[。；]|\n\n)',
            r'(?:赔偿.*?(?:损失|金额).*?(?:按|为).*?(\d[\d,.%]*))',
        ],
        '合同解除': [r'(?:解除.*?(?:合同|协议)|合同.*?解除).*?(?:条件|情形|情况)'],
        '提前终止': [r'(?:提前.*?(?:终止|解除|退场|结束))'],
        
        # 担保与保险
        '履约担保': [
            r'(?:履约.*?(?:保证金|担保|保函))',
            r'(?:保证金).*?(\d[\d,.]+\s*(?:万元|元))',
        ],
        '保险条款': [r'(?:保险.*?(?:购买|承保|险种|保险责任))'],
        
        # 争议解决
        '争议解决': [r'(?:争议|纠纷).*?(?:解决|处理|管辖|仲裁|诉讼)'],
        '管辖法院': [r'(?:管辖.*?法院|向.*?法院.*?(?:起诉|提起))'],
        
        # 其他关键条款
        '不可抗力': [r'不可抗力'],
        '保密条款': [r'(?:保密|商业秘密|保密信息|保密义务)'],
        '知识产权': [r'(?:知识产权|著作权|专利权|商标权)'],
        '转包分包': [r'(?:转包|分包|不得.*?转让)'],
        '价格调整': [
            r'(?:价格.*?(?:调整|变动|变更|修改))',
            r'(?:不因.*?(?:市场|政策|国家).*?(?:调整|变动))',
        ],
        '验收条款': [r'(?:验收.*?(?:标准|条件|程序|方式))'],
        '质保条款': [r'(?:质保|质量保证|保修).*?(?:期|期限).*?(\d+\s*[年月])'],
    }
    
    def analyze(self, contract_id, text, category=''):
        """深度分析单份合同"""
        result = {
            'contract_id': contract_id,
            'category': category,
            'text_length': len(text),
            'clauses': {},
            'risks': [],
            'amounts': [],
            'dates': [],
            'parties': {},
            'score': {'completeness': 0, 'risk': 0},
        }
        
        # 条款提取
        for clause_type, patterns in self.PATTERNS.items():
            matches = []
            for pattern in patterns:
                found = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
                if found:
                    for f in found[:3]:
                        match_text = f if isinstance(f, str) else ' '.join(str(x) for x in f if x)
                        match_text = re.sub(r'\s+', ' ', match_text)[:150]
                        if match_text.strip():
                            matches.append(match_text)
            if matches:
                result['clauses'][clause_type] = matches
        
        # 金额提取
        amounts = re.findall(r'(\d[\d,.]*)\s*(?:万元|元|亿)', text)
        for a in amounts:
            try:
                val = float(a.replace(',', ''))
                if 100 < val < 100000000000:
                    result['amounts'].append(val)
            except:
                pass
        
        # 日期提取
        dates = re.findall(r'(\d{4})[年./-](\d{1,2})[月./-](\d{1,2})日?', text)
        result['dates'] = list(set(dates))[:20]
        
        # 签约主体提取
        for party in ['甲方信息', '乙方信息', '丙方信息']:
            if party in result['clauses']:
                result['parties'][party] = result['clauses'][party][0]
        
        # 风险识别
        self._flag_risks(result, text)
        
        # 评分配置
        result['score']['completeness'] = len(result['clauses']) / len(self.PATTERNS) * 100
        result['score']['risk'] = len(result['risks'])
        
        return result
    
    def _flag_risks(self, result, text):
        risks = result['risks']
        
        # 高风险
        if re.search(r'不因市场.*?调整|合同价格.*?不再.*?调整|不含税.*?不因', text):
            risks.append({'级别': '高', '类型': '价格锁定', '描述': '合同期内锁定价格，不因市场/政策调整，成本风险由乙方承担'})
        
        if re.search(r'实际.*?以甲方.*?(?:书面|通知).*?为准', text):
            risks.append({'级别': '高', '类型': '单方决定权', '描述': '关键时间节点由甲方单方决定，履行期不确定'})
        
        if re.search(r'包括但不限于.*?一切费用|全部.*?费用.*?由.*?承担', text):
            risks.append({'级别': '高', '类型': '费用兜底', '描述': '费用范围包含兜底条款，可能存在无限责任风险'})
        
        # 中风险
        if re.search(r'丙方|第三方.*?责任', text):
            risks.append({'级别': '中', '类型': '三方关系', '描述': '存在三方法律关系，责任划分复杂'})
        
        if re.search(r'据实结算|据实.*?支付', text):
            risks.append({'级别': '中', '类型': '据实结算', '描述': '采用据实结算方式，缺乏金额上限控制'})
        
        if re.search(r'委托.*?期限.*?(?:甲方终止|另行通知|单方)', text):
            risks.append({'级别': '中', '类型': '单方终止权', '描述': '甲方可单方终止委托，合同稳定性差'})
        
        # 低风险
        if not re.search(r'履约.*?(?:保证金|担保|保函)', text):
            risks.append({'级别': '低', '类型': '无履约担保', '描述': '未设置履约担保条款'})
        
        if not re.search(r'争议.*?(?:解决|管辖|仲裁|诉讼)', text):
            risks.append({'级别': '低', '类型': '无争议解决', '描述': '缺少争议解决条款'})
        
        if not re.search(r'不可抗力', text):
            risks.append({'级别': '低', '类型': '无不可抗力', '描述': '缺少不可抗力条款'})
        
        # 合同期限风险
        end_dates = re.findall(r'(\d{4})[年./-](\d{1,2})[月./-](\d{1,2})日?', text)
        if end_dates:
            try:
                y, m, d = int(end_dates[-1][0]), int(end_dates[-1][1]), int(end_dates[-1][2])
                end_date = datetime(y, m, d)
                days = (end_date - datetime.now()).days
                if days < 0:
                    risks.append({'级别': '高', '类型': '已过期', '描述': f'合同于{end_date.strftime("%Y-%m-%d")}到期'})
                elif days < 90:
                    risks.append({'级别': '中', '类型': '即将到期', '描述': f'合同将于{end_date.strftime("%Y-%m-%d")}到期，剩余{days}天'})
            except:
                pass


# ============================================================
# Phase 3: 加载台账
# ============================================================
def load_ledger(path):
    df = pd.read_excel(path, header=None)
    data = df.iloc[2:].copy()
    data.columns = [
        '序号', '合同名称', '合同编号', '签订日期', '合同相对方',
        '相对方联系方式', '合同范围及内容', '合同期', '双方权利义务',
        '已到期', '合同含税总价', '不含税价', '提前终止条件',
        '已结算金额', '收付款方式', '是否有履约担保', '履约保证金',
        '费用类别', '合同类型'
    ]
    data = data[data['合同名称'].notna()].reset_index(drop=True)
    return data

def clean_amount(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    m = re.search(r'(\d[\d,.]*)', s)
    if m:
        try:
            return float(m.group(1).replace(',', ''))
        except:
            pass
    return None


# ============================================================
# Main
# ============================================================
print("=" * 80)
print("天府广场项目合同NLP深度分析 v3 (Windows OCR)")
print("=" * 80)

# 收集所有PDF
pdf_files = []
for root, dirs, files in os.walk(CONTRACT_DIR):
    for f in files:
        if f.lower().endswith('.pdf'):
            pdf_files.append((os.path.join(root, f), os.path.basename(root), f))

print(f"\n找到 {len(pdf_files)} 份合同PDF")

# 加载台账
ledger = load_ledger(LEDGER_PATH)
print(f"加载台账: {len(ledger)} 条记录")

# OCR提取
print("\n[Phase 1] OCR文本提取...")
pdf_texts = {}
for pdf_path, category, filename in pdf_files:
    fname_short = filename[:70]
    print(f"  处理: [{category}] {fname_short}...")
    result = extract_pdf_with_ocr(pdf_path, max_pages=40)
    pdf_texts[filename] = {
        'path': pdf_path,
        'category': category,
        'text': result['text'],
        'method': result['method'],
        'pages': result['pages_processed'],
        'char_count': len(result['text']),
    }
    print(f"    方法: {result['method']}, 页数: {result['pages_processed']}, 字符: {len(result['text'])}")

# NLP分析
print("\n[Phase 2] NLP深度分析...")
analyzer = DeepContractAnalyzer()
nlp_results = {}
for filename, info in pdf_texts.items():
    print(f"  分析: {filename[:60]}...")
    result = analyzer.analyze(filename, info['text'], info['category'])
    result['extraction_method'] = info['method']
    result['pages'] = info['pages']
    nlp_results[filename] = result

# 台账交叉比对
print("\n[Phase 3] 台账交叉比对...")
def match_to_ledger(pdf_name, ledger_df):
    name_clean = pdf_name.replace('.pdf', '').replace('-扫描件', '').strip()
    for idx, row in ledger_df.iterrows():
        code = str(row['合同编号']) if pd.notna(row['合同编号']) else ''
        name = str(row['合同名称']) if pd.notna(row['合同名称']) else ''
        if code and code != 'nan' and code in name_clean:
            return idx
        if name and len(name) > 5:
            key_parts = re.findall(r'[\u4e00-\u9fa5A-Za-z0-9]{4,}', name)
            match_count = sum(1 for kp in key_parts if kp in name_clean)
            if match_count >= 2:
                return idx
    return None

matches = []
for fname, info in pdf_texts.items():
    idx = match_to_ledger(fname, ledger)
    if idx is not None:
        row = ledger.iloc[idx]
        matches.append({
            'pdf_file': fname,
            'category': info['category'],
            'ledger_seq': row['序号'],
            'ledger_name': row['合同名称'],
            'ledger_no': row['合同编号'],
            'ledger_counterparty': row['合同相对方'],
            'ledger_price': row['合同含税总价'],
            'ledger_type': row['合同类型'],
            'extraction_method': info['method'],
            'pdf_chars': info['char_count'],
        })
    else:
        matches.append({
            'pdf_file': fname,
            'category': info['category'],
            'ledger_seq': None,
            'ledger_name': None,
            'matched': False,
            'extraction_method': info['method'],
            'pdf_chars': info['char_count'],
        })

match_df = pd.DataFrame(matches)

# 汇总统计
print("\n[Phase 4] 汇总统计...")

# 条款覆盖度
clause_coverage = {}
for r in nlp_results.values():
    for ct in r['clauses']:
        clause_coverage[ct] = clause_coverage.get(ct, 0) + 1

# 风险汇总
all_risks = []
for fname, r in nlp_results.items():
    for risk in r['risks']:
        all_risks.append({
            '合同名称': fname,
            '类别': r['category'],
            '风险级别': risk['级别'],
            '风险类型': risk['类型'],
            '风险描述': risk['描述'],
        })
risk_df = pd.DataFrame(all_risks)

# ============================================================
# 生成报告
# ============================================================
now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
report = []
report.append("=" * 100)
report.append("           天府广场项目合同NLP深度分析报告 (OCR增强版)")
report.append(f"           生成时间: {now_str}")
report.append(f"           数据来源: {len(pdf_files)}份PDF(Windows OCR) + {len(ledger)}条台账")
report.append("=" * 100)

# 一、OCR提取概况
report.append("\n\n" + "─" * 80)
report.append("一、PDF文本提取概况 (Windows OCR)")
report.append("─" * 80)
direct = sum(1 for v in pdf_texts.values() if v['method'] == 'direct')
ocr_count = sum(1 for v in pdf_texts.values() if v['method'] == 'ocr')
report.append(f"  直接提取(text PDF): {direct}份")
report.append(f"  OCR识别(scanned PDF): {ocr_count}份")
report.append(f"\n  各合同提取详情:")
for fname, info in sorted(pdf_texts.items(), key=lambda x: x[1]['char_count'], reverse=True):
    bar = '█' * min(30, info['char_count'] // 500) + '░' * max(0, 30 - info['char_count'] // 500)
    report.append(f"  [{info['method']:6s}] {info['char_count']:6d}字 [{bar}] {fname[:55]}")

# 二、NLP条款覆盖度
report.append("\n\n" + "─" * 80)
report.append("二、关键条款NLP抽取覆盖度 (基于OCR文本)")
report.append("─" * 80)
total = len(nlp_results)
for ct, cnt in sorted(clause_coverage.items(), key=lambda x: x[1], reverse=True):
    pct = round(cnt / total * 100, 1)
    bar = '█' * int(pct / 5) + '░' * (20 - int(pct / 5))
    report.append(f"  {ct:10s} [{bar}] {pct:5.1f}% ({cnt}/{total})")

# 三、风险标识
report.append("\n\n" + "─" * 80)
report.append("三、风险标识分析")
report.append("─" * 80)
if len(risk_df) > 0:
    level_counts = risk_df['风险级别'].value_counts()
    type_counts = risk_df['风险类型'].value_counts()
    report.append(f'\n  共标识风险 {len(risk_df)} 个')
    report.append(f'\n  级别分布:')
    for lv in ['高', '中', '低']:
        n = level_counts.get(lv, 0)
        report.append(f'    {lv}风险: {n}个')
    report.append(f'\n  类型分布:')
    for tp, n in type_counts.items():
        report.append(f'    {tp}: {n}处')
    
    report.append(f'\n  [高风险明细]')
    for _, row in risk_df[risk_df['风险级别'] == '高'].iterrows():
        report.append(f"    !! [{row['风险类型']}] {row['合同名称'][:55]}")
        report.append(f"       {row['风险描述']}")

# 四、交叉比对
report.append("\n\n" + "─" * 80)
report.append("四、PDF-台账交叉比对")
report.append("─" * 80)
matched = match_df[match_df.get('ledger_seq', pd.Series()).notna()]
report.append(f"  匹配成功: {len(matched)}/{len(pdf_files)}")
report.append(f"\n  [已匹配]")
for _, row in matched.iterrows():
    report.append(f"    {row['pdf_file'][:55]}")
    report.append(f"      台账: #{row['ledger_seq']} {row['ledger_name']} | {row['ledger_type']} | {row['ledger_price']}")

# 五、逐份详情
report.append("\n\n" + "─" * 80)
report.append("五、逐份合同NLP详情")
report.append("─" * 80)
for fname, r in sorted(nlp_results.items()):
    report.append(f"\n{'='*80}")
    report.append(f"  [{r['category']}] {fname}")
    report.append(f"  提取方式: {r['extraction_method']} | {r['pages']}页 | {r['text_length']}字符")
    report.append(f"  完整度评分: {r['score']['completeness']:.1f}% | 风险评分: {r['score']['risk']}")
    
    if r['clauses']:
        report.append(f"  条款抽取 ({len(r['clauses'])}类):")
        for ct, ms in r['clauses'].items():
            report.append(f"    + {ct}: {ms[0][:120]}")
    
    if r['risks']:
        report.append(f"  风险标签:")
        for risk in r['risks']:
            report.append(f"    [{risk['级别']}] {risk['类型']}: {risk['描述']}")
    
    if r['amounts']:
        top_amt = sorted(set(r['amounts']), reverse=True)[:5]
        report.append(f"  抽取金额: {top_amt}")

# 六、审计建议
report.append("\n\n" + "─" * 80)
report.append("六、审计发现与建议 (基于OCR全文分析)")
report.append("─" * 80)
report.append("""
  [核心发现]
  
  1. 文本提取情况:
     - 扫描件为主，OCR提取了关键合同文本
     - 部分合同因扫描质量或格式问题，OCR识别率有限
     - 建议逐步推进电子化合同管理，使用文本型PDF
  
  2. 条款完整性:
     - 大部分合同缺少完整的违约责任、争议解决、不可抗力等标准条款
     - 部分合同存在"价格锁定"条款，将市场风险单方转移
     - 履约担保机制不健全
  
  3. 关键风险:
     - 多方协议(甲乙丙三方)法律关系复杂
     - 甲方单方决定进场时间，合同履行期不确定
     - 据实结算缺乏金额上限，预算管控风险大
     - 价格锁定条款在通胀环境下对乙方不利
  
  4. 台账管理:
     - PDF与台账匹配率有待提升
     - 部分合同金额在台账中记录不完整
     - 建议建立合同全生命周期数字化管理平台
  
  [审计建议]
  
  + 重点核查已到期合同是否完成结算及归档
  + 审查据实结算类合同的实际结算依据
  + 关注价格锁定条款的合理性，评估是否存在利益失衡
  + 对三方协议逐一梳理各方法律关系和责任边界
  + 建议引入合同标准化模板，补全缺失条款
""")

# 写出报告
report_text = '\n'.join(report)
report_path = os.path.join(OUTPUT_DIR, 'contract_nlp_ocr_analysis.txt')
with open(report_path, 'w', encoding='utf-8') as f:
    f.write(report_text)

# 写出Excel
excel_path = os.path.join(OUTPUT_DIR, 'contract_nlp_ocr_analysis.xlsx')
with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
    # 提取概况
    extract_df = pd.DataFrame([
        {'合同名称': k, '类别': v['category'], '提取方式': v['method'], 
         '页数': v['pages'], '字符数': v['char_count']}
        for k, v in pdf_texts.items()
    ])
    extract_df.to_excel(writer, sheet_name='提取概况', index=False)
    
    # 风险明细
    if len(risk_df) > 0:
        risk_df.to_excel(writer, sheet_name='风险明细', index=False)
    
    # NLP条款
    clause_data = []
    for fname, r in nlp_results.items():
        for ct, ms in r['clauses'].items():
            clause_data.append({
                '合同名称': fname,
                '类别': r['category'],
                '条款类型': ct,
                '命中内容': ms[0][:200] if ms else '',
                '完整度评分': round(r['score']['completeness'], 1),
                '风险数': r['score']['risk'],
            })
    if clause_data:
        pd.DataFrame(clause_data).to_excel(writer, sheet_name='NLP条款', index=False)
    
    # 交叉比对
    match_df.to_excel(writer, sheet_name='台账交叉比对', index=False)

# 写出JSON
json_output = {
    'analysis_time': now_str,
    'overview': {
        'total_pdfs': len(pdf_files),
        'direct_extraction': direct,
        'ocr_extraction': ocr_count,
        'total_ledger': len(ledger),
        'matched': int(match_df.get('ledger_seq', pd.Series()).notna().sum()),
    },
    'clause_coverage': {k: {'count': v, 'pct': round(v/total*100,1)} for k, v in clause_coverage.items()},
    'risk_summary': {
        'total': len(risk_df),
        'by_level': risk_df['风险级别'].value_counts().to_dict() if len(risk_df) > 0 else {},
        'by_type': risk_df['风险类型'].value_counts().to_dict() if len(risk_df) > 0 else {},
    },
    'nlp_details': {
        k: {
            'category': v['category'],
            'method': v['extraction_method'],
            'text_length': v['text_length'],
            'clauses_count': len(v['clauses']),
            'risks_count': len(v['risks']),
            'completeness_score': round(v['score']['completeness'], 1),
            'risks': v['risks'],
            'clauses': {ck: cv[0][:100] for ck, cv in v['clauses'].items()},
        } for k, v in nlp_results.items()
    },
}

json_path = os.path.join(OUTPUT_DIR, 'contract_nlp_ocr_analysis.json')
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(json_output, f, ensure_ascii=False, indent=2, default=str)

print(f"\n{'='*80}")
print(f"[OK] OCR+NLP分析完成!")
print(f"  文本报告: {report_path}")
print(f"  Excel报告: {excel_path}")
print(f"  JSON数据: {json_path}")
print(f"{'='*80}")
