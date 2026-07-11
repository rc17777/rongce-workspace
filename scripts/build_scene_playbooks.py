#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build boss/project-manager playbooks from original audit knowledge files.

Read-only for source materials. Outputs new markdown manuals under Rongce v2.0.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

VAULT = Path(r"C:\Users\scrccpa\Documents\Obsidian Vault")
CATALOG = VAULT / "审计资料清单.json"
CASE_ROOT = VAULT / "审计案例库-OCR"
V2_ROOT = CASE_ROOT / "融策标准作业体系 v2.0"
OUT_DIR = V2_ROOT / "06-场景作战手册"

CORE_SCENES = [
    "预算执行审计", "绩效审计", "工程审计", "社保民生审计", "其他审计", "信息系统审计",
    "国企审计", "资源环境审计", "经济责任审计", "内部审计", "金融审计", "农业农村审计",
    "政策落实审计", "教科文卫审计",
]
CORE_SCENE_SET = set(CORE_SCENES)
GENERATED_MARKERS = [
    "案例卡片", "模板", "标准作业包", "实战试点包", "训练清单", "方法词典",
    "资料总览", "老板版", "融策标准作业体系", "覆盖率与同步机制", "逐篇审计逻辑提炼",
    "知识库健康体检报告", "场景作战手册",
]

