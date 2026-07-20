#!/usr/bin/env python3
"""
wiki_graph.py — 知识图谱可视化
从 entity_registry.sqlite 读取实体和关系，生成交互式 HTML 图谱

用法:
  python -X utf8 scripts/wiki_graph.py                    # 生成全量图谱
  python -X utf8 scripts/wiki_graph.py --limit 200        # 限制节点数
  python -X utf8 scripts/wiki_graph.py --ego "实体名"     # 自我中心子图
  python -X utf8 scripts/wiki_graph.py --export-graphml   # 导出 GraphML
"""
import json, sys, sqlite3
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE = Path(__file__).parent.parent
CONFIG_DIR = WORKSPACE / "config"
DB_PATH = CONFIG_DIR / "entity_registry.sqlite"
OUTPUT_DIR = WORKSPACE / "output"

# 实体类型配色
TYPE_COLORS = {
    'regulation': '#1A5C6E',      # 青绿 - 法规
    'project': '#0A1F3F',         # 深蓝 - 项目
    'organization': '#C5955C',    # 铜金 - 机构
    'fund': '#E74C3C',            # 红 - 资金
    'indicator': '#3498DB',       # 蓝 - 指标
    'audit_finding': '#E67E22',   # 橙 - 审计问题
    'audit_procedure': '#2ECC71', # 绿 - 审计程序
    'rectification': '#9B59B6',   # 紫 - 整改
    'person': '#95A5A6',          # 灰 - 人员
}

TYPE_LABELS = {
    'regulation': '法规制度',
    'project': '项目工程',
    'organization': '单位机构',
    'fund': '资金经费',
    'indicator': '绩效指标',
    'audit_finding': '审计问题',
    'audit_procedure': '审计程序',
    'rectification': '整改措施',
    'person': '人员角色',
}

RELATION_COLORS = {
    'supersedes': '#E74C3C',
    'violates': '#E74C3C',
    'regulates': '#3498DB',
    'references': '#3498DB',
    'uses': '#27AE60',
    'belongs_to': '#95A5A6',
    'involves': '#F39C12',
    'rectifies': '#9B59B6',
    'measured_by': '#1ABC9C',
    'related_to': '#BDC3C7',
}


