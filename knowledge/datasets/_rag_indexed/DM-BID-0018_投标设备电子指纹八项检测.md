---
title: "投标设备电子指纹八项检测"
type: "detection_method"
layer: "L18"
confidence_level: "铁证"
alias: "L18-电子指纹"
business_line: "通用"
keywords: [电子指纹, IP, MAC, CPU ID, 硬盘SN, 机器码, GUID, 同设备]
dataset_id: "DM-BID-0018"
---

# 投标设备电子指纹八项检测

## 方法描述
从投标平台日志/投标文件元数据中提取八项设备指纹：IP地址、MAC地址、CPU ID、硬盘序列号、主板序列号、整机机器码、文件创建GUID、图片哈希。任一指纹跨不同投标人匹配→同一设备/同一网络提交→串标。

## 检测逻辑
八项指纹逐项提取→构建指纹→投标人映射表→任一指纹被≥2个不同投标人共享→标记。注意：IP/MAC需要从代理后台日志获取；CPU ID/硬盘SN/机器码需要客户端控件上报。

## 输入数据
- 必须：投标平台后台日志（IP/MAC）, 投标客户端上报的设备指纹
- 可选：投标文件中的计算机名残留, 文件创建GUID

## 技术参数
```python
# IP/MAC: 精确字符串匹配
shared_ips = df.groupby('ip')['bidder'].unique()
collision = shared_ips[shared_ips.apply(len) >= 2]
```

## 误报风险
- 同一写字楼共用出口IP→NAT环境下的IP碰撞需排除
- 投标人在同一代理机构现场投标→IP必然相同

## 组合规则
- 与L3文本雷同组合→同IP+文本雷同→排除NAT误报
- 与L1报价组合→同IP+协同报价→铁证
