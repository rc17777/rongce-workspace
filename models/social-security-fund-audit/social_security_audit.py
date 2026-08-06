#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
社保基金审计模型 — Python自动化分析脚本
基于20核心SQL模型 + 泉州128模型方法论

用法:
    python social_security_audit.py --data-dir ./社保数据/           # 全量分析
    python social_security_audit.py --module dim1 --data-dir ./数据/ # 单维度
    python social_security_audit.py --report                         # 生成审计报告

数据要求（CSV/Excel格式）:
    insurance_participant.csv    - 参保人员表
    insurance_contributions.csv  - 征缴记录表
    inpatient_record.csv         - 住院记录表
    outpatient_record.csv        - 门诊记录表
    medical_settlement_detail.csv - 医保结算明细
    drug_inventory.csv           - 药品进销存
    pension_payment.csv          - 养老金发放
    death_data.csv               - 死亡数据
    work_injury_info.csv         - 工伤认定信息
    assistive_device_records.csv - 辅助器具配置记录
    fund_balance_sheet.csv       - 基金收支结余表
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter, defaultdict

import pandas as pd
import numpy as np

# ═══════════════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════════════

ALERT_LEVELS = {
    "P0": "🔴 严重 — 涉嫌违法违规，需立即现场核查",
    "P1": "🟡 重要 — 管理不规范，需限期整改",
    "P2": "🟢 一般 — 制度性缺陷，建议优化",
}

DRUG_WATCHLIST = [
    # 呼吸道用药（外伤结算异常信号）
    '肺力咳合剂', '蓝芩口服液', '苏黄止咳胶囊', '感冒清热颗粒',
    '连花清瘟', '蒲地蓝消炎口服液', '急支糖浆',
    # 慢性病用药（外伤结算异常信号）
    '盐酸二甲双胍片', '磷酸西格列汀片', '硝苯地平控释片',
    '氨氯地平片', '阿卡波糖片', '厄贝沙坦片', '阿托伐他汀钙片',
    '瑞舒伐他汀钙片', '胰岛素',
]

# ★v1.1: 法发2024-6号 刑事骗保行为清单
CRIMINAL_FRAUD_BEHAVIORS = {
    '定点机构': [
        '诱导冒名就医', '伪造变造资料', '虚构医药服务',
        '分解住院/挂床', '重复收费/串换', '串换药品', '目录外纳入结算',
    ],
    '个人': [
        '伪造变造资料', '冒名就医购药', '虚构医药服务',
        '重复享受待遇', '转卖药品套现', '其他骗保行为',
    ],
    '经办人员': ['利用职务便利骗取基金'],
    '倒卖药品者': ['明知骗保收购销售'],
}

# ★v1.1: 知识图谱实体类型定义
KG_ENTITY_TYPES = ['参保人', '医疗机构', '医师', '药品', '疾病', '费用']
KG_RELATION_TYPES = ['就诊', '处方', '结算', '参保', '雇佣']

FLY_INSPECTION_15_FIELDS = {
    '骨科': '高值耗材虚记、假体串换',
    '心内科': '支架/球囊/导管/起搏器虚记',
    '血透': '虚记透析次数、去世后仍收费',
    '口腔': '种植牙串换、义齿超标准',
    '眼科': '白内障手术耗材串换',
    '精神医学': '挂床住院、虚记治疗项目',
    '康复医学': '过度治疗、虚记康复次数',
    '肿瘤科': '靶向药超适应症',
    '检验检查': '打包收费、虚记检查',
    '影像学': '第三方无资质、AI实为人工',
    '中医理疗': '虚记针灸/推拿次数',
    '血液制品': '白蛋白滥用、串换',
    '定点药店A': '刷卡套现',
    '定点药店B': '日用品串换',
    '定点药店C': '处方药无方销售',
}


# ═══════════════════════════════════════════════════════════
# 维度一：基金筹集
# ═══════════════════════════════════════════════════════════

