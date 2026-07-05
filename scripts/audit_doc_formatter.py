#!/usr/bin/env python3
"""
审计文档智能排版引擎 — Audit Doc Formatter

灵感来源: ResearchX 学术论文格式转换 → 审计文档领域
目标: 上传原始审计文稿 → 选择目标报告模板 → 一键生成格式化 .docx

报告类型:
  - 绩效评价报告
  - 资产清查报告
  - 财政评审报告
  - 工程结算报告
  - 专项债审计报告
  - 通用审计/咨询报告（默认）

运行:
  python scripts/audit_doc_formatter.py input.md --type 绩效评价
  python scripts/audit_doc_formatter.py input.md --type 资产清查 -o output.docx
  python scripts/audit_doc_formatter.py --list-types
"""
from __future__ import annotations

import sys
import re
import argparse
from pathlib import Path
from dataclasses import dataclass, field

# 加载 ai-word-skill core
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ai-word-skill"))
from core import (
    open_template, save_doc,
    rewrite_paragraph, replace_placeholders, fill_table_cell,
)


# ============================================================
#  模板注册表
# ============================================================

@dataclass
class ReportTemplate:
    """报告模板定义"""
    name: str                    # 模板名称
    description: str             # 用途说明
    template_file: str           # .docx 母版路径（相对于 workspace）
    sections: dict[str, str]     # 章节名 → 占位符关键词
    cover_fields: list[str]      # 封面占位符列表

ROOT = Path(__file__).resolve().parent.parent

TEMPLATES: dict[str, ReportTemplate] = {
    "通用审计": ReportTemplate(
        name="通用审计/咨询报告",
        description="适用于绩效评价、资产清查、专项检查等（默认模板）",
        template_file="审计报告标准模板.docx",
        cover_fields=[
            "委托单位", "被审计/咨询单位", "项目类型",
            "报告日期", "编制单位", "报告标题", "报告副标题",
        ],
        sections={
            "核心发现":      "核心发现摘要",
            "项目概述":      "一、项目概述",
            "项目背景":      "1.1 项目背景",
            "审计目标":      "1.2 审计/咨询目标",
            "范围方法":      "1.3 审计/咨询范围与方法",
            "总体情况":      "二、项目总体情况",
            "预算执行":      "3.1 预算执行方面",
            "资金管理":      "3.2 资金管理方面",
            "项目管理":      "3.3 项目管理方面",
            "内部控制":      "3.4 内部控制方面",
            "问题汇总":      "四、问题发现汇总",
            "改进建议":      "五、改进建议",
        },
    ),
    "绩效评价": ReportTemplate(
        name="绩效评价报告",
        description="适用于预算绩效评价、专项资金绩效评价等",
        template_file="审计报告标准模板.docx",
        cover_fields=[
            "委托单位", "被审计/咨询单位", "项目类型",
            "报告日期", "编制单位", "报告标题", "报告副标题",
        ],
        sections={
            "核心发现":      "核心发现摘要",
            "项目概述":      "一、项目概述",
            "项目背景":      "1.1 项目背景",
            "绩效目标":      "1.2 审计/咨询目标",
            "评价方法":      "1.3 审计/咨询范围与方法",
            "总体情况":      "二、项目总体情况",
            "决策指标":      "3.1 预算执行方面",
            "过程指标":      "3.2 资金管理方面",
            "产出指标":      "3.3 项目管理方面",
            "效益指标":      "3.4 内部控制方面",
            "问题汇总":      "四、问题发现汇总",
            "改进建议":      "五、改进建议",
        },
    ),
    "资产清查": ReportTemplate(
        name="资产清查报告",
        description="适用于行政事业单位国有资产清查",
        template_file="审计报告标准模板.docx",
        cover_fields=[
            "委托单位", "被审计/咨询单位", "项目类型",
            "报告日期", "编制单位", "报告标题", "报告副标题",
        ],
        sections={
            "核心发现":      "核心发现摘要",
            "项目概述":      "一、项目概述",
            "清查背景":      "1.1 项目背景",
            "清查目标":      "1.2 审计/咨询目标",
            "清查方法":      "1.3 审计/咨询范围与方法",
            "总体情况":      "二、项目总体情况",
            "账实核对":      "3.1 预算执行方面",
            "盘盈盘亏":      "3.2 资金管理方面",
            "闲置资产":      "3.3 项目管理方面",
            "处置规范":      "3.4 内部控制方面",
            "问题汇总":      "四、问题发现汇总",
            "改进建议":      "五、改进建议",
        },
    ),
    "工程结算": ReportTemplate(
        name="工程结算报告",
        description="适用于工程竣工结算审核",
        template_file="审计报告标准模板.docx",
        cover_fields=[
            "委托单位", "被审计/咨询单位", "项目类型",
            "报告日期", "编制单位", "报告标题", "报告副标题",
        ],
        sections={
            "核心发现":      "核心发现摘要",
            "项目概述":      "一、项目概述",
            "工程概况":      "1.1 项目背景",
            "审核目标":      "1.2 审计/咨询目标",
            "审核方法":      "1.3 审计/咨询范围与方法",
            "总体情况":      "二、项目总体情况",
            "量价审核":      "3.1 预算执行方面",
            "变更签证":      "3.2 资金管理方面",
            "合同履约":      "3.3 项目管理方面",
            "质量安全":      "3.4 内部控制方面",
            "问题汇总":      "四、问题发现汇总",
            "改进建议":      "五、改进建议",
        },
    ),
}


