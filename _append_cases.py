import os, sys
sys.stdout.reconfigure(encoding='utf-8')

md = r'C:\Users\Admin\.openclaw\workspace\skills\rongce-gov-audit\SKILL.md'
with open(md, 'r', encoding='utf-8') as f:
    content = f.read()

cases = '''
---

## 审计案例索引库

> 来源：《审计案例》2026年第3册
> 用途：审计前快速匹配同类案例的方法论，审计中查类似的审计思路

### 财政审计案例

| 案例 | 核心技术 | 技能匹配 |
|------|---------|----------|
| 国债资金消费品以旧换新审计追踪 | 政策资金流向追踪 | two-new-audit-checklist |
| 高新区政府采购"李鬼"识别 | 关联关系挖掘+文件痕迹比对 | bid-collusion-audit |
| 货运订单背后虚开发票 | 资金流+物流交叉验证 | audit-sql-patterns |
| 发补贴要明标准 | 补贴标准合规审查 | 两新补贴审计规则 |
| 保险补偿机制变利益瓜分盛宴 | 补偿机制漏洞追踪 | audit-policy-monitor |
| 专项债券100%支出进度真相 | 进度造假定性分析 | audit-data-analyst |
| "爱干净"的公务车 | 三公经费异常检测 | audit-anomaly-detect |

### 民生审计案例

| 案例 | 核心技术 | 技能匹配 |
|------|---------|----------|
| "真假培训"现形记 | 培训真实性多维度核验 | audit-data-quality |
| 骗取养老保险基金 | 重复领取+虚构身份+数据分析 | audit-benford + anomaly-detect |
| 少儿晚会制播分离出租迷局 | 合同实质vs形式分析 | audit-contract-analyze |
| 军休服管用房乱象 | 资产用途合规审查 | eco-responsibility-audit |

### 企业/投资/资源审计案例

| 案例 | 核心技术 | 技能匹配 |
|------|---------|----------|
| 国企加油站"影子"交易员 | 交易员身份+利益闭环分析 | audit-watchdog |
| 国有矿业权"旋转门"交易(200万→3亿) | 资产评估异常+关联交易穿透 | bid-collusion-audit |
| 重点建设项目阻尼器质量审计 | 材料检测+供应链追踪 | audit-sop-master |
| 土地出让收益反哺"账面达标"假象 | 资金归集路径分析 | audit-data-analyst |

### 技术方法参考

| 方法 | 关键技术 | 技能匹配 |
|------|---------|----------|
| GIS+无人机赋能资源环境审计 | 地理信息+遥感数据比对 | 地理分析+数据可视化 |
| 数据分析叫停"车轮腐败" | 加油记录+里程+GPS交叉 | audit-sql-patterns |
| 大数据建模深挖养老服务工单漏洞 | 时间/地点/人员/服务多维度建模 | audit-data-analyst(金川医保同类思路) |

### 审计文书范例

- 农村生活污水治理项目资金筹集及建设运维专项审计调查 — 李传宇、李思琦
- 适用场景：专项资金审计报告结构参考
'''

with open(md, 'w', encoding='utf-8') as f:
    f.write(content.rstrip() + '\n' + cases)

print(f'Updated: {os.path.getsize(md)} chars')
