"""
融策AI审计知识库 - Web界面
启动：python rag_server.py
访问：http://localhost:5000
"""
import sys, os, json, pickle, re
sys.stdout.reconfigure(encoding='utf-8')

INDEX_FILE = r'D:\openclaw-workspace\.rag_index\rag_index.json'
DS_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
DS_API_URL = 'https://api.deepseek.com/v1/chat/completions'
DS_MODEL = 'deepseek-chat'

print("Loading index...")
with open(INDEX_FILE, 'rb') as f:
    data = pickle.load(f)
vectorizer = data['vectorizer']
tfidf_matrix = data['matrix']
texts = data['texts']
all_chunks = data['chunks']
_index_mtime = os.path.getmtime(INDEX_FILE)
print(f"Loaded {len(all_chunks)} chunks")

from sklearn.metrics.pairwise import cosine_similarity
import requests

def ensure_fresh_index():
    """索引文件重建后自动重载，避免内存里的旧索引继续答题 (2026-07-15)"""
    global vectorizer, tfidf_matrix, texts, all_chunks, _index_mtime
    try:
        m = os.path.getmtime(INDEX_FILE)
        if m != _index_mtime:
            print(f"[reload] index changed, reloading...")
            with open(INDEX_FILE, 'rb') as f:
                d = pickle.load(f)
            vectorizer = d['vectorizer']
            tfidf_matrix = d['matrix']
            texts = d['texts']
            all_chunks = d['chunks']
            _index_mtime = m
            print(f"[reload] done, {len(all_chunks)} chunks")
    except Exception as e:
        print(f"[reload] failed: {e}")

def search(query, top_k=5):
    ensure_fresh_index()
    q_vec = vectorizer.transform([query])
    scores = cosine_similarity(q_vec, tfidf_matrix)[0]
    top_idx = scores.argsort()[::-1][:top_k]
    results = []
    for idx in top_idx:
        if scores[idx] > 0.01:
            results.append({
                'score': float(scores[idx]),
                'source': all_chunks[idx]['source'],
                'text': all_chunks[idx]['text'][:600]
            })
    return results

