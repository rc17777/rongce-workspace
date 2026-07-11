# 工具 | Neo4j：善于处理关系，所以强大（二）- 部署和应用

- **日期**: 2020-11-09
- **标签**: 工具
- **原文链接**: https://mp.weixin.qq.com/s?__biz=MzI1NTA5NDA2MA==&mid=2648441713&idx=1&sn=1003084db47a25f6c86653eb4825316b

---

内容导读：安装部署 neo4j，实战招标数据异常分析

本文中的所有信息和数据都是虚拟的，仅为说明数据化审计的思路和过程，不代表真实的交易情况。代码很业余，只为抛砖引玉，拓展思路。专业人士请忽略！

全文内容较多，分为两个部分：
- 第一部分：业务背景，数据库技术介绍，图数据库 Neo4j 概述。（文章链接）
- 第二部分：图数据库 Neo4j 审计应用实例。分为3个章节：Part I Neo4j数据库部署，Part II 用图数据视角理解数据和cypher语言初步，Part III 数据转换和实战招标异常数据分析

## Part I Neo4j安装部署

### 1.软件下载

适用环境 win7及以上，请注意区分32位系统和64位系统。下载Java环境软件 jdk-8u181-windows-x64.exe （32位系统用 jdk-8u181-windows-i586.exe ) 和 neo4j-community_windows-x64_3_0_3.exe （32位系统用 neo4j-community_windows_3_0_3.exe ）

鉴于官网软件下载速度比较慢，可以关注公众号"数据化审计"后，在公众号对话框中输入 "neo4j" 获取软件、资料和数据的下载链接。

### 2.Java环境

快捷键 Win+R 打开运行窗口，输入 cmd 打开命令行窗口，输入 java -version 命令运行。如果出现如下内容：

```
java version "1.8.0_60"
Java(TM) SE Runtime Environment (build 1.8.0_60-b27)
Java HotSpot(TM) 64-Bit Server VM (build 25.60-b23, mixed mode)
```

就说明Java环境正常。否则运行 jdk-8u181-windows-x64.exe，一路默认即可。

### 3.安装 neo4j 3.0.3 社区版

运行 neo4j-community_windows-x64_3_0_3.exe，一路默认即可。

为避免后续运行遇到奇怪的问题，强烈建议：
- 安装在系统盘C盘之外，防止读写权限问题；
- 不要安装在中文目录下，防止数据读写异常。

## 启动和初始化数据库

### 1.启动 Neo4j 数据库

安装完毕，就可以在开始菜单看到 Neo4j Community Edition 菜单了，点击菜单启动数据库。由于是Java程序，首次运行会有点慢，耐心等待。

### 2.初始化数据库

主要包括如下步骤：
- 设置Neo4j数据库的数据存放路径。比如 D:\data\databases\audit，如果不存在会自动创建目录；
- 启动Neo4j数据库。窗口出现绿色背景提示：Neo4j is ready. Browse to http://localhost:7474/ 说明一切顺利；
- 通过浏览器访问Neo4j数据库。打开firefox等浏览器，访问网址：http://localhost:7474/，初始用户和密码都是neo4j；
- 重置Neo4j数据库密码。将初始密码改为自己的密码。
