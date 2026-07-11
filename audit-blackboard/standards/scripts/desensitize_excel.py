# -*- coding: utf-8 -*-
"""
融策审计数据脱敏工具 v1.0
支持：Excel(.xlsx/.xls)、CSV、JSON

用法：
  python desensitize_excel.py \
    --input "原始数据/支付明细.xlsx" \
    --output "脱敏数据/支付明细_脱敏.xlsx" \
    --rules "audit-blackboard/standards/脱敏规则配置.json"

或 Python 调用：
  from desensitize_excel import desensitize_field, desensitize_dataframe
  df_clean = desensitize_dataframe(df, rules)
"""
import os, sys, re, json, argparse
import pandas as pd
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# ================================================================
# 默认脱敏规则（内置）
# ================================================================

DEFAULT_RULES = {
    "name": {
        "type": "regex",
        "pattern": r"([\u4e00-\u9fa5]{1})([\u4e00-\u9fa5]+)",
        "replacement": r"\1**",
        "description": "姓名：保留姓，名替换为**"
    },
    "id_card": {
        "type": "regex",
        "pattern": r"(\d{6})(\d{8})(\d{4})",
        "replacement": r"\1****\3",
        "description": "身份证号：保留前6位+后4位"
    },
    "phone": {
        "type": "regex",
        "pattern": r"(\d{3})(\d{4})(\d{4})",
        "replacement": r"\1****\3",
        "description": "手机号：保留前3位+后4位"
    },
    "bank_card": {
        "type": "regex",
        "pattern": r"(\d{4})(\d{8,})(\d{4})",
        "replacement": r"\1****\3",
        "description": "银行卡号：保留前4位+后4位"
    },
    "email": {
        "type": "regex",
        "pattern": r"([\w.]+)@([\w.]+)",
        "replacement": r"****@\2",
        "description": "邮箱：用户名脱敏"
    },
    "address": {
        "type": "custom",
        "description": "地址：保留到区县，详细地址替换"
    },
    "amount": {
        "type": "custom",
        "description": "金额：区间化"
    },
    "company_name": {
        "type": "custom",
        "description": "企业名称：保留行政区划+行业，具体字号替换"
    },
    "credit_code": {
        "type": "regex",
        "pattern": r"([A-Z0-9]{8})([A-Z0-9]{10})",
        "replacement": r"\1****\2",
        "description": "统一社会信用代码：保留前8位+后4位"
    }
}


# ================================================================
# 核心脱敏函数
# ================================================================

def desensitize_name(value):
    """姓名脱敏：保留姓，名替换为**"""
    if not isinstance(value, str) or len(value) < 2:
        return value
    # 复姓处理
    compound = ['欧阳', '太史', '端木', '上官', '司马', '东方', '独孤', '南宫', '夏侯', '诸葛',
                '尉迟', '皇甫', '公孙', '慕容', '轩辕', '令狐', '钟离', '宇文', '长孙', '鲜于',
                '闾丘', '司徒', '司空', '亓官', '司寇', '子车', '颛孙', '宰父', '谷梁', '段干']
    for cp in compound:
        if value.startswith(cp):
            return cp + '**'
    return value[0] + '**' if len(value) >= 2 else value[0] + '*'


def desensitize_id_card(value):
    """身份证号脱敏：保留前6位+后4位"""
    s = str(value).strip().replace(' ', '')
    # 15位或18位身份证
    if re.match(r'^\d{15}$', s):
        return s[:6] + '****' + s[-4:]
    elif re.match(r'^\d{17}[\dXx]$', s):
        return s[:6] + '****' + s[-4:]
    return value


def desensitize_phone(value):
    """手机号脱敏：保留前3位+后4位"""
    s = str(value).strip().replace(' ', '').replace('-', '')
    if re.match(r'^1\d{10}$', s):
        return s[:3] + '****' + s[-4:]
    return value


def desensitize_bank_card(value):
    """银行卡号脱敏：保留前4位+后4位"""
    s = str(value).strip().replace(' ', '')
    if re.match(r'^\d{16,19}$', s):
        return s[:4] + '****' + s[-4:]
    return value


