# -*- coding: utf-8 -*-
"""为采购、经责、绩效各生成3条可执行规则（条码+字段+算法+阈值+测试数据）。"""
from pathlib import Path
import json

OUT=Path(__file__).resolve().parents[1]/'knowledge/executable_rules'
OUT.mkdir(parents=True,exist_ok=True)

rules=[
# ========== 采购招投标 3条 ==========
{
'rule_id':'PROC-EXEC-001','business_line':'采购招投标审计','rule_name':'多家投标文件上传IP/MAC一致',
'required_fields':[{'name':'bidder_name','type':'string','desc':'投标人名称'},{'name':'upload_ip','type':'string','desc':'上传IP地址'},{'name':'upload_device_id','type':'string','desc':'设备指纹/UUID/MAC'}],
'logic':'GROUP BY upload_ip, upload_device_id HAVING COUNT(DISTINCT bidder_name) >= 2 -> 标记为疑似同一终端操作不同投标人',
'threshold':{'value':'>=2家','type':'离散','unit':'家'},
'confidence':{'high':{'>=2家+IP+MAC全一致':0.95},'medium':{'仅IP一致':0.7}},
'false_positive':['同一单位使用不同分公司的员工在同一局域网投标','代理机构协助上传时的中间人操作','VPN出口IP一致但实际不同地点'],
'verification_steps':['要求代理机构提供电子交易平台后台IP/设备日志','比对投标文件创建时间和上传时间','询问投标人是否使用同一网络','如有代理机构操作记录，提取其操作日志'],
'law_refs':['《招标投标法实施条例》第四十条','《政府采购法实施条例》第七十四条'],
'output_fields':['bidder_list','upload_ip','device_id','timestamp','confidence'],
'sample_data':json.dumps([{'bidder':'A公司','ip':'192.168.1.1','device':'MAC-00-1A-2B-3C-4D-5E','time':'2025-06-01 09:15:22'},{'bidder':'B公司','ip':'192.168.1.1','device':'MAC-00-1A-2B-3C-4D-5E','time':'2025-06-01 09:17:05'},{'bidder':'C公司','ip':'10.0.0.5','device':'MAC-AA-BB-CC-DD-EE-FF','time':'2025-06-01 10:00:11'}],ensure_ascii=False),
'expected_output':['A公司+B公司 IP一致且设备一致 → 疑似同一终端操作','C公司无异常'],
'sql_template':'SELECT bidder_name,upload_ip,upload_device_id,COUNT(*) OVER(PARTITION BY upload_ip,upload_device_id) AS cnt FROM tender_upload_log WHERE cnt>=2 ORDER BY cnt DESC',
},
{
'rule_id':'PROC-EXEC-002','business_line':'采购招投标审计','rule_name':'报价异常低价（低于平均值50%）',
'required_fields':[{'name':'bidder','type':'string'},{'name':'bid_price','type':'number','unit':'元'},{'name':'budget_control','type':'number','unit':'元'},{'name':'other_bidders_prices','type':'array[number]'}],
'logic':'计算所有有效报价的算术平均值，筛出报价<平均值*0.5的投标人；同时比较次低报价和最高限价阈值。',
'threshold':{'低于平均值50%':'触发异常低价审查','低于次低报价50%':'触发','低于最高限价45%':'触发'},
'confidence':{'高':{'低于平均值50%+低于次低50%':0.95},'中':{'仅低于平均值50%':0.75}},
'false_positive':['企业有特殊技术优势或专利','新产品推广期战略性亏损报价','清仓或处理库存的特殊情况','联合体投标内部成本分摊'],
'verification_steps':['要求投标人7日内提供书面成本构成说明','逐项核验材料费、人工费、管理费','对比该企业历史报价与行业均价','确认是否属于异常低价审查办法规定的四种情形（财库〔2026〕2号）'],
'law_refs':['财库〔2026〕2号 异常低价审查办法','招标投标法第四十一条','政府采购法实施条例第五十条'],
'output_fields':['bidder','bid_price','avg_price','threshold_50pct','triggered','confidence'],
'sample_data':json.dumps({'bidders':[{'name':'A','price':1000000},{'name':'B','price':950000},{'name':'C','price':420000},{'name':'D','price':880000}],'control_price':1200000},ensure_ascii=False),
'expected_output':'平均价=812500, 50%阈值=406250, C报价420000>406250, 未触发异常低价, 但接近阈值需关注说明',
'sql_template':'SELECT bidder,bid_price,AVG(bid_price)OVER() AS avg_price,bid_price/(AVG(bid_price)OVER()) AS ratio FROM bid_open_table WHERE ratio<0.5',
},
{
'rule_id':'PROC-EXEC-003','business_line':'采购招投标审计','rule_name':'评委打分偏离度异常（倾向性评分）',
'required_fields':[{'name':'bidder','type':'string'},{'name':'expert_name','type':'string'},{'name':'score_item','type':'string'},{'name':'score','type':'number'},{'name':'all_scores_for_item','type':'array[number]'}],
'logic':'计算每个评委对每个评分项的打分与同组其他评委平均分的偏离度。同一评委对某投标人在多评分项持续偏离>2个标准差，且该投标人最终得分显著偏高，标记为"疑似倾向性评分"。',
'threshold':{'星级偏离':'偏离度>2个标准差 或 偏离>评分项满分20%','持续偏离':'同一评委对同一投标人≥3个评分项持续偏离'},
'confidence':{'高':{'偏离>2σ+持续≥3项+该投标人最终中标':0.9},'中':{'仅偏离>2σ但未持续':0.7}},
'false_positive':['评委专业领域与评分项高度匹配，评分确实有差异','评委对评分标准理解不同（需查看培训记录）','该投标人确实在特定评分项有绝对优势'],
'verification_steps':['检查评标现场记录和录音','查看该评委对其他项目的评分模式','对比评分标准与评委打分的匹配度','访谈该评委，询问评分依据'],
'law_refs':['招标投标法实施条例第四十九条','评标委员会和评标方法暂行规定','政府采购法实施条例第四十条'],
'output_fields':['expert','bidder','score_item','deviation_sigma','sustained_anomaly','result'],
'sample_data':json.dumps({'评委张':{'A公司':[95,92,90,88],'B公司':[70,68,65,72],'C公司':[75,72,70,74]},'其他评委平均':{'A公司':[80,78,82,75],'B公司':[72,70,68,73],'C公司':[76,73,71,75]}},ensure_ascii=False),
'expected_output':'评委张对A公司4项评分平均偏离>15分（>2σ），且A公司中标 → 疑似倾向性评分',
'sql_template':'SELECT expert_name,bidder,score_item,score,AVG(score) OVER(PARTITION BY score_item) AS avg_score,score-AVG(score) OVER(PARTITION BY score_item) AS deviation FROM scoring_detail WHERE ABS(deviation)>2*STDDEV(score) OVER(PARTITION BY score_item)',
},

# ========== 经济责任审计 3条 ==========
{
'rule_id':'ECON-EXEC-001','business_line':'经济责任审计','rule_name':'任期交界点异常支出（前后3个月集中支付）',
'required_fields':[{'name':'payment_date','type':'date'},{'name':'payment_amount','type':'number','unit':'元'},{'name':'recipient','type':'string'},{'name':'payment_description','type':'string'},{'name':'approver','type':'string'},{'name':'handover_date','type':'date'}],
'logic':'以离任交接日期为基准，前后各90天为窗口期。统计窗口期内支付金额、笔数和收款方，与全年月均比较。窗口期月均金额或笔数 > 全年月均*3倍，且收款方集中度>60%，标记为"交界点异常支出"。',
'threshold':{'金额倍数':'>全年月均*3','笔数倍数':'>全年月均*3','收款方集中度':'>60%窗口期总金额'},
'confidence':{'高':{'金额倍数>3+收款方集中度>60%+无交接前审批':0.9},'中':{'仅金额倍数>3':0.7}},
'false_positive':['季节性集中支付（如年底结算、项目尾款）','政策要求的集中支付（如疫情期间特别支付）','上级统一安排的集中采购','确实正常的工程项目进度款结算'],
'verification_steps':['逐笔核验窗口期支出的审批手续是否齐全','对比交接前与交接后的审批人并记录','检查收款方与领导是否存在关联关系','访谈财务人员了解集中支付的真实原因','比对预算和实际支出匹配度'],
'law_refs':['党政主要领导干部和国有企事业单位主要领导人员经济责任审计规定','财政违法行为处罚处分条例'],
'output_fields':['handover_date','window_start','window_end','window_total','window_monthly_avg','annual_avg','ratio','recipient_concentration','severity','confidence'],
'sample_data':json.dumps({'handover_date':'2025-06-30','全年月均支出':1200000,'窗口期支出':[{'date':'2025-04-15','amount':5500000,'recipient':'X建设公司','desc':'工程款'},{'date':'2025-05-20','amount':3200000,'recipient':'X建设公司','desc':'工程款'},{'date':'2025-06-28','amount':1800000,'recipient':'Y设备公司','desc':'设备采购'}],'全年总支出':14400000},ensure_ascii=False),
'expected_output':'窗口期(2025-04-01至2025-06-30)总支出=1050万, 月均350万, 全年月均120万, 倍数=2.92, 接近阈值; X建设公司集中度82.86% → 需核验审批手续',
'sql_template':'SELECT payment_date,amount,recipient,approver FROM payment_journal WHERE payment_date BETWEEN handover_date-90 AND handover_date+90 GROUP BY recipient ORDER BY amount DESC',
},
{
'rule_id':'ECON-EXEC-002','business_line':'经济责任审计','rule_name':'三重一大事项程序闭环缺失',
'required_fields':[{'name':'decision_id','type':'string'},{'name':'decision_date','type':'date'},{'name':'decision_type','type':'string','enum':['重大项目投资','大额资金使用','重要人事任免','重大并购重组','大额资产处置']},{'name':'amount','type':'number','unit':'元'},{'name':'meeting_date','type':'date'},{'name':'meeting_attendance','type':'number'},{'name':'meeting_total','type':'number'},{'name':'approval_doc','type':'string'},{'name':'implementation_report','type':'string'}],
'logic':'检查每一笔三重一大事项四个环节的完整性：(1)会议记录（出席人数≥应到2/3）(2)决策文件（有正式决议）(3)执行记录（有实施报告）(4)检查评估（有结果反馈）。缺失任一环节或会议人数不足三分之二，标记为"程序闭环缺失"。',
'threshold':{'会议出席率':'<66.7%视为无效决策','闭环完成率':'<100%即标记缺失'},
'confidence':{'高':{'会议出席<2/3+无正式决议':0.95},'中':{'仅缺执行记录或检查报告':0.75}},
'false_positive':['紧急事项走"先执行后补程序"通道（需有审批记录）','部分小事项(金额<50万)经授权简化流程','会议纪要会后补充但已归档'],
'verification_steps':['调取所有三重一大事项的会议记录原件','核验签到表人数与应到人数','确认议题是否在会议通知中','检查决议是否正式行文','追踪执行结果是否有反馈记录'],
'law_refs':['国有企业领导人员廉洁从业若干规定','三重一大决策制度实施办法','经济责任审计规定第十五条'],
'output_fields':['decision_id','type','amount','meeting_date','attendance_rate','approval','execution','evaluation','missing_items','severity'],
'sample_data':json.dumps([{'id':'D001','type':'重大项目投资','amount':80000000,'meeting_date':'2025-03-15','出席':5,'应到':7,'决议':'有','执行':'有','检查':'有'},{'id':'D002','type':'大额资产处置','amount':15000000,'meeting_date':'2025-05-20','出席':4,'应到':7,'决议':'有','执行':'无','检查':'无'}],ensure_ascii=False),
'expected_output':'D001：完整（出席率71.4%>2/3，闭环完整）；D002：缺失执行记录和检查评估，出席率57.1%<2/3 → 疑似无效决策',
'sql_template':"SELECT * FROM three_heavy_decisions WHERE attendance/expected*100<66.7 OR approval IS NULL OR execution IS NULL OR evaluation IS NULL",
},
{
'rule_id':'ECON-EXEC-003','business_line':'经济责任审计','rule_name':'任期前后财务指标断崖式变化',
'required_fields':[{'name':'indicator','type':'string','enum':['资产负债率','收入增长率','净利润','应收账款周转率','存货周转率','经营性现金流']},{'name':'pre_term_value','type':'number'},{'name':'post_term_value','type':'number'},{'name':'pre_term_period','type':'string'},{'name':'post_term_period','type':'string'},{'name':'industry_benchmark','type':'number'}],
'logic':'前任离任前12个月与接任后12个月的关键财务指标对比。变化幅度超过±50%且与行业趋势反向的，标记为"疑似指标操纵"或"会计政策变更"。尤其关注离任前突击做大收入和利润、接任后大额计提减值。',
'threshold':{'变更幅度':'>±50%','方向一致':'与行业趋势反向则标记'},
'confidence':{'高':{'变更>±80%+与行业反向':0.9},'中':{'变更>±50%但行业同步':0.7}},
'false_positive':['会计准则变更导致的调整','重大资产重组或并购合并范围变化','行业周期波动或政策调整','自然灾害等不可抗力因素'],
'verification_steps':['检查会计政策是否变更','核实收入确认时点是否存在跨期调节','检查大额资产减值计提依据','对比同行业可比公司同期变化','关注应收账款和预收账款异常变动'],
'law_refs':['企业会计准则—基本准则','经济责任审计规定第二十条','审计法第三十六条'],
'output_fields':['indicator','pre_value','post_value','change_pct','industry_trend','direction_match','severity','confidence'],
'sample_data':json.dumps({'pre':{'收入':500000000,'净利润':50000000,'应收账款':80000000,'坏账准备':2000000},'post':{'收入':350000000,'净利润':-30000000,'应收账款':120000000,'坏账准备':25000000},'行业趋势':{'收入同比':-0.05,'净利润同比':-0.10}},ensure_ascii=False),
'expected_output':'收入变化-30%（行业-5%），净利润变化-160%（行业-10%），应收账款及坏账准备大幅增加 → 疑似突击确认收入后接任者大额计提，需核验收入确认政策和坏账计提依据',
'sql_template':'SELECT indicator,pre_term_value,post_term_value,(post_term_value-pre_term_value)/pre_term_value*100 AS change_pct FROM financial_indicators WHERE ABS(change_pct)>50',
},

# ========== 绩效评价 3条 ==========
{
'rule_id':'PERF-EXEC-001','business_line':'绩效评价','rule_name':'绩效目标与产出的可衡量性验真',
'required_fields':[{'name':'target_id','type':'string'},{'name':'target_description','type':'string'},{'name':'target_type','type':'string','enum':['产出指标','效益指标','满意度指标','时效指标','成本指标']},{'name':'target_unit','type':'string'},{'name':'target_value','type':'string'},{'name':'actual_value','type':'string'},{'name':'verification_source','type':'string'}],
'logic':'检查绩效目标是否满足SMART原则：具体(Specific)、可衡量(Measurable)、可达成(Achievable)、相关(Relevant)、有时限(Time-bound)。非量化目标（如"提高群众满意度""加强管理"）且无验证依据的，标记为"不可衡量目标"。同时计算实际完成值与目标值的偏差。',
'threshold':{'不可衡量':'无量化指标+无验收标准+无验证依据','目标偏差':'|实际值-目标值|/目标值>20%'},
'confidence':{'高':{'非量化目标+无验证依据':0.95},'中':{'量化目标但无验收标准':0.75}},
'false_positive':['定性目标在政策文件中确有合理性（如"持续改善"）','目标值在申报时确有合理预期但实际情况变化','部分服务类项目确实难以量化'],
'verification_steps':['对照绩效目标申报表逐项核验','检查是否有第三方评估或验收报告','访谈项目管理方了解目标设定依据','对比同类项目目标设定水平'],
'law_refs':['项目支出绩效评价管理办法（财预〔2020〕10号）','中共中央 国务院关于全面实施预算绩效管理的意见'],
'output_fields':['target_id','description','is_measurable','target_value','actual_value','deviation_pct','verification_passed','severity'],
'sample_data':json.dumps([{'id':'T001','desc':'培训500人次','target':'500','actual':'487','source':'签到表','type':'量化'},{'id':'T002','desc':'提高群众满意度','target':'显著提高','actual':'未提供','source':'无','type':'定性'}],ensure_ascii=False),
'expected_output':'T001：完成率97.4% 偏差2.6% 通过；T002：非量化目标+无验证依据 → 不可衡量，需补充满意度调查或受益对象证明',
'sql_template':"SELECT target_id,target_description,target_value,actual_value,ABS(CAST(actual_value AS FLOAT)-CAST(target_value AS FLOAT))/CAST(target_value AS FLOAT)*100 AS deviation FROM performance_targets WHERE deviation>20 OR (target_type='定性' AND verification_source IS NULL)",
},
{
'rule_id':'PERF-EXEC-002','business_line':'绩效评价','rule_name':'预算执行偏差与资金使用效率',
'required_fields':[{'name':'budget_item','type':'string'},{'name':'budget_amount','type':'number','unit':'元'},{'name':'actual_spent','type':'number','unit':'元'},{'name':'spent_by_period','type':'array[number]'},{'name':'project_period','type':'string'},{'name':'remaining_balance','type':'number','unit':'元'}],
'logic':'计算预算执行率=实际支出/预算金额。执行率<80%或>120%皆标记异常。同时检查资金拨付进度与项目进度的匹配度，拨付远高于实施进度的标记为"资金闲置风险"，拨付远低于进度的标记为"资金不足影响进度"。',
'threshold':{'执行率偏低':'<80%','执行率偏高':'>120%','拨付与进度差':'拨付进度-实施进度>20%'},
'confidence':{'高':{'执行率<60%+资金闲置>30%':0.9},'中':{'执行率<80%或>120%':0.8}},
'false_positive':['跨年度项目当年未完工（执行率偏低）','年中追加预算但支出尚未完成（执行率偏高）','预拨款项但项目尚未启动','集中采购分期付款导致资金闲置'],
'verification_steps':['检查资金闲置的具体原因','确认项目进度与资金使用是否匹配','核实是否存在资金被挪用或滞留','检查资金拨付审批手续是否完整'],
'law_refs':['预算法第五十七条','预算绩效管理制度','项目支出绩效评价管理办法第十五条'],
'output_fields':['budget_item','budget','actual','execution_rate','implementation_progress','gap','risk_type','severity'],
'sample_data':json.dumps([{'item':'设备采购','budget':10000000,'actual':2800000,'progress':0.25,'period':'2025-01至2025-12'},{'item':'培训费','budget':500000,'actual':520000,'progress':0.95,'period':'2025-01至2025-12'}],ensure_ascii=False),
'expected_output':'设备采购：执行率28%严重偏低，实施进度25%与实际支出基本匹配，但资金闲置72%疑似进度滞后；培训费：执行率104%正常，进度95%匹配',
'sql_template':'SELECT budget_item,budget_amount,actual_spent,actual_spent/budget_amount*100 AS exec_rate,implementation_progress*100 AS impl_pct FROM budget_execution WHERE exec_rate<80 OR exec_rate>120',
},
{
'rule_id':'PERF-EXEC-003','business_line':'绩效评价','rule_name':'受益对象真实性与覆盖范围',
'required_fields':[{'name':'beneficiary_name','type':'string'},{'name':'id_number','type':'string','sensitive':True,'desc':'仅用于去重，输出前脱敏显示'},{'name':'benefit_type','type':'string','enum':['培训/教育补贴','生活补贴','产业扶持','就业服务','物资发放']},{'name':'benefit_date','type':'date'},{'name':'benefit_amount','type':'number','unit':'元'},{'name':'signature','type':'string','desc':'签名或指纹'},{'name':'verification_by','type':'string','desc':'核实人'}],
'logic':'对受益对象名单进行去重分析，检查是否存在同一人重复申报、同一项目多期重复领取、同一人在不同项目间重复受益。同时抽样核实受益对象身份真实性：电话回访+实地走访。',
'threshold':{'重复率':'>3%视为异常','失踪比例':'>5%电话无法接通或地址不存在则标记','虚报金额':'>10%总受益金额'},
'confidence':{'高':{'重复率>10%+失踪率>15%':0.95},'中':{'重复率>3%+部分无法核实':0.8}},
'false_positive':['同一人确实符合多个项目条件（如同时享受低保和医疗救助）','不同项目名称不同但受益对象相同（系统交叉比对时需区分项目）','部分对象确实外出务工或更换联系方式'],
'verification_steps':['提取身份证号去重统计','随机抽取≥10%样本进行电话核实','对异常数据实地走访','检查原始签名或指纹是否一致','对比社区/村组花名册确认身份'],
'law_refs':['财政违法行为处罚处分条例','社会救助暂行办法','惠民惠农补贴资金"一卡通"管理规定'],
'output_fields':['total_beneficiaries','duplicate_count','duplicate_rate','unreachable_rate','falsified_amount','risk_level','confidence'],
'sample_data':json.dumps({'total':500,'duplicates':{'同一身份证号出现2次':35,'同一身份证号出现3次以上':8},'抽样':{'电话成功':300,'电话无法接通':45,'号码不存在':12,'确认未享受':8}},ensure_ascii=False),
'expected_output':'重复率(35+8)/500=8.6%>3%阈值；电话无法接通+号码不存在率=(45+12)/500=11.4%>5%阈值；疑似虚报确认未享受8人 → 需重点核查并计算虚报金额',
'sql_template':'SELECT id_number,COUNT(*) AS cnt FROM beneficiary_list GROUP BY id_number HAVING cnt>=2 ORDER BY cnt DESC',
}
]

for r in rules: (OUT/f'{r["rule_id"]}.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'generated':len(rules),'path':str(OUT)},ensure_ascii=False))