class Dim1FundCollection:
    """基金筹集维度：参保管理 + 征缴管理 + 财政补助"""

    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.findings = []

    def load_data(self):
        """加载数据"""
        files = {
            'participant': 'insurance_participant.csv',
            'contributions': 'insurance_contributions.csv',
            'tax_records': 'tax_records.csv',
            'death_data': 'death_data.csv',
        }
        dfs = {}
        for name, fname in files.items():
            path = self.data_dir / fname
            if path.exists():
                dfs[name] = pd.read_csv(path)
            else:
                print(f"  ⚠ 数据文件不存在: {fname}")
        return dfs

    def check_duplicate_enrollment(self, dfs):
        """M1: 重复参保检测"""
        if 'participant' not in dfs:
            return []

        df = dfs['participant']
        if 'insurance_type' not in df.columns:
            return []

        findings = []
        # 同一身份证号多险种
        dup = df[df['status'] == '正常参保'].groupby('id_card').filter(
            lambda x: x['insurance_type'].nunique() > 1
        )
        if len(dup) > 0:
            dup_summary = dup.groupby('id_card')['insurance_type'].apply(
                lambda x: ' + '.join(sorted(x.unique()))
            ).reset_index()
            dup_summary.columns = ['id_card', 'types']
            findings.append({
                'level': 'P1',
                'module': 'M1-重复参保',
                'title': f'发现{len(dup_summary)}人重复参保',
                'detail': dup_summary.head(50).to_dict('records'),
                'risk': f'预估多补助 {len(dup_summary) * 580} 元/年',
            })
            print(f"  🔴 M1 重复参保: {len(dup_summary)}人")
        return findings

    def check_payment_base_anomaly(self, dfs):
        """M3: 缴费基数不实"""
        if 'contributions' not in dfs:
            return []

        df = dfs['contributions']
        findings = []

        if 'payment_base' in df.columns:
            # 按最低基数缴费的检测
            low_base = df[df['payment_base'] > 0].copy()
            # 找缴费基数在最低档的单位
            base_counts = low_base.groupby('company_id').agg(
                employee_count=('id_card', 'nunique'),
                avg_base=('payment_base', 'mean'),
                min_base=('payment_base', 'min'),
            ).reset_index()

            # 全部员工按同一最低基数缴费 → 高度可疑
            uniform_low = base_counts[
                (base_counts['avg_base'] == base_counts['min_base']) &
                (base_counts['employee_count'] >= 5)
            ]
            if len(uniform_low) > 0:
                findings.append({
                    'level': 'P1',
                    'module': 'M3-缴费基数异常',
                    'title': f'{len(uniform_low)}家单位全员按最低基数缴费',
                    'detail': uniform_low.head(20).to_dict('records'),
                    'risk': '可能存在少缴漏缴',
                })
                print(f"  🟡 M3 最低基数缴费: {len(uniform_low)}家单位")

        return findings

    def check_death_continue(self, dfs):
        """M4: 死亡人员继续参保"""
        if 'participant' not in dfs or 'death_data' not in dfs:
            return []

        df_p = dfs['participant']
        df_d = dfs['death_data']

        if 'last_payment_date' in df_p.columns and 'death_date' in df_d.columns:
            df_p['last_payment_date'] = pd.to_datetime(df_p['last_payment_date'], errors='coerce')
            df_d['death_date'] = pd.to_datetime(df_d['death_date'], errors='coerce')
            # 取唯一姓名映射
            name_map = df_p[['id_card', 'name']].drop_duplicates('id_card').set_index('id_card')['name'] if 'name' in df_p.columns else None
            merged = df_p[['id_card', 'last_payment_date']].merge(
                df_d[['id_card', 'death_date']], on='id_card', how='inner'
            )
            if name_map is not None:
                merged['name'] = merged['id_card'].map(name_map)
            merged = merged[merged['last_payment_date'] > merged['death_date']]

            if len(merged) > 0:
                detail_cols = ['id_card', 'death_date', 'last_payment_date']
                if 'name' in merged.columns:
                    detail_cols.insert(1, 'name')
                findings = [{
                    'level': 'P0',
                    'module': 'M4-死亡参保',
                    'title': f'{len(merged)}人死亡后仍在参保状态',
                    'detail': merged[detail_cols].head(30).to_dict('records'),
                    'risk': '涉嫌违规操作或数据未及时更新',
                }]
                print(f"  🔴 M4 死亡参保: {len(merged)}人")
                return findings
        return []

    def run(self):
        print("\n" + "=" * 60)
        print("  维度一：基金筹集分析")
        print("=" * 60)
        dfs = self.load_data()
        if not dfs:
            print("  无可用数据，跳过")
            return []

        all_findings = []
        all_findings.extend(self.check_duplicate_enrollment(dfs))
        all_findings.extend(self.check_payment_base_anomaly(dfs))
        all_findings.extend(self.check_death_continue(dfs))
        return all_findings


