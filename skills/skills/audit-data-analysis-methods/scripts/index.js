#!/usr/bin/env node
/**
 * 审计数据分析工具包 — 7大方法 Node.js版本
 * 
 * 用法: node index.js <方法编号> --input <文件> [参数]
 * 
 * 方法:
 *   01 描述性统计  --column   分析一列数据的均值/中位数/IQR
 *   02 相关性分析  --columns  多列相关系数矩阵
 *   03 回归分析    --target --features  预测模型+异常偏离
 *   04 聚类分析    --features --clusters  K-Means供应商分群
 *   05 异常检测    --column --method     IQR/Z分法
 *   06 关联规则    --columns --min-support Apriori规则挖掘
 *   07 时间序列    --date-col --value-col  趋势+季节性
 * 
 * 环境: Node.js, 依赖 csv-parse + exceljs
 */
const fs = require('fs');
const path = require('path');
const { parse } = require('csv-parse/sync');
const ExcelJS = require('exceljs');

// ============== 工具函数 ==============

async function readData(filepath) {
  if (filepath.endsWith('.xlsx')) return readXLSX(filepath);
  if (filepath.endsWith('.csv')) return readCSV(filepath);
  try { return readCSV(filepath); } catch(e) { return readXLSX(filepath); }
}

function readCSV(filepath) {
  const content = fs.readFileSync(filepath, 'utf8').trim();
  const records = parse(content, { columns: true, skip_empty_lines: true, bom: true, relax_column_count: true });
  if (!records || records.length === 0) throw new Error('空文件');
  return records;
}

async function readXLSX(filepath) {
  const wb = new ExcelJS.Workbook();
  await wb.xlsx.readFile(filepath);
  const ws = wb.worksheets[0];
  const rows = ws.getRows(1, ws.rowCount);
  if (!rows || rows.length === 0) throw new Error('空工作表');
  const headers = rows[0].values.filter(v => v !== undefined);
  const data = [];
  for (let i = 1; i < rows.length; i++) {
    const vals = rows[i].values;
    const row = {};
    headers.forEach((h, idx) => { row[h] = vals[idx+1] !== undefined ? vals[idx+1] : ''; });
    data.push(row);
  }
  const nonEmpty = data.filter(r => Object.values(r).some(v => v !== '' && v !== null && v !== undefined));
  return nonEmpty.length > 0 ? nonEmpty : data;
}

async function writeXLSX(filepath, sheets) {
  const wb = new ExcelJS.Workbook();
  if (!Array.isArray(sheets)) sheets = [{ name: '结果', data: sheets }];
  for (const s of sheets) {
    const ws = wb.addWorksheet(s.name || '结果');
    if (s.data && s.data.length > 0) {
      const headers = Object.keys(s.data[0]);
      ws.columns = headers.map(h => ({ header: h, key: h, width: Math.max(h.length * 2, 15) }));
      s.data.forEach(row => ws.addRow(row));
    }
  }
  await wb.xlsx.writeFile(filepath);
  console.log(`  ✅ ${path.basename(filepath)}`);
}

function getNumericCols(data, exclude = []) {
  return Object.keys(data[0]).filter(h => {
    if (exclude.includes(h)) return false;
    return data.map(r => parseFloat(r[h])).filter(v => !isNaN(v)).length > data.length * 0.5;
  });
}

function getVals(data, col) {
  return data.map(r => parseFloat(r[col])).filter(v => !isNaN(v));
}

