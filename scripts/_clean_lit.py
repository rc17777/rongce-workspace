"""
清理 literature/ 目录：去重 + 去噪
先预览，确认后再执行
"""
import os, sys, re, shutil, json
sys.stdout.reconfigure(encoding='utf-8')

LIT = r'C:\Users\scrccpa\.openclaw\workspace\knowledge\literature'
CLEANED = os.path.join(LIT, '_cleaned')

# === 审计相关关键词（英文） ===
AUDIT_KEYWORDS = [
    'audit', 'auditing', 'auditor',
    'internal control', 'internal-control',
    'governance', 'financial reporting', 'financial-reporting',
    'fraud', 'earnings management', 'earnings-management',
    'accounting', 'accountability',
    'compliance', 'risk', 'risk-based',
    'assurance', 'attestation',
    'fiscal', 'public finance', 'public-finance',
    'budget', 'expenditure', 'procurement',
    'anti-corruption', 'anti-corruption',
    'whistleblow', 'transparency',
    'regulation', 'regulatory',
    'environmental audit', 'environmental-audit',
    'performance audit', 'performance-audit',
    'government audit', 'government-audit', 'state audit',
    'supreme audit', 'SAI',
    'tax audit', 'tax-audit',
    'esg', 'sustainability reporting',
    'blockchain audit',
    'data analytics audit',
]

# === 明显非审计关键词（噪音） ===
NOISE_KEYWORDS = [
    'weed detection', 'immigration trauma', 'posttraumatic',
    'catholic secondary school', 'école', 'élèves',
    'jeu de rôle', 'rôle ludique', 'collectivités territoriales',
    'sociolinguistics', 'machine identity', 'llm personality',
    'urbanisms', 'heritage and housing', 'jakarta',
    'dong-energy', 'ørsted',
    'house of cards', 'humphreys', 'slaughter',
    'organisational crime',
    'continental shift', 'operations and supply chain',
    'algorithmic justice', 'responsible ai journalism',
    'dark personality', 'project management',
    'multispecies', 'weed', 'crop',
    'immigration', 'refugee', 'trauma',
    'catholic', 'seminary', 'enrollment decline',
    'social media influencers', 'therapeutic compliance',
    'teachers involvement', 'schools', 'france',
    'interprofessional collaboration',
    'new public management', 'cultural fields',
    'professionalization commodification',
    'nursing', 'healthcare', 'clinical trial',
    'biomedical papers',
    'scientific and technical talent', 'housing',
    'constitutional protection', 'citizens privacy',
    'obe与职业', '高职纳税',
    'game strategy', 'mutual safety', 'coal mine',
    'maritime operation',
    'innovation practices', 'local authorities',
    'digital government', 'ai society',
    'supply chain', 'payment system',
]

def is_audit_related(filename_lower):
    """Check if filename suggests audit relevance"""
    # Chinese audit keywords
    cn_kw = ['审计', '内部控', '政府采', '预算', '绩效评', '财政', '会计', '合规']
    for kw in cn_kw:
        if kw in filename_lower:
            return True
    
    for kw in AUDIT_KEYWORDS:
        if kw in filename_lower:
            return True
    
    for kw in NOISE_KEYWORDS:
        if kw in filename_lower:
            return False
    
    # If none matched, check more carefully
    # These are borderline - keep if they have audit-adjacent terms
    borderline = ['financial', 'finance', 'corporate', 'disclosure', 'regulat', 
                  'govern', 'control', 'policy', 'public sector', 'public-sector']
    for kw in borderline:
        if kw in filename_lower:
            return True
    
    return False

def normalize_name(name):
    """Strip -N suffix for dedup comparison"""
    return re.sub(r'-\d+$', '', name.replace('.md', ''))

