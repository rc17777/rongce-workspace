#!/usr/bin/env python3
"""
wiki_compile.py — 融策 wiki 知识库编译管线
L1 本地层: chunk合并 → 实体抽取 → 注册表 → 语义相似度 → 规则Lint → 页面生成
L2 轻量LLM层: 实体消歧/双链精排/摘要/关系提取 (v4-flash, 可降级)
L3 深度LLM层: 矛盾仲裁/知识缺口 (v4-pro, 按需)

用法:
  python -X utf8 scripts/wiki_compile.py --init          # 初始化
  python -X utf8 scripts/wiki_compile.py --compile       # 全库编译 (L1 only)
  python -X utf8 scripts/wiki_compile.py --compile --l2  # L1+L2
  python -X utf8 scripts/wiki_compile.py --incremental   # 增量更新
  python -X utf8 scripts/wiki_compile.py --stats         # 统计
"""
import re, json, os, sys, hashlib, argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

# 本地依赖
try:
    import sqlite3
    import yaml
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError as e:
    print(f"缺少依赖: {e}. 运行: pip install pyyaml scikit-learn numpy")
    sys.exit(1)

# 可选依赖
HAS_TEXT2VEC = False
# 注: BGE 模型需要从 HuggingFace 下载，国内环境可能被墙
# 如需启用: 先配置 HF_ENDPOINT=https://hf-mirror.com 环境变量
# try:
#     from sentence_transformers import SentenceTransformer
#     HAS_TEXT2VEC = True
# except ImportError:
#     pass

HAS_FAISS = False
try:
    import faiss
    HAS_FAISS = True
except ImportError:
    print("⚠ faiss 未安装, 将使用暴力搜索")

WORKSPACE = Path(__file__).parent.parent
CONFIG_DIR = WORKSPACE / "config"
KNOWLEDGE_DIR = WORKSPACE / "knowledge"
OBSIDIAN_DIR = WORKSPACE / "obsidian-vault"
WIKI_OUTPUT = WORKSPACE / "obsidian-vault" / "wiki"
sys.path.insert(0, str(WORKSPACE / "scripts"))
from entity_registry import EntityRegistry


