#!/usr/bin/env python3
"""
模型7: 采购异常交易检测 — Isolation Forest
来源：群众语言堂《七大核心方法玩转审计数据分析》
"""
import pandas as pd
import numpy as np
import argparse
import sys
import os
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

def main():
    parser = argparse.ArgumentParser(description='采购异常交易检测')
    parser.add_argument('--input', '-i', required=True, help='采购明细.xlsx')
    parser.add_argument('--features', '-f', nargs='+', help='检测特征列')
    parser.add_argument('--output', '-o', default='./output/', help='输出目录')
    parser.add_argument('--contamination', '-c', type=float, default=0.05, help='预期异常比例')
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    df = pd.read_excel(args.input) if args.input.endswith('.xlsx') else pd.read_csv(args.input, encoding='utf-8-sig')
    
    features = args.features or [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])][:5]
    if len(features) < 2:
        print(f"❌ 需要至少2个数值特征")
        sys.exit(1)

    print(f"📊 采购异常检测 — Isolation Forest")
    print(f"   特征: {features}")
    print(f"   总记录: {len(df)}")
    print(f"   预期异常率: {args.contamination:.0%}")

    mask = df[features].notna().all(axis=1)
    X = df.loc[mask, features]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = IsolationForest(contamination=args.contamination, random_state=42, n_estimators=100)
    df.loc[mask, '异常标签'] = model.fit_predict(X_scaled)
    df.loc[mask, '异常分数'] = model.decision_function(X_scaled).round(4)

    anomalies = df[df['异常标签'] == -1].copy()
    print(f"\n发现 {len(anomalies)} 条异常交易 ({(len(anomalies)/len(df))*100:.1f}%)")

    if len(anomalies) > 0:
        vendor_col = next((c for c in df.columns if '供应商' in c or 'vendor' in c.lower()), None)
        if vendor_col:
            vendor_summary = anomalies.groupby(vendor_col).agg(
                异常交易数=('异常标签', 'count'),
                平均异常分数=('异常分数', 'mean')
            ).sort_values('异常交易数', ascending=False)
            
            print(f"\n按{vendor_col}汇总:")
            print(vendor_summary.head(20).to_string())

        out_file = os.path.join(args.output, '结果_异常交易.xlsx')
        with pd.ExcelWriter(out_file) as w:
            anomalies.to_excel(w, sheet_name='异常交易', index=False)
            if vendor_col:
                vendor_summary.to_excel(w, sheet_name='按供应商汇总')
        print(f"\n✅ 输出: {out_file}")
    else:
        print("✅ 未发现异常交易")
        pd.DataFrame().to_excel(os.path.join(args.output, '结果_异常交易.xlsx'), index=False)

if __name__ == '__main__':
    main()
