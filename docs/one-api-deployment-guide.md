# 融策自建大模型中转站 — 完整部署手册

> 目标：在香港云服务器上部署 one-api 网关，替代 cbwxy.top 单点依赖，实现多模型统一管理、负载均衡、自动故障转移。

---

## 一、服务器选型与购买

### 推荐配置

| 项目 | 推荐 | 备选 |
|:-----|:-----|:-----|
| **地域** | 香港 | 新加坡/东京 |
| **CPU** | 2核 | 1核也能跑 |
| **内存** | 4GB | 2GB（最低） |
| **带宽** | 3-5Mbps | 按量计费 |
| **系统** | Ubuntu 22.04 LTS | Debian 12 |
| **月费** | ¥50-150 | — |

### 推荐商家

| 商家 | 产品 | 参考价 | 优势 |
|:-----|:-----|:------|:-----|
| **阿里云** | 轻量应用服务器-香港 | ¥74/月 (2C2G) | 国内直连延迟低 |
| **腾讯云** | 轻量应用服务器-香港 | ¥67/月 (2C2G) | 同样稳定 |
| **UCloud** | 香港轻量 | ¥50/月 | 性价比高 |
| **AWS Lightsail** | 香港/新加坡 | $5/月 | 国际线路好 |

> ⚠️ **为什么必须是香港？** 只有境外服务器才能直连 OpenAI/Anthropic/Google 官方 API。国内服务器会被墙。

### 服务器初始化（SSH登录后执行）

```bash
# 1. 更新系统
apt update && apt upgrade -y

# 2. 安装 Docker
curl -fsSL https://get.docker.com | bash

# 3. 安装 Docker Compose
apt install docker-compose-plugin -y

# 4. 验证
docker --version
docker compose version

# 5. 设置开机自启
systemctl enable docker

# 6. 设置时区
timedatectl set-timezone Asia/Shanghai

# 7. 防火墙（只开放必要端口）
ufw allow 22/tcp        # SSH
ufw allow 3000/tcp      # one-api Web
ufw allow 80,443/tcp    # HTTP/HTTPS（如需反向代理）
ufw enable
```

---

## 二、部署 one-api

### 2.1 创建目录结构

```bash
mkdir -p /opt/one-api
cd /opt/one-api

# 创建 docker-compose.yml
cat > docker-compose.yml << 'EOF'
services:
  one-api:
    image: justsong/one-api:latest
    container_name: one-api
    restart: always
    ports:
      - "3000:3000"
    environment:
      - TZ=Asia/Shanghai
      # SQLite 模式（默认，无需外部数据库）
      - SQL_DSN=one-api.db
      # 日志级别
      - LOG_SQL_DSN=false
    volumes:
      - ./data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/api/status"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
EOF
```

### 2.2 启动

```bash
docker compose up -d

# 查看日志确认启动
docker compose logs -f
```

看到 `Server started at http://0.0.0.0:3000` 即成功。

### 2.3 首次登录

浏览器打开 `http://<服务器IP>:3000`

- **用户名**: `root`
- **密码**: `123456`

> ⚠️ **第一件事：改密码！** 登录后立即在「系统设置 → 个人设置」改掉默认密码。

---

## 三、配置模型渠道

### 3.1 渠道概念

one-api 的架构：

```
令牌(Token) → 用户鉴权
渠道(Channel) → 模型提供商的API配置
模型 → 渠道 + 模型名的组合
```

一个模型可以配多个渠道，one-api 自动负载均衡 + 故障转移。

### 3.2 添加渠道 — 国内模型（免翻墙，优先配）

#### 渠道1：DeepSeek 官方（你的主力）

1. 「渠道」→「添加渠道」
2. 填写：

| 字段 | 值 |
|:-----|:---|
| 名称 | `DeepSeek-官方` |
| 类型 | `DeepSeek` |
| 模型 | `deepseek-chat,deepseek-reasoner` |
| 密钥 | `你的DeepSeek API Key` |
| 代理 | 留空（直连） |
| 分组 | `default` |

- DeepSeek API Key 获取：https://platform.deepseek.com/api_keys
- deepseek-chat = V3/Flash，deepseek-reasoner = R1/Pro

#### 渠道2：通义千问（阿里云）

| 字段 | 值 |
|:-----|:---|
| 名称 | `通义千问-官方` |
| 类型 | `阿里通义千问` |
| 模型 | `qwen-max,qwen-plus,qwen-turbo` |
| 密钥 | `阿里云 DashScope API Key` |
| 代理 | 留空 |

