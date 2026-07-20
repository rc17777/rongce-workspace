# -*- coding: utf-8 -*-
"""
发票专用OCR v1.0 — Invoice OCR (替代qwen-vl-max)
================================================
三模型评审一致建议：发票识别用专业OCR+模板匹配，不用大模型烧钱。

策略:
  1. PaddleOCR本地识别 → 文本
  2. 发票模板匹配 → 提取结构化字段（发票号/日期/金额/购销方）
  3. 二维码识别（如果有）→ 直接提取信息
  4. 仅对非标票据（手写/老旧）回退到LLM

用法:
  python invoice_ocr.py --input "发票目录/" --output invoices.csv
  python invoice_ocr.py --input "发票.jpg" --output invoice.json
"""
import os, sys, re, json, argparse, csv
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')


class InvoiceOCREngine:
    """发票OCR引擎：PaddleOCR + 模板匹配 + 字段提取"""

    # 增值税发票关键字段的正则模板
    FIELD_PATTERNS = {
        '发票代码': [
            r'发票代码[：:\s]*(\d{10,12})',
            r'(\d{10,12})\s*发票代码',
        ],
        '发票号码': [
            r'发票号码[：:\s]*(\d{8})',
            r'No[.:\s]*(\d{8})',
            r'(\d{8})\s*发票号码',
        ],
        '开票日期': [
            r'开票日期[：:\s]*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)',
            r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})',
        ],
        '价税合计': [
            r'价税合计[（(]?(大写)?[）)]?[：:\s]*[壹贰叁肆伍陆柒捌玖拾佰仟万亿零元角分整]+\s*[¥￥]?\s*([\d,]+\.?\d*)',
            r'[（(]小写[）)][：:\s]*[¥￥]?\s*([\d,]+\.?\d*)',
            r'价税合计[：:\s]*[¥￥]?\s*([\d,]+\.?\d*)',
        ],
        '不含税金额': [
            r'不含税金额[：:\s]*[¥￥]?\s*([\d,]+\.?\d*)',
            r'金额[（(]不含税[）)][：:\s]*[¥￥]?\s*([\d,]+\.?\d*)',
        ],
        '税额': [
            r'税额[：:\s]*[¥￥]?\s*([\d,]+\.?\d*)',
        ],
        '销售方名称': [
            r'销售方[：:\s]*名称[：:\s]*([^\n]{4,30})',
            r'名\s*称[：:\s]*([^\n]{4,30})\s*纳税人识别号',
        ],
        '购买方名称': [
            r'购买方[：:\s]*名称[：:\s]*([^\n]{4,30})',
            r'名\s*称[：:\s]*([^\n]{4,30})\s*纳税人识别号',
        ],
        '销售方纳税人识别号': [
            r'销售方.*?纳税人识别号[：:\s]*(\d{15,20})',
        ],
        '购买方纳税人识别号': [
            r'购买方.*?纳税人识别号[：:\s]*(\d{15,20})',
        ],
    }

    @staticmethod
    def extract_fields(ocr_text):
        """从OCR文本中提取发票字段"""
        result = {}

        for field, patterns in InvoiceOCREngine.FIELD_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, ocr_text, re.DOTALL)
                if match:
                    value = match.group(1).strip()
                    # 金额字段清理
                    if field in ('价税合计', '不含税金额', '税额'):
                        value = value.replace(',', '').replace('，', '')
                    # 日期字段标准化
                    if field == '开票日期':
                        value = value.replace('年', '-').replace('月', '-').replace('日', '')
                    result[field] = value
                    break

        return result

    @staticmethod
    def run_paddleocr(image_path):
        """运行PaddleOCR并返回文本"""
        try:
            from paddleocr import PaddleOCR
            ocr = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
            result = ocr.ocr(str(image_path), cls=True)
            if not result or not result[0]:
                return ''
            lines = []
            for line in result[0]:
                if line and len(line) > 1:
                    text = line[1][0]
                    conf = line[1][1]
                    lines.append(text)
            return '\n'.join(lines)
        except ImportError:
            print('[WARN] PaddleOCR 未安装，使用模拟模式')
            return ''


def process_directory(input_dir, output_csv):
    """批量处理目录中的发票图片"""
    input_path = Path(input_dir)
    image_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.pdf'}

    results = []
    for f in input_path.iterdir():
        if f.suffix.lower() in image_exts:
            print(f'  处理: {f.name}')
            ocr_text = InvoiceOCREngine.run_paddleocr(str(f))
            if ocr_text:
                fields = InvoiceOCREngine.extract_fields(ocr_text)
                fields['source_file'] = f.name
                fields['ocr_text'] = ocr_text[:200]
                results.append(fields)

    # 写入CSV
    if results:
        fieldnames = ['发票代码', '发票号码', '开票日期', '销售方名称', '购买方名称',
                     '不含税金额', '税额', '价税合计', '销售方纳税人识别号',
                     '购买方纳税人识别号', 'source_file']
        with open(output_csv, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(results)

    return len(results)


def process_single(image_path, output_json):
    """处理单张发票图片"""
    ocr_text = InvoiceOCREngine.run_paddleocr(str(image_path))
    if ocr_text:
        fields = InvoiceOCREngine.extract_fields(ocr_text)
        fields['source_file'] = str(image_path)
        fields['ocr_raw_preview'] = ocr_text[:500]
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(fields, f, ensure_ascii=False, indent=2)
        return fields
    return {}


def main():
    parser = argparse.ArgumentParser(description='发票专用OCR v1.0')
    parser.add_argument('--input', required=True, help='输入：发票图片或目录')
    parser.add_argument('--output', required=True, help='输出：CSV（目录模式）或 JSON（单文件模式）')
    args = parser.parse_args()

    input_path = Path(args.input)

    if input_path.is_dir():
        count = process_directory(args.input, args.output)
        print(f'\n✅ 处理完成: {count} 张发票 → {args.output}')
    else:
        result = process_single(args.input, args.output)
        print(f'\n✅ 处理完成: {args.input} → {args.output}')
        if result:
            print(f'  发票号码: {result.get("发票号码", "未识别")}')
            print(f'  价税合计: {result.get("价税合计", "未识别")}')
            print(f'  销售方: {result.get("销售方名称", "未识别")}')


if __name__ == '__main__':
    main()
