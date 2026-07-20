"""
天府广场合同OCR+NLP v5 - 并行Tesseract.js
==========================================
管道: pymupdf(PDF→PNG批量) → 并行Tesseract.js OCR → NLP
"""
import pandas as pd
import numpy as np
import re, os, sys, json, fitz, subprocess, shutil, time
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 配置
# ============================================================
CONTRACT_DIR = r"C:\Users\scrccpa\Desktop\成都轨道资源资料\业主发送资料\天府广场项目2026年专项审计资料清单（第一批）\1合同协议"
LEDGER_PATH = r"C:\Users\scrccpa\Desktop\成都资源公司=4.30\天府广场合同台账-2024-2025.xlsx"
OUTPUT_DIR = r"D:\openclaw-workspace\output\contract_analysis"
TEMP_DIR = os.path.join(OUTPUT_DIR, "tesseract_batch")
BATCH_OCR = r"D:\openclaw-workspace\scripts\batch_ocr.js"
MAX_WORKERS = 3  # 并行OCR进程数
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# Phase 1: PDF→PNG (快速，不需OCR)
# ============================================================
def pdf_to_images(pdf_path, filename, dpi=200):
    """将PDF所有页转换为PNG，返回图片目录"""
    safe = re.sub(r'[^\w\-.]', '_', filename)[:40]
    img_dir = os.path.join(TEMP_DIR, safe)
    os.makedirs(img_dir, exist_ok=True)
    
    doc = fitz.open(pdf_path)
    total = min(len(doc), 50)
    for i in range(total):
        pix = doc[i].get_pixmap(dpi=dpi)
        pix.save(os.path.join(img_dir, f"p{i+1:03d}.png"))
    doc.close()
    return img_dir, total

