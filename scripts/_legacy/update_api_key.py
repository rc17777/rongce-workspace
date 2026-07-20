"""API Key 更新工具
用法:
  python scripts/update_api_key.py list              # 列出所有 provider 的 key 状态
  python scripts/update_api_key.py set <provider> <new_key>   # 更新某个 provider 的 key
  python scripts/update_api_key.py batch             # 批量更新所有 key（交互式）
  python scripts/update_api_key.py check             # 健康检查 + key 状态

示例:
  python scripts/update_api_key.py set custom-cbwyy-fable sk-xxxxx
  python scripts/update_api_key.py list
"""

import json, sys, io, os, subprocess, datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CONFIG_PATH = r'C:\Users\scrccpa\.openclaw\openclaw.json'
BACKUP_DIR = r'C:\Users\scrccpa\.openclaw\workspace\backups'
os.makedirs(BACKUP_DIR, exist_ok=True)

# Provider 显示名映射
PROVIDER_NAMES = {
    'custom-cbwyy-top-v1': 'deepseek-v4-flash/pro（日常执行）',
    'custom-cbwyy-gpt55': 'gpt-5.5（表达审查）',
    'custom-cbwyy-claude': 'claude-sonnet-5（逻辑审查）',
    'custom-cbwyy-opus': 'claude-opus-4-8（终审签字）',
    'custom-cbwyy-fable': 'claude-fable-5（咨询层）',
    'custom-cbwyy-doubao': 'doubao-seed-2.0-lite（合规备选）',
    'custom-cbwyy-image': 'gpt-image-2（生图）',
    'custom-cbwyy-qwen': 'qwen3.7-plus（中文·图片）',
    'custom-cbwyy-luna': 'gpt-5.6-luna（审查）',
    'custom-cbwyy-sol': 'gpt-5.6-sol（审查）',
    'custom-cbwyy-terra': 'gpt-5.6-terra（审查）',
}


def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_config(config, backup=True):
    if backup:
        ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(BACKUP_DIR, f'openclaw_{ts}.json')
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f'[BACKUP] {backup_path}')
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f'[SAVED] {CONFIG_PATH}')


def mask_key(key, show=8):
    """显示 key 前 show 位和后 4 位"""
    if not key or len(key) < 15:
        return '(空)'
    return key[:show] + '...' + key[-4:]


def list_keys():
    config = load_config()
    providers = config['models']['providers']
    
    if not providers:
        print('[WARN] 未找到任何 provider')
        return
    
    print(f'{"Provider":<30} {"Key状态":<40} {"模型":<25}')
    print('-' * 95)
    for pid, prov in providers.items():
        key = prov.get('apiKey', '')
        models = ', '.join(m.get('id', '?') for m in prov.get('models', []))
        if key.startswith('env://'):
            key_status = f'[env引用] {key[6:]}'
        elif key:
            key_status = f'[明文] {mask_key(key)}'
        else:
            key_status = '[空]'
        name = PROVIDER_NAMES.get(pid, pid)
        print(f'{pid:<30} {key_status:<40} {models:<25}')
        print(f'  {"":>30} {name}')


def set_key(provider_id, new_key):
    config = load_config()
    providers = config['models']['providers']
    
    if provider_id not in providers:
        print(f'[ERROR] 未找到 provider: {provider_id}')
        print(f'  可用: {", ".join(providers.keys())}')
        sys.exit(1)
    
    old_key = providers[provider_id].get('apiKey', '')
    providers[provider_id]['apiKey'] = new_key
    
    save_config(config)
    
    name = PROVIDER_NAMES.get(provider_id, provider_id)
    print(f'[UPDATED] {provider_id} ({name})')
    print(f'  旧: {mask_key(old_key)}')
    print(f'  新: {mask_key(new_key)}')
    print()
    print('[*] 配置已更新，建议重启 Gateway: openclaw gateway restart')


def batch_update():
    """交互式批量更新"""
    config = load_config()
    providers = config['models']['providers']
    
    print(f'找到 {len(providers)} 个 provider:')
    print()
    
    updates = {}
    for pid, prov in providers.items():
        key = prov.get('apiKey', '')
        old_masked = mask_key(key)
        name = PROVIDER_NAMES.get(pid, pid)
        print(f'  [{pid}]')
        print(f'    说明: {name}')
        print(f'    当前: {old_masked}')
        print(f'    模型: {", ".join(m.get("id", "?") for m in prov.get("models", []))}')
        new_key = input(f'    新 key (回车跳过): ').strip()
        if new_key:
            updates[pid] = new_key
        print()
    
    if not updates:
        print('[INFO] 没有更新任何 key')
        return
    
    print(f'即将更新 {len(updates)} 个 provider:')
    for pid, new_key in updates.items():
        old_key = providers[pid].get('apiKey', '')
        print(f'  {pid}: {mask_key(old_key)} -> {mask_key(new_key)}')
    
    confirm = input(f'确认更新? (y/N): ').strip().lower()
    if confirm != 'y':
        print('[CANCELED]')
        return
    
    for pid, new_key in updates.items():
        providers[pid]['apiKey'] = new_key
    
    save_config(config)
    print(f'[DONE] 已更新 {len(updates)} 个 key')
    print('[*] 建议重启 Gateway: openclaw gateway restart')


def check():
    """健康检查 + key 状态"""
    print('=' * 60)
    print('Key 状态检查')
    print('=' * 60)
    list_keys()
    print()
    
    print('=' * 60)
    print('运行健康检查...')
    print('=' * 60)
    result = subprocess.run(
        [sys.executable, 'scripts/deepseek_model_check.py'],
        capture_output=True, timeout=120
    )
    out = result.stdout.decode('utf-8', errors='replace')
    err = result.stderr.decode('utf-8', errors='replace')
    print(out)
    if err.strip():
        print('STDERR:', err[:500])
    
    if result.returncode == 0:
        print('[OK] 全部正常')
    else:
        print('[WARN] 有异常，请检查上方输出')


def usage():
    print(__doc__)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == 'list':
        list_keys()
    elif action == 'set':
        if len(sys.argv) < 4:
            print('[ERROR] 用法: python scripts/update_api_key.py set <provider_id> <new_key>')
            print('  可用 provider 列表:')
            list_keys()
            sys.exit(1)
        set_key(sys.argv[2], sys.argv[3])
    elif action == 'batch':
        batch_update()
    elif action == 'check':
        check()
    else:
        print(f'[ERROR] 未知操作: {action}')
        usage()
        sys.exit(1)