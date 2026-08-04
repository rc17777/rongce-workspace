# encoding: utf-8
"""等待第32本(公共机构能源审计实务)完成，确认状态落盘后停止 nightly_ocr 主进程"""
import os, sys, json, time, subprocess

sys.stdout.reconfigure(encoding='utf-8')

MD = r'E:\2026\审计方法&政策文件\_ocr_output\能源\公共机构能源审计实务.pdf.md'
STATE = r'C:\Users\scrccpa\.openclaw\workspace\scripts\hybrid_ocr_state.json'
MAIN_PID = 21008  # nightly_ocr 主进程 PID

def log(msg):
    print(f'[{time.strftime("%H:%M:%S")}] {msg}', flush=True)

def pid_alive(pid):
    try:
        r = subprocess.run(['tasklist', '/fi', f'PID eq {pid}', '/fo', 'csv', '/nh'],
                           capture_output=True, text=True, timeout=10)
        return str(pid) in r.stdout
    except Exception:
        return False

start = time.time()
log(f'守护启动: 等待 {MD}')
while time.time() - start < 5400:  # 最长90分钟
    if os.path.exists(MD):
        # md 已生成，等待 state 落盘（done 数 >= 32）
        for _ in range(30):  # 最多再等60秒
            try:
                state = json.load(open(STATE, encoding='utf-8'))
                if len(state.get('done', [])) >= 32:
                    log('✅ 第32本完成且状态已落盘 (done=32)')
                    break
            except Exception:
                pass
            time.sleep(2)
        # 停掉主进程
        if pid_alive(MAIN_PID):
            subprocess.run(['taskkill', '/PID', str(MAIN_PID), '/T', '/F'],
                           capture_output=True, text=True)
            log(f'🛑 nightly_ocr 主进程 {MAIN_PID} 已停止')
        else:
            log('主进程已不在（可能自行退出）')
        # 顺带清理可能残留的 paddle worker
        r = subprocess.run(['tasklist', '/fi', 'IMAGENAME eq python.exe', '/fo', 'csv', '/nh'],
                           capture_output=True, text=True)
        for line in r.stdout.splitlines():
            if 'python.exe' in line and '10732' not in line:
                parts = line.split('","')
                if len(parts) > 1:
                    pid = parts[1].strip('"')
                    try:
                        subprocess.run(['taskkill', '/PID', pid, '/F'], capture_output=True, text=True)
                        log(f'清理残留 python 进程: {pid}')
                    except Exception:
                        pass
        # 清理 pid 文件（如果主进程被杀没来得及清理）
        pidfile = r'C:\Users\scrccpa\.openclaw\workspace\scripts\nightly_ocr.pid'
        if os.path.exists(pidfile):
            try:
                os.unlink(pidfile)
                log('清理过期 PID 文件')
            except Exception:
                pass
        log('守护完成')
        sys.exit(0)
    time.sleep(30)

log('⚠️ 90分钟超时，第32本未完成，守护退出（不干预进程）')
