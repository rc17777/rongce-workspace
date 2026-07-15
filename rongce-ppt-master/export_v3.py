import win32com.client
import os

pptx = r"C:\Users\scrccpa\.openclaw\workspace\rongce-ppt-master\融策业务能力展示_轻奢暗金_AI封面版.pptx"
outdir = r"C:\Users\scrccpa\.openclaw\workspace\rongce-ppt-master\render_v3"
os.makedirs(outdir, exist_ok=True)

ppt = win32com.client.Dispatch("PowerPoint.Application")
pres = ppt.Presentations.Open(pptx, WithWindow=False)
for n in (1, 10):
    slide = pres.Slides(n)
    path = os.path.join(outdir, f"s{n:02d}.png")
    slide.Export(path, "PNG", 1600, 900)
    print("exported", path)
pres.Close()
ppt.Quit()
print("DONE")
