#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import re
from collections import defaultdict
from pathlib import Path

VAULT = Path(r'C:\Users\scrccpa\Documents\Obsidian Vault')
IDX = VAULT / '中国审计第6期-OCR归档索引.json'
ROOT = VAULT / '审计案例库-OCR' / '中国审计第6期'
BOSS = ROOT / '第6期审计案例精华提炼（老板版）.md'
TEMPLATE_DIR = ROOT / '融策审计项目可直接套用模板包'

BIZ_SCENES = {
    '工程审计模板': ['工程审计'],
    '政策落实审计模板': ['政策落实审计'],
    '国企审计模板': ['国企审计'],
    '医保卫健数据审计模板': ['信息系统审计'],
    '农业农村审计模板': ['农业农村审计'],
}

SCENE_SUMMARY = {
    '工程审计': '聚焦招投标、项目决策、工程程序、结算支付和责任链条。',
    '政策落实审计': '聚焦重大政策、区域协同、专项资金、项目落地和整改闭环。',
    '国企审计': '聚焦企业治理、奖补资金、合规经营、中介套利和国资安全。',
    '信息系统审计': '聚焦多源数据比对、规则校验、模型筛查和异常行为识别。',
    '农业农村审计': '聚焦乡村振兴、涉农资金、基层权力运行和数字化监督。',
}


def read_data():
    return json.loads(IDX.read_text(encoding='utf-8'))


def read_text(path):
    return Path(path).read_text(encoding='utf-8', errors='replace')


def extract_section(text: str, heading: str) -> str:
    m = re.search(rf'## {re.escape(heading)}\n\n(.*?)(?:\n## |\Z)', text, re.S)
    return m.group(1).strip() if m else ''


def bullets(text: str, heading: str, limit: int = 3):
    body = extract_section(text, heading)
    out = []
    for line in body.splitlines():
        line = line.strip()
        if re.match(r'^(?:\d+\.|-)\s+', line):
            out.append(re.sub(r'^(?:\d+\.|-)\s+', '', line))
    return out[:limit]


def first_sentence(text: str, heading: str, max_len: int = 180):
    body = extract_section(text, heading).replace('\n', ' ').strip()
    return body[:max_len] + ('…' if len(body) > max_len else '') if body else ''


def methods_from_item(item, text):
    joined = ' '.join(item.get('keywords', [])) + ' ' + extract_section(text, '内容摘要') + ' ' + extract_section(text, '审计发现线索')
    methods = []
    mapping = [
        ('数据比对', ['数据', 'SQL', 'Excel', '比对']),
        ('穿透核查', ['穿透', '全流程', '链条', '核查']),
        ('现场踏勘', ['现场', '勘验', '走访', '实地']),
        ('政策对标', ['政策', '规划纲要', '两重', '两新', '协同']),
        ('绩效分析', ['绩效', '资金', '奖补', '补助']),
        ('模型筛查', ['模型', '相似度', '算法', '异常']),
        ('整改闭环', ['整改', '回头看', '长效机制']),
    ]
    for label, kws in mapping:
        if any(k in joined for k in kws):
            methods.append(label)
    return methods[:5] or ['问题导向']


