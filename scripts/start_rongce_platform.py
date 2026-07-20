"""
融策审计中台 - 一键启动脚本 v2
==================================
启动：python scripts/start_rongce_platform.py
"""

import sys, os, time, subprocess, socket, webbrowser, json

sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE = r'C:\Users\scrccpa\.openclaw\workspace'
SCRIPTS = os.path.join(WORKSPACE, 'scripts')

SERVICES = {
    'rag_api': {
        'name': '🔍 RAG混合检索API',
        'port': 5001,
        'cmd': [sys.executable, '-X', 'utf8', os.path.join(SCRIPTS, 'rag_vector.py'), 'serve', '--port', '5001'],
        'url': 'http://127.0.0.1:5001/health',
        'essential': True,
    },
    'web_ui': {
        'name': '🌐 融策·审盾 Web界面',
        'port': 5005,
        'cmd': [sys.executable, '-X', 'utf8', os.path.join(SCRIPTS, 'web_ui.py')],
        'url': 'http://127.0.0.1:5005',
        'essential': False,
    },
    'review_web': {
        'name': '🛡️ 报告复核器',
        'port': 5006,
        'cmd': [sys.executable, '-X', 'utf8', os.path.join(SCRIPTS, 'review_web.py')],
        'url': 'http://127.0.0.1:5006',
        'essential': False,
    },
}

def is_port_open(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex(('127.0.0.1', port)) == 0
    except:
        return False

def wait_for_port(port, timeout=30):
    for i in range(timeout):
        if is_port_open(port):
            return True
        time.sleep(1)
    return False

def main():
    print('=' * 60)
    print('  融策·审盾 v2')
    print('  混合检索 + Reranker + 反馈闭环')
    print('=' * 60)
    print()
    
    # 检查索引
    idx_dir = os.path.join(WORKSPACE, '.rag_vector_index')
    meta_file = os.path.join(idx_dir, 'build_meta.json')
    if os.path.exists(meta_file):
        with open(meta_file, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        print(f'✅ 向量索引就绪: {meta["chunks"]} chunks | {meta["dimensions"]}维 | {meta["built_at"]}')
    else:
        print('❌ 索引未构建，请先运行: python scripts/rag_vector.py build')
        input('\n按Enter退出...')
        return
    print()
    
    # 启动服务
    processes = {}
    for key, svc in SERVICES.items():
        if is_port_open(svc['port']):
            print(f'✅ {svc["name"]} 已在运行 (端口 {svc["port"]})')
            continue
        print(f'🔄 启动 {svc["name"]} (端口 {svc["port"]})...')
        try:
            proc = subprocess.Popen(
                svc['cmd'],
                cwd=WORKSPACE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0,
            )
            processes[key] = proc
            if wait_for_port(svc['port'], timeout=15):
                print(f'   ✅ 就绪！')
            else:
                print(f'   ⚠️ 端口未响应')
        except Exception as e:
            print(f'   ❌ 启动失败: {e}')
    print()
    
    # 状态
    print('─' * 60)
    for key, svc in SERVICES.items():
        status = '✅' if is_port_open(svc['port']) else '❌'
        print(f'  {svc["name"]}: {status} http://127.0.0.1:{svc["port"]}')
    print()
    
    # 打开浏览器
    web_url = 'http://127.0.0.1:5005' if is_port_open(5005) else 'http://127.0.0.1:5001'
    print(f'📌 访问: {web_url}')
    choice = input('\n浏览器打开？(Y/n): ').strip().lower()
    if choice != 'n':
        webbrowser.open(web_url)
    
    print('\n服务在后台运行。关闭窗口不会停止。')
    input('按Enter关闭...')

if __name__ == '__main__':
    main()