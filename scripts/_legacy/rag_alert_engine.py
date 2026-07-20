#!/usr/bin/env python3
"""
RAG知识库 → 实时预警引擎（含智能降噪层）
RAG Alert Engine v2: 被动检索 → 主动预警 → 智能降噪 → 精准推送

核心能力:
1. 知识变化监控 — 检测RAG索引新增/更新的chunk
2. 项目风险匹配 — 将新知识与活跃审计项目上下文做语义比对
3. 主动预警推送 — 新政策/案例/法规触及项目风险域时自动告警
4. 知识缺口发现 — 识别项目需要的知识RAG中缺失
5. 智能降噪 — 去重/分级/聚合/每日摘要推送
"""

import sys, io, json, os, pickle, hashlib, time
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Set
from collections import defaultdict
import re
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 配置
# ============================================================

RAG_INDEX_FILE = r'D:\openclaw-workspace\.rag_index\rag_index.json'
RAG_DATA_FILE = r'D:\openclaw-workspace\.rag_index\rag_index.json'  # pickle格式，同index文件
RAG_CHUNKS_FILE = r'D:\openclaw-workspace\.rag_index\chunks.json'  # chunks metadata
WORKSPACE = Path(r'D:\openclaw-workspace')
ALERT_STATE_FILE = WORKSPACE / '.rag_alert_state.json'  # 已推送告警记录（去重用）

# 项目风险域关键词（映射审计类型 → 需要关注的知识主题）
PROJECT_RISK_DOMAINS = {
    "专项资金": [
        "专项资金管理办法", "转移支付", "资金挪用", "截留", "惠农资金",
        "社保资金", "教育经费", "保障性住房", "民政救济", "补贴发放",
        "一卡通", "资金监管", "国库集中支付", "零余额"
    ],
    "经责审计": [
        "经济责任审计", "自然资源资产", "离任审计", "三重一大",
        "决策程序", "债务风险", "国有资产", "领导干部",
        "问责", "一票否决", "整改落实", "巡视"
    ],
    "工程审计": [
        "竣工决算", "工程结算", "造价", "变更签证", "超概算",
        "招标投标", "合同管理", "进度款", "质保金", "监理",
        "工程量清单", "定额", "材料价差"
    ],
    "财政监督": [
        "财政监督", "财会监督", "预算执行", "三公经费", "过紧日子",
        "政府采购", "国有资产", "非税收入", "往来款", "存量资金"
    ],
    "采购审计": [
        "政府采购", "招标投标", "围标串标", "供应商", "评审专家",
        "采购需求", "合同履约", "电子卖场", "框架协议"
    ],
    "绩效评价": [
        "绩效管理", "绩效目标", "绩效评价", "指标体系", "满意度",
        "成本效益", "事前评估", "事中监控", "结果运用"
    ],
    "补贴审计": [
        "补贴", "农机补贴", "耕地地力", "产业扶持", "退耕还林",
        "粮食补贴", "乡村振兴", "农业保险"
    ],
    "预算执行": [
        "预算法", "预算编制", "预算调整", "决算", "政府债务",
        "专项债", "一般债", "隐性债务"
    ],
}

# 告警级别与语义
ALERT_TRIGGERS = {
    "新法规发布": {
        "level": "P1",
        "patterns": ["管理办法", "条例", "规定", "办法.*修订", "新修订", "出台"],
        "message_tpl": "新法规/政策发布: {title} — 可能影响项目 {project} 的审计结论"
    },
    "审计案例曝光": {
        "level": "P1",
        "patterns": ["审计查出", "审计发现", "典型案例", "曝光", "问题金额", "移送"],
        "message_tpl": "相关审计案例曝光: {title} — 与项目 {project} 风险域 {domain} 高度相关"
    },
    "新型违规手法": {
        "level": "P0",
        "patterns": ["新型", "新手段", "变相", "隐蔽", "规避", "绕过", "打擦边球"],
        "message_tpl": "⚠️ 新型违规手法发现: {title} — 项目 {project} 需重点关注"
    },
    "监管政策收紧": {
        "level": "P2",
        "patterns": ["加强", "严格", "专项治理", "专项整治", "重点检查", "回头看"],
        "message_tpl": "监管政策收紧信号: {title} — 项目 {project} 审计重点需调整"
    },
}


