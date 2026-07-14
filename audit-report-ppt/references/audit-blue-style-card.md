# 蓝色汇报风格卡（审计报告专用）

## 颜色系统

```python
COLORS = {
    'primary':      (0, 51, 102),      # #003366 深蓝 - 标题、重点元素
    'secondary':    (0, 102, 204),     # #0066CC 科技蓝 - 图表、装饰
    'accent':       (255, 102, 0),     # #FF6600 橙色 - 数据高亮、警示
    'background':   (245, 247, 250),   # #F5F7FA 浅灰 - 背景底色
    'text':         (51, 51, 51),      # #333333 正文
    'text_light':   (102, 102, 102),   # #666666 辅助文字
    'warning':      (204, 0, 0),       # #CC0000 红色 - 严重问题
    'success':      (0, 128, 0),       # #008000 绿色 - 整改成效
    'problem':      (255, 68, 68),     # #FF4444 问题标红
}
```

## 字体系统

```python
FONTS = {
    'title':     {'family': '微软雅黑', 'size': 32, 'bold': True, 'color': COLORS['primary']},
    'subtitle':  {'family': '微软雅黑', 'size': 20, 'bold': False, 'color': COLORS['primary']},
    'body':      {'family': '微软雅黑', 'size': 14, 'bold': False, 'color': COLORS['text']},
    'data':      {'family': 'DIN', 'size': 60, 'bold': True, 'color': COLORS['accent']},
    'small':     {'family': '微软雅黑', 'size': 10, 'bold': False, 'color': COLORS['text_light']},
}
```

## 间距规则

```python
MARGINS = {
    'page':     {'top': 0.5, 'bottom': 0.5, 'left': 0.5, 'right': 0.5},  # 英寸
    'title':    {'top': 0.3, 'height': 0.8},   # 标题区
    'content':  {'top': 1.3, 'height': 5.5},   # 内容区
    'footer':   {'top': 7.0, 'height': 0.5},   # 页脚
}
```

## 禁忌

- ❌ 不使用圆角过大的装饰
- ❌ 不使用卡通风格图标
- ❌ 不出现英文为主的排版
- ❌ 避免信息过载（每页文字不超过50字）
- ❌ 数字<100万不要用大红（用橙色警示）
- ❌ 整改率<80%时不要用绿色（用橙色表示"正在整改"）

## 特殊符号规范

| 符号 | 含义 | 使用场景 |
|------|------|----------|
| ↑ | 同比增长 | 整改成效展示 |
| ↓ | 同比下降 | 问题数量下降 |
| ✅ | 已完成 | 整改完成项 |
| ⏳ | 进行中 | 整改中项 |
| ❌ | 未完成 | 未整改项 |
| 🔴 | P0严重问题 | 问题优先级 |
| 🟡 | P1重要问题 | 问题优先级 |
| 🟢 | P2一般问题 | 问题优先级 |