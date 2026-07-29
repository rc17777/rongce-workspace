# -*- coding: utf-8 -*-
r"""
混合OCR管线 v1.0 — PaddleOCR打底 + Qwen3.7补强
================================================
策略: PaddleOCR本地免费跑 → 置信度评估 → 低质量页送Qwen3.7重识别
输出: 结构化Markdown (YAML frontmatter + 章节保留) → Obsidian/LLM-Wiki/RAG就绪

用法:
  python hybrid_ocr_pipeline.py scan --dir "D:\books" --output "D:\ocr_output"
  python hybrid_ocr_pipeline.py test --dir "D:\books" --limit 1
  python hybrid_ocr_pipeline.py status
  python hybrid_ocr_pipeline.py estimate --dir "D:\books"
"""
import sys, os, json, time, re, base64, io, subprocess, tempfile, hashlib
import requests
import fitz  # PyMuPDF
sys.stdout.reconfigure(encoding='utf-8')

# ============================================================
# 配置
# ============================================================
PADDLE_PYTHON = r"C:\Users\scrccpa\miniconda3\envs\paddleocr\python.exe"
QWEN_PROVIDER = "custom-cbwyy-qwen"  # dashscope直连
QWEN_MODEL = "qwen3.7-plus"

# Qwen3.7 API配置（从openclaw.json读取）
def load_qwen_config():
    cfg_path = os.path.join(os.path.expanduser('~'), '.openclaw', 'openclaw.json')
    with open(cfg_path, encoding='utf-8') as f:
        cfg = json.load(f)
    p = cfg['models']['providers'][QWEN_PROVIDER]
    return p['apiKey'], p['baseUrl']

QWEN_API_KEY, QWEN_BASE_URL = load_qwen_config()

# 默认路径
DEFAULT_INPUT = r"D:\books_scanned"
DEFAULT_OUTPUT = r"D:\ocr_output"
STATE_FILE = os.path.join(os.path.dirname(__file__), 'hybrid_ocr_state.json')
COST_LOG = os.path.join(os.path.dirname(__file__), '..', 'logs', 'hybrid_ocr_cost.jsonl')

# PaddleOCR置信度阈值
CONFIDENCE_HIGH = 0.90    # >= 此值直接采用，不进Qwen
CONFIDENCE_LOW = 0.70     # <= 此值肯定送Qwen
# 0.70-0.90 区间: 如果连续3页低置信度 → 送Qwen（说明整段质量差）

# Qwen DPI 配置（不需要300dpi，200足够OCR）
QWEN_DPI = 200
# Paddle OCR DPI
PADDLE_DPI = 200

# Qwen API 限流
QWEN_RATE_LIMIT = 3  # 每秒最多N个请求
QWEN_MAX_RETRIES = 3

# ============================================================
# 工具函数
# ============================================================

def sanitize_filename(name):
    """清理文件名"""
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    return name.strip()[:120]

def get_business_line(path, filename):
    """根据目录名/文件名推断业务线"""
    keywords = {
        '经责': ['经责', '经济责任', '任期', '离任', '自然资源'],
        '收支': ['收支', '财务收支'],
        '预算': ['预算执行', '预算', '决算'],
        '专项': ['专项', '专项资金', '社保', '营养餐'],
        '招投标': ['招投标', '招标', '投标', '采购', '串标', '围标'],
        '国企': ['国企', '国有', '国资'],
        '成本': ['成本', '效益', '成本效益'],
        '能源': ['能源', '节能', '碳中和', '碳达峰'],
        '工程': ['工程', '竣工', '结算', '决算', '造价'],
        '绩效': ['绩效', '绩效评价', '绩效管理'],
        '补贴': ['补贴', '补助', '政府补贴'],
        '往来款': ['往来', '清理', '资金'],
    }
    full = (path + filename).lower()
    for biz, kws in keywords.items():
        for kw in kws:
            if kw in full:
                return biz
    return '通用'

def pdf_page_to_png_bytes(doc, page_num, dpi=200):
    """将PDF单页渲染为PNG字节"""
    page = doc[page_num]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)
    return pix.tobytes('png')

def pdf_page_to_base64(doc, page_num, dpi=200):
    """将PDF单页渲染为base64 data URL"""
    img_bytes = pdf_page_to_png_bytes(doc, page_num, dpi)
    b64 = base64.b64encode(img_bytes).decode('utf-8')
    return f'data:image/png;base64,{b64}'