# ============================================================
# 数据模型
# ============================================================

@dataclass
class RAGAlert:
    """RAG知识告警"""
    alert_id: str
    trigger_type: str
    level: str
    project: str
    domain: str
    message: str
    chunk_source: str
    chunk_text: str
    match_score: float
    timestamp: str
    status: str = "new"


@dataclass
class AlertDigest:
    """每日摘要"""
    date: str
    project: str
    total_raw: int
    after_dedup: int
    counts_by_level: Dict[str, int]
    counts_by_type: Dict[str, int]
    p0_alerts: List[RAGAlert]
    p1_alerts: List[RAGAlert]
    top_p2_alerts: List[RAGAlert]
    knowledge_gaps: List[str]
    rag_status: str


# ============================================================
# 智能降噪层
# ============================================================

class AlertFilter:
    """智能降噪过滤器
    
    三层降噪:
    1. 去重 — 同一来源(文件)的同类告警只保留一条
    2. 分级 — 默认只推送P0/P1，P2/P3进入日报
    3. 已见过滤 — 已推送过的告警不再重复推
    """
    
    def __init__(self, state_file: str = str(ALERT_STATE_FILE)):
        self.state_file = Path(state_file)
        self.seen_keys: Set[str] = set()
        self._load_state()
    
    def _load_state(self):
        """加载已见告警记录"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                self.seen_keys = set(state.get('seen_keys', []))
                print(f"[降噪] 加载历史告警记录: {len(self.seen_keys)} 条")
            except:
                self.seen_keys = set()
    
    def _save_state(self):
        """保存已见告警记录"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        # 只保留最近7天的记录，防止文件膨胀
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump({
                'seen_keys': list(self.seen_keys),
                'updated_at': datetime.now().isoformat(),
            }, f, ensure_ascii=False)
    
    def _make_key(self, alert: RAGAlert) -> str:
        """生成去重key: 触发类型 + 来源文件 + 风险域"""
        return f"{alert.trigger_type}:{alert.chunk_source}:{alert.domain}"
    
    def deduplicate(self, alerts: List[RAGAlert]) -> List[RAGAlert]:
        """第一层去重：同一来源+同类触发 只保留一条"""
        seen = set()
        unique = []
        for a in alerts:
            key = self._make_key(a)
            if key not in seen:
                seen.add(key)
                unique.append(a)
        print(f"  [降噪①去重] {len(alerts)} → {len(unique)} (源: {len(alerts)} → 唯: {len(unique)})")
        return unique
    
    def filter_seen(self, alerts: List[RAGAlert]) -> List[RAGAlert]:
        """第二层过滤：已推送过的不再推"""
        new_alerts = [a for a in alerts if self._make_key(a) not in self.seen_keys]
        print(f"  [降噪②已见过滤] {len(alerts)} → {len(new_alerts)} (已推送 {len(alerts) - len(new_alerts)} 条)")
        
        # 记录本次推送的新告警
        for a in new_alerts:
            self.seen_keys.add(self._make_key(a))
        self._save_state()
        
        return new_alerts
    
    def grade(self, alerts: List[RAGAlert], push_level: str = "P1") -> Tuple[List[RAGAlert], List[RAGAlert]]:
        """第三层分级：按级别拆分
        
        Args:
            alerts: 告警列表
            push_level: 推送级别线，<=此级别才推送 (P0 < P1 < P2 < P3)
            
        Returns:
            (push_alerts: 推送级别以上的, digest_alerts: 进入日报汇总的)
        """
        level_order = {'P0': 0, 'P1': 1, 'P2': 2, 'P3': 3}
        push_threshold = level_order.get(push_level, 1)
        
        push_list = []
        digest_list = []
        
        for a in alerts:
            a_level = level_order.get(a.level, 9)
            if a_level <= push_threshold:
                push_list.append(a)
            else:
                digest_list.append(a)
        
        print(f"  [降噪③分级] 推送线={push_level} → 推送 {len(push_list)} 条, 入日报 {len(digest_list)} 条")
        return push_list, digest_list
    
    def full_filter(self, alerts: List[RAGAlert], push_level: str = "P1") -> Dict:
        """完整降噪流水线"""
        print(f"\n[降噪流水线] 输入 {len(alerts)} 条原始告警")
        
        # ① 去重
        deduped = self.deduplicate(alerts)
        
        # ② 已见过滤
        new_alerts = self.filter_seen(deduped)
        
        # ③ 分级
        push_alerts, digest_alerts = self.grade(new_alerts, push_level)
        
        stats = {
            'raw': len(alerts),
            'after_dedup': len(deduped),
            'after_seen_filter': len(new_alerts),
            'push_count': len(push_alerts),
            'digest_count': len(digest_alerts),
            'push_level': push_level,
        }
        
        return {
            'push': push_alerts,
            'digest': digest_alerts,
            'stats': stats,
        }