class WikiGraph:
    """知识图谱生成器"""

    def __init__(self):
        if not DB_PATH.exists():
            raise FileNotFoundError(f"注册表不存在: {DB_PATH}")

    def load_data(self, limit=None, ego_entity=None):
        """加载实体和关系"""
        with sqlite3.connect(str(DB_PATH)) as db:
            db.row_factory = sqlite3.Row

            # 关系
            rel_sql = """
                SELECT r.*, s.canonical_name as subject_name, s.entity_type as subject_type,
                       o.canonical_name as object_name, o.entity_type as object_type
                FROM relations r
                JOIN entities s ON r.subject_id = s.id
                JOIN entities o ON r.object_id = o.id
                WHERE r.relation_status NOT IN ('rejected', 'deprecated')
            """
            if ego_entity:
                entity = db.execute(
                    "SELECT id FROM entities WHERE canonical_name LIKE ?",
                    (f'%{ego_entity}%',)).fetchone()
                if entity:
                    eid = entity['id']
                    rel_sql += f" AND (r.subject_id='{eid}' OR r.object_id='{eid}')"

            relations = [dict(r) for r in db.execute(rel_sql).fetchall()]

            # 收集涉及的实体
            entity_ids = set()
            for r in relations:
                entity_ids.add(r['subject_id'])
                entity_ids.add(r['object_id'])

            if limit:
                entity_ids = set(list(entity_ids)[:limit])

            # 实体详情
            if entity_ids:
                placeholders = ','.join(f"'{eid}'" for eid in entity_ids)
                entities = [dict(e) for e in db.execute(
                    f"SELECT * FROM entities WHERE id IN ({placeholders}) AND review_status != 'deprecated'"
                ).fetchall()]
            else:
                entities = []

        return entities, relations

    def generate_html(self, entities, relations, output_path=None):
        """生成 PyVis 交互式 HTML 图谱"""
        try:
            from pyvis.network import Network
        except ImportError:
            print("⚠ pyvis 未安装 (pip install pyvis)")
            return self._generate_fallback_html(entities, relations, output_path)

        net = Network(height='800px', width='100%', bgcolor='#F5F2EC', font_color='#0A1F3F')
        net.set_options("""
        {
          "physics": {
            "barnesHut": { "gravitationalConstant": -2000, "centralGravity": 0.3, "springLength": 150 },
            "minVelocity": 0.75
          },
          "interaction": { "hover": true, "tooltipDelay": 200 }
        }
        """)

        # 节点
        for e in entities:
            etype = e.get('entity_type', 'unknown')
            color = TYPE_COLORS.get(etype, '#95A5A6')
            label = e.get('canonical_name', e['id'][:8])
            title = f"{TYPE_LABELS.get(etype, etype)}: {label}"
            net.add_node(e['id'], label=label[:20], title=title, color=color, size=15)

        # 边
        for r in relations:
            edge_color = RELATION_COLORS.get(r['predicate'], '#BDC3C7')
            status = r.get('relation_status', 'candidate')
            if status == 'candidate':
                edge_color = f'{edge_color}88'  # 候选边半透明

            net.add_edge(
                r['subject_id'], r['object_id'],
                title=f"{r['predicate']} ({status})",
                color=edge_color,
                arrows='to' if r.get('predicate') not in ('related_to',) else '',
                width=2 if status in ('confirmed', 'human_verified') else 1,
            )

        # 图例
        legend_html = '<div style="position:absolute;top:10px;right:10px;background:white;padding:10px;border-radius:5px;font-size:12px">'
        legend_html += '<b>实体</b><br>'
        for etype, color in TYPE_COLORS.items():
            legend_html += f'<span style="color:{color}">●</span> {TYPE_LABELS.get(etype, etype)}<br>'
        legend_html += '<br><b>关系</b><br>'
        for pred, color in RELATION_COLORS.items():
            legend_html += f'<span style="color:{color}">━</span> {pred}<br>'
        legend_html += '</div>'

        if output_path is None:
            output_path = OUTPUT_DIR / f"wiki_graph_{datetime.now().strftime('%Y%m%d')}.html"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        net.save_graph(str(output_path))

        # 注入图例
        html = output_path.read_text(encoding='utf-8')
        html = html.replace('<body>', f'<body>\n{legend_html}')
        output_path.write_text(html, encoding='utf-8')

        print(f"✅ 图谱已生成: {output_path}")
        print(f"   节点: {len(entities)}, 边: {len(relations)}")

    def _generate_fallback_html(self, entities, relations, output_path=None):
        """无 PyVis 时的纯 HTML + D3.js 回退"""
        nodes_json = []
        for e in entities:
            etype = e.get('entity_type', 'unknown')
            nodes_json.append({
                'id': e['id'],
                'label': e.get('canonical_name', e['id'][:8])[:25],
                'type': etype,
                'color': TYPE_COLORS.get(etype, '#95A5A6'),
                'size': 8,
            })

        edges_json = []
        for r in relations:
            edges_json.append({
                'source': r['subject_id'],
                'target': r['object_id'],
                'label': r['predicate'],
                'status': r.get('relation_status', 'candidate'),
            })

        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>融策审计知识图谱</title>
