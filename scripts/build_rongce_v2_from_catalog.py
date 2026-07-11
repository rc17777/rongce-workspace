#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build Rongce audit operating system v2.0 from the whole Obsidian audit catalog."""
from __future__ import annotations

import ast
import json
import re
from collections import defaultdict
from pathlib import Path

VAULT = Path(r'C:\Users\scrccpa\Documents\Obsidian Vault')
CATALOG = VAULT / '审计资料清单.json'
BASE = VAULT / '审计案例库-OCR' / '融策标准作业体系 v2.0'
TRAINING = BASE / '01-训练清单' / '场景-审计逻辑-可复用方法训练清单 v2.0.md'
CARDS = BASE / '02-案例卡片'
TEMPLATES = BASE / '03-融策审计项目可直接套用模板包'
STANDARD = BASE / '04-融策标准作业包 v2.0'
PRACTICAL = BASE / '05-融策实战试点包 v2.0'

CORE_SCENES = [
    '工程审计', '政策落实审计', '国企审计', '信息系统审计', '农业农村审计',
    '预算执行审计', '绩效审计', '经济责任审计', '社保民生审计', '资源环境审计',
    '专项资金审计', '金融审计', '内部审计', '教科文卫审计', '其他审计'
]

GENERATED_MARKERS = ['案例卡片', '模板', '标准作业包', '实战试点包', '训练清单', '方法词典', '资料总览', '老板版', '融策标准作业体系']

SCENE_PROFILES = {
    '工程审计': ('工程项目、招投标、合同执行、变更签证、结算支付', ['招投标链条拆解', '交易台账比对', '合同支付穿透', '现场踏勘']),
    '政策落实审计': ('重大政策部署、专项资金、项目落地、部门协同、整改闭环', ['政策链条对标', '资金直达核查', '部门协同验证', '整改回头看']),
    '国企审计': ('国资安全、企业治理、投资经营、奖补资金、风险内控', ['三重一大核查', '资金流向穿透', '异常交易筛查', '内控测试']),
    '信息系统审计': ('多源数据、业务系统、医保卫健、模型筛查、数据治理', ['字段清洗', '跨系统比对', 'SQL疑点筛查', '规则校验']),
    '农业农村审计': ('乡村振兴、涉农资金、基层项目、高标准农田、补贴发放', ['涉农台账比对', '受益对象核验', '现场踏勘/无人机', '资金绩效分析']),
    '预算执行审计': ('预算编制、预算执行、财政收支、专项支出和绩效结果', ['预算指标比对', '支付进度分析', '结余结转核查', '三公经费筛查']),
    '绩效审计': ('目标设定、投入产出、效益评价、绩效整改', ['绩效目标对标', '指标完成度分析', '成本效益分析', '整改闭环']),
    '经济责任审计': ('领导干部履职、权力运行、重大决策、责任界定', ['权责清单对照', '重大事项穿透', '政绩观偏差识别', '责任链条分析']),
    '社保民生审计': ('民生政策、社保医保、教育医疗、群众利益', ['受益对象比对', '资金发放核查', '服务真实性验证', '群众诉求线索']),
    '资源环境审计': ('自然资源资产、生态补偿、绿色发展、环境治理', ['资源台账比对', '生态补偿资金核查', '现场核验', '整改效果跟踪']),
    '专项资金审计': ('专项资金分配、拨付、使用、绩效和监管', ['资金链条穿透', '项目库比对', '票据凭证核验', '绩效评价']),
    '金融审计': ('保证金、融资、债务、资金链条和金融风险', ['资金流水核查', '担保关系穿透', '债务台账比对', '异常交易识别']),
    '内部审计': ('内控、风险管理、公司治理、整改闭环', ['内控制度测试', '风险清单核验', '整改台账跟踪', '治理建议转化']),
    '教科文卫审计': ('教育、科技、文化、卫生项目和资金绩效', ['项目资金核查', '服务真实性验证', '绩效指标分析', '业务数据比对']),
    '其他审计': ('审计管理、研究型审计、方法论和综合案例', ['研究型审计', '经验复盘', '制度机制分析', '成果转化']),
}


def is_generated(item: dict) -> bool:
    path = item.get('path', '')
    title = item.get('title', '')
    return any(m in path or m in title for m in GENERATED_MARKERS)


def read_md(item: dict) -> str:
    return (VAULT / item['path']).read_text(encoding='utf-8', errors='replace')


def extract_section(text: str, heading: str) -> str:
    m = re.search(rf'## {re.escape(heading)}\n\n(.*?)(?:\n## |\Z)', text, re.S)
    return m.group(1).strip() if m else ''


