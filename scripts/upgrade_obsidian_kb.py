# -*- coding: utf-8 -*-
"""融策知识库/Obsidian升级：断链、元数据、业务驾驶舱、工程咨询、项目回流。"""
from pathlib import Path
from datetime import date
import json, re

VAULT=Path(r'D:\openclaw-workspace\obsidian-vault')
WS=Path(r'C:\Users\scrccpa\.openclaw\workspace')
TODAY=str(date.today())

def write(rel, text):
    p=VAULT/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text.strip()+"\n",encoding='utf-8'); return p

def fm(kind,title,line,stage='全流程',status='active'):
    return f'''---
type: {kind}
title: "{title}"
business_line: "{line}"
scene: "{line}"
audit_stage: "{stage}"
document_type: "{kind}"
keywords: [{line}, 工作流, 融策]
source: "融策自建"
source_date: {TODAY}
effective_date: {TODAY}
validity: "内部有效"
evidence_level: "工作指引"
source_path: ""
status: "{status}"
updated: {TODAY}
---'''

# 1. 创建原来被链接但不存在的索引
indexes={
'04-法规案例库/核心法规/_index.md':('核心法规','法规索引'),
'04-法规案例库/问题定性依据/_index.md':('问题定性依据','定性索引'),
'04-法规案例库/典型案例/_index.md':('典型案例','案例索引'),
}
for rel,(title,kind) in indexes.items():
    write(rel,f'''{fm(kind,title,'通用')}
# {title}

```dataview
TABLE business_line AS 业务线, validity AS 有效性, updated AS 更新时间
FROM "{str(Path(rel).parent).replace(chr(92),'/')}"
WHERE file.name != "_index"
SORT updated DESC
```
''')

# 2. 元数据标准与来源台账
write('00-系统/元数据标准.md',f'''{fm('系统标准','融策知识元数据标准','通用')}
# 融策知识元数据标准

## 最低必填字段

| 字段 | 含义 | 示例 |
|---|---|---|
| type | 卡片类型 | audit_rule / regulation / case / project |
| business_line | 业务线 | 采购招投标审计 |
| audit_stage | 环节 | 投标/审前/现场/报告/整改 |
| document_type | 文档类型 | 法规/案例/模板/规则/底稿 |
| validity | 有效性 | 现行有效/已废止/待核验/内部有效 |
| evidence_level | 证据等级 | 法定依据/权威案例/工作指引/经验线索 |
| source_path | 原文路径 | knowledge/references/xxx.md |
| updated | 最近更新 | YYYY-MM-DD |

## 唯一数据源原则

- 原文、OCR、采集资料只存 `knowledge/`。
- Obsidian只存项目页、业务驾驶舱、知识卡、规则、模板和整改记录。
- Obsidian卡片通过 `source_path` 指向原文，不复制长篇全文。
- 正式定性必须回看原文并核对法规有效性。
''')
write('00-系统/知识源台账.md',f'''{fm('数据源台账','知识源台账','通用')}
# 知识源台账

| 数据源 | 当前口径 | 用途 | 是否入RAG | 更新方式 |
|---|---:|---|---|---|
| workspace/knowledge | 355 Markdown（2026-07-11扫描） | 机器知识底座 | 是 | 情报采集+人工沉淀 |
| Obsidian Vault | 升级前56 Markdown | 人工业务控制台 | 应纳入 | 驾驶舱+项目回流 |
| D:/杂志资料 | 外部OCR资料 | 行业案例来源 | 待核验 | 批量OCR |
| audit-blackboard/projects | 项目发现和底稿 | 项目执行数据 | 选择性脱敏入库 | 项目结束回流 |

> 每次RAG重建应记录：来源、文件数、chunk数、时间、基线测试结果。不同来源数量不得混称为“知识库篇数”。
''')

