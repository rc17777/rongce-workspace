"""
审计文本润色检查器
扫描审计报告文本，标记：模糊词、过度声明、缺少依据的结论、被动语态隐藏责任主体
用法: py polish_text.py <input.txt> [--output report.txt]
"""
import re
import sys
import argparse

# === 检查规则 ===

FUZZY_WORDS = [
    (r'较大|一定程度|部分|某些|个别|少数|多数|一些|若干', '模糊量词 — 建议用具体数字替换'),
    (r'约\d+多万|大概\d+|大约\d+左右', '模糊数字 — 建议用精确数值'),
    (r'基本合规|基本符合|基本达到|基本实现', '模糊定性 — 建议明确：除XX外均符合规定'),
    (r'据了解|据悉|据了解情况|据反映', '听说式表达 — 建议改为：审计发现/根据XX文件显示'),
    (r'存在较大问题|存在严重问题|问题较为突出|风险较大', '缺乏量化的定性表述 — 建议量化：发现X项问题，涉及金额X万元'),
    (r'应该|可能|也许|或许|大概|估计', '不确定表述 — 审计报告应使用确定性语言'),
]

OVERCLAIMS = [
    (r'完全违规|严重违法|重大犯罪|涉嫌贪污|涉嫌挪用', '⚠️ 过度定性 — 审计无权定性犯罪，建议改为：涉嫌违反XX法第X条，建议移送XX机关'),
    (r'所有|全部|每一个|没有一个', '绝对化表述 — 审计极少能覆盖全部，建议标注抽查范围'),
    (r'证明了|证实了|确认了', '强因果表述 — 建议改为：审计证据表明/审计发现'),
    (r'令人震惊|触目惊心|竟然|居然', '情绪化表达 — 审计报告应保持中性客观'),
]

MISSING_BASIS = [
    (r'不符合规定[^，。]*(?:[，。])', '缺少依据 — "不符合规定"后应注明具体法规+条款'),
    (r'存在风险[^，。]*(?:[，。])', '缺少依据 — "存在风险"后应说明风险类型和依据'),
    (r'违规[^，。]*(?:[，。])', '检查依据 — "违规"后应注明违反的具体法规+条款'),
]

PASSIVE_HIDING = [
    (r'(?:未被|没有被|未得到).*(?:执行|落实|遵守|遵循)', '被动语态隐藏责任主体 — 建议改为主动语态，明确责任人'),
    (r'(?:招标程序|采购流程|审批手续).*(?:未被|未得到)', '被动语态 — 建议明确：XX部门/XX单位未执行XX程序'),
]

WEAK_SUGGESTIONS = [
    (r'建议加强[管理控制监督]', '空泛建议 — 建议具体化：谁做/做什么/何时完成/如何验证'),
    (r'建议引起重视', '空泛建议 — 无执行价值，建议改为具体整改措施'),
    (r'建议进一步[规范完善改进加强提升]', '空泛建议 — 建议明确：规范什么/谁负责/什么时限'),
    (r'建议今后注意', '空泛建议 — 无约束力，建议改为具体的制度修订或流程改进'),
]


def scan_text(text):
    results = []
    lines = text.split('\n')

    all_rules = [
        ('模糊表述', FUZZY_WORDS),
        ('过度声明', OVERCLAIMS),
        ('缺少依据', MISSING_BASIS),
        ('被动语态', PASSIVE_HIDING),
        ('空泛建议', WEAK_SUGGESTIONS),
    ]

    for line_num, line in enumerate(lines, 1):
        if not line.strip():
            continue
        for category, rules in all_rules:
            for pattern, message in rules:
                matches = list(re.finditer(pattern, line))
                for m in matches:
                    results.append({
                        'line': line_num,
                        'category': category,
                        'match': m.group(),
                        'message': message,
                        'context': line.strip()[:120],
                    })

    return results


def format_report(results):
    if not results:
        return '✅ 未发现明显问题。文本通过基础审查。'

    lines = []
    lines.append('=' * 60)
    lines.append('审计报告文本润色检查报告')
    lines.append('=' * 60)
    lines.append(f'共发现 {len(results)} 处需要关注的问题\n')

    # Group by category
    categories = {}
    for r in results:
        cat = r['category']
        categories.setdefault(cat, []).append(r)

    for cat, items in categories.items():
        lines.append(f'\n--- {cat} ({len(items)}处) ---')
        for item in items:
            lines.append(f"\n  第{item['line']}行 | \"{item['match']}\"")
            lines.append(f"  💡 {item['message']}")
            lines.append(f"  📝 上下文: {item['context']}")

    # Summary stats
    lines.append(f'\n{"=" * 60}')
    lines.append('汇总：')
    for cat, items in categories.items():
        lines.append(f'  {cat}: {len(items)}处')
    lines.append(f'  总计: {len(results)}处')

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='审计文本润色检查器')
    parser.add_argument('input', help='输入文本文件路径')
    parser.add_argument('--output', '-o', help='输出报告文件路径（默认打印到终端）')
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        text = f.read()

    results = scan_text(text)
    report = format_report(results)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f'检查报告已保存: {args.output}')
    else:
        print(report)


if __name__ == '__main__':
    main()