# ============================================================
# PaddleOCR 子进程调用
# ============================================================

def paddle_batch_ocr(pdf_path):
    """
    调用 paddle_batch_worker.py 一次性OCR所有页。
    PaddleOCR只加载一次模型，然后批量处理所有页。
    通过JSON配置文件传递路径，绕过命令行中文编码问题。
    返回: [(text, confidence, chars), ...]
    """
    worker_script = os.path.join(os.path.dirname(__file__), 'paddle_batch_worker.py')

    # 写配置JSON（绕过命令行编码问题）
    tmp_cfg = tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w', encoding='utf-8')
    tmp_result = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
    config = {
        'pdf_path': pdf_path,
        'output_json': tmp_result.name,
    }
    json.dump(config, tmp_cfg, ensure_ascii=False)
    tmp_cfg.close()
    tmp_result.close()

    try:
        proc = subprocess.run(
            [PADDLE_PYTHON, worker_script, tmp_cfg.name],
            capture_output=True, text=True, timeout=7200,
            encoding='utf-8', errors='replace'
        )

        # 打印worker输出
        for line in (proc.stdout or '').split('\n'):
            line = line.strip()
            if line and '[PaddleWorker]' in line:
                print(f'   {line}', flush=True)

        # 读取结果JSON
        if os.path.exists(tmp_result.name) and os.path.getsize(tmp_result.name) > 0:
            with open(tmp_result.name, encoding='utf-8') as f:
                data = json.load(f)
            results = []
            for r in data.get('results', []):
                results.append((r['text'], r['confidence'], r['chars']))
            return results
        else:
            print(f'   [ERROR] PaddleWorker 无输出', flush=True)
            if proc.stderr:
                print(f'   stderr: {proc.stderr[:500]}', flush=True)
            return []
    finally:
        try:
            os.unlink(tmp_cfg.name)
        except:
            pass
        try:
            os.unlink(tmp_result.name)
        except:
            pass


# ============================================================
# Qwen3.7 OCR 调用
# ============================================================

def qwen_ocr_page(doc, page_num):
    """
    调用Qwen3.7-plus识别单页。
    返回: (text: str, tokens_used: int)
    """
    data_url = pdf_page_to_base64(doc, page_num, QWEN_DPI)

    payload = {
        'model': QWEN_MODEL,
        'messages': [{
            'role': 'user',
            'content': [
                {'type': 'image_url', 'image_url': {'url': data_url}},
                {'type': 'text', 'text': (
                    '请完整识别这张扫描件的所有中文文字，包括页眉页脚。'
                    '保持原文的段落结构和换行。'
                    '如果图片中有表格，请用Markdown表格格式输出。'
                    '如果文字模糊不清，标注为[模糊]。'
                    '只输出识别到的文字内容，不要加任何解释说明。'
                )}
            ]
        }],
        'max_tokens': 4096,
        'temperature': 0.1
    }

    for attempt in range(QWEN_MAX_RETRIES):
        try:
            r = requests.post(
                QWEN_BASE_URL.rstrip('/') + '/chat/completions',
                headers={
                    'Authorization': f'Bearer {QWEN_API_KEY}',
                    'Content-Type': 'application/json'
                },
                json=payload,
                timeout=90
            )
            if r.status_code == 200:
                data = r.json()
                text = data['choices'][0]['message']['content']
                tokens = data.get('usage', {}).get('total_tokens', 0)
                return text, tokens
            elif r.status_code == 429:
                wait = min(2 ** attempt, 30)
                time.sleep(wait)
            else:
                if attempt < QWEN_MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                else:
                    return f'[QWEN_ERROR HTTP {r.status_code}: {r.text[:200]}]', 0
        except Exception as e:
            if attempt < QWEN_MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
            else:
                return f'[QWEN_ERROR: {e}]', 0

    return '[QWEN_ERROR: max retries]', 0


def qwen_ocr_selected_pages(doc, page_indices):
    """
    对指定页码列表调用Qwen3.7 OCR。
    返回: {page_num: (text, tokens), ...}
    """
    results = {}
    total = len(page_indices)
    for idx, page_num in enumerate(page_indices):
        # 限流
        if idx > 0:
            time.sleep(1.0 / QWEN_RATE_LIMIT)

        text, tokens = qwen_ocr_page(doc, page_num)
        results[page_num] = (text, tokens)

        if (idx + 1) % 5 == 0:
            print(f'    Qwen进度: {idx+1}/{total}', flush=True)

    return results


