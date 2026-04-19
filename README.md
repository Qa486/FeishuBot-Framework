# 🤖 Feishu Bot Framework

> 飞书（Lark）模块化机器人 SaaS 框架 · Python + Flask + APScheduler

[English](README-en.md) | 简体中文

---

## 📌 简介

Feishu Bot Framework 是一套面向小型企业的飞书机器人 SaaS 开发框架。无需编程基础，通过 YAML 配置文件即可管理自动回复、定时通知、问卷调查、FAQ 助手和消息转发五大模块。代码结构清晰，支持 Docker 一键部署，方便二次开发和转售给不同客户。

**核心特性：**
- 🔁 **自动回复** — 关键词触发，支持文本/富文本/图片/卡片
- 📅 **定时通知** — Cron 表达式驱动，向任意群或用户推送
- 📋 **问卷调查** — 飞书卡片投票，实时收集反馈
- 💬 **FAQ 助手** — 模糊匹配智能问答引擎
- 🔄 **消息转发** — 跨群/跨用户路由，支持关键词过滤
- 🖥️ **Web 管理后台** — 可视化配置，技术人员和非技术人员均可用

---

## 🏗️ 技术栈

| 组件 | 技术选型 |
|------|---------|
| Web 框架 | Flask 3.0 |
| 定时任务 | APScheduler |
| 配置格式 | YAML (PyYAML) |
| 飞书 API | 飞书开放平台 REST API |
| 容器化 | Docker + Docker Compose |
| 前端 | 原生 HTML/CSS/JS（无框架依赖）|

---

## 🚀 快速部署

### 前置要求

