"""Fix inner double quotes in data entries by replacing them with Chinese guillemets"""
import re

with open(r"D:\openclaw-workspace\zhixi_intelligent\generate_materials_checklist.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find lines that are tuple entries with problematic inner quotes
# Pattern: lines that start with spaces + ( and contain Chinese text with double quotes
lines = content.split("\n")
fixed_lines = []
fixes = 0

for i, line in enumerate(lines):
    stripped = line.strip()
    # Only fix lines that are data entries in the materials list
    if stripped.startswith("(") and ("必需" in stripped or "重要" in stripped or "建议" in stripped):
        # These are material entry tuples: ("材料名称", "优先级", "说明")
        # We need to protect inner quotes in the first and third elements
        
        # Strategy: replace problematic inner " with 「」
        # Identify the first string (material name) and third string (note)
        
        # Simple approach: count quotes and figure out where inner ones are
        # A correct entry should have exactly 6 quotes: ( "name" , "priority" , "note" )
        # If there are more than 6, inner quotes exist
        
        quote_positions = [j for j, c in enumerate(line) if c == '"']
        
        if len(quote_positions) > 8:  # More than 8 = definitely has extra inner quotes
            # Rebuild the line with Chinese quotes for inner text
            # This is fragile but the data is structured
            
            # Find the first 3 fields (separated by commas)
            # First: before first comma after opening (
            # Second: between first and second comma
            # Third: after second comma
            
            # Let me try a different approach: just find and replace known problematic patterns
            problematic = [
                ('"三重一大"', '\u300e三重一大\u300f'),
                ('"三资"', '\u300e三资\u300f'),
                ('"一卡通"', '\u300e一卡通\u300f'),
            ]
            
            newline = line
            for old, new in problematic:
                if old in newline:
                    newline = newline.replace(old, new)
                    fixes += 1
            
            fixed_lines.append(newline)
        else:
            fixed_lines.append(line)
    else:
        fixed_lines.append(line)

if fixes:
    with open(r"D:\openclaw-workspace\zhixi_intelligent\generate_materials_checklist.py", "w", encoding="utf-8") as f:
        f.write("\n".join(fixed_lines))
    print(f"Fixed {fixes} occurrences")
else:
    # Do a broader search
    for i, line in enumerate(lines):
        q_count = line.count('"')
        if q_count > 8 and line.strip().startswith("("):
            print(f"Line {i+1} has {q_count} quotes: {line.strip()[:120]}")
    print("No automatic fixes applied - need manual review")
