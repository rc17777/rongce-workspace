"""融策 Skill 安全扫描器 — 检查共享技能中的安全隐患"""
import sys, os, re, glob

sys.stdout.reconfigure(encoding='utf-8')

SHARED_ROOT = os.path.expanduser(r'~\.openclaw\workspace\shared-skills')

# 检测规则
PATTERNS = {
    '内部IP地址': r'\b(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})\b',
    '硬编码API Key': r'(api[_-]?key|apikey|secret[_-]?key|access[_-]?key)\s*[:=]\s*["\']?[a-zA-Z0-9_\-]{20,}["\']?',
    '身份证号': r'\b[1-9]\d{5}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b',
    '手机号': r'\b1[3-9]\d{9}\b',
    '银行账号': r'\b\d{16,19}\b',
    '疑似客户数据': r'(客户名称|被审计单位|XXX公司|某某某).{0,20}(账号|密码|金额|余额|收入|支出)',
    '内网域名': r'\.(local|internal|corp|lan)\b|\.oa\.com\b',
}

def scan_file(filepath):
    results = []
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        lines = content.split('\n')
    
    for rule_name, pattern in PATTERNS.items():
        for i, line in enumerate(lines, 1):
            # 跳过注释行
            if line.strip().startswith('#') or line.strip().startswith('//'):
                continue
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for m in matches:
                results.append({
                    'rule': rule_name,
                    'line': i,
                    'match': m.group()[:60],
                })
    return results

def main():
    skill_files = glob.glob(os.path.join(SHARED_ROOT, '**/SKILL.md'), recursive=True)
    skill_files += glob.glob(os.path.join(SHARED_ROOT, '**/README.md'), recursive=True)
    
    total_issues = 0
    files_with_issues = 0
    
    print("=" * 60)
    print("融策 Skill 安全扫描报告")
    print("=" * 60)
    
    for fpath in sorted(skill_files):
        issues = scan_file(fpath)
        if issues:
            files_with_issues += 1
            total_issues += len(issues)
            rel = os.path.relpath(fpath, SHARED_ROOT)
            print(f"\n📄 {rel}")
            for issue in issues:
                print(f"  ⚠️  [{issue['rule']}] L{issue['line']}: ...{issue['match']}...")
    
    print(f"\n{'=' * 60}")
    if total_issues == 0:
        print("✅ 未发现安全隐患")
    else:
        print(f"⚠️  发现 {total_issues} 个潜在风险，涉及 {files_with_issues} 个文件")
        print(f"   请人工核实，确认无泄露后可将此扫描加入 git push hook")
    
    return 1 if total_issues > 0 else 0

if __name__ == '__main__':
    sys.exit(main())
