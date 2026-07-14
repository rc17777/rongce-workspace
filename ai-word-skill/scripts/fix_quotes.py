import sys, re

path = sys.argv[1]
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace ASCII double quotes that are INSIDE Python strings and represent Chinese quotes
# Pattern: look for "Chinese text patterns with inner quotes
# We'll replace known problematic patterns
replacements = [
    ('"分段平行施工、流水作业"', '「分段平行施工、流水作业」'),
    ('"多杆合一"', '「多杆合一」'),
    ('"XX局"', '「XX局」'),
    ('"乡村振兴示范项目"', '「乡村振兴示范项目」'),
    ('"能走"', '「能走」'),
    ('"愿意反复走"', '「愿意反复走」'),
    ('"有没有"', '「有没有」'),
    ('"好不好用、好不好维护、好不好解释"', '「好不好用、好不好维护、好不好解释」'),
    ('"禁止机动车"', '「禁止机动车」'),
]
for old, new in replacements:
    content = content.replace(old, new)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'Fixed quotes in {path}')
