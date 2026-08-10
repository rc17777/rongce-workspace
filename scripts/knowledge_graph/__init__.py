"""
融策知识图谱 + RAG 联合召回接口
提供 OpenClaw session 中可直接调用的高层 API
"""

import json, sys, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts" / "knowledge_graph"))
from graph_engine import remember, recall, forget, improve, stats, load_graph, save_graph

# ─── RAG integration ──────────────────────────────────────────────

def _rag_search(query: str, top_k: int = 5) -> list:
    """Search the existing RAG knowledge base (TF-IDF)."""
    try:
        sys.path.insert(0, str(ROOT / "scripts"))
        from rag_query import search as rag_search_fn
        results = rag_search_fn(query, top_k=top_k)
        return [
            {"type": "rag", "text": r.get("content", "")[:500], 
             "source": r.get("source", ""), "score": r.get("score", 0)}
            for r in results
        ]
    except Exception as e:
        # RAG not available
        return []

def hybrid_recall(query: str, session_id: str = None, 
                  use_rag: bool = True, max_hops: int = 2) -> dict:
    """
    Combined recall: Graph traversal + RAG semantic search.
    
    Args:
        query: Natural language query
        session_id: Optional session for cache lookup
        use_rag: Enable RAG fallback
        max_hops: Graph traversal depth
    
    Returns:
        Structured results with graph paths and semantic matches
    """
    result = {
        "query": query,
        "graph": None,
        "rag": None,
        "summary": "",
        "relationships_found": [],
        "key_entities": []
    }
    
    # 1. Graph recall
    graph_result = recall(query, session_id=session_id, max_hops=max_hops)
    result["graph"] = graph_result
    
    # Extract key relationships for summary
    for item in graph_result["graph_results"]:
        if item["type"] == "relation" and item.get("hops", 99) == 1:
            result["relationships_found"].append(
                f"{item['from_name']} → {', '.join(item['relation_types'])} → {item['to_name']}"
            )
        elif item["type"] == "node":
            result["key_entities"].append(f"{item['name']} ({item['entity_type']})")
    
    # 2. RAG search (if graph results are sparse)
    if use_rag and len(graph_result["graph_results"]) < 3:
        try:
            rag_results = _rag_search(query, top_k=3)
            result["rag"] = rag_results
        except:
            pass
    
    # 3. Generate summary
    parts = []
    if result["relationships_found"]:
        parts.append("📊 图谱关系：\n" + "\n".join(f"  • {r}" for r in result["relationships_found"][:5]))
    if result["key_entities"]:
        parts.append("🏷️ 关键实体：\n" + "\n".join(f"  • {e}" for e in result["key_entities"][:5]))
    if result.get("rag"):
        parts.append(f"📚 RAG补充：找到 {len(result['rag'])} 条相关文档")
    
    result["summary"] = "\n\n".join(parts) if parts else "未找到相关信息"
    
    return result

# ─── Batch memory ingestion ───────────────────────────────────────

def ingest_file(filepath: str, session_id: str = None) -> dict:
    """Remember a single file's content into the knowledge graph."""
    path = Path(filepath)
    if not path.exists():
        return {"error": f"File not found: {filepath}"}
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Skip YAML frontmatter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            content = parts[2]
    
    return remember(content, source=str(path.relative_to(ROOT)), 
                    session_id=session_id, auto_cognify=True)

def ingest_text(text: str, label: str = "manual") -> dict:
    """Remember arbitrary text (e.g., chat summary, finding, note)."""
    return remember(text, source=label, auto_cognify=True)

# ─── Convenience functions ────────────────────────────────────────

def ask(query: str) -> str:
    """Simple Q&A interface: returns human-readable answer."""
    result = hybrid_recall(query)
    return result["summary"]

def graph_report() -> str:
    """Get a human-readable graph status report."""
    s = stats()
    lines = [
        f"📊 知识图谱状态",
        f"  节点: {s['total_nodes']} | 边: {s['total_edges']}",
        f"  实体类型: {', '.join(f'{k}({v})' for k,v in s['entity_types'].items())}",
        f"  关系类型: {', '.join(f'{k}({v})' for k,v in s['relation_types'].items())}",
        f"  会话缓存: {s['session_count']} 个",
        f"",
        f"  核心实体:"
    ]
    for node in s['top_connected'][:5]:
        lines.append(f"    {node['name']} ({node['degree']}条关联)")
    return "\n".join(lines)

# ─── Session management (Cognee-style) ────────────────────────────

def start_session(session_id: str) -> dict:
    """Start a new Cognee-style session."""
    return {"session_id": session_id, "status": "started"}

def end_session(session_id: str, sync_to_graph: bool = True) -> dict:
    """End a session, optionally syncing to permanent graph."""
    if sync_to_graph:
        return improve(session_id)
    return {"session_id": session_id, "status": "ended", "synced": False}

# ─── CLI ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="融策知识图谱高层接口")
    sub = ap.add_subparsers(dest="cmd")
    
    sub.add_parser("report", help="Graph status report")
    
    ask_p = sub.add_parser("ask", help="Query the knowledge graph")
    ask_p.add_argument("query", help="Query string")
    ask_p.add_argument("--json", action="store_true")
    
    ingest_p = sub.add_parser("ingest", help="Ingest a file")
    ingest_p.add_argument("filepath", help="File to ingest")
    
    ingest_t = sub.add_parser("ingest-text", help="Ingest text")
    ingest_t.add_argument("text", help="Text to ingest")
    ingest_t.add_argument("--label", default="manual")
    
    args = ap.parse_args()
    
    if args.cmd == "report":
        print(graph_report())
    elif args.cmd == "ask":
        r = hybrid_recall(args.query)
        if args.json:
            print(json.dumps(r, ensure_ascii=False, indent=2))
        else:
            print(r["summary"])
    elif args.cmd == "ingest":
        r = ingest_file(args.filepath)
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif args.cmd == "ingest-text":
        r = ingest_text(args.text, label=args.label)
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        ap.print_help()
