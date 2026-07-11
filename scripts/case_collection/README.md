# 审计案例采集脚本

用途：定期采集财政/审计相关政策和案例，人工确认后分类归档到知识库。

主流程：

1. `case_collector.py`：采集候选条目，输出到 `logs/case_collection/pending/`。
2. `case_classifier.py`：按融策业务线分类。
3. `case_archiver.py`：归档到知识库/Obsidian。
4. `README_case_collection.md`：详细使用说明。

原则：所有外部采集内容必须先确认再归档，避免把低质量网页灌进知识库。
