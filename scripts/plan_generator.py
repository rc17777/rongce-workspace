#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
融策智能方案生成器 — RAG增强版
═══════════════════════════════
输入：项目类型 + 基本信息
输出：实施方案的"深度穿透策略"章节（自动嵌入5×6矩阵+E规则+RAG案例）

工作原理：
  1. 根据审计类型 → 匹配5×6矩阵中的适用坐标系和措施
  2. 查询RAG知识库 → 检索同类项目案例、法规、审计要点
  3. 匹配E规则 → 选出可执行的筛查规则
  4. 组装输出 → 可直接嵌入实施方案 + 投标文件技术方案

用法：
  # 生成完整的深度穿透策略章节
  python scripts/plan_generator.py --type 预算执行 --name "XX局2026年度预算执行审计"

  # 生成投标文件的技术方案部分
  python scripts/plan_generator.py --type 经济责任 --name "XX集团经责审计" --mode bid

  # 仅查询RAG，不生成完整方案
  python scripts/plan_generator.py --type 专项资金 --rag-only

  # 交互模式（用自然语言描述项目）
  python scripts/plan_generator.py --interactive
"""

import sys
import os
import json
import subprocess
import argparse
from datetime import datetime

# 确保脚本目录在路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ═══════════════════════════════════════════
# 一、5×6矩阵映射表（审计类型 → 适用坐标系+措施）
# ═══════════════════════════════════════════

MATRIX = {
    '预算执行': {
        'display': '预算执行审计',
        'coordinates': {
            '时空': {
                '措施': ['门禁打卡×出差报销时空矛盾检测', '街景历史影像×验收照片时空比对'],
                '规则': ['E01', 'E02'],
                '方法描述': '将差旅/会议/培训报销数据与门禁打卡、GPS轨迹等独立时空数据做交叉比对，验证"人在哪"的真实性。',
            },
            '物理': {
                '措施': ['纸张消耗反推印刷量', '餐费标准反推实际就餐天数'],
                '规则': ['E09'],
                '方法描述': '用纸张采购量反推印刷品数量、用食材/餐费标准反推实际就餐人数天数，验证支出的物理真实性。',
            },
            '社会关系': {
                '措施': ['报销经办人×收款方工商关联穿透'],
                '规则': ['E15'],
                '方法描述': '对长期向同一收款方付款的经办人，穿透收款方工商信息，识别未披露的利益关联。',
            },
            '行为': {
                '措施': ['审批时间行为模式异常检测', '经办人报销行为画像'],
                '规则': ['E19'],
                '方法描述': '分析OA审批日志中的时间模式——深夜审批、秒批、节假日审批——构建异常行为画像。',
            },
            '时间序列': {
                '措施': ['年末突击支出节奏检测', '月度支出均衡性分析'],
                '规则': ['E23'],
                '方法描述': '绘制全年支出节奏曲线，检测Q4尤其是12月的异常支出峰值，识别"以拨代支"和突击花钱。',
            },
        },
        'rag_queries': [
            '预算执行审计 典型案例 审计方法',
            '预算执行 突击花钱 虚列支出 审计发现',
            '三公经费 审计 核查方法',
        ],
    },
    '专项资金': {
        'display': '专项资金审计',
        'coordinates': {
            '时空': {
                '措施': ['受益对象GPS坐标地理聚类', '卫星影像×项目施工进度时空比对'],
                '规则': ['E03', 'E04'],
                '方法描述': '将补贴受益对象地址转GPS坐标，做聚类分析识别"虚假分散申报"；用卫星影像历史回溯验证项目进度声称。',
            },
            '物理': {
                '措施': ['建材消耗反推实际建筑面积', '耗材消耗反推检测/实验真实性'],
                '规则': ['E10', 'E11'],
                '方法描述': '用水泥/钢材/商砼的实际采购量反推最大可建设面积，与验收面积比对；用实验室耗材采购量反推检测真实性。',
            },
            '社会关系': {
                '措施': ['申报主体×资金承接方股权关联穿透'],
                '规则': ['E16'],
                '方法描述': '提取申报方与实际收款方的股东/法人，做工商关联穿透，识别未披露关联和"一女多嫁"套取多笔资金。',
            },
            '行为': {
                '措施': ['资金申请行为突变检测'],
                '规则': [],
                '方法描述': '对同一申报主体的申请频率、金额、类型做时间序列分析，检测异常突变点。',
            },
            '时间序列': {
                '措施': ['资金拨付节奏异常峰值检测'],
                '规则': ['E24b'],
                '方法描述': '按日/周聚合拨付金额，检测考核截止前、审计进场前的集中拨付潮。',
            },
        },
        'rag_queries': [
            '专项资金审计 套取 挪用 典型案例',
            '财政专项资金 虚假申报 重复申报 审计方法',
            '专项资金 资金沉淀 拨付进度 审计',
        ],
    },
    '采购': {
        'display': '招投标/采购审计',
        'coordinates': {
            '时空': {
                '措施': ['投标文件元数据同源检测', '评标专家×投标人时空交集检测'],
                '规则': ['E05', 'E06'],
                '方法描述': '提取投标文件core.xml元数据（创建时间/修改时间/保存者），识别同一电脑制作；检测评标期间评委与投标人的时空交集。',
            },
            '物理': {
                '措施': ['供货真实性物理验证（量、质、时）'],
                '规则': [],
                '方法描述': '对已中标项目的实际供货量与合同约定量做物理比对——用仓库出入库记录、物流运单等独立数据源验证。',
            },
            '社会关系': {
                '措施': ['投标人关联图谱分析 [见bid-collusion模型]'],
                '规则': [],
                '方法描述': '股权穿透、高管交叉任职、历史共同投标——23层检测体系中的L8工商关联穿透。',
            },
            '行为': {
                '措施': ['报价数学规律异常检测', '轮流中标模式检测'],
                '规则': ['E20', 'E21'],
                '方法描述': '检测全部投标报价的分布规律（极端一致/等差数列/刚好在控制价下方）；检测同一批投标人轮流中标的围标联盟模式。',
            },
            '时间序列': {
                '措施': ['先定后招时间矛盾检测', '紧急采购时间模式分析'],
                '规则': ['E22'],
                '方法描述': '提取招标公告→开标→中标→签约四个关键日期，检测时序矛盾；分析紧急采购的时间分布和品类集中度。',
            },
        },
        'rag_queries': [
            '围标串标 审计方法 典型案例',
            '政府采购 虚假招标 评委违规',
            '招投标 报价分析 中标模式 异常检测',
        ],
    },
    '经济责任': {
        'display': '经济责任审计',
        'coordinates': {
            '时空': {
                '措施': ['领导行踪与重大决策时间线重建'],
                '规则': ['E07'],
                '方法描述': '将被审计领导任期内所有重大决策的审批节点与个人行踪做时空比对——识别"人不在但签了字"的矛盾。',
            },
            '物理': {
                '措施': ['重大项目物理真实性抽样验证'],
                '规则': [],
                '方法描述': '对被审计领导任期内主抓的重大项目，按金额排序取Top-N做物理痕迹验证（同工程/补贴类方法）。',
            },
            '社会关系': {
                '措施': ['领导干部亲属经商办企关联图谱', '交叉任职与旋转门地图'],
                '规则': ['E17', 'E18'],
                '方法描述': '提取被审计领导的配偶、子女、亲属 → 工商查询持股/任职企业 → 与管辖范围内供应商/项目方做交集。（合规前提下执行）',
            },
            '行为': {
                '措施': ['审批权画像分析', '离任前行为突变检测'],
                '规则': ['E19b'],
                '方法描述': '构建任期内审批偏好画像（金额/类型/对象分布）；检测离任前3-6个月的审批异常突变（突击提拔、密集签约）。',
            },
            '时间序列': {
                '措施': ['任期前后关键指标纵向对比'],
                '规则': ['E24'],
                '方法描述': '将上任前→任期内→离任后的收支结构、债务规模、项目数量做连续时间曲线，检测结构性断点。',
            },
        },
        'rag_queries': [
            '经济责任审计 典型案例 审计发现',
            '领导干部 经责审计 量化评价 责任界定',
            '经济责任 亲属经商 利益输送 审计方法',
        ],
    },
    '工程': {
        'display': '投资/工程审计',
        'coordinates': {
            '时空': {
                '措施': ['卫星影像×施工日志进度比对', '变更签证时空逻辑验证'],
                '规则': ['E08'],
                '方法描述': '用Google Earth历史影像对比施工日志声称的各时间节点工程形象进度；验证变更签证的时空合理性。',
            },
            '物理': {
                '措施': ['商砼/钢材供货量反推实际工程量', '机械台班反推施工强度', '隐蔽工程探地雷达检测'],
                '规则': ['E12'],
                '方法描述': '绕过施工方数据，直接调取商砼站/钢材经销商的独立供货记录反推最大可施工量；用柴油消耗反推机械台班真实性。',
            },
            '社会关系': {
                '措施': ['施工方×监理方人员关联', '材料供应商×甲方人员关联'],
                '规则': [],
                '方法描述': '比对施工方和监理方核心人员的历史共职/社保记录；穿透主要材料供应商的股东/高管与甲方工程管理人员的关系。',
            },
            '行为': {
                '措施': ['监理签字行为画像'],
                '规则': [],
                '方法描述': '按监理人员聚合签字频次和时间分布，识别"总在特定施工方的特定工序出现"的异常模式。',
            },
            '时间序列': {
                '措施': ['工程进度S曲线畸形检测'],
                '规则': [],
                '方法描述': '绘制累计完成百分比的时间曲线，检测前期拖沓→后期突然加速到"不可能速度"的异常模式。',
            },
        },
        'rag_queries': [
            '工程竣工财务决算审计 案例分析',
            '工程造价 虚报工程量 审计方法',
            '工程签证 变更 真实性 审计',
        ],
    },
    '两新补贴': {
        'display': '两新/消费品以旧换新补贴审计',
        'coordinates': {
            '时空': {
                '措施': ['收货地址地理聚类分析', '购买-配送时空逻辑验证'],
                '规则': ['E08b'],
                '方法描述': '将海量收货地址转GPS坐标做热力图，识别集中发往仓库/公司地址的虚假消费者；验证购买时间与配送时间的逻辑合理性。',
            },
            '物理': {
                '措施': ['进销存三向比对', '旧机回收量反推新品销售量', '物流运单验证'],
                '规则': ['E13', 'E14'],
                '方法描述': '期初库存+进货−销售≠期末库存=虚构销售套补；以旧换新中旧机回收量远小于新品销量=虚构以旧换新。',
            },
            '社会关系': {
                '措施': ['消费者×商家关联透视'],
                '规则': [],
                '方法描述': '将消费者姓名与商家员工/股东/法人做匹配，识别内部人员伪装消费者套取补贴。',
            },
            '行为': {
                '措施': ['消费者购买行为异常分析', '价格异常波动检测'],
                '规则': [],
                '方法描述': '检测同一消费者短期多次购买、深夜购买、跨省跳跃购买的异常模式；检测补贴前后的价格异常波动。',
            },
            '时间序列': {
                '措施': ['补贴截止前申报冲量检测'],
                '规则': ['E24c'],
                '方法描述': '按日聚合申报量，检测政策截止前1-2周的异常暴增峰。',
            },
        },
        'rag_queries': [
            '消费品以旧换新 补贴 审计 套取',
            '两新政策 审计 虚假交易 骗补',
            '消费补贴 进销存 审计方法',
        ],
    },
    '绩效': {
        'display': '绩效评价',
        'coordinates': {
            '时空': {
                '措施': ['产出/效果声称的时空一致性验证'],
                '规则': [],
                '方法描述': '对自评报告中声称的"服务人次""培训场次""覆盖范围"等用独立时空数据做交叉验证。',
            },
            '物理': {
                '措施': ['产出物物理验证（设备、耗材、场地）'],
                '规则': [],
                '方法描述': '对评价对象声称的设备采购、耗材消耗做物理验证——设备序列号、耗材采购量是否匹配。',
            },
            '社会关系': {
                '措施': ['第三方服务供应商关联透视'],
                '规则': [],
                '方法描述': '对绩效评价中涉及的第三方调查/评估机构做独立性审查。',
            },
            '行为': {
                '措施': ['绩效指标合理性反向测试', '自评打分模式分析'],
                '规则': [],
                '方法描述': '检测全部指标达标度的分布——是否"刚好全达标"（目标设置过低）或"全部不达标"（目标过高或数据失真）。',
            },
            '时间序列': {
                '措施': ['政策实施前后对比分析（DID）'],
                '规则': [],
                '方法描述': '用实施前后+同类地区对照的双重差分方法，剥离自然增长，提取政策的净效果。',
            },
        },
        'rag_queries': [
            '绩效评价 指标体系 审计方法',
            '财政支出绩效评价 典型案例 问题发现',
            '预算绩效管理 第三方评价 质量审核',
        ],
    },
    '收支': {
        'display': '收支审计',
        'coordinates': {
            '时空': {'措施': ['收费现场与台账时空比对', '会议/培训活动时空验证'], '规则': [], '方法描述': '核对收费记录的时空分布与实际业务量是否一致。'},
            '物理': {'措施': ['非税收入票据×银行流水物理匹配'], '规则': [], '方法描述': '票据存根与银行入账记录逐笔匹配，检测"坐支"和截留。'},
            '社会关系': {'措施': ['大额支出收款方关联穿透'], '规则': [], '方法描述': '对大额支出的收款方做工商关联穿透。'},
            '行为': {'措施': ['支出审批权限使用行为画像'], '规则': [], '方法描述': '分析审批权限的使用频率、金额分布和对象偏好。'},
            '时间序列': {'措施': ['收入缴库节奏分析', '月度支出均衡性'], '规则': ['E23'], '方法描述': '检测非税收入缴库是否存在年底集中现象；月度支出分布是否均衡。'},
        },
        'rag_queries': ['收支审计 坐支 截留 审计方法', '非税收入 审计 典型案例'],
    },
    '国企': {
        'display': '国有企业审计',
        'coordinates': {
            '时空': {'措施': ['关联交易时空合理性验证'], '规则': [], '方法描述': '验证关联交易发生的时间、地点与实际业务需求是否匹配。'},
            '物理': {'措施': ['存货实物盘点×账面三向比对'], '规则': [], '方法描述': '存货账面→实物盘点→出入库记录三向比对，识别虚假库存。'},
            '社会关系': {'措施': ['四层穿透式股权关联图谱'], '规则': [], '方法描述': '集团→子公司→孙公司→参股公司全链条穿透，识别隐藏关联方和利益输送通道。'},
            '行为': {'措施': ['大额资金调度审批行为画像'], '规则': [], '方法描述': '分析大额资金调度的审批模式——是否有特定人\特定时间的规律性。'},
            '时间序列': {'措施': ['关联交易时间分布分析'], '规则': [], '方法描述': '检测关联交易是否集中在报告期末——可能是为了粉饰报表。'},
        },
        'rag_queries': ['国企审计 关联交易 利益输送 审计方法', '国有企业 经济责任 穿透式监管'],
    },
}


# ═══════════════════════════════════════════
# 二、RAG查询引擎
# ═══════════════════════════════════════════

def query_rag(query, top_n=5):
    """查询本地RAG知识库"""
    try:
        result = subprocess.run(
            ['python', '-X', 'utf8', 'scripts/rag_query.py', query, '--top', str(top_n)],
            capture_output=True, text=True, timeout=60,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        if result.returncode == 0:
            return result.stdout
        else:
            return f"RAG查询未返回结果: {result.stderr[:200]}"
    except Exception as e:
        return f"RAG服务不可用: {e}"


def extract_rag_insights(raw_output, max_items=3):
    """从RAG原始输出中提取关键信息"""
    insights = []
    lines = raw_output.split('\n')
    current_source = ''
    current_text = ''

    for line in lines:
        if 'references/' in line or 'magazine/' in line or 'cases/' in line:
            if current_source and current_text:
                insights.append(f"- **{current_source}**: {current_text[:150]}...")
                if len(insights) >= max_items:
                    break
            current_source = line.strip().split('references/')[-1].split('.md')[0][:50] if 'references/' in line else '知识库'
            current_text = ''
        elif line.strip() and not line.startswith('[') and not line.startswith('==='):
            current_text += line.strip() + ' '

    if current_source and current_text and len(insights) < max_items:
        insights.append(f"- **{current_source}**: {current_text[:150]}...")

    return insights if insights else ['（RAG未检索到相关内容，建议手动补充）']


# ═══════════════════════════════════════════
# 三、方案生成引擎
# ═══════════════════════════════════════════

def generate_plan(audit_type, project_name, mode='plan', rag_results=None):
    """
    生成深度穿透策略方案

    Args:
        audit_type: 审计类型（预算执行/专项资金/采购/经济责任/工程/两新补贴/绩效/收支/国企）
        project_name: 项目名称
        mode: 'plan'=实施方案 | 'bid'=投标技术方案 | 'brief'=简要思路
        rag_results: RAG查询结果dict（可选）
    """
    if audit_type not in MATRIX:
        # 模糊匹配
        for key in MATRIX:
            if audit_type in key or key in audit_type:
                audit_type = key
                break
        else:
            return f"❌ 未识别的审计类型: {audit_type}\n支持类型: {', '.join(MATRIX.keys())}"

    matrix = MATRIX[audit_type]
    display = matrix['display']
    coordinates = matrix['coordinates']
    now = datetime.now().strftime('%Y-%m-%d %H:%M')

    # ── 头部 ──
    lines = []
    if mode == 'bid':
        lines.append(f'## 审计技术方案——深度穿透策略')
        lines.append(f'')
        lines.append(f'> 本项目依据《融策审计深度穿透方法论V2.0》的5坐标系×6审计类型矩阵，针对**{display}**特点，系统部署以下穿透式审计措施。')
    else:
        lines.append(f'## 深度穿透策略')
        lines.append(f'')
        lines.append(f'> 本项目依据《融策审计深度穿透方法论V2.0》的5坐标系×6审计类型矩阵，')
        lines.append(f'> 结合{display}的行业特点和风险高发领域，部署以下穿透式审计措施。')
        lines.append(f'> 策略生成时间：{now}')

    lines.append('')

    # ── 措施总表 ──
    lines.append(f'### 穿透措施一览（5坐标系部署）')
    lines.append('')
    lines.append(f'| 坐标系 | 核心穿透措施 | 适用规则 | 方法简介 |')
    lines.append(f'|:--|:--|:--|:--|')

    applicable_rules = []
    for coord_name, coord_data in coordinates.items():
        measures = '、'.join(coord_data['措施'][:3])
        rules = '、'.join(coord_data['规则']) if coord_data['规则'] else '—'
        method = coord_data['方法描述'][:80] + '…' if len(coord_data['方法描述']) > 80 else coord_data['方法描述']
        lines.append(f'| **{coord_name}** | {measures} | {rules} | {method} |')
        applicable_rules.extend(coord_data['规则'])

    lines.append('')

    # ── 详细措施 ──
    lines.append(f'### 各坐标系穿透措施详解')
    lines.append('')

    for coord_name, coord_data in coordinates.items():
        lines.append(f'#### {coord_name}坐标系')
        lines.append('')
        lines.append(f'**核心逻辑**：{coord_data["方法描述"]}')
        lines.append('')
        lines.append('**拟执行措施**：')
        for i, measure in enumerate(coord_data['措施'], 1):
            rules_str = f' [{", ".join(coord_data["规则"])}]' if coord_data['规则'] else ''
            lines.append(f'{i}. **{measure}**{rules_str}')
        lines.append('')

    # ── 规则执行计划 ──
    if applicable_rules:
        lines.append(f'### 自动化筛查规则执行计划')
        lines.append('')
        lines.append(f'| 规则编号 | 规则名称 | 数据要求 | 执行方式 |')
        lines.append(f'|:--|:--|:--|:--|')
        for rule in applicable_rules:
            rule_info = get_rule_info(rule)
            lines.append(f'| {rule} | {rule_info["name"]} | {rule_info["data"]} | {rule_info["method"]} |')
        lines.append('')

    # ── RAG知识库支撑 ──
    lines.append(f'### 知识库支撑')
    lines.append('')
    lines.append(f'本项目方案编制过程中检索了融策RAG审计知识库（16,000+知识块），以下为相关案例和方法论：')
    lines.append('')

    if rag_results:
        for query, result in rag_results.items():
            insights = extract_rag_insights(result) if result else ['（未检索到）']
            lines.append(f'**检索主题**：{query}')
            for ins in insights:
                lines.append(f'{ins}')
            lines.append('')
    else:
        lines.append('（RAG查询将在方案正式编制时执行，此处为框架占位）')
        lines.append('')

    # ── 案例产出目标 ──
    lines.append(f'### 预期案例产出')
    lines.append('')
    lines.append(f'本项目计划产出 **2-3篇** 审计案例，预期满足以下价值标准：')
    lines.append('')
    lines.append(f'- [ ] 暴露系统性漏洞（非偶发人为失误）')
    lines.append(f'- [ ] 运用创新审计方法（独立数据源交叉验证）')
    lines.append(f'- [ ] 推动制度性整改')
    lines.append(f'- [ ] 方法可推广至同类项目复用')
    lines.append('')

    # ── 落地排期（仅方案模式）──
    if mode == 'plan':
        lines.append(f'### 穿透措施落地排期')
        lines.append('')
        lines.append(f'| 阶段 | 时间 | 动作 | 责任人 |')
        lines.append(f'|:--|:--|:--|:--|')
        lines.append(f'| 审前研究 | 第1-2周 | 收集穿透所需独立数据源清单，RAG检索同类案例 | 项目负责人 |')
        lines.append(f'| 方案编制 | 第2-3周 | 确定各坐标系适用措施和规则，编制穿透方案 | 项目负责人 |')
        lines.append(f'| 数据采集 | 第3-4周 | 向被审计单位索要穿透所需数据（门禁/OA/供货记录等） | 数据分析岗 |')
        lines.append(f'| 现场实施 | 第4-8周 | 逐项执行穿透措施，每日复盘穿透进展 | 项目组 |')
        lines.append(f'| 报告编制 | 第9-10周 | 穿透发现写入报告，编制案例初稿 | 主审 |')
        lines.append(f'| 复盘归档 | 项目结束后1月 | 穿透方法入库，案例定稿归档 | 项目负责人 |')
        lines.append('')

    return '\n'.join(lines)


def get_rule_info(rule_id):
    """获取规则详细信息"""
    rules_db = {
        'E01': {'name': '门禁打卡×出差报销时空矛盾', 'data': '差旅报销表 + 门禁记录', 'method': '`python scripts/anomaly_rules/e01_door_access_vs_travel.py`'},
        'E02': {'name': '街景历史影像×验收照片比对', 'data': '验收照片(GPS+时间) + 街景API', 'method': '手动操作或API调用'},
        'E03': {'name': '受益对象GPS坐标地理聚类', 'data': '申报地址 + 地理编码API', 'method': 'Python脚本（待实现）'},
        'E04': {'name': '卫星影像×施工日志进度比对', 'data': '施工日志 + Google Earth', 'method': '手动操作Google Earth Pro'},
        'E05': {'name': '投标文件元数据同源检测', 'data': '投标文件.docx/.pdf', 'method': '`python scripts/anomaly_rules/e05_bid_metadata_homology.py`'},
        'E06': {'name': '评标专家×投标人时空交集', 'data': '评委名单+通信/酒店记录', 'method': '需合规授权后获取数据'},
        'E07': {'name': '领导行踪×决策时间线重建', 'data': '会议纪要+出差记录+GPS', 'method': '手动时间线比对'},
        'E08': {'name': '卫星影像×施工日志进度', 'data': '施工日志+Google Earth', 'method': '手动操作Google Earth Pro'},
        'E08b': {'name': '补贴收货地址地理聚类', 'data': '收货地址+地理编码API', 'method': 'Python脚本（待实现）'},
        'E09': {'name': '纸张消耗反推印刷量', 'data': '印刷报销+纸品采购记录', 'method': 'Excel公式计算'},
        'E10': {'name': '建材消耗反推实际建筑面积', 'data': '建材采购记录+验收面积', 'method': 'Python/Excel计算'},
        'E11': {'name': '耗材消耗反推检测真实性', 'data': '检测报告+耗材采购记录', 'method': 'Excel计算'},
        'E12': {'name': '商砼/钢材供货量反推工程量', 'data': '商砼站供货记录+结算清单', 'method': '数据比对'},
        'E13': {'name': '进销存三向比对', 'data': '进货+销售+库存台账', 'method': '`python scripts/anomaly_rules/e13_purchase_sales_inventory.py`'},
        'E14': {'name': '旧机回收量反推新品销售量', 'data': '以旧换新+回收登记台账', 'method': 'Excel比对'},
        'E15': {'name': '报销经办人×收款方工商关联', 'data': '报销台账+工商信息', 'method': '`python scripts/anomaly_rules/e15_handler_payee_association.py`'},
        'E16': {'name': '申报方×资金承接方股权穿透', 'data': '拨付台账+天眼查API', 'method': 'Python脚本（待实现）'},
        'E17': {'name': '领导干部亲属经商办企关联图谱', 'data': '个人事项+工商信息', 'method': '合规前提下执行'},
        'E18': {'name': '交叉任职与旋转门地图', 'data': '人事档案+供应商工商', 'method': '手动分析'},
        'E19': {'name': '审批时间行为模式异常检测', 'data': 'OA审批日志', 'method': 'Python脚本（待实现）'},
        'E19b': {'name': '离任前审批行为突变检测', 'data': '审批日志+离任日期', 'method': 'Python脚本（待实现）'},
        'E20': {'name': '报价数学规律异常检测', 'data': '开标一览表', 'method': 'Python脚本（待实现）'},
        'E21': {'name': '轮流中标模式检测', 'data': '3年+招投标台账', 'method': 'Python脚本（待实现）'},
        'E22': {'name': '紧急采购时间模式分析', 'data': '紧急采购台账', 'method': 'Excel分析'},
        'E23': {'name': '年末突击支出节奏检测', 'data': '月度支出数据', 'method': '`python scripts/anomaly_rules/e23_year_end_spending.py`'},
        'E24': {'name': '任期前后关键指标纵向对比', 'data': '连续5年财务数据', 'method': 'Excel折线图'},
        'E24b': {'name': '资金拨付节奏异常峰值检测', 'data': '拨付台账', 'method': 'Python/Excel'},
        'E24c': {'name': '补贴截止前申报冲量检测', 'data': '补贴申请台账', 'method': 'Python/Excel'},
    }
    return rules_db.get(rule_id, {'name': '未知规则', 'data': '—', 'method': '—'})


def interactive_mode():
    """交互模式：自然语言描述项目，自动识别类型并生成方案"""
    print("融策智能方案生成器 — 交互模式")
    print("═" * 50)
    print("请描述您的审计项目（或输入 'quit' 退出）：")
    print("示例：XX市财政局2026年度预算执行审计")
    print()

    desc = input("项目描述: ").strip()
    if desc.lower() == 'quit':
        return

    # 关键词匹配识别审计类型
    type_keywords = {
        '预算执行': ['预算执行', '预算', '决算', '三公', '国库'],
        '专项资金': ['专项资金', '专项', '补贴资金', '资金审计', '社保', '营养餐'],
        '采购': ['采购', '招投标', '招标', '投标', '政府采购', '围标', '串标'],
        '经济责任': ['经济责任', '经责', '离任', '任中', '自然资源'],
        '工程': ['工程', '竣工', '决算', '造价', '全过程', '结算'],
        '两新补贴': ['两新', '以旧换新', '消费补贴', '消费品'],
        '绩效': ['绩效', '绩效评价', '绩效评估'],
        '收支': ['收支', '财务收支'],
        '国企': ['国企', '国有', '集团', '国有资产'],
    }

    matched_type = None
    max_matches = 0
    for atype, keywords in type_keywords.items():
        matches = sum(1 for kw in keywords if kw in desc)
        if matches > max_matches:
            max_matches = matches
            matched_type = atype

    if not matched_type or max_matches == 0:
        print(f"\n⚠️ 无法自动识别审计类型，请从以下选择：")
        for key in MATRIX:
            print(f"  {key} — {MATRIX[key]['display']}")
        matched_type = input("请输入类型: ").strip()

    print(f"\n✅ 识别为: {MATRIX[matched_type]['display']}")
    print(f"正在查询RAG知识库...")

    # 执行RAG查询
    rag_results = {}
    for query in MATRIX[matched_type]['rag_queries'][:2]:  # 限2个查询控制时间
        print(f"  RAG检索: {query}")
        rag_results[query] = query_rag(query)

    # 生成方案
    plan = generate_plan(matched_type, desc, 'plan', rag_results)
    print(f"\n{'═' * 50}")
    print(plan)

    # 保存
    output_file = f'output/方案_深度穿透策略_{matched_type}_{datetime.now().strftime("%Y%m%d_%H%M")}.md'
    os.makedirs('output', exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(plan)
    print(f"\n💾 已保存至: {output_file}")


# ═══════════════════════════════════════════
# 四、CLI入口
# ═══════════════════════════════════════════

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='融策智能方案生成器 — 基于5坐标系×6审计类型矩阵+RAG知识库自动生成深度穿透策略',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python plan_generator.py --type 预算执行 --name "XX局2026年预算执行审计"
  python plan_generator.py --type 经济责任 --name "XX集团经责审计" --mode bid
  python plan_generator.py --type 两新补贴 --rag-only
  python plan_generator.py --interactive
  python plan_generator.py --list-types
        '''
    )
    parser.add_argument('--type', '-t', help='审计类型', choices=list(MATRIX.keys()))
    parser.add_argument('--name', '-n', default='待定项目', help='项目名称')
    parser.add_argument('--mode', '-m', default='plan', choices=['plan', 'bid', 'brief'],
                       help='输出模式: plan=实施方案, bid=投标技术方案, brief=简要思路')
    parser.add_argument('--rag-only', action='store_true', help='仅执行RAG查询，不生成方案')
    parser.add_argument('--no-rag', action='store_true', help='跳过RAG查询（仅用矩阵映射）')
    parser.add_argument('--list-types', action='store_true', help='列出支持的审计类型')
    parser.add_argument('--interactive', '-i', action='store_true', help='交互模式')
    parser.add_argument('-o', '--output', help='输出文件路径')

    args = parser.parse_args()

    if args.list_types:
        print("支持的审计类型（输入 --type 参数时使用简称）：")
        print()
        for key, info in MATRIX.items():
            coords = ', '.join(info['coordinates'].keys())
            rules_count = sum(len(c['规则']) for c in info['coordinates'].values())
            print(f"  {key:<8} → {info['display']:<20} 适用坐标系: {coords}  ({rules_count}条规则)")
        sys.exit(0)

    if args.interactive:
        interactive_mode()
        sys.exit(0)

    if not args.type:
        parser.print_help()
        print("\n💡 提示: 使用 --interactive 进入交互模式，或 --list-types 查看支持的审计类型")
        sys.exit(1)

    # RAG查询
    rag_results = {}
    if not args.no_rag:
        print(f"RAG知识库检索中...")
        for query in MATRIX[args.type]['rag_queries'][:2]:
            print(f"  检索: {query}")
            rag_results[query] = query_rag(query)
        print()

    if args.rag_only:
        print("═══ RAG检索结果 ═══")
        for query, result in rag_results.items():
            print(f"\n查询: {query}")
            print(result[:1000])
        sys.exit(0)

    # 生成方案
    plan = generate_plan(args.type, args.name, args.mode, rag_results)
    print(plan)

    # 保存
    if args.output:
        output_file = args.output
    else:
        filename = f'方案_深度穿透策略_{args.type}_{datetime.now().strftime("%Y%m%d_%H%M")}.md'
        output_file = os.path.join('output', filename)

    os.makedirs(os.path.dirname(output_file) or 'output', exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(plan)
    print(f"\n💾 已保存至: {output_file}")
