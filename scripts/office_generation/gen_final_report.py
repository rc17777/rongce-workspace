"""
直接基于已有OCR结果生成最终报告 (10份已完成)
"""
import re, os, sys, json, time
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
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 收集所有PDF以建立映射
pdf_map = {}  # safe_name -> (filename, category, path)
for root, dirs, files in os.walk(CONTRACT_DIR):
    for f in files:
        if f.lower().endswith('.pdf'):
            safe = re.sub(r'[^\w\-.]', '_', f)[:40]
            pdf_map[safe] = (f, os.path.basename(root), os.path.join(root, f))

# 读取已有OCR结果
ocr_data = {}
for f in os.listdir(TEMP_DIR):
    if not f.endswith('_result.json'):
        continue
    safe = f.replace('_result.json', '')
    try:
        with open(os.path.join(TEMP_DIR, f), 'r', encoding='utf-8') as fh:
            j = json.load(fh)
        if j.get('error') and not j.get('total_chars'):
            continue
        fn, cat, path = pdf_map.get(safe, (safe, 'unknown', ''))
        ocr_data[fn] = {'cat': cat, 'path': path, 'pages': j.get('total_pages', 0),
                        'chars': j.get('total_chars', 0), 'conf': j.get('avg_confidence', 0),
                        'text': '\n'.join([r.get('text','') for r in j.get('results',[])])}
    except:
        continue

print(f"有效OCR结果: {len(ocr_data)}份")
for fn, d in ocr_data.items():
    print(f"  {d['chars']}字 {d['conf']}% {d['pages']}p | {fn[:60]}")

# 加载台账
ledger = pd.read_excel(LEDGER_PATH, header=None)
data = ledger.iloc[2:].copy()
data.columns = ['序号','合同名称','合同编号','签订日期','合同相对方','相对方联系方式',
                '合同范围及内容','合同期','双方权利义务','已到期','合同含税总价','不含税价',
                '提前终止条件','已结算金额','收付款方式','是否有履约担保','履约保证金','费用类别','合同类型']
data = data[data['合同名称'].notna()].reset_index(drop=True)

