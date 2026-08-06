# 招投标审计 — 算法→数据格式映射手册
# ====================================
# 融策审盾 v5.0 | bid_hunter 18个算法 | 2026-08-06

"""
═══════════════════════════════════════════════════════════
  招投标审计数据采集清单 & 算法对接手册
  适用场景: 政府采购/工程招标/货物服务采购/医疗设备
═══════════════════════════════════════════════════════════

一句话说明:
  收集以下7张表的数据 → 18个算法自动检测围标串标/虚假材料/价格偏离

【核心数据表】
  1. 投标人基本信息表     → 关联方检测/集中度分析
  2. 投标项目汇总表       → 围标模式/轮庄检测
  3. 投标文件中标情况表   → 集中度/轮庄/异常价格
  4. 电子投标元数据表     → 特征码/暗标记号/文件指纹
  5. 投标文件文本内容     → 文本雷同/跨年重复/错别字比对
  6. 供应商资质材料表     → 虚假认证/检测报告/业绩造假
  7. 资金流向表           → 陪标费/回扣/资金回流
"""

# ============================================================
# 表1: 投标人基本信息 — 对接关联方/集中度/空壳检测
# ============================================================
BIDDER_INFO_SCHEMA = {
    "table_name": "t_bidder_info",
    "description": "每个投标人的工商信息和关键人员",
    "required_fields": {
        "bidder_id":       "string  — 统一社会信用代码(18位)",
        "bidder_name":     "string  — 公司全称",
        "legal_person":    "string  — 法定代表人姓名",
        "reg_address":     "string  — 注册地址(精确到门牌号)",
        "reg_capital":     "decimal — 注册资本(万元)",
        "est_date":        "date    — 成立日期",
        "shareholders":    "json    — 股东列表 [{name,ratio,invest_date}]",
        "key_personnel":   "json    — 董监高 [{name,position,id_number}]",
        "contact_phone":   "string  — 企业联系电话",
        "contact_email":   "string  — 企业联系邮箱",
        "business_scope":  "string  — 经营范围",
        "industry_code":   "string  — 国民经济行业分类代码",
    },
    "optional_fields": {
        "website":         "string  — 官网",
        "branch_count":    "int     — 分支机构数量",
        "employee_count":  "int     — 参保人数",
        "parent_company":  "string  — 母公司",
    },
    "mapped_algorithms": [
        "PROC-RELATED-001: 关联方13维检测 → legal_person, shareholders, key_personnel, reg_address, contact_phone, contact_email",
        "PROC-CONCEN-001: 供应商集中度 → bidder_id, bid_amount(来自中标表)",
        "PROC2-004: 无介质围标团伙 → bidder_id列表, 共同投标记录",
        "VENDOR-VERIFY-001: 供应商虚假三查 → 对接资质材料表",
    ],
    "detection_signals": [
        "① 两家投标人 share_phone = true → 关联信号",
        "② 注册地址前N个字符完全相同 → 同址办公",
        "③ 法定代表人为同一人 → 直接关联",
        "④ 股东交叉持股 > 20% → 隐蔽关联",
        "⑤ 成立时间在项目公告后 → 空壳公司",
        "⑥ 注册资本/参保人数 = 0 → 皮包公司",
    ],
}