# ============================================================
# 摘要生成
# ============================================================

class AlertDigestBuilder:
    """告警摘要生成器"""
    
    @staticmethod
    def build_digest(
        push_alerts: List[RAGAlert],
        digest_alerts: List[RAGAlert],
        knowledge_gaps: List[str],
        project: str,
        rag_status: str = ""
    ) -> AlertDigest:
        """构建每日摘要"""
        
        today = datetime.now().strftime('%Y-%m-%d')
        all_alerts = push_alerts + digest_alerts
        
        # 按级别统计
        counts_by_level = defaultdict(int)
        for a in all_alerts:
            counts_by_level[a.level] += 1
        
        # 按类型统计
        counts_by_type = defaultdict(int)
        for a in all_alerts:
            counts_by_type[a.trigger_type] += 1
        
        # 按级别排序
        level_order = {'P0': 0, 'P1': 1, 'P2': 2, 'P3': 3}
        p0 = sorted([a for a in all_alerts if a.level == 'P0'], key=lambda x: x.match_score, reverse=True)
        p1 = sorted([a for a in all_alerts if a.level == 'P1'], key=lambda x: x.match_score, reverse=True)
        p2 = sorted([a for a in all_alerts if a.level == 'P2'], key=lambda x: x.match_score, reverse=True)
        
        return AlertDigest(
            date=today,
            project=project,
            total_raw=len(all_alerts),
            after_dedup=len(push_alerts) + len(digest_alerts),
            counts_by_level=dict(counts_by_level),
            counts_by_type=dict(counts_by_type),
            p0_alerts=p0,
            p1_alerts=p1,
            top_p2_alerts=p2[:5],
            knowledge_gaps=knowledge_gaps,
            rag_status=rag_status,
        )
    
    @staticmethod
    def format_digest_text(digest: AlertDigest, max_detail: int = 5) -> str:
        """生成可推送的文本格式"""
        
        lines = [
            f"🧠 RAG知识库预警日报",
            f"━━━━━━━━━━━━━━━━━━━",
            f"日期: {digest.date}",
            f"项目: {digest.project}",
            f"RAG状态: {digest.rag_status}",
            f"",
        ]
        
        # 汇总
        total = sum(digest.counts_by_level.values())
        lines.append(f"📊 今日告警: {total} 条 (去重后)")
        
        level_icons = {'P0': '🔴', 'P1': '🟡', 'P2': '🟢', 'P3': '⚪'}
        for lv in ['P0', 'P1', 'P2', 'P3']:
            if digest.counts_by_level.get(lv, 0) > 0:
                icon = level_icons.get(lv, '')
                lines.append(f"  {icon} {lv}: {digest.counts_by_level[lv]} 条")
        
        # 按类型统计
        lines.append("")
        lines.append("📋 按触发类型:")
        for ttype, count in sorted(digest.counts_by_type.items(), key=lambda x: -x[1]):
            lines.append(f"  • {ttype}: {count} 条")
        
        # P0告警（最紧急）
        if digest.p0_alerts:
            lines.append("")
            lines.append(f"🔴 急迫告警 ({len(digest.p0_alerts)} 条):")
            for a in digest.p0_alerts[:max_detail]:
                lines.append(f"  • {a.message[:100]}")
                lines.append(f"    来源: {a.chunk_source}")
        
        # P1告警
        if digest.p1_alerts:
            lines.append("")
            lines.append(f"🟡 重要告警 ({len(digest.p1_alerts)} 条，显示前{max_detail}条):")
            for a in digest.p1_alerts[:max_detail]:
                lines.append(f"  • {a.message[:100]}")
                lines.append(f"    来源: {a.chunk_source}")
        
        # P2精选
        if digest.top_p2_alerts:
            lines.append("")
            lines.append(f"🟢 提示信息 (P2, {len(digest.top_p2_alerts)} 条):")
            for a in digest.top_p2_alerts:
                lines.append(f"  • {a.message[:80]}")
        
        # 知识缺口
        if digest.knowledge_gaps:
            lines.append("")
            lines.append("⚡ 知识缺口:")
            for g in digest.knowledge_gaps[:3]:
                lines.append(f"  {g}")
        
        # 底部
        lines.append("")
        lines.append("───")
        lines.append("生成自动，如需详细清单运行: python scripts/rag_alert_engine.py --report --json")
        
        return '\n'.join(lines)


