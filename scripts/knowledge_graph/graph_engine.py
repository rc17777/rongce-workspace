"""
融策知识图谱引擎 v1.0 — Cognee 风格本地实现
借鉴 Cognee 的 remember/recall/cognify 模式，
基于 NetworkX + DeepSeek + 现有 RAG 构建本地知识图谱。

核心思路：
  - cognify: DeepSeek 自动从文本抽取实体和关系
  - remember: 存数据 + 自动 cognify + 并入图谱
  - recall: 语义搜索(RAG) + 图遍历 双路召回
  - session: 会话级快缓存 → 后台同步入永久图谱
"""

import json, os, re, sys, hashlib, time
from datetime import datetime
from pathlib import Path
from typing import Optional

import networkx as nx

# Workspace root
ROOT = Path(__file__).resolve().parent.parent.parent
GRAPH_DIR = ROOT / "data" / "knowledge_graph"
GRAPH_DIR.mkdir(parents=True, exist_ok=True)

NODES_FILE = GRAPH_DIR / "nodes.json"
EDGES_FILE = GRAPH_DIR / "edges.json"
SESSION_DIR = GRAPH_DIR / "sessions"
SESSION_DIR.mkdir(exist_ok=True)

# ─── Graph persistence ───────────────────────────────────────────

def load_graph() -> nx.DiGraph:
    """Load graph from JSON files, returns NetworkX DiGraph."""
    G = nx.DiGraph()
    if NODES_FILE.exists():
        with open(NODES_FILE, 'r', encoding='utf-8') as f:
            nodes = json.load(f)
        for n in nodes:
            G.add_node(n['id'], **{k: v for k, v in n.items() if k != 'id'})
    if EDGES_FILE.exists():
        with open(EDGES_FILE, 'r', encoding='utf-8') as f:
            edges = json.load(f)
        for e in edges:
            G.add_edge(e['source'], e['target'], **{k: v for k, v in e.items() if k not in ('source', 'target')})
    return G

def save_graph(G: nx.DiGraph):
    """Save graph to JSON files."""
    nodes = []
    for n, data in G.nodes(data=True):
        node = {'id': n, **data}
        nodes.append(node)
    with open(NODES_FILE, 'w', encoding='utf-8') as f:
        json.dump(nodes, f, ensure_ascii=False, indent=2)

    edges = []
    for s, t, data in G.edges(data=True):
        edge = {'source': s, 'target': t, **data}
        edges.append(edge)
    with open(EDGES_FILE, 'w', encoding='utf-8') as f:
        json.dump(edges, f, ensure_ascii=False, indent=2)

# ─── Entity ID ────────────────────────────────────────────────────

def entity_id(name: str, etype: str) -> str:
    """Generate a stable ID from entity name + type."""
    h = hashlib.md5(f"{name}|{etype}".encode()).hexdigest()[:8]
    return f"{etype}:{h}"

# ─── Cognify: LLM-based entity/relation extraction ────────────────

COGNIFY_PROMPT = """从以下文本中提取实体和关系，用于构建知识图谱。

输出严格JSON格式，不要任何额外文本：
{{
  "entities": [
    {{"name": "实体名", "type": "类型", "properties": {{}}}}
  ],
  "relations": [
    {{"source": "源实体名", "target": "目标实体名", "type": "关系类型", "evidence": "原文依据片段"}}
  ]
}}

实体类型从以下选择（可扩展）：Person Company Project Regulation Law Document Agency Account Contract Bid Vendor Method Tool Skill KnowledgeDomain Date Amount Location Phone Address

关系类型从以下选择：owns controls works_at bid_on won awarded signed referenced involves audits applies_to related_to part_of located_in same_as uses depends_on

注意：
- 每个实体至少提取name, type
- 关系必须基于原文，evidence需截取原文片段
- 数字金额需保留原始数值
- 中文实体名保持原样

文本：
{text}"""

