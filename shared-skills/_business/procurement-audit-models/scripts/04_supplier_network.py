#!/usr/bin/env python3
"""
模型4: 供应商关联网络挖掘 — 同一控制人多公司围标
来源：群众语言堂公众号《政府采购审计大数据技术超详细操作》
依赖：pip install pandas openpyxl networkx matplotlib
"""
import pandas as pd
import argparse
import sys
import os

def main():
    parser = argparse.ArgumentParser(description='供应商关联网络挖掘')
    parser.add_argument('--input', '-i', required=True, help='供应商股东表.xlsx（需含"供应商"和"股东姓名"列）')
    parser.add_argument('--output', '-o', default='./output/', help='输出目录')
    parser.add_argument('--min-nodes', type=int, default=3, help='最小关联集团节点数（默认3）')
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    try:
        df = pd.read_excel(args.input)
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        sys.exit(1)

    required = ['供应商', '股东姓名']
    for col in required:
        if col not in df.columns:
            print(f"❌ 缺少必要字段: {col}")
            print(f"   现有字段: {list(df.columns)}")
            sys.exit(1)

    # 构建网络
    import networkx as nx
    import matplotlib.pyplot as plt

    G = nx.Graph()
    for _, row in df.iterrows():
        G.add_edge(row['供应商'], row['股东姓名'], relation='股东')

    # 识别连通分量（关联集团）
    components = list(nx.connected_components(G))
    
    # 筛选大分量
    large_components = [comp for comp in components if len(comp) >= args.min_nodes]
    large_components.sort(key=len, reverse=True)

    if len(large_components) == 0:
        print(f"✅ 未发现≥{args.min_nodes}个节点的关联集团")
        pd.DataFrame(columns=['集团编号', '节点数', '供应商', '股东姓名']).to_excel(
            os.path.join(args.output, '疑点_关联集团.xlsx'), index=False)
        return

    # 输出分析结果
    all_records = []
    for idx, comp in enumerate(large_components):
        comp_list = sorted(comp)
        suppliers_in_comp = [n for n in comp_list if n in set(df['供应商'])]
        shareholders_in_comp = [n for n in comp_list if n in set(df['股东姓名'])]
        
        all_records.append({
            '集团编号': idx + 1,
            '节点数': len(comp),
            '供应商数量': len(suppliers_in_comp),
            '股东数量': len(shareholders_in_comp),
            '供应商名单': '、'.join(suppliers_in_comp),
            '股东名单': '、'.join(shareholders_in_comp)
        })

        # 画网络图（每个集团一张）
        plt.figure(figsize=(10, 8))
        subgraph = G.subgraph(comp)
        pos = nx.spring_layout(subgraph, seed=42, k=2)
        
        # 着色：供应商蓝色，股东红色
        node_colors = []
        for n in subgraph.nodes():
            if n in set(df['供应商']):
                node_colors.append('#4A90D9')  # 蓝色=供应商
            else:
                node_colors.append('#E74C3C')  # 红色=股东
        
        nx.draw(subgraph, pos, with_labels=True, node_color=node_colors,
                node_size=2000, font_size=10, font_family='Microsoft YaHei',
                edge_color='gray', width=1.5, alpha=0.8)
        
        plt.title(f"关联集团 #{idx+1} ({len(comp)}个节点)", fontsize=14, fontfamily='Microsoft YaHei')
        plt.tight_layout()
        plt.savefig(os.path.join(args.output, f'network_group_{idx+1}.png'), dpi=150, bbox_inches='tight')
        plt.close()

    # 保存汇总表
    summary_df = pd.DataFrame(all_records)
    summary_df.to_excel(os.path.join(args.output, '疑点_关联集团.xlsx'), index=False)

    # 输出关联明细（供应商之间的连接路径）
    details = []
    for comp in large_components:
        suppliers_in = [n for n in comp if n in set(df['供应商'])]
        if len(suppliers_in) >= 2:
            for i in range(len(suppliers_in)):
                for j in range(i+1, len(suppliers_in)):
                    path = nx.shortest_path(G, suppliers_in[i], suppliers_in[j])
                    details.append({
                        '供应商A': suppliers_in[i],
                        '供应商B': suppliers_in[j],
                        '关联路径': ' → '.join(path)
                    })

    if details:
        detail_df = pd.DataFrame(details)
        detail_df.to_excel(os.path.join(args.output, '疑点_供应商关联路径.xlsx'), index=False)

    print(f"✅ 完成！共发现 {len(large_components)} 个关联集团（≥{args.min_nodes}个节点）")
    print(f"   输出目录: {args.output}")
    print(f"   文件列表:")
    for f in os.listdir(args.output):
        print(f"     📄 {f}")
    print(f"\n   最大关联集团 Top 3:")
    for comp in large_components[:3]:
        suppliers = sorted([n for n in comp if n in set(df['供应商'])])
        shareholders = sorted([n for n in comp if n in set(df['股东姓名'])])
        print(f"   集团({len(comp)}节点): 供应商({len(suppliers)}家) → {'、'.join(suppliers[:5])}")
        if len(suppliers) > 5:
            print(f"      ...还有{len(suppliers)-5}家")
        print(f"     股东({len(shareholders)}人) → {'、'.join(shareholders[:3])}")

if __name__ == '__main__':
    main()