# ============================================================
# RAGAlertEngine（原有）+ 降噪集成
# ============================================================

@dataclass
class RAGAlert:
    """RAG知识告警"""
    alert_id: str
    trigger_type: str
    level: str
    project: str
    domain: str
    message: str
    chunk_source: str
    chunk_text: str
    match_score: float
    timestamp: str
    status: str = "new"


class RAGAlertEngine:
    """RAG知识库告警引擎"""
    
    def __init__(self, index_path: str = RAG_INDEX_FILE, data_path: str = RAG_DATA_FILE):
        self.index_path = index_path
        self.data_path = data_path
        self.index_hash = None
        self.last_chunk_count = 0
        self.new_chunks: List[Dict] = []
        self.vectorizer = None
        self.tfidf_matrix = None
        self.all_chunks = []
        self._loaded = False
        
    def load_rag(self):
        """加载RAG索引"""
        try:
            if os.path.exists(self.data_path):
                with open(self.data_path, 'rb') as f:
                    data = pickle.load(f)
                self.vectorizer = data['vectorizer']
                self.tfidf_matrix = data['matrix']
                self.all_chunks = data.get('chunks', [])
                self._loaded = True
                print(f"[RAG加载] {len(self.all_chunks)} chunks已加载")
                return True
        except Exception as e:
            print(f"[RAG加载失败] {e}")
        
        return False
    
    def check_index_changes(self) -> Tuple[bool, int, int]:
        """检查RAG索引是否有变化"""
        current_hash = None
        current_count = 0
        
        if os.path.exists(self.index_path):
            with open(self.index_path, 'rb') as f:
                raw = f.read()
                current_hash = hashlib.md5(raw).hexdigest()
            
            try:
                data = json.loads(raw)
                current_count = data.get('chunk_count', 0) if isinstance(data, dict) else 0
            except:
                pass
        
        if self.index_hash and self.index_hash != current_hash:
            delta = current_count - self.last_chunk_count
            changed = True
        else:
            delta = 0
            changed = False
        
        self.index_hash = current_hash
        self.last_chunk_count = current_count
        return changed, delta, current_count
    
    def semantic_match(self, chunk_text: str, keywords: List[str]) -> float:
        """判断chunk与项目风险域关键词的语义匹配度"""
        if not chunk_text or not keywords:
            return 0.0
        
        chunk_lower = chunk_text.lower()
        match_count = 0
        
        for kw in keywords:
            if kw.lower() in chunk_lower:
                match_count += 1
        
        # 匹配率
        score = match_count / len(keywords) if keywords else 0
        
        # 加权：标题匹配加分
        if any(kw.lower() in chunk_lower[:100] for kw in keywords):
            score = min(1.0, score + 0.2)
        
        return score
    
    def classify_trigger(self, chunk_text: str, source: str) -> Optional[Tuple[str, str]]:
        """判断chunk属于哪种告警触发类型"""
        for trigger_name, config in ALERT_TRIGGERS.items():
            for pattern in config["patterns"]:
                if re.search(pattern, chunk_text) or re.search(pattern, source):
                    return trigger_name, config["level"]
        return None
    
    def scan_for_project(self, project_dir: str, project_type: str = None) -> List[RAGAlert]:
        """针对指定项目扫描RAG知识库，生成告警"""
        if not self._loaded:
            if not self.load_rag():
                return []
        
        project_path = Path(project_dir)
        project_name = project_path.name
        
        # 自动检测项目类型
        if not project_type:
            project_type = self._detect_project_type(project_dir)
        
        # 获取风险域关键词
        risk_keywords = PROJECT_RISK_DOMAINS.get(project_type, [])
        if not risk_keywords:
            for ptype, kws in PROJECT_RISK_DOMAINS.items():
                if ptype in project_name or project_name in ptype:
                    risk_keywords = kws
                    break
        
        if not risk_keywords:
            risk_keywords = list(set(kw for kws in PROJECT_RISK_DOMAINS.values() for kw in kws))
        
        print(f"\n[RAG扫描] 项目: {project_name} | 类型: {project_type or '自动'} | 风险关键词: {len(risk_keywords)}个")
        
        alerts = []
        alert_id = 0
        matched_count = 0
        
        for chunk in self.all_chunks:
            text = chunk.get('text', '')
            source = chunk.get('source', '')
            
            if not text:
                continue
            
            score = self.semantic_match(text, risk_keywords)
            if score < 0.15:
                continue
            
            matched_count += 1
            trigger = self.classify_trigger(text, source)
            if not trigger:
                continue
            
            trigger_type, level = trigger
            config = ALERT_TRIGGERS[trigger_type]
            
            matched_kws = [kw for kw in risk_keywords if kw.lower() in text.lower()]
            domain = matched_kws[0] if matched_kws else "综合"
            
            alert_id += 1
            message = config["message_tpl"].format(
                title=source,
                project=project_name,
                domain=domain
            )
            
            alerts.append(RAGAlert(
                alert_id=f"RAG-ALT-{alert_id:04d}",
                trigger_type=trigger_type,
                level=level,
                project=project_name,
                domain=domain,
                message=message,
                chunk_source=source,
                chunk_text=text[:300],
                match_score=round(score, 3),
                timestamp=datetime.now().isoformat(),
            ))
        
        print(f"  语义匹配: {matched_count}/{len(self.all_chunks)} chunks命中")
        print(f"  告警产生: {len(alerts)} 条")
        
        if alerts:
            levels = defaultdict(int)
            for a in alerts:
                levels[a.level] += 1
            for lv in ['P0', 'P1', 'P2']:
                if levels[lv]:
                    print(f"    {lv}: {levels[lv]}条")
        
        return alerts
    
    def scan_all_projects(self, projects_root: str = None) -> Dict[str, List[RAGAlert]]:
        """扫描所有活跃项目"""
        if projects_root is None:
            projects_root = WORKSPACE / 'projects'
        
        results = {}
        p_root = Path(projects_root)
        
        if not p_root.exists():
            print(f"[无项目目录] {projects_root}")
            return results
        
        for project_dir in p_root.iterdir():
            if not project_dir.is_dir() or project_dir.name.startswith('.'):
                continue
            
            status_file = project_dir / 'status.json'
            if not status_file.exists():
                continue
            
            alerts = self.scan_for_project(str(project_dir))
            if alerts:
                results[project_dir.name] = alerts
        
        return results
    
    def find_knowledge_gaps(self, project_dir: str) -> List[str]:
        """发现项目需要的知识在RAG中的缺口"""
        project_path = Path(project_dir)
        project_name = project_path.name
        
        project_type = self._detect_project_type(project_dir)
        risk_keywords = PROJECT_RISK_DOMAINS.get(project_type, [])
        
        gaps = []
        if not self._loaded:
            self.load_rag()
        
        for kw in risk_keywords:
            matches = sum(1 for chunk in self.all_chunks 
                         if kw.lower() in chunk.get('text', '').lower())
            if matches == 0:
                gaps.append(f"  关键词'{kw}'在RAG知识库中无匹配 — 建议补充")
            elif matches < 3:
                gaps.append(f"  关键词'{kw}'仅匹配{matches}条 — 覆盖度偏低")
        
        return gaps
    
    def _detect_project_type(self, project_dir: str) -> str:
        """自动检测项目类型"""
        project_path = Path(project_dir)
        project_name = project_path.name.lower()
        
        for ptype in PROJECT_RISK_DOMAINS:
            if ptype.lower() in project_name:
                return ptype
        
        status_file = project_path / 'status.json'
        if status_file.exists():
            try:
                with open(status_file, 'r', encoding='utf-8') as f:
                    status = json.load(f)
                    ptype = status.get('type', '')
                    for k in PROJECT_RISK_DOMAINS:
                        if k.lower() in ptype.lower():
                            return k
            except:
                pass
        
        return "综合"
    
    def generate_report(self, project_dir: str = None) -> str:
        """生成RAG预警报告"""
        lines = [
            f"## RAG知识库预警报告",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"RAG状态: {len(self.all_chunks)} chunks已加载",
            f"",
        ]
        
        if project_dir:
            alerts = self.scan_for_project(project_dir)
            gaps = self.find_knowledge_gaps(project_dir)
            
            lines.append(f"### 项目: {Path(project_dir).name}")
            if alerts:
                lines.append(f"\n#### 知识预警 ({len(alerts)}条)")
                for a in alerts[:20]:
                    level_icon = {'P0': '🔴', 'P1': '🟡', 'P2': '🟢'}.get(a.level, '⚪')
                    lines.append(f"- {level_icon} [{a.trigger_type}] {a.message}")
                    lines.append(f"  来源: {a.chunk_source} | 匹配度: {a.match_score}")
            else:
                lines.append("✅ 当前无知识预警")
            
            if gaps:
                lines.append(f"\n#### 知识缺口 ({len(gaps)}个)")
                for g in gaps:
                    lines.append(g)
            else:
                lines.append("\n✅ 知识覆盖完整")
        else:
            all_results = self.scan_all_projects()
            lines.append(f"\n### 全项目扫描 ({len(all_results)}个活跃项目)")
            total_alerts = 0
            for proj_name, alerts in all_results.items():
                lines.append(f"\n#### {proj_name}: {len(alerts)}条预警")
                for a in alerts[:3]:
                    lines.append(f"- {a.level} [{a.trigger_type}] {a.message[:80]}")
                if len(alerts) > 3:
                    lines.append(f"  ... 共{len(alerts)}条")
                total_alerts += len(alerts)
            if total_alerts == 0:
                lines.append("✅ 所有项目无知识预警")
        
        return '\n'.join(lines)


