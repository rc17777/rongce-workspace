# 审计人员数字技能修炼手册 | 进阶篇（四）：数据架构与数据治理

> **来源：** 数审派 微信公众号  
> **原文链接：** https://mp.weixin.qq.com/s?__biz=Mzk3NTk5MjY2MQ==&mid=2247483848&idx=1&sn=2736ae5e4e44e1fe7d8ce9332715e82d  
> **抓取时间：** 2026-05-06 20:05:00  
> **抓取方式：** curl + WeChat UA → HTML 提取

---

各位审计同仁，大家好！

上期我们完成了统计学基础的学习。今天我们进入进阶篇的最后一站——**数据架构与数据治理**，后面将进入**高阶篇**的学习。

作为审计人员，我们不仅要会分析数据，还需要理解数据是如何产生、存储、流转和管理的。掌握数据治理知识，可以帮助你更好地评估数据质量、识别数据风险、提出改进建议。

## 一、为什么审计人员要了解数据架构？

### 1.1 数据架构的重要性

场景
数据架构知识的作用
信息系统审计
评估系统设计和数据流程的控制有效性
数据质量审计
理解数据来源和流转路径，识别质量问题根源
财务系统审计
了解业务系统与财务系统的数据交互
风险评估
评估数据治理不完善带来的风险
审计建议
提出切实可行的数据改进建议

### 1.2 数据架构 vs 数据治理

数据架构（Data Architecture）
└── 关注数据的"设计"和"结构"
    ├── 数据模型设计
    ├── 数据存储方案
    ├── 数据流转路径
    └── 集成架构

数据治理（Data Governance）
└── 关注数据的"管理"和"管控"
    ├── 数据标准
    ├── 数据质量
    ├── 数据安全
    ├── 数据隐私
    └── 数据生命周期

## 二、数据架构基础

### 2.1 数据模型

数据模型是对现实世界数据结构的抽象和简化。

**三种主要数据模型**：

模型类型
说明
审计应用场景**概念模型**
高度抽象的业务实体及其关系
业务理解、需求分析**逻辑模型**
技术无关的数据结构定义
数据库设计、系统设计**物理模型**
具体的技术实现方案
IT审计、数据库审计

**ER图（实体-关系图）**：

┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   供应商     │ 1    N  │   采购合同   │ N    1  │   采购订单   │
│             │─────────┤             │─────────┤             │
│ 供应商代码   │         │ 合同编号     │         │ 订单编号     │
│ 供应商名称   │         │ 供应商代码   │         │ 合同编号     │
│ 联系人       │         │ 签订日期     │         │ 订单日期     │
│ 地址         │         │ 合同金额     │         │ 订单金额     │
│ 信用评级     │         │ 有效期       │         │ 订单状态     │
└─────────────┘         └─────────────┘         └─────────────┘

### 2.2 常见数据库类型

数据库类型
特点
审计注意事项**关系型数据库（RDBMS）**
使用SQL，表与表之间有关联
关注数据完整性和一致性**NoSQL数据库**
灵活的数据结构，高扩展性
关注事务支持和数据一致性保证**数据仓库**
用于分析的集成数据存储
关注数据抽取和转换过程**数据湖**
存储各种类型的原始数据
关注数据质量和访问控制**时序数据库**
优化时间序列数据存储
关注数据采集频率和精度

**审计中常见的数据库**：

系统
数据库类型
数据内容
SAP
Oracle/SQL Server/HANA
财务数据、业务数据
Oracle EBS
Oracle
财务数据
金蝶EAS
SQL Server/Oracle
财务数据
用友NC
SQL Server
财务数据
CRM系统
MySQL/Oracle
客户数据、销售数据
电商系统
MySQL/PostgreSQL
交易数据

### 2.3 数据流转架构

典型的企业数据流转：

┌──────────────┐
│  业务系统     │  ← ERP、CRM、SCM等
│  (源系统)     │
└──────┬───────┘
       ↓ ETL/ELT
┌──────────────┐
│   数据仓库    │  ← 抽取、转换、加载
│ (Data Warehouse)│
└──────┬───────┘
       ↓
┌──────────────┐
│   数据集市    │  ← 按部门/主题划分
│ (Data Mart)  │
└──────┬───────┘
       ↓
