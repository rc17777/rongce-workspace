#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import csv

VAULT = Path(r'C:\Users\scrccpa\Documents\Obsidian Vault')
WIKI = VAULT / 'wiki' / '融策AI知识中枢'
DELIVER = VAULT / '融策AI知识中枢' / '交付模板雏形'
HUB = VAULT / '融策AI知识中枢.md'
CHECKLIST = VAULT / '融策AI知识中枢-通宵推进清单.md'
FINAL_REPORT = VAULT / '融策AI知识中枢-阶段一至四完成报告.md'

SCENES = {
    '工程审计': {
        'focus': '招投标、立项决策、合同支付、变更签证、工程量核实、现场踏勘',
        'methods': ['招投标链条拆解', '交易台账比对', '合同支付穿透', '现场踏勘', '整改闭环'],
        'queries': ['工程审计 招投标 审计逻辑', '围标串标 投标文件 雷同 数据分析', '工程变更签证 审计疑点 取证路径'],
    },
    '医保卫健数据审计': {
        'focus': '医保结算、HIS诊疗、检验检查、公共卫生服务、死亡/年龄/频次逻辑校验',
        'methods': ['多源数据清洗', '跨系统比对', 'SQL疑点筛查', '规则校验', '原始记录回溯'],
        'queries': ['医保 卫健 数据审计 老年人健康管理 造假', '医院 串换诊疗项目 过度诊疗 数据分析', '死亡人员 体检记录 SQL 疑点筛查'],
    },
    '政策落实审计': {
        'focus': '重大政策、专项资金、项目落地、部门协同、两重两新、整改回头看',
        'methods': ['政策链条对标', '资金直达核查', '部门协同验证', '绩效目标比对', '整改回头看'],
        'queries': ['政策落实审计 两重 两新 审理', '重大政策落实 资金直达 整改闭环', '京津冀协同 审计逻辑 政策链条'],
    },
}

METHODS = {
    '数据比对': '将不同来源、不同口径的数据按对象、时间、金额、项目编码等关键字段进行交叉验证，识别异常和逻辑冲突。',
    '穿透核查': '沿政策、项目、资金、合同、凭证、现场和责任主体逐层追溯，形成闭环证据链。',
    '政策对标': '将项目执行情况与政策目标、支持范围、资金用途、绩效要求逐项比对，识别打折扣和最后一公里堵点。',
    '现场核验': '对数据疑点、工程量、服务真实性和项目实施情况开展踏勘、访谈、抽样和照片记录。',
    '整改闭环': '把问题清单、整改措施、责任单位、完成时限、回头看结果串成闭环，防止纸面整改。',
    '模型筛查': '基于规则、SQL、相似度、异常频次或风险画像模型，批量筛选疑点后回溯核实。',
}


def front(title, scene='LLM Wiki'):
    return f'---\ntitle: "{title}"\nscene: {scene}\ntags: [融策, LLM Wiki, 本地知识库]\nupdated: {datetime.now().strftime("%Y-%m-%d %H:%M")}\n---\n\n'


