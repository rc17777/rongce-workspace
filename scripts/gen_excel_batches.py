#!/usr/bin/env python3
"""Generate batch JSONs for 审盾 v2.0 Excel workbook."""
import json, os

xlsx = r"C:\Users\scrccpa\Desktop\审盾-三位一体方案-v2.0.xlsx"
outdir = os.path.dirname(os.path.abspath(__file__))

def S(path, value, **props):
    return {"op": "set", "path": path, "props": {"value": value, **props}}

def M(path):
    return {"op": "set", "path": path, "props": {"merge": True}}

def H(path, value):
    return S(path, value, bold=True, fill="0A1F3F", font_color="FFFFFF", font_size=11)

# ======== 总览 ========
overview = [
    S("/总览/A1", "融策·审盾 三位一体AI审计中台建设方案 v2.0", bold=True, font_size=16, font_color="0A1F3F"),
    M("/总览/A1:H1"),
    S("/总览/A2", "修订：2026-07-21 | 四模型联合评审+苏格拉底追问后修订 | 负责人：融策平头哥", font_size=10, font_color="666666"),
    M("/总览/A2:H2"),
    S("/总览/A4", "▎核心定位", bold=True, font_size=12, font_color="1A5C6E"),
    S("/总览/A5", "融策·审盾 —— 用AI武装的政府财政资金安全与绩效智能守门人", font_size=11),
    S("/总览/A6", "一期唯一用户：审计项目经理（报告复核） | 实战场景：若尔盖审计局 校园餐+医保资金审计", font_size=10),
    S("/总览/A8", "▎v1.0 → v2.0 关键变更（四模型联合评审驱动）", bold=True, font_size=12, font_color="1A5C6E"),
]
# Headers
headers = ["修正点", "v1.0", "v2.0", "触发来源"]
for i, h in enumerate(headers):
    overview.append(S(f"/总览/{chr(65+i)}9", h, bold=True, fill="0A1F3F", font_color="FFFFFF", font_size=11))

changes = [
    ("目标用户", "模糊（三类人）", "单一用户：审计项目经理", "苏格拉底Q3"),
    ("技术路线", "微调13B-32B模型", "RAG+Agentic Workflow为主", "Gemini+GPT-5.5力挺"),
    ("硬件路线", "RTX 5090×1(Day1)", "现有工作站+API，GPU推迟至Day90", "Luna+GPT-5.5"),
    ("验证数据", "融策内部报告", "10份不同客户/年份/格式", "苏格拉底Q9"),
    ("验证节奏", "30天出盲测", "30天规则引擎+60天语义复核", "Claude+GPT-5.5+Luna"),
    ("量化标准", "无", "检出率≥80% 误报率≤20% 采纳率≥40%", "Claude+GPT-5.5"),
    ("止损机制", "无", "Day180不达标→不进入Phase2", "Claude+GPT-5.5"),
    ("SaaS化", "多租户SaaS", "三级路径：溢价→联合体→私有化部署", "Claude+GPT-5.5+Luna"),
    ("数据飞轮", "Phase2才建标注平台", "Day1启动Label Studio", "四模型全票"),
    ("团队", "Phase1即招1人AI工程师", "Day1-90平头哥亲自+OpenClaw", "苏格拉底Q5"),
    ("业务线扩展", "Phase2做5条线", "Phase2深度打磨3条线", "Luna+GPT-5.5"),
    ("三年总投入", "¥720万", "¥325-431万（↓40-55%）", "Gemini+Claude"),
]
for i, (a, b, c, d) in enumerate(changes):
    row = 10 + i
    overview.append(S(f"/总览/A{row}", a, font_size=10))
    overview.append(S(f"/总览/B{row}", b, font_size=10, font_color="888888"))
    overview.append(S(f"/总览/C{row}", c, font_size=10, font_color="1A5C6E"))
    overview.append(S(f"/总览/D{row}", d, font_size=10))

# Budget summary
br = len(changes) + 11
overview.append(S(f"/总览/A{br}", "▎三年投入速查", bold=True, font_size=12, font_color="1A5C6E"))
br += 1
for i, h in enumerate(["阶段", "时间", "一次性投入", "年运营成本", "累计投入"]):
    overview.append(S(f"/总览/{chr(65+i)}{br}", h, bold=True, fill="0A1F3F", font_color="FFFFFF", font_size=11))
