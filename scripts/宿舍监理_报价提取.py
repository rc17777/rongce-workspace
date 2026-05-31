import sys, os, fitz, re
sys.stdout.reconfigure(encoding='utf-8')

BASE = r"C:\Users\scrccpa\Desktop\招投标审计\5号6号学生宿舍建设项目监理\监理投标文件(PDF)"
results = []

for fname in sorted(os.listdir(BASE)):
    if not fname.endswith('.pdf'): continue
    path = os.path.join(BASE, fname)
    name = fname.replace('.pdf', '').strip()
    doc = fitz.open(path)
    
    # Search all pages for bid price
    found_price = None
    found_page = None
    
    for pg in range(len(doc)):
        text = doc[pg].get_text()
        
        # Search for price patterns in context of bidding
        if any(kw in text for kw in ['投标报价', '监理服务费', '投标总价', '愿以']):
            # Find price near these keywords
            prices = re.findall(r'(\d[\d,]{2,}(?:\.\d{2})?)\s*元', text)
            if prices:
                # Take the first substantial price
                for p in prices:
                    val = float(p.replace(',', ''))
                    if 100000 < val < 5000000:  # reasonable range
                        found_price = val
                        found_page = pg + 1
                        break
            if found_price:
                break
    
    # If not found, try broader search
    if not found_price:
        for pg in range(min(20, len(doc))):
            text = doc[pg].get_text()
            # Search for standalone prices
            prices = re.findall(r'(\d[\d,]{2,}(?:\.\d{2})?)\s*元', text)
            for p in prices:
                val = float(p.replace(',', ''))
                if 100000 < val < 5000000:
                    found_price = val
                    found_page = pg + 1
                    break
            if found_price:
                break
    
    results.append((name[:25], found_price, found_page))
    doc.close()

# Print sorted by price
results.sort(key=lambda x: x[1] or 0)
print(f"{'Bidder':25s} {'Price':>12s}  Page")
print("-" * 50)
for name, price, pg in results:
    if price:
        print(f"{name:25s} {price:>12,.2f}  pg={pg}")
    else:
        print(f"{name:25s} {'NOT FOUND':>12s}  -")
