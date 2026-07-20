"""
审计报告敏感信息脱敏器
=========================
用途：上传报告到 LLM API 前脱敏，处理后还原
用法:
    from scripts.desensitize import sanitize_for_llm, restore_from_llm
    
    sanitized, mapping = sanitize_for_llm("报告原文...")
    # 发送 sanitized 到 LLM
    # 收到 LLM 回复后：
    result = restore_from_llm(llm_reply, mapping)
"""
import re

# 敏感信息模式
PATTERNS = {
    'name': re.compile(r'[^\d\W][\u4e00-\u9fa5]{1,3}(?:先生|女士|同志|局长|处长|科长|主任|书记|总经理|董事长|经理)'),  # 人名+职务
    'org': re.compile(r'(?:[^\d\W][\u4e00-\u9fa5]{2,8}(?:局|处|科|委|办|中心|公司|集团|院|所|校|银行|股|有限|责任))'),  # 单位名
    'money': re.compile(r'(\d[\d,.]{0,12}(?:万元|亿元|元|万|亿))'),  # 金额
    'docno': re.compile(r'([\u4e00-\u9fa5]{1,6}(?:发|字|函|文|号|办)\[[\d]{4}\]\d{1,6}号?)'),  # 文号
    'idcard': re.compile(r'\d{18}[\dXx]?|\d{17}[\dXx]'),  # 身份证号
    'phone': re.compile(r'1[3-9]\d{9}'),  # 手机号
    'bankcard': re.compile(r'\d{16,19}'),  # 银行卡号
}

REPLACEMENTS = {
    'name': '[姓名]',
    'org': '[单位]',
    'money': '[金额]',
    'docno': '[文号]',
    'idcard': '[身份证号]',
    'phone': '[手机号]',
    'bankcard': '[银行卡号]',
}

def sanitize_for_llm(text):
    """脱敏：替换敏感信息为占位符，返回(脱敏文本, 映射表)"""
    mapping = {k: [] for k in PATTERNS}
    result = text
    
    for key, pattern in PATTERNS.items():
        found = pattern.findall(result)
        for val in found:
            placeholder = REPLACEMENTS[key]
            # 同一个值在不同的位置可能不同，用唯一ID
            uid = f'{placeholder}_{len(mapping[key])}'
            result = result.replace(val, uid, 1)
            mapping[key].append({'original': val, 'placeholder': uid})
    
    return result, mapping

def restore_from_llm(text, mapping):
    """还原：将LLM回复中的占位符替换回原始值"""
    result = text
    for key, items in mapping.items():
        for item in items:
            result = result.replace(item['placeholder'], item['original'])
    return result

# ====== 测试 ======
if __name__ == '__main__':
    test = """根据审计方案，李建国处长带队对XX市财政局2023年度预算执行情况进行审计。
发现虚列支出金额328.5万元，涉及文号X财发[2023]45号。
相关人员联系电话13800138000。"""
    
    sanitized, mapping = sanitize_for_llm(test)
    print('=== 脱敏后 ===')
    print(sanitized)
    print()
    print('=== 映射表 ===')
    for k, v in mapping.items():
        if v:
            print(f'  {k}: {v}')
    
    restored = restore_from_llm(sanitized, mapping)
    print()
    print('=== 还原后 ===')
    print(restored)
    print()
    print(f'还原匹配: {test == restored}')