"""
补跑剩余11份PDF + 全量NLP分析
"""
import re, os, sys, json, fitz, subprocess, shutil, time
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

CONTRACT_DIR = r"C:\Users\scrccpa\Desktop\成都轨道资源资料\业主发送资料\天府广场项目2026年专项审计资料清单（第一批）\1合同协议"
LEDGER_PATH = r"C:\Users\scrccpa\Desktop\成都资源公司=4.30\天府广场合同台账-2024-2025.xlsx"
OUTPUT_DIR = r"D:\openclaw-workspace\output\contract_analysis"
TEMP_DIR = os.path.join(OUTPUT_DIR, "tesseract_batch")
BATCH_OCR = r"D:\openclaw-workspace\scripts\batch_ocr.js"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 检查已有结果
existing = set()
for f in os.listdir(TEMP_DIR):
    if f.endswith('_result.json'):
        base = f.replace('_result.json', '')
        existing.add(base)

print(f"已有OCR结果: {len(existing)}")

# 收集所有PDF
pdf_files = []
for root, dirs, files in os.walk(CONTRACT_DIR):
    for f in files:
        if f.lower().endswith('.pdf'):
            pdf_files.append((os.path.join(root, f), os.path.basename(root), f))

# 找出未处理的
todo = []
for pp, cat, fn in pdf_files:
    safe = re.sub(r'[^\w\-.]', '_', fn)[:40]
    if safe not in existing:
        todo.append((pp, cat, fn, safe))

print(f"需要OCR: {len(todo)}份")

# 顺序OCR未处理的
for pp, cat, fn, safe in todo:
    print(f"\n处理: [{cat}] {fn[:60]}")
    
    # 转图片
    img_dir = os.path.join(TEMP_DIR, safe)
    if not os.path.exists(img_dir):
        os.makedirs(img_dir, exist_ok=True)
        doc = fitz.open(pp)
        total = min(len(doc), 50)
        for i in range(total):
            pix = doc[i].get_pixmap(dpi=200)
            pix.save(os.path.join(img_dir, f"p{i+1:03d}.png"))
        doc.close()
        print(f"  转换: {total}页")
    else:
        imgs = [f for f in os.listdir(img_dir) if f.endswith('.png')]
        total = len(imgs)
        print(f"  已有图片: {total}页")
    
    # OCR
    out_json = img_dir + '_result.json'
    if os.path.exists(out_json):
        print(f"  跳过(已有结果)")
        continue
    
    t0 = time.time()
    proc = subprocess.run(['node', BATCH_OCR, img_dir, out_json], 
                         capture_output=True, text=True, encoding='utf-8', errors='replace',
                         timeout=600, cwd=os.path.dirname(BATCH_OCR))
    elapsed = time.time() - t0
    
    if os.path.exists(out_json):
        with open(out_json, 'r', encoding='utf-8') as f:
            j = json.load(f)
        print(f"  OCR完成: {j.get('total_chars',0)}字, {j.get('avg_confidence',0)}% ({elapsed:.0f}s)")
    else:
        print(f"  失败: {proc.stderr[:200]}")

# ============================================================
# 全量NLP分析
# ============================================================
print(f"\n\n{'='*60}")
print("全量NLP分析")
print(f"{'='*60}")

# 收集中间结果
existing2 = set()
for f in os.listdir(TEMP_DIR):
    if f.endswith('_result.json'):
        existing2.add(f.replace('_result.json', ''))

print(f"OCR结果总数: {len(existing2)}")

# 反向映射
safe_to_name = {}
for pp, cat, fn in pdf_files:
    safe = re.sub(r'[^\w\-.]', '_', fn)[:40]
    safe_to_name[safe] = (fn, cat)

# 加载台账
ledger = pd.read_excel(LEDGER_PATH, header=None)
data = ledger.iloc[2:].copy()
data.columns = ['序号','合同名称','合同编号','签订日期','合同相对方','相对方联系方式',
                '合同范围及内容','合同期','双方权利义务','已到期','合同含税总价','不含税价',
                '提前终止条件','已结算金额','收付款方式','是否有履约担保','履约保证金','费用类别','合同类型']