def main(dry_run=True):
    if dry_run:
        print("="*65)
        print("  🔍 预览模式 — 不实际删除")
        print("="*65)
    
    stats = {
        'total_before': 0,
        'duplicates': 0,
        'noise': 0,
        'anomalous_date': 0,
        'total_after': 0
    }
    
    removed = []
    
    # Scan all files
    all_files = []
    for root, dirs, files in os.walk(LIT):
        if '_cleaned' in root:
            continue
        for f in files:
            if f.endswith('.md'):
                fp = os.path.join(root, f)
                rel = os.path.relpath(fp, LIT)
                all_files.append({
                    'path': fp,
                    'relative': rel,
                    'name': f,
                    'size': os.path.getsize(fp),
                    'dir': os.path.dirname(fp)
                })
    
    stats['total_before'] = len(all_files)
    
    # === Pass 1: Dedup (keep largest version) ===
    name_groups = {}
    for f in all_files:
        norm = normalize_name(f['name'])
        if norm not in name_groups:
            name_groups[norm] = []
        name_groups[norm].append(f)
    
    keep_dedup = []
    for norm, group in name_groups.items():
        if len(group) == 1:
            keep_dedup.append(group[0])
        else:
            # Keep the largest file
            group.sort(key=lambda x: -x['size'])
            keep_dedup.append(group[0])
            for dup in group[1:]:
                removed.append({**dup, 'reason': f'重复({len(group)}份副本)'})
                stats['duplicates'] += 1
    
    print(f"\n  去重: {len(all_files)} → {len(keep_dedup)} (移除 {stats['duplicates']} 重复)")
    
    # === Pass 2: Remove noise (non-audit) ===
    keep_noise = []
    for f in keep_dedup:
        name_lower = f['name'].lower()
        if is_audit_related(name_lower):
            keep_noise.append(f)
        else:
            removed.append({**f, 'reason': '非审计主题(噪音)'})
            stats['noise'] += 1
    
    print(f"  去噪: {len(keep_dedup)} → {len(keep_noise)} (移除 {stats['noise']} 噪音)")
    
    # === Pass 3: Flag anomalous dates ===
    anomalous_dirs = ['2027', '2028', '2031', '2050']
    keep_final = []
    for f in keep_noise:
        is_anomalous = any(ad in f['relative'] for ad in anomalous_dirs)
        if is_anomalous:
            # Move to anomalous but keep (might have valid content)
            removed.append({**f, 'reason': '日期异常(移到_anomalous)'})
            stats['anomalous_date'] += 1
        else:
            keep_final.append(f)
    
    stats['total_after'] = len(keep_final)
    
    # === Report ===
    print(f"\n{'='*65}")
    print(f"  清理预览")
    print(f"{'='*65}")
    print(f"  清理前: {stats['total_before']}篇")
    print(f"  去重:   -{stats['duplicates']}篇")
    print(f"  去噪:   -{stats['noise']}篇")
    print(f"  日期异常: -{stats['anomalous_date']}篇")
    print(f"  清理后: {stats['total_after']}篇")
    print(f"  保留率: {stats['total_after']/stats['total_before']*100:.0f}%")
    
    # Show noise samples
    noise_samples = [r for r in removed if r['reason'] == '非审计主题(噪音)'][:15]
    if noise_samples:
        print(f"\n  🗑️ 噪音样例 ({stats['noise']}篇中):")
        for r in noise_samples:
            print(f"    · {r['name'][:70]}")
    
    # Show date anomaly samples
    date_samples = [r for r in removed if '日期异常' in r['reason']][:10]
    if date_samples:
        print(f"\n  📅 日期异常样例 ({stats['anomalous_date']}篇):")
        for r in date_samples:
            print(f"    · [{os.path.basename(os.path.dirname(r['path']))}] {r['name'][:60]}")
    
    if dry_run:
        print(f"\n  ⚠️ 预览完成。要执行清理请运行: python scripts/_clean_lit.py --execute")
    else:
        # Execute
        os.makedirs(CLEANED, exist_ok=True)
        
        # Move removed files
        for r in removed:
            rel_dir = os.path.dirname(r['relative'])
            dest_dir = os.path.join(CLEANED, rel_dir)
            os.makedirs(dest_dir, exist_ok=True)
            dest = os.path.join(dest_dir, r['name'])
            try:
                shutil.move(r['path'], dest)
            except Exception as e:
                print(f"  ❌ 移动失败 {r['name']}: {e}")
        
        # Save manifest
        manifest = {
            'stats': stats,
            'removed': [{'name': r['name'], 'relative': r['relative'], 'reason': r['reason']} for r in removed],
            'cleaned_to': CLEANED
        }
        with open(os.path.join(CLEANED, '_cleanup_manifest.json'), 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        
        # Clean empty dirs
        for root, dirs, files in os.walk(LIT, topdown=False):
            if '_cleaned' in root:
                continue
            if not os.listdir(root):
                os.rmdir(root)
        
        print(f"\n  ✅ 清理完成！{stats['duplicates']+stats['noise']+stats['anomalous_date']}篇已移至 _cleaned/")
        print(f"  如需恢复: 从 _cleaned/ 移回即可")

if __name__ == '__main__':
    execute = '--execute' in sys.argv
    main(dry_run=not execute)
