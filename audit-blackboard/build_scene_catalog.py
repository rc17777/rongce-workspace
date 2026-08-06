# -*- coding: utf-8 -*-
"""
按业务场景归档 135 个政府审计算法 → 算法库场景目录
产出:
  1. audit-blackboard/scene_taxonomy.json      标准业务场景体系（两级）
  2. audit-blackboard/algorithms_by_scene.json 场景 → 算法列表（机器用）
  3. audit-blackboard/ALGORITHMS_BY_SCENE.md   按场景目录文档（人读）
"""
import json, sys, os, re
from collections import OrderedDict
sys.stdout.reconfigure(encoding='utf-8')

BASE = r'C:\Users\scrccpa\.openclaw\workspace\audit-blackboard'
REG = os.path.join(BASE, 'algorithm_registry.json')

# ============ 1. 标准业务场景体系（一级15类 + 二级细分） ============
TAXONOMY = OrderedDict([
    ("招投标与政府采购", ["围标串标", "供应商审查", "电子卖场与价格", "评标与暗标"]),
    ("农业农村审计", ["涉农补贴与保险", "乡村振兴产业", "村级财务", "粮食储备"]),
    ("民生与社保医保", ["社保基金", "医保基金", "养老与救助", "就业与消费补贴", "工伤保障"]),
    ("金融审计", ["信贷与银行", "保险基金", "资管与基金投资"]),
    ("工程与投资审计", ["竣工决算与结算", "工程量与造价", "征地拆迁", "政府投资项目", "信息化项目"]),
    ("资源环境审计", ["自然资源资产", "遥感与地理信息", "矿业与土地", "生态环保"]),
    ("国企审计", ["亏损与投资损失", "研发与人力", "供应链与中间人", "国资运营"]),
    ("财政与政府债务", ["专项债", "转移支付", "债务风险与化债", "特许经营"]),
    ("预算执行与财政管理", ["预算执行", "公用经费与三公", "非税收入", "预算编制与评审"]),
    ("绩效评价", ["绩效指标", "成本效益", "预算绩效管理"]),
    ("经济责任审计", ["经责核查", "离任审计"]),
    ("监督检查与经费舞弊", ["小金库与资金套取", "差旅与报销", "人员经费", "举报监督"]),
    ("税务审计", ["发票与税收", "平台经济"]),
    ("全场景通用", ["数据勾稽与核对", "SQL审计范式", "规则匹配", "风险画像与预警"]),
])

# ============ 2. 关键词 → 场景 规则（主场景判定，按顺序优先） ============
# (一级场景, [关键词列表]) —— 命中即归入；主场景取第一个命中的规则
# 注："全场景通用"置顶，只保留强信号词（"全场景"/"所有审计业务场景"），避免误伤业务算法
SCENE_RULES = [
    ("全场景通用", ["全场景", "所有审计业务场景"]),
    ("招投标与政府采购", ["围标", "串标", "陪标", "投标", "招标", "政府采购", "采购集中", "供应商", "电子卖场", "评标", "暗标", "中标", "产权交易", "受控拍卖", "采购审计", "招投标", "排他性参数", "保证金", "采购"]),
    ("农业农村审计", ["农业", "农机", "高标准农田", "乡村振兴", "村级", "储备粮", "粮食", "涉农", "帮扶", "以工代赈", "农村", "农险", "畜牧", "养殖"]),
    ("民生与社保医保", ["社保", "医保", "生育", "养老", "工伤", "就业", "惠民", "消费券", "消费补贴", "居家养老", "救助", "殡葬", "燃气补贴", "公租房", "DRG", "耗材", "医疗", "医保基金", "工伤保险", "失业保险", "补贴对象", "顶格申报", "减租", "适老化", "以旧换新", "促消费", "焕新"]),
    ("金融审计", ["信贷", "银行", "保险", "资管", "农商行", "快贷", "投保", "理赔", "金融机构", "金融服务", "空壳公司", "金融"]),
    ("工程与投资审计", ["竣工决算", "工程结算", "工程量", "造价", "土方", "征拆", "补偿", "签证", "GIS", "征地", "基本建设", "政府投资", "投资审计", "水利项目", "通信工程", "工程"]),
    ("资源环境审计", ["自然资源", "遥感", "耕地", "林地", "矿业权", "采矿", "公益林", "土地", "环保", "生态", "水资源", "污水处理费", "地表", "图斑", "退二进三"]),
    ("国企审计", ["国企", "国有企业", "集团", "亏损项目", "研发支出", "中间人", "高息融资", "贸易", "供应链", "国资", "子公司", "客户经理", "六步穿透", "三程序"]),
    ("财政与政府债务", ["专项债", "政府债务", "转移支付", "化债", "特许经营", "债券", "县域财政", "财政风险", "基金", "收支自平衡", "特别国债", "奖补"]),
    ("预算执行与财政管理", ["预算执行", "预算编制", "公用经费", "三公", "公务用车", "非税收入", "预算评审", "零基预算", "支出标准", "预算绩效", "成本预算绩效", "往来科目", "存量资金", "通信费用", "预算", "公用事业"]),
    ("绩效评价", ["绩效", "成本效益", "偏离度", "效益", "评价"]),
    ("经济责任审计", ["经济责任", "经责", "离任", "领导干部", "自然资源资产离任"]),
    ("监督检查与经费舞弊", ["小金库", "差旅", "报销", "吃空饷", "虚列", "举报", "财会监督", "八项规定", "人员经费", "违规", "监督", "白条", "五对照", "四信号"]),
    ("税务审计", ["税务", "税收", "虚开", "税源", "注销", "平台经济", "货运"]),
]