def _get_llm_clients():
    """Get available LLM API clients, prioritized.
    Returns list of (api_key, base_url, model) tuples."""
    config_path = Path.home() / ".openclaw" / "openclaw.json"
    if not config_path.exists():
        return []
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    clients = []
    providers = config.get("models", {}).get("providers", {})
    
    # Priority 1: deepseek-direct/deepseek-chat (non-reasoning, reliable for JSON)
    for pid, pdata in providers.items():
        if "deepseek-direct" in pid:
            clients.append((pdata.get("apiKey", ""), pdata.get("baseUrl", ""), "deepseek-chat"))
            break
    
    return clients

async def cognify_text(text: str) -> dict:
    """Extract entities and relations from text using available LLMs.
    Tries deepseek-direct first (non-reasoning), falls back to cbwyy-top."""
    import aiohttp
    
    if len(text) > 25000:
        text = text[:25000] + "..."
    
    prompt = COGNIFY_PROMPT.format(text=text)
    clients = _get_llm_clients()
    
    if not clients:
        print("[cognify] No LLM clients available")
        return {"entities": [], "relations": []}
    
    last_error = None
    for api_key, base_url, model in clients:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1,
                        "max_tokens": 4000
                    },
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as resp:
                    data = await resp.json()
            
            if "choices" not in data:
                last_error = data
                continue
            
            msg = data["choices"][0]["message"]
            content = msg.get("content") or msg.get("reasoning_content") or ""
            
            if not content:
                last_error = "Empty content"
                continue
            
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError as je:
                    # JSON parse error - try to extract just the first complete JSON object
                    print(f"[cognify] JSON parse error: {je}, trying to recover...")
                    # Find balanced braces
                    brace_start = json_match.start()
                    depth = 0
                    for i, c in enumerate(content[brace_start:], brace_start):
                        if c == '{':
                            depth += 1
                        elif c == '}':
                            depth -= 1
                            if depth == 0:
                                try:
                                    return json.loads(content[brace_start:i+1])
                                except:
                                    break
                    
            print(f"[cognify] {model}: No valid JSON in response, first 200: {content[:200]}")
            last_error = f"No JSON from {model}"
            continue
            
        except Exception as e:
            last_error = str(e)
            continue
    
    print(f"[cognify] All clients failed. Last error: {last_error}")
    return {"entities": [], "relations": []}

def cognify_text_sync(text: str) -> dict:
    """Synchronous wrapper for cognify_text."""
    import asyncio
    import threading
    try:
        loop = asyncio.get_running_loop()
        # We're in an async context already, can't nest
        return {"entities": [], "relations": [], "error": "async_context"}
    except RuntimeError:
        # No running loop, create new one
        return asyncio.run(cognify_text(text))

# ─── Remember ─────────────────────────────────────────────────────

def remember(text: str, source: str = "manual", session_id: Optional[str] = None, 
             auto_cognify: bool = True) -> dict:
    """
    Cognee-style remember(): store data and (optionally) cognify into graph.
    
    For async contexts, use aremember() instead.
    """
    import asyncio
    try:
        loop = asyncio.get_running_loop()
        # We're in an async context - use sync-only path (no cognify)
        return _remember_without_cognify(text, source, session_id)
    except RuntimeError:
        # No running loop, safe to run sync
        return _remember_sync(text, source, session_id, auto_cognify)

async def aremember(text: str, source: str = "manual", session_id: Optional[str] = None,
                    auto_cognify: bool = True) -> dict:
    """Async version of remember() for use in async contexts."""
    return await _remember_async(text, source, session_id, auto_cognify)

def _remember_without_cognify(text: str, source: str, session_id: Optional[str]) -> dict:
    """Remember without cognify (for async contexts where we can't nest event loops)."""
    G = load_graph()
    result = {
        "status": "ok",
        "text_length": len(text),
        "source": source,
        "entities_added": 0,
        "relations_added": 0,
        "session_id": session_id,
        "cognified": False,
        "note": "Use aremember() for async cognify"
    }
    if session_id:
        _cache_session(session_id, text, source)
        result["session_cached"] = True
    return result

