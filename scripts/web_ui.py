"""
融策审计中台 - Web 界面 v2
=============================
升级：混合检索、Reranker、反馈按钮、日期过滤
启动：python scripts/web_ui.py
访问：http://127.0.0.1:5005
"""
import sys, os, json, datetime
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer
from scripts.rag_vector import hybrid_search, rerank, EMBEDDING_MODEL, INDEX_DIR

print(f'加载模型: {EMBEDDING_MODEL}...')
_model = SentenceTransformer(EMBEDDING_MODEL)
print('模型就绪')

app = Flask(__name__)
MODEL_NAME = 'text2vec-base-chinese + BM25 + Reranker'

# 反馈数据存储
FEEDBACK_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'feedback.jsonl')
os.makedirs(os.path.dirname(FEEDBACK_FILE), exist_ok=True)

HTML = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>融策审计中台 v2</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family: -apple-system, "Microsoft YaHei", sans-serif; background: #f0f2f5; min-height: 100vh; }
.header { background: linear-gradient(135deg, #0A1F3F 0%, #1A5C6E 100%); color: white; padding: 24px 20px; text-align: center; }
.header h1 { font-size: 24px; margin-bottom: 4px; letter-spacing: 2px; }
.header .sub { opacity: 0.75; font-size: 12px; }
.header .sub2 { display:flex; justify-content:center; gap:12px; margin-top:8px; font-size:11px; opacity:0.65; }
.container { max-width: 900px; margin: 0 auto; padding: 12px; }
.toolbar { display:flex; gap:8px; align-items:center; padding:8px 0 4px; }
.toolbar label { font-size:12px; color:#666; }
.toolbar select { padding:4px 8px; font-size:12px; border:1px solid #ddd; border-radius:6px; }
.chat-box { background: white; border-radius: 12px; box-shadow: 0 2px 16px rgba(0,0,0,0.08); overflow: hidden; }
.messages { height: 480px; overflow-y: auto; padding: 16px 20px; }
.msg { margin-bottom: 14px; }
.msg-user { text-align: right; }
.msg-user .bubble { background: #0A1F3F; color: white; display: inline-block; padding: 10px 14px; border-radius: 14px 14px 4px 14px; max-width: 78%; text-align: left; font-size: 14px; line-height: 1.5; }
.msg-ai .bubble { background: #f5f5f5; display: inline-block; padding: 10px 14px; border-radius: 14px 14px 14px 4px; max-width: 92%; font-size: 13px; line-height: 1.6; color: #333; }
.msg-ai .src-line { font-size: 11px; color: #888; margin: 2px 0 4px; }
.msg-ai .tag { display: inline-block; font-size: 10px; padding: 1px 6px; border-radius: 8px; margin-right: 4px; }
.tag-reg { background: #e3f2fd; color: #1565c0; }
.tag-case { background: #fce4ec; color: #c62828; }
.tag-table { background: #e8f5e9; color: #2e7d32; }
.feedback { display: inline-flex; gap:6px; margin-left:8px; opacity:0.3; }
.feedback:hover { opacity:1; }
.feedback span { cursor:pointer; font-size:14px; padding:0 2px; }
.feedback span.active { opacity:1; }
.feedback span:hover { transform:scale(1.2); }
.msg-loading .bubble { background: #f5f5f5; padding: 10px 14px; border-radius: 14px 14px 14px 4px; display: inline-block; color: #999; }
@keyframes pulse { 0%,100%{opacity:0.3} 50%{opacity:1} }
.dot-pulse::after { content: '...'; animation: pulse 1.5s infinite; }
.input-area { border-top: 1px solid #e0e0e0; padding: 12px 16px; display: flex; gap: 8px; }
.input-area input { flex: 1; padding: 10px 14px; border: 1px solid #ddd; border-radius: 20px; font-size: 14px; outline: none; background: #fafafa; }
.input-area input:focus { border-color: #1A5C6E; background: white; }
.input-area button { padding: 9px 20px; background: #0A1F3F; color: white; border: none; border-radius: 20px; font-size: 14px; cursor: pointer; }
.input-area button:hover { background: #1A5C6E; }
.examples { padding: 8px 14px; border-top: 1px solid #f0f0f0; }
.examples span { display: inline-block; padding: 3px 10px; margin: 2px 3px; background: #F5F2EC; color: #1A5C6E; border-radius: 10px; font-size: 11px; cursor: pointer; border: 1px solid #e8e3d8; }
.examples span:hover { background: #C5955C; color: white; border-color: #C5955C; }
.footer { text-align: center; padding: 10px; font-size: 11px; color: #aaa; }
</style>
</head>
<body>
<div class="header">
  <h1>🔍 融策·审盾</h1>
  <div class="sub">RAG语义搜索 · %CHUNKS%条知识库 · %SOURCES%份文档</div>
  <div class="sub2"><span>模型: %MODEL%</span><span>检索: 混合检索(BM25+向量+RRF)</span><span>重排: BGE-reranker</span></div>
  <div style="margin-top:6px"><a href="http://127.0.0.1:5006" style="color:#C5955C;font-size:12px;text-decoration:none">🛡️ 报告复核器 →</a></div>
</div>
<div class="container">
<div class="toolbar">
  <label>📅 年份过滤:</label>
  <select id="yearFilter"><option value="">不限</option><option>2020</option><option>2021</option><option>2022</option><option>2023</option><option>2024</option><option>2025</option><option>2026</option></select>
  <label style="margin-left:12px">🔍 重排:</label>
  <select id="rerankToggle"><option value="1">开启</option><option value="0">关闭</option></select>
</div>
<div class="chat-box">
<div class="messages" id="messages">
<div class="msg msg-ai"><div class="bubble">
欢迎使用融策·审盾 v2 👋<br><br>
已加载 <b>%CHUNKS%</b> 条知识库，支持混合检索+重排。<br>
直接输入审计问题，系统会从知识库检索最相关的内容。
</div></div>
</div>
<div class="examples" id="examples"></div>
<div class="input-area">
<input id="input" placeholder="输入审计问题，回车发送..." onkeydown="if(event.key==='Enter')search()"/>
<button onclick="search()">🔍 搜索</button>
</div>
</div>
</div>
<div class="footer">融策·审盾 v2 · 混合检索+重排+反馈闭环</div>
<script>
const examples = [
  "串标围标怎么取证？","预算执行审计常见问题","竣工财务决算审核流程",
  "经济责任审计一票否决情形","工程结算审核关键点","虚列支出怎么定性"
];
document.getElementById('examples').innerHTML = examples.map(e => '<span onclick="quickAsk(\''+e+'\')">'+e+'</span>').join('');

function addMsg(role, content) {
    const div = document.createElement('div');
    div.className = 'msg msg-' + role;
    div.innerHTML = '<div class="bubble">' + content.replace(/\n/g,'<br>') + '</div>';
    document.getElementById('messages').appendChild(div);
    document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
}

function addResultMsg(query, results) {
    let html = '<b>检索结果</b><br><br>';
    results.forEach(function(r, i) {
        var tag = '';
        if (r.type === 'table') tag = '<span class="tag tag-table">表格</span>';
        else if (r.heading) tag = '<span class="tag tag-reg">' + r.heading.substring(0,12) + '</span>';
        var d = r.effective_date ? ' 📅' + r.effective_date : '';
        var rk = r.rerank_score ? ' rerank:' + (r.rerank_score*100).toFixed(0) + '%' : '';
        html += '<b>' + (i+1) + '.</b> ' + tag + '<span class="score" style="font-size:10px;color:#1A5C6E;background:#e0f2f1;padding:1px 5px;border-radius:6px;margin-left:3px;">' + (r.score*100).toFixed(0) + '%' + rk + '</span>' + d + '<br>';
        html += r.text.replace(/</g,'&lt;').substring(0,300) + '<br>';
        html += '<div class="src-line">📄 ' + r.source + 
                ' <span class="feedback" data-idx="' + i + '"><span onclick="feedback(' + i + ',1,this)">👍</span><span onclick="feedback(' + i + ',-1,this)">👎</span></span></div><br>';
    });
    
    const div = document.createElement('div');
    div.className = 'msg msg-ai';
    div.innerHTML = '<div class="bubble">' + html + '</div>';
    document.getElementById('messages').appendChild(div);
    document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
}

function feedback(idx, val, el) {
    var parent = el.parentNode;
    parent.querySelectorAll('span').forEach(function(s){ s.classList.remove('active'); });
    el.classList.add('active');
    fetch('/feedback', {method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({idx:idx, value:val, timestamp:new Date().toISOString()})});
}

function quickAsk(q) { document.getElementById('input').value = q; search(); }
function search() {
    const q = document.getElementById('input').value.trim();
    if (!q) return;
    addMsg('user', q);
    document.getElementById('input').value = '';
    
    const lid = 'load-' + Date.now();
    document.getElementById('messages').innerHTML += '<div class="msg msg-loading" id="'+lid+'"><div class="bubble"><span class="dot-pulse">检索中</span></div></div>';
    
    var year = document.getElementById('yearFilter').value;
    var rerank = document.getElementById('rerankToggle').value === '1';
    
    fetch('/search', {method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({query:q, top_k:10, rerank:rerank, year: year ? parseInt(year) : null})})
    .then(r => r.json())
    .then(data => {
        document.getElementById(lid).remove();
        if (!data.results || data.results.length === 0) {
            addMsg('ai', '未找到相关知识。试试其他关键词？');
            return;
        }
        addResultMsg(q, data.results);
    })
    .catch(e => { document.getElementById(lid)?.remove(); addMsg('ai', '请求失败: ' + e.message); });
}
</script>
</body>
</html>'''

@app.route('/')
def index():
    import pickle
    meta_path = os.path.join(INDEX_DIR, 'build_meta.json')
    chunks, sources = '?', '?'
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        chunks, sources = str(meta['chunks']), str(meta['sources'])
    return HTML.replace('%CHUNKS%', chunks).replace('%SOURCES%', sources).replace('%MODEL%', MODEL_NAME)

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    query = data.get('query', '')
    top_k = data.get('top_k', 10)
    use_rerank = data.get('rerank', True)
    year = data.get('year', None)
    if not query:
        return jsonify({'error': 'Missing query'}), 400
    result = hybrid_search(query, top_k, model=_model, year_filter=year)
    if use_rerank and result.get('results'):
        result['results'] = rerank(query, result['results'], min(top_k, 5))
    return jsonify(result)

@app.route('/feedback', methods=['POST'])
def feedback():
    data = request.get_json()
    with open(FEEDBACK_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False) + '\n')
    return jsonify({'ok': True})

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'model': MODEL_NAME})

if __name__ == '__main__':
    print(f'\n{"="*55}')
    print(f'  融策·审盾 v2')
    PORT = 5005
    print(f'  浏览器访问: http://127.0.0.1:{PORT}')
    print(f'  反馈日志: {FEEDBACK_FILE}')
    print(f'{"="*55}\n')
    app.run(host='127.0.0.1', port=PORT, debug=False, threaded=True)