┌──────────────┐
│   数据可视化  │  ← 报表、仪表板
│ (BI Tools)  │
└──────────────┘

## 三、数据治理框架

### 3.1 DAMA数据治理框架

DAMA国际（数据管理协会）提出了数据治理的五大领域：

数据治理
├── 数据架构管理
├── 数据建模与设计
├── 数据存储与操作
├── 数据安全管理
└── 数据质量管理

### 3.2 数据治理的核心要素

要素
说明
审计关注点**数据标准**
数据的定义、格式、编码规则
是否存在标准、是否执行**数据质量**
数据的准确性、完整性、一致性
质量问题频率和处理机制**元数据管理**
关于数据的数据
数据字典、数据血缘**主数据管理**
核心业务实体的统一数据
客户、供应商、产品主数据**参考数据管理**
标准代码和分类
科目代码、行业分类**数据安全**
访问控制、加密、隐私保护
权限管理、敏感数据保护**数据生命周期**
数据的创建、使用、归档、销毁
保留策略、销毁记录

## 四、数据质量管理

### 4.1 数据质量维度

维度
说明
审计评估方法**完整性**
数据是否完整，无缺失
空值比例分析**准确性**
数据是否正确反映实际
与源数据核对**一致性**
不同系统数据是否一致
跨系统比对**及时性**
数据是否及时更新
时间戳分析**唯一性**
数据是否存在重复
重复记录检测**有效性**
数据是否符合业务规则
业务规则验证

### 4.2 数据质量评估示例

import pandas as pd
import numpy as np

defassess_data_quality(df, table_name):
    """评估数据质量"""
    results = {
        '表名': table_name,
        '总记录数': len(df),
        '字段数': len(df.columns),
        '质量问题': []
    }

    for col in df.columns:
        # 空值检查
        null_count = df[col].isnull().sum()
        null_ratio = null_count / len(df)
        if null_ratio > 0.05:  # 超过5%为空值
            results['质量问题'].append({
                '字段': col,
                '类型': '空值过多',
                '数量': null_count,
                '比例': f"{null_ratio:.2%}"
            })

        # 重复值检查
        if df[col].duplicated().sum() > 0and col in ['身份证号', '供应商代码', '客户编号']:
            results['质量问题'].append({
                '字段': col,
                '类型': '可能存在重复',
                '数量': df[col].duplicated().sum()
            })

        # 格式检查（针对特定字段）
        if'日期'in col or'Date'in col.upper():
            try:
                pd.to_datetime(df[col])
            except:
                results['质量问题'].append({
                    '字段': col,
                    '类型': '日期格式错误',
                    '示例': df[col].dropna().iloc[0] iflen(df[col].dropna()) > 0else'N/A'
                })

        if'金额'in col or'Amount'in col.upper():
            try:
                numeric_check = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
                invalid_count = numeric_check.isnull().sum() - null_count
                if invalid_count > 0:
                    results['质量问题'].append({
                        '字段': col,
                        '类型': '金额格式错误',
                        '数量': invalid_count
                    })
            except:
                pass

    return results

# 使用示例
# data = pd.read_excel('科目余额表.xlsx')
# quality_report = assess_data_quality(data, '科目余额表')
# print(quality_report)

### 4.3 数据质量问题分析

import pandas as pd

defgenerate_quality_report(df, table_name):
    """生成数据质量报告"""

    print("=" * 70)
    print(f"数据质量报告 - {table_name}")
    print("=" * 70)

    print(f"\n【基本信息】")
    print(f"总记录数: {len(df):,}")
    print(f"字段数: {len(df.columns)}")

    print(f"\n【各字段空值统计】")
    null_stats = []
    for col in df.columns:
        null_count = df[col].isnull().sum()
        null_ratio = null_count / len(df)
        null_stats.append({
            '字段名': col,
            '非空记录': len(df) - null_count,
            '空值数': null_count,
            '空值率': f"{null_ratio:.2%}",
            '数据类型': str(df[col].dtype)
        })

    null_df = pd.DataFrame(null_stats)
    null_df = null_df.sort_values('空值数', ascending=False)
    print(null_df.to_string(index=False))

    print(f"\n【唯一值统计（前10字段）】")
    unique_stats = []
    for col in df.columns:
        unique_stats.append({
            '字段名': col,
            '唯一值数': df[col].nunique(),
            '唯一率': f"{df[col].nunique() / len(df):.2%}"
        })
    unique_df = pd.DataFrame(unique_stats).sort_values('唯一值数', ascending=False)
    print(unique_df.head(10).to_string(index=False))

    return null_df, unique_df

