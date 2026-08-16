# 审计项目实施服务平台 — 第一版PRD

> 版本：v1.0 | 日期：2026-06-03 | 编制：平头哥 + OpenClaw

## 1. 产品概述

- **产品名称**：审计项目实施服务平台
- **技术栈**：Electron + Vue 3 + Element Plus + SQLite
- **目标用户**：融策内部30人（合伙人/总监/项目经理/助理）
- **核心价值**：审计项目全流程在一个软件里管起来，数据不出本地

## 2. 用户角色与权限

### 角色定义

| 角色 | 说明 | 数据权限 |
|------|------|---------|
| super_admin | 系统管理员 | 全部 |
| partner | 合伙人 | 所有项目CRUD |
| director | 总监 | 所有项目CRUD（不可删除） |
| manager | 项目经理 | 自己项目全部+被分配项目只读 |
| assistant | 审计助理 | 被分配项目的底稿/取证/问题编辑（不可删除项目/报告只读） |
| client | 客户（二期） | 仅看自己报告+整改进度 |

### 功能权限矩阵

| 模块 | partner | director | manager | assistant |
|------|---------|----------|---------|-----------|
| 工作台首页 | ✅ | ✅ | ✅ | ✅ |
| 项目管理 | 全部 | 全部 | 自己的 | 被分配的 |
| 底稿管理 | 全部 | 全部 | 自己的 | 被分配的 |
| 取证单 | 全部 | 全部 | 自己的 | 被分配的 |
| 问题线索 | 全部 | 全部 | 自己的 | 被分配的 |
| 审计报告 | 全部 | 全部 | 自己的 | 只读 |
| 数据分析中心 | ✅ | ✅ | ✅ | 只读 |
| SQL分析 | ✅ | ✅ | ✅ | ✅ |
| 文件管理 | 全部 | 全部 | 自己的 | 被分配的 |
| 知识库 | 全部 | 全部 | 全部 | 只读 |
| 预算成本 | 全部 | 自己的 | 自己的 | 只读工时 |
| AI助手 | ✅ | ✅ | ✅ | ✅ |
| 系统管理 | ✅ | ❌ | ❌ | ❌ |

## 3. 功能模块与优先级

| 模块 | 功能 | 优先级 | 预计工时 |
|------|------|--------|---------|
| M01 系统框架 | Electron+Vue3+SQLite初始化、登录、导航、首页 | P0 | 7天 |
| M02 用户权限 | 用户CRUD+角色+数据权限+菜单权限 | P1 | 6天 |
| M03 项目管理 | 项目列表+CRUD+8Tab详情+状态流转+时间线 | P0 | 9天 |
| M04 底稿管理 | 底稿CRUD+4类型+富文本+关联取证单/问题+导出Word | P0 | 13天 |
| M05 取证单 | 取证单CRUD+4类证据+关联底稿+关联问题 | P0 | 6天 |
| M06 问题线索 | 问题CRUD+风险等级+整改流转+到期提醒 | P0 | 6天 |
| M07 审计报告 | 报告创建+多类型+关联汇总底稿取证+导出Word | P1 | 7天 |
| M08 文件管理 | 文件上传+按项目分类+预览+搜索 | P1 | 5天 |
| M09 数据分析中心 | 数据看板+多源管理+分析结果汇总 | P1 | 9天 |
| M10 SQL分析 | 多数据库连接+SQL编辑器+结果可视化+脚本库 | P0 | 11天 |
| M11 预算成本 | 预算编制+实际归集+工时+报销+对比分析 | P1 | 14天 |
| M12 知识库 | 分类+搜索+资料上传+Obsidian同步+收藏 | P1 | 11天 |
| M13 AI深度集成 | Agent架构+风险扫描+底稿/报告生成+SQL生成 | P1 | 16天 |

**合计P0+P1：约120个工作日（3个月+）**

## 4. 核心数据流

```
立项 → 分配成员 → 编制审计方案 → 执行
                                    ↓
                 ┌──────────────────┼──────────────────┐
                 ↓                  ↓                  ↓
         工作底稿              取证单              SQL分析
                 │                  │                  │
                 └──────────────────┼──────────────────┘
                                    ↓
                             问题线索发现
                                    ↓
                               整改跟踪
                                    ↓
                               生成报告
                                    ↓
                               归档
```

## 5. 页面结构

