# 图表规格参考

## 通用参数

| 参数 | 默认值 | 说明 |
|------|-------|------|
| DPI | 200 | 打印质量≥200dpi，展示用≥150dpi |
| 字体 | 微软雅黑 | 正文；黑体用于标题 |
| 图片格式 | PNG | 透明背景用PNG，文档嵌入用PNG |

## 各图表尺寸建议

| 图表类型 | 建议宽度 | 建议高度 | 布局方向 |
|---------|:-------:|:--------:|:--------:|
| 风险热力图 | 800px | items×80+100px | 横版 |
| 柱状图（<5项） | 800px | 500px | 横版 |
| 柱状图（≥5项） | 1000px | 600px | 横版 |
| 饼图 | 600px | 500px | 正方形 |
| 折线图 | 1000px | 500px | 横版宽幅 |
| 彩色表格 | cols×120px | rows×50+100px | 自适应 |
| 组织结构图 | 1000px | 700px | 横版 |
| 流程图 | 700px | items×100+120px | 竖版/支持阶段分组 |
| 时间轴 | items×140+120px | 350px | 横版 |
| 循环图 | 500px | 500px | 正方形 |

## Python Data JSON Schema

### heatmap
```json
{
  "rows": ["资产租赁", "停车场管理", ...],
  "columns": ["可能性", "影响程度"],
  "values": [[3,4], [4,5], ...],
  "min": 1, "max": 5,
  "title": "审计重点风险评估"
}
```

### bar
```json
{
  "labels": ["预算", "实际", "差异"],
  "values": [100, 85, 15],
  "title": "预算执行对比"
}
// Grouped bars:
{
  "labels": ["部门A", "部门B", "部门C"],
  "values": [[80, 70], [60, 55], [90, 85]],
  "group_names": ["预算", "实际"],
  "title": "各部门预算执行对比"
}
```

### pie
```json
{
  "labels": ["人工成本", "场地费", "材料费", "管理费"],
  "values": [45, 25, 15, 15],
  "donut": true,
  "title": "成本构成分析"
}
```

### line
```json
{
  "labels": ["Q1", "Q2", "Q3", "Q4"],
  "values": [[80, 95, 88, 102]],
  "series_names": ["收入"],
  "title": "季度收入趋势",
  "ylabel": "万元"
}
```

### flowchart
```json
{
  "title": "审计工作流程图",
  "orientation": "vertical",
  "steps": [
    {"name": "接收委托", "desc": "接收审计任务书", "color": "#388E3C"},
    {"name": "控制测试", "desc": "是否通过？", "color": "#FBC02D", "shape": "diamond", "arrowLabel": "否"},
    {"name": "出具报告", "desc": "正式签发", "color": "#D32F2F"}
  ],
  "stages": [
    {"name": "准备阶段", "start": 0, "end": 1}
  ],
  "actors": ["审计组", "被审计单位"]
}
```

### timeline
```json
{
  "title": "项目里程碑",
  "orientation": "horizontal",
  "milestones": [
    {"date": "2026.01", "label": "启动", "desc": "方案确认", "color": "#388E3C"},
    {"date": "2026.05", "label": "完成", "desc": "报告出具"}
  ]
}
```

### cycle
```json
{
  "title": "PDCA循环",
  "items": ["P-计划", "D-执行", "C-检查", "A-改进"]
}
```

### colored_table
```json
{
  "headers": ["序号", "问题类型", "涉及金额", "状态"],
  "rows": [
    ["1", "合同违规", "50万", "高风险"],
    ["2", "台账缺失", "0", "中风险"],
    ["3", "数据异常", "12万", "高风险"]
  ],
  "status_column": 3,
  "title": "审计发现问题汇总"
}
```