budgets = [
    ("第一阶段·验证闭环", "月1-6", "¥0-3万", "¥15-18万", "¥15-21万"),
    ("第二阶段·规模化打磨", "月7-18", "¥15-25万", "¥105-115万", "¥120-140万"),
    ("第三阶段·行业壁垒", "月19-36", "¥40-75万", "¥150-195万", "¥190-270万"),
    ("三年合计", "36个月", "¥55-103万", "¥270-328万", "¥325-431万"),
]
for i, (a, b, c, d, e) in enumerate(budgets):
    row = br + 1 + i
    is_total = i == 3
    overview.append(S(f"/总览/A{row}", a, bold=is_total, font_size=10))
    overview.append(S(f"/总览/B{row}", b, font_size=10))
    overview.append(S(f"/总览/C{row}", c, font_size=10))
    overview.append(S(f"/总览/D{row}", d, font_size=10))
    overview.append(S(f"/总览/E{row}", e, bold=is_total, font_color="C5955C" if is_total else None, font_size=10))

# Col widths
for col, w in [("A",20),("B",20),("C",35),("D",25),("E",15)]:
    overview.append({"op": "set", "path": f"/总览/{col}1:{col}1", "props": {"width": w}})

with open(os.path.join(outdir, "_batch_overview.json"), "w", encoding="utf-8") as f:
    json.dump(overview, f, ensure_ascii=False, indent=2)
print(f"Overview: {len(overview)} ops written.")

# ======== 一阶段 ========
p1 = [
    S("/一阶段-验证闭环/A1", "第一阶段：验证闭环（2026年7月-12月）", bold=True, font_size=14, font_color="0A1F3F"),
    M("/一阶段-验证闭环/A1:F1"),
    S("/一阶段-验证闭环/A2", "唯一目标：证明AI复核在政府审计报告场景中的可行性与业务价值", font_size=10),
    S("/一阶段-验证闭环/A4", "本阶段不做（写死在墙上）", bold=True, font_size=11, font_color="CC0000"),
]
dont_do = ["不做投标方案生成","不做质控汇总平台","不做其他业务线Agent","不做SaaS/多租户","不做模型微调","不买新GPU硬件（Day90决策）"]
for i, item in enumerate(dont_do):
    p1.append(S(f"/一阶段-验证闭环/A{5+i}", f"❌ {item}", font_size=10, font_color="CC0000"))

# Phase 1A
p1.append(S("/一阶段-验证闭环/A12", "阶段1A：零阶段·准备工作（Day 1-14）¥0投入", bold=True, font_size=12, font_color="1A5C6E"))
for i, h in enumerate(["天数", "任务", "产出物"]):
    p1.append(S(f"/一阶段-验证闭环/{chr(65+i)}13", h, bold=True, fill="0A1F3F", font_color="FFFFFF"))
tasks_1a = [
    ("Day 1-2", "收集校园餐+医保全部原始资料；合规三问调研", "原始资料包 + 合规调研笔记"),
    ("Day 3-4", "手工标注第1份校园餐报告", "人工复核Checklist v1.0"),
    ("Day 5-6", "OpenClaw跑AI复核 vs 人工对比", "第1份人机对比表"),
    ("Day 7-8", "换医保资金报告，重复对比", "第2份人机对比表"),
    ("Day 9-10", "第3-5份不同来源/年份报告", "5份原始AI复核结果"),
    ("Day 11-12", "整理首周发现", "第1周验证周报"),
    ("Day 13", "定稿量化通过标准", "标准文档"),
    ("Day 14", "输出《政府审计AI辅助能力白皮书》初稿", "白皮书v1.0"),
]
for i, (a, b, c) in enumerate(tasks_1a):
    row = 14 + i
    p1.append(S(f"/一阶段-验证闭环/A{row}", a, font_size=10))
    p1.append(S(f"/一阶段-验证闭环/B{row}", b, font_size=10))
    p1.append(S(f"/一阶段-验证闭环/C{row}", c, font_size=10))

# Phase 1B
r = 14 + len(tasks_1a) + 1
p1.append(S(f"/一阶段-验证闭环/A{r}", "阶段1B：规则引擎验证（Day 15-60）¥0-1万（API费）", bold=True, font_size=12, font_color="1A5C6E"))
r += 1
for i, h in enumerate(["维度","内容","说明"]):
    p1.append(S(f"/一阶段-验证闭环/{chr(65+i)}{r}", h, bold=True, fill="0A1F3F", font_color="FFFFFF"))
