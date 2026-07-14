import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'C:\Users\scrccpa\.openclaw\workspace\scripts\write_report.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all wrong numbers
replacements = [
    ("568,918", "547,660"),
    ("49,252", "70,510"),
    ("56.89万元", "54.77万元"),
    ("56.89万", "54.77万"),
    ("核减4.93万元，核减率7.97%", "核减7.05万元，核减率11.41%"),
    ("核减4.93万元（核减率7.97%）", "核减7.05万元（核减率11.41%）"),
    ("核减4.93万元（审减率7.97%）", "核减7.05万元（审减率11.41%）"),
    ("审减4.93万元（审减率7.97%）", "审减7.05万元（审减率11.41%）"),
]

for old, new in replacements:
    if old in content:
        count = content.count(old)
        content = content.replace(old, new)
        print(f"Replaced '{old}' -> '{new}' ({count} occurrences)")
    else:
        print(f"NOT FOUND: '{old}'")

# The individual line for 7.97% in the table row: '核减率7.97%，取整56.89万元'
# already handled by the first two replacements

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("\nDone fixing report script.")
