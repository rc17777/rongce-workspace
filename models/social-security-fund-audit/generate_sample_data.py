#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
社保基金审计模型 — 示例数据生成器
用于测试模型流程，生成模拟的社保基金数据

用法:
    python generate_sample_data.py --output ./sample_data/
"""

import os
import argparse
from pathlib import Path
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42)

def generate_participant(n=5000):
    """生成参保人员表"""
    insurance_types = ['职工医保', '居民医保', '职工养老', '居民养老', '工伤', '失业']
    statuses = ['正常参保'] * 90 + ['暂停参保'] * 5 + ['终止参保'] * 5

    data = []
    for i in range(n):
        data.append({
            'id_card': f'5101{str(i).zfill(14)}',
            'name': f'参保人{i:04d}',
            'insurance_type': np.random.choice(insurance_types),
            'status': np.random.choice(statuses),
            'company_id': f'COMP{np.random.randint(1, 200):04d}',
            'company_name': f'单位{np.random.randint(1, 200):03d}',
            'last_payment_date': (datetime.now() - timedelta(days=np.random.randint(0, 365))).strftime('%Y-%m-%d'),
        })
    # 故意制造重复参保
    for i in range(30):
        data.append({
            'id_card': data[i]['id_card'],
            'name': data[i]['name'],
            'insurance_type': '居民医保' if data[i]['insurance_type'] == '职工医保' else '职工医保',
            'status': '正常参保',
            'company_id': data[i]['company_id'],
            'company_name': data[i]['company_name'],
            'last_payment_date': data[i]['last_payment_date'],
        })

    return pd.DataFrame(data)


def generate_contributions(n=3000):
    """生成征缴记录"""
    data = []
    for i in range(n):
        base = np.random.choice([3493, 5000, 8000, 12000, 20000, 30000])  # 四川最低基数3493
        data.append({
            'id_card': f'5101{str(np.random.randint(0, 5000)).zfill(14)}',
            'company_id': f'COMP{np.random.randint(1, 200):04d}',
            'company_name': f'单位{np.random.randint(1, 200):03d}',
            'payment_base': base,
            'payment_amount': base * 0.28,
            'period': f'{np.random.randint(2024, 2026)}-{np.random.randint(1, 13):02d}',
            'payment_type': np.random.choice(['正常缴纳', '正常缴纳', '正常缴纳', '一次性补缴']),
        })
    return pd.DataFrame(data)


def generate_inpatient(n=2000):
    """生成住院记录（含故意制造的分解住院）"""
    drgs = ['GD25', 'RC19', 'FS34', 'ET15', 'BR21', 'GJ11', 'HC35', 'IA18']
    diagnoses = ['阑尾炎', '肺炎', '骨折', '白内障', '冠心病', '糖尿病', '脑梗', '肾结石']
    data = []

    for i in range(n):
        admit = datetime.now() - timedelta(days=np.random.randint(0, 730))
        los = np.random.randint(1, 30)
        discharge = admit + timedelta(days=los)
        drg = np.random.choice(drgs)
        dx = diagnoses[drgs.index(drg)]

        data.append({
            'patient_id': f'P{np.random.randint(0, 3000):06d}',
            'patient_name': f'患者{i:04d}',
            'admission_date': admit.strftime('%Y-%m-%d'),
            'discharge_date': discharge.strftime('%Y-%m-%d'),
            'primary_diagnosis': dx,
            'drg_code': drg,
            'total_cost': np.random.lognormal(9, 0.8),
            'institution_name': f'医院{chr(65+np.random.randint(0, 20))}',
            'institution_code': f'HOSP{np.random.randint(1, 30):03d}',
        })

    # 故意制造分解住院
    for i in range(30):
        base = data[np.random.randint(0, n)]
        new_discharge = datetime.strptime(base['discharge_date'], '%Y-%m-%d')
        new_admit = new_discharge + timedelta(days=np.random.randint(0, 6))
        data.append({
            'patient_id': base['patient_id'],
            'patient_name': base['patient_name'],
            'admission_date': new_admit.strftime('%Y-%m-%d'),
            'discharge_date': (new_admit + timedelta(days=np.random.randint(3, 15))).strftime('%Y-%m-%d'),
            'primary_diagnosis': base['primary_diagnosis'],
            'drg_code': base['drg_code'],
            'total_cost': np.random.lognormal(9, 0.6),
            'institution_name': base['institution_name'],
            'institution_code': base['institution_code'],
        })

    return pd.DataFrame(data)


def generate_settlement(n=5000):
    """生成医保结算明细"""
    drugs = [
        '阿莫西林胶囊', '盐酸二甲双胍片', '硝苯地平控释片', '肺力咳合剂',
        '蓝芩口服液', '苏黄止咳胶囊', '阿托伐他汀钙片', '厄贝沙坦片',
        '氯化钠注射液', '头孢呋辛钠', '胰岛素注射液', '氨氯地平片',
        '奥美拉唑', '阿卡波糖片', '磷酸西格列汀片', '感冒清热颗粒',
    ]
    categories = {
        '阿莫西林胶囊': '抗生素', '盐酸二甲双胍片': '慢性病用药',
        '硝苯地平控释片': '慢性病用药', '肺力咳合剂': '呼吸系统用药',
        '蓝芩口服液': '呼吸系统用药', '苏黄止咳胶囊': '呼吸系统用药',
        '阿托伐他汀钙片': '慢性病用药', '厄贝沙坦片': '慢性病用药',
        '氯化钠注射液': '输液', '头孢呋辛钠': '抗生素',
        '胰岛素注射液': '慢性病用药', '氨氯地平片': '慢性病用药',
        '奥美拉唑': '消化系统', '阿卡波糖片': '慢性病用药',
        '磷酸西格列汀片': '慢性病用药', '感冒清热颗粒': '呼吸系统用药',
    }

    data = []
    for i in range(n):
        drug = np.random.choice(drugs)
        person_id = f'P{np.random.randint(0, 3000):06d}'
        data.append({
            'person_id': person_id,
            'patient_name': f'患者{np.random.randint(0, 3000):04d}',
            'drug_name': drug,
            'drug_code': f'YP{hash(drug) % 10000:04d}',
            'drug_category': categories[drug],
            'quantity': np.random.randint(1, 10),
            'unit_price': np.random.uniform(5, 500),
            'total_cost': np.random.uniform(10, 3000),
            'cost': np.random.uniform(10, 3000),
            'settlement_date': (datetime.now() - timedelta(days=np.random.randint(0, 365))).strftime('%Y-%m-%d'),
            'institution_name': f'医院{chr(65+np.random.randint(0, 20))}',
            'institution_code': f'HOSP{np.random.randint(1, 30):03d}',
            'drg_code': np.random.choice(['GD25', 'RC19', 'FS34', 'ET15', None]),
            'item_category': np.random.choice(['药品', '检查', '检验', '治疗']),
            'item_code': f'XM{np.random.randint(1000, 9999)}',
            'item_name': drug,
        })
    return pd.DataFrame(data)


def generate_death_data(n=100):
    """生成死亡数据"""
    data = []
    for i in range(n):
        death_date = datetime.now() - timedelta(days=np.random.randint(0, 1095))
        data.append({
            'id_card': f'5101{str(np.random.randint(0, 5000)).zfill(14)}',
            'name': f'已故人员{i:03d}',
            'death_date': death_date.strftime('%Y-%m-%d'),
            'death_cause': np.random.choice(['疾病', '意外', '自然死亡']),
        })
    return pd.DataFrame(data)


def generate_pension(n=1000):
    """生成养老金发放记录"""
    data = []
    for i in range(n):
        last_pay = datetime.now() - timedelta(days=np.random.randint(0, 90))
        data.append({
            'id_card': f'5101{str(np.random.randint(0, 5000)).zfill(14)}',
            'name': f'退休人员{i:04d}',
            'pension_type': np.random.choice(['职工养老', '居民养老']),
            'monthly_amount': np.random.choice([1800, 2500, 3500, 5000, 8000]),
            'last_payment_date': last_pay.strftime('%Y-%m-%d'),
        })
    # 故意制造重复领取
    for i in range(15):
        data.append({
            'id_card': data[i]['id_card'],
            'name': data[i]['name'],
            'pension_type': '居民养老' if data[i]['pension_type'] == '职工养老' else '职工养老',
            'monthly_amount': np.random.choice([300, 500, 800]),
            'last_payment_date': data[i]['last_payment_date'],
        })
    return pd.DataFrame(data)


def generate_work_injury(n=200):
    """生成工伤认定信息"""
    data = []
    for i in range(n):
        data.append({
            'person_id': f'P{np.random.randint(0, 3000):06d}',
            'name': f'工伤人员{i:03d}',
            'injury_type': np.random.choice(['外伤-骨折', '外伤-烧伤', '职业病-尘肺', '上下班交通事故', '工伤-其他']),
            'injury_date': (datetime.now() - timedelta(days=np.random.randint(30, 730))).strftime('%Y-%m-%d'),
        })
    return pd.DataFrame(data)


def generate_assistive_device(n=150):
    """生成辅助器具配置记录"""
    data = []
    for i in range(n):
        config_date = datetime.now() - timedelta(days=np.random.randint(0, 2190))
        data.append({
            'person_id': f'P{np.random.randint(0, 3000):06d}',
            'person_name': f'配置人{i:03d}',
            'device_type': np.random.choice(['制氧机', '轮椅', '假肢', '矫形器', '助听器']),
            'device_model': f'型号{np.random.randint(1, 10)}',
            'config_date': config_date.strftime('%Y-%m-%d'),
            'price': np.random.choice([3000, 5000, 8000, 12000, 20000]),
        })
    # 故意制造异常：刚满5年就按最高价更换
    for i in range(15):
        config_date = datetime.now() - timedelta(days=np.random.randint(1820, 1830))
        data.append({
            'person_id': f'P{np.random.randint(0, 500):06d}',
            'person_name': f'异常配置人{i:02d}',
            'device_type': '制氧机',
            'device_model': '型号MAX',
            'config_date': config_date.strftime('%Y-%m-%d'),
            'price': 20000,
        })
    return pd.DataFrame(data)


def main():
    parser = argparse.ArgumentParser(description='社保基金审计模型-示例数据生成')
    parser.add_argument('--output', default='./sample_data', help='输出目录')
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("生成示例社保基金数据...")

    datasets = {
        'insurance_participant.csv': generate_participant(5000),
        'insurance_contributions.csv': generate_contributions(3000),
        'inpatient_record.csv': generate_inpatient(2000),
        'outpatient_record.csv': generate_inpatient(500),  # 复用结构
        'medical_settlement_detail.csv': generate_settlement(5000),
        'pension_payment.csv': generate_pension(1000),
        'death_data.csv': generate_death_data(100),
        'work_injury_info.csv': generate_work_injury(200),
        'assistive_device_records.csv': generate_assistive_device(150),
    }

    for fname, df in datasets.items():
        path = output_dir / fname
        df.to_csv(path, index=False, encoding='utf-8-sig')
        print(f"  ✓ {fname} ({len(df)} 行)")

    print(f"\n数据已生成到: {output_dir.absolute()}")
    print(f"\n运行分析:")
    print(f"  python social_security_audit.py --data-dir {output_dir} --report")


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