r += 1
p1b = [
    ("验证范围", "格式检查+合计校验+法规引用完整性+附表交叉比对", "只做规则层面，不碰语义判断"),
    ("测试报告", "10份（5份校园餐+5份医保），≥3个不同客户来源", "必须不同年份、不同格式"),
    ("通过标准", "规则引擎准确率≥95%，误报率≤10%", "未达标→延长至Day90重测"),
    ("数据积累", "每条人工修正diff存入Label Studio", "每天至少攒10条"),
    ("Prompt管理", "建立评估表：每次改prompt记录预期vs实际", "防止调参死循环"),
]
for i, (a, b, c) in enumerate(p1b):
    p1.append(S(f"/一阶段-验证闭环/A{r+i}", a, bold=True, font_size=10))
    p1.append(S(f"/一阶段-验证闭环/B{r+i}", b, font_size=10))
    p1.append(S(f"/一阶段-验证闭环/C{r+i}", c, font_size=10))

# Phase 1C
r += len(p1b) + 1
p1.append(S(f"/一阶段-验证闭环/A{r}", "阶段1C：语义复核验证（Day 61-90）¥1-3万（API增加+Qwen备援）", bold=True, font_size=12, font_color="1A5C6E"))
r += 1
p1c = [
    ("验证范围", "语义层面：结论与证据链一致性+法规适用准确性+指标合理性+文字专业性"),
    ("方法", "RAG增强：每条AI意见附引用源chunk（溯源链=审计师信任基础）"),
    ("通过标准（三指标）", "①关键错误检出率≥人工80% ②误报率≤20% ③采纳率≥40%  三指标须同时达标"),
    ("盲测设计", "3份未训练报告，AI vs 平头哥独立复核，盲测对比（防止看答案出题）"),
    ("API容灾", "确认Qwen/豆包API可用，完成同一报告跨模型对比"),
    ("Day90决策门", "达标→招第1个AI工程师 | 部分达标→延长30天 | 严重不达标→降级为辅助模式"),
]
for i, (a, b) in enumerate(p1c):
    p1.append(S(f"/一阶段-验证闭环/A{r+i}", a, bold=True, font_size=10))
    p1.append(S(f"/一阶段-验证闭环/B{r+i}", b, font_size=10))
    M(f"/一阶段-验证闭环/B{r+i}:C{r+i}")

# Phase 1D
r += len(p1c) + 1
p1.append(S(f"/一阶段-验证闭环/A{r}", "阶段1D：工程师入场+实战交付（Day 91-180）¥10-15万", bold=True, font_size=12, font_color="1A5C6E"))
r += 1
p1d = [
    ("招人画像", "Python+LangChain+向量数据库+FastAPI，月薪1.5-2万(成都)，不要求微调/K8s/前端"),
    ("固化为Web界面", "审计师可自行上传报告→收到AI复核结果（简陋版，能用就行）"),
    ("扩至3条业务线", "校园餐+医保资金+绩效评价"),
    ("标注数据≥1000条", "为未来微调打底"),
    ("若尔盖项目AI辅助交付", "审计师自愿使用，不强推——内部口碑种子"),
    ("Day180决策门", "达标(3线效率+30%,≥10人周用≥3次)→进入Phase2 | 不达标→维持1人+API低成本运作"),
]
for i, (a, b) in enumerate(p1d):
    p1.append(S(f"/一阶段-验证闭环/A{r+i}", a, bold=True, font_size=10))
    p1.append(S(f"/一阶段-验证闭环/B{r+i}", b, font_size=10))
    M(f"/一阶段-验证闭环/B{r+i}:F{r+i}")

for col, w in [("A",22),("B",45),("C",30)]:
    p1.append({"op": "set", "path": f"/一阶段-验证闭环/{col}1:{col}1", "props": {"width": w}})

with open(os.path.join(outdir, "_batch_p1.json"), "w", encoding="utf-8") as f:
    json.dump(p1, f, ensure_ascii=False, indent=2)
print(f"Phase1: {len(p1)} ops written.")

# ======== 预算对比 ========
budget = [
    S("/预算对比/A1", "三阶段预算对比：v1.0 vs v2.0", bold=True, font_size=14, font_color="0A1F3F"),
    M("/预算对比/A1:F1"),
    S("/预算对比/A2", "v2.0省钱核心逻辑：砍GPU集群→用API、砍微调→走RAG、砍SaaS→私有化部署、砍5线→3线", font_size=10, font_color="666666"),
]
for i, h in enumerate(["项目", "v1.0预算", "v2.0修正", "变化", "修正原因"]):
    budget.append(S(f"/预算对比/{chr(65+i)}4", h, bold=True, fill="0A1F3F", font_color="FFFFFF"))