def _remember_sync(text: str, source: str, session_id: Optional[str], 
                   auto_cognify: bool) -> dict:
    """Synchronous remember with optional cognify."""
    G = load_graph()
    result = {
        "status": "ok",
        "text_length": len(text),
        "source": source,
        "entities_added": 0,
        "relations_added": 0,
        "session_id": session_id
    }
    
    if session_id:
        _cache_session(session_id, text, source)
        result["session_cached"] = True
    
    if auto_cognify:
        extraction = cognify_text_sync(text)
        if "error" not in extraction:
            e_added, r_added = _merge_extraction(G, extraction, source)
            result["entities_added"] = e_added
            result["relations_added"] = r_added
            result["cognified"] = True
    
    return result

async def _remember_async(text: str, source: str, session_id: Optional[str],
                          auto_cognify: bool) -> dict:
    """Async remember with cognify."""
    G = load_graph()
    result = {
        "status": "ok",
        "text_length": len(text),
        "source": source,
        "entities_added": 0,
        "relations_added": 0,
        "session_id": session_id
    }
    
    if session_id:
        _cache_session(session_id, text, source)
        result["session_cached"] = True
    
    if auto_cognify:
        extraction = await cognify_text(text)
        if "error" not in extraction:
            e_added, r_added = _merge_extraction(G, extraction, source)
            result["entities_added"] = e_added
            result["relations_added"] = r_added
            result["cognified"] = True
    
    return result

def _cache_session(session_id: str, text: str, source: str):
    """Cache text in session storage."""
    from datetime import datetime
    session_file = SESSION_DIR / f"{session_id}.json"
    sessions = []
    if session_file.exists():
        with open(session_file, 'r', encoding='utf-8') as f:
            sessions = json.load(f)
    sessions.append({
        "timestamp": datetime.now().isoformat(),
        "text": text[:5000],
        "source": source
    })
    sessions = sessions[-50:]
    with open(session_file, 'w', encoding='utf-8') as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)

def _merge_extraction(G, extraction: dict, source: str) -> tuple:
    """Merge extracted entities and relations into graph. Returns (entities_added, relations_added)."""
    from datetime import datetime
    entities = extraction.get("entities", [])
    relations = extraction.get("relations", [])
    
    e_added = 0
    for ent in entities:
        eid = entity_id(ent["name"], ent["type"])
        if not G.has_node(eid):
            G.add_node(eid, 
                       name=ent["name"], 
                       type=ent["type"],
                       properties=ent.get("properties", {}),
                       sources=[source],
                       first_seen=datetime.now().isoformat())
            e_added += 1
        else:
            existing_sources = G.nodes[eid].get("sources", [])
            if source not in existing_sources:
                existing_sources.append(source)
                G.nodes[eid]["sources"] = existing_sources
    
    r_added = 0
    for rel in relations:
        src_type = _guess_type(rel["source"], entities)
        tgt_type = _guess_type(rel["target"], entities)
        src_id = entity_id(rel["source"], src_type)
        tgt_id = entity_id(rel["target"], tgt_type)
        
        if not G.has_edge(src_id, tgt_id) or G.edges[src_id, tgt_id].get("type") != rel["type"]:
            G.add_edge(src_id, tgt_id,
                       type=rel["type"],
                       evidence=rel.get("evidence", ""),
                       sources=[source],
                       first_seen=datetime.now().isoformat())
            r_added += 1
        else:
            existing_sources = G.edges[src_id, tgt_id].get("sources", [])
            if source not in existing_sources:
                existing_sources.append(source)
                G.edges[src_id, tgt_id]["sources"] = existing_sources
    
    save_graph(G)
    return e_added, r_added

def _guess_type(name: str, entities: list) -> str:
    """Guess entity type from name if type not provided."""
    for ent in entities:
        if ent["name"] == name:
            return ent["type"]
    return "Unknown"

# ─── Recall ───────────────────────────────────────────────────────

