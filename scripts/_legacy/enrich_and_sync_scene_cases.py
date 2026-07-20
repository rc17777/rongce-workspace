#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Enrich every real audit article/case with audit logic and sync to scene libraries."""
from __future__ import annotations

import json
import re
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path

VAULT = Path(r'C:\Users\scrccpa\Documents\Obsidian Vault')
CATALOG = VAULT / '审计资料清单.json'
SCENE_ROOT = VAULT / '审计案例库-OCR'
REPORT = SCENE_ROOT / '融策标准作业体系 v2.0' / '00-逐篇审计逻辑提炼与场景同步报告.md'

CORE_SCENES = {
    '工程审计', '政策落实审计', '国企审计', '信息系统审计', '农业农村审计',
    '预算执行审计', '绩效审计', '经济责任审计', '社保民生审计', '资源环境审计',
    '专项资金审计', '金融审计', '内部审计', '教科文卫审计', '其他审计'
}
GENERATED_MARKERS = ['案例卡片', '模板', '标准作业包', '实战试点包', '训练清单', '方法词典', '资料总览', '老板版', '融策标准作业体系']

SCENE_HINTS = {
    '工程审计': {
        'target': '围绕工程项目立项、招投标、合同执行、变更签证、结算支付和现场实施情况，揭示程序不规范、工程量不实、资金支付不当和整改责任不清等问题。',
        'object': '建设单位、主管部门、施工/监理/代理机构、项目台账、合同及支付资料。',
        'data': '立项批复、招投标资料、合同及补充协议、设计变更签证、计量支付、竣工验收、财政评审/结算资料。',
        'method': '招投标链条拆解、交易台账比对、合同支付穿透、现场踏勘。',
    },
    '政策落实审计': {
        'target': '围绕重大政策部署、专项资金安排、项目落地、部门协同和整改闭环，揭示政策执行打折扣、资金使用偏离、项目推进滞后和监管缺位等问题。',
        'object': '主管部门、实施单位、政策项目库、资金拨付链条和绩效目标。',
        'data': '政策文件、实施方案、项目申报资料、资金下达和拨付明细、绩效评价、整改台账。',
        'method': '政策链条对标、资金直达核查、多部门数据交叉验证、整改回头看。',
    },
    '国企审计': {
        'target': '围绕国资安全、企业治理、投资经营、奖补资金和风险内控，揭示决策不规范、内控失效、资金流向异常和经营风险。',
        'object': '国有企业、出资监管部门、投资项目、资金往来、三重一大决策资料。',
        'data': '公司章程、会议纪要、合同台账、财务明细、投资资料、采购和资产管理资料。',
        'method': '三重一大核查、资金流向穿透、异常交易筛查、内控测试。',
    },
    '信息系统审计': {
        'target': '围绕业务系统、多源数据、算法模型和数据治理，揭示数据不一致、业务真实性不足、异常行为和系统管控漏洞。',
        'object': '业务系统、数据表、主管部门和业务经办单位。',
        'data': '系统导出明细、字段字典、业务台账、结算/支付明细、日志或规则配置。',
        'method': '字段清洗、跨系统比对、SQL疑点筛查、规则校验、模型/相似度筛查。',
    },
    '农业农村审计': {
        'target': '围绕乡村振兴、涉农资金、基层项目、补贴发放和权力运行，揭示资金发放不实、项目实施不到位和绩效不佳等问题。',
        'object': '农业农村主管部门、乡镇村组、项目实施单位和受益对象。',
        'data': '项目台账、补贴台账、受益对象清单、验收资料、资金拨付凭证、现场核验资料。',
        'method': '涉农台账比对、受益对象核验、现场踏勘/无人机、资金绩效分析。',
    },
    '预算执行审计': {
        'target': '围绕预算编制、预算执行、财政收支、专项支出和绩效结果，揭示预算约束不严、支出不规范和资金绩效不足。',
        'object': '财政部门、预算单位、预算指标和支付链条。',
        'data': '预算批复、指标文件、支付明细、决算报表、项目支出台账。',
        'method': '预算指标比对、支付进度分析、结余结转核查、三公经费筛查。',
    },
    '绩效审计': {
        'target': '围绕绩效目标、投入产出、效益评价和整改效果，揭示目标设置不合理、项目绩效不足和成果转化不充分。',
        'object': '项目主管部门、实施单位、绩效目标和评价指标体系。',
        'data': '绩效目标表、资金支出明细、产出成果、评价报告和整改材料。',
        'method': '绩效目标对标、指标完成度分析、成本效益分析、整改闭环。',
    },
    '经济责任审计': {
        'target': '围绕领导干部履职、权力运行、重大决策、财政财务管理和责任界定，揭示履职不到位、决策不规范和政绩观偏差。',
        'object': '被审计领导干部所在单位、重大事项、资金资产资源和权力运行链条。',
        'data': '权责清单、会议纪要、重大决策资料、财务报表、项目台账、整改资料。',
        'method': '权责清单对照、重大事项穿透、政绩观偏差识别、责任链条分析。',
    },
    '社保民生审计': {
        'target': '围绕民生政策、社保医保、教育医疗和群众利益，揭示资金发放不准、服务不实和监管薄弱等问题。',
        'object': '民生主管部门、服务机构、受益对象和资金发放链条。',
        'data': '受益对象清单、资金发放明细、服务记录、系统数据、投诉线索。',
        'method': '受益对象比对、资金发放核查、服务真实性验证、群众诉求线索分析。',
    },
    '资源环境审计': {
        'target': '围绕自然资源资产、生态补偿、环境治理和绿色发展，揭示资源管理不到位、生态资金使用不规范和整改效果不实。',
        'object': '资源环境主管部门、项目实施单位、生态资金和自然资源台账。',
        'data': '资源台账、生态补偿资金资料、项目资料、监测数据、现场核验记录。',
        'method': '资源台账比对、生态补偿资金核查、现场核验、整改效果跟踪。',
    },
    '专项资金审计': {
        'target': '围绕专项资金分配、拨付、使用、绩效和监管，揭示虚报冒领、截留挪用、闲置沉淀和绩效不足。',
        'object': '资金主管部门、项目单位、受益对象和资金支付链条。',
        'data': '资金文件、项目库、支付明细、票据凭证、验收和绩效资料。',
        'method': '资金链条穿透、项目库比对、票据凭证核验、绩效评价。',
    },
    '金融审计': {
        'target': '围绕保证金、融资、债务、资金链条和金融风险，揭示资金沉淀、违规融资、担保风险和异常交易。',
        'object': '金融机构、主管部门、资金账户、债务台账和交易主体。',
        'data': '资金流水、合同协议、担保资料、债务台账、审批资料。',
        'method': '资金流水核查、担保关系穿透、债务台账比对、异常交易识别。',
    },
    '内部审计': {
        'target': '围绕内控、风险管理、公司治理和整改闭环，揭示制度执行不到位、监督弱化和治理效能不足。',
        'object': '内部审计机构、被审计业务部门、风险清单和整改台账。',
        'data': '内控制度、内审计划、审计报告、整改台账、风险管理资料。',
        'method': '内控制度测试、风险清单核验、整改台账跟踪、治理建议转化。',
    },
    '教科文卫审计': {
        'target': '围绕教育、科技、文化、卫生项目和资金绩效，揭示项目管理不规范、资金使用不合规和服务绩效不足。',
        'object': '教科文卫主管部门、学校医院科研文化单位、项目和资金链条。',
        'data': '项目资料、资金明细、服务记录、业务系统数据、绩效评价材料。',
        'method': '项目资金核查、服务真实性验证、绩效指标分析、业务数据比对。',
    },
    '其他审计': {
        'target': '围绕审计管理、研究型审计、方法论和综合案例，提炼可迁移的组织方式、研究方法和成果转化路径。',
        'object': '审计机关、综合监督事项、方法论文章和经验材料。',
        'data': '工作方案、制度文件、研究材料、审计成果和整改转化资料。',
        'method': '研究型审计、经验复盘、制度机制分析、成果转化。',
    },
}


