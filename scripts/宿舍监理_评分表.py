"""提取完整的评分表（监理大纲+报价评分）"""
import fitz, sys
sys.stdout.reconfigure(encoding='utf-8')

path = r"C:\Users\scrccpa\Desktop\招投标审计\5号6号学生宿舍建设项目监理\监理招标文件定稿.pdf"
doc = fitz.open(path)

# Pages 72-76 should contain the full scoring criteria
for pg in [71, 72, 73, 74, 75]:  # 0-indexed
    text = doc[pg].get_text()
    if text.strip():
        print(f'\n{"="*60}')
        print(f'PAGE {pg+1}')
        print("="*60)
        print(text)
        print()

doc.close()
