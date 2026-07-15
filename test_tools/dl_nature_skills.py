"""Download nature-skills as ZIP from GitHub."""
import sys, os, urllib.request, zipfile, shutil

sys.stdout.reconfigure(encoding='utf-8')

url = 'https://github.com/Yuan1z0825/nature-skills/archive/refs/heads/main.zip'
dest_zip = r'D:\openclaw-workspace\test_tools\nature-skills.zip'
dest_dir = r'D:\openclaw-workspace\test_tools'
final_dir = r'D:\openclaw-workspace\test_tools\nature-skills'

# Clean up
for p in [dest_zip, final_dir]:
    if os.path.exists(p):
        if os.path.isdir(p):
            shutil.rmtree(p, ignore_errors=True)
        else:
            os.remove(p)

print(f"Downloading from GitHub...")
for attempt in range(5):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
            with open(dest_zip, 'wb') as f:
                f.write(data)
            print(f"Downloaded: {len(data):,} bytes ({len(data)/1024/1024:.1f} MB)")
            break
    except Exception as e:
        print(f"  Attempt {attempt+1} failed: {e}")
        if attempt == 4:
            sys.exit(1)
        import time; time.sleep(3)

print("Extracting...")
with zipfile.ZipFile(dest_zip, 'r') as zf:
    # Files are inside nature-skills-main/
    zf.extractall(dest_dir)

# Rename nature-skills-main to nature-skills
extracted = os.path.join(dest_dir, 'nature-skills-main')
if os.path.exists(extracted):
    if os.path.exists(final_dir):
        shutil.rmtree(final_dir)
    os.rename(extracted, final_dir)
    print(f"Extracted to: {final_dir}")

# List top-level contents
print("\nTop-level contents:")
for item in sorted(os.listdir(final_dir)):
    full = os.path.join(final_dir, item)
    if os.path.isdir(full):
        print(f"  📁 {item}/")
    else:
        print(f"  📄 {item}")

# List skills
skills_dir = os.path.join(final_dir, 'skills')
if os.path.exists(skills_dir):
    print("\nAvailable skills:")
    for item in sorted(os.listdir(skills_dir)):
        print(f"  📁 {item}/")

# Clean up zip
os.remove(dest_zip)
print("\nDone!")
