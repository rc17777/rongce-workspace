import win32com.client
import os

pptx = r"C:\Users\scrccpa\.openclaw\workspace\rongce-ppt-master\融策业务能力展示_轻奢暗金.pptx"
outdir = r"C:\Users\scrccpa\.openclaw\workspace\rongce-ppt-master\render"
os.makedirs(outdir, exist_ok=True)

ppt = win32com.client.Dispatch("PowerPoint.Application")
pres = ppt.Presentations.Open(pptx, WithWindow=False)
for i, slide in enumerate(pres.Slides, 1):
    path = os.path.join(outdir, f"render{i:02d}.png")
    slide.Export(path, "PNG", 1600, 900)
    print("exported", path)
pres.Close()
ppt.Quit()
print("DONE")
