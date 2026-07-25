#!/usr/bin/env python3
"""
P0-5: 第零道门 — 数据分级+脱敏前置守卫
任何API调用前必须通过：数据分级 → 脱敏 → 本地留存映射表
涉密项目 → 禁公有云API → 本地化+物理隔离
"""

import re, json, hashlib, os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class DataClass(Enum):
    """数据敏感度分级"""
    SECRET = "涉密"       # 经济责任/专项资金审计中的涉密数据，禁走公有API
    SENSITIVE = "敏感"    # 含个人信息/财务明细，需脱敏后才能用API
    INTERNAL = "内部"     # 一般业务数据，需访问控制
    PUBLIC = "公开"       # 已公开数据

class AuditDataType(Enum):
    """审计数据类型"""
    FINANCIAL = "财务数据"
    PERSONAL = "个人信息"
    CONTRACT = "合同文本"
    BIDDING = "招投标数据"
    LEGAL = "法律文书"
    GENERAL = "通用数据"


@dataclass
class DesensitizeRule:
    """脱敏规则"""
    name: str           # 规则名称
    pattern: str        # 正则表达式
    replacement: str    # 替换为
    priority: int = 0   # 优先级


# 脱敏规则库
DESENSITIZE_RULES = [
    # 身份证号 → 前面+****+后4位
    DesensitizeRule(
        "身份证号", 
        r'([1-9]\d{5}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx])',
        lambda m: m.group()[:3] + '****' + m.group()[-4:],
        1
    ),
    # 手机号
    DesensitizeRule(
        "手机号",
        r'1[3-9]\d{9}',
        lambda m: m.group()[:3] + '****' + m.group()[-4:],
        1
    ),
    # 银行卡号
    DesensitizeRule(
        "银行卡号",
        r'[1-9]\d{15,18}',
        lambda m: m.group()[:4] + '****' + m.group()[-4:],
        1
    ),
    # 统一社会信用代码 → 保留前2位+后4位
    DesensitizeRule(
        "统一社会信用代码",
        r'[1-9A-HJ-NPQRTUWXY]\d{14}[0-9A-HJ-NPQRTUWXY]',
        lambda m: m.group()[:2] + '***' + m.group()[-4:],
        2
    ),
    # 被审计单位名称（特定模式）
    DesensitizeRule(
        "被审计单位名",
        r'(成都市郫都区|四川省|成都市)[\u4e00-\u9fa5]+(人民政府|街道办事处|财政局|审计局|教育局)',
        lambda m: m.group()[:4] + '***' + m.group()[-3:],
        3
    ),
]


@dataclass
class DataGuardResult:
    """数据守卫检查结果"""
    data_class: DataClass
    can_use_public_api: bool = False
    needs_desensitization: bool = False
    desensitized_text: str = ""
    mapping: Dict[str, str] = field(default_factory=dict)  # 脱敏映射表
    warnings: List[str] = field(default_factory=list)
    checksum: str = ""  # 原始数据hash
    timestamp: str = ""


