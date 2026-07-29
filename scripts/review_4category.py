#!/usr/bin/env python3
"""
审计报告四分类输出后处理器 v1.0
基于文章1-守拙四条规矩：将复核报告从扁平问题列表改造为四层分类结构

输入：审盾复核器的原始输出（15维复核JSON）
输出：四分类结构化报告（已确认事实/风险提示/待核实事项/历史相似线索）
"""

import json, re, sys, os
from pathlib import Path
from datetime import datetime
from typing import Optional

# ── 四分类标签定义 ───────────────────────────────────

CATEGORIES = {
    "confirmed": {
        "id": "confirmed",
        "label": "✅ 已确认事实",
        "subtitle": "（有充分证据链支撑，被审计单位已签字确认）",
        "sort": 1,
        "rules": [
            "取证单已签字确认",
            "法规引用有明确原文支撑",
            "金额计算有原始凭证佐证",
            "事实描述与证据一致"
        ]
    },
    "risk": {
        "id": "risk",
        "label": "⚠️ 风险提示",
        "subtitle": "（根据现有资料推测，需进一步查证）",
        "sort": 2,
        "rules": [
            "基于现有数据的合理推测",
            "存在其他可能的合理解释",
            "尚未取得直接证据",
            "结论有前提条件（如'如果XX，则YY'）"
        ]
    },
    "pending": {
        "id": "pending",
        "label": "❓ 待核实事项",
        "subtitle": "（证据不足或数据矛盾，需要补充取证）",
        "sort": 3,
        "rules": [
            "现有证据不足以支撑结论",
            "存在相互矛盾的证据",
            "关键资料尚未取得",
            "数据口径不一致待确认"
        ]
    },
    "historical": {
        "id": "historical",
        "label": "📚 历史相似线索",
        "subtitle": "（非本项目已确认事实，仅供参考）",
        "sort": 4,
        "rules": [
            "来自RAG相似案例匹配",
            "类似项目中出现过的问题",
            "不可直接作为本项目结论",
            "用于提示检查方向"
        ]
    }
}