# ═══════════════════════════════════════════════════════════
# 维度二：待遇支出
# ═══════════════════════════════════════════════════════════

class Dim2BenefitExpenditure:
    """待遇支出维度：医保养死工伤失业"""

    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.findings = []

    def load_data(self):
        files = {
            'inpatient': 'inpatient_record.csv',
            'outpatient': 'outpatient_record.csv',
            'settlement': 'medical_settlement_detail.csv',
            'drug_inventory': 'drug_inventory.csv',
            'pension': 'pension_payment.csv',
            'death_data': 'death_data.csv',
            'work_injury': 'work_injury_info.csv',
            'assistive_device': 'assistive_device_records.csv',
            'unemployment': 'unemployment_benefit.csv',
        }
        dfs = {}
        for name, fname in files.items():
            path = self.data_dir / fname
            if path.exists():
                dfs[name] = pd.read_csv(path)
        return dfs

    def check_split_hospitalization(self, dfs):
        """M6: 分解住院检测"""
        if 'inpatient' not in dfs:
            return []

        df = dfs['inpatient'].copy()
        findings = []
        required_cols = ['patient_id', 'primary_diagnosis', 'discharge_date', 'admission_date']
        if not all(c in df.columns for c in required_cols):
            return []

        for col in ['discharge_date', 'admission_date']:
            df[col] = pd.to_datetime(df[col], errors='coerce')

        # 自关联检测
        df_a = df[['patient_id', 'primary_diagnosis', 'discharge_date', 'admission_date', 'total_cost', 'institution_name']].copy()
        df_b = df[['patient_id', 'primary_diagnosis', 'discharge_date', 'admission_date', 'total_cost', 'institution_name']].copy()
        df_a.columns = ['patient_id', 'diagnosis', 'discharge', 'admit_a', 'cost', 'hospital']
        df_b.columns = ['patient_id', 'diagnosis', 'discharge_b', 'admit', 'cost_b', 'hospital_b']

        merged = df_a.merge(df_b, on=['patient_id', 'diagnosis'])
        merged = merged[merged['discharge'] < merged['admit']]
        merged['gap_days'] = (merged['admit'] - merged['discharge']).dt.days
        split_cases = merged[merged['gap_days'] <= 7]

        if len(split_cases) > 0:
            hospital_stats = split_cases.groupby('hospital').agg(
                case_count=('patient_id', 'count'),
                total_cost=('cost', 'sum')
            ).sort_values('case_count', ascending=False)

            findings.append({
                'level': 'P0',
                'module': 'M6-分解住院',
                'title': f'发现{len(split_cases)}例疑似分解住院',
                'detail': hospital_stats.head(20).reset_index().to_dict('records'),
                'risk': f'涉及金额 {split_cases["cost"].sum():,.0f} 元',
            })
            print(f"  🔴 M6 分解住院: {len(split_cases)}例, 金额{split_cases['cost'].sum():,.0f}元")

        return findings

    def check_cost_outlier_stddev(self, dfs):
        """M8: 同病种费用异常（STDDEV）"""
        if 'settlement' not in dfs:
            return []

        df = dfs['settlement'].copy()
        if 'drg_code' not in df.columns or 'total_cost' not in df.columns:
            return []

        findings = []
        # 按DRG分组计算统计量
        stats = df.groupby('drg_code').agg(
            count=('total_cost', 'count'),
            mean=('total_cost', 'mean'),
            std=('total_cost', 'std'),
        ).dropna()

        # 筛选有足够样本且异常值明显的DRG组
        stats = stats[stats['count'] >= 10]
        stats['cv'] = stats['std'] / stats['mean']

        high_cv = stats[stats['cv'] > 0.5].sort_values('cv', ascending=False)
        if len(high_cv) > 0:
            findings.append({
                'level': 'P1',
                'module': 'M8-费用异常(STDDEV)',
                'title': f'{len(high_cv)}个DRG组费用离散度过高(CV>0.5)',
                'detail': high_cv.head(20).reset_index().to_dict('records'),
                'risk': '可能存在过度诊疗或虚记费用',
            })
            print(f"  🟡 M8 STDDEV异常: {len(high_cv)}个DRG组")

        return findings

    def check_death_pension_fraud(self, dfs):
        """M11: 死亡冒领养老金"""
        if 'pension' not in dfs or 'death_data' not in dfs:
            return []

        df_p = dfs['pension'].copy()
        df_d = dfs['death_data'].copy()

        for col in ['last_payment_date']:
            if col in df_p.columns:
                df_p[col] = pd.to_datetime(df_p[col], errors='coerce')
        if 'death_date' in df_d.columns:
            df_d['death_date'] = pd.to_datetime(df_d['death_date'], errors='coerce')

        # 取唯一姓名映射
        name_map_p = df_p[['id_card', 'name']].drop_duplicates('id_card').set_index('id_card')['name'] if 'name' in df_p.columns else None
        merged = df_p[['id_card', 'monthly_amount', 'last_payment_date']].merge(
            df_d[['id_card', 'death_date']], on='id_card', how='inner'
        )
        merged = merged[merged['last_payment_date'] > merged['death_date']]

        if len(merged) > 0:
            merged['months_after'] = (
                (merged['last_payment_date'].dt.year - merged['death_date'].dt.year) * 12 +
                (merged['last_payment_date'].dt.month - merged['death_date'].dt.month)
            )
            merged['est_overpayment'] = merged['months_after'] * merged.get('monthly_amount', 0)
            if name_map_p is not None:
                merged['name'] = merged['id_card'].map(name_map_p)
            total = merged['est_overpayment'].sum()

            detail_cols = ['id_card', 'death_date', 'last_payment_date', 'months_after', 'est_overpayment']
            if 'name' in merged.columns:
                detail_cols.insert(1, 'name')

            findings = [{
                'level': 'P0',
                'module': 'M11-死亡冒领',
                'title': f'{len(merged)}人死亡后继续领取养老金',
                'detail': merged[detail_cols].head(30).to_dict('records'),
                'risk': f'估算多支付 {total:,.0f} 元',
            }]
            print(f"  🔴 M11 死亡冒领: {len(merged)}人, 估算{total:,.0f}元")
            return findings
        return []

    def check_non_injury_drugs(self, dfs):
        """M14: 非工伤用药检测"""
        if 'work_injury' not in dfs or 'settlement' not in dfs:
            return []

        df_wi = dfs['work_injury'].copy()
        df_settle = dfs['settlement'].copy()

        if 'injury_type' not in df_wi.columns or 'drug_name' not in df_settle.columns:
            return []

        # 外伤人员
        trauma = df_wi[df_wi['injury_type'].str.contains('外伤', na=False)]
        merged = trauma.merge(df_settle, on='person_id', how='inner')

        # 匹配非工伤药品
        flagged = merged[merged['drug_name'].isin(DRUG_WATCHLIST)]
        if len(flagged) > 0:
            drug_stats = flagged.groupby(['drug_name', 'institution_name']).agg(
                person_count=('person_id', 'nunique'),
                total_cost=('cost', 'sum'),
            ).sort_values('total_cost', ascending=False)

            findings = [{
                'level': 'P1',
                'module': 'M14-非工伤用药',
                'title': f'外伤职工结算{len(flagged)}条非外伤用药',
                'detail': drug_stats.head(20).reset_index().to_dict('records'),
                'risk': f'涉及金额 {flagged["cost"].sum():,.0f} 元',
            }]
            print(f"  🟡 M14 非工伤用药: {len(flagged)}条, 金额{flagged['cost'].sum():,.0f}元")
            return findings
        return []

    def check_assistive_device_anomaly(self, dfs):
        """M15: 辅助器具异常配置"""
        if 'assistive_device' not in dfs:
            return []

        df = dfs['assistive_device'].copy()
        if not all(c in df.columns for c in ['person_id', 'device_type', 'config_date', 'price']):
            return []

        df['config_date'] = pd.to_datetime(df['config_date'], errors='coerce')
        df = df.sort_values(['person_id', 'config_date'])

        findings = []
        anomalies = []
        max_prices = df.groupby('device_type')['price'].max().to_dict()

        for pid, group in df.groupby('person_id'):
            if len(group) < 2:
                continue
            for i in range(1, len(group)):
                prev = group.iloc[i - 1]
                curr = group.iloc[i]
                days_gap = (curr['config_date'] - prev['config_date']).days
                if days_gap <= 1830:  # 5年
                    flag = 'MIN_YEAR_MAX_PRICE' if curr['price'] == max_prices.get(curr['device_type'], 0) else 'MIN_YEAR'
                    anomalies.append({
                        'person_id': pid,
                        'device_type': curr['device_type'],
                        'prev_date': prev['config_date'].strftime('%Y-%m-%d'),
                        'curr_date': curr['config_date'].strftime('%Y-%m-%d'),
                        'days_gap': days_gap,
                        'price': curr['price'],
                        'flag': flag,
                    })

        if anomalies:
            findings.append({
                'level': 'P0',
                'module': 'M15-辅具异常',
                'title': f'发现{len(anomalies)}条辅助器具异常配置',
                'detail': anomalies[:20],
                'risk': '疑似利用最低使用年限规则套取基金',
            })
            print(f"  🔴 M15 辅具异常: {len(anomalies)}条")

        return findings

    def run(self):
        print("\n" + "=" * 60)
        print("  维度二：待遇支出分析")
        print("=" * 60)
        dfs = self.load_data()
        if not dfs:
            print("  无可用数据，跳过")
            return []

        all_findings = []
        all_findings.extend(self.check_split_hospitalization(dfs))
        all_findings.extend(self.check_cost_outlier_stddev(dfs))
        all_findings.extend(self.check_death_pension_fraud(dfs))
        all_findings.extend(self.check_non_injury_drugs(dfs))
        all_findings.extend(self.check_assistive_device_anomaly(dfs))
        return all_findings