def make_boss(data):
    scored = []
    for item in data:
        text = read_text(item['archive_path'])
        methods = methods_from_item(item, text)
        value = len(methods) + len(bullets(text, '审计发现线索', 2)) + (1 if item.get('manual_review_note') else 0)
        scored.append((value, item, text, methods))
    top = [x for _, x, t, m in sorted(scored, key=lambda z: z[0], reverse=True)[:10]]

    lines = [
        '---',
        'title: "第6期审计案例精华提炼（老板版）"',
        'scene: 老板版',
        'tags: [审计案例, 老板版, 中国审计第6期]',
        '---\n',
        '# 第6期审计案例精华提炼（老板版）\n',
        '> 目的：给融策平头哥快速看懂“这期文章里，哪些能直接拿来打项目、带团队、做培训”。\n',
        '## 一、最值得学的 10 个审计思路\n',
    ]
    for i, item in enumerate(top, 1):
        text = read_text(item['archive_path'])
        summary = first_sentence(text, '内容摘要', 120)
        findings = bullets(text, '审计发现线索', 1)
        methods = methods_from_item(item, text)
        lines.append(f'### {i}. {item["title"]}【{item["scene"]}】')
        lines.append(f'- 为什么值得学：{summary}')
        if findings:
            lines.append(f'- 核心抓手：{findings[0]}')
        lines.append(f'- 可直接迁移：' + ' / '.join(methods))
        lines.append('')

    lines.append('## 二、哪些最适合直接迁移到融策项目\n')
    lines.append('- **工程咨询/财政评审**：优先复用《工程建设领域招标投标审计审前调查研究思路》《“先种后铲”的绿化闹剧》里的全链条拆解与程序核查写法。')
    lines.append('- **政府审计/政策跟踪**：优先复用“两重”“两新”、京津冀协同、湖北支点建设等文章里的政策对标+整改闭环方法。')
    lines.append('- **医保/卫健数据审计**：优先复用医院串换诊疗、老年人健康管理造假两篇里的 SQL/Excel/规则校验套路。')
    lines.append('- **国企/奖补资金审计**：优先复用高企认定奖励问题一文里的企业名单比对、文本相似度筛查和中介套利链识别。')
    lines.append('- **农业农村/乡村振兴**：优先复用齐鲁样板文章中的大数据审计、无人机核查、涉农资金闭环治理思路。\n')

    lines.append('## 三、哪些适合拿去做内部培训\n')
    lines.append('- 新人入门：工程招投标审前调查、林业生态补偿补助资金审计重点。')
    lines.append('- 方法训练：医院诊疗数据审计、老年人健康管理造假识别、高企奖补申报相似度筛查。')
    lines.append('- 领导层培训：政策落实审计、研究型审计、整改闭环与成果转化。\n')

    lines.append('## 四、建议沉淀成公司标准方法的模块\n')
    modules = [
        '工程招投标审前调查模块',
        '医保/卫健数据比对模块',
        '企业奖补资金异常筛查模块',
        '政策落实审计审理把关模块',
        '整改闭环与专报转化模块',
        '乡村振兴/涉农资金数字化核查模块',
    ]
    for m in modules:
        lines.append(f'- {m}')

    lines.append('\n## 五、老板一句话结论\n')
    lines.append('这 23 篇里，真正最值钱的不是“观点文章”，而是那些能拆出**取数路径、疑点逻辑、核查动作、整改话术**的文章。对融策来说，优先把工程、政策落实、卫健数据、奖补资金四条线做成标准模板，回报最高。')
    BOSS.write_text('\n'.join(lines), encoding='utf-8')


def make_template(name, items):
    lines = [
        '---',
        f'title: "{name}"',
        'scene: 项目模板',
        'tags: [审计模板, 中国审计第6期, 融策]',
        '---\n',
        f'# {name}\n',
        f'> 适用说明：{SCENE_SUMMARY.get(items[0]["scene"], "适用于同类项目。") if items else "适用于同类项目。"}\n',
        '## 一、审计目标写法\n',
        '- 围绕项目/资金/政策落实情况，重点关注制度执行、业务流程、资金安全、绩效结果和整改责任。',
        '- 聚焦本领域高风险环节，揭示程序不规范、数据异常、管理缺位、绩效不佳和责任虚化等问题。\n',
        '## 二、审前调查写法\n',
        '- 梳理政策法规、主管部门职责、项目链条和资金流向。',
        '- 收集基础台账、明细数据、业务系统字段、合同/会议纪要/批复文件。',
        '- 形成“对象画像 + 风险点清单 + 取数清单 + 核查路线图”。\n',
        '## 三、数据取证路径\n',
    ]
    methods_seen = set()
    for item in items[:4]:
        text = read_text(item['archive_path'])
        methods = methods_from_item(item, text)
        for m in methods:
            if m not in methods_seen:
                lines.append(f'- {m}：参考《{item["title"]}》')
                methods_seen.add(m)
    lines.extend([
        '\n## 四、发现问题表述模板\n',
        '- 经审计发现，部分事项在制度执行、审批程序、资金管理或业务真实性方面存在薄弱环节，反映出相关单位内部控制不严、过程管理不到位。',
        '- 经比对业务数据、资金台账及支撑资料，发现部分项目（资金）存在异常特征，疑似存在虚报冒领、违规支付、程序倒置、绩效不实等问题。',
        '- 有关问题表明，相关主管部门在监督、协同、整改和长效机制建设方面仍存在短板。\n',
        '## 五、审计建议模板\n',
        '- 建议相关单位健全制度机制，压实岗位责任，完善业务流程和审批闭环。',
        '- 建议围绕问题台账逐项整改，强化追责问责与“回头看”，推动由个案整改向系统治理延伸。',
        '- 建议加强数据治理、跨部门协同和绩效跟踪，提高资金使用效益和政策落实质量。\n',
        '## 六、可直接参考案例\n',
    ])
    for item in items[:6]:
        lines.append(f'- {item["title"]}（{item["scene"]}）')
    return '\n'.join(lines)


def make_templates(data):
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    by_scene = defaultdict(list)
    for item in data:
        by_scene[item['scene']].append(item)
    for name, scenes in BIZ_SCENES.items():
        selected = []
        for sc in scenes:
            selected.extend(by_scene.get(sc, []))
        content = make_template(name, selected)
        (TEMPLATE_DIR / f'{name}.md').write_text(content, encoding='utf-8')


def main():
    data = read_data()
    make_boss(data)
    make_templates(data)
    print(f'BOSS\t{BOSS}')
    print(f'TEMPLATES\t{TEMPLATE_DIR}')

if __name__ == '__main__':
    main()
