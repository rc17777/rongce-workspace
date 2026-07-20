#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build refined SOP manuals for priority audit scenes."""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

VAULT = Path(r"C:\Users\scrccpa\Documents\Obsidian Vault")
CATALOG = VAULT / "审计资料清单.json"
V2_ROOT = VAULT / "审计案例库-OCR" / "融策标准作业体系 v2.0"
PLAYBOOK_DIR = V2_ROOT / "06-场景作战手册"
OUT_DIR = V2_ROOT / "07-重点场景精修SOP"

GENERATED_MARKERS = [
    "案例卡片", "模板", "标准作业包", "实战试点包", "训练清单", "方法词典",
    "资料总览", "老板版", "融策标准作业体系", "覆盖率与同步机制", "逐篇审计逻辑提炼",
    "知识库健康体检报告", "场景作战手册", "重点场景精修SOP",
]

SOPS = {
    "绩效评价": {
        "source_scenes": ["绩效审计", "预算执行审计"],
        "keywords": ["绩效", "评价", "预算绩效", "成本绩效", "事前绩效", "指标", "效益", "零基预算"],
        "source_manual": PLAYBOOK_DIR / "02-绩效审计作战手册.md",
        "filename": "01-绩效评价精修SOP.md",
        "position": "适用于财政重点项目、部门整体支出、专项资金、政府购买服务、公共服务项目、成本预算绩效和事前绩效评估。核心不是写评分表，而是判断财政资金是否形成真实产出和公共效益。",
        "boss_decision": [
            "客户要的是第三方绩效评价、财政监督检查，还是预算安排优化建议，三者交付深度不同。",
            "资料能否取得到项目台账、支付明细、绩效目标、产出证明和服务对象反馈；缺两类以上，评价会变成作文。",
            "项目是否有可量化产出或可核验服务对象；纯口号型项目要先做目标重构。",
            "是否具备后续预算挂钩空间；能影响来年预算安排的项目，成果价值更高。",
        ],
        "workflow": [
            ("审前定位", "确认评价对象、评价期间、资金范围、主管部门、实施单位、评价目的。"),
            ("目标拆解", "把总体目标拆成投入、过程、产出、效益、满意度、可持续六类指标。"),
            ("证据映射", "每个指标必须匹配至少一个可取得证据，不能取证的指标降权或替换。"),
            ("数据核验", "预算、支付、合同、验收、成果、服务对象反馈六类数据交叉验证。"),
            ("现场抽核", "围绕高金额、高风险、低完成率、群众反馈异常的样本开展现场核验。"),
            ("评分定级", "评分不是平均打分，要按证据强弱、影响程度、责任原因形成可解释结论。"),
            ("结果应用", "把评价结论转化为预算压减、标准调整、制度完善、项目退出或整改建议。"),
        ],
        "data_request": [
            "项目立项申报书、可研/实施方案、绩效目标申报表、预算批复文件。",
            "项目资金下达文件、预算指标表、国库支付明细、银行流水、凭证附件。",
            "合同、采购文件、验收报告、服务记录、成果清单、资产移交资料。",
            "绩效自评报告、主管部门监控记录、以前年度评价报告和整改台账。",
            "服务对象清单、满意度调查原始样本、投诉举报、第三方监测或行业统计数据。",
        ],
        "models": [
            ("目标空泛模型", "绩效目标只写加强、提升、完善，无数量、质量、时效、成本指标。", "绩效目标表 + 项目实施方案"),
            ("目标预算脱节模型", "预算安排金额与目标任务量不匹配，单价明显高于同类项目。", "预算明细 + 历史项目 + 市场价格"),
            ("支付成果错配模型", "资金支付进度快于实际产出或验收进度。", "支付明细 + 合同节点 + 验收资料"),
            ("产出真实性模型", "服务记录批量雷同、照片复用、签到集中补录、成果文件模板化。", "服务记录 + 照片元数据 + 签到表"),
            ("资金闲置模型", "资金下达后长期未支出，或拨到下级后以拨代支。", "指标下达日期 + 支付日期 + 下级账户"),
            ("满意度失真模型", "满意度样本过少、对象不匹配、问卷时间集中、分值异常满分。", "问卷原始数据 + 服务对象清单"),
            ("结果不应用模型", "连续评价低分但预算不减、项目不调、责任不追。", "评价报告 + 次年预算 + 整改台账"),
        ],
        "working_paper_fields": ["指标名称", "评价标准", "数据来源", "证据编号", "核查结果", "偏差金额/数量", "原因分析", "责任主体", "评分影响", "整改建议"],
        "interviews": [
            "绩效目标是谁设置的？是否经过论证和审核？",
            "预算金额如何测算？有没有成本标准或历史价格依据？",
            "项目产出如何验收？谁验收？验收依据是什么？",
            "满意度调查由谁做？样本怎么抽？原始问卷在哪里？",
            "以前年度评价问题是否整改？整改后预算安排有没有变化？",
        ],
        "deliverables": ["绩效评价报告", "指标体系和评分底稿", "问题清单及证据索引", "低效无效资金清单", "预算安排优化建议", "整改跟踪台账"],
        "quality_redlines": [
            "不能只按材料完整性打分，必须核验产出真实性和效益实现程度。",
            "不能把被评价单位自评结论直接搬进报告。",
            "满意度没有原始样本和抽样说明，不作为强证据。",
            "扣分项必须能回到证据，不能凭印象评价。",
        ],
    },
    "经济责任审计": {
        "source_scenes": ["经济责任审计"],
        "keywords": ["经济责任", "领导干部", "履职", "任期", "权力", "责任", "政绩观", "重大决策"],
        "source_manual": PLAYBOOK_DIR / "09-经济责任审计作战手册.md",
        "filename": "02-经济责任审计精修SOP.md",
        "position": "适用于党政机关、事业单位、国企和医院学校等单位主要领导干部任中、离任或专项经济责任审计。核心是把问题事实落到权力运行、责任边界和任期履职评价上。",
        "boss_decision": [
            "先判断审计对象是党政部门、事业单位、国企还是公共机构，不同对象责任边界不同。",
            "项目价值在于责任界定和治理建议，不只是列财务问题。",
            "必须拿到任期、分工、会议纪要、重大事项清单，否则责任链条会虚。",
            "敏感问题要坚持事实先行，结论表述稳健，避免责任扩大化。",
        ],
        "workflow": [
            ("任期画像", "确认任期起止、岗位职责、分管事项、历史遗留问题和前任后任边界。"),
            ("权力清单", "梳理重大决策、预算资金、项目建设、资产资源、采购合同、人事薪酬等权力事项。"),
            ("事项穿透", "按金额大、风险高、群众关注、反复整改四类事项做穿透核查。"),
            ("问题归因", "区分制度缺陷、执行不到位、个人决策、集体决策、历史遗留和客观原因。"),
            ("责任界定", "按直接责任、主管责任、领导责任或管理责任形成证据支撑。"),
            ("履职评价", "从依法履职、重大决策、财政财务、资产资源、廉政风险、整改成效综合评价。"),
            ("成果转化", "形成干部管理、制度完善、追责问责、整改闭环建议。"),
        ],
        "data_request": [
            "任免文件、职责分工、权责清单、领导班子分工和议事规则。",
            "党委会/党组会/办公会/董事会会议纪要、重大事项决策资料。",
            "财务报表、预算决算、科目余额、序时账、银行流水、往来款明细。",
            "项目台账、采购合同、工程资料、资产资源台账、国资监管资料。",
            "以前年度审计报告、巡视巡察反馈、整改台账、信访举报和问题线索。",
        ],
        "models": [
            ("重大决策缺程序模型", "重大项目、大额资金、资产处置未见集体决策或前置论证。", "会议纪要 + 审批资料 + 合同支付"),
            ("新官不理旧账模型", "历史遗留问题任期内继续扩大、长期不整改或整改走形式。", "历史问题台账 + 任期整改记录"),
            ("政绩工程模型", "项目目标偏离实际需求，重建设轻运营，形成闲置浪费。", "立项资料 + 运营数据 + 现场核验"),
            ("责任期间错配模型", "问题发生、扩大、暴露、整改跨多个任期，责任未分段。", "时间线 + 决策链 + 支付链"),
            ("资金资产失控模型", "往来款长期挂账、资产账实不符、出租出借不规范。", "财务账 + 资产台账 + 合同"),
            ("采购利益输送模型", "供应商集中、中标异常、合同变更频繁、验收流于形式。", "采购文件 + 中标记录 + 合同验收"),
        ],
        "working_paper_fields": ["事项名称", "发生期间", "涉及金额", "决策主体", "执行主体", "证据链", "违反依据", "影响后果", "责任类型", "责任人/责任部门", "整改建议"],
        "interviews": [
            "任期内最重要的三项决策是什么？依据和效果如何？",
            "哪些问题是历史遗留？任期内采取了什么措施？",
            "重大资金和项目是否经过集体研究？会议纪要在哪里？",
            "以前审计或巡视问题是否整改？谁负责跟踪？",
            "资产资源、采购合同、往来款中最薄弱的环节是什么？",
        ],
        "deliverables": ["经济责任审计报告", "领导干部履职评价表", "重大事项责任界定底稿", "问题时间线和责任链条图", "整改责任清单", "干部管理建议材料"],
        "quality_redlines": [
            "不能只写单位问题，必须判断与领导干部履职责任的关系。",
            "跨任期问题必须分段，不能一锅扣到现任或离任领导头上。",
            "责任表述要有证据支撑，避免用情绪化词语。",
            "评价结论必须与问题数量、金额、性质、整改情况相匹配。",
        ],
    },
    "医保资金审计": {
        "source_scenes": ["社保民生审计", "信息系统审计", "预算执行审计"],
        "keywords": ["医保", "医改", "骗保", "医院", "医疗", "基金", "诊疗", "药品", "耗材", "DRG", "DIP"],
        "source_manual": PLAYBOOK_DIR / "04-社保民生审计作战手册.md",
        "filename": "03-医保资金审计精修SOP.md",
        "position": "适用于医保基金、定点医疗机构、药品耗材采购、医保支付方式改革、医疗服务收费和骗保套保专项审计。核心是守住基金安全，并用数据穿透诊疗行为真实性。",
        "boss_decision": [
            "医保项目必须数据先行，没有结算明细、诊疗明细、药品耗材明细，审计深度会大幅下降。",
            "重点不是单纯查错账，而是查虚假诊疗、分解住院、过度医疗、串换项目、重复收费、借壳骗保。",
            "需要医疗业务专家或熟悉医保目录、诊疗规范的人参与复核。",
            "涉及个人医疗信息，必须控制数据范围、脱敏使用、限定人员和留痕管理。",
        ],
        "workflow": [
            ("数据授权", "明确医保局、医院、结算平台的数据范围、字段、期间和脱敏要求。"),
            ("字段体检", "核验参保人、机构、医生、诊断、项目、药品、金额、结算时间等关键字段完整性。"),
            ("规则筛查", "围绕重复收费、超标准收费、目录外报销、异常频次、分解住院等建立规则。"),
            ("行为画像", "按医院、科室、医生、患者、药品耗材、诊疗项目形成异常排名。"),
            ("病历回源", "对高风险样本调病历、处方、检查报告、护理记录、收费清单进行回源。"),
            ("机构核实", "与医保经办、医疗机构、临床专家核对事实，区分编码错误、管理缺陷和主观骗保。"),
            ("基金追回", "形成违规金额测算、追回建议、协议处理和监管规则优化建议。"),
        ],
        "data_request": [
            "医保结算明细：参保人脱敏ID、机构、科室、医生、诊断、结算日期、基金支付、个人支付。",
            "诊疗项目明细：项目编码、项目名称、数量、单价、金额、执行科室、执行时间。",
            "药品耗材明细：医保编码、规格、数量、单价、采购价、使用人、使用时间。",
            "住院病案首页、入出院记录、医嘱、检查检验报告、手术麻醉记录、护理记录。",
            "定点协议、医保目录、收费标准、DRG/DIP分组结果、稽核处罚和投诉举报资料。",
        ],
        "models": [
            ("重复收费模型", "同一患者同日同项目多次收费，或互斥项目同时收费。", "诊疗明细 + 收费目录"),
            ("分解住院模型", "同一患者短期内频繁出入院，诊断相近，住院间隔异常短。", "住院结算 + 病案首页"),
            ("虚假诊疗模型", "有收费无医嘱、无报告、无耗材出库或无护理记录。", "收费明细 + 医嘱 + 检查报告 + 库存"),
            ("串换项目模型", "低价项目实际执行，高价医保项目结算；目录限制条件不满足仍报销。", "项目编码 + 病历记录 + 医保目录"),
            ("过度医疗模型", "检查、用药、耗材使用频次明显高于同病种同级别机构。", "同病种横向对比 + 临床路径"),
            ("借壳骗保模型", "非医疗主体或异常机构通过定点资质套取基金。", "机构资质 + 结算记录 + 工商/人员关系"),
            ("药品耗材异常模型", "采购、库存、使用、收费数量不一致，或高值耗材集中异常。", "采购入库 + 库存出库 + 收费明细"),
        ],
        "working_paper_fields": ["疑点类型", "机构/科室/医生", "患者脱敏ID", "结算日期", "项目/药品编码", "疑点金额", "规则命中原因", "病历核验结果", "违规依据", "拟追回金额", "处理建议"],
        "interviews": [
            "医保结算审核规则有哪些？哪些规则目前靠人工审核？",
            "异常结算是否有历史稽核记录？处理结果如何？",
            "医院收费项目与医嘱、报告、耗材出库如何关联？",
            "DRG/DIP分组异常病例如何复核？",
            "定点机构协议管理和退出机制是否真正执行？",
        ],
        "deliverables": ["医保基金疑点清单", "违规金额测算表", "病历回源核验底稿", "定点机构风险排名", "基金追回和协议处理建议", "医保智能监管规则清单"],
        "quality_redlines": [
            "医保数据涉及个人隐私，交付物原则上使用脱敏ID。",
            "规则命中只是疑点，必须病历回源或专家复核后才能定性。",
            "不能只按金额排序，高频小额骗保同样要关注。",
            "临床合理性问题不能由审计人员单独下结论，必须有制度依据或专业复核。",
        ],
    },
}


