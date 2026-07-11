"""
审计管道引擎 — 配置驱动的多模型审计检测框架

核心理念：实施方案产出场景配置，管道引擎按配置跑模型。
新项目只写 config，不改 engine。

用法：
    python audit_pipeline.py --config profiles/财务收支审计.yaml --data ./project_data/
"""

import pandas as pd
import numpy as np
import yaml
import json
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable

# ============================================================
# 配置结构定义
# ============================================================

@dataclass
class ModelConfig:
    """单个模型的配置"""
    id: str
    name: str
    enabled: bool = True
    weight: float = 1.0          # 综合风险评分中的权重
    threshold: Dict = field(default_factory=dict)  # 模型专属阈值
    rules: List[Dict] = field(default_factory=list)  # 规则列表
    features: List[str] = field(default_factory=list)  # 需要提取的特征

@dataclass
class ScenarioConfig:
    """场景配置（一个审计项目的模型组合）"""
    name: str
    description: str
    audit_type: str
    data_requirements: Dict = field(default_factory=dict)
    models: List[ModelConfig] = field(default_factory=list)
    risk_mapping: Dict = field(default_factory=dict)  # 风险等级→行动


# ============================================================
# 第一层：数据标准化
# ============================================================

class DataStandardizer:
    """将各种来源的原始数据拍成标准格式"""
    
    # 标准凭证 Schema
    VOUCHER_SCHEMA = {
        '凭证编号':    {'type': 'str',  'required': True},
        '凭证日期':    {'type': 'date', 'required': True},
        '摘要':        {'type': 'str',  'required': True},
        '科目代码':    {'type': 'str',  'required': True},
        '科目名称':    {'type': 'str',  'required': True},
        '借方金额':    {'type': 'num',  'required': True,  'default': 0},
        '贷方金额':    {'type': 'num',  'required': True,  'default': 0},
        '对方科目':    {'type': 'str',  'required': False},
        '附件张数':    {'type': 'int',  'required': False, 'default': 0},
        '制单人':      {'type': 'str',  'required': False},
        '审核人':      {'type': 'str',  'required': False},
        '记账人':      {'type': 'str',  'required': False},
        '供应商':      {'type': 'str',  'required': False},
        '合同编号':    {'type': 'str',  'required': False},
        '预算项目':    {'type': 'str',  'required': False},
    }
    
    @classmethod
    def standardize(cls, df: pd.DataFrame, source_type: str = '序时账') -> pd.DataFrame:
        """标准化入口"""
        df = df.copy()
        
        # 列名映射（常见导出的中文列名 → 标准列名）
        COLUMN_MAP = {
            '凭证号': '凭证编号', '记-': '凭证编号',
            '日期': '凭证日期', '记账日期': '凭证日期', '制单日期': '凭证日期',
            '借方': '借方金额', '借方金额(元)': '借方金额', 'debit': '借方金额',
            '贷方': '贷方金额', '贷方金额(元)': '贷方金额', 'credit': '贷方金额',
            '会计科目': '科目名称', 'account_name': '科目名称',
            '科目编码': '科目代码', '科目号': '科目代码', 'account_code': '科目代码',
            '制单': '制单人', '审核': '审核人', '记账': '记账人',
            '客商': '供应商', '往来单位': '供应商', 'vendor': '供应商',
            '预算科目': '预算项目', '预算项': '预算项目',
        }
        df.rename(columns=COLUMN_MAP, inplace=True)
        
        # 清洗
        for col, spec in cls.VOUCHER_SCHEMA.items():
            if col not in df.columns:
                if spec.get('required'):
                    print(f'  ⚠ 缺少必要字段: {col}')
                else:
                    df[col] = spec.get('default', '')
                continue
            
            if spec['type'] == 'num':
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.replace('，', ''), errors='coerce').fillna(0)
            elif spec['type'] == 'date':
                df[col] = pd.to_datetime(df[col], errors='coerce')
            elif spec['type'] == 'str':
                df[col] = df[col].fillna('').astype(str).str.strip()
            elif spec['type'] == 'int':
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        
        # 补充衍生字段
        if '借方金额' in df.columns and '贷方金额' in df.columns:
            df['金额'] = np.maximum(df['借方金额'].abs(), df['贷方金额'].abs())
        
        if '凭证日期' in df.columns:
            df['年'] = df['凭证日期'].dt.year
            df['月'] = df['凭证日期'].dt.month
            df['日'] = df['凭证日期'].dt.day
            df['星期'] = df['凭证日期'].dt.weekday
        
        print(f'  标准化完成: {len(df)} 条 → {len(df.columns)} 列')
        return df