# ============================================================
# 降噪集成函数（供 continuous_monitor.py 调用）
# ============================================================

def rag_alert_with_noise_reduction(
    project_dir: str = None,
    push_level: str = "P1",
    max_detail: int = 5,
    use_filter: bool = True
) -> Dict:
    """
    带降噪的RAG告警集成
    
    返回:
    {
        'digest': AlertDigest,
        'digest_text': str,  # 可推送文本
        'stats': {...},       # 降噪统计
    }
    """
    engine = RAGAlertEngine()
    engine.load_rag()
    
    # 扫描
    if project_dir:
        alerts = engine.scan_for_project(project_dir)
        gaps = engine.find_knowledge_gaps(project_dir)
        project_name = Path(project_dir).name
    else:
        all_alerts = engine.scan_all_projects()
        alerts = []
        for al in all_alerts.values():
            alerts.extend(al)
        gaps = []
        project_name = "全项目"
    
    rag_status = f"{len(engine.all_chunks)} chunks"
    changed, delta, total = engine.check_index_changes()
    if changed:
        rag_status += f" (索引已更新: {delta} chunks)"
    
    # 降噪
    if use_filter and alerts:
        filt = AlertFilter()
        filtered = filt.full_filter(alerts, push_level=push_level)
        push_alerts = filtered['push']
        digest_alerts = filtered['digest']
        stats = filtered['stats']
    else:
        push_alerts = alerts
        digest_alerts = []
        stats = {'raw': len(alerts), 'after_dedup': len(alerts), 'push_count': len(alerts)}
    
    # 生成摘要
    digest = AlertDigestBuilder.build_digest(
        push_alerts, digest_alerts, gaps, project_name, rag_status
    )
    digest_text = AlertDigestBuilder.format_digest_text(digest, max_detail=max_detail)
    
    return {
        'digest': digest,
        'digest_text': digest_text,
        'stats': stats,
        'rag_status': rag_status,
    }