class DataGuard:
    """
    第零道门：数据安全守卫
    
    使用：
    >>> guard = DataGuard()
    >>> result = guard.check("项目涉及张三身份证510123199001011234", 
    ...     project_type="预算执行审计")
    >>> if result.can_use_public_api:
    ...     safe_text = result.desensitized_text
    """
    
    # 涉密项目类型
    SECRET_PROJECTS = [
        '经济责任审计', '专项资金审计', '政府补贴审计',
        '国企审计', '招投标审计'
    ]
    
    # 敏感项目类型
    SENSITIVE_PROJECTS = [
        '预算执行审计', '收支审计', '绩效评价', 
        '工程竣工决算财务审计', '往来款清理'
    ]

    def classify_data(self, text: str, project_type: str) -> DataClass:
        """自动分级"""
        if project_type in self.SECRET_PROJECTS:
            return DataClass.SECRET
        
        # 检测敏感内容
        has_personal = any(bool(re.search(r.pattern, text)) for r in DESENSITIZE_RULES[:3])
        has_financial = bool(re.search(r'[0-9,]+\.?\d*\s*(元|万元|亿元)', text))
        
        if has_personal or has_financial:
            return DataClass.SENSITIVE
        
        if project_type in self.SENSITIVE_PROJECTS:
            return DataClass.INTERNAL
        
        return DataClass.PUBLIC

    def desensitize(self, text: str) -> Tuple[str, Dict[str, str]]:
        """执行脱敏"""
        result = text
        mapping = {}
        
        for rule in sorted(DESENSITIZE_RULES, key=lambda r: r.priority):
            matches = list(re.finditer(rule.pattern, text))
            for i, m in enumerate(matches):
                original = m.group()
                if callable(rule.replacement):
                    replacement = rule.replacement(m)
                else:
                    replacement = f"[{rule.name}_{i+1}]"
                mapping[replacement] = original
                result = result.replace(original, replacement, 1)
        
        return result, mapping

    def check(self, text: str, project_type: str, 
              project_name: str = "") -> DataGuardResult:
        """完整检查流程"""
        # Step 1: 数据分级
        data_class = self.classify_data(text, project_type)
        result = DataGuardResult(
            data_class=data_class,
            checksum=hashlib.sha256(text.encode()).hexdigest()[:16],
            timestamp=datetime.now().isoformat()
        )
        
        # Step 2: 涉密项目 → 禁止公有API
        if result.data_class == DataClass.SECRET:
            result.can_use_public_api = False
            result.warnings.append(
                f"🚫 涉密项目禁止调用公有云API。项目类型：{project_type}。"
                f"请使用本地化部署模型（昇腾910B + DeepSeek开源版）"
            )
            return result
        
        # Step 3: 敏感数据 → 脱敏
        if result.data_class in (DataClass.SENSITIVE, DataClass.INTERNAL):
            result.needs_desensitization = True
            result.desensitized_text, result.mapping = self.desensitize(text)
            result.can_use_public_api = True
            result.warnings.append(
                f"⚠️ 已脱敏：{len(result.mapping)}条敏感信息。映射表已本地留存。"
            )
            return result
        
        # Step 4: 普通数据 → 可裸传
        result.can_use_public_api = True
        result.desensitized_text = text
        return result

    def save_mapping(self, result: DataGuardResult, output_dir: str = ""):
        """保存脱敏映射表到本地"""
        if not output_dir:
            output_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'output', 'algorithm_quality')
        os.makedirs(output_dir, exist_ok=True)
        
        path = os.path.join(output_dir, f"desensitize_{result.checksum}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({
                'checksum': result.checksum,
                'timestamp': result.timestamp,
                'data_class': result.data_class.value,
                'mapping': result.mapping,
                'warnings': result.warnings
            }, f, ensure_ascii=False, indent=2)
        
        return path

    def guard_decorator(self, project_type: str):
        """装饰器：自动守卫API调用前的数据"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                text = kwargs.get('text', args[0] if args else '')
                result = self.check(text, project_type)
                if not result.can_use_public_api:
                    return {'error': 'DATA_GUARD_BLOCKED', 'warnings': result.warnings}
                kwargs['text'] = result.desensitized_text
                kwargs['_guard_result'] = result
                func_result = func(*args, **kwargs)
                # 还原脱敏
                if isinstance(func_result, dict) and 'output' in func_result:
                    output = func_result['output']
                    for masked, original in result.mapping.items():
                        output = output.replace(masked, original)
                    func_result['output'] = output
                return func_result
            return wrapper
        return decorator


# ===== CLI Demo =====
if __name__ == '__main__':
    guard = DataGuard()
    
    test_text = """
    被审计单位：成都市郫都区人民政府红光街道办事处
    法定代表人身份证：510123199001011234
    联系人手机：13812345678
    开户行账号：6222021234567890123
    统一社会信用代码：91510124MA6ABCD123
    项目预算：4,079,300元
    """
    
    print("=" * 60)
    print("  第零道门：数据分级脱敏守卫")
    print("=" * 60)
    
    # 测试涉密项目
    print("\n【场景1：经济责任审计（涉密）】")
    r = guard.check(test_text, "经济责任审计")
    print(f"  数据分级: {r.data_class.value}")
    print(f"  可调公有API: {r.can_use_public_api}")
    print(f"  {'; '.join(r.warnings)}")
    
    # 测试敏感项目
    print("\n【场景2：预算执行审计（敏感）】")
    r = guard.check(test_text, "预算执行审计")
    print(f"  数据分级: {r.data_class.value}")
    print(f"  可调公有API: {r.can_use_public_api}")
    print(f"  需脱敏: {r.needs_desensitization}")
    if r.desensitized_text:
        print(f"  脱敏后:\n{r.desensitized_text[:300]}...")
    print(f"  {'; '.join(r.warnings)}")
    
    # 保存映射
    path = guard.save_mapping(r, 'output/algorithm_quality')
    print(f"\n  📁 映射表已保存: {path}")
