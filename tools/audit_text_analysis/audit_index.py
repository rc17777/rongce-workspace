"""
P2: 独立索引子系统 (5d)

审计底稿交叉引用索引系统，支持：
1. 自动分配唯一索引号
2. 索引条目增删改查
3. 交叉引用完整性校验（闭环检测）
4. 全文搜索
5. 索引与底稿文件的双向追踪

索引格式示例: WP-ARR-001 / EV-PMT-003 / CT-ENG-015
  WP = Workpaper（底稿）
  EV = Evidence（证据）
  CT = Contract（合同）
  PM = Payment（支付记录）
  AP = Approval（审批）
  RP = Report（报告）
"""

import re
import json
import os
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path


# ── 索引类型 ──────────────────────────────────────────────

INDEX_PREFIXES = {
    "WP": "工作底稿",
    "EV": "审计证据",
    "CT": "合同文件",
    "PM": "支付记录",
    "AP": "审批文件",
    "RP": "审计报告",
    "MM": "会议纪要",
    "PL": "人员名单",
    "RV": "复核记录",
    "EX": "例外事项",
    "FX": "函证记录",
    "IM": "整改材料",
}


@dataclass
class IndexEntry:
    """索引条目"""
    index_id: str              # 唯一索引号: WP-ARR-001
    title: str                 # 标题
    entry_type: str            # 索引类型前缀
    category: str              # 分类（如 ARR=应收账款）
    sequence: int              # 序号
    file_path: str = ""        # 文件路径
    description: str = ""      # 描述

    # 交叉引用
    refs_from: List[str] = field(default_factory=list)    # 引用本条的索引号
    refs_to: List[str] = field(default_factory=list)      # 本条引用的索引号

    # 元信息
    created_at: str = ""
    updated_at: str = ""
    audit_program_ref: str = ""
    assertions: List[str] = field(default_factory=list)

    # 状态
    status: str = "active"     # active | archived | void
    reviewed: bool = False
    review_level: int = 0      # 0=未复核, 1=L1, 2=L2, 3=L3

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at


@dataclass
class IndexValidationResult:
    """索引校验结果"""
    total_entries: int
    valid_refs: int
    broken_refs: int            # 断链：引用了不存在的索引
    orphan_entries: int         # 孤岛：无任何引用关系
    completeness: float         # 引用完整性 0-1
    broken_details: List[Dict[str, str]] = field(default_factory=list)
    orphan_details: List[str] = field(default_factory=list)