# ============================================================
# 第二层：特征工程
# ============================================================

class FeatureEngine:
    """从标准化凭证中提取审计特征"""
    
    # 中国法定节假日（简化，按需补充）
    HOLIDAYS = {
        '元旦': [(1, 1)],
        '春节': [(1, 28), (1, 29), (1, 30), (1, 31), (2, 1), (2, 2), (2, 3)],  # 示例
        '清明': [(4, 5)],
        '五一': [(5, 1), (5, 2), (5, 3), (5, 4), (5, 5)],
        '端午': [(6, 10)],
        '中秋': [(10, 6)],
        '国庆': [(10, 1), (10, 2), (10, 3), (10, 4), (10, 5), (10, 6), (10, 7)],
    }
    
    # 异常科目搭配（借方→贷方，不应同时出现的组合）
    SUSPICIOUS_PAIRS = [
        ('管理费用', '主营业务收入'),
        ('固定资产', '库存现金'),
        ('在建工程', '其他应收款'),
        ('预付账款', '预付账款'),
    ]
    
    # 模糊摘要关键词
    VAGUE_WORDS = ['其他', '其它', '杂项', '等', '相关', '费用', '支出', '付款', '暂', '补', '冲', '调']
    
    @classmethod
    def extract_all(cls, df: pd.DataFrame, feature_list: List[str] = None) -> pd.DataFrame:
        """批量提取特征，feature_list为空则提取全部"""
        all_features = {
            '金额': cls._amount_features,
            '时间': cls._time_features,
            '摘要': cls._summary_features,
            '科目': cls._account_features,
            '制单人': cls._person_features,
            '附件': cls._attachment_features,
        }
        
        if feature_list is None:
            feature_list = list(all_features.keys())
        
        for group in feature_list:
            if group in all_features:
                df = all_features[group](df)
        
        return df
    
    @classmethod
    def _amount_features(cls, df):
        if '金额' not in df.columns: return df
        df['f_金额首位数字'] = df['金额'].apply(lambda x: int(str(int(abs(x)))[0]) if abs(x) >= 1 and x != 0 else 0)
        df['f_金额末位数字'] = (df['金额'].abs() % 10).astype(int)
        df['f_是否整数'] = (df['金额'].abs() % 1 == 0).astype(int)
        df['f_是否整百'] = ((df['金额'].abs() % 100 == 0) & (df['金额'].abs() >= 500)).astype(int)
        df['f_是否整千'] = ((df['金额'].abs() % 1000 == 0) & (df['金额'].abs() >= 3000)).astype(int)
        df['f_是否大额'] = (df['金额'].abs() >= 50000).astype(int)
        df['f_借贷差额'] = abs(df['借方金额'].abs() - df['贷方金额'].abs())
        df['f_借贷不平'] = (df['f_借贷差额'] > 0.01).astype(int)
        return df
    
    @classmethod
    def _time_features(cls, df):
        if '凭证日期' not in df.columns: return df
        df['f_是否周末'] = (df['星期'].isin([5, 6])).astype(int)
        df['f_是否月末'] = (df['日'] >= 28).astype(int)
        df['f_是否季末'] = ((df['月'].isin([3, 6, 9, 12])) & (df['日'] >= 28)).astype(int)
        df['f_是否年末'] = (df['月'] == 12).astype(int)
        # 节假日临近检测
        df['f_是否节假前后'] = df.apply(
            lambda r: cls._is_holiday_nearby(r['月'], r['日']), axis=1
        ).astype(int)
        return df
    
    @classmethod
    def _summary_features(cls, df):
        if '摘要' not in df.columns: return df
        df['f_摘要长度'] = df['摘要'].str.len()
        df['f_摘要含金额'] = df['摘要'].str.contains(r'\d+\.?\d*', regex=True).fillna(False).astype(int)
        df['f_摘要含冲调'] = df['摘要'].str.contains('冲|调', regex=True).fillna(False).astype(int)
        df['f_摘要含暂'] = df['摘要'].str.contains('暂', regex=True).fillna(False).astype(int)
        df['f_摘要含退'] = df['摘要'].str.contains('退|还|返', regex=True).fillna(False).astype(int)
        df['f_摘要模糊度'] = df['摘要'].apply(cls._vague_score)
        for word in cls.VAGUE_WORDS[:5]:
            safe_name = word.replace('|', '_')
            df[f'f_摘要含_{safe_name}'] = df['摘要'].str.contains(word, regex=False).fillna(False).astype(int)
        return df
    
    @classmethod
    def _account_features(cls, df):
        if '科目代码' not in df.columns: return df
        df['f_是否费用类'] = df['科目代码'].astype(str).str.startswith(('5', '66')).astype(int)
        df['f_是否收入类'] = df['科目代码'].astype(str).str.startswith(('6', '60')).astype(int)
        df['f_是否往来类'] = df['科目代码'].astype(str).str.match(r'^12[123]|^22[34]').fillna(False).astype(int)
        df['f_是否现金'] = df['科目名称'].str.contains('库存现金|现金', na=False).astype(int)
        df['f_是否预付'] = df['科目名称'].str.contains('预付', na=False).astype(int)
        return df
    
    @classmethod
    def _person_features(cls, df):
        if '制单人' in df.columns and '审核人' in df.columns:
            df['f_制单审核同一人'] = (df['制单人'].fillna('') == df['审核人'].fillna('')).astype(int)
        return df
    
    @classmethod
    def _attachment_features(cls, df):
        if '附件张数' in df.columns:
            df['f_无附件'] = (df['附件张数'] == 0).astype(int)
        return df
    
    @classmethod
    def _is_holiday_nearby(cls, month, day, days=2):
        """判断日期是否在节假日前后N天内"""
        for holiday_dates in cls.HOLIDAYS.values():
            for hm, hd in holiday_dates:
                h_date = datetime(2025, hm, hd)
                check_date = datetime(2025, month, day)
                if abs((check_date - h_date).days) <= days:
                    return True
        return False
    
    @classmethod
    def _vague_score(cls, text):
        """摘要模糊度评分：越短越模糊，含模糊词加分"""
        if not isinstance(text, str): return 1.0
        score = 0.0
        if len(text) < 5: score += 0.4
        elif len(text) < 10: score += 0.2
        for w in cls.VAGUE_WORDS:
            if w in text: score += 0.1
        return min(score, 1.0)


