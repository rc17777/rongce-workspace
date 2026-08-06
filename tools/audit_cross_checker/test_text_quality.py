#!/usr/bin/env python3
"""Quick test of TextQualityFilter with a deliberately flawed audit report sample."""
import sys
sys.path.insert(0, ".")

from tools.audit_cross_checker.text_quality_filter import TextQualityFilter

test_report = """
被审计单位基本情况
XX局是市政府组成部门，内设8个科室，编制50人。

审计评价
该局财务管理工作总体较好，领导班子全心全意、兢兢业业履行职责，各项支出基本合规。

审计发现的主要问题
1、财务管理还不够到位
审计认为，该单位的预算执行率较低，可能是由于年初预算编制不够科学。2019年未按规定公开部门决算，依据《财政违法行为处罚处分条例》定性为违规。
2、内控制度不够到位
固定资产账实不符，定性为固定资产管理不规范。将出具审计决定予以处理。

责任认定
经查，该单位负责人主持召开了相关会议，签批了相关文件，应承担直接责任。

审计建议
1、遵守财经纪律，加强财务管理
2、提高思想认识，高度重视预算工作
3、建议修改预算法以完善预算管理
"""

tqf = TextQualityFilter()
results = tqf.evaluate(test_report)

for r in results:
    if not r.passed or r.requires_human_review:
        status = 'X' if not r.passed else '?'
        review = ' [NEEDS HUMAN]' if r.requires_human_review else ''
        print(f'[{status}] [{r.rule_id}] {r.dimension_name}: {r.description}{review}')
        if r.detail:
            print(f'     detail: {r.detail}')
        if r.excerpt and not r.passed:
            print(f'     excerpt: {r.excerpt[:150]}')
        if r.suggestion:
            print(f'     suggestion: {r.suggestion}')
        print()

score = tqf.score(results)
print(f'=== Score: {score["overall_score"]}/100  Grade: {score["grade"]} ===')
print(f'Passed: {score["passed_checks"]}, Failed: {score["failed_checks"]}, Review: {score["needs_human_review"]}')
print()
print("Dimension scores:")
for dim, info in sorted(score["dimension_scores"].items()):
    print(f'  {dim}: {info["score"]} (weight: {info["weight"]}, weighted: {info["weighted"]})')