def yaml_field_list(text: str, field: str) -> list[str]:
    head = ''
    if text.startswith('---'):
        end = text.find('---', 3)
        if end > 0:
            head = text[3:end]
    m = re.search(rf'(?m)^{field}:\s*(\[.*?\])\s*$', head)
    if m:
        try:
            val = ast.literal_eval(m.group(1))
            if isinstance(val, list):
                return [str(x) for x in val if str(x).strip()]
        except Exception:
            pass
    return []


def bullets_from_section(text: str, heading: str, limit=3) -> list[str]:
    body = extract_section(text, heading)
    out = []
    for line in body.splitlines():
        line = line.strip()
        if re.match(r'^(?:\d+\.|-)\s+', line):
            out.append(re.sub(r'^(?:\d+\.|-)\s+', '', line))
    return out[:limit]


def get_findings(text: str, limit=3) -> list[str]:
    return (yaml_field_list(text, 'findings') or bullets_from_section(text, '审计发现线索', limit))[:limit]


def get_recs(text: str, limit=3) -> list[str]:
    return (yaml_field_list(text, 'recommendations') or bullets_from_section(text, '审计建议', limit))[:limit]


def get_keywords(text: str) -> list[str]:
    return yaml_field_list(text, 'keywords')[:10]


def summary(text: str, n=180) -> str:
    body = extract_section(text, '内容摘要')
    if not body:
        body = re.sub(r'^---.*?---', '', text, flags=re.S).strip()
    body = re.sub(r'\s+', '', body)
    return body[:n] + ('...' if len(body) > n else '')


def methods(scene: str, text: str, kws: list[str]) -> list[str]:
    joined = ''.join(kws) + summary(text, 500) + ''.join(get_findings(text, 3))
    rules = [
        ('数据比对', ['数据', 'SQL', 'Excel', '比对', '关联']),
        ('穿透核查', ['穿透', '全流程', '链条', '核查']),
        ('现场踏勘', ['现场', '实地', '踏勘', '勘验', '走访']),
        ('政策对标', ['政策', '规划', '落实', '两重', '两新']),
        ('资金绩效分析', ['资金', '绩效', '补助', '奖补', '预算']),
        ('模型/相似度筛查', ['模型', '相似度', '算法', '异常', '画像']),
        ('整改闭环', ['整改', '回头看', '长效机制', '闭环']),
    ]
    found = [name for name, words in rules if any(w in joined for w in words)]
    profile = SCENE_PROFILES.get(scene)
    if profile:
        found.extend(profile[1][:2])
    dedup = []
    for x in found:
        if x not in dedup:
            dedup.append(x)
    return dedup[:6] or ['问题导向分析']


def load_cases():
    data = json.loads(CATALOG.read_text(encoding='utf-8'))
    cases = []
    for item in data:
        scene = item.get('scene', '')
        if scene not in CORE_SCENES or is_generated(item):
            continue
        fp = VAULT / item['path']
        if not fp.exists():
            continue
        cases.append(item)
    return cases


def select_cards(cases, per_scene=3):
    by_scene = defaultdict(list)
    for item in cases:
        score = (3 if item.get('has_findings') else 0) + (2 if item.get('has_keywords') else 0)
        title = item.get('title', '')
        if any(k in title for k in ['思路', '方法', '重点', '审计', '案例', '数据', '资金']):
            score += 2
        by_scene[item['scene']].append((score, item))
    selected = []
    for scene in CORE_SCENES:
        ranked = sorted(by_scene.get(scene, []), key=lambda x: (-x[0], x[1].get('title', '')))
        selected.extend([item for _, item in ranked[:per_scene]])
    return selected


def write_training(cases):
    TRAINING.parent.mkdir(parents=True, exist_ok=True)
    by_scene = defaultdict(list)
    for item in cases:
        by_scene[item['scene']].append(item)
    lines = ['---', 'title: "融策全库-场景-审计逻辑-可复用方法训练清单 v2.0"', 'scene: 训练清单', 'tags: [融策, 训练清单, v2.0]', '---\n', '# 融策全库｜场景-审计逻辑-可复用方法训练清单 v2.0\n', '> 来源：Obsidian 审计资料清单，过滤二次生成物后按场景提炼。\n']
    for scene in CORE_SCENES:
        items = by_scene.get(scene, [])
        if not items:
            continue
        lines.append(f'## {scene}\n')
        for item in items[:10]:
            text = read_md(item)
            kws = get_keywords(text)
            fs = get_findings(text, 2)
            rs = get_recs(text, 2)
            ms = methods(scene, text, kws)
            lines.append(f'### {item["title"]}')
            lines.append(f'- 路径：`{item["path"]}`')
            lines.append(f'- 审计逻辑：{summary(text, 160)}')
            lines.append(f'- 关键疑点：' + ('；'.join(fs) if fs else '（待补）'))
            lines.append(f'- 可复用方法：' + ' / '.join(ms))
            lines.append(f'- 建议抓手：' + ('；'.join(rs) if rs else '围绕问题清单限期整改，推动制度完善和闭环管理。'))
            lines.append('')
    TRAINING.write_text('\n'.join(lines), encoding='utf-8')


