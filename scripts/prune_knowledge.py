"""
知识库内容清理工具 - prune_knowledge.py
扫描 knowledge/ 和 obsidian-vault/ 中的 md/json 文件，
标记 6 个月未修改的笔记，建议归档或删除。
"""
import os, sys, json, time
from pathlib import Path
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE = Path(r"C:\Users\scrccpa\.openclaw\workspace")
KNOWLEDGE = WORKSPACE / "knowledge"
OBSIDIAN = WORKSPACE / "obsidian-vault"
ARCHIVE_DIR = WORKSPACE / "knowledge" / "archives"

SIX_MONTHS = 180 * 24 * 3600  # 秒
ONE_YEAR = 365 * 24 * 3600

def scan_files(root: Path, patterns=("*.md", "*.json"), skip_dirs=None):
    """递归扫描目录，返回文件列表"""
    skip_dirs = skip_dirs or {'.obsidian', '_templates', 'archives', '.git'}
    files = []
    for p in patterns:
        for f in root.rglob(p):
            if any(s in f.parts for s in skip_dirs):
                continue
            files.append(f)
    return files

def classify_file(fpath: Path) -> dict:
    """分类文件：活跃 / 休眠 / 僵尸"""
    mtime = fpath.stat().st_mtime
    age = time.time() - mtime
    size = fpath.stat().st_size
    
    if age < SIX_MONTHS:
        status = "active"
        icon = "🟢"
    elif age < ONE_YEAR:
        status = "dormant"
        icon = "🟡"
    else:
        status = "zombie"
        icon = "🔴"
    
    return {
        "path": str(fpath.relative_to(WORKSPACE)),
        "mtime": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d"),
        "age_days": int(age / 86400),
        "size_kb": round(size / 1024, 1),
        "status": status,
        "icon": icon
    }

def main():
    print("=" * 60)
    print("  知识库内容清理扫描")
    print(f"  扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  休眠阈值: 6个月 | 僵尸阈值: 1年")
    print("=" * 60)
    
    all_files = []
    for root, label in [(KNOWLEDGE, "knowledge"), (OBSIDIAN, "obsidian-vault")]:
        if not root.exists():
            print(f"\n  ⚠️ {label} 目录不存在，跳过")
            continue
        files = scan_files(root)
        for f in files:
            info = classify_file(f)
            info["source"] = label
            all_files.append(info)
    
    # 统计
    active = [f for f in all_files if f["status"] == "active"]
    dormant = [f for f in all_files if f["status"] == "dormant"]
    zombie = [f for f in all_files if f["status"] == "zombie"]
    
    print(f"\n📊 总体概览")
    print(f"  总文件数: {len(all_files)}")
    print(f"  🟢 活跃 (<6月):  {len(active):4d} ({len(active)/max(len(all_files),1)*100:.0f}%)")
    print(f"  🟡 休眠 (6-12月): {len(dormant):4d} ({len(dormant)/max(len(all_files),1)*100:.0f}%)")
    print(f"  🔴 僵尸 (>1年):   {len(zombie):4d} ({len(zombie)/max(len(all_files),1)*100:.0f}%)")
    
    # 按来源统计
    for src in ["knowledge", "obsidian-vault"]:
        src_files = [f for f in all_files if f["source"] == src]
        if not src_files:
            continue
        src_zombie = [f for f in src_files if f["status"] == "zombie"]
        src_dormant = [f for f in src_files if f["status"] == "dormant"]
        print(f"\n📁 {src}/")
        print(f"  文件数: {len(src_files)} | 僵尸: {len(src_zombie)} | 休眠: {len(src_dormant)}")
        if src_zombie:
            print(f"  僵尸文件列表:")
            for f in sorted(src_zombie, key=lambda x: x["age_days"], reverse=True)[:20]:
                print(f"    🔴 {f['path']:50s} ({f['age_days']}天前, {f['size_kb']}KB)")
    
    # 建议
    print(f"\n💡 建议操作")
    
    total_zombie_size = sum(f["size_kb"] for f in zombie)
    total_dormant = len(dormant)
    
    if not dormant and not zombie:
        print("  ✅ 知识库状态良好，无需清理")
    else:
        print(f"  📦 可归档文件: {len(zombie)} 个僵尸 ({total_zombie_size:.0f}KB)")
        print(f"  ⏸️  待观察: {len(dormant)} 个休眠文件")
        print(f"")
        print(f"  操作选项:")
        print(f"    python prune_knowledge.py --dry-run     # 预览模式（默认）")
        print(f"    python prune_knowledge.py --archive     # 移动僵尸文件到 archives/")
        print(f"    python prune_knowledge.py --delete      # ⚠️ 删除僵尸文件（谨慎！）")
        print(f"    python prune_knowledge.py --report json # 导出 JSON 报告")
    
    # 导出报告
    report_path = WORKSPACE / "knowledge" / "prune_report.json"
    report = {
        "scan_time": datetime.now().isoformat(),
        "totals": {"active": len(active), "dormant": len(dormant), "zombie": len(zombie)},
        "zombie_files": [{"path": f["path"], "age_days": f["age_days"], "size_kb": f["size_kb"]} 
                        for f in sorted(zombie, key=lambda x: x["age_days"], reverse=True)],
        "dormant_files": [{"path": f["path"], "age_days": f["age_days"], "size_kb": f["size_kb"]} 
                         for f in sorted(dormant, key=lambda x: x["age_days"], reverse=True)]
    }
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n📋 报告已保存: {report_path}")
    
    return all_files, zombie, dormant

def do_archive(zombie_files):
    """移动僵尸文件到 archives/"""
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    moved = 0
    for f in zombie_files:
        src = WORKSPACE / f["path"]
        # 保持相对路径结构
        dst = ARCHIVE_DIR / Path(f["path"]).name
        if src.exists():
            src.rename(dst)
            moved += 1
            print(f"  📦 {f['path']} → archives/")
    print(f"\n✅ 已归档 {moved} 个文件到 {ARCHIVE_DIR}")
    return moved

def do_delete(zombie_files):
    """删除僵尸文件"""
    deleted = 0
    for f in zombie_files:
        src = WORKSPACE / f["path"]
        if src.exists():
            src.unlink()
            deleted += 1
            print(f"  🗑️ 已删除: {f['path']}")
    print(f"\n✅ 已删除 {deleted} 个文件")
    return deleted

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "--dry-run"
    all_files, zombie, dormant = main()
    
    if mode == "--archive" and zombie:
        confirm = input(f"\n⚠️ 将归档 {len(zombie)} 个僵尸文件到 archives/，确认？(y/N): ")
        if confirm.lower() == 'y':
            do_archive(zombie)
    elif mode == "--delete" and zombie:
        confirm = input(f"\n⚠️⚠️ 将永久删除 {len(zombie)} 个文件，不可恢复！确认？(yes/N): ")
        if confirm.lower() == 'yes':
            do_delete(zombie)
