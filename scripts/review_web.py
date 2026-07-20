"""
绩效评价报告复核器 - Web界面
==============================
上传.docx → 自动复核 → 展示复核意见
启动: python scripts/review_web.py
访问: http://127.0.0.1:5006
"""
import sys, os, json, time
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify, render_template_string
from scripts.report_reviewer import ReviewEngine, parse_docx, extract_issues, extract_regulations
from scripts.rag_vector import hybrid_search, rerank, EMBEDDING_MODEL
from sentence_transformers import SentenceTransformer

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(WORKSPACE, 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

print(f'加载模型: {EMBEDDING_MODEL}...')
_model = SentenceTransformer(EMBEDDING_MODEL)
print('模型就绪')

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

HTML = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>融策·审盾 - 报告复核器</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family: -apple-system, "Microsoft YaHei", sans-serif; background: #f0f2f5; min-height: 100vh; }
.header { background: linear-gradient(135deg, #0A1F3F 0%, #1A5C6E 100%); color: white; padding: 24px 20px; text-align: center; }
.header h1 { font-size: 24px; margin-bottom: 4px; }
.header .sub { opacity: 0.75; font-size: 12px; }
.container { max-width: 1000px; margin: 0 auto; padding: 16px; }
.upload-area { background: white; border-radius: 12px; box-shadow: 0 2px 16px rgba(0,0,0,0.08); padding: 40px; text-align: center; margin-bottom: 16px; }
.upload-zone { border: 2px dashed #ddd; border-radius: 12px; padding: 50px 20px; cursor: pointer; transition: all 0.3s; }
.upload-zone:hover, .upload-zone.dragover { border-color: #1A5C6E; background: #f0f8ff; }
.upload-zone .icon { font-size: 48px; margin-bottom: 12px; }
.upload-zone p { color: #666; font-size: 14px; }
.upload-zone input[type=file] { display: none; }
.btn { display: inline-block; padding: 10px 24px; background: #0A1F3F; color: white; border: none; border-radius: 8px; font-size: 14px; cursor: pointer; margin-top: 12px; }
.btn:hover { background: #1A5C6E; }
.report-card { background: white; border-radius: 12px; box-shadow: 0 2px 16px rgba(0,0,0,0.08); padding: 24px; margin-bottom: 16px; }
.report-card h3 { color: #0A1F3F; margin-bottom: 12px; font-size: 16px; }
.report-meta { display: flex; gap: 16px; margin-bottom: 16px; font-size: 13px; color: #666; flex-wrap: wrap; }
.report-meta span { background: #f5f5f5; padding: 3px 10px; border-radius: 10px; }
.issue-item { border: 1px solid #eee; border-radius: 8px; padding: 14px; margin-bottom: 10px; }
.issue-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px; }
.issue-text { font-size: 14px; color: #333; line-height: 1.6; }
.issue-type { font-size: 11px; background: #e3f2fd; color: #1565c0; padding: 2px 8px; border-radius: 8px; white-space: nowrap; margin-left: 8px; }
.reg-section { margin-top: 10px; padding-top: 10px; border-top: 1px dashed #eee; }
.reg-item { font-size: 12px; color: #555; margin-bottom: 4px; padding-left: 12px; border-left: 3px solid #C5955C; }
.reg-item .score { color: #1A5C6E; font-weight: 500; }
.reg-item .date { color: #999; font-size: 11px; }
.reg-item .src { color: #999; font-size: 11px; }
.case-item { border-left-color: #2e7d32; }
.expired-warn { background: #fff3e0; border: 1px solid #ffb74d; border-radius: 8px; padding: 12px; margin-bottom: 12px; font-size: 13px; color: #e65100; }
.feedback { display: inline-flex; gap:6px; margin-left:8px; opacity:0.3; }
.feedback:hover { opacity:1; }
.feedback span { cursor:pointer; font-size:14px; }
.feedback span.active { opacity:1; }
.loading { text-align: center; padding: 40px; color: #666; }
.empty { text-align: center; padding: 60px 20px; color: #999; }
.empty .icon { font-size: 48px; margin-bottom: 12px; }
.nav { display: flex; gap: 8px; padding: 8px 16px; background: white; border-bottom: 1px solid #eee; margin-bottom: 16px; border-radius: 8px; }
.nav a { padding: 6px 14px; text-decoration: none; color: #666; font-size: 13px; border-radius: 6px; }
.nav a:hover, .nav a.active { background: #0A1F3F; color: white; }
</style>
</head>
<body>
<div class="header">
  <h1>🛡️ 融策·审盾</h1>
  <div class="sub">绩效评价报告复核器 · 混合检索+Reranker</div>
</div>
<div class="container">
<div class="nav">
  <a href="http://127.0.0.1:5005">🔍 知识搜索</a>
  <a href="#" class="active">🛡️ 报告复核</a>
</div>
<div class="upload-area" id="uploadArea">
  <div class="upload-zone" id="dropZone" onclick="document.getElementById('fileInput').click()">
    <div class="icon">📄</div>
    <p>拖放 .docx 报告到这里，或点击选择文件</p>
    <p style="font-size:12px;color:#999;margin-top:4px;">支持绩效评价报告、审计报告（.docx）</p>
    <input type="file" id="fileInput" accept=".docx,.doc">
  </div>
  <button class="btn" onclick="document.getElementById('fileInput').click()">选择报告文件</button>
</div>
<div id="reportArea"></div>
</div>
<div class="footer" style="text-align:center;padding:16px;font-size:11px;color:#aaa;">融策·审盾 v2 · 报告复核器</div>
<script>
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const reportArea = document.getElementById('reportArea');

dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', e => { e.preventDefault(); dropZone.classList.remove('dragover'); if(e.dataTransfer.files.length) upload(e.dataTransfer.files[0]); });
fileInput.addEventListener('change', () => { if(fileInput.files.length) upload(fileInput.files[0]); });

function upload(file) {
    if (!file.name.endsWith('.docx') && !file.name.endsWith('.doc')) {
        alert('只支持 .docx 格式'); return;
    }
    const formData = new FormData();
    formData.append('file', file);
    reportArea.innerHTML = '<div class="loading">🔍 解析报告中...</div>';
    fetch('/review', {method:'POST', body:formData})
    .then(r => r.json())
    .then(data => {
        if (data.error) { reportArea.innerHTML = '<div class="report-card"><p style="color:red">'+data.error+'</p></div>'; return; }
        renderReport(data);
    })
    .catch(e => { reportArea.innerHTML = '<div class="report-card"><p style="color:red">上传失败: '+e.message+'</p></div>'; });
}

function renderReport(data) {
    let html = '';
    
    // 报告概览
    html += '<div class="report-card">';
    html += '<h3>📋 ' + (data.title || '报告复核结果') + '</h3>';
    html += '<div class="report-meta">';
    html += '<span>📝 ' + data.char_count + '字</span>';
    html += '<span>⚠️ ' + data.issues_count + '个问题</span>';
    html += '<span>📜 ' + data.regulations_count + '条法规</span>';
    html += '<span>📊 ' + data.tables_count + '个表格</span>';
    html += '</div>';
    
    // 过期法规警告
    if (data.expired_regulations && data.expired_regulations.length > 0) {
        html += '<div class="expired-warn">⚠️ <b>发现 ' + data.expired_regulations.length + ' 条可能过期的法规：</b><br>';
        data.expired_regulations.forEach(r => {
            html += '• ' + r.regulation + ' (' + r.year + ') — 建议核实是否已被修订或废止<br>';
        });
        html += '</div>';
    }
    html += '</div>';
    
    // 逐问题复核
    html += '<div class="report-card"><h3>🔍 逐问题复核意见</h3>';
    data.reviews.forEach((r, i) => {
        html += '<div class="issue-item">';
        html += '<div class="issue-header">';
        html += '<div class="issue-text"><b>问题 ' + (i+1) + ':</b> ' + r.issue.text + '</div>';
        html += '<span class="issue-type">' + r.issue.type + '</span>';
        html += '</div>';
        
        // 相关法规
        if (r.regulations && r.regulations.length > 0) {
            html += '<div class="reg-section"><b style="font-size:12px;color:#C5955C">📜 相关法规:</b>';
            r.regulations.forEach(reg => {
                html += '<div class="reg-item">';
                html += '<span class="score">[' + (reg.rerank_score ? (reg.rerank_score*100).toFixed(0) + '%' : (reg.score*100).toFixed(0) + '%') + ']</span> ';
                html += reg.text;
                if (reg.effective_date) html += ' <span class="date">📅' + reg.effective_date + '</span>';
                html += '<div class="src">📄 ' + reg.source + '</div>';
                html += '</div>';
            });
            html += '</div>';
        }
        
        // 同类案例
        if (r.cases && r.cases.length > 0) {
            html += '<div class="reg-section"><b style="font-size:12px;color:#2e7d32">📚 同类案例:</b>';
            r.cases.forEach(c => {
                html += '<div class="reg-item case-item">';
                html += '<span class="score">[' + (c.rerank_score ? (c.rerank_score*100).toFixed(0) + '%' : (c.score*100).toFixed(0) + '%') + ']</span> ';
                html += c.text;
                html += '<div class="src">📄 ' + c.source + '</div>';
                html += '</div>';
            });
            html += '</div>';
        }
        
        html += '</div>';
    });
    html += '</div>';
    
    reportArea.innerHTML = html;
}
</script>
</body>
</html>'''

@app.route('/')
def index():
    return HTML

@app.route('/review', methods=['POST'])
def review():
    if 'file' not in request.files:
        return jsonify({'error': '未选择文件'}), 400
    f = request.files['file']
    if f.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    
    # 保存上传文件
    filepath = os.path.join(UPLOAD_DIR, f.filename)
    f.save(filepath)
    
    try:
        # 解析
        report = parse_docx(filepath)
        
        # 逐问题复核
        reviews = []
        for issue in report['issues'][:10]:
            regs = hybrid_search(f"审计发现：{issue['text']} 相关法规依据", 3, model=_model)
            cases = hybrid_search(f"审计案例：{issue['text']} 处理处罚", 3, model=_model)
            
            if regs.get('results'):
                regs['results'] = rerank(f"审计发现：{issue['text']}", regs['results'], 3)
            if cases.get('results'):
                cases['results'] = rerank(f"审计案例：{issue['text']}", cases['results'], 3)
            
            reviews.append({
                'issue': issue,
                'regulations': [{
                    'score': r['score'],
                    'rerank_score': r.get('rerank_score', 0),
                    'source': r['source'],
                    'effective_date': r.get('effective_date', ''),
                    'text': r['text'][:200],
                } for r in regs.get('results', [])],
                'cases': [{
                    'score': r['score'],
                    'rerank_score': r.get('rerank_score', 0),
                    'source': r['source'],
                    'text': r['text'][:200],
                } for r in cases.get('results', [])],
            })
        
        # 法规时效性
        expired = []
        for reg in report['regulations']:
            results = hybrid_search(reg, 1, model=_model)
            if results.get('results'):
                doc = results['results'][0]
                if doc.get('effective_date'):
                    year = doc['effective_date'][:4]
                    if year.isdigit() and int(year) < 2020:
                        expired.append({'regulation': reg, 'year': year, 'source': doc['source']})
        
        return jsonify({
            'title': report['title'],
            'char_count': report['char_count'],
            'issues_count': len(report['issues']),
            'regulations_count': len(report['regulations']),
            'tables_count': report['tables_count'],
            'reviews': reviews,
            'expired_regulations': expired,
        })
    except Exception as e:
        return jsonify({'error': f'复核失败: {str(e)}'}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'model': 'text2vec-base-chinese + BM25 + Reranker'})

if __name__ == '__main__':
    print(f'\n{"="*55}')
    print(f'  融策·审盾 - 报告复核器')
    PORT = 5006
    print(f'  浏览器访问: http://127.0.0.1:{PORT}')
    print(f'{"="*55}\n')
    app.run(host='127.0.0.1', port=PORT, debug=False, threaded=True)