#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import re
from collections import defaultdict
from pathlib import Path

VAULT = Path(r'C:\Users\scrccpa\Documents\Obsidian Vault')
IDX = VAULT / '中国审计第6期-OCR归档索引.json'
ROOT = VAULT / '审计案例库-OCR' / '中国审计第6期'
CARDS_DIR = ROOT / '案例卡片'
UPGRADED_DIR = ROOT / '案例卡片-报告可直接引用版'
METHOD_DICT = ROOT / '审计方法词典.md'

SCENE_MIGRATION = {
    '工程审计': ['政府投资项目审计', '工程结算审计', '招投标审计'],
    '信息系统审计': ['医保基金审计', '卫健审计', '大数据审计'],
    '政策落实审计': ['重大政策跟踪审计', '专项资金审计', '区域协同发展审计'],
    '国企审计': ['国资监管审计', '奖补资金审计', '企业合规审计'],
    '资源环境审计': ['生态补偿审计', '自然资源资产审计', '绿色发展审计'],
    '农业农村审计': ['乡村振兴审计', '涉农资金审计', '高标准农田审计'],
    '金融审计': ['保证金审计', '融资风险审计', '资金链条审计'],
    '其他审计': ['研究型审计', '综合监督', '审计管理'],
}

TITLE_HINTS = {
    '“先种后铲”的绿化闹剧': ('工程项目决策失当与整改偏差', '围绕医院建设项目与林地整改争议，审查立项决策、程序合规和责任链条。'),
    '工程建设领域招标投标审计审前调查研究思路': ('招投标全链条风险画像', '围绕招标、投标、评标、定标、中标后管理拆解关键节点，构建审前调查台账。'),
    '揭示医院串换诊疗项目和过度诊疗行为的数据分析思路与方法': ('医保诊疗数据穿透比对', '围绕医院诊疗、第三方检验与医保结算数据交叉验证，发现违规收费和骗保线索。'),
    '运用 Excel与 SQL技术揭示老年人健康管理服务造假行为': ('公共卫生服务数据造假识别', '围绕老年人健康管理服务记录与基础数据交叉校验，识别虚构服务和套补问题。'),
    '运用 SQL 技术和 UniSim相似度算法揭示虚假申报高新技术企业认定奖励问题': ('企业奖补申报造假识别', '围绕高企认定奖励、企业申报材料和中介服务链条识别虚假包装与财政套利。'),
    '林业生态补偿补助资金审计重点': ('生态补偿资金全流程审计', '围绕补助分配、资金拨付、管护支出和绩效管理开展穿透核查。'),
    '审理视角下的“两重”“两新”审计实践与思考': ('重大政策资金审理把关', '围绕“两重”“两新”项目政策适配、审理深度和多部门协同开展质量控制。'),
    '绘就齐鲁乡村振兴和美画卷--山东省审计厅助力高质量打造乡村振兴齐鲁样板工作纪实': ('乡村振兴综合监督模式', '围绕乡村振兴资金、项目、权力运行与数字化监督构建综合审计框架。'),
}

METHOD_RULES = [
    ('数据比对法', ['数据', '比对', '交叉', 'SQL', 'Excel']),
    ('穿透核查法', ['穿透', '全流程', '链条', '核查']),
    ('现场踏勘法', ['现场', '实地', '走访', '勘验']),
    ('政策对标法', ['政策', '规划纲要', '落实', '两重', '两新']),
    ('资金绩效分析法', ['绩效', '奖补', '补助', '资金', '国债']),
    ('相似度/模型筛查法', ['模型', '算法', '相似度', '异常', '画像']),
    ('整改闭环法', ['整改', '回头看', '长效机制', '约谈']),
]


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
    if not body:
        return ''
    return body[:max_len] + ('…' if len(body) > max_len else '')


def methods_from_text(*parts):
    joined = ' '.join([p for p in parts if p])
    methods = []
    for label, kws in METHOD_RULES:
        if any(k in joined for k in kws):
            methods.append(label)
    return methods or ['通用问题导向审计法']


