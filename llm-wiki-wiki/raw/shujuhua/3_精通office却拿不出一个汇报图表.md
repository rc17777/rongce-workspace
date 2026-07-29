# Python | 精通office，却拿不出一个汇报图表？

- **日期**: 2020-09-17
- **标签**: Python
- **原文链接**: https://mp.weixin.qq.com/s?__biz=MzI1NTA5NDA2MA==&mid=2648441548&idx=1&sn=8c23fc1e6c7f58653543d4d50ffd360b

---

## 重要声明

本文不是广告，但问题的解决很有通用性。本文中的所有信息和数据都是虚拟的，仅为说明数据化风控的思路和过程，不代表真实的交易情况。所有的数据都是使用Python的faker库生成，非真实数据，并根据分析需要进行了调整。

## 面临的问题

又到汇报季节，领导看到如下的检查问题整改数据，提出要求："能否将这些信息放到一个图表中进行对比展示，即可看到问题，又可以看到整改情况；即看得到金额比较，也看得到个数对比？"

有图有真相，看起来也比数据直观。但需求和现实之间总有差距，看似简单的要求，也是工作中常见的需求，但找不到实现的方法。

精通 office 的同学，翻遍了度娘，可以实现双Y轴或者双数据，但同时满足貌似无解？更麻烦的是，如果有很多机构，需要分机构生成不同机构的情况，也一个个作图？

## 实现思路

领导提出的问题，实际上是一个**先分类再双Y轴**展现的问题。利用 Python 的绘图库 matplotlib，先创建一个图层，绘制金额方面的柱状图，再复制当前图层，绘制问题笔数方面的折线图，并将笔数标注在从Y轴上。

## 实现代码

### 1.环境初始化

需要 Python 的绘图库 **matplotlib** 和数据处理库 **pandas**：

```python
# -*- coding:utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
```

### 2.读取数据绘制图表

```python
## 读取数据 跳过表格标题
df = pd.read_excel('检查问题及整改情况.xlsx',skiprows=1)
## 图表初始化
plt.clf()
## 设置图表的中文显示
plt.rcParams['font.sans-serif']=['SimHei']
## 设置图表的显示样式
plt.style.use('ggplot')
## 初始化绘图区
fig, ax = plt.subplots(figsize=(12,8))
## 设置图表标题 加个回车\n是为了空出一行
ax.set_title('检查问题及整改情况\n',fontdict={'weight':'bold','size': 30, 'color':'#336699'})
## X轴的标签数据 月份
labels = df['月份']
## X轴对应月份的12个数字
x = np.arange(len(labels))
## 主坐标轴的数据
y1 = df['问题金额']
y2 = df['已整改金额']
## 柱状图的宽度
barwidth = 0.4
## 设置X轴刻度
ax.set_xticks(x)
ax.set_xticklabels(labels)
## 设置y轴的标签
ax.set_ylabel('问题金额')
## 设置y轴的刻度范围
ax.set_ylim(bottom=0,top=50000)
## 绘制主坐标的两个柱状图
ax.bar(x-barwidth/2.0, y1, barwidth, label='问题金额',color="tab:blue")
ax.bar(x+barwidth/2.0, y2, barwidth, label='已整改金额',color="tab:orange")
## 显示主坐标的图例
## 图例默认显示在图表左上角 通过bbox_to_anchor参数放置到主图下面
plt.legend(loc='lower left', bbox_to_anchor=(0.3,0.02), bbox_transform=fig.transFigure, ncol=2, borderaxespad = 0)
## 次坐标图表 twinx()函数很关键！！
ax2 = plt.twinx()
ax2.set_ylabel('问题个数')
ax2.set_ylim(bottom=0,top=70)
## 绘制折线图
p1=ax2.plot(df['问题个数'],color="blue",linestyle='dashdot',label='问题个数')
p2=ax2.plot(df['已整改个数'],color="orange",linestyle='dashdot',label='已整改个数')
ax2.yaxis.set_tick_params(direction='out')
## 显示图例
plt.legend(loc='lower left', bbox_to_anchor=(0.6,0.02), bbox_transform=fig.transFigure, ncol=2, borderaxespad = 0)
## 显示图表绘制结果
plt.show()
```

## 延伸思考

如果只要作一次图，使用 office 2007 以上版本，可以通过**组合图表**实现。

关注公众号，对话框回复"图表"获得实例使用的数据