# ============================================================
# 第三层：模型检测器
# ============================================================

class RuleEngine:
    """L1: 规则引擎 — 硬规则，命中即疑点
    
    规则格式（YAML）：
      - id: "R01"
        desc: "制单人与审核人同一人"
        level: "高"
        weight: 15
        conditions:
          - {col: "f_制单审核同一人", op: "eq", val: 1}
    
    支持的操作符: eq(等于), ne(不等于), gt(大于), gte(大于等于), lt(小于), lte(小于等于)
    多个 conditions 之间是 AND 关系。
    """
    
    OPS = {
        'eq': lambda s, v: s == v,
        'ne': lambda s, v: s != v,
        'gt': lambda s, v: s > v,
        'gte': lambda s, v: s >= v,
        'lt': lambda s, v: s < v,
        'lte': lambda s, v: s <= v,
    }
    
    @staticmethod
    def run(df, rules: List[Dict]) -> pd.DataFrame:
        results = []
        for rule in rules:
            if not rule.get('enabled', True):
                continue
            try:
                # 构建布尔掩码
                conditions = rule.get('conditions', [])
                if not conditions:
                    continue
                
                mask = pd.Series(True, index=df.index)
                for cond in conditions:
                    col = cond['col']
                    op = cond.get('op', 'eq')
                    val = cond['val']
                    if col not in df.columns:
                        print(f'  [WARN] Rule [{rule["id"]}]: column "{col}" not found')
                        mask = pd.Series(False, index=df.index)
                        break
                    op_func = RuleEngine.OPS.get(op)
                    if op_func is None:
                        print(f'  [WARN] Rule [{rule["id"]}]: unknown op "{op}"')
                        mask = pd.Series(False, index=df.index)
                        break
                    mask = mask & op_func(df[col], val)
                
                hits = df[mask]
                if len(hits) > 0:
                    for idx in hits.index:
                        results.append({
                            '凭证编号': hits.loc[idx, '凭证编号'] if '凭证编号' in hits.columns else idx,
                            '凭证日期': str(hits.loc[idx, '凭证日期']) if '凭证日期' in hits.columns else '',
                            '模型': '规则引擎',
                            '规则': rule['id'],
                            '描述': rule['desc'],
                            '风险等级': rule.get('level', '中'),
                            '分数': rule.get('weight', 10),
                            '摘要': hits.loc[idx, '摘要'] if '摘要' in hits.columns else '',
                            '金额': hits.loc[idx, '金额'] if '金额' in hits.columns else 0,
                        })
            except Exception as e:
                print(f'  [WARN] Rule [{rule["id"]}] failed: {str(e)[:80]}')
        
        return pd.DataFrame(results)


