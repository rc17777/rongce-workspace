import os, sys, glob

# The base directory for this project
base = r'C:\Users\scrccpa\Desktop\成都轨道资源资料'

# Find the dir number 35
target_dir = None
for root, dirs, files in os.walk(base):
    for d in dirs:
        if d == '35':  # exact match for the directory number
            target_dir = os.path.join(root, d)
            break
    if target_dir:
        break

print("Target dir:", repr(target_dir))

if target_dir:
    files = sorted(os.listdir(target_dir))
    print("\nFiles in 35:")
    for f in files:
        fpath = os.path.join(target_dir, f)
        size = os.path.getsize(fpath)
        print(f"  {repr(f)}  ({size} bytes)")
    
    print("\n\n=== Examining file structures ===")
    import pandas as pd
    
    for fname in files:
        fpath = os.path.join(target_dir, fname)
        ext = os.path.splitext(fname)[1].lower()
        print(f"\n{'='*80}")
        print(f"FILE: {repr(fname)}")
        print(f"Extension: {ext}")
        
        try:
            if ext == '.csv':
                # Try with different encodings
                for enc in ['utf-8', 'gbk', 'gb2312', 'gb18030', 'utf-16']:
                    try:
                        df = pd.read_csv(fpath, encoding=enc, nrows=5)
                        print(f"  Encoding: {enc}")
                        print(f"  Shape: {df.shape}")
                        print(f"  Columns: {list(df.columns)}")
                        print(f"  Dtypes:")
                        print(df.dtypes)
                        print(f"  First row:")
                        print(df.iloc[0].to_dict())
                        break
                    except Exception as e:
                        print(f"  Enc {enc}: {type(e).__name__}: {e}")
                        continue
            elif ext == '.xlsx':
                df = pd.read_excel(fpath, nrows=5)
                print(f"  Shape: {df.shape}")
                print(f"  Columns: {list(df.columns)}")
                print(f"  Dtypes:")
                print(df.dtypes)
                print(f"  First row:")
                print(df.iloc[0].to_dict())
            else:
                print(f"  Unknown extension")
        except Exception as e:
            print(f"  ERROR: {type(e).__name__}: {e}")
    
    # Also check file 34 (协议车位台账)
    print("\n\n=== Checking Dir 34 (协议台账) ===")
    target34 = os.path.join(os.path.dirname(target_dir), '34')
    if os.path.exists(target34):
        for f in os.listdir(target34):
            fpath = os.path.join(target34, f)
            print(f"\nFILE: {repr(f)}")
            try:
                # xls file
                df = pd.read_excel(fpath, nrows=5)
                print(f"  Shape: {df.shape}")
                print(f"  Columns: {list(df.columns)}")
                print(f"  First row:")
                print(df.iloc[0].to_dict())
            except Exception as e:
                print(f"  ERROR: {type(e).__name__}: {e}")

else:
    print("Could not find directory '35'")
    # Let's search more broadly
    for root, dirs, files in os.walk(base):
        print(f"Dir: {repr(root)}")
        if files:
            for f in files[:5]:
                print(f"  {repr(f)}")