# ============================================================
# 表2: 投标项目汇总 — 对接围标模式/陪标/轮庄
# ============================================================
BID_PROJECT_SCHEMA = {
    "table_name": "t_bid_project",
    "description": "每个招标项目的完整信息",
    "required_fields": {
        "project_id":      "string  — 项目编号/政府采购编号",
        "project_name":    "string  — 项目名称",
        "procurement_type":"string  — 采购方式(公开招标/竞争性磋商/询价/单一来源)",
        "procurement_org": "string  — 采购人单位名称",
        "budget_amount":   "decimal — 预算金额(元)",
        "bid_open_date":   "date    — 开标日期",
        "notice_date":     "date    — 公告日期",
        "evaluation_method":"string — 评标办法(综合评分/最低价/性价比)",
        "bidder_count":    "int     — 投标人数",
        "winner_id":       "string  — 中标人ID",
        "winner_name":     "string  — 中标人名称",
        "win_amount":      "decimal — 中标金额(元)",
    },
    "optional_fields": {
        "bid_sections":    "json   — 标段信息 [{section_id, name, winner_id, amount}]",
        "re_bid_flag":     "bool   — 是否为二次招标/废标重招",
        "appeal_record":   "bool   — 是否有质疑投诉记录",
    },
    "mapped_algorithms": [
        "BID-PATTERN-005: Apriori围标模式 → bidder_id组合, project_id, win_status",
        "BID-ROTATE-001: 互惠轮庄 → 跨项目 中标人/投标人 旋转矩阵",
        "INVEST2-001: 四码围标 → 对接元数据表 投标人×项目 交叉",
        "PROC2-004: 无介质围标 → 共同投标频次, 杰卡德相似系数",
    ],
    "detection_signals": [
        "① A→B→C→A 跨项目轮流中标 → 轮庄",
        "② 中标率差异(>=3家轮流)：'陪标99%败 + 主标80%胜'",
        "③ 废标后唯一投标人中标 → 围标",
        "④ 中标价/预算价 > 95% → 价格异常接近预算",
    ],
}

# ============================================================
# 表3: 电子投标元数据 — 对接硬件指纹/暗标记号
# ============================================================
BID_METADATA_SCHEMA = {
    "table_name": "t_bid_metadata",
    "description": "每个投标文件的电子指纹 — 这是近年围标检测最有效的维度",
    "required_fields": {
        "bid_id":          "string  — 投标记录ID",
        "project_id":      "string  — 关联项目ID",
        "bidder_id":       "string  — 投标人ID",
        "file_md5":        "string  — 投标文件MD5哈希(整体)",
        "file_sha256":     "string  — SHA256哈希",
        "submit_ip":       "string  — 投标提交IP",
        "submit_time":     "datetime— 投标提交时间",
        "upload_mac":      "string  — 上传设备MAC地址(电子招投标平台可获取)",
        "os_info":         "string  — 操作系统版本",
        "browser_info":    "string  — 浏览器User-Agent",
        "cpu_serial":      "string  — CPU序列号(如可用)",
        "disk_serial":     "string  — 硬盘序列号(如可用)",
        "doc_author":      "string  — 文档作者(Word属性)",
        "doc_creator":     "string  — 文档创建者",
        "doc_create_time": "datetime— 文档创建时间",
        "doc_modify_time": "datetime— 最后修改时间",
        "doc_edit_minutes":"int     — 文档编辑总时长(分钟)",
        "doc_revision_count":"int   — 文档修订次数",
    },
    "optional_fields": {
        "cert_serial":     "string  — 数字证书序列号",
        "sign_time":       "datetime— 签名时间",
        "machine_code":    "string  — 机器码(平台生成)",
    },
    "mapped_algorithms": [
        "INVEST-001: 电子投标特征码检测 → IP, MAC, 文档作者, 创建者, 机器码",
        "INVEST2-001: 四码串标 → IP, MAC, CPU_ID, disk_serial",
        "BID-DARKMARK-001: 暗标记号 → doc_author, doc_creator, doc_create_time, doc_revision_count",
        "BUDGET-019: 跨年度虚假资料 → submit_ip, doc_create_time, 跨项目比对",
    ],
    "detection_signals": [
        "① 同一IP提交多家标书 → 串标铁证(但VPN时代需结合其他维度)",
        "② 同一MAC地址 → 同一台电脑",
        "③ 同一CPU序列号/硬盘SN → 同一物理机器",
        "④ 文档作者相同 → 同一人制作多份标书",
        "⑤ 文档创建时间 < 公告发布时间 → 提前获取信息",
        "⑥ 文档修订次数为0 → 模板文件, 非认真响应",
    ],
}