function calcStats(vals) {
  const n = vals.length;
  const sorted = [...vals].sort((a,b)=>a-b);
  const mean = vals.reduce((a,b)=>a+b,0)/n;
  const median = n%2===0 ? (sorted[n/2-1]+sorted[n/2])/2 : sorted[Math.floor(n/2)];
  const freq = {};
  vals.forEach(v => { freq[v] = (freq[v]||0)+1; });
  let mode = vals[0], maxF = 1;
  for (const [v,c] of Object.entries(freq)) { if (c>maxF) { maxF=c; mode=parseFloat(v); } }
  const variance = vals.reduce((s,v)=>s+(v-mean)**2,0)/n;
  const std = Math.sqrt(variance);
  const Q1 = sorted[Math.floor(n*0.25)];
  const Q3 = sorted[Math.floor(n*0.75)];
  return { n, mean: round2(mean), median: round2(median), mode, std: round2(std), min: sorted[0], max: sorted[n-1], range: round2(sorted[n-1]-sorted[0]), Q1, Q3, IQR: round2(Q3-Q1), skew: round2(vals.reduce((s,v)=>s+((v-mean)/std)**3,0)/n), kurt: round2(vals.reduce((s,v)=>s+((v-mean)/std)**4,0)/n-3) };
}

function round2(v) { return Math.round(v*100)/100; }
function round4(v) { return Math.round(v*10000)/10000; }

// ============== 7种方法 ==============

async function method01(args) {
  const data = await readData(args.input);
  const col = args.column || getNumericCols(data)[0];
  const vals = getVals(data, col);
  const s = calcStats(vals);
  const rows = Object.entries(s).map(([k,v]) => ({ 指标: k, 数值: typeof v === 'number' ? round2(v) : v }));

  const threshold = 2 * s.std;
  const outliers = data.filter(r => { const v = parseFloat(r[col]); return !isNaN(v) && (v > s.mean+threshold || v < s.mean-threshold); });

  console.log(`\n📊 描述性统计: ${col}`);
  console.log('='.repeat(50));
  rows.forEach(r => console.log(`  ${r.指标.padEnd(10)}: ${r.数值}`));
  console.log(`\n⚠️ 异常值 (±2σ): ${outliers.length} 条`);

  const sheets = [{ name: '统计值', data: rows }];
  if (outliers.length) sheets.push({ name: '异常值', data: outliers.slice(0, 500) });
  await writeXLSX(args.output || './输出_描述性统计.xlsx', sheets);
}

async function method02(args) {
  const data = await readData(args.input);
  const cols = args.columns ? args.columns.split(',') : getNumericCols(data);
  const colVals = {};
  cols.forEach(c => { colVals[c] = getVals(data, c); });

  function pearson(a, b) {
    const n = Math.min(a.length,b.length); const ma = a.reduce((s,v)=>s+v,0)/n; const mb = b.reduce((s,v)=>s+v,0)/n;
    const num = a.slice(0,n).reduce((s,ai,i)=>s+(ai-ma)*(b[i]-mb),0);
    const da = Math.sqrt(a.slice(0,n).reduce((s,ai)=>s+(ai-ma)**2,0));
    const db = Math.sqrt(b.slice(0,n).reduce((s,bi)=>s+(bi-mb)**2,0));
    return da*db===0?0:num/(da*db);
  }

  const matrix = [], pairs = [];
  for (let i = 0; i < cols.length; i++) {
    const row = { 变量: cols[i] };
    for (let j = 0; j < cols.length; j++) {
      const r = i===j ? 1 : round4(pearson(colVals[cols[i]], colVals[cols[j]]));
      row[cols[j]] = r;
      if (j>i && Math.abs(r) > (args.threshold||0.7)) pairs.push({ 变量1: cols[i], 变量2: cols[j], Pearson: r });
    }
    matrix.push(row);
  }

  console.log(`\n📊 相关性分析 (${cols.length}个变量)`);
  console.log('='.repeat(50));
  matrix.forEach(r => console.log(`  ${r.变量.padEnd(10)}: ${cols.map(c=>String(r[c]).padEnd(12)).join('')}`));
  console.log(`\n高相关对 (|r|>${args.threshold||0.7}): ${pairs.length} 对`);
  pairs.forEach(p => console.log(`  ${p.变量1} ↔ ${p.变量2}: ${p.Pearson}`));
  await writeXLSX(args.output || './输出_相关性分析.xlsx', [{name:'相关矩阵',data:matrix}, {name:'高相关对',data:pairs}]);
}

