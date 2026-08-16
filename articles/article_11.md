# 审计人员数字技能修炼手册 | 入门篇（三）：Python爬虫与数据采集

> **来源：** http://mp.weixin.qq.com/s?__biz=Mzk3NTk5MjY2MQ==&mid=2247483827&idx=1&sn=1337aa7e10737b2362caddf7a51291af&chksm=c4c26389f3b5ea9fd687d40adc6e9abd5e4bad5e2291e476e9ae8c8fe91c642babca16e72c51#rd
> **抓取时间：** 2026-05-06 12:12:38 +08:00 (Asia/Shanghai)
> **公众号：** 数审派

---

各位审计同仁，大家好！

前两期我们完成了Excel高级功能和SQL基础的学习。今天我们进入入门篇的最后一站——Python爬虫与数据采集**。

作为审计人员，你是否遇到过这些情况：
- • 需要从某个网站获取公开的财务数据，但数据量太大无法手动复制
- • 企业的某个业务系统没有报表导出功能，只能一个个截图
- • 需要定期从外部网站采集数据进行对比分析

这时候，Python爬虫就是你的得力助手！

## 一、认识网络爬虫

### 1.1 什么是网络爬虫？

网络爬虫（Web Scraper）是一种自动获取网页内容的程序。它模拟浏览器访问网站，自动抓取页面中的数据。

用户（手动复制）                    爬虫（自动批量）
    ↓                                    ↓
访问网站 → 找到数据 → 复制到Excel   →  模拟浏览器 → 自动解析页面 → 直接存入数据库`
```

### 1.2 爬虫在审计中的应用场景

| **| 应用场景 | 说明 
| 工商信息采集** | 从工商网站批量获取企业股东、变更、处罚信息 
| 税务数据获取** | 从电子税务局获取企业申报数据 
| 舆情监控** | 监控企业或高管的新闻、公告信息 
| 竞品分析** | 采集竞争对手的公开数据 
| 行业数据** | 从统计局、行业网站采集行业数据用于分析 
| 价格监测** | 监控采购物资的市场价格 

### 1.3 爬虫的基本原理

请求网页 → 获取HTML → 解析数据 → 存储数据
    ↓
┌─────────────────────────────────────┐
│  1. 发送请求（Requests）            │
│  2. 解析页面（BeautifulSoup/Re）    │
│  3. 提取数据（XPath/CSS选择器）     │
│  4. 存储数据（CSV/Excel/数据库）    │
└─────────────────────────────────────┘`
```

## 二、环境准备

### 2.1 安装必要的库

pip install requests beautifulsoup4 pandas openpyxl lxml`
```

### 2.2 库介绍

| **| 库名 | 用途 
| requests** | 发送HTTP请求，获取网页内容 
| beautifulsoup4** | 解析HTML/XML，提取数据 
| pandas** | 数据处理和存储 
| lxml** | 解析器，提高解析效率 

## 三、基础爬虫实战

### 3.1 第一个爬虫：获取网页内容

import requests

# 发送GET请求
url = 'https://example.com'
response = requests.get(url)

# 查看响应状态
print(f"状态码: {response.status_code}")

# 查看网页内容
print(f"内容长度: {len(response.text)} 字符")
print(f"内容预览:\n{response.text[:500]}")`
```

### 3.2 处理中文乱码

import requests

response = requests.get(url)

# 方法1：自动检测编码
response.encoding = response.apparent_encoding

# 方法2：手动指定编码
response.encoding = 'utf-8'

# 方法3：使用content（字节形式）
print(response.content.decode('utf-8'))`
```

### 3.3 添加请求头

很多网站会检测爬虫，我们需要模拟浏览器：

import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

response = requests.get(url, headers=headers)
print(response.text[:500])`
```

## 四、网页解析

### 4.1 BeautifulSoup基础

from bs4 import BeautifulSoup

html = """
<html>
    <body>
        <table id="financial">
            <tr>
                <th>科目</th>
                <th>金额</th>
            </tr>
            <tr>
                <td>营业收入</td>
                <td>10,000,000</td>
            </tr>
            <tr>
                <td>营业成本</td>
                <td>7,000,000</td>
            </tr>
        </table>
    </body>
</html>
"""

# 解析HTML
soup = BeautifulSoup(html, 'lxml')

# 查找表格
table = soup.find('table', id='financial')
print(f"找到表格: {table}")

# 查找所有行
rows = table.find_all('tr')
for row in rows:
    cells = row.find_all(['td', 'th'])
    print([cell.get_text() for cell in cells])`
```

