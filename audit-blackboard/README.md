# 融策多Agent审计平台

> v2.0 | Blackboard架构 | 7Agent + 碰撞引擎 + 12业务线

## 你怎么用？

三步，每步一行命令。

```
# 1. 启动项目（一键创建+准备任务）
python launch.py "校服采购审计" --type 招投标

# 2. 对融策右护卫说："开始审计 校服采购审计"
#    → 右护卫自动：读取spawn plan → sessions_spawn派出Agent → 等待完成

# 3. 碰撞分析
python orchestrate.py collect 校服采购审计

# 4. 看报告
python orchestrate.py report 校服采购审计
```

**核心分工：** 你启动项目，我派出Agent，你收报告。

## 支持的12种业务

| 简称 | 业务线 | 必选Agent |
|------|--------|:---:|
| 经责 | 经济责任审计 | 数据+合同+法规+底稿+报告+复核 |
| 收支 | 收支审计 | 数据+法规+底稿+报告+复核 |
| 预算 | 预算执行审计 | 数据+法规+底稿+报告+复核 |
| 专项 | 专项审计 | 全7Agent |
| 往来款 | 往来款清理 | 数据+底稿+报告+复核 |
| 招投标 | 招投标审计 | 招投标+法规+底稿+报告+复核 |
| 国企 | 国企审计 | 全7Agent |
| 工程 | 工程审计 | 全7Agent |
| 绩效 | 绩效评价 | 数据+法规+底稿+报告+复核 |
| 补贴 | 政府补贴 | 数据+合同+法规+底稿+报告+复核 |
| 能源 | 能源审计 | 数据+法规+底稿+报告+复核 |
| 成本 | 成本效益审计 | 数据+合同+法规+底稿+报告+复核 |

## 7个Agent各干什么

| Agent | 中文名 | 职责 |
|-------|-------|------|
| data_scout | 数据侦察兵 | 扫序时账→找财务异常/资金挪用/数据异常 |
| contract_hound | 合同猎犬 | 扫合同→找缺条款/先付款后签/虚增成本 |
| bid_hunter | 招投标猎手 | 扫投标文件→围标串标检测（L1~L11） |
| law_inspector | 法规检察官 | 对照法规→违规定性+引用条款 |
| workpaper_crafter | 底稿工匠 | 汇总发现→生成审计底稿 | 
| report_writer | 报告笔杆子 | 起草审计报告 |
| review_sentinel | 复核哨兵 | 复核底稿+报告（15维度检查） |

## 怎么放真实数据？

子Agent能读workspace内的文件。数据放这里：

```
audit-blackboard/projects/<项目名>/raw_data/
    ├── 序时账.xlsx
    ├── 合同台账.xlsx
    ├── 投标文件/  (文件夹)
    └── ...
```

启动前把数据丢进去，Agent会自动读取。

## 成果示例

上次跑「校服采购审计v2」：
- 3个Agent并行，~1分钟完成
- 产出16条发现（高26/中6）
- 碰撞引擎产生15条交叉线索
- 🔴 A服饰被3Agent同时标记 → 系统性围标嫌疑
- 🔴 合同HT-2023-045被3Agent标记 → 利益输送高危

## 目录结构

```
audit-blackboard/
├── launch.py              ← 一键启动（你用这个）
├── orchestrate.py         ← 调度中枢（我调用）
├── agent_specs/           ← 7个Agent的规格定义
├── schemas/               ← 发现格式统一标准
└── projects/              ← 每个审计项目一个目录
    └── <项目名>/
        ├── raw_data/      ← 原始数据（序时账/合同/投标文件）
        ├── tasks/         ← Agent任务文件
        ├── findings/      ← 各Agent发现（JSON）
        ├── collision/     ← 交叉碰撞结果
        ├── workpapers/    ← 审计底稿
        ├── output/        ← 报告
        └── status.json    ← 进度看板
```

## 命令速查

```bash
# 创建项目
python launch.py "项目名" --type 业务简称

# 指定Agent（可选）
python orchestrate.py prepare "项目名" --agents data,contract,bid

# 收集+碰撞
python orchestrate.py collect "项目名"

# 看进度
python orchestrate.py status "项目名"

# 看报告
python orchestrate.py report "项目名"
```