async function method03(args) {
  const data = await readData(args.input);
  if (!args.target) throw new Error('需要 --target');
  const features = args.features ? args.features.split(',') : getNumericCols(data, [args.target]).slice(0, 5);
  const clean = data.filter(r => !isNaN(parseFloat(r[args.target])) && features.every(f => !isNaN(parseFloat(r[f]))));
  const n = clean.length;

  const y = clean.map(r => parseFloat(r[args.target]));
  const X = features.map(f => clean.map(r => parseFloat(r[f])));
  const yMean = y.reduce((a,b)=>a+b,0)/n; const yStd = Math.sqrt(y.reduce((s,v)=>s+(v-yMean)**2,0)/n);
  const means = X.map(xs => xs.reduce((a,b)=>a+b,0)/n);
  const stds = X.map(xs => Math.sqrt(xs.reduce((s,v)=>s+(v-means[X.indexOf(xs)])**2,0)/n));

  // OLS using normal equations via Gaussian elimination
  const Xm = Array.from({length:n}, (_,ri) => [1, ...X.map(xs => (xs[ri]-means[X.indexOf(xs)])/(stds[X.indexOf(xs)]||1))]);
  const Xt = Xm[0].map((_,i) => Xm.map(row => row[i]));
  const XtX = Xt.map(row => Xm[0].map((_,j) => row.reduce((s,v,k)=>s+v*Xm[k][j],0)));
  const XtY = Xt.map(row => row.reduce((s,v,i)=>s+v*y[i],0));

  let A = XtX.map((row,i) => [...row, XtY[i]]);
  const m = XtX.length;
  for (let i = 0; i < m; i++) {
    let mr = i; for (let j=i+1; j<m; j++) if (Math.abs(A[j][i]) > Math.abs(A[mr][i])) mr = j;
    [A[i], A[mr]] = [A[mr], A[i]];
    const pv = A[i][i]; if (Math.abs(pv)<1e-10) continue;
    for (let j=i; j<=m; j++) A[i][j] /= pv;
    for (let j=0; j<m; j++) if (j!==i) { const f = A[j][i]; for (let k=i; k<=m; k++) A[j][k] -= f * A[i][k]; }
  }
  const coef = A.map(row => row[m]);

  const preds = clean.map((_,ri) => {
    const zp = coef[0] + X.reduce((s,xs,fi) => s + ((xs[ri]-means[fi])/(stds[fi]||1))*coef[fi+1], 0);
    return zp + yMean;
  });
  const rmse = Math.sqrt(preds.reduce((s,p,i)=>s+(p-y[i])**2,0)/n);
  const ssRes = preds.reduce((s,p,i)=>s+(y[i]-p)**2,0);
  const ssTot = y.reduce((s,v)=>s+(v-yMean)**2,0);
  const R2 = 1 - ssRes/ssTot;

  const resRows = clean.map((r,i) => ({ ...r, 预测值: round2(preds[i]), 残差: round2(y[i]-preds[i]) }));
  const abnormal = resRows.filter(r => Math.abs(r.残差) > 2*rmse);

  const params = [{指标:'R²',数值:round4(R2)},{指标:'RMSE',数值:round2(rmse)},{指标:'截距',数值:round2(coef[0]+yMean)}];
  features.forEach((f,i) => params.push({指标:f, 数值:round4(coef[i+1])}));

  console.log(`\n📊 回归分析 ${args.target} = f(${features.join(',')})`);
  console.log(`R²=${round4(R2)} RMSE=${round2(rmse)} ${R2>0.8?'✅':R2>0.5?'⚠️':'❌'}`);
  console.log(`\n⚠️ 异常偏离: ${abnormal.length} 条`);
  await writeXLSX(args.output || './输出_回归分析.xlsx', [{name:'模型参数',data:params}, {name:'异常偏离',data:abnormal.slice(0,500)}]);
}

