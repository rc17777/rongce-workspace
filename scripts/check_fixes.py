import os, re
checks = {
    '绩效清算倒扣': (r'月度预发.*60%', '01-薪酬管理制度.md'),
    '年终奖离职折算': (r'中途离职.*按实际在岗月数.*折算', '01-薪酬管理制度.md'),
    'D等不强制': (r'不设强制最低比例', '02-绩效考核管理制度.md'),
    '绩效奖取消表述': (r'取消当年度.*未发放', '22-执业责任追究制度.md'),
    '小项目简化复核': (r'小项目简化规则', '21-三级复核实施细则.md'),
    '毛利率预警': (r'毛利率低于15%', '17-业务承接与合同管理制度.md'),
    '组织角色条款': (r'组织角色与审批替代规则', '05-制度发布与版本管理规范.md'),
    '长期驻场条款': (r'连续驻场15日', '06-财务报销管理制度.md'),
    '有效成本率': (r'有效小时成本率', '37-可分配利润核算细则.md'),
    '部门名称统一': (r'综合管理部.*人力资源部', '03-员工手册.md'),
    '协同奖励披露': (r'隐瞒.*夸大.*如实披露', '35-跨部门协同与交叉营销奖励办法.md'),
    '持证津贴引用': (r'薪酬制度如未列入持证津贴', '11-培训与发展管理制度.md'),
}
d = r'C:\Users\scrccpa\.openclaw\workspace\output\新制度体系'
all_ok = True
for label, (pattern, fname) in checks.items():
    with open(os.path.join(d, fname), encoding='utf-8') as fh:
        c = fh.read()
    found = bool(re.search(pattern, c, re.DOTALL))
    status = "OK" if found else "MISS"
    print(f'  [{status}] {label}')
    if not found:
        all_ok = False
if all_ok:
    print('\nAll fixes verified.')
else:
    print('\nSome fixes missing.')