def is_generated(item):
    scene = item.get('scene', '')
    s = f"{item.get('path','')} {item.get('title','')} {item.get('filename','')}"
    return scene not in CORE_SCENES or any(m in s for m in GENERATED_MARKERS)


def ensure_title(text, item):
    if text.startswith('---'):
        return text
    title = item.get('title') or Path(item['path']).stem
    scene = item.get('scene') or '其他审计'
    return f'---\ntitle: "{title}"\nscene: {scene}\ntags: [审计案例, 融策审计逻辑]\n---\n\n' + text


def strip_existing_logic(text):
    # Avoid duplicate section when rerun.
    return re.sub(r'\n## 融策审计逻辑提炼\n\n.*?(?=\n## |\Z)', '\n', text, flags=re.S).rstrip() + '\n'


def extract_summary(text):
    m = re.search(r'## 内容摘要\n\n(.*?)(?:\n## |\Z)', text, re.S)
    if m:
        s = m.group(1)
    else:
        s = re.sub(r'^---.*?---', '', text, flags=re.S)
    s = re.sub(r'[#>`*\-\s]+', '', s).strip()
    return s[:220] + ('...' if len(s) > 220 else '')


def logic_section(item, text):
    scene = item.get('scene') or '其他审计'
    hint = SCENE_HINTS.get(scene, SCENE_HINTS['其他审计'])
    title = item.get('title') or Path(item['path']).stem
    summary = extract_summary(text)
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    return f'''
## 融策审计逻辑提炼

> 自动提炼时间：{now}  
> 场景归类：{scene}  
> 原始路径：`{item['path']}`

### 1. 场景定位

{title} 属于 **{scene}** 场景。资料核心内容可概括为：{summary}

### 2. 审计目标

{hint['target']}

### 3. 审计对象与关键资料

- 审计对象：{hint['object']}
- 关键资料：{hint['data']}

### 4. 审计方法

{hint['method']}

### 5. 疑点逻辑

- 从政策/制度要求出发，识别业务流程中容易失控的关键环节。
- 从资金、项目、对象、时间、数量等字段切入，筛查异常记录和逻辑冲突。
- 将数据疑点回溯到合同、凭证、台账、现场记录和责任主体，形成证据链。

### 6. 可复用方法

- 可作为同类 **{scene}** 项目的审前调查参考。
- 可复用其中的问题识别思路、取证路径和整改建议表达。
- 可同步纳入融策标准作业体系 v2.0 的训练清单、案例卡片和项目模板。
'''