# 3. 业务驾驶舱
business={
'采购招投标审计':{
'重点':['采购方式与程序合规','资格条件和评分办法是否排他','投标文件雷同及电子痕迹','评委打分偏离','合同与招标承诺一致性'],
'资料':['采购计划及预算','采购需求与论证','招标文件及澄清','所有投标文件原件','开评标记录及逐项评分','电子交易平台IP/MAC/上传日志','中标合同及验收付款资料'],
'rules':['报价规律与异常低价','IP/MAC/设备指纹一致','投标文本相似','图片与资源哈希','文档元数据','工商关联及保证金资金链','评委打分偏离','历史陪标与中标模式'],
'outputs':['资格条件审查表','评分点合规审查表','围标串标疑点清单','现场核查任务单','问题底稿','采购审计报告']},
'经济责任审计':{
'重点':['重大政策贯彻','重大经济决策','财政财务收支','资产资源管理','内部控制','廉洁从业与责任界定'],
'资料':['任职文件和职责分工','任期工作总结','三重一大制度及会议纪要','预算决算和财务账套','重大项目与合同台账','资产与债权债务台账','历次审计及整改资料'],
'rules':['任期前后指标对比','重大决策程序闭环','异常支出与任期交界点','资产损失与长期挂账','违规担保借款投资','个人责任与集体责任区分'],
'outputs':['审前调查表','任期事项清单','重大决策核验表','财政财务问题表','责任界定底稿','经责审计报告']},
'绩效评价':{
'重点':['决策立项','过程管理','成本控制','产出数量质量时效','经济社会生态效益','满意度与可持续性'],
'资料':['项目申报及立项依据','绩效目标申报表','预算及执行数据','合同验收和产出资料','服务对象名册','满意度调查资料','政策制度与行业标准'],
'rules':['绩效目标可衡量性','预算执行偏差','投入产出效率','成本偏离','产出真实性与覆盖率','满意度样本有效性','长期效益和可持续性'],
'outputs':['资料清单','绩效指标体系','基础数据表','评分底稿','问题清单','绩效评价报告']},
}

def dashboard(name,cfg,root='02-主题数据库'):
    bullets=lambda xs:'\n'.join('- '+x for x in xs)
    base=f'{root}/{name}'
    write(f'{base}/项目启动.md',f'''{fm('工作指引',name+'项目启动',name,'审前')}
# {name}｜项目启动

## 五项输入
项目名称、服务对象、工作范围、期间、交付期限。

## 自动装配成果
1. 项目任务书；2. 审前调查清单；3. 资料需求清单；4. 风险画像；5. 工作分工；6. 访谈提纲；7. 进度计划。

## 启动门槛
- [ ] 范围和边界确认
- [ ] 资料清单发出
- [ ] 数据安全与脱敏要求确认
- [ ] 关键联系人确认
- [ ] 项目风险和复核层级确定
''')
    write(f'{base}/资料清单.md',f'''{fm('资料清单',name+'资料清单',name,'审前')}
# {name}｜资料清单
{bullets(cfg['资料'])}

## 资料验收字段
文件名称、所属期间、提供部门、提供时间、完整性、缺失说明、补充期限。
''')
    write(f'{base}/风险与识别规则.md',f'''{fm('audit_rule_index',name+'风险与识别规则',name,'现场')}
# {name}｜风险与识别规则

## 核心审计重点
{bullets(cfg['重点'])}

## 首批规则
{bullets(cfg['rules'])}

## 每条规则必须具备
数据字段、判断逻辑、阈值、误报条件、核查步骤、法规依据、输出字段。
''')
    write(f'{base}/现场核查与访谈.md',f'''{fm('工作指引',name+'现场核查与访谈',name,'现场')}
# {name}｜现场核查与访谈

## 核查任务单
| 疑点 | 涉及主体 | 数据证据 | 待补资料 | 访谈对象 | 核查结论 |
|---|---|---|---|---|---|

## 访谈原则
先事实、后原因；先开放、后封闭；同一事项至少采用数据、文件、人员三角印证。
''')
    write(f'{base}/底稿报告与复核.md',f'''{fm('工作指引',name+'底稿报告与复核',name,'报告')}
# {name}｜底稿、报告与复核

## 标准成果
{bullets(cfg['outputs'])}

## 强制复核
- [ ] 每项关键金额重新计算
- [ ] 数据来源、计算方法、交叉验证结果齐全
- [ ] 事实—证据—法规—责任—建议闭环
- [ ] 报告、附表、取证单、底稿一致
- [ ] 法规现行有效，引用条款准确
''')
    write(f'{base}/_index.md',f'''{fm('业务驾驶舱',name+'驾驶舱',name)}
# {name}｜业务驾驶舱

> 从项目启动到报告整改的可执行入口，不是文章目录。

## 立即开工
- [[{base}/项目启动|① 项目启动]]
- [[{base}/资料清单|② 资料清单]]
- [[{base}/风险与识别规则|③ 风险与识别规则]]
- [[{base}/现场核查与访谈|④ 现场核查与访谈]]
- [[{base}/底稿报告与复核|⑤ 底稿报告与复核]]

## 项目与知识动态视图
```dataview
TABLE audit_stage AS 环节, document_type AS 类型, updated AS 更新
FROM "{base}"
WHERE file.name != "_index"
SORT audit_stage ASC
```

## 场景入口
- [[场景/场景-{name}]]
''')

