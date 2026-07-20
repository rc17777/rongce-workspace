#!/usr/bin/env python3
"""
wiki_l2.py — L2 轻量 LLM 层 (v4-flash, 免费可降级)
实体消歧 / 双链精排 / 摘要生成 / typed 关系提取

用法:
  python -X utf8 scripts/wiki_l2.py --disambiguate    # 实体消歧
  python -X utf8 scripts/wiki_l2.py --summarize       # 批量摘要
  python -X utf8 scripts/wiki_l2.py --relations       # 关系提取
  python -X utf8 scripts/wiki_l2.py --all             # 全部
"""
import json, sys, os, sqlite3, hashlib, time
from pathlib import Path
from datetime import datetime
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE = Path(__file__).parent.parent
CONFIG_DIR = WORKSPACE / "config"
DB_PATH = CONFIG_DIR / "entity_registry.sqlite"
sys.path.insert(0, str(WORKSPACE / "scripts"))
from entity_registry import EntityRegistry

# API 配置 (通过 cbwyy 代理)
try:
    from openai import OpenAI
    _config_path = WORKSPACE.parent / "openclaw.json"
    if _config_path.exists():
        with open(_config_path, 'r', encoding='utf-8') as _f:
            _cfg = json.load(_f)
        _prov = _cfg.get('models', {}).get('providers', {}).get('custom-cbwyy-top-v1', {})
        L2_BASE_URL = _prov.get('baseUrl', 'https://cbwyy.top/v1')
        L2_API_KEY = _prov.get('apiKey', os.getenv('OC_KEY_TOP_V1', ''))
    else:
        from dotenv import load_dotenv
        load_dotenv(WORKSPACE / ".env")
        L2_API_KEY = os.getenv("OC_KEY_TOP_V1") or os.getenv("DEEPSEEK_API_KEY", "")
        L2_BASE_URL = "https://cbwyy.top/v1"
    FLASH_CLIENT = OpenAI(api_key=L2_API_KEY, base_url=L2_BASE_URL) if L2_API_KEY else None
except ImportError:
    FLASH_CLIENT = None
    print("⚠ openai 未安装, L2 将使用降级模式")

L2_MODEL = "deepseek-v4-flash"  # 免费, 通过 cbwyy 代理
DEGRADED = False  # 降级标志


def call_l2(prompt, max_tokens=500, temperature=0.1):
    """调用 v4-flash，带降级"""
    global DEGRADED
    if DEGRADED or not FLASH_CLIENT:
        return None

    try:
        resp = FLASH_CLIENT.chat.completions.create(
            model=L2_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=30,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"  ⚠ L2 调用失败: {e}")
        DEGRADED = True
        return None


# ==================== 实体消歧 ====================

def disambiguate_entities(reg, batch_size=20):
    """批量实体消歧：找出可能的别名/同义实体对，让 L2 判断是否合并"""
    print("\n## L2 实体消歧")

    with sqlite3.connect(str(DB_PATH)) as db:
        db.row_factory = sqlite3.Row
        # 找疑似重复：同类型 + 名称相似度 > 0.6
        entities = db.execute("""
            SELECT id, canonical_name, entity_type FROM entities
            WHERE review_status != 'deprecated' AND entity_type IN ('organization', 'regulation', 'project')
            ORDER BY entity_type, canonical_name
        """).fetchall()

    # 按类型分组，找相似对
    groups = defaultdict(list)
    for e in entities:
        groups[e['entity_type']].append(e)

    candidates = []
    from difflib import SequenceMatcher

    for etype, items in groups.items():
        for i in range(len(items)):
            for j in range(i+1, len(items)):
                sim = SequenceMatcher(None, items[i]['canonical_name'], items[j]['canonical_name']).ratio()
                if 0.6 < sim < 0.95:  # 太像或太不像都不管
                    candidates.append((items[i], items[j], sim))

    candidates.sort(key=lambda x: x[2], reverse=True)
    print(f"  疑似重复对: {len(candidates)} (相似度 0.6-0.95)")

    if not candidates:
        return 0

    # 批量送 L2
    merged_count = 0
    for batch_start in range(0, min(len(candidates), 200), batch_size):
        batch = candidates[batch_start:batch_start+batch_size]

        prompt = """你是审计领域实体消歧专家。以下是一些可能重复或同义的实体对，请判断每对是否应合并为同一个实体。

判断标准：
- 同一机构的全称/简称/曾用名 → 是（如"四川省财政厅"和"省财政厅"）
- 同一法规的不同引用方式 → 是（如"《审计法》"和"《中华人民共和国审计法》"）
- 明显不同的实体 → 否
- 相似但不完全相同的法规（如不同年份版本）→ 否，标记为 related

请逐行回复，格式: id1|id2|yes/no/related|理由（一句话）

实体对列表：
"""
        for a, b, sim in batch:
            prompt += f"{a['id']}|{b['id']}|{a['canonical_name']}|{b['canonical_name']}|{a['entity_type']}|sim={sim:.2f}\n"

        result = call_l2(prompt, max_tokens=2000, temperature=0.0)
        if not result:
            # 降级：高相似度(>0.85)的自动合并
            for a, b, sim in batch:
                if sim > 0.85:
                    reg.merge_entities(b['id'], a['id'], f"降级模式-自动合并(相似度{sim:.2f})")
                    merged_count += 1
            reg.log_degradation('disambiguation', [f"{a['id']}|{b['id']}" for a, b, _ in batch],
                               "L2不可用, 高相似度自动合并")
            continue

        # 解析结果
        for line in result.strip().split('\n'):
            line = line.strip()
            if '|' not in line:
                continue
            parts = line.split('|')
            if len(parts) >= 3 and parts[2].strip().lower().startswith(('yes', 'y')):
                id1, id2 = parts[0].strip(), parts[1].strip()
                reason = parts[-1].strip() if len(parts) > 3 else "L2判断应合并"
                try:
                    reg.merge_entities(id2, id1, reason)
                    merged_count += 1
                    print(f"  合并: {id1[:8]} ← {id2[:8]} ({reason})")
                except Exception as e:
                    print(f"  合并失败: {e}")

    print(f"  完成: 合并 {merged_count} 对")
    return merged_count


