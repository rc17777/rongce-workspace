"""Apply keyword updates from co-occurrence analysis to business_lines.yaml"""
import yaml, sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'C:\Users\scrccpa\.openclaw\workspace\knowledge\taxonomy\business_lines.yaml'
with open(path, 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f)

updates = {
    'L1': {'secondary': ['党政领导干部', '国有企事业单位领导人', '任期经济责任',
                          '三重一大', '廉政', '定责', '责任界定', '党政', '领导人员', '任期', '干部监督']},
    'L2': {'secondary': ['三公经费', '小金库', '部门预算收支', '财政拨款', '预算单位财务',
                          '罚没收入', '上缴']},
    'L3': {'secondary': ['结转结余', '超预算支出', '无预算支出', '预算批复', '预算调整', '预算公开',
                          '零基预算', '过紧日子', '预算一体化', '人大监督']},
    'L4': {'secondary': ['补助资金', '补贴资金', '截留挪用', '套取资金', '滞留资金', '配套资金',
                          '统筹整合', '事权支出', '资金拨付', '乡村振兴']},
    'L5': {'primary': ['往来款清理', '往来款项', '应收应付', '债权债务', '坏账', '呆账', '应收款', '逾期'],
           'secondary': ['挂账', '长期未清', '借款清理', '其他应收款', '其他应付款', '账龄分析',
                         '清收', '催收', '预付账款', '坏账核销']},
    'L6': {'secondary': ['招标文件', '投标人', '中标结果', '公开招标', '邀请招标', '竞争性谈判',
                          '询价采购', '单一来源', '陪标', '串通投标']},
    'L7': {'secondary': ['国资委', '混合所有制', '国有控股', '出资人', '保值增值', '公司治理', '改制',
                          '资产盘活', '闲置资产', '资产流失', '出租出借']},
    'L8': {'primary': ['成本效益分析', '投入产出', '成本控制', '盈亏平衡', '量本利', '经济性'],
           'secondary': ['单价核定', '定额标准', '成本核算', '费用控制', '经济评价', '造价分析',
                         '业财融合', '节约']},
    'L9': {'secondary': ['节能减排', '能源管理', '可再生能源', '清洁能源', '用能单位', '减排', '排放']},
    'L10': {'secondary': ['待摊投资', '建安工程费', '征地拆迁', '竣工验收', '建设单位管理费',
                           '勘察设计费', '监理费', '固定资产投资', '工程造价', '工程款']},
    'L11': {'secondary': ['绩效指标体系', '绩效自评', '再评价', '结果应用', '绩效运行监控', '满意度调查',
                           '无效', '挂钩', '全面实施']},
    'L12': {'primary': ['政府补贴', '财政补贴', '惠企政策', '奖补资金', '稳岗返还', '就业补贴', '公平竞争审查'],
            'secondary': ['补贴申报', '虚报冒领', '重复补贴', '补贴公示', '资格审核', '产业扶持资金',
                          '招商引资', '优惠', '兑现', '负面清单']},
    'L13': {'primary': ['监督检查', '财经纪律', '会计信息质量检查', '预决算公开', '直达资金', '严肃财经纪律'],
            'secondary': ['财政监督', '会计监督', '专项检查', '整改落实', '问题清单', '违规问题线索',
                          '纪检监察', '整治', '会计法', '财经秩序']},
}

changes = 0
for node in data['nodes']:
    lid = node['id']
    if lid not in updates:
        continue
    upd = updates[lid]
    kw = node.get('keywords', {})
    for key in ['primary', 'secondary']:
        if key in upd:
            old = kw.get(key, [])
            kw[key] = upd[key]
            print(f"  {lid}: {key} {len(old)}→{len(upd[key])} (+{len(upd[key])-len(old)})")
            changes += 1

# Save
with open(path, 'w', encoding='utf-8') as f:
    yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False, width=200)

print(f"\n✅ {changes} keyword fields updated, saved to {path}")
