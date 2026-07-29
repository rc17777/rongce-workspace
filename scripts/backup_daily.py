"""每日资料备份：git commit + push + OneDrive 同步
用法：python scripts/backup_daily.py
退出码：0=成功 1=commit失败 2=push失败 3=OneDrive失败
"""
import sys, os, subprocess, datetime

WORKSPACE = os.path.expanduser('~/.openclaw/workspace')
ONE_DRIVE = os.path.expanduser('~/OneDrive/融策备份')

def run(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, encoding='gbk', errors='replace', cwd=cwd or WORKSPACE, timeout=120)
    return result.returncode, result.stdout.strip(), result.stderr.strip()

def git_backup():
    """Step 1: git commit + push"""
    print('[1/3] Git backup...')
    
    # Check if there are changes
    code, out, err = run('git status --porcelain')
    if code != 0:
        print(f'  git status failed: {err}')
        return 1
    
    if not out:
        print('  No changes to commit')
        # Still try to push (catch up)
        code, out, err = run('git push origin master')
        if code == 0:
            print('  Push OK (no new commits)')
            return 0
        else:
            print(f'  Push failed (proxy down?): {err[:100]}')
            return 2
        return 0
    
    # Commit changes
    date_tag = datetime.datetime.now().strftime('%Y-%m-%d')
    code, out, err = run(f'git add -A . && git commit -m "Auto backup {date_tag}"')
    if code != 0:
        # Maybe no changes to commit after add
        if 'nothing to commit' in err.lower() or 'nothing to commit' in out.lower():
            print('  Nothing to commit after add')
        else:
            print(f'  Commit failed: {err[:200]}')
            return 1
    
    # Push
    code, out, err = run('git push origin master')
    if code == 0:
        print('  Commit + Push OK')
        return 0
    else:
        print(f'  Push failed (proxy down?): {err[:100]}')
        return 2

def onedrive_sync():
    """Step 2: Sync D-knowledge to OneDrive"""
    print('[2/3] OneDrive sync...')
    
    d_knowledge = r'D:\openclaw-workspace\knowledge'
    target = os.path.join(ONE_DRIVE, 'knowledge')
    
    os.makedirs(target, exist_ok=True)
    
    code, out, err = run(f'robocopy "{d_knowledge}" "{target}" /E /R:2 /W:3 /NP /NFL /NDL /XO')
    # robocopy returns 0=ok, 1=copied, 2=extra, 3=copied+extra
    if code <= 3:
        print('  OneDrive knowledge sync OK')
    else:
        print(f'  OneDrive sync warning: code={code}')
        return 3
    
    # Backup openclaw.json
    src = os.path.expanduser('~/.openclaw/openclaw.json')
    dst = os.path.join(ONE_DRIVE, 'openclaw.json.bak')
    if os.path.exists(src):
        import shutil
        shutil.copy2(src, dst)
        print('  API key backup OK')
    
    return 0

def main():
    errors = 0
    
    r1 = git_backup()
    if r1 > 0:
        errors += 1
    
    r2 = onedrive_sync()
    if r2 > 0:
        errors += 1
    
    print(f'[3/3] Done. Errors: {errors}')
    return min(errors, 3)

if __name__ == '__main__':
    sys.exit(main())