SCENE_CONFIG = {
    "预算执行审计": {
        "position": "财政预算安排、指标下达、支付执行、结余结转、决算反映和预算绩效的全链条审计。",
        "boss": ["财政收支真实性与规范性", "预算约束是否刚性", "专项资金是否沉淀或偏离用途", "预算绩效是否能支撑财政决策"],
        "startup": ["财政预算批复、指标文件、支付明细、决算报表", "按单位、项目、资金性质建立穿透台账", "先做预算数、执行数、决算数、绩效数四表勾稽"],
        "red_flags": ["预算调整频繁但依据不足", "年底集中支付、突击花钱", "结余结转长期沉淀", "项目绩效目标与资金安排脱节"],
        "deliverables": ["预算执行问题清单", "资金沉淀和低效使用台账", "预算绩效管理建议", "财政管理制度完善建议"],
    },
    "绩效审计": {
        "position": "围绕财政资金、政策项目和公共服务的投入、产出、效益、满意度与可持续性开展评价。",
        "boss": ["钱花出去有没有结果", "目标设置是否可量化可考核", "项目产出是否真实", "整改建议能否推动预算安排优化"],
        "startup": ["绩效目标表、预算批复、支出明细、项目成果、评价报告", "先拆目标，再拆指标，最后映射证据资料", "建立投入—过程—产出—效益证据链"],
        "red_flags": ["目标空泛不可考核", "产出数量有但质量弱", "资金支付进度快但成果滞后", "满意度调查样本和过程不可靠"],
        "deliverables": ["绩效评价指标体系", "绩效问题与原因分析", "低效无效资金清单", "预算安排优化建议"],
    },
    "工程审计": {
        "position": "覆盖立项审批、招投标、合同签订、变更签证、计量支付、竣工结算和资产交付的工程项目审计。",
        "boss": ["工程量和价格是否真实", "招投标是否合规公平", "变更签证是否成为套钱口", "项目决策和现场实施是否一致"],
        "startup": ["立项批复、招投标资料、合同、变更签证、计量支付、结算资料", "先搭项目全生命周期台账", "现场踏勘必须与合同、图纸、计量、支付同步核对"],
        "red_flags": ["先施工后审批", "低价中标高价结算", "无价材料定价不透明", "签证变更集中且缺少现场依据"],
        "deliverables": ["工程造价核减清单", "招投标疑点清单", "变更签证问题底稿", "项目管理整改建议"],
    },
    "社保民生审计": {
        "position": "围绕社保、医保、教育、住房、就业、救助等民生政策和资金的精准性、公平性和安全性审计。",
        "boss": ["资金是否发到该发的人", "待遇享受对象是否真实合规", "群众服务是否到位", "系统和部门数据是否一致"],
        "startup": ["受益对象清单、发放明细、业务系统数据、死亡/户籍/工商等比对数据", "先做对象资格和资金发放双校验", "重点抽查重复领取、死亡领取、超范围享受"],
        "red_flags": ["同人多头领取", "死亡人员继续享受待遇", "资格变化未及时停发", "服务记录和资金支付不匹配"],
        "deliverables": ["违规享受待遇清单", "民生资金追回建议", "系统数据治理建议", "监管闭环台账"],
    },
    "信息系统审计": {
        "position": "以业务系统、数据表、算法规则、日志和接口为对象，审查数据真实性、规则有效性和系统控制。",
        "boss": ["系统数据能不能信", "业务规则有没有漏洞", "跨系统数据是否打架", "能否用模型替代人工翻账"],
        "startup": ["字段字典、数据库表、业务规则、接口说明、日志、系统导出明细", "先要数据字典和业务流程，再写核查规则", "字段口径不清时先做样本回源验证"],
        "red_flags": ["关键字段为空或重复", "审批时间倒挂", "金额、数量、状态跨表不一致", "手工修改痕迹集中"],
        "deliverables": ["数据质量问题清单", "SQL/模型筛查规则", "系统内控漏洞清单", "数据治理整改建议"],
    },
    "国企审计": {
        "position": "围绕国有资产保值增值、三重一大决策、投资经营、采购交易、薪酬绩效和风险内控开展审计。",
        "boss": ["国资有没有流失", "重大决策是否合规", "关联交易是否输送利益", "经营风险是否被掩盖"],
        "startup": ["章程、三重一大资料、合同台账、财务明细、投资资料、采购资料", "先画资金、合同、股权和人员关系图", "重点穿透大额交易和异常供应商"],
        "red_flags": ["未履行集体决策", "关联方低买高卖", "应收款长期挂账", "投资项目亏损但责任不清"],
        "deliverables": ["国资风险清单", "关联交易穿透底稿", "投资项目问题清单", "内控整改建议"],
    },
    "资源环境审计": {
        "position": "围绕自然资源资产、生态环境治理、生态补偿资金、绿色发展目标和整改效果开展审计。",
        "boss": ["资源资产底数是否清楚", "生态资金是否用到实处", "治理项目是否真实有效", "整改是不是纸面整改"],
        "startup": ["资源台账、生态资金、项目资料、遥感影像、监测数据、整改台账", "先把资金、项目、空间位置三者叠起来", "现场核验与遥感/监测数据交叉验证"],
        "red_flags": ["项目位置与治理范围不一致", "监测数据异常平滑", "生态补偿对象不精准", "整改销号缺少现场证据"],
        "deliverables": ["资源环境问题图斑", "生态资金问题台账", "整改真实性核查表", "长效治理建议"],
    },
    "经济责任审计": {
        "position": "围绕领导干部任期内权力运行、重大决策、财政财务、资产资源、项目建设和整改责任开展审计。",
        "boss": ["责任边界能不能说清", "重大事项有没有违规决策", "财务和项目问题能否落实到责任链条", "评价结论是否稳妥可支撑"],
        "startup": ["权责清单、会议纪要、重大决策资料、财务报表、项目台账、整改资料", "先搭任期事项清单和权力运行链条", "问题定性必须同步考虑责任主体和发生期间"],
        "red_flags": ["重大事项未集体研究", "新官不理旧账", "政绩工程和形象工程", "整改责任长期悬空"],
        "deliverables": ["经济责任问题清单", "责任界定底稿", "履职评价材料", "整改责任建议"],
    },
    "内部审计": {
        "position": "服务单位治理、内控、风险管理、合规运营和整改闭环的内部监督。",
        "boss": ["制度有没有真正执行", "关键风险有没有人管", "内审成果能否转成管理动作", "整改是不是闭环"],
        "startup": ["内控制度、风险清单、业务台账、审计报告、整改台账", "先识别高频高损风险点", "用制度要求反推控制证据"],
        "red_flags": ["制度有但无执行记录", "同类问题反复发生", "整改只写说明不见动作", "关键岗位权限过大"],
        "deliverables": ["内控缺陷清单", "风险地图", "整改跟踪台账", "管理提升建议"],
    },
    "金融审计": {
        "position": "围绕资金流、债务、融资、担保、保证金、金融机构业务和财政金融风险开展审计。",
        "boss": ["资金最终流向哪里", "债务风险是否真实反映", "担保圈和资金链是否隐藏风险", "保证金和专户是否被占用"],
        "startup": ["银行流水、账户清单、融资合同、担保资料、债务台账、审批资料", "先做账户全量清单和资金流向图", "大额、频繁、整数、对倒交易优先筛查"],
        "red_flags": ["资金短期过桥", "同日进出或闭环流转", "担保链条过长", "债务台账与财务账不一致"],
        "deliverables": ["资金流向图", "债务风险清单", "担保圈分析", "异常交易底稿"],
    },
    "农业农村审计": {
        "position": "围绕乡村振兴、涉农补贴、农田水利、农村项目、集体资产和基层治理开展审计。",
        "boss": ["涉农资金有没有到户到项目", "补贴对象是否真实精准", "项目有没有建成见效", "基层权力运行是否透明"],
        "startup": ["项目台账、补贴清单、受益对象、验收资料、支付凭证、现场核验资料", "先按村、户、项目、资金建立明细台账", "补贴对象与户籍、土地、工商、死亡数据比对"],
        "red_flags": ["一户多补或虚假冒领", "项目验收与现场不符", "资金拨付到村后滞留", "村集体资产账实不符"],
        "deliverables": ["涉农资金问题清单", "补贴异常对象台账", "项目现场核验记录", "基层治理建议"],
    },
    "政策落实审计": {
        "position": "围绕重大政策部署、任务分解、资金保障、项目落地、部门协同和整改成效开展审计。",
        "boss": ["政策有没有真正落地", "任务有没有层层空转", "资金和项目是否支撑政策目标", "部门协同有没有断点"],
        "startup": ["政策文件、实施方案、任务清单、资金文件、项目库、绩效和整改资料", "先拆政策目标、任务、责任、资金、项目五张表", "用时间线检查推进滞后和责任空档"],
        "red_flags": ["方案照抄上级但无本地措施", "项目库与政策目标脱节", "资金安排慢于任务进度", "整改销号依据不足"],
        "deliverables": ["政策落实堵点清单", "任务资金项目对照表", "部门责任链条", "政策优化建议"],
    },
    "教科文卫审计": {
        "position": "围绕教育、科技、文化、卫生等公共服务领域项目资金、资源配置、服务绩效和合规管理开展审计。",
        "boss": ["公共服务资源是否公平有效", "项目资金是否合规使用", "服务数量和质量是否真实", "行业监管是否到位"],
        "startup": ["项目资料、资金明细、服务记录、业务系统数据、绩效评价和监管资料", "先按项目、机构、对象、资金四类建台账", "服务记录必须和资金支付、系统数据互证"],
        "red_flags": ["服务记录批量雷同", "设备采购闲置", "科研/项目资金挤占挪用", "绩效数据缺少原始支撑"],
        "deliverables": ["公共服务绩效问题清单", "项目资金核查底稿", "资源闲置清单", "行业监管建议"],
    },
    "其他审计": {
        "position": "沉淀综合审计方法、研究型审计、组织方式、质量控制和成果转化经验。",
        "boss": ["哪些方法能复用", "哪些组织方式能提升效率", "哪些成果能转成公司标准产品", "哪些经验适合培训团队"],
        "startup": ["方法文章、综合案例、制度文件、项目复盘、成果材料", "先判断可迁移场景", "把经验拆成流程、表单、话术、底稿模板"],
        "red_flags": ["只有口号没有操作步骤", "方法脱离资料条件", "案例无法形成证据链", "成果难以复制到项目"],
        "deliverables": ["方法库条目", "培训素材", "项目复盘模板", "标准作业升级建议"],
    },
}