# ============================================================
# 表4: 投标文件文本内容 — 对接文本雷同/错别字比对
# ============================================================
BID_TEXT_SCHEMA = {
    "table_name": "t_bid_text",
    "description": "投标文件文本内容(技术方案/商务响应/实施方案等)",
    "required_fields": {
        "bid_id":          "string  — 投标记录ID",
        "project_id":      "string  — 项目ID",
        "bidder_id":       "string  — 投标人ID",
        "section":         "string  — 章节(技术方案/商务条款偏离表/实施方案/售后服务)",
        "text_content":    "text    — 章节全文",
        "word_count":      "int     — 字数",
    },
    "mapped_algorithms": [
        "PROC2-001: 跨年度文本雷同 → text_content, TF-IDF向量, 错别字位置比对",
        "BID-PATTERN-005: Apriori关联规则(文本相似度维度)",
        "PROC2-004: 杰卡德相似系数 → 分词后集合交集/并集",
    ],
    "detection_signals": [
        "① 两家标书相似度 > 70% → 文本雷同(阈值可调)",
        "② 错别字出现在了同样的位置 → 复制粘贴证据",
        "③ 跨年度同一投标人 技术方案完全一样 → 套用旧模板",
        "④ 两家报价清单 错位完全一致 → 共同编制",
    ],
}

# ============================================================
# 表5: 供应商资质材料 — 对接虚假认证/检测报告/业绩造假
# ============================================================
VENDOR_CREDENTIAL_SCHEMA = {
    "table_name": "t_vendor_credential",
    "description": "投标人提交的资质证书/认证/检测报告/合同业绩",
    "required_fields": {
        "bidder_id":       "string  — 投标人ID",
        "project_id":      "string  — 项目ID",
        "cert_type":       "string  — 证书类型(ISO9001/CCC/CMA检测报告/专利/软著/业绩合同)",
        "cert_number":     "string  — 证书编号",
        "issuing_body":    "string  — 发证机构",
        "issue_date":      "date    — 发证日期",
        "expire_date":     "date    — 有效期至",
        "cert_scope":      "string  — 认证范围",
        "cert_file":       "binary  — 证书扫描件(OCR提取文本)",
    },
    "optional_fields": {
        "verify_url":      "string  — 官方查询网址",
        "verify_result":   "string  — 官网查询结果",
        "contract_party":  "string  — 业绩合同对方名称",
        "contract_amount": "decimal — 合同金额",
        "contract_date":   "date    — 合同签订日期",
    },
    "mapped_algorithms": [
        "VENDOR-VERIFY-001: 三查核验 → cert_number vs 官网查询, 检测报告内容比对",
        "PROC-FAKE-001: 虚假材料识别 → cert_number, issuing_body, issue_date, expire_date",
        "PROC2-001: 跨年度重复套用 → cert_file, 伪造证书编号模式",
    ],
    "detection_signals": [
        "① 证书编号在官网查询不到 → 假证",
        "② 检测报告中检测项目不包含招标要求项 → 无效报告",
        "③ 合同业绩甲方为招标人关联单位 → 自循环业绩",
        "④ 证书有效期 < 投标截止日 → 过期证书",
        "⑤ 多家投标人同一发证机构同一批次证书 → 批量购买假证",
    ],
}

# ============================================================
# 表6: 资金流向 — 对接陪标费/回扣/资金回流
# ============================================================
FUND_FLOW_SCHEMA = {
    "table_name": "t_fund_flow",
    "description": "投标人相关银行流水(银行对账单/大额转账记录)",
    "required_fields": {
        "bidder_id":       "string  — 投标人ID",
        "trans_date":      "date    — 交易日期",
        "trans_amount":    "decimal — 交易金额(元)",
        "counterparty":    "string  — 对方户名",
        "counterparty_account":"string — 对方账号",
        "counterparty_bank":"string  — 对方开户行",
        "trans_purpose":   "string  — 用途摘要",
        "balance_after":   "decimal — 交易后余额",
    },
    "mapped_algorithms": [
        "FIN2-001: 银行费用资金回流 → 陪标保证金的交退闭环",
        "BUDGET-002: 政府投资基金循环回流 → 跨项目资金闭环",
        "BID-ROTATE-001: 陪标费资金轨迹 → 投标人之间的小额转账",
        "FUND-SIPHON-001: 套取资金三分类 → 大额整数转账/频率异常",
    ],
    "detection_signals": [
        "① 投标保证金 交→退 后在A公司退到B公司账户 → 陪标费",
        "② A公司中标后向未中标的B公司转账 → 陪标报酬",
        "③ 投标保证金来自同一账户 → 幕后统一控制",
        "④ 投标前后出现大额整数转账 → 可能为回扣",
    ],
}