def recall(query: str, session_id: Optional[str] = None, 
           max_hops: int = 2, top_k: int = 10) -> dict:
    """
    Cognee-style recall(): search graph + session cache.
    
    Strategy:
    1. Session cache first (if session_id provided)
    2. Entity name matching in graph
    3. Graph traversal (N-hop neighbors)
    4. Combined and ranked results
    
    Args:
        query: Search query
        session_id: Session to search first
        max_hops: Graph traversal depth
        top_k: Max results
    
    Returns:
        dict with results
    """
    results = {
        "query": query,
        "session_results": [],
        "graph_results": [],
        "combined": []
    }
    
    # 1. Session cache
    if session_id:
        session_file = SESSION_DIR / f"{session_id}.json"
        if session_file.exists():
            with open(session_file, 'r', encoding='utf-8') as f:
                sessions = json.load(f)
            # Simple keyword match in session
            query_lower = query.lower()
            for s in sessions[-10:]:  # Last 10 entries
                if any(kw in s["text"].lower() for kw in query_lower.split()):
                    results["session_results"].append({
                        "type": "session",
                        "text": s["text"][:500],
                        "timestamp": s["timestamp"],
                        "source": s.get("source", "unknown")
                    })
    
    # 2. Graph search - fuzzy matching on entity names
    G = load_graph()
    query_lower = query.lower()
    
    # Tokenize query into search terms
    import jieba
    try:
        search_terms = list(jieba.cut(query))
    except ImportError:
        search_terms = query_lower.split()
    # Add query as whole phrase too
    search_terms.append(query_lower)
    # Remove pure punctuation/whitespace terms
    search_terms = [t.strip().lower() for t in search_terms if t.strip() and len(t.strip()) > 1]
    
    # Find matching nodes - score by how many terms match
    scored_nodes = []
    for n, data in G.nodes(data=True):
        name = (data.get("name") or "").lower()
        ntype = (data.get("type") or "").lower()
        score = 0
        for term in search_terms:
            if term in name:
                score += 3  # Name match is strong
            elif term in ntype:
                score += 1  # Type match is weak
            # Partial match: check if term chars are in name
            elif len(term) >= 2 and all(c in name for c in term):
                score += 1
        if score > 0:
            scored_nodes.append((score, n, data))
    
    # Sort by score descending, take top 5
    scored_nodes.sort(key=lambda x: x[0], reverse=True)
    matched_nodes = [(n, d) for _, n, d in scored_nodes[:5]]
    
    # Graph traversal from matched nodes
    seen = set()
    graph_hits = []
    
    for node_id, node_data in matched_nodes[:5]:  # Start from top 5 matches
        if node_id in seen:
            continue
        seen.add(node_id)
        
        # Add the node itself
        graph_hits.append({
            "type": "node",
            "id": node_id,
            "name": node_data.get("name"),
            "entity_type": node_data.get("type"),
            "properties": node_data.get("properties", {}),
            "sources": node_data.get("sources", [])
        })
        
        # N-hop neighbors
        for hop in range(1, max_hops + 1):
            for neighbor in nx.single_source_shortest_path_length(G, node_id, cutoff=hop):
                if neighbor in seen or neighbor == node_id:
                    continue
                seen.add(neighbor)
                n_data = G.nodes[neighbor]
                # Get all paths to this neighbor
                paths = list(nx.all_simple_paths(G, node_id, neighbor, cutoff=hop))
                edge_types = []
                for path in paths:
                    for i in range(len(path) - 1):
                        e_data = G.edges[path[i], path[i+1]]
                        edge_types.append(e_data.get("type", "unknown"))
                
                graph_hits.append({
                    "type": "relation",
                    "from_id": node_id,
                    "from_name": node_data.get("name"),
                    "to_id": neighbor,
                    "to_name": n_data.get("name"),
                    "to_type": n_data.get("type"),
                    "hops": hop,
                    "relation_types": list(set(edge_types)),
                    "sources": n_data.get("sources", [])
                })
    
    # Rank: closer hops first, then by name match quality
    graph_hits.sort(key=lambda x: (
        x.get("hops", 0),
        0 if query_lower in (x.get("name") or "").lower() else 1
    ))
    
    results["graph_results"] = graph_hits[:top_k * 2]
    results["combined"] = _combine_results(
        results["session_results"][:5], 
        graph_hits[:top_k]
    )
    results["total_nodes"] = G.number_of_nodes()
    results["total_edges"] = G.number_of_edges()
    
    return results

