#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Full sync/audit script for Rongce standard operating system v2.0."""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

VAULT = Path(r'C:\Users\scrccpa\Documents\Obsidian Vault')
CATALOG = VAULT / '审计资料清单.json'
BASE = VAULT / '审计案例库-OCR' / '融策标准作业体系 v2.0'
TRAINING = BASE / '01-训练清单' / '场景-审计逻辑-可复用方法训练清单 v2.0.md'
COVERAGE = BASE / '00-覆盖率与同步机制说明.md'
STATE = VAULT / '审计案例库-OCR' / '融策标准作业体系 v2.0-sync-state.json'

CORE_SCENES = {
    '工程审计', '政策落实审计', '国企审计', '信息系统审计', '农业农村审计',
    '预算执行审计', '绩效审计', '经济责任审计', '社保民生审计', '资源环境审计',
    '专项资金审计', '金融审计', '内部审计', '教科文卫审计', '其他审计'
}
GENERATED_MARKERS = ['案例卡片', '模板', '标准作业包', '实战试点包', '训练清单', '方法词典', '资料总览', '老板版', '融策标准作业体系']
SCENE_ORDER = ['工程审计','政策落实审计','国企审计','信息系统审计','农业农村审计','预算执行审计','绩效审计','经济责任审计','社保民生审计','资源环境审计','专项资金审计','金融审计','内部审计','教科文卫审计','其他审计']

SCENE_METHODS = {
    '工程审计': ['招投标链条拆解', '交易台账比对', '合同支付穿透', '现场踏勘'],
    '政策落实审计': ['政策链条对标', '资金直达核查', '部门协同验证', '整改回头看'],
    '国企审计': ['三重一大核查', '资金流向穿透', '异常交易筛查', '内控测试'],
    '信息系统审计': ['字段清洗', '跨系统比对', 'SQL疑点筛查', '规则校验'],
    '农业农村审计': ['涉农台账比对', '受益对象核验', '现场踏勘/无人机', '资金绩效分析'],
    '预算执行审计': ['预算指标比对', '支付进度分析', '结余结转核查', '三公经费筛查'],
    '绩效审计': ['绩效目标对标', '指标完成度分析', '成本效益分析', '整改闭环'],
    '经济责任审计': ['权责清单对照', '重大事项穿透', '政绩观偏差识别', '责任链条分析'],
    '社保民生审计': ['受益对象比对', '资金发放核查', '服务真实性验证', '群众诉求线索'],
    '资源环境审计': ['资源台账比对', '生态补偿资金核查', '现场核验', '整改效果跟踪'],
    '专项资金审计': ['资金链条穿透', '项目库比对', '票据凭证核验', '绩效评价'],
    '金融审计': ['资金流水核查', '担保关系穿透', '债务台账比对', '异常交易识别'],
    '内部审计': ['内控制度测试', '风险清单核验', '整改台账跟踪', '治理建议转化'],
    '教科文卫审计': ['项目资金核查', '服务真实性验证', '绩效指标分析', '业务数据比对'],
    '其他审计': ['研究型审计', '经验复盘', '制度机制分析', '成果转化'],
}


def is_generated(item):
    scene = item.get('scene', '')
    s = f"{item.get('path','')} {item.get('title','')} {item.get('filename','')}"
    return scene not in CORE_SCENES or any(m in s for m in GENERATED_MARKERS)


def read_text(item):
    return (VAULT / item['path']).read_text(encoding='utf-8', errors='replace')


def strip_yaml(text):
    if text.startswith('---'):
        end = text.find('---', 3)
        if end > 0:
            return text[end+3:]
    return text


def section(text, heading):
    m = re.search(rf'## {re.escape(heading)}\n\n(.*?)(?:\n## |\Z)', text, re.S)
    return m.group(1).strip() if m else ''


def brief(text, n=160):
    body = section(text, '内容摘要') or strip_yaml(text)
    body = re.sub(r'[#>`*\-\s]+', '', body)
    return body[:n] + ('...' if len(body) > n else '')


def bullet_items(text, heading, limit=2):
    body = section(text, heading)
    out = []
    for line in body.splitlines():
        line = line.strip()
        if re.match(r'^(?:\d+\.|-)\s+', line):
            out.append(re.sub(r'^(?:\d+\.|-)\s+', '', line))
    return out[:limit]


def methods(scene, text):
    joined = brief(text, 500) + section(text, '审计发现线索') + section(text, '审计建议')
    found = []
    rules = [
        ('数据比对', ['数据', '比对', 'SQL', 'Excel', '关联']),
        ('穿透核查', ['穿透', '链条', '全流程', '核查']),
        ('现场核验', ['现场', '实地', '踏勘', '勘验', '走访']),
        ('政策对标', ['政策', '落实', '规划', '两重', '两新']),
        ('资金绩效分析', ['资金', '绩效', '预算', '补助', '奖补']),
        ('模型筛查', ['模型', '算法', '相似度', '异常', '画像']),
        ('整改闭环', ['整改', '回头看', '闭环', '长效机制']),
    ]
    for name, words in rules:
        if any(w in joined for w in words):
            found.append(name)
    found.extend(SCENE_METHODS.get(scene, [])[:2])
    dedup = []
    for x in found:
        if x not in dedup:
            dedup.append(x)
    return dedup[:6] or ['问题导向分析']