def desensitize_address(value):
    """地址脱敏：保留到区县，详细地址替换"""
    if not isinstance(value, str):
        return value
    # 匹配到区县级别
    # 匹配模式：省/直辖市 + 市/区 + 区/县 + 街道/镇/乡
    # 保留到区县级
    match = re.match(r'(.{2,7}(?:省|自治区|直辖市))(.{2,10}(?:市|州|盟))(.{2,10}(?:区|县|旗|市))', value)
    if match:
        return match.group(1) + match.group(2) + match.group(3) + '**'
    # 简化版：直辖市/省会城市直接匹配
    match2 = re.match(r'((?:北京|天津|上海|重庆).{2,10}(?:区|县))', value)
    if match2:
        return match2.group(1) + '**'
    # 无法匹配则保留前6个字符
    return value[:6] + '**' if len(value) > 6 else value


def desensitize_amount(value):
    """金额区间化"""
    try:
        v = float(value)
    except (ValueError, TypeError):
        return value

    if v < 50000:
        return '5万以下'
    elif v < 100000:
        return '5-10万'
    elif v < 500000:
        return '10-50万'
    elif v < 1000000:
        return '50-100万'
    elif v < 5000000:
        return '100-500万'
    elif v < 10000000:
        return '500-1000万'
    elif v < 50000000:
        return '1000-5000万'
    elif v < 100000000:
        return '5000万-1亿'
    else:
        return '1亿以上'


def desensitize_company_name(value):
    """企业名称脱敏：保留行政区划+行业，具体字号替换为XX"""
    if not isinstance(value, str):
        return value
    # 保留行政区划前缀（如"四川""成都"）
    prefix = re.match(r'^([\u4e00-\u9fa5]{2,4}(?:省|市|自治区|区|县))', value)
    if prefix:
        prefix_str = prefix.group(1)
        rest = value[len(prefix_str):]
        # 保留行业后缀（如"有限公司""建筑公司"）
        suffix = re.search(r'(?:建筑|工程|科技|贸易|咨询|事务所|会计师|有限责任公司|股份有限公司|有限公司|公司)$', rest)
        if suffix:
            suffix_str = suffix.group(0)
            middle = rest[:suffix.start()]
            return prefix_str + 'XX' + middle[suffix.start():] if middle else prefix_str + 'XX' + suffix_str
        return prefix_str + 'XX' + rest[-4:] if len(rest) > 4 else prefix_str + 'XX'
    return 'XX' + value[-4:] if len(value) > 4 else 'XX公司'


def desensitize_credit_code(value):
    """统一社会信用代码脱敏：保留前8位+后4位"""
    s = str(value).strip().replace(' ', '')
    if re.match(r'^[A-Z0-9]{18}$', s):
        return s[:8] + '****' + s[-4:]
    return value


def desensitize_email(value):
    """邮箱脱敏：用户名替换为****"""
    if not isinstance(value, str) or '@' not in value:
        return value
    user, domain = value.split('@', 1)
    return f'****@{domain}'


# 字段名 → 脱敏函数映射（自动识别）
FIELD_MAP = {
    'name': ['姓名', '名字', '联系人', '负责人', '经办人', '法定代表人', '法人代表', '法人',
             'name', 'contact', 'legal_rep', 'person'],
    'id_card': ['身份证号', '身份证号码', '身份证', '公民身份证号', 'id_card', 'id_number', 'identity'],
    'phone': ['手机号', '电话', '手机', '联系电话', 'phone', 'mobile', 'tel', 'telephone'],
    'bank_card': ['银行卡号', '银行账号', '账号', '卡号', 'bank_card', 'account_number', 'bank_account'],
    'address': ['地址', '住址', '居住地址', '联系地址', 'addr', 'address', 'location'],
    'amount': ['金额', '数额', '合同金额', '支付金额', '中标金额', '金额（元）', '金额(元)',
               'amount', 'price', 'sum', 'value', 'money', 'total', 'payment'],
    'company_name': ['供应商名称', '企业名称', '公司名称', '单位名称', '中标单位', '投标单位',
                     'company', 'supplier', 'vendor', 'enterprise', 'firm'],
    'credit_code': ['统一社会信用代码', '信用代码', '社会信用代码', '统一代码',
                    'credit_code', 'unified_code', 'uscc'],
    'email': ['邮箱', '电子邮件', 'e-mail', 'email', 'mail']
}


