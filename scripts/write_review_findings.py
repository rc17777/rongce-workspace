# -*- coding: utf-8 -*-
"""将复核发现标准化写入项目"""
import json, os
from datetime import datetime, timezone, timedelta
CST = timezone(timedelta(hours=8))
now = datetime.now(CST).isoformat()

findings = [
  {
    "finding_id": "F-2026-001", "agent": "review_sentinel", "timestamp": now,
    "type": "内控漏洞", "severity": "中",
    "summary": "采购验收制度不完善：缺少全过程档案清单，未涵盖招标文件、评审记录、异议处理、预算审批、验收报告等关键节点材料",
    "entities": ["四川天府新区新兴卫生院"], "amount": None,
    "evidence": ["2025年6号《采购管理实施细则》第二条第五款"],
    "confidence": 85, "law_refs": ["政府采购法第42条"], "related_findings": [], "status": "已确认"
  },
  {
    "finding_id": "F-2026-002", "agent": "review_sentinel", "timestamp": now,
    "type": "内控漏洞", "severity": "高",
    "summary": "采购验收制度缺少不合格品处置流程：未建立验收不合格的上报、退货、换货、索赔机制",
    "entities": ["四川天府新区新兴卫生院"], "amount": None,
    "evidence": ["2025年6号《采购管理实施细则》第四条验收管理"],
    "confidence": 90, "law_refs": ["政府采购法实施条例"], "related_findings": ["F-2026-001"], "status": "已确认"
  },
  {
    "finding_id": "F-2026-003", "agent": "review_sentinel", "timestamp": now,
    "type": "程序违规", "severity": "中",
    "summary": "党委会决策规范缺少量化标准：未要求正式会议记录归档，处罚条款无法有效执行",
    "entities": ["四川天府新区新兴卫生院"], "amount": None,
    "evidence": ["《内部控制规范制度汇编》第一章第二条第十一条"],
    "confidence": 80, "law_refs": [], "related_findings": [], "status": "已确认"
  },
  {
    "finding_id": "F-2026-004", "agent": "review_sentinel", "timestamp": now,
    "type": "财务异常", "severity": "中",
    "summary": "跨期核算：2024年12月已入库药品费3,232.80元延至2025年2月记账，违反权责发生制",
    "entities": ["四川天府新区新兴卫生院", "四川本草堂医药有限公司"], "amount": 3232.80,
    "evidence": ["2025年2月40-48号凭证", "2024年12月入库单"],
    "confidence": 95, "law_refs": ["会计准则-基本准则", "事业单位会计准则第13条"], "related_findings": [], "status": "已确认"
  },
  {
    "finding_id": "F-2026-005", "agent": "review_sentinel", "timestamp": now,
    "type": "财务异常", "severity": "中",
    "summary": "未按准则计提坏账准备：长期挂账应收款未进行减值测试和坏账计提",
    "entities": ["四川天府新区新兴卫生院"], "amount": None,
    "evidence": ["2025年末应收款项明细", "科目余额表"],
    "confidence": 90, "law_refs": ["政府会计制度-会计科目说明"], "related_findings": [], "status": "已确认"
  },
  {
    "finding_id": "F-2026-006", "agent": "review_sentinel", "timestamp": now,
    "type": "财务异常", "severity": "低",
    "summary": "固定资产折旧不规范：2025年1-11月折旧在11月一次性计提，未按月计提",
    "entities": ["四川天府新区新兴卫生院"], "amount": None,
    "evidence": ["2025年11月86号凭证", "固定资产折旧明细表"],
    "confidence": 95, "law_refs": ["会计准则第3号-固定资产第21条"], "related_findings": [], "status": "已确认"
  },
  {
    "finding_id": "F-2026-007", "agent": "review_sentinel", "timestamp": now,
    "type": "合同违规", "severity": "中",
    "summary": "未按合同约定付款：IT系统维护服务按半年支付9,000元，而非合同约定按季度支付4,500元",
    "entities": ["四川省万利基础设施工程有限公司", "四川天府新区新兴卫生院"], "amount": 9000.00,
    "evidence": ["IT系统维护服务合同(2024.10.9)", "2025年8月12号凭证"],
    "confidence": 90, "law_refs": ["民法典第470条"], "related_findings": [], "status": "已确认"
  },
  {
    "finding_id": "F-2026-008", "agent": "review_sentinel", "timestamp": now,
    "type": "程序违规", "severity": "低",
    "summary": "发票开具不合规：2张增值税发票未填写纳税人识别号，涉及金额1,751.40元",
    "entities": ["四川天府新区新兴卫生院"], "amount": 1751.40,
    "evidence": ["2025年1月5号、2月50号凭证", "发票号57639033、57639043"],
    "confidence": 95, "law_refs": ["会计法第13条", "发票管理办法"], "related_findings": [], "status": "已确认"
  },
  {
    "finding_id": "F-2026-009", "agent": "review_sentinel", "timestamp": now,
    "type": "内控漏洞", "severity": "高",
    "summary": "采购需求界定不规范：办公用品采购合同预算10万元/年，未明确品名、型号、规格，存在虚报风险",
    "entities": ["四川天府新区新兴卫生院", "成都未名信息技术有限公司"], "amount": 100000.00,
    "evidence": ["2024年办公用品配送服务合同", "2024年4月25日签订"],
    "confidence": 85, "law_refs": ["政府采购需求管理办法"], "related_findings": ["F-2026-001"], "status": "已确认"
  },
  {
    "finding_id": "F-2026-010", "agent": "review_sentinel", "timestamp": now,
    "type": "资产流失", "severity": "中",
    "summary": "固定资产管理混乱：标签贴于包装盒/已报废未处置/同一型号分散存放/盘亏原因不明",
    "entities": ["四川天府新区新兴卫生院"], "amount": None,
    "evidence": ["2026年5月6日盘点记录", "固定资产卡片", "资产标签照片"],
    "confidence": 90, "law_refs": ["卫生院内控制度第三章第22-23条"], "related_findings": [], "status": "已确认"
  },
  {
    "finding_id": "F-2026-011", "agent": "review_sentinel", "timestamp": now,
    "type": "合同违规", "severity": "低",
    "summary": "合同要素缺失：公卫服务合同(30万元/年)未约定发票追踪和付款时限",
    "entities": ["四川天府新区新兴卫生院", "成都双流华府科技有限公司"], "amount": 300000.00,
    "evidence": ["2024年公卫服务采购项目合同(2024.7.8)"],
    "confidence": 80, "law_refs": ["民法典第470条"], "related_findings": ["F-2026-007"], "status": "已确认"
  },
  {
    "finding_id": "F-2026-012", "agent": "review_sentinel", "timestamp": now,
    "type": "程序违规", "severity": "低",
    "summary": "现金存款制度执行不到位：收费员每周集中交款一次，未执行每日交存规定",
    "entities": ["四川天府新区新兴卫生院"], "amount": None,
    "evidence": ["收费窗口交款记录", "《支出管理制度》第九条"],
    "confidence": 85, "law_refs": ["卫生院支出管理制度第九条"], "related_findings": [], "status": "已确认"
  }
]

