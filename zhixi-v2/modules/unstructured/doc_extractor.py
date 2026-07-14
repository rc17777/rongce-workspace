# 智析智能体 v2.0 — 非结构化数据处理模块
# 功能：OCR识别 / 文档关键要素提取（合同/招投标/会议纪要）

import re
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import os


class OCREngine:
    """OCR识别引擎 - 支持 PaddleOCR / Tesseract"""
    
    def __init__(self, backend: str = "paddleocr"):
        self.backend = backend
        self._engine = None
    
    def _get_engine(self):
        if self._engine is not None:
            return self._engine
        if self.backend == "paddleocr":
            try:
                from paddleocr import PaddleOCR
                self._engine = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
            except ImportError:
                raise ImportError("请安装 paddleocr: pip install paddleocr")
        elif self.backend == "tesseract":
            try:
                import pytesseract
                self._engine = pytesseract
            except ImportError:
                raise ImportError("请安装 pytesseract: pip install pytesseract")
        else:
            raise ValueError(f"不支持的OCR后端: {self.backend}")
        return self._engine
    
    def recognize(self, image_path: str) -> str:
        """识别单张图片返回纯文本"""
        if self.backend == "paddleocr":
            engine = self._get_engine()
            result = engine.ocr(image_path, cls=True)
            if not result or not result[0]:
                return ""
            lines = [line[1][0] for line in result[0] if line and len(line) > 1]
            return "\n".join(lines)
        elif self.backend == "tesseract":
            engine = self._get_engine()
            return engine.image_to_string(image_path, lang="chi_sim+eng")
        return ""
    
    def recognize_batch(self, image_paths: List[str]) -> Dict[str, str]:
        """批量识别"""
        return {path: self.recognize(path) for path in image_paths}