def write_cards(selected):
    CARDS.mkdir(parents=True, exist_ok=True)
    for item in selected:
        text = read_md(item)
        scene = item['scene']
        kws = get_keywords(text)
        fs = get_findings(text, 4)
        rs = get_recs(text, 4)
        ms = methods(scene, text, kws)
        out = ['---', f'title: "案例卡片-{item["title"]}"', f'scene: {scene}', 'tags: [融策, 案例卡片, v2.0]', '---\n', f'# 案例卡片｜{item["title"]}\n', f'- 场景：**{scene}**', f'- 原文路径：`{item["path"]}`', f'- 关键词：' + '、'.join(kws[:8]), '', '## 一句话价值\n', summary(text, 220), '\n## 审计逻辑\n']
        for x in fs or ['（待补）']:
            out.append(f'- {x}')
        out.append('\n## 可复用方法\n')
        for x in ms:
            out.append(f'- {x}')
        out.append('\n## 可迁移建议\n')
        for x in rs or ['围绕问题清单限期整改，推动制度完善和闭环管理。']:
            out.append(f'- {x}')
        name = re.sub(r'[\\/*?:"<>|]', '_', item['title'])[:120] + '.md'
        (CARDS / name).write_text('\n'.join(out), encoding='utf-8')


def write_template_pack(selected):
    TEMPLATES.mkdir(parents=True, exist_ok=True)
    by_scene = defaultdict(list)
    for item in selected:
        by_scene[item['scene']].append(item)
    for scene in CORE_SCENES[:14]:
        profile = SCENE_PROFILES.get(scene, ('适用于同类审计项目。', ['问题导向分析']))
        items = by_scene.get(scene, [])
        lines = ['---', f'title: "{scene}项目可直接套用模板 v2.0"', 'scene: 项目模板', 'tags: [融策, 项目模板, v2.0]', '---\n', f'# {scene}项目可直接套用模板 v2.0\n', f'> 适用：{profile[0]}\n', '## 一、审计目标写法\n', '- 查清业务真实性、程序合规性、资金安全性和绩效结果。', '- 揭示制度执行、过程管控、数据质量和责任落实方面的问题。\n', '## 二、审前调查写法\n', '- 梳理政策依据、职责边界、项目链条和资金流向。', '- 收集业务台账、资金台账、合同批复、系统数据和整改材料。\n', '## 三、数据取证路径\n']
        for p in profile[1]:
            lines.append(f'- {p}')
        lines.extend(['\n## 四、问题表述模板\n', '- 经审计发现，相关单位在制度执行、程序履行、资金管理或业务真实性方面存在薄弱环节。', '- 经比对相关数据和资料，发现部分事项存在异常特征，需进一步核实责任主体和影响后果。\n', '## 五、审计建议模板\n', '- 建议健全制度、压实责任、完善流程、强化协同。', '- 建议围绕问题台账限期整改，并建立回头看和长效治理机制。\n', '## 六、参考案例\n'])
        for item in items[:6]:
            lines.append(f'- {item["title"]}')
        (TEMPLATES / f'{scene}模板.md').write_text('\n'.join(lines), encoding='utf-8')