items = [
    ("【第一阶段】", "", "", "", ""),
    ("GPU工作站", "¥8-10万", "¥0（推迟至Day90）", "↓100%", "Luna：验证期API够用；GPT-5.5：5090未上市"),
    ("AI工程师(前3月)", "¥12-18万/年", "¥0（平头哥亲自+OpenClaw）", "↓100%", "苏格拉底Q5：那个人就是我"),
    ("AI工程师(后3月)", "—", "¥6-8万(Day90起)", "新增", "月薪¥1.8-2.4万含社保"),
    ("数据平台", "¥3万/年", "¥3万/年", "不变", "Qdrant+PG免费，天眼查¥2-4万"),
    ("API费用", "¥3-5万/年", "¥5-8万/年", "↑60%", "GPT-5.5+Gemini：单次复核token消耗大"),
    ("合规+法律顾问", "¥0", "¥1-2万/年", "新增", "Gemini：合规框架Day1建立"),
    ("一阶段小计", "¥40万", "¥15-21万", "↓50%", "风险后移，先验证后投入"),
    ("", "", "", "", ""),
    ("【第二阶段】", "", "", "", ""),
    ("GPU服务器", "¥20-25万", "¥5-7万(1台4090工作站)", "↓75%", "不做微调，无需A6000"),
    ("NAS+网络", "含上述", "¥1-2万", "拆分明细", ""),
    ("数据平台+标注", "¥13-20万/年", "¥10-15万/年", "↓25%", "开源工具为主"),
    ("应用开发", "¥23-37万/年", "¥20-28万/年", "↓25%", "3条线而非5条"),
    ("人力", "¥60-80万/年", "¥78万/年", "持平", "1全栈+1数据+3兼职专家"),
    ("品牌+输出", "¥0", "¥5-8万", "新增", "白皮书+行业会议+私测试点"),
    ("二阶段小计", "¥180万", "¥120-140万", "↓25%", ""),
    ("", "", "", "", ""),
    ("【第三阶段】", "", "", "", ""),
    ("算力集群", "¥100万+", "¥8-15万(单卡或云GPU)", "↓90%", "不做集群，不跑K8s"),
    ("数据平台+多模态", "含上述", "¥31-50万", "", "标注数据建设为核心"),
    ("应用开发", "含上述", "¥16-25万", "", "RAG+微调混合架构"),
    ("SaaS/输出", "含上述", "¥12-20万(私有化部署)", "", "不做SaaS多租户"),
    ("人力(5-6人)", "含上述", "¥120-160万", "", "AI团队+产品经理+业务专家"),
    ("三阶段小计", "¥500万+", "¥190-270万", "↓50%", ""),
    ("", "", "", "", ""),
    ("【三年总计】", "¥720万", "¥325-431万", "↓40-55%", ""),
]
for i, (a, b, c, d, e) in enumerate(items):
    row = 5 + i
    is_header = a.startswith("【")
    is_total = "小计" in a or "总计" in a
    budget.append(S(f"/预算对比/A{row}", a, bold=is_header or is_total, font_size=10, font_color="1A5C6E" if is_header else None))
    budget.append(S(f"/预算对比/B{row}", b, font_size=10, font_color="888888" if not is_total else None, bold=is_total))
    budget.append(S(f"/预算对比/C{row}", c, font_size=10, font_color="C5955C", bold=is_total))
    budget.append(S(f"/预算对比/D{row}", d, font_size=10, font_color="CC0000" if "↓" in str(d) else "228B22" if "↓" not in str(d) and d else None))
    budget.append(S(f"/预算对比/E{row}", e, font_size=10))

for col, w in [("A",22),("B",18),("C",22),("D",12),("E",35)]:
    budget.append({"op": "set", "path": f"/预算对比/{col}1:{col}1", "props": {"width": w}})

with open(os.path.join(outdir, "_batch_budget.json"), "w", encoding="utf-8") as f:
    json.dump(budget, f, ensure_ascii=False, indent=2)
print(f"Budget: {len(budget)} ops written.")

# ======== 风险清单 ========
risks = [
    S("/风险清单/A1", "Top 10 风险清单（概率×影响排序）", bold=True, font_size=14, font_color="0A1F3F"),
    M("/风险清单/A1:H1"),
]
for i, h in enumerate(["#","风险","概率","影响","等级","最小验证实验(7天)","通过标准","所需资源"]):
    risks.append(S(f"/风险清单/{chr(65+i)}3", h, bold=True, fill="0A1F3F", font_color="FFFFFF", font_size=10))