class DocExtractor:
    """文档关键要素提取器 - 合同 / 招投标 / 会议纪要"""
    
    # ============================================================
    # 合同关键要素提取 (基于prompt-librarian合同审查模板)
    # ============================================================
    
    @staticmethod
    def extract_contract(text: str) -> Dict:
        """提取合同关键要素"""
        result = {
            "doc_type": "contract",
            "parties": DocExtractor._extract_parties(text),
            "contract_amount": DocExtractor._extract_amount(text),
            "subject_matter": DocExtractor._extract_subject(text),
            "performance_period": DocExtractor._extract_period(text),
            "breach_liability": DocExtractor._extract_breach(text),
            "sign_date": DocExtractor._extract_date(text),
            "payment_terms": DocExtractor._extract_payment(text),
            "warranty": DocExtractor._extract_section(text, r"(质保|保修|保证).{0,50}(：|:)", 200),
            "dispute_resolution": DocExtractor._extract_section(text, r"(争议|仲裁|诉讼|管辖).{0,50}(：|:)", 200),
        }
        return result
    
    # ============================================================
    # 招投标文件关键要素提取
    # ============================================================
    
    @staticmethod
    def extract_bidding(text: str) -> Dict:
        """提取招投标文件关键要素"""
        return {
            "doc_type": "bidding",
            "project_name": DocExtractor._extract_section(text, r"(项目名称|采购项目名称).{0,20}(：|:)", 100),
            "procurement_method": DocExtractor._extract_section(text, r"(采购方式|招标方式).{0,20}(：|:)", 50),
            "budget_amount": DocExtractor._extract_amount(text),
            "bidder_name": DocExtractor._extract_bidder_name(text),
            "evaluation_method": DocExtractor._extract_section(text, r"(评标方法|评审方法).{0,20}(：|:)", 100),
            "bid_guarantee": DocExtractor._extract_amount(text, r"(投标保证金|投标担保)"),
            "performance_bond": DocExtractor._extract_amount(text, r"(履约保证金|履约担保)"),
            "bid_deadline": DocExtractor._extract_date(text),
            "technical_specs": DocExtractor._extract_section(text, r"(技术规格|技术参数|技术要求).{0,20}(：|:)", 300),
            "qualification_req": DocExtractor._extract_section(text, r"(资格要求|资质要求|投标人资格).{0,20}(：|:)", 300),
            "evaluation_committee": DocExtractor._extract_section(text, r"(评标委员会|评审委员会).{0,20}(：|:)", 200),
        }
    
    # ============================================================
    # 会议纪要关键要素提取
    # ============================================================
    
    @staticmethod
    def extract_meeting_minutes(text: str) -> Dict:
        """提取会议纪要关键要素"""
        return {
            "doc_type": "meeting_minutes",
            "meeting_title": DocExtractor._extract_section(text, r"(会议名称|会议议题|关于).{0,20}(会议|纪要)", 80),
            "meeting_date": DocExtractor._extract_date(text),
            "attendees": DocExtractor._extract_section(text, r"(参会人员|出席人员|参加人员).{0,20}(：|:)", 200),
            "host": DocExtractor._extract_section(text, r"(主持人|主持).{0,20}(：|:)", 30),
            "agenda_items": DocExtractor._extract_list(text, r"(\d+[\.\、\)]|（\d+）|[一二三四五六七八九十][\.\、\)])", r"(议题|议程)"),
            "resolutions": DocExtractor._extract_list(text, r"(决议|决定|会议要求|会议决定)"),
            "action_items": DocExtractor._extract_list(text, r"(责任单位|责任人|牵头单位|落实)"),
            "deadlines": DocExtractor._extract_deadlines(text),
        }
    
    # ============================================================
    # 通用提取方法
    # ============================================================
    
    @staticmethod
    def _extract_parties(text: str) -> List[Dict]:
        """提取合同双方"""
        patterns = [
            r"(甲方|发包人|买方|采购人|委托方)[：:]*\s*(\S.{0,50}?)(?:\n|。|；|乙方|承包)",
            r"(乙方|承包人|卖方|供应商|受托方)[：:]*\s*(\S.{0,50}?)(?:\n|。|；|甲方)",
        ]
        parties = []
        for p in patterns:
            match = re.search(p, text)
            if match:
                parties.append({"role": match.group(1), "name": match.group(2).strip()})
        return parties
    
    @staticmethod
    def _extract_amount(text: str, prefix_pattern: str = None) -> Optional[Dict]:
        """提取金额"""
        if prefix_pattern:
            ctx = DocExtractor._extract_section(text, prefix_pattern, 100)
            if ctx is None:
                ctx = text[:2000]
        else:
            ctx = text[:2000]
        if ctx is None:
            return None
        
        patterns = [
            r"(人民币|大写)?\s*(\d[\d,.]*)\s*(万元|元|亿元)",
            r"(?:金额|合同价款|预算金额|中标金额).{0,20}?(\d[\d,.]*)\s*(万元|元|亿元)",
        ]
        for p in patterns:
            match = re.search(p, str(ctx))
            if match:
                try:
                    groups = match.groups()
                    amount = None
                    unit = None
                    for g in groups:
                        if g and re.match(r'\d', g):
                            amount = g.replace(",", "")
                        elif g in ("万元", "元", "亿元"):
                            unit = g
                    if amount:
                        return {"amount": amount, "unit": unit or "元", "raw": match.group(0)}
                except:
                    pass
        return None
    
    @staticmethod
    def _extract_subject(text: str) -> Optional[str]:
        """提取合同标的"""
        patterns = [
            r"(标的|采购内容|服务内容|工程内容|项目内容).{0,30}(：|:)\s*(.{0,200}?)(?:\n|。|；)",
            r"(?:就|关于)(.{0,100}?)(?:项目|工程|服务|采购).{0,20}(?:签订|达成|订立|协商一致)",
        ]
        for p in patterns:
            match = re.search(p, text)
            if match:
                return match.group(0).strip()
        return None
    
    @staticmethod
    def _extract_period(text: str) -> Optional[str]:
        patterns = [
            r"(合同期限|履约期限|服务期限|工期).{0,30}(：|:)\s*(.{0,100}?)(?:\n|。|；)",
            r"自\s*(.{0,30}?)\s*至\s*(.{0,30}?)\s*(?:止|截止)",
        ]
        for p in patterns:
            match = re.search(p, text)
            if match:
                return match.group(0).strip()
        return None
    
    @staticmethod
    def _extract_breach(text: str) -> Optional[str]:
        return DocExtractor._extract_section(text, r"(违约责任|违约条款|违约).{0,20}(：|:)", 300)
    
    @staticmethod
    def _extract_date(text: str) -> Optional[str]:
        patterns = [
            r"(\d{4})\s*[年\-\.\/]\s*(\d{1,2})\s*[月\-\.\/]\s*(\d{1,2})\s*日?",
            r"(?:签订日期|开标日期|会议日期|日期).{0,10}?(\d{4})[年\-\.\/](\d{1,2})[月\-\.\/](\d{1,2})",
        ]
        for p in patterns:
            match = re.search(p, text)
            if match:
                groups = match.groups()
                return f"{groups[0]}-{groups[1].zfill(2)}-{groups[2].zfill(2)}"
        return None
    
    @staticmethod
    def _extract_payment(text: str) -> Optional[str]:
        return DocExtractor._extract_section(text, r"(付款方式|支付方式|结算方式|付款条件).{0,20}(：|:)", 200)
    
    @staticmethod
    def _extract_bidder_name(text: str) -> Optional[str]:
        patterns = [
            r"(中标人|中标单位|中标供应商|成交供应商).{0,20}(：|:)\s*(\S.{0,50}?)(?:\n|。|；)",
            r"(投标人|投标单位).{0,10}名称.{0,10}：?\s*(\S.{0,50}?)(?:\n|。|；)",
        ]
        for p in patterns:
            match = re.search(p, text)
            if match:
                return match.group(match.lastindex).strip()
        return None
    
    @staticmethod
    def _extract_section(text: str, start_pattern: str, max_chars: int = 200) -> Optional[str]:
        match = re.search(start_pattern, text)
        if match:
            start = match.start()
            end = min(start + max_chars, len(text))
            return text[start:end].strip()
        return None
    
    @staticmethod
    def _extract_list(text: str, prefix: str, context_hint: str = "") -> List[str]:
        """提取列表项"""
        items = []
        if context_hint:
            ctx_match = re.search(context_hint, text)
            if ctx_match:
                search_start = ctx_match.start()
            else:
                search_start = 0
        else:
            search_start = 0
        
        for m in re.finditer(rf"{prefix}\s*(.{{0,200}}?)(?:\n|。|；)", text[search_start:]):
            item = m.group(0).strip()
            if len(item) > 2:
                items.append(item)
        return items[:10]
    
    @staticmethod
    def _extract_deadlines(text: str) -> List[Dict]:
        """提取责任人和时间节点"""
        items = []
        pattern = r"(\S.{0,20}?)\s*(?:负责|牵头|完成|落实).{0,30}?(\d{4}[年\-\.\/]\d{1,2}[月\-\.\/]\d{1,2})"
        for m in re.finditer(pattern, text):
            items.append({"responsible": m.group(1).strip(), "deadline": m.group(2)})
        return items[:10]
    
    # ============================================================
    # 批量处理
    # ============================================================
    
    @classmethod
    def process_document(cls, text: str, doc_type: str = "auto") -> Dict:
        """根据文档类型自动选择提取器"""
        # 自动识别文档类型
        if doc_type == "auto":
            if any(kw in text[:500] for kw in ["合同", "协议", "甲方", "乙方", "签订"]):
                doc_type = "contract"
            elif any(kw in text[:500] for kw in ["招标", "投标", "中标", "采购", "开标"]):
                doc_type = "bidding"
            elif any(kw in text[:500] for kw in ["会议纪要", "会议记录", "参会人员", "议题"]):
                doc_type = "meeting_minutes"
            else:
                doc_type = "generic"
        
        if doc_type == "contract":
            return cls.extract_contract(text)
        elif doc_type == "bidding":
            return cls.extract_bidding(text)
        elif doc_type == "meeting_minutes":
            return cls.extract_meeting_minutes(text)
        else:
            return {"doc_type": "generic", "text_length": len(text)}
    
    @classmethod
    def process_batch(cls, documents: List[Dict[str, str]]) -> List[Dict]:
        """批量处理文档 {path: text}"""
        return [{"path": path, **cls.process_document(text)} for path, text in documents]