class BenfordDetector:
    """L2: Benford 定律检测"""
    
    @staticmethod
    def run(df, config: Dict = None) -> pd.DataFrame:
        from scipy import stats
        
        data = df[df['金额'] > 0]['金额']
        first_digits = [int(str(int(abs(x)))[0]) for x in data if abs(x) >= 1]
        
        if len(first_digits) < 50:
            return pd.DataFrame()
        
        actual = [first_digits.count(d) for d in range(1, 10)]
        benford = [np.log10(1 + 1/d) for d in range(1, 10)]
        total = sum(actual)
        expected = [total * p for p in benford]
        
        chi2, p_value = stats.chisquare(actual, expected)
        mad = np.mean([abs(a/total - b) for a, b in zip(actual, benford)])
        
        threshold = (config or {}).get('threshold', {})
        is_anomaly = p_value < threshold.get('p_value', 0.01) or mad > threshold.get('mad', 0.015)
        
        return pd.DataFrame([{
            '模型': 'Benford',
            '描述': f'数字分布偏离（卡方={chi2:.1f}, p={p_value:.4f}, MAD={mad:.4f}）',
            '风险等级': '🔴' if is_anomaly else '🟢',
            '分数': 30 if is_anomaly else 0,
            '详情': {
                'chi2': chi2, 'p_value': p_value, 'mad': mad,
                'actual_distribution': {str(d): round(c/total, 4) for d, c in zip(range(1,10), actual)},
            }
        }])


class StatisticalAnomalyDetector:
    """L2: 统计异常 — Z分/IQR"""
    
    @staticmethod
    def run(df, config: Dict = None) -> pd.DataFrame:
        cfg = config or {}
        group_by = cfg.get('group_by', [])
        threshold = cfg.get('threshold', {}).get('z_score', 3.0)
        
        results = []
        
        def detect(group_df, group_label='整体'):
            for col in ['金额', 'f_附件张数']:
                if col not in group_df.columns: continue
                series = group_df[col].dropna()
                if len(series) < 10: continue
                mean, std = series.mean(), series.std()
                if std == 0: continue
                
                z_scores = (group_df[col] - mean) / std
                anomalies = group_df[abs(z_scores) > threshold]
                
                for idx in anomalies.index:
                    results.append({
                        '凭证编号': anomalies.loc[idx, '凭证编号'] if '凭证编号' in anomalies.columns else idx,
                        '凭证日期': str(anomalies.loc[idx, '凭证日期']) if '凭证日期' in anomalies.columns else '',
                        '模型': '统计异常',
                        '描述': f'{col} Z分={z_scores[idx]:.1f} (均值{mean:.0f}, 当前{series.loc[idx]:.0f})',
                        '风险等级': '🟡' if abs(z_scores[idx]) < 5 else '🔴',
                        '分数': min(abs(z_scores[idx]) * 5, 40),
                        '摘要': anomalies.loc[idx, '摘要'] if '摘要' in anomalies.columns else '',
                        '金额': anomalies.loc[idx, '金额'] if '金额' in anomalies.columns else 0,
                    })
        
        if group_by:
            for keys, group in df.groupby(group_by):
                label = '|'.join(keys) if isinstance(keys, tuple) else keys
                detect(group, label)
        else:
            detect(df)
        
        return pd.DataFrame(results)