# ============================================================
# 表7: 评标过程数据 — 对接评标异常/打分偏离
# ============================================================
EVALUATION_SCHEMA = {
    "table_name": "t_evaluation_record",
    "description": "评标过程记录(打分表/评审意见/专家信息)",
    "required_fields": {
        "project_id":      "string  — 项目ID",
        "bidder_id":       "string  — 投标人ID",
        "expert_id":       "string  — 评审专家ID",
        "expert_name":     "string  — 专家姓名",
        "score_item":      "string  — 评分项(价格分/技术分/商务分/...)",
        "score_value":     "decimal — 得分",
        "max_score":       "decimal — 满分值",
        "review_comment":  "string  — 评审意见",
    },
    "optional_fields": {
        "expert_org":      "string  — 专家单位",
        "expert_field":    "string  — 专家专业领域",
    },
    "mapped_algorithms": [
        "BID-PATTERN-005: 评分模式异常 → 专家×投标人 打分矩阵",
        "expert_bias_detector: 评标偏离度(对应Agent, 当前待接入)",
    ],
    "detection_signals": [
        "① 某专家对A投标人全部打满分 → 倾向性评分",
        "② 中标人在所有专家中得分都>95% → 异常集中",
        "③ 价格分占比设置异常低(如技术分80%价格分20%) → 为内定铺路",
    ],
}

# ============================================================
# 快速落地指南 — 按数据就绪度分三个等级
# ============================================================
QUICK_START = """
【Level 1 — 无系统数据(Excel即可)】
  适用: 手工采集的投标数据
  可跑算法: PROC-CONCEN-001(集中度), PROC-RELATED-001(关联方),
             BID-ROTATE-001(轮庄), PROC-FAKE-001(虚假材料)
  需要的数据: 投标人基本信息表 + 中标情况表(Excel格式)
  检测效果: ★★★☆☆ (能抓显性关联和明面轮庄)

【Level 2 — 有电子招投标平台数据】
  适用: 能导出投标元数据(IP/MAC/文档属性)
  可跑算法: Level1全部 + INVEST-001, INVEST2-001, BID-DARKMARK-001,
             PROC2-001(文本雷同)
  需要的数据: Level1 + 电子投标元数据表
  检测效果: ★★★★☆ (能抓同机投标/同人做标书/文本雷同)
            ↑ 串标围标检测铁三角: 同IP+同文档作者+文本相似>70% = 几乎定案

【Level 3 — 有完整资金流数据】
  适用: 能获取投标人银行流水或电子保函数据
  可跑算法: Level2全部 + FIN2-001(资金回流), BUDGET-002(循环回流)
  需要的数据: Level2 + 资金流向表
  检测效果: ★★★★★ (资金+行为+文本 三维交叉锁定)
            ↑ 铁证三连: 同MAC地址 + 文本雷同 + 保证金同源账户 = 无争议定案
"""


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print(__doc__)
    print("\n" + "="*60)
    print("数据采集优先级建议:")
    print("-"*40)
    print("  必采: 投标人基本信息表(工商+人员)")
    print("  必采: 投标项目汇总表(中标/落标/金额)")
    print("  强烈建议: 电子投标元数据(IP/MAC/文档指纹)")
    print("  强烈建议: 投标文件文本内容(TF-IDF相似度)")
    print("  如有条件: 供应商资质材料(证书/检测报告)")
    print("  如有条件: 资金流向(银行流水)")
    print("="*60)