- 获取：https://dashscope.console.aliyun.com/apiKey

#### 渠道3：豆包（火山引擎）

| 字段 | 值 |
|:-----|:---|
| 名称 | `豆包-火山引擎` |
| 类型 | `字节豆包` |
| 模型 | `doubao-pro-32k,doubao-lite-32k` |
| 密钥 | `火山引擎 Access Key` |
| 代理 | 留空 |

- 获取：https://console.volcengine.com/ark

#### 渠道4：智谱 GLM

| 字段 | 值 |
|:-----|:---|
| 名称 | `智谱-GLM` |
| 类型 | `智谱ChatGLM` |
| 模型 | `glm-4-flash,glm-4-plus` |
| 密钥 | `智谱 API Key` |
| 代理 | 留空 |

#### 渠道5：硅基流动（多模型聚合，强烈推荐）

硅基流动一个API Key可以调用几十个开源模型，性价比极高：

| 字段 | 值 |
|:-----|:---|
| 名称 | `硅基流动` |
| 类型 | `硅基流动(SiliconCloud)` |
| 模型 | `deepseek-ai/DeepSeek-V3,deepseek-ai/DeepSeek-R1,Qwen/Qwen2.5-72B-Instruct` |
| 密钥 | `SiliconCloud API Key` |

- 获取：https://cloud.siliconflow.cn → 注册即送额度

### 3.3 添加渠道 — 海外模型（香港直连）

#### 渠道6：OpenAI（GPT-4/5）

| 字段 | 值 |
|:-----|:---|
| 名称 | `OpenAI-官方` |
| 类型 | `OpenAI` |
| 模型 | `gpt-4o,gpt-4o-mini,gpt-4.1` |
| 密钥 | `sk-xxx...` |
| 代理 | 留空（香港直连） |

- 获取：https://platform.openai.com/api-keys
- ⚠️ 需要海外信用卡或充值渠道

#### 渠道7：Anthropic（Claude）

| 字段 | 值 |
|:-----|:---|
| 名称 | `Anthropic-官方` |
| 类型 | `Anthropic Claude` |
| 模型 | `claude-sonnet-4-20250514,claude-opus-4-20250514` |
| 密钥 | `sk-ant-xxx...` |
| 代理 | 留空（香港直连） |

#### 渠道8：Google Gemini

| 字段 | 值 |
|:-----|:---|
| 名称 | `Google-Gemini` |
| 类型 | `Google Gemini` |
| 模型 | `gemini-2.5-pro,gemini-2.5-flash` |
| 密钥 | Gemini API Key |

#### 渠道9：xAI Grok

| 字段 | 值 |
|:-----|:---|
| 名称 | `xAI-Grok` |
| 类型 | `xAI` |
| 模型 | `grok-3` |
| 密钥 | xAI API Key |

### 3.4 渠道备份策略（关键！）

**同一个模型配置多个渠道 = 自动故障转移**

例如 DeepSeek 模型：

| 优先级 | 渠道 | 作用 |
|:------|:-----|:-----|
| 主 | DeepSeek 官方 | 免费，主力 |
| 备1 | 硅基流动 | 稳定，付费 |
| 备2 | cbwxy.top（保留） | 与原代理兼容 |

在 one-api 中为同一个模型 `deepseek-chat` 添加3个渠道，one-api 会：
1. 默认走优先级最高的可用渠道
2. 主渠道挂了自动切备用
3. 恢复后自动切回

---

## 四、配置令牌（API Key）

one-api 通过「令牌」管理访问权限：

1. 「令牌」→「添加令牌」
2. 填写：

| 字段 | 值 |
|:-----|:---|
| 名称 | `融策-生产环境` |
| 过期时间 | 永不过期（或设1年） |
| 额度 | 不限制（或设 $100） |
| 允许的模型范围 | 全部 |
| IP限制 | 留空（或限制为公司IP） |

3. 生成的 `sk-xxxxxxxxxxxx` 就是网关的 API Key

---

## 五、接入 OpenClaw

### 5.1 改造 models.json 为直连 one-api

将现有所有 provider 合并为一个 `rongce-gateway` 即可：

