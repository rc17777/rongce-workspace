import os, datetime, glob
files = sorted(glob.glob(r'temp_ocr\output_new\稽查文件3\p*.md'))
print(f'Total files on disk: {len(files)}')
# Check last 5 modified times
recent = sorted(files, key=os.path.getmtime, reverse=True)[:5]
for f in recent:
    t = datetime.datetime.fromtimestamp(os.path.getmtime(f))
    print(f'{os.path.basename(f)}  {t.strftime("%H:%M:%S")}')
