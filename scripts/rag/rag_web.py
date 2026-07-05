"""
融策审计知识库 RAG - Web界面
启动：python rag_web.py
访问：http://localhost:7860
"""
import sys, os, json, pickle, re
sys.stdout.reconfigure(encoding='utf-8')
os.environ['NO_PROXY'] = 'localhost,127.0.0.1'

INDEX_FILE = r'D:\openclaw-workspace\.rag_index\rag_index.json'
DEEPSEEK_API = 'sk-7d5037d1d1c145f5b9ef928fcd696e5c'

# 加载索引
print("Loading index...")
with open(INDEX_FILE, 'rb') as f:
    data = pickle.load(f)
vectorizer = data['vectorizer']
tfidf_matrix = data['matrix']
texts = data['texts']
all_chunks = data['chunks']
print(f"Loaded {len(all_chunks)} chunks")

from sklearn.metrics.pairwise import cosine_similarity

def search(query, top_k=5):
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

def rag_answer(query, history):
    if not query.strip():
        return "", history
    
    results = search(query)
    
    if not results:
        answer = "未找到相关文档。请换一种方式提问。"
    else:
        context = "\n\n---\n\n".join([f"【{r['source']}】\n{r['text']}" for r in results])
        
        # Build sources display
        sources_str = ""
        for i, r in enumerate(results):
            score_pct = int(r['score'] * 100)
            sources_str += f"\n📄 [{i+1}] {r['source']} (匹配度: {score_pct}%)"
        
        prompt = f"""你是一名审计专家，请基于以下知识库内容回答用户问题。

知识库内容：
{context}

用户问题：{query}

请给出专业、准确的回答。如果知识库内容不足，结合你的专业知识补充。回答中引用相关来源时标注【文件名】。"""
        
        import requests
        try:
            resp = requests.post(
                'https://api.deepseek.com/chat/completions',
                headers={
                    'Authorization': f'Bearer {DEEPSEEK_API}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'deepseek-chat',
                    'messages': [
                        {'role': 'system', 'content': '你是一名中国审计专家，精通政府审计、工程审计、财务审计。回答专业、简洁、准确。'},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.3,
                    'max_tokens': 2000
                },
                timeout=60
            )
            if resp.status_code == 200:
                ai_answer = resp.json()['choices'][0]['message']['content']
                answer = ai_answer + "\n\n---\n📚 **参考来源**" + sources_str
            else:
                answer = f"API错误: {resp.status_code}\n\n📚 **检索到的相关内容** (AI回答不可用):" + sources_str + "\n\n" + "\n\n".join([f"**来源{i+1}**: {r['source']}\n{r['text'][:300]}" for i, r in enumerate(results)])
        except Exception as e:
            answer = f"API调用失败: {e}\n\n📚 **检索到的相关内容:**" + sources_str + "\n\n" + "\n\n".join([f"**来源{i+1}**: {r['source']}\n{r['text'][:300]}" for i, r in enumerate(results)])
    
    history.append((query, answer))
    return "", history

# Gradio界面
import gradio as gr

with gr.Blocks(title="融策AI审计知识库", theme=gr.themes.Soft(primary_hue="blue")) as demo:
    gr.Markdown("""
    # 🧠 融策AI审计知识库
    ### 基于融策知识库 + DeepSeek AI 的智能审计问答系统
    
    问任何审计相关问题，AI会从知识库中检索相关资料并结合专业知识回答。
    """)
    
    chatbot = gr.Chatbot(label="对话", height=500)
    msg = gr.Textbox(label="输入审计问题", placeholder="例如：串标围标怎么取证？竣工财务决算审核流程？绩效评价方法？")
    clear = gr.ClearButton([msg, chatbot])
    
    # 示例问题
    gr.Markdown("### 💡 试试这些问题")
    examples = [
        "串标围标怎么取证",
        "竣工财务决算审核流程",
        "经济责任审计一票否决的情形",
        "政府投资条例主要规定",
        "绩效评价的常用方法",
        "工程造价审核的关键点",
    ]
    
    with gr.Row():
        for ex in examples:
            gr.Button(ex, size="sm").click(
                lambda q=ex: rag_answer(q, chatbot.value if chatbot.value else []),
                outputs=[msg, chatbot]
            ).then(
                fn=None, inputs=None, outputs=None
            )
    
    msg.submit(rag_answer, [msg, chatbot], [msg, chatbot])

if __name__ == '__main__':
    demo.launch(server_name='127.0.0.1', server_port=7860)
