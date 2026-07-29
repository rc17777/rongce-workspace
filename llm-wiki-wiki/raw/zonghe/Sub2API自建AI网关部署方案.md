# Sub2API 自建AI网关部署方案（美西VPS + 国内回源）

> 创建日期：2026-07-15
> 状态：方案确认，待采购VPS后实施
> 场景：替代第三方中转站（cbwyy.top 类），自建可控的 AI API 网关，国内免科学上网访问，支持支付宝/微信结算
> 决策人：融策平头哥（已选定：美西VPS + 国内CDN回源路线）

## 一、项目背景

| 痛点 | 自建解法 |
|:--|:--|
| 第三方中转站权限说变就变（2026-07-15 gemini 403 事件） | 上游账号自持，权限自控 |
| 充值差价被中间商赚走 | 上游API原价 + 基础设施成本 ≈ ¥660-1000/年 |
| 稳定性依赖别人 | 自己运维，Docker 一键升级/迁移 |
| 支付方式不透明 | 内置支付宝/微信/易支付/Stripe 收款 |

## 二、核心开源项目

**Wei-Shaw/sub2api**（32,278⭐，Go + Vue + PostgreSQL + Redis）
- GitHub: https://github.com/Wei-Shaw/sub2api
- 功能：把 Claude/OpenAI/Gemini/Grok 订阅或API Key 统一接入，生成 OpenAI 兼容 API Key 分发
- 特性：多账号池智能调度、粘性会话、Token级计费、并发/限流控制、**内置支付系统**（原 sub2apipay 已合并）、Web管理后台、一键升级
- 配套生态：
  - qixing-jk/all-api-hub（4,458⭐）：余额/用量管理面板
  - ckken/sub2api-mobile：移动端管理App

### ⚠️ 风险声明（README官方警告）
1. 订阅转API分发**违反 Anthropic 等上游服务条款**，账号有封禁风险
2. 项目**不授权商业化运营**——自用/公司内部用OK，公开售卖是灰色地带
3. **融策数据合规红线**：敏感审计项目数据（经责/补贴/国企/纪检）仍只走国内模型，不过境外服务器

## 三、架构

```
国内用户（免科学上网）
    │ HTTPS
    ▼
国内入口（二选一）
  方案A：腾讯云CDN动态加速（ECDN） ← 需备案域名
  方案B：腾讯云轻量服务器 Nginx 反代 ← 备案服务器复用，¥0增量 ⭐先用这个
    │ CN2 GIA 优化线路
    ▼
美西VPS（搬瓦工 洛杉矶 DC6/DC9）
  Docker: sub2api + PostgreSQL + Redis
    │ 境外直连（无墙）
    ▼
上游AI：Claude / OpenAI / Gemini / Grok
```

**关键结论：服务端在境外直连上游，客户端在国内直连入口，两头都不需要科学上网。**

## 四、采购清单

| 项目 | 商家/规格 | 年成本 | 支付方式 |
|:--|:--|:--|:--|
| 美西VPS | 搬瓦工 CN2 GIA-E 2G（bandwagonhost.com，洛杉矶DC6/DC9） | ~$65.99 ≈ ¥480 | 支付宝 |
| 备选VPS | DMIT LAX Pro（dmit.io，更稳更贵） | ~$100+ | 支付宝/微信 |
| 国内轻量服务器 | 腾讯云轻量 2C2G4M（备案锚点+Nginx反代） | ~¥112 | 微信/支付宝 |
| 域名 | 腾讯云/阿里云 .com（中性名称，勿带ai/gpt字样） | ~¥70 | 微信/支付宝 |
| CDN（可选） | 腾讯云ECDN动态加速 | ¥120-360 | 按量 |
| **合计** | | **¥660-1000/年** | |

## 五、实施时间线

```
第1天    买VPS+域名+轻量服务器 → Docker部署sub2api → IP:8080 直连先用起来
第1-2天  提交企业备案（腾讯云备案小程序：营业执照+法人身份证+人脸核验）
第2-21天 管局审核期（不影响IP直连使用）
备案通过 配置Nginx反代/CDN + HTTPS证书 → 域名正式切换
```

## 六、部署命令（美西VPS上）

```bash
# 1. 装 Docker
curl -fsSL https://get.docker.com | bash

# 2. 一键部署（自动生成密钥/建目录/下载compose）
mkdir -p sub2api-deploy && cd sub2api-deploy
curl -sSL https://raw.githubusercontent.com/Wei-Shaw/sub2api/main/deploy/docker-deploy.sh | bash
docker compose up -d

# 3. 日志确认 + 找初始管理员密码
docker compose logs -f sub2api
docker compose logs sub2api | grep "admin password"

# 4. 浏览器打开 http://VPS_IP:8080 走初始化向导（配库+建管理员）
```

### 日常维护
```bash
docker compose pull && docker compose up -d        # 升级（或后台一键升级）
docker compose down && tar czf backup.tar.gz .     # 整站备份/迁移（local目录版）
```

## 七、国内反代配置（腾讯云轻量服务器）

```nginx
server {
    listen 443 ssl;
    server_name api.你的域名.com;
    ssl_certificate     /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    location / {
        proxy_pass https://美西VPS_IP:8080;
        proxy_ssl_server_name on;
        proxy_read_timeout 300s;   # AI流式响应长超时
        proxy_buffering off;       # 关缓冲，流式输出不卡顿
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## 八、支付配置（sub2api 内置）

管理后台按 `docs/PAYMENT.md` 配置，支持四渠道：

| 渠道 | 门槛 | 适用 |
|:--|:--|:--|
| 易支付 EasyPay | 最低，个人可用 | 聚合支付宝/微信 |
| 支付宝官方 | 企业商户号 | ⭐融策有公司主体，走官方 |
| 微信支付官方 | 企业商户号 | ⭐同上 |
| Stripe | 国际信用卡 | 海外收款 |

## 九、上游账号接入

管理后台 → 账号管理：
- **OAuth订阅**：Claude Pro/Max、ChatGPT Plus 订阅授权接入（拼车模式）
- **API Key**：Anthropic/OpenAI/Gemini 官方 Key 直填
- 多账号池自动调度，单账号限流自动切换

## 十、安全加固清单

- [ ] `security.url_allowlist.allow_insecure_http: false`（强制HTTPS）
- [ ] 管理后台开 2FA（TOTP）
- [ ] IP直连过渡期后关闭 8080 公网暴露，只留反代通道
- [ ] JWT_SECRET / TOTP_ENCRYPTION_KEY 妥善保存（部署脚本自动生成）
- [ ] 定期 `tar czf` 备份整个部署目录

## 十一、与 OpenClaw 的对接

部署完成后，把 openclaw.json 里 provider 的 baseUrl 从 cbwyy.top 换成自建网关：
```
baseUrl: https://api.你的域名.com/v1（备案后）
       或 http://VPS_IP:8080/v1（过渡期）
```
注意：换 baseUrl/key 时同步更新 `scripts/model_health_check.py` 里的副本（两份存储的老坑）。

## 附：参考资料
- README 存档：`output/sub2api_readme.md`
- 官方文档：https://github.com/Wei-Shaw/sub2api/tree/main/docs
- 支付配置：https://github.com/Wei-Shaw/sub2api/blob/main/docs/PAYMENT.md
