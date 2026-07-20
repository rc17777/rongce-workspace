import shutil, sys
sys.stdout.reconfigure(encoding='utf-8')
src = r'C:\Users\scrccpa\Desktop\马尔康项目决算审核报告-三级复核结果-20260720.xlsx'
dst = r'C:\Users\scrccpa\Desktop\马尔康项目决算审核报告-三级复核结果-20260720-v2.xlsx'
shutil.copyfile(src, dst)
print('copied to v2')
