# -*- coding: utf-8 -*-
"""
单本补跑 OCR — 能源审计方法（一)(二）.pdf
========================================
背景: 该书 488页/163MB, 2026-08-04 PaddleOCR 三次超时失败,
      且失败被误标记为 done（nightly_ocr.py bug）导致不再重试。
方案: 走 Qwen API 视觉 OCR（process_one_pdf_qwen），跳过 Paddle。
用法: paddleocr 环境不需要; 用默认 python 运行:
      python scripts/run_missing_book.py
"""
import sys, os, json, time

sys.stdout.reconfigure(encoding='utf-8')
SCRIPT_DIR = r'C:\Users\scrccpa\.openclaw\workspace\scripts'
sys.path.insert(0, SCRIPT_DIR)

PDF = r'E:\2026\审计方法&政策文件\审计相关书籍\能源审计\能源审计方法（一)(二）.pdf'
NAME = '能源审计方法（一)(二）.pdf'
OUTPUT_DIR = r'E:\2026\审计方法&政策文件\_ocr_output'
STATE = os.path.join(SCRIPT_DIR, 'hybrid_ocr_state.json')
LOG_FILE = os.path.join(SCRIPT_DIR, '..', 'logs', 'missing_book.log')

def log(msg):
    line = f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] {msg}'
    print(line, flush=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + '\n')

def main():
    # 冒烟测试：只测前2页，确认API可用
    if '--smoke' in sys.argv:
        import fitz, base64, requests, json as j
        cfg = j.load(open(os.path.join(os.path.expanduser('~'), '.openclaw', 'openclaw.json'), encoding='utf-8'))
        p = cfg['models']['providers']['custom-cbwyy-qwen']
        url = p['baseUrl'].rstrip('/') + '/chat/completions'
        doc = fitz.open(PDF)
        ok = 0
        for pg in range(min(2, doc.page_count)):
            pix = doc[pg].get_pixmap(dpi=120)
            b64 = base64.b64encode(pix.tobytes('png')).decode('utf-8')
            r = requests.post(url,
                headers={'Authorization': f'Bearer {p["apiKey"]}', 'Content-Type': 'application/json'},
                json={'model': 'qwen3.7-plus', 'messages': [{'role': 'user', 'content': [
                    {'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{b64}'}},
                    {'type': 'text', 'text': '请识别本页所有中文文字，保持原文段落。只输出识别内容。'}]}],
                    'max_tokens': 2048, 'temperature': 0.1},
                timeout=120)
            if r.status_code == 200:
                content = r.json()['choices'][0]['message']['content']
                ok += 1
                log(f'冒烟测试 第{pg+1}页 OK: {len(content)}字 | 样本: {content[:60]!r}')
            else:
                log(f'冒烟测试 第{pg+1}页失败 HTTP {r.status_code}: {r.text[:200]}')
                sys.exit(1)
        log(f'冒烟测试完成 {ok}/2 页通过, API 可用')
        sys.exit(0 if ok == 2 else 1)

    # ---- 正式补跑 ----
    from nightly_ocr import process_one_pdf_qwen

    # 1. 从 state 移除该书 done 标记（若在）
    state = {}
    if os.path.exists(STATE):
        with open(STATE, encoding='utf-8') as f:
            state = json.load(f)
    done = [d for d in state.get('done', []) if d != PDF]
    if len(done) != len(state.get('done', [])):
        log(f'从 done 移除该书 (done {len(state.get("done",[]))} -> {len(done)})')
    state['done'] = done
    with open(STATE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    # 2. Qwen 补跑
    log(f'开始 Qwen 补跑: {NAME}')
    success, result = process_one_pdf_qwen(PDF, NAME, OUTPUT_DIR)

    # 3. 更新 state
    if success:
        state['done'] = list(done) + [PDF]
        state['results'] = state.get('results', []) + [{
            'name': result['name'], 'pages': result['pages'], 'chars': result.get('chars', 0),
            'confidence': result.get('confidence', 0), 'qwen_pages': result.get('qwen_pages', 0),
            'qwen_tokens': result.get('qwen_tokens', 0), 'qwen_cost': result.get('qwen_cost', 0),
            'time': result['time'], 'output': result['output'], 'retries': result.get('retries', 0)}]
        state['total_qwen_tokens'] = state.get('total_qwen_tokens', 0) + result.get('qwen_tokens', 0)
        state['total_qwen_cost'] = state.get('total_qwen_cost', 0) + result.get('qwen_cost', 0)
        with open(STATE, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        log(f'✅ 补跑成功! 输出: {result["output"]} | {result["pages"]}页 {result.get("chars",0)}字 | 费用¥{result.get("qwen_cost",0):.4f} | {result["time"]}s')
        # 4. 重新生成 manifest
        import subprocess
        subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, 'regenerate_ocr_manifest.py')], timeout=300)
        log('manifest 已重新生成')
    else:
        log(f'❌ 补跑失败: {result}')
        sys.exit(1)

if __name__ == '__main__':
    main()
