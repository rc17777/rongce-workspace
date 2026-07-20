#!/usr/bin/env python3
"""
wiki_l3.py — L3 深度 LLM 层 (v4-pro, 按需)
矛盾仲裁 / 知识缺口分析 / 全文重写 / 法规时点校验

用法:
  python -X utf8 scripts/wiki_l3.py --contradictions    # 矛盾检测
  python -X utf8 scripts/wiki_l3.py --gaps              # 知识缺口分析
  python -X utf8 scripts/wiki_l3.py --validate-regs     # 法规时效校验
  python -X utf8 scripts/wiki_l3.py --all               # 全部
"""
import json, sys, os, sqlite3, re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE = Path(__file__).parent.parent
CONFIG_DIR = WORKSPACE / "config"
DB_PATH = CONFIG_DIR / "entity_registry.sqlite"
WIKI_DIR = WORKSPACE / "obsidian-vault" / "wiki"
sys.path.insert(0, str(WORKSPACE / "scripts"))
from entity_registry import EntityRegistry

# API (通过 cbwyy 代理)
try:
    from openai import OpenAI
    _config_path = WORKSPACE.parent / "openclaw.json"
    if _config_path.exists():
        with open(_config_path, 'r', encoding='utf-8') as _f:
            _cfg = json.load(_f)
        _prov = _cfg.get('models', {}).get('providers', {}).get('custom-cbwyy-top-v1', {})
        L3_BASE_URL = _prov.get('baseUrl', 'https://cbwyy.top/v1')
        L3_API_KEY = _prov.get('apiKey', os.getenv('OC_KEY_TOP_V1', ''))
    else:
        from dotenv import load_dotenv
        load_dotenv(WORKSPACE / ".env")
        L3_API_KEY = os.getenv("OC_KEY_TOP_V1") or os.getenv("DEEPSEEK_API_KEY", "")
        L3_BASE_URL = "https://cbwyy.top/v1"
    PRO_CLIENT = OpenAI(api_key=L3_API_KEY, base_url=L3_BASE_URL) if L3_API_KEY else None
except ImportError:
    PRO_CLIENT = None

L3_MODEL = "deepseek-v4-pro"  # 按需, 通过 cbwyy 代理


def call_l3(prompt, max_tokens=2000, temperature=0.1):
    if not PRO_CLIENT:
        print("  ⚠ DeepSeek API 未配置")
        return None
    try:
        resp = PRO_CLIENT.chat.completions.create(
            model=L3_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=60,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"  ⚠ L3 调用失败: {e}")
        return None


# ==================== 矛盾仲裁 ====================

def detect_contradictions(reg):
    """
    L1 预筛候选对 → L2 预判 → L3 最终裁决
    L1: 同类型实体 + 同属性 + 数值/日期不一致
    """
    print("\n## L3 矛盾检测")

    # Step 1: L1 预筛 —— 找金额/日期不一致的候选对
    candidates = []
    with sqlite3.connect(str(DB_PATH)) as db:
        db.row_factory = sqlite3.Row

        # 查资金类实体：同一类型、同名、不同金额
        funds = db.execute("""
            SELECT id, canonical_name, properties, source_doc_id, source_quote
            FROM entities
            WHERE entity_type='fund' AND review_status != 'deprecated'
              AND properties IS NOT NULL AND properties != '{}'
        """).fetchall()

        # 按名称分组
        fund_groups = defaultdict(list)
        for f in funds:
            name = re.sub(r'\d+\.?\d*万[元圆]?', '', f['canonical_name']).strip()
            fund_groups[name].append(f)

        for name, items in fund_groups.items():
            if len(items) < 2:
                continue
            for i in range(len(items)):
                for j in range(i+1, len(items)):
                    try:
                        p_i = json.loads(items[i]['properties'])
                        p_j = json.loads(items[j]['properties'])
                        amt_i = p_i.get('amount_wan_yuan', 0)
                        amt_j = p_j.get('amount_wan_yuan', 0)
                        if amt_i > 0 and amt_j > 0 and abs(amt_i - amt_j) / max(amt_i, amt_j) > 0.1:
                            candidates.append({
                                'type': 'amount_conflict',
                                'entity_a': dict(items[i]),
                                'entity_b': dict(items[j]),
                                'detail': f"{name}: {amt_i:.2f}万元 vs {amt_j:.2f}万元",
                                'diff_pct': abs(amt_i - amt_j) / max(amt_i, amt_j) * 100,
                            })
                    except (json.JSONDecodeError, KeyError, ZeroDivisionError):
                        pass

    # 按差异度排序，取前20个最可疑的
    candidates.sort(key=lambda x: x.get('diff_pct', 0), reverse=True)
    candidates = candidates[:20]

    print(f"  L1 候选矛盾: {len(candidates)} 对")

    if not candidates:
        print("  未发现明显矛盾")
        return 0

    arbited = 0
    for c in candidates:
        if c['type'] == 'amount_conflict':
            prompt = f"""你是审计矛盾仲裁专家。判断以下两条金额陈述是否存在实质矛盾，或只是不同范围/时点的正常差异。

陈述A:
  实体: {c['entity_a']['canonical_name']}
  来源: {c['entity_a'].get('source_quote', '')[:300]}

陈述B:
  实体: {c['entity_b']['canonical_name']}
  来源: {c['entity_b'].get('source_quote', '')[:300]}

请按以下格式回复:
判定: 矛盾/无矛盾/无法判断
置信度: 0-1
理由: 一句话
建议: (如有, 一句话)"""

            result = call_l3(prompt, max_tokens=400)
            if not result:
                continue

            verdict = _parse_verdict(result)
            if verdict['判定'] == '矛盾' and verdict.get('置信度', 0) >= 0.7:
                # 记录矛盾
                reg.add_relation(
                    c['entity_a']['id'], 'conflicts_with', c['entity_b']['id'],
                    properties={'type': 'amount_conflict', 'detail': c['detail'], 'verdict': verdict},
                    evidence_quote=f"A:{c['entity_a'].get('source_quote','')[:100]}|B:{c['entity_b'].get('source_quote','')[:100]}",
                    confidence=verdict.get('置信度', 0.7),
                    relation_status='candidate',
                    extractor='l3_pro',
                )
                arbited += 1
                print(f"  ⚡ 矛盾: {c['detail'][:60]}")

    print(f"  完成: 确认 {arbited} 处矛盾")
    return arbited


