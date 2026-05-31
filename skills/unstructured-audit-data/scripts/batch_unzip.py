#!/usr/bin/env python3
"""压缩文件批处理: 批量解压投标项目压缩包→定位关键文件→输出报告"""
import sys, io, os, zipfile, argparse, json
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

KEY_PATTERNS = {
    '招标公告': ['招标公告', '招标文件', '采购公告', '磋商公告', 'bidding', 'tender'],
    '投标须知': ['投标须知', '投标人须知', '供应商须知', 'instructions'],
    '技术方案': ['设计方案', '施工组织', '技术方案', '监理大纲', 'technical', 'design'],
    '工程量清单': ['工程量清单', '报价清单', '价格清单', '分项报价', 'boq', 'pricing'],
    '合同条款': ['合同', 'contract', 'agreement'],
    '资格文件': ['资格', '资质', 'qualification', '营业执照'],
}


def batch_unzip(zip_dir: str, output_dir: str = None):
    """批量解压并定位关键文件"""
    zip_dir = Path(zip_dir)
    if not zip_dir.exists():
        print(f"错误: 目录不存在 {zip_dir}")
        return

    results = []
    zip_files = list(zip_dir.glob('*.zip')) + list(zip_dir.glob('*.rar'))

    if not zip_files:
        print(f"未找到压缩文件(仅支持.zip)")
        # Try subdirectories
        zip_files = list(zip_dir.glob('*/*.zip'))

    print(f"找到 {len(zip_files)} 个压缩文件")

    for zf in zip_files:
        project_name = zf.stem
        print(f"\n处理: {zf.name}")

        try:
            with zipfile.ZipFile(zf) as z:
                all_files = z.namelist()
                key_files = {}

                for category, patterns in KEY_PATTERNS.items():
                    matched = [f for f in all_files
                               if any(p.lower() in f.lower() for p in patterns)]
                    if matched:
                        key_files[category] = matched[:5]  # 最多5个

                # Extract matched files
                if output_dir:
                    out_proj = Path(output_dir) / project_name
                    out_proj.mkdir(parents=True, exist_ok=True)
                    for cat, files in key_files.items():
                        for f in files:
                            try:
                                z.extract(f, out_proj)
                            except:
                                pass

                results.append({
                    'project': project_name,
                    'total_files': len(all_files),
                    'key_files_found': {k: len(v) for k, v in key_files.items()},
                    'matched_files': key_files
                })

                for cat, files in key_files.items():
                    print(f"  [{cat}] 找到 {len(files)} 个: {files[0][:80]}...")

        except Exception as e:
            print(f"  错误: {e}")

    # Summary
    print(f"\n{'='*60}")
    print(f"处理完成: {len(results)}/{len(zip_files)} 个项目成功")
    total_key = sum(
        sum(v.get('key_files_found', {}).values()) for v in results)
    print(f"提取关键文件: {total_key} 个")

    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='批量解压招投标项目压缩包')
    parser.add_argument('zip_dir', help='压缩包目录')
    parser.add_argument('output_dir', nargs='?', help='输出目录(可选,不指定则仅定位不解压)')
    args = parser.parse_args()

    batch_unzip(args.zip_dir, args.output_dir)
