"""
批量构建知识图谱 — 遍历 knowledge/ 目录，逐文件 cognify 并入图谱
"""

import sys, os, asyncio, json, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts" / "knowledge_graph"))
from graph_engine import remember, stats, GRAPH_DIR, NODES_FILE

KNOWLEDGE_DIR = ROOT / "knowledge"

# 只处理 .md 文件，跳过索引文件
SKIP_PATTERNS = ["INDEX.md", "PARA-INDEX.md", "README.md", "SKILL.md", "CONTRIBUTING.md"]

def get_files_to_process(max_files: int = 0):
    """Get list of .md files to process, newest first."""
    files = []
    for f in KNOWLEDGE_DIR.rglob("*.md"):
        if f.name in SKIP_PATTERNS:
            continue
        if "_incoming" in str(f):
            continue  # Skip incoming, process separately
        files.append(f)
    
    files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    
    if max_files > 0:
        files = files[:max_files]
    
    return files

async def process_file(filepath: Path, dry_run: bool = False):
    """Process a single file: read + cognify + remember."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"  SKIP (read error): {filepath.name} - {e}")
        return None
    
    # Extract just the body (skip YAML frontmatter)
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            content = parts[2]
    
    if len(content) < 100:
        print(f"  SKIP (too short): {filepath.name}")
        return None
    
    rel_path = str(filepath.relative_to(ROOT))
    
    if dry_run:
        print(f"  [DRY] Would cognify: {rel_path} ({len(content)} chars)")
        return {"file": rel_path, "size": len(content)}
    
    print(f"  Cognifying: {rel_path} ({len(content)} chars)...", end=" ", flush=True)
    result = remember(content, source=rel_path, auto_cognify=True)
    print(f"+{result['entities_added']} entities, +{result['relations_added']} relations")
    return result

async def build_graph(max_files: int = 0, dry_run: bool = False, delay: float = 1.0):
    """Main build function."""
    files = get_files_to_process(max_files)
    print(f"Found {len(files)} files to process")
    
    results = []
    total_entities = 0
    total_relations = 0
    errors = 0
    
    for i, f in enumerate(files):
        print(f"[{i+1}/{len(files)}]", end=" ")
        try:
            r = await process_file(f, dry_run)
            if r:
                results.append(r)
                total_entities += r.get("entities_added", 0)
                total_relations += r.get("relations_added", 0)
            else:
                errors += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            errors += 1
        
        # Rate limiting
        if not dry_run and i < len(files) - 1:
            await asyncio.sleep(delay)
    
    print(f"\nDone. {len(results)} processed, {errors} errors")
    print(f"Total: +{total_entities} entities, +{total_relations} relations")
    
    # Print final stats
    s = stats()
    print(f"Graph: {s['total_nodes']} nodes, {s['total_edges']} edges")
    
    return results

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="批量构建知识图谱")
    ap.add_argument("--max", type=int, default=0, help="Max files to process (0=all)")
    ap.add_argument("--dry-run", action="store_true", help="List files without processing")
    ap.add_argument("--delay", type=float, default=1.0, help="Delay between files (seconds)")
    ap.add_argument("--reset", action="store_true", help="Clear existing graph before building")
    
    args = ap.parse_args()
    
    if args.reset:
        if NODES_FILE.exists():
            NODES_FILE.unlink()
            print("Graph reset.")
    
    asyncio.run(build_graph(max_files=args.max, dry_run=args.dry_run, delay=args.delay))