def _parse_verdict(text):
    verdict = {}
    for line in text.split('\n'):
        if ':' in line:
            k, v = line.split(':', 1)
            k, v = k.strip(), v.strip()
            verdict[k] = v
            if k == '置信度':
                try:
                    verdict[k] = float(v)
                except ValueError:
                    verdict[k] = 0.5
    return verdict


# ==================== 知识缺口分析 ====================

def analyze_knowledge_gaps(reg):
    """分析知识库覆盖缺口"""
    print("\n## L3 知识缺口分析")

    stats = reg.stats()
    by_type = stats.get('by_type', {})

    # 找缺口信号
    gaps = []

    # 缺口1: 孤儿实体过多
    with sqlite3.connect(str(DB_PATH)) as db:
        db.row_factory = sqlite3.Row
        # 没有关系的实体
        no_rels = db.execute("""
            SELECT e.id, e.canonical_name, e.entity_type
            FROM entities e
            WHERE e.review_status != 'deprecated'
              AND NOT EXISTS (SELECT 1 FROM relations r WHERE r.subject_id=e.id OR r.object_id=e.id)
            LIMIT 100
        """).fetchall()

    if no_rels:
        gap_entities = [{'name': r['canonical_name'], 'type': r['entity_type']} for r in no_rels[:30]]
        gaps.append({
            'type': 'orphan_entities',
            'severity': 'P2',
            'description': f"{len(no_rels)} 个实体无任何关系连接",
            'entities': gap_entities,
        })

    # 缺口2: 实体类型分布失衡
    expected_types = {'regulation': 0.15, 'project': 0.15, 'organization': 0.25, 'audit_finding': 0.10}
    total = stats['total_entities']
    for etype, expected_ratio in expected_types.items():
        actual = by_type.get(etype, 0) / total if total else 0
        if actual < expected_ratio * 0.3:  # 不到预期的30%
            gaps.append({
                'type': 'entity_type_deficit',
                'severity': 'P2',
                'description': f"实体类型 '{etype}' 占比 {actual:.1%}, 预期 {expected_ratio:.0%}",
            })

    # 缺口3: L3 深度分析
    if gaps:
        entities_summary = '\n'.join(
            f"- [{g['type']}] {g['description']}"
            for g in gaps
        )
        prompt = f"""你是审计知识管理专家。当前知识库发现以下缺口：

{entities_summary}

请给出具体的知识补充建议（各2-3条），按优先级排列：
1. 当前最需要补充哪些类型的文档/法规？
2. 哪些主题明显覆盖不足？
3. 建议优先人工创建哪些核心页面？"""

        result = call_l3(prompt, max_tokens=1000)
        if result:
            # 保存缺口报告
            report_path = WORKSPACE / "output" / "knowledge_gap_report.md"
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report = f"""# 知识缺口分析报告
> 生成时间: {datetime.now().isoformat()}

## 自动检测的缺口

{chr(10).join(f'### {g["type"]}\n- 严重程度: {g["severity"]}\n- {g["description"]}' for g in gaps)}

## L3 深度建议

{result}
"""
            report_path.write_text(report, encoding='utf-8')
            print(f"  📄 缺口报告: {report_path}")

    print(f"  完成: 检测到 {len(gaps)} 个缺口")
    return len(gaps)


