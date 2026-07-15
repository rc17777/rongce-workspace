"""Quick batch ingest: key reference files into knowledge graph.
Fixed: uses async cognify directly to avoid event loop nesting."""
import asyncio, sys, json, hashlib
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\scrccpa\.openclaw\workspace\scripts\knowledge_graph')
from graph_engine import cognify_text, load_graph, save_graph, entity_id, stats
from pathlib import Path

async def main():
    root = Path(r'C:\Users\scrccpa\.openclaw\workspace')
    files = [
        'knowledge/references/审计署2026年1号公告-招投标六类违规检查清单.md',
        'knowledge/references/经济责任审计-融策整合模板v2.0.md',
    ]
    
    G = load_graph()
    
    for fp in files:
        fpath = root / fp
        if not fpath.exists():
            print(f'NOT FOUND: {fp}')
            continue
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        if content.startswith('---'):
            parts = content.split('---', 2)
            content = parts[2] if len(parts) >= 3 else content
        content = content[:5000]
        print(f'Cognifying: {fp} ({len(content)} chars)...')
        
        extraction = await cognify_text(content)
        entities = extraction.get("entities", [])
        relations = extraction.get("relations", [])
        
        e_added = 0
        for ent in entities:
            eid = entity_id(ent["name"], ent["type"])
            if not G.has_node(eid):
                G.add_node(eid, name=ent["name"], type=ent["type"],
                           properties=ent.get("properties", {}), sources=[fp])
                e_added += 1
            else:
                srcs = G.nodes[eid].get("sources", [])
                if fp not in srcs:
                    srcs.append(fp)
                    G.nodes[eid]["sources"] = srcs
        
        r_added = 0
        for rel in relations:
            # Guess types for source/target
            src_type = next((e["type"] for e in entities if e["name"] == rel["source"]), "Unknown")
            tgt_type = next((e["type"] for e in entities if e["name"] == rel["target"]), "Unknown")
            src_id = entity_id(rel["source"], src_type)
            tgt_id = entity_id(rel["target"], tgt_type)
            
            if not G.has_edge(src_id, tgt_id):
                G.add_edge(src_id, tgt_id, type=rel["type"], 
                           evidence=rel.get("evidence", ""), sources=[fp])
                r_added += 1
        
        print(f'  +{e_added} entities, +{r_added} relations')
        save_graph(G)
        await asyncio.sleep(1.5)
    
    s = stats()
    print(f'\nGraph: {s["total_nodes"]} nodes, {s["total_edges"]} edges')
    for ent_type, count in sorted(s['entity_types'].items(), key=lambda x: -x[1]):
        print(f'  {ent_type}: {count}')

asyncio.run(main())