### 5.1 登录页
用户名+密码+登录按钮

### 5.2 工作台首页
顶部统计卡片（全部/进行中/待整改/已归档）+ 今日待办 + 我的项目列表

### 5.3 项目列表
表格+卡片双视图 + 搜索/筛选 + 新建按钮

### 5.4 项目详情（8Tab）
概览/方案/底稿/取证/问题/SQL/报告/归档

### 5.5 其他页面（详见完整文档）

## 6. AI集成方案

桌面软件通过HTTP调用本地OpenClaw Gateway。Agent执行过程全部记录到ai_runs表，保证可追溯。

## 7. 数据库设计（共20张表）

### 7.1 用户与权限（2张）
- users（11字段）：id, username, password_hash, real_name, role, is_active, created_at, updated_at...
- project_members（5字段）：id, project_id, user_id, role_in_project, assigned_at

### 7.2 项目（2张）
- projects（17字段）：id, name, code, description, audit_type, client_name, status, priority, start_date, end_date, budget_amount, actual_amount, manager_id, created_by, created_at, updated_at, archived_at
- status_logs（7字段）：id, project_id, from_status, to_status, changed_by, reason, created_at

### 7.3 核心业务（7张）
- drafts（11字段）：id, project_id, title, draft_type, content, status, author_id, reviewer_id, review_comment, created_at, updated_at
- draft_evidences：draft_id, evidence_id（关联表）
- draft_issues：draft_id, issue_id（关联表）
- evidences（12字段）：id, project_id, evidence_type, title, description, source, method, collector_id, collected_at, file_path, created_at
- issues（14字段）：id, project_id, title, description, risk_level, amount_involved, status, found_by, found_at, rectification_measure, rectification_person, rectification_deadline, resolved_at, created_at
- issue_evidences：issue_id, evidence_id（关联表）
- reports（10字段）：id, project_id, title, report_type, content, status, prepared_by, approved_by, issue_date, created_at

### 7.4 预算成本（5张）
- budgets（9字段）：id, project_id, total_budget, labor_budget, travel_budget, outsourced_budget, other_budget, notes, created_by
- costs（8字段）：id, project_id, cost_type, amount, description, incurred_by, incurred_at, created_at
- timesheets（7字段）：id, user_id, project_id, date, hours, description, created_at
- travels（13字段）：id, project_id, user_id, departure, destination, start_date, end_date, transport_fee, accommodation_fee, allowance, total, notes

### 7.5 SQL与AI（3张）
- sql_scripts（10字段）：id, project_id, name, description, db_type, sql_content, category, tags, created_by, created_at
- sql_runs（10字段）：id, script_id, project_id, db_connection_id, sql_text, result_json, row_count, duration_ms, error_message, created_at
- ai_runs（9字段）：id, project_id, agent_type, user_message, steps_json, final_result, status, duration_ms, created_at

### 7.6 文件与知识库（建议后续补充）
- files（迁移后补充）
- knowledge（迁移后补充）

## 8. 第一期开发排期（3个月）

| 周 | 工作内容 | 验收标准 |
|----|---------|----------|
| W1 | Electron+Vue3初始化+登录+导航 | 能登录、能看到首页+导航 |
| W2 | 项目列表+卡片/表格+搜索+CRUD | 能创建2个项目+编辑+删除 |
| W3 | 项目详情8Tab框架+概览+状态流转 | 项目状态能流转、有记录 |
| W4 | 底稿CRUD+4类型+富文本+关联项目 | 能创建底稿、富文本编辑 |
| W5 | 取证单CRUD+4类证据+关联底稿/问题 | 能创建取证单、关联到底稿 |
| W6 | 问题线索+风险等级+整改流转+到期提醒 | 问题能发现-整改-销号 |
| W7 | 审计报告+多类型+关联汇总+导出Word | 能出一份报告汇总数据 |
| W8 | 用户角色+数据权限+菜单权限 | 4种角色看到不同内容 |
| W9 | SQL分析：多数据库连接+SQL编辑器 | 能连本地SQLite执行查询 |
| W10 | SQL结果展示+图表+脚本库+文件管理 | 查询结果有表格有图表 |
| W11 | 预算成本：预算编制+实际归集+工时+图表 | 能录入预算和实际 |
| W12 | AI集成初版+知识库初版 | Agent能运行并留下过程 |
