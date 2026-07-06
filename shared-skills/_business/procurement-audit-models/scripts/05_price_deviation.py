#!/usr/bin/env python3
"""
模型5: 采购价格偏离度分析 — Z值异常 + 政府监测价格比对
来源：群众语言堂公众号《国有企业审计大数据技术超详细操作》
依赖：pip install pandas openpyxl numpy
"""
import pandas as pd
import numpy as np
import argparse
import sys
import os

def main():
    parser = argparse.ArgumentParser(description='采购价格偏离度分析')
    parser.add_argument('--input', '-i', required=True, help='采购明细.xlsx')
    parser.add_argument('--monitor', '-m', help='政府价格监测.xlsx（可选）')
    parser.add_argument('--output', '-o', default='./output/', help='输出目录')
    parser.add_argument('--z-threshold', type=float, default=2.0, help='Z值异常阈值（默认2.0）')
    parser.add_argument('--price-deviation', type=float, default=0.3, help='监测价格偏离率阈值（默认0.3=30%）')
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    # 读取采购数据
    try:
        df = pd.read_excel(args.input)
    except Exception as e:
        print(f"❌ 读取采购文件失败: {e}")
        sys.exit(1)

    # 检查字段
    required = ['物料编码', '采购单价', '物料名称', '采购时间']
    fields_present = [c for c in required if c in df.columns]
    if len(fields_present) < 2:
        print(f"❌ 缺少核心字段。需要至少包含: 物料编码 + 采购单价")
        print(f"   现有字段: {list(df.columns)}")
        sys.exit(1)

    # 确定物料编码字段
    code_col = '物料编码' if '物料编码' in df.columns else df.columns[0]
    price_col = '采购单价' if '采购单价' in df.columns else next((c for c in df.columns if '价' in c or '金额' in c), df.columns[1])

    print(f"📊 使用物料编码列: {code_col}")
    print(f"📊 使用价格列: {price_col}")
    print(f"📊 总记录数: {len(df)}")

    # 方法1: Z值偏离度分析
    if price_col in df.columns:
        df['价格Z值'] = df.groupby(code_col, group_keys=False)[price_col].transform(
            lambda x: (x - x.mean()) / x.std() if x.std() > 0 else 0
        )
        high_price = df[abs(df['价格Z值']) > args.z_threshold].copy()
        high_price = high_price.sort_values('价格Z值', ascending=False)

        if len(high_price) > 0:
            out1 = os.path.join(args.output, '疑点_价格Z值异常.xlsx')
            high_price.to_excel(out1, index=False)
            print(f"\n✅ 方法1完成: Z值偏离疑点 {len(high_price)} 条")
            print(f"   输出: {out1}")
            print(f"   示例:")
            for _, row in high_price.head(5).iterrows():
                print(f"   {row.get(code_col,'?')} | Z值={row['价格Z值']:.2f} | 单价={row.get(price_col,'?')}")
        else:
            print(f"\n✅ 方法1: 未发现Z值偏离>{args.z_threshold}的疑点")
            pd.DataFrame().to_excel(os.path.join(args.output, '疑点_价格Z值异常.xlsx'), index=False)
    else:
        print(f"⚠️ 跳过Z值分析: 找不到价格列")

    # 方法2: 与政府监测价格比对
    if args.monitor and os.path.exists(args.monitor):
        try:
            monitor_df = pd.read_excel(args.monitor)
            print(f"\n📊 政府监测数据: {len(monitor_df)} 条记录")
            
            # 自动匹配列名
            name_col = None
            for c in ['物料名称', '商品名称', '品名', '名称']:
                if c in df.columns and c in monitor_df.columns:
                    name_col = c
                    break
            
            time_col_df = None
            time_col_m = None
            for c in ['采购时间', '月份', '日期', '年月']:
                if c in df.columns:
                    time_col_df = c
                if c in monitor_df.columns:
                    time_col_m = c

            if name_col and time_col_df and time_col_m:
                merged = pd.merge(df, monitor_df, on=[name_col, time_col_df], suffixes=('_采购', '_监测'))
                if price_col in merged.columns and '监测价格' in merged.columns:
                    merged['偏离率'] = (merged[price_col] - merged['监测价格']) / merged['监测价格']
                    suspicious = merged[abs(merged['偏离率']) > args.price_deviation].sort_values('偏离率', ascending=False)
                    
                    if len(suspicious) > 0:
                        out2 = os.path.join(args.output, '疑点_价格偏离监测.xlsx')
                        suspicious.to_excel(out2, index=False)
                        print(f"✅ 方法2完成: 价格偏离疑点 {len(suspicious)} 条")
                        print(f"   输出: {out2}")
                        for _, row in suspicious.head(5).iterrows():
                            print(f"   {row.get(name_col,'?')} | 偏离率={row['偏离率']:.1%}")
                    else:
                        print(f"✅ 方法2: 未发现价格偏离>{args.price_deviation:.0%}的疑点")
            else:
                print(f"⚠️ 方法2跳过: 无法自动匹配字段")
                print(f"  采购字段: {list(df.columns)}")
                print(f"  监测字段: {list(monitor_df.columns)}")
        except Exception as e:
            print(f"⚠️ 方法2失败: {e}")
    else:
        print(f"ℹ️ 方法2跳过: 未提供政府监测数据 (--monitor)")

    print(f"\n✅ 全部完成! 输出目录: {args.output}")
    for f in os.listdir(args.output):
        print(f"   📄 {f}")

if __name__ == '__main__':
    main()