def safe_scene_path(scene, filename):
    return SCENE_ROOT / scene / filename


def main():
    data = json.loads(CATALOG.read_text(encoding='utf-8'))
    real = [x for x in data if not is_generated(x)]
    enriched = 0
    synced = 0
    failed = []
    by_scene = Counter()

    for item in real:
        src = VAULT / item['path']
        if not src.exists():
            failed.append((item['path'], 'missing'))
            continue
        try:
            text = src.read_text(encoding='utf-8', errors='replace')
            text = ensure_title(text, item)
            text = strip_existing_logic(text)
            text = text + logic_section(item, text)
            src.write_text(text, encoding='utf-8')
            enriched += 1
            scene = item['scene']
            by_scene[scene] += 1

            # Sync one enriched copy into the scene library root.
            dst_dir = SCENE_ROOT / scene
            dst_dir.mkdir(parents=True, exist_ok=True)
            dst = dst_dir / src.name
            if src.resolve() != dst.resolve():
                # Prefix with source folder if filename collision and target belongs to another source.
                if dst.exists():
                    try:
                        existing = dst.read_text(encoding='utf-8', errors='replace')
                    except Exception:
                        existing = ''
                    if item['path'] not in existing:
                        stem = src.stem[:80]
                        dst = dst_dir / f'{stem}__{abs(hash(item["path"])) % 100000}.md'
                shutil.copy2(src, dst)
                synced += 1
        except Exception as e:
            failed.append((item['path'], repr(e)))

    report_lines = [
        '---',
        'title: "逐篇审计逻辑提炼与场景同步报告"',
        'scene: 标准作业包',
        'tags: [融策, 审计逻辑, 场景同步]',
        '---\n',
        '# 逐篇审计逻辑提炼与场景同步报告\n',
        f'- 执行时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}',
        f'- 真实案例/文章数量：{len(real)}',
        f'- 已写入“融策审计逻辑提炼”模块：{enriched}',
        f'- 已同步到场景案例库根目录的副本：{synced}',
        f'- 失败数量：{len(failed)}',
        '',
        '## 场景分布\n',
    ]
    for scene, count in by_scene.most_common():
        report_lines.append(f'- {scene}：{count} 篇')
    if failed:
        report_lines.append('\n## 失败样例\n')
        for path, err in failed[:50]:
            report_lines.append(f'- `{path}`：{err}')
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text('\n'.join(report_lines), encoding='utf-8')

    print('REAL', len(real))
    print('ENRICHED', enriched)
    print('SYNCED_COPIES', synced)
    print('FAILED', len(failed))
    print('REPORT', REPORT)

if __name__ == '__main__':
    main()