data = data[data['合同名称'].notna()].reset_index(drop=True)

# NLP分析器
class Analyzer:
    PATTERNS = {
        '甲方信息': [r'甲方[：:]\s*(.+?)(?:[。；\n]|乙方|$)'],
        '乙方信息': [r'乙方[：:]\s*(.+?)(?:[。；\n]|甲方|丙方|$)'],
        '合同金额': [r'(?:合同(?:总价|金额|价款|价格)|含税总价)[：:]*.*?(\d[\d,.]+\s*(?:万元|元|亿))', r'(?:¥|￥)\s*(\d[\d,.]+)'],
        '付款方式': [r'(?:付款|支付|结算)\s*(?:方式|方法|条件).*?[：:]\s*(.+?)(?:[。；]|\n)', r'据实.*?(?:结算|支付|月结)'],
        '合同期限': [r'(?:合同期|服务期|维保期|租赁期).*?[：:]\s*(.+?)(?:[。；]|\n)'],
        '违约责任': [r'(?:违约|违约责任|违约金).*?[：:]\s*(.+?)(?:[。；]|\n)'],
        '履约担保': [r'履约.*?(?:保证金|担保|保函)', r'保证金.*?(\d[\d,.]+\s*(?:万元|元))'],
        '争议解决': [r'(?:争议|纠纷).*?(?:解决|管辖|仲裁|诉讼)'],
        '不可抗力': [r'不可抗力'],
        '价格调整': [r'价格.*?(?:调整|变动|不因市场)', r'不因.*?(?:市场|政策).*?(?:调整|变动)'],
        '质保条款': [r'(?:质保|质量保证|保修).*?(?:期|期限).*?(\d+\s*[年月])'],
        '服务范围': [r'(?:服务|实施|维保|租赁)\s*(?:范围|内容|区域).*?[：:]\s*(.+?)(?:[。；]|\n)'],
    }
    
    def analyze(self, cid, text, cat=''):
        r = {'id': cid, 'cat': cat, 'len': len(text), 'cls': {}, 'risks': [], 'amts': [], 'scr': {'comp': 0, 'risk': 0}}
        for ct, ps in self.PATTERNS.items():
            ms = []
            for p in ps:
                for f in re.findall(p, text, re.IGNORECASE|re.DOTALL)[:3]:
                    mt = re.sub(r'\s+', ' ', f if isinstance(f,str) else ' '.join(str(x) for x in f if x))[:150]
                    if mt.strip(): ms.append(mt)
            if ms: r['cls'][ct] = ms
        for a in re.findall(r'(\d[\d,.]*)\s*(?:万元|元|亿)', text):
            try:
                v = float(a.replace(',',''))
                if 100 < v < 1e11: r['amts'].append(v)
            except: pass
        self._risks(r, text)
        r['scr']['comp'] = len(r['cls'])/len(self.PATTERNS)*100
        r['scr']['risk'] = len(r['risks'])
        return r
    
    def _risks(self, r, t):
        if re.search(r'不因市场.*?调整|不含税.*?不因', t): r['risks'].append({'lvl':'高','type':'价格锁定','desc':'锁价，不因市场/政策调整'})
        if re.search(r'以甲方.*?书面.*?为准', t): r['risks'].append({'lvl':'高','type':'单方决定权','desc':'甲方单方决定关键时间'})
        if re.search(r'包括但不限于.*?一切费用', t): r['risks'].append({'lvl':'高','type':'费用兜底','desc':'兜底条款'})
        if re.search(r'丙方|第三方.*?责任', t): r['risks'].append({'lvl':'中','type':'三方关系','desc':'三方法律关系'})
        if re.search(r'据实结算|据实.*?支付', t): r['risks'].append({'lvl':'中','type':'据实结算','desc':'缺金额上限'})
        if re.search(r'委托.*?期限.*?(?:甲方终止|另行通知)', t): r['risks'].append({'lvl':'中','type':'单方终止','desc':'甲方可单方终止'})
        if not re.search(r'履约.*?(?:保证金|担保|保函)', t): r['risks'].append({'lvl':'低','type':'无履约担保','desc':'未设履约担保'})
        if not re.search(r'争议.*?(?:解决|管辖|仲裁|诉讼)', t): r['risks'].append({'lvl':'低','type':'无争议解决','desc':'缺争议解决'})
        if not re.search(r'不可抗力', t): r['risks'].append({'lvl':'低','type':'无不可抗力','desc':'缺不可抗力'})
        ed = re.findall(r'(\d{4})[年./-](\d{1,2})[月./-](\d{1,2})日?', t)
        if ed:
            try:
                y,m,d = int(ed[-1][0]),int(ed[-1][1]),int(ed[-1][2])
                dl = (datetime(y,m,d)-datetime.now()).days
                if dl < 0: r['risks'].append({'lvl':'高','type':'已过期','desc':f'{datetime(y,m,d).strftime("%Y-%m-%d")}'})
                elif dl < 90: r['risks'].append({'lvl':'中','type':'即将到期','desc':f'剩余{dl}天'})
            except: pass

