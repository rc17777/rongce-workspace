import json, shutil, time
from pathlib import Path

home = Path.home()
root_cfg = home / '.openclaw' / 'openclaw.json'
agent_models = home / '.openclaw' / 'agents' / 'main' / 'agent' / 'models.json'
stamp = time.strftime('%Y%m%d-%H%M%S')

MAIN_PROVIDER = 'custom-cbwyy-top-v1'
MAIN_MODEL = 'gpt-5.5'
HEARTBEAT_PROVIDER = 'custom-cbwxy-top-v1'
HEARTBEAT_MODEL = 'deepseek-v4-flash'

for p in [root_cfg, agent_models]:
    if not p.exists():
        raise SystemExit(f'MISSING: {p}')

backup_dir = home / '.openclaw' / 'backup' / f'model-config-{stamp}'
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(root_cfg, backup_dir / 'openclaw.json')
shutil.copy2(agent_models, backup_dir / 'agent.models.json')

root = json.loads(root_cfg.read_text(encoding='utf-8'))
agent = json.loads(agent_models.read_text(encoding='utf-8'))

def provider_has_model(providers, pid, mid):
    return pid in providers and any(m.get('id') == mid for m in providers[pid].get('models', []))

root_providers = root.setdefault('models', {}).setdefault('providers', {})
agent_providers = agent.setdefault('providers', {})

# 校验：主配置必须有 cbwyy/gpt-5.5；agent models 必须有 cbwyy/gpt-5.5 和 cbwxy/deepseek-v4-flash
if not provider_has_model(root_providers, MAIN_PROVIDER, MAIN_MODEL):
    raise SystemExit(f'Root config missing {MAIN_PROVIDER}/{MAIN_MODEL}; backup at {backup_dir}')
if not provider_has_model(agent_providers, MAIN_PROVIDER, MAIN_MODEL):
    raise SystemExit(f'Agent models missing {MAIN_PROVIDER}/{MAIN_MODEL}; backup at {backup_dir}')
if not provider_has_model(agent_providers, HEARTBEAT_PROVIDER, HEARTBEAT_MODEL):
    raise SystemExit(f'Agent models missing heartbeat {HEARTBEAT_PROVIDER}/{HEARTBEAT_MODEL}; backup at {backup_dir}')

# 1) 主配置默认模型固定
root.setdefault('agents', {}).setdefault('defaults', {})['model'] = {
    'primary': f'{MAIN_PROVIDER}/{MAIN_MODEL}',
    'fallbacks': [
        'custom-cbwyy-top/claude-fable-5',
        f'{MAIN_PROVIDER}/{MAIN_MODEL}'
    ]
}

# 2) 修正 claude-sonnet-5 显示名 typo（仅显示名）
for pid in ['custom-cbwyy-top']:
    if pid in root_providers:
        for m in root_providers[pid].get('models', []):
            if m.get('id') == 'claude-sonnet-5' and m.get('name') == 'chaude-sonnet-5':
                m['name'] = 'claude-sonnet-5'
    if pid in agent_providers:
        for m in agent_providers[pid].get('models', []):
            if m.get('id') == 'claude-sonnet-5' and m.get('name') == 'chaude-sonnet-5':
                m['name'] = 'claude-sonnet-5'

# 3) Agent models.json：保留 cbwyy 主 provider、cbwyy claude fallback、cbwxy 心跳 provider、deepseek 官方 provider。
#    删除明显历史/简写重复项，避免 UI 打开后模型池混乱。
keep = {'deepseek', MAIN_PROVIDER, 'custom-cbwyy-top', HEARTBEAT_PROVIDER}
removed = sorted([k for k in list(agent_providers.keys()) if k not in keep])
agent['providers'] = {k: v for k, v in agent_providers.items() if k in keep}

# 4) 对齐 cbwyy 主 provider：只保留当前明确需要的主模型和 deepseek 两个模型
if MAIN_PROVIDER in agent['providers']:
    wanted = {MAIN_MODEL, 'deepseek-v4-pro', 'deepseek-v4-flash'}
    agent['providers'][MAIN_PROVIDER]['models'] = [m for m in agent['providers'][MAIN_PROVIDER].get('models', []) if m.get('id') in wanted]

# 5) 心跳 provider 只保留 deepseek-v4-flash，避免被误选为普通模型池
if HEARTBEAT_PROVIDER in agent['providers']:
    agent['providers'][HEARTBEAT_PROVIDER]['models'] = [m for m in agent['providers'][HEARTBEAT_PROVIDER].get('models', []) if m.get('id') == HEARTBEAT_MODEL]

root_cfg.write_text(json.dumps(root, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
agent_models.write_text(json.dumps(agent, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

print('OK')
print('backup:', backup_dir)
print('removed_agent_providers:', ', '.join(removed) if removed else '(none)')
print('default:', f'{MAIN_PROVIDER}/{MAIN_MODEL}')
print('heartbeat_kept:', f'{HEARTBEAT_PROVIDER}/{HEARTBEAT_MODEL}')
