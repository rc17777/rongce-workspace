"""
RAG 知识库桥接器 - rag_bridge.py
从命令行查询 RAG 知识库，返回格式化 Markdown 结果。
可用于 Obsidian Shell Commands / Templater 插件集成。

用法：
  python rag_bridge.py "围标串标检测方法"          # 搜索并打印结果
  python rag_bridge.py --insert "政府采购审计"       # 搜索并生成可插入Obsidian的卡片
  python rag_bridge.py --open                        # 打开 RAG Web UI
"""
import sys, os, json, requests, webbrowser

sys.stdout.reconfigure(encoding='utf-8')

RAG_URL = "http://127.0.0.1:5000/api/rag/query"
WORKSPACE = r"C:\Users\scrccpa\.openclaw\workspace"

def query_rag(query: str, top_k: int = 5) -> dict:
    """调用 RAG API 查询"""
    try:
        r = requests.post(RAG_URL,
            json={"query": query, "top_k": top_k},
            timeout=30)
        if r.status_code == 200:
            return r.json()
        else:
            return {"error": f"RAG 返回 {r.status_code}", "raw": r.text[:200]}
    except requests.exceptions.ConnectionError:
        return {"error": "RAG 服务未启动。请先运行 '启动RAG知识库.bat'"}
    except Exception as e:
        return {"error": str(e)}

def format_as_card(query: str, result: dict) -> str:
    """格式化为 Obsidian 卡片"""
    lines = []
    lines.append(f"> [!info] RAG 检索结果")
    lines.append(f"> 查询：**{query}**")
    lines.append(f"> 时间：{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    
    if "error" in result:
        lines.append(f"⚠️ **错误**：{result['error']}")
        return "\n".join(lines)
    
    # RAG 返回的 chunks
    chunks = result.get("chunks", []) or result.get("results", [])
    if not chunks:
        lines.append("📭 未找到相关内容")
        return "\n".join(lines)
    
    lines.append(f"找到 {len(chunks)} 条相关内容：\n")
    
    for i, chunk in enumerate(chunks[:5], 1):
        content = chunk.get("content", chunk.get("text", str(chunk)))
        source = chunk.get("source", chunk.get("file", "未知来源"))
        score = chunk.get("score", chunk.get("similarity", 0))
        
        # 截短内容
        if len(content) > 300:
            content = content[:300] + "..."
        
        lines.append(f"### {i}. {source}")
        lines.append(f"📊 相关度：{score:.2f}" if isinstance(score, float) else f"📊 相关度：{score}")
        lines.append(f"> {content.strip()}")
        lines.append("")
    
    # 如果有 LLM 生成的回答
    if "answer" in result:
        lines.append("---")
        lines.append("### 🤖 AI 综合回答")
        lines.append(result["answer"])
    
    return "\n".join(lines)

def format_as_list(query: str, result: dict) -> str:
    """格式化为简洁列表"""
    lines = []
    
    if "error" in result:
        lines.append(f"RAG错误: {result['error']}")
        return "\n".join(lines)
    
    chunks = result.get("chunks", []) or result.get("results", [])
    if not chunks:
        return "📭 无结果"
    
    for chunk in chunks[:5]:
        content = chunk.get("content", chunk.get("text", str(chunk)))
        source = chunk.get("source", chunk.get("file", "?"))
        # 取第一句
        first_line = content.strip().split('\n')[0][:100]
        lines.append(f"- [[{source}]] — {first_line}")
    
    return "\n".join(lines)

def main():
    args = sys.argv[1:]
    
    if not args:
        print("用法:")
        print("  python rag_bridge.py \"查询内容\"         # 搜索并显示卡片")
        print("  python rag_bridge.py --list \"查询内容\"   # 简洁列表格式")
        print("  python rag_bridge.py --open               # 打开 RAG Web UI")
        print("  python rag_bridge.py --status              # 检查 RAG 服务状态")
        return
    
    # 打开 Web UI
    if args[0] == "--open":
        webbrowser.open("http://127.0.0.1:5000")
        print("✅ 已打开 RAG Web UI: http://127.0.0.1:5000")
        return
    
    # 检查状态
    if args[0] == "--status":
        try:
            r = requests.get("http://127.0.0.1:5000", timeout=5)
            print(f"✅ RAG 服务运行中 (HTTP {r.status_code})")
        except:
            print("❌ RAG 服务未启动。请运行桌面 '启动RAG知识库.bat'")
        return
    
    # 搜索模式
    mode = "card"
    if args[0] == "--list":
        query = " ".join(args[1:])
        mode = "list"
    elif args[0] == "--insert":
        # 用于 Obsidian 模板插入
        query = " ".join(args[1:])
        mode = "card"
    else:
        query = " ".join(args)
    
    if not query.strip():
        print("⚠️ 请输入查询内容")
        return
    
    print(f"🔍 正在查询 RAG 知识库：\"{query}\"")
    result = query_rag(query)
    
    if mode == "list":
        print(format_as_list(query, result))
    else:
        print(format_as_card(query, result))

if __name__ == "__main__":
    main()