# 示例输出格式
# data = pd.read_excel('应收账款明细.xlsx')
# null_df, unique_df = generate_quality_report(data, '应收账款明细')

## 五、数据安全与隐私

### 5.1 数据安全框架

数据安全
├── 访问控制
│   ├── 用户认证（密码、生物识别、MFA）
│   ├── 授权管理（RBAC、ABAC）
│   └── 权限审计
├── 数据加密
│   ├── 传输加密（TLS/SSL）
│   ├── 存储加密（AES等）
│   └── 脱敏处理
├── 数据备份与恢复
│   ├── 备份策略
│   ├── 恢复测试
│   └── 灾难恢复计划
└── 合规管理
    ├── 个人信息保护
    ├── 行业法规合规
    └── 跨境数据流动

### 5.2 敏感数据识别

import re

defidentify_sensitive_fields(df):
    """识别敏感数据字段"""

    sensitive_patterns = {
        '个人身份信息': [
            (r'姓名', '客户姓名'),
            (r'身份证', '身份证号'),
            (r'手机[号码]', '手机号码'),
            (r'电话[号号码]', '电话号码'),
            (r'地址', '地址信息'),
            (r'邮箱', '邮箱地址'),
        ],
        '金融信息': [
            (r'银行[账号卡号]', '银行账号'),
            (r'信用卡', '信用卡号'),
            (r'CVV', 'CVV'),
            (r'密码', '密码'),
            (r'社保', '社保账号'),
        ],
        '健康信息': [
            (r'病历', '病历信息'),
            (r'诊断', '诊断信息'),
            (r'医保', '医保信息'),
        ],
        '经营信息': [
            (r'商业秘密', '商业秘密'),
            (r'配方', '工艺配方'),
        ]
    }

    sensitive_fields = []

    for category, patterns in sensitive_patterns.items():
        for col in df.columns:
            for pattern, description in patterns:
                if re.search(pattern, col, re.IGNORECASE):
                    sensitive_fields.append({
                        '字段名': col,
                        '敏感类型': category,
                        '说明': description,
                        '样本数据': df[col].dropna().iloc[0] iflen(df[col].dropna()) > 0else'N/A'
                    })

    return sensitive_fields

# 示例
# df = pd.read_excel('客户信息表.xlsx')
# sensitive = identify_sensitive_fields(df)
# print(pd.DataFrame(sensitive))

### 5.3 数据脱敏检查

def check_data_masking(df):
    """检查数据脱敏情况"""

    unmasked = []

    # 检查明显的未脱敏字段
    for col in df.columns:
        col_lower = col.lower()

        # 手机号检查（11位数字是否完整显示）
        if'手机'in col and df[col].dtype == 'object':
            sample = df[col].dropna().astype(str).iloc[0] iflen(df[col].dropna()) > 0else''
            iflen(re.findall(r'\d{11}', sample)) > 0:
                unmasked.append({
                    '字段': col,
                    '问题': '手机号未脱敏',
                    '样本': sample[:3] + '****' + sample[-4:] iflen(sample) >= 7else sample
                })

        # 身份证检查（前6后4是否显示）
        if'身份证'in col and df[col].dtype == 'object':
            sample = df[col].dropna().astype(str).iloc[0] iflen(df[col].dropna()) > 0else''
            iflen(re.findall(r'\d{17}[\dXx]', sample)) > 0:
                unmasked.append({
                    '字段': col,
                    '问题': '身份证号未脱敏',
                    '样本': sample[:6] + '********' + sample[-4:] iflen(sample) >= 14else sample
                })

    return unmasked

## 六、数据血缘分析

### 6.1 什么是数据血缘

数据血缘（Data Lineage）描述了数据的来源、流转路径和加工过程。

┌─────────────┐
│  源系统1    │
│  (银行流水) │
└──────┬──────┘
       ↓ 抽取