# ==================== 批量摘要 ====================

def generate_summaries(reg, batch_size=30):
    """为无摘要的实体批量生成一句话摘要"""
    print("\n## L2 摘要生成")

    with sqlite3.connect(str(DB_PATH)) as db:
        db.row_factory = sqlite3.Row
        entities = db.execute("""
            SELECT id, canonical_name, entity_type, source_quote
            FROM entities
            WHERE (properties IS NULL OR properties NOT LIKE '%"summary"%')
              AND source_quote IS NOT NULL AND source_quote != ''
              AND review_status != 'deprecated'
            LIMIT 300
        """).fetchall()

    if not entities:
        print("  无需摘要的实体")
        return 0

    print(f"  待摘要: {len(entities)} 个实体")
    summarized = 0

    for i in range(0, len(entities), batch_size):
        batch = entities[i:i+batch_size]
        items = []
        for j, e in enumerate(batch):
            ctx = e['source_quote'][:200].replace('\n', ' ')
            items.append(f"{j+1}. [{e['entity_type']}] {e['canonical_name']}\n   上下文: {ctx}")

        prompt = f"""为以下审计领域实体各生成一句摘要（20字以内，只陈述事实）：

{chr(10).join(items)}

请逐行回复，格式: 序号|摘要
"""
        result = call_l2(prompt, max_tokens=1500, temperature=0.1)
        if not result:
            reg.log_degradation('summary', [e['id'] for e in batch], "L2不可用")
            continue

        for line in result.strip().split('\n'):
            line = line.strip()
            if '|' not in line:
                continue
            parts = line.split('|', 1)
            try:
                idx = int(parts[0].strip()) - 1
                summary = parts[1].strip()[:50]
                if 0 <= idx < len(batch):
                    eid = batch[idx]['id']
                    with sqlite3.connect(str(DB_PATH)) as db:
                        row = db.execute("SELECT properties FROM entities WHERE id=?", (eid,)).fetchone()
                        props = json.loads(row[0]) if row and row[0] else {}
                        props['summary'] = summary
                        db.execute("UPDATE entities SET properties=?, updated_at=? WHERE id=?",
                                  (json.dumps(props, ensure_ascii=False), datetime.now().isoformat(), eid))
                    summarized += 1
            except (ValueError, IndexError):
                pass

    print(f"  完成: 生成 {summarized} 条摘要")
    return summarized


# ==================== Typed 关系提取 ====================