# ============================================================
#  内容解析器
# ============================================================

@dataclass
class ParsedSection:
    title: str
    content: str
    level: int  # 1 = 一级标题, 2 = 二级

class ContentParser:
    """从 Markdown 或纯文本中解析审计报告结构化内容"""

    # 一级标题匹配模式
    H1_PATTERNS = [
        re.compile(r'^#\s+(.+)$', re.MULTILINE),
        re.compile(r'^(.+?)[  ]*\n[=]{3,}', re.MULTILINE),
    ]
    # 二级标题匹配模式
    H2_PATTERNS = [
        re.compile(r'^##\s+(.+)$', re.MULTILINE),
        re.compile(r'^(.+?)[  ]*\n[-]{3,}', re.MULTILINE),
    ]
    # 中文数字标题: "一、xxx" "二、xxx"
    CN_H1 = re.compile(r'^([一二三四五六七八九十]+)[、，。．.．\s]+(.+)$')
    # 子标题: "1.1 xxx" "（一）xxx" "(一)xxx"
    CN_H2 = re.compile(r'^[(（][一二三四五六七八九十]+[)）]\s*(.+)$')
    NUM_H2 = re.compile(r'^(\d+)[\.\、]\s*(\d*)\s*(.+)$')

    @staticmethod
    def parse(text: str) -> list[ParsedSection]:
        """解析文本为结构化段落列表"""
        lines = text.strip().split('\n')
        sections = []
        current_title = ""
        current_lines = []
        current_level = 1
        in_core_findings = False

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if current_lines:
                    current_lines.append('')
                continue

            # 检测一级标题
            h1 = ContentParser._match_h1(stripped)
            if h1:
                ContentParser._flush(sections, current_title, current_lines)
                current_title = h1
                current_lines = []
                current_level = 1
                continue

            # 检测二级标题
            h2 = ContentParser._match_h2(stripped)
            if h2:
                ContentParser._flush(sections, current_title, current_lines)
                current_title = h2
                current_lines = []
                current_level = 2
                continue

            current_lines.append(stripped)

        ContentParser._flush(sections, current_title, current_lines)
        return sections

    @staticmethod
    def _match_h1(line: str) -> str | None:
        if m := re.match(r'^#\s+(.+?)$', line):
            return m.group(1).strip()
        if m := ContentParser.CN_H1.match(line):
            return line.strip()
        return None

    @staticmethod
    def _match_h2(line: str) -> str | None:
        if m := re.match(r'^##\s+(.+?)$', line):
            return m.group(1).strip()
        if m := ContentParser.CN_H2.match(line):
            return line.strip()
        if m := ContentParser.NUM_H2.match(line):
            return line.strip()
        return None

    @staticmethod
    def _flush(sections, title, lines):
        if lines:
            content = '\n'.join(lines).strip()
            if content:
                # 推断层级
                level = 1 if title and re.match(ContentParser.CN_H1, title) else 2
                sections.append(ParsedSection(title=title or "", content=content, level=level))


