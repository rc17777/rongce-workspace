"""Build expanded script by combining lines 1-518 of v5b with new Part 3 content"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

src = r'D:\openclaw-workspace\scripts\gen_ppt_v5b.py'
dst = r'D:\openclaw-workspace\scripts\gen_ppt_v6.py'

with open(src, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find where Part 3 starts
cut = None
for i, line in enumerate(lines):
    if 'SLIDE 18: PART 3 DIVIDER' in line:
        cut = i
        break

if cut is None:
    print('ERROR: could not find Part 3 divider')
    sys.exit(1)

print(f'Part 3 starts at line {cut+1}, keeping lines 1-{cut}')

# Keep everything before Part 3 divider
prefix = ''.join(lines[:cut])

# The expanded Part 3 content
expanded_part3 = r'''
# ═══════════════════════════════════
# SLIDE 18: PART 3 DIVIDER (EXPANDED)
# ═══════════════════════════════════
print('Slide 18: Part 3 Divider')
s = add_slide(2); add_decor(s)
add_title_box(s, '第三部分', top=emu(1.5), font_size=44, color=CLR['green'],
              align=PP_ALIGN.CENTER, width=SW-emu(2.0), left=emu(1.0))
add_title_box(s, '从问题到提升·管理升华', top=emu(2.8), font_size=28, color=CLR['dark'],
              align=PP_ALIGN.CENTER, width=SW-emu(2.0), left=emu(1.0), bold=False)
tb = add_text_box(s, ['13项问题 → 4大根因 → 5条建议 → 6步落地 → 1张路线图'],
                  top=emu(4.0), font_size=16, color=CLR['gray'], left=emu(1.5), width=SW-emu(3.0))
tb.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

# ═══════════════════════════════════
# SLIDE 19: ROOT CAUSE
# ═══════════════════════════════════
print('Slide 19: Root Cause')
s = add_slide(1); add_decor(s)
add_title_box(s, '13项问题的底层逻辑：管理闭环的四个断裂点', top=emu(0.5), font_size=24)
add_text_box(s, [
    ('13项问题表面各不相同，但根因指向同一个事实：管理闭环断裂', True, CLR['accent']),
    '',
    ('\U0001f534 断裂点一：制度与执行脱节 — 墙上制度', True, CLR['accent']),
    '不相容职务分离制度写了，执行时一人兼审核+收费+对账 \u2192 问题2',
    '退租交接流程定了，退租后钥匙还在你手里 \u2192 问题8',
    '',
    ('\U0001f534 断裂点二：台账与实物不符 — 纸上台账', True, CLR['accent']),
    '车位备案379个，实际有效320个，四种口径四个数 \u2192 问题1',
    '物业用房5间仅1间入台账，门牌缺失 \u2192 问题9',
    '空调多2台、消火栓少18个，账面与实物差20个 \u2192 问题12',
    '',
    ('\U0001f534 断裂点三：审批与管控虚设 — 橡皮图章', True, CLR['accent']),
    '三人行优惠变1带多，67人中仅9人是老客户 \u2192 问题3',
    '商户从40\u33a1调到66\u33a1无审批无调价 \u2192 问题7',
    '17间房10间没签协议，默认\uff1c配套用房不用签\uff1e \u2192 问题5',
    '',
    ('\U0001f534 断裂点四：监督与闭环缺失 — 形式检查', True, CLR['accent']),
    '维保记录提前签字、两份记录内容截然不同 \u2192 问题12',
    '年度考评走过场，扣1,200元走个形式 \u2192 问题13',
    '351次手动放行无台账无核对无追溯 \u2192 问题2',
], top=emu(1.1), font_size=11.5, line_spacing=1.1)

# ═══════════════════════════════════
# SLIDE 20: THREE-LEVEL IC
# ═══════════════════════════════════
print('Slide 20: Three-Level IC')
s = add_slide(1); add_decor(s)
add_title_box(s, '内控体系的三阶进化', top=emu(0.5), font_size=28)
levels = [
    ('第一阶', '合规型内控', '制度齐全\n满足监管最低要求\n\u201c该有的都有了\u201d', '及格线', CLR['gray']),
    ('第二阶', '有效型内控', '制度落地执行\n流程闭环留痕\n\u201c做了的都有记录\u201d', '优良线', CLR['amber']),
    ('第三阶', '卓越型内控', '数据驱动预警\n主动风险防控\n\u201c没发生的也能预见\u201d', '标杆线', CLR['green']),
]
cw, g = emu(3.8), emu(0.2)
for i, (stage, title, desc, level, clr) in enumerate(levels):
    x = emu(0.7) + i*(cw+g)
    add_label(s, f'{stage}\uff1a{title}', emu(1.3), x, cw, emu(0.5), bg_color=clr, font_size=15)
    add_label(s, level, emu(1.9), x+emu(1.0), emu(1.8), emu(0.35), bg_color=CLR['accent'], font_size=11)
    tb = add_text_box(s, [desc], top=emu(2.5), left=x+emu(0.2), width=cw-emu(0.4), height=emu(1.5), font_size=13)
    tb.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
add_text_box(s, [
    ('\u25b6 现状诊断', True, CLR['title']),
    '天府广场项目管理处于\u201c第一阶\u2192第二阶\u201d之间\u2014\u2014制度有但执行不实',
    ('\u25b6 目标', True, CLR['title']),
    '2027年底前达到第二阶\uff08有效型\uff09\uff0c向第三阶\uff08卓越型\uff09迈进',
], top=emu(4.2), font_size=14, line_spacing=1.3)

# ═══════════════════════════════════
# SLIDE 21: THREE LINES OF DEFENSE
# ═══════════════════════════════════
print('Slide 21: Three Lines of Defense')
s = add_slide(1); add_decor(s)
add_title_box(s, '风险管理的三道防线', top=emu(0.5), font_size=28)
lines_data = [
    ('第一道', '业务部门', '风险所有者', '日常操作中的\n自我管控与自查', '停车场收费员、商户管理员\n维保人员、审批经办人', CLR['blue']),
    ('第二道', '风控/合规部门', '风险管理者', '制度建设、监督检查\n风险预警与报告', '内控部门、财务部门\n法务部门、安质部门', CLR['amber']),
    ('第三道', '审计部门', '独立保证者', '独立评价、问题发现\n改进建议与追责', '内部审计、外部审计\n纪检、巡视', CLR['accent']),
]
cw, g = emu(3.8), emu(0.2)
for i, (num, dept, role, duty, who, clr) in enumerate(lines_data):
    x = emu(0.7) + i*(cw+g)
    add_label(s, f'{num}防线\uff1a{dept}', emu(1.2), x, cw, emu(0.4), bg_color=clr, font_size=13)
    add_text_box(s, [
        (role, True, clr),
        duty,
    ], top=emu(1.8), left=x+emu(0.1), width=cw-emu(0.2), height=emu(1.2), font_size=12, line_spacing=1.2)
    add_text_box(s, [
        ('典型岗位', True, CLR['gray']),
        who,
    ], top=emu(3.2), left=x+emu(0.1), width=cw-emu(0.2), height=emu(1.0), font_size=11, line_spacing=1.2, color=CLR['gray'])
add_text_box(s, [
    ('\u26a0 现状问题', True, CLR['accent']),
    '三道防线之间信息断裂、各自为战\uff1a第一道觉得\u201c反正有人查\u201d\uff0c第二道觉得\u201c等审计来\u201d\uff0c第三道一年只来一次',
    ('\u25b6 改进方向', True, CLR['title']),
    '建立三道防线信息共享与协同机制 \u2192 季度联席风险分析会 \u2192 问题台账动态共享',
], top=emu(4.5), font_size=13, line_spacing=1.15)

# ═══════════════════════════════════
# SLIDE 22: RECOMMENDATIONS (EXPANDED)
# ═══════════════════════════════════
print('Slide 22: Recommendations')
s = add_slide(1); add_decor(s)
add_title_box(s, '综合管理建议', top=emu(0.5), font_size=28)
recs_expanded = [
    ('\U0001f17f 停车场管理', [
        '底数清查\uff1a逐位实测+备案变更\uff0c确保一个口径一个数',
        '岗位分设\uff1a审核/收费/对账/系统录入四岗分离',
        '手动放行管控\uff1a每次放行\u2192即时登记\u2192双人复核\u2192周周核对',
    ], CLR['accent']),
    ('\U0001f3e2 租赁与物业用房', [
        '权属排查\uff1a补充协议全覆盖\uff0c不认\u201c默认\u201d只认签字',
        '面积核验\uff1a定期抽查商户实际使用面积vs合同面积',
        '退租闭环\uff1a钥匙交还+现场核验+双方签字+归档',
    ], CLR['amber']),
    ('\U0001f441 现场运营', [
        '维保标准化\uff1a统一记录模板+拍照留证+双人签字',
        '设备盘点\uff1a季度实物盘点+与台账比对+差异即时上报',
        '考评闭环\uff1a年度考评结果与绩效挂钩+整改复查',
    ], CLR['blue']),
    ('\U0001f504 常态化机制', [
        '月度自查\uff1a各部门按清单自查\uff0c问题即查即改即报',
        '季度联席会\uff1a风控+业务+审计三方数据比对',
        '年度外审\uff1a独立第三方穿透式评价',
    ], CLR['green']),
]
y = emu(1.2)
for title, items, clr in recs_expanded:
    add_label(s, title, y, emu(0.8), emu(3.2), emu(0.4), bg_color=clr, font_size=12)
    add_text_box(s, items, top=y, left=emu(4.2), width=emu(8.0), height=emu(1.0), font_size=11, line_spacing=1.15)
    y += emu(1.1)
add_text_box(s, [('四条建议四个关键词\uff1a分离\u00b7核验\u00b7标准化\u00b7闭环\u00b7协同', True, CLR['title'])],
             top=emu(5.7), font_size=14)

# ═══════════════════════════════════
# SLIDE 23: SIX-STEP (EXPANDED)
# ═══════════════════════════════════
print('Slide 23: Six-Step')
s = add_slide(1); add_decor(s)
add_title_box(s, '制度落地六步法\uff1a从天府广场案例看每一步怎么走', top=emu(0.4), font_size=22)
steps_exp = [
    ('\u2460建制度', '停车场无手动放行制度\uff1f\u2192 立即补建', '制度不在多\uff0c在管用', CLR['blue']),
    ('\u2461明职责', '谁审月租\uff1f谁管收费\uff1f谁核对账\uff1f\u2192 落实到人', '一岗一责\uff0c白纸黑字', CLR['blue']),
    ('\u2462讲培训', '新制度出台谁教过\uff1f\u2192 每人签字确认培训记录', '没培训=没发布', CLR['amber']),
    ('\u2463建台账', '手动放行登记了吗\uff1f退租交接签了吗\uff1f\u2192 留痕', '没记录=没发生', CLR['amber']),
    ('\u2464强检查', '检查不是翻翻本子签字走人\u2192 交叉互查+飞行检查', '检查也是要留痕的', CLR['accent']),
    ('\u2465严问责', '问题整改谁盯\uff1f到期未改谁扛\uff1f\u2192 闭环到人', '没有问责=没有闭环', CLR['accent']),
]
y = emu(1.1)
for action, example, principle, clr in steps_exp:
    add_label(s, action, y, emu(0.7), emu(2.0), emu(0.4), bg_color=clr, font_size=13)
    add_text_box(s, [example], top=y, left=emu(2.9), width=emu(5.5), height=emu(0.35), font_size=12, line_spacing=1.1)
    add_text_box(s, [f'\u2192 {principle}'], top=y+emu(0.05), left=emu(8.5), width=emu(3.5), height=emu(0.35), font_size=12, color=CLR['accent'])
    y += emu(0.75)
add_text_box(s, [
    ('核心结论', True, CLR['title']),
    '打通\u201c最后一公里\u201d的关键\uff0c不在于制度有多少\uff0c而在于执行有多实',
    '六步法的本质\uff1a把\u201c应该做\u201d变成\u201c必须做\u201d\uff0c把\u201c做了\u201d变成\u201c能证明做了\u201d',
], top=emu(5.4), font_size=13, line_spacing=1.2)

# ═══════════════════════════════════
# SLIDE 24: DIGITAL AUDIT PREP
# ═══════════════════════════════════
print('Slide 24: Digital Audit Prep')
s = add_slide(1); add_decor(s)
add_title_box(s, '数字化审计时代\uff1a企业必须做好的四项准备', top=emu(0.5), font_size=24)
add_text_box(s, [
    ('2026年起\uff0c穿透式智能监管平台全面上线\u3002审计不再是翻凭证\u3001看台账\u2014\u2014', True, CLR['accent']),
    ('而是系统自动抓数据\u3001自动比对\u3001自动预警\u3002企业必须提前准备\u3002', True, CLR['accent']),
    '',
    ('\u2776 财务系统标准化与互联互通', True, CLR['title']),
    '停车场收费系统\u3001租赁管理系统\u3001物业管理系统\u3001财务系统\u2014\u2014四系统必须打通',
    '打破信息孤岛\uff1a一个商户的租金收缴\u3001面积使用\u3001合同变更\uff0c在一个视图里看到全貌',
    '',
    ('\u2777 业务数据全流程数字化留痕', True, CLR['title']),
    '每一笔收费从收\u2192核\u2192存全链路可追溯\uff1b每一次审批从提\u2192审\u2192批有完整时间戳',
    '手动放行\u3001现金收款这类\u201c离线操作\u201d必须纳入系统管控',
    '',
    ('\u2778 建立数据治理机制', True, CLR['title']),
    '数据质量是数字化审计的生命线\uff1a录错了\u3001漏了\u3001改了\u2014\u2014都会被自动标记',
    '指定数据责任人+数据录入标准+异常数据自动报警',
    '',
    ('\u2779 培养全员的数字化思维', True, CLR['title']),
    '不是IT部门的事\uff0c是每个岗位的事\u3002你在系统里录的每一条数据\uff0c都会被审计追踪',
    '\u201c以前都这么干的\u201d在数字化审计面前不再是免责理由',
], top=emu(1.1), font_size=11, line_spacing=1.1)

# ═══════════════════════════════════
# SLIDE 25: PROACTIVE DEFENSE
# ═══════════════════════════════════
print('Slide 25: Proactive Defense')
s = add_slide(1); add_decor(s)
add_title_box(s, '从\u201c被动整改\u201d到\u201c主动防控\u201d\uff1a管理思维的跃迁', top=emu(0.5), font_size=24)
add_text_box(s, [
    ('传统模式\uff08被动\uff09\uff1a', True, CLR['accent']),
    '审计发现问题 \u2192 写整改报告 \u2192 下次审计再发现新问题 \u2192 再写整改报告',
    '永远在追着问题跑\uff0c永远在\u201c不及格\u2192及格\u2192又不及格\u201d的循环中',
    '',
    ('目标模式\uff08主动\uff09\uff1a', True, CLR['green']),
    '风险自查 \u2192 自动预警 \u2192 即时纠偏 \u2192 审计确认 \u2192 制度优化',
    '问题在萌芽阶段被识别和解决\uff0c审计变成\u201c确认\u201d而非\u201c发现\u201d',
    '',
    ('实现路径\uff1a三件事', True, CLR['title']),
    '',
    ('第一件\uff1a建立部门风险自查清单', True, CLR['dark']),
    '每个业务部门有一张\u201c可能出问题的清单\u201d\u2014\u2014对标今天的13项问题',
    '停车场\uff1a车位变动登记了吗\uff1f手动放行有没有记录\uff1f优惠政策有没有超范围\uff1f',
    '',
    ('第二件\uff1a季度风险扫描', True, CLR['dark']),
    '每季度由第二道防线\uff08风控/合规\uff09牵头\uff0c用\u201c审计视角\u201d扫一遍关键流程',
    '发现问题 \u2192 即时整改 \u2192 不再等到外部审计来',
    '',
    ('第三件\uff1a问题台账动态清零', True, CLR['dark']),
    '建立\u201c问题库\u201d\u2014\u2014每一项问题有编号\u3001有责任人\u3001有整改期限',
    '整改一项销号一项\uff0c超期未销号自动升级到追责',
    '',
    ('一句话\uff1a最好的审计结果是\u201c审不出大问题\u201d\u2014\u2014不是查不到\uff0c是真没问题', True, CLR['accent']),
], top=emu(1.1), font_size=11, line_spacing=1.05)

# ═══════════════════════════════════
# SLIDE 26: ACTION ROADMAP
# ═══════════════════════════════════
print('Slide 26: Roadmap')
s = add_slide(1); add_decor(s)
add_title_box(s, '2026-2027 行动路线图\uff1a从天府广场整改到监管达标', top=emu(0.5), font_size=24)
phases = [
    ('2026\nQ3', '制度补缺\n与整改', '完成13项问题整改\n补建缺失制度\n完成停车位备案变更', CLR['accent']),
    ('2026\nQ4', '流程重构\n与培训', '不相容职务分离落地\n全员制度培训\n台账模板标准化', CLR['amber']),
    ('2027\nQ1', '系统打通\n与数据治理', '四大系统互联互通\n历史数据清洗\n数据责任人指定', CLR['blue']),
    ('2027\nQ2', '机制常态化\n与自检', '季度风险扫描机制运行\n自查清单迭代优化\n问题台账动态清零', CLR['blue']),
    ('2027\nQ3-Q4', '迎接验收\n对标达标', '穿透式监管平台对接\n第三方独立评价\n达到内控二阶标准', CLR['green']),
]
cw, g = emu(2.3), emu(0.1)
for i, (time, title, desc, clr) in enumerate(phases):
    x = emu(0.5) + i*(cw+g)
    add_label(s, time, emu(1.2), x, cw, emu(0.65), bg_color=clr, font_size=11)
    add_text_box(s, [(title, True, clr)], top=emu(2.0), left=x, width=cw, height=emu(0.35), font_size=12)
    s.shapes[-1].text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    add_text_box(s, [desc], top=emu(2.5), left=x+emu(0.05), width=cw-emu(0.1), height=emu(2.0), font_size=10.5, line_spacing=1.15)
add_text_box(s, [
    ('关键节点', True, CLR['title']),
    '2027年底\uff1a四川省国资委对省级国企穿透式监管平台达标验收\u2014\u201460%省属企业必须达标',
    '天府广场项目作为轨道公司核心商业资产\uff0c应作为首批达标单位',
], top=emu(4.8), font_size=13, line_spacing=1.2)

# ═══════════════════════════════════
# SLIDE 27: KEY INSIGHTS
# ═══════════════════════════════════
print('Slide 27: Key Insights')
s = add_slide(1); add_decor(s)
add_title_box(s, '关键启示', top=emu(0.5), font_size=28)
add_text_box(s, [
    ('三句话', True, CLR['title']),
    '',
    '\u2776 内控不是墙上的制度\uff0c是做出来的',
    '    \u2014\u2014天府广场13项问题\uff0c每一项都有制度\uff0c每一项都没执行到位',
    '',
    '\u2777 台账不是纸上的记录\uff0c是出了事能查到的',
    '    \u2014\u2014351次手动放行无记录=出了事无人能答\uff0c这不是侥幸\uff0c是隐患',
    '',
    '\u2778 审批不是流程走过场\uff0c是责任落实到人',
    '    \u2014\u201467人的\u201c三人行\u201d变成\u201c1带多\u201d\uff0c审批松一松\uff0c后果自己扛',
    '',
    '',
    ('四位一体框架\u2014\u2014从\u201c知道\u201d到\u201c做到\u201d的完整逻辑', True, CLR['title']),
    '',
    '1号文 \u2192 用系统减少\u201c人\u201d的随意性       2号文 \u2192 用框架消除\u201c管\u201d的盲区',
    '15号文 \u2192 用执行填补\u201c制\u201d与\u201c行\u201d之间的鸿沟   46号令 \u2192 用问责守住该守的底线',
], top=emu(1.2), font_size=14, line_spacing=1.15)

# ═══════════════════════════════════
# SLIDE 28: SELF-CHECK
# ═══════════════════════════════════
print('Slide 28: Self-Check')
s = add_slide(1); add_decor(s)
add_title_box(s, '合规自查要点\uff08课后作业\uff09', top=emu(0.5), font_size=28)
checks = [
    ('对照1号文', '财务系统打通了吗\uff1f预警自动了吗\uff1f'),
    ('对照2号文', '穿透到底了吗\uff1f资金可追溯了吗\uff1f'),
    ('对照15号文', '内控制度全覆盖了吗\uff1f整改闭环了吗\uff1f'),
    ('对照46号令', '红线全员知晓了吗\uff1f容错边界明确了吗\uff1f'),
]
y = emu(1.4)
for label, question in checks:
    add_label(s, label, y, emu(0.8), emu(2.5), emu(0.4), bg_color=CLR['title'], font_size=13)
    add_text_box(s, [question], top=y+emu(0.05), left=emu(3.5), width=emu(8.5), height=emu(0.4), font_size=16)
    y += emu(0.85)
add_text_box(s, [
    '',
    ('核心原则八字诀', True, CLR['title']),
    '制度有 \u00b7 执行实  |  台账有 \u00b7 信息全  |  流程有 \u00b7 留痕清  |  审批严 \u00b7 追责准',
], top=emu(4.5), font_size=18, line_spacing=1.3)

# ═══════════════════════════════════
# SLIDE 29: CLOSING
# ═══════════════════════════════════
print('Slide 29: Closing')
s = add_slide(1); add_decor(s)
add_title_box(s, '结语', top=emu(0.5), font_size=28)
add_text_box(s, [
    ('送大家三句话', True, CLR['title']),
    '',
    ('\U0001f50d 每一次审计都是一次体检', True, CLR['dark']),
    '体检不是为难你\uff0c是帮你发现隐患\u2014\u2014早发现\uff0c早治疗\uff0c早安心',
    '',
    ('\U0001fa9e 每一个问题都是一面镜子', True, CLR['dark']),
    '照出来的不是你一个人的问题\uff0c是整个管理体系的问题\u2014\u2014改一个点\uff0c堵一个面',
    '',
    ('\U0001f4c8 每一项整改都是一次升级', True, CLR['dark']),
    '把问题改到位了\uff0c你的管理水平就上了一个台阶\u2014\u2014不是应付检查\uff0c是提升自己',
    '',
    '',
    ('今天开始\uff0c从\u201c不会查到我\u201d到\u201c查了我也不怕\u201d', True, CLR['accent']),
    '\u2014\u2014这就是\u201c全员审计风险意识\u201d的真正含义',
], top=emu(1.2), font_size=15, line_spacing=1.2)

# ═══════════════════════════════════
# SLIDE 30: THANK YOU
# ═══════════════════════════════════
print('Slide 30: Thank You')
s = add_slide(1); add_decor(s)
add_title_box(s, '谢谢大家', top=emu(1.5), font_size=48, color=CLR['title'],
              align=PP_ALIGN.CENTER, width=SW-emu(2.0), left=emu(1.0))
tb = add_text_box(s, [
    '\u201c提升全员审计风险意识\u201d\u2014\u2014核心词不是\u201c审计\u201d\uff0c是\u201c全员\u201d',
    '审计团队来查是一年一次\uff0c但风险发生是每时每刻',
    '真正防住风险的人\uff0c是你们每一个业务岗位上的每一个人',
    '',
    '四川融策会计师事务所  |  2026年6月',
    '欢迎会后交流提问',
], top=emu(3.0), font_size=16, color=CLR['dark'], left=emu(1.5), width=SW-emu(3.0))
for p in tb.text_frame.paragraphs:
    p.alignment = PP_ALIGN.CENTER

# ── Save ──
OUT = r'D:\\openclaw-workspace\\output\\v5_expanded.pptx'
print(f'\\nSaving 30 slides to {OUT}...')
prs.save(OUT)
print(f'Saved to {OUT}')
'''

# Write the full script
full = prefix + expanded_part3
with open(dst, 'w', encoding='utf-8') as f:
    f.write(full)

print(f'Wrote {len(full.splitlines())} lines to {dst}')
