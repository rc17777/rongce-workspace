"""
Phase 2: Batch AI Analysis Prompt Template
Read category JSON, chunk into batches, send to LLM
"""
import os, json

CAT_DIR = r'D:\openclaw-workspace\temp\magazine_extract'
BATCH_SIZE = 8  # Articles per LLM call
OUTPUT_DIR = r'D:\openclaw-workspace\temp\magazine_skills'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_batch_prompts(cat_file, cat_name):
    """Generate batch prompts for a category"""
    with open(os.path.join(CAT_DIR, cat_file), 'r', encoding='utf-8') as f:
        articles = json.load(f)
    
    batches = []
    for i in range(0, len(articles), BATCH_SIZE):
        batch = articles[i:i + BATCH_SIZE]
        articles_text = ''
        for j, art in enumerate(batch):
            articles_text += f"""
### 文章{j+1}: {art['title']}
- 来源: {art['issue']}
- 标签: {', '.join(art['tags'][:5])}
- 摘要: {art['summary'][:300]}
"""
        
        prompt = f"""你是资深政府审计专家。请从以下{len(batch)}篇《中国审计》/《审计案例》文章中提取可复用的审计知识和技能。

{articles_text}

请按以下结构化格式输出（纯文本，不用JSON）：

## 提取结果 - {cat_name} (第{i//BATCH_SIZE + 1}批)

### 一、审计逻辑与方法论
列出从这些文章中识别出的共性审计逻辑、分析框架、方法论（3-5条，每条50字以内）

### 二、关键技能与技巧
具体的审计操作技能、查证技巧、发现方法（3-5条，每条说明适用场景）

### 三、红线/问题模式
常见问题类型、违规模式、预警信号（3-5条）

### 四、可直接复用的模板
审计程序步骤、检查清单、分析表结构（2-3个，简洁版）

### 五、适用场景
这些知识最适合融策公司哪类审计业务？（如：经责审计/绩效评价/专项债/工程审计等）
"""
        batches.append({
            'cat_name': cat_name,
            'batch_num': i // BATCH_SIZE + 1,
            'total_batches': (len(articles) + BATCH_SIZE - 1) // BATCH_SIZE,
            'article_count': len(batch),
            'prompt': prompt
        })
    
    return batches

# Generate all batches
all_batches = []
files = sorted([f for f in os.listdir(CAT_DIR) if f.endswith('.json') and not f.startswith('_')])
for f in files:
    cat_name = f.replace('.json', '')
    batches = generate_batch_prompts(f, cat_name)
    all_batches.extend(batches)
    print(f'{cat_name}: {len(batches)} batches ({len(batches)*BATCH_SIZE} articles)')

# Save all batches
with open(os.path.join(OUTPUT_DIR, '_all_batches.json'), 'w', encoding='utf-8') as f:
    json.dump(all_batches, f, ensure_ascii=False, indent=2)

print(f'\nTotal: {len(all_batches)} batches across {len(files)} categories')
print(f'Output: {OUTPUT_DIR}/_all_batches.json')