# ============================================================
# 置信度路由决策
# ============================================================

def decide_qwen_pages(paddle_results):
    """
    根据PaddleOCR结果决定哪些页需要送Qwen。
    
    规则:
    1. confidence <= CONFIDENCE_LOW → 送Qwen
    2. confidence 在 LOW-HIGH 之间 → 如果上下文(±2页)也有低置信度 → 送Qwen
    3. confidence >= CONFIDENCE_HIGH → 直接用Paddle
    4. 空文本页(可能纯图) → 送Qwen
    """
    n = len(paddle_results)
    needs_qwen = set()

    for i, (text, conf, chars) in enumerate(paddle_results):
        # 规则1: 绝对低置信度
        if conf <= CONFIDENCE_LOW:
            needs_qwen.add(i)
            continue

        # 规则4: 空文本（可能是图表/纯图）
        if chars < 5 and conf < CONFIDENCE_HIGH:
            needs_qwen.add(i)
            continue

        # 规则2: 中等置信度 + 上下文也低 → 整段重扫
        if CONFIDENCE_LOW < conf < CONFIDENCE_HIGH:
            # 检查前后2页
            start = max(0, i - 2)
            end = min(n, i + 3)
            neighbors = paddle_results[start:end]
            low_neighbors = sum(1 for _, nc, _ in neighbors if nc <= CONFIDENCE_LOW)
            if low_neighbors >= 1:
                needs_qwen.add(i)

    return needs_qwen


# ============================================================
# Markdown 生成
# ============================================================

def build_markdown(pdf_name, biz_line, pdf_path, page_results, meta):
    """
    生成最终Markdown。
    page_results: [(page_num, text, engine, confidence), ...]
    """
    lines = []
    # YAML frontmatter
    lines.append('---')
    lines.append(f'title: "{pdf_name}"')
    lines.append(f'source: "{os.path.basename(pdf_path)}"')
    lines.append(f'source_type: "书籍扫描件"')
    lines.append(f'business_line: "{biz_line}"')
    lines.append(f'total_pages: {meta["total_pages"]}')
    lines.append(f'ocr_date: "{time.strftime("%Y-%m-%d %H:%M")}"')
    lines.append(f'ocr_pages_paddle: {meta["paddle_pages"]}')
    lines.append(f'ocr_pages_qwen: {meta["qwen_pages"]}')
    lines.append(f'ocr_qwen_tokens: {meta["qwen_tokens"]}')
    lines.append(f'ocr_qwen_cost_est: {meta["qwen_cost_est"]}')
    lines.append(f'ocr_avg_confidence: {meta["avg_confidence"]}')
    lines.append(f'ocr_duration_s: {meta["elapsed"]}')
    lines.append('tags:')
    lines.append(f'  - {biz_line}')
    lines.append(f'  - 书籍OCR')
    lines.append('---')
    lines.append('')
    lines.append(f'# {pdf_name}')
    lines.append('')

    # 各页内容
    for page_num, text, engine, confidence in page_results:
        engine_tag = {
            'paddle': f'PaddleOCR (置信度: {confidence:.2%})',
            'qwen': 'Qwen3.7-plus',
            'hybrid': f'Paddle+Qwen (置信度: {confidence:.2%})',
        }.get(engine, engine)

        lines.append(f'## 第{page_num + 1}页')
        lines.append(f'')
        lines.append(f'> 引擎: {engine_tag}')
        lines.append('')
        lines.append(text)
        lines.append('')

    return '\n'.join(lines)


# ============================================================
# 管线主流程
# ============================================================

