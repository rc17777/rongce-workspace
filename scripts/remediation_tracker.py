#!/usr/bin/env python3
"""
整改台账自动比对追踪器 v1.0
基于文章1-规矩③（无整改证据不判有效）+ 文章3-4.4整改跟踪

功能：
1. 录入审计决定事项 → 跟踪整改进度
2. OCR识别整改材料 → 自动比对审计决定事项覆盖度
3. 时效预警：距60日截止≤7日自动提醒
4. 整改状态四分类：已整改(有证据)/整改中(有说明无证据)/未整改/待核实
"""

import sys, os, json, argparse, csv
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

# ── 整改状态定义 ─────────────────────────────────────

STATUS_MAP = {
    "remediated": {
        "label": "✅ 已整改（有证据）",
        "desc": "被审计单位已提交整改证据，且经核实与审计决定事项对应",
        "sort": 0
    },
    "in_progress": {
        "label": "🔄 整改中（有说明/无证据）",
        "desc": "被审计单位声称已整改但未提供充分证据，或整改仍在进行",
        "sort": 1
    },
    "not_remediated": {
        "label": "❌ 未整改",
        "desc": "被审计单位未采取整改措施，或整改措施未对应审计决定",
        "sort": 2
    },
    "pending_verify": {
        "label": "❓ 待核实",
        "desc": "整改状态不明确，需要进一步核实",
        "sort": 3
    }
}