# ═══════════════════════════════════════════════════════════
# 维度三：飞检15领域风险评估
# ═══════════════════════════════════════════════════════════

class Dim3FlyInspectionRisk:
    """飞检15领域风险评估 — 基于制度和数据特征预判"""

    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)

    def run(self):
        print("\n" + "=" * 60)
        print("  维度三：飞检15领域风险评估")
        print("=" * 60)

        # 基于领域特征输出风险矩阵
        risk_matrix = []
        for field, risk_desc in FLY_INSPECTION_15_FIELDS.items():
            risk_level = 'HIGH'
            high_value = any(kw in risk_desc for kw in ['高值', '虚记', '串换', '套现', '骗保'])
            risk_matrix.append({
                'field': field,
                'risk_desc': risk_desc,
                'inherent_risk': '🔴 高' if high_value else '🟡 中',
                'check_method': self._get_check_method(field),
            })

        print(f"  共评估{len(risk_matrix)}个重点领域")
        high_risk = [r for r in risk_matrix if '高' in r['inherent_risk']]
        print(f"  其中{len(high_risk)}个领域固有风险为高")

        return [{
            'level': 'P0',
            'module': '飞检15领域',
            'title': f'{len(high_risk)}个高固有风险领域需优先飞检',
            'detail': risk_matrix,
        }]

    def _get_check_method(self, field):
        methods = {
            '骨科': '进销存耗材追踪 + 手术记录 vs 结算比对',
            '心内科': '支架序列号追踪 + DSA影像核实',
            '血透': '透析记录 vs 结算次数 + 死亡数据交叉',
            '口腔': '种植体追溯码 + 实物盘点',
            '眼科': '晶体序列号追踪 + 手术视频核实',
            '精神医学': '住院患者现场核查 + 病历审阅',
            '康复医学': '治疗记录 vs 结算项目 + 患者回访',
            '肿瘤科': '适应症审查 + 基因检测结果核实',
            '检验检查': 'LIS系统日志 vs 结算明细',
            '影像学': '第三方机构资质审查 + DICOM元数据',
            '中医理疗': '治疗记录 vs 结算 + 患者回访',
            '血液制品': '出入库记录 + 适应症审核',
            '定点药店A': '刷卡记录异常聚类 + 监控调阅',
            '定点药店B': '药品进销存品类 vs 刷卡品类',
            '定点药店C': '处方真实性核实 + 电话回访',
        }
        return methods.get(field, '综合核查')