class AuditIndexSystem:
    """
    审计索引子系统

    用法:
        idx = AuditIndexSystem("2024年度经责审计")
        idx.add_entry("WP", "ARR", "应收账款存在性测试底稿", file_path="...")
        idx.add_ref("WP-ARR-001", "EV-INV-005")  # 底稿引用证据
        idx.validate()  # 校验完整性
    """

    def __init__(self, project_name: str = ""):
        self.project_name = project_name
        self.entries: Dict[str, IndexEntry] = {}
        self._counters: Dict[str, Dict[str, int]] = {}  # {prefix: {category: count}}

    # ── CRUD ─────────────────────────────────────────────

    def _next_sequence(self, prefix: str, category: str) -> int:
        """获取下一个序号"""
        if prefix not in self._counters:
            self._counters[prefix] = {}
        if category not in self._counters[prefix]:
            # 扫描已有条目获取最大值
            existing = [
                e.sequence for e in self.entries.values()
                if e.entry_type == prefix and e.category == category
            ]
            self._counters[prefix][category] = max(existing) + 1 if existing else 1
        else:
            self._counters[prefix][category] += 1

        return self._counters[prefix][category]

    def _make_index_id(self, prefix: str, category: str, sequence: int) -> str:
        """组装索引号"""
        return f"{prefix}-{category}-{sequence:03d}"

    def add_entry(
        self,
        entry_type: str,
        category: str,
        title: str,
        file_path: str = "",
        description: str = "",
        assertions: Optional[List[str]] = None,
        index_id: Optional[str] = None,
    ) -> str:
        """
        添加索引条目

        Args:
            entry_type: 类型前缀 (WP/EV/CT/...)
            category: 分类 (ARR=应收账款/INV=存货/...)
            title: 标题
            file_path: 文件路径
            description: 描述
            assertions: 对应的审计认定
            index_id: 手动指定索引号（可选，默认自动生成）

        Returns:
            生成的索引号
        """
        if entry_type not in INDEX_PREFIXES:
            raise ValueError(f"未知索引类型: {entry_type}，可选: {list(INDEX_PREFIXES.keys())}")

        seq = self._next_sequence(entry_type, category)

        if index_id is None:
            index_id = self._make_index_id(entry_type, category, seq)
        else:
            # 手动指定索引号时更新计数器
            match = re.match(rf"(\w+)-(\w+)-(\d+)", index_id)
            if match:
                self._counters[entry_type][category] = max(
                    seq, int(match.group(3))
                )

        entry = IndexEntry(
            index_id=index_id,
            title=title,
            entry_type=entry_type,
            category=category,
            sequence=seq,
            file_path=file_path,
            description=description,
            assertions=assertions or [],
        )
        self.entries[index_id] = entry
        return index_id

    def get_entry(self, index_id: str) -> Optional[IndexEntry]:
        """获取索引条目"""
        return self.entries.get(index_id)

    def update_entry(
        self, index_id: str, **kwargs
    ) -> Optional[IndexEntry]:
        """更新索引条目"""
        entry = self.entries.get(index_id)
        if not entry:
            return None

        for key, value in kwargs.items():
            if hasattr(entry, key):
                setattr(entry, key, value)

        entry.updated_at = datetime.now().isoformat()
        return entry

    def delete_entry(self, index_id: str) -> bool:
        """删除索引条目（同时清理双向引用）"""
        if index_id not in self.entries:
            return False

        # 清理被引用关系
        for e in self.entries.values():
            if index_id in e.refs_to:
                e.refs_to.remove(index_id)
            if index_id in e.refs_from:
                e.refs_from.remove(index_id)

        del self.entries[index_id]
        return True

    # ── 交叉引用管理 ─────────────────────────────────────

    def add_ref(self, from_id: str, to_id: str) -> bool:
        """
        添加交叉引用

        Args:
            from_id: 引用方索引号
            to_id: 被引用方索引号

        Returns:
            是否成功
        """
        if from_id not in self.entries or to_id not in self.entries:
            return False
        if from_id == to_id:
            return False  # 不能自引用

        from_entry = self.entries[from_id]
        to_entry = self.entries[to_id]

        if to_id not in from_entry.refs_to:
            from_entry.refs_to.append(to_id)
        if from_id not in to_entry.refs_from:
            to_entry.refs_from.append(from_id)

        from_entry.updated_at = datetime.now().isoformat()
        return True

    def remove_ref(self, from_id: str, to_id: str) -> bool:
        """移除交叉引用"""
        if from_id not in self.entries or to_id not in self.entries:
            return False

        from_entry = self.entries[from_id]
        to_entry = self.entries[to_id]

        if to_id in from_entry.refs_to:
            from_entry.refs_to.remove(to_id)
        if from_id in to_entry.refs_from:
            to_entry.refs_from.remove(from_id)

        return True

    def get_ref_chain(self, start_id: str, max_depth: int = 5) -> List[List[str]]:
        """
        获取引用链（BFS遍历）

        Returns:
            路径列表，如 [["WP-ARR-001", "EV-INV-005", "PM-001-012"]]
        """
        if start_id not in self.entries:
            return []

        chains = []
        visited = {start_id}
        queue = [[start_id]]

        while queue:
            path = queue.pop(0)
            if len(path) > max_depth:
                continue

            current = path[-1]
            entry = self.entries.get(current)
            if not entry:
                chains.append(path)
                continue

            has_next = False
            for ref in entry.refs_to:
                if ref not in visited:
                    visited.add(ref)
                    queue.append(path + [ref])
                    has_next = True

            if not has_next:
                chains.append(path)

        return chains

    # ── 校验 ────────────────────────────────────────────

    def validate(self) -> IndexValidationResult:
        """
        索引完整性校验

        检测：
        1. 断链：引用了不存在的索引号
        2. 孤岛：条目无任何引用关系
        3. 循环引用（简单检测）
        """
        all_ids = set(self.entries.keys())
        broken = []
        orphans = []

        for entry in self.entries.values():
            # 断链检测
            for ref in entry.refs_to:
                if ref not in all_ids:
                    broken.append({
                        "from": entry.index_id,
                        "to": ref,
                        "error": "引用目标不存在",
                    })

            # 孤岛检测
            if not entry.refs_from and not entry.refs_to:
                orphans.append(entry.index_id)

        total = len(self.entries)
        valid_refs = total - len(broken) - len(orphans)
        completeness = valid_refs / total if total > 0 else 1.0

        return IndexValidationResult(
            total_entries=total,
            valid_refs=valid_refs,
            broken_refs=len(broken),
            orphan_entries=len(orphans),
            completeness=round(completeness, 4),
            broken_details=broken,
            orphan_details=orphans,
        )

    # ── 搜索 ────────────────────────────────────────────

    def search(self, query: str) -> List[IndexEntry]:
        """全文搜索"""
        query_lower = query.lower()
        return [
            e for e in self.entries.values()
            if query_lower in e.title.lower()
            or query_lower in e.index_id.lower()
            or query_lower in e.description.lower()
        ]

    def list_by_type(self, entry_type: str) -> List[IndexEntry]:
        """按类型列出"""
        return [
            e for e in self.entries.values()
            if e.entry_type == entry_type
        ]

    def list_by_category(self, category: str) -> List[IndexEntry]:
        """按分类列出"""
        return [
            e for e in self.entries.values()
            if e.category == category
        ]

    def list_unreviewed(self) -> List[IndexEntry]:
        """列出未复核条目"""
        return [e for e in self.entries.values() if not e.reviewed]

    # ── 统计 ────────────────────────────────────────────

    @property
    def stats(self) -> Dict[str, Any]:
        """系统统计"""
        types = {}
        for e in self.entries.values():
            types[e.entry_type] = types.get(e.entry_type, 0) + 1

        validation = self.validate()

        return {
            "project": self.project_name,
            "total_entries": len(self.entries),
            "by_type": types,
            "reviewed": sum(1 for e in self.entries.values() if e.reviewed),
            "unreviewed": sum(1 for e in self.entries.values() if not e.reviewed),
            "total_refs": sum(
                len(e.refs_to) for e in self.entries.values()
            ),
            "completeness": f"{validation.completeness:.1%}",
            "broken_refs": validation.broken_refs,
            "orphan_entries": validation.orphan_entries,
        }

    # ── 可视化 ──────────────────────────────────────────

    def to_mermaid(self) -> str:
        """生成Mermaid流程图（可在Markdown中渲染引用关系图）"""
        lines = ["graph LR"]
        lines.append(f'    title["{self.project_name} 索引关系图"]')

        for entry in self.entries.values():
            node_id = entry.index_id.replace("-", "_")
            label = f"{entry.index_id}<br/>{entry.title[:15]}"
            lines.append(f'    {node_id}["{label}"]')

        for entry in self.entries.values():
            from_id = entry.index_id.replace("-", "_")
            for ref in entry.refs_to:
                to_id = ref.replace("-", "_")
                lines.append(f"    {from_id} --> {to_id}")

        return "\n".join(lines)

    def to_table(self) -> str:
        """生成Markdown索引表"""
        lines = [
            f"# {self.project_name} — 索引表",
            "",
            "| 索引号 | 类型 | 标题 | 引用→ | 被引用← | 状态 |",
            "|--------|------|------|--------|---------|------|",
        ]

        for e in sorted(self.entries.values(), key=lambda x: x.index_id):
            refs_to = ", ".join(e.refs_to[:3])
            if len(e.refs_to) > 3:
                refs_to += f"等{len(e.refs_to)}项"
            refs_from = ", ".join(e.refs_from[:3])
            if len(e.refs_from) > 3:
                refs_from += f"等{len(e.refs_from)}项"

            review_status = f"L{e.review_level}" if e.reviewed else "未复核"

            lines.append(
                f"| {e.index_id} | {INDEX_PREFIXES.get(e.entry_type, e.entry_type)} "
                f"| {e.title[:30]} | {refs_to or '-'} | {refs_from or '-'} "
                f"| {review_status} |"
            )

        return "\n".join(lines)

    # ── 序列化 ──────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """序列化"""
        return {
            "project_name": self.project_name,
            "entries": [
                {
                    "index_id": e.index_id,
                    "title": e.title,
                    "entry_type": e.entry_type,
                    "category": e.category,
                    "sequence": e.sequence,
                    "file_path": e.file_path,
                    "description": e.description,
                    "refs_to": e.refs_to,
                    "refs_from": e.refs_from,
                    "assertions": e.assertions,
                    "status": e.status,
                    "reviewed": e.reviewed,
                    "review_level": e.review_level,
                    "created_at": e.created_at,
                }
                for e in self.entries.values()
            ],
        }

    def to_json(self, filepath: str):
        """保存为JSON"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, filepath: str) -> "AuditIndexSystem":
        """从JSON加载"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        idx = cls(project_name=data.get("project_name", ""))
        for e_data in data.get("entries", []):
            entry = IndexEntry(
                index_id=e_data["index_id"],
                title=e_data["title"],
                entry_type=e_data["entry_type"],
                category=e_data["category"],
                sequence=e_data["sequence"],
                file_path=e_data.get("file_path", ""),
                description=e_data.get("description", ""),
                refs_to=e_data.get("refs_to", []),
                refs_from=e_data.get("refs_from", []),
                assertions=e_data.get("assertions", []),
                status=e_data.get("status", "active"),
                reviewed=e_data.get("reviewed", False),
                review_level=e_data.get("review_level", 0),
                created_at=e_data.get("created_at", ""),
            )
            idx.entries[entry.index_id] = entry

        return idx

    # ── 导入导出 ──────────────────────────────────────────

    def batch_import(
        self, items: List[Dict[str, Any]]
    ) -> List[str]:
        """批量导入索引条目"""
        ids = []
        for item in items:
            idx_id = self.add_entry(
                entry_type=item.get("entry_type", "WP"),
                category=item.get("category", "GEN"),
                title=item.get("title", ""),
                file_path=item.get("file_path", ""),
                description=item.get("description", ""),
                assertions=item.get("assertions"),
                index_id=item.get("index_id"),
            )
            ids.append(idx_id)
        return ids

    def extract_refs_from_text(
        self, text: str
    ) -> List[str]:
        """
        从文本中自动提取索引引用

        识别模式：WP-XXX-NNN, EV-XXX-NNN 等
        """
        pattern = r'\b([A-Z]{2,3})-(\w{2,6})-(\d{3,4})\b'
        matches = re.findall(pattern, text)
        return [f"{m[0]}-{m[1]}-{m[2]}" for m in matches]

    def auto_link_from_text(
        self, index_id: str, text: str
    ) -> int:
        """
        从文本自动建立交叉引用

        扫描文本中的索引号，自动创建引用关系
        """
        refs = self.extract_refs_from_text(text)
        linked = 0
        for ref in refs:
            if ref in self.entries and ref != index_id:
                if self.add_ref(index_id, ref):
                    linked += 1
        return linked