# ============ 3. 加载注册表 ============
with open(REG, encoding='utf-8') as f:
    data = json.load(f)
algs = data['algorithms']

def match_scenes(alg):
    """返回 (主场景, [附加场景])"""
    text = ' '.join([
        alg.get('name', ''),
        alg.get('biz_scene', ''),
        alg.get('biz_line', ''),
        alg.get('scene_text', ''),
    ])
    hits = []
    for scene, kws in SCENE_RULES:
        for kw in kws:
            if kw in text:
                hits.append(scene)
                break
    # 去重保序
    seen = []
    for h in hits:
        if h not in seen:
            seen.append(h)
    if not seen:
        return ('全场景通用', [])
    primary = seen[0]
    return (primary, seen[1:])

# ============ 4. 生成映射 ============
by_scene = OrderedDict((s, []) for s in TAXONOMY)
unmapped = []
for code, alg in sorted(algs.items()):
    primary, extra = match_scenes(alg)
    item = {
        'sn': code,
        'name': alg.get('name', '?'),
        'type': alg.get('type', '?'),
        'priority': alg.get('priority', '?'),
        'complexity': alg.get('complexity', '?'),
        'risk_mechanism': alg.get('risk_mechanism', alg.get('family', '?')),
        'agents': alg.get('assigned_agents', []),
        'scene': alg.get('biz_scene', ''),
        'primary_scene': primary,
        'extra_scenes': extra,
    }
    by_scene[primary].append(item)
    for ex in extra:
        by_scene[ex].append(item)

# 检查未映射
for s, items in by_scene.items():
    print('{:14s} {:3d} 个算法'.format(s, len(items)))
total_primary = sum(len(v) for k, v in by_scene.items() if k in TAXONOMY)
print('主场景覆盖:', total_primary, '/', len(algs))