def extract_typed_relations(reg, batch_size=15):
    """从实体共现中提取有类型的关系"""
    print("\n## L2 Typed 关系提取")

    # 找共现实体对（同一文档内出现的一对实体）
    with sqlite3.connect(str(DB_PATH)) as db:
        db.row_factory = sqlite3.Row
        doc_entities = db.execute("""
            SELECT source_doc_id, id, canonical_name, entity_type, source_quote
            FROM entities
            WHERE source_doc_id IS NOT NULL
              AND review_status != 'deprecated'
            ORDER BY source_doc_id
        """).fetchall()

    # 按文档分组
    doc_groups = defaultdict(list)
    for e in doc_entities:
        doc_groups[e['source_doc_id']].append(e)

    # 每个文档内找实体对
    candidate_pairs = []
    seen_pairs = set()
    for doc_id, ents in doc_groups.items():
        if len(ents) < 2:
            continue
        for i in range(len(ents)):
            for j in range(i+1, len(ents)):
                if ents[i]['entity_type'] == ents[j]['entity_type']:
                    continue  # 同类型跳过
                pair_key = tuple(sorted([ents[i]['id'], ents[j]['id']]))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                # 检查是否已有关系
                existing = db.execute(
                    "SELECT COUNT(*) FROM relations WHERE subject_id=? AND object_id=?",
                    (ents[i]['id'], ents[j]['id'])
                ).fetchone()[0]
                if existing:
                    continue

                candidate_pairs.append((ents[i], ents[j], doc_id))

    # 按实体类型多样性排序，优先处理跨类型对
    candidate_pairs.sort(key=lambda x: (x[0]['entity_type'] == x[1]['entity_type'],))

    print(f"  候选关系对: {len(candidate_pairs)}")
    if not candidate_pairs:
        return 0

    # 关系类型定义
    relation_defs = """
可用关系类型:
- regulates: A约束B (法规→项目/资金/审计问题)
- references: A引用B (审计问题/程序→法规)
- involves: A涉及B (项目/审计问题→机构/法规)
- supersedes: A替代B (法规→法规)
- belongs_to: A隶属B (项目/资金→机构)
- uses: A使用B (项目→资金)
- no_relation: 无明显关系
"""

    created = 0
    for i in range(0, min(len(candidate_pairs), 150), batch_size):
        batch = candidate_pairs[i:i+batch_size]
        items = []
        for j, (a, b, _) in enumerate(batch):
            items.append(f"{j+1}. [{a['entity_type']}] {a['canonical_name']}\n   [{b['entity_type']}] {b['canonical_name']}")

        prompt = f"""你是审计领域关系抽取专家。判断以下实体对之间的业务关系。

{relation_defs}

请逐行回复，格式: 序号|关系类型|置信度(0-1)|一句话理由

实体对:
{chr(10).join(items)}"""
        result = call_l2(prompt, max_tokens=1500, temperature=0.0)
        if not result:
            reg.log_degradation('relation_extraction', [f"{a['id']}|{b['id']}" for a, b, _ in batch], "L2不可用")
            continue

        for line in result.strip().split('\n'):
            line = line.strip()
            if '|' not in line:
                continue
            parts = line.split('|')
            if len(parts) < 3:
                continue
            try:
                idx = int(parts[0].strip()) - 1
                rel_type = parts[1].strip().lower()
                confidence = float(parts[2].strip())
                if 0 <= idx < len(batch) and rel_type != 'no_relation' and confidence >= 0.7:
                    a, b, doc_id = batch[idx]
                    status = 'llm_verified' if confidence >= 0.85 else 'candidate'
                    reg.add_relation(
                        a['id'], rel_type, b['id'],
                        evidence_doc_id=doc_id,
                        evidence_quote=f"{a.get('source_quote', '')} | {b.get('source_quote', '')}",
                        confidence=confidence,
                        relation_status=status,
                        extractor='l2_flash',
                    )
                    created += 1
            except (ValueError, IndexError):
                pass

    print(f"  完成: 创建 {created} 条关系")
    return created


# ==================== 双链精排 ====================