class FrequencyAnomalyDetector:
    """L2: 频率异常 — 同一实体短期内交易频率异常"""
    
    @staticmethod
    def run(df, config: Dict = None) -> pd.DataFrame:
        cfg = config or {}
        freq_col = cfg.get('group_by', '供应商')
        if freq_col not in df.columns:
            freq_col = '科目名称'
        
        results = []
        if '凭证日期' not in df.columns or '金额' not in df.columns:
            return pd.DataFrame()
        
        df = df.sort_values('凭证日期')
        
        for entity, group in df.groupby(freq_col):
            if len(group) < 3: continue
            time_span = (group['凭证日期'].max() - group['凭证日期'].min()).days
            if time_span == 0: time_span = 1
            daily_rate = len(group) / time_span
            total = group['金额'].sum()
            
            if daily_rate > 0.5 or (len(group) > 10 and time_span < 30):
                results.append({
                    '模型': '频率异常',
                    '描述': f'{freq_col}={entity}：{len(group)}笔/{time_span}天，日均{daily_rate:.1f}笔',
                    '风险等级': '🔴' if daily_rate > 1 else '🟡',
                    '分数': min(daily_rate * 20, 30),
                    '详情': {'entity': entity, 'count': len(group), 'days': time_span, 'total': float(total)},
                })
        
        return pd.DataFrame(results)


# ============================================================
# 管道引擎
# ============================================================