def detect_field_type(column_name):
    """根据列名自动识别字段类型"""
    col_lower = str(column_name).lower().strip()
    for field_type, keywords in FIELD_MAP.items():
        for kw in keywords:
            if kw in col_lower or col_lower in kw:
                return field_type
    return None


def desensitize_field(value, field_type):
    """根据字段类型选择脱敏函数"""
    handlers = {
        'name': desensitize_name,
        'id_card': desensitize_id_card,
        'phone': desensitize_phone,
        'bank_card': desensitize_bank_card,
        'address': desensitize_address,
        'amount': desensitize_amount,
        'company_name': desensitize_company_name,
        'credit_code': desensitize_credit_code,
        'email': desensitize_email,
    }
    handler = handlers.get(field_type)
    if handler:
        return handler(value)
    return value


def desensitize_dataframe(df, custom_rules=None, verbose=True):
    """脱敏整个DataFrame

    Args:
        df: pandas DataFrame
        custom_rules: 自定义规则 {列名: 字段类型} 或 None（自动识别）
        verbose: 是否打印脱敏信息

    Returns:
        脱敏后的DataFrame
    """
    df = df.copy()
    desensitized_cols = []

    for col in df.columns:
        # 优先使用自定义规则
        if custom_rules and col in custom_rules:
            field_type = custom_rules[col]
        else:
            field_type = detect_field_type(col)

        if field_type:
            df[col] = df[col].apply(lambda x: desensitize_field(x, field_type))
            desensitized_cols.append(f"{col} → {field_type}")

    if verbose and desensitized_cols:
        print(f"\n✅ 已脱敏 {len(desensitized_cols)} 列:")
        for c in desensitized_cols:
            print(f"   {c}")

    return df


# ================================================================
# 文件级脱敏
# ================================================================

def desensitize_excel(input_path, output_path, custom_rules=None):
    """脱敏Excel文件（支持多sheet）"""
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 读取所有sheet
    xls = pd.ExcelFile(input_path)
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(input_path, sheet_name=sheet_name)
            df_clean = desensitize_dataframe(df, custom_rules, verbose=True)
            df_clean.to_excel(writer, sheet_name=sheet_name, index=False)
            print(f"   Sheet [{sheet_name}]: {len(df)} 行已脱敏")

    print(f"\n💾 脱敏文件已保存: {output_path}")
    return output_path


def desensitize_csv(input_path, output_path, custom_rules=None, encoding='utf-8'):
    """脱敏CSV文件"""
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_path, encoding=encoding)
    df_clean = desensitize_dataframe(df, custom_rules, verbose=True)
    df_clean.to_csv(output_path, index=False, encoding=encoding)

    print(f"\n💾 脱敏文件已保存: {output_path}")
    return output_path


# ================================================================
# CLI
# ================================================================

def main():
    parser = argparse.ArgumentParser(description='融策审计数据脱敏工具 v1.0')
    parser.add_argument('--input', '-i', required=True, help='输入文件路径')
    parser.add_argument('--output', '-o', required=True, help='输出文件路径')
    parser.add_argument('--rules', '-r', help='自定义规则JSON文件（可选）')
    parser.add_argument('--encoding', '-e', default='utf-8', help='CSV编码（默认utf-8）')
    args = parser.parse_args()

    custom_rules = None
    if args.rules and Path(args.rules).exists():
        custom_rules = json.loads(Path(args.rules).read_text(encoding='utf-8'))
        print(f"📋 已加载自定义规则: {args.rules}")

    ext = Path(args.input).suffix.lower()
    if ext in ('.xlsx', '.xls'):
        desensitize_excel(args.input, args.output, custom_rules)
    elif ext == '.csv':
        desensitize_csv(args.input, args.output, custom_rules, args.encoding)
    else:
        print(f"❌ 不支持的文件格式: {ext}，仅支持 .xlsx/.xls/.csv")
        return 1

    print("\n✅ 脱敏完成！")
    return 0


if __name__ == '__main__':
    sys.exit(main())
