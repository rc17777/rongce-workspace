import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')
base = r'E:\2026\审计方法&政策文件\_ocr_output'
m = os.path.join(base, '_manifest.json')

if os.path.exists(m):
    d = json.load(open(m, 'r', encoding='utf-8'))
    s = d['stats']
    print('状态: 完成')
    print(f"PDF: {s['total_pdfs']} | 页: {s['total_pages']} | 字: {s['total_chars']} | 失败: {s['failed']}")
    print(f"时间: {d['timestamp']}")
    for lbl, rs in d['results'].items():
        ok = sum(1 for r in rs if 'error' not in r)
        fail = sum(1 for r in rs if 'error' in r)
        print(f"  {lbl}: {ok}成功 {fail}失败")
        for r in rs:
            if 'error' in r:
                print(f"    ❌ {r['filename']}: {r['error']}")
else:
    # check dir
    if os.path.exists(base):
        cnt = 0
        for root, dirs, files in os.walk(base):
            cnt += sum(1 for f in files if f.endswith('.md'))
        print(f"清单不存在，但找到 {cnt} 个md文件")
        for root, dirs, files in os.walk(base):
            for f in sorted(files)[:10]:
                if f.endswith('.md'):
                    fp = os.path.join(root, f)
                    sz = os.path.getsize(fp)
                    print(f"  {os.path.basename(fp)} ({sz}B)")
    else:
        print('输出目录不存在 - OCR未执行')
