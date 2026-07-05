"""
融策 RAG 索引 - 文件监控自动重建
监控 knowledge/ 和 obsidian-vault/ 目录，检测到 .md 文件变化后自动重建索引
"""
import sys, os, time, subprocess, hashlib
sys.stdout.reconfigure(encoding='utf-8')

KNOWLEDGE_DIRS = [
    r'D:\openclaw-workspace\knowledge',
    r'D:\openclaw-workspace\obsidian-vault',
]
REBUILD_SCRIPT = r'D:\openclaw-workspace\scripts\rag_rebuild.py'

def get_file_hashes(dirs):
    """获取所有 .md 文件的哈希值"""
    hashes = {}
    for root in dirs:
        for dirpath, _, filenames in os.walk(root):
            skip = ['.git', '__pycache__', 'node_modules', '.obsidian']
            if any(s in dirpath for s in skip):
                continue
            for fn in filenames:
                if fn.endswith('.md') and not fn.startswith('.'):
                    fp = os.path.join(dirpath, fn)
                    try:
                        with open(fp, 'rb') as f:
                            h = hashlib.md5(f.read(16384)).hexdigest()  # first 16KB
                        hashes[fp] = h
                    except:
                        continue
    return hashes

print("=" * 50)
print(" 融策 RAG 索引 - 文件监控模式")
print(" 监控中: knowledge/ + obsidian-vault/")
print("=" * 50)
print("\n首次扫描...")

old_hashes = get_file_hashes(KNOWLEDGE_DIRS)
print(f"已记录 {len(old_hashes)} 个文件的状态")

trigger_count = 0
last_rebuild_time = 0

while True:
    time.sleep(15)  # 每15秒检查一次
    
    new_hashes = get_file_hashes(KNOWLEDGE_DIRS)
    
    changes = []
    for fp, h in new_hashes.items():
        if fp in old_hashes:
            if old_hashes[fp] != h:
                changes.append(f"修改: {os.path.relpath(fp, os.path.dirname(KNOWLEDGE_DIRS[0]))}")
        else:
            changes.append(f"新增: {os.path.relpath(fp, os.path.dirname(KNOWLEDGE_DIRS[0]))}")
    
    deleted = set(old_hashes.keys()) - set(new_hashes.keys())
    for fp in deleted:
        changes.append(f"删除: {os.path.relpath(fp, os.path.dirname(KNOWLEDGE_DIRS[0]))}")
    
    if changes:
        now = time.time()
        if now - last_rebuild_time > 30:  # 30秒内不重复重建
            print(f"\n[{time.strftime('%H:%M:%S')}] 检测到 {len(changes)} 处变更:")
            for c in changes[:5]:
                print(f"  {c}")
            if len(changes) > 5:
                print(f"  ...及{len(changes)-5}处其他变更")
            
            print("  正在重建索引...")
            try:
                result = subprocess.run([sys.executable, REBUILD_SCRIPT], 
                                        capture_output=True, text=True, timeout=300)
                if result.returncode == 0:
                    trigger_count += 1
                    last_rebuild_time = now
                    print(f"  ✅ 索引重建完成 (#{trigger_count})")
                else:
                    print(f"  ❌ 重建失败: {result.stderr[:200]}")
            except Exception as e:
                print(f"  ❌ 重建异常: {e}")
        
        old_hashes = new_hashes
