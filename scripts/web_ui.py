"""
融策审计中台 - Web 聊天界面
===============================
统一的搜索 + 聊天界面，直接调用向量RAG引擎。
启动：python scripts\web_ui.py
访问：http://127.0.0.1:5000
"""
import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify

# 启动时预加载模型（只加载一次）
from sentence_transformers import SentenceTransformer
from scripts.rag_vector import semantic_search, EMBEDDING_MODEL

print(f'加载模型: {EMBEDDING_MODEL}...')
_model = SentenceTransformer(EMBEDDING_MODEL)
print('模型就绪')

app = Flask(__name__)
MODEL_NAME = 'text2vec-base-chinese'

HTML = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>融策审计中台</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family: -apple-system, "Microsoft YaHei", sans-serif; background: #f0f2f5; min-height: 100vh; }
.header { background: linear-gradient(135deg, #0A1F3F 0%, #1A5C6E 100%); color: white; padding: 28px 20px; text-align: center; }
.header h1 { font-size: 26px; margin-bottom: 6px; letter-spacing: 2px; }
.header p { opacity: 0.8; font-size: 13px; }
.stats { display: flex; justify-content: center; gap: 20px; margin-top: 10px; font-size: 12px; opacity: 0.75; }
.container { max-width: 860px; margin: 0 auto; padding: 16px; }
.chat-box { background: white; border-radius: 12px; box-shadow: 0 2px 16px rgba(0,0,0,0.08); overflow: hidden; }
.messages { height: 460px; overflow-y: auto; padding: 20px; }
.msg { margin-bottom: 18px; }
.msg-user { text-align: right; }
.msg-user .bubble { background: #0A1F3F; color: white; display: inline-block; padding: 11px 16px; border-radius: 16px 16px 4px 16px; max-width: 80%; text-align: left; font-size: 14px; line-height: 1.5; }
.msg-ai .bubble { background: #f5f5f5; display: inline-block; padding: 11px 16px; border-radius: 16px 16px 16px 4px; max-width: 88%; font-size: 14px; line-height: 1.7; color: #333; }
.msg-ai .score { display: inline-block; font-size: 10px; color: #1A5C6E; background: #e0f2f1; padding: 2px 7px; border-radius: 8px; margin-left: 4px; }
.msg-ai .src-line { font-size: 11px; color: #888; margin-top: 3px; }
.msg-loading .bubble { background: #f5f5f5; padding: 11px 16px; border-radius: 16px 16px 16px 4px; display: inline-block; color: #999; }
@keyframes pulse { 0%,100%{opacity:0.3} 50%{opacity:1} }
.dot-pulse::after { content: '...'; animation: pulse 1.5s infinite; }
.input-area { border-top: 1px solid #e0e0e0; padding: 14px 18px; display: flex; gap: 10px; }
.input-area input { flex: 1; padding: 11px 15px; border: 1px solid #ddd; border-radius: 22px; font-size: 14px; outline: none; background: #fafafa; }
.input-area input:focus { border-color: #1A5C6E; background: white; }
.input-area button { padding: 10px 22px; background: #0A1F3F; color: white; border: none; border-radius: 22px; font-size: 14px; cursor: pointer; font-weight: 500; }
.input-area button:hover { background: #1A5C6E; }
.examples { padding: 12px 18px; border-top: 1px solid #eee; }
.examples span { display: inline-block; padding: 4px 11px; margin: 3px 4px 3px 0; background: #F5F2EC; color: #1A5C6E; border-radius: 12px; font-size: 12px; cursor: pointer; border: 1px solid #e8e3d8; }
.examples span:hover { background: #C5955C; color: white; border-color: #C5955C; }
.footer { text-align: center; padding: 12px; font-size: 11px; color: #aaa; }
</style>
</head>
<body>
<div class="header">
  <h1>🔍 融策审计中台</h1>
  <p>RAG语义搜索 · %CHUNKS%条知识库 · %SOURCES%份文档</p>
  <div class="stats"><span>模型: %MODEL%</span><span>维度: 768</span><span>方法: 余弦相似度</span></div>
</div>
<div class="container">
<div class="chat-box">
<div class="messages" id="messages">
<div class="msg msg-ai"><div class="bubble">
欢迎使用融策审计中台 👋<br><br>
已加载 <b>%CHUNKS%</b> 条知识库内容，覆盖审计法规、案例、方法、政策等。<br>
直接输入你的审计问题，我会从知识库中检索最相关的内容并生成回答。
</div></div>
</div>
<div class="examples" id="examples"></div>
<div class="input-area">
<input id="input" placeholder="输入审计问题，回车发送..." onkeydown="if(event.key==='Enter')search()"/>
<button onclick="search()">🔍 搜索</button>
</div>
</div>
</div>
<div class="footer">融策审计中台 v1.0 · RAG语义检索引擎</div>
<script>
const examples = [
  "串标围标怎么取证？","竣工财务决算审核流程","经济责任审计一票否决情形",
  "预算执行审计常见问题","工程结算审核关键点","领导干部违规插手工程项目"
];
document.getElementById('examples').innerHTML = examples.map(e => '<span onclick="quickAsk(\''+e+'\')">'+e+'</span>').join('');

function addMsg(role, content) {
    const div = document.createElement('div');
    div.className = 'msg msg-' + role;
    div.innerHTML = '<div class="bubble">' + content.replace(/\n/g,'<br>') + '</div>';
    document.getElementById('messages').appendChild(div);
    document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
}

function quickAsk(q) { document.getElementById('input').value = q; search(); }
function search() {
    const q = document.getElementById('input').value.trim();
    if (!q) return;
    addMsg('user', q);
    document.getElementById('input').value = '';
    
    const lid = 'load-' + Date.now();
    document.getElementById('messages').innerHTML += '<div class="msg msg-loading" id="'+lid+'"><div class="bubble"><span class="dot-pulse">检索中</span></div></div>';
    
    fetch('/search', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:q,top_k:8})})
    .then(r => r.json())
    .then(data => {
        document.getElementById(lid).remove();
        if (!data.results || data.results.length === 0) {
            addMsg('ai', '未找到相关知识。换个问法试试？');
            return;
        }
        let html = '<b>检索到 ' + data.total_hits + ' 条知识中，最相关的 ' + data.results.length + ' 条：</b><br><br>';
        data.results.forEach((r,i) => {
            html += '<b>' + (i+1) + '.</b> <span class="score">' + (r.score*100).toFixed(1) + '%</span> ' + r.text.replace(/</g,'&lt;').substring(0,200) + '<br>';
            html += '<div class="src-line">📄 ' + r.source + '</div><br>';
        });
        addMsg('ai', html);
    })
    .catch(e => { document.getElementById(lid)?.remove(); addMsg('ai', '请求失败: ' + e.message); });
}
</script>
</body>
</html>'''

@app.route('/')
def index():
    """首页"""
    import pickle, os as _os
    meta_path = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), '.rag_vector_index', 'build_meta.json')
    chunks, sources = '?', '?'
    if _os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        chunks, sources = str(meta['chunks']), str(meta['sources'])
    return HTML.replace('%CHUNKS%', chunks).replace('%SOURCES%', sources).replace('%MODEL%', MODEL_NAME)

@app.route('/search', methods=['POST'])
def search():
    """语义搜索接口"""
    data = request.get_json()
    query = data.get('query', '')
    top_k = data.get('top_k', 8)
    if not query: return jsonify({'error': 'Missing query'}), 400
    result = semantic_search(query, top_k, model=_model)
    return jsonify(result)

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'model': MODEL_NAME})

if __name__ == '__main__':
    print(f'\n{"="*55}')
    print(f'  融策审计中台 Web 界面')
    PORT = 5005
    print(f'  浏览器访问: http://127.0.0.1:{PORT}')
    print(f'{"="*55}\n')
    app.run(host='127.0.0.1', port=PORT, debug=False, threaded=True)
