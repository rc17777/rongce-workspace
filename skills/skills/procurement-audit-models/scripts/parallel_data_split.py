"""技能⑤ 多线程智能拆分 — 海量数据并行预处理
来源：重庆审计局"利用多线程技术智能拆分海量审计数据"
用途：大项目投标数据/补贴数据/资产数据的并行分组处理
"""
import sys, os, json
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
sys.stdout.reconfigure(encoding='utf-8')


def smart_split(data, group_field, max_per_group=None, 
                auto_balance=True):
    """智能数据拆分
    
    data: 原始数据列表
    group_field: 拆分字段（如"地区"/"年份"/"金额段"）
    max_per_group: 每组最大记录数（默认自动均衡）
    auto_balance: 自动均衡各批次大小
    
    返回: {"分组1": [records...], "分组2": [...], ...}
    """
    groups = defaultdict(list)
    for record in data:
        key = record.get(group_field, "未分组")
        groups[key].append(record)
    
    # 如果指定了max_per_group，对大组进行再拆分
    if max_per_group:
        final_groups = {}
        task_id = 1
        for key, group_data in groups.items():
            if len(group_data) > max_per_group:
                # 拆分为多个子批
                for i in range(0, len(group_data), max_per_group):
                    final_groups[f"{key}_第{task_id}批"] = \
                        group_data[i:i+max_per_group]
                    task_id += 1
            else:
                final_groups[key] = group_data
        return final_groups
    
    return dict(groups)


def parallel_process(groups, process_func, max_workers=4):
    """多线程并行处理
    
    groups: smart_split的输出 {"分组名": [records]}
    process_func: 处理函数 fn(group_name, records) -> result
    max_workers: 最大线程数
    
    返回: {"分组名": 处理结果, ...}
    """
    results = {}
    total = sum(len(v) for v in groups.values())
    
    print(f"[并行处理] 总记录: {total} | 分组: {len(groups)} | 线程: {max_workers}")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(process_func, name, records): name
            for name, records in groups.items()
        }
        
        done = 0
        for future in as_completed(futures):
            name = futures[future]
            done += 1
            try:
                result = future.result(timeout=300)
                results[name] = result
                print(f"  [{done}/{len(groups)}] {name} ✓ "
                      f"({len(groups[name]) if name in groups else '?'}条)")
            except Exception as e:
                print(f"  [{done}/{len(groups)}] {name} ✗ {e}")
                results[name] = {"error": str(e)}
    
    return results


def batch_sql_generator(data, table_name, batch_size=1000):
    """批量生成INSERT SQL（大表写入优化）
    
    用途：将分析结果批量导入数据库
    """
    if not data:
        return []
    
    # 获取所有字段
    all_fields = set()
    for row in data:
        all_fields.update(row.keys())
    fields = sorted(all_fields)
    
    batches = []
    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        values = []
        for row in batch:
            vals = []
            for f in fields:
                v = row.get(f, "")
                if isinstance(v, str):
                    vals.append(f"'{v.replace(chr(39), chr(39)+chr(39))}'")
                elif v is None:
                    vals.append("NULL")
                else:
                    vals.append(str(v))
            values.append(f"({', '.join(vals)})")
        
        sql = (f"-- 批次 {i//batch_size + 1}, {len(batch)}条\n"
               f"INSERT INTO {table_name} ({', '.join(fields)})\n"
               f"VALUES\n{',\n'.join(values)};")
        batches.append(sql)
    
    return batches


def smart_output_formatter(results, output_format="summary"):
    """智能输出格式（对标重庆审计局"智能判定输出格式"）
    
    output_format:
      - "summary": 仅汇总统计
      - "detail": 全部明细
      - "flagged": 仅异常标记的记录
      - "custom": 自定义过滤
    """
    if output_format == "summary":
        return {
            "总记录数": sum(len(v) if isinstance(v, list) else 1 for v in results.values()),
            "分组数": len(results),
            "分组摘要": {k: (len(v) if isinstance(v, list) else "非列表")
                       for k, v in results.items()}
        }
    elif output_format == "flagged":
        flagged = {}
        for k, v in results.items():
            if isinstance(v, list):
                flagged[k] = [r for r in v if r.get("_标志") or r.get("标志")]
            else:
                flagged[k] = v
        return flagged
    else:
        return results


# ===== 示例 =====
if __name__ == "__main__":
    print("=" * 60)
    print("多线程智能拆分 — 海量数据并行处理")
    print("=" * 60)
    
    # 生成模拟数据（100条记录，模拟大项目）
    import random
    random.seed(42)
    
    data = []
    regions = ["成都", "德阳", "绵阳", "宜宾", "泸州", "南充", "达州", "乐山"]
    for i in range(100):
        data.append({
            "序号": i+1,
            "地区": random.choice(regions),
            "项目编号": f"P{random.randint(1,30):03d}",
            "金额": random.randint(10, 1000),
            "状态": random.choice(["正常","异常","待核实"]),
        })
    
    # 1. 智能拆分
    groups = smart_split(data, "地区", max_per_group=20)
    print(f"\n拆分结果: {len(groups)}个分组")
    for name, records in sorted(groups.items()):
        print(f"  {name}: {len(records)}条")
    
    # 2. 并行处理示例
    def simple_analyzer(name, records):
        """示例分析函数"""
        total = sum(r["金额"] for r in records)
        abnormal = [r for r in records if r["状态"] == "异常"]
        return {
            "总金额": total,
            "均值": total / len(records),
            "异常数": len(abnormal),
            "异常率%": round(len(abnormal)/len(records)*100, 1)
        }
    
    results = parallel_process(groups, simple_analyzer, max_workers=4)
    
    # 3. 智能输出
    print(f"\n--- 智能输出（summary模式）---")
    summary = smart_output_formatter(results, "summary")
    for k, v in summary["分组摘要"].items():
        print(f"  {k}: {v}")
    
    print(f"\n提示: 实际使用时，max_workers可设置为CPU核心数")
    print(f"  当前机器建议: max_workers={os.cpu_count() or 4}")
