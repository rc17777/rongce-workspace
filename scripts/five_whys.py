#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
融策·审盾 - 五问为什么根因回溯引擎
=====================================
输入：一个审计发现的描述（JSON或自然语言）
输出：五层追问链 + 证据缺口标记 + 根因定位和建议

用法：
  python five_whys.py --finding "审计发现描述"
  python five_whys.py --file findings.json
  python five_whys.py --interactive

依赖：DeepSeek API (环境变量 DEEPSEEK_API_KEY)
"""

import os
import sys
import json
import argparse
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

# DeepSeek API 配置
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-dbc61b4ba6a64222a2621d646f15234c")
API_BASE = "https://api.deepseek.com/v1"
MODEL = "deepseek-chat"

FIVE_WHYS_PROMPT = """你是融策会计师事务所的资深审计师，专长是透过表象挖根因。

请对以下审计发现进行五层追问分析：

【审计发现】
{finding}

【业务背景】
{context}

【要求】
请严格按照以下结构输出分析：

## 第一问：为什么会出现这个发现？
（从事实出发，追问直接触发原因）

## 第二问：导致直接原因的背后是什么？
（追问深层机制层面的原因）

## 第三问：这个深层原因是不是系统性的？
（判断是个案还是普遍问题，给出判断依据）

## 第四问：如果表层问题解决了，类似问题还会发生吗？为什么？
（检验当前应对方案是否触及根因）

## 第五问：最根本的原因是什么？
（四个维度分类：利益格局 / 制度缺陷 / 权力运行 / 外部环境，选一个最接近的）

## 根因定位
（一句话概括真正的病根）

## 制度缺陷分析（如适用）
- 什么制度设计导致/纵容了这个问题？
- 制度与业务之间哪里脱节？
- 违规成本与违规收益的比较

## 利益关联分析（如适用）
- 谁从这个问题中得到了好处？
- 受益人与决策人之间有无关联？
- 是否存在隐形的利益输送链？

## 权力运行分析（如适用）
- 决策权力的实际分布是否与制度规定一致？
- 是否存在权力越位/集权/滥用？
- "集体决策"程序是否真正发挥作用？

## 外部环境分析（如适用）
- 外部环境变化在其中扮演了什么角色？
- 如果外部环境不变，根因能否消除？

## 证据缺口
列出验证这个根因还需要但当前没有的证据：
1. xxx
2. xxx

## 机制性建议（禁止使用"加强管理""提高意识"等无效建议）
1. 【止血措施】xxx（立即能做，不能等）
2. 【治本措施】xxx（针对根因的制度性改革）
3. 【验证方法】xxx（怎么判断问题真正解决了）