for n,c in business.items(): dashboard(n,c)

# 4. 工程咨询四场景
engineering={
'预算编制':{
'重点':['图纸与范围完整性','工程量计算准确性','定额套用','材料设备价格','措施费与规费税金','控制价风险'],
'资料':['施工图及设计说明','地勘资料','招标范围及技术标准','工程量清单','计价依据和取费文件','材料设备询价资料','同类项目指标'],
'rules':['图纸清单漏项','重复计量','定额错套高套','材料价异常','措施费重复','暂估价不合理'],
'outputs':['编制说明','工程量清单','招标控制价','材料询价记录','指标分析表','复核记录']},
'财政评审':{
'重点':['项目建设必要性','投资估算合理性','工程量和单价','费用边界','财政资金合规','评审核减依据'],
'资料':['立项批复','概算批复','施工图预算','资金来源文件','清单计价文件','询价和市场价格','项目特殊情况说明'],
'rules':['超概算风险','建设内容越界','工程量虚增','材料价偏高','费用重复计取','无依据暂列暂估'],
'outputs':['评审意见书','核增核减表','争议事项表','取费复核表','评审底稿','评审报告']},
'工程结算':{
'重点':['合同计价条款','竣工图与现场','变更签证','工程量','材料价差','索赔奖罚','付款扣款'],
'资料':['施工合同及补充协议','招投标和清单文件','竣工图','变更签证','隐蔽验收','材料认价','付款资料','竣工验收资料'],
'rules':['竣工图与现场不符','签证手续不全','工程量重复','变更价款超合同','材料调差错误','应扣未扣'],
'outputs':['结算审核报告','工程量核对表','价差审核表','签证审核表','争议事项表','核减明细']},
'全过程工程咨询':{
'重点':['投资决策','设计限额','招标采购','合同管理','进度成本质量','变更索赔','竣工移交'],
'资料':['立项及可研','设计成果','招标采购文件','合同台账','进度计划','投资动态控制表','变更索赔台账','验收移交资料'],
'rules':['决策依据不足','设计超限额','招标合同脱节','进度成本偏差','变更失控','支付超进度','责任边界不清'],
'outputs':['项目管理策划','投资控制月报','风险清单','合同台账','变更台账','阶段咨询报告']},
}
for n,c in engineering.items(): dashboard(n,c,'工程咨询')

write('工程咨询/_index.md',f'''{fm('业务总览','工程咨询业务驾驶舱','工程咨询')}
# 工程咨询业务驾驶舱

- [[工程咨询/预算编制/_index|预算编制]]
- [[工程咨询/财政评审/_index|财政评审]]
- [[工程咨询/工程结算/_index|工程结算]]
- [[工程咨询/全过程工程咨询/_index|全过程工程咨询]]

```dataview
TABLE business_line AS 业务线, audit_stage AS 环节, updated AS 更新
FROM "工程咨询"
WHERE type != "业务总览"
SORT business_line ASC
```
''')