METHOD_PATTERNS = [
    "数据比对", "穿透核查", "政策对标", "资金绩效分析", "现场核验", "整改闭环", "模型筛查",
    "招投标链条拆解", "交易台账比对", "SQL", "遥感", "资金流水", "关联分析", "内控测试",
]

SCENE_KEYWORDS = {
    "预算执行审计": ["预算", "决算", "财政", "支出", "指标", "结转", "结余", "执行"],
    "绩效审计": ["绩效", "评价", "效益", "成本", "产出", "指标", "目标"],
    "工程审计": ["工程", "项目", "招标", "投标", "结算", "造价", "签证", "变更", "施工", "PPP", "特许经营", "防洪", "土方"],
    "社保民生审计": ["社保", "医保", "民生", "救助", "补贴", "养老", "就业", "群众"],
    "信息系统审计": ["数据", "系统", "信息化", "SQL", "Excel", "模型", "算法", "平台", "数字"],
    "国企审计": ["国企", "企业", "国资", "投资", "经营", "集团", "三重一大", "公司"],
    "资源环境审计": ["资源", "环境", "生态", "自然资源", "耕地", "水", "环保", "绿色"],
    "经济责任审计": ["经济责任", "领导干部", "履职", "任期", "责任", "权力"],
    "内部审计": ["内部审计", "内控", "风险", "治理", "整改", "监督"],
    "金融审计": ["金融", "资金", "债务", "融资", "担保", "银行", "账户", "保证金"],
    "农业农村审计": ["农业", "农村", "乡村", "涉农", "农田", "粮食", "补贴", "水利"],
    "政策落实审计": ["政策", "落实", "改革", "任务", "部署", "执行", "协同"],
    "教科文卫审计": ["教育", "科技", "文化", "卫生", "医院", "学校", "科研", "医疗"],
    "其他审计": ["研究型审计", "审计机关", "方法", "经验", "质量", "成果", "监督"],
}