class DocToDB:
    """将提取的非结构化数据转为结构化数据库表"""
    
    @staticmethod
    def contract_to_table(contracts: List[Dict]) -> pd.DataFrame:
        import pandas as pd
        rows = []
        for c in contracts:
            row = {
                "doc_type": c.get("doc_type"),
                "party_a": c.get("parties", [{}])[0].get("name", "") if c.get("parties") else "",
                "party_b": c.get("parties", [{}])[1].get("name", "") if len(c.get("parties", [])) > 1 else "",
                "amount_value": c.get("contract_amount", {}).get("amount", "") if c.get("contract_amount") else "",
                "amount_unit": c.get("contract_amount", {}).get("unit", "") if c.get("contract_amount") else "",
                "subject": c.get("subject_matter", ""),
                "performance_period": c.get("performance_period", ""),
                "sign_date": c.get("sign_date", ""),
                "payment_terms": c.get("payment_terms", ""),
                "breach_liability": c.get("breach_liability", ""),
            }
            rows.append(row)
        return pd.DataFrame(rows)
    
    @staticmethod
    def bidding_to_table(biddings: List[Dict]) -> pd.DataFrame:
        import pandas as pd
        rows = []
        for b in biddings:
            row = {
                "project_name": b.get("project_name", ""),
                "procurement_method": b.get("procurement_method", ""),
                "budget_amount": b.get("budget_amount", {}).get("raw", "") if b.get("budget_amount") else "",
                "bidder_name": b.get("bidder_name", ""),
                "evaluation_method": b.get("evaluation_method", ""),
                "bid_deadline": b.get("bid_deadline", ""),
                "bid_guarantee": b.get("bid_guarantee", {}).get("raw", "") if b.get("bid_guarantee") else "",
            }
            rows.append(row)
        return pd.DataFrame(rows)
