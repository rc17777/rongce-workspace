# encoding: utf-8
"""
夜间OCR批量调度脚本 v2.0
=======================
用法: python -X utf8 scripts/nightly_ocr.py [--dry-run]
由 cron 每日 00:00 触发，按本数限制（每夜最多N本），失败自动重试。
"""
import os, sys, json, time, subprocess
import atexit

sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)  # 确保独立运行时能找到同级模块
PIPELINE = os.path.join(SCRIPT_DIR, 'hybrid_ocr_pipeline.py')
PADDLE_WORKER = os.path.join(SCRIPT_DIR, 'paddle_batch_worker.py')
STATE = os.path.join(SCRIPT_DIR, 'hybrid_ocr_state.json')
NIGHTLY_LOG = os.path.join(SCRIPT_DIR, '..', 'logs', 'nightly_ocr.log')

# 夜间配置
MAX_BOOKS_PER_NIGHT = 8          # 每晚上限本数
NO_QWEN = True                    # 夜间不调Qwen，¥0费用
MAX_RETRIES = 2                   # 单本失败最大重试次数
NIGHTLY_TIMEOUT = 21600           # 6小时硬超时（0点-6点）

# 互斥锁（防多实例并发）
PID_FILE = os.path.join(SCRIPT_DIR, 'nightly_ocr.pid')

def check_mutex():
    """检查是否已有实例在运行，有则退出"""
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                old_pid = f.read().strip()
            if old_pid:
                # 检查进程是否还在运行
                result = subprocess.run(
                    ['tasklist', '/fi', f'PID eq {old_pid}', '/fo', 'csv', '/nh'],
                    capture_output=True, text=True, timeout=10
                )
                if old_pid in result.stdout:
                    print(f'[互斥锁] 已有实例运行 (PID {old_pid})，退出')
                    sys.exit(0)
                else:
                    print(f'[互斥锁] 清理过期PID文件: {old_pid}')
        except Exception as e:
            print(f'[互斥锁] 检查失败: {e}，继续')
    
    # 写入当前PID
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))
    print(f'[互斥锁] PID {os.getpid()} 已注册')

def cleanup_pid():
    """退出时清理PID文件"""
    try:
        if os.path.exists(PID_FILE):
            with open(PID_FILE, 'r') as f:
                pid = f.read().strip()
            if pid == str(os.getpid()):
                os.unlink(PID_FILE)
                print(f'[互斥锁] PID文件已清理')
    except:
        pass

# 注册退出清理
atexit.register(cleanup_pid)

# 启动时检查互斥锁
check_mutex()

SOURCE_DIR = r'E:\2026\审计方法&政策文件\审计相关书籍'
OUTPUT_DIR = r'E:\2026\审计方法&政策文件\_ocr_output'

# 重试状态文件
RETRY_FILE = os.path.join(SCRIPT_DIR, 'nightly_retry.json')