def load_catalog() -> list[dict]:
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def combined(item: dict) -> str:
    return " ".join(str(item.get(k, "")) for k in ("path", "filename", "title", "scene"))


def is_generated(item: dict) -> bool:
    text = combined(item)
    return any(marker in text for marker in GENERATED_MARKERS) or item.get("scene") in {"训练清单", "标准作业包", "项目模板", "实战试点包"}


def match_items(data: list[dict], cfg: dict) -> list[dict]:
    rows = []
    for item in data:
        if is_generated(item):
            continue
        text = combined(item)
        scene_hit = item.get("scene") in cfg["source_scenes"]
        keyword_hit = any(k in text for k in cfg["keywords"])
        if scene_hit and keyword_hit:
            rows.append(item)
        elif cfg is SOPS["医保资金审计"] and keyword_hit:
            rows.append(item)
    dedup = {}
    for item in rows:
        key = item.get("path") or item.get("title")
        dedup[key] = item
    return list(dedup.values())


def rel_list(items: list[dict], limit: int = 18) -> list[str]:
    lines = []
    for item in items[:limit]:
        title = item.get("title") or item.get("filename")
        lines.append(f"- {item.get('scene')}｜{title}｜`{item.get('path')}`")
    return lines


def make_table(rows: list[tuple[str, str, str]]) -> list[str]:
    lines = ["| 模型 | 识别逻辑 | 关键证据 |", "|---|---|---|"]
    for a, b, c in rows:
        lines.append(f"| {a} | {b} | {c} |")
    return lines


