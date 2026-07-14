"""Fix Chinese full-width quotation marks in source files"""
import os

files_to_fix = [
    r"D:\openclaw-workspace\zhixi_intelligent\generate_materials_checklist.py",
    r"D:\openclaw-workspace\zhixi_intelligent\SKILL.md",
]

for filepath in files_to_fix:
    if not os.path.exists(filepath):
        continue
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    fixed = content.replace("\u201c", "\u300c").replace("\u201d", "\u300d")
    
    if fixed != content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(fixed)
        count = content.count("\u201c") + content.count("\u201d")
        print(f"Fixed {count} quotes in: {os.path.basename(filepath)}")
    else:
        print(f"No changes needed: {os.path.basename(filepath)}")

os.remove("find.txt") if os.path.exists("find.txt") else None
print("Done")