<style>
body {{ margin:0; background:#F5F2EC; font-family:'Microsoft YaHei',sans-serif; }}
#graph {{ width:100vw; height:100vh; }}
.legend {{ position:absolute; top:10px; right:10px; background:white; padding:10px;
           border-radius:6px; font-size:12px; box-shadow:0 2px 8px rgba(0,0,0,0.1); }}
.info {{ position:absolute; bottom:10px; left:10px; background:white; padding:8px 12px;
        border-radius:6px; font-size:12px; }}
</style></head><body>
<div class="legend"><b>实体类型</b><br>
{''.join(f'<span style="color:{c}">●</span> {TYPE_LABELS.get(t,t)}<br>' for t,c in TYPE_COLORS.items())}
</div>
<div class="info">节点: {len(entities)} | 边: {len(relations)} | 融策右护卫·知识图谱</div>
<div id="graph"></div>
<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
const data = {{
  nodes: {json.dumps(nodes_json, ensure_ascii=False)},
  links: {json.dumps(edges_json, ensure_ascii=False)}
}};
const W=window.innerWidth, H=window.innerHeight;
const svg=d3.select('#graph').append('svg').attr('width',W).attr('height',H);
const sim=d3.forceSimulation(data.nodes)
  .force('link',d3.forceLink(data.links).id(d=>d.id).distance(100))
  .force('charge',d3.forceManyBody().strength(-300))
  .force('center',d3.forceCenter(W/2,H/2));
const link=svg.append('g').selectAll('line').data(data.links).join('line')
  .attr('stroke',d=>d.status==='candidate'?'#ccc':'#666')
  .attr('stroke-width',d=>d.status==='candidate'?1:2);
const node=svg.append('g').selectAll('circle').data(data.nodes).join('circle')
  .attr('r',d=>d.size).attr('fill',d=>d.color)
  .call(d3.drag().on('start',(e,d)=>{{if(!e.active)sim.alphaTarget(0.3).restart();d.fx=d.x;d.fy=d.y;}})
    .on('drag',(e,d)=>{{d.fx=e.x;d.fy=e.y;}}).on('end',(e,d)=>{{if(!e.active)sim.alphaTarget(0);d.fx=null;d.fy=null;}}));
const label=svg.append('g').selectAll('text').data(data.nodes).join('text')
  .text(d=>d.label).attr('font-size',10).attr('dx',12).attr('dy',4);
sim.on('tick',()=>{{
  link.attr('x1',d=>d.source.x).attr('y1',d=>d.source.y).attr('x2',d=>d.target.x).attr('y2',d=>d.target.y);
  node.attr('cx',d=>d.x).attr('cy',d=>d.y);
  label.attr('x',d=>d.x).attr('y',d=>d.y);
}});
</script></body></html>"""
        if output_path is None:
            output_path = OUTPUT_DIR / f"wiki_graph_{datetime.now().strftime('%Y%m%d')}.html"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding='utf-8')
        print(f"✅ 图谱已生成 (D3.js 回退模式): {output_path}")
        print(f"   节点: {len(entities)}, 边: {len(relations)}")

    def centrality_analysis(self, entities, relations):
        """中心性分析：找出核心实体"""
        import networkx as nx
        G = nx.DiGraph()
        for e in entities:
            G.add_node(e['id'], label=e.get('canonical_name', ''), type=e.get('entity_type', ''))
        for r in relations:
            G.add_edge(r['subject_id'], r['object_id'], predicate=r['predicate'])

        if len(G) == 0:
            return []

        # PageRank
        pr = nx.pagerank(G, alpha=0.85)
        top = sorted(pr.items(), key=lambda x: x[1], reverse=True)[:20]

        results = []
        for nid, score in top:
            node_data = G.nodes[nid]
            results.append({
                'id': nid[:12],
                'label': node_data.get('label', '?'),
                'type': node_data.get('type', '?'),
                'pagerank': round(score, 4),
                'degree': G.degree(nid),
            })

        print("\n## 📊 中心性分析 (Top 20)")
        for i, r in enumerate(results[:10], 1):
            print(f"  {i}. {r['label']} [{r['type']}] PR={r['pagerank']:.4f} deg={r['degree']}")

        return results

    def export_graphml(self, entities, relations, output_path=None):
        """导出 GraphML 格式"""
        import networkx as nx
        G = nx.DiGraph()
        for e in entities:
            G.add_node(e['id'], label=e.get('canonical_name', ''), type=e.get('entity_type', ''))
        for r in relations:
            G.add_edge(r['subject_id'], r['object_id'],
                       predicate=r['predicate'], status=r.get('relation_status', ''))

        if output_path is None:
            output_path = OUTPUT_DIR / f"wiki_graph_{datetime.now().strftime('%Y%m%d')}.graphml"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        nx.write_graphml(G, str(output_path))
        print(f"✅ GraphML 导出: {output_path}")


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--limit', type=int, default=500, help='限制节点数')
    p.add_argument('--ego', type=str, help='自我中心子图 (实体名)')
    p.add_argument('--export-graphml', action='store_true', help='导出 GraphML')
    p.add_argument('--centrality', action='store_true', help='中心性分析')
    args = p.parse_args()

    try:
        graph = WikiGraph()
        entities, relations = graph.load_data(limit=args.limit, ego_entity=args.ego)

        if not entities:
            print("⚠ 注册表为空，请先运行 wiki_compile.py --init && wiki_compile.py --compile")
            return

        graph.generate_html(entities, relations)

        if args.centrality:
            graph.centrality_analysis(entities, relations)

        if args.export_graphml:
            graph.export_graphml(entities, relations)

    except FileNotFoundError as e:
        print(f"❌ {e}")
        print("请先: python -X utf8 scripts/wiki_compile.py --init")


if __name__ == '__main__':
    main()
