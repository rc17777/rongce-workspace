# -*- coding: utf-8 -*-
"""
杂志资料处理流水线 v1.0
处理流程：扫描→提取文本→AI总结分类→写入知识库+Obsidian

用法：
  # 处理单个杂志
  python magazine_pipeline.py process --magdir "E:\2026\审计方法&政策文件\杂志资料\财政监督"
  
  # 查看进度
  python magazine_pipeline.py status
  
  # 列出所有未处理杂志
  python magazine_pipeline.py pending
"""
import sys, os, re, json, hashlib, time
sys.stdout.reconfigure(encoding='utf-8')

BASE = r"E:\2026\审计方法&政策文件\杂志资料"
OUTPUT_KNOWLEDGE = r"C:\Users\scrccpa\.openclaw\workspace\knowledge"
OUTPUT_OBSIDIAN = r"C:\Users\scrccpa\.openclaw\workspace\obsidian-vault"
STATE_FILE = os.path.join(os.path.dirname(__file__), "magazine_progress.json")

# ========== 业务场景分类体系 ==========
BIZ_SCENES = {
    "经济责任审计": ["经责", "经济责任", "领导干部", "离任审计", "任期审计"],
    "收支审计": ["收支", "财政收支", "财务收支"],
    "预算执行审计": ["预算执行", "预算审计", "预算管理"],
    "专项资金审计": ["专项", "专项资金", "社保", "营养餐", "扶贫", "惠农"],
    "招投标审计": ["招投标", "采购审计", "政府采购", "串标", "围标"],
    "国企审计": ["国企", "国有企业", "国资"],
    "工程审计": ["工程", "基建", "竣工决算", "工程造价", "投资审计"],
    "绩效评价": ["绩效", "绩效评价", "绩效管理", "绩效考核", "事前评估", "事中监控"],
    "政府补贴审计": ["补贴", "补助", "转移支付", "专项资金"],
    "财政监督": ["财政监督", "财会监督", "财政监管", "监督"],
    "内部控制": ["内控", "内部控制", "内审", "内部审计"],
    "会计实务": ["会计", "会计准则", "核算", "审计准则"],
    "政策法规": ["法规", "政策", "制度", "通知", "办法", "规定"],
    "事务所管理": ["事务所", "执业", "CPA", "注协"],
    "信息化/AI审计": ["信息化", "大数据", "AI", "人工智能", "数字化", "智慧"],
    "能源/碳中和": ["能源", "双碳", "碳中和", "碳排放", "节能"],
}

# ========== 工具函数 ==========

def extract_docx_text(filepath):
    """从docx提取纯文本"""
    import zipfile
    try:
        z = zipfile.ZipFile(filepath)
        xml = z.read('word/document.xml').decode('utf-8')
        text = re.sub(r'<[^>]+>', '', xml)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    except Exception as e:
        return f"[提取失败: {e}]"

def extract_pdf_text(filepath):
    """尝试从PDF提取文本（仅限数字PDF），返回空字符串则需OCR"""
    try:
        from pdfminer.high_level import extract_text
        text = extract_text(filepath)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    except:
        return ""

def classify_by_keywords(text, title=""):
    """基于关键词的业务场景分类"""
    combined = title + " " + text[:500]
    hits = {}
    for scene, keywords in BIZ_SCENES.items():
        score = 0
        for kw in keywords:
            if kw in combined:
                score += 1
        if score > 0:
            hits[scene] = score
    if not hits:
        return ["其他"]
    # 按得分排序，返回top场景
    sorted_hits = sorted(hits.items(), key=lambda x: -x[1])
    return [s[0] for s in sorted_hits[:3]]

def make_filename(title, idx=0):
    """生成安全的文件名"""
    clean = re.sub(r'[\\/:*?"<>|]', '', title)
    clean = re.sub(r'\s+', '_', clean).strip()
    if len(clean) > 80:
        clean = clean[:80]
    prefix = f"{idx:03d}_" if idx else ""
    return prefix + clean + ".md"