- Python 3.10+
- 飞书企业自建应用（[飞书开放平台](https://open.feishu.cn/)）

### 方式一：手动部署

```bash
# 1. 克隆项目
git clone https://github.com/your-repo/feishu-bot-framework.git
cd feishu-bot-framework

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置
cp config_example.yaml config.yaml
# 编辑 config.yaml，填入飞书 App ID / Secret / Verification Token

# 5. 启动
python bot.py
```

### 方式二：Docker 部署

```bash
# 1. 配置
cp config_example.yaml config.yaml
# 编辑 config.yaml

# 2. 构建并启动
docker-compose up -d

# 3. 查看日志
docker-compose logs -f
```

> `docker-compose.yml` 已包含在项目中，基于官方 Python 镜像，开箱即用。

### 方式三：云托管（Pro 版用户）

联系我们的销售团队，获取专属云托管链接，扫码即可开通，无需任何服务器操作。

---

## ⚙️ 配置说明

### 主配置文件 `config.yaml`

```yaml
feishu:
  app_id: "cli_xxxxxxxxxx"           # 飞书应用 App ID
  app_secret: "xxxxxxxxxxxx"          # 飞书应用 App Secret
  verification_token: "xxxxxxxxxx"    # 事件订阅 Verification Token
  encrypt_key: "xxxxxxxxxxxxxx"      # 事件加密密钥（可选）

server:
  host: "0.0.0.0"
  port: 8080
  debug: false

modules:
  auto_reply:
    enabled: true
    config_file: "modules/auto_reply/config.yaml"
  scheduler:
    enabled: true
    config_file: "modules/scheduler/config.yaml"
  survey:
    enabled: true
    config_file: "modules/survey/config.yaml"
  faq:
    enabled: true
    config_file: "modules/faq/config.yaml"
  forwarder:
    enabled: true
    config_file: "modules/forwarder/config.yaml"

dashboard:
  enabled: true
  username: "admin"
  password: "change_me_123"
  secret_key: "your-flask-secret-key"
```

### 模块独立配置

每个模块有独立的 `config.yaml`，修改后重启 bot 即可生效：

```
modules/
├── auto_reply/config.yaml   # 自动回复规则
├── scheduler/config.yaml    # 定时任务
├── survey/config.yaml       # 问卷模板
├── faq/config.yaml          # FAQ 问答对
└── forwarder/config.yaml    # 转发规则
```

### 飞书应用权限配置

在飞书开放平台 > 应用功能 > 权限管理，申请以下权限：

| 权限名 | 说明 |
|--------|------|
| `im:message` | 读取和发送消息 |
| `im:message.group_at_msg` | 接收群 @ 机器人消息 |
| `im:chat` | 获取群信息 |
| `contact:user` | 读取用户信息 |

---

## 🌐 Web 管理后台

启动服务后访问 `http://your-host:8080/dashboard/`

- **用户名**：`admin`（可在 config.yaml 中修改）
- **密码**：`change_me_123`（首次使用请务必修改）
- 功能：查看各模块状态，在线编辑 YAML 配置

---

## 💰 定价方案

| 版本 | 价格 | 适用场景 |
|------|------|---------|
| **Free 免费版** | ¥0 / 永久 | 个人开发者、技术团队自建 |
| **Pro 专业版** | ¥99/月 | 小型企业，托管 + 免运维 |
| **Enterprise 定制版** | 定制报价 | 中大型企业，私有化部署 |

### Free 功能列表
- ✅ 1 个机器人实例
- ✅ 5 大模块完整功能
- ✅ 无限规则 / FAQ 条目
- ✅ Docker 部署支持
- ✅ 社区技术支持

### Pro 功能列表
- ✅ 无限机器人实例
- ✅ 云端托管（无需服务器）
- ✅ 自定义品牌（Logo、名称）
- ✅ 数据统计面板
- ✅ 专属技术支持群

---

## 🏗️ 二次开发指南

### 添加新模块

1. 在 `modules/` 下创建新目录，例如 `modules/my_module/`
2. 创建 `module.py`，实现以下接口：

```python
class MyModule:
    NAME = "my_module"

    def __init__(self, feishu, config: dict, logger):
        ...

    def handle(self, event_type: str, event: dict, msg: dict, feishu_client):
        # 处理飞书事件
        pass

    def get_config(self) -> dict:
        return {}

    def save_config(self, data: dict) -> bool:
        return True

    def status(self) -> dict:
        return {}
```

3. 在 `bot.py` 的 `load_module()` 函数中注册新模块
4. 在 `config.yaml` 的 `modules:` 下添加配置项

### 修改消息处理器

主事件入口在 `bot.py` 的 `/webhook/feishu` 路由。所有消息经 `modules/*/handle()` 分发给各模块。

### 自定义卡片模板

FAQ 和 Survey 模块支持飞书[交互式卡片](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/im-v1/message-card guid)格式，参考飞书官方文档。

---

## 📁 项目结构

```
feishu-bot-framework/
├── bot.py                    # 主入口，Flask 路由 + 模块调度
├── feishu_client.py          # 飞书 API 客户端（认证/发消息/文件）
├── config_example.yaml       # 配置示例
├── requirements.txt          # Python 依赖
├── README.md                  # 中文说明
├── README-en.md              # English README
│
├── modules/
│   ├── auto_reply/           # 自动回复模块
│   │   ├── module.py
│   │   └── config.yaml
│   ├── scheduler/            # 定时通知模块
│   │   ├── module.py
│   │   └── config.yaml
│   ├── survey/               # 问卷调查模块
│   │   ├── module.py
│   │   └── config.yaml
│   ├── faq/                  # FAQ 助手模块
│   │   ├── module.py
│   │   └── config.yaml
│   └── forwarder/            # 消息转发模块
│       ├── module.py
│       └── config.yaml
│
├── dashboard/                # Web 管理后台（HTML + JS）
│   └── index.html
│
├── public/                   # 公开静态页面（产品介绍页）
│   └── index.html
│
└── docker/
    ├── Dockerfile
    └── docker-compose.yml
```

---

## 🐛 常见问题

**Q: 机器人收不到消息？**
- 检查飞书开放平台的「事件订阅」配置，确认 Webhook URL 已填写并通过验证
- 确认应用已开通 `im:message` 和 `im:message.group_at_msg` 权限
- 确认机器人已加入目标群

**Q: 定时任务没有触发？**
- 确认 APScheduler 时区设置为 `Asia/Shanghai`
- 检查 `modules/scheduler/config.yaml` 中的 cron 时间是否正确

**Q: Docker 启动失败？**
- 确认 Dockerfile 和 docker-compose.yml 路径正确
- 确认 config.yaml 中的凭证格式无误

---

## 📄 License

MIT License — 可自由使用、修改和商业转售。

---

## 🔗 相关链接

- [飞书开放平台文档](https://open.feishu.cn/document/)
- [Feishu Card Builder](https://open.feishu.cn/document/ukTMukTMukTM/im-v1/message-card/create)
- [飞书 Bot 官方指南](https://open.feishu.cn/document/ukTMukTMukTM/bot-v3/bot-overview)
