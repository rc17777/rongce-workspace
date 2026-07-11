"""
融策审计智析Agent — 文本分析工具集 v7

五大核心工具（v4）：
1. text_hotword_analysis    — TF-IDF会议纪要热词提取
2. text_similarity_compare  — Jaccard相似度串换筛查
3. contract_field_extract   — 正则+NER合同八大字段拆解
4. personnel_profile_check  — 集合运算人员身份比对
5. budget_compliance_scan   — 关键词+规则预算合规校验

四大统计/行为分析工具（v7）：
6. benford_analysis              — Benford定律首位数字异常检测
7. supplier_fingerprint          — 供应商行为指纹相似度引擎
8. timeline_anomaly              — 时间序列异常检测器
9. contract_change_trajectory    — 合同变更轨迹分析器

v5增强：
- simulator_duality — 模拟器对偶（Why层因果推理）
- structured_output — Agent输出结构化（四段式Schema）
- workpaper_scorer  — L1底稿质量自动评分引擎
"""

from .hotword import TextHotwordAnalyzer, text_hotword_analysis
from .similarity import TextSimilarityComparator, text_similarity_compare
from .contract import ContractFieldExtractor, contract_field_extract
from .personnel import PersonnelProfileChecker, personnel_profile_check
from .budget import BudgetComplianceScanner, budget_compliance_scan
from .simulator_duality import SimulatorDualityEngine, generate_simulator_inferences
from .structured_output import (
    AgentStructuredOutput, OutputBuilder, OutputValidator,
    build_from_tool_result, validate_output,
)
from .workpaper_scorer import WorkpaperScorer, ScoreReport, QualityGrade
from .pipeline import AuditTextPipeline
from .agent_config import (
    AGENT_CONFIGS, get_agent_tool_matrix, get_tool_agent_map,
    get_agent_for_project, get_system_prompt, inject_kb_to_prompt,
    get_voucher_check_templates, get_templates_for_agent,
    format_voucher_check_prompt, inject_voucher_templates_to_prompt,
)
from .pitfall_guards import PitfallGuard, PitfallCheck, PitfallReport
from .year_over_year import YearOverYearDetector, YearOverYearReport, detect_copy_paste
from .data_readiness import DataReadinessAssessor, DataReadinessLevel, ReadinessDashboard
from .audit_ontology import AuditOntology, AuditRule, EntityDef, RelationDef, get_ontology
from .audit_index import AuditIndexSystem, IndexEntry, IndexValidationResult, INDEX_PREFIXES
from .benford import BenfordAnalyzer, benford_analysis
from .supplier_fingerprint import SupplierFingerprintEngine, supplier_fingerprint
from .timeline_anomaly import TimelineAnomalyDetector, timeline_anomaly
from .contract_change_trajectory import ContractChangeTrajectoryAnalyzer, contract_change_trajectory
from .data_script_generator import DataScriptGenerator, data_script_generator
from .human_review_rules import ReviewPlanner, ReviewPlan, generate_review_plan
from .throughput_benchmark import ThroughputTracker, ThroughputReport, get_all_sla_summary
from .context_window_monitor import ContextWindowMonitor, WindowStatus, CheckpointSummary, check_context_window, generate_resume_checkpoint
from .duplicate_claim_detector import DuplicateClaimDetector, DuplicateDetectionResult, detect_duplicate_claims
from .journal_validator import JournalEntryValidator, ValidationResult, journal_entry_validate

__version__ = "7.0.0"
__all__ = [
    # 5 tools
    "TextHotwordAnalyzer", "text_hotword_analysis",
    "TextSimilarityComparator", "text_similarity_compare",
    "ContractFieldExtractor", "contract_field_extract",
    "PersonnelProfileChecker", "personnel_profile_check",
    "BudgetComplianceScanner", "budget_compliance_scan",
    # v5
    "SimulatorDualityEngine", "generate_simulator_inferences",
    # 结构化输出
    "AgentStructuredOutput", "OutputBuilder", "OutputValidator",
    "build_from_tool_result", "validate_output",
    # 评分引擎
    "WorkpaperScorer", "ScoreReport", "QualityGrade",
    # 流水线
    "AuditTextPipeline",
    # Agent配置 (P1)
    "AGENT_CONFIGS", "get_agent_tool_matrix", "get_tool_agent_map",
    "get_agent_for_project", "get_system_prompt", "inject_kb_to_prompt",
    # 避坑约束 (P1)
    "PitfallGuard", "PitfallCheck", "PitfallReport",
    # 年度对比 (P1)
    "YearOverYearDetector", "YearOverYearReport", "detect_copy_paste",
    # 数据就绪度 (P1)
    "DataReadinessAssessor", "DataReadinessLevel", "ReadinessDashboard",
    # 业务本体论 (P2)
    "AuditOntology", "AuditRule", "EntityDef", "RelationDef", "get_ontology",
    # 索引子系统 (P2)
    "AuditIndexSystem", "IndexEntry", "IndexValidationResult", "INDEX_PREFIXES",
    # v7 四大统计/行为分析工具
    "BenfordAnalyzer", "benford_analysis",
    "SupplierFingerprintEngine", "supplier_fingerprint",
    "TimelineAnomalyDetector", "timeline_anomaly",
    "ContractChangeTrajectoryAnalyzer", "contract_change_trajectory",
    # v8 翻凭证Prompt模板
    "get_voucher_check_templates", "get_templates_for_agent",
    "format_voucher_check_prompt", "inject_voucher_templates_to_prompt",
    # v6 DSG + P2增强
    "DataScriptGenerator", "data_script_generator",
    "ReviewPlanner", "ReviewPlan", "generate_review_plan",
    "ThroughputTracker", "ThroughputReport", "get_all_sla_summary",
    "ContextWindowMonitor", "WindowStatus", "CheckpointSummary",
    "check_context_window", "generate_resume_checkpoint",
    "DuplicateClaimDetector", "DuplicateDetectionResult",
    "detect_duplicate_claims",
    "JournalEntryValidator", "ValidationResult", "journal_entry_validate",
]