# ============================================================
# 推送函数
# ============================================================

def push_alert_digest(
    push_level: str = "P1",
    project_dir: str = None,
    max_detail: int = 5,
    to_channel: str = None,
    to_target: str = None
) -> Dict:
    """
    推送RAG告警摘要
    
    to_channel: 推送渠道 (webchat / wecom / telegram等)
    to_target: 推送目标 (用户ID/群名)
    """
    # 生成带降噪的摘要
    result = rag_alert_with_noise_reduction(
        project_dir=project_dir,
        push_level=push_level,
        max_detail=max_detail,
    )
    
    digest_text = result['digest_text']
    stats = result['stats']
    
    # 有推送内容才推送
    push_count = stats.get('push_count', 0) + stats.get('digest_count', 0)
    if push_count == 0:
        print("[推送] 无新告警，跳过推送")
        # 也发一个无告警确认
        no_alert_msg = (
            f"🧠 RAG知识库预警简报\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"状态: ✅ 无新告警\n"
            f"RAG: {result.get('rag_status', 'N/A')}\n"
            f"来源: {project_dir or '全项目'}\n"
            f"时间: {datetime.now().strftime('%H:%M')}"
        )
        if to_channel:
            try:
                from openclaw import message
                message(action='send', channel=to_channel, to=to_target, message=no_alert_msg)
            except ImportError:
                print(f"[推送模拟] 渠道={to_channel}, 目标={to_target}")
                print(no_alert_msg)
        return result
    
    # 推送
    if to_channel:
        try:
            from openclaw import message
            message(action='send', channel=to_channel, to=to_target, message=digest_text)
            print(f"[推送] 已发送到 {to_channel}/{to_target}")
        except ImportError:
            print(f"[推送模拟] 渠道={to_channel}, 目标={to_target}")
            print(digest_text)
    else:
        # 无推送渠道，直接打印
        print(digest_text)
    
    return result