```json
{
  "models": {
    "providers": {
      "rongce-gateway": {
        "apiKey": "sk-你的one-api令牌key",
        "baseUrl": "http://你的服务器IP:3000/v1",
        "api": "openai-completions",
        "models": [
          {
            "id": "deepseek-chat",
            "name": "DeepSeek V4 Flash",
            "input": ["text"]
          },
          {
            "id": "deepseek-reasoner",
            "name": "DeepSeek V4 Pro",
            "input": ["text"]
          },
          {
            "id": "gpt-4o",
            "name": "GPT-4o",
            "input": ["text", "image"]
          },
          {
            "id": "gpt-4.1",
            "name": "GPT-4.1",
            "input": ["text", "image"]
          },
          {
            "id": "claude-sonnet-4-20250514",
            "name": "Claude Sonnet 4",
            "input": ["text", "image"]
          },
          {
            "id": "claude-opus-4-20250514",
            "name": "Claude Opus 4",
            "input": ["text", "image"]
          },
          {
            "id": "gemini-2.5-pro",
            "name": "Gemini 2.5 Pro",
            "input": ["text", "image"]
          },
          {
            "id": "gemini-2.5-flash",
            "name": "Gemini 2.5 Flash",
            "input": ["text", "image"]
          },
          {
            "id": "qwen-max",
            "name": "通义千问 Max",
            "input": ["text"]
          },
          {
            "id": "qwen-plus",
            "name": "通义千问 Plus",
            "input": ["text"]
          },
          {
            "id": "doubao-pro-32k",
            "name": "豆包 Pro 32K",
            "input": ["text"]
          },
          {
            "id": "glm-4-flash",
            "name": "智谱 GLM-4 Flash（免费）",
            "input": ["text"]
          },
          {
            "id": "grok-3",
            "name": "Grok 3",
            "input": ["text"]
          }
        ]
      },
      "rongce-gateway-claude": {
        "apiKey": "sk-你的one-api令牌key",
        "baseUrl": "http://你的服务器IP:3000",
        "api": "anthropic-messages",
        "models": [
          {
            "id": "claude-sonnet-4-20250514",
            "name": "Claude Sonnet 4 (原生)",
            "input": ["text", "image"]
          },
          {
            "id": "claude-opus-4-20250514",
            "name": "Claude Opus 4 (原生)",
            "input": ["text", "image"]
          }
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "rongce-gateway/deepseek-chat",
        "fallbacks": [
          "rongce-gateway/deepseek-reasoner",
          "rongce-gateway-claude/claude-sonnet-4-20250514"
        ]
      }
    }
  }
}
```

> 📌 **注意**：one-api 对 OpenAI 格式的支持最完善。Claude 的 anthropic-messages 原生格式也支持，但建议同时配一个 OpenAI 兼容的 Claude 渠道（one-api 会自动转换）。此处配置两套 provider 是保险做法。

### 5.2 渐进式迁移（推荐）

不要一步到位把 cbwxy 全删了。**先并存，验证稳定后再下线：**

```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "rongce-gateway/deepseek-chat",
        "fallbacks": [
          "custom-cbwyy-top-v1/deepseek-v4-flash",
          "rongce-gateway/deepseek-reasoner",
          "custom-cbwyy-claude/claude-sonnet-5"
        ]
      }
    }
  }
}
```

这样 one-api 挂了自动回退到 cbwxy，等于双重保险。等 one-api 稳定跑 1-2 周后再删 cbwxy。

---

## 六、安全加固

### 6.1 使用 Nginx 反向代理 + HTTPS

```bash
# 在服务器上安装 nginx + certbot
apt install nginx certbot python3-certbot-nginx -y

# 配置反向代理（如果已有域名）
cat > /etc/nginx/sites-available/one-api << 'EOF'
server {
    listen 80;
    server_name ai.rongce.com;  # 换成你的域名

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;  # SSE流式传输必须关闭
    }
}
EOF

ln -s /etc/nginx/sites-available/one-api /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# 申请 SSL 证书
certbot --nginx -d ai.rongce.com
```

### 6.2 如果没有域名

可以用纯 IP 访问，但建议至少做以下加固：

```bash
# 1. 修改 one-api docker-compose 端口为仅本地监听
# ports:
#   - "127.0.0.1:3000:3000"

# 2. 用 SSH 隧道访问管理后台（从本地电脑执行）
ssh -L 3000:localhost:3000 root@你的服务器IP
# 然后浏览器打开 http://localhost:3000
```

### 6.3 one-api 自身安全设置

登录 one-api 后台：

