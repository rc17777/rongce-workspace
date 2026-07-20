"""OCR key scoring pages from archive PDF"""
import pytesseract
from PIL import Image

img_dir = r'D:\openclaw-workspace\output\急救实训室_extracted\归档图片_hires'

# Page 106 - Scoring Summary Table
print('='*60)
print('PAGE 106 - 评分汇总表 (cropped middle)')
print('='*60)
img = Image.open(f'{img_dir}\\page_106_enhanced.png')
w, h = img.size
crop = img.crop((int(w*0.05), int(h*0.15), int(w*0.95), int(h*0.85)))
text = pytesseract.image_to_string(crop, lang='chi_sim', config='--psm 6')
for line in text.split('\n'):
    line = line.strip()
    if line and len(line) > 3:
        print(line)
print(f'\n[Total chars: {len(text)}]')

# Page 89 - Detailed individual scoring
print('\n' + '='*60)
print('PAGE 89 - 符合审查表(个人) - cropped')
print('='*60)
img2 = Image.open(f'{img_dir}\\page_089_enhanced.png')
w2, h2 = img2.size
crop2 = img2.crop((int(w2*0.05), int(h2*0.12), int(w2*0.95), int(h2*0.88)))
text2 = pytesseract.image_to_string(crop2, lang='chi_sim', config='--psm 6')
for line in text2.split('\n'):
    line = line.strip()
    if line and len(line) > 3:
        print(line)
print(f'\n[Total chars: {len(text2)}]')

# Page 104 and 107 - might have score data
for pg in [104, 105, 107]:
    try:
        img = Image.open(f'{img_dir}\\page_{pg:03d}_enhanced.png')
        w, h = img.size
        crop = img.crop((int(w*0.05), int(h*0.12), int(w*0.95), int(h*0.88)))
        text = pytesseract.image_to_string(crop, lang='chi_sim', config='--psm 6')
        if any(kw in text for kw in ['分','得分','价格','技术','演示','服务','业绩','环境']):
            print(f'\n=== PAGE {pg} ===')
            for line in text.split('\n'):
                line = line.strip()
                if line and len(line) > 3:
                    print(line)
            print(f'[Total chars: {len(text)}]')
    except:
        pass

print('\nDone')
