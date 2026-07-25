# -*- coding: utf-8 -*-
"""This script generates gen_word_full.py which is the actual Word doc generator.
It avoids escaping issues by building the target script programmatically."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

lines = []

# Add all code as raw strings
lines.extend([
'# -*- coding: utf-8 -*-',
'import os, sys, re',
'sys.stdout.reconfigure(encoding="utf-8")',
'from docx import Document',
'from docx.shared import Pt, Cm, RGBColor',
'from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING',
'from docx.oxml.ns import qn, nsdecls',
'from docx.oxml import parse_xml',
'',
"SRC = r'C:\\Users\\scrccpa\\.openclaw\\workspace\\output\\新制度体系'",
'DESK = os.path.join(os.path.expanduser("~"), "Desktop")',
'',
"FH = '黑体'",
"FF = '仿宋'",
"FS = '宋体'",
'SE = Pt(22)',
'SS = Pt(16)',
'SI = Pt(14)',
'SW = Pt(10.5)',
'',
])

# DOCS definition
docs_code = 'DOCS = ['
docs_code += '\n    ("00","00-制度体系架构.md","RC-SYS-000","制度体系架构","总纲"),'
docs_code += '\n    ("01","01-薪酬管理制度.md","RC-HR-001","薪酬管理制度","人力资源"),'
docs_code += '\n    ("02","02-绩效考核管理制度.md","RC-HR-002","绩效考核管理制度","人力资源"),'
docs_code += '\n    ("03","03-员工手册.md","RC-HR-003","员工手册","人力资源"),'
docs_code += '\n    ("04","04-项目管理规范.md","RC-BIZ-001","项目管理规范","业务质控"),'
docs_code += '\n    ("05","05-制度发布与版本管理规范.md","RC-ADM-006","制度发布与版本管理规范","行政综合"),'
docs_code += '\n    ("06","06-财务报销管理制度.md","RC-FIN-001","财务报销管理制度","财务管理"),'
docs_code += '\n    ("07","07-审计质量控制制度.md","RC-QC-001","审计质量控制制度","业务质控"),'
docs_code += '\n    ("08","08-造价咨询质量控制制度.md","RC-QC-002","造价咨询质量控制制度","业务质控"),'
docs_code += '\n    ("09","09-股东会议事规则.md","RC-GOV-003","股东会议事规则","行政综合"),'
docs_code += '\n    ("10","10-招聘与入职管理制度.md","RC-HR-004","招聘与入职管理制度","人力资源"),'
docs_code += '\n    ("11","11-培训与发展管理制度.md","RC-HR-005","培训与发展管理制度","人力资源"),'
docs_code += '\n    ("12","12-职级晋升管理制度.md","RC-HR-006","职级晋升管理制度","人力资源"),'
docs_code += '\n    ("13","13-项目收入确认与回款管理制度.md","RC-FIN-002","项目收入确认与回款管理制度","财务管理"),'
docs_code += '\n    ("14","14-预算管理制度.md","RC-FIN-003","预算管理制度","财务管理"),'
docs_code += '\n    ("15","15-资金管理制度.md","RC-FIN-004","资金管理制度","财务管理"),'
docs_code += '\n    ("16","16-固定资产管理制度.md","RC-FIN-005","固定资产管理制度","财务管理"),'
docs_code += '\n    ("17","17-业务承接与合同管理制度.md","RC-BIZ-002","业务承接与合同管理制度","业务质控"),'
docs_code += '\n    ("18","18-客户关系管理制度.md","RC-BIZ-003","客户关系管理制度","业务质控"),'
docs_code += '\n    ("19","19-业务分包管理制度.md","RC-BIZ-004","业务分包管理制度","业务质控"),'
docs_code += '\n    ("20","20-投标管理制度.md","RC-BIZ-005","投标管理制度","业务质控"),'
docs_code += '\n    ("21","21-三级复核实施细则.md","RC-QC-003","三级复核实施细则","业务质控"),'
docs_code += '\n    ("22","22-执业责任追究制度.md","RC-QC-004","执业责任追究制度","业务质控"),'
docs_code += '\n    ("23","23-信息安全与保密管理制度.md","RC-ADM-002","信息安全与保密管理制度","行政综合"),'
docs_code += '\n    ("24","24-印章与证照管理制度.md","RC-ADM-004","印章与证照管理制度","行政综合"),'
docs_code += '\n    ("25","25-档案管理制度.md","RC-ADM-005","档案管理制度","行政综合"),'
docs_code += '\n    ("26","26-公司章程-会计师事务所.md","RC-GOV-001","公司章程-会计师事务所","行政综合"),'
docs_code += '\n    ("27","27-公司章程-工程咨询公司.md","RC-GOV-002","公司章程-工程咨询公司","行政综合"),'
docs_code += '\n    ("28","28-办公场所管理制度.md","RC-ADM-001","办公场所管理制度","行政综合"),'
docs_code += '\n    ("29","29-采购管理制度.md","RC-ADM-003","采购管理制度","行政综合"),'
docs_code += '\n    ("30","30-数智化建设管理制度.md","RC-SPL-001","数智化建设管理制度","行政综合"),'
docs_code += '\n    ("31","31-业务拓展与创新管理制度.md","RC-SPL-002","业务拓展与创新管理制度","行政综合"),'
docs_code += '\n    ("32","32-风险管理制度.md","RC-SPL-003","风险管理制度","行政综合"),'
docs_code += '\n    ("33","33-党建工作制度.md","RC-SPL-004","党建工作制度","行政综合"),'
docs_code += '\n]'
lines.append(docs_code)

# ASMS
lines.append('ASMS = {')
lines.append('    "人力资源篇": ["00","01","02","03","10","11","12"],')
lines.append('    "财务管理篇": ["06","13","14","15","16"],')
lines.append('    "业务质控篇": ["04","07","08","17","18","19","20","21","22"],')
lines.append('    "行政综合篇": ["05","09","23","24","25","26","27","28","29","30","31","32","33"],')
lines.append('}')

with open(r'C:\Users\scrccpa\.openclaw\workspace\gen_word_full.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print('Part 1: header + data structures written')