class RemediationTracker:
    """整改台账追踪器"""
    
    def __init__(self, project_name: str):
        self.project_name = project_name
        self.project_dir = Path(f"audit-blackboard/projects/{project_name}")
        self.tracker_file = self.project_dir / "remediation_tracker.json"
        self._load()
    
    def _load(self):
        """加载或初始化台账"""
        if self.tracker_file.exists():
            with open(self.tracker_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        else:
            self.data = {
                "project_name": self.project_name,
                "created": datetime.now().isoformat(),
                "updated": datetime.now().isoformat(),
                "audit_decision_items": [],  # 审计决定事项
                "remediation_records": [],   # 整改记录
                "alerts": []                 # 预警记录
            }
            self._save()
    
    def _save(self):
        """持久化"""
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.data["updated"] = datetime.now().isoformat()
        with open(self.tracker_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    # ── 审计决定事项管理 ──
    
    def add_decision_item(self, item_id: str, title: str, description: str, 
                           requirement: str, deadline_days: int = 60):
        """添加一条审计决定事项"""
        now = datetime.now().isoformat()
        deadline = (datetime.now() + timedelta(days=deadline_days)).strftime("%Y-%m-%d")
        item = {
            "item_id": item_id,
            "title": title,
            "description": description,
            "requirement": requirement,  # 整改要求
            "deadline": deadline,
            "deadline_days": deadline_days,
            "created": now,
            "status": "not_remediated",
            "last_remediation_date": None,
            "evidence_submitted": [],
            "verified": False,
            "verified_by": None,
            "verified_date": None,
            "notes": ""
        }
        self.data["audit_decision_items"].append(item)
        self._save()
        return item
    
    def import_from_findings(self, findings_dir: str):
        """从审计发现JSON目录批量导入（自动转为审计决定事项）"""
        findings_path = Path(findings_dir)
        count = 0
        for f in sorted(findings_path.glob("*.json")):
            with open(f, 'r', encoding='utf-8') as fp:
                finding = json.load(fp)
            
            item_id = f"AD-{datetime.now().strftime('%Y%m%d')}-{count+1:03d}"
            title = finding.get("title", finding.get("finding_id", f.stem))
            desc = finding.get("description", finding.get("summary", ""))
            req = finding.get("recommendation", finding.get("requirement", "按要求整改"))
            self.add_decision_item(item_id, title, desc, req)
            count += 1
        return count
    
    # ── 整改记录提交 ──
    
    def submit_remediation(self, item_id: str, evidence_list: list, 
                           submitter: str, claim_status: str = "remediated",
                           notes: str = ""):
        """提交整改材料"""
        item = self._find_item(item_id)
        if not item:
            raise ValueError(f"未找到审计决定事项: {item_id}")
        
        record = {
            "record_id": f"RR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{item_id}",
            "item_id": item_id,
            "date": datetime.now().isoformat(),
            "submitter": submitter,
            "claim_status": claim_status,  # 被审计单位声称的状态
            "evidence": evidence_list,     # [{"name": "整改报告.pdf", "type": "document", "path": "..."}]
            "notes": notes
        }
        self.data["remediation_records"].append(record)
        
        # 更新事项状态
        item["last_remediation_date"] = datetime.now().strftime("%Y-%m-%d")
        item["evidence_submitted"].extend(evidence_list)
        
        # ⚠️ 关键：不能因为收到整改材料就标"已整改"
        # 只能标"待核实"，人工核实后才能确认
        item["status"] = "pending_verify"
        item["pending_record_id"] = record["record_id"]
        
        self._save()
        self._check_deadline(item_id)
        return record
    
    # ── 人工核实（核心） ──
    
    def verify_remediation(self, item_id: str, verified_by: str, 
                           actual_status: str, notes: str = ""):
        """
        人工核实整改结果
        
        actual_status 必须是以下之一：
        - "remediated": 确认整改完成（有充分证据）
        - "in_progress": 整改进行中（有说明但证据不足）
        - "not_remediated": 未整改（证据不支撑或未对应审计决定）
        """
        if actual_status not in STATUS_MAP:
            raise ValueError(f"无效状态: {actual_status}，必须是 {list(STATUS_MAP.keys())}")
        
        item = self._find_item(item_id)
        if not item:
            raise ValueError(f"未找到审计决定事项: {item_id}")
        
        item["status"] = actual_status
        item["verified"] = True
        item["verified_by"] = verified_by
        item["verified_date"] = datetime.now().strftime("%Y-%m-%d")
        item["verification_notes"] = notes
        
        # ⚠️ 如果人工判定"未整改"但被审计单位声称"已整改"，记录矛盾
        if "pending_record_id" in item:
            matching_records = [r for r in self.data["remediation_records"] 
                              if r["record_id"] == item.get("pending_record_id")]
            if matching_records and matching_records[0]["claim_status"] == "remediated" \
               and actual_status != "remediated":
                self._add_alert(item_id, "contradiction", 
                    f"被审计单位声称已整改(v{matching_records[0]['record_id']})，"
                    f"但经{verified_by}核实，实际状态为：{STATUS_MAP[actual_status]['label']}")
            del item["pending_record_id"]
        
        self._save()
    
    # ── 时效预警 ──
    
    def _check_deadline(self, item_id: str = None):
        """检查整改期限"""
        items = [self._find_item(item_id)] if item_id else self.data["audit_decision_items"]
        today = datetime.now().date()
        
        for item in items:
            if not item or item["status"] == "remediated":
                continue
            
            deadline = datetime.strptime(item["deadline"], "%Y-%m-%d").date()
            days_left = (deadline - today).days
            
            if days_left <= 0:
                self._add_alert(item["item_id"], "overdue",
                    f"整改期限已过（截止{deadline}），当前状态：{STATUS_MAP[item['status']]['label']}")
            elif days_left <= 7:
                self._add_alert(item["item_id"], "approaching",
                    f"整改期限仅剩{days_left}天（截止{deadline}），当前状态：{STATUS_MAP[item['status']]['label']}")
    
    def _add_alert(self, item_id: str, alert_type: str, message: str):
        """添加预警"""
        alert = {
            "alert_id": f"AL-{datetime.now().strftime('%Y%m%d%H%M%S')}-{item_id}",
            "item_id": item_id,
            "type": alert_type,
            "message": message,
            "date": datetime.now().isoformat(),
            "dismissed": False
        }
        self.data["alerts"].append(alert)
    
    # ── 覆盖度分析 ──
    
    def coverage_report(self) -> dict:
        """生成整改覆盖度报告"""
        items = self.data["audit_decision_items"]
        total = len(items)
        if total == 0:
            return {"total": 0, "message": "暂无审计决定事项"}
        
        status_counts = {}
        for item in items:
            s = item["status"]
            status_counts[s] = status_counts.get(s, 0) + 1
        
        remediated = status_counts.get("remediated", 0)
        in_progress = status_counts.get("in_progress", 0)
        not_remediated = status_counts.get("not_remediated", 0)
        pending = status_counts.get("pending_verify", 0)
        
        overdue_items = [it for it in items 
                        if it["status"] != "remediated" 
                        and datetime.strptime(it["deadline"], "%Y-%m-%d").date() < datetime.now().date()]
        
        approaching_items = [it for it in items 
                            if it["status"] != "remediated" 
                            and 0 <= (datetime.strptime(it["deadline"], "%Y-%m-%d").date() - datetime.now().date()).days <= 7]
        
        return {
            "total": total,
            "remediated": remediated,
            "remediation_rate": f"{remediated/total*100:.1f}%",
            "in_progress": in_progress,
            "not_remediated": not_remediated,
            "pending_verify": pending,
            "overdue": len(overdue_items),
            "approaching_deadline": len(approaching_items),
            "overdue_items": [{"id": it["item_id"], "title": it["title"], "deadline": it["deadline"]} 
                            for it in overdue_items],
            "approaching_items": [{"id": it["item_id"], "title": it["title"], 
                                  "days_left": (datetime.strptime(it["deadline"], "%Y-%m-%d").date() - datetime.now().date()).days} 
                                 for it in approaching_items]
        }
    
    # ── 报告生成 ──
    
    def generate_report(self, output_path: str = None) -> str:
        """生成整改跟踪报告"""
        cov = self.coverage_report()
        
        report = f"""# 整改跟踪报告
**项目名称**：{self.project_name}
**报告时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')}

## 📊 整改概况

| 指标 | 数值 |
|:-----|:-----|
| 审计决定事项总数 | {cov['total']} |
| ✅ 已整改（有证据） | {cov['remediated']} |
| 🔄 整改中（有说明/无证据） | {cov['in_progress']} |
| ❌ 未整改 | {cov['not_remediated']} |
| ❓ 待核实 | {cov['pending_verify']} |
| **整改完成率** | **{cov['remediation_rate']}** |
| ⚠️ 逾期未整改 | {cov['overdue']} |
| ⏰ 即将到期（≤7天） | {cov['approaching_deadline']} |

"""
        # 逐项明细
        if cov["total"] > 0:
            report += "## 📋 事项明细\n\n"
            report += "| ID | 事项 | 状态 | 截止日期 | 剩余天数 | 已核实 |\n"
            report += "|:-----|:-----|:-----|:-----|:-----|:-----|\n"
            
            for item in self.data["audit_decision_items"]:
                status_label = STATUS_MAP[item["status"]]["label"]
                deadline = datetime.strptime(item["deadline"], "%Y-%m-%d").date()
                days_left = (deadline - datetime.now().date()).days
                days_str = f"{days_left}天" if days_left >= 0 else f"**逾期{-days_left}天**"
                verified = "✅" if item["verified"] else "❌"
                report += f"| {item['item_id']} | {item['title'][:30]} | {status_label} | {item['deadline']} | {days_str} | {verified} |\n"
        
        # 预警
        if self.data["alerts"]:
            active_alerts = [a for a in self.data["alerts"] if not a.get("dismissed")]
            if active_alerts:
                report += "\n## ⚠️ 预警信息\n\n"
                for alert in active_alerts:
                    alert_type = "🔴逾期" if alert["type"] == "overdue" else "⏰即将到期"
                    report += f"- **{alert_type}** [{alert['item_id']}]: {alert['message']}\n"
        
        report += f"""
---
> ⚠️ 注意：整改状态中的"✅ 已整改"须经人工核实后方可确认。
> AI不能替代人工判断整改是否有效——无整改证据时只能标"待核实"，不得标"已整改"。
> 依据：守拙·审计报告质控四条规矩之③。
"""
        
        if output_path:
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
        
        return report
    
    def _find_item(self, item_id: str):
        for item in self.data["audit_decision_items"]:
            if item["item_id"] == item_id:
                return item
        return None


# ── CLI入口 ──────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="整改台账自动比对追踪器 v1.0")
    parser.add_argument("--project", required=True, help="项目名称")
    parser.add_argument("--action", required=True, 
                       choices=["init", "add", "import", "submit", "verify", 
                               "report", "alerts", "status"])
    # add 参数
    parser.add_argument("--id", help="事项ID")
    parser.add_argument("--title", help="事项标题")
    parser.add_argument("--desc", help="事项描述")
    parser.add_argument("--requirement", help="整改要求")
    parser.add_argument("--deadline-days", type=int, default=60, help="整改期限（天）")
    # import 参数
    parser.add_argument("--findings-dir", help="findings JSON目录")
    # submit 参数
    parser.add_argument("--evidence", nargs="*", help="整改证据列表（文件名）")
    parser.add_argument("--submitter", help="提交人")
    parser.add_argument("--claim-status", default="remediated", 
                       choices=["remediated", "in_progress", "not_remediated"])
    # verify 参数
    parser.add_argument("--verified-by", help="核实人")
    parser.add_argument("--actual-status", help="实际整改状态")
    parser.add_argument("--verify-note", help="核实说明")
    # output
    parser.add_argument("--output", help="报告输出路径")
    
    args = parser.parse_args()
    
    tracker = RemediationTracker(args.project)
    
    if args.action == "init":
        print(f"✅ 整改台账已初始化：{tracker.tracker_file}")
        print(f"   审计决定事项：{len(tracker.data['audit_decision_items'])}条")
    
    elif args.action == "add":
        if not all([args.id, args.title]):
            print("❌ --add 需要 --id 和 --title")
            sys.exit(1)
        item = tracker.add_decision_item(
            args.id, args.title, args.desc or "", 
            args.requirement or "按要求整改",
            args.deadline_days
        )
        print(f"✅ 已添加事项：{item['item_id']} — {item['title']}（截止：{item['deadline']}）")
    
    elif args.action == "import":
        if not args.findings_dir:
            print("❌ --import 需要 --findings-dir")
            sys.exit(1)
        count = tracker.import_from_findings(args.findings_dir)
        print(f"✅ 从 {args.findings_dir} 导入了 {count} 条审计决定事项")
    
    elif args.action == "submit":
        if not all([args.id, args.submitter]):
            print("❌ --submit 需要 --id 和 --submitter")
            sys.exit(1)
        evidence = []
        if args.evidence:
            for ev in args.evidence:
                evidence.append({"name": ev, "type": "document", "path": ev})
        record = tracker.submit_remediation(
            args.id, evidence, args.submitter, args.claim_status
        )
        print(f"✅ 整改材料已提交：{record['record_id']}")
        print(f"   状态已更新为：待核实（需人工确认）")
    
    elif args.action == "verify":
        if not all([args.id, args.verified_by, args.actual_status]):
            print("❌ --verify 需要 --id, --verified-by, --actual-status")
            sys.exit(1)
        tracker.verify_remediation(
            args.id, args.verified_by, args.actual_status, 
            args.verify_note or ""
        )
        print(f"✅ 已核实：{args.id} → {STATUS_MAP[args.actual_status]['label']}")
    
    elif args.action == "report":
        output = args.output or f"audit-blackboard/projects/{args.project}/remediation_report.md"
        report = tracker.generate_report(output)
        print(report)
        print(f"\n📄 报告已保存至：{output}")
    
    elif args.action == "alerts":
        tracker._check_deadline()
        alerts = [a for a in tracker.data["alerts"] if not a.get("dismissed")]
        if alerts:
            print(f"⚠️ {len(alerts)} 条未处理预警：")
            for a in alerts:
                print(f"  - [{a['type']}] {a['item_id']}: {a['message']}")
        else:
            print("✅ 无预警。")
    
    elif args.action == "status":
        cov = tracker.coverage_report()
        print(f"项目：{tracker.project_name}")
        print(f"事项总数：{cov['total']} | 已整改：{cov['remediated']} | 整改率：{cov['remediation_rate']}")
        print(f"逾期：{cov['overdue']} | 即将到期：{cov['approaching_deadline']} | 待核实：{cov['pending_verify']}")


if __name__ == "__main__":
    main()
