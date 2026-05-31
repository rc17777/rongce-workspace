import os, glob
import os.path as op

# Search for Obsidian vaults (look for .obsidian dir)
found = []
searches = [
    r'C:\Users\Admin\Documents',
    r'C:\Users\Admin\Desktop', 
    r'C:\Users\Admin\OneDrive',
    r'C:\Users\Admin',
]

for base in searches:
    if not op.exists(base):
        continue
    for root, dirs, files in os.walk(base):
        if '.obsidian' in dirs:
            found.append(os.path.join(root, '.obsidian'))
            if len(found) >= 3:
                break
        if len(found) >= 3:
            break

if found:
    for f in found:
        # Get parent (vault root)
        vault = os.path.dirname(f)
        print(f'VAULT: {vault}')
else:
    print('No Obsidian vault found in standard locations')
    print('Please provide your vault path')
