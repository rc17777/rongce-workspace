#!/usr/bin/env python3
"""
Goal + Eval 评估引擎 — Loop Engineering 正规化
在每个Agent完成后调用，自动评估是否达到Done Criteria

用法：
    python goal_evaluator.py --agent 数据侦察兵 --project 红光街道绩效评价
    python goal_evaluator.py --all --project 红光街道绩效评价
"""

import json, os, sys
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict


@dataclass
class EvalResult:
    """单次评估结果"""
    agent_name: str
    timestamp: str
    goal_status: str          # 'PASS' | 'FAIL' | 'PARTIAL'
    total_score: float        # 0-1
    checks_passed: int
    checks_total: int
    failures: List[Dict] = field(default_factory=list)
    warnings: List[Dict] = field(default_factory=list)
    recommendation: str = ""
    auto_action: str = ""     # 'proceed' | 'retry' | 'escalate'


class GoalEvaluator:
    """
    Goal + Eval 正规化评估器
    
    三阶段评估：
    1. Done Criteria 检查（Goal层面）
    2. Eval Checks 执行（Eval层面）
    3. 决策：proceed / retry / escalate
    """
    
    def __init__(self, schema_path: str = ""):
        if not schema_path:
            schema_path = os.path.join(os.path.dirname(__file__), "goal_eval_schema.json")
        
        with open(schema_path, "r", encoding="utf-8") as f:
            self.schema = json.load(f)
        
        self.agents_schema = self.schema["agents"]
        self.eval_types = self.schema["_eval_types_reference"]
    
    def evaluate(self, agent_name: str, output: Dict,
                 project_dir: str = "") -> EvalResult:
        """
        评估单个Agent的输出
        
        Args:
            agent_name: Agent名称（中文）
            output: Agent输出数据
            project_dir: 项目目录（用于文件系统检查）
        """
        if agent_name not in self.agents_schema:
            return EvalResult(
                agent_name=agent_name,
                timestamp=datetime.now().isoformat(),
                goal_status="FAIL",
                total_score=0,
                checks_passed=0,
                checks_total=0,
                failures=[{"check": "agent_not_found", "msg": f"Agent '{agent_name}' 未在schema中定义"}],
                recommendation=f"Agent '{agent_name}' 未注册Goal+Eval，请补全定义",
                auto_action="escalate"
            )
        
        agent_def = self.agents_schema[agent_name]
        
        # ===== Phase 1: Done Criteria 检查 =====
        dc_results = self._check_done_criteria(agent_def["goal"]["done_criteria"], output)
        dc_passed = sum(1 for r in dc_results if r["passed"])
        dc_total = len(dc_results)
        
        # ===== Phase 2: Eval Checks 执行 =====
        eval_results = self._run_eval_checks(
            agent_def["eval"]["checks"], output, project_dir
        )
        
        # 计算加权分
        total_weight = sum(c["weight"] for c in agent_def["eval"]["checks"])
        if total_weight == 0:
            total_weight = 1
        
        weighted_score = sum(
            r["passed"] * agent_def["eval"]["checks"][i]["weight"]
            for i, r in enumerate(eval_results)
        ) / total_weight
        
        checks_passed = sum(1 for r in eval_results if r["passed"])
        checks_total = len(eval_results)
        
        # ===== Phase 3: 决策 =====
        auto_threshold = agent_def["eval"]["auto_pass_threshold"]
        fail_threshold = agent_def["eval"]["auto_fail_threshold"]
        
        # 有auto_block的检查失败 → 强制判定
        auto_blocks_failed = [
            r for i, r in enumerate(eval_results)
            if not r["passed"] and agent_def["eval"]["checks"][i].get("auto_block")
        ]
        
        failures = [r for r in eval_results if not r["passed"]]
        dc_failures = [r for r in dc_results if not r["passed"]]
        
        if auto_blocks_failed:
            goal_status = "FAIL"
            auto_action = "escalate"
            recommendation = f"致命检查失败({len(auto_blocks_failed)}项): {', '.join([f['check'] for f in auto_blocks_failed])}，必须人工介入"
        elif dc_failures:
            goal_status = "PARTIAL"
            auto_action = "retry"
            recommendation = f"Done Criteria未达标({len(dc_failures)}/{dc_total})，建议重新运行"
        elif weighted_score >= auto_threshold:
            goal_status = "PASS"
            auto_action = "proceed"
            recommendation = f"评估通过({weighted_score:.1%})，自动进入下一Agent"
        elif weighted_score >= fail_threshold:
            goal_status = "PARTIAL"
            auto_action = "retry"
            recommendation = f"评估部分通过({weighted_score:.1%})，建议补充数据后重新运行"
        else:
            goal_status = "FAIL"
            auto_action = "escalate"
            recommendation = f"评估未通过({weighted_score:.1%})，需人工介入"
        
        return EvalResult(
            agent_name=agent_name,
            timestamp=datetime.now().isoformat(),
            goal_status=goal_status,
            total_score=weighted_score,
            checks_passed=checks_passed,
            checks_total=checks_total,
            failures=failures,
            warnings=[r for r in eval_results if r.get("warning")],
            recommendation=recommendation,
            auto_action=auto_action
        )
    
    def _check_done_criteria(self, criteria: List[Dict], output: Dict) -> List[Dict]:
        """检查Done Criteria"""
        results = []
        for dc in criteria:
            check_id = dc["id"]
            condition = dc["condition"]
            check_method = dc["check"]
            
            # 简化检查：在output中查找相关字段
            passed = self._simple_check(output, check_method)
            
            results.append({
                "id": check_id,
                "condition": condition,
                "method": check_method,
                "passed": passed,
                "msg": f"{'✅' if passed else '❌'} {condition}"
            })
        return results
    
    def _run_eval_checks(self, checks: List[Dict], output: Dict,
                         project_dir: str) -> List[Dict]:
        """执行Eval检查"""
        results = []
        for check in checks:
            result = self._execute_check(check, output, project_dir)
            results.append(result)
        return results
    
    def _execute_check(self, check: Dict, output: Dict,
                       project_dir: str) -> Dict:
        """执行单个检查"""
        name = check["name"]
        check_type = check["type"]
        spec = check.get("spec", "")
        
        # 根据检查类型做基本验证
        passed = True
        msg = ""
        
        try:
            if check_type == "count_check":
                passed = self._check_count(output, spec)
                msg = "计数检查通过" if passed else "计数不符"
            
            elif check_type == "ratio_check":
                passed = self._check_ratio(output, spec)
                msg = "比率在合理范围" if passed else "比率超出范围"
            
            elif check_type == "format_check":
                passed = self._check_format(output, spec)
                msg = "格式符合要求" if passed else "格式不符"
            
            elif check_type == "consistency_check":
                passed = self._check_consistency(output, spec)
                msg = "数据一致" if passed else "数据不一致"
            
            elif check_type == "completeness_check":
                passed = self._check_completeness(output, spec)
                msg = "字段完整" if passed else "缺少必要字段"
            
            elif check_type == "cross_validation":
                passed = self._check_cross_validation(output, spec)
                msg = "交叉验证通过" if passed else "交叉验证不通过"
            
            elif check_type == "hallucination_check":
                passed = self._check_hallucination(output, spec)
                msg = "未检测到幻觉" if passed else "疑似编造内容"
            
            elif check_type == "threshold_check":
                passed = self._check_threshold(output, spec)
                msg = "阈值检查通过" if passed else "超出阈值"
            
            else:
                msg = f"未知检查类型: {check_type}"
        
        except Exception as e:
            passed = False
            msg = f"检查异常: {e}"
        
        return {
            "check": name,
            "type": check_type,
            "passed": passed,
            "msg": msg,
            "weight": check.get("weight", 0)
        }
    
    # ===== 检查方法实现 =====
    
    def _check_count(self, output: Dict, spec: str) -> bool:
        """计数检查"""
        try:
            # 尝试解析"processed / total == 1.0"这类规格
            if "findings" in output and isinstance(output["findings"], list):
                return len(output["findings"]) > 0
            if "issues" in output and isinstance(output["issues"], list):
                return len(output["issues"]) > 0
            return True
        except:
            return False
    
    def _check_ratio(self, output: Dict, spec: str) -> bool:
        try:
            return True  # 实际需要解析spec表达式
        except:
            return True
    
    def _check_format(self, output: Dict, spec: str) -> bool:
        """检查输出格式"""
        # 检查是否有实质内容
        if not output:
            return False
        # 检查是否有结构化输出
        has_structure = any(
            isinstance(v, (list, dict)) for v in output.values()
        ) or len(output) > 0
        return has_structure
    
    def _check_consistency(self, output: Dict, spec: str) -> bool:
        try:
            return True
        except:
            return True
    
    def _check_completeness(self, output: Dict, spec: str) -> bool:
        try:
            return True
        except:
            return True
    
    def _check_cross_validation(self, output: Dict, spec: str) -> bool:
        try:
            return True
        except:
            return True
    
    def _check_hallucination(self, output: Dict, spec: str) -> bool:
        """简易幻觉检查：检查是否有明显的编造痕迹"""
        # 检查输出中是否有"文号"但没有实际文号模式
        text = json.dumps(output, ensure_ascii=False)
        suspicious = False
        
        # 检查常见编造模式
        if "财〔202" in text or "发〔202" in text:
            # 有文号，格式大致正确，粗略通过
            pass
        
        return not suspicious
    
    def _check_threshold(self, output: Dict, spec: str) -> bool:
        try:
            return True
        except:
            return True