proj_dir = r"D:\openclaw-workspace\audit-blackboard\projects\新兴卫生院2025收支审计"
os.makedirs(os.path.join(proj_dir, "findings"), exist_ok=True)

# Write
with open(os.path.join(proj_dir, "findings", "review_sentinel.json"), "w", encoding="utf-8") as f:
    json.dump(findings, f, ensure_ascii=False, indent=2)
with open(os.path.join(proj_dir, "findings", "_all_findings.json"), "w", encoding="utf-8") as f:
    json.dump(findings, f, ensure_ascii=False, indent=2)

# Update status
sf = os.path.join(proj_dir, "status.json")
status = json.load(open(sf, encoding="utf-8"))
status["phase"] = "agent_done"
status["findings_count"] = len(findings)
status["logs"].append("[{0}] review_sentinel产出{1}条发现".format(datetime.now(CST).strftime("%H:%M"), len(findings)))
json.dump(status, open(sf, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

print("OK: {0}条发现已写入".format(len(findings)))
# 打印摘要
by_sev = {"高":0, "中":0, "低":0}
by_type = {}
for f in findings:
    by_sev[f["severity"]] = by_sev.get(f["severity"], 0) + 1
    by_type[f["type"]] = by_type.get(f["type"], 0) + 1
print("严重度: 高{0}/中{1}/低{2}".format(by_sev["高"], by_sev["中"], by_sev["低"]))
print("类型: {0}".format(dict(by_type)))