class WikiCompiler:
    """wiki 知识库编译器"""

    def __init__(self, use_l2=False, use_l3=False):
        self.use_l2 = use_l2
        self.use_l3 = use_l3
        self.reg = EntityRegistry()
        self.ontology = self._load_ontology()
        self.embed_model = None
        self.embed_index = None
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.stats = defaultdict(int)

    def _load_ontology(self):
        path = CONFIG_DIR / "ontology.yaml"
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        print("⚠ ontology.yaml 未找到，使用默认配置")
        return {}

    # ========== L1: 文档合并与预处理 ==========

    def collect_documents(self, source_dirs=None):
        """收集知识库文档，合并 chunks"""
        if source_dirs is None:
            source_dirs = [KNOWLEDGE_DIR, OBSIDIAN_DIR]

        documents = []
        for src_dir in source_dirs:
            if not Path(src_dir).exists():
                continue
            for md_file in Path(src_dir).rglob("*.md"):
                try:
                    content = md_file.read_text(encoding='utf-8', errors='replace')
                    if len(content.strip()) < 50:
                        continue
                    doc_id = hashlib.md5(str(md_file).encode()).hexdigest()[:12]
                    documents.append({
                        'id': doc_id,
                        'path': str(md_file),
                        'filename': md_file.name,
                        'content': content,
                        'hash': hashlib.md5(content.encode()).hexdigest(),
                        'size': len(content),
                        'source_type': 'original',
                    })
                except Exception as e:
                    print(f"  跳过 {md_file}: {e}")

        print(f"收集文档: {len(documents)} 篇")
        return documents

    # ========== L1: 实体抽取 ==========

    def extract_entities(self, documents):
        """正则 + 词典 抽取审计实体"""
        entity_types = self.ontology.get('entity_types', {})
        all_entities = []

        for doc in documents:
            content = doc['content']
            doc_entities = []

            for etype, config in entity_types.items():
                patterns = config.get('patterns', [])
                for p in patterns:
                    if 'regex' in p:
                        matches = re.finditer(p['regex'], content)
                        for m in matches:
                            name = m.group(0).strip()
                            if len(name) < 2 or len(name) > 80:
                                continue
                            doc_entities.append({
                                'name': name,
                                'type': etype,
                                'confidence': p.get('priority', 60) / 100.0,
                                'extractor': 'regex',
                                'char_start': m.start(),
                                'char_end': m.end(),
                                'source_quote': content[max(0,m.start()-20):m.end()+20],
                            })
                    elif 'keywords' in p:
                        for kw in p['keywords']:
                            for m in re.finditer(re.escape(kw), content):
                                doc_entities.append({
                                    'name': kw,
                                    'type': etype,
                                    'confidence': p.get('priority', 70) / 100.0,
                                    'extractor': 'dictionary',
                                    'char_start': m.start(),
                                    'char_end': m.end(),
                                    'source_quote': content[max(0,m.start()-20):m.end()+20],
                                })
                    elif 'patterns' in p:
                        for sub_pat in p['patterns']:
                            for m in re.finditer(sub_pat, content):
                                name = m.group(0).strip()
                                if len(name) < 2:
                                    continue
                                doc_entities.append({
                                    'name': name,
                                    'type': etype,
                                    'confidence': p.get('priority', 85) / 100.0,
                                    'extractor': 'dictionary',
                                    'char_start': m.start(),
                                    'char_end': m.end(),
                                    'source_quote': content[max(0,m.start()-20):m.end()+20],
                                })

            # 金额归一化
            amount_config = self.ontology.get('normalization', {}).get('amount', {})
            for ap in amount_config.get('patterns', []):
                for m in re.finditer(ap['pattern'], content):
                    try:
                        raw_val = m.group(1).replace(',', '')
                        val = float(raw_val) * ap['factor']
                        name = f"{val:.2f}万元"
                        doc_entities.append({
                            'name': name,
                            'type': 'fund',
                            'confidence': 0.90,
                            'extractor': 'regex',
                            'normalized_amount': val,
                            'char_start': m.start(),
                            'char_end': m.end(),
                            'source_quote': content[max(0,m.start()-30):m.end()+30],
                        })
                    except ValueError:
                        pass

            # 去重: 同文档内同名同类型只保留最高置信度
            seen = {}
            for e in doc_entities:
                key = (e['name'], e['type'])
                if key not in seen or e['confidence'] > seen[key]['confidence']:
                    seen[key] = e

            for e in seen.values():
                all_entities.append({
                    'doc_id': doc['id'],
                    'doc_path': doc['path'],
                    'content_hash': doc['hash'],
                    **e
                })

        print(f"抽取实体候选: {len(all_entities)}")
        self.stats['entities_extracted'] = len(all_entities)
        return all_entities

    # ========== L1: 注册表入库 ==========

    def register_entities(self, entities):
        """实体写入注册表"""
        new_count, exist_count = 0, 0

        for e in entities:
            eid, is_new = self.reg.upsert_entity(
                canonical_name=e['name'],
                entity_type=e['type'],
                source_doc_id=e['doc_id'],
                source_quote=e.get('source_quote', ''),
                char_start=e.get('char_start'),
                char_end=e.get('char_end'),
                confidence=e['confidence'],
                extractor=e['extractor'],
                extractor_version='v1.0',
                source_type='original',
            )
            if is_new:
                new_count += 1
                # 尝试从内容提取更多元数据
                self._extract_entity_metadata(eid, e)
            else:
                exist_count += 1

        print(f"注册表: 新增 {new_count}, 已存在 {exist_count}")
        self.stats['entities_new'] = new_count
        self.stats['entities_existing'] = exist_count

    def _extract_entity_metadata(self, eid, entity):
        """从原文提取实体属性 (日期/金额等)"""
        quote = entity.get('source_quote', '')
        etype = entity['type']

        if etype == 'regulation':
            # 提取日期
            dates = re.findall(r'(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})', quote)
            if dates:
                d = dates[0]
                date_str = f"{d[0]}-{int(d[1]):02d}-{int(d[2]):02d}"
                self.reg._update_entity(eid, valid_from=date_str)

        elif etype == 'fund' and 'normalized_amount' in entity:
            props = {'amount_wan_yuan': entity['normalized_amount']}
            self.reg._update_entity(eid, properties=props)

    # ========== L1: 语义相似度与双链候选 ==========

    def build_similarity_index(self, documents):
        """构建语义索引"""
        texts = [f"{d['filename']}\n{d['content'][:2000]}" for d in documents]
        doc_ids = [d['id'] for d in documents]

        # 当前使用 TF-IDF（BGE 需要 HuggingFace 下载，国内被墙）
        print("使用 TF-IDF 构建语义索引 (BGE 待网络配置后启用)...")
        self.tfidf_vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
        tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
        self._tfidf_data = (tfidf_matrix, doc_ids)

        self._doc_texts = dict(zip(doc_ids, texts))
        self._docs = {d['id']: d for d in documents}

    def find_similar_docs(self, doc_id, top_k=10):
        """为文档找到最相似的文档作为双链候选"""
        if not hasattr(self, '_doc_texts'):
            return []

        idx = None
        if HAS_TEXT2VEC and hasattr(self, '_embed_data'):
            embeddings, doc_ids = self._embed_data
            idx = next((i for i, did in enumerate(doc_ids) if did == doc_id), None)
            if idx is not None and self.embed_index:
                D, I = self.embed_index.search(embeddings[idx:idx+1], top_k+1)
                results = [(doc_ids[I[0][i]], float(D[0][i])) for i in range(1, min(top_k+1, len(I[0])))]
            elif idx is not None:
                sims = cosine_similarity(embeddings[idx:idx+1], embeddings)[0]
                top_indices = np.argsort(sims)[::-1][1:top_k+1]
                results = [(doc_ids[i], float(sims[i])) for i in top_indices]
            else:
                return []
        elif hasattr(self, '_tfidf_data'):
            tfidf_matrix, doc_ids = self._tfidf_data
            idx = next((i for i, did in enumerate(doc_ids) if did == doc_id), None)
            if idx is None:
                return []
            sims = cosine_similarity(tfidf_matrix[idx:idx+1], tfidf_matrix)[0]
            top_indices = np.argsort(sims)[::-1][1:top_k+1]
            results = [(doc_ids[i], float(sims[i])) for i in top_indices]
        else:
            return []

        # 过滤: 相似度太低的不链接
        results = [(did, s) for did, s in results if s > 0.3]
        return results

    # ========== L1: 规则 Lint ==========

    def run_lint(self, documents):
        """规则引擎健康检查"""
        issues = []
        doc_paths = {d['path'] for d in documents}
        wiki_pages = list(Path(WIKI_OUTPUT).rglob("*.md")) if WIKI_OUTPUT.exists() else []

        # 死链检查
        for wp in wiki_pages:
            content = wp.read_text(encoding='utf-8', errors='replace')
            links = re.findall(r'\[\[([^\]]+)\]\]', content)
            for link in links:
                target = WIKI_OUTPUT / f"{link}.md"
                if not target.exists():
                    issues.append({
                        'type': 'broken_link', 'severity': 'P2',
                        'source': str(wp), 'detail': f"链接目标不存在: [[{link}]]"
                    })

        # 孤儿页检测 (链接数<2)
        link_count = defaultdict(int)
        for wp in wiki_pages:
            content = wp.read_text(encoding='utf-8', errors='replace')
            links = re.findall(r'\[\[([^\]]+)\]\]', content)
            link_count[str(wp)] += len(links)
            for link in links:
                target = WIKI_OUTPUT / f"{link}.md"
                link_count[str(target)] += 1

        for wp in wiki_pages:
            if link_count.get(str(wp), 0) < 2:
                issues.append({
                    'type': 'orphan_page', 'severity': 'P2',
                    'source': str(wp), 'detail': f"孤立页面，链接数={link_count.get(str(wp), 0)}"
                })

        # 过期法规引用告警
        aging = self.ontology.get('regulation_aging', {}).get('lint_rules', [])
        for rule in aging:
            if rule['name'] == '引用已废止法规':
                for wp in wiki_pages:
                    content = wp.read_text(encoding='utf-8', errors='replace')
                    reg_refs = re.findall(r'《([^》]+)》', content)
                    for ref in reg_refs:
                        entity = self.reg.find_by_name(ref, 'regulation')
                        if entity:
                            props = json.loads(entity.get('properties', '{}'))
                            if props.get('status') == '已废止':
                                issues.append({
                                    'type': 'deprecated_regulation_ref', 'severity': rule['severity'],
                                    'source': str(wp), 'detail': f"引用已废止法规: {ref}"
                                })

        # 缺 frontmatter
        for wp in wiki_pages:
            content = wp.read_text(encoding='utf-8', errors='replace')
            if not content.startswith('---'):
                issues.append({
                    'type': 'missing_frontmatter', 'severity': 'P2',
                    'source': str(wp), 'detail': "缺少 YAML frontmatter"
                })

        print(f"Lint 检查: 发现 {len(issues)} 个问题")
        self.stats['lint_issues'] = len(issues)
        return issues

    # ========== L1: Wiki 页面生成 ==========

    def generate_wiki_pages(self, documents):
        """从文档生成四类结构化 wiki 页面"""
        templates = self.ontology.get('page_templates', {})
        WIKI_OUTPUT.mkdir(parents=True, exist_ok=True)

        generated = 0
        for doc in documents:
            entity_type = self._classify_document(doc)
            template = templates.get(entity_type, {})
            sections = template.get('sections', ['摘要', '来源'])
            locked = template.get('locked_fields', [])

            # 构建 YAML frontmatter
            fm = {
                'title': doc['filename'].replace('.md', ''),
                'type': entity_type,
                'source': doc['path'],
                'source_doc_id': doc['id'],
                'source_type': 'original',
                'content_hash': doc['hash'],
                'compiled_at': datetime.now().isoformat(),
                'version': 1,
                'status': 'draft',
            }

            # 查找该文档关联的实体
            with sqlite3.connect(str(self.reg.db_path)) as db:
                db.row_factory = sqlite3.Row
                entities = db.execute(
                    "SELECT canonical_name, entity_type FROM entities WHERE source_doc_id=? AND review_status != 'deprecated'",
                    (doc['id'],)).fetchall()
                fm['entities'] = [e['canonical_name'] for e in entities]

            # 生成页面
            page = self._render_wiki_page(fm, doc, sections, locked)
            safe_name = re.sub(r'[\\/*?:"<>|]', '_', doc['filename'])
            output_path = WIKI_OUTPUT / safe_name
            output_path.write_text(page, encoding='utf-8')
            generated += 1

        print(f"生成 wiki 页面: {generated} 篇")
        self.stats['pages_generated'] = generated

    def _classify_document(self, doc):
        """文档→实体类型分类"""
        text = doc['content'][:1000]
        signals = {
            'regulation': ['法规', '条例', '办法', '规定', '通知', '令第', '号令'],
            'project': ['项目', '工程', '建设', '施工', '招标', '竣工'],
            'audit_finding': ['审计发现', '问题', '违规', '整改', '检查'],
        }
        scores = {}
        for etype, keywords in signals.items():
            scores[etype] = sum(1 for kw in keywords if kw in text)
        if not scores:
            return 'organization'
        return max(scores, key=scores.get)

    def _render_wiki_page(self, fm, doc, sections, locked):
        """渲染 wiki markdown 页面"""
        lines = ['---']
        for k, v in fm.items():
            if isinstance(v, list):
                lines.append(f"{k}: [{', '.join(v)}]")
            elif isinstance(v, str):
                lines.append(f'{k}: "{v}"')
            else:
                lines.append(f'{k}: {v}')
        lines.append('---\n')

        lines.append(f'# {fm["title"]}\n')
        lines.append(f'<!-- AUTO:start -->')

        for section in sections:
            locked_tag = ' 🔒' if section in locked else ''
            lines.append(f'## {section}{locked_tag}\n')
            if section in locked:
                lines.append('> ⚠️ 此字段为锁定字段，自动编译不会覆盖。\n')

        # 实体链接
        if fm.get('entities'):
            lines.append('## 🔗 关联实体\n')
            for ent in fm['entities'][:20]:
                lines.append(f'- [[{ent}]]')

        # 溯源块
        lines.append('\n## 📎 来源证据\n')
        lines.append(f'- 源文档: {fm["source"]}')
        lines.append(f'- 文档ID: `{fm["source_doc_id"]}`')
        lines.append(f'- 内容哈希: `{fm["content_hash"]}`')
        lines.append(f'- 编译时间: {fm["compiled_at"]}')
        lines.append(f'- 来源类型: `{fm["source_type"]}`')

        lines.append('\n<!-- AUTO:end -->')
        lines.append('<!-- HUMAN:start -->')
        lines.append('<!-- 在此区域手动编辑，不会被自动编译覆盖 -->')
        lines.append('<!-- HUMAN:end -->')

        return '\n'.join(lines)

    # ========== 主流程 ==========

    def compile(self, incremental=False):
        """主编译流程"""
        print(f"\n{'='*60}")
        print(f"wiki_compile 运行 ID: {self.run_id}")
        print(f"L2={self.use_l2} L3={self.use_l3} incremental={incremental}")
        print(f"{'='*60}\n")

        t0 = datetime.now()

        # Step 1: 收集文档
        documents = self.collect_documents()
        if not documents:
            print("无文档可处理")
            return

        # Step 2: 实体抽取
        entities = self.extract_entities(documents)

        # Step 3: 注册表入库
        self.register_entities(entities)

        # Step 4: 构建语义索引
        self.build_similarity_index(documents)

        # Step 5: 双链候选 (采样展示)
        sample_doc = documents[0]
        similar = self.find_similar_docs(sample_doc['id'], top_k=5)
        print(f"示例双链 (文档 {sample_doc['filename']}): {len(similar)} 个候选")
        for sid, score in similar[:3]:
            doc = self._docs.get(sid, {})
            print(f"  → {doc.get('filename', sid)} (相似度={score:.3f})")

        # Step 6: 生成 wiki 页面
        self.generate_wiki_pages(documents)

        # Step 7: Lint
        issues = self.run_lint(documents)
        if issues:
            p1_count = sum(1 for i in issues if i['severity'] == 'P1')
            p2_count = len(issues) - p1_count
            print(f"  🚨 P1={p1_count} ⚠️ P2={p2_count}")

        # Step 8: 保存运行日志
        elapsed = (datetime.now() - t0).total_seconds()
        self._save_run_log(elapsed)

        print(f"\n✅ 编译完成 ({elapsed:.1f}s)")
        stats = self.reg.stats()
        print(f"  注册表: {stats['total_entities']} 实体, {stats['total_relations']} 关系")
        print(f"  待审核: {stats['pending_review']} 条")
        print(f"  降级任务: {stats['degraded_tasks']} 条")

    def _save_run_log(self, elapsed):
        with sqlite3.connect(str(self.reg.db_path)) as db:
            db.execute("""
                INSERT INTO compile_runs (id, started_at, finished_at, docs_processed,
                    entities_extracted, relations_created, l2_calls, l3_calls, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (self.run_id, datetime.now().isoformat(), datetime.now().isoformat(),
                  self.stats.get('docs', 0), self.stats.get('entities_extracted', 0),
                  self.stats.get('relations', 0), self.stats.get('l2_calls', 0),
                  self.stats.get('l3_calls', 0), 'completed'))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--init', action='store_true', help='初始化注册表')
    p.add_argument('--compile', action='store_true', help='全库编译')
    p.add_argument('--l2', action='store_true', help='启用 L2 (v4-flash)')
    p.add_argument('--l3', action='store_true', help='启用 L3 (v4-pro)')
    p.add_argument('--incremental', action='store_true', help='增量更新')
    p.add_argument('--stats', action='store_true', help='统计信息')
    args = p.parse_args()

    if args.init:
        reg = EntityRegistry()
        reg.stats()  # 触发初始化
        print("✅ 实体注册表初始化完成:", reg.db_path)
        print("✅ 本体配置:", CONFIG_DIR / "ontology.yaml")
        return

    if args.stats:
        reg = EntityRegistry()
        s = reg.stats()
        print(json.dumps(s, ensure_ascii=False, indent=2))
        return

    if args.compile or args.l2 or args.l3 or args.incremental:
        compiler = WikiCompiler(use_l2=args.l2, use_l3=args.l3)
        compiler.compile(incremental=args.incremental)

        # 串行调用 L2
        if args.l2:
            print(f"\n{'='*60}")
            print("→ 启动 L2 管线...")
            from wiki_l2 import run_l2_all
            run_l2_all()

        # 串行调用 L3
        if args.l3:
            print(f"\n{'='*60}")
            print("→ 启动 L3 管线...")
            from wiki_l3 import run_l3_all
            run_l3_all()
    else:
        p.print_help()


if __name__ == '__main__':
    main()
