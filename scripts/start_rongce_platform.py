"""
融策审计中台 - 一键启动脚本
==============================
启动后自动开启所有服务，浏览器打开Web界面。
用法：python scripts/start_rongce_platform.py
"""

import sys, os, time, subprocess, socket, webbrowser, json

sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE = r'C:\Users\scrccpa\.openclaw\workspace'
SCRIPTS = os.path.join(WORKSPACE, 'scripts')

# ======== 服务配置 ========
SERVICES = {
    'rag_vector': {
        'name': '🔍 RAG向量搜索引擎',
        'port': 5001,
        'cmd': [sys.executable, '-X', 'utf8', os.path.join(SCRIPTS, 'rag_vector.py'), 'serve', '--port', '5001'],
        'url': 'http://127.0.0.1:5001/health',
        'essential': True,
    },
    'rag_web': {
        'name': '🌐 RAG Web界面',
        'port': 5000,
        'cmd': [sys.executable, '-X', 'utf8', os.path.join(SCRIPTS, 'rag_server.py')],
        'url': 'http://127.0.0.1:5000',
        'essential': False,
    },
}

# 智析v2.0独立管理，不在此启动（需手动配置）
ZHIXI_NOTE = """
🧠 智析v2.0 API (5002端口) 需单独启动：
   cd D:\\openclaw-workspace\\skills\\zhixi-v2-enhanced
   python zhixi_tools.py serve --port 5002
"""

def is_port_open(port):
    """检查端口是否已被占用"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            result = s.connect_ex(('127.0.0.1', port))
            return result == 0
    except:
        return False

def wait_for_port(port, timeout=30):
    """等待端口就绪"""
    for i in range(timeout):
        if is_port_open(port):
            return True
        time.sleep(1)
    return False

def main():
    print('=' * 60)
    print('  融策审计中台 v1.0')
    print('  RAG语义搜索引擎 + 知识库Web界面')
    print('=' * 60)
    print()
    
    # 1. 检查向量索引
    idx_dir = os.path.join(WORKSPACE, '.rag_vector_index')
    idx_file = os.path.join(idx_dir, 'embeddings.npy')
    meta_file = os.path.join(idx_dir, 'build_meta.json')
    
    if not os.path.exists(idx_file):
        print('⚠️  向量索引未构建！先运行：')
        print(f'   python scripts/rag_vector.py build')
        print()
        choice = input('是否现在构建？(y/n): ').strip().lower()
        if choice == 'y':
            print('\n开始构建索引（需要约33分钟）...\n')
            result = subprocess.run(
                [sys.executable, '-X', 'utf8', os.path.join(SCRIPTS, 'rag_vector.py'), 'build'],
                cwd=WORKSPACE
            )
            if result.returncode != 0:
                print('\n❌ 索引构建失败，请检查网络连接（需访问 huggingface.co 下载模型）')
                input('\n按Enter退出...')
                return
        else:
            print('已取消。请手动构建索引后再启动。')
            input('\n按Enter退出...')
            return
    
    # 显示索引信息
    if os.path.exists(meta_file):
        with open(meta_file, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        print(f'✅ 向量索引就绪: {meta["chunks"]} chunks | {meta["dimensions"]}维 | {meta["built_at"]}')
    else:
        print('✅ 向量索引就绪（无元数据）')
    print()
    
    # 2. 启动服务
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
            print(f'   PID: {proc.pid} | 等待端口 {svc["port"]}...')
            
            if wait_for_port(svc['port'], timeout=15):
                print(f'   ✅ 就绪！')
            else:
                print(f'   ⚠️ 端口未在15秒内响应（服务可能仍在启动中）')
        except Exception as e:
            print(f'   ❌ 启动失败: {e}')
    print()
    
    # 3. 状态汇总
    print('─' * 60)
    print('  服务状态')
    print('─' * 60)
    
    all_ok = True
    for key, svc in SERVICES.items():
        status = '✅ 运行中' if is_port_open(svc['port']) else '❌ 未启动'
        print(f'  {svc["name"]}: {status} (http://127.0.0.1:{svc["port"]})')
        if svc['essential'] and not is_port_open(svc['port']):
            all_ok = False
    
    print()
    print(ZHIXI_NOTE)
    
    # 4. 打开浏览器
    if is_port_open(5001):
        web_url = 'http://127.0.0.1:5001'
    elif is_port_open(5000):
        web_url = 'http://127.0.0.1:5000'
    else:
        web_url = None
    
    if web_url:
        print(f'\n📌 访问地址: {web_url}')
        choice = input('\n是否在浏览器中打开？(Y/n): ').strip().lower()
        if choice != 'n':
            webbrowser.open(web_url)
    else:
        print('\n⚠️  无可用Web界面')
    
    print('\n服务将在后台持续运行。关闭此窗口不会停止服务。')
    print('要停止服务，请在任务管理器中结束 python.exe 进程。')
    input('\n按Enter关闭此窗口...')

if __name__ == '__main__':
    main()