risk_data = [
    ("1","你自己放弃——旺季挤压+多线作战","高","毁灭","🔴🔴🔴","连续7天每天30min打卡","7天不间断","0元"),
    ("2","AI结果不被项目经理接受(采纳率<30%)","高","高","🔴🔴🔴","1份报告AI复核→逐条标注接受/不接受","≥10条AI发现+失效分类","0元"),
    ("3","被格式多样性打垮(换客户就崩)","高","高","🔴🔴🔴","≥3个不同来源报告各跑一遍","记录每种格式失效模式","0元"),
    ("4","无量化基线即推进","中","高","🔴🔴","定下通过标准并书面确认","标准已写在方案里","0元"),
    ("5","合规信息黑洞(客户问等保一问三不知)","中","高","🔴🔴","查等保费用/周期+数据出本地要求+云合规方案","拿到3个明确答案","30分钟"),
    ("6","原始数据质量极差(AI无法处理)","中","中","🟡","列10个数据质量问题","10条具体脏数据清单","0元"),
    ("7","Prompt调优陷入死循环","中","中","🟡","每次改prompt记录预期vs实际","≥2轮有记录的对比","0元"),
    ("8","范围蔓延(做到一半又想加功能)","低","高","🟡","写下\"审盾一期不做X\"贴在显眼处","一句话已完成","0元"),
    ("9","DeepSeek API宕机","低","中","🟡","确认备援模型可正常返回复核结果","备用API已就绪","已有key"),
    ("10","客户知道AI参与后要求降价","低","低(一年内)","🟢","暂不验证，标记为观察项","—","—"),
]
for i, (n, r, p, im, lv, exp, std, res) in enumerate(risk_data):
    row = 4 + i
    risks.append(S(f"/风险清单/A{row}", n, font_size=10))
    risks.append(S(f"/风险清单/B{row}", r, font_size=10))
    risks.append(S(f"/风险清单/C{row}", p, font_size=10))
    risks.append(S(f"/风险清单/D{row}", im, font_size=10))
    risks.append(S(f"/风险清单/E{row}", lv, font_size=14))
    risks.append(S(f"/风险清单/F{row}", exp, font_size=10))
    risks.append(S(f"/风险清单/G{row}", std, font_size=10))
    risks.append(S(f"/风险清单/H{row}", res, font_size=10))

for col, w in [("A",4),("B",28),("C",6),("D",6),("E",10),("F",30),("G",22),("H",12)]:
    risks.append({"op": "set", "path": f"/风险清单/{col}1:{col}1", "props": {"width": w}})

with open(os.path.join(outdir, "_batch_risks.json"), "w", encoding="utf-8") as f:
    json.dump(risks, f, ensure_ascii=False, indent=2)
print(f"Risks: {len(risks)} ops written.")

# ======== 第1周计划 ========
w1 = [
    S("/第1周计划/A1", "审盾一期·第1周行动计划（2026年7月22日-28日）", bold=True, font_size=14, font_color="0A1F3F"),
    M("/第1周计划/A1:D1"),
    S("/第1周计划/A2", "总耗时：约8小时 | 总预算：¥0 | 不需要新硬件/新人员", font_size=10, font_color="666666"),
    S("/第1周计划/A3", "每日硬性规则：早8点发\"审盾 Day X，今天做____\"，晚8点发\"审盾 Day X，完成了____\"", bold=True, font_size=10, font_color="CC0000"),
]
for i, h in enumerate(["星期", "日期", "任务", "产出物", "耗时"]):
    w1.append(S(f"/第1周计划/{chr(65+i)}5", h, bold=True, fill="0A1F3F", font_color="FFFFFF"))