analyzer = Analyzer()

# 读取OCR结果并NLP
results = {}
for safe_dir in sorted(existing2):
    result_path = os.path.join(TEMP_DIR, safe_dir + '_result.json')
    try:
        with open(result_path, 'r', encoding='utf-8') as f:
            ocr = json.load(f)
    except:
        continue
    
    fn, cat = safe_to_name.get(safe_dir, (safe_dir, 'unknown'))
    if ocr.get('error'):
        text = f"[OCR_ERROR: {ocr['error']}]"
    else:
        text = '\n'.join([r.get('text','') for r in ocr.get('results',[])])
    
    nr = analyzer.analyze(fn, text, cat)
    nr['ocr_chars'] = ocr.get('total_chars', 0)
    nr['ocr_conf'] = ocr.get('avg_confidence', 0)
    nr['ocr_pages'] = ocr.get('total_pages', 0)
    results[fn] = nr

print(f"NLP分析完成: {len(results)}份")

# 台账匹配
def match_ledger(nm, df):
    nc = nm.replace('.pdf','').replace('-扫描件','').strip()
    for idx, row in df.iterrows():
        cd = str(row['合同编号']) if pd.notna(row['合同编号']) else ''
        if cd != 'nan' and cd in nc: return idx
        nm2 = str(row['合同名称']) if pd.notna(row['合同名称']) else ''
        if len(nm2)>5:
            kp = re.findall(r'[\u4e00-\u9fa5A-Za-z0-9]{4,}', nm2)
            if sum(1 for k in kp if k in nc) >= 2: return idx
    return None

# 生成报告
now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
clause_cov = {}
for r in results.values():
    for ct in r['cls']: clause_cov[ct] = clause_cov.get(ct, 0) + 1

all_risks = []
for fn, r in results.items():
    for risk in r['risks']:
        all_risks.append({'合同':fn,'类别':r['cat'],'级别':risk['lvl'],'类型':risk['type'],'描述':risk['desc']})
risk_df = pd.DataFrame(all_risks)

matches = []
for fn, r in results.items():
    idx = match_ledger(fn, data)
    row = {'pdf_file':fn,'category':r['cat'],'ocr_chars':r['ocr_chars'],'ocr_conf':r['ocr_conf'],
           'pages':r['ocr_pages'],'nlp_clauses':len(r['cls']),'nlp_risks':len(r['risks']),
           'completeness':round(r['scr']['comp'],1)}
    if idx is not None:
        lr = data.iloc[idx]
        row.update({'ledger_seq':lr['序号'],'ledger_name':lr['合同名称'],'ledger_no':lr['合同编号'],
                    'ledger_type':lr['合同类型'],'ledger_price':lr['合同含税总价']})
    matches.append(row)
match_df = pd.DataFrame(matches)

report_lines = []
report_lines.append("="*100)
report_lines.append(f"    天府广场合同NLP深度分析 (Tesseract.js OCR) - {now_str}")
report_lines.append(f"    OCR成功: {len(results)}/21份 | 总风险: {len(risk_df)}个")
report_lines.append("="*100)

