"""
从 INDEX.md 数据生成技能文件
"""
import os

SKILLS_DIR = r'D:\openclaw-workspace\skills\magazine-knowledge'
os.makedirs(SKILLS_DIR, exist_ok=True)

# Article data from INDEX.md (abbreviated)
# Each skill file maps to 融策 business line + technique + case reference

skills = {
    '01-magazine-index': {
        'name': 'magazine-knowledge-master',
        'desc': '杂志资料知识库总索引。覆盖《中国审计》1-5期+《审计案例》1-5册共251篇文章，按9大审计领域分类，含技术栈统计和方法论模式。触发：查案例/找方法/审计方法论。',
        'domain': '跨领域',
        'applies': '全部12类审计业务',
    },
    '02-fiscal-audit-methods': {
        'name': 'magazine-fiscal-audit',
        'desc': '财政审计方法体系（28篇案例）。覆盖预算执行/专项债券/以旧换新补贴/政府采购/公务支出/政府投资基金。核心技术：资金流水追踪/发票链追踪/政策比对/补贴流穿透。触发：财政审计/预算审计/补贴核查。',
        'domain': '财政审计',
        'applies': '政府资金专项审计/预算绩效管理/政府补贴审计/收支审计',
    },
    '03-agriculture-audit-methods': {
        'name': 'magazine-agriculture-audit',
        'desc': '农业农村审计方法体系（17篇案例）。覆盖高标准农田/农业保险/乡村振兴/涉农补贴/有机肥质量鉴定/土地整治。核心技术：五维资金穿透/保单穿透/工程量核查/政策执行比对。触发：农业审计/涉农资金/乡村振兴。',
        'domain': '农业农村审计',
        'applies': '政府资金专项审计/涉农补贴审计/乡村振兴绩效评价',
    },
    '04-livelihood-audit-methods': {
        'name': 'magazine-livelihood-audit',
        'desc': '民生审计方法体系（27篇案例）。覆盖教育/医疗/食品安全/殡葬/养老/保障房/工伤保险。核心技术：大数据比对/医保数据穿透/收费合规性核查/供应商画像。触发：民生审计/社保审计/教育审计/医疗审计。',
        'domain': '民生审计',
        'applies': '社保资金审计/营养餐审计/绩效评价/政府补贴审计',
    },
    '05-investment-audit-methods': {
        'name': 'magazine-investment-audit',
        'desc': '投资审计方法体系（8篇案例+10篇专题）。覆盖工程招标/征地拆迁/基建造价/政府投资/超长期国债。核心技术：穿透式审计/GIS+征拆/造价核查/RPA+图数据库围标识别。触发：投资审计/工程审计/招投标。',
        'domain': '投资审计',
        'applies': '招投标审计/工程竣工决算审计/全过程工程咨询',
    },
    '06-econ-responsibility-methods': {
        'name': 'magazine-econ-responsibility',
        'desc': '经济责任审计方法体系（6篇案例）。覆盖任中/离任/自然资源经责。核心技术：微腐败六类识别/车轮腐败专项/Python爬虫评审/方案全流程贯通。触发：经责审计/领导干部审计。',
        'domain': '经济责任审计',
        'applies': '经济责任审计/自然资源经责审计',
    },
    '07-resource-env-methods': {
        'name': 'magazine-resource-env',
        'desc': '资源环境审计方法体系（7篇案例+GIS专题）。覆盖矿产/土地/林业/水/生态。核心技术：卫星影像对比/ArcGIS+奥维双平台/QGIS+NDVI/无人机航测/历史影像对比。触发：资源审计/环境审计/土地审计。',
        'domain': '资源环境审计',
        'applies': '能源审计/碳中和审计/资产清查',
    },
    '08-enterprise-audit-methods': {
        'name': 'magazine-enterprise-audit',
        'desc': '企业审计方法体系（6篇案例）。覆盖应收/存货/关联交易/IT投资/生物资产/国企。核心技术：五看框架/应收七步法/关联方五层穿透/存货审计/融资合规性。触发：企业审计/国企审计。',
        'domain': '企业审计',
        'applies': '国企专项审计/成本效益审计/往来款清理',
    },
    '09-financial-audit-methods': {
        'name': 'magazine-financial-audit',
        'desc': '金融审计方法体系（3篇案例+银行专题）。覆盖银行违规/保险穿透/收益分析。核心技术：SQL数据分析模型/多层次交叉验证/保单穿透。触发：金融审计/银行审计/保险审计。',
        'domain': '金融审计',
        'applies': '政府资金专项审计/金融补贴审计',
    },
    '10-tech-methods-cross': {
        'name': 'magazine-tech-cross',
        'desc': '跨领域技术方法大全（15篇方法论文章）。覆盖SQL六模式/Python四模式/GIS五模式/图数据库/RPA/机器学习。每项技术配具体案例和SQL/Python代码模板。触发：写SQL/用Python/GIS分析/大数据分析。',
        'domain': '跨领域技术',
        'applies': '全部12类审计业务（技术赋能）',
    },
    '11-audit-patterns': {
        'name': 'magazine-audit-patterns',
        'desc': '七大审计方法模式（从251篇案例中提炼）。1)疑点导向→多源比对→现场核实 2)数据模型→画像→关系网络 3)卫星遥感→GIS叠加→空间分析 4)SQL/Python→清洗→异常检测 5)政策比对→资金穿透→实物核查 6)合同审查→票据追踪→访谈印证 7)多源数据碰撞→交叉验证→可视化。触发：设计审计方案/选择审计方法。',
        'domain': '跨领域',
        'applies': '全部12类审计业务',
    },
}

for filename, info in skills.items():
    content = f'''---
name: {info['name']}
description: {info['desc']}
---

# {info['domain']}方法体系（杂志资料提炼）

> 数据来源：《中国审计》2026年1-5期 + 《审计案例》1-5册（251篇）
> 融策适配：{info['applies']}

## 来源

本技能从 Obsidian 杂志资料库中提炼，原始 PDF 位于：
`C:\\Users\\scrccpa\\Documents\\Obsidian Vault\\杂志资料\\`

完整索引见：`C:\\Users\\scrccpa\\Documents\\Obsidian Vault\\杂志资料\\INDEX.md`

## 使用方法

触发本技能后，将自动检索对应领域的所有案例文章（MD文件），
提取相关技术方法和审计逻辑，匹配融策业务场景。

## 相关技能

{chr(10).join([f'- [[{s["name"]}]] - {s["domain"]}' for fn, s in list(skills.items())[:8]])}

---
*由 magazine-knowledge 系统于 2026-06-21 生成（Origin: INDEX.md）*
'''

    filepath = os.path.join(SKILLS_DIR, f'{filename}.md')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'  Created: {filename}.md')

print(f'\n{len(skills)} skill files created in {SKILLS_DIR}')