def write_wiki():
    WIKI.mkdir(parents=True, exist_ok=True)
    (WIKI / '00-Wiki总入口.md').write_text(front('融策 LLM Wiki 总入口') + '''# 融策 LLM Wiki 总入口

> 定位：LLM Wiki 是知识组织层，不替代 RAG，也不替代 Obsidian 案例库。它负责把场景、方法、案例和作业模板串成可演化的知识图谱。

## 四类页面

- [[01-审计场景页|审计场景页]]
- [[02-审计方法页|审计方法页]]
- [[03-案例资产页|案例资产页]]
- [[04-作业模板页|作业模板页]]

## 与其他系统的关系

- Obsidian 场景案例库：存放原文和逐篇审计逻辑。
- 融策标准作业体系 v2.0：沉淀训练清单、案例卡片、模板包、标准包、试点包。
- RAG 本地知识库：负责检索和召回相关片段。
- LLM Wiki：负责主题组织、导航和知识演化。

## 当前原则

- 不接外部 API。
- 先本地可查、可读、可维护。
- 等本地模型部署后，再接本地生成层。
''', encoding='utf-8')

    scene_lines = [front('审计场景页'), '# 审计场景页\n']
    for scene, cfg in SCENES.items():
        scene_lines.append(f'## {scene}\n')
        scene_lines.append(f'- 关注重点：{cfg["focus"]}')
        scene_lines.append(f'- 常用方法：' + '、'.join(cfg['methods']))
        scene_lines.append(f'- 场景案例库：[[审计案例库-OCR/{scene}|{scene}案例库]]')
        scene_lines.append(f'- 导航页：[[融策AI知识中枢/场景导航/{scene}导航|{scene}导航]]\n')
    (WIKI / '01-审计场景页.md').write_text('\n'.join(scene_lines), encoding='utf-8')

    method_lines = [front('审计方法页'), '# 审计方法页\n']
    for name, desc in METHODS.items():
        method_lines.append(f'## {name}\n')
        method_lines.append(f'- 方法定义：{desc}')
        method_lines.append('- 使用方式：先形成疑点，再回溯原始资料和责任主体，最后进入问题清单与整改闭环。\n')
    (WIKI / '02-审计方法页.md').write_text('\n'.join(method_lines), encoding='utf-8')

    (WIKI / '03-案例资产页.md').write_text(front('案例资产页') + '''# 案例资产页

## 核心入口

- [[审计案例库-OCR/融策标准作业体系 v2.0/01-训练清单/场景-审计逻辑-可复用方法训练清单 v2.0|全库训练清单 v2.0]]
- [[审计案例库-OCR/融策标准作业体系 v2.0/02-案例卡片|案例卡片]]
- [[审计案例库-OCR/融策标准作业体系 v2.0/00-逐篇审计逻辑提炼与场景同步报告|逐篇审计逻辑提炼报告]]

## 使用方式

1. 先按场景检索案例。
2. 再看案例内的“融策审计逻辑提炼”。
3. 最后复制可复用方法到实施方案或报告模板。
''', encoding='utf-8')

    (WIKI / '04-作业模板页.md').write_text(front('作业模板页') + '''# 作业模板页

## 标准作业体系

- [[审计案例库-OCR/融策标准作业体系 v2.0/03-融策审计项目可直接套用模板包|项目可直接套用模板包]]
- [[审计案例库-OCR/融策标准作业体系 v2.0/04-融策标准作业包 v2.0|标准作业包 v2.0]]
- [[审计案例库-OCR/融策标准作业体系 v2.0/05-融策实战试点包 v2.0|实战试点包 v2.0]]

## 交付模板雏形

- [[融策AI知识中枢/交付模板雏形|交付模板雏形目录]]

## 固定作业顺序

审计目标 → 审前调查 → 取证路径 → 问题表述 → 审计建议 → 汇报/专报。
''', encoding='utf-8')


def deliverable_md(scene, cfg):
    return front(f'{scene}交付版', '交付模板') + f'''# {scene}交付版

## 一、审计实施方案

### 项目背景

围绕{cfg['focus']}开展审计，揭示政策执行、业务真实性、程序合规、资金安全和绩效结果等问题。

### 审计目标

- 查清重点事项真实情况、业务流程和资金流向。
- 识别制度执行、过程管控、数据质量和整改责任方面的问题。
- 形成问题清单、取证单、报告/专报和整改建议。

### 审计重点

{chr(10).join('- ' + m for m in cfg['methods'])}

## 二、取数清单

| 序号 | 数据/资料 | 用途 | 提供单位 | 备注 |
|---:|---|---|---|---|
| 1 | 政策制度文件 | 判断依据 | 主管部门 | |
| 2 | 项目/业务台账 | 对象画像 | 实施单位 | |
| 3 | 资金拨付/结算明细 | 资金流向 | 财务/财政/医保 | |
| 4 | 合同/批复/会议纪要 | 程序核验 | 实施单位 | |
| 5 | 整改台账 | 闭环跟踪 | 被审计单位 | |

## 三、问题清单样表

| 序号 | 问题事实 | 依据 | 金额/数量 | 责任单位 | 风险影响 | 整改建议 |
|---:|---|---|---|---|---|---|
| 1 |  |  |  |  |  |  |

## 四、汇报提纲

1. 项目背景
2. 审计重点
3. 工作开展情况
4. 主要发现
5. 风险影响
6. 整改建议

## 五、专报初稿模板

### 基本情况

根据工作安排，审计组围绕{cfg['focus']}开展审计。

### 主要问题

经审计发现，……反映出相关单位在制度执行、过程管控和责任落实方面存在薄弱环节。

### 审计建议

建议相关单位对照问题清单限期整改，完善制度流程，建立长效治理机制。
'''