# ============================================================
# CLI
# ============================================================

if __name__ == '__main__':
    import argparse
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    parser = argparse.ArgumentParser(description='RAG知识库实时预警引擎 v2')
    parser.add_argument('--project-dir', help='单项目扫描目录')
    parser.add_argument('--report', action='store_true', help='生成原始预警报告')
    parser.add_argument('--digest', action='store_true', help='生成降噪摘要')
    parser.add_argument('--push', action='store_true', help='推送摘要到指定渠道')
    parser.add_argument('--channel', default='webchat', help='推送渠道 (webchat/wecom/telegram)')
    parser.add_argument('--target', help='推送目标')
    parser.add_argument('--push-level', default='P1', choices=['P0', 'P1', 'P2', 'P3'],
                       help='推送级别线 (<=此级别才推送，P0最紧急)')
    parser.add_argument('--max-detail', type=int, default=5, help='摘要中每条级别显示的最大条数')
    parser.add_argument('--json', action='store_true', help='JSON格式输出')
    parser.add_argument('--watch', action='store_true', help='持续监控模式')
    parser.add_argument('--interval', type=int, default=300, help='监控间隔(秒)')
    parser.add_argument('--no-filter', action='store_true', help='跳过降噪过滤')
    
    args = parser.parse_args()
    
    engine = RAGAlertEngine()
    engine.load_rag()
    
    if args.watch:
        print(f"RAG预警引擎启动，每{args.interval}秒扫描一次，推送级别线={args.push_level}...")
        print(f"按 Ctrl+C 停止\n")
        try:
            while True:
                push_alert_digest(
                    push_level=args.push_level,
                    project_dir=args.project_dir,
                    max_detail=args.max_detail,
                    to_channel=args.channel if args.push else None,
                    to_target=args.target,
                )
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n监控已停止")
    
    elif args.digest:
        result = push_alert_digest(
            push_level=args.push_level,
            project_dir=args.project_dir,
            max_detail=args.max_detail,
            to_channel=args.channel if args.push else None,
            to_target=args.target,
        )
        if args.json:
            print(json.dumps({
                'stats': result['stats'],
                'digest_text': result['digest_text'],
            }, ensure_ascii=False, indent=2))
    
    elif args.push:
        result = push_alert_digest(
            push_level=args.push_level,
            project_dir=args.project_dir,
            max_detail=args.max_detail,
            to_channel=args.channel,
            to_target=args.target,
        )
    
    elif args.report:
        print(engine.generate_report(args.project_dir))
    
    elif args.json:
        result = rag_alert_with_noise_reduction(
            project_dir=args.project_dir,
            push_level=args.push_level,
            use_filter=not args.no_filter,
        )
        print(json.dumps({
            'stats': result['stats'],
            'digest_text': result['digest_text'],
        }, ensure_ascii=False, indent=2))
    
    else:
        parser.print_help()