class AuditPipeline:
    """主引擎：加载配置 → 加载数据 → 标准化 → 特征 → 跑模型 → 汇总"""
    
    def __init__(self, config_path: str):
        with open(config_path, 'r', encoding='utf-8') as f:
            raw = yaml.safe_load(f)
        
        self.config_name = raw.get('name', '未命名')
        self.config_desc = raw.get('description', '')
        self.audit_type = raw.get('audit_type', '')
        self.data_reqs = raw.get('data_requirements', {})
        self.risk_mapping = raw.get('risk_mapping', {})
        
        # 解析模型配置
        self.models = []
        for m in raw.get('models', []):
            self.models.append(ModelConfig(
                id=m['id'], name=m['name'],
                enabled=m.get('enabled', True),
                weight=m.get('weight', 1.0),
                threshold=m.get('threshold', {}),
                rules=m.get('rules', []),
                features=m.get('features', []),
            ))
        
        self.df = None
        self.featured_df = None
        self.findings = []
    
    def load_data(self, data_path: str):
        """加载数据文件"""
        path = Path(data_path)
        if path.is_file():
            files = [path]
        else:
            files = list(path.glob('*.csv')) + list(path.glob('*.xlsx')) + list(path.glob('*.xls'))
        
        if not files:
            raise FileNotFoundError(f'未找到数据文件: {data_path}')
        
        dfs = []
        for f in files:
            print(f'  加载: {f.name}')
            if f.suffix in ('.xlsx', '.xls'):
                dfs.append(pd.read_excel(f))
            else:
                for enc in ['utf-8', 'gbk', 'gb2312', 'gb18030']:
                    try:
                        dfs.append(pd.read_csv(f, encoding=enc))
                        break
                    except: continue
        
        raw = pd.concat(dfs, ignore_index=True) if len(dfs) > 1 else dfs[0]
        print(f'  原始: {len(raw)} 条, {len(raw.columns)} 列')
        
        # 标准化
        self.df = DataStandardizer.standardize(raw)
        return self
    
    def extract_features(self):
        """提取特征"""
        active_features = set()
        for m in self.models:
            if m.enabled:
                active_features.update(m.features)
        
        if not active_features:
            active_features = {'金额', '时间', '摘要', '科目', '制单人', '附件'}
        
        self.featured_df = FeatureEngine.extract_all(self.df, list(active_features))
        return self
    
    def run_models(self):
        """按配置跑所有启用的模型"""
        print(f'\n{"="*50}')
        print(f'  管道引擎: {self.config_name}')
        print(f'  审计类型: {self.audit_type}')
        print(f'  启用模型: {sum(1 for m in self.models if m.enabled)}/{len(self.models)}')
        print(f'{"="*50}\n')
        
        # 注册模型执行器
        MODEL_EXECUTORS = {
            'rule_engine':     (RuleEngine, 'run'),
            'benford':         (BenfordDetector, 'run'),
            'statistical':     (StatisticalAnomalyDetector, 'run'),
            'frequency':       (FrequencyAnomalyDetector, 'run'),
        }
        
        for model in self.models:
            if not model.enabled: continue
            
            executor = MODEL_EXECUTORS.get(model.id)
            if executor is None:
                print(f'  ⚠ 未知模型: {model.id}')
                continue
            
            cls, method = executor
            print(f'  [{model.name}] 运行中...')
            
            try:
                if model.id == 'rule_engine':
                    result = getattr(cls, method)(self.featured_df, model.rules)
                else:
                    result = getattr(cls, method)(self.featured_df, {'threshold': model.threshold})
                
                if len(result) > 0:
                    result['模型名'] = model.id
                    result['权重'] = model.weight
                    self.findings.append(result)
                    print(f'    [OK] Found {len(result)} items')
                else:
                    print(f'    [OK] No anomalies')
            except Exception as e:
                import sys
                msg = str(e)[:100]
                if sys.stdout.encoding.lower() in ('gbk', 'cp936'):
                    print(f'    [FAIL] {msg}')
                else:
                    print(f'    [FAIL] {msg}')
        
        return self
    
    def summary(self) -> pd.DataFrame:
        """汇总所有发现"""
        if not self.findings:
            print('\n  [OK] No anomalies found')
            return pd.DataFrame()
        
        all_findings = pd.concat(self.findings, ignore_index=True)
        
        # 按凭证编号合并（同一条凭证被多个模型标记，合并得分）
        if '凭证编号' in all_findings.columns:
            merged = all_findings.groupby('凭证编号').agg({
                '分数': 'sum',
                '凭证日期': 'first',
                '摘要': 'first',
                '金额': 'first',
                '描述': lambda x: '; '.join(x.dropna().astype(str)),
            }).reset_index()
            merged['综合风险'] = merged['分数'].apply(
                lambda s: '高' if s >= 60 else ('中' if s >= 30 else '低'))
            merged = merged.sort_values('分数', ascending=False)
        else:
            merged = all_findings
        
        print(f'\n{"="*50}')
        print(f'  汇总: {len(merged)} 条异常')
        high = len(merged[merged['综合风险'] == '高']) if '综合风险' in merged.columns else 0
        mid = len(merged[merged['综合风险'] == '中']) if '综合风险' in merged.columns else 0
        print(f'  HIGH: {high}')
        print(f'  MID: {mid}')
        print(f'{"="*50}')
        
        return merged
    
    def export(self, output_path: str = None):
        """导出结果"""
        summary_df = self.summary()
        if summary_df.empty: return
        
        if output_path is None:
            output_path = f'审计疑点清单_{self.config_name}_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            summary_df.to_excel(writer, sheet_name='疑点清单', index=False)
            # 附原始数据摘要
            if self.df is not None:
                self.df.head(100).to_excel(writer, sheet_name='原始数据(前100行)', index=False)
        
        print(f'\n  [DONE] Exported: {output_path}')
        return output_path


# ============================================================
# CLI
# ============================================================

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='配置驱动的审计检测管道')
    parser.add_argument('--config', required=True, help='场景配置文件 (YAML)')
    parser.add_argument('--data', required=True, help='数据文件或目录')
    parser.add_argument('--output', help='输出 Excel 路径')
    args = parser.parse_args()
    
    pipeline = AuditPipeline(args.config)
    pipeline.load_data(args.data)
    pipeline.extract_features()
    pipeline.run_models()
    pipeline.export(args.output)