┌─────────────┐
│  ODS层      │  ← 原始数据层
│ (银行流水ODS)│
└──────┬──────┘
       ↓ 清洗转换
┌─────────────┐
│  DW层       │  ← 数据仓库层
│ (银行流水DW)│
└──────┬──────┘
       ↓ 汇总
┌─────────────┐
│  数据集市   │  ← 审计分析数据集市
│ (银行流水MA)│
└─────────────┘

### 6.2 数据血缘审计关注点

关注点
审计问题
数据来源
数据从哪里来？是否准确？
转换规则
数据经过哪些转换？转换逻辑是否正确？
数据漂移
数据定义是否随时间变化？
异常处理
ETL失败时如何处理？是否有补救机制？
追溯能力
能否从结果追溯到原始数据？

## 七、数据治理审计检查表

### 7.1 数据治理组织

检查项
评估内容
数据治理架构
是否建立数据治理组织？职责是否清晰？
数据Owner
关键数据是否有明确的数据Owner？
数据标准执行
数据标准是否得到执行？

### 7.2 数据质量管理

检查项
评估内容
数据质量规则
是否建立了数据质量规则？
质量监控
是否进行数据质量监控？
问题处理
数据质量问题如何处理？是否有闭环机制？

### 7.3 数据安全管理

检查项
评估内容
访问控制
访问权限是否最小化？
敏感数据保护
敏感数据是否脱敏或加密？
审计日志
数据访问是否有日志记录？

### 7.4 主数据与参考数据

检查项
评估内容
主数据管理
客户、供应商等主数据是否统一管理？
参考数据
科目代码等参考数据是否规范？
代码一致性
不同系统的代码是否一致？

## 八、实战案例

### 案例：财务系统数据治理审计

import pandas as pd
import numpy as np

classDataGovernanceAuditor:
    def__init__(self):
        self.findings = []
        self.recommendations = []

    defaudit_data_quality(self, df, table_name):
        """审计数据质量"""
        print(f"\n{'='*60}")
        print(f"数据质量审计 - {table_name}")
        print(f"{'='*60}")

        # 1. 空值审计
        null_ratio = df.isnull().sum() / len(df)
        high_null_cols = null_ratio[null_ratio > 0.1]  # 超过10%空值

        iflen(high_null_cols) > 0:
            print(f"\n⚠️ 发现 {len(high_null_cols)} 个字段空值率超过10%：")
            for col in high_null_cols.index:
                print(f"  - {col}: {high_null_cols[col]:.2%}")

            self.findings.append({
                '类别': '数据质量-完整性',
                '问题': f'{table_name}表存在{len(high_null_cols)}个高空值率字段',
                '影响': '可能导致分析结果不准确',
                '建议': '排查数据源，修复数据采集问题'
            })

        # 2. 重复数据审计
        for col in ['科目代码', '供应商代码', '客户编号']:
            if col in df.columns:
                dup_count = df[col].duplicated().sum()
                if dup_count > 0:
                    print(f"\n⚠️ {col}存在{dup_count}条重复记录")
                    self.findings.append({
                        '类别': '数据质量-唯一性',
                        '问题': f'{col}存在重复值',
                        '数量': dup_count
                    })

        # 3. 数据一致性审计（同一科目在系统间是否一致）
        if'科目代码'in df.columns and'科目名称'in df.columns:
            code_name_mapping = df.groupby('科目代码')['科目名称'].nunique()
            inconsistent = code_name_mapping[code_name_mapping > 1]
            iflen(inconsistent) > 0:
                print(f"\n⚠️ 发现{len(inconsistent)}个科目代码对应多个科目名称")
                self.findings.append({
                    '类别': '数据质量-一致性',
                    '问题': '科目代码与名称映射不唯一',
                    '建议': '建立主数据管理系统，统一科目定义'
                })

    defaudit_data_security(self, df):
        """审计数据安全"""
        print(f"\n{'='*60}")
        print("数据安全审计")
        print(f"{'='*60}")

        sensitive_keywords = ['密码', '密钥', '身份证', '手机', '地址']

        for col in df.columns:
            for keyword in sensitive_keywords:
                if keyword in col.lower():
                    print(f"\n⚠️ 发现敏感字段: {col}")
                    # 检查是否已脱敏
                    sample = str(df[col].dropna().iloc[0]) iflen(df[col].dropna()) > 0else''
                    iflen(re.findall(r'\d{11}', sample)) > 0orlen(re.findall(r'\d{17}[\dXx]', sample)) > 0:
                        print(f"   状态: 未脱敏 ⚠️")
                        self.findings.append({
                            '类别': '数据安全',
                            '问题': f'{col}包含敏感信息且未脱敏',
                            '风险等级': '高',
                            '建议': '对该字段进行脱敏处理'
                        })

    defaudit_process_controls(self):
        """审计流程控制"""
        print(f"\n{'='*60}")
        print("ETL流程控制审计")
        print(f"{'='*60}")

        # 检查ETL日志是否存在
        # 检查数据更新时间是否正常
        # 检查异常数据处理机制

        controls = [
            ("数据抽取日志", True, "已实现"),
            ("数据转换规则版本管理", False, "未实现"),
            ("ETL失败告警", True, "已实现"),
            ("数据质量检查", True, "已实现"),
            ("异常数据处理流程", False, "未完全实现"),
        ]

        for control, status, remark in controls:
            status_icon = "✓"if status else"✗"
            print(f"  {status_icon} {control}: {remark}")

            ifnot status:
                self.findings.append({
                    '类别': '流程控制',
                    '问题': f'{control}缺失或不完善',
                    '建议': '完善该控制措施'
                })

    defgenerate_audit_report(self):
        """生成审计报告"""
        print(f"\n{'='*60}")
        print("数据治理审计报告")
        print(f"{'='*60}")

        print(f"\n共发现 {len(self.findings)} 个问题：")

        findings_df = pd.DataFrame(self.findings)
        iflen(findings_df) > 0:
            by_category = findings_df.groupby('类别').size()
            print("\n问题分类统计：")
            for category, count in by_category.items():
                print(f"  - {category}: {count}个")

            print("\n详细发现：")
            for i, finding inenumerate(self.findings, 1):
                print(f"\n  {i}. [{finding['类别']}] {finding['问题']}")
                if'影响'in finding:
                    print(f"     影响: {finding['影响']}")
                if'建议'in finding:
                    print(f"     建议: {finding['建议']}")

        return findings_df