def load_catalog() -> list[dict]:
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def combined_text(item: dict) -> str:
    return " ".join(str(item.get(k, "")) for k in ("path", "filename", "title", "scene"))


def is_generated_or_noncase(item: dict) -> bool:
    text = combined_text(item)
    return item.get("scene") not in CORE_SCENE_SET or any(marker in text for marker in GENERATED_MARKERS)


def is_scene_sync_copy(item: dict) -> bool:
    rel = item.get("path", "")
    parts = re.split(r"[\\/]", rel)
    return len(parts) == 3 and parts[0] == "审计案例库-OCR" and parts[1] in CORE_SCENE_SET


def physical_path(item: dict) -> Path:
    return VAULT / item["path"]


def read_text(item: dict) -> str:
    path = physical_path(item)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def section(text: str, heading: str) -> str:
    pattern = rf"###\s*{re.escape(heading)}\s*\n\n?(.*?)(?=\n###\s+|\n##\s+|\Z)"
    match = re.search(pattern, text, flags=re.S)
    if not match:
        return ""
    return re.sub(r"\s+", " ", match.group(1)).strip()


def summary(text: str) -> str:
    # Prefer original article text. The appended auto-enrichment block is useful
    # for structure, but a playbook summary should not start with metadata like
    # "自动提炼时间".
    source = text.split("## 融策审计逻辑提炼", 1)[0]
    m = re.search(r"(?:案例摘要|内容摘要|摘要)\s*[:：]?\s*(.*?)(?=\n##|\n#|\Z)", source, flags=re.S)
    if m:
        source = m.group(1)
    source = re.sub(r"---.*?---", "", source, flags=re.S)
    source = re.sub(r"```.*?```", "", source, flags=re.S)
    source = re.sub(r"[#>*`\-\|]+", " ", source)
    source = re.sub(r"\s+", " ", source).strip()
    return source[:180] + ("..." if len(source) > 180 else "")


def source_before_logic(text: str) -> str:
    return text.split("## 融策审计逻辑提炼", 1)[0]


def count_methods(items: list[dict], texts: dict[str, str]) -> Counter:
    counter: Counter = Counter()
    for item in items:
        text = source_before_logic(texts.get(item["path"], "")) + " " + combined_text(item)
        for method in METHOD_PATTERNS:
            if method.lower() in text.lower():
                counter[method] += 1
    return counter


def scene_relevance(scene: str, item: dict, text: str) -> int:
    title_text = combined_text(item)
    haystack = (title_text + " " + source_before_logic(text)[:2000]).lower()
    score = 0
    for keyword in SCENE_KEYWORDS.get(scene, []):
        kw = keyword.lower()
        if kw in haystack:
            score += 3 if kw in title_text.lower() else 1
    if scene == "工程审计" and not any(k.lower() in title_text.lower() for k in SCENE_KEYWORDS[scene]):
        score -= 5
    return score


