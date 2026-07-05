"""从原始投标PDF中提取报价表格"""
import pdfplumber, os, re

base = r"C:\Users\scrccpa\Desktop\招投标审计\2025-XZ15-Y-37-2024年多功能急救实训室建设项目\2024年多功能急救实训室建设项目投标文件(1)\投标文件\采购包1"

bidders = {
    '好医助': '四川省好医助医疗器械有限公司(包1)',
    '易可天地': '成都易可天地科技有限公司(包1)',
    '江西正好': '江西正好医疗器械有限公司(包1)',
}

for name, folder in bidders.items():
    bidder_dir = os.path.join(base, folder)
    price_file = os.path.join(bidder_dir, '报价表.pdf')
    
    if not os.path.exists(price_file):
        print(f"{name}: 报价表.pdf not found")
        continue
    
    print(f"\n{'='*60}")
    print(f"【{name}】报价表表格提取")
    print(f"{'='*60}")
    
    with pdfplumber.open(price_file) as pdf:
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            print(f"\n--- Page {i+1} ---")
            if tables:
                for j, table in enumerate(tables):
                    print(f"  Table {j+1}: {len(table)} rows x {len(table[0]) if table else 0} cols")
                    for row in table[:3]:  # Show first 3 rows
                        cells = [str(c)[:30] if c else '' for c in row]
                        print(f"    {' | '.join(cells)}")
                    print(f"    ... ({len(table)} rows total)")
                    # Look for price data
                    for row in table:
                        for cell in row:
                            if cell and re.search(r'\d{4,}', str(cell)):
                                if '元' in str(cell) or re.search(r'^\d[\d,.]*$', str(cell).strip()):
                                    pass  # These are price cells
            else:
                # Try text extraction instead
                text = page.extract_text()
                if text:
                    # Find lines with prices
                    for line in text.split('\n'):
                        line = line.strip()
                        if re.search(r'[\d,]{4,}', line) and len(line) > 3:
                            print(f"    {line[:150]}")
