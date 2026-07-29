# encoding: utf-8
import sys, time
sys.stdout.reconfigure(encoding='utf-8')
t0 = time.time()
from paddleocr import PaddleOCR
print(f'PADDLE_INIT: {time.time()-t0:.1f}s', flush=True)
