# 审计报告数据可视化配色方案

## 语义色板

### 风险等级色板

| 语义 | 色名 | HEX | RGB | 用途 |
|------|------|-----|-----|------|
| 高风险 | 审计红 | #C0392B | 192,57,43 | 高风险发现、重大违规 |
| 中风险 | 警示橙 | #E67E22 | 230,126,34 | 中等风险、需关注事项 |
| 低风险 | 合规绿 | #27AE60 | 39,174,96 | 合规项、低风险 |
| 基准 | 专业蓝 | #2980B9 | 41,128,185 | 基准线、参考数据 |
| 中性 | 雅灰 | #BDC3C7 | 189,195,199 | 背景、辅助线 |

### 分析对比色板（用于多组数据对比）

| 编号 | 色名 | HEX | 用途 |
|------|------|-----|------|
| 1 | 深蓝 | #2C3E50 | 主方法/主数据 |
| 2 | 青蓝 | #3498DB | 对比方法/对比数据A |
| 3 | 绿色 | #27AE60 | 对比方法/对比数据B |
| 4 | 橙色 | #E67E22 | 对比方法/对比数据C |
| 5 | 紫色 | #8E44AD | 对比方法/对比数据D |
| 6 | 红色 | #C0392B | 异常值/预警 |

### 财务数据色板

| 语义 | HEX | 用途 |
|------|-----|------|
| 收入 | #27AE60 | 收入类数据 |
| 支出 | #C0392B | 支出类数据 |
| 结余/净额 | #2980B9 | 结余、净额 |
| 预算 | #BDC3C7 | 预算基准线 |
| 实际 | #2C3E50 | 实际执行数据 |

## 使用规则

### Rule 1: 同一项目统一色系
同一个审计项目在所有图表中，同一类数据使用同一颜色。
例如：如果"采购金额"在柱状图中是蓝色，折线图中也必须是蓝色。

### Rule 2: 每图最多5种颜色
超过5种颜色会分散注意力。如果数据维度超过5个：
- 合并低关注度维度
- 使用灰度区分次要维度
- 分成多个子图

### Rule 3: 异常值必须高亮
超出阈值的数据点使用红色/橙色，与正常数据形成视觉对比。

### Rule 4: SVG文字可编辑导出
matplotlib导出SVG时设置：
```python
import matplotlib
matplotlib.rcParams['svg.fonttype'] = 'none'
```
这样导出的SVG在Illustrator中文字仍然可编辑。

### Rule 5: 图表自明性
每张图表必须包含：
- 标题（描述"什么数据+什么维度"）
- 单位（万元/%/个）
- 数据来源
- 图例（如果有多组数据）
- 时间范围

## Python代码模板

### 柱状图（审计发现分布）

```python
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['svg.fonttype'] = 'none'

colors = {'高风险': '#C0392B', '中风险': '#E67E22', '低风险': '#27AE60', '合规': '#2980B9'}
categories = list(counts.keys())
values = list(counts.values())
bar_colors = [colors.get(c, '#BDC3C7') for c in categories]

plt.figure(figsize=(10, 6))
bars = plt.bar(categories, values, color=bar_colors, edgecolor='white', linewidth=0.5)
plt.title('审计发现风险等级分布', fontsize=14, fontweight='bold')
plt.ylabel('问题数量（个）')
for bar, val in zip(bars, values):
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3, str(val),
             ha='center', fontsize=11)
plt.tight_layout()
plt.savefig('audit_findings.svg', format='svg')
plt.savefig('audit_findings.png', dpi=300)
```

### 资金流向桑基图

```python
# 使用 plotly 绘制资金流向
import plotly.graph_objects as go

fig = go.Figure(data=[go.Sankey(
    node=dict(color='#2980B9', label=['预算', '采购', '工程', '服务', '其他']),
    link=dict(source=[0,0,0,0], target=[1,2,3,4],
              value=[金额1, 金额2, 金额3, 金额4],
              color=['rgba(41,128,185,0.3)']*4)
)])
fig.update_layout(title_text='项目资金流向分析')
fig.write_image('fund_flow.svg')
```

## 字体设置

### 中文报告
- 标题：黑体 / SimHei, 16pt, 加粗
- 正文：宋体 / SimSun, 12pt
- 图表标注：微软雅黑, 10pt

### 英文报告
- 标题：Arial, 16pt, Bold
- 正文：Times New Roman, 12pt
- 图表标注：Arial, 10pt