# 5. 项目闭环模板与控制台
write('_templates/tpl-项目主页.md',f'''{fm('project','项目名称','业务线','审前')}
# 项目名称

## 基本信息
- 委托单位：
- 被审计/服务对象：
- 业务类型：
- 工作期间：
- 计划交付日：
- 项目负责人：
- 复核负责人：

## 项目进度
- [ ] 启动
- [ ] 资料接收
- [ ] 数据分析
- [ ] 现场核查
- [ ] 底稿
- [ ] 报告
- [ ] 整改/归档

## 关键链接
- 资料清单：
- 风险规则：
- 问题台账：
- 底稿目录：
- 报告版本：
- 项目复盘：
''')
write('_templates/tpl-项目复盘与知识回流.md',f'''{fm('project_review','项目复盘','业务线','归档')}
# 项目复盘与知识回流

## 项目成果
- 项目：
- 业务线：
- 交付物：
- 关键发现数量：
- 报告复核等级：

## 候选知识
### 新问题
### 新规则
### 新法规/案例
### 误报与排除条件
### 可复用模板

## 回流验收
- [ ] 已脱敏
- [ ] 有事实和证据来源
- [ ] 法规有效性已核验
- [ ] 规则字段与阈值明确
- [ ] 监工Agent已复核
- [ ] 已写入knowledge并更新对应驾驶舱
''')
write('00-系统/项目控制台.base','''filters:
  and:
    - 'type == "project"'
    - 'file.ext == "md"'
formulas:
  days_to_due: 'if(due_date, (date(due_date) - today()).days, "")'
properties:
  business_line:
    displayName: "业务线"
  status:
    displayName: "状态"
  due_date:
    displayName: "交付日"
  formula.days_to_due:
    displayName: "距交付天数"
views:
  - type: table
    name: "进行中项目"
    filters:
      and:
        - 'status != "archived"'
    order:
      - file.name
      - business_line
      - status
      - due_date
      - formula.days_to_due
  - type: table
    name: "已归档"
    filters:
      and:
        - 'status == "archived"'
    order:
      - file.name
      - business_line
      - updated
''')

# 修复 [[目录/]] 为 [[目录/_index]]，只在目标_index存在时修改
for p in VAULT.rglob('*.md'):
    s=p.read_text(encoding='utf-8',errors='ignore')
    def repl(m):
        target=m.group(1).rstrip('/')
        return f'[[{target}/_index{m.group(2) or ""}]]' if (VAULT/target/'_index.md').exists() else m.group(0)
    ns=re.sub(r'\[\[([^\]|#]+/)(\|[^\]]+)?\]\]', repl, s)
    if ns!=s:p.write_text(ns,encoding='utf-8')

# 更新首页
index=f'''---
type: MOC
title: 融策业务知识控制台
updated: {TODAY}
---
# 🧠 融策业务知识控制台

## 🚀 高频业务直接开工
- [[02-主题数据库/采购招投标审计/_index|采购招投标审计]]
- [[02-主题数据库/经济责任审计/_index|经济责任审计]]
- [[02-主题数据库/绩效评价/_index|绩效评价]]
- [[工程咨询/_index|工程咨询四场景]]

## 🗂 项目管理
- [[01-项目对象库/_index|项目对象库]]
- [[00-系统/知识源台账|知识源台账]]
- [[00-系统/元数据标准|元数据标准]]
- ![[00-系统/项目控制台.base]]

## 📚 五大知识库
- [[01-项目对象库/_index|① 项目对象库：审谁]]
- [[02-主题数据库/_index|② 主题数据库：审什么]]
- [[03-操作指引库/_index|③ 操作指引库：怎么审]]
- [[04-法规案例库/_index|④ 法规案例库：凭什么判]]
- [[05-审计整改库/_index|⑤ 审计整改库：审完怎么办]]

## 🔄 知识闭环
外部资料进入knowledge原料库 → AI摘要与分类 → Obsidian驾驶舱 → 项目执行 → 项目复盘 → 脱敏回流。
'''
write('index.md',index)
print(json.dumps({'vault':str(VAULT),'generated':True},ensure_ascii=False))
