#!/usr/bin/env python3
"""智析 v2.0 模块加载测试"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from modules.data_collection.collector import DatabaseAdapter, CollectorManager
from modules.data_validation.validator import ValidationEngine, DataCleaner
from modules.data_migration.standardizer import AuditStandardizer, StandardLibrary
from modules.unstructured.doc_extractor import DocExtractor
from modules.audit_models.workbench import ModelWorkbench, ANALYSIS_METHODS
from modules.bigdata.analytics import GraphAnalyzer, TextMiner
from modules.knowledge.engine import CoTEngine, PromptLibrary, DataQualityChecker, MethodologyEngine

# 验证各引擎初始化
mw = ModelWorkbench()
print(f"审计模型: {len(mw.models)} 个, {len(mw.list_categories())} 大类")

v = ValidationEngine()
print(f"校验规则: {len(v.rules)} 条内置规则")

ce = CoTEngine()
print(f"思维链: {len(ce.list_chains())} 条")

pl = PromptLibrary()
print(f"提示词: {len(pl.list_all())} 个")

dq = DataQualityChecker()
result = dq.run_checks({"columns": [{"name": "account_code", "type": "str"}, {"name": "amount", "type": "float"}], "pk": "id"})
print(f"数据标准检查: {result['score']}分 ({result['grade']}级)")

me = MethodologyEngine()
print(f"方法论框架: {len(me.list_all())} 个")

std = AuditStandardizer()
print(f"审计数据标准域: {std.list_domains()}")

db = DatabaseAdapter()
print(f"数据库适配: {len(db.list_supported())} 种 (含{len(db.list_domestic())}种国产)")

# 测试文档提取
result = DocExtractor.process_document("甲方：XX市教育局 乙方：XX建设公司 合同金额：人民币500万元 签订日期2025年3月15日")
print(f"文档提取: doc_type={result['doc_type']}")

# 测试模型搜索
results = mw.search("招标")
print(f"模型搜索'招标': {len(results)} 个匹配")

# 测试文本挖掘
tm = TextMiner()
freq = tm.word_frequency(["专项资金使用管理不规范存在挪用现象", "专项资金拨付进度缓慢导致资金闲置"], top_n=10)
print(f"词频TOP5: {freq[:5]}")

# 测试方法论推荐
rec = me.recommend_for_audit_type("政府采购")
print(f"政府采购推荐框架: {rec}")

print()
print("=== 所有模块加载验证通过 ===")
