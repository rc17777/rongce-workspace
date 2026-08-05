# -*- coding: utf-8 -*-
"""生成测试夹具: 电子件PDF / 扫描件PDF / SQL dump / 本地API"""
import sys, os, json
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

OUT = Path(__file__).parent / 'testdata'
OUT.mkdir(exist_ok=True)
import fitz  # pymupdf

# ─── 1. 电子件PDF (文本层+表格) ───
doc = fitz.open()
# 嵌入中文字体, 保证文本层可提取
fontfile = None
for fp in [r'C:\Windows\Fonts\msyh.ttc', r'C:\Windows\Fonts\simhei.ttf', r'C:\Windows\Fonts\simsun.ttc']:
    if os.path.exists(fp):
        fontfile = fp
        break
page = doc.new_page()
if fontfile:
    try:
        page.insert_font(fontname='cjk', fontfile=fontfile)
    except Exception:
        fontfile = None

def t(x, y, s, size=10):
    page.insert_text((x, y), s, fontsize=size, fontname='cjk' if fontfile else 'helv')

t(72, 72, "2025年度运行经费明细表", 16)
t(72, 100, "编制单位: 某某单位    期间: 2025-01-01 至 2025-12-31", 10)
# 画表格线, 让 pdfplumber 能定位表格
col_edges = [72, 160, 260, 360, 470, 545]
rows_y = [130, 148, 166, 184, 202, 220]
for x0 in col_edges:
    page.draw_line((x0, rows_y[0]), (x0, rows_y[-1]))
for yy in rows_y:
    page.draw_line((col_edges[0], yy), (col_edges[-1], yy))

table_rows = [
    ["凭证号", "日期", "科目名称", "借方金额", "贷方金额"],
    ["记-0001", "2025-01-05", "办公费", "1,500.00", "0.00"],
    ["记-0002", "2025-01-12", "差旅费", "2,300.50", "0.00"],
    ["记-0003", "2025-02-03", "办公费", "800.00", "0.00"],
    ["记-0004", "2025-02-15", "培训费", "5,000.00", "0.00"],
]
for ri, row in enumerate(table_rows):
    yy = rows_y[ri] + 12
    for ci, cell in enumerate(row):
        t(col_edges[ci] + 6, yy, cell, 9)
doc.save(OUT / 'sample_electronic.pdf')
doc.close()
print('✅ sample_electronic.pdf (文本层+表格线)')

# ─── 2. 扫描件PDF (图片渲染, 无文本层) ───
doc = fitz.open()
page = doc.new_page()
# 用文本框渲染成图片再贴回 → 无文本层
import io
from PIL import Image, ImageDraw, ImageFont
font = None
for fp in [r'C:\Windows\Fonts\msyh.ttc', r'C:\Windows\Fonts\simhei.ttf', r'C:\Windows\Fonts\simsun.ttc']:
    if os.path.exists(fp):
        try:
            font = ImageFont.truetype(fp, 18)
            break
        except:
            pass
img = Image.new('RGB', (595, 842), 'white')
d = ImageDraw.Draw(img)
d.text((60, 60), "银行回单", font=font, fill='black')
d.text((60, 100), "付款方: 某某单位  收款方: 四川XX公司", font=font, fill='black')
d.text((60, 140), "金额: 12,500.00  日期: 2025-03-10", font=font, fill='black')
d.text((60, 180), "用途: 办公用品采购", font=font, fill='black')
buf = io.BytesIO()
img.save(buf, format='PNG')
page.insert_image(page.rect, stream=buf.getvalue())
doc.save(OUT / 'sample_scanned.pdf')
doc.close()
print('✅ sample_scanned.pdf (无文本层, 图片)')

# ─── 3. SQL dump ───
sql = """-- MySQL dump 10.13
/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;

CREATE TABLE `voucher` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `凭证号` varchar(20) NOT NULL,
  `日期` date DEFAULT NULL,
  `科目` varchar(50) DEFAULT NULL,
  `借方金额` decimal(12,2) DEFAULT NULL,
  `贷方金额` decimal(12,2) DEFAULT NULL,
  `摘要` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `voucher` (`id`,`凭证号`,`日期`,`科目`,`借方金额`,`贷方金额`,`摘要`) VALUES
(1,'记-0001','2025-01-05','办公费',1500.00,0.00,'购买打印纸'),
(2,'记-0002','2025-01-12','差旅费',2300.50,0.00,'出差成都-北京'),
(3,'记-0003','2025-02-03','办公费',800.00,0.00,'购买墨盒'),
(4,'记-0004','2025-02-15','培训费',5000.00,0.00,'全员培训'),
(5,'记-0005','2025-03-01','维修费',NULL,0.00,'欠发票待补');
"""
(OUT / 'sample_dump.sql').write_text(sql, encoding='utf-8')
print('✅ sample_dump.sql (2表结构+5行数据, 含NULL)')

# ─── 4. 本地API测试服务 ───
api_py = '''# -*- coding: utf-8 -*-
"""本地分页API测试服务: python test_api_server.py [port]"""
import sys, json
from http.server import BaseHTTPRequestHandler, HTTPServer

RECORDS = [{"voucher_no": f"记-{i:04d}", "amount": i * 100.5, "dept": "财务处" if i % 2 else "办公室"} for i in range(1, 55)]

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        import urllib.parse
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        page = int(q.get('page', ['1'])[0])
        size = int(q.get('page_size', ['20'])[0])
        start = (page - 1) * size
        items = RECORDS[start:start + size]
        body = json.dumps({"code": 0, "data": {"total": len(RECORDS), "items": items}}).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *a):
        pass

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8971
    print(f'API测试服务: http://127.0.0.1:{port}/records')
    HTTPServer(('127.0.0.1', port), H).serve_forever()
'''
(OUT / 'test_api_server.py').write_text(api_py, encoding='utf-8')

api_cfg = {
    "url": "http://127.0.0.1:8971/records",
    "method": "GET",
    "headers": {},
    "params": {},
    "pagination": {"type": "page", "param": "page", "page_size_param": "page_size", "page_size": 20, "max_pages": 10, "stop_when_empty": True},
    "data_path": "data.items",
    "fields": [
        {"name": "凭证号", "path": "voucher_no"},
        {"name": "金额", "path": "amount"},
        {"name": "部门", "path": "dept"},
    ],
    "rate_limit_seconds": 0
}
(OUT / 'api_config.json').write_text(json.dumps(api_cfg, ensure_ascii=False, indent=2), encoding='utf-8')
print('✅ test_api_server.py + api_config.json')