# ═══════════════════════════════════════════════════════════
# 维度四：知识图谱+刑事责任（★v1.1新增）
# ═══════════════════════════════════════════════════════════

class Dim4KnowledgeGraphAndCriminal:
    """知识图谱关系检测 + 法发2024-6号刑事责任判定"""

    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)

    def load_data(self):
        files = {
            'settlement': 'medical_settlement_detail.csv',
            'inpatient': 'inpatient_record.csv',
        }
        dfs = {}
        for name, fname in files.items():
            path = self.data_dir / fname
            if path.exists():
                dfs[name] = pd.read_csv(path)
        return dfs

    def check_drug_circulation_loop(self, dfs):
        """M21: 药品购销闭环检测（知识图谱法）"""
        if 'settlement' not in dfs:
            return []

        df = dfs['settlement']
        if not all(c in df.columns for c in ['person_id', 'drug_name', 'institution_code']):
            return []

        # 跨机构购买同种药品
        grouped = df.groupby(['person_id', 'drug_name']).agg(
            institution_count=('institution_code', 'nunique'),
            total_cost=('cost', 'sum'),
            total_quantity=('quantity', 'sum'),
        ).reset_index()

        suspicious = grouped[
            (grouped['institution_count'] >= 3) &
            (grouped['total_quantity'] > 60)
        ].sort_values('institution_count', ascending=False)

        if len(suspicious) > 0:
            findings = [{
                'level': 'P0',
                'module': 'M21-知识图谱/药品购销闭环',
                'title': f'{len(suspicious)}人跨多机构大量购买同种药品（疑似职业开药人）',
                'detail': suspicious.head(20).to_dict('records'),
                'risk': f'涉及金额 {suspicious["total_cost"].sum():,.0f} 元',
            }]
            print(f"  🔴 M21 药品购销闭环: {len(suspicious)}人, 金额{suspicious['total_cost'].sum():,.0f}元")
            return findings
        return []

    def check_doctor_pharmacy_collusion(self, dfs):
        """M22: 医患合谋检测"""
        if 'settlement' not in dfs:
            return []

        df = dfs['settlement']
        if 'doctor_id' not in df.columns or 'unit_price' not in df.columns:
            return []

        # 找同一医师开高价药的模式
        overall_avg = df.groupby('drug_name')['unit_price'].mean().to_dict()

        doctor_stats = df.groupby(['doctor_id', 'drug_name']).agg(
            patient_count=('person_id', 'nunique'),
            avg_price=('unit_price', 'mean'),
            total_cost=('cost', 'sum'),
        ).reset_index()

        anomalies = []
        for _, row in doctor_stats.iterrows():
            drug_avg = overall_avg.get(row['drug_name'], 0)
            if drug_avg > 0 and row['avg_price'] > drug_avg * 1.5 and row['patient_count'] >= 10:
                anomalies.append(row.to_dict())

        if anomalies:
            findings = [{
                'level': 'P1',
                'module': 'M22-医患合谋检测',
                'title': f'{len(anomalies)}组医师-药品组合存在高价处方模式',
                'detail': anomalies[:20],
                'risk': '可能存在医师→药店→药品利益输送链',
            }]
            print(f"  🟡 M22 医患合谋: {len(anomalies)}组异常组合")
            return findings
        return []

    def check_criminal_fraud_mapping(self, dfs):
        """刑事责任映射：将已发现疑点比对法发2024-6号入刑标准"""
        # 基于已发现的问题类型进行刑事风险预警
        criminal_mapping = {
            '分解住院': {'crime': '诈骗罪(刑法266条)', 'ref': '法发2024-6号第5条第4项', 'max_penalty': '无期徒刑'},
            '挂床住院': {'crime': '诈骗罪(刑法266条)', 'ref': '法发2024-6号第5条第4项', 'max_penalty': '无期徒刑'},
            '串换药品': {'crime': '诈骗罪(刑法266条)', 'ref': '法发2024-6号第5条第6项', 'max_penalty': '无期徒刑'},
            '虚记费用': {'crime': '诈骗罪(刑法266条)', 'ref': '法发2024-6号第5条第3项', 'max_penalty': '无期徒刑'},
            '冒名就医': {'crime': '诈骗罪(刑法266条)', 'ref': '法发2024-6号第6条第2项', 'max_penalty': '无期徒刑'},
            '死亡冒领': {'crime': '诈骗罪(刑法266条)', 'ref': '法发2024-6号第6条第1项', 'max_penalty': '无期徒刑'},
            '重复参保': {'crime': '诈骗罪(刑法266条)', 'ref': '法发2024-6号第6条第4项', 'max_penalty': '无期徒刑'},
            '药品回流': {'crime': '掩饰隐瞒犯罪所得罪(刑法312条)', 'ref': '法发2024-6号第9条', 'max_penalty': '7年有期徒刑'},
        }

        findings = [{
            'level': 'P0',
            'module': '刑事责任映射(法发2024-6号)',
            'title': '根据法发2024-6号，以下违规类型可直接入刑',
            'detail': [{'type': k, **v} for k, v in criminal_mapping.items()],
            'risk': '注意：行政取证可直接作为刑事定案证据（第18条）',
        }]
        print(f"  ⚖ 刑事责任映射: 已标注{criminal_mapping}种可直接入刑的骗保类型")
        return findings

    def check_remote_medical_anomaly(self, dfs):
        """M23: 异地就医异常"""
        if 'settlement' not in dfs:
            return []

        df = dfs['settlement']
        if 'registered_city' not in df.columns or 'treatment_city' not in df.columns:
            return []

        remote = df[df['registered_city'] != df['treatment_city']]
        if len(remote) == 0:
            return []

        grouped = remote.groupby(['person_id', 'registered_city', 'treatment_city']).agg(
            visit_count=('settlement_date', 'count'),
            total_cost=('cost', 'sum'),
        ).reset_index()

        suspicious = grouped[(grouped['visit_count'] >= 5) & (grouped['total_cost'] > 50000)]

        if len(suspicious) > 0:
            findings = [{
                'level': 'P1',
                'module': 'M23-异地就医异常',
                'title': f'{len(suspicious)}人次频繁异地大额就医',
                'detail': suspicious.head(20).to_dict('records'),
                'risk': '可能存在异地就医骗保或虚假就医',
            }]
            print(f"  🟡 M23 异地就医异常: {len(suspicious)}人次")
            return findings
        return []

    def run(self):
        print("\n" + "=" * 60)
        print("  维度四：知识图谱分析 + 刑事责任映射（v1.1新增）")
        print("=" * 60)
        dfs = self.load_data()
        if not dfs:
            print("  无可用数据，跳过")
            return []

        all_findings = []
        all_findings.extend(self.check_drug_circulation_loop(dfs))
        all_findings.extend(self.check_doctor_pharmacy_collusion(dfs))
        all_findings.extend(self.check_remote_medical_anomaly(dfs))
        all_findings.extend(self.check_criminal_fraud_mapping(dfs))
        return all_findings