async function method04(args) {
  const data = await readData(args.input);
  const features = args.features ? args.features.split(',') : getNumericCols(data);
  const k = parseInt(args.clusters || 4);
  const clean = data.filter(r => features.every(f => !isNaN(parseFloat(r[f]))));
  const vals = {}; const mins={}, maxs={};
  features.forEach(f => { vals[f]=getVals(clean,f); mins[f]=Math.min(...vals[f]); maxs[f]=Math.max(...vals[f]); });
  const vecs = clean.map(r => features.map(f => (parseFloat(r[f])-mins[f])/((maxs[f]-mins[f])||1)));

  function ppInit(v, kc) { const c=[v[Math.floor(Math.random()*v.length)]]; for(let ci=1;ci<kc;ci++){ const d=v.map(p=>Math.min(...c.map(ct=>Math.sqrt(p.reduce((s,vi,i)=>s+(vi-ct[i])**2,0))))); const t=d.reduce((a,b)=>a+b,0); let r=Math.random()*t; for(let i=0;i<v.length;i++){r-=d[i];if(r<=0){c.push(v[i]);break;}} } return c; }

  function assign(v, c) { return v.map(p => { let md=Infinity, li=-1; c.forEach((ct,ci)=>{ const d=Math.sqrt(p.reduce((s,vi,i)=>s+(vi-ct[i])**2,0)); if(d<md){md=d;li=ci;} }); return li; }); }

  function update(v, lbls, kc) { const nc=Array.from({length:kc},()=>Array(v[0].length).fill(0)); const cnt=Array(kc).fill(0); v.forEach((p,i)=>{ cnt[lbls[i]]++; p.forEach((c,j)=>nc[lbls[i]][j]+=c); }); return nc.map((c,i)=>cnt[i]>0?c.map(x=>x/cnt[i]):c); }

  let centers = ppInit(vecs, k); let labels, last;
  for (let iter=0; iter<100; iter++) { labels=assign(vecs,centers); if(last&&JSON.stringify(labels)===JSON.stringify(last)) break; last=[...labels]; centers=update(vecs,labels,k); }

  clean.forEach((r,i) => r['聚类标签'] = labels[i]);
  const sumMap = {};
  for (let i=0; i<clean.length; i++) {
    const l=labels[i]; if(!sumMap[l]){sumMap[l]={样本数:0}; features.forEach(f=>sumMap[l][f]=0);}
    sumMap[l].样本数++; features.forEach(f=>sumMap[l][f]+=parseFloat(clean[i][f]));
  }
  const sumRows = Object.entries(sumMap).map(([l,v])=> {
    const row={聚类标签:parseInt(l),样本数:v.样本数}; features.forEach(f=>row[f]=round2(v[f]/v.样本数)); return row;
  }).sort((a,b)=>a.聚类标签-b.聚类标签);

  console.log(`\n📊 聚类分析 (${k}类, ${features.length}个特征)`);
  console.log('='.repeat(50));
  sumRows.forEach(r => console.log(`  类别${r.聚类标签}(${r.样本数}): ${features.map(f=>`${f}:${r[f]}`).join(', ')}`));
  await writeXLSX(args.output || './输出_聚类分析.xlsx', [{name:'聚类汇总',data:sumRows}, {name:'全部含标签',data:clean.slice(0,1000)}]);
}

