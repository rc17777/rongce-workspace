"""
MCP Server — 文本分析工具集 MCP 服务

将5个文本分析工具封装为 MCP (Model Context Protocol) 标准接口，
供 LLM Agent 通过 MCP 协议调用。

启动方式：
    python mcp_server.py
    或
    python -m audit_text_analysis.mcp_server

支持的工具：
    - text_hotword_analysis
    - text_similarity_compare
    - contract_field_extract
    - personnel_profile_check
    - budget_compliance_scan
    - benford_analysis             (v7 Benford定律)
    - supplier_fingerprint         (v7 供应商行为指纹)
    - timeline_anomaly             (v7 时间序列异常)
    - contract_change_trajectory   (v7 合同变更轨迹)
    - audit_text_pipeline_run      (4步流水线)
    - simulator_inference_generate (v5模拟器对偶)
"""

import json
import sys
from typing import Any, Dict, List, Optional


# ── MCP Server (标准JSON-RPC实现) ──────────────────────────────

class MCPServer:
    """
    轻量 MCP Server

    遵循 MCP 协议规范，通过 stdin/stdout JSON-RPC 通信。
    兼容任何支持 MCP 的 LLM Agent 框架。
    """

    def __init__(self):
        self.tools = self._register_tools()
        self._tool_handlers = self._register_handlers()

    def _register_tools(self) -> List[Dict[str, Any]]:
        """注册工具列表（MCP tools/list）"""
        return [
            {
                "name": "text_hotword_analysis",
                "description": "TF-IDF会议纪要热词提取：批量读取会议纪要，提取高频决策关键词，"
                              "快速锁定测绘费、工程外包、补贴发放、资产处置等高危审计领域",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "documents": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "文本数组",
                        },
                        "doc_type": {
                            "type": "string",
                            "enum": ["meeting_minutes", "policy", "report"],
                            "default": "meeting_minutes",
                            "description": "文档类型",
                        },
                        "top_n": {
                            "type": "integer",
                            "default": 20,
                            "description": "返回热词数量",
                        },
                        "custom_stopwords": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "自定义停用词列表",
                        },
                        "audit_focus": {
                            "type": "string",
                            "description": "审计重点类型（可选，自动推断）",
                        },
                    },
                    "required": ["documents"],
                },
            },
            {
                "name": "text_similarity_compare",
                "description": "Jaccard相似度串换筛查：比对文本相似度，识别品名串换、名称微调等违规",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "reference_texts": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "标准/合规文本数组",
                        },
                        "check_texts": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "待核查文本数组",
                        },
                        "mode": {
                            "type": "string",
                            "enum": ["global", "local"],
                            "default": "global",
                            "description": "比对模式",
                        },
                        "threshold": {
                            "type": "number",
                            "default": 0.7,
                            "description": "相似度阈值",
                        },
                        "audit_type": {
                            "type": "string",
                            "description": "审计类型",
                        },
                    },
                    "required": ["reference_texts", "check_texts"],
                },
            },
            {
                "name": "contract_field_extract",
                "description": "合同八大字段拆解：自动提取合同核心字段（主体、金额、日期、付款条件等），"
                              "与财务支付数据交叉比对",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "contract_files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "合同文件路径数组",
                        },
                        "extract_fields": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "要提取的字段列表（可选，默认全部）",
                        },
                        "payment_records": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "财务支付记录（用于交叉比对）",
                        },
                        "project_ledger": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "项目台账（用于交叉比对）",
                        },
                    },
                    "required": ["contract_files"],
                },
            },
            {
                "name": "personnel_profile_check",
                "description": "人员身份比对：筛查财政供养人员、死亡人员、重复申领等违规领取补贴情况",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "applicants": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "申报人列表 [{\"name\": \"...\", \"subsidy_type\": \"...\", ...}]",
                        },
                        "reference_lists": {
                            "type": "object",
                            "description": "参照名单 {\"finance_staff\": [...], \"deceased\": [...], ...}",
                        },
                        "check_rules": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "检查规则（可选，默认全部）",
                        },
                    },
                    "required": ["applicants", "reference_lists"],
                },
            },
            {
                "name": "budget_compliance_scan",
                "description": "预算合规校验：全量扫描报销文本，识别超标接待、私车公养、违规采购等",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "expense_texts": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "报销备注/凭证文本数组",
                        },
                        "rule_set": {
                            "type": "object",
                            "description": "自定义规则集（可选，默认使用内置规则）",
                        },
                        "custom_rules": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "额外自定义规则",
                        },
                    },
                    "required": ["expense_texts"],
                },
            },
            {
                "name": "audit_text_pipeline_run",
                "description": "运行完整的4步审计文本分析流水线：数据归集→规则配置→批量分析→人机核验",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "source_files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "源文件路径列表",
                        },
                        "project_name": {
                            "type": "string",
                            "description": "项目名称",
                        },
                        "project_type": {
                            "type": "string",
                            "description": "项目类型（可选，自动推断）",
                        },
                        "enable_simulator": {
                            "type": "boolean",
                            "default": True,
                            "description": "是否启用v5模拟器对偶推理",
                        },
                    },
                    "required": ["source_files"],
                },
            },
            {
                "name": "benford_analysis",
                "description": "Benford定律首位数字异常检测：对发票/合同金额进行首位数字分布检验，"
                              "卡方拟合优度检验判断是否存在人为操控（分拆发票/虚报金额等），"
                              "支持按品类/单位分组对比分析",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "amounts": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "金额数值数组",
                        },
                        "csv_file": {
                            "type": "string",
                            "description": "CSV文件路径（与amounts二选一）",
                        },
                        "amount_column": {
                            "type": "string",
                            "description": "CSV中金额列名（csv_file时必填）",
                        },
                        "group_column": {
                            "type": "string",
                            "description": "CSV中分组列名（如'品类''单位'，用于分组对比）",
                        },
                    },
                    "required": [],
                },
            },
            {
                "name": "supplier_fingerprint",
                "description": "供应商行为指纹相似度分析：提取供应商多维行为特征（参与单位/中标率/"
                              "金额分布/项目类别/投标时间）形成向量，余弦相似度计算发现表面无关联但"
                              "行为模式高度一致的供应商组，识别隐性围标串标",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "records": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "采购记录列表，每条含supplier_name/amount/project_category/unit_name等",
                        },
                        "threshold": {
                            "type": "number",
                            "default": 0.80,
                            "description": "相似度阈值（0-1），默认0.80",
                        },
                        "csv_file": {
                            "type": "string",
                            "description": "CSV文件路径（与records二选一）",
                        },
                    },
                    "required": [],
                },
            },
            {
                "name": "timeline_anomaly",
                "description": "时间序列异常检测：检测付款时间早于合同签订时间的异常项目（先付款后签合同），"
                              "金额偏离率分析，及经办人聚焦统计——识别系统性违规模式和关键经办人",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "projects": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "项目记录数组，含contract_date/payment_date/contract_amount/payment_amount/handler等",
                        },
                        "date_format": {
                            "type": "string",
                            "default": "%Y-%m-%d",
                            "description": "日期格式",
                        },
                        "max_lead_days": {
                            "type": "integer",
                            "default": 0,
                            "description": "允许的最大提前付款天数（0=严格禁止）",
                        },
                        "csv_file": {
                            "type": "string",
                            "description": "CSV文件路径（与projects二选一）",
                        },
                    },
                    "required": [],
                },
            },
            {
                "name": "data_script_generator",
                "description": "数据处理脚本生成器（DSG）：提供CSV列名+处理需求描述，"
                              "自动生成可直接本地执行的Python/Pandas脚本。"
                              "内置敏感数据检测（身份证/银行账号），"安全模式：表头给AI，数据本地跑"",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "csv_path": {
                            "type": "string",
                            "description": "输入CSV文件路径",
                        },
                        "column_headers": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "CSV列名列表",
                        },
                        "processing_requirements": {
                            "type": "string",
                            "description": "处理需求描述（自然语言），如'筛选金额大于1万的记录并按部门汇总'",
                        },
                        "output_path": {
                            "type": "string",
                            "default": "output.csv",
                            "description": "输出文件路径",
                        },
                    },
                    "required": ["csv_path", "column_headers", "processing_requirements"],
                },
            },
            {
                "name": "generate_review_plan",
                "description": "生成人机复核计划：根据审计发现总数、AI评分、高危标记，"
                              "按三级复核量化规则（L1抽检5%、L2异常全检、L3全量复核）"
                              "计算各级样本量和预估工时",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "total_items": {"type": "integer", "description": "审计发现总条数"},
                        "ai_scores": {"type": "array", "items": {"type": "number"}, "description": "L1 AI评分列表"},
                        "high_risk_count": {"type": "integer", "default": 0, "description": "高危发现数"},
                        "l2_triggered_count": {"type": "integer", "default": 0, "description": "L2 Agent触发异常数"},
                    },
                    "required": ["total_items"],
                },
            },
            {
                "name": "detect_duplicate_claims",
                "description": "三维联合去重检测：对费用报销记录进行报销人×金额×时间三维联合匹配，"
                              "发现重复报销、拆分报销、团伙虚假报销",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "records": {"type": "array", "items": {"type": "object"}, "description": "报销记录[{\"claimant\":\"\",\"amount\":0,\"date\":\"\"}]"},
                        "amount_tolerance_pct": {"type": "number", "default": 5.0, "description": "金额容差百分比"},
                        "time_window_days": {"type": "integer", "default": 3, "description": "时间窗口天数"},
                    },
                    "required": ["records"],
                },
            },
            {
                "name": "check_context_window",
                "description": "检查上下文窗口使用率，预估token消耗，在接近上限时发出预警",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "model": {"type": "string", "default": "default", "description": "模型名称"},
                        "estimated_tokens": {"type": "integer", "description": "已使用token数"},
                        "base_tokens": {"type": "integer", "default": 0, "description": "基础提示词token数"},
                    },
                    "required": ["estimated_tokens"],
                },
            },
            {
                "name": "bid_rigging_detect",
                "description": "招投标围标串标多维检测：5维特征并行检测（同IP/同设备、报价规律雷同、保证金同源、"
                              "投标文件基因相似、时间窗口扎堆），输出0-5分风险评分+特征交叉矩阵+命中率统计",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "segments": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "标段数据列表，每条含segment_id/bidders（含ip/mac/ca/bid_amount/doc_text/submit_time等）",
                        },
                        "industry": {
                            "type": "string",
                            "description": "行业类型（construction/it_service/equipment/consulting/epc/design，默认default）",
                        },
                        "verbose": {
                            "type": "boolean",
                            "default": False,
                            "description": "是否输出详细日志",
                        },
                    },
                    "required": ["segments"],
                },
            },
            {
                "name": "evidence_chain_graph",
                "description": "证据链图谱生成：基于围标检测结果生成力导向图（ECharts/D3.js格式），"
                              "一键导出HTML交互式图谱或Markdown证据摘要卡片（A4一页纸），直接嵌入审计报告",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "rigging_result_json": {
                            "type": "string",
                            "description": "BidRiggingResult的JSON序列化结果（从bid_rigging_detect输出）",
                        },
                        "export_html": {
                            "type": "boolean",
                            "default": False,
                            "description": "是否导出独立HTML文件",
                        },
                        "output_dir": {
                            "type": "string",
                            "default": "./evidence_graphs",
                            "description": "HTML输出目录",
                        },
                        "max_graphs": {
                            "type": "integer",
                            "default": 20,
                            "description": "最多生成的图谱数",
                        },
                    },
                    "required": ["rigging_result_json"],
                },
            },
            {
                "name": "contract_change_trajectory",
                "description": "合同变更轨迹分析：横向投影分析变更类型分布，对标行业基准值检测异常变更率，"
                              "时间点聚集分析（验收后调减=结算水分），识别高风险变更项目",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "contracts": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "合同列表，含project_id/contract_date/completion_date/contract_amount等",
                        },
                        "changes": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "变更记录，含project_id/change_date/change_type/change_amount等",
                        },
                        "industry": {
                            "type": "string",
                            "enum": ["procurement", "project_construction", "general"],
                            "default": "general",
                            "description": "行业基准类型",
                        },
                        "csv_contracts": {
                            "type": "string",
                            "description": "合同CSV路径",
                        },
                        "csv_changes": {
                            "type": "string",
                            "description": "变更记录CSV路径",
                        },
                    },
                    "required": [],
                },
            },
            {
                "name": "simulator_inference_generate",
                "description": "v5增强：为工具发现生成模拟器对偶推理（Why层因果分析）",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "tool_name": {
                            "type": "string",
                            "enum": [
                                "text_hotword_analysis",
                                "text_similarity_compare",
                                "contract_field_extract",
                                "personnel_profile_check",
                                "budget_compliance_scan",
                                "benford_analysis",
                                "supplier_fingerprint",
                                "timeline_anomaly",
                                "contract_change_trajectory",
                                "bid_rigging_detect",
                                "evidence_chain_graph",
                            ],
                            "description": "源工具名称",
                        },
                        "findings": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "工具发现列表",
                        },
                        "context": {
                            "type": "object",
                            "description": "上下文信息（如audit_type）",
                        },
                    },
                    "required": ["tool_name", "findings"],
                },
            },
        ]

    def _register_handlers(self) -> Dict[str, Any]:
        """注册工具处理函数映射"""
        from .hotword import text_hotword_analysis
        from .similarity import text_similarity_compare
        from .contract import contract_field_extract
        from .personnel import personnel_profile_check
        from .budget import budget_compliance_scan
        from .benford import benford_analysis
        from .supplier_fingerprint import supplier_fingerprint
        from .timeline_anomaly import timeline_anomaly
        from .contract_change_trajectory import contract_change_trajectory
        from .bid_rigging_detector import detect_bid_rigging
        from .evidence_chain_graph import generate_evidence_chains, generate_summary_card
        from .data_script_generator import data_script_generator
        from .human_review_rules import generate_review_plan
        from .throughput_benchmark import get_all_sla_summary
        from .context_window_monitor import check_context_window, generate_resume_checkpoint
        from .duplicate_claim_detector import detect_duplicate_claims
        from .journal_validator import journal_entry_validate
        from .pipeline import AuditTextPipeline
        from .simulator_duality import generate_simulator_inferences

        def handle_pipeline(args):
            pipeline = AuditTextPipeline()
            return pipeline.run(
                source_files=args.get("source_files", []),
                project_name=args.get("project_name", ""),
                project_type=args.get("project_type", ""),
                enable_simulator=args.get("enable_simulator", True),
            )

        def handle_simulator(args):
            return {
                "findings_with_inference": generate_simulator_inferences(
                    tool_name=args["tool_name"],
                    findings=args["findings"],
                    context=args.get("context"),
                )
            }

        def handle_bid_rigging(args):
            """v9: 围标串标多维检测"""
            segments = args.get("segments", [])
            industry = args.get("industry", "default")
            verbose = args.get("verbose", False)
            result = detect_bid_rigging(segments, industry=industry)
            return {
                "total_segments": result.total_segments,
                "flagged_segments": result.flagged_segments,
                "risk_distribution": result.risk_distribution,
                "hit_rate_stats": result.hit_rate_stats,
                "cross_hit_matrix": result.cross_hit_matrix,
                "summary": result.summary,
                "risks": [
                    {
                        "segment_id": r.segment_id,
                        "segment_name": r.segment_name,
                        "risk_score": r.risk_score,
                        "risk_level": r.risk_level,
                        "feature_flags": r.feature_flags,
                        "combined_evidence": r.combined_evidence,
                        "recommendation": r.recommendation,
                    }
                    for r in result.risks[:50]  # 最多返回50条
                ],
            }

        def handle_evidence_chain(args):
            """v9: 证据链图谱生成"""
            import json as _json
            rigging_json = args.get("rigging_result_json", "{}")
            export_html = args.get("export_html", False)
            output_dir = args.get("output_dir", "./evidence_graphs")
            max_graphs = args.get("max_graphs", 20)

            # 从JSON重建结果对象（使用简化字典形式）
            rigging_data = _json.loads(rigging_json) if isinstance(rigging_json, str) else rigging_json

            # 创建简化版result对象
            from .bid_rigging_detector import BidRiggingRisk, BidRiggingResult
            risks_list = []
            for r_data in rigging_data.get("risks", [])[:max_graphs]:
                risk = BidRiggingRisk(
                    segment_id=r_data.get("segment_id", ""),
                    segment_name=r_data.get("segment_name", ""),
                    total_bidders=r_data.get("total_bidders", 0),
                    risk_score=r_data.get("risk_score", 0),
                    risk_level=r_data.get("risk_level", "low"),
                    feature_flags=r_data.get("feature_flags", {}),
                    feature_details=r_data.get("feature_details", {}),
                    combined_evidence=r_data.get("combined_evidence", []),
                    recommendation=r_data.get("recommendation", ""),
                )
                risks_list.append(risk)

            rigging_result = BidRiggingResult(
                total_segments=rigging_data.get("total_segments", 0),
                flagged_segments=rigging_data.get("flagged_segments", 0),
                risk_distribution=rigging_data.get("risk_distribution", {}),
                risks=risks_list,
                hit_rate_stats=rigging_data.get("hit_rate_stats", {}),
                cross_hit_matrix=rigging_data.get("cross_hit_matrix", {}),
                summary=rigging_data.get("summary", ""),
            )

            result = generate_evidence_chains(
                rigging_result,
                export_html=export_html,
                output_dir=output_dir,
            )

            return {
                "total_graphs": result.total_segments,
                "generated_at": result.generated_at,
                "graphs": [
                    {
                        "segment_id": g.segment_id,
                        "segment_name": g.segment_name,
                        "risk_score": g.risk_score,
                        "risk_level": g.risk_level,
                        "nodes_count": len(g.nodes),
                        "edges_count": len(g.edges),
                        "summary_text": g.summary_text,
                    }
                    for g in result.graphs
                ],
            }

        return {
            "text_hotword_analysis": text_hotword_analysis,
            "text_similarity_compare": text_similarity_compare,
            "contract_field_extract": contract_field_extract,
            "personnel_profile_check": personnel_profile_check,
            "budget_compliance_scan": budget_compliance_scan,
            "benford_analysis": benford_analysis,
            "supplier_fingerprint": supplier_fingerprint,
            "timeline_anomaly": timeline_anomaly,
            "contract_change_trajectory": contract_change_trajectory,
            "bid_rigging_detect": handle_bid_rigging,
            "evidence_chain_graph": handle_evidence_chain,
            "data_script_generator": data_script_generator,
            "generate_review_plan": generate_review_plan,
            "get_all_sla_summary": get_all_sla_summary,
            "check_context_window": check_context_window,
            "generate_resume_checkpoint": generate_resume_checkpoint,
            "detect_duplicate_claims": detect_duplicate_claims,
            "journal_entry_validate": journal_entry_validate,
            "audit_text_pipeline_run": handle_pipeline,
            "simulator_inference_generate": handle_simulator,
        }

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理单个JSON-RPC请求"""
        method = request.get("method", "")
        req_id = request.get("id")

        # tools/list
        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": self.tools},
            }

        # tools/call
        if method == "tools/call":
            params = request.get("params", {})
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})

            if isinstance(arguments, str):
                arguments = json.loads(arguments)

            handler = self._tool_handlers.get(tool_name)
            if not handler:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Unknown tool: {tool_name}",
                    },
                }

            try:
                result = handler(arguments)
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(
                                    result, ensure_ascii=False, indent=2
                                ),
                            }
                        ]
                    },
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32000,
                        "message": f"Tool execution error: {str(e)}",
                    },
                }

        # 未知方法
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}",
            },
        }

    def run_stdio(self):
        """通过stdin/stdout运行MCP Server"""
        import sys

        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue

            try:
                request = json.loads(line)
            except json.JSONDecodeError:
                error_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": "Parse error"},
                }
                sys.stdout.write(json.dumps(error_resp) + "\n")
                sys.stdout.flush()
                continue

            response = self.handle_request(request)
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()


# ── 命令行入口 ──────────────────────────────────────────────

def main():
    """MCP Server主入口"""
    server = MCPServer()

    # 如果有命令行参数，进入交互模式
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        print("融策审计智析Agent — 文本分析工具集 MCP Server")
        print(f"已注册 {len(server.tools)} 个工具：")
        for t in server.tools:
            print(f"  - {t['name']}: {t['description'][:60]}...")
        print("\n输入JSON-RPC请求（Ctrl+C退出）：")

        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue
                if line.lower() in ("exit", "quit", "q"):
                    break
                try:
                    request = json.loads(line)
                except json.JSONDecodeError:
                    print(f"JSON解析错误: {line}")
                    continue
                response = server.handle_request(request)
                print(json.dumps(response, ensure_ascii=False, indent=2))
        except KeyboardInterrupt:
            print("\n已退出")
    else:
        # MCP模式：stdin/stdout
        server.run_stdio()


if __name__ == "__main__":
    main()