def load_cases():
    data = json.loads(CATALOG.read_text(encoding='utf-8'))
    real = [x for x in data if not is_generated(x)]
    generated = [x for x in data if is_generated(x)]
    return data, real, generated


def write_full_training(real):
    TRAINING.parent.mkdir(parents=True, exist_ok=True)
    by_scene = defaultdict(list)
    for item in real:
        by_scene[item['scene']].append(item)
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    lines = [
        '---',
        'title: "融策全库-场景-审计逻辑-可复用方法训练清单 v2.0"',
        'scene: 训练清单',
        'tags: [融策, 训练清单, v2.0, 全量覆盖]',
        '---\n',
        '# 融策全库｜场景-审计逻辑-可复用方法训练清单 v2.0\n',
        f'> 更新时间：{now}。本清单为全量训练清单，覆盖过滤后的真实案例/文章 {len(real)} 篇；案例卡片另做高价值精选。\n',
    ]
    for scene in SCENE_ORDER:
        items = by_scene.get(scene, [])
        if not items:
            continue
        lines.append(f'## {scene}（{len(items)}篇）\n')
        for i, item in enumerate(items, 1):
            text = read_text(item)
            fs = bullet_items(text, '审计发现线索', 2)
            rs = bullet_items(text, '审计建议', 2)
            lines.append(f'### {i}. {item.get("title") or item.get("filename")}')
            lines.append(f'- 路径：`{item["path"]}`')
            lines.append(f'- 审计逻辑：{brief(text, 180)}')
            lines.append(f'- 关键疑点：' + ('；'.join(fs) if fs else '（原文未结构化提取，建议后续精修）'))
            lines.append(f'- 可复用方法：' + ' / '.join(methods(scene, text)))
            lines.append(f'- 建议抓手：' + ('；'.join(rs) if rs else '围绕问题清单限期整改，推动制度完善和闭环管理。'))
            lines.append('')
    TRAINING.write_text('\n'.join(lines), encoding='utf-8')


def write_coverage(data, real, generated):
    by_scene = Counter(x['scene'] for x in real)
    v2_files = list(BASE.rglob('*.md')) if BASE.exists() else []
    lines = [
        '---',
        'title: "融策标准作业体系 v2.0-覆盖率与同步机制说明"',
        'scene: 标准作业包',
        'tags: [融策, 覆盖率, 同步机制, v2.0]',
        '---\n',
        '# 融策标准作业体系 v2.0｜覆盖率与同步机制说明\n',
        f'- 当前资料清单总条目：**{len(data)}**',
        f'- 真实案例/文章条目：**{len(real)}**',
        f'- 模板/卡片/方法词典等二次产物或非核心场景：**{len(generated)}**',
        f'- v2.0 体系文件数：**{len(v2_files)}**',
        f'- 全量训练清单覆盖真实案例/文章：**{len(real)} / {len(real)}**',
        '',
        '## 场景分布\n',
    ]
    for scene, count in by_scene.most_common():
        lines.append(f'- {scene}：{count} 篇')
    lines.extend([
        '\n## 同步机制建议\n',
        '### 1. 原始资料入库',
        '- 新 PDF/Word/Markdown 先进入 Obsidian 对应资料目录。',
        '- OCR 后必须写入 YAML：`title`、`scene`、`tags`、`keywords`、`findings`、`recommendations`。',
        '- 如果暂时无法精修，至少保证 `scene` 字段存在。',
        '\n### 2. 索引刷新',
        '- 运行：`python scripts\\build_catalog.py`',
        '- 生成/更新：`C:\\Users\\scrccpa\\Documents\\Obsidian Vault\\审计资料清单.json`',
        '\n### 3. v2.0 作业体系同步',
        '- 运行：`python scripts\\rongce_v2_sync.py`',
        '- 自动重新生成全量训练清单、覆盖率说明，并保留模板包/标准包/试点包结构。',
        '\n### 4. 高频同步策略',
        '- 手动方式：每次新增一批案例后运行以上两个脚本。',
        '- 半自动方式：加入 HEARTBEAT，每天晚间检查资料清单变化，有新增则同步。',
        '- 定时方式：用 cron 每天 20:30 自动运行同步任务。',
        '- 真实时方式：使用文件监听器监控 Obsidian 目录，但不建议常驻，Windows 下容易被文件保存/同步软件反复触发。',
        '\n## 推荐落地方案\n',
        '短期采用“新增后手动同步 + 晚间 heartbeat 检查”；稳定后再改为每日 cron。这样成本低、出错少，也不会让文件监听器把电脑当成迪厅。',
    ])
    COVERAGE.write_text('\n'.join(lines), encoding='utf-8')
    STATE.write_text(json.dumps({
        'updated_at': datetime.now().isoformat(),
        'catalog_total': len(data),
        'real_cases': len(real),
        'generated_or_noncase': len(generated),
        'v2_files': len(v2_files),
        'by_scene': dict(by_scene),
    }, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    data, real, generated = load_cases()
    write_full_training(real)
    write_coverage(data, real, generated)
    print('CATALOG_TOTAL', len(data))
    print('REAL_CASES', len(real))
    print('GENERATED_OR_NONCASE', len(generated))
    print('TRAINING_FULL_COVERAGE', len(real))
    print('COVERAGE_DOC', COVERAGE)

if __name__ == '__main__':
    main()