# ============================================================
#  段落匹配引擎
# ============================================================

class SectionMatcher:
    """将解析后的段落匹配到模板占位符"""

    # 关键词权重表：匹配 section key 的各种说法
    KEYWORD_MAP = {
        "核心发现":  ["核心发现", "主要发现", "审计发现", "重要发现", "结论"],
        "项目概述":  ["项目概述", "概述", "基本情况", "项目概况"],
        "项目背景":  ["项目背景", "背景", "立项背景", "项目由来"],
        "审计目标":  ["审计目标", "审计目的", "评价目标", "审核目标",
                    "绩效目标", "清查目标", "工作目标"],
        "范围方法":  ["审计范围", "审计方法", "评价方法", "审核方法",
                    "清查方法", "工作方法", "范围与方法", "范围和方式"],
        "总体情况":  ["总体情况", "项目总体情况", "总体评价", "整体情况",
                    "基本评价", "综合评价"],
        "预算执行":  ["预算执行", "预算管理", "资金拨付", "决策",
                    "决策指标", "账实核对", "量价审核"],
        "资金管理":  ["资金管理", "专项资金", "资金使用", "经费管理",
                    "过程", "过程指标", "盘盈盘亏", "变更签证"],
        "项目管理":  ["项目管理", "项目管理方面", "产出", "产出指标",
                    "实施管理", "招投标", "采购管理", "闲置资产", "合同履约"],
        "内部控制":  ["内部控制", "内控制度", "制度建设", "效益",
                    "效益指标", "处置规范", "质量安全"],
        "问题汇总":  ["问题汇总", "问题发现", "问题清单", "发现的问题",
                    "存在问题", "主要问题"],
        "改进建议":  ["改进建议", "建议", "整改建议", "审计建议",
                    "管理建议", "对策建议"],
    }

    @staticmethod
    def match(sections: list[ParsedSection], template: ReportTemplate) -> dict[str, str]:
        """匹配段落到模板section，返回 {section_key: content}"""
        result = {}
        used_sections = set()

        for sec in sections:
            matched_key = SectionMatcher._find_best_match(sec.title, template)
            if matched_key and matched_key not in used_sections:
                result[matched_key] = sec.content
                used_sections.add(matched_key)
            elif matched_key:
                # 同名section拼接
                result[matched_key] += '\n\n' + sec.content

        return result

    @staticmethod
    def _find_best_match(title: str, template: ReportTemplate) -> str | None:
        """根据标题文字找到最匹配的模板 section key"""
        if not title:
            return None

        best_key = None
        best_score = 0
        title_stripped = title.lstrip('#').strip()

        # 直接遍历模板的 section keys
        for section_key in template.sections:
            # 1) 精确匹配：section key 出现在标题中
            if section_key in title_stripped:
                score = len(section_key) / max(len(title_stripped), 1)
                if score > best_score:
                    best_score = score
                    best_key = section_key

            # 2) 通过关键词表匹配
            keywords = SectionMatcher.KEYWORD_MAP.get(section_key, [section_key])
            for kw in keywords:
                if kw in title_stripped and kw != section_key:
                    score = len(kw) / max(len(title_stripped), 1)
                    if score > best_score:
                        best_score = score
                        best_key = section_key

        return best_key


# ============================================================
#  排版引擎
# ============================================================

