import shutil, os, sys
sys.stdout.reconfigure(encoding='utf-8')
src = r'D:\openclaw-workspace\output\v5_final.pptx'
dst = r'C:\Users\scrccpa\Desktop\轨道培训\四川轨道公司审计风险培训-v5_模板.pptx'
try:
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    # If file exists and is locked, try a different name
    if os.path.exists(dst):
        try:
            os.remove(dst)
        except:
            base = r'C:\Users\scrccpa\Desktop\轨道培训\四川轨道公司审计风险培训-v5_模板'
            for i in range(2, 10):
                alt = f'{base}_{i}.pptx'
                if not os.path.exists(alt):
                    dst = alt
                    break
    shutil.copy2(src, dst)
    print(f'Copied to: {dst}')
except Exception as e:
    print(f'Error: {e}')
    # Fallback: copy to desktop root
    fallback = r'C:\Users\scrccpa\Desktop\轨道培训审计风险-v5.pptx'
    try:
        shutil.copy2(src, fallback)
        print(f'Fallback: {fallback}')
    except Exception as e2:
        print(f'Fallback also failed: {e2}')
        print(f'File remains at: {src}')