def process_pdf(pdf_path, output_base, no_qwen=False):
    """
    处理单个PDF的完整混合OCR管线。
    no_qwen=True 时跳过Qwen3.7阶段，只用PaddleOCR。
    返回: result dict
    """
    t_start = time.time()
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    biz_line = get_business_line(pdf_path, pdf_name)

    print(f'\n{"=" * 70}')
    print(f'📄 {pdf_name}')
    print(f'   业务线: {biz_line} | 大小: {os.path.getsize(pdf_path)/1024/1024:.1f}MB')
    print(f'{"=" * 70}')

    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    print(f'   总页数: {total_pages}')

    # === 阶段1: PaddleOCR全部页 ===
    print(f'\n   [1/4] PaddleOCR 批量识别 {total_pages}页...')
    paddle_results = paddle_batch_ocr(pdf_path)

    if not paddle_results:
        print(f'   ❌ PaddleOCR失败，终止')
        doc.close()
        return {'success': False, 'error': 'PaddleOCR returned no results'}

    paddle_chars = sum(chars for _, _, chars in paddle_results)
    avg_conf = sum(conf for _, conf, _ in paddle_results) / total_pages if total_pages else 0
    print(f'   ✅ PaddleOCR完成: {paddle_chars}字, 平均置信度 {avg_conf:.2%}')

    # === 阶段2: 路由决策 ===
    print(f'\n   [2/4] 置信度路由分析...')
    qwen_pages = decide_qwen_pages(paddle_results)

    # 统计各档
    high = sum(1 for _, c, _ in paddle_results if c >= CONFIDENCE_HIGH)
    mid = sum(1 for _, c, _ in paddle_results if CONFIDENCE_LOW < c < CONFIDENCE_HIGH)
    low = sum(1 for _, c, _ in paddle_results if c <= CONFIDENCE_LOW)
    print(f'   高质量页(≥{CONFIDENCE_HIGH:.0%}): {high} | 中等: {mid} | 低质量(≤{CONFIDENCE_LOW:.0%}): {low}')
    print(f'   需Qwen重识别: {len(qwen_pages)}页 ({len(qwen_pages)/total_pages*100:.1f}%)')

    # === 阶段3: Qwen3.7补强（如果有） ===
    qwen_results = {}
    total_qwen_tokens = 0
    if qwen_pages and not no_qwen:
        print(f'\n   [3/4] Qwen3.7 补强识别 {len(qwen_pages)}页...')
        try:
            qwen_results = qwen_ocr_selected_pages(doc, sorted(qwen_pages))
            total_qwen_tokens = sum(t for _, t in qwen_results.values())
            print(f'   ✅ Qwen完成: {total_qwen_tokens} tokens')
            qwen_cost_est = round(total_qwen_tokens * 0.000002, 4)
            print(f'   💰 预估费用: ¥{qwen_cost_est:.4f}')
        except Exception as e:
            print(f'   ⚠️ Qwen API失败: {e}，降级为PaddleOCR结果')
            qwen_results = {}
            total_qwen_tokens = 0
            qwen_cost_est = 0.0
    elif qwen_pages and no_qwen:
        print(f'\n   [3/4] ⏭ 跳过Qwen3.7 (--no-qwen模式)')
        print(f'   ⚠️ {len(qwen_pages)}页低质量，将保留PaddleOCR原始结果')
        qwen_cost_est = 0.0
    else:
        print(f'\n   [3/4] 跳过Qwen3.7 (所有页PaddleOCR质量达标)')
        qwen_cost_est = 0.0

    # === 阶段4: 合成最终输出 ===
    print(f'\n   [4/4] 合成Markdown...')
    page_results = []
    for i in range(total_pages):
        text, conf, chars = paddle_results[i]
        if i in qwen_results:
            qwen_text, _ = qwen_results[i]
            # 优先用Qwen结果
            page_results.append((i, qwen_text, 'qwen', conf))
        else:
            page_results.append((i, text, 'paddle', conf))

    # 计算最终统计
    meta = {
        'total_pages': total_pages,
        'paddle_pages': total_pages - len(qwen_pages),
        'qwen_pages': len(qwen_pages),
        'qwen_tokens': total_qwen_tokens,
        'qwen_cost_est': qwen_cost_est,
        'avg_confidence': avg_conf,
        'elapsed': round(time.time() - t_start, 1),
    }

    md_content = build_markdown(pdf_name, biz_line, pdf_path, page_results, meta)

    # 写入文件
    safe_name = sanitize_filename(pdf_name)
    out_dir = os.path.join(output_base, biz_line)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f'{safe_name}.md')

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

    doc.close()

    out_size = os.path.getsize(out_path)
    result = {
        'pdf': pdf_path,
        'name': pdf_name,
        'biz_line': biz_line,
        'pages': total_pages,
        'qwen_pages': len(qwen_pages),
        'qwen_tokens': total_qwen_tokens,
        'qwen_cost': qwen_cost_est,
        'chars': len(md_content),
        'time': meta['elapsed'],
        'output': out_path,
        'success': True,
    }

    print(f'   ✅ 完成: {meta["elapsed"]:.0f}s | {len(md_content)}字 | {out_size/1024:.0f}KB')
    print(f'   📁 {out_path}')
    return result