class FourCategoryProcessor:
    """四分类输出处理器"""
    
    def __init__(self):
        self.findings = []  # 原始审计发现
        self.classified = {k: [] for k in CATEGORIES}
    
    def load_review_results(self, review_json_path: str):
        """加载审盾复核器输出的JSON"""
        with open(review_json_path, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        
        # 兼容不同格式
        if isinstance(raw, list):
            self.findings = raw
        elif "findings" in raw:
            self.findings = raw["findings"]
        elif "issues" in raw:
            self.findings = raw["issues"]
        elif "results" in raw:
            self.findings = raw["results"]
        else:
            # 尝试扁平化提取
            self.findings = self._flatten_findings(raw)
        
        print(f"[四分类处理器] 加载 {len(self.findings)} 条审计发现")
    
    def _flatten_findings(self, data, prefix=""):
        """递归扁平化提取发现"""
        results = []
        if isinstance(data, dict):
            for k, v in data.items():
                if k in ("finding", "issue", "problem", "observation"):
                    if isinstance(v, dict):
                        results.append(v)
                    elif isinstance(v, str):
                        results.append({"title": k, "description": v})
                elif isinstance(v, (dict, list)):
                    results.extend(self._flatten_findings(v, f"{prefix}{k}."))
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    results.append(item)
                elif isinstance(item, str):
                    results.append({"description": item})
                else:
                    results.extend(self._flatten_findings(item, prefix))
        return results
    
    def classify(self, manual_mapping: dict = None) -> dict:
        """
        对发现进行分类
        
        manual_mapping: {"finding_index": "category_id", ...} 手动指定
        如不提供，使用自动分类规则
        """
        for i, finding in enumerate(self.findings):
            if manual_mapping and str(i) in manual_mapping:
                cat = manual_mapping[str(i)]
                self.classified[cat].append({**finding, "_classify_method": "manual"})
                continue
            
            # 自动分类
            cat = self._auto_classify(finding)
            self.classified[cat].append({**finding, "_classify_method": "auto"})
        
        return self.classified
    
    def _auto_classify(self, finding: dict) -> str:
        """
        自动分类逻辑
        
        优先级：
        1. 已有分类标注 → 直接使用
        2. 关键词匹配 → 推断分类
        3. 默认 → pending（待核实）
        """
        # 已有显式分类
        if "category" in finding:
            if finding["category"] in CATEGORIES:
                return finding["category"]
        
        if "severity" in finding:
            sev = str(finding["severity"]).upper()
            # P0/P1且有证据引用 → confirmed
            if sev in ("P0", "P1", "CRITICAL", "HIGH") and self._has_evidence(finding):
                return "confirmed"
        
        # 关键词匹配
        text = json.dumps(finding, ensure_ascii=False).lower()
        
        # 证据充足类
        evidence_keywords = ["取证单", "证据", "已确认", "经核实", "签字确认", "原件"]
        if any(kw in text for kw in evidence_keywords):
            return "confirmed"
        
        # 风险推测类
        risk_keywords = ["可能存在", "不排除", "疑似", "异常", "偏高", "偏低", 
                         "趋势", "波动", "建议关注", "可能是", "推测"]
        if any(kw in text for kw in risk_keywords):
            return "risk"
        
        # 历史匹配类
        historical_keywords = ["相似案例", "历史", "类似项目", "RAG", "knowledge",
                               "案例库", "参考案例", "以往"]
        if any(kw in text for kw in historical_keywords):
            return "historical"
        
        # 待核实类
        pending_keywords = ["待核实", "需进一步", "尚需", "有待", "未确认", 
                           "需补充", "资料不足", "无法判断", "口径不一致"]
        if any(kw in text for kw in pending_keywords):
            return "pending"
        
        # 默认：待核实（最安全的默认值）
        return "pending"
    
    def _has_evidence(self, finding: dict) -> bool:
        """判断是否有证据引用"""
        ev_fields = ["evidence", "source", "ref", "attachment", "取证单", "依据"]
        for field in ev_fields:
            if field in finding and finding[field]:
                return True
        # 检查描述中是否引用了证据编号
        desc = str(finding.get("description", finding.get("summary", "")))
        evidence_patterns = [r"取证单[：:]*[A-Za-z0-9\-]+", r"D-\d+", r"附件\d+",
                            r"凭证[：:]*[A-Za-z0-9\-]+"]
        for pat in evidence_patterns:
            if re.search(pat, desc):
                return True
        return False
    
    def generate_report(self, output_path: str = None) -> str:
        """生成四分类复核报告"""
        report = f"""# 审计报告AI复核报告（四分类版）

**复核时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')}
**复核范围**：10维正文复核 + 5维交叉比对（15维全面复核）
**输出格式**：四分类——已确认事实 | 风险提示 | 待核实事项 | 历史相似线索

> ⚠️ 阅读指南
> - **已确认事实**：可直接引用到报告中的问题
> - **风险提示**：需要审计人员进一步判断后再决定是否写入报告
> - **待核实事项**：当前证据不足，建议补充取证后再评估
> - **历史相似线索**：仅供检查方向参考，不是本项目已确认问题
>
> 本输出遵循守拙·审计报告质控四条规矩。

---

## 📊 总体概况

| 分类 | 数量 |
|:-----|:-----|
| ✅ 已确认事实 | {len(self.classified['confirmed'])} |
| ⚠️ 风险提示 | {len(self.classified['risk'])} |
| ❓ 待核实事项 | {len(self.classified['pending'])} |
| 📚 历史相似线索 | {len(self.classified['historical'])} |
| **合计** | **{sum(len(v) for v in self.classified.values())}** |

---
"""
        
        # 逐类输出
        for cat_id in ["confirmed", "risk", "pending", "historical"]:
            cat = CATEGORIES[cat_id]
            items = self.classified[cat_id]
            
            if not items:
                report += f"### {cat['label']}\n\n> 无\n\n---\n"
                continue
            
            report += f"## {cat['label']}\n"
            report += f"*{cat['subtitle']}*\n\n"
            
            for j, item in enumerate(items):
                title = item.get("title", item.get("issue", f"发现{self.findings.index(item)+1 if item in self.findings else j+1}"))
                desc = item.get("description", item.get("summary", item.get("detail", "")))
                severity = item.get("severity", "")
                source = item.get("source", item.get("evidence", ""))
                suggestion = item.get("suggestion", item.get("recommendation", ""))
                classify_method = item.get("_classify_method", "")
                
                sev_badge = f"`{severity}` " if severity else ""
                method_badge = "🤖" if classify_method == "auto" else "👤"
                
                report += f"### {method_badge} {sev_badge}{title}\n\n"
                
                if desc:
                    report += f"{desc}\n\n"
                
                if source:
                    report += f"**依据/证据**：{source}\n\n"
                
                if suggestion:
                    report += f"**建议**：{suggestion}\n\n"
                
                # 分类专属标注
                if cat_id == "risk":
                    report += "> ⚠️ 此项为风险提示，非已确认事实。写入报告前需进一步核实。\n\n"
                elif cat_id == "pending":
                    report += "> ❓ 此项证据不足，建议补充取证后重新评估。\n\n"
                elif cat_id == "historical":
                    report += "> 📚 **历史相似线索，非本项目已确认事实。** 过去发生过不代表当前项目也发生了。\n\n"
                
                report += "---\n"
        
        # 人工确认清单
        report += """
## 👤 人工确认三步

### 第一步：回到原始依据
- [ ] 核对AI引用的制度条款是否真实有效（版本/时效/适用范围）
- [ ] 核对AI引用的数据是否与原始资料一致
- [ ] 标注为"待核实"的规定条款是否需要查证

### 第二步：回到本项目证据
- [ ] 逐一核实"已确认事实"的证据是否充分适当
- [ ] 评估"风险提示"是否需要进一步取证
- [ ] 确定"待核实事项"的取证计划和时间安排
- [ ] 判断"历史相似线索"中哪些确实值得检查

### 第三步：回到多级质控
- [ ] 主审复核：确认四分类是否准确
- [ ] 组长复核：确认问题定性、处理意见、报告位置
- [ ] 审计业务会议：最终审定

---
> 📋 依据：守拙·审计报告质控四条规矩 ①每个判断标明来源 ②事实/风险/待核实分开 ③无整改证据不判有效 ④历史匹配标为线索
"""
        
        if output_path:
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
        
        return report


# ── CLI ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser = __import__('argparse').ArgumentParser
    ap = parser(description="审计报告四分类输出后处理器")
    ap.add_argument("--input", required=True, help="审盾复核器JSON输出")
    ap.add_argument("--output", default="output/review_4category.md", help="输出路径")
    ap.add_argument("--manual", help="手动分类映射JSON: {\"0\":\"confirmed\",\"1\":\"risk\",...}")
    args = ap.parse_args()
    
    processor = FourCategoryProcessor()
    processor.load_review_results(args.input)
    
    manual_map = None
    if args.manual:
        manual_map = json.loads(args.manual)
    
    processor.classify(manual_map)
    report = processor.generate_report(args.output)
    print(report)
    print(f"\n📄 四分类报告已保存至：{args.output}")


if __name__ == "__main__":
    main()
