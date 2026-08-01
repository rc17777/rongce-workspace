# -*- coding: utf-8 -*-
"""
口径匹配 LLM 增强模块 v0.2
当正则模糊匹配失败时，调用大模型判断口径名相似度
用法: 在 caliber_checker.py 中可选启用 (--use-llm)
"""
import sys, os, json, hashlib
sys.stdout.reconfigure(encoding='utf-8')

# LLM 缓存文件路径
CACHE_FILE = os.path.join(os.path.dirname(__file__), '.llm_match_cache.json')

def _load_cache():
    """加载 LLM 匹配缓存"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def _save_cache(cache):
    """保存 LLM 匹配缓存"""
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f'  ⚠️ 缓存保存失败: {e}')

def _make_cache_key(indicator, caliber_names):
    """生成缓存键"""
    key_str = f"{indicator}||{json.dumps(sorted(caliber_names), ensure_ascii=False)}"
    return hashlib.md5(key_str.encode('utf-8')).hexdigest()

# 从 openclaw.json 读取 API 配置
def get_llm_client():
    """获取 LLM 客户端（优先 deepseek，备选 qwen）"""
    config_path = r'C:\Users\scrccpa\.openclaw\openclaw.json'
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    
    # 尝试 deepseek
    try:
        api_key = config['models']['providers']['deepseek-direct']['apiKey']
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url='https://api.deepseek.com/v1', timeout=30)
        return client, 'deepseek-chat'
    except:
        pass
    
    # 备选 qwen
    try:
        api_key = config['models']['providers']['qwen-direct']['apiKey']
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url='https://dashscope.aliyuncs.com/compatible-mode/v1', timeout=30)
        return client, 'qwen-turbo'
    except:
        pass
    
    return None, None

def check_caliber_similarity(indicator_name, caliber_names, client=None, model=None, use_cache=True):
    """
    用 LLM 判断 indicator_name 与 caliber_names 列表中哪个最相似
    返回: (best_match, confidence) 或 (None, 0)
    """
    # 检查缓存
    cache = _load_cache() if use_cache else {}
    cache_key = _make_cache_key(indicator_name, caliber_names)
    
    if use_cache and cache_key in cache:
        cached = cache[cache_key]
        return cached.get('match'), cached.get('confidence', 0)
    
    if not client:
        client, model = get_llm_client()
    if not client:
        return None, 0
    
    prompt = f"""你是一个审计口径匹配专家。请判断以下报告中的指标名称与档案中定义的口径名称哪个最匹配。

报告中的指标：{indicator_name}

档案中的口径列表：
{json.dumps(caliber_names, ensure_ascii=False, indent=2)}

请返回最匹配的口径名称和置信度（0-100）。如果没有匹配的，返回 null。

格式：{{"match": "口径名称或null", "confidence": 0-100, "reason": "简要理由"}}"""
    
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=200,
            temperature=0.1
        )
        result_text = resp.choices[0].message.content.strip()
        # 提取 JSON
        if '{' in result_text:
            start = result_text.index('{')
            end = result_text.rindex('}') + 1
            result = json.loads(result_text[start:end])
            match_val = result.get('match')
            conf_val = result.get('confidence', 0)
            # 写入缓存
            if use_cache:
                cache[cache_key] = {'match': match_val, 'confidence': conf_val}
                _save_cache(cache)
            return match_val, conf_val
    except Exception as e:
        print(f'  ⚠️ LLM 匹配失败: {e}')
    
    return None, 0

def clear_cache():
    """清空 LLM 匹配缓存"""
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
        print(f'✅ 缓存已清空: {CACHE_FILE}')
    else:
        print('ℹ️ 缓存文件不存在')

def batch_match_claims(claims, caliber_definitions, threshold=60, use_cache=True):
    """
    批量匹配 claims，对模糊匹配失败的调用 LLM
    返回: 增强后的 claims 列表（增加 llm_match 字段）
    """
    client, model = get_llm_client()
    if not client:
        print('  ⚠️ 无法获取 LLM 客户端，跳过语义匹配')
        return claims
    
    caliber_names = [c['name'] for c in caliber_definitions]
    enhanced = []
    cache_hits = 0
    
    for claim in claims:
        indicator = claim.get('indicator', '')
        if not indicator:
            enhanced.append(claim)
            continue
        
        # 先尝试简单的字符串匹配
        best_match = None
        for cal_name in caliber_names:
            if cal_name in indicator or indicator in cal_name:
                best_match = cal_name
                break
        
        if best_match:
            claim['match_type'] = 'string'
            claim['llm_match'] = best_match
            claim['llm_confidence'] = 80
            enhanced.append(claim)
            continue
        
        # 字符串匹配失败，调用 LLM
        llm_match, confidence = check_caliber_similarity(indicator, caliber_names, client, model, use_cache)
        if llm_match and confidence >= threshold:
            claim['match_type'] = 'llm'
            claim['llm_match'] = llm_match
            claim['llm_confidence'] = confidence
            enhanced.append(claim)
        else:
            claim['match_type'] = 'none'
            claim['llm_match'] = None
            claim['llm_confidence'] = 0
            enhanced.append(claim)
    
    # 统计缓存命中
    cache = _load_cache()
    print(f'  📊 LLM 缓存命中: {len(cache)} 条')
    
    return enhanced

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='LLM 口径匹配缓存管理')
    parser.add_argument('--clear', action='store_true', help='清空缓存')
    parser.add_argument('--test', action='store_true', help='测试匹配')
    args = parser.parse_args()
    
    if args.clear:
        clear_cache()
    elif args.test:
        # 测试
        test_indicator = "评审业务费预算"
        test_calibers = ["评审业务费年度预算", "运行经费年度预算", "项目评审金额"]
        
        match, conf = check_caliber_similarity(test_indicator, test_calibers)
        print(f"指标: {test_indicator}")
        print(f"匹配: {match} (置信度: {conf})")
    else:
        # 显示缓存统计
        cache = _load_cache()
        print(f'📊 LLM 匹配缓存: {len(cache)} 条')
        if cache:
            print(f'   文件: {CACHE_FILE}')
