# Python | 如何从大量Excel文件中用多关键词且不指定字段名称进行检索

- 来源：「数据化审计」公众号 | 作者：小叶 | 日期：2022-01-16
- 原文：https://mp.weixin.qq.com/s?__biz=MzI1NTA5NDA2MA==&mid=2648442237&idx=1&sn=ded877af03084ab4d3ab6ae41021ad73

## 需求场景

拿到某单位一年的工作日志Excel文件包，文件分布在多层目录下，字段名称不统一。需求：
1. 多关键字检索（存放在查询条件.txt中）
2. 返回关键字所在文件名、sheet页、字段
3. 返回所在行完整内容
4. 结果存放在一个Excel中，可点击文件名链接跳转

## 实现思路（遍历法）

1. `glob.iglob` 迭代列出多层目录下的Excel日志文件
2. `pd.read_excel(sheet_name=None)` 读取所有sheet页
3. 对每个sheet逐字段检索
4. 记录结果到DataFrame，文件名转为超链接格式
5. 输出Excel结果文件

## 核心代码

```python
import pandas as pd
import glob, os

def filename2url(filename):
    furl = 'file:///%s/%s' % (os.getcwd().replace('\\','/'), filename)
    return '=HYPERLINK("%s","点击打开：%s")' % (furl, filename.split('\\')[-1])

with open('查询条件.txt', 'r', encoding='utf8') as fp:
    qwordlst = fp.readlines()
keywords = '|'.join(w.strip() for w in qwordlst)

df_reusltall = pd.DataFrame(columns=['文件链接','文件名','sheet名','行数','字段名','字段值','整行内容'])

for f in glob.iglob('**/*日志*.xlsx', recursive=True):
    df_lst = pd.read_excel(f, sheet_name=None)
    for (k, v) in df_lst.items():
        df_cur = v.astype(str)
        df_cur['index'] = df_cur.index + 1
        for col in df_cur.columns[0:-1]:
            df_result = df_cur[df_cur[col].str.contains(keywords)]
            if len(df_result) > 0:
                for idx, row in enumerate(list(df_result['index'])):
                    df_reusltall.loc[len(df_reusltall)] = [
                        filename2url(f), f, k, row, col,
                        df_result[col].values[idx],
                        df_result.iloc[idx].to_string(header=False, index=False)
                    ]
df_reusltall.to_excel('检索结果.xlsx', index_label='结果序号')
```

环境：Python 3.8 / Pandas 1.1.3