def yaml_frontmatter(title, source, scenes, summary, word_count):
    """生成YAML frontmatter"""
    return f"""---
title: "{title}"
source: "{source}"
source_type: "杂志"
business_scenes: {json.dumps(scenes, ensure_ascii=False)}
summary: "{summary}"
word_count: {word_count}
processed_date: "{time.strftime('%Y-%m-%d')}"
---
"""

# ========== 处理流水线 ==========

def process_magazine(magdir):
    """处理单个杂志目录"""
    mag_name = os.path.basename(magdir)
    print(f"\n{'='*60}")
    print(f"开始处理: {mag_name}")
    print(f"{'='*60}")
    
    # 目标目录
    kb_dir = os.path.join(OUTPUT_KNOWLEDGE, "magazines", mag_name)
    ob_dir = os.path.join(OUTPUT_OBSIDIAN, "magazines", mag_name)
    os.makedirs(kb_dir, exist_ok=True)
    os.makedirs(ob_dir, exist_ok=True)
    
    # 列出所有文件（按期次分组）
    issues = {}  # {issue_name: [files]}
    
    # 根目录下的文件
    root_files = sorted([f for f in os.listdir(magdir) if os.path.isfile(os.path.join(magdir, f))])
    if root_files:
        issues["."] = [os.path.join(magdir, f) for f in root_files]
    
    # 子目录（期次）
    subs = sorted([d for d in os.listdir(magdir) if os.path.isdir(os.path.join(magdir, d))])
    for s in subs:
        sp = os.path.join(magdir, s)
        files = sorted([os.path.join(sp, f) for f in os.listdir(sp) if os.path.isfile(os.path.join(sp, f))])
        if files:
            issues[s] = files
    
    total_articles = sum(len(v) for v in issues.values())
    processed = 0
    results = []
    
    # 加载进度
    state = load_state()
    processed_set = set(state.get("processed_files", []))
    
    for issue_name, files in sorted(issues.items()):
        print(f"\n  【期次】{issue_name} ({len(files)}篇)")
        
        # 创建期次目录（知识库）
        issue_kb_dir = os.path.join(kb_dir, issue_name) if issue_name != "." else kb_dir
        issue_ob_dir = os.path.join(ob_dir, issue_name) if issue_name != "." else ob_dir
        os.makedirs(issue_kb_dir, exist_ok=True)
        os.makedirs(issue_ob_dir, exist_ok=True)
        
        for idx, fp in enumerate(files, 1):
            fname = os.path.basename(fp)
            print(f"    [{processed+1}/{total_articles}] {fname}...", end="")
            
            # 跳过已处理
            file_key = fp
            if file_key in processed_set:
                print(f" 跳过（已处理）")
                continue
            
            # 提取文本
            ext = os.path.splitext(fp)[1].lower()
            text = ""
            word_count = 0
            is_ocr = False
            
            if ext == '.docx':
                text = extract_docx_text(fp)
                word_count = len(text)
            elif ext == '.pdf':
                text = extract_pdf_text(fp)
                if len(text) < 100:  # 扫描件
                    is_ocr = True
                    print(f" [需OCR]", end="")
                    text = f"[本文为扫描件PDF，尚未完成OCR识别，请用PaddleOCR处理后再分类入库]"
                    word_count = 0
                else:
                    word_count = len(text)
            
            if not text or word_count < 50:
                if not is_ocr:
                    print(f" 内容过短，跳过")
                else:
                    print(f" OCR待处理")
                processed += 1
                continue
            
            # 生成标题 - 从文件名推断
            title = re.sub(r'\.(docx|pdf)$', '', fname)
            # 去掉编号前缀
            title = re.sub(r'^\d+[\.\s-]*', '', title).strip()
            
            # 分类
            scenes = classify_by_keywords(text, title)
            
            # 生成摘要（取前200字）
            summary = text[:200].replace('"', "'").replace('\n', ' ').strip() + "…"
            
            # 确定年份 - 从期次名提取
            year_match = re.search(r'(\d{4})', issue_name if issue_name != "." else mag_name)
            year = year_match.group(1) if year_match else ""
            
            # 写入知识库
            kb_filename = make_filename(title, idx)
            kb_filepath = os.path.join(issue_kb_dir, kb_filename)
            
            content = yaml_frontmatter(title, f"{mag_name}/{issue_name}", scenes, summary, word_count)
            content += f"\n## 摘要\n\n{summary}\n\n"
            content += f"\n## 业务场景\n\n" + "、".join(scenes) + "\n\n"
            content += f"\n## 全文\n\n{text}\n\n"
            content += f"\n---\n*来源: {mag_name}/{issue_name} | 处理日期: {time.strftime('%Y-%m-%d')}*"
            
            with open(kb_filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 写入Obsidian（简版，带双向链接）
            ob_filename = make_filename(title, idx)
            ob_filepath = os.path.join(issue_ob_dir, ob_filename)
            
            ob_content = yaml_frontmatter(title, f"{mag_name}/{issue_name}", scenes, summary, word_count)
            ob_content += f"\n# {title}\n\n"
            ob_content += f"**来源**: [[{mag_name}]] / [[{issue_name}]]\n\n"
            ob_content += f"**业务场景**: " + "、".join([f"[[{s}]]" for s in scenes]) + "\n\n"
            ob_content += f"**字数**: {word_count} | **处理日期**: {time.strftime('%Y-%m-%d')}\n\n"
            ob_content += f"## 摘要\n\n{summary}\n\n"
            
            with open(ob_filepath, 'w', encoding='utf-8') as f:
                f.write(ob_content)
            
            # 记录结果
            results.append({
                "file": fp,
                "title": title,
                "scenes": scenes,
                "kb_file": kb_filepath,
                "ob_file": ob_filepath,
                "word_count": word_count,
                "is_ocr": is_ocr
            })
            
            # 保存进度
            processed_set.add(file_key)
            save_state({"processed_files": list(processed_set), "results": results})
            
            print(f" ✅ {', '.join(scenes[:2])} ({word_count}字)")
            processed += 1
            
            # 防过快
            if processed % 5 == 0:
                time.sleep(0.5)
    
    # 统计
    print(f"\n{'='*60}")
    print(f"处理完成: {mag_name}")
    print(f"  成功: {len(results)}篇")
    ocr_pending = sum(1 for r in results if r.get("is_ocr"))
    if ocr_pending:
        print(f"  OCR待处理: {ocr_pending}篇")
    print(f"{'='*60}")
    
    return results

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_state(state):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def show_status():
    state = load_state()
    results = state.get("results", [])
    processed = len(state.get("processed_files", []))
    
    print(f"=== 处理进度 ===")
    print(f"已处理文件: {processed}")
    print(f"已入库文章: {len(results)}")
    
    # 按杂志统计
    mags = {}
    for r in results:
        mag = os.path.basename(os.path.dirname(os.path.dirname(r.get("kb_file", ""))))
        if mag not in mags:
            mags[mag] = 0
        mags[mag] += 1
    
    print(f"\n按杂志统计:")
    for mag, cnt in sorted(mags.items()):
        print(f"  {mag}: {cnt}篇")
    
    # OCR待处理
    ocr = [r for r in results if r.get("is_ocr")]
    if ocr:
        print(f"\nOCR待处理: {len(ocr)}篇")
        for r in ocr:
            print(f"  {r.get('title')}")

def show_pending():
    """列出待处理的杂志"""
    mags = sorted([d for d in os.listdir(BASE) if os.path.isdir(os.path.join(BASE, d))])
    state = load_state()
    processed = state.get("processed_files", [])
    
    print(f"=== 待处理杂志 ===")
    for mag in mags:
        mag_path = os.path.join(BASE, mag)
        all_files = set()
        for root, dirs, files in os.walk(mag_path):
            for f in files:
                all_files.add(os.path.join(root, f))
        
        total = len(all_files)
        done = sum(1 for f in all_files if f in processed)
        pct = done/total*100 if total > 0 else 0
        print(f"  {mag}: {done}/{total} ({pct:.0f}%)")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == 'process':
        magdir = sys.argv[2] if len(sys.argv) > 2 else None
        if not magdir:
            print("用法: python magazine_pipeline.py process --magdir <目录>")
            sys.exit(1)
        process_magazine(magdir)
    
    elif cmd == 'status':
        show_status()
    
    elif cmd == 'pending':
        show_pending()
    
    else:
        print(__doc__)
