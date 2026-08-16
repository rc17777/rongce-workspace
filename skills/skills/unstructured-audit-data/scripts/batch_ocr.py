#!/usr/bin/env python3
"""批量OCR: PaddleOCR(推荐)/pytesseract 图片→文本转存"""
import sys, io, os, argparse
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SUPPORTED_EXTS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp'}


def ocr_with_paddle(image_dir: str, output_dir: str, lang: str = 'ch') -> int:
    """PaddleOCR批量识别 (精度更高,支持GPU)"""
    try:
        from paddleocr import PaddleOCR
    except ImportError:
        print("PaddleOCR未安装。安装命令:")
        print("  pip install paddleocr paddlepaddle")
        print("回落至pytesseract...")
        return ocr_with_tesseract(image_dir, output_dir, lang)

    ocr = PaddleOCR(lang=lang, show_log=False)
    img_dir = Path(image_dir)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    image_files = [f for f in img_dir.glob('*') if f.suffix.lower() in SUPPORTED_EXTS]
    count = 0

    for f in image_files:
        print(f"[{count+1}/{len(image_files)}] {f.name}")
        try:
            result = ocr.ocr(str(f))
            lines = []
            if result and result[0]:
                for line in result[0]:
                    if line[1] and line[1][0]:
                        lines.append(line[1][0])

            text = '\n'.join(lines)
            out_path = out_dir / f'{f.stem}.txt'
            with open(out_path, 'w', encoding='utf-8') as fout:
                fout.write(text)
            count += 1
        except Exception as e:
            print(f"  错误: {e}")

    return count


def ocr_with_tesseract(image_dir: str, output_dir: str, lang: str = 'chi_sim') -> int:
    """pytesseract批量识别 (轻量备选)"""
    import pytesseract
    from PIL import Image

    img_dir = Path(image_dir)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    image_files = [f for f in img_dir.glob('*') if f.suffix.lower() in SUPPORTED_EXTS]
    count = 0

    for f in image_files:
        print(f"[{count+1}/{len(image_files)}] {f.name}")
        try:
            img = Image.open(str(f))
            text = pytesseract.image_to_string(img, lang=lang)
            out_path = out_dir / f'{f.stem}.txt'
            with open(out_path, 'w', encoding='utf-8') as fout:
                fout.write(text.strip())
            count += 1
        except Exception as e:
            print(f"  错误: {e}")

    return count


def batch_ocr(image_dir: str, output_dir: str, engine: str = 'paddle',
              lang: str = 'ch') -> int:
    """批量OCR入口"""
    img_dir = Path(image_dir)
    if not img_dir.exists():
        print(f"错误: 目录不存在 {image_dir}")
        return 0

    image_files = [f for f in img_dir.glob('*') if f.suffix.lower() in SUPPORTED_EXTS]
    print(f"找到 {len(image_files)} 个图片文件")

    if engine == 'paddle':
        count = ocr_with_paddle(image_dir, output_dir, lang)
    else:
        count = ocr_with_tesseract(image_dir, output_dir,
                                   'chi_sim' if lang == 'ch' else lang)

    print(f"\n完成: {count}/{len(image_files)} 个文件OCR成功")
    print(f"输出: {output_dir}")
    return count


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='批量OCR图文识别')
    parser.add_argument('image_dir', help='图片/PDF截图目录')
    parser.add_argument('output_dir', help='文本输出目录')
    parser.add_argument('--engine', default='paddle', choices=['paddle', 'tesseract'],
                        help='OCR引擎: paddle(推荐) 或 tesseract(备选)')
    parser.add_argument('--lang', default='ch', help='语言: ch(中文) 或 eng')
    args = parser.parse_args()

    batch_ocr(args.image_dir, args.output_dir, args.engine, args.lang)