def refine_links(reg, top_n=200):
    """精排双链候选：让 L2 判断从 wiki_compile 产出的候选链接是否值得保留"""
    print("\n## L2 双链精排")

    WIKI_DIR = WORKSPACE / "obsidian-vault" / "wiki"
    if not WIKI_DIR.exists():
        print("  wiki 目录不存在")
        return 0

    # 收集所有候选双链（从相似度计算来）
    # 这里简化：找所有 wiki 页面，对每页找最相似的5篇
    pages = list(WIKI_DIR.rglob("*.md"))
    if len(pages) < 2:
        return 0

    from difflib import SequenceMatcher
    candidates = []
    for i in range(min(len(pages), top_n)):
        for j in range(i+1, min(len(pages), i+6)):
            if j >= len(pages):
                break
            name_i = pages[i].stem
            name_j = pages[j].stem
            text_i = pages[i].read_text(encoding='utf-8', errors='replace')[:1000]
            text_j = pages[j].read_text(encoding='utf-8', errors='replace')[:1000]
            sim = SequenceMatcher(None, text_i, text_j).ratio()
            if sim > 0.25:
                candidates.append((pages[i], pages[j], sim))

    if not candidates:
        return 0

    print(f"  候选链接: {len(candidates)}")
    confirmed = 0
    batch_size = 20

    for i in range(0, min(len(candidates), 200), batch_size):
        batch = candidates[i:i+batch_size]
        items = []
        for j, (a, b, sim) in enumerate(batch):
            items.append(f"{j+1}. {a.stem} ↔ {b.stem} (相似度={sim:.2f})")

        prompt = f"""判断以下页面对应否建立双向链接。标准：
- 同一主题的不同角度 → yes
- 一个文档引用了另一个的核心内容 → yes
- 只有表面文字相似但无关 → no

回复: 序号|yes/no

{chr(10).join(items)}"""
        result = call_l2(prompt, max_tokens=1000, temperature=0.0)
        if not result:
            reg.log_degradation('link_refinement', [f"{a.stem}|{b.stem}" for a, b, _ in batch], "L2不可用")
            continue

        for line in result.strip().split('\n'):
            line = line.strip()
            if '|' not in line:
                continue
            parts = line.split('|')
            try:
                idx = int(parts[0].strip()) - 1
                decision = parts[1].strip().lower()
                if 0 <= idx < len(batch) and decision.startswith('y'):
                    a, b, _ = batch[idx]
                    # 写入确认链接到页面
                    _add_confirmed_link(a, b)
                    _add_confirmed_link(b, a)
                    confirmed += 1
            except (ValueError, IndexError):
                pass

    print(f"  完成: 确认 {confirmed} 条链接")
    return confirmed


def _add_confirmed_link(page, target):
    """在页面底部添加确认链接"""
    content = page.read_text(encoding='utf-8', errors='replace')
    link_section = '\n## 🔗 建议关联\n'
    link_line = f'- [[{target.stem}]]\n'

    if link_section in content:
        if link_line not in content:
            content = content.replace(link_section, link_section + link_line)
    else:
        if '<!-- AUTO:end -->' in content:
            content = content.replace('<!-- AUTO:end -->', f'\n{link_section}{link_line}\n<!-- AUTO:end -->')
        else:
            content += f'\n{link_section}{link_line}'

    page.write_text(content, encoding='utf-8')


# ==================== 主流程 ====================

def run_l2_all():
    """执行全部 L2 任务"""
    print("=" * 60)
    print(f"L2 管线启动 (模型: {L2_MODEL})")
    print("=" * 60)

    if not FLASH_CLIENT:
        print("⚠ DeepSeek API 未配置, 将使用降级模式")
        global DEGRADED
        DEGRADED = True

    reg = EntityRegistry()

    # 1. 实体消歧
    n1 = disambiguate_entities(reg)

    # 2. 摘要生成
    n2 = generate_summaries(reg)

    # 3. Typed 关系提取
    n3 = extract_typed_relations(reg)

    # 4. 双链精排
    n4 = refine_links(reg)

    # 统计
    stats = reg.stats()
    print(f"\n{'='*60}")
    print(f"L2 完成: 消歧合并 {n1} | 摘要 {n2} | 关系 {n3} | 链接确认 {n4}")
    print(f"注册表: {stats['total_entities']} 实体, {stats['total_relations']} 关系")
    if stats['degraded_tasks']:
        print(f"⚠ 降级任务: {stats['degraded_tasks']} 条, 恢复后运行 python scripts/wiki_l2.py --replay")


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--disambiguate', action='store_true')
    p.add_argument('--summarize', action='store_true')
    p.add_argument('--relations', action='store_true')
    p.add_argument('--links', action='store_true')
    p.add_argument('--all', action='store_true')
    p.add_argument('--replay', action='store_true', help='回补降级任务')
    args = p.parse_args()

    if args.replay:
        reg = EntityRegistry()
        unplayed = reg.get_unreplayed()
        print(f"未回补降级任务: {len(unplayed)}")
        if unplayed:
            print("重新运行 L2 管线恢复...")
            DEGRADED = False
            disambiguate_entities(reg)
            generate_summaries(reg)
            extract_typed_relations(reg)
            for u in unplayed:
                reg.mark_replayed(u['id'])
            print("✅ 降级任务回补完成")
        return

    if args.all or (not any([args.disambiguate, args.summarize, args.relations, args.links])):
        run_l2_all()
    else:
        reg = EntityRegistry()
        if args.disambiguate:
            disambiguate_entities(reg)
        if args.summarize:
            generate_summaries(reg)
        if args.relations:
            extract_typed_relations(reg)
        if args.links:
            refine_links(reg)


if __name__ == '__main__':
    main()