async function method05(args) {
  const data = await readData(args.input);
  const col = args.column || getNumericCols(data)[0];
  const vals = getVals(data, col);
  const s = calcStats(vals);
  const th = parseFloat(args.threshold || 1.5);

  let result;
  if (args.method === 'zscore') {
    const t = parseFloat(args.zthreshold || 3);
    result = data.filter(r => { const v = parseFloat(r[col]); return !isNaN(v) && Math.abs(v-s.mean)/s.std > t; })
      .map(r => ({...r, 异常类型: `Z分(${t}σ)`, Z分数: round2(Math.abs((parseFloat(r[col])-s.mean)/s.std)) }));
  } else {
    const lo = s.Q1 - th*s.IQR, hi = s.Q3 + th*s.IQR;
    result = data.filter(r => { const v = parseFloat(r[col]); return !isNaN(v) && (v<lo||v>hi); })
      .map(r => ({...r, 异常类型: `IQR(${th}×)`, 下限: round2(lo), 上限: round2(hi) }));
  }

  console.log(`\n📊 异常检测: ${col} (${args.method==='zscore'?'Z分法':'IQR法'})`);
  console.log(`总样本: ${vals.length}  异常: ${result.length} (${(result.length/vals.length*100).toFixed(1)}%)`);
  if (result.length) { result.slice(0,10).forEach(r => console.log(`  ${r[col]} | ${r.异常类型}`)); }
  await writeXLSX(args.output || './输出_异常检测.xlsx', [{name:'异常数据',data:result.slice(0,1000)}]);
}

async function method06(args) {
  const data = await readData(args.input);
  const cols = args.columns ? args.columns.split(',') : Object.keys(data[0]).slice(0,5);
  const minSupp = parseFloat(args['min-support'] || 0.05);
  const txns = data.map(r => cols.map(c=>String(r[c])).filter(v=>v&&v!=='null'&&v!=='undefined'));
  const n = txns.length;

  const ifreq={}, pfreq={}, tfreq={};
  for (const t of txns) {
    t.forEach(it=>{ifreq[it]=(ifreq[it]||0)+1;});
    if (t.length>=2) { for(let i=0;i<t.length;i++) for(let j=i+1;j<t.length;j++){ const k=[t[i],t[j]].sort().join('|'); pfreq[k]=(pfreq[k]||0)+1; } }
    if (t.length>=3) { for(let i=0;i<t.length;i++) for(let j=i+1;j<t.length;j++) for(let l=j+1;l<t.length;l++){ const k=[t[i],t[j],t[l]].sort().join('|'); tfreq[k]=(tfreq[k]||0)+1; } }
  }

  const rules = [];
  for (const [key,cnt] of Object.entries(pfreq)) {
    const sup=cnt/n; if(sup<minSupp) continue;
    const [a,b]=key.split('|'); const sa=ifreq[a]/n, sb=ifreq[b]/n;
    if(sa===0||sb===0) continue;
    const ca=cnt/ifreq[a], cb=cnt/ifreq[b];
    if(ca>0.5){rules.push({前项:a,后项:b,支持度:round4(sup),置信度:round4(ca),提升度:round4(sup/(sa*sb))});}
    if(cb>0.5){rules.push({前项:b,后项:a,支持度:round4(sup),置信度:round4(cb),提升度:round4(sup/(sa*sb))});}
  }

  rules.sort((a,b)=>b.提升度-a.提升度);
  console.log(`\n📊 关联规则 (${cols.length}维, minSupp=${minSupp})`);
  console.log(`事务: ${n}  规则: ${rules.length}`);
  rules.slice(0,20).forEach(r => console.log(`  ${r.前项} → ${r.后项} (支持:${r.支持度},置信:${r.置信度},提升:${r.提升度})`));
  await writeXLSX(args.output || './输出_关联规则.xlsx', [{name:'关联规则',data:rules}]);
}