## 风险预警
基于这个根因，预判可能存在的其他潜在问题领域。
"""


def call_deepseek(prompt: str, max_tokens: int = 4000) -> str:
    """调用DeepSeek API"""
    import urllib.request
    import urllib.error

    data = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "你是一位资深的政府审计专家，擅长根因分析和制度诊断。"},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.3  # 低温度，保证分析严谨
    }).encode('utf-8')

    req = urllib.request.Request(
        f"{API_BASE}/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            return result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else ''
        raise RuntimeError(f"API调用失败 (HTTP {e.code}): {error_body[:500]}")


def analyze_finding(finding: str, context: str = "政府审计项目，被审计单位为行政事业单位/国有企业") -> str:
    """对单个审计发现进行五问分析"""
    prompt = FIVE_WHYS_PROMPT.format(finding=finding, context=context)
    return call_deepseek(prompt)


def analyze_findings_from_file(filepath: str, context: str = "") -> list:
    """从JSON文件读取多个发现并分析"""
    with open(filepath, 'r', encoding='utf-8') as f:
        findings = json.load(f)

    if isinstance(findings, dict):
        findings = [findings]

    results = []
    for i, finding in enumerate(findings, 1):
        finding_text = finding.get("description", finding.get("finding", json.dumps(finding, ensure_ascii=False)))
        ctx = context or finding.get("context", "政府审计项目")

        print(f"\n{'='*60}")
        print(f"正在分析第 {i}/{len(findings)} 个发现...")
        print(f"发现摘要: {finding_text[:100]}...")
        print(f"{'='*60}")

        try:
            analysis = analyze_finding(finding_text, ctx)
            results.append({
                "finding_id": finding.get("id", f"F-{i:03d}"),
                "finding": finding_text,
                "analysis": analysis,
                "timestamp": datetime.now().isoformat()
            })
            print(f"✅ 第 {i} 个分析完成")
        except Exception as e:
            print(f"❌ 第 {i} 个分析失败: {e}")
            results.append({
                "finding_id": finding.get("id", f"F-{i:03d}"),
                "finding": finding_text,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

    return results


def interactive_mode():
    """交互式分析模式"""
    print("=" * 60)
    print("  融策·审盾 — 五问为什么根因回溯引擎")
    print("=" * 60)
    print("\n请输入审计发现（输入完后按回车，以空行结束）：")
    print()

    lines = []
    while True:
        try:
            line = input()
            if line.strip() == "":
                break
            lines.append(line)
        except EOFError:
            break

    if not lines:
        print("未输入任何内容。")
        return

    finding = "\n".join(lines)

    print("\n请输入业务背景（可选，直接回车使用默认值）：")
    context = input().strip()
    if not context:
        context = "政府审计项目，被审计单位为行政事业单位/国有企业"

    print("\n🔄 正在调用DeepSeek进行五层追问分析...\n")
    try:
        result = analyze_finding(finding, context)
        print(result)
        print("\n" + "=" * 60)
        print("分析完成。")
    except Exception as e:
        print(f"\n❌ 分析失败: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="融策·审盾 五问为什么根因回溯引擎",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python five_whys.py --interactive
  python five_whys.py --finding "发现差旅费超标且审批异常"
  python five_whys.py --file findings.json --output analysis.md
  python five_whys.py --file findings.json --context "某市住建局2025年度预算执行审计"
        """
    )
    parser.add_argument("--interactive", "-i", action="store_true", help="交互式模式")
    parser.add_argument("--finding", "-f", type=str, help="单个审计发现（文本）")
    parser.add_argument("--file", type=str, help="审计发现JSON文件")
    parser.add_argument("--context", "-c", type=str, default="", help="业务背景描述")
    parser.add_argument("--output", "-o", type=str, help="输出文件路径（支持.md/.json）")

    args = parser.parse_args()

    if args.interactive:
        interactive_mode()
        return

    if args.finding:
        print("🔄 正在分析...\n")
        try:
            result = analyze_finding(args.finding, args.context)
            print(result)
        except Exception as e:
            print(f"❌ 分析失败: {e}")
            sys.exit(1)

        if args.output:
            ext = os.path.splitext(args.output)[1]
            if ext == '.json':
                output = [{
                    "finding": args.finding,
                    "context": args.context,
                    "analysis": result,
                    "timestamp": datetime.now().isoformat()
                }]
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(output, f, ensure_ascii=False, indent=2)
            else:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(f"# 五问为什么根因分析\n\n")
                    f.write(f"**审计发现**：{args.finding}\n\n")
                    f.write(f"**业务背景**：{args.context}\n\n")
                    f.write(f"**分析时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
                    f.write("---\n\n")
                    f.write(result)
            print(f"\n✅ 结果已保存至: {args.output}")
        return

    if args.file:
        results = analyze_findings_from_file(args.file, args.context)

        if args.output:
            ext = os.path.splitext(args.output)[1]
            if ext == '.json':
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
            else:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(f"# 批量五问为什么根因分析\n\n")
                    f.write(f"**源文件**：{args.file}\n")
                    f.write(f"**分析时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
                    f.write(f"**分析数量**：{len(results)}\n\n---\n\n")
                    for r in results:
                        f.write(f"## 发现 {r['finding_id']}\n\n")
                        f.write(f"**原始描述**：{r['finding']}\n\n")
                        if 'error' in r:
                            f.write(f"❌ 分析失败：{r['error']}\n\n")
                        else:
                            f.write(r['analysis'])
                            f.write("\n\n---\n\n")
            print(f"\n✅ 结果已保存至: {args.output}")

        # 打印摘要
        success_count = sum(1 for r in results if 'error' not in r)
        print(f"\n📊 分析摘要：{success_count}/{len(results)} 成功")
        for r in results:
            status = "✅" if 'error' not in r else "❌"
            summary = r['finding'][:80] + "..." if len(r['finding']) > 80 else r['finding']
            print(f"  {status} {r['finding_id']}: {summary}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
