# 应用 | 如何在不联网的离线环境下安装python库

- **日期**: 2021-01-19
- **标签**: 应用
- **原文链接**: https://mp.weixin.qq.com/s?__biz=MzI1NTA5NDA2MA==&mid=2648441772&idx=1&sn=59e5c8a689d736ca24cb56d447ea3227

---

内容摘要：内外网隔离情况下，不联网的机器如何在离线环境下安装python库？

## 问题背景

在内部审计工作中，根据数据安全管理需要，内部审计人员使用的机器内部网和外部网一般是隔离的。虽然anaconda自带了常用的python库，但在数字化审计过程中，安装新的库会面临：
- 无法直接连接互联网，通过"pip install 库名"的方式直接在线安装；
- Python库之间可能存在多重依赖，多层嵌套的库依赖操作繁琐。

## 解决思路

1. 在连接互联网的机器上使用"pip install 库名"安装所需要的新python库。
2. 安装python的依赖库管理工具 pipdeptree，使用pipdeptree生成requirements.txt。
3. 使用"pip download"根据requirements.txt下载库所依赖的所有库。
4. 将下载的所有库复制到内部网机器上的指定目录。
5. 在内部网机器上使用"pip install"并指定find-links参数即可安装。

## 实战案例：安装pyautogui

### 联网机器操作：
```bash
# 生成依赖库文件
pipdeptree -f -p pyautogui > D:\pyautogui\requirements.txt

# 下载pyautogui及其依赖库的安装文件
pip download -d D:\pyautogui -r D:\pyautogui\requirements.txt
```

### 离线机器操作：
```bash
# 离线安装pyautogui库
pip install --no-index --find-links=D:\pyautogui -r D:\pyautogui\requirements.txt
```

注意：要求内外网机器必须是同一位数类型的操作系统，比如都是windows10 64位。