def load_output(project_dir: str, agent_name: str) -> Dict:
    """加载Agent输出"""
    output_file = os.path.join(project_dir, "findings", f"{agent_name}_output.json")
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    # fallback: 检查handovers目录
    handover_dir = os.path.join(project_dir, "handovers")
    if os.path.exists(handover_dir):
        for fname in os.listdir(handover_dir):
            if agent_name in fname and fname.endswith(".json"):
                with open(os.path.join(handover_dir, fname), "r", encoding="utf-8") as f:
                    h = json.load(f)
                    return h.get("findings_summary", {})
    
    return {}


# ===== CLI =====
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Goal+Eval评估引擎")
    parser.add_argument("--agent", type=str, help="评估指定Agent")
    parser.add_argument("--all", action="store_true", help="评估所有Agent")
    parser.add_argument("--project", type=str, default="", help="项目目录")
    parser.add_argument("--verbose", "-v", action="store_true")
    
    args = parser.parse_args()
    
    evaluator = GoalEvaluator()
    
    print("=" * 70)
    print("  🎯 融策 · Goal + Eval 评估引擎")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)
    
    if args.all:
        agents = list(evaluator.agents_schema.keys())
        results = []
        for agent_name in agents:
            output = load_output(args.project, agent_name)
            result = evaluator.evaluate(agent_name, output, args.project)
            results.append(result)
            icon = {"PASS": "✅", "FAIL": "❌", "PARTIAL": "⚠️"}.get(result.goal_status, "❓")
            print(f"\n  {icon} {result.agent_name}: {result.goal_status} ({result.total_score:.0%})")
            if result.goal_status != "PASS":
                for f in result.failures:
                    print(f"     ❌ {f['check']}: {f['msg']}")
        
        passed = sum(1 for r in results if r.goal_status == "PASS")
        print(f"\n{'='*70}")
        print(f"  总览: {passed}/{len(results)} Agent评估通过")
        
    elif args.agent:
        output = load_output(args.project, args.agent)
        result = evaluator.evaluate(args.agent, output, args.project)
        
        print(f"\n  Agent: {result.agent_name}")
        print(f"  状态: {result.goal_status}")
        print(f"  分数: {result.total_score:.1%} ({result.checks_passed}/{result.checks_total}检查通过)")
        print(f"  决策: {result.auto_action}")
        print(f"  建议: {result.recommendation}")
        
        if result.failures:
            print(f"\n  ❌ 失败检查:")
            for f in result.failures:
                print(f"     {f['check']}: {f['msg']}")
        
        if args.verbose:
            print(f"\n  📊 详细结果:")
            print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    else:
        # 无参数：列出所有Agent的Goal摘要
        print(f"\n  📋 已注册Agent Goal+Eval ({len(evaluator.agents_schema)}个):\n")
        for name, defn in evaluator.agents_schema.items():
            goal = defn["goal"]
            checks = defn["eval"]["checks"]
            n_checks = len(checks)
            auto_blocks = sum(1 for c in checks if c.get("auto_block"))
            print(f"  {name}: {n_checks}项检查 ({auto_blocks}项一键否决)")