### 4.2 CSS选择器

from bs4 import BeautifulSoup

html = """
<div class="company-info">
    <h1 class="title">某科技有限公司</h1>
    <p class="address">北京市朝阳区XX路1号</p>
    <table class="financial">
        <tr><td>注册资本</td><td>1000万元</td></tr>
        <tr><td>成立日期</td><td>2015-06-01</td></tr>
    </table>
</div>
"""

soup = BeautifulSoup(html, 'lxml')

# 按CSS类名查找
title = soup.find('h1', class_='title')
print(f"公司名称: {title.get_text()}")

# 按标签和属性组合查找
address = soup.find('p', class_='address')
print(f"地址: {address.get_text()}")

# 使用select（CSS选择器）
table = soup.select_one('table.financial')
rows = table.select('tr')
for row in rows:
    cells = row.select('td')
    iflen(cells) == 2:
        print(f"{cells[0].get_text()}: {cells[1].get_text()}")`
```

### 4.3 正则表达式提取

对于复杂的文本模式，正则表达式更强大：

import re

text = """
公司名称：某科技有限公司
注册资本：1000万元人民币
成立日期：2015年6月1日
联系电话：010-12345678
"""

# 提取注册资本
capital = re.search(r'注册资本[：:]\s*(\d+)\s*(?:万元|亿)', text)
if capital:
    print(f"注册资本: {capital.group(1)}万元")

# 提取日期
date = re.search(r'成立日期[：:]\s*(\d{4}[年/-]\d{1,2}[月/-]\d{1,2}[日]?)', text)
if date:
    print(f"成立日期: {date.group(1)}")

# 提取电话号码
phone = re.search(r'(\d{3,4}[-]?\d{7,8})', text)
if phone:
    print(f"电话: {phone.group(1)}")`
```

## 五、实战案例

### 案例一：工商信息采集

从企业信用信息公示系统采集公开的工商信息：

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

defget_business_info(company_name):
    """获取企业工商信息"""
    url = 'https://www.gsxt.gov.cn/corp-query-search-info.html'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    data = {
        'searchword': company_name,
        'tab': '01',
    }

    try:
        response = requests.post(url, data=data, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'lxml')

        results = []

        # 解析搜索结果
        search_results = soup.select('.search-result-item')
        for item in search_results:
            try:
                name = item.select_one('.name').get_text().strip()
                legal_person = item.select_one('.legal-person')
                capital = item.select_one('.capital')
                status = item.select_one('.status')

                results.append({
                    '企业名称': name,
                    '法定代表人': legal_person.get_text().strip() if legal_person else'',
                    '注册资本': capital.get_text().strip() if capital else'',
                    '状态': status.get_text().strip() if status else'',
                })
            except Exception as e:
                print(f"解析错误: {e}")
                continue

        return results

    except Exception as e:
        print(f"请求错误: {e}")
        return []

# 使用示例
companies = ['阿里巴巴（中国）有限公司', '腾讯科技有限公司', '百度在线网络技术有限公司']

all_data = []
for company in companies:
    print(f"正在查询: {company}")
    data = get_business_info(company)
    all_data.extend(data)
    time.sleep(2)  # 避免请求过快

# 保存结果
df = pd.DataFrame(all_data)
df.to_excel('企业工商信息.xlsx', index=False)
print(f"\n已采集 {len(df)} 条企业信息")`
```

### 案例二：审计报告数据采集

从指定网站采集上市公司审计报告数据：

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time

defget_audit_reports(page=1):
    """采集审计报告列表"""
    url = f'https://www.crerc.com/audit-report?page={page}'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'lxml')

    reports = []

    # 假设页面结构
    table = soup.find('table', class_='report-table')
    if table:
        rows = table.select('tbody tr')
        for row in rows:
            cols = row.select('td')

            report = {
                '公司名称': cols[0].get_text().strip(),
                '股票代码': cols[1].get_text().strip(),
                '审计年度': cols[2].get_text().strip(),
                '审计机构': cols[3].get_text().strip(),
                '审计意见': cols[4].get_text().strip(),
                '报告日期': cols[5].get_text().strip(),
            }

            # 提取审计意见类型
            opinion_text = report['审计意见']
            if'标准无保留'in opinion_text:
                report['意见类型'] = '标准无保留'
            elif'保留意见'in opinion_text:
                report['意见类型'] = '保留意见'
            elif'无法表示'in opinion_text:
                report['意见类型'] = '无法表示意见'
            elif'否定'in opinion_text:
                report['意见类型'] = '否定意见'
            else:
                report['意见类型'] = '其他'

            reports.append(report)

    return reports

