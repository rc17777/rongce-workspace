#!/usr/bin/env python3
"""
方法3: 回归分析 — 建立预测模型，识别异常偏离
"""
import pandas as pd
import numpy as np
import argparse
import sys
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.preprocessing import StandardScaler

def main():
    parser = argparse.ArgumentParser(description='回归分析')
    parser.add_argument('--input', '-i', required=True)
    parser.add_argument('--target', '-t', required=True, help='目标变量列名')
    parser.add_argument('--features', '-f', nargs='+', help='特征变量列名（多个）')
    parser.add_argument('--output', '-o', default='./输出_回归分析.xlsx')
    args = parser.parse_args()

    df = pd.read_excel(args.input) if args.input.endswith('.xlsx') else pd.read_csv(args.input, encoding='utf-8-sig')
    
    features = args.features or [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c != args.target][:5]
    if args.target not in df.columns:
        print(f"❌ 目标列 '{args.target}' 不存在")
        sys.exit(1)

    df_clean = df[[args.target] + features].dropna()
    X = df_clean[features]
    y = df_clean[args.target]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
    model = LinearRegression()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))

    print(f"📊 回归分析 — 预测={args.target}")
    print("=" * 50)
    print(f"R² 分数: {r2:.4f}")
    print(f"RMSE: {rmse:.2f}")
    print(f"解释: R²>{0.8 if r2 > 0.8 else (0.5 if r2 > 0.5 else 0)}" + 
          "效果不错" if r2 > 0.8 else ("勉强可用" if r2 > 0.5 else "需改进"))
    print("\n回归系数:")
    for feat, coef in zip(features, model.coef_):
        print(f"  {feat}: {coef:.4f}")
    print(f"截距: {model.intercept_:.4f}")

    # 异常偏离识别
    df['预测值'] = model.predict(scaler.transform(X))
    df['残差'] = df[args.target] - df['预测值']
    abnormal = df[np.abs(df['残差']) > 2 * rmse]
    print(f"\n⚠️ 异常偏离 (>2×RMSE): {len(abnormal)} 条")

    with pd.ExcelWriter(args.output) as w:
        pd.DataFrame({'变量': ['截距'] + features, '系数': [model.intercept_] + list(model.coef_)}).to_excel(w, sheet_name='模型参数', index=False)
        abnormal.to_excel(w, sheet_name='异常偏离', index=False)
    print(f"✅ 输出: {args.output}")

if __name__ == '__main__':
    main()