class FormatterEngine:
    """将匹配结果写入模板 docx"""

    def __init__(self, template: ReportTemplate):
        self.template = template
        template_path = ROOT / template.template_file
        if not template_path.exists():
            raise FileNotFoundError(f"模板文件不存在: {template_path}")
        self.template_path = template_path

    def format(self, content_mapping: dict[str, str],
               cover_data: dict[str, str] | None = None,
               output_path: str | Path | None = None) -> Path:
        """执行排版，返回输出文件路径"""
        if output_path is None:
            output_path = ROOT / "output" / "formatted_report.docx"
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Step 1: 母版副本
        doc = open_template(self.template_path, output_path)

        # Step 2: 项目类型标记
        project_type = {
            "绩效评价": "▣ 绩效评价  □ 资产清查  □ 专项债审计  □ 工程结算",
            "资产清查": "□ 绩效评价  ▣ 资产清查  □ 专项债审计  □ 工程结算",
            "工程结算": "□ 绩效评价  □ 资产清查  □ 专项债审计  ▣ 工程结算",
        }
        if self.template.name in project_type and doc.tables and doc.tables[0].rows:
            try:
                cell = doc.tables[0].rows[2].cells[1]
                if cell.paragraphs:
                    from core import rewrite_paragraph
                    rewrite_paragraph(cell.paragraphs[0], project_type[self.template.name])
            except (IndexError, AttributeError):
                pass

        # Step 3: 填充封面信息
        if cover_data:
            from core import replace_all
            for key, val in cover_data.items():
                replace_all(doc, f"[请输入{key}]", val)

        # Step 4: 按模板 section 映射写入正文
        body_written = 0
        for content_key, placeholder in self.template.sections.items():
            if content_key not in content_mapping:
                continue
            content = content_mapping[content_key]

            # 在模板中查找包含此占位符的段落
            found = False
            for p in doc.paragraphs:
                if placeholder in p.text:
                    from core import rewrite_paragraph
                    # 保留标题行，在下一段写内容
                    # 找到标题后的正文段落
                    next_p = FormatterEngine._find_next_body_paragraph(doc, p)
                    if next_p and not found:
                        rewrite_paragraph(next_p, content)
                        body_written += 1
                        found = True
                        break

        print(f"  [排版] 已填充 {body_written} 个章节")

        # Step 5: 保存
        save_doc(doc, output_path)
        return output_path

    @staticmethod
    def _find_next_body_paragraph(doc, ref_p):
        """找到参考段落之后的下一个正文段落"""
        found_ref = False
        for p in doc.paragraphs:
            if p._element is ref_p._element:
                found_ref = True
                continue
            if found_ref and p.text.strip():
                return p
        return None


# ============================================================
#  CLI 入口
# ============================================================