- 「系统设置」→ 修改默认 root 密码
- 「系统设置」→ 关闭「允许新用户注册」  
- 「令牌」→ 如果有IP限制需求，限制为公司出口IP

### 6.4 审计数据安全

在 one-api 渠道分组中设置数据路由规则：

| 数据类型 | 路由分组 | 允许模型 |
|:-----|:-----|:-----|
| 公开信息/日常 | `default` | 全部模型 |
| 脱敏审计数据 | `domestic-only` | 仅国内模型（DeepSeek/通义/豆包） |
| 敏感财务数据 | `local-only` | 仅 DeepSeek（数据不出境焦虑最低） |

---

## 七、监控与运维

### 7.1 健康检查

```bash
# 添加 cron 定时检查
crontab -e

# 每5分钟检查一次，挂了自动重启
*/5 * * * * /usr/bin/docker ps | grep one-api || /usr/bin/docker compose -f /opt/one-api/docker-compose.yml up -d
```

### 7.2 日志查看

```bash
# one-api 日志
docker compose -f /opt/one-api/docker-compose.yml logs -f --tail=100

# Nginx 访问日志
tail -f /var/log/nginx/access.log
```

### 7.3 备份

```bash
# 定期备份 one-api 数据库（含所有渠道配置、令牌）
0 3 * * * cp /opt/one-api/data/one-api.db /opt/backups/one-api-$(date +\%Y\%m\%d).db
```

### 7.4 更新 one-api

```bash
cd /opt/one-api
docker compose pull     # 拉取最新镜像
docker compose up -d    # 重建容器
```

---

## 八、费用预估（月）

| 项目 | 保守 | 正常 | 备注 |
|:-----|:----:|:----:|:-----|
| 服务器 | ¥67 | ¥74 | 腾讯/阿里轻量香港 |
| DeepSeek API | ¥0 | ¥0 | Flash免费，Pro极低 |
| 通义千问 | ¥0 | ¥5 | 有免费额度 |
| 豆包 | ¥0 | ¥5 | 有免费额度 |
| 智谱 GLM | ¥0 | ¥0 | Flash免费 |
| 硅基流动 | ¥0 | ¥10 | 注册送额度 |
| OpenAI GPT | — | ¥30-100 | 按需 |
| Anthropic Claude | — | ¥20-80 | 按需 |
| Google Gemini | ¥0 | ¥5 | 免费额度大 |
| **月合计** | **¥67** | **¥150-300** | 含API |

对比：cbwxy.top 的代理费+溢价抽水，自建后大概率更便宜。

---

## 九、执行清单

```
□ 1. 购买香港云服务器（阿里云/腾讯云轻量）
□ 2. SSH登录，执行初始化脚本（Docker安装）
□ 3. 部署 one-api（docker compose up -d）
□ 4. 登录改密码
□ 5. 注册/获取各模型官方API Key
     □ DeepSeek: https://platform.deepseek.com
     □ 通义千问: https://dashscope.console.aliyun.com
     □ 豆包: https://console.volcengine.com/ark
     □ 智谱: https://open.bigmodel.cn
     □ 硅基流动: https://cloud.siliconflow.cn
     □ OpenAI: https://platform.openai.com（需海外充值）
     □ Anthropic: https://console.anthropic.com
     □ Google: https://aistudio.google.com
□ 6. 在 one-api 中添加各渠道
□ 7. 创建令牌（API Key）
□ 8. 用 curl 测试网关连通性
□ 9. 配置 Nginx + HTTPS（如有域名）
□ 10. 修改 OpenClaw models.json 加入 rongce-gateway
□ 11. 先在 fallback 位置验证，观察1周稳定性
□ 12. 切换 primary 到 one-api
□ 13. 稳定2周后下线 cbwxy 旧配置
```

---

## 十、测试命令

部署完成后用这些命令验证：

```bash
# 测试 OpenAI 兼容接口（DeepSeek通过one-api）
curl http://你的服务器IP:3000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-你的令牌key" \
  -d '{
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "你好，请用一句话自我介绍"}],
    "stream": false
  }'

# 测试 通义千问
curl http://你的服务器IP:3000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-你的令牌key" \
  -d '{
    "model": "qwen-plus",
    "messages": [{"role": "user", "content": "你好"}],
    "stream": false
  }'
```

---

*文档版本: v1.0 | 创建日期: 2026-07-06 | 适用对象: 融策公司*