# ============================================================
# 状态管理（支持断点续传）
# ============================================================

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {'done': [], 'results': [], 'total_qwen_tokens': 0, 'total_qwen_cost': 0}

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def log_cost(pdf_name, qwen_pages, qwen_tokens, cost):
    """记录Qwen调用费用"""
    log_dir = os.path.dirname(COST_LOG)
    os.makedirs(log_dir, exist_ok=True)
    with open(COST_LOG, 'a', encoding='utf-8') as f:
        entry = {
            'time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'pdf': pdf_name,
            'qwen_pages': qwen_pages,
            'qwen_tokens': qwen_tokens,
            'cost_est': cost,
        }
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


# ============================================================
# 扫描与估算
# ============================================================

def scan_pdfs(input_dir):
    """扫描目录下所有PDF"""
    pdfs = []
    for root, dirs, files in os.walk(input_dir):
        for f in sorted(files):
            if f.lower().endswith('.pdf') and not f.startswith('~$'):
                fp = os.path.join(root, f)
                biz = get_business_line(fp, f)
                size_mb = round(os.path.getsize(fp) / 1024 / 1024, 1)
                pdfs.append({
                    'path': fp,
                    'name': f,
                    'biz_line': biz,
                    'size_mb': size_mb,
                })
    return pdfs

def estimate_cost(pdfs):
    """估算总费用（按15%页需要Qwen的保守估计）"""
    total_pages_est = sum(p['size_mb'] * 12 for p in pdfs)  # 约12页/MB
    qwen_pages_est = int(total_pages_est * 0.15)
    tokens_est = qwen_pages_est * 500  # 平均500 token/页
    cost_est = tokens_est * 0.000002   # 约¥0.000002/token
    return {
        'pdfs': len(pdfs),
        'total_size_mb': sum(p['size_mb'] for p in pdfs),
        'total_pages_est': int(total_pages_est),
        'qwen_pages_est': qwen_pages_est,
        'qwen_tokens_est': int(tokens_est),
        'cost_est': round(cost_est, 2),
    }


# ============================================================
# CLI
# ============================================================

def cmd_estimate(input_dir):
    """估算模式"""
    input_dir = input_dir or DEFAULT_INPUT
    if not os.path.exists(input_dir):
        print(f'❌ 目录不存在: {input_dir}')
        return

    pdfs = scan_pdfs(input_dir)
    est = estimate_cost(pdfs)

    print(f'\n{"=" * 60}')
    print(f'📊 费用估算 — {input_dir}')
    print(f'{"=" * 60}')
    print(f'  PDF数量:     {est["pdfs"]}')
    print(f'  总大小:       {est["total_size_mb"]:.0f} MB ({est["total_size_mb"]/1024:.1f} GB)')
    print(f'  估算总页数:   ~{est["total_pages_est"]}')
    print(f'  预计Qwen处理: ~{est["qwen_pages_est"]}页 (15%)')
    print(f'  预估Token:    ~{est["qwen_tokens_est"]:,}')
    print(f'  预估费用:     ¥{est["cost_est"]:.2f}')
    print(f'{"=" * 60}')

    # 按业务线分组
    print(f'\n📂 业务线分布:')
    from collections import Counter
    biz_counts = Counter(p['biz_line'] for p in pdfs)
    for biz, count in biz_counts.most_common():
        size = sum(p['size_mb'] for p in pdfs if p['biz_line'] == biz)
        print(f'  {biz:　<8s} {count:>3d}个PDF  {size:>6.0f}MB')