def create_sample_input(report_type: str) -> str:
    """为指定的报告类型生成示例 Markdown 输入文件"""
    samples = {
        "绩效评价": """# 核心发现摘要
► XX市养老服务体系建设专项资金绩效评价总体得分为82.5分，等级为"良"
► 资金拨付及时率达95%，但项目产出质量存在短板
► 建议优化资金分配机制，强化过程监控

# 一、项目概述
根据XX市财政局《关于开展2025年度专项资金绩效评价工作的通知》（X财绩〔2026〕1号），四川融策会计师事务所受XX市财政局委托，对XX市2025年度养老服务体系建设专项资金开展绩效评价。本次评价覆盖市本级及5个区县，涉及专项资金总额3,200万元。评价工作自2026年2月10日启动，历时45天，投入8人次。

# 1.1 项目背景
XX市2025年度养老服务体系建设专项资金主要用于社区养老服务中心建设、居家养老服务补贴、养老机构运营补助三大方向。截至2025年12月31日，专项资金已拨付3,050万元，拨付率95.3%，实际支出2,780万元，支出率91.1%。

# 绩效目标
本次绩效评价的主要目标：① 评价专项资金使用的经济性、效率性和效果性；② 检查资金管理制度的健全性和执行有效性；③ 评估养老服务项目的实际产出和群众满意度；④ 为下年度预算安排和政策优化提供参考依据。

# 评价方法
本次评价采用"资料审查+实地走访+问卷调查+数据分析"相结合的方式。覆盖全市6个区县、24个社区养老服务中心、12家养老机构。发放满意度问卷500份，回收有效问卷468份。采用层次分析法（AHP）构建评价指标体系，共设4个一级指标、12个二级指标、36个三级指标。

# 二、项目总体情况
评价结果表明，XX市养老服务体系建设专项资金总体使用规范，项目推进有序。综合得分82.5分（满分100分），等级为"良"。其中决策指标得分18.2/20，过程指标得分16.5/20，产出指标得分22.8/30，效益指标得分25.0/30。

# 决策指标
项目立项依据充分，绩效目标设置较为合理。但存在以下问题：① 部分区县资金分配未充分考虑老年人口分布的实际需求，资源配置与需求存在错位；② 个别项目绩效指标设置过于笼统，缺乏可量化、可考核的具体标准。

# 过程指标
资金管理总体规范，但存在：① XX区民政局将养老专项资金85万元用于单位日常公用经费，不符合专款专用规定；② 3个社区养老服务中心建设项目未按合同约定及时拨付工程款，拖欠施工单位款项合计120万元。

# 产出指标
项目产出基本完成计划目标，但存在：① 2个社区养老服务中心建设进度滞后，较计划延期6个月以上，截至评价日尚未完成竣工验收；② 部分居家养老服务记录不完整，抽查发现约15%的服务工单缺少服务对象签字确认。

# 效益指标
养老服务满意度调查得分86.3分（百分制），群众总体认可度较高。但存在：① 农村地区养老服务覆盖不足，部分偏远乡镇老年人未能享受到居家养老服务；② 养老机构床位利用率仅62%，存在资源闲置问题；③ 医养结合服务推进缓慢，仅3家养老机构具备基本医疗服务能力。

# 四、问题发现汇总
本次绩效评价共发现问题15项，其中高风险问题5项（涉及资金占用、项目延期等），中风险问题6项，低风险问题4项。高风险问题涉及违规金额205万元，已督促相关单位限期整改。

# 五、改进建议
1. 优化资金分配机制。建议建立"因素法+项目法"相结合的资金分配模型，将老年人口数量、老龄化程度、经济发展水平等因素纳入分配权重。
2. 强化过程监控。建立专项资金使用"红黄绿"预警机制，对执行率偏低或偏离绩效目标的项目及时预警。
3. 完善服务监管。推广居家养老服务信息化管理平台，实现服务过程全程留痕、实时监控。
4. 推进医养结合。加强民政与卫健部门协作，推动养老机构与基层医疗机构签约合作，提高医养结合覆盖率。
""",
        "资产清查": """# 核心发现摘要
► XX局账面资产总额12,560万元，清查核实为11,830万元，盘亏730万元
► 闲置资产价值合计865万元，占资产总额的7.3%
► 建议建立资产全生命周期管理体系，盘活闲置资产

# 一、项目概述
根据XX市财政局《关于开展行政事业单位国有资产清查工作的通知》（X财资〔2026〕3号），四川融策会计师事务所受XX局委托，对XX局及其下属5个单位截至2025年12月31日的国有资产进行全面清查。清查工作自2026年1月15日至3月10日，累计投入12人次。

# 清查背景
XX局账面资产总额12,560万元，其中固定资产11,200万元，无形资产860万元，在建工程500万元。资产主要分布在局机关及下属5个单位，类别涵盖房屋建筑物、通用设备、专用设备、家具用具、无形资产等。

# 清查目标
① 核实资产账实相符情况，查明盘盈盘亏及原因；② 评估资产使用效益，识别闲置、低效资产；③ 检查资产处置、出租出借等管理规范性；④ 完善资产管理制度和流程。

# 清查方法
采用"全面盘点+重点抽查+资料核查"相结合的方式。对房屋建筑物、车辆等重大资产进行全面盘点，对通用设备按30%比例抽查，对家具用具按15%比例抽查。累计盘点资产3,820件（套），抽查1,146件（套）。

# 二、项目总体情况
经清查，XX局及下属单位实际拥有资产11,830万元，与账面12,560万元相比盘亏730万元（5.8%），主要原因为已报废未销账资产和盘亏资产。整体看，资产管理基本规范，但存在账实不符、闲置浪费、处置不规范等问题。

# 账实核对
账实差异主要集中在：① 已报废未销账资产520万元（通用设备310万元、家具用具210万元），涉及资产186件；② 盘亏资产210万元（部分电子设备去向不明），涉及资产42件。差异资产均已逐项登记并查明原因。

# 盘盈盘亏
盘盈资产0元，盘亏资产730万元。盘亏的主要原因：① 部分老旧电子设备在机构改革过程中移交手续不完善导致去向不明；② 部分已处置资产未及时办理资产核销手续；③ 个别直属单位资产管理制度不健全，资产台账更新不及时。

# 闲置资产
发现闲置资产865万元，包括：① XX局旧址办公楼2,400平方米，账面价值620万元，自2024年搬迁后闲置至今；② 闲置通用设备（打印机、复印机等）38台，价值45万元；③ 闲置专用设备（检测仪器等）12台，价值200万元。以上资产长期闲置，未提出明确的盘活利用方案。

# 处置规范
发现资产处置不规范问题3项：① 2024年5月处置报废车辆2辆，未按规定报财政部门审批；② 2024年11月报废通用设备一批（原值85万元），未进行残值评估直接报废；③ 下属某单位将闲置办公室出借给外部单位使用，未签订使用协议也未收取使用费。

# 四、问题发现汇总
本次清查共发现问题9项，按风险等级分类：高风险3项（涉及闲置资产865万元、违规处置115万元），中风险4项，低风险2项。

# 五、改进建议
1. 全面清理核销。对已报废未销账的520万元资产，按规定程序尽快办理核销手续，确保账实相符。
2. 盘活闲置资产。对XX局旧址办公楼提出置换、调剂或公开招租等盘活方案；对闲置设备提出调剂使用或公开处置建议。
3. 规范处置程序。严格按《行政事业性国有资产管理条例》规定执行资产处置审批程序，杜绝先处置后补手续。
4. 加强制度建设。建立资产全生命周期管理制度，将资产购置、使用、维护、处置全过程纳入信息化管理系统。
""",
    }

    if report_type not in samples:
        report_type = "绩效评价"
    return samples[report_type]