def write_deliverables():
    DELIVER.mkdir(parents=True, exist_ok=True)
    for scene, cfg in SCENES.items():
        safe = scene.replace('/', '_')
        (DELIVER / f'{safe}交付版.md').write_text(deliverable_md(scene, cfg), encoding='utf-8')
        csv_path = DELIVER / f'{safe}取数清单.csv'
        with csv_path.open('w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['序号', '数据/资料', '用途', '提供单位', '格式要求', '备注'])
            rows = [
                ['1', '政策制度文件', '判断依据', '主管部门', 'PDF/Word/Markdown', ''],
                ['2', '项目/业务台账', '对象画像', '实施单位', 'Excel原始明细', '不得只给汇总表'],
                ['3', '资金拨付/结算明细', '资金流向', '财务/财政/医保', 'Excel原始明细', '保留字段'],
                ['4', '合同/批复/会议纪要', '程序核验', '实施单位', 'PDF/扫描件/Word', ''],
                ['5', '整改台账', '闭环跟踪', '被审计单位', 'Excel/Word', ''],
            ]
            writer.writerows(rows)
        ppt = front(f'{scene}PPT汇报提纲', '交付模板') + f'''# {scene}PPT 汇报提纲

## 1. 项目背景

- 审计原因
- 审计范围
- 审计重点：{cfg['focus']}

## 2. 审计方法

{chr(10).join('- ' + m for m in cfg['methods'])}

## 3. 主要发现

- 问题一：
- 问题二：
- 问题三：

## 4. 风险影响

- 资金风险
- 管理风险
- 政策绩效风险
- 廉政风险

## 5. 整改建议

- 立即整改
- 制度完善
- 长效治理
'''
        (DELIVER / f'{safe}PPT汇报提纲.md').write_text(ppt, encoding='utf-8')


def update_checklist():
    if CHECKLIST.exists():
        text = CHECKLIST.read_text(encoding='utf-8', errors='replace')
        text = text.replace('- [ ] 升级 `融策AI知识中枢.md` 为正式导航页', '- [x] 升级 `融策AI知识中枢.md` 为正式导航页')
        text = text.replace('- [ ] 建立场景导航页：工程、政策落实、医保卫健/信息系统、国企、农业农村、绩效', '- [x] 建立场景导航页：工程、政策落实、医保卫健/信息系统、国企、农业农村、绩效')
        text = text.replace('- [ ] 建立 RAG 查询示例库', '- [x] 建立 RAG 查询示例库')
        text = text.replace('- [ ] 建立新增资料同步 SOP', '- [x] 建立新增资料同步 SOP')
        text = text.replace('- [ ] 建立 Wiki 总入口', '- [x] 建立 Wiki 总入口')
        text = text.replace('- [ ] 建立“审计场景页”', '- [x] 建立“审计场景页”')
        text = text.replace('- [ ] 建立“审计方法页”', '- [x] 建立“审计方法页”')
        text = text.replace('- [ ] 建立“案例资产页”', '- [x] 建立“案例资产页”')
        text = text.replace('- [ ] 建立“作业模板页”', '- [x] 建立“作业模板页”')
        text = text.replace('- [ ] 将 v2.0 作业体系链接进 Wiki', '- [x] 将 v2.0 作业体系链接进 Wiki')
        text = text.replace('- [ ] 工程审计 Word/Markdown 交付版', '- [x] 工程审计 Word/Markdown 交付版')
        text = text.replace('- [ ] 医保卫健数据审计 Word/Markdown 交付版', '- [x] 医保卫健数据审计 Word/Markdown 交付版')
        text = text.replace('- [ ] 政策落实审计 Word/Markdown 交付版', '- [x] 政策落实审计 Word/Markdown 交付版')
        text = text.replace('- [ ] Excel 取数清单字段版', '- [x] Excel 取数清单字段版')
        text = text.replace('- [ ] PPT 汇报提纲版', '- [x] PPT 汇报提纲版')
        CHECKLIST.write_text(text, encoding='utf-8')


def write_final_report():
    FINAL_REPORT.write_text(front('融策AI知识中枢-阶段一至四完成报告', '项目管理') + f'''# 融策AI知识中枢｜阶段一至四完成报告

## 完成时间

{datetime.now().strftime('%Y-%m-%d %H:%M')}

## 阶段一：稳定可用版

- 已升级 `融策AI知识中枢.md`。
- 已建立高频场景导航页。
- 已建立 RAG 查询示例库。
- 已建立新增资料同步 SOP。

## 阶段二：LLM Wiki 主题化

- 已建立 Wiki 总入口。
- 已建立审计场景页、审计方法页、案例资产页、作业模板页。
- 已将 v2.0 作业体系链接进 Wiki。

## 阶段三：交付模板雏形

- 已生成工程审计、医保卫健数据审计、政策落实审计交付版 Markdown。
- 已生成 CSV 取数清单字段版。
- 已生成 PPT 汇报提纲 Markdown 版。

## 阶段四：验证与收口

- 需继续执行：刷新总资料清单、重建 RAG、测试典型查询。

## 当前原则

- 不接外部 API。
- 不启用每日自动同步。
- 先本地可查、可读、可维护。
''', encoding='utf-8')


def main():
    write_wiki()
    write_deliverables()
    update_checklist()
    write_final_report()
    print('WIKI', WIKI)
    print('DELIVER', DELIVER)
    print('REPORT', FINAL_REPORT)

if __name__ == '__main__':
    main()