# ============================================================
# Phase 2: 并行Tesseract.js OCR
# ============================================================
def ocr_one_pdf(img_dir):
    """调用batch_ocr.js处理一个PDF的全部页面"""
    out_json = img_dir + '_result.json'
    cmd = ['node', BATCH_OCR, img_dir, out_json]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', 
                            errors='replace', timeout=600, cwd=os.path.dirname(BATCH_OCR))
        if os.path.exists(out_json):
            with open(out_json, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        return {'error': str(e), 'dir': img_dir}
    return {'error': 'no output', 'dir': img_dir}

# ============================================================
# Phase 3: NLP分析器
# ============================================================
class ContractAnalyzer:
    PATTERNS = {
        '甲方信息': [r'甲方[：:]\s*(.+?)(?:[。；\n]|乙方|$)'],
        '乙方信息': [r'乙方[：:]\s*(.+?)(?:[。；\n]|甲方|丙方|$)'],
        '丙方信息': [r'丙方[：:]\s*(.+?)(?:[。；\n]|$)'],
        '合同金额': [r'(?:合同(?:总价|金额|价款|价格)|含税总价)[：:]*\s*.*?(\d[\d,.]+\s*(?:万元|元|亿))', r'(?:不含税.*?(?:金额|总价)).*?(\d[\d,.]+\s*(?:万元|元|亿))', r'(?:¥|￥)\s*(\d[\d,.]+)'],
        '付款方式': [r'(?:付款|支付|结算)\s*(?:方式|方法|条件).*?[：:]\s*(.+?)(?:[。；]|\n\n)', r'(?:据实.*?(?:结算|支付|月结))'],
        '合同期限': [r'(?:合同期|服务期|维保期|租赁期).*?[：:]\s*(.+?)(?:[。；]|\n)'],
        '违约责任': [r'(?:违约|违约责任|违约金).*?[：:]\s*(.+?)(?:[。；]|\n\n)', r'赔偿.*?(?:损失|金额).*?(\d[\d,.%]*)'],
        '履约担保': [r'履约.*?(?:保证金|担保|保函)', r'保证金.*?(\d[\d,.]+\s*(?:万元|元))'],
        '保险条款': [r'保险.*?(?:购买|承保|险种)'],
        '争议解决': [r'(?:争议|纠纷).*?(?:解决|管辖|仲裁|诉讼)'],
        '不可抗力': [r'不可抗力'],
        '保密条款': [r'(?:保密|商业秘密|保密义务)'],
        '价格调整': [r'(?:价格.*?(?:调整|变动|不因市场))', r'不因.*?(?:市场|政策).*?(?:调整|变动)'],
        '质保条款': [r'(?:质保|质量保证|保修).*?(?:期|期限).*?(\d+\s*[年月])'],
        '转包分包': [r'(?:转包|分包|不得.*?转让)'],
        '验收条款': [r'验收.*?(?:标准|条件|程序)'],
        '服务范围': [r'(?:服务|实施|维保|租赁)\s*(?:范围|内容|区域).*?[：:]\s*(.+?)(?:[。；]|\n)'],
    }
    
    def analyze(self, cid, text, category=''):
        result = {'contract_id': cid, 'category': category, 'text_length': len(text), 
                  'clauses': {}, 'risks': [], 'amounts': [], 'score': {'completeness': 0, 'risk': 0}}
        for ct, patterns in self.PATTERNS.items():
            matches = []
            for p in patterns:
                found = re.findall(p, text, re.IGNORECASE | re.DOTALL)
                for f in found[:3]:
                    mt = re.sub(r'\s+', ' ', f if isinstance(f,str) else ' '.join(str(x) for x in f if x))[:150]
                    if mt.strip(): matches.append(mt)
            if matches: result['clauses'][ct] = matches
        amounts = re.findall(r'(\d[\d,.]*)\s*(?:万元|元|亿)', text)
        for a in amounts:
            try:
                v = float(a.replace(',',''))
                if 100 < v < 1e11: result['amounts'].append(v)
            except: pass
        self._risks(result, text)
        result['score']['completeness'] = len(result['clauses'])/len(self.PATTERNS)*100
        result['score']['risk'] = len(result['risks'])
        return result
    
    def _risks(self, result, text):
        r = result['risks']
        if re.search(r'不因市场.*?调整|不含税.*?不因', text): r.append({'级别':'高','类型':'价格锁定','描述':'锁价，不因市场/政策调整'})
        if re.search(r'以甲方.*?书面.*?为准', text): r.append({'级别':'高','类型':'单方决定权','描述':'甲方单方决定关键时间节点'})
        if re.search(r'包括但不限于.*?一切费用|全部.*?费用.*?由.*?承担', text): r.append({'级别':'高','类型':'费用兜底','描述':'兜底条款，无限责任风险'})
        if re.search(r'丙方|第三方.*?责任', text): r.append({'级别':'中','类型':'三方关系','描述':'三方法律关系'})
        if re.search(r'据实结算|据实.*?支付', text): r.append({'级别':'中','类型':'据实结算','描述':'缺金额上限管控'})
        if re.search(r'委托.*?期限.*?(?:甲方终止|另行通知)', text): r.append({'级别':'中','类型':'单方终止权','描述':'甲方可单方终止委托'})
        if not re.search(r'履约.*?(?:保证金|担保|保函)', text): r.append({'级别':'低','类型':'无履约担保','描述':'未设履约担保'})
        if not re.search(r'争议.*?(?:解决|管辖|仲裁|诉讼)', text): r.append({'级别':'低','类型':'无争议解决','描述':'缺争议解决条款'})
        if not re.search(r'不可抗力', text): r.append({'级别':'低','类型':'无不可抗力','描述':'缺不可抗力条款'})
        ends = re.findall(r'(\d{4})[年./-](\d{1,2})[月./-](\d{1,2})日?', text)
        if ends:
            try:
                y,m,d = int(ends[-1][0]), int(ends[-1][1]), int(ends[-1][2])
                ed = datetime(y,m,d)
                days = (ed-datetime.now()).days
                if days < 0: r.append({'级别':'高','类型':'已过期','描述':f'{ed.strftime("%Y-%m-%d")}到期'})
                elif days < 90: r.append({'级别':'中','类型':'即将到期','描述':f'剩余{days}天'})
            except: pass

# ============================================================
# Phase 4: 台账
# ============================================================
def load_ledger(path):
    df = pd.read_excel(path, header=None)
    data = df.iloc[2:].copy()
    data.columns = ['序号','合同名称','合同编号','签订日期','合同相对方','相对方联系方式',
                    '合同范围及内容','合同期','双方权利义务','已到期','合同含税总价','不含税价',
                    '提前终止条件','已结算金额','收付款方式','是否有履约担保','履约保证金','费用类别','合同类型']
    return data[data['合同名称'].notna()].reset_index(drop=True)


# ============================================================
# Main Pipeline
# ============================================================
print("=" * 80)
print("天府广场合同OCR+NLP v5 (并行Tesseract.js)")
print("=" * 80)

# 收集PDF
pdf_files = []
for root, dirs, files in os.walk(CONTRACT_DIR):
    for f in files:
        if f.lower().endswith('.pdf'):
            pdf_files.append((os.path.join(root, f), os.path.basename(root), f))
print(f"\nPDF: {len(pdf_files)}份")

# Step 1: 全部PDF→PNG
print(f"\n[Step 1] PDF→PNG转换...")
start_t = time.time()
img_dirs = {}
for pdf_path, cat, fname in pdf_files:
    print(f"  转换: [{cat}] {fname[:50]}...")
    img_dir, pages = pdf_to_images(pdf_path, fname)
    img_dirs[fname] = {'dir': img_dir, 'category': cat, 'pages': pages, 'path': pdf_path}
print(f"  转换完成 ({time.time()-start_t:.0f}s)")

# Step 2: 并行OCR
print(f"\n[Step 2] 并行Tesseract.js OCR ({MAX_WORKERS} workers)...")
start_t = time.time()
ocr_results = {}
futures = {}
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
    for fname, info in img_dirs.items():
        fut = pool.submit(ocr_one_pdf, info['dir'])
        futures[fut] = fname
    
    done_count = 0
    for fut in as_completed(futures):
        fname = futures[fut]
        result = fut.result()
        ocr_results[fname] = result
        done_count += 1
        err = result.get('error', '')
        chars = result.get('total_chars', 0) if not err else 0
        conf = result.get('avg_confidence', 0) if not err else 0
        elapsed = time.time() - start_t
        print(f"  [{done_count}/{len(pdf_files)}] {fname[:45]}: {chars}字 置信{conf}% ({elapsed:.0f}s)")

# Step 3: NLP分析
print(f"\n[Step 3] NLP条款分析...")
analyzer = ContractAnalyzer()
nlp_results = {}
for fname, ocr_data in ocr_results.items():
    info = img_dirs[fname]
    if ocr_data.get('error'):
        text = f"[OCR_ERROR: {ocr_data['error']}]"
    else:
        text = '\n'.join([r.get('text','') for r in ocr_data.get('results', [])])
    
    result = analyzer.analyze(fname, text, info['category'])
    result['pages'] = info['pages']
    result['ocr_chars'] = ocr_data.get('total_chars', 0)
    result['ocr_confidence'] = ocr_data.get('avg_confidence', 0)
    nlp_results[fname] = result
    print(f"  {fname[:45]}: 条款{len(result['clauses'])}类 风险{len(result['risks'])}个 金额{len(result['amounts'])}个")

# Step 4: 台账匹配
print(f"\n[Step 4] 台账交叉比对...")
ledger = load_ledger(LEDGER_PATH)
def match_ledger(pdf_name, ldf):
    nc = pdf_name.replace('.pdf','').replace('-扫描件','').strip()
    for idx, row in ldf.iterrows():
        code = str(row['合同编号']) if pd.notna(row['合同编号']) else ''
        name = str(row['合同名称']) if pd.notna(row['合同名称']) else ''
        if code != 'nan' and code in nc: return idx
        if len(name) > 5:
            kp = re.findall(r'[\u4e00-\u9fa5A-Za-z0-9]{4,}', name)
            if sum(1 for k in kp if k in nc) >= 2: return idx
    return None

matches = []
for fname in pdf_files:
    idx = match_ledger(fname[2], ledger)
    info = img_dirs[fname[2]]
    nr = nlp_results.get(fname[2], {})
    row = {'pdf_file': fname[2], 'category': info['category'], 'pages': info['pages'],
           'ocr_chars': nr.get('ocr_chars',0), 'ocr_confidence': nr.get('ocr_confidence',0),
           'nlp_clauses': len(nr.get('clauses',{})), 'nlp_risks': len(nr.get('risks',[])),
           'completeness': round(nr.get('score',{}).get('completeness',0),1)}
    if idx is not None:
        lr = ledger.iloc[idx]
        row.update({'ledger_seq': lr['序号'], 'ledger_name': lr['合同名称'],
                    'ledger_no': lr['合同编号'], 'ledger_type': lr['合同类型'],
                    'ledger_price': lr['合同含税总价']})
    matches.append(row)
match_df = pd.DataFrame(matches)

# Step 5: 生成报告
print(f"\n[Step 5] 生成报告...")
now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# 条款覆盖度
clause_cov = {}
for r in nlp_results.values():
    for ct in r['clauses']: clause_cov[ct] = clause_cov.get(ct, 0) + 1

# 风险汇总
all_risks = []
for fname, r in nlp_results.items():
    for risk in r['risks']:
        all_risks.append({'合同名称':fname,'类别':r['category'],'风险级别':risk['级别'],
                         '风险类型':risk['类型'],'风险描述':risk['描述']})
risk_df = pd.DataFrame(all_risks)

report = []
report.append("="*100)
report.append("    天府广场项目合同NLP深度分析 (Tesseract.js OCR v5)")
report.append(f"    生成: {now_str} | 21份PDF全文OCR | {MAX_WORKERS}并行Worker")
report.append("="*100)

report.append("\n\n一、OCR提取概况")
report.append("-"*60)
ocr_ok = sum(1 for v in nlp_results.values() if v.get('ocr_chars',0) > 100)
total_chars = sum(v.get('ocr_chars',0) for v in nlp_results.values())
avg_conf = np.mean([v.get('ocr_confidence',0) for v in nlp_results.values() if v.get('ocr_confidence',0) > 0]) if ocr_ok else 0
report.append(f"  成功提取: {ocr_ok}/{len(pdf_files)}份 | 总字符: {total_chars:,} | 平均置信度: {avg_conf:.0f}%")
report.append(f"\n  合同OCR质量:")
for fname in sorted(nlp_results.keys(), key=lambda x: nlp_results[x].get('ocr_chars',0), reverse=True):
    nr = nlp_results[fname]
    bl = min(30, nr.get('ocr_chars',0)//500)
    conf_str = f"置信{nr.get('ocr_confidence',0)}%" if nr.get('ocr_confidence',0) > 0 else ""
    report.append(f"  {nr.get('ocr_chars',0):6d}字 [{'█'*bl}{'░'*(30-bl)}] {conf_str} {fname[:50]}")

report.append("\n\n二、NLP条款覆盖度")
report.append("-"*60)
for ct, cnt in sorted(clause_cov.items(), key=lambda x: x[1], reverse=True):
    pct = round(cnt/len(nlp_results)*100, 1)
    bl = int(pct/5)
    report.append(f"  {ct:10s} [{'█'*bl}{'░'*(20-bl)}] {pct:5.1f}% ({cnt}/{len(nlp_results)})")

report.append("\n\n三、风险标识")
report.append("-"*60)
if len(risk_df) > 0:
    lc = risk_df['风险级别'].value_counts()
    tc = risk_df['风险类型'].value_counts()
    report.append(f'  共{len(risk_df)}个风险，涉及{risk_df["合同名称"].nunique()}份合同')
    report.append(f'  级别: 高{lc.get("高",0)} 中{lc.get("中",0)} 低{lc.get("低",0)}')
    for tp, n in tc.items(): report.append(f'  {tp}: {n}处')
    for level in ['高','中','低']:
        sub = risk_df[risk_df['风险级别']==level]
        if len(sub) > 0:
            report.append(f'\n  [{level}风险]')
            for _, row in sub.head(15).iterrows():
                report.append(f"    [{row['风险类型']}] {row['合同名称'][:45]}: {row['风险描述']}")

report.append("\n\n四、台账交叉比对")
report.append("-"*60)
matched_count = match_df['ledger_seq'].notna().sum()
report.append(f"  匹配: {matched_count}/{len(pdf_files)}")
for _, row in match_df.iterrows():
    if pd.notna(row.get('ledger_seq')):
        report.append(f"  ✓ {row['pdf_file'][:40]} → #{row['ledger_seq']} {row['ledger_name']} ({row['ledger_type']})")
    else:
        report.append(f"  ✗ {row['pdf_file'][:40]} (未匹配)")

report.append("\n\n五、逐份详情")
report.append("-"*60)
for fname, r in sorted(nlp_results.items()):
    report.append(f"\n{'─'*60}")
    report.append(f"[{r['category']}] {fname}")
    report.append(f"OCR: {r.get('ocr_chars',0)}字 置信{r.get('ocr_confidence',0)}% | 条款{r['score']['completeness']:.0f}% | 风险{r['score']['risk']}")
    if r['clauses']:
        report.append(f"条款:")
        for ct, ms in r['clauses'].items():
            report.append(f"  + {ct}: {ms[0][:100]}")
    if r['risks']:
        for risk in r['risks']:
            report.append(f"  [{risk['级别']}] {risk['类型']}: {risk['描述']}")
    if r['amounts']:
        report.append(f"金额: {sorted(set(r['amounts']), reverse=True)[:5]}")

# 写出
report_path = os.path.join(OUTPUT_DIR, 'contract_nlp_tesseract_v5.txt')
with open(report_path, 'w', encoding='utf-8') as f: f.write('\n'.join(report))

excel_path = os.path.join(OUTPUT_DIR, 'contract_nlp_tesseract_v5.xlsx')
with pd.ExcelWriter(excel_path, engine='openpyxl') as w:
    match_df.to_excel(w, sheet_name='OCR概况', index=False)
    if len(risk_df) > 0: risk_df.to_excel(w, sheet_name='风险明细', index=False)
    cd = []
    for fn, r in nlp_results.items():
        for ct, ms in r['clauses'].items():
            cd.append({'合同名称':fn,'类别':r['category'],'条款类型':ct,
                       '命中内容':ms[0][:200] if ms else '','完整度':round(r['score']['completeness'],1)})
    if cd: pd.DataFrame(cd).to_excel(w, sheet_name='NLP条款', index=False)

print(f"\n[OK] 完成!")
print(f"  报告: {report_path}")
print(f"  Excel: {excel_path}")

# 清理临时文件
try: shutil.rmtree(TEMP_DIR)
except: pass