# ==================== 法规时效校验 ====================

def validate_regulation_aging(reg):
    """批量校验法规时效状态"""
    print("\n## L3 法规时效校验")

    with sqlite3.connect(str(DB_PATH)) as db:
        db.row_factory = sqlite3.Row
        # 找状态未知的法规
        unknown = db.execute("""
            SELECT id, canonical_name, properties, source_quote
            FROM entities
            WHERE entity_type='regulation'
              AND review_status != 'deprecated'
              AND (properties IS NULL OR properties NOT LIKE '%"status"%')
            LIMIT 50
        """).fetchall()

    if not unknown:
        print("  所有法规已有状态标注")
        return 0

    print(f"  待校验法规: {len(unknown)}")

    batch_size = 15
    validated = 0

    for i in range(0, len(unknown), batch_size):
        batch = unknown[i:i+batch_size]
        items = []
        for j, r in enumerate(batch):
            ctx = r['source_quote'][:200] if r['source_quote'] else ''
            items.append(f"{j+1}. {r['canonical_name']}\n   上下文: {ctx}")

        prompt = f"""你是法规时效判断专家。判断以下法规的效力状态。

状态选项: 现行有效 / 已修订 / 已废止 / 部分废止 / 征求意见稿 / 未知

如果上下文提供的信息不足，请标注"未知"。

回复格式: 序号|状态|置信度(0-1)|一句理由

{chr(10).join(items)}"""
        result = call_l3(prompt, max_tokens=1000, temperature=0.0)
        if not result:
            continue

        for line in result.strip().split('\n'):
            line = line.strip()
            if '|' not in line:
                continue
            parts = line.split('|')
            try:
                idx = int(parts[0].strip()) - 1
                status = parts[1].strip()
                conf = float(parts[2].strip()) if len(parts) > 2 else 0.7
                if 0 <= idx < len(batch) and conf >= 0.5:
                    eid = batch[idx]['id']
                    with sqlite3.connect(str(DB_PATH)) as db:
                        row = db.execute("SELECT properties FROM entities WHERE id=?", (eid,)).fetchone()
                        props = json.loads(row[0]) if row and row[0] else {}
                        props['status'] = status
                        props['status_confidence'] = conf
                        props['status_source'] = 'l3_pro'
                        db.execute("UPDATE entities SET properties=?, review_status=? WHERE id=?",
                                  (json.dumps(props, ensure_ascii=False),
                                   'confirmed' if conf >= 0.85 else 'pending',
                                   eid))
                    validated += 1
            except (ValueError, IndexError):
                pass

    print(f"  完成: 校验 {validated} 条法规")
    return validated


# ==================== 主流程 ====================

def run_l3_all():
    print("=" * 60)
    print(f"L3 管线启动 (模型: {L3_MODEL})")
    print("=" * 60)

    if not PRO_CLIENT:
        print("❌ DeepSeek API 未配置, 无法运行 L3")
        return

    reg = EntityRegistry()

    n1 = detect_contradictions(reg)
    n2 = validate_regulation_aging(reg)
    n3 = analyze_knowledge_gaps(reg)

    stats = reg.stats()
    print(f"\n{'='*60}")
    print(f"L3 完成: 矛盾 {n1} | 法规校验 {n2} | 缺口 {n3}")
    print(f"注册表: {stats['total_entities']} 实体, {stats['total_relations']} 关系")
    print(f"💰 预估费用: ~{(n1+n2+n3)*0.05:.2f} ¥")


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--contradictions', action='store_true')
    p.add_argument('--gaps', action='store_true')
    p.add_argument('--validate-regs', action='store_true')
    p.add_argument('--all', action='store_true')
    args = p.parse_args()

    if not PRO_CLIENT:
        print("❌ 请先配置 DEEPSEEK_API_KEY 环境变量")
        return

    reg = EntityRegistry()

    if args.contradictions:
        detect_contradictions(reg)
    if args.gaps:
        analyze_knowledge_gaps(reg)
    if args.validate_regs:
        validate_regulation_aging(reg)
    if args.all:
        run_l3_all()
    if not any([args.contradictions, args.gaps, args.validate_regs, args.all]):
        p.print_help()


if __name__ == '__main__':
    main()