def ask(query):
    results = search(query)
    if not results:
        return {"answer": "未找到相关文档，请换一种方式提问。", "sources": []}
    
    context = "\n\n---\n\n".join([f"【{r['source']}】\n{r['text']}" for r in results])
    sources = [{"file": r['source'], "score": f"{int(r['score']*100)}%", "preview": r['text'][:150]} for r in results]
    
    prompt = f"""你是一名审计专家，请基于以下知识库内容回答用户问题。

知识库内容：
{context}

用户问题：{query}

请给出专业、准确的回答，引用时标注【文件名】。如果知识库内容不足，结合你的审计专业知识补充。"""
    
    try:
        resp = requests.post(
            DS_API_URL,
            headers={'Authorization': f'Bearer {DS_API_KEY}', 'Content-Type': 'application/json'},
            json={
                'model': DS_MODEL,
                'messages': [
                    {'role': 'system', 'content': '你是一名中国审计专家，精通政府审计、工程审计、财务审计。回答专业简洁。'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.3, 'max_tokens': 2000
            },
            timeout=60
        )
        if resp.status_code == 200:
            answer = resp.json()['choices'][0]['message']['content']
        else:
            answer = f"API错误 (状态码: {resp.status_code})，以下为检索结果。"
    except Exception as e:
        answer = f"API调用失败: {e}"
    
    return {"answer": answer, "sources": sources}

# Flask
from flask import Flask, request, jsonify, send_from_directory
app = Flask(__name__)

HTML_PAGE = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>融策AI审计知识库</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, "Microsoft YaHei", sans-serif; background: #f0f2f5; }
.header { background: linear-gradient(135deg, #1a237e, #283593); color: white; padding: 30px 20px; text-align: center; }
.header h1 { font-size: 28px; margin-bottom: 8px; }
.header p { opacity: 0.85; font-size: 14px; }
.container { max-width: 900px; margin: 0 auto; padding: 20px; }
.chat-box { background: white; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); overflow: hidden; }
.messages { height: 450px; overflow-y: auto; padding: 20px; }
.msg { margin-bottom: 20px; }
.msg-user { text-align: right; }
.msg-user .bubble { background: #1976d2; color: white; display: inline-block; padding: 12px 18px; border-radius: 18px 18px 4px 18px; max-width: 80%; text-align: left; font-size: 14px; line-height: 1.5; }
.msg-ai .bubble { background: #f5f5f5; display: inline-block; padding: 12px 18px; border-radius: 18px 18px 18px 4px; max-width: 85%; text-align: left; font-size: 14px; line-height: 1.7; }
.msg-ai .bubble p { margin: 6px 0; }
.msg-ai .bubble .source-tag { font-size: 11px; color: #1976d2; background: #e3f2fd; padding: 2px 8px; border-radius: 10px; margin-right: 4px; }
.msg-loading .bubble { background: #f5f5f5; padding: 12px 18px; border-radius: 18px 18px 18px 4px; display: inline-block; }
.dot-pulse { display: inline-block; }
.dot-pulse::after { content: '...'; animation: pulse 1.5s infinite; }
@keyframes pulse { 0%, 100% { opacity: 0.3; } 50% { opacity: 1; } }
.sources { margin-top: 8px; font-size: 12px; }
.sources details { margin-top: 4px; }
.sources summary { color: #666; cursor: pointer; }
.sources .src-item { padding: 4px 0; color: #555; }
.input-area { border-top: 1px solid #e0e0e0; padding: 15px 20px; display: flex; gap: 10px; }
.input-area input { flex: 1; padding: 12px 16px; border: 1px solid #ddd; border-radius: 24px; font-size: 14px; outline: none; }
.input-area input:focus { border-color: #1976d2; }
.input-area button { padding: 10px 24px; background: #1976d2; color: white; border: none; border-radius: 24px; font-size: 14px; cursor: pointer; }
.input-area button:hover { background: #1565c0; }
.examples { padding: 15px 20px; border-top: 1px solid #eee; }
.examples span { display: inline-block; padding: 5px 12px; margin: 3px; background: #e3f2fd; color: #1976d2; border-radius: 14px; font-size: 12px; cursor: pointer; }
.examples span:hover { background: #bbdefb; }
.loading-overlay { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.1); z-index: 999; }
</style>
</head>
<body>
<div class="header"><h1>🧠 融策AI审计知识库</h1><p>基于融策知识库 + DeepSeek AI · 智能审计问答系统</p></div>
<div class="container">
<div class="chat-box">
<div class="messages" id="messages">
<div class="msg msg-ai"><div class="bubble">你好！我是融策AI审计助手，已加载 <b>13,635</b> 份审计相关文档。有什么审计问题可以问我？</div></div>
</div>
<div class="examples" id="examples"></div>
<div class="input-area">
<input id="input" placeholder="输入审计问题，例如：串标围标怎么取证？" onkeydown="if(event.key==='Enter')send()"/>
<button onclick="send()">发送</button>
</div>
</div>
</div>
<div class="loading-overlay" id="loading"></div>
<script>
const examples = ["串标围标怎么取证","竣工财务决算审核流程","经济责任审计一票否决","绩效评价常用方法","工程造价审核关键点","政府投资条例主要规定"];
const exDiv = document.getElementById('examples');
examples.forEach(ex => { const s = document.createElement('span'); s.textContent=ex; s.onclick=()=>ask(ex); exDiv.appendChild(s); });

function addMsg(role, content, sources) {
    const div = document.createElement('div');
    div.className = 'msg msg-' + role;
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.innerHTML = content.replace(/\n/g, '<br>');
    div.appendChild(bubble);
    if (sources && sources.length > 0 && role === 'ai') {
        const srcDiv = document.createElement('div');
        srcDiv.className = 'sources';
        let srcHtml = '<details><summary>📚 ' + sources.length + '个参考来源</summary>';
        sources.forEach(s => { srcHtml += '<div class="src-item">📄 <b>' + s.file + '</b> (匹配度: ' + s.score + ')<br><span style="color:#888;font-size:11px">' + s.preview + '</span></div>'; });
        srcHtml += '</details>';
        srcDiv.innerHTML = srcHtml;
        div.appendChild(srcDiv);
    }
    document.getElementById('messages').appendChild(div);
    document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
}

function send() {
    const q = document.getElementById('input').value.trim();
    if (!q) return;
    ask(q);
}

function ask(q) {
    addMsg('user', q);
    document.getElementById('input').value = '';
    
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'msg msg-ai msg-loading';
    loadingDiv.innerHTML = '<div class="bubble"><span class="dot-pulse">AI思考中</span></div>';
    loadingDiv.id = 'loading-msg';
    document.getElementById('messages').appendChild(loadingDiv);
    
    fetch('/api/ask', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({query: q})
    })
    .then(r => r.json())
    .then(data => {
        document.getElementById('loading-msg').remove();
        addMsg('ai', data.answer, data.sources || []);
    })
    .catch(e => {
        document.getElementById('loading-msg').remove();
        addMsg('ai', '请求失败: ' + e.message);
    });
}
</script>
</body>
</html>'''

@app.route('/')
def index():
    return HTML_PAGE

@app.route('/api/ask', methods=['POST'])
def api_ask():
    data = request.get_json()
    query = data.get('query', '')
    return jsonify(ask(query))

if __name__ == '__main__':
    print("\n" + "="*50)
    print(" 融策AI审计知识库已启动!")
    print(" 浏览器访问: http://localhost:5001")
    print("="*50 + "\n")
    app.run(host='127.0.0.1', port=5001, debug=False, threaded=True)
