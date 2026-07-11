#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import re
import shutil
from collections import defaultdict
from pathlib import Path

VAULT = Path(r'C:\Users\scrccpa\Documents\Obsidian Vault')
IDX = VAULT / '中国审计第6期-OCR归档索引.json'
ROOT = VAULT / '审计案例库-OCR'
TOPIC = ROOT / '中国审计第6期'
SUMMARY = TOPIC / '按场景汇总总览.md'
CATALOG = VAULT / '审计资料清单.json'

RECLASS = {
    '信息窗': '其他审计',
    '提升思维能力 深耕审计实践以科学思想方法推动审计工作高质量发展': '其他审计',
    '科学规范提升审计效能服务湖北支点建设大局': '政策落实审计',
}

MANUAL_NOTES = {
    '信息窗': '人工复核：该文为期刊快讯/信息窗栏目，内容横跨财政、经责、投资、内审、乡村振兴等多类项目，不宜归入单一工程审计，改为“其他审计”。',
    '提升思维能力 深耕审计实践以科学思想方法推动审计工作高质量发展': '人工复核：该文为审计理念与方法论文章，核心是战略思维、辩证思维、法治思维及审计质量提升，不是特定经济责任审计案例，改为“其他审计”。',
    '科学规范提升审计效能服务湖北支点建设大局': '人工复核：该文围绕服务湖北支点建设、重大部署落实、审计立项与整改机制展开，更贴近“政策落实审计”场景，而非信息系统审计。',
}


def replace_scene_in_text(text: str, new_scene: str) -> str:
    text = re.sub(r'(?m)^scene: .*$', f'scene: {new_scene}', text)
    text = re.sub(r'(?m)^  - [^\n]+审计$', lambda m: f'  - {new_scene}' if 'OCR' not in m.group(0) and '审计案例' not in m.group(0) else m.group(0), text, count=1)
    text = re.sub(r'(?m)^- 场景分类: .*$', f'- 场景分类: {new_scene}', text)
    return text


def extract_section(text: str, heading: str) -> str:
    m = re.search(rf'## {re.escape(heading)}\n\n(.*?)(?:\n## |\Z)', text, re.S)
    return m.group(1).strip() if m else ''


def short_list_section(text: str, heading: str, limit: int = 3) -> list[str]:
    body = extract_section(text, heading)
    items = []
    for line in body.splitlines():
        line = line.strip()
        if re.match(r'^(?:\d+\.|-)\s+', line):
            items.append(re.sub(r'^(?:\d+\.|-)\s+', '', line))
    return items[:limit]


def main():
    data = json.loads(IDX.read_text(encoding='utf-8'))
    # reclassify obvious mismatches
    for item in data:
        title = item['title']
        if title not in RECLASS:
            continue
        new_scene = RECLASS[title]
        old_path = Path(item['archive_path'])
        old_scene = item['scene']
        text = old_path.read_text(encoding='utf-8')
        text = replace_scene_in_text(text, new_scene)
        if '## 备注' in text:
            text = text + ''
        text += f"\n\n## 人工复核说明\n\n- {MANUAL_NOTES[title]}\n"
        new_topic_dir = TOPIC / new_scene
        new_root_dir = ROOT / new_scene
        new_topic_dir.mkdir(parents=True, exist_ok=True)
        new_root_dir.mkdir(parents=True, exist_ok=True)
        new_topic_path = new_topic_dir / old_path.name
        new_root_path = new_root_dir / old_path.name
        new_topic_path.write_text(text, encoding='utf-8')
        new_root_path.write_text(text, encoding='utf-8')
        # remove previous copies
        if old_path.exists() and old_path != new_topic_path:
            old_path.unlink()
        old_root_path = ROOT / old_scene / old_path.name
        if old_root_path.exists() and old_root_path != new_root_path:
            old_root_path.unlink()
        item['scene'] = new_scene
        item['archive_path'] = str(new_topic_path)
        item['manual_review_note'] = MANUAL_NOTES[title]

    IDX.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    by_scene = defaultdict(list)
    for item in data:
        by_scene[item['scene']].append(item)

    lines = []
    lines.append('---')
    lines.append('title: "中国审计第6期-按场景汇总总览"')
    lines.append('scene: 资料总览')
    lines.append('tags: [审计案例, OCR, 中国审计第6期, 场景总览]')
    lines.append('---\n')
    lines.append('# 中国审计第6期｜按场景汇总总览\n')
    lines.append('> 说明：基于 23 篇 OCR 文章整理，包含自动提取的审计逻辑摘要，并对明显错分文章做了人工复核重分。\n')
    lines.append('## 场景分布\n')
    for scene in sorted(by_scene):
        lines.append(f'- **{scene}**：{len(by_scene[scene])} 篇')
    lines.append('')

    for scene in sorted(by_scene):
        lines.append(f'## {scene}\n')
        for i, item in enumerate(by_scene[scene], 1):
            p = Path(item['archive_path'])
            text = p.read_text(encoding='utf-8', errors='replace')
            summary = extract_section(text, '内容摘要').replace('\n', ' ').strip()
            summary = summary[:220] + ('…' if len(summary) > 220 else '')
            logic = short_list_section(text, '审计逻辑', limit=0)
            findings = short_list_section(text, '审计发现线索', limit=2)
            recs = short_list_section(text, '审计建议', limit=2)
            lines.append(f'### {i}. {item["title"]}')
            lines.append(f'- 路径：`{item["archive_path"]}`')
            lines.append(f'- 摘要：{summary}')
            if findings:
                lines.append(f'- 关键发现：' + '；'.join(findings[:2]))
            if recs:
                lines.append(f'- 审计建议：' + '；'.join(recs[:2]))
            if item.get('manual_review_note'):
                lines.append(f'- 人工复核：{item["manual_review_note"]}')
            lines.append('')

    lines.append('## 人工复核与重分记录\n')
    for title, note in MANUAL_NOTES.items():
        lines.append(f'- **{title}**：{note}')

    SUMMARY.write_text('\n'.join(lines), encoding='utf-8')
    print(f'WROTE_SUMMARY\t{SUMMARY}')
    print('RECLASSIFIED\t3')

if __name__ == '__main__':
    main()