def cmd_scan(input_dir, output_dir, limit=None, no_qwen=False, max_pages=None):
    """批量OCR"""
    input_dir = input_dir or DEFAULT_INPUT
    output_dir = output_dir or DEFAULT_OUTPUT

    if not os.path.exists(input_dir):
        print(f'❌ 目录不存在: {input_dir}')
        return

    pdfs = scan_pdfs(input_dir)
    if limit:
        pdfs = pdfs[:limit]

    # 估费确认
    est = estimate_cost(pdfs)
    print(f'\n{"=" * 60}')
    print(f'📊 费用估算')
    print(f'{"=" * 60}')
    print(f'  PDF: {est["pdfs"]}个 | 总大小: {est["total_size_mb"]:.0f}MB')
    print(f'  预估页数: ~{est["total_pages_est"]} | Qwen: ~{est["qwen_pages_est"]}页')
    print(f'  💰 预估费用: ¥{est["cost_est"]:.2f}')
    print(f'  输出目录: {output_dir}')
    print(f'{"=" * 60}')

    # 加载进度
    state = load_state()
    done_paths = set(state.get('done', []))

    pending = [p for p in pdfs if p['path'] not in done_paths]
    if not pending:
        print('\n✅ 全部已完成！')
        show_summary(state)
        return

    print(f'\n已完成: {len(done_paths)} | 待处理: {len(pending)}')

    accumulated_pages = 0
    for i, pdf_info in enumerate(pending, 1):
        # 检查夜量限制
        if max_pages and accumulated_pages >= max_pages:
            print(f'\n⏸ 已达夜量上限 ({max_pages}页)，剩余 {len(pending) - i + 1} 个PDF待后续处理')
            save_state(state)
            break

        print(f'\n[{i}/{len(pending)}]', end='')

        try:
            result = process_pdf(pdf_info['path'], output_dir, no_qwen=no_qwen)
            if result['success']:
                done_paths.add(pdf_info['path'])
                state['done'] = list(done_paths)
                state.setdefault('results', []).append({
                    'name': result['name'],
                    'pages': result['pages'],
                    'qwen_pages': result['qwen_pages'],
                    'qwen_tokens': result['qwen_tokens'],
                    'qwen_cost': result['qwen_cost'],
                    'time': result['time'],
                    'output': result['output'],
                })
                state['total_qwen_tokens'] = state.get('total_qwen_tokens', 0) + result['qwen_tokens']
                state['total_qwen_cost'] = state.get('total_qwen_cost', 0) + result['qwen_cost']

                save_state(state)
                log_cost(result['name'], result['qwen_pages'],
                         result['qwen_tokens'], result['qwen_cost'])

                accumulated_pages += result['pages']
                remaining = len(pending) - i
                print(f'  📊 进度: {len(done_paths)}/{len(pdfs)}, 剩余 {remaining} | 本次已处理 {accumulated_pages}页')
                print(f'  💰 累计费用: ¥{state["total_qwen_cost"]:.4f}')
            else:
                print(f'  ❌ 失败: {pdf_info["name"]}')

        except KeyboardInterrupt:
            print(f'\n⏸ 用户中断。进度已保存。')
            save_state(state)
            show_summary(state)
            return
        except Exception as e:
            print(f'  ❌ 异常: {e}')
            import traceback
            traceback.print_exc()
            save_state(state)

    print(f'\n{"=" * 60}')
    print(f'🎉 全部完成！')
    show_summary(state)


def cmd_test(input_dir, output_dir):
    """测试模式：处理第一个PDF"""
    if not input_dir:
        input_dir = DEFAULT_INPUT
    if not os.path.exists(input_dir):
        print(f'❌ 目录不存在: {input_dir}')
        return

    pdfs = scan_pdfs(input_dir)
    if not pdfs:
        print(f'❌ 目录下无PDF: {input_dir}')
        return

    # 找最小的PDF跑测试
    pdfs.sort(key=lambda x: x['size_mb'])
    test_pdf = pdfs[0]

    output_dir = output_dir or os.path.join(DEFAULT_OUTPUT, '_test')
    print(f'\n🧪 测试模式 — 选择最小PDF验证管线')
    print(f'   文件: {test_pdf["name"]} ({test_pdf["size_mb"]}MB)')
    print(f'   业务线: {test_pdf["biz_line"]}')

    try:
        result = process_pdf(test_pdf['path'], output_dir)
        if result['success']:
            print(f'\n✅ 测试通过！')
            print(f'   输出: {result["output"]}')
            print(f'   页数: {result["pages"]} | Qwen页: {result["qwen_pages"]}')
            print(f'   耗时: {result["time"]}s | 费用: ¥{result["qwen_cost"]:.4f}')

            # 显示前500字预览
            with open(result['output'], encoding='utf-8') as f:
                preview = f.read()[:500]
            print(f'\n📖 预览 (前500字):')
            print('─' * 40)
            print(preview)
        else:
            print(f'\n❌ 测试失败')
    except KeyboardInterrupt:
        print('\n⏸ 中断')
    except Exception as e:
        print(f'\n❌ 异常: {e}')
        import traceback
        traceback.print_exc()


