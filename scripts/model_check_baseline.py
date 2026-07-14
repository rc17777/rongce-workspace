"""模型调用状态基线验证
用法: python scripts/model_check_baseline.py
用途: 验证所有模型可调用，输出健康报告
"""
import json, subprocess, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 直接调用健康检查，处理GBK编码问题
result = subprocess.run(
    [sys.executable, 'scripts/deepseek_model_check.py'],
    capture_output=True, timeout=120
)
# 解码输出（处理GBK问题）
out = result.stdout.decode('utf-8', errors='replace')
err = result.stderr.decode('utf-8', errors='replace')
print(out)

# 检查 openclaw.json 是否还有 env://
path = r'C:\Users\scrccpa\.openclaw\openclaw.json'
with open(path, 'r', encoding='utf-8') as f:
    config = json.load(f)

env_refs = []
for prov_id, prov in config['models']['providers'].items():
    for k in ['apiKey', 'apiSecret']:
        val = prov.get(k, '')
        if val.startswith('env://'):
            env_refs.append(f'{prov_id}.{k}')

if env_refs:
    print(f'[WARN] 仍有 {len(env_refs)} 个 env:// 引用: {env_refs}')
else:
    print('[OK] 所有 key 为明文，无 env:// 引用')

sys.exit(0 if result.returncode == 0 else 1)