def pick_cases(scene: str, items: list[dict], texts: dict[str, str], limit: int = 12) -> list[dict]:
    scored = []
    for item in items:
        text = texts.get(item["path"], "")
        original = source_before_logic(text)
        score = scene_relevance(scene, item, text)
        if "技术方法" in original or "分析思路" in combined_text(item):
            score += 4
        if "案例" in original or "案例故事" in original:
            score += 3
        score += min(len(original) // 3000, 3)
        scored.append((score, item))
    relevant = [(score, item) for score, item in scored if score > 0]
    pool = relevant if relevant else scored
    return [item for _, item in sorted(pool, key=lambda x: (-x[0], x[1].get("title", "")))[:limit]]


def md_list(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items]


def scene_filename(index: int, scene: str) -> str:
    return f"{index:02d}-{scene}作战手册.md"


def build_scene_manual(index: int, scene: str, items: list[dict], texts: dict[str, str]) -> str:
    cfg = SCENE_CONFIG[scene]
    methods = count_methods(items, texts)
    picked = pick_cases(scene, items, texts)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines: list[str] = [
        "---",
        f'title: "{scene}作战手册"',
        f"scene: {scene}",
        "tags: [融策, 场景作战手册, 项目经理, 老板版]",
        "---",
        "",
        f"# {scene}作战手册",
        "",
        f"> 生成时间：{now}  ",
        f"> 来源资料：{len(items)} 篇原始资料  ",
        "> 用途：老板判断项目机会，项目经理快速启动审前调查、取数、实施和成果交付。",
        "",
        "## 1. 场景定位",
        "",
        cfg["position"],
        "",
        "## 2. 老板先看：值不值得接、怎么定打法",
        "",
        *md_list(cfg["boss"]),
        "",
        "## 3. 项目经理启动清单",
        "",
        *md_list(cfg["startup"]),
        "",
        "## 4. 必查资料清单",
        "",
        "- 政策制度：上级政策、部门制度、实施方案、会议纪要、审批文件。",
        "- 业务台账：项目库、对象清单、合同台账、支付台账、整改台账。",
        "- 财务资料：预算指标、支付明细、凭证附件、银行流水、决算报表。",
        "- 系统数据：字段字典、系统导出明细、日志、接口数据、历史变更记录。",
        "- 外部佐证：工商、户籍、自然资源、遥感、现场照片、第三方报告。",
        "",
        "## 5. 高频风险信号",
        "",
        *md_list(cfg["red_flags"]),
        "",
        "## 6. 常用审计方法",
        "",
    ]
    if methods:
        for method, count in methods.most_common(10):
            lines.append(f"- {method}：资料库命中 {count} 次，适合优先固化为项目检查程序。")
    else:
        lines.append("- 以政策对标、台账比对、资金穿透、现场核验、整改闭环为基础方法组合。")
    lines += [
        "",
        "## 7. 典型案例与参考资料",
        "",
    ]
    for idx, item in enumerate(picked, start=1):
        title = item.get("title") or item.get("filename")
        rel = item.get("path")
        text = texts.get(item["path"], "")
        lines.extend([
            f"### {idx}. {title}",
            f"- 路径：`{rel}`",
            f"- 可借鉴点：{summary(text)}",
            "",
        ])
    lines += [
        "## 8. 交付成果模板",
        "",
        *md_list(cfg["deliverables"]),
        "- 审计发现底稿：问题事实、定性依据、金额/数量、责任主体、证据索引、整改建议。",
        "- 领导汇报页：项目背景、关键发现、风险影响、整改抓手、可复制经验。",
        "",
        "## 9. 现场工作节奏",
        "",
        "- 第 1 天：审前调查、资料清单、项目台账、访谈提纲。",
        "- 第 2-3 天：数据清洗、台账勾稽、疑点初筛、样本抽取。",
        "- 第 4-5 天：凭证/合同/现场回源核验，形成问题底稿。",
        "- 第 6 天后：与被审计单位沟通事实，补证据、定责任、写建议。",
        "",
        "## 10. 质量控制红线",
        "",
        "- 没有证据链的问题不上报告。",
        "- 只有数据异常、没有业务解释的问题先列疑点，不直接定性。",
        "- 金额、对象、期间、政策依据必须四件套齐全。",
        "- 整改建议必须能落到责任部门、时间节点和制度动作。",
        "",
    ]
    return "\n".join(lines)


def build_overview(scene_items: dict[str, list[dict]]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    total = sum(len(items) for items in scene_items.values())
    lines = [
        "---",
        'title: "融策审计场景作战手册总览"',
        "scene: 标准作业包",
        "tags: [融策, 场景作战手册, 老板版, 项目经理]",
        "---",
        "",
        "# 融策审计场景作战手册总览",
        "",
        f"> 生成时间：{now}  ",
        f"> 原始资料口径：{total} 篇  ",
        "> 定位：把资料库从“能检索”推进到“能接活、能开工、能交付”。",
        "",
        "## 一、怎么用",
        "",
        "- 老板看：每个场景的项目机会、风险口、交付物和团队打法。",
        "- 项目经理看：启动清单、必查资料、疑点模型、现场节奏和质量红线。",
        "- 新人看：先照手册做审前调查，再回到案例库查具体案例。",
        "- 复盘看：每做完一个项目，把新问题、新资料、新底稿反哺到对应场景。",
        "",
        "## 二、场景分册索引",
        "",
        "| 场景 | 原始资料数 | 分册 |",
        "|---|---:|---|",
    ]
    for idx, scene in enumerate(CORE_SCENES, start=1):
        items = scene_items.get(scene, [])
        if not items:
            continue
        filename = scene_filename(idx, scene)
        lines.append(f"| {scene} | {len(items)} | [[{filename[:-3]}]] |")
    lines += [
        "",
        "## 三、老板版场景选择",
        "",
        "| 客户需求 | 优先场景 | 快速判断 |",
        "|---|---|---|",
        "| 财政资金花得是否规范 | 预算执行审计 / 专项资金审计 / 绩效审计 | 看资金链、项目链、绩效链是否能打通 |",
        "| 工程项目有没有猫腻 | 工程审计 / 招投标相关方法 | 看招投标、合同、变更、结算、现场是否能互证 |",
        "| 领导干部任期评价 | 经济责任审计 | 看重大决策、财务项目、责任期间和责任边界 |",
        "| 民生资金是否精准 | 社保民生审计 / 农业农村审计 | 看对象资格、发放记录和外部数据比对 |",
        "| 想做数字化审计 | 信息系统审计 / 金融审计 | 看数据字段、业务规则、资金流水是否可取得 |",
        "| 国企经营和内控风险 | 国企审计 / 内部审计 | 看三重一大、关联交易、投资经营和内控证据 |",
        "",
        "## 四、项目经理通用打法",
        "",
        "1. 先画三张图：政策任务图、资金流向图、业务流程图。",
        "2. 再建四张表：项目台账、对象清单、支付明细、问题疑点表。",
        "3. 同步做两类核验：数据勾稽核验、现场/凭证回源核验。",
        "4. 最后形成一条链：问题事实 → 定性依据 → 影响金额/范围 → 责任主体 → 整改建议。",
        "",
        "## 五、不要踩的坑",
        "",
        "- 不要只讲案例故事，要落到资料清单和审计程序。",
        "- 不要只跑数据模型，要回源业务资料验证。",
        "- 不要只写问题金额，要讲清政策影响、管理漏洞和整改抓手。",
        "- 不要把场景同步副本当原始资料数量汇报。",
        "",
    ]
    return "\n".join(lines)


def build_startup_checklist(scene_items: dict[str, list[dict]]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "---",
        'title: "融策审计项目启动清单"',
        "scene: 标准作业包",
        "tags: [融策, 项目启动, 审前调查, 项目经理]",
        "---",
        "",
        "# 融策审计项目启动清单",
        "",
        f"> 生成时间：{now}  ",
        "> 用途：接到项目后 30 分钟内确定打法，1 天内发出资料清单，3 天内形成疑点初筛。",
        "",
        "## 1. 接活判断",
        "",
        "- 项目类型属于哪个审计场景？是否需要组合场景？",
        "- 客户真正要的是查问题、做评价、出报告、还是建制度？",
        "- 资料可得性如何：财政、业务、系统、现场、外部数据能否取得？",
        "- 团队是否具备数据分析、工程、财务、政策研究等能力？",
        "",
        "## 2. 审前调查四件套",
        "",
        "- 政策制度包：政策文件、实施方案、管理办法、会议纪要。",
        "- 业务台账包：项目库、对象清单、合同台账、审批台账。",
        "- 资金数据包：预算指标、支付明细、凭证附件、银行流水。",
        "- 结果证据包：验收资料、绩效报告、现场照片、整改资料。",
        "",
        "## 3. 第一轮访谈问题",
        "",
        "- 这项工作由谁负责？责任链条怎么分？",
        "- 钱从哪里来、到哪里去、经过哪些账户或单位？",
        "- 项目或对象如何申报、审核、实施、验收、评价？",
        "- 历史上最容易出问题的环节是什么？已有整改是否闭环？",
        "",
        "## 4. 数据初筛动作",
        "",
        "- 查重复：人、单位、项目、账号、手机号、地址、证照号。",
        "- 查异常：大额、整数、频繁、临界值、年底集中、审批倒挂。",
        "- 查不一致：预算—支付—合同—验收—绩效五类数据互相勾稽。",
        "- 查断点：有资金无项目、有项目无验收、有验收无现场、有整改无证据。",
        "",
        "## 5. 分场景启动入口",
        "",
        "| 场景 | 原始资料数 | 第一动作 |",
        "|---|---:|---|",
    ]
    for scene in CORE_SCENES:
        if scene not in scene_items:
            continue
        cfg = SCENE_CONFIG[scene]
        first_action = cfg["startup"][0]
        lines.append(f"| {scene} | {len(scene_items[scene])} | {first_action} |")
    lines += [
        "",
        "## 6. 质量控制",
        "",
        "- 每个问题至少有一个政策依据、一个事实证据、一个金额/数量/范围口径。",
        "- 数据疑点必须回源到合同、凭证、台账、现场或访谈纪要。",
        "- 报告建议必须可执行，不写“加强管理”这种空气话。",
        "- 重大问题先内部复核，再与被审计单位核事实，不抢跑定性。",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    data = load_catalog()
    originals = [item for item in data if not is_generated_or_noncase(item) and not is_scene_sync_copy(item)]
    by_scene: dict[str, list[dict]] = defaultdict(list)
    texts: dict[str, str] = {}
    missing = []
    for item in originals:
        path = physical_path(item)
        if not path.exists():
            missing.append(item)
            continue
        by_scene[item["scene"]].append(item)
        texts[item["path"]] = read_text(item)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    files = []
    overview = OUT_DIR / "00-总览-老板和项目经理版.md"
    overview.write_text(build_overview(by_scene), encoding="utf-8")
    files.append(overview)
    startup = OUT_DIR / "00-项目启动清单.md"
    startup.write_text(build_startup_checklist(by_scene), encoding="utf-8")
    files.append(startup)

    for idx, scene in enumerate(CORE_SCENES, start=1):
        items = by_scene.get(scene, [])
        if not items:
            continue
        path = OUT_DIR / scene_filename(idx, scene)
        path.write_text(build_scene_manual(idx, scene, items, texts), encoding="utf-8")
        files.append(path)

    manifest_lines = [
        "# 场景作战手册生成清单",
        "",
        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- 原始资料数：{len(originals)}",
        f"- 已读取资料数：{sum(len(items) for items in by_scene.values())}",
        f"- 缺失资料数：{len(missing)}",
        f"- 输出文件数：{len(files)}",
        "",
        "## 输出文件",
        "",
    ]
    for file in files:
        manifest_lines.append(f"- `{file}`")
    if missing:
        manifest_lines.extend(["", "## 缺失资料", ""])
        for item in missing[:50]:
            manifest_lines.append(f"- `{item.get('path')}`")
    manifest = OUT_DIR / "00-生成清单.md"
    manifest.write_text("\n".join(manifest_lines), encoding="utf-8")
    files.append(manifest)

    print(f"ORIGINALS {len(originals)}")
    print(f"READ {sum(len(items) for items in by_scene.values())}")
    print(f"MISSING {len(missing)}")
    print(f"SCENES {len(by_scene)}")
    print(f"FILES {len(files)}")
    print(f"OUT_DIR {OUT_DIR}")


if __name__ == "__main__":
    main()