def make_upgrade(item):
    p = Path(item['archive_path'])
    text = p.read_text(encoding='utf-8', errors='replace')
    findings = bullets(text, '审计发现线索', 3)
    recs = bullets(text, '审计建议', 3)
    summary = first_sentence(text, '内容摘要', 240)
    methods = methods_from_text(summary, ' '.join(findings), ' '.join(recs), ' '.join(item.get('keywords', [])))
    audit_bg, focus = TITLE_HINTS.get(item['title'], ('典型审计案例', summary or '围绕重点事项开展审计。'))
    migrate = SCENE_MIGRATION.get(item['scene'], ['同类专题审计'])
    report_templates = [
        f'经审计发现，{(findings[0] if findings else "相关管理环节存在薄弱点")[:80]}，反映出该领域在制度执行、过程管控或资源配置方面仍存在不足。',
        f'建议相关单位围绕{audit_bg}，进一步健全制度、压实责任、完善流程，推动问题整改由个案处置向系统治理延伸。',
        f'审计应重点关注{focus}，通过“{"、".join(methods[:3])}”等方式提高问题发现的精准性和整改的实效性。',
    ]
    out = []
    out.append('---')
    out.append(f'title: "报告引用版-{item["title"]}"')
    out.append(f'scene: {item["scene"]}')
    out.append('tags: [审计案例, 报告引用版, 中国审计第6期]')
    out.append('---\n')
    out.append(f'# 报告可直接引用版｜{item["title"]}\n')
    out.append(f'- 场景：**{item["scene"]}**')
    out.append(f'- 原文：`{item["archive_path"]}`')
    out.append(f'- 适配方向：{audit_bg}')
    out.append('')
    out.append('## 审计背景\n')
    out.append(focus)
    out.append('\n## 发现逻辑\n')
    for x in findings or ['（待补）']:
        out.append(f'- {x}')
    out.append('\n## 证据链条\n')
    for x in methods[:4]:
        out.append(f'- {x}')
    out.append('\n## 定性要点\n')
    out.append(f'- 重点关注制度执行、程序合规、资金安全、绩效结果与整改责任之间的对应关系。')
    out.append(f'- 结合{item["scene"]}场景，从“政策依据—业务流程—数据/资料—异常疑点—责任主体”形成闭环认定。')
    out.append('\n## 报告表述模板\n')
    for x in report_templates:
        out.append(f'- {x}')
    out.append('\n## 可迁移场景\n')
    for x in migrate:
        out.append(f'- {x}')
    if item.get('manual_review_note'):
        out.append('\n## 人工复核\n')
        out.append(f'- {item["manual_review_note"]}')
    return '\n'.join(out)


def build_method_dict(data):
    scene_map = defaultdict(list)
    for item in data:
        p = Path(item['archive_path'])
        text = p.read_text(encoding='utf-8', errors='replace')
        findings = bullets(text, '审计发现线索', 2)
        recs = bullets(text, '审计建议', 2)
        methods = methods_from_text(first_sentence(text, '内容摘要', 180), ' '.join(findings), ' '.join(recs), ' '.join(item.get('keywords', [])))
        for m in methods:
            scene_map[m].append((item['scene'], item['title'], findings[:1], recs[:1]))

    lines = [
        '---',
        'title: "中国审计第6期-审计方法词典"',
        'scene: 方法词典',
        'tags: [审计案例, 方法词典, 中国审计第6期]',
        '---\n',
        '# 中国审计第6期｜审计方法词典\n',
        '> 用途：把案例里的方法拆出来，按“方法定义—适用场景—操作抓手—引用案例”沉淀为可复用工具。\n',
    ]
    for method in sorted(scene_map):
        lines.append(f'## {method}\n')
        lines.append(f'- 方法定义：围绕“{method}”识别问题、核实疑点、形成证据链。')
        scenes = sorted({x[0] for x in scene_map[method]})
        lines.append(f'- 适用场景：' + '、'.join(scenes))
        lines.append(f'- 操作抓手：结合台账、业务流程、政策依据、数据字段、现场核查与整改跟踪形成闭环。')
        lines.append('- 引用案例：')
        for scene, title, finding, rec in scene_map[method][:6]:
            lines.append(f'  - [{scene}] {title}')
            if finding:
                lines.append(f'    - 疑点示例：{finding[0][:120]}')
            if rec:
                lines.append(f'    - 落地示例：{rec[0][:120]}')
        lines.append('')
    METHOD_DICT.write_text('\n'.join(lines), encoding='utf-8')


def main():
    data = json.loads(IDX.read_text(encoding='utf-8'))
    UPGRADED_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    for item in data:
        src_card = CARDS_DIR / f'{item["title"]}.md'
        if not src_card.exists():
            continue
        out = UPGRADED_DIR / f'{item["title"]}.md'
        out.write_text(make_upgrade(item), encoding='utf-8')
        count += 1
    build_method_dict(data)
    print(f'UPGRADED\t{count}')
    print(f'METHOD_DICT\t{METHOD_DICT}')

if __name__ == '__main__':
    main()