def _combine_results(session_results: list, graph_results: list) -> list:
    """Merge and deduplicate results."""
    combined = []
    seen_texts = set()
    
    for r in session_results:
        key = r["text"][:100]
        if key not in seen_texts:
            seen_texts.add(key)
            combined.append(r)
    
    for r in graph_results:
        key = f"{r.get('id', '')}:{r.get('name', '')}"
        if key not in seen_texts:
            seen_texts.add(key)
            combined.append(r)
    
    return combined

# ─── Forget ───────────────────────────────────────────────────────

def forget(node_id: Optional[str] = None, session_id: Optional[str] = None) -> dict:
    """Remove data from graph or session cache."""
    result = {"status": "ok"}
    
    if node_id:
        G = load_graph()
        if G.has_node(node_id):
            G.remove_node(node_id)
            save_graph(G)
            result["node_removed"] = node_id
        else:
            result["node_not_found"] = node_id
    
    if session_id:
        session_file = SESSION_DIR / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()
            result["session_cleared"] = session_id
    
    return result

# ─── Improve (session → graph sync) ───────────────────────────────

def improve(session_id: str) -> dict:
    """
    Cognee-style improve(): sync session cache into permanent graph.
    Cognifies each session entry and merges into the main graph.
    """
    session_file = SESSION_DIR / f"{session_id}.json"
    if not session_file.exists():
        return {"status": "error", "message": f"Session {session_id} not found"}
    
    with open(session_file, 'r', encoding='utf-8') as f:
        sessions = json.load(f)
    
    result = {"status": "ok", "entries_processed": 0, "entities_added": 0, "relations_added": 0}
    
    for entry in sessions:
        r = remember(
            entry["text"], 
            source=f"session:{session_id}:{entry['timestamp']}",
            auto_cognify=True
        )
        result["entries_processed"] += 1
        result["entities_added"] += r.get("entities_added", 0)
        result["relations_added"] += r.get("relations_added", 0)
    
    # Clear session after sync
    session_file.unlink()
    
    return result

# ─── Stats ────────────────────────────────────────────────────────

def stats() -> dict:
    """Get graph statistics."""
    G = load_graph()
    
    # Count by type
    types = {}
    for n, data in G.nodes(data=True):
        t = data.get("type", "Unknown")
        types[t] = types.get(t, 0) + 1
    
    # Count by relation type
    rel_types = {}
    for s, t, data in G.edges(data=True):
        rt = data.get("type", "unknown")
        rel_types[rt] = rel_types.get(rt, 0) + 1
    
    # Top connected nodes
    degrees = sorted(G.degree(), key=lambda x: x[1], reverse=True)[:10]
    top_nodes = [
        {"id": n, "name": G.nodes[n].get("name", n), "degree": d}
        for n, d in degrees
    ]
    
    return {
        "total_nodes": G.number_of_nodes(),
        "total_edges": G.number_of_edges(),
        "entity_types": types,
        "relation_types": rel_types,
        "top_connected": top_nodes,
        "session_count": len(list(SESSION_DIR.glob("*.json")))
    }

# ─── CLI ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="融策知识图谱引擎")
    ap.add_argument("action", choices=["stats", "remember", "recall", "forget", "improve"])
    ap.add_argument("--text", help="Text to remember")
    ap.add_argument("--query", help="Search query")
    ap.add_argument("--source", default="manual", help="Source identifier")
    ap.add_argument("--session", help="Session ID")
    ap.add_argument("--node", help="Node ID to forget")
    ap.add_argument("--hops", type=int, default=2, help="Graph traversal depth")
    ap.add_argument("--json", action="store_true", help="JSON output")
    
    args = ap.parse_args()
    
    def output(data):
        if args.json:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(data)
    
    if args.action == "stats":
        output(stats())
    elif args.action == "remember":
        if not args.text:
            print("Error: --text required")
            sys.exit(1)
        output(remember(args.text, source=args.source, session_id=args.session))
    elif args.action == "recall":
        if not args.query:
            print("Error: --query required")
            sys.exit(1)
        output(recall(args.query, session_id=args.session, max_hops=args.hops))
    elif args.action == "forget":
        output(forget(node_id=args.node, session_id=args.session))
    elif args.action == "improve":
        if not args.session:
            print("Error: --session required")
            sys.exit(1)
        output(improve(args.session))
