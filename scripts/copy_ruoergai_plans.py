# -*- coding: utf-8 -*-
"""为若尔盖项目复制实施方案文件"""
import shutil, os

impl_dir = "E:/2026/实施方案"
dirs = os.listdir(impl_dir)

# 医保 [0]
med_src = os.path.join(impl_dir, dirs[0])
med_dst = "D:/openclaw-workspace/audit-blackboard/projects/若尔盖医保资金审计/raw_data"
os.makedirs(med_dst, exist_ok=True)
for f in os.listdir(med_src):
    shutil.copy2(os.path.join(med_src, f), os.path.join(med_dst, f))
    print("医保方案: " + f)

# 校园餐 [1] + [2]
campus_dst = "D:/openclaw-workspace/audit-blackboard/projects/若尔盖校园餐专项资金审计/raw_data"
os.makedirs(campus_dst, exist_ok=True)
for idx in [1, 2]:
    src = os.path.join(impl_dir, dirs[idx])
    for f in os.listdir(src):
        shutil.copy2(os.path.join(src, f), os.path.join(campus_dst, f))
        print("校园餐方案: " + f)

# 验证
for name in ["若尔盖校园餐专项资金审计", "若尔盖医保资金审计"]:
    d = "D:/openclaw-workspace/audit-blackboard/projects/" + name + "/raw_data"
    files = os.listdir(d)
    total = sum(os.path.getsize(os.path.join(d, f)) for f in files)
    print("")
    print(name + ": " + str(len(files)) + " files, " + str(int(total/1024)) + "KB")