# 二级细分：按关键词细化（仅文档用）
def sub_scene_of(scene, text):
    subs = TAXONOMY.get(scene, [])
    for sub in subs:
        # 二级关键词
        SUB_KW = {
            "围标串标": ["围标", "串标", "陪标", "暗标", "特征码", "共同投标", "轮庄", "指纹"],
            "供应商审查": ["供应商", "虚假材料", "关联方", "壳特征", "集中度", "三查", "13维"],
            "电子卖场与价格": ["电子卖场", "价格偏离", "比价"],
            "评标与暗标": ["评标", "暗标", "偏离", "评分"],
            "涉农补贴与保险": ["农业保险", "补贴", "农机", "农险", "投保", "理赔", "骗补"],
            "乡村振兴产业": ["乡村振兴", "产业", "合资", "帮扶", "以工代赈"],
            "村级财务": ["村级", "白条"],
            "粮食储备": ["储备粮", "粮食", "粮库"],
            "社保基金": ["社保", "养老保险", "参保"],
            "医保基金": ["医保", "DRG", "耗材", "套码"],
            "养老与救助": ["养老", "救助", "殡葬"],
            "就业与消费补贴": ["就业", "消费券", "消费补贴", "以旧换新", "减租"],
            "工伤保障": ["工伤", "辅助器具"],
            "信贷与银行": ["信贷", "银行", "农商行", "快贷", "空壳"],
            "保险基金": ["保险", "投保", "理赔", "政策性农业保险"],
            "资管与基金投资": ["资管", "估值", "刚性兑付", "投资基金", "画皮"],
            "竣工决算与结算": ["竣工决算", "结算", "一审", "抽样"],
            "工程量与造价": ["工程量", "造价", "土方", "签证", "软件造价"],
            "征地拆迁": ["征拆", "征地", "补偿", "图斑-影像"],
            "政府投资项目": ["政府投资", "规避审批", "概算", "水利项目", "防洪"],
            "信息化项目": ["信息化", "软件造价", "IT"],
            "自然资源资产": ["自然资源", "离任", "经责审计清单"],
            "遥感与地理信息": ["遥感", "GIS", "图斑", "NDVI", "变化检测"],
            "矿业与土地": ["矿业权", "采矿", "土地", "退二进三", "公益林"],
            "生态环保": ["生态", "环保"],
            "亏损与投资损失": ["亏损", "六步穿透", "投资损失"],
            "研发与人力": ["研发", "人力", "培训", "在职不在岗", "工资"],
            "供应链与中间人": ["中间人", "供应链", "贸易", "绕道"],
            "国资运营": ["国资", "出租", "代征", "非税"],
            "专项债": ["专项债", "债券"],
            "转移支付": ["转移支付"],
            "债务风险与化债": ["债务", "化债", "县域财政", "风险预警"],
            "特许经营": ["特许经营", "PPP", "BOO", "BOT"],
            "预算执行": ["预算执行", "60条", "违规清单"],
            "公用经费与三公": ["公用经费", "三公", "公务用车", "通信费用", "车辆"],
            "非税收入": ["非税收入", "代征", "污水处理费", "水费", "燃气"],
            "预算编制与评审": ["预算编制", "预算评审", "零基预算", "支出标准", "申报"],
            "绩效指标": ["绩效", "偏离度", "指标"],
            "成本效益": ["成本效益", "成本预算绩效", "六步法"],
            "预算绩效管理": ["预算绩效管理", "绩效评价"],
            "经责核查": ["经济责任", "经责", "三账比对", "未履约"],
            "离任审计": ["离任", "自然资源资产离任"],
            "小金库与资金套取": ["小金库", "套取", "回流", "画皮", "三分类", "五对照"],
            "差旅与报销": ["差旅", "报销", "四信号", "发票", "整百"],
            "人员经费": ["吃空饷", "人员经费", "在职不在岗", "工资"],
            "举报监督": ["举报", "财会监督", "闭环"],
            "发票与税收": ["发票", "虚开", "税收", "税务"],
            "平台经济": ["平台经济", "网络货运", "货运"],
            "数据勾稽与核对": ["勾稽", "核对", "比对", "三账"],
            "SQL审计范式": ["SQL", "范式"],
            "规则匹配": ["规则", "匹配", "语义相似度"],
            "风险画像与预警": ["风险画像", "预警", "Benford"],
        }
        for kw in SUB_KW.get(sub, []):
            if kw in text:
                return sub
    return None

# 生成文档
doc_lines = []
doc_lines.append('# 政府审计算法库 · 按业务场景目录（135 算法）\n')
doc_lines.append('> 来源：`audit-blackboard/algorithm_registry.json`（v{ver}） ｜ 生成：{date} ｜ 一级场景 {n1} 类，二级细分 {n2} 类\n'.format(
    ver=data.get('version', '?'), date=data.get('generated_at', '?'),
    n1=len(TAXONOMY), n2=sum(len(v) for v in TAXONOMY.values())))
