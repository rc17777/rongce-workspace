# -*- coding: utf-8 -*-
"""
专项资金合规性审计工具
用法：把支出明细Excel丢进来，自动标记每笔支出是否合规
"""
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
import jieba
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
import pandas as pd
import numpy as np

# =====================================================
# 配置区：改这里的文件名即可
# =====================================================
INPUT_FILE = '支出明细.xlsx'       # 你的Excel文件名
COLUMN_NAME = '摘要'               # 支出摘要所在列名（或'项目名称'/'用途'）
MONEY_COLUMN = '金额'              # 金额列名（没有就填None）
FUND_TYPE = '信息化专项资金'        # 资金类型（用于报告描述）

# =====================================================
# 内置训练数据（也可以自己补充）
# =====================================================
BUILTIN_TRAIN = {
    '信息化专项资金': {
        'N': ['办公费', '差旅费', '印刷费', '培训费', '会议费', '报刊费',
              '考勤机', '档案密集架', '工会活动费', '接待费', '补缴养老保险',
              '打印机耗材', '会议室装修', '办公家具', '物业管理费',
              '水电费', '公务车维修', '招待费', '节日慰问品'],
        'Y': ['信息中心', '网络维护', '系统维护', '数据备份', '软件升级',
              '网络安全', '保密系统', '数据库运维', '政务云', '网站运维',
              'OA系统', '财务软件', '视频会议', '机房', '防火墙',
              '杀毒软件', '带宽租赁', '信息化规划', '等级保护', '信息资产']
    },
    '农业专项资金': {
        'N': ['办公费', '差旅费', '印刷费', '招待费', '车辆维修',
              '设备采购', '基建支出', '会议费'],
        'Y': ['种子', '化肥', '农药', '农田', '灌溉', '农机',
              '种植', '养殖', '培训', '技术服务', '示范推广']
    },
    '教育专项资金': {
        'N': ['办公费', '招待费', '差旅费', '车辆费用', '出国考察'],
        'Y': ['教学设备', '实验室', '图书', '教师培训', '课程开发',
              '信息化教室', '学生资助', '教材']
    }
}

# =====================================================
# 主流程
# =====================================================
def load_user_labels():
    """如果用户自己标注了训练数据，加载进来"""
    label_file = 'fund_labels.txt'
    if os.path.exists(label_file):
        data = []
        with open(label_file, 'r', encoding='utf-8') as f:
            for line in f:
                if '\t' in line:
                    label, text = line.strip().split('\t', 1)
                    data.append((label, text))
        return data
    return []

def build_train_data(fund_type):
    """构造训练数据"""
    rules = BUILTIN_TRAIN.get(fund_type, BUILTIN_TRAIN['信息化专项资金'])
    data = []
    for text in rules['N']:
        data.append(('N', text))
    for text in rules['Y']:
        data.append(('Y', text))
    # 加用户自定义
    data.extend(load_user_labels())
    return data

def train_model(train_data):
    """训练分类模型"""
    texts = [' '.join(jieba.cut(t)) for _, t in train_data]
    labels = [l for l, _ in train_data]
    vec = CountVectorizer(analyzer='char', ngram_range=(1, 3))
    X = vec.fit_transform(texts)
    clf = LogisticRegression(random_state=42, max_iter=1000)
    clf.fit(X, labels)
    return vec, clf

def audit_file(input_file, col_name, money_col, fund_type):
    """主审计函数"""
    print(f'╔══════════════════════════════════════╗')
    print(f'║ {fund_type}合规性审计工具 v1.0 ║')
    print(f'╚══════════════════════════════════════╝\n')

    # 1. 读取数据
    if input_file.endswith('.xlsx'):
        df = pd.read_excel(input_file)
    else:
        df = pd.read_csv(input_file)

    if col_name not in df.columns:
        print(f'错误: 找不到列"{col_name}"，当前列: {list(df.columns)}')
        return

    texts = df[col_name].astype(str).tolist()
    amounts = df[money_col].tolist() if money_col and money_col in df.columns else [0]*len(texts)
    print(f'[1/4] 读取数据: {len(texts)} 条支出记录\n')

    # 2. 训练模型
    train_data = build_train_data(fund_type)
    vec, clf = train_model(train_data)
    acc = clf.score(vec.transform([' '.join(jieba.cut(t)) for _, t in train_data]),
                    [l for l, _ in train_data])
    print(f'[2/4] 训练模型: 准确率 {acc:.0%} ({len(train_data)}条训练数据)\n')

    # 3. 预测
    X = vec.transform([' '.join(jieba.cut(t)) for t in texts])
    preds = clf.predict(X)
    probs = clf.predict_proba(X)
    print(f'[3/4] 分类完成\n')

    # 4. 输出结果
    n_count = sum(1 for p in preds if p == 'N')
    n_amount = sum(a for p, a in zip(preds, amounts) if p == 'N')
    print(f'╔══════════════ 审计结果 ══════════════╗')
    print(f'║ 合规支出: {len(texts)-n_count} 条')
    print(f'║ 不合规支出: {n_count} 条')
    if money_col and money_col in df.columns:
        print(f'║ 不合规金额: {n_amount:,.0f} 元')
    print(f'╚══════════════════════════════════════╝\n')

    print('=== 不合规支出明细 ===')
    for i, (text, pred, prob) in enumerate(zip(texts, preds, probs)):
        if pred == 'N':
            conf = max(prob)
            amt = f' | ¥{amounts[i]:,.0f}' if amounts[i] else ''
            print(f'  [N] 置信度{conf:.0%} | {text}{amt}')

    # 写Excel报告
    output = input_file.replace('.xlsx', '_审计结果.xlsx').replace('.csv', '_审计结果.xlsx')
    df_result = df.copy()
    df_result['合规判断'] = ['合规' if p == 'Y' else '不合规' for p in preds]
    df_result['置信度'] = [f'{max(probs[i]):.0%}' for i in range(len(probs))]
    df_result.to_excel(output, index=False)

    print(f'\n[4/4] 结果已保存到: {output}')
    img = '✅' if n_count > 0 else '⚠️'
    print(f'{img} 审计完成! 发现 {n_count} 条不合规支出，请在结果表中逐条核实。')

# =====================================================
# 入口
# =====================================================
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='专项资金合规性审计工具')
    p.add_argument('file', nargs='?', default=INPUT_FILE, help='支出明细Excel文件')
    p.add_argument('-c', '--column', default=COLUMN_NAME, help='摘要所在列名')
    p.add_argument('-m', '--money', default=MONEY_COLUMN, help='金额列名')
    p.add_argument('-t', '--type', default=FUND_TYPE, help='资金类型')
    args = p.parse_args()
    audit_file(args.file, args.column, args.money, args.type)
