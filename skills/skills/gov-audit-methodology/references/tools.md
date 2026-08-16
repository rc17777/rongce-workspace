# 工具安装与使用指南

## Orange — 零代码数据分析工具

**适用场景**：业务人员快速探索数据、无Python基础的人员入门数字化审计

### 安装

```bash
pip install orange3 --user
```

启动：`python -m Orange.canvas` 或通过官网下载安装包 https://orangedatamining.com/download/

### 核心组件集

| 组件集 | 功能 | 审计场景 |
|--------|------|---------|
| **Data** | CSV/Excel导入、数据库读取、透视表、抽样 | 从被审计单位Excel快速导入 |
| **Visualize** | 箱体图、散点图、直方图、热图 | 快速看分布、找离群值 |
| **Model** | KNN、随机森林、SVM、逻辑回归、神经网络 | 分类/预测风险 |
| **Evaluate** | 交叉验证、ROC曲线 | 模型效果评估 |
| **Unsupervised** | PCA、t-SNE、K-Means、层次聚类 | 异常检测、分组聚类 |

### 典型工作流

```
CSV File Import → Data Table(预览) → Distributions(分布图)
                                    → Scatter Plot(散点图)
                                    → K-Means(聚类) → Scatter Plot(可视化)
```

> 来源：#50「Orange零代码数据分析」

## OpenCV — 计算机视觉资产盘点

**适用场景**：固定资产实地盘点、库存商品盘点

### 安装

```bash
pip install opencv-python
pip install pyzbar  # 条码识别
```

### 有条码资产快速识别

```python
import cv2
import pyzbar.pyzbar as pyzbar

img = cv2.imread('资产照片.jpg')
img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
barcodes = pyzbar.decode(img_gray)

for barcode in barcodes:
    code = barcode.data.decode('utf8')
    print(f"条码: {code}")
    (x, y, w, h) = barcode.rect
    cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
```

### 无条码物件计数（轮廓检测）

```python
import cv2

img = cv2.imread('资产.jpg')
img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
ret, img_bi = cv2.threshold(img_gray, 110, 255, cv2.THRESH_BINARY_INV)
img_edged = cv2.Canny(img_bi, 30, 100)
# 膨胀+腐蚀闭合边缘
img_edged = cv2.dilate(img_edged, None, iterations=5)
img_edged = cv2.erode(img_edged, None, iterations=4)
# 轮廓检测
(contours, _) = cv2.findContours(img_edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
print(f"检测到 {len(contours)} 个物体")
```

> 来源：#72「用计算机视觉技术进行资产盘点」

## QGIS — 空间维度聚类分析

**适用场景**：工程项目地理分布分析、供应商地域聚类、异常地理集中的疑点发现

### 安装

官网下载：https://qgis.org/download/ （免费开源）

### 审计应用

1. 导入审计对象的地理坐标数据（CSV含经纬度）
2. 叠加行政区划图层
3. K-Means聚类分析 → 发现异常集中的项目群
4. 热力图 → 直观展示分布密度

> 来源：#79「用QGIS进行空间维度聚类分析提取疑点清单」

## Python 核心审计库速查

| 库 | 用途 | 典型审计场景 |
|:---|:-----|:-----------|
| **pandas** | 数据处理 | 数据清洗、合并、透视、批量Excel读取 |
| **scikit-learn** | 机器学习 | K-Means聚类、孤立森林异常检测、TF-IDF文本雷同 |
| **matplotlib/seaborn** | 可视化 | 趋势图、分布图、异常标注图 |
| **zmail** | 邮件发送 | 批量发送整改通知和台账（`pip install zmail`） |
| **glob** | 文件遍历 | 多层目录批量读取Excel/Word |
| **openpyxl** | Excel读写 | 生成带超链接的审计底稿 |
| **jieba** | 中文分词 | 合同/报告文本关键词提取 |

## 环境建议

- **入门级**：Anaconda（集成Python+pandas+numpy+matplotlib）
- **可视化探索**：Orange（拖拽操作）
- **空间分析**：QGIS（桌面GIS）
- **高级分析**：scikit-learn + jupyter