def log(msg):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f'[{timestamp}] {msg}'
    print(line, flush=True)
    os.makedirs(os.path.dirname(NIGHTLY_LOG), exist_ok=True)
    with open(NIGHTLY_LOG, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def load_retry_state():
    if os.path.exists(RETRY_FILE):
        with open(RETRY_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_retry_state(rs):
    with open(RETRY_FILE, 'w', encoding='utf-8') as f:
        json.dump(rs, f, ensure_ascii=False, indent=2)


def find_next_pdf(source_dir, done_paths):
    """找下一个待处理的PDF（按文件大小升序，先小后大）"""
    pdfs = []
    for root, dirs, files in os.walk(source_dir):
        for f in sorted(files):
            if f.lower().endswith('.pdf') and not f.startswith('~$'):
                fp = os.path.join(root, f)
                if fp not in done_paths:
                    pdfs.append((fp, f, os.path.getsize(fp)))
    pdfs.sort(key=lambda x: x[2])  # 按大小升序
    return pdfs


def process_one_pdf(pdf_path, pdf_name, output_dir):
    """处理单个PDF（含重试逻辑），返回 (success, result)"""
    PADDLE_PYTHON = r'C:\Users\scrccpa\miniconda3\envs\paddleocr\python.exe'
    
    for attempt in range(1, MAX_RETRIES + 2):  # 1次初始 + N次重试
        if attempt > 1:
            log(f'  🔄 重试 {attempt-1}/{MAX_RETRIES}: {pdf_name}')
            time.sleep(5)  # 重试前等5秒
        
        try:
            # 步骤1: PaddleOCR批量worker
            import tempfile
            
            # 写配置
            tmp_cfg = tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w', encoding='utf-8')
            tmp_result = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
            config = {'pdf_path': pdf_path, 'output_json': tmp_result.name}
            json.dump(config, tmp_cfg, ensure_ascii=False)
            tmp_cfg.close()
            tmp_result.close()
            
            log(f'  📄 [{attempt}] PaddleOCR: {pdf_name}')
            t0 = time.time()
            
            proc = subprocess.run(
                [PADDLE_PYTHON, PADDLE_WORKER, tmp_cfg.name],
                capture_output=True, text=True, timeout=3600,
                encoding='utf-8', errors='replace'
            )
            
            # 清理配置文件
            try:
                os.unlink(tmp_cfg.name)
            except:
                pass
            
            # 检查结果
            if proc.returncode != 0:
                stderr_tail = (proc.stderr or '')[-300:]
                log(f'  ⚠️ PaddleWorker 退出码 {proc.returncode}: {stderr_tail}')
                try:
                    os.unlink(tmp_result.name)
                except:
                    pass
                
                if attempt <= MAX_RETRIES:
                    continue
                else:
                    log(f'  ❌ 已达最大重试次数，跳过: {pdf_name}')
                    return False, {'error': f'PaddleWorker failed after {MAX_RETRIES+1} attempts'}
            
            # 读取OCR结果
            if not os.path.exists(tmp_result.name) or os.path.getsize(tmp_result.name) == 0:
                log(f'  ⚠️ PaddleWorker 无输出文件')
                try:
                    os.unlink(tmp_result.name)
                except:
                    pass
                
                if attempt <= MAX_RETRIES:
                    continue
                else:
                    return False, {'error': 'Empty result'}
            
            with open(tmp_result.name, encoding='utf-8') as f:
                data = json.load(f)
            try:
                os.unlink(tmp_result.name)
            except:
                pass
            
            total_pages = data['total_pages']
            total_chars = data['total_chars']
            avg_conf = data['avg_confidence']
            elapsed = time.time() - t0
            
            log(f'  ✅ {total_pages}页 {total_chars}字 置信度{avg_conf:.2%} {elapsed:.0f}s')
            
            # 步骤2: 生成Markdown（不需要再调OCR，直接用PaddleWorker结果）
            from hybrid_ocr_pipeline import get_business_line, sanitize_filename, build_markdown
            
            biz_line = get_business_line(pdf_path, pdf_name)
            
            # 构建page_results
            page_results = []
            for r in data['results']:
                text = r['text']
                conf = r['confidence']
                page_results.append((r['page'], text, 'paddle', conf))
            
            meta = {
                'total_pages': total_pages,
                'paddle_pages': total_pages,
                'qwen_pages': 0,
                'qwen_tokens': 0,
                'qwen_cost_est': 0.0,
                'avg_confidence': avg_conf,
                'elapsed': round(elapsed, 1),
            }
            
            md_content = build_markdown(pdf_name, biz_line, pdf_path, page_results, meta)
            
            safe_name = sanitize_filename(pdf_name)
            out_dir = os.path.join(output_dir, biz_line)
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, f'{safe_name}.md')
            
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            log(f'  📁 {out_path} ({os.path.getsize(out_path)/1024:.0f}KB)')
            
            return True, {
                'name': pdf_name,
                'pages': total_pages,
                'chars': total_chars,
                'confidence': avg_conf,
                'biz_line': biz_line,
                'qwen_pages': 0,
                'qwen_tokens': 0,
                'qwen_cost': 0.0,
                'time': round(elapsed, 1),
                'output': out_path,
                'retries': attempt - 1,
            }
            
        except subprocess.TimeoutExpired:
            log(f'  ⚠️ PaddleWorker 超时 (1小时)')
            if attempt <= MAX_RETRIES:
                continue
            else:
                return False, {'error': 'Timeout'}
        except Exception as e:
            log(f'  ⚠️ 异常: {e}')
            if attempt <= MAX_RETRIES:
                continue
            else:
                return False, {'error': str(e)}


def main():
    dry_run = '--dry-run' in sys.argv
    force = '--force' in sys.argv
    
    log('=' * 60)
    log('夜间OCR批量处理 v2.0 启动')
    log(f'每晚上限: {MAX_BOOKS_PER_NIGHT}本 | Qwen: {"关闭" if NO_QWEN else "开启"}')
    log(f'重试次数: {MAX_RETRIES} | 超时: {NIGHTLY_TIMEOUT//3600}小时')
    
    # 加载进度
    state = {}
    if os.path.exists(STATE):
        with open(STATE, encoding='utf-8') as f:
            state = json.load(f)
    done_paths = set(state.get('done', []))
    total_cost = state.get('total_qwen_cost', 0)
    total_results = state.get('results', [])
    
    log(f'历史进度: 已完成 {len(done_paths)} 本, 累计费用 ¥{total_cost:.4f}')
    
    if dry_run:
        log('DRY RUN — 扫描待处理列表:')
        pending = find_next_pdf(SOURCE_DIR, done_paths)
        for i, (fp, name, size) in enumerate(pending[:10]):
            log(f'  [{i+1}] {name} ({size/1024/1024:.1f}MB)')
        log(f'  ...共 {len(pending)} 本待处理')
        return
    
    t_global = time.time()
    books_done = 0
    pages_done = 0
    failed_books = []
    
    # 逐本处理
    while books_done < MAX_BOOKS_PER_NIGHT:
        # 检查总超时
        if time.time() - t_global > NIGHTLY_TIMEOUT:
            log(f'⏰ 已达夜间窗口上限 ({NIGHTLY_TIMEOUT//3600}小时)，停止')
            break
        
        # 找下一本
        pending = find_next_pdf(SOURCE_DIR, done_paths)
        if not pending:
            log('🎉 全部PDF已处理完毕！')
            break
        
        pdf_path, pdf_name, pdf_size = pending[0]
        log(f'\n--- 第 {books_done+1}/{MAX_BOOKS_PER_NIGHT} 本: {pdf_name} ({pdf_size/1024/1024:.1f}MB) ---')
        
        success, result = process_one_pdf(pdf_path, pdf_name, OUTPUT_DIR)
        
        if success:
            done_paths.add(pdf_path)
            books_done += 1
            pages_done += result['pages']
            
            total_results.append({
                'name': result['name'],
                'pages': result['pages'],
                'chars': result.get('chars', 0),
                'confidence': result.get('confidence', 0),
                'qwen_pages': 0,
                'qwen_tokens': 0,
                'qwen_cost': 0,
                'time': result['time'],
                'output': result['output'],
                'retries': result.get('retries', 0),
            })
            
            state['done'] = list(done_paths)
            state['results'] = total_results
            state['total_qwen_tokens'] = state.get('total_qwen_tokens', 0)
            state['total_qwen_cost'] = state.get('total_qwen_cost', 0)
            
            # 每本保存一次进度（防崩溃丢进度）
            with open(STATE, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            
            log(f'📊 今夜: {books_done}本 {pages_done}页 | 累计: {len(done_paths)}本')
        else:
            failed_books.append((pdf_name, result.get('error', 'unknown')))
            log(f'❌ 失败: {pdf_name} - {result.get("error")}')
            # 失败也跳过，不阻塞后续
            done_paths.add(pdf_path)
            state['done'] = list(done_paths)
            with open(STATE, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
    
    elapsed = time.time() - t_global
    log(f'\n{"=" * 60}')
    log(f'今夜总结: {books_done}本 {pages_done}页 | 耗时 {elapsed/60:.0f}分钟')
    log(f'累计完成: {len(done_paths)}本')
    
    if failed_books:
        log(f'失败: {len(failed_books)}本')
        for name, err in failed_books:
            log(f'  - {name}: {err[:100]}')
    
    # 估算剩余
    all_pdfs = find_next_pdf(SOURCE_DIR, set())
    remaining = len(all_pdfs) - len(done_paths)
    if remaining > 0:
        nights_left = (remaining + MAX_BOOKS_PER_NIGHT - 1) // MAX_BOOKS_PER_NIGHT
        log(f'剩余: {remaining}本, 预计还需 {nights_left} 晚')
    
    log('=' * 60)


if __name__ == '__main__':
    main()