plan = [
    ("周二", "7/22", "①收集校园餐+医保全部原始资料 ②合规三问调研", "📁原始资料包+📝合规调研笔记", "1.5h"),
    ("周三", "7/23", "手工标注第1份校园餐报告：记录人工检查点", "📝人工复核Checklist v1.0", "1h"),
    ("周四", "7/24", "OpenClaw跑AI复核 vs 人工对比，统计采纳率", "🔀人机对比表#1", "1h"),
    ("周五", "7/25", "换医保资金报告→人机对比#2", "🔀人机对比表#2", "1h"),
    ("周六", "7/26", "第3份不同来源/年份报告→人机对比#3", "🔀人机对比表#3", "1h"),
    ("周日", "7/27", "整理周报：采纳率+失效模式+脏数据清单", "📄第1周验证周报", "1.5h"),
    ("周一", "7/28", "定稿量化通过标准+白皮书大纲", "✅标准文档+📘白皮书大纲", "1h"),
]
for i, (day, date, task, output, time) in enumerate(plan):
    row = 6 + i
    w1.append(S(f"/第1周计划/A{row}", day, font_size=10))
    w1.append(S(f"/第1周计划/B{row}", date, font_size=10))
    w1.append(S(f"/第1周计划/C{row}", task, font_size=10))
    w1.append(S(f"/第1周计划/D{row}", output, font_size=10))
    w1.append(S(f"/第1周计划/E{row}", time, font_size=10, font_color="1A5C6E", bold=True))

for col, w in [("A",8),("B",8),("C",42),("D",30),("E",8)]:
    w1.append({"op": "set", "path": f"/第1周计划/{col}1:{col}1", "props": {"width": w}})

with open(os.path.join(outdir, "_batch_w1.json"), "w", encoding="utf-8") as f:
    json.dump(w1, f, ensure_ascii=False, indent=2)
print(f"Week1: {len(w1)} ops written.")

# ======== 决策门 ========
gates = [
    S("/决策门/A1", "审盾一期·决策门（Go/No-Go Gates）", bold=True, font_size=14, font_color="0A1F3F"),
    M("/决策门/A1:E1"),
    S("/决策门/A2", "没有止损线=没有真正的验证。每次决策门不达标，必须执行对应的降级动作。", font_size=10, font_color="CC0000"),
]
for i, h in enumerate(["节点", "检查标准", "达标动作", "不达标动作", "责任人"]):
    gates.append(S(f"/决策门/{chr(65+i)}4", h, bold=True, fill="0A1F3F", font_color="FFFFFF"))

gate_data = [
    ("Day 14\n(M0)", "≥5份报告人机对比完成\n量化标准已书面确认\n合规三问有答案", "进入阶段1B（规则引擎验证）", "延长1周补做，暂不进入1B", "平头哥"),
    ("Day 60\n(M1)", "规则引擎准确率≥95%\n误报率≤10%\n≥200条标注数据", "进入阶段1C（语义复核验证）", "延长至Day90重测\n不招人", "平头哥"),
    ("Day 90\n(M2)", "三指标同时达标：\n检出率≥80%+误报率≤20%+采纳率≥40%", "招第1个AI工程师\n进入阶段1D", "部分达标→延长30天\n严重不达标→降级为AI辅助建议模式\n不招人、不买GPU", "平头哥"),
    ("Day 180\n(M3)", "3条线AI效率≥30%\n≥10人每周使用≥3次\n工程师可独立维护", "进入第二阶段\n追加GPU+扩团队", "不进入Phase 2\n维持1人+API\n作为AI辅助工具集\n低成本运作", "平头哥"),
    ("Phase 2\n第3月", "每条线采纳率趋势上升\n核心用户留存>80%", "继续推广", "缩减为2条线\n砍掉效果最差的那条", "平头哥"),
    ("Phase 2\n第12月", "≥3条线采纳率≥50%\n核心用户≥20人\n私测合作方反馈正向\n标注数据集≥5000条", "进入第三阶段", "不进入Phase 3\n仅内部使用\n放弃对外输出", "平头哥"),
]
for i, (node, check, go, nogo, owner) in enumerate(gate_data):
    row = 5 + i
    gates.append(S(f"/决策门/A{row}", node, bold=True, font_size=10))
    gates.append(S(f"/决策门/B{row}", check, font_size=10))
    gates.append(S(f"/决策门/C{row}", go, font_size=10, font_color="228B22"))
    gates.append(S(f"/决策门/D{row}", nogo, font_size=10, font_color="CC0000"))
    gates.append(S(f"/决策门/E{row}", owner, font_size=10))

for col, w in [("A",12),("B",35),("C",22),("D",25),("E",10)]:
    gates.append({"op": "set", "path": f"/决策门/{col}1:{col}1", "props": {"width": w}})

with open(os.path.join(outdir, "_batch_gates.json"), "w", encoding="utf-8") as f:
    json.dump(gates, f, ensure_ascii=False, indent=2)
print(f"Gates: {len(gates)} ops written.")

print("\nAll batch JSONs generated!")
print(f"Files in: {outdir}")
