#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import re
from collections import defaultdict
from pathlib import Path

VAULT = Path(r'C:\Users\scrccpa\Documents\Obsidian Vault')
IDX = VAULT / '中国审计第6期-OCR归档索引.json'
ROOT = VAULT / '审计案例库-OCR' / '中国审计第6期'
TRAINING = ROOT / '场景-审计逻辑-可复用方法训练清单.md'
CARDS_DIR = ROOT / '案例卡片'

HIGH_VALUE_TITLES = {
    '“先种后铲”的绿化闹剧',
    '工程建设领域招标投标审计审前调查研究思路',
    '揭示医院串换诊疗项目和过度诊疗行为的数据分析思路与方法',
    '运用 Excel与 SQL技术揭示老年人健康管理服务造假行为',
    '运用 SQL 技术和 UniSim相似度算法揭示虚假申报高新技术企业认定奖励问题',
    '林业生态补偿补助资金审计重点',
    '审理视角下的“两重”“两新”审计实践与思考',
    '绘就齐鲁乡村振兴和美画卷--山东省审计厅助力高质量打造乡村振兴齐鲁样板工作纪实',
}


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


def normalize_method(findings, recs, keywords):
    methods = []
    joined = ' '.join(findings + recs + keywords)
    rules = [
        ('数据比对', ['数据', '比对', 'SQL', 'Excel', '关联', '筛查']),
        ('穿透核查', ['穿透', '全流程', '链条', '核查', '核实']),
        ('现场踏勘', ['现场', '勘验', '实地', '走访']),
        ('政策对标', ['政策', '规划纲要', '落实', '协同发展', '两重', '两新']),
        ('资金绩效分析', ['绩效', '资金', '补助', '国债', '奖补']),
        ('风险画像/疑点模型', ['模型', '算法', '相似度', '异常', '风险']),
        ('整改闭环', ['整改', '回头看', '长效机制', '约谈']),
    ]
    for label, kws in rules:
        if any(k in joined for k in kws):
            methods.append(label)
    return methods[:5]


def make_training(data):
    by_scene = defaultdict(list)
    for item in data:
        by_scene[item['scene']].append(item)

    lines = [
        '---',
        'title: "中国审计第6期-场景-审计逻辑-可复用方法训练清单"',
        'scene: 训练清单',
        'tags: [审计案例, OCR, 中国审计第6期, 训练清单]',
        '---\n',
        '# 中国审计第6期｜场景-审计逻辑-可复用方法训练清单\n',
        '> 用途：将 23 篇文章压缩成可复用的审计训练资料，便于写方案、带团队、喂知识库。\n',
        '## 使用建议\n',
        '- 先按场景找相近案例，再看“审计目标/关键疑点/可复用方法”。',
        '- 优先复用“数据比对、穿透核查、政策对标、整改闭环”等方法模块。',
        '- 遇到泛理论文章，重点提炼其组织方式、立项逻辑和整改转化机制。\n',
    ]

    for scene in sorted(by_scene):
        lines.append(f'## {scene}\n')
        for item in by_scene[scene]:
            p = Path(item['archive_path'])
            text = p.read_text(encoding='utf-8', errors='replace')
            summary = first_sentence(text, '内容摘要', 160)
            findings = bullets(text, '审计发现线索', 2)
            recs = bullets(text, '审计建议', 2)
            methods = normalize_method(findings, recs, item.get('keywords', []))
            lines.append(f'### {item["title"]}')
            lines.append(f'- 文章定位：{summary}')
            lines.append(f'- 关键疑点：' + ('；'.join(findings) if findings else '（待补）'))
            lines.append(f'- 可复用方法：' + (' / '.join(methods) if methods else '通用审计分析'))
            lines.append(f'- 落地建议：' + ('；'.join(recs) if recs else '（待补）'))
            if item.get('manual_review_note'):
                lines.append(f'- 人工复核：{item["manual_review_note"]}')
            lines.append('')

    TRAINING.write_text('\n'.join(lines), encoding='utf-8')


def make_cards(data):
    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    wrote = []
    for item in data:
        if item['title'] not in HIGH_VALUE_TITLES:
            continue
        p = Path(item['archive_path'])
        text = p.read_text(encoding='utf-8', errors='replace')
        summary = first_sentence(text, '内容摘要', 240)
        findings = bullets(text, '审计发现线索', 3)
        recs = bullets(text, '审计建议', 3)
        methods = normalize_method(findings, recs, item.get('keywords', []))
        card = []
        card.append('---')
        card.append(f'title: "案例卡片-{item["title"]}"')
        card.append(f'scene: {item["scene"]}')
        card.append('tags: [审计案例, 案例卡片, 中国审计第6期]')
        card.append('---\n')
        card.append(f'# 案例卡片｜{item["title"]}\n')
        card.append(f'- 场景：**{item["scene"]}**')
        card.append(f'- 原文路径：`{item["archive_path"]}`')
        card.append(f'- 关键词：' + '、'.join(item.get('keywords', [])[:8]))
        card.append('')
        card.append('## 一句话价值\n')
        card.append(summary or '（待补）')
        card.append('\n## 审计要点\n')
        for x in findings or ['（待补）']:
            card.append(f'- {x}')
        card.append('\n## 可复用方法\n')
        for x in methods or ['通用审计分析']:
            card.append(f'- {x}')
        card.append('\n## 可直接迁移的写法\n')
        for x in recs or ['（待补）']:
            card.append(f'- {x}')
        if item.get('manual_review_note'):
            card.append('\n## 人工复核\n')
            card.append(f'- {item["manual_review_note"]}')
        out = CARDS_DIR / f'{item["title"]}.md'
        out.write_text('\n'.join(card), encoding='utf-8')
        wrote.append(str(out))
    return wrote


def main():
    data = json.loads(IDX.read_text(encoding='utf-8'))
    make_training(data)
    wrote = make_cards(data)
    print(f'TRAINING\t{TRAINING}')
    print(f'CARDS\t{len(wrote)}')
    for p in wrote:
        print(p)

if __name__ == '__main__':
    main()
