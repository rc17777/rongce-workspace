#!/usr/bin/env python3
"""
模型1: 同一IP地址多家投标 — 围标串标特征识别
来源：群众语言堂公众号《政府采购审计大数据技术超详细操作》
"""
import pandas as pd
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description='同一IP多家投标识别')
    parser.add_argument('--input', '-i', required=True, help='投标记录表.xlsx')
    parser.add_argument('--output', '-o', default='疑点_同一IP多家投标.xlsx', help='输出文件')
    parser.add_argument('--min-unit', type=int, default=1, help='最小单位数（>此值输出，默认1）')
    args = parser.parse_args()

    try:
        df = pd.read_excel(args.input)
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        sys.exit(1)

    # 检查必要字段
    required = ['投标IP', '投标单位']
    for col in required:
        if col not in df.columns:
            print(f"❌ 缺少必要字段: {col}")
            print(f"   现有字段: {list(df.columns)}")
            sys.exit(1)

    # 按IP分组，统计投标单位数
    ip_groups = df.groupby('投标IP')['投标单位'].apply(list).reset_index()
    ip_groups['单位数'] = ip_groups['投标单位'].apply(lambda x: len(set(x)))
    ip_groups['单位名单'] = ip_groups['投标单位'].apply(lambda x: '、'.join(sorted(set(x))))

    # 筛选疑点
    suspicious = ip_groups[ip_groups['单位数'] > args.min_unit].copy()
    suspicious = suspicious.sort_values('单位数', ascending=False)

    if len(suspicious) == 0:
        print("✅ 未发现同一IP多家投标的疑点")
        # 输出空文件
        pd.DataFrame(columns=['投标IP', '单位数', '单位名单']).to_excel(args.output, index=False)
        return

    suspicious.to_excel(args.output, index=False, columns=['投标IP', '单位数', '单位名单'])
    print(f"✅ 完成！共发现 {len(suspicious)} 个疑点IP")
    print(f"   输出文件: {args.output}")
    print(f"\n   疑点汇总:")
    for _, row in suspicious.head(10).iterrows():
        print(f"   IP: {row['投标IP']} → {row['单位数']}家单位: {row['单位名单']}")
    if len(suspicious) > 10:
        print(f"   ... 还有 {len(suspicious)-10} 条疑点，详见输出文件")

if __name__ == '__main__':
    main()