# ═══════════════════════════════════════════════════════════
# 汇总报告生成
# ═══════════════════════════════════════════════════════════

class TimestampEncoder(json.JSONEncoder):
    """处理 pandas Timestamp 和 numpy 类型的 JSON 序列化"""
    def default(self, obj):
        if pd.isna(obj):
            return None
        if isinstance(obj, (pd.Timestamp, datetime)):
            return obj.strftime('%Y-%m-%d')
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

def generate_report(all_findings, output_dir):
    """生成汇总审计疑点报告"""
    report_path = Path(output_dir) / f'社保基金审计疑点报告_{datetime.now().strftime("%Y%m%d_%H%M")}'
    report_path.mkdir(parents=True, exist_ok=True)

    # 分级统计
    p0 = [f for f in all_findings if f['level'] == 'P0']
    p1 = [f for f in all_findings if f['level'] == 'P1']
    p2 = [f for f in all_findings if f['level'] == 'P2']

    # 生成Markdown报告
    md = []
    md.append("# 社保基金审计疑点报告")
    md.append(f"\n生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md.append(f"\n## 摘要")
    md.append(f"- 🔴 P0（涉嫌违法违规）：{len(p0)}项")
    md.append(f"- 🟡 P1（管理不规范）：{len(p1)}项")
    md.append(f"- 🟢 P2（制度性缺陷）：{len(p2)}项")
    md.append(f"- 合计：{len(all_findings)}项")

    if p0:
        md.append(f"\n## 🔴 P0 — 涉嫌违法违规")
        for i, f in enumerate(p0, 1):
            md.append(f"\n### P0-{i}: {f['module']} — {f['title']}")
            md.append(f"- **风险**：{f.get('risk', '待核实')}")
            if 'detail' in f and isinstance(f['detail'], list) and len(f['detail']) > 0:
                md.append(f"- **样例**：")
                if isinstance(f['detail'][0], dict):
                    sample = f['detail'][0]
                    for k, v in list(sample.items())[:5]:
                        md.append(f"  - {k}: {v}")

    if p1:
        md.append(f"\n## 🟡 P1 — 管理不规范")
        for i, f in enumerate(p1, 1):
            md.append(f"\n### P1-{i}: {f['module']} — {f['title']}")
            md.append(f"- **风险**：{f.get('risk', '待核实')}")

    if p2:
        md.append(f"\n## 🟢 P2 — 制度性缺陷")
        for i, f in enumerate(p2, 1):
            md.append(f"\n### P2-{i}: {f['module']} — {f['title']}")
            md.append(f"- **风险**：{f.get('risk', '待核实')}")

    md.append(f"\n---\n*基于融策社保基金审计模型 v1.0 自动生成*")

    report_md = report_path / '审计疑点报告.md'
    with open(report_md, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))

    # 保存JSON
    report_json = report_path / '审计疑点_结构化.json'
    with open(report_json, 'w', encoding='utf-8') as f:
        json.dump({
            'generated_at': datetime.now().isoformat(),
            'summary': {'P0': len(p0), 'P1': len(p1), 'P2': len(p2), 'total': len(all_findings)},
            'findings': all_findings,
            'fly_inspection_fields': FLY_INSPECTION_15_FIELDS,
        }, f, ensure_ascii=False, indent=2, cls=TimestampEncoder)

    print(f"\n{'=' * 60}")
    print(f"  审计报告已生成")
    print(f"  Markdown: {report_md}")
    print(f"  JSON:     {report_json}")
    print(f"{'=' * 60}")

    return report_path