# NLP
class A:
    P = {
        '甲方': [r'甲方[：:]\s*(.+?)(?:[。；\n]|乙方|$)'],
        '乙方': [r'乙方[：:]\s*(.+?)(?:[。；\n]|甲方|丙方|$)'],
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
    def a(self,cid,text,cat=''):
        r={'id':cid,'cat':cat,'len':len(text),'cls':{},'risks':[],'amts':[],'sc':{'comp':0,'risk':0}}
        for ct,ps in self.P.items():
            ms=[]
            for p in ps:
                for f in re.findall(p,text,re.I|re.S)[:3]:
                    mt=re.sub(r'\s+',' ',f if isinstance(f,str) else ' '.join(str(x) for x in f if x))[:150]
                    if mt.strip(): ms.append(mt)
            if ms: r['cls'][ct]=ms
        for a in re.findall(r'(\d[\d,.]*)\s*(?:万元|元|亿)',text):
            try:
                v=float(a.replace(',',''))
                if 100<v<1e11: r['amts'].append(v)
            except: pass
        self._r(r,text)
        r['sc']['comp']=len(r['cls'])/len(self.P)*100
        r['sc']['risk']=len(r['risks'])
        return r
    def _r(self,r,t):
        if re.search(r'不因市场.*?调整|不含税.*?不因',t): r['risks'].append({'l':'高','t':'价格锁定','d':'锁价不因市场/政策调整'})
        if re.search(r'以甲方.*?书面.*?为准',t): r['risks'].append({'l':'高','t':'单方决定权','d':'甲方单方决定关键时间节点'})
        if re.search(r'包括但不限于.*?一切费用',t): r['risks'].append({'l':'高','t':'费用兜底','d':'无限责任风险'})
        if re.search(r'丙方|第三方.*?责任',t): r['risks'].append({'l':'中','t':'三方关系','d':'三方法律关系'})
        if re.search(r'据实结算|据实.*?支付',t): r['risks'].append({'l':'中','t':'据实结算','d':'缺金额上限管控'})
        if re.search(r'委托.*?期限.*?(?:甲方终止|另行通知)',t): r['risks'].append({'l':'中','t':'单方终止','d':'甲方可单方终止'})
        if not re.search(r'履约.*?(?:保证金|担保|保函)',t): r['risks'].append({'l':'低','t':'无履约担保','d':'未设履约担保'})
        if not re.search(r'争议.*?(?:解决|管辖|仲裁|诉讼)',t): r['risks'].append({'l':'低','t':'无争议解决','d':'缺争议解决条款'})
        if not re.search(r'不可抗力',t): r['risks'].append({'l':'低','t':'无不可抗力','d':'缺不可抗力条款'})
        ed=re.findall(r'(\d{4})[年./-](\d{1,2})[月./-](\d{1,2})日?',t)
        if ed:
            try:
                y,m,d=int(ed[-1][0]),int(ed[-1][1]),int(ed[-1][2])
                dl=(datetime(y,m,d)-datetime.now()).days
                if dl<0: r['risks'].append({'l':'高','t':'已过期','d':f'{datetime(y,m,d).strftime("%Y-%m-%d")}'})
                elif dl<90: r['risks'].append({'l':'中','t':'即将到期','d':f'剩余{dl}天'})
            except: pass

an=A()
results={}
for fn,d in ocr_data.items():
    results[fn]=an.a(fn,d['text'],d['cat'])
    results[fn]['ocr_chars']=d['chars']
    results[fn]['ocr_conf']=d['conf']
    results[fn]['pages']=d['pages']
    print(f"  NLP: {fn[:45]} -> {len(results[fn]['cls'])} clauses, {len(results[fn]['risks'])} risks")

# 匹配台账
def mtc(nm,df):
    nc=nm.replace('.pdf','').replace('-扫描件','').strip()
    for idx,row in df.iterrows():
        cd=str(row['合同编号']) if pd.notna(row['合同编号']) else ''
        if cd!='nan' and cd in nc: return idx
        nm2=str(row['合同名称']) if pd.notna(row['合同名称']) else ''
        if len(nm2)>5:
            kp=re.findall(r'[\u4e00-\u9fa5A-Za-z0-9]{4,}',nm2)
            if sum(1 for k in kp if k in nc)>=2: return idx
    return None

# 汇总
now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
cc={}
for r in results.values():
    for ct in r['cls']: cc[ct]=cc.get(ct,0)+1

ars=[]
for fn,r in results.items():
    for rk in r['risks']:
        ars.append({'合同':fn,'类别':r['cat'],'级别':rk['l'],'类型':rk['t'],'描述':rk['d']})
rdf=pd.DataFrame(ars)

mts=[]
for fn,d in ocr_data.items():
    r=results[fn]
    idx=mtc(fn,data)
    row={'pdf':fn,'cat':d['cat'],'ocr_chars':d['chars'],'ocr_conf':d['conf'],
         'pages':d['pages'],'nlp_clauses':len(r['cls']),'nlp_risks':len(r['risks']),
         'comp':round(r['sc']['comp'],1)}
    if idx is not None:
        lr=data.iloc[idx]
        row.update({'lseq':lr['序号'],'lname':lr['合同名称'],'lno':lr['合同编号'],
                    'ltype':lr['合同类型'],'lprice':lr['合同含税总价']})
    mts.append(row)
mdf=pd.DataFrame(mts)

# 报告
rl=[]
rl.append("="*100)
rl.append(f"    天府广场项目合同NLP深度分析 (Tesseract.js OCR)")
rl.append(f"    {now} | OCR: {len(ocr_data)}/21份 | 风险: {len(rdf)}个")
rl.append("="*100)

rl.append("\n\n一、OCR文本提取概况")
rl.append("-"*60)
tc=sum(r['ocr_chars'] for r in results.values())
avgs=[r['ocr_conf'] for r in results.values() if r['ocr_conf']>0]
ac=int(np.mean(avgs)) if avgs else 0
rl.append(f"  成功: {len(ocr_data)}/21 | 总字符: {tc:,} | 平均置信: {ac}%")
for fn,r in sorted(results.items(), key=lambda x: x[1]['ocr_chars'], reverse=True):
    bl=min(30,r['ocr_chars']//500)
    rl.append(f"  {r['ocr_chars']:6d}字 [{'█'*bl}{'░'*(30-bl)}] 置信{r['ocr_conf']}% | {fn[:55]}")

rl.append("\n\n二、NLP条款覆盖度")
rl.append("-"*60)
for ct,cnt in sorted(cc.items(), key=lambda x: x[1], reverse=True):
    pct=round(cnt/len(results)*100,1); bl=int(pct/5)
    rl.append(f"  {ct:8s} [{'█'*bl}{'░'*(20-bl)}] {pct:5.1f}% ({cnt}/{len(results)})")

rl.append("\n\n三、风险标识")
rl.append("-"*60)
if len(rdf)>0:
    lc=rdf['级别'].value_counts(); tp=rdf['类型'].value_counts()
    rl.append(f"  共{len(rdf)}个风险, {rdf['合同'].nunique()}份合同")
    for lv in ['高','中','低']: rl.append(f"  {lv}: {lc.get(lv,0)}个")
    for t,n in tp.items(): rl.append(f"  {t}: {n}处")
    for lv in ['高','中','低']:
        sub=rdf[rdf['级别']==lv]
        if len(sub)>0:
            rl.append(f"\n  【{lv}风险】")
            for _,row in sub.iterrows():
                rl.append(f"    [{row['类型']}] {row['合同'][:40]}: {row['描述']}")

rl.append("\n\n四、台账交叉比对")
rl.append("-"*60)
mc=mdf['lseq'].notna().sum()
rl.append(f"  匹配: {mc}/{len(ocr_data)}")
for _,row in mdf.iterrows():
    if pd.notna(row.get('lseq')):
        rl.append(f"  v {row['pdf'][:35]} -> #{int(row['lseq'])} {row.get('lname','')}")

rl.append("\n\n五、逐份合同NLP详情")
rl.append("-"*60)
for fn,r in sorted(results.items()):
    rl.append(f"\n{'─'*60}")
    rl.append(f"[{r['cat']}] {fn}")
    rl.append(f"OCR: {r['ocr_chars']}字/{r['pages']}p 置信{r['ocr_conf']}% | 条款{r['sc']['comp']:.0f}% | 风险{r['sc']['risk']}")
    if r['cls']:
        for ct,ms in r['cls'].items():
            rl.append(f"  + {ct}: {ms[0][:100]}")
    for rk in r['risks']:
        rl.append(f"  [{rk['l']}] {rk['t']}: {rk['d']}")
    if r['amts']:
        rl.append(f"  金额: {sorted(set(r['amts']), reverse=True)[:5]}")

rp=os.path.join(OUTPUT_DIR,'contract_nlp_tesseract_final.txt')
with open(rp,'w',encoding='utf-8') as f: f.write('\n'.join(rl))

ep=os.path.join(OUTPUT_DIR,'contract_nlp_tesseract_final.xlsx')
with pd.ExcelWriter(ep,engine='openpyxl') as w:
    mdf.to_excel(w,sheet_name='OCR概况',index=False)
    if len(rdf)>0: rdf.to_excel(w,sheet_name='风险明细',index=False)
    cd=[]
    for fn,r in results.items():
        for ct,ms in r['cls'].items():
            cd.append({'合同':fn,'类别':r['cat'],'条款':ct,'内容':ms[0][:200] if ms else '','完整度':round(r['sc']['comp'],1)})
    if cd: pd.DataFrame(cd).to_excel(w,sheet_name='NLP条款',index=False)

print(f"\n[OK] 报告: {rp}")
print(f"Excel: {ep}")

# 列出未完成
completed = set(ocr_data.keys())
all_pdfs = set()
for root, dirs, files in os.walk(CONTRACT_DIR):
    for f in files:
        if f.lower().endswith('.pdf'):
            all_pdfs.add(f)
pending = all_pdfs - completed
print(f"\n未完成({len(pending)}份):")
for p in sorted(pending):
    print(f"  {p[:80]}")