def write_standard_pack():
    STANDARD.mkdir(parents=True, exist_ok=True)
    docs = {
        '01-总说明.md': '# 融策标准作业包 v2.0\n\n## 定位\n\n基于 Obsidian 全库案例提炼，形成融策内部跨业务线可复用的审计作业标准。\n\n## 固定结构\n\n审计目标 -> 审前调查 -> 取证路径 -> 问题表述 -> 审计建议 -> 汇报/专报。\n',
        '02-通用审计实施骨架.md': '# 通用审计实施骨架\n\n## 审计目标\n\n查清事实、揭示风险、压实责任、推动治理。\n\n## 审计步骤\n\n1. 审前调查\n2. 风险画像\n3. 数据筛查\n4. 现场核查\n5. 定性取证\n6. 成果转化\n',
        '03-问题定性与证据链标准.md': '# 问题定性与证据链标准\n\n## 四要素\n\n- 事实成立\n- 依据充分\n- 影响明确\n- 责任可指\n\n## 证据链\n\n政策依据 + 业务流程 + 数据/凭证 + 现场/访谈 + 整改材料。\n',
        '04-汇报与专报标准.md': '# 汇报与专报标准\n\n## 汇报顺序\n\n背景、重点、发现、风险、建议、需协调事项。\n\n## 专报句式\n\n经审计发现……反映出……建议……。\n',
    }
    for name, content in docs.items():
        (STANDARD / name).write_text('---\nscene: 标准作业包\ntags: [融策, 标准作业包, v2.0]\n---\n\n' + content, encoding='utf-8')


def write_practical_packs():
    PRACTICAL.mkdir(parents=True, exist_ok=True)
    pilot_scenes = ['工程审计', '政策落实审计', '信息系统审计', '国企审计', '农业农村审计']
    for scene in pilot_scenes:
        profile = SCENE_PROFILES[scene]
        d = PRACTICAL / f'{scene}实战试点包'
        d.mkdir(parents=True, exist_ok=True)
        plan = f'''---
scene: 实战试点包
tags: [融策, 实战试点包, v2.0]
---

# {scene}实战试点包｜审计实施方案

## 项目背景

围绕{profile[0]}开展审计，重点揭示政策执行、业务真实性、程序合规、资金安全和绩效结果等问题。

## 审计重点

{chr(10).join('- ' + x for x in profile[1])}

## 工作步骤

1. 审前调查：收集政策、台账、数据和业务资料。
2. 风险画像：按业务链条形成疑点清单。
3. 数据分析：比对关键字段、金额、时间和对象。
4. 现场核查：访谈、踏勘、资料复核。
5. 定性取证：形成取证单、问题清单和证据链。
6. 成果输出：形成汇报、报告或专报。
'''
        data = f'''---
scene: 实战试点包
tags: [融策, 取数清单, v2.0]
---

# {scene}实战试点包｜取数清单

| 序号 | 数据/资料 | 用途 | 提供单位 | 备注 |
|---:|---|---|---|---|
| 1 | 政策制度文件 | 判断依据 | 主管部门 | |
| 2 | 项目/业务台账 | 对象画像 | 实施单位 | |
| 3 | 资金拨付明细 | 资金流向 | 财务/财政 | |
| 4 | 合同/批复/会议纪要 | 程序核验 | 实施单位 | |
| 5 | 整改台账 | 闭环跟踪 | 被审计单位 | |
'''
        issue = '# 问题清单样表\n\n| 序号 | 问题事实 | 依据 | 金额/数量 | 责任单位 | 风险影响 | 整改建议 |\n|---:|---|---|---|---|---|---|\n| 1 |  |  |  |  |  |  |\n'
        evidence = '# 取证单样表\n\n## 问题事实\n\n经审计核查，发现……\n\n## 证据材料\n\n- 材料1：\n- 材料2：\n\n## 被审计单位说明\n\n\n## 审计组意见\n\n'
        ppt = '# 汇报PPT提纲\n\n1. 项目背景\n2. 审计重点\n3. 工作开展情况\n4. 主要发现\n5. 风险影响\n6. 整改建议\n'
        report = f'# {scene}审计专报初稿模板\n\n## 基本情况\n\n审计组围绕{profile[0]}开展审计。\n\n## 主要问题\n\n### （一）……\n\n经审计发现……\n\n## 建议\n\n建议限期整改、完善制度、强化监管。\n'
        files = {'01-审计实施方案模板.md': plan, '02-取数清单模板.md': data, '03-问题清单样表.md': issue, '04-取证单样表.md': evidence, '05-汇报PPT提纲.md': ppt, '06-专报初稿模板.md': report}
        for name, content in files.items():
            if not content.startswith('---'):
                content = '---\nscene: 实战试点包\ntags: [融策, 实战试点包, v2.0]\n---\n\n' + content
            (d / name).write_text(content, encoding='utf-8')


def main():
    cases = load_cases()
    selected = select_cards(cases, per_scene=3)
    write_training(cases)
    write_cards(selected)
    write_template_pack(selected)
    write_standard_pack()
    write_practical_packs()
    print(f'CASES\t{len(cases)}')
    print(f'CARDS\t{len(selected)}')
    print(f'BASE\t{BASE}')

if __name__ == '__main__':
    main()