doc_lines.append('> 旗舰=P0（40） ｜ 骨架=P1（95） ｜ 一个算法可归属多个场景（主场景+附加场景）\n')
doc_lines.append('---\n')

total_flag = sum(1 for a in algs.values() if a.get('type') == '旗舰')
doc_lines.append('## 全景统计\n')
doc_lines.append('| 指标 | 数值 |')
doc_lines.append('|:--|:--|')
doc_lines.append('| 算法总数 | {} |'.format(len(algs)))
doc_lines.append('| 旗舰 P0 | {} |'.format(total_flag))
doc_lines.append('| 骨架 P1 | {} |'.format(len(algs) - total_flag))
doc_lines.append('| 一级业务场景 | {} 类 |'.format(len(TAXONOMY)))
doc_lines.append('| 二级细分 | {} 类 |'.format(sum(len(v) for v in TAXONOMY.values())))
doc_lines.append('')

# 每场景一节
for scene, subs in TAXONOMY.items():
    items = by_scene.get(scene, [])
    if not items:
        continue
    flag_n = sum(1 for i in items if i['type'] == '旗舰')
    doc_lines.append('## {}（{} 个算法，旗舰 {}）\n'.format(scene, len(items), flag_n))
    doc_lines.append('| 编号 | 算法名称 | 类型 | 优先级 | 复杂度 | 风险机制 | 主战Agent | 二级细分 | 归属 |')
    doc_lines.append('|:--|:--|:--|:--|:--|:--|:--|:--|:--|')
    for i in sorted(items, key=lambda x: (x['type'] != '旗舰', x['sn'])):
        agents = ','.join(i['agents'][:2]) if i['agents'] else '—'
        text = ' '.join([i['name'], i['scene']])
        sub = sub_scene_of(scene, text) or '—'
        # 归属：主场景 / 附加场景
        belong = '主' if i.get('primary_scene') == scene else '附'
        doc_lines.append('| {} | {} | {} | {} | {} | {} | {} | {} | {} |'.format(
            i['sn'], i['name'], i['type'], i['priority'], i['complexity'],
            i['risk_mechanism'], agents, sub, belong))
    doc_lines.append('')

# 追加使用说明
doc_lines.append('---\n')
doc_lines.append('## 使用说明\n')
doc_lines.append('- **归属列**：`主`=该算法在此场景的主场景，`附`=附加适用场景（一个算法可有多个附加场景）\n')
doc_lines.append('- 程序化查询：`python -X utf8 -c "from algorithm_loader import list_algorithms_by_scene; import json; print(json.dumps(list_algorithms_by_scene(\'社保审计\'), ensure_ascii=False, indent=1))"`\n')
doc_lines.append('- 场景体系定义：`scene_taxonomy.json` ｜ 场景→算法映射：`algorithms_by_scene.json`\n')
doc_lines.append('- 重建本文档：`python -X utf8 build_scene_catalog.py`（读取 algorithm_registry.json 重新生成）\n')

# 保存文档
doc_path = os.path.join(BASE, 'ALGORITHMS_BY_SCENE.md')
with open(doc_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(doc_lines))
print('\n文档已生成:', doc_path)

# 保存 taxonomy
tax_path = os.path.join(BASE, 'scene_taxonomy.json')
with open(tax_path, 'w', encoding='utf-8') as f:
    json.dump({'version': '1.0', 'generated_at': data.get('generated_at'),
               'description': '政府审计算法库 标准业务场景体系（一级+二级）',
               'taxonomy': TAXONOMY, 'scene_rules': SCENE_RULES},
              f, ensure_ascii=False, indent=2)
print('Taxonomy 已保存:', tax_path)

# 保存 by_scene JSON
bs_path = os.path.join(BASE, 'algorithms_by_scene.json')
with open(bs_path, 'w', encoding='utf-8') as f:
    json.dump({'version': '1.0', 'generated_at': data.get('generated_at'),
               'total_algorithms': len(algs),
               'scenes': by_scene}, f, ensure_ascii=False, indent=2)
print('场景映射已保存:', bs_path)
