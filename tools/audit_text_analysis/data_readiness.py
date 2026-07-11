"""
P1: 非结构化数据就绪度评估 (2d)

针对政府审计场景中纸质材料比例高的痛点，
在审计项目启动前对数据源进行分类评估：
  L1 绿色：结构化数据（数据库/API，直接可用）
  L2 黄色：半结构化数据（Excel/PDF表单，需解析）
  L3 红色：非结构化数据（扫描件/手写/图片，需OCR+纠错）

输出就绪度仪表盘和无纸化建议。
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import os


class DataReadinessLevel(Enum):
    L1_GREEN = "L1_绿色"
    L2_YELLOW = "L2_黄色"
    L3_RED = "L3_红色"


@dataclass
class DataSource:
    """单个数据源"""
    name: str
    source_type: str           # database | api | excel | pdf_form | scanned_pdf | image | handwritten
    path: str = ""
    file_count: int = 0
    estimated_pages: int = 0
    readiness: DataReadinessLevel = DataReadinessLevel.L3_RED
    can_auto_process: bool = False
    needs_ocr: bool = False
    needs_manual: bool = False
    notes: str = ""


@dataclass
class ReadinessDashboard:
    """数据就绪度仪表盘"""
    project_name: str
    sources: List[DataSource]
    total_files: int
    total_pages: int

    l1_count: int = 0   # 绿色
    l2_count: int = 0   # 黄色
    l3_count: int = 0   # 红色

    l1_ratio: float = 0.0
    l2_ratio: float = 0.0
    l3_ratio: float = 0.0

    overall_readiness: float = 0.0  # 0-100
    readiness_grade: str = ""       # 优秀 | 良好 | 一般 | 不足

    needs_ocr_pages: int = 0
    needs_manual_pages: int = 0
    estimated_ocr_hours: float = 0.0

    preprocess_required: bool = False
    recommendation: str = ""


class DataReadinessAssessor:
    """
    数据就绪度评估器

    在审计项目启动前评估各数据源的就绪程度，
    为流水线配置决策提供依据。
    """

    # 文件类型到就绪度的映射
    FILE_TYPE_MAP = {
        # L1 绿色：结构化数据
        ".csv": DataReadinessLevel.L1_GREEN,
        ".json": DataReadinessLevel.L1_GREEN,
        ".xml": DataReadinessLevel.L1_GREEN,
        ".sql": DataReadinessLevel.L1_GREEN,
        ".db": DataReadinessLevel.L1_GREEN,
        ".sqlite": DataReadinessLevel.L1_GREEN,

        # L2 黄色：半结构化数据
        ".xlsx": DataReadinessLevel.L2_YELLOW,
        ".xls": DataReadinessLevel.L2_YELLOW,
        ".txt": DataReadinessLevel.L2_YELLOW,
        ".docx": DataReadinessLevel.L2_YELLOW,
        ".doc": DataReadinessLevel.L2_YELLOW,
        ".html": DataReadinessLevel.L2_YELLOW,
        ".htm": DataReadinessLevel.L2_YELLOW,

        # L3 红色：非结构化数据（需要OCR）
        ".pdf": DataReadinessLevel.L3_RED,     # 默认假设为扫描件
        ".jpg": DataReadinessLevel.L3_RED,
        ".jpeg": DataReadinessLevel.L3_RED,
        ".png": DataReadinessLevel.L3_RED,
        ".bmp": DataReadinessLevel.L3_RED,
        ".tiff": DataReadinessLevel.L3_RED,
        ".tif": DataReadinessLevel.L3_RED,
        ".gif": DataReadinessLevel.L3_RED,
    }

    def __init__(self):
        pass

    def assess_directory(
        self,
        directory: str,
        project_name: str = "",
        expected_file_count: Optional[int] = None,
    ) -> ReadinessDashboard:
        """
        评估目录下所有文件的数据就绪度

        Args:
            directory: 数据目录路径
            project_name: 项目名称
            expected_file_count: 预期文件数

        Returns:
            ReadinessDashboard
        """
        sources: List[DataSource] = []
        file_counts: Dict[DataReadinessLevel, int] = {l: 0 for l in DataReadinessLevel}

        total_files = 0
        total_pages = 0

        dir_path = Path(directory)
        if not dir_path.exists():
            return ReadinessDashboard(
                project_name=project_name,
                sources=[],
                total_files=0,
                total_pages=0,
                recommendation=f"目录不存在: {directory}",
            )

        # 按扩展名分组
        ext_groups: Dict[str, List[Path]] = {}
        for f in dir_path.rglob("*"):
            if f.is_file():
                ext = f.suffix.lower()
                if ext not in ext_groups:
                    ext_groups[ext] = []
                ext_groups[ext].append(f)

        for ext, files in ext_groups.items():
            readiness = self.FILE_TYPE_MAP.get(ext, DataReadinessLevel.L3_RED)
            file_count = len(files)

            # 估算页数
            est_pages = self._estimate_pages(ext, file_count)

            total_files += file_count
            total_pages += est_pages
            file_counts[readiness] += file_count

            # 判断是否需要OCR
            needs_ocr = readiness == DataReadinessLevel.L3_RED
            needs_manual = ext in (".jpg", ".jpeg", ".png", ".bmp")
            can_auto = readiness in (
                DataReadinessLevel.L1_GREEN, DataReadinessLevel.L2_YELLOW
            )

            sources.append(DataSource(
                name=f"{ext}文件",
                source_type=self._ext_to_type(ext),
                path=str(directory),
                file_count=file_count,
                estimated_pages=est_pages,
                readiness=readiness,
                can_auto_process=can_auto,
                needs_ocr=needs_ocr,
                needs_manual=needs_manual,
                notes=self._get_notes(ext, file_count, needs_ocr),
            ))

        # 计算比率
        l1 = file_counts[DataReadinessLevel.L1_GREEN]
        l2 = file_counts[DataReadinessLevel.L2_YELLOW]
        l3 = file_counts[DataReadinessLevel.L3_RED]

        total = total_files or 1

        l1_ratio = l1 / total
        l2_ratio = l2 / total
        l3_ratio = l3 / total

        # 就绪度得分 = L1*1.0 + L2*0.6 + L3*0.2
        readiness_score = (l1 * 1.0 + l2 * 0.6 + l3 * 0.2) / total * 100

        # OCR估算
        needs_ocr_pages = sum(
            s.estimated_pages for s in sources if s.needs_ocr
        )
        estimated_ocr_hours = needs_ocr_pages / 60  # 假设60页/小时

        # 等级
        if readiness_score >= 85:
            grade = "优秀"
        elif readiness_score >= 70:
            grade = "良好"
        elif readiness_score >= 50:
            grade = "一般"
        else:
            grade = "不足"

        # 是否需要预处理流程
        needs_preprocess = l3_ratio > 0.3

        # 汇总建议
        recommendation = self._build_recommendation(
            l1_ratio, l2_ratio, l3_ratio, needs_ocr_pages, estimated_ocr_hours,
            expected_file_count, total_files,
        )

        return ReadinessDashboard(
            project_name=project_name,
            sources=sorted(sources, key=lambda s: s.readiness.value),
            total_files=total_files,
            total_pages=total_pages,
            l1_count=l1,
            l2_count=l2,
            l3_count=l3,
            l1_ratio=round(l1_ratio, 3),
            l2_ratio=round(l2_ratio, 3),
            l3_ratio=round(l3_ratio, 3),
            overall_readiness=round(readiness_score, 1),
            readiness_grade=grade,
            needs_ocr_pages=needs_ocr_pages,
            needs_manual_pages=sum(
                s.estimated_pages for s in sources if s.needs_manual
            ),
            estimated_ocr_hours=round(estimated_ocr_hours, 1),
            preprocess_required=needs_preprocess,
            recommendation=recommendation,
        )

    def assess_file_list(
        self,
        files: List[Dict[str, Any]],
        project_name: str = "",
    ) -> ReadinessDashboard:
        """
        评估指定文件列表的数据就绪度

        Args:
            files: [{"name": "...", "type": "...", "pages": N}, ...]
            project_name: 项目名称
        """
        from collections import defaultdict
        groups = defaultdict(list)

        for f in files:
            ext = Path(f.get("name", "")).suffix.lower()
            groups[ext].append(f)

        # 构建sources列表然后整合
        sources = []
        for ext, items in groups.items():
            readiness = self.FILE_TYPE_MAP.get(ext, DataReadinessLevel.L3_RED)
            sources.append(DataSource(
                name=f"{ext}文件",
                source_type=self._ext_to_type(ext),
                file_count=len(items),
                estimated_pages=sum(it.get("pages", 0) for it in items),
                readiness=readiness,
                can_auto_process=readiness != DataReadinessLevel.L3_RED,
                needs_ocr=readiness == DataReadinessLevel.L3_RED,
            ))

        # 使用已有逻辑计算
        dashboard = ReadinessDashboard(
            project_name=project_name,
            sources=sorted(sources, key=lambda s: s.readiness.value),
            total_files=sum(s.file_count for s in sources),
            total_pages=sum(s.estimated_pages for s in sources),
        )

        # 计算统计 - 按文件数而非数据源数
        l1_file_count = sum(
            s.file_count for s in sources
            if s.readiness == DataReadinessLevel.L1_GREEN
        )
        l2_file_count = sum(
            s.file_count for s in sources
            if s.readiness == DataReadinessLevel.L2_YELLOW
        )
        l3_file_count = sum(
            s.file_count for s in sources
            if s.readiness == DataReadinessLevel.L3_RED
        )
        dashboard.l1_count = l1_file_count
        dashboard.l2_count = l2_file_count
        dashboard.l3_count = l3_file_count

        total = dashboard.total_files or 1
        dashboard.l1_ratio = dashboard.l1_count / total
        dashboard.l2_ratio = dashboard.l2_count / total
        dashboard.l3_ratio = dashboard.l3_count / total

        dashboard.overall_readiness = (
            dashboard.l1_count * 100 + dashboard.l2_count * 60 + dashboard.l3_count * 20
        ) / total

        return dashboard

    def _estimate_pages(self, ext: str, file_count: int) -> int:
        """估算文件总页数"""
        estimates = {
            ".pdf": 15,
            ".docx": 10,
            ".xlsx": 3,
            ".csv": 1,
            ".jpg": 1,
            ".png": 1,
            ".txt": 5,
        }
        return estimates.get(ext, 5) * file_count

    def _ext_to_type(self, ext: str) -> str:
        """扩展名到数据源类型"""
        mapping = {
            ".csv": "spreadsheet",
            ".xlsx": "spreadsheet",
            ".xls": "spreadsheet",
            ".json": "api",
            ".xml": "api",
            ".sql": "database",
            ".db": "database",
            ".pdf": "scanned_document",
            ".docx": "document",
            ".doc": "document",
            ".jpg": "image",
            ".png": "image",
            ".txt": "text",
        }
        return mapping.get(ext, "unknown")

    def _get_notes(
        self, ext: str, count: int, needs_ocr: bool
    ) -> str:
        parts = [f"共{count}个{ext}文件"]
        if needs_ocr:
            parts.append("需要OCR识别")
        if ext in (".jpg", ".png", ".bmp"):
            parts.append("图片格式，建议先转换为PDF批量OCR")
        return "；".join(parts)

    def _build_recommendation(
        self,
        l1_ratio: float,
        l2_ratio: float,
        l3_ratio: float,
        needs_ocr_pages: int,
        ocr_hours: float,
        expected: Optional[int],
        actual: int,
    ) -> str:
        """构建处理建议"""
        recs = []

        if l3_ratio > 0.6:
            recs.append(
                f"⚠️ L3红色数据占比{l3_ratio:.0%}，建议优先进行OCR预处理"
                f"（预估{ocr_hours:.1f}小时）再启动自动分析"
            )
        elif l3_ratio > 0.3:
            recs.append(
                f"L3占比{l3_ratio:.0%}，建议并行：OCR处理+人工整理同步进行"
            )
        elif l3_ratio > 0:
            recs.append("少量L3数据（建议OCR处理）")

        if l2_ratio > 0.3:
            recs.append(
                f"L2半结构化数据占比{l2_ratio:.0%}，需配置解析规则后分析"
            )

        if l1_ratio >= 0.7:
            recs.append("大部分数据已就绪，可直接启动分析流水线")

        if expected and actual < expected:
            recs.append(
                f"⚠️ 数据完整性问题：期望{expected}份，实收{actual}份"
            )

        return "；".join(recs) if recs else "数据已就绪，可直接分析"