# 采集多页数据
all_reports = []
for page inrange(1, 6):  # 采集前5页
    print(f"正在采集第 {page} 页...")
    reports = get_audit_reports(page)
    all_reports.extend(reports)
    time.sleep(1)

# 转换为DataFrame
df = pd.DataFrame(all_reports)

# 统计分析
print("\n审计意见分布：")
print(df['意见类型'].value_counts())

# 按年度统计
print("\n各年度审计报告数量：")
print(df.groupby('审计年度').size())

# 保存数据
df.to_excel('审计报告数据.xlsx', index=False)
print(f"\n共采集 {len(df)} 条审计报告")`
```

### 案例三：财务数据定期采集

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime

defget_financial_data(stock_code):
    """获取上市公司财务数据"""
    url = f'https://finance.example.com/stock/{stock_code}/financial'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'lxml')

        # 提取关键财务指标
        data = {
            '股票代码': stock_code,
            '采集时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

        # 查找财务指标表格
        tables = soup.select('table.financial-data')
        for table in tables:
            rows = table.select('tr')
            for row in rows:
                cells = row.select('td')
                iflen(cells) == 2:
                    key = cells[0].get_text().strip()
                    value = cells[1].get_text().strip()
                    data[key] = value

        return data

    except Exception as e:
        print(f"获取 {stock_code} 数据失败: {e}")
        returnNone

defregular_collection(stock_codes, interval_hours=24):
    """定期采集数据"""
    all_data = []

    whileTrue:
        print(f"\n{'='*50}")
        print(f"开始采集时间: {datetime.now()}")
        print(f"{'='*50}")

        for code in stock_codes:
            print(f"正在采集: {code}")
            data = get_financial_data(code)
            if data:
                all_data.append(data)
            time.sleep(1)

        # 保存数据
        df = pd.DataFrame(all_data)
        df.to_excel(f'财务数据_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx', index=False)
        print(f"\n本次共采集 {len(df)} 条数据，已保存")

        # 等待下一次采集
        print(f"\n等待 {interval_hours} 小时后进行下一次采集...")
        time.sleep(interval_hours * 3600)

# 使用示例
stock_list = ['600519', '601318', '000858', '000001']
# regular_collection(stock_list, interval_hours=24)  # 取消注释启动定期采集`
```

## 六、反爬虫与应对策略

### 6.1 常见反爬虫机制

| **| 机制 | 说明 | 应对方法 
| IP封禁** | 短时间内请求过多，IP被封 | 使用代理IP，控制请求频率 
| User-Agent检测** | 检测是否为浏览器 | 添加真实的User-Agent 
| 验证码** | 需要手动输入验证码 | 人工打码服务、机器学习识别 
| Cookie验证** | 需要携带Cookie | 先访问首页获取Cookie 
| JavaScript渲染** | 数据由JS动态生成 | 使用Selenium模拟浏览器 
| 请求频率限制** | 限制单位时间内请求次数 | 添加延时，合理设置请求间隔 

### 6.2 使用Selenium处理JS渲染

有些页面的数据是通过JavaScript动态加载的，requests无法直接获取：

from selenium import webdriver
from selenium.webdriver.common.by import By
import time

# 启动浏览器（需要安装ChromeDriver）
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # 无头模式，不显示浏览器窗口
driver = webdriver.Chrome(options=options)

try:
    # 打开网页
    url = 'https://example.com/dynamic-page'
    driver.get(url)

    # 等待页面加载
    time.sleep(3)

    # 等待特定元素出现
    driver.implicitly_wait(10)

    # 获取页面源代码（已渲染）
    html = driver.page_source

    # 查找数据
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'lxml')
    items = soup.select('.data-item')

    for item in items:
        print(item.get_text())

finally:
    driver.quit()  # 关闭浏览器`
```

### 6.3 设置请求延时

import time

def crawl_with_delay(urls, delay_seconds=1):
    """带延时的爬取"""
    for i, url in enumerate(urls):
        print(f"正在爬取 ({i+1}/{len(urls)}): {url}")

        response = requests.get(url)
        # 处理数据...

        # 延时
        if i < len(urls) - 1:
            print(f"等待 {delay_seconds} 秒...")
            time.sleep(delay_seconds)`
```

## 七、数据存储

### 7.1 保存为CSV

import pandas as pd

# 数据
data = [
    {'公司名称': 'A公司', '营业收入': 10000000, '净利润': 1000000},
    {'公司名称': 'B公司', '营业收入': 20000000, '净利润': 2000000},
]

df = pd.DataFrame(data)

# 保存为CSV
df.to_csv('公司数据.csv', index=False, encoding='utf-8-sig')
print("已保存为CSV文件")`
```

### 7.2 保存为Excel

# 保存为Excel（支持多Sheet）
with pd.ExcelWriter('综合数据.xlsx') as writer:
    df.to_excel(writer, sheet_name='公司基本信息', index=False)

    # 添加另一个Sheet
    df2 = pd.DataFrame({'财务指标': ['ROE', '毛利率'], '数值': [15.5, 30.2]})
    df2.to_excel(writer, sheet_name='财务指标', index=False)

print("已保存为Excel文件")`
```

### 7.3 保存到数据库

import sqlite3

# 连接数据库（SQLite，轻量级，无需安装）
conn = sqlite3.connect('audit_data.db')
cursor = conn.cursor()

# 创建表
cursor.execute('''
    CREATE TABLE IF NOT EXISTS company_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT,
        revenue REAL,
        profit REAL,
        crawl_date TEXT
    )
''')

# 插入数据
data = [
    ('A公司', 10000000, 1000000, '2024-01-01'),
    ('B公司', 20000000, 2000000, '2024-01-01'),
]

cursor.executemany(
    'INSERT INTO company_info (company_name, revenue, profit, crawl_date) VALUES (?, ?, ?, ?)',
    data
)

conn.commit()
conn.close()
print("已保存到数据库")`
```

## 八、法律合规与注意事项

### 8.1 爬虫法律风险

| **| 风险类型 | 说明 | 风险等级 
| 侵犯著作权** | 抓取受版权保护的内容 | 中-高 
| 侵犯商业秘密** | 抓取商业敏感信息 | 高 
| 违反网站协议** | 违反robots.txt或使用条款 | 中 
| 不正当竞争** | 用于商业竞争目的 | 高 
| 个人信息保护** | 抓取个人隐私信息 | 高 

### 8.2 合规爬虫建议

- 1. 遵守robots.txt**：查看网站的robots.txt文件，遵守爬虫协议
- 2. 控制请求频率**：不要对服务器造成过大压力
- 3. 只采集公开数据**：不要采集需要登录的私人数据
- 4. 尊重数据版权**：注明数据来源，不要用于商业侵权
- 5. 保护个人信息**：不要采集和存储个人隐私信息
- 6. 获取授权**：商业用途尽量获取对方授权

### 8.3 robots.txt示例

# robots.txt示例
User-agent: *
Allow: /                     # 允许访问
Disallow: /private/          # 禁止访问
Disallow: /api/              # 禁止访问API

User-agent: Baiduspider       # 百度爬虫特殊规则
Disallow: /`
```

## 九、实战作业

- 1. 环境准备**：

- • 安装Python和相关库
- • 找一个简单的网站练习基础爬取

- 2. 基础练习**：

- • 编写爬虫获取任意网页的标题和链接
- • 使用BeautifulSoup解析HTML表格数据

- 3. 进阶实践**：

- • 选择一个审计相关的公开数据网站
- • 编写完整的数据采集程序
- • 将数据保存到Excel或数据库

- 4. 合规检查**：

- • 了解robots.txt的作用
- • 检查目标网站的爬虫政策

## 总结

今天我们学习了Python爬虫与数据采集：
| **| 知识点 | 说明 | 审计应用 
| requests | 发送HTTP请求 | 获取网页内容 
| BeautifulSoup | HTML解析 | 提取网页数据 
| CSS选择器 | 精确定位元素 | 提取特定数据 
| 正则表达式 | 模式匹配 | 提取复杂文本 
| Selenium | 浏览器自动化 | 处理JS渲染页面 
| 数据存储 | CSV/Excel/数据库 | 保存采集结果 

爬虫是审计人员获取外部数据的重要工具。但使用时务必遵守法律法规，尊重数据版权。

入门篇总结**

我们完成了入门篇的学习：
- • 第一篇：Excel高级功能（数据透视表、Power Query、VBA）
- • 第二篇：SQL基础（数据查询、关联分析）
- • 第三篇：Python爬虫与数据采集

下期预告**：我们将进入进阶篇**的学习！
- • 进阶一：Python数据分析（Pandas、NumPy、Matplotlib）
- • 进阶二：Power BI数据可视化
- • 进阶三：统计学基础（用于异常检测）

进阶篇将带你进入更高级的数据分析领域，敬请期待！

如果你觉得这篇文章有帮助，欢迎转发给需要的同事和朋友。
