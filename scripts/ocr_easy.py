"""Try adaptive threshold + easyocr on scoring page"""
import cv2
import numpy as np
from PIL import Image

img_dir = r'D:\openclaw-workspace\output\急救实训室_extracted\归档图片_hires'

# Load page 106 (scoring summary)
img = Image.open(f'{img_dir}\\page_106_enhanced.png')
img_cv = np.array(img)

# Convert to grayscale if needed
if len(img_cv.shape) == 3:
    img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)

# Adaptive threshold binarization
binarized = cv2.adaptiveThreshold(
    img_cv, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY, 31, 10
)

# Save for inspection
out_path = f'{img_dir}\\page_106_binary.png'
cv2.imwrite(out_path, binarized)
print(f'Saved binary: {out_path}')

# Try easyocr on the binarized image
try:
    import easyocr
    reader = easyocr.Reader(['ch_sim'], gpu=False)
    results = reader.readtext(binarized, detail=0)
    print('\n--- EasyOCR results ---')
    for r in results:
        print(r)
except Exception as e:
    print(f'EasyOCR error: {e}')

# Also do the same for page 104 (price scores)
img2 = Image.open(f'{img_dir}\\page_104_enhanced.png')
img_cv2 = np.array(img2)
if len(img_cv2.shape) == 3:
    img_cv2 = cv2.cvtColor(img_cv2, cv2.COLOR_RGB2GRAY)
binarized2 = cv2.adaptiveThreshold(
    img_cv2, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY, 31, 10
)
cv2.imwrite(f'{img_dir}\\page_104_binary.png', binarized2)

print('\n--- Page 104 EasyOCR ---')
try:
    results2 = reader.readtext(binarized2, detail=0)
    for r in results2:
        print(r)
except Exception as e:
    print(f'EasyOCR error: {e}')