async function method07(args) {
  const data = await readData(args.input);
  const parsed = data.map(r => {
    const d=new Date(r[args['date-col']]), v=parseFloat(r[args['value-col']]);
    return {date:d, month:d.getMonth()+1, value:v};
  }).filter(r => !isNaN(r.date.getTime()) && !isNaN(r.value)).sort((a,b)=>a.date-b.date);

  const vals=parsed.map(r=>r.value); const n=parsed.length; const mean=vals.reduce((a,b)=>a+b,0)/n;
  const xMean=(n-1)/2;
  const num=parsed.reduce((s,_,i)=>s+(i-xMean)*(vals[i]-mean),0);
  const den=parsed.reduce((s,_,i)=>s+(i-xMean)**2,0);
  const slope=den===0?0:num/den, intercept=mean-slope*xMean;

  parsed.forEach((r,i) => { r.趋势值=intercept+slope*i; r.移动平均=i<2?vals[i]:(vals[i-2]+vals[i-1]+vals[i])/3; r.趋势偏离=r.value-r.趋势值; });
  const residStd=Math.sqrt(parsed.reduce((s,r)=>s+r.趋势偏离**2,0)/n);
  const trendA=parsed.filter(r=>Math.abs(r.趋势偏离)>2*residStd);

  const mmap={}; parsed.forEach(r=>{if(!mmap[r.month])mmap[r.month]=[]; mmap[r.month].push(r.value);});
  const sidx={}; for(const[m,vs]of Object.entries(mmap)) sidx[m]=vs.reduce((a,b)=>a+b,0)/vs.length/mean;
  const seasA=parsed.filter(r=>{const e=mean*(sidx[r.month]||1); return Math.abs(r.value-e)/e>0.2;});

  console.log(`\n📊 时间序列: ${args['value-col']} (${slope>0?'📈上升':'📉下降'}, 斜率=${round4(slope)})`);
  console.log(`趋势异常: ${trendA.length}  季节异常: ${seasA.length}`);
  for(let m=1;m<=12;m++){ if(sidx[m]){ const bar='█'.repeat(Math.round(Math.abs((sidx[m]-1)*40))); console.log(`  ${String(m).padStart(2)}月: ${sidx[m]>1?'+':''}${round2(sidx[m])} ${bar}`); } }

  await writeXLSX(args.output || './输出_时间序列.xlsx', [
    {name:'趋势分析',data:parsed.map(r=>({日期:r.date.toISOString().split('T')[0],原始值:round2(r.value),趋势值:round2(r.趋势值),移动平均:round2(r.移动平均),趋势偏离:round2(r.趋势偏离)}))},
    {name:'季节指数',data:Object.entries(sidx).map(([m,i])=>({月份:parseInt(m),季节指数:round2(i)}))},
    {name:'趋势异常',data:trendA.map(r=>({日期:r.date.toISOString().split('T')[0],值:r.value,偏离:round2(r.趋势偏离)}))}
  ]);
}

// ============== Main ==============

async function main() {
  const argv = process.argv.slice(2);
  if (argv.length===0 || argv[0]==='--help' || argv[0]==='-h') {
    console.log(`\n审计数据分析工具包 — 7大方法\n
用法: node index.js <方法编号> [参数]
方法:
  01 描述性统计  --input <文件> [--column <列>] [--output <文件>]
  02 相关性分析  --input <文件> [--columns <c1,c2,...>] [--threshold 0.7]
  03 回归分析    --input <文件> --target <列> [--features <f1,f2,...>]
  04 聚类分析    --input <文件> [--features <f1,f2,...>] [--clusters 4]
  05 异常检测    --input <文件> [--column <列>] [--method iqr|zscore] [--threshold 1.5]
  06 关联规则    --input <文件> --columns <c1,c2,...> [--min-support 0.05]
  07 时间序列    --input <文件> --date-col <列> --value-col <列>

示例:
  node index.js 01 --input 费用表.xlsx --column 金额
  node index.js 04 --input 供应商表.xlsx --clusters 4
  node index.js 05 --input 采购明细.xlsx --method zscore
  node index.js 06 --input 采购审批.xlsx --columns 审批人,时间,金额区间`);
    return;
  }

  const method = argv[0];
  const args = {};
  for (let i=1; i<argv.length; i+=2) { if (argv[i].startsWith('--')) args[argv[i].slice(2)] = argv[i+1]; }
  if (!args.input) { console.log('❌ 需要 --input <文件>'); return; }

  const methods = { '01': method01, '02': method02, '03': method03, '04': method04, '05': method05, '06': method06, '07': method07 };
  const fn = methods[method];
  if (!fn) { console.log(`❌ 未知方法: ${method} (可用: 01-07)`); return; }

  try { await fn(args); } catch(e) { console.error(`❌ ${e.message}`); }
}

main();