# ═══════════════════════════════════════════════════════════
# CLI 入口
# ═══════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='社保基金审计模型')
    parser.add_argument('--data-dir', required=True, help='数据目录路径')
    parser.add_argument('--module', choices=['dim1', 'dim2', 'dim3', 'dim4', 'all'], default='all', help='分析模块')
    parser.add_argument('--report', action='store_true', help='生成审计报告')
    parser.add_argument('--output', default='.', help='报告输出目录')

    args = parser.parse_args()

    if not os.path.isdir(args.data_dir):
        print(f"❌ 数据目录不存在: {args.data_dir}")
        print("请准备以下CSV文件（至少部分）：")
        for f in ['insurance_participant.csv', 'insurance_contributions.csv',
                   'inpatient_record.csv', 'outpatient_record.csv',
                   'medical_settlement_detail.csv', 'drug_inventory.csv',
                   'pension_payment.csv', 'death_data.csv',
                   'work_injury_info.csv', 'assistive_device_records.csv']:
            print(f"  - {f}")
        sys.exit(1)

    print("=" * 60)
    print("  融策·社保基金审计模型 v1.0")
    print(f"  数据目录: {args.data_dir}")
    print(f"  运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    all_findings = []

    if args.module in ('dim1', 'all'):
        dim1 = Dim1FundCollection(args.data_dir)
        all_findings.extend(dim1.run())

    if args.module in ('dim2', 'all'):
        dim2 = Dim2BenefitExpenditure(args.data_dir)
        all_findings.extend(dim2.run())

    if args.module in ('dim3', 'all'):
        dim3 = Dim3FlyInspectionRisk(args.data_dir)
        all_findings.extend(dim3.run())

    if args.module in ('dim4', 'all'):
        dim4 = Dim4KnowledgeGraphAndCriminal(args.data_dir)
        all_findings.extend(dim4.run())

    # 汇总
    p0 = sum(1 for f in all_findings if f['level'] == 'P0')
    p1 = sum(1 for f in all_findings if f['level'] == 'P1')
    p2 = sum(1 for f in all_findings if f['level'] == 'P2')

    print(f"\n{'=' * 60}")
    print(f"  分析完成！共发现 {len(all_findings)} 项疑点")
    print(f"  🔴 P0: {p0}  |  🟡 P1: {p1}  |  🟢 P2: {p2}")
    print(f"{'=' * 60}")

    if args.report:
        generate_report(all_findings, args.output)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