def show_summary(state):
    """显示处理汇总"""
    results = state.get('results', [])
    done = state.get('done', [])
    if not results:
        print('  无处理记录')
        return

    total_pages = sum(r['pages'] for r in results)
    total_qwen = sum(r['qwen_pages'] for r in results)
    total_tokens = sum(r['qwen_tokens'] for r in results)
    total_cost = sum(r['qwen_cost'] for r in results)

    print(f'\n📊 汇总:')
    print(f'  PDF: {len(done)}个 | 总页数: {total_pages}')
    print(f'  PaddleOCR: {total_pages - total_qwen}页 | Qwen3.7: {total_qwen}页')
    print(f'  Qwen令牌: {total_tokens:,} | 总费用: ¥{total_cost:.4f}')
    print(f'  Qwen占比: {total_qwen/total_pages*100:.1f}%' if total_pages else '')


def cmd_status():
    """查看进度"""
    state = load_state()
    results = state.get('results', [])
    done = state.get('done', [])

    print(f'\n{"=" * 50}')
    print(f'📊 混合OCR管线进度')
    print(f'{"=" * 50}')
    print(f'  已完成: {len(done)} 个PDF')
    print(f'  累计Qwen Token: {state.get("total_qwen_tokens", 0):,}')
    print(f'  累计费用: ¥{state.get("total_qwen_cost", 0):.4f}')
    print()

    if results:
        print(f'  最近完成:')
        for r in results[-10:]:
            q = r.get('qwen_pages', 0)
            print(f'    ✅ {r["name"][:50]:<50s} {r["pages"]:>3d}页 Qwen:{q:>3d}页 ¥{r.get("qwen_cost", 0):.5f}')

    # 检查费用日志
    if os.path.exists(COST_LOG):
        with open(COST_LOG, encoding='utf-8') as f:
            lines = f.readlines()
        today = time.strftime('%Y-%m-%d')
        today_lines = [l for l in lines if today in l]
        if today_lines:
            today_cost = sum(json.loads(l)['cost_est'] for l in today_lines)
            print(f'\n  💰 今日费用: ¥{today_cost:.4f}')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='混合OCR管线 — PaddleOCR打底 + Qwen3.7补强',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=r"""
示例:
  python hybrid_ocr_pipeline.py estimate --dir "D:\books"
  python hybrid_ocr_pipeline.py test --dir "D:\books"
  python hybrid_ocr_pipeline.py scan --dir "D:\books" --output "D:\ocr_output"
  python hybrid_ocr_pipeline.py status
来源:
  PaddleOCR 2.7.3 (conda paddleocr) + Qwen3.7-plus (dashscope)
        """
    )

    sub = parser.add_subparsers(dest='command', help='子命令')

    # scan
    p_scan = sub.add_parser('scan', help='批量OCR处理')
    p_scan.add_argument('--dir', help='PDF源目录')
    p_scan.add_argument('--output', help='输出目录')
    p_scan.add_argument('--limit', type=int, help='限制处理N个PDF')
    p_scan.add_argument('--no-qwen', action='store_true', help='跳过Qwen3.7阶段（¥0费用）')
    p_scan.add_argument('--max-pages', type=int, help='每批次最大处理页数（夜间模式）')

    # test
    p_test = sub.add_parser('test', help='单文件测试')
    p_test.add_argument('--dir', help='PDF源目录')
    p_test.add_argument('--output', help='输出目录')

    # estimate
    p_est = sub.add_parser('estimate', help='费用估算')
    p_est.add_argument('--dir', help='PDF源目录')

    # status
    sub.add_parser('status', help='查看进度')

    args = parser.parse_args()

    if args.command == 'scan':
        cmd_scan(args.dir, args.output, args.limit,
                 no_qwen=getattr(args, 'no_qwen', False),
                 max_pages=getattr(args, 'max_pages', None))
    elif args.command == 'test':
        cmd_test(args.dir, args.output)
    elif args.command == 'estimate':
        cmd_estimate(args.dir)
    elif args.command == 'status':
        cmd_status()
    else:
        parser.print_help()