def main():
    parser = argparse.ArgumentParser(
        description="审计文档智能排版引擎 — 原始文稿 → 标准报告 .docx",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python audit_doc_formatter.py report.md --type 绩效评价
  python audit_doc_formatter.py report.md --type 资产清查 -o output/清查报告.docx
  python audit_doc_formatter.py --sample 绩效评价 --type 绩效评价
  python audit_doc_formatter.py --list-types
"""
    )
    parser.add_argument("input", nargs="?", help="输入文件路径（Markdown 或纯文本）")
    parser.add_argument("--type", dest="report_type", default="通用审计",
                        choices=list(TEMPLATES.keys()),
                        help="报告类型 (默认: 通用审计)")
    parser.add_argument("-o", "--output", help="输出 .docx 路径 (默认: output/formatted_report.docx)")
    parser.add_argument("--sample", action="store_true",
                        help="使用内置示例数据生成报告")
    parser.add_argument("--list-types", action="store_true",
                        help="列出所有支持的模板类型")

    args = parser.parse_args()

    if args.list_types:
        print("支持的审计报告模板类型:\n")
        for key, tmpl in TEMPLATES.items():
            print(f"  {key:8s} — {tmpl.description}")
        print('\n提示: 所有类型共用《审计报告标准模板.docx》母版，通过章节映射区分内容结构')
        return

    # 选择模板
    template = TEMPLATES[args.report_type]
    print(f"[*] 模板: {template.name}")
    print(f"[*] 母版: {template.template_file}")

    # 获取输入内容
    if args.sample or not args.input:
        print(f"[*] 使用内置示例数据 [{args.report_type}]")
        raw_text = create_sample_input(args.report_type)
    else:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"[ERROR] 文件不存在: {args.input}")
            sys.exit(1)
        raw_text = input_path.read_text(encoding="utf-8")
        print(f"[*] 读取输入: {args.input} ({len(raw_text)} 字符)")

    # 解析
    sections = ContentParser.parse(raw_text)
    print(f"[*] 解析到 {len(sections)} 个段落")

    # 匹配
    mapping = SectionMatcher.match(sections, template)
    print(f"[*] 匹配到 {len(mapping)} 个章节: {list(mapping.keys())}")

    # 排版
    engine = FormatterEngine(template)
    output = engine.format(mapping, output_path=args.output)
    print(f"\n[OK] 排版完成: {output}")
    print(f"     用 Word 打开查看 — 保留母版仿宋字体和1.5倍行距")


if __name__ == "__main__":
    main()