# 使用示例
# auditor = DataGovernanceAuditor()
# auditor.audit_data_quality(df_gl_balance, '科目余额表')
# auditor.audit_data_security(df_customer)
# auditor.audit_process_controls()
# report = auditor.generate_audit_report()

## 九、实战作业

1. **理解数据架构**：
• 了解你所在企业的数据架构
• 画出关键系统的数据流转图
2. **评估数据质量**：
• 选择一个数据表进行质量评估
• 使用本文学到的质量检查方法
3. **安全审计**：
• 识别系统中的敏感数据字段
• 检查数据脱敏情况
4. **提出改进建议**：
• 根据审计发现，提出数据治理改进建议

## 总结

今天我们学习了数据架构与数据治理：

知识点
说明
审计应用
数据架构
数据的设计和结构
理解数据流转
数据模型
实体和关系建模
需求分析、系统设计
数据库类型
RDBMS、NoSQL、数据仓库
技术选型评估
数据治理框架
DAMA五大领域
建立治理体系
数据质量管理
六大质量维度
评估数据质量
数据安全
访问控制、加密、脱敏
安全审计
数据血缘
数据来源和流转追溯
异常追溯

数据治理是确保数据资产得到有效管理和保护的系统性方法。作为审计人员，理解数据治理可以帮助你：
• 更深入地评估信息系统风险
• 提出切实可行的改进建议
• 更好地保护数据资产

**进阶篇总结**

我们完成了进阶篇的学习：
• 进阶一：Python数据分析（Pandas、NumPy、Matplotlib）
• 进阶二：Power BI数据可视化
• 进阶三：统计学基础（用于异常检测）
• 进阶四：数据架构与数据治理

进阶篇涵盖了从数据处理到可视化的完整技能体系，为高阶篇打下了坚实基础。

**下期预告**：我们将进入**高阶篇**的学习！高阶篇将带你进入机器学习和AI的智能化审计领域，敬请期待！

希望这个系列文章对你有帮助！如有问题，欢迎在评论区讨论。
