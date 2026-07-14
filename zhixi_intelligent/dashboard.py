"""
数据采集进度看板
==============
按照四川省审计厅合同（N5100012024002699）要求，
按审计行业分类追踪13个行业的数据采集进度，自动生成JSON报告和HTML可视化看板。
"""
import json
from datetime import datetime

# 加载连接器和扫描器（不直接import避免循环依赖，按需）
from .connector import DatabaseConnector
from .scanner import MetadataScanner


class CollectionDashboard:
    """合同约定的数据采集进度管理系统"""

    # 13个行业清单（来自合同第3条第1款）
    INDUSTRIES = [
        "工商", "财政财务", "民生民政", "教科文卫", "社保医保",
        "公积金", "企业及金融机构", "重大投资项目", "公共资源交易",
        "农业", "高校", "医院", "其他"
    ]

    # 状态常量
    STATUS = {
        "pending": "待采集",
        "in_progress": "进行中",
        "completed": "已完成",
        "failed": "采集失败"
    }

    # 状态颜色
    STATUS_COLORS = {
        "pending": "#95A5A6",      # 灰
        "in_progress": "#E67E22",  # 橙
        "completed": "#27AE60",    # 绿
        "failed": "#E74C3C"        # 红
    }

    def __init__(self):
        self.collections = {}       # {行业名: [采集记录列表]}
        self.metadata_scanner = None  # 可选：关联元数据扫描器自动更新行数
        self.db_connector = None

    def bind_scanner(self, connector: DatabaseConnector, scanner: MetadataScanner):
        """绑定连接器和扫描器，使看板能自动从真实数据库更新行数"""
        self.db_connector = connector
        self.metadata_scanner = scanner

    def register(self, industry, data_source, table_count=0, row_count=0,
                 size_gb=0.0, status="completed", note=""):
        """
        登记一次数据采集
        
        参数:
            industry    - 行业名称（必须是INDUSTRIES中的之一）
            data_source - 数据来源单位
            table_count - 采集的表数量
            row_count   - 总行数
            size_gb     - 数据大小(GB)
            status      - 状态: completed/in_progress/pending/failed
            note        - 备注
        
        返回:
            dict: 登记结果
        """
        if industry not in self.INDUSTRIES:
            return {"error": f"未知行业: {industry}，支持行业: {self.INDUSTRIES}"}

        if industry not in self.collections:
            self.collections[industry] = []

        record = {
            "industry": industry,
            "data_source": data_source,
            "table_count": table_count,
            "row_count": row_count,
            "size_gb": round(size_gb, 2),
            "status": status,
            "note": note,
            "time": datetime.now().isoformat()
        }
        self.collections[industry].append(record)
        return {"status": "registered", "record": record}

    def auto_update_from_scan(self, connection_name, industry_map=None):
        """
        从元数据扫描结果自动更新采集进度
        
        参数:
            connection_name: 已扫描的数据库连接名
            industry_map   : 表名到行业的映射，如 {"fiscal_*": "财政财务", "edu_*": "教科文卫"}
                           不传则自动尝试推断
        
        使用前提:
            已调用 scanner.scan(connection_name) 完成元数据扫描
        """
        if not self.metadata_scanner:
            return {"error": "请先调用 bind_scanner() 绑定扫描器"}

        scan_result = self.metadata_scanner.results.get(connection_name)
        if not scan_result:
            return {"error": f"请先对 '{connection_name}' 执行 scan()"}

        # 简单策略：所有表归入行业映射，没有映射的归入"其他"
        if not industry_map:
            industry_map = {}

        industry_stats = {}
        for t in scan_result["tables"]:
            # 匹配行业
            matched = False
            for pattern, industry in industry_map.items():
                if pattern.replace("*", "") in t["table_name"].lower():
                    if industry not in industry_stats:
                        industry_stats[industry] = {"tables": 0, "rows": 0, "size": 0}
                    industry_stats[industry]["tables"] += 1
                    industry_stats[industry]["rows"] += (t.get("row_count") or 0)
                    matched = True
                    break

            if not matched:
                if "其他" not in industry_stats:
                    industry_stats["其他"] = {"tables": 0, "rows": 0, "size": 0}
                industry_stats["其他"]["tables"] += 1
                industry_stats["其他"]["rows"] += (t.get("row_count") or 0)

        # 登记
        for industry, stats in industry_stats.items():
            size_gb = stats["size"] / 1024 ** 3 if stats["size"] > 0 else 0
            self.register(
                industry=industry,
                data_source=f"自动扫描({connection_name})",
                table_count=stats["tables"],
                row_count=stats["rows"],
                size_gb=size_gb,
                status="completed",
                note=f"元数据扫描自动登记"
            )

        return {"status": "updated", "industries_updated": list(industry_stats.keys())}

    def generate_report(self):
        """生成完整采集进度报告"""
        total = len(self.INDUSTRIES)
        completed = 0
        in_progress = 0
        failed = 0
        total_size = 0.0
        total_rows = 0
        total_tables = 0

        details = []
        for industry in self.INDUSTRIES:
            records = self.collections.get(industry, [])
            if records:
                latest = records[-1]
                details.append({
                    "行业": industry,
                    "状态": self.STATUS.get(latest["status"], latest["status"]),
                    "状态码": latest["status"],
                    "数据来源": latest["data_source"],
                    "表数量": latest["table_count"],
                    "总行数": latest["row_count"],
                    "数据大小(GB)": latest["size_gb"],
                    "最后更新": latest["time"],
                    "备注": latest.get("note", "")
                })
                if latest["status"] == "completed":
                    completed += 1
                    total_size += (latest["size_gb"] or 0)
                    total_rows += (latest["row_count"] or 0)
                    total_tables += (latest["table_count"] or 0)
                elif latest["status"] == "in_progress":
                    in_progress += 1
                elif latest["status"] == "failed":
                    failed += 1
            else:
                details.append({
                    "行业": industry,
                    "状态": "待采集",
                    "状态码": "pending",
                    "数据来源": "",
                    "表数量": 0,
                    "总行数": 0,
                    "数据大小(GB)": 0,
                    "最后更新": "",
                    "备注": ""
                })

        pending = total - completed - in_progress - failed

        return {
            "报告生成时间": datetime.now().isoformat(),
            "合同编号": "N5100012024002699",
            "年度目标(TB)": 40,
            "采集进度": f"{completed}/{total} ({completed/total*100:.0f}%)",
            "已完成行业": completed,
            "进行中行业": in_progress,
            "失败行业": failed,
            "待采集行业": pending,
            "已采集数据量(GB)": round(total_size, 2),
            "已采集总行数": total_rows,
            "已采集总表数": total_tables,
            "年度完成率": f"{total_size/40000*100:.2f}%",
            "行业明细": details
        }

    def save_report(self, filepath):
        """保存JSON格式报告"""
        report = self.generate_report()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        return {"status": "saved", "path": filepath, "report": report}

    def render_html(self, report=None):
        """生成可视化HTML数据采集进度看板"""
        if report is None:
            report = self.generate_report()

        progress_pct = (
            sum(1 for d in report["行业明细"] if d["状态码"] != "pending")
            / len(report["行业明细"]) * 100
        )

        rows_html = ""
        for d in report["行业明细"]:
            row_count_str = f"{d['总行数']:,}" if d["总行数"] else "-"
            size_str = f"{d['数据大小(GB)']} GB" if d["数据大小(GB)"] else "-"
            color = self.STATUS_COLORS.get(d["状态码"], "#95A5A6")

            rows_html += f"""
            <tr>
                <td><strong>{d['行业']}</strong></td>
                <td>{d.get('数据来源') or '-'}</td>
                <td style="text-align:center">{d['表数量']}</td>
                <td style="text-align:right">{row_count_str}</td>
                <td style="text-align:right">{size_str}</td>
                <td style="text-align:center"><span class="status-badge" style="background:{color}">{d['状态']}</span></td>
                <td style="font-size:11px;color:#7f8c8d">{d.get('最后更新', '-')[:16] or '-'}</td>
            </tr>"""

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>数据采集进度看板 - 智析智能</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Microsoft YaHei',-apple-system,sans-serif;background:#f0f2f5;padding:24px;color:#333}}
.header{{background:linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);color:white;padding:24px 28px;border-radius:12px;margin-bottom:20px}}
.header h1{{font-size:22px;margin-bottom:4px}}
.header .sub{{font-size:13px;opacity:0.75}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:20px}}
.card{{background:white;border-radius:10px;padding:20px;box-shadow:0 1px 4px rgba(0,0,0,0.06)}}
.card .label{{font-size:12px;color:#7f8c8d;margin-bottom:8px;text-transform:uppercase;letter-spacing:0.5px}}
.card .value{{font-size:28px;font-weight:700;color:#2c3e50}}
.card .sub{{font-size:12px;color:#95a5a6;margin-top:4px}}
.card.green .value{{color:#27AE60}}
.card.orange .value{{color:#E67E22}}
.card.red .value{{color:#E74C3C}}
.card.blue .value{{color:#2980B9}}
.progress-section{{background:white;border-radius:10px;padding:20px;margin-bottom:20px;box-shadow:0 1px 4px rgba(0,0,0,0.06)}}
.progress-section h3{{font-size:14px;color:#7f8c8d;margin-bottom:12px}}
.progress-bar{{background:#ecf0f1;border-radius:12px;height:28px;overflow:hidden;position:relative}}
.progress-fill{{background:linear-gradient(90deg,#27AE60,#2ECC71);height:100%;border-radius:12px;transition:width 0.6s ease;display:flex;align-items:center;justify-content:flex-end;padding-right:12px;color:white;font-weight:600;font-size:13px;min-width:60px}}
table{{width:100%;background:white;border-radius:10px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.06);border-collapse:collapse}}
th{{background:#2980B9;color:white;padding:12px 14px;text-align:left;font-size:12px;font-weight:600;letter-spacing:0.5px}}
td{{padding:11px 14px;border-bottom:1px solid #f0f0f0;font-size:13px}}
tr:last-child td{{border-bottom:none}}
tr:hover{{background:#f8f9ff}}
.status-badge{{display:inline-block;padding:3px 10px;border-radius:12px;color:white;font-size:12px;white-space:nowrap}}
.footer{{text-align:center;margin-top:24px;color:#95a5a6;font-size:11px}}
</style>
</head>
<body>
<div class="header">
<h1>📊 四川省审计厅 · 数据采集进度看板</h1>
<div class="sub">智析智能 · 融策数据采集管理平台 | 报告时间: {report['报告生成时间'][:19]}</div>
</div>

<div class="cards">
<div class="card green">
    <div class="label">采集进度</div>
    <div class="value">{report['采集进度']}</div>
    <div class="sub">共13个行业</div>
</div>
<div class="card blue">
    <div class="label">已采集数据量</div>
    <div class="value">{report['已采集数据量(GB)']:.1f} GB</div>
    <div class="sub">年度目标40TB | {report['年度完成率']}</div>
</div>
<div class="card">
    <div class="label">已采集表数</div>
    <div class="value">{report['已采集总表数']:,}</div>
    <div class="sub">共{report['已采集总行数']:,}行数据</div>
</div>
<div class="card orange">
    <div class="label">进行中</div>
    <div class="value">{report['进行中行业']}</div>
    <div class="sub">{report['已完成行业']}个已完成 / {report['待采集行业']}个待采集</div>
</div>
</div>

<div class="progress-section">
<h3>整体进度</h3>
<div class="progress-bar">
<div class="progress-fill" style="width:{progress_pct:.1f}%">{progress_pct:.0f}%</div>
</div>
</div>

<table>
<thead>
<tr>
    <th style="width:120px">行业</th>
    <th style="width:180px">数据来源</th>
    <th style="width:60px;text-align:center">表数</th>
    <th style="width:100px;text-align:right">总行数</th>
    <th style="width:80px;text-align:right">数据量</th>
    <th style="width:80px;text-align:center">状态</th>
    <th style="width:140px">更新时间</th>
</tr>
</thead>
<tbody>{rows_html}</tbody>
</table>

<div class="footer">智析智能 v1.0 | 融策会计师事务所 | 数据采集进度管理</div>
</body>
</html>"""
        return html

    def save_html(self, filepath, report=None):
        """保存HTML看板"""
        html = self.render_html(report)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        return {"status": "saved", "path": filepath}