report_lines.append("\n\n一、OCR提取概况")
report_lines.append("-"*60)
total_chars = sum(r['ocr_chars'] for r in results.values())
avgs = [r['ocr_conf'] for r in results.values() if r['ocr_conf']>0]
avg_conf = np.mean(avgs) if avgs else 0
report_lines.append(f"  成功: {len(results)}/21份 | 总字符: {total_chars:,} | 平均置信: {avg_conf:.0f}%")
for fn, r in sorted(results.items(), key=lambda x: x[1]['ocr_chars'], reverse=True):
    bl = min(30, r['ocr_chars']//500)
    report_lines.append(f"  {r['ocr_chars']:6d}字 [{'█'*bl}{'░'*(30-bl)}] 置信{r['ocr_conf']}% | {fn[:55]}")

report_lines.append("\n\n二、NLP条款覆盖度")
report_lines.append("-"*60)
for ct, cnt in sorted(clause_cov.items(), key=lambda x: x[1], reverse=True):
    pct = round(cnt/len(results)*100, 1)
    bl = int(pct/5)
    report_lines.append(f"  {ct:10s} [{'█'*bl}{'░'*(20-bl)}] {pct:5.1f}% ({cnt}/{len(results)})")

report_lines.append("\n\n三、风险标识")
report_lines.append("-"*60)
if len(risk_df)>0:
    lc = risk_df['级别'].value_counts()
    tc = risk_df['类型'].value_counts()
    report_lines.append(f"  共{len(risk_df)}个, 涉及{risk_df['合同'].nunique()}份")
    for lv in ['高','中','低']: report_lines.append(f"  {lv}: {lc.get(lv,0)}")
    for tp,n in tc.items(): report_lines.append(f"  {tp}: {n}")
    for lv in ['高','中','低']:
        sub = risk_df[risk_df['级别']==lv]
        if len(sub)>0:
            report_lines.append(f"\n  [{lv}风险]")
            for _,row in sub.head(15).iterrows():
                report_lines.append(f"    [{row['类型']}] {row['合同'][:45]}: {row['描述']}")

report_lines.append("\n\n四、台账交叉比对")
report_lines.append("-"*60)
mc = match_df['ledger_seq'].notna().sum()
report_lines.append(f"  匹配: {mc}/{len(results)}")
for _, row in match_df.iterrows():
    if pd.notna(row.get('ledger_seq')):
        report_lines.append(f"  v {row['pdf_file'][:35]} -> #{row['ledger_seq']} {row.get('ledger_name','')} ({row.get('ledger_type','')})")

report_lines.append("\n\n五、逐份详情")
report_lines.append("-"*60)
for fn, r in sorted(results.items()):
    report_lines.append(f"\n{'─'*60}")
    report_lines.append(f"[{r['cat']}] {fn}")
    report_lines.append(f"OCR: {r['ocr_chars']}字/{r['ocr_pages']}页 置信{r['ocr_conf']}% | 条款{r['scr']['comp']:.0f}% | 风险{r['scr']['risk']}")
    if r['cls']:
        for ct, ms in r['cls'].items():
            report_lines.append(f"  + {ct}: {ms[0][:100]}")
    if r['risks']:
        for rk in r['risks']:
            report_lines.append(f"  [{rk['lvl']}] {rk['type']}: {rk['desc']}")
    if r['amts']:
        report_lines.append(f"  金额: {sorted(set(r['amts']), reverse=True)[:5]}")

report_path = os.path.join(OUTPUT_DIR, 'contract_nlp_final_report.txt')
with open(report_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(report_lines))

excel_path = os.path.join(OUTPUT_DIR, 'contract_nlp_final.xlsx')
with pd.ExcelWriter(excel_path, engine='openpyxl') as w:
    match_df.to_excel(w, sheet_name='OCR概况', index=False)
    if len(risk_df)>0: risk_df.to_excel(w, sheet_name='风险明细', index=False)
    cd = []
    for fn, r in results.items():
        for ct, ms in r['cls'].items():
            cd.append({'合同':fn,'类别':r['cat'],'条款类型':ct,'内容':ms[0][:200] if ms else '','完整度':round(r['scr']['comp'],1)})
    if cd: pd.DataFrame(cd).to_excel(w, sheet_name='NLP条款', index=False)

print(f"\n[OK] 完成! 报告: {report_path}")
