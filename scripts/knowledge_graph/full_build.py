"""Full batch knowledge graph builder - processes all knowledge/ files."""
import asyncio, sys, os, time, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\scrccpa\.openclaw\workspace\scripts\knowledge_graph')
from graph_engine import aremember, stats, load_graph, save_graph
from pathlib import Path

ROOT = Path(r'C:\Users\scrccpa\.openclaw\workspace')
KNOWLEDGE_DIR = ROOT / 'knowledge'
PROGRESS_FILE = ROOT / 'data' / 'knowledge_graph' / 'build_progress.json'

SKIP_PATTERNS = ['INDEX.md', 'PARA-INDEX.md', 'README.md', 'SKILL.md', 'CONTRIBUTING.md']


def load_progress():
    if PROGRESS_FILE.exists():
        try:
            return set(json.loads(PROGRESS_FILE.read_text(encoding='utf-8')))
        except Exception:
            return set()
    return set()


def save_progress(done: set):
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_FILE.write_text(json.dumps(sorted(done), ensure_ascii=False), encoding='utf-8')

async def main(max_files: int = 0, delay: float = 1.5, chunk_size: int = 5000):
    files = []
    for f in KNOWLEDGE_DIR.rglob('*.md'):
        if f.name in SKIP_PATTERNS:
            continue
        if '_incoming' in str(f):
            continue
        files.append(f)
    
    files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    if max_files > 0:
        files = files[:max_files]
    
    done = load_progress()
    if done:
        before = len(files)
        files = [f for f in files if str(f.relative_to(ROOT)) not in done]
        print(f'Resume mode: {len(done)} already done, {before - len(files)} skipped')
    
    print(f'Starting batch: {len(files)} files')
    print(f'Chunk size: {chunk_size} chars | Delay: {delay}s')
    print('=' * 60)
    
    start_time = time.time()
    total_entities = 0
    total_relations = 0
    processed = 0
    errors = 0
    skipped = 0
    
    for i, fpath in enumerate(files):
        rel = str(fpath.relative_to(ROOT))
        
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            errors += 1
            continue
        
        # Skip YAML frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                content = parts[2]
        
        if len(content) < 200:
            skipped += 1
            done.add(rel)
            save_progress(done)
            continue
        
        # Chunk if too long
        content = content[:chunk_size]
        
        print(f'[{i+1}/{len(files)}] {rel} ({len(content)}c)...', end=' ', flush=True)
        
        try:
            r = await aremember(content, source=rel, auto_cognify=True)
            e = r.get('entities_added', 0)
            rl = r.get('relations_added', 0)
            total_entities += e
            total_relations += rl
            processed += 1
            done.add(rel)
            save_progress(done)
            print(f'+{e}e +{rl}r')
        except Exception as ex:
            print(f'ERROR: {ex}')
            errors += 1
        
        # Progress report every 10 files
        if (i + 1) % 10 == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed * 60 if elapsed > 0 else 0
            eta = (len(files) - i - 1) / rate if rate > 0 else 0
            s = stats()
            print(f'  --- Progress: {i+1}/{len(files)} | {rate:.1f} files/min | ETA {eta:.1f}min | Graph: {s["total_nodes"]}n/{s["total_edges"]}e ---')
        
        await asyncio.sleep(delay)
    
    elapsed = time.time() - start_time
    s = stats()
    
    print('\n' + '=' * 60)
    print(f'DONE in {elapsed/60:.1f} min')
    print(f'Processed: {processed} | Skipped: {skipped} | Errors: {errors}')
    print(f'New entities: {total_entities} | New relations: {total_relations}')
    print(f'Total graph: {s["total_nodes"]} nodes | {s["total_edges"]} edges')
    print(f'Entity types: {json.dumps(s["entity_types"], ensure_ascii=False)}')

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--max', type=int, default=0, help='Max files (0=all)')
    ap.add_argument('--delay', type=float, default=1.5, help='Delay between files')
    ap.add_argument('--chunk', type=int, default=5000, help='Chars per file')
    args = ap.parse_args()
    asyncio.run(main(max_files=args.max, delay=args.delay, chunk_size=args.chunk))