def build_sop(name: str, cfg: dict, refs: list[dict]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    source_manual = cfg["source_manual"]
    lines = [
        "---",
        f'title: "{name}精修SOP"',
        "scene: 重点场景精修SOP",
        "tags: [融策, 精修SOP, 项目经理, 老板版, 审计作战]",
        "---",
        "",
        f"# {name}精修SOP",
        "",
        f"> 生成时间：{now}  ",
        f"> 参考原始资料：{len(refs)} 篇  ",
        f"> 基础手册：`{source_manual}`  ",
        "> 定位：从“知道怎么查”推进到“项目经理能直接照着启动、取数、筛疑点、写底稿、出成果”。",
        "",
        "## 1. 场景定位",
        "",
        cfg["position"],
        "",
        "## 2. 老板决策口径",
        "",
    ]
    lines.extend(f"- {x}" for x in cfg["boss_decision"])
    lines.extend(["", "## 3. 项目实施流程", ""])
    lines.extend(["| 阶段 | 动作 |", "|---|---|"])
    for stage, action in cfg["workflow"]:
        lines.append(f"| {stage} | {action} |")
    lines.extend(["", "## 4. 取数与资料清单", ""])
    lines.extend(f"- {x}" for x in cfg["data_request"])
    lines.extend(["", "## 5. 疑点模型", ""])
    lines.extend(make_table(cfg["models"]))
    lines.extend(["", "## 6. 底稿字段", ""])
    lines.append("| " + " | ".join(cfg["working_paper_fields"]) + " |")
    lines.append("|" + "---|" * len(cfg["working_paper_fields"]))
    lines.append("| " + " | ".join(["待填"] * len(cfg["working_paper_fields"])) + " |")
    lines.extend(["", "## 7. 访谈提纲", ""])
    lines.extend(f"- {x}" for x in cfg["interviews"])
    lines.extend(["", "## 8. 交付成果", ""])
    lines.extend(f"- {x}" for x in cfg["deliverables"])
    lines.extend(["", "## 9. 质量控制红线", ""])
    lines.extend(f"- {x}" for x in cfg["quality_redlines"])
    lines.extend(["", "## 10. 参考资料样例", ""])
    lines.extend(rel_list(refs))
    lines.extend(["", "## 11. 项目经理开工动作", "", "1. 用第4节资料清单发第一轮取数函。", "2. 用第5节疑点模型建立Excel/SQL筛查规则。", "3. 用第6节字段搭底稿表。", "4. 用第7节访谈提纲做第一轮访谈。", "5. 用第8节交付成果反推工作底稿是否齐全。", ""])
    return "\n".join(lines)


def build_index(outputs: list[Path], counts: dict[str, int]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# 重点场景精修SOP索引",
        "",
        f"- 生成时间：{now}",
        "- 精修范围：绩效评价、经济责任审计、医保资金审计",
        "- 使用对象：老板、项目经理、现场主审、数据分析人员",
        "",
        "## 文件清单",
        "",
        "| 场景 | 参考资料数 | 文件 |",
        "|---|---:|---|",
    ]
    for path in outputs:
        scene = path.stem.split("-", 1)[1].replace("精修SOP", "") if "-" in path.stem else path.stem
        lines.append(f"| {scene} | {counts.get(scene, 0)} | [[{path.stem}]] |")
    lines.extend(["", "## 使用建议", "", "- 接到项目先看对应SOP第2节，判断项目价值和资料风险。", "- 进场前直接复制第4节作为取数函骨架。", "- 数据分析人员按第5节疑点模型建规则。", "- 主审按第6节字段统一底稿，避免各写各的。", ""])
    return "\n".join(lines)


def main() -> None:
    data = load_catalog()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = []
    counts = {}
    for name, cfg in SOPS.items():
        refs = match_items(data, cfg)
        out = OUT_DIR / cfg["filename"]
        out.write_text(build_sop(name, cfg, refs), encoding="utf-8")
        outputs.append(out)
        counts[name] = len(refs)
    index = OUT_DIR / "00-重点场景精修SOP索引.md"
    index.write_text(build_index(outputs, counts), encoding="utf-8")
    print(f"OUT_DIR {OUT_DIR}")
    print(f"FILES {len(outputs) + 1}")
    for name in SOPS:
        print(f"{name} {counts[name]}")


if __name__ == "__main__":
    main()
